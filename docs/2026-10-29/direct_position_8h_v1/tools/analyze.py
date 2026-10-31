"""장시간 학습의 보상·압현·관절 추종을 CPU에서 스트리밍 집계한다."""
import argparse
from collections import Counter, defaultdict
import gzip
import json
import math
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from guitar_learning.training.training_log_io import iter_episode_rows

REWARDS = dict(song_left_approach='목표 패드 접근', song_left_contact='최초 접촉',
               song_clean_hold='압현 유지', song_left_success='압현 달성',
               song_wrong_press='오압현', song_performance_deficit='음 수행 부족',
               song_finger_standby='대기 자세', song_thumb_support='엄지 안내',
               action_change='행동 변화')


def load(path):
    return json.loads(path.read_text())


def lines(path):
    with path.open() as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def number(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Nonfinite analysis input')
    return value


def add_episode(total, episode):
    song = episode['song']
    total['episodes'] += 1
    total['achieved_notes'] += number(song['left_success_count'])
    total['target_notes'] += number(song['denominator'])
    total['episode_note_fraction_sum'] += (song['left_success_count'] / song['denominator']
                                           if song['denominator'] else 0)
    total['reward_sum'] += number(episode['reward'])
    total['timeline_complete'] += episode['reason'] == 'timeline_complete'
    total['reasons'][episode['reason']] += 1
    total['failure_reasons'].update(episode.get('failure_reasons', []))


def finish(total):
    n = total['episodes']
    return dict(total, mean_achieved_notes=total['achieved_notes'] / n,
                mean_target_notes=total['target_notes'] / n,
                note_weighted_achievement=(total['achieved_notes'] / total['target_notes']
                                           if total['target_notes'] else None),
                episode_weighted_achievement=total['episode_note_fraction_sum'] / n,
                mean_reward=total['reward_sum'] / n)


def totals():
    return dict(episodes=0, achieved_notes=0, target_notes=0, episode_note_fraction_sum=0,
                reward_sum=0, timeline_complete=0, reasons=Counter(), failure_reasons=Counter())


def add_control(acc, summary):
    names = summary['joint_names']
    n = summary['completed_physics_samples']
    for key, values in summary['values'].items():
        for i, name in enumerate(names):
            count = summary['sensor_samples'][i] if key.startswith('native_sensor') else n
            if not count:
                continue
            if key.startswith('submitted_effort') and not summary['submitted_effort_available'][i]:
                continue
            value = number(values[i])
            acc[(name, key)][0] += (value ** 2 if key.endswith('_rms') else value) * count
            acc[(name, key)][1] += count


def controls(acc):
    out = defaultdict(dict)
    for (name, key), (total, count) in acc.items():
        mean = total / count if count else None
        out[name][key] = dict(value=math.sqrt(mean) if mean is not None and key.endswith('_rms') else mean,
                              valid_physics_samples=count)
    return dict(out)


def analyze(root):
    run = root / 'train/J'
    report = load(run / 'report.json')
    # 큰 PPO 세부 진단은 즉시 버리고 그래프용 숫자만 보존한다.
    metrics = [{key: row[key] for key in ('update_index', 'transitions', 'reward_component_means')}
               for row in lines(run / 'learning_metrics.jsonl')]
    if not metrics:
        raise ValueError('No learning metrics')
    last = max(row['update_index'] for row in metrics)
    window = max(1, math.ceil(len(metrics) * 0.1))
    first_end = metrics[min(window, len(metrics)) - 1]['update_index']
    last_start = metrics[max(0, len(metrics) - window)]['update_index']
    groups = defaultdict(totals)
    acc = defaultdict(lambda: [0., 0])
    for row in iter_episode_rows(run):
        episode = row['episode']
        scope = episode['finger_skill']['scope']
        add_episode(groups[scope + '/all'], episode)
        if row['update_index'] <= first_end:
            add_episode(groups[scope + '/first10pct'], episode)
        if row['update_index'] >= last_start:
            add_episode(groups[scope + '/last10pct'], episode)
        add_control(acc, episode['finger_control_diagnostics'])
    partial = defaultdict(lambda: [0., 0])
    for summary in load(run / 'finger_control_diagnostics.json')['environments']:
        add_control(partial, summary)
    reward_windows = {}
    for label, rows in [('first10pct', metrics[:window]), ('last10pct', metrics[-window:])]:
        denom = sum(row['transitions'] for row in rows)
        reward_windows[label] = dict(transitions=denom, updates=len(rows), means={
            key: sum(number(row['reward_component_means'][key]) * row['transitions'] for row in rows) / denom
            for key in REWARDS})
    evaluations = {}
    for name in ['initial', 'middle', 'final']:
        path = root / 'evaluation' / name
        if not (path / 'report.json').exists():
            continue
        evaluation = load(path / 'report.json')
        summary = totals()
        for row in iter_episode_rows(path):
            add_episode(summary, row['episode'])
        if summary['episodes'] != evaluation['episodes']:
            raise ValueError('Evaluation episode count mismatch: ' + name)
        evaluations[name] = dict(completed=evaluation.get('completed'), failure=evaluation.get('failure'),
                                 checkpoint_sha256=evaluation['checkpoint_sha256'], scope=evaluation['scope'],
                                 summary=finish(summary) if summary['episodes'] else None)
    selection_path = root / 'evaluated_candidates.json'
    selection = load(selection_path) if selection_path.exists() else None
    if selection is not None and selection['selected']['name'] not in evaluations:
        raise ValueError('Selected checkpoint has no evaluation evidence')
    trace = dict(scope='env0 first600 control ticks across resets; not late-training evidence', samples=0)
    with gzip.open(str(run / 'finger_control_trace.jsonl.gz'), 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            trace['samples'] += 1
            trace['last_episode_local_control_tick'] = row['control_tick']
    result = dict(schema='direct_position_8h_analysis.v1', root=str(root),
                  training={key: report.get(key) for key in ['completed', 'stopped', 'failure', 'wall_s',
                            'optimizer_updates', 'updates_in_run', 'transitions', 'exposure_transitions']},
                  first_window_update_end=first_end, last_window_update_start=last_start,
                  last_update_index=last, episodes={key: finish(value) for key, value in groups.items()},
                  reward_windows=reward_windows, completed_episode_control=controls(acc),
                  closing_partial_episode_control=controls(partial), evaluations=evaluations,
                  evaluated_candidate_selection=selection, trace=trace)
    out = root / 'analysis'
    out.mkdir(exist_ok=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 3, figsize=(15, 10))
    stride = max(1, math.ceil(len(metrics) / 150))
    for ax, key in zip(axes.flat, REWARDS):
        points = []
        for start in range(0, len(metrics), stride):
            batch = metrics[start:start + stride]
            n = sum(row['transitions'] for row in batch)
            points.append((batch[-1]['update_index'] + 1,
                           sum(number(row['reward_component_means'][key]) * row['transitions'] for row in batch) / n))
        ax.plot(*zip(*points))
        ax.set(title=key, xlabel='optimizer update (1-based)', ylabel='weighted mean per control transition')
        ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(str(out / 'reward_curves.png'), dpi=150)
    plt.close(fig)
    (out / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    text = ['# 직접 목표각 장시간 학습 결과', '',
            '학습 상태: `%s`; 종료 사유: `%s`; 반복: %s; 전이: %s; 학습 시간: %.2f시간.' % (
                report['completed'], report['stopped'], report['optimizer_updates'], report['transitions'], report['wall_s'] / 3600),
            '', '## 보상 변화', '',
            '각 창은 실제 기록된 반복의 처음/마지막 10%%(각 %d회). 물리 제어 전이 수로 가중한 전이당 보상이며 에피소드 총점이 아니다. 구간/전곡 노출 혼합의 영향이 있다.' % window,
            '', '|보상|처음|마지막|', '|---|---:|---:|']
    for key, label in REWARDS.items():
        text.append('|%s|%.7g|%.7g|' % (label, reward_windows['first10pct']['means'][key], reward_windows['last10pct']['means'][key]))
    text += ['', '![보상 변화](reward_curves.png)', '', '## 압현과 종료', '',
             '실패 에피소드도 포함한다. 구간과 전곡의 평균 달성 음을 섞지 않는다. 비율은 달성 음 합계/선정 목표 음 합계이며 음향 성공률이 아닌 현재 기하·접촉 판정이다.', '',
             '|범위/기간|에피소드|평균 달성/평균 목표|음 기준 달성률|타임라인 완료|', '|---|---:|---:|---:|---:|']
    for key, value in result['episodes'].items():
        text.append('|%s|%d|%.3f/%.3f|%.3f%%|%d|' % (key, value['episodes'], value['mean_achieved_notes'],
                    value['mean_target_notes'], 100 * value['note_weighted_achievement'], value['timeline_complete']))
    text += ['', '|범위/기간|종료 사유별 횟수|실패 원인별 횟수(중복 가능)|', '|---|---|---|']
    for key, value in result['episodes'].items():
        text.append('|%s|%s|%s|' % (key, dict(value['reasons']), dict(value['failure_reasons'])))
    text += ['', '관절별 수치는 [summary.json](summary.json)에 저장했다. 관절 RMS는 표본 수로 제곱평균 후 제곱근을 취했다. 힘 센서는 관절별 유효 표본 수로 가중했다. 완료 에피소드와 종료 시 미완료 에피소드의 집계는 분리했다.',
             '', '센서는 순 일반화 힘이며 모터 힘이나 힘 제한 도달률을 뜻하지 않는다. 위치 구동 관절의 제출 토크가 미제공이면 통계에서 제외한다. 상세 추적은 대표 환경의 최초 600 제어틱까지만 있으므로 후반 학습 행동을 설명하는 자료로 사용하지 않는다.',
             '', '### 완료 에피소드 관절 추종', '',
             '|관절|요청−실제 RMS(rad)|전달−실제 RMS(rad)|속도제한 차이 RMS(rad)|속도 RMS(rad/s)|',
             '|---|---:|---:|---:|---:|']
    for name, values in result['completed_episode_control'].items():
        keys = ['requested_tracking_error_rad_rms', 'applied_tracking_error_rad_rms',
                'rate_limit_gap_rad_rms', 'velocity_rad_s_rms']
        text.append('|%s|%s|' % (name, '|'.join('%.5g' % values[key]['value'] for key in keys)))
    text += ['', '## 별도 평가', '']
    for name, evaluation in evaluations.items():
        text.append('- `%s`: %s' % (name, json.dumps(evaluation, ensure_ascii=False)))
    if not evaluations:
        text.append('별도 평가 결과 없음. 학습 중 통계를 최종 정책 성능으로 해석할 수 없다.')
    if selection is not None:
        chosen = selection['selected']
        text.append('\n영상용 선택 후보: `%s` (`%s`). 선택 규칙: %s.' % (
            chosen['name'], chosen['checkpoint'], selection['selection']))
    text += ['', '초기/중간/최종 평가가 동일한 범위와 환경 설정인지 확인한 뒤 비교해야 한다. 선택은 실제 평가한 후보들에 한정되며 전체 저장본 중 최고라는 뜻은 아니다.', '']
    (out / 'RESULTS.md').write_text('\n'.join(text))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    analyze(parser.parse_args().root.resolve())
