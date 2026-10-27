"""Bounded native GPU recording check; sources must remain frozen while running."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[4]
phase = Path(__file__).resolve().parents[1]
environment = dict(os.environ)
environment.update(PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/bin:/usr/bin:/bin',
    PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='0',
    PYTHONPATH=str(root/'isaacgym/python')+':'+str(root),
    LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',
    OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
python = '/home/ajou/miniconda3/envs/rl38/bin/python'
legacy = '--legacy' in sys.argv
resume = '--resume' in sys.argv or legacy
name = 'gpu_legacy_resume' if legacy else 'gpu_resume' if resume else 'gpu_smoke_retry1'
command = [python, '-B', '-m', 'guitar_learning.train', '--hand', 'left',
    '--device', 'cuda:0', '--physics', 'gpu', '--size', 'large' if legacy else 'small',
    '--num-envs', '1024' if legacy else '16',
    '--horizon', '32', '--updates', '1' if resume else '65',
    '--checkpoint-every', '32', '--out', str(phase/name)]
if resume:
    checkpoint = root/'docs/2026-10-24/guitar_learning_long_training_v17/train2000/final.pt' if legacy else phase/'gpu_smoke_retry1/final.pt'
    command.extend(['--resume', str(checkpoint)])
with (phase/(name+'_console.log')).open('x') as log:
    result = subprocess.run(command, cwd=str(root), env=environment,
        stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
print(json.dumps(dict(returncode=result.returncode, run=str(phase/name))))
if result.returncode:
    print((phase/(name+'_console.log')).read_text()[-6000:])
raise SystemExit(result.returncode)
