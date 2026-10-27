import hashlib,json,os,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1';S=R/'stability_adapter_2/make_near_rear_artifacts.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'artifact_execution.json').exists();before=sha(S);shutil.copyfile(S,P/'artifact_source.py');shutil.copyfile(__file__,P/'artifact_execution_producer.py')
command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.make_near_rear_artifacts'];env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_near_rear_artifacts');start=time.monotonic()
with (P/'artifact_execution.log').open('wb') as out,(P/'artifact_execution.err').open('wb') as err:result=subprocess.run(command,cwd=str(R),env=env,stdout=out,stderr=err)
metadata=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(S),log_sha256=sha(P/'artifact_execution.log'),stderr_sha256=sha(P/'artifact_execution.err'),native_calls=0,unconsumed_producer_preparation='Luna draft; root fixed transitive closure/self binding, English plotting fonts, external legends/detail view and near-phase output path before first execution')
(P/'artifact_execution.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata,indent=2));print((P/'artifact_execution.log').read_text()[-1500:]);print((P/'artifact_execution.err').read_text()[-1500:]);assert result.returncode==0 and before==sha(S)
