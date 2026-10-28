"""CPU-only analysis of three fixed-tape native runs; never starts a simulator."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SOURCE = BASE.parent/'contact_load_probe/run_final300_policy'
HELPER = SOURCE.parent/'analysis/analyze.py'
spec = importlib.util.spec_from_file_location('preserved_load_analysis_helpers', HELPER)
helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
read, sha, write, stats, rotate, output_csv = [getattr(helper, k) for k in ('read', 'sha', 'write', 'stats', 'rotate', 'output_csv')]
CASES = ('original', 'no_new_inward', 'no_new_inward_and_relax')
FILES = ('physics240.npz', 'control60.npz', 'target_control60.npz', 'evaluation.json', 'first_attempt_notes.json',
    'load_probe_report.json', 'target_windup_report.json', 'report.json', 'settings.json', 'inputs_before.json', 'inputs_after.json')


def arrays(path):
    with np.load(path, allow_pickle=False) as z: return {k: z[k] for k in z.files}


def exact(a, b, prefix=None):
    checks = {k: k in b and np.array_equal(v if prefix is None else v[:prefix],
        b[k] if prefix is None else b[k][:prefix]) for k, v in a.items()}
    checks['same_fields'] = set(a) == set(b)
    return checks


def phases(time, view):
    return dict(before=time < view['local_onset_s'], audible=(time >= view['local_onset_s']) & (time <= view['local_end_s']),
        after=time > view['local_end_s'])


def ready():
    status = []
    for name in CASES:
        required = [BASE/('run_'+name)/f for f in FILES]+[BASE/(name+'_launcher.json')]
        missing = [str(p) for p in required if not p.is_file()]
        status.append(dict(condition=name, ready=not missing, missing=missing))
    return status


def target_checks(t, threshold, mode):
    """Recompute every first-control gate, geometry dot and numerical constraint."""
    first = t['first_attempt']; gate = t['gate']
    expected = (first & (t['start_clock'] >= 480) & ~t['prior_failure'] & ~t['stale_J'] & ~t['invalid_state']
        & ~t['invalid_J'] & (t['signed_normal_force_N'] > threshold))
    assert np.array_equal(gate, expected)
    g = np.einsum('tnc,tncj->tnj', t['normal_W'].astype(float), t['point_J'].astype(float))
    np.testing.assert_allclose(t['normal_J'], g, atol=1e-12, rtol=1e-12)
    assert np.array_equal(t['zero_J'], gate & (np.abs(g).max(-1) == 0))
    old, raw, final, actual = [t[k].astype(float) for k in ('old_target4', 'raw_target4', 'final_target4', 'actual4')]
    delta, request = final-old, raw-old
    for key, value in dict(old_normal_error_m=np.sum(g*(old-actual), -1), final_normal_error_m=np.sum(g*(final-actual), -1),
            raw_normal_increment_m=np.sum(g*request, -1), filtered_normal_increment_m=np.sum(g*delta, -1)).items():
        np.testing.assert_allclose(t[key], value, atol=1e-12, rtol=1e-12)
    displacement = np.einsum('tncj,tnj->tnc', t['point_J'].astype(float), final-raw)
    tangent = displacement-t['normal_W']*np.sum(displacement*t['normal_W'], -1, keepdims=True)
    np.testing.assert_allclose(t['tangent_change_m'], tangent, atol=1e-12, rtol=1e-12)
    L, U = t['lower_increment'], t['upper_increment']
    coordinate_tolerance = 8*np.finfo(np.float32).eps*np.maximum.reduce([np.abs(old), np.abs(raw), np.abs(final), np.ones_like(old)])
    excess = np.maximum.reduce([L-delta, delta-U, np.zeros_like(delta)])
    assert (excess[first] <= coordinate_tolerance[first]).all()
    assert (np.abs(delta)[first] <= 4/60+coordinate_tolerance[first]).all()
    np.testing.assert_allclose(t['box_excess_rad'][first], excess.max(-1)[first], atol=1e-15, rtol=1e-12)
    np.testing.assert_allclose(t['coordinate_tolerance_rad'][first], coordinate_tolerance.max(-1)[first], atol=1e-15, rtol=1e-12)
    changed = np.any(final != raw, -1)
    assert not changed[first & (t['start_clock'] < 480)].any() and not changed[first & ~gate].any()
    if mode == 'original': assert not changed[first].any()
    else:
        capacity = np.sum(g*np.where(g > 0, U, np.where(g < 0, L, 0)), -1)
        beta = np.minimum(np.maximum(0, -np.sum(g*(old-actual), -1)), capacity) if mode.endswith('relax') else np.zeros_like(capacity)
        np.testing.assert_allclose(t['capacity_m'][gate], capacity[gate], atol=1e-12, rtol=1e-12)
        np.testing.assert_allclose(t['beta_m'][gate], beta[gate], atol=1e-12, rtol=1e-12)
        residual = np.sum(g*delta, -1)-beta
        np.testing.assert_allclose(t['halfspace_residual_m'][gate], residual[gate], atol=1e-12, rtol=1e-12)
        scale = np.max(np.abs(g), -1)
        normalized_beta = np.divide(beta, scale, out=np.zeros_like(beta), where=scale > 0)
        normalized_g = np.divide(g, scale[..., None], out=np.zeros_like(g), where=scale[..., None] > 0)
        tolerance = (np.sum(np.abs(normalized_g)*coordinate_tolerance, -1)+8*np.finfo(np.float32).eps*np.abs(normalized_beta))*scale
        np.testing.assert_allclose(t['halfspace_tolerance_m'][gate], tolerance[gate], atol=1e-15, rtol=1e-12)
        assert (residual[gate] >= -tolerance[gate]).all()
    assert not t['memory_submit_error_rad'][first].any() and not t['other_target_change_rad'][first].any()
    return changed, coordinate_tolerance


def analyze(name, source_a, source_c, source_eval, source_notes, original_t):
    folder = BASE/('run_'+name)
    inputs = {str(folder/f): sha(folder/f) for f in FILES}
    launcher = BASE/(name+'_launcher.json'); inputs[str(launcher)] = sha(launcher)
    assert read(launcher)['returncode'] == 0
    a, c, t = [arrays(folder/f) for f in FILES[:3]]
    assert all(np.isfinite(v).all() for group in (a, c, t) for v in group.values())
    load, target, base = [read(folder/f) for f in ('load_probe_report.json', 'target_windup_report.json', 'report.json')]
    before, after = read(folder/'inputs_before.json'), read(folder/'inputs_after.json')
    assert after['verified'] and after['input_pins'] == before and not after['changed_paths'] and not after['unpinned_project_sources']
    assert base['closed'] and load['scene']['closed']
    evaluation, notes = read(folder/'evaluation.json'), sorted(read(folder/'first_attempt_notes.json'), key=lambda r: r['env_id'])
    episodes = sorted(evaluation['episodes'], key=lambda r: r['env_id'])
    assert evaluation['assigned_quotas'] == [1]*128 and [r['env_id'] for r in episodes] == list(range(128))
    assert [r['env_id'] for r in notes] == list(range(128))
    first, failed = a['first_attempt'], a['failure_latched']
    assert first.shape[1] == 128 and first.shape[0] <= 872 and len(c['clock']) <= 218
    assert len(a['clock']) == 4*len(c['clock']) == 4*len(t['clock'])
    assert np.array_equal(first[3::4], c['first_attempt']) and np.array_equal(c['first_attempt'], t['first_attempt'])
    assert np.array_equal(failed, first & np.maximum.accumulate(a['tick_physical_failure'] | a['tick_wrist_failure'], axis=0))
    assert np.array_equal(failed[3::4], c['failure_latched']) and np.array_equal(t['post_failure'], c['failure_latched'])
    assert np.array_equal(c['clock'], t['clock']) and (t['start_clock'][t['first_attempt']] == t['clock'][t['first_attempt']]-4).all()
    assert all(np.array_equal(a['clock'][:, i][first[:, i]], np.arange(1, first[:, i].sum()+1)) for i in range(128))
    with np.load(BASE/'fixed_inputs.npz') as fixed:
        tape, local = fixed['action4'], fixed['point_local']
    mask = c['first_attempt']
    assert np.array_equal(c['executed_action_selected4'][mask], tape[:len(mask)][mask])
    assert np.array_equal(t['tape_action4'][mask], tape[:len(mask)][mask])
    changed, tolerance = target_checks(t, read(BASE/'precommit.json')['force_threshold_N'], name)
    live = first & ~failed; control_live = mask & ~c['failure_latched']
    short = read(folder/'settings.json')['song']['short_learning']
    view = short['view']
    rotation_length_scale = short['wrist_control']['rotation_length_scale_m']
    assert rotation_length_scale > 0
    windows, control_windows = phases(a['local_time_s'], view), phases(t['start_clock']/240, view)
    metadata = load['metadata']; guitar_q = a['guitar_pose'][..., 3:7].astype(float)
    def normal(plane):
        p = np.asarray(plane, float)[:3]; return rotate(guitar_q, p/np.linalg.norm(p))
    assert np.max(np.abs(np.linalg.norm(guitar_q[first], axis=-1)-1)) < 1e-4
    press, rear = normal(metadata['press_plane_G']), normal(metadata['thumb_rear_plane_G'])
    force = a['distal_force_W'].astype(float)
    scalar = dict(selected_resultant_N=np.linalg.norm(force[:, :, 2], axis=-1), thumb_resultant_N=np.linalg.norm(force[:, :, 0], axis=-1),
        selected_signed_press_N=np.sum(force[:, :, 2]*press, -1), thumb_signed_press_N=np.sum(force[:, :, 0]*press, -1), thumb_signed_rear_N=np.sum(force[:, :, 0]*rear, -1))
    force_rows = [dict(condition=name, phase=phase, metric=metric, **stats(v[live & window]))
        for phase, window in windows.items() for metric, v in scalar.items()]
    gate = t['gate'] & control_live
    residual = np.linalg.norm(t['predicted_velocity_W'].astype(float)-t['point_velocity_W'], axis=-1)
    original_arm = np.zeros_like(t['arm_request12']); comparable = np.zeros_like(mask)
    overlap = min(len(mask), len(original_t['clock']))
    original_arm[:overlap] = original_t['arm_request12'][:overlap]
    comparable[:overlap] = original_t['first_attempt'][:overlap] & ~original_t['post_failure'][:overlap]
    arm_delta = np.linalg.norm(t['arm_request12'].astype(float)-original_arm, axis=-1)
    control_metrics = {k:t[k] for k in ('old_normal_error_m','final_normal_error_m','raw_normal_increment_m','filtered_normal_increment_m')}
    control_metrics.update(tangent_change_norm_m=np.linalg.norm(t['tangent_change_m'], axis=-1),
        target_change_norm_rad=np.linalg.norm(t['final_target4'].astype(float)-t['raw_target4'], axis=-1),
        fixed_point_velocity_residual_m_s=residual, fixed_point_actual_speed_m_s=np.linalg.norm(t['point_velocity_W'], axis=-1))
    control_rows, counts = [], {}
    for phase, window in control_windows.items():
        valid, exposed = control_live & window, gate & window
        counts[phase] = dict(first_controls=int((mask & window).sum()), failure_censored_controls=int((mask & window & ~control_live).sum()),
            eligible_controls=int(exposed.sum()), changed_eligible_controls=int((exposed & changed).sum()),
            gate_zero_J_controls=int((exposed & t['zero_J']).sum()),
            box_boundary_coordinates=int(((np.minimum(np.abs(t['final_target4'].astype(float)-t['old_target4']-t['lower_increment']),
                np.abs(t['final_target4'].astype(float)-t['old_target4']-t['upper_increment'])) <= tolerance) & valid[..., None]).sum()),
            rate_boundary_coordinates=int(((np.abs(np.abs(t['final_target4'].astype(float)-t['old_target4'])-4/60) <= tolerance) & valid[..., None]).sum()),
            **{k:int((mask & window & t[k]).sum()) for k in ('gate','prior_failure','stale_J','invalid_state','invalid_J','post_failure')})
        for metric, value in control_metrics.items(): control_rows.append(dict(condition=name, phase=phase, population='gate_true_before_failure', metric=metric, **stats(value[exposed])))
        control_rows.append(dict(condition=name, phase=phase, population='matched_original_first_controls_before_failure',
            metric='arm_request_difference_vs_original_rad', **stats(arm_delta[valid & comparable])))
        counts[phase]['arm_comparable_controls'] = int((valid & comparable).sum())
        for metric, value in dict(wrist_position_error_m=np.linalg.norm(t['wrist_error6'][..., :3], axis=-1), wrist_orientation_error_rad=np.linalg.norm(t['wrist_error6'][..., 3:], axis=-1)/rotation_length_scale).items():
            control_rows.append(dict(condition=name, phase=phase, population='all_controls_before_failure', metric=metric, **stats(value[valid])))
        counts[phase]['fixed_point_velocity_residual_RMS_m_s'] = float(np.sqrt(np.mean(residual[exposed]**2))) if exposed.any() else None
        counts[phase]['fixed_point_actual_speed_RMS_m_s'] = float(np.sqrt(np.mean(np.sum(t['point_velocity_W'][exposed].astype(float)**2, -1)))) if exposed.any() else None
    material_error, normal_error = 0., 0.
    # Gate rows are non-reset control starts, hence correspond to an earlier actual physics endpoint.
    for row, env in zip(*np.nonzero(t['gate'])):
        previous = int(t['start_clock'][row, env])-1
        body = a['selected_distal_pose'][previous, env].astype(float)
        point = body[:3]+rotate(body[3:7], local[env])
        material_error = max(material_error, float(np.max(np.abs(point-t['fixed_point_W'][row, env]))))
        normal_error = max(normal_error, float(np.max(np.abs(press[previous, env]-t['normal_W'][row, env]))))
    assert material_error < 4e-6 and normal_error < 4e-6  # float32 pose arithmetic, not physical thresholds
    env_rows = []
    for i, ep in enumerate(episodes):
        row = dict(condition=name, env_id=i, achieved=ep['achieved'], physical_failure=ep['termination']['physical_failure'], wrist_failure=ep['termination']['wrist_failure'])
        for phase in ('audible', 'after'):
            for metric in ('selected_resultant_N', 'thumb_resultant_N'):
                values = scalar[metric][:, i][live[:, i] & windows[phase][:, i]]
                row[phase+'_'+metric+'_max'] = float(values.max()) if values.size else None
        env_rows.append(row)
    terms, note_order = load['protocol']['reward_order'], load['protocol']['note_order']
    paid = np.array([[r['reward_components'][k] for k in terms] for r in episodes])
    np.testing.assert_array_equal(paid, [[r['reward_components'][k] for k in terms] for r in notes])
    np.testing.assert_allclose(np.sum(c['reward_increment']*mask[..., None], axis=0), paid, atol=2e-6, rtol=0)
    for i in range(128):
        last = np.flatnonzero(mask[:, i])[-1]
        np.testing.assert_allclose(c['reward_cumulative'][last, i], paid[i], atol=1e-9, rtol=0)
        np.testing.assert_allclose(c['note_ledger'][last, i], [notes[i]['selected_note'][k] for k in note_order], atol=1e-9, rtol=0)
    reward_rows = [dict(condition=name, term=k, environments=128, mean=float(paid[:, j].mean()), **stats(paid[:, j])) for j,k in enumerate(terms)]
    calculated = dict(episodes=128, achieved_fraction=sum(r['achieved'] for r in episodes)/128,
        mean_clean_fraction=sum(r['clean_fraction'] for r in episodes)/128, mean_audible_wrong_fraction=sum(r['audible_wrong_fraction'] for r in episodes)/128,
        physical_failure_fraction=sum(r['termination']['physical_failure'] for r in episodes)/128, wrist_failure_fraction=sum(r['termination']['wrist_failure'] for r in episodes)/128,
        any_failure_fraction=sum(r['reason']=='terminal_failure' for r in episodes)/128)
    assert all(np.isclose(evaluation['summary'][k],v,atol=1e-12,rtol=0) for k,v in calculated.items())
    prefix = exact(source_a, a, 480)
    original_checks = dict(physics=all(exact(source_a,a).values()), control=all(exact(source_c,c).values()),
        evaluation=evaluation==source_eval, notes=notes==source_notes) if name == 'original' else None
    return dict(condition=name, evaluation=calculated, denominator=128, force_valid_endpoints=int(live.sum()),
        failure_censored_endpoints=int((first & failed).sum()), prefix_exact=prefix, original_source_exact=original_checks,
        native_reports_pass=base['completed'] and load['completed'] and target['completed'] and all(load['checks'].values()) and all(target['checks'].values()),
        fixed_point_reconstruction_max_error_m=material_error, normal_reconstruction_max_error=normal_error,
        controls=counts, checks=dict(launcher0=True,scene_closed=True,input_audit=True,first_clock_failure_censor=True,tape=True,
            gate_J_dot_box_rate=True,fixed_material_pose=True,reward9_ledger=True,summary_recomputed=True)), force_rows, control_rows, env_rows, reward_rows, inputs


def plot(path, forces, controls):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for i,name in enumerate(CASES):
        for j,phase in enumerate(('audible','after')):
            row = next(r for r in forces if r['condition']==name and r['phase']==phase and r['metric']=='selected_resultant_N')
            if row['samples']: axes[0].plot([i+(j-.5)*.2]*2,[row['p50'],row['p95']], lw=3,color=('tab:blue','tab:orange')[j],label=phase if i==0 else None)
        row = next(r for r in controls if r['condition']==name and r['phase']=='audible' and r['metric']=='final_normal_error_m')
        if row['samples']: axes[1].scatter(i,row['p50']*1000)
    axes[0].set_title('Middle3 body resultant p50--p95'); axes[0].set_ylabel('N; not pair pressure'); axes[0].legend()
    axes[1].set_title('Fixed-point Jn(target-q), gated controls'); axes[1].set_ylabel('mm; local proxy, not penetration'); axes[1].axhline(0,color='gray',lw=.5)
    for ax in axes: ax.set_xticks(range(3)); ax.set_xticklabels(CASES,fontsize=8,rotation=12); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(path,dpi=140); plt.close(fig)


def results(summaries, forces, controls, rewards, matched):
    lines=['# 고정 중지4 tape target 누적 진단', '', 'matched 비교 전제: **%s**. 원본 전체 재현과 세 조건 첫480 물리 상태/관찰 필드 exact가 필요하다. 미충족 시 수치는 기술 통계로만 읽고 개입 효과 해석을 보류한다.'%('충족' if matched else '미충족'), '',
        '| 조건 | 달성/128 | clean/wrong 평균 | 물리/손목 실패 | 실패 제외 endpoint |', '|---|---:|---:|---:|---:|']
    for s in summaries:
        e=s['evaluation']; lines.append('|%s|%d|%.6f / %.6f|%d / %d|%d|'%(s['condition'],round(e['achieved_fraction']*128),e['mean_clean_fraction'],e['mean_audible_wrong_fraction'],round(e['physical_failure_fraction']*128),round(e['wrist_failure_fraction']*128),s['failure_censored_endpoints']))
    lines += ['', '| 조건/구간 | 중지 resultant p50/p95/max N | 엄지 resultant p50/p95/max N |', '|---|---:|---:|']
    for name in CASES:
        for phase in ('audible','after'):
            cells=[]
            for body in ('selected','thumb'):
                r=next(r for r in forces if r['condition']==name and r['phase']==phase and r['metric']==body+'_resultant_N')
                cells.append(' / '.join('미확보' if r[k] is None else '%.4f'%r[k] for k in ('p50','p95','max')))
            lines.append('|%s/%s|%s|%s|'%(name,phase,*cells))
    def metric(rows,name,phase,key):
        return next(r for r in rows if r['condition']==name and r['phase']==phase and r['metric']==key)
    def formatted(row, keys=('p50','p95','max'), scale=1.):
        return ' / '.join('미확보' if row[k] is None else '%.5g'%(row[k]*scale) for k in keys)
    lines += ['', '각 조건은 첫128시도·111,616개 물리 endpoint·27,904개 control 관찰이다. 모든 런의 launcher exit0, scene closed, source/model/RNG/업데이트 불변 감사와 rate/box/halfspace 검사를 확인했다. 원본의 전체 배열·원장·평가값 재현과 세 조건 첫480 endpoint는 실제 exact 비교 결과이며 일반적 결정론 보장은 아니다.', '',
        '| 조건 | audible 중지 press-normal p50/p95 N | 엄지 press-normal p50/p95 N | 엄지 rear-normal p50/p95 N |', '|---|---:|---:|---:|']
    for name in CASES:
        lines.append('|%s|%s|%s|%s|'%(name,*[formatted(metric(forces,name,'audible',key),('p50','p95')) for key in ('selected_signed_press_N','thumb_signed_press_N','thumb_signed_rear_N')]))
    lines += ['', '중지와 엄지 press-normal은 같은 실제 press-plane 바깥법선을 기준으로 한다. 엄지 rear-normal은 반대 후면 바깥법선 기준이며 두 부호를 합쳐 쓰지 않는다. 힘 표는 물리 endpoint 가중이며 환경별 peak 평균이 아니다.', '',
        '| 조건 | 2초 후 gate/전체control | 실제 target 변경/gate | audible gate/1024 | audible box/rate 경계 좌표 |', '|---|---:|---:|---:|---:|']
    for item in summaries:
        name=item['condition']; c=item['controls']; gates=sum(v['eligible_controls'] for v in c.values()); changed=sum(v['changed_eligible_controls'] for v in c.values()); a=c['audible']
        lines.append('|%s|%d/12544|%d/%d|%d/1024|%d / %d|'%(name,gates,changed,gates,a['eligible_controls'],a['box_boundary_coordinates'],a['rate_boundary_coordinates']))
    lines += ['', 'gate는 첫120 control 뒤 signed press-normal resultant>0.01N인 유효 행이다. 세 조건 모두 stale reset128행 외 prior failure/invalid state/J=0행이며, 유효 gate의 zero J도0이다. 경계 수는4축 좌표 기준(음 구간4096좌표)이고 native/action/rate 교집합 box다. native 단독 한계 체류와 같다고 주장하지 않는다.', '',
        '| 조건 | audible 고정Jn·기존 target−q p50 mm | 최종 target−q p50 mm | raw/filtered 증분 p50 mm/control | 접선 변경 p50/p95/max mm/control |', '|---|---:|---:|---:|---:|']
    for name in CASES:
        old=metric(controls,name,'audible','old_normal_error_m'); final=metric(controls,name,'audible','final_normal_error_m')
        raw=metric(controls,name,'audible','raw_normal_increment_m'); filtered=metric(controls,name,'audible','filtered_normal_increment_m')
        tangent=metric(controls,name,'audible','tangent_change_norm_m')
        lines.append('|%s|%s|%s|%s / %s|%s|'%(name,formatted(old,('p50',),1000),formatted(final,('p50',),1000),formatted(raw,('p50',),1000),formatted(filtered,('p50',),1000),formatted(tangent,scale=1000)))
    lines += ['', '위 표는 gate true인 control만 비교한다(original/A1024, relax408). 고정점의 순간 J를 큰 관절오차에 곱한 선형 외삽이며 실제 침투 mm가 아니다. A는 새 법선 증분을 numerical tolerance 안에서0으로 바꾸지만 기존 target−q 법선오차는 남는다. relax의 gate 없는616 control에 저장된0을 오차0으로 포함하지 않았다. 접선 변경도 분명히 존재한다.', '',
        '| 조건 | audible 실제/예측 속도 잔차 RMS m/s | 실제 속도 RMS m/s | 잔차/실제 RMS % | original 대비 팔12 요청차 norm p50 rad | 손목 위치/회전오차 p50 m/rad |', '|---|---:|---:|---:|---:|---:|']
    for item in summaries:
        name=item['condition']; c=item['controls']['audible']; residual=c['fixed_point_velocity_residual_RMS_m_s']; speed=c['fixed_point_actual_speed_RMS_m_s']
        arm=metric(controls,name,'audible','arm_request_difference_vs_original_rad')['p50']; pos=metric(controls,name,'audible','wrist_position_error_m')['p50']; angle=metric(controls,name,'audible','wrist_orientation_error_rad')['p50']
        lines.append('|%s|%.7g|%.7g|%.4f|%.5g|%.5g / %.5g|'%(name,residual,speed,residual/speed*100,arm,pos,angle))
    lines += ['', '속도 잔차는 유효 고정점에서 확인했으며 큰 target−q의 선형 외삽 정확도를 보장하지 않는다. 팔12 요청차는 같은 env/clock의 original과 비교한 유클리드 norm이고 실제 팔 관절각 차이가 아니다. 첫2초 이후 wrist feedback 혼입이 있으므로 중지 target override만의 고립된 효과로 확대할 수 없다.', '',
        '| 조건 | 전체128 평균 최초 접촉 / 유지 / 달성 지급 |', '|---|---:|']
    for name in CASES:
        lines.append('|%s|%s|'%(name,' / '.join('%.6f'%next(r['mean'] for r in rewards if r['condition']==name and r['term']==term) for term in ('song_left_contact','song_clean_hold','song_left_success'))))
    lines += ['', '추가 안쪽 증분 억제는 이번 finite tape에서 원래 성공을 유지하며 관측 하중을 낮췄다. 음 종료 뒤에도 중지 합력 중앙값35.88N이 남으므로 저부하 제어 해결로 선언하지 않는다. 유한 누적오차 완화 조건은 하중은 더 낮지만 달성0/128이므로 같은 방식의 성공 해법 근거가 아니다. 성공한 A의 한 번 실험을 정책학습 성과나 일반 controller 채택으로 확대하지 않는다.']
    lines += ['', 'force_by_phase.csv는 실제 guitar pose에서 재계산한 press/rear signed normal을 포함한다. pooled240Hz 하중은 실패 endpoint부터 제외하며 모든128 성공·실패 분모는 유지했다. environment_peaks.csv는 노출 없는 환경도 null로 보존한다.', '',
        'control_by_phase.csv/summary.json은 시작 clock 기준60Hz의 gate/skip/개입 수, box·rate 경계, 고정Jn 오차·증분·접선 변경·속도잔차, original 대비 팔 teacher 요청과 손목오차다. 실패로 끝난 control은 전체를 보수적으로 제외했다. gate 꺼짐의 저장0을 실제0오차로 평균하지 않는다. 구간별 gate 노출이 서로 달라 조건부 통계의 분모도 다르다.', '',
        'reward_payments.csv는 원래9보상 실제 지급이다. increment 합·최종 cumulative·episode·음 원장과 대조했다. 원래 성공/보상은 새 하중 목표나 힘 상한 판정으로 재정의하지 않았다.', '',
        'body resultant는 접촉쌍 압력이 아니다. 고정 material point는 any-candidate witness와 다를 수 있다. Jn·큰 target−q는 국소 선형 외삽이며 침투깊이가 아니다. 실제/예측 점속도 잔차와 실제 속도를 함께 검토해야 하며 큰 잔차 구간의 방향 해석은 보류한다. 접선 보존을 보장하지 않고 이후 팔 teacher feedback도 달라진다. 이는 finite tape 진단이며 새 정책 성과·정책 단독 인과·저부하 제어 해결·일반 controller 채택을 증명하지 않는다.', '',
        'summary.png는 작은 개요이며 원본 재현/prefix/실패·gate 분모와 원래 지급 근거는 summary.json 및 verification.json을 함께 확인한다.']
    return '\n'.join(lines)+'\n'


def self_test():
    assert stats([])['p95'] is None
    v=dict(local_onset_s=3.,local_end_s=3.12)
    p=phases(np.array([2.9,3.,3.12,3.13]),v)
    np.testing.assert_array_equal(p['audible'],[False,True,True,False])
    assert all(exact({'q':np.arange(4)}, {'q':np.arange(4)}, 2).values())
    assert not all(exact({'q':np.arange(4)}, {'q':np.array([0,9,2,3])}, 2).values())
    first=np.array([[True],[True],[True],[False]]); failure=np.array([[False],[True],[False],[False]])
    latched=first & np.maximum.accumulate(failure,axis=0)
    np.testing.assert_array_equal(first & ~latched,[[True],[False],[False],[False]])
    # Reuse the sealed CPU fake scene and actual nested hook; no native module/rollout.
    sys.path.insert(0,str(BASE)); sys.path.insert(0,str(HERE.parents[5]))
    try:
        spec=importlib.util.spec_from_file_location('sealed_windup_cpu_fixture',BASE/'self_test.py')
        fixture=importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
        import torch
        for i,name in enumerate(CASES):
            pool,trace=fixture.hook(fixture.driver.MODES[i])
            for _ in range(121): pool.step(torch.full((128,39),.9))
            target_checks(trace.values(),.01,name)
            bad={k:v.copy() for k,v in trace.values().items()}; bad['gate'][120,0]=False
            try: target_checks(bad,.01,name)
            except AssertionError: pass
            else: raise AssertionError('Tampered gate was accepted')
        assert not torch.cuda.is_initialized()
    finally: sys.path.remove(str(BASE)); sys.path.remove(str(HERE.parents[5]))
    print(json.dumps(dict(completed=True,CPU_only=True,synthetic_only=True,checks=['empty exposure','audible boundaries','exact prefix mismatch','same-failure-endpoint censor','three actual nested CPU target-hook traces independently recalculated','tampered gate rejected'])))


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--self-test',action='store_true'); parser.add_argument('--status',action='store_true')
    args=parser.parse_args()
    if args.self_test: self_test(); return
    status=ready()
    if args.status or not all(r['ready'] for r in status): print(json.dumps(dict(ready=all(r['ready'] for r in status),conditions=status),indent=2)); return
    out=HERE/'results_v1'
    if out.exists(): raise FileExistsError(str(out))
    out.mkdir()
    try:
        source_a,source_c=arrays(SOURCE/'physics240.npz'),arrays(SOURCE/'control60.npz')
        source_eval=read(SOURCE/'evaluation.json'); source_notes=sorted(read(SOURCE/'first_attempt_notes.json'),key=lambda r:r['env_id'])
        original_t=arrays(BASE/'run_original/target_control60.npz')
        summaries,forces,controls,environments,rewards,inputs=[],[],[],[],[],{}
        for name in CASES:
            s,f,c,e,r,p=analyze(name,source_a,source_c,source_eval,source_notes,original_t)
            summaries.append(s);forces+=f;controls+=c;environments+=e;rewards+=r;inputs.update(p)
        for p in [HERE/'analyze.py',HERE/'README.md',HELPER,BASE/'precommit.json',BASE/'fixed_inputs.npz',*[SOURCE/f for f in ('physics240.npz','control60.npz','evaluation.json','first_attempt_notes.json')]]: inputs[str(p)]=sha(p)
        matched=all(s['native_reports_pass'] and all(s['prefix_exact'].values()) for s in summaries) and all(summaries[0]['original_source_exact'].values())
        write(out/'summary.json',dict(matched_interpretation_prerequisites=matched,conditions=summaries))
        for filename,rows in (('force_by_phase.csv',forces),('control_by_phase.csv',controls),('environment_peaks.csv',environments),('reward_payments.csv',rewards)): output_csv(out/filename,rows)
        plot(out/'summary.png',forces,controls)
        with (out/'RESULTS.md').open('x') as stream: stream.write(results(summaries,forces,controls,rewards,matched))
        assert all(sha(p)==h for p,h in inputs.items())
        write(out/'verification.json',dict(completed=True,CPU_only=True,matched_interpretation_prerequisites=matched,input_files_unchanged=True,input_sha256=inputs,checks={s['condition']:s['checks'] for s in summaries}))
        print(json.dumps(dict(completed=True,matched_interpretation_prerequisites=matched,output=str(out))))
    except BaseException as error:
        if not (out/'verification.json').exists(): write(out/'verification.json',dict(completed=False,CPU_only=True,failure=dict(type=type(error).__name__,message=str(error))))
        raise


if __name__=='__main__': main()
