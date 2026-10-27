import hashlib,json,os,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v1';S=R/'stability_adapter_2/search_rear_thumb_facet.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'search_execution.json').exists() and not (P/'attempt.json').exists()
review=P/'source_pre_review.md';assert review.exists()
source_sha=sha(S);before={str(p):sha(p) for p in [S,review,R/'stability_adapter_2/THREE_FACE_REAR_FACET_PLAN.md',R/'stability_adapter_2/THREE_FACE_REAR_FACET_EXECUTION.md']}
shutil.copyfile(S,P/'search_source.py');shutil.copyfile(__file__,P/'search_execution_producer.py');assert sha(P/'search_source.py')==source_sha
command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.search_rear_thumb_facet']
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
start=time.monotonic()
with (P/'search.log').open('wb') as log: result=subprocess.run(command,cwd=str(R),env=env,stdout=log,stderr=subprocess.STDOUT)
metadata=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=source_sha,source_sha256_after=sha(S),log_sha256=sha(P/'search.log'),input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},native_calls=0)
(P/'search_execution.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata,indent=2));print((P/'search.log').read_text()[-4000:]);assert result.returncode==0
