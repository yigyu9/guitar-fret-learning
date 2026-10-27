import json,os,subprocess,time,hashlib
from pathlib import Path
root=Path('/home/ajou/yigyu/3');phase=root/'docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1'
config=json.loads((phase/'environment.json').read_text());env=dict(os.environ,**config['env_overrides']);python='/home/ajou/miniconda3/envs/rl38/bin/python'
(phase/'analysis_pipeline_producer.py').write_bytes(Path(__file__).read_bytes())
steps=[('probe_analysis','stability_adapter_2.analyze_seed2_guitar_response',[]),('heldout_selection','stability_adapter_2.prepare_seed2_response_heldout',[]),('heldout','stability_adapter_2.run_seed2_guitar_response',['--trial',str(root/'stability_adapter_2/trials/seed2_guitar_response_v1/heldout.json'),'--out',str(phase/'native/heldout'),'--proposal',str(phase/'heldout_proposal.json')]),('heldout_analysis','stability_adapter_2.analyze_seed2_response_heldout',[])]
for label,module,args in steps:
    logpath=phase/(label+'_execution.log');record=phase/(label+'_execution.json')
    if logpath.exists() or record.exists():raise FileExistsError('preserve execution')
    command=[python,'-u','-m',module]+args;start=time.monotonic();print('START',label,flush=True)
    with logpath.open('w') as log:proc=subprocess.run(command,cwd=str(root),env=env,stdout=log,stderr=subprocess.STDOUT)
    record.write_text(json.dumps({'command':command,'exit_code':proc.returncode,'elapsed_s':time.monotonic()-start,'log_path':str(logpath),'log_sha256':hashlib.sha256(logpath.read_bytes()).hexdigest()},indent=2)+'\n')
    print('END',label,proc.returncode,round(time.monotonic()-start,2),flush=True)
    if proc.returncode:raise RuntimeError('failed; preserve outputs and stop')
