import json,hashlib,shutil,os,subprocess,time
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1';A=R/'stability_adapter_2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert json.loads((P/'native_execution.json').read_text())['exit_code']==0
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_torso_hold',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib');shutil.copyfile(__file__,P/'post_execution_producer.py')
for label,module in [('analysis','analyze_torso_hold_diagnostic'),('feature','analyze_torso_hold_features'),('early','audit_torso_hold_early_motion')]:
 source=A/(module+'.py');before=sha(source);shutil.copyfile(source,P/(label+'_source.py'));command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.'+module];start=time.monotonic();print('START',label,flush=True)
 with (P/(label+'.log')).open('wb') as log:result=subprocess.run(command,cwd=str(R),env=env,stdout=log,stderr=subprocess.STDOUT)
 metadata=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(source),log_sha256=sha(P/(label+'.log')),native_calls=0);(P/(label+'_execution.json')).write_text(json.dumps(metadata,indent=2)+'\n');print(label,result.returncode,(P/(label+'.log')).read_text()[-1100:],flush=True);assert result.returncode==0 and metadata['source_sha256_before']==metadata['source_sha256_after']
