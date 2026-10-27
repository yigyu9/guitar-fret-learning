import hashlib,json,os,subprocess,time,shutil
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
pre=json.loads((P/'root_native_preflight.json').read_text());assert all(pre['checks'].values());assert all(sha(p)==h for p,h in pre['input_sha256'].items())
for label in ('original_targets','initial_finger_targets'):
    out=P/'native'/label;trial=R/'stability_adapter_2/trials/three_face_near_contact_diagnostic_v1'/f'{label}.json';proposal=P/f'{label}_proposal.json'
    assert not out.exists()
    closure=json.loads(proposal.read_text())['input_sha256'];assert all(sha(p)==h for p,h in closure.items())
    protected={**closure,**pre['input_sha256'],str(trial):sha(trial),str(proposal):sha(proposal),str(P/'root_native_preflight.json'):sha(P/'root_native_preflight.json')}
    command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-m','stability_adapter_2.run_near_contact_diagnostic','--trial',str(trial),'--proposal',str(proposal),'--out',str(out)]
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_palm_finite',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
    print('START',label,flush=True);start=time.monotonic();log=P/f'{label}_native.log'
    with log.open('wb') as f:result=subprocess.run(command,cwd=str(R),env=env,stdout=f,stderr=subprocess.STDOUT)
    metadata=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,input_sha256_before=protected,input_sha256_after={p:sha(p) for p in protected},log_sha256=sha(log))
    (P/f'{label}_native_execution.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('END',label,result.returncode,metadata['wall_seconds'],flush=True);print(log.read_text()[-3000:],flush=True)
    assert all(metadata['input_sha256_after'][p]==h for p,h in protected.items())
    if result.returncode:break
shutil.copyfile(__file__,P/'native_execution_producer.py')
