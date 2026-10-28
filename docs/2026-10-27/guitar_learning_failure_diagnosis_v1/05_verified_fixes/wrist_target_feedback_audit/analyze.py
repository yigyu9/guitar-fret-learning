"""Existing env0/60Hz reference evidence; virtual wrist FK, no native execution."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[1]
ROOT = DIAG.parents[2]
sys.path.insert(0, str(ROOT))
CASES = dict(original=DIAG/'03_short_learning/other_finger_precheck_v3',
    low_gain=DIAG/'05_verified_fixes/index_wrist_gain_probe',
    qpos_v2=DIAG/'05_verified_fixes/wrist_position_jacobian_v2/native_precheck')
PRIOR = DIAG/'05_verified_fixes/wrist_position_jacobian_v2/analysis/results_v1/verification.json'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    import numpy as np
    from scipy.spatial.transform import Rotation as R
    from guitar_learning.runtime import prepared_reset_v1 as prepared
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.native.lower_body_release_v1.common import HUMAN
    from guitar_learning.core.control import LEFT_ARM_NAMES
    out = HERE/'results_v1'
    if out.exists() or out.is_symlink():
        raise FileExistsError(str(out))
    prior = read(PRIOR)
    # Reuse prior archive/source verification; verify the actual FK/prepared inputs we use, not old entire active source.
    source_meta = DIAG/'02_contact_reward/teacher_fixed_B_export/metadata.json'
    metadata = read(source_meta)
    state = prepared.load_prepared_reset_contract()['state']
    qref = np.array([row['pos'] for row in state['human_dof_states']])
    fk = full_fk(SimpleNamespace(names=metadata['joint_names'], human_bodies=metadata['human_bodies'], q_ref=qref), state)
    pins = {str(p.resolve()):sha(p) for p in [Path(__file__), HERE/'PLAN.md', PRIOR, source_meta]}
    source_paths = [ROOT/'guitar_learning/native/lower_body_release_v1/controller_horizontal_v4.py',
        ROOT/'guitar_learning/runtime/prepared_reset_v1.py', Path(HUMAN), *map(Path, prepared.SOURCE_SHA256)]
    original_pins = read(CASES['original']/'runs/index_reference/inputs_before.json')
    source_verification = []
    for path in source_paths:
        path = path.resolve(); expected = original_pins[str(path)]
        assert sha(path) == expected, str(path)
        entries = [r for r in prior['source_verification'] if r['path'] == str(path) and r['sha256'] == expected]
        assert entries and any(sha(Path(r['verified_at'])) == expected for r in entries)
        source_verification.append(dict(path=str(path), sha256=expected, prior_verification=str(PRIOR)))
        pins[str(path)] = expected
    all_curves, report = {}, {}

    def stats(value):
        return dict(min=float(np.min(value)), median=float(np.median(value)), p95=float(np.quantile(value,.95)), max=float(np.max(value)))

    for label, base in CASES.items():
        folder = base/'runs/index_reference'
        for name in ('trace_env0_episode0.npz','trace_metadata.json','training_contract.json','settings.json','evaluation.json','inputs_before.json','inputs_after.json','report.json','gpu_scene_final.json'):
            path = folder/name; pins[str(path)] = sha(path)
            assert prior['input_sha256'][str(path)] == sha(path)
        evaluation, setting, meta, contract = [read(folder/name) for name in ('evaluation.json','settings.json','trace_metadata.json','training_contract.json')]
        assert evaluation['assigned_quotas'] == [1]*4 and len(evaluation['episodes']) == 4
        assert sorted(e['env_id'] for e in evaluation['episodes']) == list(range(4))
        assert read(folder/'report.json')['completed'] and read(folder/'gpu_scene_final.json')['closed']
        assert meta['joint_names'] == metadata['joint_names'] and meta['body_names'] == metadata['body_names']
        trace = np.load(folder/'trace_env0_episode0.npz')
        time = trace['time_s'].astype(float); ids = np.flatnonzero(time >= 2.)
        complete = time[ids-1] >= 2.
        assert len(time) == 221 and np.all(ids > 0) and len(ids) == 102 and complete.sum() == 101
        assert abs(time[0]-1/60) < 1e-6 and np.allclose(np.diff(time), 1/60, atol=4e-7)
        names, bodies = meta['joint_names'], meta['body_names']
        arm = np.array([names.index(name) for name in LEFT_ARM_NAMES])
        wrist, guitar = (bodies.index(name) for name in ('human/L_Wrist','guitar/guitar'))
        actual_fk = [fk(q.astype(float))['L_Wrist'] for q in trace['q']]
        pose_p = np.array([np.linalg.norm(p-b[:3]) for (p,r),b in zip(actual_fk,trace['body_state'][:,wrist])])
        pose_r = np.array([(r*R.from_quat(b[3:7]).inv()).magnitude() for (p,r),b in zip(actual_fk,trace['body_state'][:,wrist])])
        assert pose_p.max() < 1e-5 and pose_r.max() < 1e-5
        target_contract = contract['action']['target_contract']
        alpha = np.array(target_contract['smoothing_alpha'][:12])
        rate = np.array(target_contract['rate_rad_s'])[arm]
        low, high = (np.array(target_contract[k][:12]) for k in ('action_lower_rad','action_upper_rad'))
        req = trace['wrist_requested_arm_rad'].astype(float)
        target, actual = trace['target'][:, arm].astype(float), trace['q'][:, arm].astype(float)
        rows = {key:[] for key in ('time_s','actual_position_error_mm','request_virtual_position_error_mm',
            'target_virtual_position_error_mm','actual_rotation_error_deg','request_virtual_rotation_error_deg',
            'target_virtual_rotation_error_deg','request_actual_max_gap_deg','target_actual_max_gap_deg',
            'request_target_max_gap_deg','request_increment_max_deg','raw_delta_max_deg',
            'pre_actual_position_error_W_m','pre_old_request_position_error_W_m','pre_request_step_W_m',
            'pre_actual_rotation_error_W_rad','pre_old_request_rotation_error_W_rad','pre_request_step_rotation_W_rad',
            'position_actual_dot_old_request_m2','position_actual_dot_request_step_m2',
            'position_old_request_dot_step_m2','rotation_actual_dot_old_request_rad2',
            'rotation_actual_dot_request_step_rad2','position_virtual_distance_increased',
            'rotation_virtual_distance_increased','position_opposite_halfspace','rotation_opposite_log_direction',
            'position_continues_actual_direction','rotation_continues_actual_direction','position_accumulation_witness',
            'rotation_accumulation_witness','stored_pose_error_max_abs','request_recurrence_error_rad',
            'target_smoothing_error_rad','requested_rate_excess_rad','submitted_rate_excess_rad')}

        def virtual(q, angles):
            value = q.astype(float).copy(); value[arm] = angles
            return fk(value)['L_Wrist']

        for k in ids:
            q = trace['q'][k]; previous_q = trace['q'][k-1]
            gp = trace['body_state'][k,guitar].astype(float); gr = R.from_quat(gp[3:7])
            goal_p = gp[:3]+gr.apply(trace['wrist_goal_G_m'][k])
            goal_r = gr*R.from_quat(trace['wrist_goal_G_xyzw'][k])
            pa, ra = actual_fk[k]; pr, rr = virtual(q,req[k]); pt, rt = virtual(q,target[k])
            # Feedback[k] uses precontrol[k-1], while its goal is the next endpoint[k].
            pre_gp = trace['body_state'][k-1,guitar].astype(float); pre_gr = R.from_quat(pre_gp[3:7])
            pre_goal_p = pre_gp[:3]+pre_gr.apply(trace['wrist_goal_G_m'][k])
            pre_goal_r = pre_gr*R.from_quat(trace['wrist_goal_G_xyzw'][k])
            pre_pa, pre_ra = actual_fk[k-1]
            old_p, old_r = virtual(previous_q,req[k-1]); new_p, new_r = virtual(previous_q,req[k])
            ea, er, step = pre_goal_p-pre_pa, pre_goal_p-old_p, new_p-old_p
            ar = (pre_goal_r*pre_ra.inv()).as_rotvec(); er_rot = (pre_goal_r*old_r.inv()).as_rotvec()
            rotation_step = (new_r*old_r.inv()).as_rotvec()
            opposite = float(ea@er) < 0; along = float(ea@step) > 0
            away = np.linalg.norm(pre_goal_p-new_p) > np.linalg.norm(er)
            rot_opposite = float(ar@er_rot) < 0; rot_along = float(ar@rotation_step) > 0
            rot_away = (pre_goal_r*new_r.inv()).magnitude() > np.linalg.norm(er_rot)
            predicted_target = np.clip(target[k-1]+alpha*(req[k]-target[k-1]),target[k-1]-rate/60,target[k-1]+rate/60)
            predicted_target = np.clip(predicted_target,low,high)
            predicted_request = np.clip(req[k-1]+trace['wrist_requested_delta_rad'][k],low,high)
            error = np.r_[ea,.1*ar]
            row = dict(time_s=time[k],actual_position_error_mm=np.linalg.norm(goal_p-pa)*1000,
                request_virtual_position_error_mm=np.linalg.norm(goal_p-pr)*1000,
                target_virtual_position_error_mm=np.linalg.norm(goal_p-pt)*1000,
                actual_rotation_error_deg=np.rad2deg((goal_r*ra.inv()).magnitude()),
                request_virtual_rotation_error_deg=np.rad2deg((goal_r*rr.inv()).magnitude()),
                target_virtual_rotation_error_deg=np.rad2deg((goal_r*rt.inv()).magnitude()),
                request_actual_max_gap_deg=np.rad2deg(abs(req[k]-actual[k])).max(),
                target_actual_max_gap_deg=np.rad2deg(abs(target[k]-actual[k])).max(),
                request_target_max_gap_deg=np.rad2deg(abs(req[k]-target[k])).max(),
                request_increment_max_deg=np.rad2deg(abs(req[k]-req[k-1])).max(),
                raw_delta_max_deg=np.rad2deg(abs(trace['wrist_requested_delta_rad'][k])).max(),
                pre_actual_position_error_W_m=ea,pre_old_request_position_error_W_m=er,pre_request_step_W_m=step,
                pre_actual_rotation_error_W_rad=ar,pre_old_request_rotation_error_W_rad=er_rot,
                pre_request_step_rotation_W_rad=rotation_step,
                position_actual_dot_old_request_m2=ea@er,position_actual_dot_request_step_m2=ea@step,
                position_old_request_dot_step_m2=er@step,
                rotation_actual_dot_old_request_rad2=ar@er_rot,rotation_actual_dot_request_step_rad2=ar@rotation_step,
                position_virtual_distance_increased=away,rotation_virtual_distance_increased=rot_away,
                position_opposite_halfspace=opposite,rotation_opposite_log_direction=rot_opposite,
                position_continues_actual_direction=along,rotation_continues_actual_direction=rot_along,
                position_accumulation_witness=opposite and along and away,
                rotation_accumulation_witness=rot_opposite and rot_along and rot_away,
                stored_pose_error_max_abs=abs(error-trace['wrist_pose_error_world'][k]).max(),
                request_recurrence_error_rad=abs(predicted_request-req[k]).max(),
                target_smoothing_error_rad=abs(predicted_target-target[k]).max(),
                requested_rate_excess_rad=max(0.,float((abs(req[k]-req[k-1])-rate/60).max())),
                submitted_rate_excess_rad=max(0.,float((abs(target[k]-target[k-1])-rate/60).max())))
            for key,value in row.items():rows[key].append(value)
        curves = {k:np.array(v) for k,v in rows.items()};curves['complete_post_ramp_transition'] = complete
        all_curves[label] = curves
        gates = ('position_opposite_halfspace','rotation_opposite_log_direction','position_continues_actual_direction',
            'rotation_continues_actual_direction','position_virtual_distance_increased','rotation_virtual_distance_increased',
            'position_accumulation_witness','rotation_accumulation_witness')
        firsts = {key:float(curves['time_s'][np.flatnonzero(curves[key])[0]]) if curves[key].any() else None for key in gates}
        last = {key:curves[key][-1].tolist() for key in ('actual_position_error_mm','request_virtual_position_error_mm',
            'target_virtual_position_error_mm','actual_rotation_error_deg','request_virtual_rotation_error_deg','target_virtual_rotation_error_deg')}
        report[label] = dict(full_actual_FK_endpoints=len(time),post_ramp_endpoints=len(ids),complete_post_ramp_transitions=int(complete.sum()),
            FK_native_max_position_m=float(pose_p.max()),FK_native_max_rotation_rad=float(pose_r.max()),
            statistics={k:stats(v) for k,v in curves.items() if v.ndim==1 and v.dtype!=bool and k not in ('time_s',)},
            diagnostic_counts_all102={k:int(curves[k].sum()) for k in gates},
            diagnostic_counts_complete101={k:int(curves[k][complete].sum()) for k in gates},first_witness_endpoint_s=firsts,
            final_endpoint=last,strict_lag_checks=dict(stored_pose_error_max_abs=float(curves['stored_pose_error_max_abs'].max()),
                request_recurrence_max_rad_complete101=float(curves['request_recurrence_error_rad'][complete].max()),
                smoothing_max_rad=float(curves['target_smoothing_error_rad'].max()),
                request_rate_excess_max_rad=float(curves['requested_rate_excess_rad'].max()),
                submitted_rate_excess_max_rad=float(curves['submitted_rate_excess_rad'].max())),
            all_four_reference_outcomes=evaluation['summary'])
    assert 'isaacgym' not in sys.modules
    out.mkdir()
    write(out/'measurements.json',report)
    for label,curves in all_curves.items():
        with (out/(label+'_curves.npz')).open('xb') as stream:np.savez_compressed(stream,**curves)
    both_axes = {}
    for label,c in all_curves.items():
        both = c['position_accumulation_witness'] & c['rotation_accumulation_witness']
        both_axes[label] = dict(both_position_and_rotation_witness=int(both.sum()),
            first_endpoint_s=float(c['time_s'][np.flatnonzero(both)[0]]) if both.any() else None,
            both_virtual_distances_increased=int((c['position_virtual_distance_increased'] & c['rotation_virtual_distance_increased']).sum()))
    write(out/'verification.json',dict(supplementary_postcapture_both_axes_counts=both_axes,CPU_only=True,native_executed=False,GPU_executed=False,input_sha256=pins,
        prior_archive_verification=str(PRIOR),unchanged_used_FK_sources=source_verification,
        scope='three reference env0 traces only; postramp102 endpoints each;101fullpostramp transitions;virtual wrist FK only',
        definitions=dict(position_halfspace='e_actual dot e_old_request <0',
            position_continues='e_actual dot (p_new_request-p_old_request)>0',
            accumulation='halfspace & continues & virtual goal distance increased',
            rotation='same signs using world Log errors and relative request rotation step; local descriptive diagnostic')))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,2,figsize=(11,8.5),sharex=True,constrained_layout=True)
    for i,(label,c) in enumerate(all_curves.items()):
        for key,name in [('actual','actual native-validated FK'),('request_virtual','request virtual FK'),('target_virtual','submitted target virtual FK')]:
            axes[i,0].plot(c['time_s'],c[key+'_position_error_mm'],label=name)
            axes[i,1].plot(c['time_s'],c[key+'_rotation_error_deg'],label=name)
        axes[i,0].set(ylabel=label+'\nposition error (mm)');axes[i,1].set(ylabel='rotation error (deg)')
        for col,key in [(0,'position_accumulation_witness'),(1,'rotation_accumulation_witness')]:
            mask=c[key];axes[i,col].scatter(c['time_s'][mask],np.zeros(mask.sum()),s=9,c='black',label='3-part accumulation witness')
            axes[i,col].grid(alpha=.2)
    for ax in axes[-1]:ax.set_xlabel('endpoint time (s)')
    axes[0,0].legend(fontsize=7);axes[0,1].legend(fontsize=7)
    fig.savefig(out/'tracking_and_virtual_request.png',dpi=160);plt.close(fig)
    print(json.dumps({k:dict(counts=v['diagnostic_counts_all102'],checks=v['strict_lag_checks'],stats={n:v['statistics'][n] for n in ('actual_position_error_mm','request_virtual_position_error_mm','request_actual_max_gap_deg')}) for k,v in report.items()},indent=2))


if __name__ == '__main__':main()
