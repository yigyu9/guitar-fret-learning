import json,hashlib,shutil,os,subprocess,time
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/palm_measured_geometry_v1';source=R/'stability_adapter_2/make_measured_palm_geometry_artifacts.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_torso_hold');shutil.copyfile(__file__,P/'artifact_execution_producer.py');before=sha(source);shutil.copyfile(source,P/'artifact_source.py');command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.make_measured_palm_geometry_artifacts'];start=time.monotonic()
with (P/'artifact.log').open('wb') as log:result=subprocess.run(command,cwd=str(R),env=env,stdout=log,stderr=subprocess.STDOUT)
metadata=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(source),log_sha256=sha(P/'artifact.log'),native_calls=0);(P/'artifact_execution.json').write_text(json.dumps(metadata,indent=2)+'\n');print(result.returncode,(P/'artifact.log').read_text()[-1000:]);assert result.returncode==0 and metadata['source_sha256_before']==metadata['source_sha256_after']
