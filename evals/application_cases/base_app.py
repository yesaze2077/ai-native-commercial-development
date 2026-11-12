"""Synthetic local fixture, never a production application."""
import argparse
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def create_server(host, port, data_path, fail_health=False):
    with sqlite3.connect(data_path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS tickets(id INTEGER PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL)')

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, value, content_type='application/json'):
            content = value.encode() if isinstance(value, str) else json.dumps(value).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == '/health':
                self.send(503 if fail_health else 200, {'status': 'unhealthy' if fail_health else 'ok'})
            elif parsed.path == '/':
                self.send(200, Path(__file__).with_name('index.html').read_text(), 'text/html; charset=utf-8')
            elif parsed.path == '/api/tickets':
                requested = parse_qs(parsed.query).get('status', ['all'])[0]
                if requested not in ('all', 'open', 'closed'):
                    return self.send(400, {'error': 'Invalid status'})
                with sqlite3.connect(data_path) as db:
                    # Existing-project fixture intentionally has an incomplete filter.
                    rows = db.execute('SELECT id,title,status FROM tickets ORDER BY id').fetchall()
                self.send(200, [{'id': r[0], 'title': r[1], 'status': r[2]} for r in rows])
            else:
                self.send(404, {'error': 'Not found'})

        def do_POST(self):
            if self.path == '/api/tickets':
                try:
                    length = int(self.headers.get('Content-Length', 0))
                    if not 0 < length <= 4096:
                        raise ValueError()
                    value = json.loads(self.rfile.read(length))
                    title = value.get('title')
                    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
                        raise ValueError()
                except (ValueError, TypeError, AttributeError):
                    return self.send(400, {'error': 'Title must contain 1 to 120 characters'})
                with sqlite3.connect(data_path) as db:
                    cursor = db.execute('INSERT INTO tickets(title,status) VALUES (?,?)', (title.strip(), 'open'))
                    ident = cursor.lastrowid
                self.send(201, {'id': ident, 'title': title.strip(), 'status': 'open'})
            elif self.path.startswith('/api/tickets/') and self.path.endswith('/close'):
                try:
                    ident = int(self.path.split('/')[3])
                except ValueError:
                    return self.send(400, {'error': 'Invalid ID'})
                with sqlite3.connect(data_path) as db:
                    count = db.execute('UPDATE tickets SET status=? WHERE id=?', ('closed', ident)).rowcount
                self.send(200 if count else 404, {'updated': bool(count)})
            else:
                self.send(404, {'error': 'Not found'})
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--data', required=True)
    parser.add_argument('--fail-health', action='store_true')
    args = parser.parse_args()
    server = create_server('127.0.0.1', args.port, args.data, args.fail_health)
    print('http://127.0.0.1:' + str(server.server_address[1]), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
