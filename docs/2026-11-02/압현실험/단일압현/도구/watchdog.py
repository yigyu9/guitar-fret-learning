"""감독 프로세스가 비정상 종료하면 같은 원장으로 최대 두 번 복구한다."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('single18_supervisor',HERE/'supervisor.py')
supervisor=importlib.util.module_from_spec(spec);spec.loader.exec_module(supervisor)
CHILD=None


def cleanup_orphan(state):
    """자신의 원장에 있고 고유 출력 경로가 명령에 남은 자식만 정리한다."""
    for attempts in state.get('jobs',{}).values():
        for job in attempts:
            pid=job.get('pid')
            if job['status']!='running' or not pid:continue
            try:
                command=Path('/proc/%d/cmdline'%pid).read_bytes().replace(b'\0',b' ').decode(errors='replace')
                ticks=Path('/proc/%d/stat'%pid).read_text().rsplit(')',1)[1].split()[19]
                if ticks!=job.get('proc_start_ticks') or job['out'] not in command:continue
                if os.getpgid(pid)!=pid:continue
                os.killpg(pid,signal.SIGTERM)
                for _ in range(20):
                    if not Path('/proc/%d'%pid).exists():break
                    time.sleep(.5)
                try:os.killpg(pid,signal.SIGKILL)
                except ProcessLookupError:pass
            except ProcessLookupError:pass
            except FileNotFoundError:pass


def main():
    global CHILD
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=supervisor.BASE/'로그/study_v1')
    parser.add_argument('--hours',type=float,default=8)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    def stop(sig,frame):
        if CHILD is not None:supervisor.terminate(CHILD)
        raise SystemExit(128+sig)
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    record=dict(pid=os.getpid(),started_at=supervisor.now(),attempts=[])
    command=[sys.executable,'-B',str(HERE/'supervisor.py'),'--out',str(args.out),'--hours',str(args.hours)]
    for attempt in range(3):
        path=args.out/'state.json'
        if path.exists():
            state=json.loads(path.read_text())
            if state['status'] in ('complete','budget_complete','blocked') or time.time()>=state['deadline_epoch']:break
            cleanup_orphan(state)
        with (args.out/('supervisor_attempt%d.log'%attempt)).open('a') as stream:
            CHILD=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            item=dict(pid=CHILD.pid,started_at=supervisor.now());record['attempts'].append(item)
            supervisor.write(args.out/'watchdog.json',record)
            while CHILD.poll() is None:
                record['heartbeat']=supervisor.now();supervisor.write(args.out/'watchdog.json',record)
                # 감독기의 heartbeat가 멎어도 외부GPU작업은 건드리지 않는다.
                if path.exists() and time.time()-path.stat().st_mtime>360:
                    supervisor.terminate(CHILD)
                time.sleep(10)
            item.update(returncode=CHILD.returncode,finished_at=supervisor.now())
            CHILD=None
        supervisor.write(args.out/'watchdog.json',record)
    record['finished_at']=supervisor.now();supervisor.write(args.out/'watchdog.json',record)


if __name__=='__main__':main()
