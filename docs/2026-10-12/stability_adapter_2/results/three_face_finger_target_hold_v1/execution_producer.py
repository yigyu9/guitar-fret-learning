import os,json,subprocess,time,hashlib
from pathlib import Path
root=Path('/home/ajou/yigyu/3');phase=root/'docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();proposal=json.loads((phase/'proposal.json').read_text());env=os.environ.copy();env.update(json.loads((phase/'environment.json').read_text())['env_overrides']);records=[]
assert all(proposal['checks'].values()) and all(sha(p)==h for p,h in proposal['input_sha256'].items());(phase/'execution_producer.py').write_bytes(Path(__file__).read_bytes());snap=phase/'source_pre_execution';snap.mkdir()
for name in ('run_seed2_support_warmstart.py','warmstart_targets.py','analyze_three_face_finger_hold.py'):
 p=root/'stability_adapter_2'/name;(snap/name).write_bytes(p.read_bytes());assert sha(p)==sha(snap/name)
for row in proposal['rows']:
 label=row['label'];cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.run_seed2_support_warmstart','--trial',row['trial_path'],'--out',str(phase/'native'/label),'--proposal',str(phase/'proposal.json')];start=time.monotonic();print('starting',label,flush=True)
 with (phase/(label+'.log')).open('w') as log:code=subprocess.call(cmd,cwd=str(root),env=env,stdout=log,stderr=subprocess.STDOUT)
 records.append({'label':label,'command':cmd,'exit_code':code,'elapsed_seconds':time.monotonic()-start,'runner_sha256':sha(root/'stability_adapter_2/run_seed2_support_warmstart.py'),'log_sha256':sha(phase/(label+'.log'))});(phase/'execution.json').write_text(json.dumps(records,indent=2)+'\n');print('finished',label,code,flush=True)
 if code:print((phase/(label+'.log')).read_text()[-4000:],flush=True);break
