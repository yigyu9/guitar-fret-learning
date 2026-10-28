"""CPU-only index reference tracking and source full-posture comparison."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
DIAG = BASE.parents[1]
ROOT = DIAG.parents[2]


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    import numpy as np
    from scipy.spatial.transform import Rotation
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk

    assert not any((HERE/n).exists() for n in ('observations.json', 'TRACKING.md', 'tracking.png'))
    run = BASE/'runs/index_reference'
    t = np.load(run/'trace_env0_episode0.npz')
    meta, settings = read(run/'trace_metadata.json'), read(run/'settings.json')
    teacher = read(BASE/'teacher_index_row1.json')
    source = DIAG/'02_contact_reward/teacher_fixed_B_export'
    old = np.load(source/'teacher_trace60.npz')
    source_meta = read(source/'metadata.json')
    source_i = int(np.flatnonzero(old['observed_time_s'] == teacher['source_time_s'])[0])
    source_q = old['actual_q105_rad'][source_i, teacher['source_row']]
    assert source_meta['joint_names'] == meta['joint_names']
    c = read(run/'training_contract.json')['action']['target_contract']
    arm_names = c['action_order'][:12]
    arm = [meta['joint_names'].index(n) for n in arm_names]
    use = (t['time_s'] >= 2-1e-9) & (t['time_s'] <= 3.67)
    ids = np.flatnonzero(use)
    time = t['time_s'][use]
    q, target, request = t['q'][:, arm], t['target'][:, arm], t['wrist_requested_arm_rad']
    base = np.array([teacher['arm_targets_rad'][n] for n in arm_names])
    correction = request-base
    lo, hi = np.array(c['action_lower_rad'][:12]), np.array(c['action_upper_rad'][:12])
    assert t['wrist_feedback_active'][use].all()
    assert np.max(abs(t['wrist_goal_G_m'][use]-teacher['wrist_position_G_m'])) < 1e-7
    g, w = [meta['body_names'].index(n) for n in ('guitar/guitar', 'human/L_Wrist')]
    gr = Rotation.from_quat(t['body_state'][:, g, 3:7])
    pG = gr.inv().apply(t['body_state'][:, w, :3]-t['body_state'][:, g, :3])
    rG = gr.inv()*Rotation.from_quat(t['body_state'][:, w, 3:7])
    pe = np.linalg.norm(pG-teacher['wrist_position_G_m'], axis=1)*1000
    re = np.rad2deg((Rotation.from_quat(teacher['wrist_quaternion_G_xyzw']).inv()*rG).magnitude())
    assert np.max((Rotation.from_quat(t['wrist_goal_G_xyzw'][use]).inv()*Rotation.from_quat(teacher['wrist_quaternion_G_xyzw'])).magnitude()) < 1e-6
    alpha = np.array(c['smoothing_alpha'][:12])
    smooth_residual = np.max(abs(target[1:]-(target[:-1]+alpha*(request[1:]-target[:-1]))))
    bounded_residual = np.max(abs(request[ids[1:]]-np.clip(request[ids[1:]-1]+t['wrist_requested_delta_rad'][ids[1:]], lo, hi)))
    assert smooth_residual < 1e-6 and bounded_residual < 1e-6
    prepared = load_prepared_reset_contract()
    initial, state = prepared['initial'], prepared['state']
    native_lo = np.array(initial['native_PD_properties']['lower'])[arm]
    native_hi = np.array(initial['native_PD_properties']['upper'])[arm]
    axes = []
    for a, name in enumerate(arm_names):
        axes.append(dict(name=name, action_bounds_deg=np.rad2deg([lo[a], hi[a]]).tolist(),
            native_bounds_deg=np.rad2deg([native_lo[a], native_hi[a]]).tolist(),
            request_bound_counts=dict(lower=int((abs(request[use, a]-lo[a]) <= 1e-6).sum()), upper=int((abs(request[use, a]-hi[a]) <= 1e-6).sum())),
            submitted_target_bound_counts=dict(lower=int((abs(target[use, a]-lo[a]) <= 1e-6).sum()), upper=int((abs(target[use, a]-hi[a]) <= 1e-6).sum())),
            actual_at_or_beyond_native_bounds=dict(lower=int((q[use, a] <= native_lo[a]+1e-6).sum()), upper=int((q[use, a] >= native_hi[a]-1e-6).sum())),
            request_actual_max_gap_deg=float(np.rad2deg(abs(request[use, a]-q[use, a])).max()),
            target_actual_max_gap_deg=float(np.rad2deg(abs(target[use, a]-q[use, a])).max()),
            correction_start_end_deg=np.rad2deg(correction[use, a][[0, -1]]).tolist(),
            raw_requested_delta_sum_deg=float(np.rad2deg(t['wrist_requested_delta_rad'][ids[1:], a]).sum()),
            raw_delta_positive_count=int((t['wrist_requested_delta_rad'][use, a] > 0).sum()),
            raw_delta_negative_count=int((t['wrist_requested_delta_rad'][use, a] < 0).sum()),
            raw_delta_at_half_degree_cap_count=int((abs(abs(t['wrist_requested_delta_rad'][use, a])-.5*np.pi/180) < 1e-7).sum())))
    samples = []
    for now in (2., 2.25, 2.5, 2.75, 3., 3.1666666667, 3.25, 3.5, time[-1]):
        i = int(np.argmin(abs(t['time_s']-now)))
        samples.append(dict(time_s=float(t['time_s'][i]), position_error_mm=float(pe[i]), rotation_error_deg=float(re[i]),
            request_actual_max_gap_deg=float(np.rad2deg(abs(request[i]-q[i])).max()),
            target_actual_max_gap_deg=float(np.rad2deg(abs(target[i]-q[i])).max()),
            maximum_absolute_correction_deg=float(np.rad2deg(abs(correction[i])).max())))
    torso_names = [n for n in meta['joint_names'] if n.startswith(('Torso_', 'Spine_', 'Chest_'))]
    torso = [meta['joint_names'].index(n) for n in torso_names]
    posture = []
    for n, j in zip(torso_names, torso):
        values = np.rad2deg(t['q'][use, j])
        posture.append(dict(name=n, source_actual_deg=float(np.rad2deg(source_q[j])),
            current_actual_min_median_max_deg=[float(values.min()), float(np.median(values)), float(values.max())],
            current_minus_source_min_median_max_deg=[float(v) for v in np.rad2deg(t['q'][use, j]-source_q[j])[[int(np.argmin(values)), int(np.argsort(values)[len(values)//2]), int(np.argmax(values))]]]))
    nonarm = [i for i in range(105) if i not in arm]
    delta = np.rad2deg(t['q'][use][:, nonarm]-source_q[nonarm])
    nonarm_order = np.argsort(abs(delta).max(0))[::-1]
    top_nonarm = [dict(name=meta['joint_names'][nonarm[j]], max_absolute_delta_deg=float(abs(delta[:, j]).max())) for j in nonarm_order[:12]]
    q0 = np.array([row['pos'] for row in state['human_dof_states']])
    fk = full_fk(SimpleNamespace(names=meta['joint_names'], human_bodies=source_meta['human_bodies'], q_ref=q0), state)
    fk_checks = []
    for now in (2., 3.):
        i = int(np.argmin(abs(t['time_s']-now)))
        p, r = fk(t['q'][i])['L_Wrist']
        body = t['body_state'][i, w]
        fk_checks.append(dict(time_s=float(t['time_s'][i]), position_error_m=float(np.linalg.norm(p-body[:3])),
            rotation_error_rad=float((r.inv()*Rotation.from_quat(body[3:7])).magnitude())))
    assert all(x['position_error_m'] < 1e-5 and x['rotation_error_rad'] < 1e-5 for x in fk_checks)
    pins = read(run/'inputs_before.json')
    inputs = [run/n for n in ('trace_env0_episode0.npz', 'trace_metadata.json', 'settings.json', 'training_contract.json', 'inputs_before.json')]
    inputs += [BASE/'teacher_index_row1.json', source/'teacher_trace60.npz', source/'metadata.json', Path(__file__).resolve(),
        ROOT/'guitar_learning/tool/experiments/short_finger_learning/runtime.py', ROOT/'guitar_learning/tool/experiments/short_finger_learning/wrist.py',
        ROOT/'guitar_learning/gpu/control.py', ROOT/'guitar_learning/native/lower_body_release_v1/controller_horizontal_v4.py']
    hashes = {str(p):sha(p) for p in inputs}
    assert all(value == pins[path] for path, value in hashes.items() if path in pins)
    result = dict(scope='index reference env0 only; native60Hz samples2.0..3.6667s; no new physics, source/teacher edits or IK solve',
        endpoint_count=int(use.sum()), time_range_s=[float(time[0]), float(time[-1])], samples=samples, axes=axes,
        position_error_range_mm=[float(pe[use].min()), float(pe[use].max())], rotation_error_range_deg=[float(re[use].min()), float(re[use].max())],
        position_difference_counts=dict(increase=int((np.diff(pe[use]) > 0).sum()), decrease=int((np.diff(pe[use]) < 0).sum())),
        request_correction_scope='Bounded correction memory is reconstructed from saved request minus fixed arm feedforward after2s using runtime desired-base; memory was not independently stored. Logged delta is after the DLS step and +/-0.5deg per-tick clamp, before request rate/action-bound clipping.',
        submitted_target_alpha_reconstruction_max_residual_rad=float(smooth_residual),
        bounded_correction_reconstruction_max_residual_rad=float(bounded_residual),
        torso_posture=posture, largest_nonarm_differences=top_nonarm, current_full_q_FK_native_checks=fk_checks,
        source_full_q_source=dict(row=teacher['source_row'], observed_time_s=teacher['source_time_s'], source_index=source_i),
        input_sha256=hashes, GPU_executed=False,
        limitation='Non-monotonic tracking, finite correction/bounds and posture differences are observations; not proof of instability, reachable/unreachable pose, causal body/contact contribution or benefit of a longer preparation.')
    with (HERE/'observations.json').open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    plt.rcParams['font.family'] = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, ax = plt.subplots(2, 2, figsize=(10, 6), sharex=True)
    ax[0, 0].plot(time, pe[use]); ax[0, 0].set_ylabel('위치 오차 (mm)')
    ax[0, 1].plot(time, re[use]); ax[0, 1].set_ylabel('회전 오차 (도)')
    ax[1, 0].plot(time, np.rad2deg(abs(request[use]-q[use])).max(1), label='request−actual 최대')
    ax[1, 0].plot(time, np.rad2deg(abs(target[use]-q[use])).max(1), label='scene target−actual 최대')
    ax[1, 0].set_ylabel('팔12 최대 절대각 차 (도)'); ax[1, 0].legend(fontsize=8)
    for a in (0, 2, 6, 7, 8, 11):
        ax[1, 1].plot(time, np.rad2deg(correction[use, a]), label=arm_names[a].replace('L_', ''))
    ax[1, 1].set_ylabel('bounded correction (도)'); ax[1, 1].legend(fontsize=7, ncol=2)
    for panel in ax.flat:
        panel.axvline(3, color='gray', ls='--', lw=.8); panel.grid(alpha=.2)
    for panel in ax[1]: panel.set_xlabel('로컬 시간 (초)')
    fig.suptitle('검지 reference · env0 · 고정 goal 이후2~3.67초의60Hz 표본')
    fig.tight_layout(); fig.savefig(HERE/'tracking.png', dpi=140); plt.close(fig)
    print(json.dumps(result, ensure_ascii=False)[:1200])


if __name__ == '__main__':
    main()
