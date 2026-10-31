"""독립된 기본 조건을 순서대로 실행한다. 성공 여부에 따른 개선 선택은 분석 후 한다."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parents[1]
TERMINAL = {'passed', 'max_updates_reached_without_two_passes', 'budget_stopped', 'error'}


def read(path):
    return json.loads(path.read_text())


def publish(current, status='running', failure=None):
    conditions = {}
    for path in ROOT.glob('*/summary.json'):
        data = read(path)
        conditions[path.parent.name] = {key:data.get(key) for key in
            ('finger', 'stage', 'status', 'passed', 'completed_updates', 'best')}
    data = dict(status=status, current=current, updated_utc=datetime.now(timezone.utc).isoformat(),
        conditions=conditions, failure=failure, production_default_changed=False,
        baseline_reproduction='index A100: 32/32 safe success, zero physical/wrist failures',
        plan='PLAN.md', budget='budget.json')
    temporary = ROOT/'progress.tmp'
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(ROOT/'progress.json')


def main():
    # 첫 중지 조건은 이 스크립트보다 먼저 시작했다. 완료 증거가 생긴 뒤 이어간다.
    first = ROOT/'middle_A_seed7_v1/progress.json'
    while True:
        state = read(first)
        publish('middle_A_seed7_v1')
        if state['status'] in TERMINAL:
            if state['status'] == 'error':
                raise RuntimeError(state['failure'])
            break
        if (datetime.now(timezone.utc)-datetime.fromisoformat(state['updated_utc'])).total_seconds() > 180:
            raise RuntimeError('first condition heartbeat expired; inspect active process')
        time.sleep(15)
    source = STUDY/'runs/index_s3_f4_A_v1/train_100/J/final.pt'
    jobs = [('ring', 'A', None), ('pinky', 'A', None), ('index', 'B', source)]
    for finger, stage, checkpoint in jobs:
        label = finger+'_'+stage+'_seed7_v1'
        command = [sys.executable, '-B', str(ROOT/'research.py'), 'stage',
            '--finger', finger, '--stage', stage, '--seed', '7', '--label', label]
        if checkpoint:
            command += ['--source', str(checkpoint)]
        publish(label)
        with (ROOT/(label+'.driver.log')).open('x') as stream:
            child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
            while child.poll() is None:
                publish(label)
                time.sleep(15)
            if child.returncode:
                raise RuntimeError(label+' exited '+str(child.returncode))
        if read(ROOT/label/'summary.json')['status'] == 'budget_stopped':
            publish(label, status='budget_stopped')
            return
    publish('baseline conditions complete; analysis and next experiments pending', status='baseline_complete')


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        publish('sequence interrupted', status='error', failure=type(error).__name__+': '+str(error))
        raise
