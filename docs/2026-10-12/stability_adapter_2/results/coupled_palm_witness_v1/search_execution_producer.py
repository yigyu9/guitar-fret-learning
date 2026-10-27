from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1'
source=R/'stability_adapter_2/search_coupled_palm_witness.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected='e959cc35bb7888d8580ae0e71599b743b189de6711198ca118ef6faa7a605f99'
assert sha(source)==expected and not P.exists()
snapshot=source.read_bytes();log_path=Path('/tmp/coupled_palm_witness_search.log');assert not log_path.exists()
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
cmd=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.search_coupled_palm_witness'];start=time.monotonic()
with log_path.open('wb') as log: result=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
P.mkdir(exist_ok=True)
(P/'search_source.py').write_bytes(snapshot);shutil.copy2(__file__,P/'search_execution_producer.py');shutil.copy2(log_path,P/'search.log')
(P/'search_execution.json').write_text(json.dumps(dict(command=cmd,exit_code=result.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=expected,source_sha256_after=sha(source),log_sha256=sha(P/'search.log'),native_initializations=0,physics_steps=0),indent=2)+'\n')
print('exit',result.returncode,(P/'search.log').read_text()[-7000:])
assert result.returncode==0 and sha(source)==expected
