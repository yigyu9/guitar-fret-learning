from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1'
s=R/'stability_adapter_2/prepare_palm_witness_initial_trial.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected='64f5dee86b55cdbf4fa58b2c5adbcfdd701e65aae954fec04e4ce2ba6ec857bf'
assert sha(s)==expected and not (P/'preparation_execution.json').exists()
shutil.copy2(s,P/'preparation_source.py');shutil.copy2(__file__,P/'preparation_execution_producer.py')
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.prepare_palm_witness_initial_trial'];start=time.monotonic()
with (P/'preparation.log').open('wb') as log:result=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
(P/'preparation_execution.json').write_text(json.dumps(dict(command=cmd,exit_code=result.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=expected,source_sha256_after=sha(s),log_sha256=sha(P/'preparation.log'),native_initializations=0,physics_steps=0),indent=2)+'\n')
print(result.returncode,(P/'preparation.log').read_text()[-3500:]);assert result.returncode==0 and sha(s)==expected
