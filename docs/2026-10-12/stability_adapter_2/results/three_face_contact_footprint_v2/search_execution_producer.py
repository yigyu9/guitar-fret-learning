import os,json,hashlib,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2';S=R/'stability_adapter_2/search_contact_footprint_v2.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not P.exists();before=sha(S)
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.search_contact_footprint_v2'];log=Path('/tmp/contact_footprint_search_v2.log');t=time.monotonic()
with log.open('w') as out:res=subprocess.run(cmd,cwd=R,env=env,stdout=out,stderr=subprocess.STDOUT)
P.mkdir(exist_ok=True);shutil.copyfile(log,P/'search.log');shutil.copyfile(S,P/'search_source.py');shutil.copyfile(__file__,P/'search_execution_producer.py')
meta={'command':cmd,'exit_code':res.returncode,'wall_seconds':time.monotonic()-t,'source_sha256_before':before,'source_sha256_after':sha(S),'log_sha256':sha(P/'search.log'),'native_calls':0};(P/'search_execution.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2));print(log.read_text()[-2400:]);raise SystemExit(res.returncode)
