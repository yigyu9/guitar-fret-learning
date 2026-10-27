import hashlib,json,os,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2';S=R/'stability_adapter_2/make_rear_facet_artifacts.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'artifact_execution.json').exists();before=sha(S);shutil.copyfile(S,P/'artifact_source.py');shutil.copyfile(__file__,P/'artifact_execution_producer.py');assert sha(P/'artifact_source.py')==before
command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u',str(S)];env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite');start=time.monotonic()
with (P/'artifact_execution.log').open('wb') as log,(P/'artifact_execution.err').open('wb') as err:result=subprocess.run(command,cwd=str(R),env=env,stdout=log,stderr=err)
meta={'command':command,'exit_code':result.returncode,'wall_seconds':time.monotonic()-start,'source_sha256_before':before,'source_sha256_after':sha(S),'log_sha256':sha(P/'artifact_execution.log'),'stderr_sha256':sha(P/'artifact_execution.err'),'native_calls':0}
if (P/'artifacts/artifact_manifest.json').exists():meta['manifest_sha256']=sha(P/'artifacts/artifact_manifest.json')
(P/'artifact_execution.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2));assert result.returncode==0,(P/'artifact_execution.err').read_text()[-2000:]
