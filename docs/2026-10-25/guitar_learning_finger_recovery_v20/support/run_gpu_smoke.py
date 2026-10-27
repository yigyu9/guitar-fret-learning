"""Sequential native integration checks; never overlap GPU simulators."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PHASE = Path(__file__).resolve().parents[1]
ROOT = PHASE.parents[2]
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'


def main():
    env = dict(os.environ)
    env.update(PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/bin:/usr/bin:/bin',
        PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='0',
        PYTHONPATH=str(ROOT/'isaacgym/python')+':'+str(ROOT),
        LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',
        OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    checks = [
        ('gpu_A', ['--size','small','--num-envs','16','--updates','65']),
        ('gpu_A_resume', ['--size','small','--num-envs','16','--updates','1',
                          '--resume',str(PHASE/'gpu_A/final.pt')]),
        ('gpu_B', ['--size','small','--num-envs','16','--updates','65','--finger-shape']),
        ('gpu_large1024', ['--size','large','--num-envs','1024','--updates','2'])]
    completed = []
    for label, args in checks:
        status = dict(running=label, completed=completed)
        (PHASE/'gpu_smoke_status.json').write_text(json.dumps(status,indent=2)+'\n')
        command = [PYTHON,'-B','-m','guitar_learning.train','--hand','left',
            '--device','cuda:0','--physics','gpu','--horizon','32',
            '--checkpoint-every','250','--seed','7','--out',str(PHASE/label)]+args
        started = time.perf_counter()
        with (PHASE/(label+'_console.log')).open('x') as log:
            result = subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        completed.append(dict(run=label,returncode=result.returncode,wall_s=time.perf_counter()-started))
        if result.returncode:
            (PHASE/'gpu_smoke_status.json').write_text(json.dumps(dict(failed=label,completed=completed),indent=2)+'\n')
            raise SystemExit(result.returncode)
    (PHASE/'gpu_smoke_status.json').write_text(json.dumps(dict(complete=True,completed=completed),indent=2)+'\n')


if __name__ == '__main__':
    main()
