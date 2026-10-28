"""CPU audit of completed B seed17; preserve all runner outputs."""
import collections
import copy
import csv
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REP = HERE.parent
BASE = REP.parent
UPDATES = (0, 50, 100, 150, 200, 250, 300)
CRITERIA = dict(achieved_fraction_min=.8, mean_clean_fraction_min=.7,
    mean_audible_wrong_fraction_max=.1, physical_failure_fraction_max=.05,
    consecutive_policy_evaluations=2)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import torch
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties

    outputs = ('final_audit.json', 'validation.json', 'performance.csv', 'replication.png', 'RESULTS.md')
    assert not any((HERE/name).exists() for name in outputs)
    hashes, current, checks, rows, controls, acceptance, settings = {}, {}, [], [], {}, {}, {}

    def remember(path):
        value = sha(path)
        hashes[str(path)] = value
        return value

    for seed, run in ((7, BASE/'B_zero_cost_head_seed7'), (17, REP/'B_zero_cost_head_seed17')):
        launcher = BASE/'B_zero_cost_head_seed7_launcher.json' if seed == 7 else REP/'B_zero_cost_head_seed17_launcher.json'
        assert read(launcher)['returncode'] == 0
        remember(launcher)
        completion = read(run/'comparison_completed.json')
        assert completion['completed'] and len(completion['stages']) == 11
        remember(run/'comparison_completed.json')
        stages = {x['name'] for x in completion['stages']}
        expected = {'train'} | {'evaluation_initial_'+c for c in ('policy', 'zero', 'random', 'reference')}
        expected |= {'evaluation_%06d' % u for u in UPDATES[1:]}
        assert stages == expected
        controls[seed] = {}
        for stage in sorted(stages):
            folder = run/stage
            report, after = read(folder/'report.json'), read(folder/'inputs_after.json')
            before, scene = read(folder/'inputs_before.json'), read(folder/'gpu_scene_final.json')
            assert report['completed'] and report['closed'] and report['failure'] is None
            assert not report['changed_inputs'] and not report['unpinned_project_sources']
            assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
            assert before == after['input_pins'] and scene['closed'] and scene['num_envs'] == 128
            for path, value in before.items():
                if path not in current:
                    current[path] = sha(path)
                assert current[path] == value, path
            checks.append(dict(seed=seed, stage=stage, completed=True, closed=True, input_pins=len(before)))
            for name in ('report.json', 'inputs_before.json', 'inputs_after.json', 'gpu_scene_final.json', 'settings.json'):
                remember(folder/name)
            if stage == 'train':
                continue
            result = read(folder/'evaluation.json')
            episodes = result['episodes']
            assert result['assigned_quotas'] == [1]*128 and len(episodes) == 128
            assert sorted(e['env_id'] for e in episodes) == list(range(128))
            summary = dict(episodes=128, achieved_fraction=sum(bool(e['achieved']) for e in episodes)/128,
                mean_clean_fraction=sum(e['clean_fraction'] for e in episodes)/128,
                mean_audible_wrong_fraction=sum(e['audible_wrong_fraction'] for e in episodes)/128,
                physical_failure_fraction=sum(e['termination']['physical_failure'] for e in episodes)/128,
                wrist_failure_fraction=sum(e['termination']['wrist_failure'] for e in episodes)/128,
                any_failure_fraction=sum(e['reason'] == 'terminal_failure' for e in episodes)/128)
            assert all(abs(result['summary'][key]-value) < 1e-12 for key, value in summary.items())
            remember(folder/'evaluation.json')
            if stage.startswith('evaluation_initial_'):
                controls[seed][stage[len('evaluation_initial_'):]] = summary
            if stage.startswith('evaluation_initial_') and stage != 'evaluation_initial_policy':
                continue
            update = 0 if stage == 'evaluation_initial_policy' else int(stage[len('evaluation_'):])
            passed = (summary['achieved_fraction'] >= .8 and summary['mean_clean_fraction'] >= .7
                and summary['mean_audible_wrong_fraction'] <= .1 and summary['physical_failure_fraction'] <= .05)
            rows.append(dict(seed=seed, update=update, achieved=round(summary['achieved_fraction']*128),
                **summary, passed=passed))
        policy = sorted((r for r in rows if r['seed'] == seed and r['update']), key=lambda r:r['update'])
        pairs = [[a['update'], b['update']] for a, b in zip(policy, policy[1:]) if a['passed'] and b['passed']]
        saved = read(run/'analysis/acceptance.json')
        assert saved['criteria'] == CRITERIA and saved['passing_pairs'] == pairs and saved['passed'] == bool(pairs)
        assert [x['passed'] for x in saved['evaluations']] == [r['passed'] for r in policy]
        acceptance[seed] = dict(passing_pairs=pairs, passed=bool(pairs), single_pass_updates=[r['update'] for r in policy if r['passed']])
        remember(run/'analysis/acceptance.json')
        settings[seed] = read(run/'train/settings.json')
    normalized = copy.deepcopy(settings)
    normalized[17]['seed'] = 7
    assert normalized[7] == normalized[17]
    initial = read(REP/'actual_initial_verification.json')
    assert initial['same_seed17_normal_initialization_identical_tensors'] == 71 and initial['actual_cost_head_exact_zero']
    for path, value in initial['input_sha256'].items():
        assert sha(path) == value
    remember(REP/'actual_initial_verification.json')
    seal = read(REP/'preparation_seal.json')
    assert all(sha(path) == value for path, value in seal['input_sha256'].items())
    remember(REP/'preparation_seal.json')

    train = REP/'B_zero_cost_head_seed17/train'
    metrics = [json.loads(line) for line in (train/'metrics.jsonl').read_text().splitlines()]
    episodes = [json.loads(line) for line in (train/'episodes.jsonl').read_text().splitlines()]
    assert [x['update'] for x in metrics] == list(range(1, 301))
    assert all(x['transitions'] == 4096 and x['cost_weight'] == 1 for x in metrics)
    assert metrics[-1]['total_transitions'] == 1228800
    failures = [dict(jsonl_line=i+1, episode=e) for i, e in enumerate(episodes)
                if e['cost'] or e['termination']['physical_failure'] or e['termination']['wrist_failure']]
    assert len(episodes) == 5632 and len(failures) == 1
    failure = failures[0]['episode']
    assert failure['update'] == 201 and failure['env_id'] == 81
    assert failure['failure_reasons'] == ['wrist_severe'] and not failure['termination']['physical_failure']
    assert all(check['closed'] for check in checks) and len(checks) == 22
    assert all(s['any_failure_fraction'] == 0 for group in controls.values() for s in group.values())
    assert all(r['any_failure_fraction'] == 0 for r in rows)
    stats = ('mean', 'std', 'min', 'max')
    features = dict(actual_failure_cost_mean=lambda x:x['mean_failure_cost'] != 0,
        cost_GAE_advantage=lambda x:any(x['diagnostics']['advantages']['cost_raw'][k] != 0 for k in stats),
        post_cost_value=lambda x:any(x['diagnostics']['post_update']['critics']['cost']['value'][k] != 0 for k in stats),
        cost_value_loss=lambda x:x['cost_value_loss'] != 0)
    nonzero = {key:[x['update'] for x in metrics if test(x)] for key, test in features.items()}
    assert nonzero['actual_failure_cost_mean'] == [201]
    assert all(nonzero[key] == list(range(201, 301)) for key in features if key != 'actual_failure_cost_mean')
    raw_sum = sum(x['mean_failure_cost']*x['transitions'] for x in metrics)
    assert abs(raw_sum-sum(e['cost'] for e in episodes)) < 1e-7
    heads = []
    for name in ('initial.pt', 'evaluation_000200.pt', 'evaluation_000250.pt', 'final.pt'):
        path = train/name
        payload = torch.load(path, map_location='cpu', weights_only=False)
        assert payload['metadata']['settings'] == settings[17]
        head = {key:dict(shape=list(v.shape), nonzero_count=int(torch.count_nonzero(v)), max_abs=float(v.abs().max()),
            l2_norm=float(v.double().norm())) for key, v in payload['model'].items() if key.startswith('cost_critic.')}
        heads.append(dict(path=str(path), sha256=remember(path), update=payload['updates'], parameters=head))
        del payload
    for name in ('metrics.jsonl', 'episodes.jsonl', 'training_contract.json'):
        remember(train/name)
    seed7_cost = BASE/'comparison_cost_head_seed7/COST_AUDIT.json'
    remember(seed7_cost)
    cost = dict(metrics_updates=300, transitions=1228800, completed_episodes=len(episodes),
        reason_counts=dict(collections.Counter(e['reason'] for e in episodes)), failures=failures,
        nonzero_update_indices=nonzero, sum_transition_cost_means_times_counts=raw_sum,
        sum_episode_cost=sum(e['cost'] for e in episodes), cost_weight_all_updates=1, checkpoint_cost_heads=heads,
        final_cost_diagnostics=metrics[-1]['diagnostics']['post_update']['critics']['cost'],
        cost_raw_field_means='GAE advantage, not immediate cost',
        seed7_all300_cost_zero_audit=str(seed7_cost), seed7_cost_audit=read(seed7_cost),
        limitation='Immediate per-transition cost min/max/tape is not stored; saved mean and episode cost/components are audited. No update201 parameter checkpoint exists.')
    audit = dict(completed=True, policy_rows=sorted(rows, key=lambda r:(r['seed'], r['update'])),
        initial_controls=controls, criteria=CRITERIA, acceptance=acceptance, seed17_cost=cost,
        actual_initial_verification_reused=True, same_settings_except_seed=True,
        scope='B replication across two seeds; no same-seed17 baseline or causal seed7 comparison; fixed guitar, finite wrist teacher, middle4 single original note')
    validation = dict(completed=True, stage_checks=checks, seed17_train_and_evaluations_closed=11,
        all22_rechecked_scenes_closed=True, launchers_returncode_zero=True,
        unique_current_input_paths_verified=len(current), preparation_pins_current=len(seal['input_sha256']),
        input_sha256=hashes, analysis_script_sha256=sha(Path(__file__)), GPU_executed=False,
        CUDA_initialized=torch.cuda.is_initialized())
    assert not validation['CUDA_initialized']
    for name, value in (('final_audit.json', audit), ('validation.json', validation)):
        with (HERE/name).open('x') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
    with (HERE/'performance.csv').open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(audit['policy_rows'])
    font = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams['font.family'] = font.get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for seed in (7, 17):
        selected = [r for r in audit['policy_rows'] if r['seed'] == seed]
        for ax, key, title in zip(axes, ('achieved_fraction', 'mean_clean_fraction', 'mean_audible_wrong_fraction'), ('압현 달성', '압현 유지', '오압현')):
            ax.plot([r['update'] for r in selected], [100*r[key] for r in selected], marker='o', label='B seed%d' % seed)
            ax.set_title(title)
            ax.set_xlabel('PPO 업데이트')
            ax.grid(alpha=.25)
            ax.set_ylim(-3, 103)
    for ax, limit in zip(axes, (80, 70, 10)):
        ax.axhline(limit, color='gray', ls='--', lw=.8)
    axes[0].set_ylabel('비율 (%) · 실패 포함128시도')
    axes[0].legend()
    fig.suptitle('B 비용 head 초기0: seed7 / seed17 재현 확인 (인과 비교 아님)')
    fig.tight_layout()
    fig.savefig(HERE/'replication.png', dpi=140)
    plt.close(fig)
    text = ['# B seed17 최종 재현 분석', '',
        '**seed7의 연속 통과는 seed17에서 재현되지 않았다.** seed17은 단일 정책 평가 기준도 통과하지 못했고, 최종300회는22/128달성·유지19.50%·오압현79.62%였다.', '',
        '같은 B 설정이며 seed만7→17이다. seed17 동seed 일반 초기화 기준선 학습은 없으므로 seed7 대비 차이를 B 효과의 인과 비교로 해석하지 않는다. 실제 native 초기값의 일반 seed17 초기화 대비71tensor 동일·cost head2개 정확0 검증은 기존 actual_initial_verification.json을 재사용하고 해시를 확인했다.', '',
        '| 반복 | seed7 달성/128 | seed17 달성/128 | seed17 유지 | seed17 오압현 | seed17 단일 기준 |',
        '|---:|---:|---:|---:|---:|---|']
    for update in UPDATES:
        a, b = [next(r for r in rows if r['seed'] == s and r['update'] == update) for s in (7, 17)]
        text.append('| %d | %d | %d | %.2f%% | %.2f%% | %s |' % (update, a['achieved'], b['achieved'], 100*b['mean_clean_fraction'], 100*b['mean_audible_wrong_fraction'], '통과' if b['passed'] else '미달'))
    text += ['', '![B 두 seed 고정 평가](replication.png)', '',
        '기존 수용 기준은 달성≥80%·유지≥70%·오압현≤10%·물리 실패≤5%를 인접 정책 평가2회에서 연속 충족하는 것이다. seed7은150–200·200–250회 통과, seed17은통과쌍이 없다. seed17 최고 달성은200회77/128(60.16%)이며 유지59.72%·오압현20.14%다. 기존 runner acceptance.json의 모든 단일평가·연속 판정을 원자료로 재계산해 일치를 확인했다.', '',
        'seed17의 초기 policy/zero는0/128, random6/128, reference108/128이다. reference 유지85.12%·오압현14.13%로 오압현 기준을 넘으며 정책 통과로 세지 않는다. 전체10평가×128=1,280시도는 실패를 포함한 배정환경 첫 시도다. 모두 물리·손목·전체 실패0이었다. 이는128개 독립 seed가 아니다.', '',
        '전체300회·1,228,800전이·5,632종료episode를 감사했다. 종료는 timeline_complete5,631건과201회 env81 wrist_severe1건이며 물리실패는0이다. 해당 비용9.316666603=기본5+남은시간4.066666603+미정산음예산0.25다. 전체 raw비용평균×전이수 합과 episode비용합이 정확히 일치한다. 심각 손목 이탈은 로컬1.6초에 발생했으며 마지막 안내초과 Gz0.11343m·심각지속0.1125초는 종료 경계 표본이다. 원인 관절·접촉이나 궤적 최대를 확정하지 않는다.', '',
        '1~200회 비용 advantage/value/손실은 정확0이다. 201회 실제 실패 비용 이후201~300회100개 업데이트에서 모두 nonzero다. 실제 비용 평균은201회만 nonzero이며 이후99회는0이다. cost_raw는 GAE advantage이므로 이후 nonzero를 새 실패로 세지 않는다. initial/200회 저장 cost head는0,250회와final은nonzero다. 초기·200회 저장본의 head0과 실제 비용 발생 이후 출력 변화,250회·최종 저장본의 nonzero 파라미터를 구분해 확인했다. 비용계수1·원래 실패비용은 유지했으며, seed7의 전기간 비용0과 구분한다. 순간 raw비용 min/max는 미저장이고201회 head 파라미터는 직접 저장되지 않았다.', '',
        'root의 실제 outer 종료코드0·wall1799.933957초, train완료/scene종료와10평가 전체완료/scene종료를 확인했다. seed7의11장면도 함께 다시 확인했다. 설정·원자료SHA·현재 입력핀·준비봉인·최종head 수치는 validation.json/final_audit.json, 전체 정책 평가 수치는 performance.csv에 있다. 원래 runner의 analysis/acceptance.json 및 모든 raw는 보존했다.', '',
        '결론의 범위는 고정 기타·유한 팔손목 teacher·중지4축·원곡1음·large128/H32/300의 B 두 seed다. 연속통과의 재현성은 확보되지 않았고 비용초기값만으로 성과·안정성·힘 문제의 원인을 확정할 수 없다. 자유 기타·전곡·압력·자연스러움·기본 채택의 근거로 확대하지 않는다. 활성 소스·기존 결과·봉인 입력을 수정하지 않았고 분석에 GPU를 사용하지 않았다.']
    with (HERE/'RESULTS.md').open('x') as f:
        f.write('\n'.join(text)+'\n')
    print(json.dumps(dict(completed=True, acceptance=acceptance, seed17_episodes=len(episodes), failure_cost=raw_sum, paths_verified=len(current), CUDA_initialized=False)))


if __name__ == '__main__':
    main()
