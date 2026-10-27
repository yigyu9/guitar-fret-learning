import json,os,subprocess,time,hashlib
from pathlib import Path
root=Path('/home/ajou/yigyu/3');p=root/'docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1'
config=json.loads((p/'environment.json').read_text());env=dict(os.environ,**config['env_overrides']);command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.analyze_seed2_response_locality']
logpath=p/'analysis_execution.log';record=p/'analysis_execution.json'
if logpath.exists() or record.exists():raise FileExistsError('preserve analysis execution')
(p/'analysis_execution_producer.py').write_bytes(Path(__file__).read_bytes())
start=time.monotonic()
with logpath.open('w') as log:proc=subprocess.run(command,cwd=str(root),env=env,stdout=log,stderr=subprocess.STDOUT)
record.write_text(json.dumps({'command':command,'exit_code':proc.returncode,'elapsed_s':time.monotonic()-start,'log_path':str(logpath),'log_sha256':hashlib.sha256(logpath.read_bytes()).hexdigest()},indent=2)+'\n')
print(record.read_text())
if proc.returncode:raise RuntimeError('analysis failed; preserve attempt')
