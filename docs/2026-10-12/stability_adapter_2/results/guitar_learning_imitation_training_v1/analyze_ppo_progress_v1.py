"""Read-only bounded PPO evidence summary; live outputs are explicitly provisional."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics


def norm(values):
    return math.sqrt(sum(float(value)**2 for value in values))


def mean(values):
    return sum(values)/len(values) if values else None


def maximum(values):
    return max(values) if values else None


def json_file(path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        # Live write() creates the exclusive file before completing its JSON.
        return None


def json_lines(path, compressed=False):
    """Return complete records even while gzip has not received its final trailer."""
    records = []
    incomplete = None
    if not path.is_file():
        return records, 'missing'
    try:
        with (gzip.open(path, 'rt') if compressed else path.open()) as stream:
            for line in stream:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    incomplete = 'incomplete JSON record'
                    break
    except (EOFError, gzip.BadGzipFile, OSError) as error:
        incomplete = type(error).__name__+': '+str(error)
    return records, incomplete


def episode_summary(info, worker, tick, committed):
    episode = info['episode']
    specialist = episode.get('specialist', info.get('specialist', {}))
    skill = specialist.get('skill', {})
    return dict(worker_id=worker, log_control_tick=tick, optimizer_committed=committed,
        valid=episode.get('valid'), reason=episode.get('reason', info.get('termination_reason')),
        reward=episode.get('reward'), cost=episode.get('cost'), steps=episode.get('steps'),
        success=bool(specialist.get('stage_success')),
        safety_invalidated=bool(specialist.get('safety_invalidated')),
        safety_reasons=specialist.get('safety_reasons', []),
        first_success_s=skill.get('first_success_s'),
        longest_dwell_s=maximum(list(skill.get('longest_dwell_s', {}).values())),
        candidate_valid_s=sum(skill.get('candidate_valid_s', {}).values()),
        geometric_crossings=skill.get('geometric_crossings', 0),
        matching_crossings=skill.get('matching_crossings', 0),
        duplicate_crossings=skill.get('duplicate_crossings', 0),
        left_contact_targets=skill.get('contact_targets', []),
        held_targets=skill.get('held_targets', []),
        crossed_targets=skill.get('crossed_targets', []),
        music=episode.get('music', info.get('music', {})))


def summarize_episodes(episodes):
    dwell = [row['longest_dwell_s'] for row in episodes if row['longest_dwell_s'] is not None]
    return dict(count=len(episodes), successes=sum(row['success'] for row in episodes),
        success_fraction=mean([float(row['success']) for row in episodes]),
        physical_failures=sum(row['reason'] == 'terminal_failure' for row in episodes),
        safety_invalidated=sum(row['safety_invalidated'] for row in episodes),
        reasons=dict(Counter(row['reason'] for row in episodes)),
        mean_reward=mean([row['reward'] for row in episodes if row['reward'] is not None]),
        mean_cost=mean([row['cost'] for row in episodes if row['cost'] is not None]),
        longest_dwell_s=maximum([row['longest_dwell_s'] for row in episodes
                                if row['longest_dwell_s'] is not None]),
        longest_dwell_distribution_s=dict(count=len(dwell), minimum=min(dwell) if dwell else None,
            median=statistics.median(dwell) if dwell else None, mean=mean(dwell),
            population_std=statistics.pstdev(dwell) if dwell else None, maximum=maximum(dwell)),
        candidate_valid_total_s=sum(row['candidate_valid_s'] for row in episodes),
        geometric_crossings=sum(row['geometric_crossings'] for row in episodes),
        matching_crossings=sum(row['matching_crossings'] for row in episodes),
        music_matched50=sum(row['music'].get('matched50', 0) for row in episodes),
        music_matched100=sum(row['music'].get('matched100', 0) for row in episodes),
        music_held_total_s=sum(row['music'].get('held_total_s', 0.) for row in episodes),
        music_missed_strict=sum(row['music'].get('missed_strict', 0) for row in episodes),
        music_wrong_crossings=sum(row['music'].get('wrong_crossings', 0) for row in episodes))


def summarize(folder):
    settings = json_file(folder/'settings.json')
    report = json_file(folder/'report.json')
    status = json_file(folder/'status.json')
    bc_report_path = folder.parent/(folder.name.split('_')[0]+'_bc_v1')/'report.json'
    bc_report = json_file(bc_report_path)
    lifecycle_paths = sorted(folder.glob('worker_*/environment/persistent_lifecycle.json'))
    lifecycles = [json_file(path) for path in lifecycle_paths]
    updates = ([value for path in sorted(folder.glob('update_*.json'))
                if (value := json_file(path)) is not None]
               if report is None else report['updates'])
    horizon = settings['horizon']
    committed_ticks = len(updates)*horizon
    rows, transition_error = json_lines(folder/'transitions.jsonl.gz', True)
    resources, resource_error = json_lines(folder/'resources.jsonl')
    episodes, guitar, feet, rotations, speeds = [], [], [], [], []
    flags_count = Counter()
    reason_count = Counter()
    terms = defaultdict(float)
    per_update = []
    for index, update in enumerate(updates):
        per_update.append(dict(update=index+1, analytic_kl=update['analytic_kl'],
            max_attempted_kl=update['max_attempted_kl'], kl_retries=update['kl_retries'],
            actor_lr=update['actor_lr'], actor_loss=update['actor_loss'],
            reward_value_loss=update['reward_value_loss'], cost_value_loss=update['cost_value_loss'],
            collection_s=update['collection_s'], update_s=update['update_s'],
            transitions=update['transitions'], episodes=[], guitar_max_mm=0.))
    for tick, row in enumerate(rows):
        committed = tick < committed_ticks
        for worker, info in enumerate(row['infos']):
            if 'episode' in info:
                episode = episode_summary(info, worker, tick, committed)
                episodes.append(episode)
                if committed:
                    per_update[tick//horizon]['episodes'].append(episode)
            if not committed:
                continue
            for key, value in info.get('reward_terms', {}).items(): terms[key] += value
            reason_count.update(info.get('failure_reasons', []))
            safety = info.get('stability', {})
            if safety:
                displacement = norm(safety['guitar_delta_m'])
                guitar.append(displacement)
                feet.append(max(norm(v) for v in safety['foot_delta_m']))
                rotations.append(norm(safety['guitar_rotation_vector_rad']))
                speeds.append(safety['max_joint_speed_rad_s'])
                flags = safety['flags']
                flags_count['samples'] += 1
                flags_count['any_main_support'] += any(flags[:3])
                flags_count['triple_support'] += all(flags[:3])
                flags_count['chest'] += bool(flags[0])
                flags_count['right_upper_arm'] += bool(flags[1])
                flags_count['thigh'] += bool(flags[2])
                flags_count['both_feet'] += all(flags[-2:])
                flags_count['left_foot'] += bool(flags[-2])
                flags_count['right_foot'] += bool(flags[-1])
                flags_count['target_fret_candidate'] += any(info.get('fret_candidates', {}).values())
                per_update[tick//horizon]['guitar_max_mm'] = max(
                    per_update[tick//horizon]['guitar_max_mm'], displacement*1000)
    for update in per_update:
        update['episode_summary'] = summarize_episodes(update.pop('episodes'))
    committed_episodes = [episode for episode in episodes if episode['optimizer_committed']]
    expected_transitions = sum(update['transitions'] for update in updates)
    logged_transitions = sum(len(row['infos']) for row in rows)
    sample_count = flags_count['samples']
    consistent = (len(rows) >= committed_ticks and expected_transitions == sample_count and
        (report is None or report['transitions'] == expected_transitions))
    memory_values = [row['available_memory_bytes'] for row in resources
                     if row.get('available_memory_bytes') is not None]
    source_paths = [folder/'settings.json', folder/'transitions.jsonl.gz', folder/'resources.jsonl']
    source_paths += sorted(folder.glob('update_*.json'))
    if report is not None: source_paths.append(folder/'report.json')
    source_paths += lifecycle_paths
    if (folder/'persistent_audit.json').is_file(): source_paths.append(folder/'persistent_audit.json')
    if bc_report is not None: source_paths.append(bc_report_path)
    sources = []
    for path in source_paths:
        before = path.stat()
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if report is not None else None
        after = path.stat()
        sources.append(dict(path=str(path.resolve()), bytes=after.st_size, sha256=digest,
            stable_during_hash=before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns))
    first_ticks = min(len(updates), 4)*horizon
    last_start_tick = max(len(updates)-4, 0)*horizon
    first = [row for row in committed_episodes if row['log_control_tick'] < first_ticks]
    last = [row for row in committed_episodes if row['log_control_tick'] >= last_start_tick]
    actual_physics_steps = (sum(round(row['native_sim_time_s']*240) for row in lifecycles)
        if lifecycles and all(row is not None for row in lifecycles) else None)
    return dict(role=settings['specialist']['role'], skill=settings['skill'],
        provisional=report is None, report_completed=report.get('completed') if report else None,
        stopped=report.get('stopped') if report else 'running',
        failure=report.get('failure') if report else None,
        updates_committed=len(updates), updates_requested=settings['updates'],
        committed_transitions=expected_transitions, logged_transitions=logged_transitions,
        uncommitted_logged_transitions=logged_transitions-sample_count,
        accounting_consistent=consistent, transition_stream_error=transition_error,
        resource_stream_error=resource_error, settings=settings,
        wall_s=report.get('wall_s') if report else status.get('elapsed_s') if status else None,
        max_wall_seconds=settings['max_wall_seconds'], status_phase=status.get('phase') if status else None,
        committed_episode_summary=summarize_episodes(committed_episodes),
        all_logged_episode_summary=summarize_episodes(episodes), episodes=episodes,
        training_window_comparison=dict(first_up_to4_updates=summarize_episodes(first),
            last_up_to4_updates=summarize_episodes(last),
            scope='stochastic training windows; no controlled improvement or generalization claim'),
        bc_training_fit=({key: bc_report['fit'][key] for key in
            ('steps', 'initial_training_mse', 'training_mse', 'max_abs_error', 'converged', 'tolerance')}
            if bc_report is not None else None),
        physics_accounting=dict(measured_task_steps240=sample_count*4,
            actual_steps240_from_native_clock=actual_physics_steps,
            preparation_steps240=actual_physics_steps-sample_count*4 if actual_physics_steps is not None else None,
            native_clock_scope='sum of rounded native simulator times; no scene recreation; task+all completed preparations',
            lifecycle_scene_creations=sum(row['native_calls']['create_sim'] for row in lifecycles if row is not None),
            lifecycle_scene_destructions=sum(row['native_calls']['destroy_sim'] for row in lifecycles if row is not None),
            episode_initializations=sum(row['episode_index']+1 for row in lifecycles if row is not None)),
        final_audit_checks=({key: report.get(key) for key in ('changed_inputs', 'guard_violations',
            'worker_failures', 'physical_flags_errors', 'cleanup_errors', 'persistent_audit')}
            if report is not None else None),
        reward_terms_committed=dict(terms), failure_reason_ticks_committed=dict(reason_count),
        endpoint_safety_60Hz=dict(samples=sample_count,
            fractions={key: value/sample_count for key, value in flags_count.items()
                       if key != 'samples'} if sample_count else {},
            guitar_displacement_max_m=maximum(guitar), guitar_rotation_max_rad=maximum(rotations),
            foot_displacement_max_m=maximum(feet), joint_speed_max_rad_s=maximum(speeds)),
        optimization=dict(kl_max=maximum([row['analytic_kl'] for row in updates]),
            attempted_kl_max=maximum([row['max_attempted_kl'] for row in updates]),
            retries=sum(row['kl_retries'] for row in updates), target_kl=settings['ppo']['target_kl'],
            actor_lr_last=updates[-1]['actor_lr'] if updates else None),
        resource_summary=dict(min_available_memory_gib=min(memory_values)/2**30 if memory_values else None,
            parent_rss_max_gib=maximum([row['parent_memory']['rss_current_bytes']/2**30
                for row in resources if row.get('parent_memory', {}).get('rss_current_bytes') is not None]),
            process_sum_pss_max_gib=maximum([
                (row.get('parent_memory', {}).get('pss_current_bytes', 0) or 0)/2**30+
                sum((worker.get('memory', {}).get('pss_current_bytes', 0) or 0)/2**30
                    for worker in row.get('workers', [])) for row in resources])),
        resource_series=[dict(elapsed_s=row['elapsed_s'], available_gib=row['available_memory_bytes']/2**30)
                         for row in resources if row.get('available_memory_bytes') is not None],
        updates=per_update, sources=sources,
        promotion='not decided here; separate deterministic native checkpoint evaluation required')


def save_plot(document, destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 2, figsize=(12, 10), constrained_layout=True)
    for role, result in document['runs'].items():
        color = '#1769aa' if role == 'left' else '#e87618'
        updates = result['updates']
        x = [row['update'] for row in updates]
        axes[0, 0].plot(x, [100*(row['episode_summary']['success_fraction'] or 0.)
            for row in updates], '.-', label=role, color=color)
        axes[0, 1].plot(x, [row['episode_summary']['mean_reward'] for row in updates],
                        '.-', label=role, color=color)
        axes[1, 0].plot(x, [row['guitar_max_mm'] for row in updates], '.-', label=role, color=color)
        axes[1, 1].plot(x, [row['analytic_kl'] for row in updates], '.-', label=role, color=color)
        episodes = [row for row in result['episodes'] if row['optimizer_committed']]
        for index, episode in enumerate(episodes):
            if role == 'left':
                axes[2, 0].plot(index+1, episode['longest_dwell_s'], '.', color=color)
        axes[2, 1].plot([row['elapsed_s']/60 for row in result['resource_series']],
            [row['available_gib'] for row in result['resource_series']], label=role, color=color)
    axes[0, 0].set(title='Safe completed skill success per update', ylabel='Success (%)', ylim=(-3, 103))
    axes[0, 1].set(title='Completed episode reward', ylabel='Mean return')
    axes[1, 0].set(title='Guitar displacement from episode reference', ylabel='Max endpoint displacement (mm)')
    axes[1, 1].set(title='Accepted analytic KL', ylabel='KL')
    axes[1, 1].axhline(.02, color='black', linestyle='--', alpha=.5, label='budget 0.02')
    axes[2, 0].set(title='Left native target-candidate dwell', xlabel='Completed left episode', ylabel='Longest contiguous dwell (s)')
    axes[2, 0].axhline(.05, color='black', linestyle='--', alpha=.5, label='hold criterion 0.05 s')
    axes[2, 1].set(title='Host available memory (shared host)', xlabel='Elapsed wall time (min)', ylabel='GiB')
    axes[2, 1].axhline(4, color='black', linestyle='--', alpha=.5, label='guard 4 GiB')
    for index, ax in enumerate(axes.flat):
        ax.grid(alpha=.2)
        if index < 4: ax.set_xlabel('Committed PPO update')
        if index != 4 or ax.get_legend_handles_labels()[0]: ax.legend(loc='best')
    label = 'PROVISIONAL - live training' if document['provisional'] else 'Final training record - checkpoint evaluation separate'
    fig.suptitle('BC-initialized single-hand PPO: '+label, fontsize=14)
    fig.savefig(destination, dpi=150)
    plt.close(fig)


def write_markdown(document, destination):
    lines = ['# BC 초기화 이후 PPO 학습 기록', '',
        '**진행 중 잠정 집계**입니다.' if document['provisional'] else '**두 실행의 report.json 기록까지 확정 집계**했습니다.', '',
        '집계 기준은 첫 음표 고정, 양손 독립 기술(left/hold·right/cross), '
        '준비 2초·기술 4초, 환경 2개·수집 길이 240입니다. BC actor에서 출발했으며, '
        '학습 중의 확률적 episode 성공률과 별도 결정적 모델 검증은 구분합니다.', '',
        '| 구분 | 왼손 hold | 오른손 cross |', '|---|---:|---:|']
    runs = document['runs']
    def row(label, getter):
        lines.append('| '+label+' | '+' | '.join(str(getter(runs[hand])) for hand in ('left', 'right'))+' |')
    row('기록 상태', lambda r: '잠정' if r['provisional'] else r['stopped'])
    row('완료된 PPO update', lambda r: f"{r['updates_committed']}/{r['updates_requested']}")
    row('optimizer 반영 transition', lambda r: r['committed_transitions'])
    row('미반영 로그 transition', lambda r: r['uncommitted_logged_transitions'])
    row('기술 성공/완료 episode', lambda r: f"{r['committed_episode_summary']['successes']}/{r['committed_episode_summary']['count']}")
    row('물리 실패 episode', lambda r: r['committed_episode_summary']['physical_failures'])
    row('음악 strict 50ms 매칭', lambda r: r['committed_episode_summary']['music_matched50'])
    row('음악 목표음 유지 합(s)', lambda r: f"{r['committed_episode_summary']['music_held_total_s']:.6f}")
    row('수용된 KL 최대', lambda r: r['optimization']['kl_max'])
    row('거절 시도 포함 KL 최대', lambda r: r['optimization']['attempted_kl_max'])
    row('KL guard 총 재시도', lambda r: r['optimization']['retries'])
    row('초기 actor learning rate', lambda r: r['settings']['ppo']['actor_lr'])
    row('마지막 실효 actor learning rate', lambda r: r['optimization']['actor_lr_last'])
    row('전체 지지 끝점(%)', lambda r: 100*r['endpoint_safety_60Hz']['fractions'].get('any_main_support', 0.))
    row('삼중 동시 지지 끝점(%)', lambda r: 100*r['endpoint_safety_60Hz']['fractions'].get('triple_support', 0.))
    row('양발 접지 끝점(%)', lambda r: 100*r['endpoint_safety_60Hz']['fractions'].get('both_feet', 0.))
    row('실제 wall time(s)', lambda r: r['wall_s'])
    row('wall 예산(s)', lambda r: r['max_wall_seconds'])
    row('사용 가능 RAM 최소(GiB)', lambda r: r['resource_summary']['min_available_memory_gib'])
    lines += ['', '## BC fit와 PPO 앞·뒤 구간 비교', '',
        'BC 수치는 단일 시범 trajectory의 action training fit입니다. 정한 수치 tolerance 달성 여부를 '
        '별도로 기록하며, native 기술 성공·수렴·일반화와 동일하지 않습니다.', '',
        '| BC 항목 | 왼손 | 오른손 |', '|---|---:|---:|']
    for label, key in (('fit step', 'steps'), ('초기 training MSE', 'initial_training_mse'),
                       ('최종 training MSE', 'training_mse'), ('최대 action 오차', 'max_abs_error'),
                       ('수치 tolerance 도달', 'converged'), ('tolerance', 'tolerance')):
        row(label, lambda r, key=key: r['bc_training_fit'][key] if r['bc_training_fit'] else None)
    lines += ['', '| PPO 확률적 학습 구간 | 성공/episode | 평균 reward | 평균 cost | longest dwell 평균(s) |',
              '|---|---:|---:|---:|---:|']
    for hand, result in runs.items():
        for label, window in result['training_window_comparison'].items():
            if label == 'scope': continue
            lines.append(f"| {hand} {label} | {window['successes']}/{window['count']} | "
                f"{window['mean_reward']} | {window['mean_cost']} | "
                f"{window['longest_dwell_distribution_s']['mean']} |")
    lines += ['', '앞·뒤 구간은 서로 다른 확률적 episode입니다. reward나 fit의 차이만으로 '
        'BC 대비 향상 또는 최종 정책의 검증 완료를 주장하지 않습니다.']
    lines += ['', '## 지지·접지와 기술의 증거 범위', '',
        '아래 최대값과 접촉 비율은 optimizer에 반영된 transition의 60Hz 끝점 기록입니다. '
        '실제 실패 검사는 기존 240Hz 경로에 남아 있습니다. 연속 dwell·기하 타현 건수는 '
        'episode에 저장된 240Hz 원래 측정 ledger 집계이며, 끝점 비율을 모든 물리 순간의 접촉 비율로 확대하지 않습니다.', '']
    for hand, result in runs.items():
        safety, episode = result['endpoint_safety_60Hz'], result['committed_episode_summary']
        lines += [f"- **{hand}**: 기타 변위 최대 {safety['guitar_displacement_max_m']}m, "
            f"회전 최대 {safety['guitar_rotation_max_rad']}rad, 발 변위 최대 {safety['foot_displacement_max_m']}m, "
            f"관절 속도 최대 {safety['joint_speed_max_rad_s']}rad/s. 접촉 끝점 비율 `{safety['fractions']}`. "
            f"최장 연속 목표 후보 dwell {episode['longest_dwell_s']}s, "
            f"episode별 longest dwell 분포(s) `{episode['longest_dwell_distribution_s']}`. "
            f"방향·줄 일치 기하 타현 {episode['matching_crossings']}회. "
            f"회계 일치 `{result['accounting_consistent']}`, 실행 완료 `{result['report_completed']}`."]
        physics = result['physics_accounting']
        lines += [f"  - 물리 회계: 과제 측정 {physics['measured_task_steps240']} step, "
            f"준비 {physics['preparation_steps240']} step, 합계 {physics['actual_steps240_from_native_clock']} step. "
            f"에피소드 초기화 {physics['episode_initializations']}회, simulator 생성/종료 "
            f"{physics['lifecycle_scene_creations']}/{physics['lifecycle_scene_destructions']}회."]
    lines += ['', '## 해석과 한계', '',
        '- hold는 원래 native 목표 접촉 후보를 연속 0.05초 확보한 독립 기술입니다. 실제 현 압력·음향 검증이 아닙니다.',
        '- cross는 선택한 줄·방향의 적격 기하 통과 기술이며 왼손 압현 조건과 음악 시각 일치가 없는 경우에도 성공할 수 있습니다.',
        '- 현 안전 gate는 전체 주요 지지의 유지와 발 접지를 검사합니다. '
        '이 gate 통과가 초기 V3의 삼중 동시 지지 95% 조건이나 왼손 하중 비의존 검증을 뜻하지 않습니다. '
        'any_main_support와 triple_support·개별 chest/upper-arm/thigh 접촉을 구분해 기록합니다.',
        '- 안정성 비용 가중치 1과 초기 std 0.02를 사용했습니다. 초기 설정 actor learning rate는 1e-5이며, '
        f"KL guard 재시도 뒤 마지막 실효 learning rate는 왼손 {runs['left']['optimization']['actor_lr_last']}, "
        f"오른손 {runs['right']['optimization']['actor_lr_last']}입니다. 수용된 KL과 거절 시도 포함 최대 KL·재시도를 구분합니다. "
        '24 update 또는 1800초 예산은 update 시작 전에 검사하므로 진행 중 update만큼 wall 예산을 초과할 수 있습니다.',
        '- BC 이전과의 무작위 대조군 비교나 수렴·일반화 입증을 수행한 집계가 아닙니다. '
        '최종 모델 승격은 별도 결정적 native checkpoint 검증 결과로 판단합니다.',
        '- 진행 중 gzip은 종료 trailer가 없을 수 있습니다. 완전한 JSON record만 집계하고 '
        '미완결 여부를 JSON에 기록합니다. '+
        ('최종 결과는 두 report 생성 후 재집계합니다.' if document['provisional'] else
         '이 문서는 두 report 종료 후 재집계한 확정 기록입니다.'), '',
        '[상세 canonical 집계](ppo_progress_v1.json) · [그래프](ppo_progress_v1.png)', '']
    destination.write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    runs = {hand: summarize(args.phase/(hand+'_ppo_v1')) for hand in ('left', 'right')}
    document = dict(schema='guitar_learning.imitation_ppo_progress.v1',
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        provisional=any(row['provisional'] for row in runs.values()), runs=runs,
        scope='training trajectories only; independent safe skill success is not joint music or sound')
    destination = args.phase/'ppo_progress_v1.json'
    temporary = destination.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(document, indent=2, allow_nan=False)+'\n')
    temporary.replace(destination)
    save_plot(document, args.phase/'ppo_progress_v1.png')
    write_markdown(document, args.phase/'ppo_analysis_v1.md')
    print(json.dumps(dict(provisional=document['provisional'],
        runs={hand: {key: row[key] for key in ('updates_committed', 'report_completed',
            'committed_episode_summary', 'accounting_consistent')} for hand, row in runs.items()})))


if __name__ == '__main__': main()
