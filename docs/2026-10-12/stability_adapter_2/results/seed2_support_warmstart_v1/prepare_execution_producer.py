import os,json,subprocess,time,hashlib
from pathlib import Path
root=Path('/home/ajou/yigyu/3');old=root/'docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1';phase=old.parent/'seed2_support_warmstart_v1'
config=json.loads((old/'environment.json').read_text());env=os.environ.copy();env.update(config['env_overrides'])
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.prepare_seed2_warmstart_trials']
p=root/'stability_adapter_2/prepare_seed2_warmstart_trials.py';original=p.read_bytes();before=hashlib.sha256(original).hexdigest();start=time.monotonic()
with Path('/tmp/warm_prepare.log').open('w') as f:code=subprocess.call(cmd,cwd=str(root),env=env,stdout=f,stderr=subprocess.STDOUT)
assert before==hashlib.sha256(p.read_bytes()).hexdigest()
if phase.exists():
 (phase/'prepare_execution_producer.py').write_bytes(Path(__file__).read_bytes());(phase/'prepare_source.py').write_bytes(original);(phase/'prepare.log').write_bytes(Path('/tmp/warm_prepare.log').read_bytes());(phase/'environment.json').write_text(json.dumps(config,indent=2)+'\n');(phase/'prepare_execution.json').write_text(json.dumps({'command':cmd,'exit_code':code,'elapsed_seconds':time.monotonic()-start,'producer_sha256':before},indent=2)+'\n')
print('prepare exit',code,flush=True)
print(Path('/tmp/warm_prepare.log').read_text()[-5000:],flush=True)
