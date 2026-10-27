import json,subprocess,time,hashlib,os
from pathlib import Path
root=Path('/home/ajou/yigyu/3');p=root/'docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1';source=root/'stability_adapter_2/make_three_face_same_target_artifacts.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before=sha(source);(p/'artifact_source.py').write_bytes(source.read_bytes());(p/'artifact_execution_producer.py').write_bytes(Path(__file__).read_bytes());cmd=['/home/ajou/miniconda3/envs/rl38/bin/python',str(source),'--out-dir',str(p/'artifacts')];env=os.environ.copy();env.update(json.loads((p/'environment.json').read_text())['env_overrides']);start=time.monotonic()
with (p/'artifact_execution.log').open('w') as log:code=subprocess.call(cmd,cwd=str(root),env=env,stdout=log,stderr=subprocess.STDOUT)
elapsed=time.monotonic()-start;assert sha(source)==before
r={'command':cmd,'returncode':code,'elapsed_seconds':elapsed,'producer_sha256':before,'log_sha256':sha(p/'artifact_execution.log'),'native_calls':0}
if (p/'artifacts/artifact_manifest.json').exists():r['manifest_sha256']=sha(p/'artifacts/artifact_manifest.json')
(p/'artifact_execution.json').write_text(json.dumps(r,indent=2)+'\n');print('artifact exit',code,flush=True);print((p/'artifact_execution.log').read_text()[-3000:],flush=True)
