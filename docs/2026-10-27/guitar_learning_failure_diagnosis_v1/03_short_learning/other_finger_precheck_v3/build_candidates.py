"""CPU extraction of three unverified fixed-wrist teacher/reference candidates."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[1]
ROOT = DIAG.parents[2]
sys.path.insert(0, str(ROOT))
ROWS = (('index', 1, 1), ('ring', 16, 3), ('pinky', 23, 4))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def main():
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.core.control import ACTIVE_NAMES, LEFT_ARM_NAMES
    from guitar_learning.runtime import prepared_reset_v1 as prepared
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.native.lower_body_release_v1.common import HUMAN
    from guitar_learning.tool.experiments.short_finger_learning.runner import make_settings
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment, ShortPolicy, teacher_goal
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_teacher, read_reference

    assert not torch.cuda.is_available(), 'CPU preparation requires CUDA_VISIBLE_DEVICES empty'
    torch.set_num_threads(1)
    source = DIAG/'02_contact_reward/teacher_fixed_B_export'
    metadata = json.loads((source/'metadata.json').read_text())
    report = json.loads((source/'report.json').read_text())
    original_pins = json.loads((source/'inputs_before.json').read_text())
    assert report['completed'] and report['failure'] is None and not report['changed_inputs']
    trace, poses = np.load(source/'teacher_trace60.npz'), np.load(source/'poses60.npz')
    contract = prepared.load_prepared_reset_contract()
    names, bodies, state = metadata['joint_names'], metadata['human_bodies'], contract['state']
    q0 = np.array([row['pos'] for row in state['human_dof_states']])
    fk = full_fk(SimpleNamespace(names=names, human_bodies=bodies, q_ref=q0), state)
    gp = np.array([state['guitar_body_states'][0]['pose']['p'][a] for a in 'xyz'])
    gr = Rotation.from_quat([state['guitar_body_states'][0]['pose']['r'][a] for a in 'xyzw'])
    wrist = metadata['body_names'].index('human/L_Wrist')
    guitar = metadata['body_names'].index('guitar/guitar')
    trace_rows = report['protocol']['trace_rows']
    errors = []
    for tick in range(0, len(poses['tick']), 30):
        for slot, row in enumerate(trace_rows):
            position, rotation = fk(poses['q'][tick, slot])['L_Wrist']
            native = poses['body_state'][tick, slot, wrist]
            errors.append((float(np.linalg.norm(position-native[:3])),
                float((rotation.inv()*Rotation.from_quat(native[3:7])).magnitude())))
    crosscheck = dict(samples=len(errors), maximum_position_error_m=max(e[0] for e in errors),
        maximum_rotation_error_rad=max(e[1] for e in errors))
    assert crosscheck['samples'] == 84 and crosscheck['maximum_position_error_m'] < 1e-5
    assert crosscheck['maximum_rotation_error_rad'] < 1e-5
    evidence = [source/name for name in ('inputs_before.json', 'report.json', 'teacher_trace60.npz', 'metadata.json', 'poses60.npz')]
    evidence += [Path(__file__).resolve(), HERE/'run_prechecks.py', Path(HUMAN),
        ROOT/'guitar_learning/native/lower_body_release_v1/controller_horizontal_v4.py',
        ROOT/'guitar_learning/native/lower_body_release_v1/common.py', ROOT/'guitar_learning/runtime/prepared_reset_v1.py',
        *prepared.SOURCE_SHA256]
    for path in evidence[7:]:
        recorded = [original_pins[key] for key in (str(path), str(path.resolve())) if key in original_pins]
        assert recorded and all(value == sha(path) for value in recorded), str(path)
    source_evidence = {str(path.absolute()):sha(path) for path in evidence}
    active = [names.index(name) for name in ACTIVE_NAMES]
    arm = [names.index(name) for name in LEFT_ARM_NAMES]
    lower = np.array(metadata['action_contract']['action_lower_rad'])
    upper = np.array(metadata['action_contract']['action_upper_rad'])
    extracted = []
    for finger_name, row, finger in ROWS:
        goal = report['goals'][row]
        assert goal['finger'] == finger and goal['failure'] is None
        now = trace['observed_time_s']
        good = (trace['active'][:, row] & trace['candidate'][:, row] & ~trace['wrong'][:, row]
            & ~np.maximum.accumulate(trace['wrist_shadow_failure'][:, row])
            & (abs(trace['wrist_guide_excess_G_m'][:, row]).max(-1) <= .02) & (now >= 5.))
        eligible = np.flatnonzero(np.convolve(good.astype(int), np.ones(4, dtype=int), 'full')[:len(now)] == 4)
        assert int(good.sum()) == 90 and len(eligible) == 87
        k = int(eligible[np.argmin(trace['body_force_n'][eligible, row])])
        q, target = trace['actual_q105_rad'][k, row], trace['actual_target105_rad'][k, row]
        assert np.array_equal(target[active], trace['current_target39_rad'][k, row])
        assert np.isfinite(np.r_[q, target]).all() and ((target[active] >= lower) & (target[active] <= upper)).all()
        selected_names = ['LH:'+finger_name+suffix for suffix in ('1_x', '1_z', '2', '3')]
        selected = [names.index(name) for name in selected_names]
        position, rotation = fk(q)['L_Wrist']
        quaternion = (gr.inv()*rotation).as_quat()
        if quaternion[3] < 0:
            quaternion = -quaternion
        direct = None
        if row in trace_rows:
            slot = trace_rows.index(row)
            p = int(np.flatnonzero(poses['tick'] == round(now[k]*60))[0])
            native_wrist, native_guitar = poses['body_state'][p, slot, wrist], poses['body_state'][p, slot, guitar]
            native_G = Rotation.from_quat(native_guitar[3:7]).inv().apply(native_wrist[:3]-native_guitar[:3])
            direct = dict(wrist_pose_W=native_wrist[:7].tolist(), guitar_pose_W=native_guitar[:7].tolist(),
                actual_wrist_position_G_m=native_G.tolist(),
                FK_position_error_W_m=float(np.linalg.norm(position-native_wrist[:3])),
                FK_vs_native_position_G_m=float(np.linalg.norm(gr.inv().apply(position-gp)-native_G)))
        teacher = dict(schema='short_finger_teacher.v2', condition='fixed_wrist_pose',
            source_target_id=goal['target_id'], finger=finger, finger_name=finger_name,
            arm_targets_rad={name:float(target[i]) for name, i in zip(LEFT_ARM_NAMES, arm)}, ramp_s=2.,
            wrist_position_G_m=gr.inv().apply(position-gp).tolist(), wrist_quaternion_G_xyzw=quaternion.tolist(),
            source_evidence=source_evidence, source_row=row, source_time_s=float(now[k]),
            source_next_command_time_s=float(trace['time_s'][k]), arm_only_contact_verified=False,
            scope='Unverified candidate only; fixed source wrist pose reconstructed from actual q; current onset3s arm-only condition not tested',
            source_selection='observed>=5s; four consecutive60Hz active candidate/wrong0, no cumulative shadow failure, excess<=20mm; minimum distal resultant',
            source_condition='fixed guitar; other fingers B; pad+wrist DLS arm12+selected4; static original-note midpoint',
            diagnostic_metadata=dict(source_note_index=goal['source_note_index'], body_resultant_n=float(trace['body_force_n'][k, row]),
                qualifying_endpoints=int(good.sum()), four_consecutive_candidates=len(eligible), FK_native_crosscheck=crosscheck,
                wrist_pose_source='prepared-calibrated FK of actual q105; not native direct readback for rows without stored body_state',
                guitar_pose_source='prepared fixed guitar root, same conversion as middle v2; per-row native pose unavailable except saved representative rows',
                source_max_guitar_displacement_m=goal['maximum_guitar_displacement_m'],
                source_max_guitar_rotation_rad=goal['maximum_guitar_rotation_rad'], native_direct_readback=direct,
                actual_arm_rad={name:float(q[i]) for name, i in zip(LEFT_ARM_NAMES, arm)},
                selected_finger_actual_rad={name:float(q[i]) for name, i in zip(selected_names, selected)},
                selected_finger_contact_target_rad={name:float(target[i]) for name, i in zip(selected_names, selected)},
                selected_finger_original_geometry_goal_rad={name:float(goal['q_target105'][i]) for name, i in zip(selected_names, selected)},
                feedforward_warning='Controller targets are not actual contact angles or a proven equilibrium'))
        teacher_path = HERE/('teacher_%s_row%d.json' % (finger_name, row))
        reference_path = HERE/('reference_%s_row%d.json' % (finger_name, row))
        write(teacher_path, teacher)
        reference = dict(schema='short_finger_reference.v2', source_target_id=goal['target_id'], ramp_s=2.,
            selected_targets_rad=teacher['diagnostic_metadata']['selected_finger_contact_target_rad'],
            source_evidence={str(teacher_path):sha(teacher_path)},
            scope='Unverified finite selected4 contact-target reference; same wrist teacher/onset3s; not policy performance')
        write(reference_path, reference)
        args = argparse.Namespace(teacher=str(teacher_path), mode='incremental', initial_std=.1711710544767014,
            song='05_BN2-131-B_solo', size='large', num_envs=4, horizon=32, updates=1, save_every=50, seed=7)
        settings = make_settings(args)
        spec = settings['song']['short_learning']
        assert read_teacher(teacher_path)['finger'] == finger and read_reference(reference_path, spec) == reference
        env = ShortEnvironment(metadata, bundle=settings['song_training']['bundle'], song=settings['song'],
            skill=settings['finger_skill'], device='cpu')
        policy = ShortPolicy(contract=env.contract, size='large')
        assert env.contract['observation']['dimension'] == 561 and int(policy._active_mask().sum()) == 4
        request = teacher_goal(torch.tensor(metadata['reference105'])[active], spec).numpy()
        assert ((request >= lower) & (request <= upper)).all()
        assert spec['view']['local_onset_s'] == 3. and spec['view']['source_index'] == goal['source_note_index']
        extracted.append(dict(finger=finger_name, row=row, source_target_id=goal['target_id'], source_time_s=float(now[k]),
            body_resultant_n=float(trace['body_force_n'][k, row]), teacher_path=str(teacher_path), teacher_sha256=sha(teacher_path),
            reference_path=str(reference_path), reference_sha256=sha(reference_path), source_index=spec['view']['source_index'],
            local_press_s=spec['view']['local_press_s'], local_end_s=spec['view']['local_end_s'],
            learned_action_names=spec['learned_action_names'], native_direct_readback_available=direct is not None))
    for path in (Path(__file__), HERE/'run_prechecks.py'):
        ast.parse(path.read_text(), feature_version=(3, 8))
    assert not torch.cuda.is_initialized()
    write(HERE/'cpu_verification.json', dict(schema='other_finger_precheck_cpu.v3', GPU_executed=False,
        CUDA_initialized=False, FK_native_crosscheck=crosscheck, candidates=extracted,
        source_evidence=source_evidence, current_teacher_spec_reference_readers_pass=True,
        teacher_goals_within_actual_controller_bounds=True, observation_dim=561, selected_axes=4,
        python38_syntax=True, limitation='candidate extraction/CPU contracts only; no arm-only onset3s native contact verification'))
    print(json.dumps(dict(candidates=extracted, FK_native_crosscheck=crosscheck, GPU_executed=False), ensure_ascii=False))


if __name__ == '__main__':
    main()
