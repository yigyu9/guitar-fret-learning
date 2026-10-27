import json,hashlib,subprocess,shutil,os,time
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2';S=R/'stability_adapter_2/analyze_contact_footprint_search_v2.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'analysis_v2.json').exists();before=sha(S);shutil.copyfile(S,P/'analysis_source_v2.py');shutil.copyfile(__file__,P/'analysis_execution_producer_v2.py');cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.analyze_contact_footprint_search_v2'];t=time.monotonic()
with (P/'analysis_v2.log').open('w') as log:r=subprocess.run(cmd,cwd=R,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),stdout=log,stderr=subprocess.STDOUT)
(P/'analysis_execution_v2.json').write_text(json.dumps({'command':cmd,'exit_code':r.returncode,'wall_seconds':time.monotonic()-t,'source_sha256_before':before,'source_sha256_after':sha(S),'log_sha256':sha(P/'analysis_v2.log'),'native_calls':0},indent=2)+'\n');print((P/'analysis_v2.log').read_text());raise SystemExit(r.returncode)
