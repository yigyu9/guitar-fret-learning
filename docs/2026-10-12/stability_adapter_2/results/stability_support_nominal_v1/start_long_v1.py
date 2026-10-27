"""Resume the verified support-nominal checkpoint until the authorized cutoff."""
import json,os,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
verified=json.loads((P/'runtime_verification_v2.json').read_text())
if not verified['checks_passed']:raise RuntimeError('native smoke verification failed')
if json.loads((P/'smoke_on_v2.exit.json').read_text())['returncode']!=0:raise RuntimeError('smoke incomplete')
previous=json.loads((P/'supervisor_smoke_v2.json').read_text())
command=[previous['command'][0],'-u',str(P/'launch_run_v2.py'),'--out',str(P/'long_on_v1'),
 '--checkpoint',str(P/'smoke_on_v2/checkpoints/update_000001.pt')]
environment=os.environ.copy();environment.update(previous['environment'])
with (P/'supervisor_long_v1.log').open('x') as log:
 process=subprocess.Popen(command,cwd='/home/ajou/yigyu/3',env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
with (P/'supervisor_long_v1.json').open('x') as f:json.dump({'pid':process.pid,'command':command,'environment':previous['environment']},f,indent=2)
print('supervisor',process.pid)
