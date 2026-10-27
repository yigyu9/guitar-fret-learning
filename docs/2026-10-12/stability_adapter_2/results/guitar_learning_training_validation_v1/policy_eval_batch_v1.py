"""Evaluate immutable before/after checkpoints with identical episode protocols."""
from pathlib import Path
import json,subprocess,sys,hashlib
base=Path(__file__).resolve().parent
root=base.parents[4]
train=base/'train_default_v1'
report=json.loads((train/'report.json').read_text())
assert report['completed'] and len(report['updates'])==4
rows=[]
for name,checkpoint in [('eval_before_v1',train/'initial.pt'),('eval_after_v1',train/'checkpoint_0003.pt')]:
 command=[sys.executable,'-m','guitar_learning.validate','--out',str(base/name),'--mode','policy','--stage','B','--seconds','3','--episodes','2','--seed','7','--checkpoint',str(checkpoint)]
 print('START '+name,flush=True)
 with (base/(name+'_console.txt')).open('x') as stream:result=subprocess.run(command,cwd=root,stdout=stream,stderr=subprocess.STDOUT)
 row=dict(name=name,command=command,exit_code=result.returncode,checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest())
 rows.append(row)
 with (base/(name+'_driver.json')).open('x') as stream:json.dump(row,stream,indent=2)
 print(json.dumps(row),flush=True)
 if result.returncode:raise SystemExit(result.returncode)
with (base/'policy_eval_batch_results.json').open('x') as stream:json.dump(rows,stream,indent=2)
