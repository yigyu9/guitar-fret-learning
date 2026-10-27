import hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path('/home/ajou/yigyu/3');P=ROOT/'docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=ROOT/'stability_adapter_2/make_three_face_support_loss_artifacts.py';before=sha(src);assert not (P/'artifact_execution.json').exists();(P/'artifact_source.py').write_bytes(src.read_bytes());assert sha(P/'artifact_source.py')==before;(P/'artifact_execution_producer.py').write_bytes(Path(__file__).read_bytes())
env=os.environ.copy();env.update(json.loads((P/'environment.json').read_text())['env_overrides']);cmd=['/home/ajou/miniconda3/envs/rl38/bin/python',str(src),'--out-dir',str(P/'artifacts')];start=time.monotonic()
with (P/'artifact_execution.log').open('w') as log:code=subprocess.call(cmd,cwd=str(ROOT),env=env,stdout=log,stderr=subprocess.STDOUT)
meta={'command':cmd,'exit_code':code,'elapsed_seconds':time.monotonic()-start,'producer_sha256_before':before,'producer_sha256_after':sha(src),'log_sha256':sha(P/'artifact_execution.log'),'native_calls':0}
if (P/'artifacts/artifact_manifest.json').exists():meta['manifest_sha256']=sha(P/'artifacts/artifact_manifest.json')
(P/'artifact_execution.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2),flush=True);print((P/'artifact_execution.log').read_text()[-3000:],flush=True);raise SystemExit(code)
