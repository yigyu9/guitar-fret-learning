import json,os,subprocess,time,hashlib
from pathlib import Path
root=Path('/home/ajou/yigyu/3')
phase=root/'docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1'
previous=phase.parent/'seed2_startup_target_v1'
config=json.loads((previous/'environment.json').read_text())
env=dict(os.environ,**config['env_overrides'])
python='/home/ajou/miniconda3/envs/rl38/bin/python'
command=[python,'-u','-m','stability_adapter_2.prepare_seed2_response_trials']
start=time.monotonic();proc=subprocess.run(command,cwd=str(root),env=env,capture_output=True,text=True)
if not phase.exists():raise RuntimeError(proc.stdout+proc.stderr)
(phase/'prepare.log').write_text(proc.stdout+proc.stderr)
(phase/'prepare_execution.json').write_text(json.dumps({'command':command,'exit_code':proc.returncode,'elapsed_s':time.monotonic()-start},indent=2)+'\n')
if proc.returncode:raise RuntimeError('prepare failed')
(phase/'environment.json').write_text(json.dumps(config,indent=2)+'\n')
(phase/'batch_producer.py').write_bytes(Path(__file__).read_bytes())
proposal=json.loads((phase/'proposal.json').read_text())
execution=[]
for row in proposal['rows']:
    label=row['label'];command=[python,'-u','-m','stability_adapter_2.run_seed2_guitar_response','--trial',row['trial_path'],'--out',str(phase/'native'/label)]
    print('START',label,flush=True);start=time.monotonic()
    with (phase/(label+'.log')).open('w') as log:result=subprocess.run(command,cwd=str(root),env=env,stdout=log,stderr=subprocess.STDOUT)
    execution.append({'label':label,'command':command,'exit_code':result.returncode,'elapsed_s':time.monotonic()-start})
    (phase/'execution.json').write_text(json.dumps(execution,indent=2)+'\n')
    print('END',label,result.returncode,round(execution[-1]['elapsed_s'],2),flush=True)
    if result.returncode:raise RuntimeError('native failed; preserve partial and stop')
print('BATCH COMPLETED',flush=True)
