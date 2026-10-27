"""Small bounded fresh/resume v18 recording check, never a long training run."""
import json
import os
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[4]
phase = Path(__file__).resolve().parents[1]
resume = '--resume' in sys.argv
name = 'gpu_resume' if resume else 'gpu_smoke'
env = dict(os.environ)
env.update(PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/bin:/usr/bin:/bin',
    PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='0',
    PYTHONPATH=str(root/'isaacgym/python')+':'+str(root),
    LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib', OMP_NUM_THREADS='1',
    OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
cmd = ['/home/ajou/miniconda3/envs/rl38/bin/python','-B','-m','guitar_learning.train',
    '--hand','left','--device','cuda:0','--physics','gpu','--size','small',
    '--num-envs','16','--horizon','32','--updates','1' if resume else '65',
    '--out',str(phase/name)]
if resume: cmd.extend(['--resume',str(phase/'gpu_smoke/final.pt')])
with (phase/(name+'_console.log')).open('x') as log:
    result = subprocess.run(cmd,cwd=str(root),env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
print(json.dumps(dict(returncode=result.returncode,run=str(phase/name))))
if result.returncode: print((phase/(name+'_console.log')).read_text()[-5000:])
raise SystemExit(result.returncode)
