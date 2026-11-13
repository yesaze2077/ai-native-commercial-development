"""Regression coverage for the accepted local status filter contract."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

from app import create_server


class StatusFilters(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data = str(Path(self.temp.name) / 'requests.sqlite')
        self.start()

    def start(self):
        self.server = create_server('127.0.0.1', 0, self.data)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_address[1])

    def stop(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()

    def tearDown(self):
        self.stop()
        self.temp.cleanup()

    def request(self, path, value=None, post=False):
        payload = json.dumps(value).encode() if value is not None else (b'' if post else None)
        with urlopen(Request(self.url + path, data=payload,
                             headers={'Content-Type': 'application/json'}), timeout=3) as response:
            return json.load(response)

    def test_all_and_filtered_statuses_survive_restart(self):
        closed = self.request('/api/tickets', {'title': 'First closed request'})
        self.request('/api/tickets/' + str(closed['id']) + '/close', post=True)
        opened = self.request('/api/tickets', {'title': 'Second open request'})
        self.stop()
        self.start()

        rows = self.request('/api/tickets?status=all')
        self.assertEqual([(row['id'], row['status']) for row in rows],
                         [(closed['id'], 'closed'), (opened['id'], 'open')])
        self.assertEqual(self.request('/api/tickets'), rows)
        self.assertEqual(self.request('/api/tickets?status=open'), [rows[1]])
        self.assertEqual(self.request('/api/tickets?status=closed'), [rows[0]])

    def test_filter_with_no_matching_rows_is_empty(self):
        opened = self.request('/api/tickets', {'title': 'Only request'})
        self.assertEqual(self.request('/api/tickets?status=closed'), [])
        self.request('/api/tickets/' + str(opened['id']) + '/close', post=True)
        self.assertEqual(self.request('/api/tickets?status=open'), [])


if __name__ == '__main__':
    unittest.main()
