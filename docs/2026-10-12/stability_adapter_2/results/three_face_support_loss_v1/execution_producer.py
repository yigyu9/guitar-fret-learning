import hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path('/home/ajou/yigyu/3');BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results';P=BASE/'three_face_support_loss_v1';OLD=BASE/'three_face_finger_target_hold_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
src=ROOT/'stability_adapter_2/run_three_face_shape_readback.py';expected='ca467248e9dbbce8d8967cfa5d8cf3893d58b8b9a0821c4d4840aac61febba60';assert sha(src)==expected
assert not (P/'execution.json').exists();(P/'execution_producer.py').write_bytes(Path(__file__).read_bytes());(P/'runner_source.py').write_bytes(src.read_bytes());assert sha(P/'runner_source.py')==expected
row=read(OLD/'proposal.json')['rows'][0];assert row['label']=='saved_finger_targets';envfile=P/'environment.json';envsha=sha(envfile);env=os.environ.copy();env.update(read(envfile)['env_overrides'])
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.run_three_face_shape_readback','--trial',row['trial_path'],'--out',str(P/'native/saved_finger_targets'),'--proposal',str(OLD/'proposal.json')]
start=time.monotonic();print('starting shape readback repeat',flush=True)
with (P/'native_execution.log').open('w') as log:code=subprocess.call(cmd,cwd=str(ROOT),env=env,stdout=log,stderr=subprocess.STDOUT)
meta={'command':cmd,'exit_code':code,'elapsed_seconds':time.monotonic()-start,'runner_sha256_before':expected,'runner_sha256_after':sha(src),'log_sha256':sha(P/'native_execution.log'),'environment_sha256_before':envsha,'environment_sha256_after':sha(envfile)};(P/'execution.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2),flush=True)
if code:print((P/'native_execution.log').read_text()[-4000:],flush=True)
raise SystemExit(code)
