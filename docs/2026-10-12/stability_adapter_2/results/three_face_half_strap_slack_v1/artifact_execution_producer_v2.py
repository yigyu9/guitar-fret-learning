import os,json,hashlib,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1';S=R/'stability_adapter_2/make_three_face_half_slack_artifacts_v2.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=sha(S);assert before=='f21ac1201e8b9300f4e5fd5ecb9f4fabafd01823d4310a98f4e039ec02a18a40'
assert not (P/'artifact_execution_v2.json').exists()
shutil.copyfile(S,P/'artifact_source_v2.py');shutil.copyfile(__file__,P/'artifact_execution_producer_v2.py')
env=os.environ.copy();env.update(json.loads((P/'environment.json').read_text())['env_overrides'])
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.make_three_face_half_slack_artifacts_v2']
t=time.monotonic()
with (P/'artifact_execution_v2.log').open('w') as f:r=subprocess.run(cmd,cwd=str(R),env=env,stdout=f,stderr=subprocess.STDOUT)
d={'command':cmd,'exit_code':r.returncode,'elapsed_seconds':time.monotonic()-t,'producer_sha256_before':before,'producer_sha256_after':sha(S),'log_sha256':sha(P/'artifact_execution_v2.log'),'native_calls':0,'physics_steps':0}
if (P/'artifacts_v2/artifact_manifest.json').exists():d['manifest_sha256']=sha(P/'artifacts_v2/artifact_manifest.json')
(P/'artifact_execution_v2.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2));assert r.returncode==0 and d['producer_sha256_after']==before
