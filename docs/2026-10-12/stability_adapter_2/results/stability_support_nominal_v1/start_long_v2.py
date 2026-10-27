"""Resume a completed saved checkpoint after a preserved native process crash."""
import hashlib,json,os,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
old=json.loads((P/'long_on_v1.exit.json').read_text())
if old['returncode']!=-11:raise ValueError('unexpected prior exit')
checkpoint=P/'long_on_v1/checkpoints/update_000157.pt'
evaluation=P/'long_on_v1/evaluations/update_000157'
report=json.loads((evaluation/'report.json').read_text())
meta=json.loads((evaluation/'evaluation.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
if not report['completed'] or not report['inputs_unchanged'] or sha(checkpoint)!=meta['checkpoint_sha256']:raise ValueError('saved evaluation/checkpoint mismatch')
closure=json.loads((P/'long_on_v1/attempt.json').read_text())['input_sha256']
if not all(sha(p)==h for p,h in closure.items()):raise ValueError('historical inputs changed')
previous=json.loads((P/'supervisor_long_v1.json').read_text())
command=[previous['command'][0],'-u',str(P/'launch_run_v2.py'),'--out',str(P/'long_on_v2'),'--checkpoint',str(checkpoint)]
environment=os.environ.copy();environment.update(previous['environment'])
with (P/'supervisor_long_v2.log').open('x') as log:
 process=subprocess.Popen(command,cwd='/home/ajou/yigyu/3',env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
with (P/'supervisor_long_v2.json').open('x') as f:json.dump({'pid':process.pid,'command':command,'environment':previous['environment'],'source_checkpoint_sha256':sha(checkpoint),'prior_exit':old['returncode'],'prior_last_logged_update':192,'resume_update':157,'scope':'model/Adam/RNG resume into fresh physical scene; unsaved updates158..192 not recovered'},f,indent=2)
print('supervisor',process.pid)
