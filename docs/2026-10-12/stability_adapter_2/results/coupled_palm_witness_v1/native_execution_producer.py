from pathlib import Path
import json,hashlib,os,shutil,subprocess,time
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';P=R/'docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
entry=A/'run_palm_witness_initial_diagnostic.py'; runner=A/'run_small_wrist_recorded_diagnostic.py'
assert sha(entry)=='2f6565f3e5bf79b682a5704fcbbaf5978ff925c53fd6a130a92f46e145bdd380'
assert sha(runner)=='34d50c9f95a1b100efce621470a099d0aa259df7bbf307e5c7e44c6927598ef6'
assert not (P/'native').exists() and not (P/'native_execution.json').exists()
proposal=P/'proposal.json'; trial=A/'trials/coupled_palm_witness_v1/initial_witness.json'
data=json.loads(proposal.read_text());assert all(data['checks'].values()) and sha(trial)==data['rows'][0]['trial_sha256']
paths=[entry,runner,proposal,trial,A/'PALM_WITNESS_INITIAL_TRIAL_PLAN.md',A/'strap_trial_recording.py',A/'warmstart_targets.py',A/'near_contact_initial_audit.py']
before={str(p):sha(p) for p in paths}
shutil.copy2(entry,P/'native_entrypoint_source.py');shutil.copy2(runner,P/'native_source.py');shutil.copy2(__file__,P/'native_execution_producer.py')
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_small_wrist',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.run_palm_witness_initial_diagnostic','--trial',str(trial),'--proposal',str(proposal),'--out',str(P/'native')];start=time.monotonic()
with (P/'native_execution.log').open('wb') as log:result=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
after={str(p):sha(p) for p in paths}
(P/'native_execution.json').write_text(json.dumps(dict(command=cmd,exit_code=result.returncode,wall_seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after=after,log_sha256=sha(P/'native_execution.log')),indent=2)+'\n')
print(result.returncode,(P/'native_execution.log').read_text()[-3500:]);assert result.returncode==0 and before==after
