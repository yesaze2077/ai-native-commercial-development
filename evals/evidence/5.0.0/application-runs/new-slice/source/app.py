"""Single-operator synthetic issue queue. Standard library; loopback only."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
import sys
from urllib.parse import parse_qs, urlsplit

WEB = Path(__file__).parent / 'web'
MAX_BODY = 8192


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def connect(data_path):
    connection = sqlite3.connect(str(data_path), timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


class QueueServer(ThreadingHTTPServer):
    daemon_threads = True

    def get_request(self):
        sock, address = super().get_request()
        sock.settimeout(5)
        return sock, address


class Handler(BaseHTTPRequestHandler):
    server_version = 'LocalQueue/1'

    def log_request(self, code='-', size='-'):
        # Bodies and titles are deliberately absent from operational logs.
        print(json.dumps({'method': self.command, 'path': urlsplit(self.path).path,
                          'status': code}), file=sys.stderr, flush=True)

    def respond(self, status, payload, content_type='application/json; charset=utf-8'):
        data = json.dumps(payload, ensure_ascii=False).encode() if content_type.startswith('application/json') else payload
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(data)

    def error(self, status, message):
        self.respond(status, {'error': message})

    def local_request(self):
        port = self.server.server_address[1]
        allowed_hosts = {'127.0.0.1:' + str(port), 'localhost:' + str(port)}
        if self.headers.get('Host') not in allowed_hosts:
            self.error(403, 'Only the local queue host is accepted.')
            return False
        origin = self.headers.get('Origin')
        if origin and origin not in {'http://' + host for host in allowed_hosts}:
            self.error(403, 'Cross-origin requests are not accepted.')
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        route = urlsplit(self.path)
        try:
            if route.path == '/health':
                with closing(connect(self.server.data_path)) as db:
                    db.execute('SELECT count(*) FROM tickets').fetchone()
                self.respond(200, {'status': 'ok'})
            elif route.path == '/api/tickets':
                query = parse_qs(route.query, keep_blank_values=True)
                values = query.get('status', ['all'])
                if set(query) - {'status'} or len(values) != 1 or values[0] not in {'all', 'open', 'closed'}:
                    self.error(400, 'Status must be all, open or closed.')
                    return
                with closing(connect(self.server.data_path)) as db:
                    if values[0] == 'all':
                        rows = db.execute('SELECT * FROM tickets ORDER BY id DESC').fetchall()
                    else:
                        rows = db.execute('SELECT * FROM tickets WHERE status = ? ORDER BY id DESC', (values[0],)).fetchall()
                self.respond(200, [dict(row) for row in rows])
            elif route.path in {'/', '/styles.css', '/app.js'}:
                name, mime = {'/': ('index.html', 'text/html; charset=utf-8'),
                              '/styles.css': ('styles.css', 'text/css; charset=utf-8'),
                              '/app.js': ('app.js', 'text/javascript; charset=utf-8')}[route.path]
                self.respond(200, (WEB / name).read_bytes(), mime)
            elif route.path == '/favicon.ico':
                self.respond(204, b'', 'image/x-icon')
            else:
                self.error(404, 'No such resource.')
        except (sqlite3.Error, OSError):
            self.error(500, 'Local storage is unavailable. Please retry or check the data file.')

    def read_body(self, required):
        length = self.headers.get('Content-Length', '0')
        if not length.isascii() or not length.isdigit():
            self.error(400, 'Invalid content length.')
            return None
        if int(length) > MAX_BODY:
            self.error(413, 'Request body is too large.')
            return None
        if not int(length) and not required:
            return {}
        if self.headers.get_content_type() != 'application/json':
            self.error(415, 'Use application/json.')
            return None
        try:
            value = json.loads(self.rfile.read(int(length)).decode('utf-8'))
            if not isinstance(value, dict):
                raise ValueError()
            return value
        except (ValueError, UnicodeDecodeError):
            self.error(400, 'Body must be a valid JSON object.')
            return None

    def do_POST(self):
        if not self.local_request():
            return
        route = urlsplit(self.path)
        match = re.fullmatch(r'/api/tickets/([1-9][0-9]*)/close', route.path)
        if route.query or (route.path != '/api/tickets' and not match):
            self.error(404, 'No such action.')
            return
        payload = self.read_body(required=not match)
        if payload is None:
            return
        try:
            if match:
                # Constrain IDs to SQLite's signed integer range before binding.
                raw_id = match.group(1)
                if len(raw_id) > 19 or int(raw_id) > 9223372036854775807:
                    self.error(404, 'Request not found.')
                    return
                ident = int(raw_id)
                with closing(connect(self.server.data_path)) as db:
                    with db:
                        db.execute("UPDATE tickets SET status = 'closed', closed_at = ? WHERE id = ? AND status = 'open'", (timestamp(), ident))
                        row = db.execute('SELECT * FROM tickets WHERE id = ?', (ident,)).fetchone()
                if row is None:
                    self.error(404, 'Request not found.')
                else:
                    self.respond(200, dict(row))
            else:
                title = payload.get('title')
                if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
                    self.error(400, 'Title must contain 1–120 nonblank characters.')
                    return
                title = title.strip()
                # Lone surrogates cannot be stored as valid UTF-8 text.
                try:
                    title.encode('utf-8')
                except UnicodeEncodeError:
                    self.error(400, 'Title must contain valid Unicode text.')
                    return
                with closing(connect(self.server.data_path)) as db:
                    with db:
                        cursor = db.execute("INSERT INTO tickets (title, status, created_at) VALUES (?, 'open', ?)", (title, timestamp()))
                        row = db.execute('SELECT * FROM tickets WHERE id = ?', (cursor.lastrowid,)).fetchone()
                self.respond(201, dict(row))
        except sqlite3.Error:
            self.error(500, 'Local storage is unavailable. Please retry or check the data file.')

    def method_not_allowed(self):
        if self.local_request():
            self.error(405, 'Method is not supported.')

    do_PUT = method_not_allowed
    do_PATCH = method_not_allowed
    do_DELETE = method_not_allowed
    do_OPTIONS = method_not_allowed


def create_server(host, port, data_path):
    """Return a stoppable server. Call shutdown(), then server_close()."""
    if host not in {'127.0.0.1', 'localhost'}:
        raise ValueError('This synthetic tool only accepts IPv4 loopback hosts.')
    path = Path(data_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Title length is enforced in Python: SQLite length(TEXT) truncates at NUL.
    with closing(connect(path)) as db:
        with db:
            db.execute("""CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('open', 'closed')),
                created_at TEXT NOT NULL,
                closed_at TEXT
            )""")
    server = QueueServer((host, port), Handler)
    server.data_path = path
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('queue.sqlite'))
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('--port must be between 0 and 65535')
    try:
        server = create_server('127.0.0.1', args.port, args.data)
    except (OSError, sqlite3.Error) as error:
        parser.exit(1, 'Cannot start local queue: ' + str(error) + '\n')
    print('http://127.0.0.1:' + str(server.server_address[1]), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
