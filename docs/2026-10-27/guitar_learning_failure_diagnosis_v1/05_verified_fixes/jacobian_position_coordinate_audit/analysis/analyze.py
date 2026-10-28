"""Read only the completed four-frame capture; all new output stays in analysis/."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
DIAG = BASE.parents[1]
ROOT = DIAG.parents[2]
OLD = DIAG/'03_short_learning/other_finger_precheck_v3'
sys.path.insert(0, str(ROOT))
CLOCKS = (476, 596, 716, 776)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'results_v2')
    args = parser.parse_args()
    out = args.out.absolute()
    if out.parent != HERE or out.exists() or out.is_symlink():
        raise ValueError('A new direct analysis/ child required')
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation as R
    from guitar_learning.runtime import prepared_reset_v1 as prepared
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.core.control import LEFT_ARM_NAMES
    from guitar_learning.tool.experiments.short_finger_learning.wrist import wrist_error_and_jacobian, WRIST_CONTROL
    assert not torch.cuda.is_available()
    torch.set_num_threads(1)
    run = BASE/'runs/index_reference'
    seal = json.loads((BASE/'preparation_seal.json').read_text())
    assert len(seal['input_pins']) == 690
    assert all(Path(p).is_file() and sha(p) == h for p, h in seal['input_pins'].items())
    launcher = json.loads((BASE/'01_launcher.json').read_text())
    capture = json.loads((run/'coordinate_audit_report.json').read_text())
    assert launcher['returncode'] == 0 and capture['completed'] and all(capture['checks'].values())
    assert capture['scene']['closed']
    a = np.load(run/'precontrol_native.npz')
    assert a['jacobian'].shape == (4, 4, 65, 6, 105)
    assert np.array_equal(a['clock'], np.array(CLOCKS)[:, None]*np.ones((4, 4)))
    assert np.array_equal(a['clock'], a['physics_step'])
    assert a['first_attempt'].all() and not a['reset_body_snapshot'].any()
    assert not a['physical_failure'].any() and not a['wrist_failure'].any()
    assert all(np.isfinite(a[key]).all() for key in a.files)
    trace = np.load(run/'trace_env0_episode0.npz')
    source = np.load(OLD/'runs/index_reference/trace_env0_episode0.npz')
    video = np.load(OLD/'native_video_index_reference/poses_env0000.npz')
    evaluated = json.loads((run/'evaluation.json').read_text())
    source_eval = json.loads((OLD/'runs/index_reference/evaluation.json').read_text())
    same_trace = {k: bool(k in trace.files and trace[k].shape == source[k].shape and np.array_equal(trace[k], source[k])) for k in source.files}
    trace_difference = {k: float(abs(trace[k].astype(float)-source[k].astype(float)).max())
        if k in trace.files and trace[k].shape == source[k].shape else None for k in source.files}
    assert evaluated['assigned_quotas'] == [1]*4 and len(evaluated['episodes']) == 4
    assert sorted(e['env_id'] for e in evaluated['episodes']) == list(range(4))
    names, bodies = capture['joint_names'], capture['body_names']
    arm = np.array([names.index(n) for n in LEFT_ARM_NAMES])
    assert len(arm) == 12 and all(names[arm[i]].startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist')[i//3]) for i in range(12))
    wrist, guitar = (bodies.index(n) for n in ('human/L_Wrist', 'guitar/guitar'))
    assert wrist == 17 and bodies[wrist] == 'human/'+capture['human_bodies'][wrist]
    state = prepared.load_prepared_reset_contract()['state']
    qref = np.array([r['pos'] for r in state['human_dof_states']])
    fk = full_fk(SimpleNamespace(names=names, human_bodies=capture['human_bodies'], q_ref=qref), state)

    def jac(q, body, columns, eps):
        value = np.empty((6, len(columns)))
        for k, col in enumerate(columns):
            qp, qm = q.copy(), q.copy(); qp[col] += eps; qm[col] -= eps
            pp, rp = fk(qp)[body]; pm, rm = fk(qm)[body]
            value[:, k] = np.r_[(pp-pm)/(2*eps), (rp*rm.inv()).as_rotvec()/(2*eps)]
        return value

    def dls(j, error):
        return np.clip(j.T@np.linalg.solve(j@j.T+WRIST_CONTROL['damping']*np.eye(6), error),
            -WRIST_CONTROL['correction_step_rad'], WRIST_CONTROL['correction_step_rad'])

    rows, blocks, saved_arrays = [], [], []
    for frame, clock in enumerate(CLOCKS):
        endpoint = int(np.argmin(abs(trace['time_s']-(clock+4)/240)))
        assert abs(trace['time_s'][endpoint]-(clock+4)/240) < 1e-6
        vrow = int(np.flatnonzero(video['physics_step'] == clock)[0])
        pre_match = {key: bool(np.array_equal(a[key][frame, 0], video[key][vrow])) for key in ('q', 'qd', 'target', 'body_state')}
        snapshot = {key: torch.from_numpy(a[key][frame].copy()) for key in ('q','qd','body_state','jacobian','reset_body_snapshot')}
        goalp = torch.tensor(trace['wrist_goal_G_m'][endpoint]).expand(4, -1)
        goalq = torch.tensor(trace['wrist_goal_G_xyzw'][endpoint]).expand(4, -1)
        error_torch, jproduction = wrist_error_and_jacobian(snapshot, wrist, guitar,
            torch.from_numpy(a['body_COM_local_m'][wrist]), torch.tensor(arm), goalp, goalq)
        delta = (jproduction.transpose(-1,-2)@torch.linalg.solve(jproduction@jproduction.transpose(-1,-2)+
            WRIST_CONTROL['damping']*torch.eye(6), error_torch[..., None])).squeeze(-1).clamp(
                -WRIST_CONTROL['correction_step_rad'], WRIST_CONTROL['correction_step_rad']).numpy()
        for env in range(4):
            q = a['q'][frame, env].astype(float)
            qd = a['qd'][frame, env].astype(float)
            body = a['body_state'][frame, env, wrist].astype(float)
            rw = R.from_quat(body[3:7]); offset = rw.apply(-a['body_COM_local_m'][wrist].astype(float))
            native = a['jacobian'][frame, env, wrist-1].astype(float)
            origin_j = native[:3]+np.cross(native[3:].T, offset).T
            jw = np.vstack((origin_j, native[3:]))
            actual = np.r_[body[7:10]+np.cross(body[10:13], offset), body[10:13]]
            closure = jw@qd-actual
            jqfull = jac(q, 'L_Wrist', range(105), 1e-5)
            jq = jqfull[:, arm]
            qpos_native_qd_error = jqfull@qd-actual
            jqhalf = jac(q, 'L_Wrist', arm, 5e-6)
            transform = np.zeros((12, 12)); half_transform = np.zeros_like(transform)
            posep, poser = fk(q)['L_Wrist']
            for joint, bodyname in enumerate(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist')):
                ids = arm[joint*3:joint*3+3]; bid = bodies.index('human/'+bodyname)
                s = a['jacobian'][frame, env, bid-1, 3:, :][:, ids].astype(float)
                m = jac(q, bodyname, ids, 1e-5)[3:]
                mh = jac(q, bodyname, ids, 5e-6)[3:]
                t = np.linalg.solve(s, m); th = np.linalg.solve(s, mh)
                transform[joint*3:joint*3+3, joint*3:joint*3+3] = t
                half_transform[joint*3:joint*3+3, joint*3:joint*3+3] = th
                p, r = fk(q)[bodyname]; actualbody = a['body_state'][frame, env, bid]
                blocks.append(dict(clock=clock, env=env, joint=bodyname, body_index=bid, native_row=bid-1,
                    native_columns=ids.tolist(), cond_S=float(np.linalg.cond(s)), cond_M=float(np.linalg.cond(m)),
                    det_S=float(np.linalg.det(s)), S_T_minus_M_max_abs=float(abs(s@t-m).max()),
                    T_minus_identity_Frobenius=float(np.linalg.norm(t-np.eye(3))),
                    half_epsilon_T_max_abs=float(abs(t-th).max()),
                    FK_position_error_m=float(np.linalg.norm(p-actualbody[:3])),
                    FK_rotation_error_rad=float((r*R.from_quat(actualbody[3:7]).inv()).magnitude())))
            converted = jw[:, arm]@transform
            mapped_difference = converted-jq
            unconverted_difference = jw[:, arm]-jq
            error = error_torch[env].numpy().astype(float)
            weighted_q = jq.copy(); weighted_q[3:] *= .1
            weighted_map = converted.copy(); weighted_map[3:] *= .1
            qdelta = dls(weighted_q, error); mapped_delta = dls(weighted_map, error)
            stored_delta = trace['wrist_requested_delta_rad'][endpoint] if env == 0 else None
            rows.append(dict(clock=clock, precontrol_time_s=clock/240, env=env, feedback_endpoint_time_s=(clock+4)/240,
                native_COM_linear_closure_m_s=float(np.linalg.norm(native[:3]@qd-body[7:10])),
                native_origin_linear_closure_m_s=float(np.linalg.norm(closure[:3])),
                native_angular_closure_rad_s=float(np.linalg.norm(closure[3:])),
                actual_origin_speed_m_s=float(np.linalg.norm(actual[:3])),
                actual_angular_speed_rad_s=float(np.linalg.norm(actual[3:])),
                native_origin_closure_relative=float(np.linalg.norm(closure[:3])/np.linalg.norm(actual[:3])),
                native_angular_closure_relative=float(np.linalg.norm(closure[3:])/np.linalg.norm(actual[3:])),
                qpos_full_J_times_native_qd_linear_error_m_s=float(np.linalg.norm(qpos_native_qd_error[:3])),
                qpos_full_J_times_native_qd_angular_error_rad_s=float(np.linalg.norm(qpos_native_qd_error[3:])),
                FK_wrist_position_error_m=float(np.linalg.norm(posep-body[:3])),
                FK_wrist_rotation_error_rad=float((poser*rw.inv()).magnitude()),
                qpos_J_half_epsilon_max_abs=float(abs(jq-jqhalf).max()),
                unconverted_linear_J_max_abs=float(abs(unconverted_difference[:3]).max()),
                unconverted_angular_J_max_abs=float(abs(unconverted_difference[3:]).max()),
                converted_linear_J_max_abs=float(abs(mapped_difference[:3]).max()),
                converted_angular_J_max_abs=float(abs(mapped_difference[3:]).max()),
                converted_J_half_epsilon_max_abs=float(abs(jw[:, arm]@half_transform-jqhalf).max()),
                qpos_DLS_vs_transformed_native_DLS_max_deg=float(np.rad2deg(abs(qdelta-mapped_delta)).max()),
                native_DLS_vs_qpos_DLS_max_deg=float(np.rad2deg(abs(delta[env]-qdelta)).max()),
                native_DLS_vs_stored_delta_max_rad=float(abs(delta[env]-stored_delta).max()) if env == 0 else None,
                native_error_vs_stored_max_abs=float(abs(error-trace['wrist_pose_error_world'][endpoint]).max()) if env == 0 else None,
                original_video_precontrol_exact=pre_match if env == 0 else None,
                qpos_DLS_delta_deg=np.rad2deg(qdelta).tolist(), native_DLS_delta_deg=np.rad2deg(delta[env]).tolist()))
            saved_arrays.append(dict(native_origin_arm_J=jw[:, arm], qpos_FD_arm_J=jq,
                qpos_to_native_velocity_T=transform, transformed_native_J=converted,
                actual_origin_twist=actual, native_predicted_origin_twist=jw@qd))
    summary = {key: max(row[key] for row in rows) for key in rows[0]
        if key.endswith(('_m_s','_rad_s','_max_abs','_max_deg','_max_rad')) and all(isinstance(row[key], (int,float)) for row in rows)}
    summary.update(ownbody_FK_max_position_m=max(r['FK_position_error_m'] for r in blocks),
        ownbody_FK_max_rotation_rad=max(r['FK_rotation_error_rad'] for r in blocks),
        cond_S_max=max(r['cond_S'] for r in blocks), cond_M_max=max(r['cond_M'] for r in blocks),
        S_T_minus_M_max_abs=max(r['S_T_minus_M_max_abs'] for r in blocks),
        native_DLS_vs_stored_delta_max_rad=max(r['native_DLS_vs_stored_delta_max_rad'] for r in rows if r['env']==0),
        native_error_vs_stored_max_abs=max(r['native_error_vs_stored_max_abs'] for r in rows if r['env']==0))
    pins = {str(p):sha(p) for p in [Path(__file__), HERE/'PLAN.md', BASE/'preparation_seal.json', BASE/'review.json',
        BASE/'01_launcher.json', BASE/'runs/report.json', run/'precontrol_native.npz', run/'coordinate_audit_report.json',
        run/'trace_env0_episode0.npz', run/'evaluation.json', OLD/'runs/index_reference/trace_env0_episode0.npz',
        OLD/'runs/index_reference/evaluation.json', OLD/'native_video_index_reference/poses_env0000.npz']}
    verification = dict(CPU_only=True, GPU_executed_by_analysis=False, raw_capture_frames=4, environments=4,
        frame_environment_samples=16, ownjoint_blocks=64, all_first_attempt=True, failed_capture_samples=0,
        saved_feedback_comparisons=4, feedback_comparison_scope='env0 only; other three environment feedback deltas were not saved',
        original_evaluation_exact=evaluated==source_eval, original_trace_exact=same_trace, original_trace_max_abs_difference=trace_difference,
        original_video_precontrol_exact=all(all(r['original_video_precontrol_exact'].values()) for r in rows if r['env']==0),
        source_seal_pins_verified=690, capture_uncompressed_bytes=sum(a[k].nbytes for k in a.files),
        launcher_returncode=launcher['returncode'], capture_checks=capture['checks'], evaluation_summary=evaluated['summary'],
        source_pins=pins, limitations=['four actual precontrol frames and four environments only',
            'T maps qpos differential to native velocity coordinates locally; no production correction implemented',
            'finger MCP two-axis qpos cannot inherit this result; actual relative orientation y requires separate validation',
            'native DLS finite qpos target addition can be diagnosed, but physical performance effect is not measured'])
    out.mkdir()
    write(out/'measurements.json', dict(summary=summary, rows=rows, ownjoint_blocks=blocks))
    write(out/'verification.json', verification)
    with (out/'matrices.npz').open('xb') as stream:
        np.savez_compressed(stream, **{k:np.stack([r[k] for r in saved_arrays]) for k in saved_arrays[0]})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1,2,figsize=(9,3.3),constrained_layout=True)
    x=np.array(CLOCKS)/240
    for key,label in [('native_origin_linear_closure_m_s','native J × native qd'),('qpos_full_J_times_native_qd_linear_error_m_s','qpos FD J × native qd')]:
        axes[0].semilogy(x,[max(r[key] for r in rows if r['clock']==c) for c in CLOCKS],'o-',label=label)
    axes[0].set(ylabel='max linear velocity error (m/s)',xlabel='precontrol time (s)',title='Velocity / basis closure');axes[0].legend(fontsize=8)
    axes[1].plot(x,[max(r['native_DLS_vs_qpos_DLS_max_deg'] for r in rows if r['clock']==c) for c in CLOCKS],'o-')
    axes[1].set(xlabel='precontrol time (s)',ylabel='max coordinate difference (deg)',title='Native-J DLS vs qpos-J DLS')
    fig.savefig(out/'coordinate_comparison.png',dpi=160);plt.close(fig)
    print(json.dumps(dict(summary=summary,verification={k:verification[k] for k in ('original_evaluation_exact','original_video_precontrol_exact','frame_environment_samples')}),indent=2))


if __name__ == '__main__':
    main()
