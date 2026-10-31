"""같은 학습을 독립 세션에서 실행하고 시작·종료와 입력 SHA를 남긴다."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
V4 = HERE.parent
ROOT = V4.parents[4]
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


if __name__ == '__main__':
    pins = json.loads((V4/'preparation_seal.json').read_text())['input_pins']
    checkpoint = V4/'runs/fit/fit.pt'
    pins[str(checkpoint)] = sha(checkpoint)
    pins[str(Path(__file__).resolve())] = sha(__file__)
    assert all(sha(path) == digest for path,digest in pins.items())
    command = [PYTHON,'-B',str(V4/'experiment.py'),'train','--checkpoint',str(checkpoint),
               '--out',str(V4/'runs/ppo_attempt02')]
    env = dict(os.environ)
    env.update(PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/cuda/bin:/usr/bin:/bin',
        PYTHONPATH=str(ROOT/'isaacgym/python')+':'+str(ROOT),
        LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',
        OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONUNBUFFERED='1')
    write(HERE/'attempt02_launch.json',dict(started_UTC=now(),launcher_pid=os.getpid(),
        command=command,cwd=str(ROOT),source_input_pins=pins,
        environment={key:env.get(key) for key in ('PATH','PYTHONPATH','LD_LIBRARY_PATH',
            'OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','PYTHONUNBUFFERED',
            'CUDA_VISIBLE_DEVICES','CUDA_DEVICE_ORDER','PYTHONHASHSEED')},
        original_attempt01_preserved=True,restart_from_fit_update0=True))
    with (V4/'execution_ppo_attempt02.log').open('x') as log:
        child = subprocess.Popen(command,cwd=str(ROOT),env=env,stdin=subprocess.DEVNULL,
                                 stdout=log,stderr=subprocess.STDOUT)
        start_ticks = Path('/proc/%d/stat'%child.pid).read_text().rsplit(')',1)[1].split()[19]
        write(HERE/'attempt02_process.json',dict(child_pid=child.pid,start_ticks=start_ticks,
            launcher_pid=os.getpid(),started_UTC=now(),command=command))
        code = child.wait()
    changed = [path for path,digest in pins.items() if not Path(path).is_file() or sha(path) != digest]
    write(HERE/'attempt02_exit.json',dict(finished_UTC=now(),returncode=code,
        changed_inputs=changed,process_terminal=True))
    sys.exit(code if code >= 0 else 128-code)
