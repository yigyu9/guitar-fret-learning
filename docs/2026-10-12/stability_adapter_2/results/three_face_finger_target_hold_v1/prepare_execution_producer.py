import os,json,subprocess,time,hashlib
from pathlib import Path
root=Path('/home/ajou/yigyu/3');old=root/'docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1';phase=old.parent/'three_face_finger_target_hold_v1';config=json.loads((old/'environment.json').read_text());env=os.environ.copy();env.update(config['env_overrides']);source=root/'stability_adapter_2/prepare_three_face_finger_hold.py';original=source.read_bytes();before=hashlib.sha256(original).hexdigest();cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.prepare_three_face_finger_hold'];start=time.monotonic()
with Path('/tmp/finger_hold_prepare.log').open('w') as log:code=subprocess.call(cmd,cwd=str(root),env=env,stdout=log,stderr=subprocess.STDOUT)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
if phase.exists():
 (phase/'prepare_source.py').write_bytes(original);(phase/'prepare_execution_producer.py').write_bytes(Path(__file__).read_bytes());(phase/'prepare.log').write_bytes(Path('/tmp/finger_hold_prepare.log').read_bytes());(phase/'environment.json').write_text(json.dumps(config,indent=2)+'\n');(phase/'prepare_execution.json').write_text(json.dumps({'command':cmd,'exit_code':code,'elapsed_seconds':time.monotonic()-start,'source_sha256':before,'native_initializations':0,'physics_steps':0},indent=2)+'\n')
print('prepare exit',code,flush=True);print(Path('/tmp/finger_hold_prepare.log').read_text()[-5000:],flush=True)
