import hashlib,json,os,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/strap_video_v1';source=R/'stability_adapter_2/verify_strap_video.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((P/'native/report.json').read_text())['completed'];assert not (P/'verification.json').exists();shutil.copyfile(source,P/'verification_source.py');shutil.copyfile(__file__,P/'verification_execution_producer.py');before=sha(source)
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib');command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.verify_strap_video'];start=time.monotonic()
with (P/'verification_execution.log').open('wb') as log:result=subprocess.run(command,cwd=str(R),env=env,stdout=log,stderr=subprocess.STDOUT)
(P/'verification_execution.json').write_text(json.dumps(dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(source),log_sha256=sha(P/'verification_execution.log'),native_calls=0),indent=2)+'\n');print(result.returncode,(P/'verification_execution.log').read_text()[-4000:]);assert result.returncode==0 and before==sha(source)
