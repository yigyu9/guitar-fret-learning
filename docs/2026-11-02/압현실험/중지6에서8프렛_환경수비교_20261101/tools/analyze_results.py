"""6→8 평가: 실패를 포함한 최초 에피소드 원장과 실제 발음 구간을 분석한다.

후보 접촉과 유효 압현을 구분한다. 표본별 후보의 의미가 불명확하면 경고를
기록하고 원시 수치를 보존하며, 후보 중복만으로 분석을 중단하지 않는다.
"""
import gzip
import importlib.util
import json
from pathlib import Path
import statistics

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
STUDY_PATH = ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3/tools/study.py'
spec = importlib.util.spec_from_file_location('recovery_original_study', STUDY_PATH)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
first_episodes = study.first_episodes
write = study.write


def analyze(out, count, *, result_path=None):
    out = Path(out)
    report = json.loads((out/'report.json').read_text())
    if (report.get('episodes') != count or not report.get('failed_episodes_in_denominator')
            or not report.get('completed') or not report.get('lifecycle_verified')
            or not report.get('first_episode_per_env_per_batch')):
        raise ValueError('실패 포함 평가 분모 검증 실패')
    rows = first_episodes(out, count)
    result = dict(episodes=count, A=0, B=0, AB=0, full_duration_pair=0,
                  physical=0, wrist=0, clean_s=[0., 0.], wrong_s=[0., 0.],
                  thumb_distance_m=0., thumb_contact_candidate_s=0., reward_terms={},
                  candidate_overlap_samples=0, A_audible_candidate_warning_samples=0)
    ids = [row['finger_control_diagnostics']['episode_id'] for row in rows]
    eligible = [row['valid'] and not row['termination']['physical_failure']
                and not row['termination']['wrist_failure'] for row in rows]
    for row in rows:
        ledger = row['left_note_ledger']['values']
        success = [bool(x) for x in ledger['left']]
        if len(success) != 2:
            raise ValueError('AB 두 음 필요')
        physical = bool(row['termination']['physical_failure'])
        wrist = bool(row['termination']['wrist_failure'])
        result['physical'] += physical
        result['wrist'] += wrist
        result['A'] += success[0]
        result['B'] += success[1]
        result['AB'] += all(success) and row['valid'] and not physical and not wrist
        result['full_duration_pair'] += all(v >= 1.5-1e-8 for v in ledger['clean']) and row['valid'] and not physical and not wrist
        for i in range(2):
            result['clean_s'][i] += ledger['clean'][i]/count
            result['wrong_s'][i] += ledger['wrong'][i]/count
        # 실제 진단 위치는 원장을 그대로 보존하고, 없는 값을 0으로 채우지 않는다.
        for key, value in row['reward_components'].items():
            result['reward_terms'][key] = result['reward_terms'].get(key, 0.)+value/count
        if abs(sum(row['reward_components'].values())-row['reward']) > 1e-4:
            raise ValueError('보상 성분 합계 불일치')
    rejection = dict(position=0, facing=0, load=0, wrong=0, clean=0)
    both_rejection = [dict(position=0, facing=0, load=0, wrong=0, clean=0) for _ in range(2)]
    samples = 0
    tail = [[] for _ in range(count)]
    onset = [None for _ in range(count)]
    with gzip.open(out/'finger_control_trace.jsonl.gz', 'rt') as stream:
        for line in stream:
            extra = json.loads(line)['natural_preparation']['transition']
            if extra['schema'] != 'guitar_learning.middle_f6_f8_environment_scale.v1':
                raise ValueError('6→8 전용 관측 계약 필요')
            goals = extra['goals']
            if [(g['fret'], g['string_index'], g['onset_s'], g['end_s']) for g in goals] != [(6, 2, 3., 4.5), (8, 2, 5.25, 6.75)]:
                raise ValueError('6→8 표준3번줄 고정 시간표 불일치')
            for env in range(count):
                if extra['all_env_episode_ids'][env] != ids[env]:
                    continue
                candidate = extra['all_env_candidate'][env]
                t = extra['all_env_episode_time_s'][env]
                if all(candidate):
                    result['candidate_overlap_samples'] += 1
                if 3. <= t < 4.5 and all(candidate) and not extra['all_env_wrong'][env][0]:
                    result['A_audible_candidate_warning_samples'] += 1
                clean = [c and not w for c, w in zip(candidate, extra['all_env_wrong'][env])]
                for i, (start, end) in enumerate(((3., 4.5), (5.25, 6.75))):
                    if not start <= t < end:
                        continue
                    if not extra['all_env_position_geometry'][env][i]: key = 'position'
                    elif not extra['all_env_facing_geometry'][env][i]: key = 'facing'
                    elif not extra['all_env_assigned_loaded'][env][i]: key = 'load'
                    elif extra['all_env_wrong'][env][i]: key = 'wrong'
                    else: key = 'clean'
                    both_rejection[i][key] += 1
                if 4.45-1e-8 <= t < 4.5-1e-8:
                    tail[env].append(clean[0])
                if onset[env] is None and t >= 5.25-1e-8:
                    onset[env] = t <= 5.25+1/240+1e-8 and clean[1]
                if not 5.25 <= t < 6.75:
                    continue
                samples += 1
                if not extra['all_env_position_geometry'][env][1]:
                    key = 'position'
                elif not extra['all_env_facing_geometry'][env][1]:
                    key = 'facing'
                elif not extra['all_env_assigned_loaded'][env][1]:
                    key = 'load'
                elif extra['all_env_wrong'][env][1]:
                    key = 'wrong'
                else:
                    key = 'clean'
                rejection[key] += 1
    result.pop('thumb_distance_m')
    result.pop('thumb_contact_candidate_s')
    result['B_endpoint_count'] = samples
    result['B_rejection_partition'] = rejection
    result['on_time_with_previous_tail'] = sum(ok and len(a) >= 11 and all(a) and bool(b) for ok, a, b in zip(eligible, tail, onset))
    result['on_time_pair'] = result['on_time_with_previous_tail']
    result['audible_rejection_partition'] = both_rejection
    result['clean_fraction'] = [v/1.5 for v in result['clean_s']]
    result['target_description'] = 'middle, standard string3, fret6→8, A3–4.5s/B5.25–6.75s'
    result['interpretation_limit'] = 'contact proxies; candidate overlap warnings require raw/sample semantics review; on-time uses final50ms A and first B endpoint'
    # 엄지 기존 진단은 원래 위치를 찾은 뒤 수치가 있는 항목만 평균한다.
    def find(value, key):
        if isinstance(value, dict):
            if key in value:
                return value[key]
            for child in value.values():
                found = find(child, key)
                if found is not None:
                    return found
        return None
    thumb = [find(row, 'thumb_support') for row in rows]
    if all(isinstance(x, dict) and 'contact_candidate_s' in x for x in thumb):
        result['thumb_contact_candidate_s'] = statistics.mean(x['contact_candidate_s'] for x in thumb)
        result['thumb_signed_gap_m'] = statistics.mean(x['mean_signed_gap_m'] for x in thumb)
        result['thumb_normal_load_N'] = statistics.mean(x['normal_load_mean_N'] for x in thumb)
    result['evaluation'] = str(out)
    write(Path(result_path) if result_path is not None else out/'analysis.json', result)
    return result


def plot_study(progress_path, out):
    """동일 경험량의 seed별 성능과 평균 보상 성분을 그림으로 저장한다."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    state = json.loads(Path(progress_path).read_text())
    rows = [r for r in state['results'].values()
            if r['mode'] == 'mean' and r['tag'] == 'development']
    if not rows:
        return []
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)
    for seed in sorted({r['seed'] for r in rows}):
        selected = sorted((r for r in rows if r['seed'] == seed), key=lambda r: r['transitions'])
        x = [r['transitions']/1e6 for r in selected]
        for ax, key, label in zip(axes, ('AB', 'full_duration_pair', 'on_time_pair'),
                                 ('Both notes achieved', 'Both notes held 1.5 seconds', 'On-time transition with A tail')):
            ax.plot(x, [100*r['metrics'][key]/r['metrics']['episodes'] for r in selected], marker='o', label=f'seed {seed}')
            ax.set(title=label, xlabel='Collected transitions (million)', ylabel='Episodes (%)', ylim=(-2, 102))
            ax.axhline(90, color='gray', linestyle=':', linewidth=1)
            ax.grid(alpha=.2)
            ax.legend()
    performance = out/'learning_performance.png'
    fig.savefig(performance, dpi=160)
    plt.close(fig)
    keys = sorted({k for r in rows for k in r['metrics']['reward_terms']})
    fig, axes = plt.subplots((len(keys)+2)//3, 3, figsize=(14, max(4, 2.8*((len(keys)+2)//3))), constrained_layout=True, squeeze=False)
    for ax, key in zip(axes.flat, keys):
        for seed in sorted({r['seed'] for r in rows}):
            selected = sorted((r for r in rows if r['seed'] == seed), key=lambda r: r['transitions'])
            ax.plot([r['transitions']/1e6 for r in selected], [r['metrics']['reward_terms'].get(key, 0.) for r in selected], marker='o', label=f'seed {seed}')
        ax.set(title=key, xlabel='Collected transitions (million)', ylabel='Mean episode return')
        ax.grid(alpha=.2)
        ax.legend()
    for ax in list(axes.flat)[len(keys):]:
        ax.set_visible(False)
    rewards = out/'reward_components.png'
    fig.savefig(rewards, dpi=160)
    plt.close(fig)
    return [str(performance), str(rewards)]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study-progress', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(plot_study(args.study_progress, args.out), ensure_ascii=False))
