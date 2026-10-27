import hashlib,json,shutil,os,subprocess,time
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((P/'native/report.json').read_text())['completed'];shutil.copyfile(__file__,P/'post_execution_producer.py')
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
for label,module in [('analysis','analyze_palm_priority_diagnostic'),('feature','analyze_palm_priority_features')]:
 source=R/'stability_adapter_2'/f'{module}.py';before=sha(source);shutil.copyfile(source,P/f'{label}_source.py');command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.'+module];start=time.monotonic()
 with (P/f'{label}.log').open('wb') as log:result=subprocess.run(command,cwd=str(R),env=env,stdout=log,stderr=subprocess.STDOUT)
 (P/f'{label}_execution.json').write_text(json.dumps(dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,source_sha256_before=before,source_sha256_after=sha(source),log_sha256=sha(P/f'{label}.log'),native_calls=0),indent=2)+'\n');print(label,result.returncode,(P/f'{label}.log').read_text()[-1700:],flush=True);assert result.returncode==0 and before==sha(source)
