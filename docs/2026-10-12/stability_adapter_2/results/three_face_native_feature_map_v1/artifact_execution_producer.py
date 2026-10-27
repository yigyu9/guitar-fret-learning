import hashlib,json,os,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1';S=R/'stability_adapter_2/make_three_face_feature_artifacts.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'artifact_execution.json').exists();source_sha=sha(S);shutil.copyfile(S,P/'artifact_source.py');shutil.copyfile(__file__,P/'artifact_execution_producer.py')
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_feature_artifact')
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u',str(S),'--out',str(P)];t=time.monotonic()
with (P/'artifact_execution.log').open('w') as log,(P/'artifact_execution.err').open('w') as err:res=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=err)
metadata={'command':cmd,'exit_code':res.returncode,'wall_seconds':time.monotonic()-t,'producer_sha256_before':source_sha,'producer_sha256_after':sha(S),'log_sha256':sha(P/'artifact_execution.log'),'stderr_sha256':sha(P/'artifact_execution.err'),'native_calls':0}
if res.returncode==0:
 manifest=json.loads((P/'artifact_execution.log').read_text());manifest['outputs_sha256']={path:sha(path) for path in manifest['outputs']};(P/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');metadata['manifest_sha256']=sha(P/'artifact_manifest.json')
(P/'artifact_execution.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata,indent=2));print((P/'artifact_execution.err').read_text()[-1500:]);raise SystemExit(res.returncode)
