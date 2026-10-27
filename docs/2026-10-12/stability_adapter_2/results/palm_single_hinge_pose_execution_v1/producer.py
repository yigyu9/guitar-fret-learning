import os,time,json,hashlib,subprocess,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');B=R/'docs/2026-10-12/stability_adapter_2/results';source=R/'stability_adapter_2/check_palm_single_hinges.py';out=B/'palm_single_hinge_pose_execution_v1';out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
shutil.copyfile(source,out/'source.py');shutil.copyfile(__file__,out/'producer.py');before=sha(source);command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.check_palm_single_hinges'];env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_runtime_fk',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib');start=time.monotonic()
with (out/'execution.log').open('wb') as log:r=subprocess.run(command,cwd=str(R),env=env,stdout=log,stderr=subprocess.STDOUT)
e=dict(command=command,exit_code=r.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(source),log_sha256=sha(out/'execution.log'),native_calls=0);(out/'execution.json').write_text(json.dumps(e,indent=2)+'\n');print(r.returncode,(out/'execution.log').read_text()[-2800:]);assert r.returncode==0 and e['source_sha256_before']==e['source_sha256_after']
