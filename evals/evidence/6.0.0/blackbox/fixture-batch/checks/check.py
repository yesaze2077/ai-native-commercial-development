import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

p=argparse.ArgumentParser()
p.add_argument('check')
p.add_argument('--audit-log', required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((root/name).read_text(encoding='utf-8'))
runtime=read('runtime/fixture.json')
assert runtime == {'fixture':'synthetic-v1','encoding':'utf-8'}

def shared():
    spec=read('src/shared/schema.json')
    assert spec['version']==1
    assert spec['required']==['id','name']
    return spec

def ui():
    spec=shared()
    form=read('src/ui/form.json')
    assert set(spec['required']).issubset(form['fields'])
    assert form['label'] in ('Save','Save changes')
    return form

def api():
    spec=shared()
    route=read('src/api/route.json')
    assert set(spec['required']).issubset(route['accepts'])
    assert route['method']=='POST'
    return route

def docs():
    topic=read('docs/topic.json')
    assert topic['title'].strip()
    assert 'Usage' in topic['sections']
    return topic

def journey():
    form, route=ui(), api()
    payload={'id':'item-001','name':'Synthetic value'}
    encoded=json.dumps({k:payload[k] for k in form['fields'] if k in payload})
    accepted={k:v for k,v in json.loads(encoded).items() if k in route['accepts']}
    assert accepted==payload
    with TemporaryDirectory(prefix='incremental-blackbox-') as td:
        record=Path(td)/'saved.json'
        record.write_text(json.dumps(accepted),encoding='utf-8')
        assert json.loads(record.read_text(encoding='utf-8'))==payload

actions={'shared-quick':shared,'ui-quick':ui,'api-quick':api,'docs-quick':docs,'journey-integration':journey,'release-smoke':lambda:(journey(),docs())}
actions[a.check]()
# This external append is observational only; it is never a test input.
with Path(a.audit_log).open('a',encoding='utf-8') as stream:
    stream.write(a.check+'\n')
print(a.check+': passed real synthetic-source assertions')
