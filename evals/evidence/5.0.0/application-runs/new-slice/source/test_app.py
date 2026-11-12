"""Behavior at actual HTTP/persistence boundaries; no external dependencies."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app

ROOT = Path(__file__).parent


class QueueTests(unittest.TestCase):
    def setUp(self):
        (ROOT / 'evidence').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'evidence')
        self.data = Path(self.temp.name) / 'queue.sqlite'
        self.start()

    def start(self):
        self.server = app.create_server('127.0.0.1', 0, self.data)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_address[1])

    def stop(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive())
        self.server.server_close()

    def tearDown(self):
        self.stop()
        self.temp.cleanup()

    def request(self, path, value=None, raw=None, method=None, headers=None):
        body = raw if raw is not None else json.dumps(value).encode() if value is not None else None
        req = Request(self.url + path, data=body, method=method,
                      headers={'Content-Type': 'application/json', **(headers or {})})
        try:
            with urlopen(req, timeout=5) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_titles_boundaries_and_exact_roundtrip(self):
        for title in ['x', 'x' * 120, '🚲' * 120, "<img src=x onerror=alert(1)> ' ; --", 'embedded\x00character', '\x00first']:
            with self.subTest(title=repr(title[:20])):
                status, result = self.request('/api/tickets', {'title': title})
                self.assertEqual(status, 201)
                self.assertEqual(result['title'], title)
        self.assertEqual(self.request('/api/tickets', {'title': '  padded  '})[1]['title'], 'padded')
        for title in ['', ' \n\t ', 'x' * 121, '🚲' * 121, None, True, 9, [], {}, '\ud800']:
            self.assertEqual(self.request('/api/tickets', {'title': title})[0], 400)
        self.assertEqual(len(self.request('/api/tickets')[1]), 7)

    def test_invalid_bodies_and_filters_do_not_write(self):
        for raw in [b'{', b'[]', b'null', b'"title"', b'\xff', b'']:
            self.assertEqual(self.request('/api/tickets', raw=raw, method='POST')[0], 400)
        self.assertEqual(self.request('/api/tickets', raw=b'{}', headers={'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.request('/api/tickets', raw=b'x' * 8193)[0], 413)
        for query in ['status=', 'status=other', 'status=open&status=closed', 'unexpected=all']:
            self.assertEqual(self.request('/api/tickets?' + query)[0], 400)
        self.assertEqual(self.request('/api/tickets')[1], [])

    def test_close_idempotency_filter_and_restart(self):
        ticket = self.request('/api/tickets', {'title': 'Finish me'})[1]
        ident = ticket['id']
        close = '/api/tickets/' + str(ident) + '/close'
        first = self.request(close, raw=b'')[1]
        self.assertEqual(first['status'], 'closed')
        self.assertIsNotNone(first['closed_at'])
        self.assertEqual(self.request(close, raw=b'')[1], first)
        self.assertEqual(self.request('/api/tickets?status=open')[1], [])
        self.assertEqual(self.request('/api/tickets?status=closed')[1], [first])
        self.stop()
        self.start()
        self.assertEqual(self.request('/api/tickets?status=all')[1], [first])
        for ident in ['99999', '99999999999999999999999999999', '0', '-1', 'abc']:
            self.assertEqual(self.request('/api/tickets/' + ident + '/close', raw=b'')[0], 404)

    def test_concurrent_creates_preserve_all_rows(self):
        def create(number):
            status, item = self.request('/api/tickets', {'title': 'Concurrent ' + str(number)})
            self.assertEqual(status, 201)
            return item['id']
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(create, range(16)))
        self.assertEqual(len(set(ids)), 16)
        rows = self.request('/api/tickets')[1]
        self.assertEqual(len(rows), 16)
        self.assertEqual([row['id'] for row in rows], sorted(ids, reverse=True))

    def test_loopback_boundary_and_unknown_routes(self):
        with self.assertRaises(ValueError):
            app.create_server('0.0.0.0', 0, self.data)
        self.assertEqual(self.request('/api/tickets', headers={'Host': 'foreign.example'})[0], 403)
        self.assertEqual(self.request('/api/tickets', {'title': 'not saved'}, headers={'Origin': 'https://foreign.example'})[0], 403)
        self.assertEqual(self.request('/api/tickets')[1], [])
        self.assertEqual(self.request('/api/tickets', method='DELETE')[0], 405)
        self.assertEqual(self.request('/no-such-path')[0], 404)
        self.assertEqual(self.request('/../app.py')[0], 404)

    def test_storage_failure_is_detected_without_reset(self):
        # Only this test's disposable synthetic database is modified.
        with sqlite3.connect(self.data) as db:
            db.execute('DROP TABLE tickets')
        status, error = self.request('/health')
        self.assertEqual(status, 500)
        self.assertIn('error', error)
        self.assertEqual(self.request('/api/tickets', {'title': 'not saved'})[0], 500)


class CliTests(unittest.TestCase):
    def test_cli_dynamic_port_persists_across_process_restart(self):
        (ROOT / 'evidence').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / 'evidence') as temp:
            data = str(Path(temp) / 'cli.sqlite')
            for iteration in range(2):
                proc = subprocess.Popen([sys.executable, '-B', str(ROOT / 'app.py'), '--data', data, '--port', '0'],
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                try:
                    url = proc.stdout.readline().strip()
                    self.assertRegex(url, r'^http://127\.0\.0\.1:\d+$')
                    if not iteration:
                        req = Request(url + '/api/tickets', data=b'{"title":"CLI persistence"}', headers={'Content-Type': 'application/json'})
                        with urlopen(req, timeout=5) as response:
                            self.assertEqual(response.status, 201)
                    else:
                        with urlopen(url + '/api/tickets', timeout=5) as response:
                            self.assertEqual(json.load(response)[0]['title'], 'CLI persistence')
                finally:
                    proc.send_signal(signal.SIGINT)
                    proc.wait(timeout=5)
                    proc.stdout.close()
                self.assertEqual(proc.returncode, 0)


if __name__ == '__main__':
    unittest.main()
