import hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path('/home/ajou/yigyu/3');BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results';P=BASE/'three_face_arm_initial_target_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
source=ROOT/'stability_adapter_2/prepare_three_face_arm_initial_targets.py';expected='98352c2a69955a8291c625c7bbcbb3e02e16115abbfdbb434c8e9f66f2246d2c';assert sha(source)==expected and not P.exists()
env=os.environ.copy();envmeta=read(BASE/'three_face_support_loss_v1/environment.json');env.update(envmeta['env_overrides']);cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.prepare_three_face_arm_initial_targets'];start=time.monotonic();result=subprocess.run(cmd,cwd=str(ROOT),env=env,capture_output=True,text=True)
P.mkdir(exist_ok=True);(P/'prepare.log').write_text(result.stdout+result.stderr);(P/'prepare_source.py').write_bytes(source.read_bytes());assert sha(P/'prepare_source.py')==expected;(P/'execution_producer.py').write_bytes(Path(__file__).read_bytes());(P/'environment.json').write_text(json.dumps(envmeta,indent=2)+'\n');(P/'prepare_execution.json').write_text(json.dumps({'command':cmd,'exit_code':result.returncode,'elapsed_seconds':time.monotonic()-start,'source_sha256':expected,'source_sha256_after':sha(source),'native_initializations':0,'physics_steps':0},indent=2)+'\n');print('prepare finished',result.returncode,result.stdout[-2000:],flush=True)
if result.returncode:print(result.stderr[-2500:],flush=True);raise SystemExit(result.returncode)
proposal=read(P/'proposal.json');records=[];runner=ROOT/'stability_adapter_2/run_seed2_support_warmstart.py';runner_sha=sha(runner);(P/'runner_source.py').write_bytes(runner.read_bytes());assert sha(P/'runner_source.py')==runner_sha
for row in proposal['rows']:
 label=row['label'];cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.run_seed2_support_warmstart','--trial',row['trial_path'],'--out',str(P/'native'/label),'--proposal',str(P/'proposal.json')];start=time.monotonic();print('starting',label,flush=True)
 with (P/(label+'.log')).open('w') as log:code=subprocess.call(cmd,cwd=str(ROOT),env=env,stdout=log,stderr=subprocess.STDOUT)
 records.append({'label':label,'command':cmd,'exit_code':code,'elapsed_seconds':time.monotonic()-start,'runner_sha256_before':runner_sha,'runner_sha256_after':sha(runner),'log_sha256':sha(P/(label+'.log'))});(P/'execution.json').write_text(json.dumps(records,indent=2)+'\n');print('finished',label,code,flush=True)
 if code:print((P/(label+'.log')).read_text()[-4000:],flush=True);raise SystemExit(code)
