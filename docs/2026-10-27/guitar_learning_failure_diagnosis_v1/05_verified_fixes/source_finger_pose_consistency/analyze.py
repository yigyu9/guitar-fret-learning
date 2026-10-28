"""CPU-only comparison of frozen source snapshots and v3 env0 native traces."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DIAG = HERE.parents[1]
SOURCE = DIAG / '02_contact_reward/teacher_fixed_B_export'
RUNS = DIAG / '05_verified_fixes/wrist_position_candidate_v3/native_precheck/runs'
CASES = {
    'index': (
        DIAG / '03_short_learning/other_finger_precheck_v3/teacher_index_row1.json',
        DIAG / '03_short_learning/other_finger_precheck_v3/reference_index_row1.json'),
    'middle': (
        DIAG / '02_contact_reward/short_finger_wrist_teacher_middle_row8_v2.json',
        DIAG / '03_short_learning/reference_middle_row8_v2.json'),
}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stats(values):
    x = np.asarray(values, dtype=np.float64)
    assert x.size and np.isfinite(x).all()
    return dict(min=np.min(x, axis=0).tolist(), median=np.median(x, axis=0).tolist(),
                max=np.max(x, axis=0).tolist(), max_abs=float(np.max(np.abs(x))))


def deg(x):
    return np.rad2deg(np.asarray(x, dtype=np.float64))


def relative(body, finger):
    palm = body[..., 18, :]
    distal = body[..., finger, :]
    rp = Rotation.from_quat(palm[..., 3:7])
    return (rp.inv().apply(distal[..., :3] - palm[..., :3]),
            rp.inv() * Rotation.from_quat(distal[..., 3:7]))


def main():
    used = set()
    evidence = []
    visited = set()

    def follow(path):
        path = Path(path)
        if path in visited:
            return
        visited.add(path)
        used.add(path)
        for name, expected in read(path).get('source_evidence', {}).items():
            p = Path(name)
            actual = sha(p) if p.exists() else None
            evidence.append(dict(owner=str(path), path=name, expected=expected,
                                 actual=actual, equal=(actual == expected)))
            assert actual == expected, name
            used.add(p)
            if p.suffix == '.json':
                follow(p)

    for pair in CASES.values():
        for path in pair:
            follow(path)

    paths = ['metadata.json', 'report.json', 'inputs_before.json',
             'teacher_trace60.npz', 'poses60.npz', 'human_shape_and_force_readback.json']
    used.update(SOURCE / name for name in paths)
    meta, report = read(SOURCE / paths[0]), read(SOURCE / paths[1])
    source_pins = read(SOURCE / 'inputs_before.json')
    assert report['completed'] and not report['changed_inputs'] and report['failure'] is None
    names = meta['joint_names']
    trace = np.load(SOURCE / 'teacher_trace60.npz', allow_pickle=False)
    poses = np.load(SOURCE / 'poses60.npz', allow_pickle=False)
    ref = np.asarray(meta['reference105'])
    result = {'scope': 'CPU only; current reference env0 first attempt, 60Hz endpoints; '
                       'frozen source row/time, no current gate recomputation or finger FK',
              'source_input_after_scope': 'No inputs_after.json stored; source report completed '
                                          'with changed_inputs empty. Historical before map preserved.',
              'source_evidence_edges': evidence, 'cases': {}}
    critical = ['guitar_learning/assets/tab2body/assets/smpl_mpl_hands_body.xml',
                'guitar_learning/gpu/scene.py', 'guitar_learning/gpu/hand_collision.py',
                'guitar_learning/core/finger_control.py', 'guitar_learning/gpu/control.py',
                'guitar_learning/runtime/prepared_reset_v1.py']
    for finger, (teacher_path, reference_path) in CASES.items():
        teacher, reference = read(teacher_path), read(reference_path)
        row = teacher['source_row']
        k = int(np.argmin(abs(trace['observed_time_s'] - teacher['source_time_s'])))
        assert abs(trace['observed_time_s'][k] - teacher['source_time_s']) < 1e-12
        assert report['goals'][row]['target_id'] == teacher['source_target_id']
        sq = trace['actual_q105_rad'][k, row].astype(np.float64)
        st = trace['actual_target105_rad'][k, row].astype(np.float64)
        run = RUNS / (finger + '_reference')
        files = ['trace_env0_episode0.npz', 'trace_metadata.json', 'training_contract.json',
                 'inputs_before.json', 'inputs_after.json', 'gpu_scene_final.json', 'report.json']
        used.update(run / name for name in files)
        z = np.load(run / files[0], allow_pickle=False)
        cm, contract, scene = (read(run / name) for name in files[1:3] + files[5:6])
        current_pins = read(run / 'inputs_before.json')
        after = read(run / 'inputs_after.json')
        assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
        assert current_pins == after['input_pins']
        assert read(run / 'report.json')['completed'] and read(run / 'report.json')['closed']
        assert names == cm['joint_names'] and meta['body_names'] == cm['body_names']
        assert meta['action_contract'] == contract['action']['target_contract']
        assert meta['hand_collision'] == scene['hand_collision']
        critical_pins = {}
        for rel in critical:
            p = ROOT / rel
            assert source_pins[str(p)] == current_pins[str(p)] == sha(p)
            used.add(p)
            critical_pins[rel] = sha(p)
        shared = sorted(set(source_pins) & set(current_pins))
        changed = {p: dict(source=source_pins[p], current=current_pins[p])
                   for p in shared if source_pins[p] != current_pins[p]}
        scene_diff = {key: dict(source=report['scene'].get(key), current=scene.get(key))
                      for key in sorted(set(report['scene']) | set(scene))
                      if report['scene'].get(key) != scene.get(key)}
        c = int(np.argmin(abs(z['time_s'] - 3)))
        assert abs(z['time_s'][c] - 3) < 1e-12
        view = contract['task']['short_learning']['view']
        masks = {'audible': (z['time_s'] >= view['local_onset_s'] - 1e-9) &
                           (z['time_s'] <= view['local_end_s'] + 1e-9),
                 'postramp': z['time_s'] >= 2 - 1e-9}
        groups = {
            'selected4': [i for i, n in enumerate(names) if n.startswith('LH:' + finger)],
            'arm12': list(range(39, 51)),
            'other_fingers12': [i for i, n in enumerate(names) if n.startswith('LH:') and
                                'thumb' not in n and not n.startswith('LH:' + finger)],
            'thumb5': list(range(51, 56)),
        }
        cols = groups['selected4']
        assert np.array_equal(st[cols], [reference['selected_targets_rad'][names[i]] for i in cols])
        assert np.array_equal(z['target'][c, cols], st[cols])
        selected_diag = teacher['diagnostic_metadata']
        recorded_q = selected_diag.get('selected_finger_actual_rad',
                                      selected_diag.get('selected_finger_contact_actual_rad'))
        assert np.array_equal(sq[cols], [recorded_q[names[i]] for i in cols])
        case = dict(source_row=row, source_observed_s=float(trace['observed_time_s'][k]),
                    source_next_command_s=float(trace['time_s'][k]), source_trace_index=k,
                    source_selected_candidate=bool(trace['candidate'][k, row]),
                    source_selected_wrong=bool(trace['wrong'][k, row]),
                    source_selected_shadow_failed=bool(trace['wrist_shadow_failure'][k, row]),
                    source_selected_resultant_n=float(trace['body_force_n'][k, row]),
                    current_endpoint_s=float(z['time_s'][c]), current_endpoint_index=c,
                    window_counts={key: int(mask.sum()) for key, mask in masks.items()},
                    group_comparisons={}, physics=dict(action_contract_exact=True,
                    hand_collision_exact=True, critical_source_sha=critical_pins,
                    shared_pin_count=len(shared), shared_changed_pins=changed,
                    scene_readback_differences=scene_diff))
        for group, ids in groups.items():
            x = dict(names=[names[i] for i in ids], source_actual_deg=deg(sq[ids]).tolist(),
                     source_native_target_deg=deg(st[ids]).tolist(),
                     source_geometry_goal_deg=deg(np.asarray(report['goals'][row]['q_target105'])[ids]).tolist(),
                     prepared035_target_deg=deg(ref[ids]).tolist(),
                     current_actual_3s_deg=deg(z['q'][c, ids]).tolist(),
                     current_target_3s_deg=deg(z['target'][c, ids]).tolist(),
                     target_difference_3s_deg=deg(z['target'][c, ids] - st[ids]).tolist(),
                     actual_difference_3s_deg=deg(z['q'][c, ids] - sq[ids]).tolist(),
                     source_target_minus_actual_deg=deg(st[ids] - sq[ids]).tolist(), windows={})
            for key, mask in masks.items():
                x['windows'][key] = dict(
                    actual_minus_source_actual_deg=stats(deg(z['q'][mask][:, ids] - sq[ids])),
                    target_minus_source_target_deg=stats(deg(z['target'][mask][:, ids] - st[ids])),
                    current_target_minus_actual_deg=stats(deg(z['target'][mask][:, ids] - z['q'][mask][:, ids])))
            case['group_comparisons'][group] = x
        case['thumb_target_exact_source_current035'] = bool(
            np.array_equal(st[groups['thumb5']], ref[groups['thumb5']]) and
            np.array_equal(st[groups['thumb5']], z['target'][c, groups['thumb5']]))
        active = [names.index(n) for n in meta['action_contract']['action_order']]
        case['source_next_selected_target_deg'] = deg(
            trace['corrected_target39_rad'][k, row][[active.index(i) for i in cols]]).tolist()
        case['native_finger_pose'] = {'available': False,
            'reason': 'row8 not among source poses60 trace_rows; no finger FK substitute'}
        if row in report['protocol']['trace_rows']:
            slot = report['protocol']['trace_rows'].index(row)
            pk = int(np.argmin(abs(poses['tick'] / 60 - teacher['source_time_s'])))
            assert abs(poses['tick'][pk] / 60 - teacher['source_time_s']) < 1e-12
            assert poses['valid'][pk, slot]
            assert np.array_equal(poses['q'][pk, slot], sq)
            assert np.array_equal(poses['target'][pk, slot], st)
            native = dict(available=True, source_tick=int(poses['tick'][pk]), source_slot=slot,
                          aligned_q_and_target_exact=True,
                          position_scope='stored native body-state positions expressed in saved palm frame; '
                                         'not a selected pad point or contact pair', bodies={})
            for segment in (1, 2, 3):
                name = 'human/LH:' + finger + str(segment)
                bi = meta['body_names'].index(name)
                sp, sr = relative(poses['body_state'][pk, slot], bi)
                cp, cr = relative(z['body_state'], bi)
                angle = np.rad2deg((sr.inv() * cr).magnitude())
                dp = (cp - sp) * 1000
                native['bodies'][name] = dict(source_palm_relative_position_m=sp.tolist(),
                    source_palm_relative_xyzw=sr.as_quat().tolist(),
                    source_palm_relative_log_rad=sr.as_rotvec().tolist(),
                    current_3s_palm_relative_position_m=cp[c].tolist(),
                    current_3s_palm_relative_xyzw=cr[c].as_quat().tolist(),
                    current_3s_palm_relative_log_rad=cr[c].as_rotvec().tolist(),
                    current_3s_position_difference_mm=dp[c].tolist(),
                    current_3s_rotation_difference_deg=float(angle[c]),
                    windows={key: dict(position_difference_mm=stats(dp[mask]),
                        position_difference_norm_mm=stats(np.linalg.norm(dp[mask], axis=1)),
                        rotation_difference_deg=stats(angle[mask])) for key, mask in masks.items()})
            case['native_finger_pose'] = native
        result['cases'][finger] = case
    result['source_protocol'] = report['protocol']
    initial_path = ROOT / 'docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/initial_values.json'
    initial = read(initial_path)
    used.add(initial_path)
    rb = read(SOURCE / 'human_shape_and_force_readback.json')
    assert rb['native_effort_caps'] == initial['native_PD_properties']['effort']
    assert rb['native_drive_modes'] == initial['native_PD_properties']['driveMode']
    result['PD_evidence'] = dict(source_native_effort_and_drive_mode_match_prepared=True,
        initialization='unchanged pinned scene.py copies prepared native_PD_properties, '
                       'overrides same flexible-left finger/thumb stiffness/damping profile, '
                       'then asserts full native property readback exact',
        limitation='No separate full stiffness/damping array saved for each compared run; '
                   'same initialization/readback assertion and source pins are evidence, not a new native readback.')
    result['input_sha256'] = {str(p): sha(p) for p in sorted(used)}
    result['analysis_sha256'] = sha(__file__)
    (HERE / 'comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({f: dict(source_time_s=c['source_observed_s'], windows=c['window_counts'],
                     thumb_exact=c['thumb_target_exact_source_current035'])
                     for f, c in result['cases'].items()}, indent=2))


if __name__ == '__main__':
    main()
