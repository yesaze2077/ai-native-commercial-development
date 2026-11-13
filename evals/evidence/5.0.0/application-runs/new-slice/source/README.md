# Local issue queue

Synthetic single-operator exercise. Python standard library only; no installation.

```bash
python3 -B app.py --data queue.sqlite --port 0
```

Open the printed `http://127.0.0.1:<port>` URL. Add a short title, filter all/open/closed, then close a request. Data persists in the SQLite path; use the same path on restart. Ctrl+C stops the server. Keep data synthetic; do not expose the service to LAN or internet.

```bash
python3 -B -m unittest -v test_app.py
node --check web/app.js
```

Integration entry point: `app.create_server('127.0.0.1', 0, data_path)` returns a `ThreadingHTTPServer` (a `HTTPServer` subclass). Start `serve_forever()` in a thread; call `shutdown()`, join that thread, then `server_close()`.

Accepted input, design/architecture and requirement/check mapping: [DELIVERY.md](DELIVERY.md). Runtime evidence is local and ignored in `evidence/`; it is not shipped as application data. No independent review, production release, real-user acceptance, market or business validation has occurred.
