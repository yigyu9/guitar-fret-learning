"""진행 중인 7시간 압현 연구의 완료 평가·훈련 로그만 CPU에서 집계한다."""
import os
for variable in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[variable] = '1'
os.environ.setdefault('MPLCONFIGDIR', '/tmp/structured_press_analysis_mpl')
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parents[1]
RUNTIME = STUDY/'runtime'
sys.path.insert(0, str(RUNTIME))
from guitar_learning.training.training_log_io import iter_episode_rows
import research

TERMS = dict(song_left_approach='목표 패드 접근', song_left_contact='최초 접촉',
    song_clean_hold='압현 유지', song_left_success='압현 달성', song_wrong_press='오압현',
    song_performance_deficit='음 수행 부족', song_finger_standby='대기 자세',
    song_thumb_support='엄지 안내', action_change='행동 변화')


def read(path):
    return json.loads(Path(path).read_text())


def mean(values):
    return statistics.mean(values) if values else None


def sha(path):
    return research.digest(path)


def combine_episode_values(episodes, finger):
    """에피소드 동일 가중 평균이며 실패·정상 종료 모두 분모에 포함한다."""
    reward, costs, clean, safe_clean, streak, phase, blocked = [], [], [], [], [], [], []
    contributions = {name: [] for name in TERMS}
    cost_terms, joint_values, control_values, reasons, distributions = {}, {}, {}, {}, {}
    count, safe_success, failures, steps = 0, 0, 0, 0
    reward_residual, cost_residual, diagnostic_count = [], [], 0
    for episode in episodes:
        count += 1
        termination = episode['termination']
        failed = bool(termination['physical_failure'] or termination['wrist_failure'])
        failures += failed
        safe_success += bool(episode['song']['left_success_count'] > 0 and not failed)
        steps += episode['steps']
        values = episode['left_note_ledger']['values']
        if len(values['clean']) != 1:
            raise ValueError('only one-target diagnostic episodes are supported')
        total, best = float(values['clean'][0]), float(values['best_clean_streak'][0])
        clean.append(total); safe_clean.append(0. if failed else total); streak.append(best)
        reward.append(float(episode['reward'])); costs.append(float(episode['cost']))
        components = episode['reward_components']
        if set(components) != set(TERMS):
            raise ValueError('expected exact current nine reward terms')
        for name in TERMS:
            contributions[name].append(float(components[name]))
        reward_residual.append(abs(sum(components.values())-float(episode['reward'])))
        for name, value in episode['cost_components'].items():
            cost_terms.setdefault(name, []).append(float(value))
        cost_residual.append(abs(sum(episode['cost_components'].values())-float(episode['cost'])))
        for reason in episode.get('failure_reasons', []):
            reasons[reason] = reasons.get(reason, 0)+1
        structure = episode.get('structured_press')
        if structure:
            phase.append(structure['phase_seconds'])
            if structure['blocked_columns'] != ['wrist', 'tangent', 'height', 'normal']:
                raise ValueError('unknown blocked-seconds column order')
            blocked.append(structure['blocked_seconds'])
            key = structure['initial_distribution']
            distributions[key] = distributions.get(key, 0)+1
        motion = episode.get('left_finger_motion')
        if motion:
            diagnostic_count += 1
            names = motion['joint_names']
            for index, name in enumerate(names):
                if not name.startswith('LH:'+finger):
                    continue
                joint = joint_values.setdefault(name, {})
                for field in ('actual_range_rad', 'target_range_rad', 'actual_native_limit_fraction',
                              'target_native_limit_fraction', 'tracking_error_rms_rad'):
                    joint.setdefault(field, []).append(float(motion['values'][field][index]))
        control = episode.get('finger_control_diagnostics', {}).get('fingers', {}).get(finger, {})
        for name in ('requested_tracking_error_rad_rms', 'applied_tracking_error_rad_rms', 'rate_limit_gap_rad_rms'):
            if name in control:
                control_values.setdefault(name, []).append(float(control[name]))
    def vector_mean(rows):
        return [mean([row[i] for row in rows]) for i in range(len(rows[0]))] if rows else None
    return dict(count=count, safe_success=safe_success, failure_episodes=failures,
        complete_episode_control_transitions=steps, mean_reward=mean(reward), mean_cost=mean(costs),
        mean_reward_minus_cost=mean([a-b for a, b in zip(reward, costs)]),
        mean_clean_s=mean(clean), mean_safe_clean_s=mean(safe_clean), mean_best_clean_s=mean(streak),
        reward_components_mean={key:mean(value) for key, value in contributions.items()},
        cost_components_mean={key:mean(value) for key, value in cost_terms.items()},
        max_reward_reconciliation_error=max(reward_residual) if reward_residual else None,
        max_cost_reconciliation_error=max(cost_residual) if cost_residual else None,
        phase_seconds_mean=vector_mean(phase), blocked_seconds_mean=vector_mean(blocked),
        structured_diagnostic_episodes=len(phase), initial_distribution_counts=distributions,
        target_finger_joint_means={joint:{key:mean(value) for key, value in fields.items()}
                                  for joint, fields in joint_values.items()},
        finger_control_240hz_mean={key:mean(value) for key, value in control_values.items()},
        motion_diagnostic_episodes=diagnostic_count, failure_reasons=reasons,
        average_definition='unweighted mean across completed episodes; RMS entries are mean of per-episode per-joint RMS summaries')


def aggregate(run, finger, evaluation=False):
    run = Path(run)
    report = read(run/'report.json')
    if not report['completed']:
        raise ValueError('incomplete run cannot enter completed aggregates: '+str(run))
    if evaluation:
        rows = list(iter_episode_rows(run))
        research.summarize_episodes(report, rows)
        values = combine_episode_values((row['episode'] for row in rows), finger)
    else:
        values = combine_episode_values((row['episode'] for row in iter_episode_rows(run)), finger)
    values.update(path=str(run), policy='deterministic fixed checkpoint' if evaluation else 'stochastic evolving PPO policy',
        sampling_scope='first episode from each of 32 environments' if evaluation else 'completed episodes in this training block only; unfinished rollouts excluded',
        report_sha256=sha(run/'report.json'), episodes_sha256=sha(run/'episodes.jsonl'),
        episode_metadata_sha256=sha(run/'episode_metadata.json') if (run/'episode_metadata.json').is_file() else None,
        seed=report.get('settings', {}).get('seed'),
        report_cumulative_training_transitions=report.get('training_transitions'),
        requested_run_updates=report.get('requested_run_updates'),
        planned_block_transitions=(report['settings']['num_envs']*report['settings']['horizon']*
                                   report['requested_run_updates']) if not evaluation else None)
    return values


def collect():
    catalog = read(RUNTIME/'guitar_learning/assets/structured_press_v2/catalog.json')
    goals = {goal['finger']:dict(song=goal['song'], physical_string=goal['physical_string'],
                               fret=goal['fret']) for goal in catalog['goals']}
    result = dict(schema='structured_press.seven_hour_analysis.v1',
        updated_utc=datetime.now(timezone.utc).isoformat(), stages=[], errors=[], goals=goals,
        budget=read(ROOT/'budget.json'), reward_labels=TERMS,
        scope='current seven_hour_v1 immediate stage summaries; historical runs excluded except explicit index reproduction',
        transition_definition='64 environments * 32 control ticks * 100 updates = 204800 sampled control transitions per block; physics 240Hz/control 60Hz')
    for path in sorted(ROOT.glob('*/summary.json')):
        summary = read(path)
        if summary.get('schema') != 'structured_press.seven_hour_stage.v1':
            continue
        stage = dict(label=path.parent.name, finger=summary['finger'], stage=summary['stage'],
            seed=summary['seed'], status=summary['status'], passed=summary['passed'],
            source=summary['source'], goal=goals[summary['finger']], rows=[], selected=None,
            evaluation_condition='free v9, unassisted' if summary['stage'].startswith('C') or summary['stage'] == 'free_v9' else 'supported '+summary['stage'],
            summary_sha256=sha(path), completed_updates=summary['completed_updates'])
        source = summary['source']
        if source:
            stage['source_sha_unchanged'] = Path(source['path']).is_file() and sha(source['path']) == source['sha256']
        result['stages'].append(stage)
        for role, rows in (('initial', [summary['initial']] if summary.get('initial') else []), ('block', summary['blocks'])):
            for row in rows:
                try:
                    evaluation = Path(row['evaluation'])
                    for name, expected in row['evaluation_sha256'].items():
                        if sha(evaluation/name) != expected:
                            raise ValueError('evaluation artifact changed: '+str(evaluation/name))
                    if sha(row['checkpoint']) != row['checkpoint_sha256']:
                        raise ValueError('checkpoint changed')
                    item = dict(role=role, updates=row['updates'], checkpoint=row['checkpoint'],
                        accepted=row['accepted'], evaluation=aggregate(evaluation, stage['finger'], True))
                    if role == 'block':
                        item['training'] = aggregate(Path(row['checkpoint']).parent.parent/'J', stage['finger'])
                        # J/report contains raw episodes but settings/transition counts belong to its parent report.
                        train_report = read(Path(row['checkpoint']).parent.parent/'report.json')
                        item['training']['planned_block_transitions'] = (train_report['settings']['num_envs']*
                            train_report['settings']['horizon']*train_report['requested_run_updates'])
                        item['training']['report_cumulative_training_transitions'] = train_report['training_transitions']
                    stage['rows'].append(item)
                    if summary.get('best') and summary['best']['checkpoint'] == row['checkpoint']:
                        stage['selected'] = item
                except (OSError, ValueError, KeyError) as error:
                    result['errors'].append(dict(label=stage['label'], role=role,
                        updates=row['updates'], message=type(error).__name__+': '+str(error)))
    reference = ROOT/'reproduce_index_100'
    if (reference/'report.json').is_file():
        try:
            result['index_reproduction'] = aggregate(reference, 'index', True)
        except (OSError, ValueError, KeyError) as error:
            result['errors'].append(dict(label='reproduce_index_100', message=str(error)))
    terminal = ('passed', 'max_updates_reached_without_two_passes', 'budget_stopped', 'error',
                'completed_comparison_not_stage_promotion')
    result['research_running'] = any(stage['status'] not in terminal for stage in result['stages'])
    if (ROOT/'progress.json').is_file():
        result['orchestrator_progress'] = read(ROOT/'progress.json')
        state = str(result['orchestrator_progress'].get('status', ''))
        result['research_running'] |= state.startswith(('running', 'preparing'))
    result['total_completed_new_block_planned_transitions'] = sum(
        row['training']['planned_block_transitions'] for stage in result['stages']
        for row in stage['rows'] if row['role'] == 'block')
    return result


def graphs(result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    groups = [('A', lambda s:s == 'A'), ('B', lambda s:s == 'B'),
              ('Unassisted C / fresh full33', lambda s:s.startswith('C') or s == 'free_v9')]
    fig, axes = plt.subplots(3, 2, figsize=(12, 12), constrained_layout=True)
    for index, (name, match) in enumerate(groups):
        any_rows = False
        for stage in result['stages']:
            if not match(stage['stage']) or not stage['rows']:
                continue
            rows = sorted(stage['rows'], key=lambda row:row['updates'])
            label = '{} {} seed{}'.format(stage['finger'], stage['stage'], stage['seed'])
            updates = [row['updates'] for row in rows]
            axes[index, 0].plot(updates, [row['evaluation']['safe_success']/32 for row in rows], 'o-', label=label)
            axes[index, 1].plot(updates, [row['evaluation']['mean_safe_clean_s'] for row in rows], 'o-', label=label)
            any_rows = True
        for column, ylabel in ((0, 'Safe success / 32'), (1, 'Mean clean seconds (failure = 0)')):
            axis = axes[index, column]
            axis.set(title=name, xlabel='Stage-local PPO updates (0 = initial)', ylabel=ylabel)
            axis.grid(alpha=.25)
            if any_rows: axis.legend(fontsize=8)
            else: axis.text(.5, .5, 'No completed evaluation yet', transform=axis.transAxes, ha='center')
        axes[index, 0].set_ylim(-.03, 1.03)
    fig.savefig(ROOT/'progress_chart.png', dpi=150); plt.close(fig)
    selected = [stage for stage in result['stages'] if stage['selected']]
    fig, axis = plt.subplots(figsize=(12, max(4, len(selected)*.7)), constrained_layout=True)
    if selected:
        positives, negatives = [0.]*len(selected), [0.]*len(selected)
        for key in list(TERMS)+['failure_cost']:
            values = [(-stage['selected']['evaluation']['mean_cost'] if key == 'failure_cost' else
                stage['selected']['evaluation']['reward_components_mean'][key]) for stage in selected]
            starts = [positives[i] if value >= 0 else negatives[i] for i, value in enumerate(values)]
            axis.barh(range(len(selected)), values, left=starts, label=key)
            for index, value in enumerate(values):
                if value >= 0: positives[index] += value
                else: negatives[index] += value
        axis.set_yticks(range(len(selected)))
        axis.set_yticklabels([stage['label']+' @'+str(stage['selected']['updates']) for stage in selected])
        axis.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=8)
    else:
        axis.text(.5, .5, 'No selected evaluated policy yet', transform=axis.transAxes, ha='center')
    axis.axvline(0, color='black', linewidth=.7)
    axis.set(xlabel='Mean completed-episode reward contribution; cost plotted negative',
             title='Selected deterministic policies: nine reward terms and failure cost')
    fig.savefig(ROOT/'reward_chart.png', dpi=150); plt.close(fig)


def document(result):
    lines = ['# 7시간 압현 연구 집계', '', '갱신 UTC: '+result['updated_utc'], '',
        '연구 상태: '+('진행 중. 아래 수치는 완료된 블록만 포함한다.' if result['research_running'] else '현재 기록된 단계 상태를 기준으로 집계했다.'), '',
        '손가락마다 목표 줄·프렛이 다르므로 손가락 자체의 난이도 차이로 해석하면 안 된다. '
        'A/B는 정렬·지원 조건 평가이고 C는 도움 없는 원래 v9 평가다. 두 분포의 성공률을 합산하지 않는다.', '',
        'large·64환경·H32·정책60Hz·물리240Hz. 블록당100회는204,800개 제어 전이이다. '
        '초기 평가(0회), 이전 단계 source, 갱신 모델 평가를 구분한다. seed는 아래 표에 표시한다. '
        '고정 정책 평가는 환경별 첫 에피소드32개이며 실패도 분모에 포함한다.', '',
        '|실험|목표(줄/프렛)|조건|seed|역할/갱신|안전 달성|실패|clean 평균, 실패0점(s)|상태|',
        '|---|---|---|--:|---|--:|--:|--:|---|']
    for stage in result['stages']:
        goal = stage['goal']
        if not stage['rows']:
            lines.append('|{}|{}/{}|{}|{}|미완료|—|—|—|{}|'.format(stage['label'], goal['physical_string'], goal['fret'],
                stage['evaluation_condition'], stage['seed'], stage['status']))
        for row in stage['rows']:
            e = row['evaluation']
            lines.append('|{}|{}/{}|{}|{}|{} / {}|{}/32|{}|{:.4f}|{}|'.format(stage['label'],
                goal['physical_string'], goal['fret'], stage['evaluation_condition'], stage['seed'],
                row['role'], row['updates'], e['safe_success'], e['failure_episodes'], e['mean_safe_clean_s'], stage['status']))
        if stage['source']:
            lines += ['', '이전 단계 source (`'+stage['label']+'`): `'+stage['source']['path']+
                '` (SHA 유지: '+str(stage['source_sha_unchanged'])+'). source의 과거 점수는 이번 초기 평가와 동일시하지 않는다.', '']
    reference = result.get('index_reproduction')
    if reference:
        lines += ['', '기존 검지 A100 재현 확인: 안전 달성 {}/32, 실패 {}, clean 평균(실패0점) {:.4f}초. '
                  '이번 신규 단계 학습과 별도 기록이다.'.format(reference['safe_success'], reference['failure_episodes'], reference['mean_safe_clean_s'])]
    lines += ['', '![진행 비교](progress_chart.png)', '', '![보상 비교](reward_chart.png)', '',
        '## 선택 모델의 보상과 제어', '',
        '선택 순서는 안전 달성 → 실패를0점 처리한 clean 평균 → 실패가 적음 → 최신이다. '
        '아래 보상은 선택 모델의 결정적 평가 에피소드 평균이다. 실패 비용은 보상9항과 별도이며 비용 가중치는1이다.']
    for stage in result['stages']:
        if not stage['selected']:
            continue
        row = stage['selected']; e = row['evaluation']
        lines += ['', '### '+stage['label'], '', '선택: `'+row['checkpoint']+'` ('+row['role']+', '+str(row['updates'])+'회)', '',
                  '|보상항|에피소드 평균|', '|---|--:|']
        for name, label in TERMS.items():
            lines.append('|{}|{:.6f}|'.format(label, e['reward_components_mean'][name]))
        lines += ['|실패 비용(별도)|{:.6f}|'.format(e['mean_cost']),
            '|보상 합계|{:.6f}|'.format(e['mean_reward']), '|보상−비용|{:.6f}|'.format(e['mean_reward_minus_cost']), '',
            '비용 세부: `'+json.dumps(e['cost_components_mean'], ensure_ascii=False)+'`.']
        if e['phase_seconds_mean']:
            lines += ['', '단계 체류 평균(손목 이동 / 정렬 / 압현): '+str([round(v, 4) for v in e['phase_seconds_mean']])+'초. '
                '진입 차단 평균(손목 / 접선 / 높이 / 법선): '+str([round(v, 4) for v in e['blocked_seconds_mean']])+''
                '초. 차단 항목은 서로 겹칠 수 있으며 압현 단계 유지 이후에도 readiness 위반 시간이 기록될 수 있다.']
        lines += ['', '|목표 손가락 관절|실제 범위 평균(°)|제어 목표 범위 평균(°)|실제 한계 체류(%)|목표 한계 체류(%)|추종 RMS 평균(°)|',
            '|---|--:|--:|--:|--:|--:|']
        for joint, values in e['target_finger_joint_means'].items():
            lines.append('|{}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|{:.3f}|'.format(joint,
                math.degrees(values['actual_range_rad']), math.degrees(values['target_range_rad']),
                100*values['actual_native_limit_fraction'], 100*values['target_native_limit_fraction'],
                math.degrees(values['tracking_error_rms_rad'])))
        lines += ['', '위 범위·한계·추종은60Hz 에피소드 요약의 동일 가중 평균이다. '
            '제어 목표 범위는 속도 제한을 거친 target이며 원요청 범위와 동일시하지 않는다. '
            '240Hz 원요청/적용 추종 및 속도 제한 gap RMS의 손가락 평균: `'+
            json.dumps(e['finger_control_240hz_mean'], ensure_ascii=False)+'` (rad). '
            'RMS는 관절별 RMS의 산술 평균을 다시 에피소드 평균한 값이다. native position-drive의 제출 토크0을 힘 부족으로 해석하지 않는다.']
        training = row.get('training')
        if training:
            lines += ['', '해당 학습 블록의 확률적 정책 완료 에피소드: {}회, 안전 달성 {}회, 실패 {}회. '
                '완료 에피소드에 속한 제어 전이 {}개 / 계획 블록 전이 {}개. '
                '미종료 rollout은 에피소드 평균에서 제외하며, 학습 중 변하는 정책이므로 고정 모델 평가 성공률과 직접 혼합하지 않는다.'.format(
                    training['count'], training['safe_success'], training['failure_episodes'],
                    training['complete_episode_control_transitions'], training['planned_block_transitions'])]
    lines += ['', '## 해석 범위', '',
        '접촉 성공은 현재 기하·합력 기반 후보 판정이다. 실제 현 압력이나 음향 성공, 자연스러움, 장기 수렴을 인증하지 않는다. '
        '훈련과 결정적 평가, A/B 지원 조건과 C 자유 조건, seed별 결과는 각각 구분한다. '
        '원시 보상9항·비용 세부·추종·단계 체류·완료 블록 전이 예산은 all_results.json에 기록했다.']
    if result['errors']:
        lines += ['', '집계에서 제외된 오류: `'+json.dumps(result['errors'], ensure_ascii=False)+'`']
    (ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def main():
    result = collect()
    research.write(ROOT/'all_results.json', result)
    graphs(result)
    document(result)
    print(json.dumps(dict(stages=len(result['stages']), running=result['research_running'], errors=result['errors']), ensure_ascii=False))


if __name__ == '__main__':
    main()
