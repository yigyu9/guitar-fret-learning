import hashlib,json,os,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_front_finger_initial_v1';S=R/'stability_adapter_2/search_front_finger_initial.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'attempt.json').exists();pre=json.loads((P/'root_preflight.json').read_text());assert all(pre['checks'].values()) and all(sha(p)==h for p,h in pre['input_sha256'].items());before={str(p):sha(p) for p in [S,P/'root_preflight.json',R/'stability_adapter_2/THREE_FACE_FRONT_FINGER_INITIAL_PLAN.md',R/'stability_adapter_2/THREE_FACE_FRONT_FINGER_EXECUTION.md']};shutil.copyfile(S,P/'search_source.py');shutil.copyfile(__file__,P/'search_execution_producer.py')
command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.search_front_finger_initial'];env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib');start=time.monotonic()
with (P/'search.log').open('wb') as log:result=subprocess.run(command,cwd=str(R),env=env,stdout=log,stderr=subprocess.STDOUT)
metadata=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},log_sha256=sha(P/'search.log'),native_calls=0,independent_pre_review=False)
(P/'search_execution.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata,indent=2));print((P/'search.log').read_text()[-2500:]);assert result.returncode==0
