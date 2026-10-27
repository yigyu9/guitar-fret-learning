import hashlib,json,os
from pathlib import Path
import subprocess
r=Path('/home/ajou/yigyu/3');g=r/'docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1'
q=g.parent/'stability_support_nominal_v1/long_on_v2'
expected=json.loads((g/'source_before_native_v1.json').read_text())
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in expected.items())
cp=q/'checkpoints/update_000241.pt'
assert hashlib.sha256(cp.read_bytes()).hexdigest()=='3d45f1dac387e97d5d318baf8f1b9ea3ff0789227ace572f100fc1a9c61b5b06'
env=dict(os.environ,PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(r/'isaacgym/python')+':'+str(r),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',VK_ICD_FILENAMES='/usr/share/vulkan/icd.d/nvidia_icd.json',MUJOCO_GL='disable',MPLCONFIGDIR='/tmp/sa2_deadline_mpl',TORCH_EXTENSIONS_DIR='/tmp/strike_live_guitar_torch_extensions',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
command=['/home/ajou/miniconda3/envs/rl38/bin/python','-u',str(g/'launch_graphics_v1.py'),'--out',str(g/'reset_probe_v1'),'--checkpoint',str(cp),'--probe-reference',str(q/'evaluations/update_000241/native/episode_0001')]
with (g/'supervisor_probe_v1.log').open('x') as log:proc=subprocess.Popen(command,env=env,cwd=r,start_new_session=True,stdout=log,stderr=subprocess.STDOUT)
with (g/'supervisor_probe_v1.json').open('x') as f:json.dump({'pid':proc.pid,'command':command,'environment':{k:env[k] for k in ('PATH','PYTHONDONTWRITEBYTECODE','PYTHONPATH','LD_LIBRARY_PATH','VK_ICD_FILENAMES','MUJOCO_GL','MPLCONFIGDIR','TORCH_EXTENSIONS_DIR','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')}},f,indent=2)
print('probe supervisor',proc.pid)
