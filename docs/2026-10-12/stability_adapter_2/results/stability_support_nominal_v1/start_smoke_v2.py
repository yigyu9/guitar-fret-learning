"""Start exactly one fresh retry using the preserved CUDA environment."""
import json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
if not (P/'review_preflight_v2.md').exists():raise RuntimeError('preflight review absent')
previous=json.loads((P/'supervisor_smoke_v1.json').read_text())
command=[previous['command'][0],'-u',str(P/'launch_run_v2.py'),'--out',str(P/'smoke_on_v2'),
 '--initialize-rms',previous['command'][previous['command'].index('--initialize-rms')+1],'--max-updates','1']
environment=os.environ.copy();environment.update(previous['environment'])
with (P/'supervisor_smoke_v2.log').open('x') as log:
 process=subprocess.Popen(command,cwd='/home/ajou/yigyu/3',env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
with (P/'supervisor_smoke_v2.json').open('x') as f:json.dump({'pid':process.pid,'command':command,'environment':previous['environment']},f,indent=2)
print('supervisor',process.pid)
