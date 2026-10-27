import os,json,subprocess,time,hashlib
from pathlib import Path
root=Path('/home/ajou/yigyu/3');phase=root/'docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1';env=os.environ.copy();env.update(json.loads((phase/'environment.json').read_text())['env_overrides']);p=root/'stability_adapter_2/analyze_three_face_finger_hold.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=p.read_bytes();before=sha(p);(phase/'analysis_source.py').write_bytes(source);(phase/'analysis_execution_producer.py').write_bytes(Path(__file__).read_bytes());cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.analyze_three_face_finger_hold'];start=time.monotonic()
with (phase/'analysis.log').open('w') as f:code=subprocess.call(cmd,cwd=str(root),env=env,stdout=f,stderr=subprocess.STDOUT)
assert sha(p)==before
(phase/'analysis_execution.json').write_text(json.dumps({'command':cmd,'exit_code':code,'elapsed_seconds':time.monotonic()-start,'producer_sha256':before,'log_sha256':sha(phase/'analysis.log'),'native_initializations':0,'physics_steps':0},indent=2)+'\n');print('analysis exit',code,flush=True);print((phase/'analysis.log').read_text()[-8000:],flush=True)
