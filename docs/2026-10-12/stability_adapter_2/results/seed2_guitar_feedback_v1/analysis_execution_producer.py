import os,json,subprocess,time,hashlib
from pathlib import Path
root=Path('/home/ajou/yigyu/3');phase=root/'docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1';config=json.loads((phase/'environment.json').read_text());env=dict(os.environ,**config['env_overrides']);command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.analyze_seed2_guitar_feedback']
(phase/'analysis_execution_producer.py').write_bytes(Path(__file__).read_bytes());start=time.monotonic()
with (phase/'analysis.log').open('w') as log:result=subprocess.run(command,cwd=str(root),env=env,stdout=log,stderr=subprocess.STDOUT)
(phase/'analysis_execution.json').write_text(json.dumps({'command':command,'environment':config['env_overrides'],'exit_code':result.returncode,'elapsed_s':time.monotonic()-start,'log_sha256':hashlib.sha256((phase/'analysis.log').read_bytes()).hexdigest()},indent=2)+'\n');print('analysis exit',result.returncode,flush=True)
if result.returncode:raise RuntimeError('analysis failed; preserve log')
