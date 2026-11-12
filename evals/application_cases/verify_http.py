"""Execute the accepted synthetic app contract via real HTTP and SQLite/file persistence."""
import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

APP = Path(sys.argv.pop(1)).resolve() if len(sys.argv) > 1 else Path('app.py').resolve()
spec = importlib.util.spec_from_file_location('fixture_app', APP)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Contract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'test.sqlite')
        self.start()
    def start(self):
        self.server = module.create_server('127.0.0.1', 0, self.path)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_address[1])
    def stop(self):
        self.server.shutdown(); self.thread.join(); self.server.server_close()
    def tearDown(self):
        self.stop(); self.temp.cleanup()
    def request(self, path, value=None, post=False):
        data = json.dumps(value).encode() if value is not None else (b'' if post else None)
        req = Request(self.url + path, data=data, headers={'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=3) as response:return response.status,json.load(response)
        except HTTPError as error:return error.code,json.load(error)
    def test_create_and_persist_across_restart(self):
        status, result = self.request('/api/tickets', {'title':'Synthetic persistence request'})
        self.assertEqual(status,201);self.assertEqual(result['status'],'open')
        self.stop();self.start()
        self.assertEqual(self.request('/api/tickets')[1][0]['title'],'Synthetic persistence request')
    def test_close_and_filter(self):
        ident=self.request('/api/tickets', {'title':'Close me'})[1]['id']
        self.request('/api/tickets/'+str(ident)+'/close',post=True)
        self.request('/api/tickets', {'title':'Keep open'})
        self.assertEqual([x['title'] for x in self.request('/api/tickets?status=open')[1]],['Keep open'])
        self.assertEqual([x['title'] for x in self.request('/api/tickets?status=closed')[1]],['Close me'])
    def test_invalid_input_and_filter(self):
        self.assertEqual(self.request('/api/tickets',{'title':'   '})[0],400)
        self.assertEqual(self.request('/api/tickets?status=unknown')[0],400)
    def test_health_and_empty(self):
        self.assertEqual(self.request('/health')[0],200)
        self.assertEqual(self.request('/api/tickets')[1],[])

if __name__=='__main__':unittest.main()
