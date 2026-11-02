"""L의 보호 중단을 보존하고 승인된 독립 H/I/T 비교를 이어간다.

학습·KL·보상·저장 모델은 변경하지 않는다. KL 보호 중단은 해당 seed의
종속 연장만 중단하고 독립 조건은 계속한다. 다른 오류는 전체를 중단한다.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
import study


original_progress = study.progress


def progress(state, out):
    # 지표 JSONL을 쓰는 순간의 불완전한 마지막 줄은 잠시 뒤 다시 읽는다.
    for attempt in range(3):
        try:
            original_progress(state, out)
            break
        except json.JSONDecodeError:
            if attempt == 2:
                state['progress_read_retries'] = state.get('progress_read_retries', 0)+1
                study.write(out/'progress.json', state)
                return
            time.sleep(.05)
    current = state.get('current_job') or {}
    completed = sum(job.get('updates', 0)*job.get('horizon_ratio', 1)
                    for job in state['jobs'].values() if job['status'] == 'complete' and job['operation'] == 'train')
    partial = state.get('current_partial_updates', 0)*current.get('horizon_ratio', 1)
    evaluated = sum(job['status'] == 'complete' and job['operation'] == 'evaluate' for job in state['jobs'].values())
    budget, evaluations = (2600, 36) if state.get('skipped_I') else (4600, 54)
    seconds = max(0, budget-completed-partial)*state.get('seconds_per_H32_update', 5.1)+max(0, evaluations-evaluated)*75+240
    state['estimated_finish_if_all_conditions'] = (datetime.now(study.KST)+timedelta(seconds=seconds)).isoformat(timespec='minutes')
    study.write(out/'progress.json', state)
    lines = ['# 구조·초기분포·엄지 후속 비교', '', '- 갱신: '+state['updated_at'], '- 상태: '+state['status'],
             '- 현재: '+current.get('label', '없음'), '- 현재 블록 완료: '+str(state.get('current_partial_updates', 0)),
             '- 남은 모든 조건을 수행할 경우 예상: '+state['estimated_finish_if_all_conditions'],
             '- 원본 L은 KL 보호 중단 상태로 보존했다. 아래는 새 독립 조건이다.', '', '[결과·분석](RESULTS.md)']
    (out/'진행상황.md').write_text('\n'.join(lines)+'\n')


study.progress = progress


def expected_kl_failure(state, out, condition, seed, total):
    label = f'{condition}_s{seed}_u{total}_train'
    folder = out/'jobs'/label
    path = folder/'J/report.json'
    if not path.is_file():
        return False
    report = json.loads(path.read_text())
    outer_path = folder/'report.json'
    if not outer_path.is_file():
        return False
    outer = json.loads(outer_path.read_text())
    failure = report.get('failure') or {}
    if (failure.get('type') != 'KLGuardError' or report.get('changed_inputs') != []
            or report.get('cleanup_errors') != [] or report.get('missing_import_pins') != []
            or report.get('lifecycle_verified') is not True
            or (outer.get('failure') or {}).get('type') != 'KLGuardError'
            or outer.get('missing_import_pins') or outer.get('changed_inputs')
            or outer.get('cleanup_errors')):
        return False
    study.check_sources(state)
    state.setdefault('protected_failures', []).append(dict(
        label=label, report=str(path), report_sha256=study.sha(path),
        completed_updates=report.get('optimizer_updates'),
        reason='KLGuardError; failed block and partial commits preserved; no relaxed KL/LR rule'))
    state['interpretations'].append(f'{label}: KL 보호로 해당 seed 연장만 중단. 독립 조건은 계속하며 불완전 블록은 성공으로 집계하지 않음.')
    study.progress(state, out)
    return True


def train_condition(state, out, name, totals, *, horizon=32, axes='arm16', script='runtime.py'):
    finals = {}
    for seed in (7, 17):
        checkpoint = None
        last = 0
        for total in totals:
            try:
                checkpoint = study.train(state, out, name, seed, total, checkpoint, total-last,
                                         horizon=horizon, axes=axes, script=script)
            except RuntimeError:
                if expected_kl_failure(state, out, name, seed, total):
                    break
                raise
            last = total
            for mode in ('mean', 'sampled'):
                study.evaluate(state, out, name, seed, total, checkpoint, mode, script=script)
        if checkpoint is not None:
            finals[seed] = study.evaluate(state, out, name+'_last_saved', seed, last,
                                         checkpoint, 'mean', count=128, script=script)
    return finals


def passed(metrics):
    n = metrics['episodes']
    return (metrics['AB']/n >= .9 and min(metrics['clean_s'])/1.5 >= .9
            and metrics['on_time_with_previous_tail']/n >= .9
            and (metrics['physical']+metrics['wrist'])/n <= .01)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError('후속 실행은 새 경로 필요')
    original = study.BASE/'runs/study_v1/progress.json'
    before = json.loads(original.read_text())
    if before['status'] != 'failed':
        raise ValueError('원래 중단 상태를 먼저 확인해야 함')
    study.check_sources(before)
    failed = before['jobs']['L_H32_s17_u1000_train']
    failure_report = Path(failed['out'])/'J/report.json'
    if json.loads(failure_report.read_text())['failure']['type'] != 'KLGuardError':
        raise ValueError('분석한 KL 중단과 다른 오류')
    out.mkdir(parents=True)
    with (out/'study.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        def stop(signum, frame):
            raise KeyboardInterrupt('종료 신호 '+str(signum))
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        state = dict(schema='transition_diagnosis.continuation.v1', status='running',
            started_at=study.now(), driver_pid=os.getpid(), source_seal=study.seal(),
            jobs={}, results={}, interpretations=[
                '원본 L은 seed7 1000회 완료, seed17 누적942회 후 KL 중단. seed17 최종 저장본은900회이며1000회 완료로 취급하지 않는다.',
                '새 실행은 KL/LR/보상/물리를 변경하지 않고 독립 H/I/T 조건을 진행한다.'],
            original_progress=str(original), original_progress_sha256=study.sha(original),
            failure_report_sha256=study.sha(failure_report),
            L_finished_at=before['finished_at'], L_status='incomplete_KL_guard',
            source_scope='new independent conditions; no legacy result status rewritten')
        try:
            horizon = train_condition(state, out, 'H128', (25, 50, 75, 150, 250), horizon=128)
            horizon_passed = len(horizon) == 2 and all(passed(m) for m in horizon.values())
            state['interpretations'].append('H128의 최종 저장 모델은 두 seed 모두 채택 기준을 '+('통과했다.' if horizon_passed else '통과하지 못했다.'))
            proof = study.BASE/'validation/B_reset_native_v2/report.json'
            if not horizon_passed:
                if json.loads(proof.read_text()).get('accepted') is not True:
                    raise ValueError('I native 검증 미통과')
                train_condition(state, out, 'I_mix', (100, 300, 600, 1000), script='initial_mix.py')
            else:
                state['skipped_I'] = True
            train_condition(state, out, 'T_arm21', (100, 200, 300), axes='arm21')
            candidates = [r for r in state['results'].values() if r['mode'] == 'mean']
            if candidates:
                best = max(candidates, key=lambda r: (
                    -(r['metrics']['physical']+r['metrics']['wrist'])/r['metrics']['episodes'],
                    r['metrics']['AB']/r['metrics']['episodes'], sum(r['metrics']['clean_s'])))
                tail = candidates[-1]
                selection = {best['checkpoint']: best, tail['checkpoint']: tail}
                publications = []
                public = study.ROOT/'docs/2026-11-02/압현실험/동영상'
                public.mkdir(parents=True, exist_ok=True)
                names = dict(H128='긴학습구간H128', I_mix='초기자세혼합', T_arm21='엄지포함21축')
                for cp, row in selection.items():
                    condition = row['condition'].replace('_last_saved', '')
                    label = f"render_{condition}_s{row['seed']}_u{row['total']}"
                    script = 'initial_mix.py' if condition == 'I_mix' else 'runtime.py'
                    rendered = study.run(state, out, label, 'render', ['--checkpoint', cp, '--num-envs', 4], script=script)
                    for kind, view in (('hand', '손확대'), ('fullbody', '전신')):
                        source = rendered/(kind+'.mp4')
                        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(source)], text=True))
                        if float(probe['format']['duration']) <= 0:
                            raise ValueError('빈 후속 영상')
                        target = public/f"15_후속비교_{names[condition]}_seed{row['seed']}_{row['total']}회_{view}.mp4"
                        if not target.exists():
                            os.link(source, target)
                        elif study.sha(source) != study.sha(target):
                            raise ValueError('기존 영상 덮어쓰기 거부')
                        publications.append(dict(path=str(target), sha256=study.sha(target), checkpoint=cp))
                study.write(out/'videos.json', publications)
            state.update(status='complete_with_KL_failed_blocks' if state.get('protected_failures') else 'complete',
                         finished_at=study.now())
        except BaseException as error:
            state.update(status='interrupted' if isinstance(error, KeyboardInterrupt) else 'failed',
                         error=str(error), finished_at=study.now())
            raise
        finally:
            study.progress(state, out)
            study.plot(state, out)
            study.write(out/'SOURCE_AND_SCOPE.json', dict(original_source_count=len(before['source_seal']),
                original_failed_status_preserved=True, kl_guard_and_policy_unchanged=True,
                protected_failure_count=len(state.get('protected_failures', []))))


if __name__ == '__main__':
    main()
