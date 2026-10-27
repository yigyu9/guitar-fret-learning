from pathlib import Path
import json,hashlib,os,shutil,subprocess,time
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';P=R/'docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=A/'analyze_palm_witness_initial.py'
assert sha(source)=='afc4d4f44a4992ef41526843a9d258954fa925615945d777674fe07ca04e07b6'
assert not (P/'analysis.json').exists() and not (P/'analysis_execution.json').exists()
assert json.loads((P/'native_execution.json').read_text())['exit_code']==0
before=sha(source)
shutil.copy2(source,P/'analysis_source.py');shutil.copy2(__file__,P/'analysis_execution_producer.py')
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.analyze_palm_witness_initial'];start=time.monotonic()
with (P/'analysis.log').open('wb') as log:result=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
(P/'analysis_execution.json').write_text(json.dumps(dict(command=cmd,exit_code=result.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(source),log_sha256=sha(P/'analysis.log'),native_initializations=0,physics_steps=0),indent=2)+'\n')
print(result.returncode,(P/'analysis.log').read_text()[-13000:]);assert result.returncode==0 and before==sha(source)
