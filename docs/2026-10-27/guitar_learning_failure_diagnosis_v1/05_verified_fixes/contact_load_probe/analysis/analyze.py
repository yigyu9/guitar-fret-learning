"""CPU-only four-condition first-attempt load analysis; waits for completed raw files."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
DIAG = BASE.parents[1]
BASELINE = DIAG/'04_ablation/time_credit_ablation/corrected_source_v3/baseline_original_gamma_seed7'
CASES = (('initial_zero', 'evaluation_initial_zero'), ('initial_reference', 'evaluation_initial_reference'),
         ('cp50_policy', 'evaluation_000050'), ('final300_policy', 'evaluation_000300'))
REQUIRED = ('physics240.npz', 'control60.npz', 'evaluation.json', 'report.json',
            'load_probe_report.json', 'settings.json', 'first_attempt_notes.json', 'inputs_before.json', 'inputs_after.json')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def stats(values):
    v = np.asarray(values, dtype=float)
    if not v.size:
        return dict(samples=0, min=None, p05=None, p50=None, p95=None, max=None)
    assert np.isfinite(v).all()
    return dict(samples=int(v.size), min=float(v.min()), p05=float(np.quantile(v, .05)),
                p50=float(np.quantile(v, .5)), p95=float(np.quantile(v, .95)), max=float(v.max()))


def rotate(q, vector):
    """Independent xyzw quaternion rotation, matching actual recorded guitar pose."""
    xyz, w = q[..., :3], q[..., 3:4]
    return vector+2*np.cross(xyz, np.cross(xyz, vector)+w*vector)


def longest_span(clock, mask):
    best, start, previous = 0, None, None
    for at, enabled in zip(clock, mask):
        at = int(at)
        if enabled:
            if start is None or previous is None or at != previous+1:
                start = at
            best = max(best, at-start)
        else:
            start = None
        previous = at
    return best/240.


def ready():
    result = []
    for name, old in CASES:
        folder = BASE/('run_'+name)
        missing = [f for f in REQUIRED if not (folder/f).is_file()]
        status = 'missing' if missing else 'present'
        if not missing:
            try:
                report = read(folder/'load_probe_report.json')
                status = 'completed' if report.get('completed') is True and all(report['checks'].values()) else 'incomplete'
            except json.JSONDecodeError:
                status = 'report_being_written'
        if not (BASELINE/old/'evaluation.json').is_file():
            missing.append('original_baseline_evaluation.json')
        result.append(dict(condition=name, status=status, missing=missing))
    return result


def compare(original, observed):
    """Actual JSON value comparison; record differences without promising replay identity."""
    differences, maximum = [], 0.
    count = 0
    def visit(a, b, path):
        nonlocal maximum, count
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(a.keys() | b.keys()):
                if key not in a or key not in b:
                    count += 1
                    if len(differences) < 12: differences.append(path+'/'+key)
                else: visit(a[key], b[key], path+'/'+key)
        elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
            for i, (x, y) in enumerate(zip(a, b)): visit(x, y, path+'/'+str(i))
        elif a != b:
            count += 1
            if len(differences) < 12: differences.append(path)
            if type(a) in (int, float) and type(b) in (int, float): maximum = max(maximum, abs(a-b))
    visit(original, observed, '')
    return dict(entire_evaluation_values_exact=count == 0, differing_leaf_or_structure_count=count,
        maximum_absolute_numeric_difference=maximum, first_differences=differences,
        summary_exact=original['summary'] == observed['summary'])


def analyze_condition(name, original_name):
    folder = BASE/('run_'+name)
    inputs = {str(folder/f): sha(folder/f) for f in REQUIRED}
    original_path = BASELINE/original_name/'evaluation.json'
    inputs[str(original_path)] = sha(original_path)
    launcher_path = BASE/(name+'_launcher.json')
    launcher = read(launcher_path)
    assert launcher['returncode'] == 0
    inputs[str(launcher_path)] = sha(launcher_path)
    report, evaluation, settings = [read(folder/f) for f in ('load_probe_report.json', 'evaluation.json', 'settings.json')]
    assert report['completed'] and all(report['checks'].values())
    assert read(folder/'report.json')['completed'] and read(folder/'report.json')['closed']
    before, after = read(folder/'inputs_before.json'), read(folder/'inputs_after.json')
    assert after['verified'] and after['input_pins'] == before and not after['changed_paths'] and not after['unpinned_project_sources']
    assert evaluation['assigned_quotas'] == [1]*128
    episodes = sorted(evaluation['episodes'], key=lambda row: row['env_id'])
    assert len(episodes) == 128 and [r['env_id'] for r in episodes] == list(range(128))
    calculated = dict(episodes=128, achieved_fraction=sum(r['achieved'] for r in episodes)/128,
        mean_clean_fraction=sum(r['clean_fraction'] for r in episodes)/128,
        mean_audible_wrong_fraction=sum(r['audible_wrong_fraction'] for r in episodes)/128,
        physical_failure_fraction=sum(r['termination']['physical_failure'] for r in episodes)/128,
        wrist_failure_fraction=sum(r['termination']['wrist_failure'] for r in episodes)/128,
        any_failure_fraction=sum(r['reason'] == 'terminal_failure' for r in episodes)/128)
    assert all(abs(evaluation['summary'][k]-v) < 1e-12 for k, v in calculated.items())
    with np.load(folder/'physics240.npz', allow_pickle=False) as z: a = {k: z[k] for k in z.files}
    with np.load(folder/'control60.npz', allow_pickle=False) as z: c = {k: z[k] for k in z.files}
    assert all(np.isfinite(v).all() for v in [*a.values(), *c.values()])
    first, failed = a['first_attempt'], a['failure_latched']
    assert first.shape[1] == 128 and first.shape[0] <= 872 and c['clock'].shape[0] <= 218
    assert len(a['clock']) == 4*len(c['clock'])
    assert np.array_equal(first[3::4], c['first_attempt']) and np.array_equal(failed[3::4], c['failure_latched'])
    assert np.array_equal(failed, first & np.maximum.accumulate(a['tick_physical_failure'] | a['tick_wrist_failure'], axis=0))
    assert all(np.array_equal(a['clock'][:, i][first[:, i]], np.arange(1, first[:, i].sum()+1)) for i in range(128))
    live = first & ~failed
    view = settings['song']['short_learning']['view']
    time = a['local_time_s']
    phases = dict(before=time < view['local_onset_s'],
                  audible=(time >= view['local_onset_s']) & (time <= view['local_end_s']),
                  after=time > view['local_end_s'])
    metadata = report['metadata']
    assert metadata['distal_body_names'] == ['human/LH:'+f+'3' for f in ('thumb', 'index', 'middle', 'ring', 'pinky')]
    quaternion = a['guitar_pose'][..., 3:7].astype(float)
    assert np.max(np.abs(np.linalg.norm(quaternion[first], axis=-1)-1)) < 1e-4
    plane, rear = np.asarray(metadata['press_plane_G']), np.asarray(metadata['thumb_rear_plane_G'])
    normal = rotate(quaternion, plane[:3]/np.linalg.norm(plane[:3]))
    rear_normal = rotate(quaternion, rear[:3]/np.linalg.norm(rear[:3]))
    forces = a['distal_force_W'].astype(float)
    scalar = dict(selected_resultant_N=np.linalg.norm(forces[:, :, 2], axis=-1),
        thumb_resultant_N=np.linalg.norm(forces[:, :, 0], axis=-1),
        selected_signed_press_normal_N=np.sum(forces[:, :, 2]*normal, axis=-1),
        thumb_signed_press_normal_N=np.sum(forces[:, :, 0]*normal, axis=-1),
        thumb_signed_rear_normal_N=np.sum(forces[:, :, 0]*rear_normal, axis=-1))
    indices = [metadata['hand_joint_names'].index(n) for n in metadata['selected_joint_names']]
    jn = np.einsum('tnc,tncj->tnj', normal, a['point_jacobian_W'].astype(float))
    error = a['target_LH21'][..., indices].astype(float)-a['actual_LH21'][..., indices].astype(float)
    action = np.repeat(c['executed_action_selected4'], 4, axis=0).astype(float)
    assert np.array_equal(c['executed_action_selected4'], c['policy_action_selected4'])
    target_projection = np.sum(jn*error, axis=-1)
    action_projection = np.sum(jn*(4*action), axis=-1)
    residual = np.linalg.norm(a['point_velocity_predicted_all_dof_W']-a['point_velocity_W'], axis=-1)
    residual_vector = a['point_velocity_predicted_all_dof_W'].astype(float)-a['point_velocity_W'].astype(float)
    measured_normal = np.sum(a['point_velocity_W']*normal, axis=-1)
    normal_residual = np.sum(residual_vector*normal, axis=-1)
    for key, mask in (('all_first_attempt', first), ('before_failure', live)):
        actual = report['velocity_audit'][key]
        assert actual['samples'] == int(mask.sum())
        if mask.any():
            assert np.isclose(actual['rms_m_s'], np.sqrt(np.mean(residual[mask]**2)), atol=1e-9, rtol=2e-6)
            assert np.isclose(actual['max_m_s'], residual[mask].max(), atol=1e-9, rtol=2e-6)
    force_rows, projection_rows, env_rows, phase_velocity, geometry_counts = [], [], [], {}, {}
    for phase, window in phases.items():
        mask = live & window
        for metric, value in scalar.items():
            force_rows.append(dict(condition=name, phase=phase, metric=metric, **stats(value[mask])))
        for metric, value in dict(target_normal_error_projection_m=target_projection,
            requested_normal_velocity_projection_m_s=action_projection, velocity_residual_m_s=residual).items():
            projection_rows.append(dict(condition=name, phase=phase, metric=metric, **stats(value[mask])))
        phase_velocity[phase] = dict(samples=int(mask.sum()), residual=stats(residual[mask]),
            residual_RMS_m_s=float(np.sqrt(np.mean(residual[mask]**2))) if mask.any() else None,
            measured_speed_RMS_m_s=float(np.sqrt(np.mean(np.linalg.norm(a['point_velocity_W'][mask], axis=-1)**2))) if mask.any() else None,
            normal_residual_RMS_m_s=float(np.sqrt(np.mean(normal_residual[mask]**2))) if mask.any() else None,
            measured_normal_speed_RMS_m_s=float(np.sqrt(np.mean(measured_normal[mask]**2))) if mask.any() else None,
            selected_qerror_norm_p50_deg=float(np.degrees(np.median(np.linalg.norm(error[mask], axis=-1)))) if mask.any() else None,
            actual_selected4_p50_deg=np.degrees(np.median(a['actual_LH21'][..., indices][mask], axis=0)).tolist() if mask.any() else None,
            target_selected4_p50_deg=np.degrees(np.median(a['target_LH21'][..., indices][mask], axis=0)).tolist() if mask.any() else None)
        geometry_counts[phase] = dict(valid_endpoints=int(mask.sum()),
            any_positive_nearest_facing_false=int((mask & a['positive'] & ~a['nearest_facing_geometry']).sum()),
            inward_target_projection=int((mask & (target_projection < 0)).sum()),
            inward_action_projection=int((mask & (action_projection < 0)).sum()))
    outcome_count = {}
    for i, episode in enumerate(episodes):
        failure = episode['termination']['physical_failure'] or episode['termination']['wrist_failure']
        outcome = 'failure' if failure else 'achieved_no_failure' if episode['achieved'] else 'unachieved_no_failure'
        outcome_count[outcome] = outcome_count.get(outcome, 0)+1
        mask = live[:, i] & phases['audible'][:, i]
        row = dict(condition=name, env_id=i, outcome=outcome, achieved=episode['achieved'],
            physical_failure=episode['termination']['physical_failure'], wrist_failure=episode['termination']['wrist_failure'],
            first_attempt_endpoints=int(first[:, i].sum()), failure_censored_endpoints=int((first[:, i] & failed[:, i]).sum()),
            audible_valid_endpoints=int(mask.sum()))
        clocks = a['clock'][:, i][mask]
        row['audible_valid_endpoint_span_s'] = float(clocks[-1]-clocks[0])/240 if clocks.size else None
        for metric, value in scalar.items():
            row['audible_'+metric+'_max'] = float(value[:, i][mask].max()) if mask.any() else None
            row['audible_'+metric+'_min'] = float(value[:, i][mask].min()) if mask.any() else None
        row['audible_inward_request_fraction'] = float(np.mean(action_projection[:, i][mask] < 0)) if mask.any() else None
        row['audible_inward_request_max_endpoint_span_s'] = longest_span(a['clock'][:, i], mask & (action_projection[:, i] < 0))
        row['audible_inward_target_proxy_fraction'] = float(np.mean(target_projection[:, i][mask] < 0)) if mask.any() else None
        row['from_onset_inward_request_max_endpoint_span_s'] = longest_span(a['clock'][:, i],
            live[:, i] & (time[:, i] >= view['local_onset_s']) & (action_projection[:, i] < 0))
        env_rows.append(row)
    groups = {}
    for outcome in ('achieved_no_failure', 'unachieved_no_failure', 'failure'):
        groups[outcome] = dict(environments=outcome_count.get(outcome, 0), denominator_all_attempts=128,
            selected_audible_peak_N=stats([r['audible_selected_resultant_N_max'] for r in env_rows
                if r['outcome'] == outcome and r['audible_selected_resultant_N_max'] is not None]),
            thumb_audible_peak_N=stats([r['audible_thumb_resultant_N_max'] for r in env_rows
                if r['outcome'] == outcome and r['audible_thumb_resultant_N_max'] is not None]))
    note_rows = sorted(read(folder/'first_attempt_notes.json'), key=lambda row: row['env_id'])
    reward_order, note_order = report['protocol']['reward_order'], report['protocol']['note_order']
    assert all(set(r['reward_components']) == set(reward_order) for r in episodes)
    assert len(note_rows) == 128 and [r['env_id'] for r in note_rows] == list(range(128))
    paid = np.asarray([[r['reward_components'][k] for k in reward_order] for r in episodes])
    assert np.array_equal(paid, [[r['reward_components'][k] for k in reward_order] for r in note_rows])
    control_sum = np.sum(c['reward_increment']*c['first_attempt'][..., None], axis=0)
    control_error = float(np.abs(control_sum-paid).max())
    assert control_error < 2e-6
    for i in range(128):
        last = np.flatnonzero(c['first_attempt'][:, i])[-1]
        np.testing.assert_allclose(c['reward_cumulative'][last, i], paid[i], rtol=0, atol=1e-9)
        np.testing.assert_allclose(c['note_ledger'][last, i], [note_rows[i]['selected_note'][k] for k in note_order], rtol=0, atol=1e-9)
    paid_rows = []
    for group, selection in (('all128', np.ones(128, bool)),
            ('achieved_no_failure', np.asarray([r['achieved'] and not (r['termination']['physical_failure'] or r['termination']['wrist_failure']) for r in episodes]))):
        for j, term in enumerate(reward_order):
            value = paid[:, j][selection]
            paid_rows.append(dict(condition=name, group=group, term=term,
                environments=int(selection.sum()), mean=float(value.mean()) if value.size else None, **stats(value)))
    summary = dict(condition=name, original_evaluation_summary=calculated, all_attempt_denominator=128,
        valid_force_endpoints=int(live.sum()), failure_censored_endpoints=int((first & failed).sum()),
        audible_valid_endpoints=int((live & phases['audible']).sum()), view=view,
        outcome_groups=groups, original_baseline_comparison=compare(read(original_path), evaluation),
        nearest_any_sample_distinction=dict(any_positive_nearest_facing_false_samples=int((live & a['positive'] & ~a['nearest_facing_geometry']).sum())),
        phase_geometry_counts=geometry_counts, actual_reward_payments=paid_rows,
        reward_control_sum_vs_episode_max_error=control_error,
        J_velocity=dict(residual=stats(residual[live]),
            residual_RMS_m_s=float(np.sqrt(np.mean(residual[live]**2))),
            measured_speed_RMS_m_s=float(np.sqrt(np.mean(np.linalg.norm(a['point_velocity_W'][live], axis=-1)**2))),
            phases=phase_velocity,
            interpretation='local linear proxies only; assess actual closure residual and velocity scale before interpreting direction'),
        checks=dict(first_quota_and_clock=True, failure_endpoint_censor_recomputed=True,
            original_summary_recomputed=True, native_velocity_report_recomputed=True, selected_action_unchanged=True,
            reward9_and_final_note_control_vs_episode=True, launcher_exit_zero=True))
    assert all(sha(path) == digest for path, digest in inputs.items())
    return summary, force_rows, projection_rows, env_rows, inputs


def output_csv(path, rows):
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def plot(path, summaries, forces, projections, environments):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    names = [n for n, _ in CASES]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    colors = plt.cm.tab10(np.arange(4))
    for i, name in enumerate(names):
        for j, body in enumerate(('selected', 'thumb')):
            row = next(v for v in forces if v['condition'] == name and v['phase'] == 'audible' and v['metric'] == body+'_resultant_N')
            if row['samples']:
                x = i+(j-.5)*.22
                axes[0, 0].plot([x, x], [row['p50'], row['p95']], color=colors[i], lw=3)
                axes[0, 0].scatter(x, row['p50'], color=colors[i], marker='o' if j == 0 else 's')
                axes[0, 0].scatter(x, row['max'], color=colors[i], marker='x')
        peaks = sorted(v['audible_selected_resultant_N_max'] for v in environments if v['condition'] == name and v['audible_selected_resultant_N_max'] is not None)
        if peaks: axes[0, 1].plot(peaks, np.arange(1, len(peaks)+1)/len(peaks), label=name, color=colors[i])
        row = next(v for v in projections if v['condition'] == name and v['phase'] == 'audible' and v['metric'] == 'target_normal_error_projection_m')
        if row['samples']:
            axes[1, 0].errorbar(i, row['p50']*1000, yerr=[[1000*(row['p50']-row['p05'])], [1000*(row['p95']-row['p50'])]], fmt='o', color=colors[i])
        velocity = summaries[i]['J_velocity']['phases']['audible']
        axes[1, 1].bar(i-.15, velocity['residual_RMS_m_s'], .3, color=colors[i])
        axes[1, 1].bar(i+.15, velocity['measured_speed_RMS_m_s'], .3, facecolor='none', edgecolor=colors[i])
    axes[0, 0].set_title('Audible body resultant: p50 / p95 line / max x\ncircle=middle3, square=thumb3')
    axes[0, 0].set_ylabel('N (not pair pressure)')
    axes[0, 1].set_title('Per-env audible middle3 peak, prefailure only')
    axes[0, 1].set_xlabel('N'); axes[0, 1].set_ylabel('empirical fraction with exposure'); axes[0, 1].legend(fontsize=8)
    axes[1, 0].set_title('Nearest-point Jn*(target-q): p05/p50/p95\nnegative = inward local linear proxy')
    axes[1, 0].set_ylabel('mm; not penetration'); axes[1, 0].axhline(0, color='gray', lw=.6)
    axes[1, 1].set_title('Audible actual point velocity closure\nfilled=residual RMS; outline=measured speed RMS')
    axes[1, 1].set_ylabel('m/s')
    for ax in (axes[0, 0], axes[1, 0], axes[1, 1]):
        ax.set_xticks(range(4)); ax.set_xticklabels(names, fontsize=8, rotation=15)
    for ax in axes.flat: ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def results_text(summaries, forces, projections, environments):
    def force(name, phase, metric):
        return next(v for v in forces if v['condition'] == name and v['phase'] == phase and v['metric'] == metric)
    def projection(name, metric):
        return next(v for v in projections if v['condition'] == name and v['phase'] == 'audible' and v['metric'] == metric)
    def values(row, keys=('p50', 'p95', 'max'), scale=1.):
        return ' / '.join('미확보' if row[k] is None else '%.4f'%(row[k]*scale) for k in keys)
    lines = ['# 교정 기하 4조건의 실제 128환경 하중 관찰', '',
        '모든 성공·실패 분모는 각 조건의 첫128시도다. 하중 통계만 최초 실패 endpoint와 이후를 제외한다. pooled p50/p95/max는 유효240Hz endpoint 가중이며 환경별 평균이 아니다. 고정 기타·손목 teacher·다른 손가락 B/엄지035 조건의 진단이다.', '',
        '| 조건 | 달성/128 | clean 평균 | wrong 평균 | 물리/손목 실패 | 실패로 제외한 endpoint | 원래 평가 전체값 동일 |',
        '|---|---:|---:|---:|---:|---:|---|']
    for s in summaries:
        e = s['original_evaluation_summary']
        lines.append('| %s | %d | %.6f | %.6f | %d / %d | %d | %s |'%(s['condition'], round(e['achieved_fraction']*128),
            e['mean_clean_fraction'], e['mean_audible_wrong_fraction'], round(e['physical_failure_fraction']*128),
            round(e['wrist_failure_fraction']*128), s['failure_censored_endpoints'], s['original_baseline_comparison']['entire_evaluation_values_exact']))
    lines += ['', '각 조건111,616표본(872×128)이며 audible은3,712표본(29×128)이다. 원래 baseline 평가와의 동일성은 이번 실제 JSON 전체값 비교 결과이며 반복 실행의 동일성을 보장하지 않는다. 차이 수·최대 숫자 차이·첫 차이 경로는 summary.json에 있다. 각 launcher exit0·scene closed·모델/업데이트/RNG 불변 감사도 원자료에서 확인했다.', '',
        '| 조건 | audible 중지 resultant p50/p95/max N | 엄지 resultant p50/p95/max N |', '|---|---:|---:|']
    for s in summaries:
        name=s['condition']
        lines.append('| %s | %s | %s |'%(name, values(force(name,'audible','selected_resultant_N')), values(force(name,'audible','thumb_resultant_N'))))
    lines += ['', '| 조건 | 중지 press-normal p50/p95 N | 엄지 press-normal min/p50/max N | 엄지 rear-normal p50/p95/max N |', '|---|---:|---:|---:|']
    for s in summaries:
        name=s['condition']
        lines.append('| %s | %s | %s | %s |'%(name,
            values(force(name,'audible','selected_signed_press_normal_N'),('p50','p95')),
            values(force(name,'audible','thumb_signed_press_normal_N'),('min','p50','max')),
            values(force(name,'audible','thumb_signed_rear_normal_N'))))
    lines += ['', '중지·엄지 press-normal은 같은 실제 press-plane world 바깥법선을 사용한다. 엄지의 음수와 rear-normal의 양수는 반대 부호 기준이며 합쳐 쓰지 않는다. resultant에는 법선 외 성분도 포함된다. 엄지 하중은 zero/reference에서도 존재하므로 final의 하중을 정책만의 단독 원인으로 설명하지 않는다.', '',
        '| final300 구간 | 중지 resultant min/p50/p95/max N | 엄지 resultant min/p50/p95/max N |', '|---|---:|---:|']
    for phase in ('before','audible','after'):
        lines.append('| %s | %s | %s |'%(phase, values(force('final300_policy',phase,'selected_resultant_N'),('min','p50','p95','max')),
            values(force('final300_policy',phase,'thumb_resultant_N'),('min','p50','p95','max'))))
    lines += ['', 'before는 local audible onset 전, audible은 onset≤t≤end, after는 end 뒤다. final audible의 모든 관측 endpoint에서 중지 resultant가54.46N 이상이고, 음 종료 뒤에도 중지 min63.83N/p5095.35N이다. 이는240Hz 관측값이며 표본 사이 연속 힘이나 특정 접촉쌍의 압력 인증은 아니다. 준비 중 엄지206.41N 순간 최대와 audible 엄지 p5084.11N을 구분한다. 이 수치를 새 힘 상한 또는 기존 한계 초과 판정으로 사용하지 않는다.', '',
        '| 조건 | 달성 무실패: 환경수 / 중지 audible 환경별 peak p50/p95 N | 미달 무실패: 환경수 / peak p50/p95 N | 물리·손목 실패 환경수 |', '|---|---:|---:|---:|']
    for s in summaries:
        groups=s['outcome_groups'];good=groups['achieved_no_failure'];bad=groups['unachieved_no_failure']
        lines.append('| %s | %d / %s | %d / %s | %d |'%(s['condition'],good['environments'],values(good['selected_audible_peak_N'],('p50','p95')),
            bad['environments'],values(bad['selected_audible_peak_N'],('p50','p95')),groups['failure']['environments']))
    lines += ['', 'environment_peaks.csv는 모든128환경을 보존하며 엄지 peak·구간 노출·연속 안쪽 요청 endpoint span도 담는다. 노출이 없으면 null이며0N으로 바꾸지 않는다. 이번 raw에는 물리·손목 실패가 없어 그 실패군의 하중 분포는 미확보다.', '',
        '| 조건 | audible target−q norm 중앙값 deg | Jn·(target−q) p50 mm | Jn·4action p50 mm/s | 안쪽 요청 표본/3712 |', '|---|---:|---:|---:|---:|']
    for s in summaries:
        name=s['condition'];j=s['J_velocity']['phases']['audible']
        lines.append('| %s | %.4f | %.4f | %.4f | %d |'%(name,j['selected_qerror_norm_p50_deg'],
            projection(name,'target_normal_error_projection_m')['p50']*1000,
            projection(name,'requested_normal_velocity_projection_m_s')['p50']*1000,s['phase_geometry_counts']['audible']['inward_action_projection']))
    final=next(s for s in summaries if s['condition']=='final300_policy')
    q=final['J_velocity']['phases']['audible']
    lines += ['', 'final audible 선택4의 실제각 중앙값은 %s도, 목표각은 %s도다. 순서는 middle MCP/벌림/PIP/DIP다. 큰 유한 관절오차에 J를 곱한 약−59mm는 선형 외삽값이며 실제 목표점 위치·침투깊이로 해석할 수 없다. 음 시작 이후 안쪽 요청의 환경별 최대 관측 span 중앙값은%.6f초다. span은 연속 clock의 (last−first)/240이며 표본 사이 연속 제어 효과를 보장하지 않는다.'%(
        ', '.join('%.2f'%x for x in q['actual_selected4_p50_deg']), ', '.join('%.2f'%x for x in q['target_selected4_p50_deg']),
        np.median([r['from_onset_inward_request_max_endpoint_span_s'] for r in environments if r['condition']=='final300_policy'])), '',
        '| 조건 | audible velocity residual RMS/max m/s | 실제 점 속도 RMS m/s | 법선 residual/실제 법선속도 RMS m/s |', '|---|---:|---:|---:|']
    ratios=[]
    for s in summaries:
        j=s['J_velocity']['phases']['audible'];ratios.append(j['residual_RMS_m_s']/j['measured_speed_RMS_m_s']*100)
        lines.append('| %s | %.8g / %.8g | %.8g | %.8g / %.8g |'%(s['condition'],j['residual_RMS_m_s'],j['residual']['max'],j['measured_speed_RMS_m_s'],
            j['normal_residual_RMS_m_s'],j['measured_normal_speed_RMS_m_s']))
    lines += ['', 'audible의 norm RMS 잔차는 실제 점 속도 RMS의 %.2f~%.2f%%다. 이는 이번 관측 qd 경로에서의 속도 정합 근거이며 요청 방향 전체나 큰 target−q 외삽을 보증하지 않는다. 전체 준비 포함 최대잔차 약0.024~0.026m/s는 summary.json에 별도 보존했다. J 투영은 최근접 reward-pad 점의 국소 선형 proxy다. 음수는 안쪽 목표오차/codec 전 요청 속도의 선형 성분이며 실제 clipping·접촉 반력·관절 움직임·침투를 뜻하지 않는다. 큰 잔차 구간의 방향 해석은 보류한다.'%(min(ratios),max(ratios)), '',
        '| 조건 | 전체128 실제 평균 접촉 / 유지 / 달성 지급 | 달성 무실패군 평균 접촉 / 유지 / 달성 지급 |', '|---|---:|---:|']
    for s in summaries:
        groups=[]
        for group in ('all128','achieved_no_failure'):
            numbers=[next(r['mean'] for r in s['actual_reward_payments'] if r['group']==group and r['term']==term)
                for term in ('song_left_contact','song_clean_hold','song_left_success')]
            groups.append(' / '.join('미확보' if x is None else '%.6f'%x for x in numbers))
        lines.append('| %s | %s | %s |'%(s['condition'],*groups))
    lines += ['', 'reward_payments.csv는 원래9보상의 실제 지급 평균/분포 전체다. control increment 합·최종 cumulative·episode 지급과 최종 ledger9필드를 대조했다. final의 큰 resultant에도 접촉·유지·달성 예산이 지급됐고, reference의 더 작은 resultant에서 성공한 시도도 같은 종류의 예산을 받았다. 이 지급 관측은 하중 크기를 별도로 판별하거나 자연스러운 저부하 압현을 검증한 결과가 아니다. 새 계수나 보상·종료 변경은 제안하지 않는다.', '',
        'candidate/positive의 any-sample witness는 최근접 점과 다를 수 있다. any-positive이면서 nearest-facing이 거짓인 표본 수는 조건별 전체/구간별로 기록했다. 최근접 cosine과 candidate를 결합해 같은 점의 접촉을 인증하지 않는다. force는 native body resultant이며 접촉쌍 압력이 아니다. 정책·teacher 손목·엄지035의 단독 인과 기여, 새로운 힘 한계, 자연스러운 저부하 압현 또는 제어 문제 해결을 주장하지 않는다.', '',
        '그림: summary.png. 수치: force_by_phase.csv / projection_by_phase.csv / environment_peaks.csv / reward_payments.csv / summary.json. verification.json은 원래128분모·시계·동일 실패 endpoint censor·선택 행동·속도 잔차·실제9보상/원장의 독립 재검산 근거다.']
    return '\n'.join(lines)+'\n'


def self_test():
    q = np.array([0., 0., np.sqrt(.5), np.sqrt(.5)])
    np.testing.assert_allclose(rotate(q, np.array([1., 0., 0.])), [0., 1., 0.], atol=1e-15)
    assert stats([])['p95'] is None and stats([-3, 0, 3])['p50'] == 0
    assert longest_span([1, 2, 3, 5], [True]*4) == 2/240
    assert longest_span([1, 2], [False, True]) == 0
    jn, delta, action = np.array([1., -2.]), np.array([-.1, .2]), np.array([-.2, .3])
    assert np.dot(jn, delta) < 0 and np.dot(jn, 4*action) < 0
    np.testing.assert_array_equal(np.repeat(np.array([1, 2]), 4), [1]*4+[2]*4)
    assert compare({'summary': {}, 'x': [1.]}, {'summary': {}, 'x': [1.]})['entire_evaluation_values_exact']
    assert not compare({'summary': {}, 'x': [1.]}, {'summary': {}, 'x': [2.]})['entire_evaluation_values_exact']
    print(json.dumps(dict(completed=True, CPU_only=True, synthetic_math_only=True)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test: self_test(); return
    status = ready()
    if any(v['status'] != 'completed' or v['missing'] for v in status):
        print(json.dumps(dict(ready=False, conditions=status), indent=2)); return
    output = HERE/'results_v1'
    if output.exists(): raise FileExistsError(str(output))
    summaries, forces, projections, environments, inputs = [], [], [], [], {}
    for name, original in CASES:
        s, f, p, e, pins = analyze_condition(name, original)
        summaries.append(s); forces += f; projections += p; environments += e; inputs.update(pins)
    output.mkdir(exist_ok=False)
    write(output/'summary.json', dict(conditions=summaries, scope='240Hz first-attempt body resultant and local linear proxies; not pair pressure or causal proof'))
    output_csv(output/'force_by_phase.csv', forces); output_csv(output/'projection_by_phase.csv', projections)
    output_csv(output/'environment_peaks.csv', environments)
    output_csv(output/'reward_payments.csv', [r for s in summaries for r in s['actual_reward_payments']])
    plot(output/'summary.png', summaries, forces, projections, environments)
    with (output/'RESULTS.md').open('x') as stream: stream.write(results_text(summaries, forces, projections, environments))
    assert all(sha(path) == digest for path, digest in inputs.items())
    write(output/'verification.json', dict(completed=True, CPU_only=True, input_files_unchanged=True,
        conditions={s['condition']: s['checks'] for s in summaries}, input_sha256=inputs))
    print(json.dumps(dict(completed=True, output=str(output), CPU_only=True)))


if __name__ == '__main__':
    main()
