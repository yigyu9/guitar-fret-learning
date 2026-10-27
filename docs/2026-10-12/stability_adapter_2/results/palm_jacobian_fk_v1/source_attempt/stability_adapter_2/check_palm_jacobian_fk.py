"""Compare a saved initial Jacobian with fresh native FK probes; no rollout."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from .environment import InitialEnvironment, gymapi, np
from .audit_palm_frames import pose
from .run_physx_contacts import native_state
from .strap import rotate


def read(path):
    return json.loads(path.read_text())


def rotation(q):
    return np.column_stack([rotate(q, axis) for axis in np.eye(3)])


def angular_difference(a, b):
    relative = rotation(b) @ rotation(a).T
    v = .5 * np.array([relative[2, 1] - relative[1, 2], relative[0, 2] - relative[2, 0], relative[1, 0] - relative[0, 1]])
    length = float(np.linalg.norm(v))
    return v if length < 1e-12 else v * np.arctan2(length, (np.trace(relative) - 1) / 2) / length


def point_jacobian(native, offset_world):
    x, y, z = offset_world
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return native[:3] - skew @ native[3:]


def observe(settings, offset):
    env = InitialEnvironment(settings)
    try:
        before = native_state(env)
        index = env.human_bodies.index('LH:palm')
        origin, q = pose(before['human_body_states'][index])
        com = env.gym.get_actor_rigid_body_properties(env.env, env.human)[index].com
        local_com = np.array([com.x, com.y, com.z])
        props = env.gym.get_actor_dof_properties(env.env, env.human).copy()
        record = {'settings': settings, 'state': before, 'body_names': env.human_bodies,
            'joint_names': env.names, 'initial_targets_rad': env.initial_q.tolist(),
            'palm_origin_world_m': origin.tolist(), 'palm_quaternion_xyzw': q.tolist(),
            'palm_local_com_m': local_com.tolist(), 'palm_com_world_m': (origin + rotate(q, local_com)).tolist(),
            'source_center_world_m': (origin + rotate(q, offset)).tolist(),
            'PD_properties': props.tolist(), 'physics_parameters': env.physics_parameters,
            'absolute_rest_length_m': env.rest_length, 'initial_route_length_m': env.initial_route_length,
            'checks': {'reads_preserve_all_states': before == native_state(env),
                'zero_steps': env.steps == 0, 'targets_equal_initial': bool(np.array_equal(env.target, env.initial_q)),
                'PD_reads_preserve_properties': bool(np.array_equal(props, env.gym.get_actor_dof_properties(env.env, env.human)))}}
        return record
    finally:
        env.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frame-dir', type=Path, required=True)
    parser.add_argument('--reference-run', type=Path, required=True)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise FileExistsError('preserve previous FK comparison')
    args.out.mkdir(parents=True, exist_ok=True)
    audit, saved = read(args.frame_dir / 'audit.json'), read(args.frame_dir / 'jacobian.json')
    if not all(audit['checks'].values()) or not all(saved['palm_rows_nonzero'].values()):
        raise ValueError('prior readiness audit did not pass')
    if not all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in audit['input_sha256'].items()):
        raise ValueError('prior readiness input SHA mismatch')
    report = read(args.reference_run / 'report.json')
    settings = read(args.settings)
    offset = np.array(audit['saved_points'][0]['palms']['L']['local_offset_m'])
    base = observe(settings, offset)
    (args.out / 'baseline.json').write_text(json.dumps(base, indent=2, allow_nan=False) + '\n')
    initial = np.array(base['initial_targets_rad'])
    names = base['joint_names']
    columns = [i for i in report['arm_indices'] if names[i].startswith('L_')]
    native = np.array(saved['values'])[0, saved['palm_rows']['L']][:, columns]
    origin = np.array(base['palm_origin_world_m'])
    com = np.array(base['palm_com_world_m'])
    center = np.array(base['source_center_world_m'])
    source_from_origin = point_jacobian(native, center - origin)
    source_from_com = point_jacobian(native, center - com)
    rows, probe_paths = [], []
    for col, index in enumerate(columns):
        name = names[index]
        arm_column = report['arm_indices'].index(index)
        low, high = report['diagnostic_lower_rad'][arm_column], report['diagnostic_upper_rad'][arm_column]
        negative, positive = initial[index] - low, high - initial[index]
        if min(negative, positive) >= .001:
            deltas, method = (-.001, .001), 'central'
        elif positive >= negative and positive > 1e-6:
            deltas, method = (0., min(.001, positive)), 'forward'
        elif negative > 1e-6:
            deltas, method = (-min(.001, negative), 0.), 'backward'
        else:
            raise ValueError('no representable approved FK interval: ' + name)
        pair = []
        for label, delta in zip(('low', 'high'), deltas):
            path = None
            if delta == 0:
                sample = copy.deepcopy(base)
            else:
                changed = copy.deepcopy(settings)
                changed['joint_angles_rad'][name] = float(initial[index] + delta)
                sample = observe(changed, offset)
                path = args.out / (name + '_' + label + '.json')
            q = np.array(sample['initial_targets_rad'])
            other = np.arange(len(q)) != index
            sample['checks'].update({'only_one_initial_joint_changed': bool(np.array_equal(q[other], initial[other])),
                'probe_in_approved_box': low - 2e-7 <= q[index] <= high + 2e-7 and abs(q[index] - initial[index]) <= .001 + 2e-7,
                'guitar_and_root_initial_states_held': sample['state']['guitar_body_states'] == base['state']['guitar_body_states'] and sample['state']['human_body_states'][0] == base['state']['human_body_states'][0],
                'PD_physics_LA_and_local_COM_held': sample['PD_properties'] == base['PD_properties'] and sample['physics_parameters'] == base['physics_parameters'] and sample['absolute_rest_length_m'] == base['absolute_rest_length_m'] and sample['palm_local_com_m'] == base['palm_local_com_m']})
            if path is not None:
                path.write_text(json.dumps(sample, indent=2, allow_nan=False) + '\n')
                probe_paths.append(path)
            pair.append(sample)
        a, b = pair
        dq = b['initial_targets_rad'][index] - a['initial_targets_rad'][index]
        if dq <= 1e-6:
            raise ValueError('actual native q interval too small')
        fd = {key: (np.array(b[key]) - np.array(a[key])) / dq for key in ('palm_origin_world_m', 'palm_com_world_m', 'source_center_world_m')}
        angular = angular_difference(np.array(a['palm_quaternion_xyzw']), np.array(b['palm_quaternion_xyzw'])) / dq
        rows.append({'joint': name, 'dof_column': index, 'method': method, 'actual_q_interval_rad': dq,
            'checks': {k: all(s['checks'][k] for s in pair) for k in pair[0]['checks']},
            'native_linear': native[:3, col].tolist(), 'native_angular': native[3:, col].tolist(),
            'FD_origin_m_per_rad': fd['palm_origin_world_m'].tolist(), 'FD_COM_m_per_rad': fd['palm_com_world_m'].tolist(),
            'FD_source_m_per_rad': fd['source_center_world_m'].tolist(), 'FD_angular_rad_per_rad': angular.tolist(),
            'origin_error_m_per_rad': float(np.linalg.norm(fd['palm_origin_world_m'] - native[:3, col])),
            'COM_error_m_per_rad': float(np.linalg.norm(fd['palm_com_world_m'] - native[:3, col])),
            'source_from_origin_error_m_per_rad': float(np.linalg.norm(fd['source_center_world_m'] - source_from_origin[:, col])),
            'source_from_COM_error_m_per_rad': float(np.linalg.norm(fd['source_center_world_m'] - source_from_com[:, col])),
            'angular_error_rad_per_rad': float(np.linalg.norm(angular - native[3:, col]))})
    paths = [args.settings, args.frame_dir / 'audit.json', args.frame_dir / 'jacobian.json', args.reference_run / 'report.json', args.reference_run / 'states.json', Path(__file__).resolve(), args.out / 'baseline.json'] + probe_paths + [Path(p) for p in audit['input_sha256']]
    checks = {'baseline_matches_saved_state': base['state'] == read(args.reference_run / 'states.json')[0],
        'baseline_targets_and_layout_match': base['initial_targets_rad'] == report['initial_joint_targets_rad'] and names == report['human_joint_names'] and base['body_names'] == report['human_body_names'],
        'left12_columns_and_row': len(columns) == 12 and saved['palm_rows']['L'] == base['body_names'].index('LH:palm') - 1,
        'all_probe_contracts': all(all(r['checks'].values()) for r in rows), 'baseline_query_contracts': all(base['checks'].values()),
        'saved_source_center_matches_baseline': bool(np.linalg.norm(center - np.array(audit['saved_points'][0]['palms']['L']['source_hull_volume_center_world_m'])) < 1e-7)}
    result = {'scope': 'fresh t=0 FK derivatives vs saved initial velocity Jacobian; no runtime/controller/stability certificate',
        'checks': checks, 'rows': rows, 'max_errors': {key: max(r[key] for r in rows) for key in ('origin_error_m_per_rad', 'COM_error_m_per_rad', 'source_from_origin_error_m_per_rad', 'source_from_COM_error_m_per_rad', 'angular_error_rad_per_rad')},
        'input_sha256': {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (args.out / 'comparison.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'checks': checks, 'max_errors': result['max_errors'], 'probes': len(probe_paths)}, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
