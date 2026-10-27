import json,hashlib,subprocess,shutil,os,time
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2';S=R/'stability_adapter_2/make_contact_footprint_artifacts_v2.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'artifact_execution_v2.json').exists();before=sha(S);shutil.copyfile(S,P/'artifact_source_v2.py');shutil.copyfile(__file__,P/'artifact_execution_producer_v2.py');cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u',str(S),'--out-dir',str(P/'artifacts_v2')];t=time.monotonic()
with (P/'artifact_execution_v2.log').open('w') as log,(P/'artifact_execution_v2.err').open('w') as err:r=subprocess.run(cmd,cwd=R,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_footprint_plot'),stdout=log,stderr=err)
e={'command':cmd,'exit_code':r.returncode,'wall_seconds':time.monotonic()-t,'source_sha256_before':before,'source_sha256_after':sha(S),'log_sha256':sha(P/'artifact_execution_v2.log'),'stderr_sha256':sha(P/'artifact_execution_v2.err'),'native_calls':0}
if r.returncode==0:
 m=json.loads((P/'artifact_execution_v2.log').read_text());(P/'artifact_manifest_v2.json').write_text(json.dumps(m,indent=2)+'\n');e['manifest_sha256']=sha(P/'artifact_manifest_v2.json')
(P/'artifact_execution_v2.json').write_text(json.dumps(e,indent=2)+'\n');print(json.dumps(e,indent=2));print((P/'artifact_execution_v2.err').read_text()[-500:]);raise SystemExit(r.returncode)
