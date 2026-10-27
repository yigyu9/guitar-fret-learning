import hashlib,json,shutil,subprocess,time,os
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1';source=R/'stability_adapter_2/make_palm_priority_artifacts.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (P/'artifacts').exists();shutil.copyfile(source,P/'artifact_source.py');shutil.copyfile(__file__,P/'artifact_execution_producer.py');before=sha(source);command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.make_palm_priority_artifacts'];env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib');start=time.monotonic()
with (P/'artifact.log').open('wb') as f:r=subprocess.run(command,cwd=str(R),env=env,stdout=f,stderr=subprocess.STDOUT)
(P/'artifact_execution.json').write_text(json.dumps(dict(command=command,exit_code=r.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(source),log_sha256=sha(P/'artifact.log'),native_calls=0),indent=2)+'\n');print(r.returncode,(P/'artifact.log').read_text()[-2000:]);assert r.returncode==0 and before==sha(source)
