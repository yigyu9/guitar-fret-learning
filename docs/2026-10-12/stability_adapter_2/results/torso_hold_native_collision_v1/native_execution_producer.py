import json,hashlib,shutil,os,subprocess,time
from pathlib import Path
R=Path('/home/ajou/yigyu/3');B=R/'docs/2026-10-12/stability_adapter_2/results';P=B/'torso_hold_native_collision_v1';OLD=B/'palm_patch_priority_diagnostic_v1';A=R/'stability_adapter_2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_torso_hold',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
shutil.copyfile(__file__,P/'native_execution_producer.py')
for label,module,args in [('initial_camera','capture_torso_hold_collision_v2',[]),('native','run_torso_hold_recorded_diagnostic',['--trial',str(A/'trials/palm_patch_priority_diagnostic_v1/palm_wide_near17.json'),'--proposal',str(OLD/'palm_wide_near17_proposal.json'),'--out',str(P/'native')])]:
 source=A/(module+'.py');files=[source,A/'TORSO_HOLD_EXECUTION.md',A/'TORSO_HOLD_AND_NATIVE_COLLISION_PLAN.md',OLD/'palm_wide_near17_proposal.json',A/'strap_trial_recording.py'];before={str(p):sha(p) for p in files};shutil.copyfile(source,P/(label+'_source.py'));command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.'+module]+args;start=time.monotonic();print('START',label,flush=True)
 with (P/(label+'.log')).open('wb') as log:result=subprocess.run(command,cwd=str(R),env=env,stdout=log,stderr=subprocess.STDOUT)
 metadata=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},log_sha256=sha(P/(label+'.log')));(P/(label+'_execution.json')).write_text(json.dumps(metadata,indent=2)+'\n');print(label,result.returncode,(P/(label+'.log')).read_text()[-1600:],flush=True);assert result.returncode==0 and metadata['input_sha256_before']==metadata['input_sha256_after']
