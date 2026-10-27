from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';P=R/'docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected={'playing_target_bridge.py':'d43ac8bef6270c1c053a456b23fc09c8f066d49e6b0458511e342dbe316f8ad8','check_playing_target_bridge.py':'97aac8701ccedca78a65ce73327f06f58067c14ec1f21164ab99095544075411','PLAYING_TARGET_BRIDGE_PLAN.md':'fe0b0f93b1196e18c1265d9f8ce35a9a9e77ecab8b6286ed11254aedcee68643'}
assert all(sha(A/p)==v for p,v in expected.items()) and not (P/'contract.json').exists() and not (P/'execution.json').exists()
for name in expected:shutil.copy2(A/name,P/name)
shutil.copy2(__file__,P/'execution_producer.py');start=time.monotonic();cmd=[sys.executable,'-u','-m','stability_adapter_2.check_playing_target_bridge'];env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',PYTHONPATH=str(R))
with (P/'execution.log').open('wb') as log:r=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
after={p:sha(A/p) for p in expected}
(P/'execution.json').write_text(json.dumps(dict(command=cmd,exit_code=r.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=expected,source_sha256_after=after,log_sha256=sha(P/'execution.log'),native_initializations=0,physics_steps=0,actor_inference_calls=0,training_updates=0),indent=2)+'\n')
print(r.returncode,(P/'execution.log').read_text()[-10000:]);assert r.returncode==0 and expected==after
