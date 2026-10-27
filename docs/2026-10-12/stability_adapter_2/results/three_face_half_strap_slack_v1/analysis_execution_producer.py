import hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path('/home/ajou/yigyu/3');P=ROOT/'docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=ROOT/'stability_adapter_2/analyze_three_face_half_slack.py';expected=sha(src);assert expected=='889f7d690df6ea137d06f974487ee4ffb087eb95c0904faf7463184071692e6c';assert not (P/'analysis_execution.json').exists();(P/'analysis_source.py').write_bytes(src.read_bytes());assert sha(P/'analysis_source.py')==expected;(P/'analysis_execution_producer.py').write_bytes(Path(__file__).read_bytes())
env=os.environ.copy();env.update(json.loads((P/'environment.json').read_text())['env_overrides']);cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.analyze_three_face_half_slack'];start=time.monotonic()
with (P/'analysis.log').open('w') as log:code=subprocess.call(cmd,cwd=str(ROOT),env=env,stdout=log,stderr=subprocess.STDOUT)
meta={'command':cmd,'exit_code':code,'elapsed_seconds':time.monotonic()-start,'producer_sha256_before':expected,'producer_sha256_after':sha(src),'log_sha256':sha(P/'analysis.log'),'native_initializations':0,'physics_steps':0};(P/'analysis_execution.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2),flush=True);print((P/'analysis.log').read_text()[-8500:],flush=True);raise SystemExit(code)
