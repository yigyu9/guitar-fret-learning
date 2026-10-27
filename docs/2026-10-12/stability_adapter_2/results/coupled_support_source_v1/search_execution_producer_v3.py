from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1';s=R/'stability_adapter_2/search_coupled_support_source_v3.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before=sha(s)
shutil.copy2(s,P/'search_source_v3.py');shutil.copy2(__file__,P/'search_execution_producer_v3.py')
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.search_coupled_support_source_v3'];start=time.monotonic()
with (P/'search_v3.log').open('wb') as log:r=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
(P/'search_execution_v3.json').write_text(json.dumps(dict(command=cmd,exit_code=r.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(s),log_sha256=sha(P/'search_v3.log'),native_initializations=0,physics_steps=0),indent=2)+'\n')
print(r.returncode,(P/'search_v3.log').read_text()[-7000:]);assert r.returncode==0 and before==sha(s)
