"""Interrupt only our own training parent after observed collection progress."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time

if __name__=='__main__':
    root=Path('/home/ajou/yigyu/3')
    phase=root/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1'
    out=phase/'interrupt_native_v1'
    checkpoint=root/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_20261018_100545/checkpoint_000009.pt'
    command=['/home/ajou/miniconda3/envs/rl38/bin/python','-m','guitar_learning.train_parallel','--settings',str(phase/'interrupt_smoke_settings.json'),'--out',str(out),'--resume',str(checkpoint)]
    started=time.monotonic();signalled=False;observed=None
    with (phase/'interrupt_console.log').open('x') as log:
        child=subprocess.Popen(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
        try:
            while child.poll() is None:
                if time.monotonic()-started>240:
                    raise TimeoutError('owned interruption test did not reach collection')
                status=out/'status.json'
                if status.exists():
                    observed=json.loads(status.read_text())
                    if observed['phase']=='collecting' and observed['ticks']>=4:
                        child.send_signal(signal.SIGINT);signalled=True;break
                time.sleep(.2)
            result=child.wait(timeout=60)
        finally:
            if child.poll() is None:
                child.terminate();child.wait(timeout=15)
    record=dict(command=command,parent_pid=child.pid,signal_sent=signalled,observed_before_signal=observed,exitcode=result,wall_s=time.monotonic()-started)
    (phase/'interrupt_driver_result.json').write_text(json.dumps(record,indent=2)+'\n')
    if not signalled:raise RuntimeError('test ended before controlled interrupt')
    report=json.loads((out/'report.json').read_text())
    if report['stopped']!='interrupted' or report['completed'] or not Path(report['recovery_checkpoint']['path']).is_file():
        raise RuntimeError('interruption recovery did not meet expected checks')
    print(json.dumps(dict(stopped=report['stopped'],recovery=report['recovery_checkpoint'],partial=report['partial_collection'],checks=dict(missing_audits=report['missing_worker_audits'],worker_failures=report['worker_failures'])),indent=2))
