import hashlib,json,os,subprocess
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1'
expected=json.loads((P/'source_before_native_v1.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in expected.items())
assert (P/'review_preflight_v1.md').exists()
source=json.loads((P/'previous_stop_snapshot_v1.json').read_text())['checkpoint_record'];checkpoint=Path(source['checkpoint'])
assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()==source['sha256']
env=dict(os.environ,PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',VK_ICD_FILENAMES='/usr/share/vulkan/icd.d/nvidia_icd.json',MUJOCO_GL='disable',MPLCONFIGDIR='/tmp/sa2_deadline_mpl',TORCH_EXTENSIONS_DIR='/tmp/strike_live_guitar_torch_extensions',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
for name,flags in (('probe_v1',['--probe']),('smoke_v1',['--checkpoint',str(checkpoint),'--adopt','--steps','64','--max-updates',str(source['updates']+1)])):
    command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u',str(P/'launch_parallel_v1.py'),'--out',str(P/name),*flags]
    with (P/('supervisor_'+name+'.log')).open('x') as stream:proc=subprocess.Popen(command,env=env,cwd=R,start_new_session=True,stdout=stream,stderr=subprocess.STDOUT)
    with (P/('supervisor_'+name+'.json')).open('x') as stream:json.dump({'pid':proc.pid,'command':command,'environment':{k:env[k] for k in ('PATH','PYTHONDONTWRITEBYTECODE','PYTHONPATH','LD_LIBRARY_PATH','VK_ICD_FILENAMES','MUJOCO_GL','MPLCONFIGDIR','TORCH_EXTENSIONS_DIR','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')}},stream,indent=2)
    print(name,'supervisor',proc.pid)
