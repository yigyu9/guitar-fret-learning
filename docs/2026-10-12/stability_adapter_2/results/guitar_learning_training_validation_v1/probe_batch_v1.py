"""Run the six prespecified, independent probes in fresh child processes."""
from pathlib import Path
import json,subprocess,sys,hashlib
base=Path(__file__).resolve().parent
root=base.parents[4]
rows=[]
for stage,mode in [('D','zero'),('D','right'),('D','left_arm'),('D','fingers'),('D','all'),('C','zero')]:
 name='probe_'+stage+'_'+mode+'_v1'
 command=[sys.executable,'-m','guitar_learning.validate','--out',str(base/name),'--mode',mode,'--stage',stage,'--seconds','5','--episodes','1','--seed','7']
 print('START '+name,flush=True)
 with (base/(name+'_console.txt')).open('x') as stream:
  result=subprocess.run(command,cwd=root,stdout=stream,stderr=subprocess.STDOUT)
 row=dict(name=name,command=command,exit_code=result.returncode)
 rows.append(row)
 with (base/(name+'_driver.json')).open('x') as stream:json.dump(row,stream,indent=2)
 print(json.dumps(row),flush=True)
 if result.returncode:raise SystemExit(result.returncode)
with (base/'probe_batch_results.json').open('x') as stream:json.dump(rows,stream,indent=2)
