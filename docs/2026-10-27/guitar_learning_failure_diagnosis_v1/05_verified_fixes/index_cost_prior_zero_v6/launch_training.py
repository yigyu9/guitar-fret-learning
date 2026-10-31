"""단일 PPO 작업을 분리 실행하고 실제 프로세스·종료·입력 불변성을 기록한다."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import experiment as ex

HERE = Path(__file__).resolve().parent
ENV_KEYS = ('PATH','PYTHONPATH','LD_LIBRARY_PATH','CUDA_VISIBLE_DEVICES','OPENBLAS_NUM_THREADS',
            'OMP_NUM_THREADS','PYTHONUNBUFFERED','HOME','DISPLAY')


def main():
    pins = ex.gate()
    checkpoint = HERE/'runs/fit/fit.pt'
    equality = ex.base.read(checkpoint.parent/'initial_tensor_equality.json')
    assert set(equality) == {'fresh.pt','fit.pt'}
    assert all(row['tensor_count'] == 71 and row['controlled_differences'] == ['cost_critic.bias','cost_critic.weight'] for row in equality.values())
    assert all(not row['full_model_exact'] and row['unchanged_tensor_count'] == 69 and row['zero_cost_head'] for row in equality.values())
    for path in (checkpoint,checkpoint.parent/'initial_tensor_equality.json',Path(__file__).resolve()):
        pins[str(path)] = ex.base.sha(path)
    folder = HERE/'execution_training'
    folder.mkdir(exist_ok=True)
    # 배타적 기록을 Popen보다 먼저 확보하여 중복 실행을 거부한다.
    with (folder/'launch_lock.json').open('x') as stream:
        json.dump(dict(supervisor_pid=os.getpid(),
            supervisor_start_ticks=int(Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]),
            argv=sys.argv,cwd=os.getcwd(),started_utc=datetime.datetime.utcnow().isoformat(),
            environment={key:os.environ[key] for key in ENV_KEYS if key in os.environ}),stream)
    command = [sys.executable,'-B',str(HERE/'experiment.py'),'train','--checkpoint',str(checkpoint),
               '--out',str(HERE/'runs/ppo')]
    assert not (HERE/'runs/ppo').exists()
    child, primary, cleanup, code = None, None, [], None
    try:
        with (folder/'execution.log').open('x') as log:
            child = subprocess.Popen(command,cwd=str(ex.parent.parent.cap.v2.ROOT),env={key:os.environ[key] for key in ENV_KEYS if key in os.environ},start_new_session=True,stdout=log,stderr=subprocess.STDOUT)
            stat = Path('/proc/%d/stat'%child.pid).read_text()
            record = dict(started_utc=datetime.datetime.utcnow().isoformat(),supervisor_pid=os.getpid(),pid=child.pid,start_ticks=int(stat.rsplit(')',1)[1].split()[19]),
                argv=command,cwd=str(ex.parent.parent.cap.v2.ROOT),input_pins=pins,
                environment={key:os.environ[key] for key in ENV_KEYS if key in os.environ})
            ex.base.write(folder/'process.json',record)
            code = child.wait()
    except BaseException as error:
        primary = error
        raise
    finally:
        try:
            if child is not None:
                if child.poll() is None: child.terminate()
                code = child.wait()
        except BaseException as error:
            if primary is None: raise
            cleanup.append(repr(error))
        changed = ex.base.changed_pins(pins)
        try:
            ex.base.write(folder/'exit.json',dict(returncode=code,process_terminal=child is None or child.poll() is not None,
                changed_inputs=changed,failure=None if primary is None else repr(primary),cleanup_errors=cleanup,
                finished_utc=datetime.datetime.utcnow().isoformat()))
        except BaseException:
            if primary is None: raise
    assert code == 0 and not changed


if __name__ == '__main__': main()
