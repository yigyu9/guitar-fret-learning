import hashlib,json,os,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1';S=R/'stability_adapter_2/prepare_near_contact_diagnostic.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'proposal.json').exists();before={str(p):sha(p) for p in [S,R/'stability_adapter_2/run_near_contact_diagnostic.py',R/'stability_adapter_2/near_contact_initial_audit.py',R/'stability_adapter_2/source_patch_interval.py',R/'stability_adapter_2/NEAR_CONTACT_NATIVE_DIAGNOSTIC_PLAN.md']};shutil.copyfile(S,P/'preparation_source.py');shutil.copyfile(__file__,P/'preparation_execution_producer.py')
command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.prepare_near_contact_diagnostic'];env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib');start=time.monotonic()
with (P/'preparation.log').open('wb') as log:result=subprocess.run(command,cwd=str(R),env=env,stdout=log,stderr=subprocess.STDOUT)
metadata=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},log_sha256=sha(P/'preparation.log'),native_calls=0)
(P/'preparation_execution.json').write_text(json.dumps(metadata,indent=2)+'\n');print(json.dumps(metadata,indent=2));print((P/'preparation.log').read_text()[-2000:]);assert result.returncode==0
