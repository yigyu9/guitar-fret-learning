"""CPU-only comparison of the three completed, frozen seed7 experiments."""
import copy
import csv
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
RUNS = {'baseline': 'baseline_original_gamma_seed7',
        'A': 'A_time_discount_30s_seed7', 'B': 'B_zero_cost_head_seed7'}
UPDATES = (0, 50, 100, 150, 200, 250, 300)
CRITERIA = dict(achieved_fraction_min=.8, mean_clean_fraction_min=.7,
                mean_audible_wrong_fraction_max=.1,
                physical_failure_fraction_max=.05, consecutive_policy_evaluations=2)


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import torch
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties

    outputs = ('comparison.json', 'validation.json', 'initial_comparability.json',
               'performance.csv', 'comparison.png', 'RESULTS.md')
    assert not any((HERE/name).exists() for name in outputs), 'Preserve existing results'
    rows, acceptance, initial_controls, settings, train_pins = [], {}, {}, {}, {}
    stage_checks, input_hashes, verified_paths = [], {}, {}
    for label, name in RUNS.items():
        run = BASE/name
        completed = read(run/'comparison_completed.json')
        launcher = read(BASE/(name+'_launcher.json'))
        assert completed['completed'] and len(completed['stages']) == 11
        assert launcher['returncode'] == 0
        stages = {row['name'] for row in completed['stages']}
        expected = {'train'} | {'evaluation_initial_'+c for c in ('policy', 'zero', 'random', 'reference')}
        expected |= {'evaluation_%06d' % u for u in UPDATES[1:]}
        assert stages == expected
        for stage in sorted(stages):
            folder = run/stage
            report, after = read(folder/'report.json'), read(folder/'inputs_after.json')
            before, scene = read(folder/'inputs_before.json'), read(folder/'gpu_scene_final.json')
            assert report['completed'] and report['closed'] and report['failure'] is None
            assert not report['changed_inputs'] and not report['unpinned_project_sources']
            assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
            assert before == after['input_pins'] and scene['closed'] and scene['num_envs'] == 128
            for path, expected_sha in before.items():
                if path not in verified_paths:
                    verified_paths[path] = digest(Path(path))
                assert verified_paths[path] == expected_sha, path
            stage_checks.append(dict(condition=label, stage=stage, completed=True,
                scene_closed=True, current_input_pins_verified=len(before)))
            for filename in ('report.json', 'inputs_before.json', 'inputs_after.json', 'gpu_scene_final.json'):
                input_hashes[str(folder/filename)] = digest(folder/filename)
        settings[label] = read(run/'train/settings.json')
        train_pins[label] = read(run/'train/inputs_before.json')
        metrics = [json.loads(line) for line in (run/'train/metrics.jsonl').read_text().splitlines()]
        assert [row['update'] for row in metrics] == list(range(1, 301))
        assert metrics[-1]['total_transitions'] == 1228800
        initial_controls[label] = {}
        for control in ('policy', 'zero', 'random', 'reference'):
            path = run/('evaluation_initial_'+control)/'evaluation.json'
            result = read(path)
            assert result['assigned_quotas'] == [1]*128 and len(result['episodes']) == 128
            assert sorted(e['env_id'] for e in result['episodes']) == list(range(128))
            initial_controls[label][control] = result['summary']
            input_hashes[str(path)] = digest(path)
        policy_rows = []
        for update in UPDATES:
            stage = 'evaluation_initial_policy' if update == 0 else 'evaluation_%06d' % update
            path = run/stage/'evaluation.json'
            result = read(path)
            episodes = result['episodes']
            assert result['assigned_quotas'] == [1]*128 and len(episodes) == 128
            assert sorted(e['env_id'] for e in episodes) == list(range(128))
            summary = dict(episodes=128,
                achieved_fraction=sum(bool(e['achieved']) for e in episodes)/128,
                mean_clean_fraction=sum(e['clean_fraction'] for e in episodes)/128,
                mean_audible_wrong_fraction=sum(e['audible_wrong_fraction'] for e in episodes)/128,
                physical_failure_fraction=sum(e['termination']['physical_failure'] for e in episodes)/128,
                wrist_failure_fraction=sum(e['termination']['wrist_failure'] for e in episodes)/128,
                any_failure_fraction=sum(e['reason'] == 'terminal_failure' for e in episodes)/128)
            assert all(abs(result['summary'][key]-value) < 1e-12 for key, value in summary.items())
            passed = (summary['achieved_fraction'] >= .8 and summary['mean_clean_fraction'] >= .7
                and summary['mean_audible_wrong_fraction'] <= .1 and summary['physical_failure_fraction'] <= .05)
            row = dict(condition=label, update=update, achieved=sum(bool(e['achieved']) for e in episodes),
                       **summary, passed_single_evaluation=passed)
            rows.append(row)
            if update:
                policy_rows.append(row)
            input_hashes[str(path)] = digest(path)
        pairs = [[a['update'], b['update']] for a, b in zip(policy_rows, policy_rows[1:])
                 if a['passed_single_evaluation'] and b['passed_single_evaluation']]
        saved = read(run/'analysis/acceptance.json')
        assert saved['criteria'] == CRITERIA and saved['passing_pairs'] == pairs
        assert saved['passed'] == bool(pairs)
        assert [e['passed'] for e in saved['evaluations']] == [r['passed_single_evaluation'] for r in policy_rows]
        acceptance[label] = dict(criteria=CRITERIA, passing_pairs=pairs, passed=bool(pairs))
        for path in (run/'train/settings.json', run/'comparison_completed.json',
                     BASE/(name+'_launcher.json'), run/'analysis/acceptance.json'):
            input_hashes[str(path)] = digest(path)

    assert initial_controls['baseline'] == initial_controls['A'] == initial_controls['B']
    normalized = copy.deepcopy(settings)
    a_tag = normalized['A']['song']['short_learning'].pop('ablation')
    b_tag = normalized['B']['song']['short_learning'].pop('ablation')
    assert a_tag['variant'] == 'A_time_discount_30s' and b_tag['variant'] == 'B_zero_cost_head'
    assert settings['A']['ppo']['gamma'] == settings['A']['song']['surface_approach_gamma']
    assert abs(settings['A']['ppo']['gamma'] - 0.9994445987368581) < 1e-15
    for section, key in (('ppo', 'gamma'), ('song', 'surface_approach_gamma')):
        normalized['A'][section][key] = .99
    assert normalized['baseline'] == normalized['A'] == normalized['B']
    models = {}
    for label, name in RUNS.items():
        path = BASE/name/'train/initial.pt'
        payload = torch.load(path, map_location='cpu', weights_only=False)
        assert payload['updates'] == 0 and len(payload['model']) == 73
        models[label] = payload['model']
        input_hashes[str(path)] = digest(path)
    a_changed = [k for k in models['baseline'] if not torch.equal(models['baseline'][k], models['A'][k])]
    b_changed = [k for k in models['baseline'] if not torch.equal(models['baseline'][k], models['B'][k])]
    assert not a_changed and sorted(b_changed) == ['cost_critic.bias', 'cost_critic.weight']
    assert all(torch.count_nonzero(models['B'][key]) == 0 for key in b_changed)
    common = set.intersection(*(set(pins) for pins in train_pins.values()))
    assert all(len({pins[path] for pins in train_pins.values()}) == 1 for path in common)
    assert not torch.cuda.is_initialized()
    initial = dict(model_tensors=73, baseline_A_identical=73, baseline_B_identical=71,
        baseline_B_changed=b_changed, B_cost_head_exact_zero=True,
        settings_differences_only_A_gamma_PBRS_and_variant_tags=True,
        initial_control_summaries_exact=True, common_train_input_pins=len(common),
        common_pins_identical_and_current=True, cuda_initialized=False)
    validation = dict(completed=True, conditions=3, train_stages=3, evaluation_stages=30,
        stages=stage_checks, unique_current_input_paths_verified=len(verified_paths),
        all33_scenes_closed=True, all_launchers_returncode_zero=True,
        original_acceptance_recomputed=True, input_sha256=input_hashes,
        analysis_script_sha256=digest(Path(__file__)))
    comparison = dict(rows=rows, acceptance=acceptance, initial_comparability=initial,
        initial_control_summaries=initial_controls, cost_audit=read(HERE/'COST_AUDIT.json'),
        scope='one seed, fixed guitar, finite wrist teacher, middle four-axis single original note;128 first attempts include failures; not independent seeds, free guitar, full song, force quality or adoption')
    for filename, value in (('comparison.json', comparison), ('validation.json', validation),
                            ('initial_comparability.json', initial)):
        (HERE/filename).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    with (HERE/'performance.csv').open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    font = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams['font.family'] = font.get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)
    for label, caption in (('baseline', '기준 gamma .99'), ('A', 'A 시간 할인 30초'), ('B', 'B 비용 head 초기0')):
        subset = [row for row in rows if row['condition'] == label]
        for ax, key, title in zip(axes,
                ('achieved_fraction', 'mean_clean_fraction', 'mean_audible_wrong_fraction'),
                ('압현 달성', '압현 유지', '오압현')):
            ax.plot([r['update'] for r in subset], [100*r[key] for r in subset], marker='o', label=caption)
            ax.set_title(title)
            ax.set_xlabel('PPO 업데이트')
            ax.grid(alpha=.25)
            ax.set_ylim(-3, 103)
    for ax, threshold in zip(axes, (80, 70, 10)):
        ax.axhline(threshold, color='gray', lw=.8, ls='--', alpha=.6)
    axes[0].set_ylabel('비율 (%) · 실패 포함128시도')
    axes[0].legend(fontsize=8)
    fig.suptitle('같은 기하·중지1음·seed7: 모든 고정 평가 시점 (점선: 기존 단일평가 기준)')
    fig.tight_layout()
    fig.savefig(HERE/'comparison.png', dpi=140)
    plt.close(fig)
    text = ['# 같은 기하에서 기준·A·B 비교', '',
        'B는150~250회에서128/128을 유지해 기존 연속2평가 기준을 통과했지만, 최종300회에서65/128로 저하됐다. 기준과 A는 연속2평가 기준을 통과하지 못했다.', '',
        '고정 기타·유한 팔 손목 안내·중지4축·원곡1음·large128/H32/300·seed7이다. 각 평가는 실패를 포함한 배정128환경 첫 시도이며128개 독립 seed가 아니다. 초기값0은 학습 전 정책이다.', '',
        '| 반복 | 기준 달성/128 | A 달성/128 | B 달성/128 | 기준 유지/오압현 | A 유지/오압현 | B 유지/오압현 |',
        '|---:|---:|---:|---:|---:|---:|---:|']
    for update in UPDATES:
        selected = [next(r for r in rows if r['condition'] == label and r['update'] == update)
                    for label in RUNS]
        text.append('| %d | %d | %d | %d | %.2f%% / %.2f%% | %.2f%% / %.2f%% | %.2f%% / %.2f%% |' %
            (update, *(r['achieved'] for r in selected),
             *(value for r in selected for value in (100*r['mean_clean_fraction'], 100*r['mean_audible_wrong_fraction']))))
    text += ['', '![3조건 전체 시점 비교](comparison.png)', '',
        '기존 수용 기준은 달성≥80%, 유지≥70%, 오압현≤10%, 물리 실패≤5%를 인접한 정책 평가2회에서 연속 충족하는 것이다. 기준은300회 단일평가만, A는150회 단일평가만 충족했다. B의 통과쌍은150–200회와200–250회다. B 최종300회는 유지53.76%, 오압현43.19%로 기준 미달이다. 최종 시점의 안정성이나 기본 채택으로 확대하지 않는다.', '',
        '모든30평가는 물리·손목·전체 실패율0이었고, 실패를 제외해 분모를 바꾸지 않았다. train3개+평가30개의 완료·현재 입력핀·scene 종료와 launcher3개의 실제 종료코드0을 확인했다. B outer wall은1786.634초다.', '',
        '실제 초기 model73개 tensor를 CPU로 비교했다. 기준과 A는73개 모두 동일했고, B는비용 head2개만 정확0이며 나머지71개가 동일했다. A는reward/PBRS gamma를0.99→0.9994445987368581로 바꾸었고 비용 gamma는 유지했다. B의 설정 차이는 별도 실험 표기뿐이며 초기 비용 head만 바꿨다. 공통 입력핀은 모두 동일·현재 일치했고, 초기 policy/zero/random/reference 네 대조의 성과 요약도3조건에서 같았다.', '',
        'B 전체300회에서 비용 advantage·critic value/target·손실이 정확0이고 final 비용 head도0이었다. 실제 비용 저장 평균과5,632종료episode의 비용도0이었다. 비용 계수는1, 원래 실패비용은 유지했다. 순간 비용min/max는 미저장이므로 직접 확인값으로 주장하지 않는다. [비용 감사](COST_AUDIT.md)에 범위를 구분했다.', '',
        '이 seed에서는 B가A의150회 이후 붕괴와 다른 학습 경로를 보였지만, 비용 초기 신호가 모든 불안정의 단독 원인이라고 확정할 수 없다. B도300회에 저하됐다. 높은 접촉 합력·자유 기타·전곡·자연스러움은 이 성과 비교로 검증되지 않는다. A의env0 오압현 witness는 [별도 원인 기록](../comparison_gamma_seed7/WRONG_PRESS_CASES.md)에 있으며 전체128 원인분포와 구분한다.', '',
        '수치·수용 판정은 comparison.json/performance.csv, 초기 검증은 initial_comparability.json, 완료·핀·원자료 SHA는 validation.json에 보존했다. 기존 결과와 활성 소스는 수정하지 않았다.']
    (HERE/'RESULTS.md').write_text('\n'.join(text)+'\n')
    print(json.dumps(dict(completed=True, scenes_closed=33, common_pins=len(common),
        passing_pairs={key: value['passing_pairs'] for key, value in acceptance.items()}, cuda_initialized=False)))


if __name__ == '__main__':
    main()
