"""새443 압현 구조의 처리량 측정·7시간 학습·최종 평가·대표 영상을 연결한다."""
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

SELF = Path(__file__).resolve()
STUDY = SELF.parents[1]
ROOT = next(p for p in SELF.parents if (p/'guitar_learning/train.py').exists())
BUDGET = 7*3600


def write(path, value):
    """중간 상태를 원자적으로 교체해 조회 중 잘린JSON이 보이지 않게 한다."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)


def now():
    return datetime.now(timezone.utc).isoformat()


def child_train(out, updates, seconds):
    """공용 소스는 바꾸지 않고 저장된 실험 설정으로만 탐색을 초기화한다."""
    import isaacgym  # Torch보다 먼저 native runtime을 불러온다.
    import torch
    from types import SimpleNamespace
    from guitar_learning.tool.experiments import compact_press as entry
    from guitar_learning.training import finger_skill_runner as runner
    settings = entry.build_settings(num_envs=1024, horizon=32, updates=updates,
        checkpoint_every=300, size='medium', seed=7)
    settings['max_wall_seconds'] = seconds
    settings['initial_std'] = math.exp(-3)
    settings['song_run_initialization'] = dict(arm_wrist_thumb_std=.15,
        index_middle_ring_pinky_std=.35, control='all left33; right6 fixed zero',
        learning_rate='existing PPO; no additional floor or adaptive schedule')
    with entry.runtime():
        original_policy, original_pins = runner._policy, runner._pins
        def policy(config, pool):
            model = original_policy(config, pool)
            with torch.no_grad():
                model.support_log_std.fill_(math.log(.15))
                model.finger_log_std.fill_(math.log(.35))
            return model
        def pins(config, folder, extra=()):
            return original_pins(config, folder, [*extra, SELF])
        runner._policy, runner._pins = policy, pins
        try:
            result = runner.run(settings, SimpleNamespace(out=out, resume=None))
        finally:
            runner._policy, runner._pins = original_policy, original_pins
    # wall_budget은 정상 저장 경계다. 상위 report.completed는 업데이트 완주 때만 참이다.
    if (result.get('failure') or result.get('stopped') not in ('updates_complete', 'wall_budget')
            or not result.get('stages')
            or any(stage['report'].get('failure') for stage in result['stages'])):
        raise RuntimeError('학습 report 실패; 원문을 확인해야 함')


def supervise():
    """분리된 프로세스로 순차 실행하며 실패·용량 부족은 보존하고 명확히 기록한다."""
    state = dict(started_at=now(), supervisor_pid=os.getpid(), status='시작', completed=False,
                 training_budget_s=BUDGET, num_envs=1024, horizon=32, state_dim=443,
                 song='05_BN2-131-B_solo', tasks={})
    state_path = STUDY/'진행상황.json'

    def run(name, args, timeout):
        log = STUDY/'로그'/(name+'.log')
        log.parent.mkdir(exist_ok=True)
        command = [sys.executable, str(ROOT/'scripts/tab2body.py'), '--cache-root',
                   str(ROOT/'.runtime/cache'), 'run', *args]
        if name == '영상':
            command = ['xvfb-run', '-a', *command]
        started = time.monotonic()
        with log.open('x') as stream:
            process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            state.update(status='실행 중', current_task=name, child_pid=process.pid)
            state['tasks'][name] = dict(started_at=now(), log=str(log), command=command)
            interrupted = False
            try:
                while process.poll() is None:
                    elapsed = time.monotonic()-started
                    state.update(updated_at=now(), task_elapsed_s=elapsed,
                                 free_disk_bytes=shutil.disk_usage(STUDY).free)
                    for candidate in (STUDY/'학습/J/status.json', STUDY/'처리량/J/status.json'):
                        if candidate.exists():
                            state['learner_status'] = json.loads(candidate.read_text())
                            break
                    if not interrupted and (elapsed > timeout or state['free_disk_bytes'] < 4*1024**3):
                        state['stop_reason'] = 'task deadline' if elapsed > timeout else 'disk below4GiB'
                        os.killpg(process.pid, signal.SIGINT)
                        interrupted = True
                        interrupt_time = time.monotonic()
                    if interrupted and time.monotonic()-interrupt_time > 90:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                        break
                    write(state_path, state)
                    time.sleep(5)
                code = process.wait()
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGINT)
                    try:
                        process.wait(timeout=90)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
        state['tasks'][name].update(completed_at=now(), returncode=code)
        write(state_path, state)
        if code or interrupted:
            raise RuntimeError(name+' 실행 실패: '+str(code))
        report_path = {'처리량': '처리량/J/report.json', '학습': '학습/J/report.json',
                       '최종평가': '최종평가/report.json', '영상': '영상원문/report.json'}[name]
        report = json.loads((STUDY/report_path).read_text())
        if not report.get('completed') or report.get('failure'):
            raise RuntimeError(name+' report 검증 실패')

    try:
        run('처리량', [str(SELF), '--child', '--updates', '8', '--seconds', '600',
                       '--out', str(STUDY/'처리량')], 720)
        metrics = [json.loads(line) for line in (STUDY/'처리량/J/learning_metrics.jsonl').read_text().splitlines()]
        step_s = sum(m['collection_s']+m['update_s'] for m in metrics[2:])/len(metrics[2:])
        updates = math.ceil(BUDGET/step_s*1.05)
        state.update(measured_update_s=step_s, requested_updates=updates,
                     training_expected_finish_unix=time.time()+BUDGET)
        write(STUDY/'실행설정.json', dict(updates=updates, max_wall_seconds=BUDGET,
              checkpoint_every=300, num_envs=1024, horizon=32, measured_update_s=step_s))
        run('학습', [str(SELF), '--child', '--updates', str(updates), '--seconds', str(BUDGET),
                      '--out', str(STUDY/'학습')], BUDGET+600)
        checkpoint = STUDY/'학습/J/final.pt'
        common = ['-m', 'guitar_learning.tool.experiments.compact_press']
        run('최종평가', [*common, 'evaluate', str(checkpoint), '--num-envs', '16',
                         '--out', str(STUDY/'최종평가')], 1800)
        run('영상', [*common, 'render', str(checkpoint), '--num-envs', '1',
                     '--out', str(STUDY/'영상원문')], 1800)
        videos = STUDY/'동영상'
        videos.mkdir(exist_ok=True)
        for name in ('hand', 'fullbody'):
            shutil.copy2(STUDY/'영상원문'/(name+'.mp4'), videos/(name+'.mp4'))
        episodes = [json.loads(line)['episode'] for line in (STUDY/'최종평가/episodes.jsonl').read_text().splitlines()]
        result = dict(episodes=len(episodes),
            mean_achieved_notes=sum(e['song']['left_success_count'] for e in episodes)/len(episodes),
            target_count=67, checkpoint=str(checkpoint), videos=str(videos))
        write(STUDY/'최종결과.json', result)
        state.update(status='완료', completed=True, result=result, completed_at=now())
    except BaseException as error:
        import traceback
        state.update(status='실패', failure=dict(type=type(error).__name__, message=str(error),
                     traceback=traceback.format_exc()), completed_at=now())
        raise
    finally:
        state.update(current_task=None, updated_at=now())
        write(state_path, state)


if __name__ == '__main__':
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', action='store_true')
    parser.add_argument('--updates', type=int)
    parser.add_argument('--seconds', type=float)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.child:
        child_train(args.out, args.updates, args.seconds)
    else:
        supervise()
