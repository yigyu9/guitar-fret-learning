"""완료된 원문 평가와 학습 로그를 읽어 야간 비교표와 그림을 갱신한다."""
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/complex-night-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

STUDY = Path(__file__).resolve().parents[1]
PREVIOUS = STUDY.parent / '복합압현_단계별실험_v1'


def read(path):
    return json.loads(path.read_text())


def journal(path):
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def analyze():
    """운영 원장은 수정하지 않으며, 성공하지 않은 목표도 분모에 남긴다."""
    out = STUDY / '분석'
    out.mkdir(exist_ok=True)
    records = []
    training = []
    states = {}
    for label, folder in (('기본', PREVIOUS), ('야간', STUDY)):
        path = folder / '진행상황.json'
        if not path.is_file():
            continue
        state = read(path)
        states[label] = state
        for task, item in state.get('tasks', {}).items():
            if item.get('action') != 'train' or not item.get('completed'):
                continue
            run = Path(item['out']) / 'J'
            metrics = journal(run / 'learning_metrics.jsonl')
            episodes = [r['episode'] for r in journal(run / 'episodes.jsonl')]
            if not metrics or not episodes:
                continue
            values = [e['left_note_ledger']['values'] for e in episodes]
            count = len(values[0]['clean'])
            first_lr = metrics[0]['actor_lr']
            drops = [i + 1 for i, r in enumerate(metrics) if r['actor_lr'] < first_lr]
            training.append(dict(
                study=label, task=task, updates=len(metrics), episodes=len(episodes),
                contact_episodes_by_target=[sum(v['contact_time'][i] > 0 for v in values) for i in range(count)],
                first_contact_completed_by_target=[sum(v['contact_done'][i] for v in values) for i in range(count)],
                achieved_episodes_by_target=[sum(v['left'][i] for v in values) for i in range(count)],
                clean_seconds_by_target=[sum(v['clean'][i] for v in values) for i in range(count)],
                best_streak_by_target_s=[max(v['best_clean_streak'][i] for v in values) for i in range(count)],
                first_actor_lr=first_lr, last_actor_lr=metrics[-1]['actor_lr'],
                first_lr_drop_in_this_run=drops[0] if drops else None,
                physical=sum(e['termination']['physical_failure'] for e in episodes),
                wrist=sum(e['termination']['wrist_failure'] for e in episodes), source=str(run)))
        for name, case in state.get('cases', {}).items():
            for update, entry in case.get('evaluations', {}).items():
                result = entry['result']
                records.append(dict(
                    study=label, case=name, update=int(update),
                    safe_success=result['safe_success'], denominator=result['denominator'],
                    target_clean_fractions=result['clean_fraction_by_target'],
                    target_streaks_s=result['mean_best_streak_by_target_s'],
                    wrong_ratio=result['wrong_target_time_ratio'],
                    strict_timing=result['strict_timing_pass'],
                    tail_release=result['terminal_release_pass'],
                    physical=result['physical'], wrist=result['wrist'],
                    passed=result['passed'], source=entry['out'],
                    selected=entry == case.get('selected')))
    payload = dict(updated_at=datetime.now(timezone.utc).isoformat(),
                   scope='같은 정렬 입력의 평균정책16환경; 독립 학습16시드 또는 자유 곡 연주 결과가 아님',
                   states={k: {f: s.get(f) for f in ('status', 'current_task', 'completed', 'failure')}
                           for k, s in states.items()}, evaluations=records, training=training)
    (out / '비교수치.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    if records:
        with (out / '비교수치.csv').open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        selected = [r for r in records if r['selected']]
        if selected:
            fig, axes = plt.subplots(2, 1, figsize=(max(10, len(selected) * .8), 7), layout='constrained')
            labels = [('base:' if r['study'] == '기본' else 'night:') + r['case'] for r in selected]
            axes[0].bar(labels, [r['safe_success'] / r['denominator'] for r in selected], label='All-note safe success')
            axes[0].plot(labels, [min(r['target_clean_fractions']) for r in selected], 'o-', color='#d07600', label='Worst target clean fraction')
            axes[0].set(ylim=(0, 1.08), ylabel='Fraction', title='Selected mean-policy evaluations (16 repeated environments)')
            axes[0].legend()
            axes[1].bar(labels, [r['wrong_ratio'] for r in selected], label='Wrong press / active-time union')
            axes[1].plot(labels, [r['strict_timing'] / r['denominator'] for r in selected], 'o-', color='#268463', label='Strict timing incl. final release')
            axes[1].set(ylim=(0, 1.08), ylabel='Fraction')
            axes[1].legend()
            for ax in axes:
                ax.tick_params(axis='x', labelrotation=55)
                ax.grid(axis='y', alpha=.2)
            fig.savefig(out / '평가비교.png', dpi=150)
            plt.close(fig)
    lines = ['# 야간 실험 비교 분석', '', '갱신: ' + payload['updated_at'], '', payload['scope'], '',
             '각 평가의 목표별 유지율·최장 연속 유지·전체 달성·오압현·엄격 시각을 따로 기록한다. 접촉하지 않은 음의 최종 해제 통과만으로 전환 성공을 판정하지 않는다.', '',
             '| 연구/조건 | 반복 | 전체 안전 달성 | 목표별 유지율 | 오압현 | 엄격 시각 | 물리/손목 실패 |',
             '| --- | ---: | ---: | --- | ---: | ---: | --- |']
    for r in records:
        lines.append('| ' + r['study'] + '/' + r['case'] + ' | ' + str(r['update']) +
                     (' 선택' if r['selected'] else '') + ' | ' + str(r['safe_success']) + '/16 | ' +
                     ', '.join(f'{v:.1%}' for v in r['target_clean_fractions']) + ' | ' +
                     f"{r['wrong_ratio']:.1%} | {r['strict_timing']}/16 | {r['physical']}/{r['wrist']} |")
    lines += ['', '## 확률적 학습 중 탐색과 학습률', '',
              '아래는 완료된 학습 실행의 원시 에피소드 합계다. 접촉 에피소드는 contact_time이 양수인 경우이며 최초 접촉 보상 완료 플래그와 구분한다. 재개 100회는 별도 행이며 최초 100회와 중복하지 않는다. 환경이 많은 조건이나 음 길이가 다른 조건의 누적 접촉 시간을 그대로 성능 순위로 비교하지 않는다.', '',
              '| 연구/실행 | 에피소드 | 목표별 접촉 에피소드 | 목표별 달성 | 목표별 최대 연속 유지(초) | 시작→마지막 학습률 | 실행 내 첫 하락 | 물리/손목 실패 |',
              '| --- | ---: | --- | --- | --- | --- | --- | --- |']
    for r in training:
        lines.append(f"| {r['study']}/{r['task']} | {r['episodes']} | " +
                     ', '.join(map(str, r['contact_episodes_by_target'])) + ' | ' +
                     ', '.join(map(str, r['achieved_episodes_by_target'])) + ' | ' +
                     ', '.join(f'{v:.3f}' for v in r['best_streak_by_target_s']) +
                     f" | {r['first_actor_lr']:.2g}→{r['last_actor_lr']:.2g} | " +
                     str(r['first_lr_drop_in_this_run']) + f" | {r['physical']}/{r['wrist']} |")
    lines += ['', '## 실행 상태와 보류 조건', '']
    for label, state in states.items():
        lines.append(f"- {label}: {state.get('status')}, 현재 {state.get('current_task')}, 오류 {state.get('failure')}")
        for name, case in state.get('cases', {}).items():
            if case.get('finished') and not case.get('selected'):
                lines.append(f"  - {name}: {case.get('status')}; {case.get('reason', case.get('blocked_by', '원장 참조'))}")
    lines += ['', '## 해석 범위', '',
              'native 참조 재생은 동일 과제에서 유한한 실제 제어로 압현 가능한지 확인하는 대조군이다. 학습 정책의 정답으로 주입하지 않는다. CPU 기하 탐색 실패나 참조 재생 실패만으로 물리적으로 불가능하다고 결론 내리지 않는다.', '',
              '팔 탐색 비교는 같은 입력·seed·모델 크기·학습 횟수에서 팔 초기 std만 바꾸는 비교다. 학습 중 우연한 접촉과 평가 평균정책의 성공을 구분한다. 결과가 없거나 모두 전환 실패라면 개선이 입증됐다고 보고하지 않는다.', '',
              '성공 여부는 기하 패드와 강체 순접촉력 기반 판정이다. 실제 줄별 힘이나 음향 품질을 보증하지 않는다. 정렬된 출발점의 조건부 실험이므로 임의 초기 자세·전곡 연주 성과로 일반화하지 않는다.']
    (out / '결과분석.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(dict(evaluations=len(records), analysis=str(out)), ensure_ascii=False))


if __name__ == '__main__':
    analyze()
