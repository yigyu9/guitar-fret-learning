import hashlib,json,os,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(module,label):
 source=R/'stability_adapter_2'/f'{module}.py';log=P/f'{label}_execution.log';assert not log.exists();shutil.copyfile(source,P/f'{label}_source.py');before=sha(source)
 env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
 command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.'+module];start=time.monotonic()
 with log.open('wb') as f:result=subprocess.run(command,cwd=str(R),env=env,stdout=f,stderr=subprocess.STDOUT)
 (P/f'{label}_execution.json').write_text(json.dumps(dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(source),log_sha256=sha(log),native_calls=0),indent=2)+'\n')
 print(label,result.returncode,log.read_text()[-4000:],flush=True);assert result.returncode==0 and before==sha(source)
assert all(json.loads((P/'native'/label/'report.json').read_text())['completed'] for label in ('original_targets','initial_finger_targets'))
run('analyze_near_contact_diagnostic','analysis');run('make_near_contact_artifacts','artifact');shutil.copyfile(__file__,P/'post_execution_producer.py')
