from pathlib import Path
import subprocess,sys,json,datetime
repo=Path('/Users/yuyuan/Documents/Codex/2026-07-23/an-z/work/lifecycle-handoffs-20261113/developer-exercise/repo')
out=Path('/Users/yuyuan/Documents/Codex/2026-07-23/an-z/work/lifecycle-handoffs-20261113/ai-native-commercial-development/evals/evidence/9.0.0/developer-exercise/phase-1')
argv=sys.argv[1:]
p=subprocess.run(argv,cwd=repo,capture_output=True,text=True)
log=out/'commands.jsonl'
with log.open('a') as f:f.write(json.dumps({'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cwd':str(repo),'argv':argv,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},ensure_ascii=False)+'\n')
print(p.stdout,end='');print(p.stderr,end='',file=sys.stderr)
sys.exit(p.returncode)
