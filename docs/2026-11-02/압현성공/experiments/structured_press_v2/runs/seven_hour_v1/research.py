"""7시간 연구의 단일 손가락·단계를 실행하고 고정 32환경 원시 평가로 판정한다."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import signal
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
STUDY = Path(__file__).resolve().parents[2]
RUNTIME = STUDY/'runtime'
MODULE = 'guitar_learning.tool.experiments.structured_press'
STAGES = ('A', 'B', 'C50', 'C75', 'C100')


def utcnow():
    return datetime.now(timezone.utc)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)


def verify_seal():
    seal = read(STUDY/'source_seal.json')
    if len(seal['files']) != 3148:
        raise ValueError('expected immutable 3148-file runtime source seal')
    changed = [name for name, expected in seal['files'].items()
               if not (RUNTIME/name).is_file() or digest(RUNTIME/name) != expected]
    if changed:
        raise ValueError('runtime source seal changed: '+str(changed[:8]))
    return digest(STUDY/'source_seal.json')


def training_budget(budget, recent_seconds=None, now=None):
    deadline = datetime.fromisoformat(budget['training_deadline_utc'].replace('Z', '+00:00'))
    remaining = (deadline-(now or utcnow())).total_seconds()
    required = max(15*60., recent_seconds*1.3+120 if recent_seconds else 0.)
    return dict(allowed=remaining >= required, remaining_seconds=remaining,
                required_seconds=required, training_deadline_utc=deadline.isoformat(),
                final_reserve_minutes=35)



class BudgetStop(RuntimeError):
    """정상 완료와 구분해 보존해야 하는 실행 중 예산 중단."""


def deadline_status(budget, operation, now=None):
    key = 'training_deadline_utc' if operation == 'train' else 'deadline_utc'
    deadline = datetime.fromisoformat(budget[key].replace('Z', '+00:00'))
    remaining = (deadline-(now or utcnow())).total_seconds()
    return dict(operation=operation, deadline_key=key, deadline_utc=deadline.isoformat(),
                remaining_seconds=remaining, expired=remaining <= 0)


def interrupt_child(child):
    """실행기에 먼저 정리 기회를 주고, 응답하지 않을 때만 강제 종료한다."""
    signals = []
    if child.poll() is not None:
        return signals
    child.send_signal(signal.SIGINT)
    signals.append('SIGINT')
    try:
        child.wait(timeout=30)
    except subprocess.TimeoutExpired:
        child.terminate()
        signals.append('SIGTERM')
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            signals.append('SIGKILL')
            child.wait()
    return signals


def summarize_episodes(report, rows):
    """압축 복원된 첫 에피소드 32개만 집계하며 실패 clean은 선택 지표에서 0점이다."""
    episodes = [row['episode'] for row in rows]
    ids = [episode['env_id'] for episode in episodes]
    if (not report.get('completed') or len(episodes) != 32 or
            len(set(ids)) != 32 or set(ids) != set(range(32))):
        raise ValueError('completed unique env0..31 first-episode denominator required')
    if report['summary']['count'] != 32 or report.get('episodes') != 32:
        raise ValueError('report/raw denominator mismatch')
    if not (report.get('first_episode_per_env') or report.get('first_episode_per_env_per_batch')):
        raise ValueError('first-episode evaluation contract required')
    failures, successes, physical, wrist = 0, 0, 0, 0
    clean, best_clean, safe_clean, safe_best, rewards, reasons = [], [], [], [], [], {}
    for episode in episodes:
        if episode.get('valid') is not True or episode['song']['target_count'] != 1:
            raise ValueError('valid single-target episodes required')
        termination = episode['termination']
        physical += bool(termination['physical_failure'])
        wrist += bool(termination['wrist_failure'])
        failed = bool(termination['physical_failure'] or termination['wrist_failure'])
        failures += failed
        successes += bool(episode['song']['left_success_count'] >= 1 and not failed)
        ledger = episode['left_note_ledger']['values']
        if len(ledger['clean']) != 1 or len(ledger['best_clean_streak']) != 1:
            raise ValueError('single-target clean ledger required')
        total, best = float(ledger['clean'][0]), float(ledger['best_clean_streak'][0])
        if not all(math.isfinite(value) and value >= 0 for value in (total, best)):
            raise ValueError('finite nonnegative clean times required')
        clean.append(total); best_clean.append(best)
        safe_clean.append(0. if failed else total); safe_best.append(0. if failed else best)
        rewards.append(float(episode['reward']))
        for reason in episode.get('failure_reasons', []):
            reasons[reason] = reasons.get(reason, 0)+1
    if report.get('failure_episode_count', failures) != failures:
        raise ValueError('raw/report union failure count mismatch')
    if report['summary']['stage_success'] != successes:
        raise ValueError('raw/report safe success mismatch')
    mean = lambda values: sum(values)/32.
    return dict(count=32, safe_success=successes, failure_episodes=failures,
        physical_failure=physical, wrist_failure=wrist,
        mean_clean_s=mean(clean), mean_best_clean_s=mean(best_clean),
        mean_safe_clean_s=mean(safe_clean), mean_safe_best_clean_s=mean(safe_best),
        mean_reward=mean(rewards), failure_reasons=reasons,
        denominator='unique first episode per env, including failures')


def accepted(stage, summary):
    if stage not in STAGES:
        raise ValueError('unknown curriculum stage')
    minimum = 24 if stage == 'A' else 22 if stage == 'B' else 16
    return (summary['safe_success'] >= minimum and
            (stage == 'A' or summary['failure_episodes'] <= 1))


def selection_key(row):
    summary = row['summary']
    return (summary['safe_success'], summary['mean_safe_clean_s'],
            -summary['failure_episodes'], row['updates'])


def aggregate(path):
    if str(RUNTIME) not in sys.path:
        sys.path.insert(0, str(RUNTIME))
    from guitar_learning.training.training_log_io import iter_episode_rows
    return summarize_episodes(read(path/'report.json'), list(iter_episode_rows(path)))


def persist(out, state):
    state['updated_utc'] = utcnow().isoformat()
    write(out/'progress.json', state)
    evaluations = ([state['initial_evaluation']] if state.get('initial_evaluation') else [])+state['blocks']
    best = max(evaluations, key=selection_key) if evaluations else None
    summary = dict(schema='structured_press.seven_hour_stage.v1', finger=state['finger'],
        stage=state['stage'], seed=state['seed'], status=state['status'],
        passed=state.get('passed', False), consecutive_passes=state.get('consecutive_passes', 0),
        completed_updates=state['blocks'][-1]['updates'] if state['blocks'] else 0,
        best=best, initial=state.get('initial_evaluation'), blocks=state['blocks'],
        source=state['source'], source_seal_sha256=state['source_seal_sha256'],
        budget=state.get('budget'), budget_stop=state.get('budget_stop'),
        failure=state.get('failure'), updated_utc=state['updated_utc'])
    write(out/'summary.json', summary)
    lines = ['# '+state['finger']+' '+state['stage']+' 연구 결과', '',
        '상태: '+state['status']+' / 평가: '+state['evaluation_kind'], '',
        '|누적 갱신|안전 달성 /32|실패 /32|clean 평균(실패 0점, 초)|통과|',
        '|--:|--:|--:|--:|:--:|']
    for row in evaluations:
        values = row['summary']
        lines.append('|{}|{}|{}|{:.4f}|{}|'.format(row['updates'], values['safe_success'],
            values['failure_episodes'], values['mean_safe_clean_s'], row['accepted']))
    if best:
        lines += ['', '선택 모델: `'+best['checkpoint']+'`',
            '선택 순서: 안전 달성 → 실패를 0점 처리한 clean 평균 → 실패 수가 적음 → 최신 갱신.']
    if state.get('failure'):
        lines += ['', '오류: '+state['failure']]
    if state.get('budget_stop'):
        lines += ['', '예산 중단(실행 중 블록은 미완료): '+json.dumps(state['budget_stop'], ensure_ascii=False)]
    if state.get('budget'):
        lines += ['', '예산 확인: '+json.dumps(state['budget'], ensure_ascii=False)]
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def execute(arguments, destination, out, state):
    """동일 환경을 계승하고 child PID·heartbeat를 기록하며 기존 산출물은 덮어쓰지 않는다."""
    destination = Path(destination)
    log = destination.with_name(destination.name+'.console.log')
    if destination.exists() or log.exists():
        raise FileExistsError('partial/existing output must be inspected, never overwritten: '+str(destination))
    verify_seal()
    command = [sys.executable, '-B', '-X', 'utf8', '-m', MODULE]+arguments
    state.update(status='running:'+arguments[0], command=command, child_started_utc=utcnow().isoformat())
    started = time.monotonic()
    with log.open('x') as stream:
        child = subprocess.Popen(command, cwd=RUNTIME, env=os.environ.copy(),
                                 stdout=stream, stderr=subprocess.STDOUT)
        state['child_pid'] = child.pid
        persist(out, state)
        try:
            while True:
                limit = deadline_status(read(ROOT/'budget.json'), arguments[0])
                if limit['expired']:
                    state.update(status='budget_stopped', budget_stop=dict(limit,
                        requested_utc=utcnow().isoformat(), partial_block=True))
                    persist(out, state)
                    state['budget_stop']['signals'] = interrupt_child(child)
                    state['budget_stop']['child_exit_code'] = child.returncode
                    raise BudgetStop(arguments[0]+' reached '+limit['deadline_key'])
                try:
                    code = child.wait(timeout=min(15., limit['remaining_seconds']))
                    break
                except subprocess.TimeoutExpired:
                    persist(out, state)
        except BudgetStop:
            raise
        except BaseException:
            child.terminate()
            try:
                child.wait(timeout=20)
            except subprocess.TimeoutExpired:
                child.kill(); child.wait()
            raise
        finally:
            state['child_pid'] = None
            state['child_finished_utc'] = utcnow().isoformat()
            persist(out, state)
    if code:
        raise RuntimeError('child exit {}: {}'.format(code, log))
    verify_seal()
    return time.monotonic()-started


def evaluation(checkpoint, destination, updates, out, state):
    execute([state['evaluation_kind'], '--checkpoint', str(checkpoint), '--num-envs', '32',
             '--out', str(destination)], destination, out, state)
    summary = aggregate(destination)
    if read(destination/'report.json')['checkpoint_sha256'] != digest(checkpoint):
        raise ValueError('evaluation/checkpoint SHA mismatch')
    row = dict(updates=updates, checkpoint=str(checkpoint), checkpoint_sha256=digest(checkpoint),
        evaluation=str(destination), evaluation_sha256={name:digest(destination/name)
            for name in ('report.json', 'episodes.jsonl', 'episode_metadata.json')},
        summary=summary, metrics=summary, accepted=accepted(state['stage'], summary))
    return row


def run_stage(args):
    if Path(args.label).name != args.label or args.label in ('.', '..'):
        raise ValueError('label must be one safe directory name')
    if args.stage != 'A' and args.source is None:
        raise ValueError('B/C stages require explicit source checkpoint')
    if args.stage == 'A' and args.source is not None:
        raise ValueError('A starts fresh; only B/C accept adjacent-stage transfer')
    source = Path(args.source).resolve() if args.source else None
    source_record = dict(path=str(source), sha256=digest(source)) if source else None
    source_seal = verify_seal()
    geometry = RUNTIME/'guitar_learning/assets/structured_press_v2/catalog.json'
    goals = [goal for goal in read(geometry)['goals'] if goal['finger'] == args.finger]
    if len(goals) != 1:
        raise ValueError('exactly one catalog goal per requested finger required')
    out = ROOT/args.label
    out.mkdir(exist_ok=False)
    state = dict(schema='structured_press.seven_hour_progress.v1', finger=args.finger,
        stage=args.stage, seed=args.seed, source=source_record, source_seal_sha256=source_seal,
        geometry_sha256=digest(geometry), song=goals[0]['song'],
        started_utc=utcnow().isoformat(), status='preparing', blocks=[], passed=False,
        consecutive_passes=0, child_pid=None,
        evaluation_kind='evaluate-free-v9' if args.stage.startswith('C') else 'evaluate')
    persist(out, state)
    previous, streak, recent = None, 0, None
    try:
        for number in range(1, 4):
            budget = training_budget(read(ROOT/'budget.json'), recent)
            state['budget'] = budget
            if not budget['allowed']:
                state['status'] = 'budget_stopped'
                break
            if source and digest(source) != source_record['sha256']:
                raise ValueError('source checkpoint changed')
            location = out/('{:03d}'.format(number*100))
            location.mkdir(exist_ok=False)
            train = location/'train'
            command = ['train', '--geometry', str(geometry), '--song', state['song'], '--stage', args.stage,
                '--size', 'large', '--num-envs', '64', '--updates', '100', '--seed', str(args.seed), '--out', str(train)]
            if previous:
                if digest(previous) != state['blocks'][-1]['checkpoint_sha256']:
                    raise ValueError('resume checkpoint changed since evaluation')
                command += ['--resume', str(previous)]
            elif source:
                command += ['--initialize-from', str(source)]
            block_started = time.monotonic()
            train_seconds = execute(command, train, out, state)
            checkpoint = train/'J/final.pt'
            if not read(train/'report.json')['completed'] or not checkpoint.is_file():
                raise RuntimeError('incomplete training block: '+str(train))
            if number == 1:
                state['initial_evaluation'] = evaluation(train/'J/initial.pt', location/'evaluate_initial', 0, out, state)
                persist(out, state)
            row = evaluation(checkpoint, location/'evaluate_final', number*100, out, state)
            row.update(train_seconds=train_seconds, block_seconds=time.monotonic()-block_started)
            # 초기 평가는 연속 통과에서 제외하고 서로 다른 갱신 저장본을 요구한다.
            if state['blocks'] and row['checkpoint_sha256'] == state['blocks'][-1]['checkpoint_sha256']:
                raise ValueError('consecutive promotion requires distinct updated checkpoints')
            state['blocks'].append(row)
            streak = streak+1 if row['accepted'] else 0
            state['consecutive_passes'] = streak
            previous, recent = checkpoint, row['block_seconds']
            if streak >= 2:
                state.update(status='passed', passed=True)
                break
            state['status'] = 'block_complete'
            persist(out, state)
        else:
            state['status'] = 'max_updates_reached_without_two_passes'
    except BudgetStop as error:
        state.update(status='budget_stopped', partial_block=True, stop_reason=str(error))
    except BaseException as error:
        state.update(status='error', failure=type(error).__name__+': '+str(error))
        raise
    finally:
        persist(out, state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('stage',))
    parser.add_argument('--finger', required=True, choices=('middle', 'ring', 'pinky', 'index'))
    parser.add_argument('--stage', required=True, choices=STAGES)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--label', required=True)
    run_stage(parser.parse_args())


if __name__ == '__main__':
    main()
