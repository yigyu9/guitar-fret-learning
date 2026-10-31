"""원자적으로 저장된 연구·학습 상태를 읽어 진행률과 조건부 ETA를 기록한다."""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import statistics


def refresh(root):
    root = Path(root)
    state = json.loads((root/'status.json').read_text())
    document = json.loads((root/'study_results.json').read_text())
    results = document['results']
    complete = [r for r in results if r['evaluation_complete']]
    done_screen = sum(r['seed'] == 7 and not r['run_id'].startswith('combined') for r in complete)
    typical = statistics.median(r['wall_s'] for r in complete) if complete else 3900.
    run = state.get('active_run')
    mode = state.get('active_mode')
    detail = None
    fraction = 0.
    if run:
        folder = root/'runs'/run
        path = folder/'train/J/status.json' if mode == 'train' else folder/'evaluation/status.json'
        if path.exists():
            detail = json.loads(path.read_text())
            if mode == 'train' and detail.get('update_index') is not None:
                tick = detail.get('ticks') or 0
                horizon = detail.get('horizon') or 32
                fraction = min(1., (detail['update_index']+tick/horizon)/200.)*.92
            elif mode == 'evaluate':
                fraction = .92 + min(1., detail.get('elapsed_s', 0.)/(typical*.08))*.08
    now = datetime.now(timezone.utc)
    finished = state.get('phase') in ('complete', 'failed')
    if finished:
        fraction = 0.
    seconds_screen = max(0., 8-done_screen-fraction)*typical
    seconds_max = max(0., 11-len(complete)-fraction)*typical
    if document.get('selection', {}).get('phase') == 'confirming':
        seconds_max = max(0., 2-sum(r['seed'] == 17 for r in complete)-fraction)*typical
    row = dict(schema='guitar_learning.study_progress.v1', heartbeat_at=now.isoformat(),
        state=state, completed_evaluated_conditions=len(complete),
        completed_first_screen_conditions=done_screen, planned_first_screen_conditions=8,
        typical_condition_wall_s=typical, active_condition_fraction_estimate=fraction,
        active_training_status=detail,
        estimated_screen_finish_utc=None if finished else (now+timedelta(seconds=seconds_screen)).isoformat(),
        estimated_finish_if_maximum_11_conditions_utc=None if finished else (now+timedelta(seconds=seconds_max)).isoformat(),
        eta_scope='descriptive elapsed-time extrapolation; optional combination and second-seed runs depend on results',
        current_code_isolation='read-only original-SHA package mounted for research subprocesses only')
    temporary = root/'progress.tmp'
    temporary.write_text(json.dumps(row, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(root/'progress.json')
    local = timezone(timedelta(hours=9))
    def display(value):
        return '해당 없음' if value is None else datetime.fromisoformat(value).astimezone(local).strftime('%m-%d %H:%M KST')
    update = detail.get('update_index') if detail else None
    lines = ['# 연구 진행 상황', '',
        '최근 확인: '+now.astimezone(local).strftime('%m-%d %H:%M:%S KST'),
        '현재 단계: '+str(state.get('phase')), '현재 조건: '+str(run),
        '현재 반복: '+('확인 중' if update is None else str(update+1)+' / 200'),
        '평가까지 완료: '+str(len(complete))+'개 조건',
        '1차 비교 완료: '+str(done_screen)+' / 8',
        '1차 비교 종료 예상: '+display(row['estimated_screen_finish_utc']),
        '추가 조합·재확인 포함 종료 예상: '+display(row['estimated_finish_if_maximum_11_conditions_utc']),
        '', '20초마다 갱신. 종료 예상은 실측 처리속도와 조건부 후속 실험 수에 따른 추정이다.',
        '조건별 수치와 해석은 RESULTS.md를 참고한다.']
    temporary = root/'progress_md.tmp'
    temporary.write_text('\n\n'.join(lines)+'\n')
    temporary.replace(root/'progress.md')
    return row
