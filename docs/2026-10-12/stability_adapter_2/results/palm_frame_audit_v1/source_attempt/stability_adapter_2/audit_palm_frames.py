"""Saved palm source points and read-only native t=0 Jacobian readiness; no steps."""
import argparse
import hashlib
import json
from pathlib import Path

from .environment import InitialEnvironment, gymapi, np, vector, quaternion
from .plot_joint_hold import geometry_asset_paths
from .plot_neck_palm import geometry
from .replay_contact_geometry import recorded_probe
from .run_physx_contacts import native_state
from .strap import rotate


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pose(body):
    q = quaternion(body['pose']['r'])
    return vector(body['pose']['p']), q / np.linalg.norm(q)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise FileExistsError('preserve previous audit')
    args.out.mkdir(parents=True, exist_ok=True)
    report, states = read(args.run / 'report.json'), read(args.run / 'states.json')
    offsets, initial_points, records = {}, {}, []
    for step in (0, 240, 720):
        state = states[step]
        if state['physics_step'] != step:
            raise ValueError('saved step layout differs')
        model, data, shapes = recorded_probe(args.run, step)
        points = {}
        for side, prefix in (('L', 'LH'), ('R', 'RH')):
            name = prefix + ':palm'
            body = state['human_body_states'][report['human_body_names'].index(name)]
            origin, q = pose(body)
            shape = next(s for s in shapes if s['actor'] == 'human' and s['body'] == name)
            center = geometry(model, data, shape).center_mass
            inverse = np.r_[-q[:3], q[3]]
            offset = rotate(inverse, center - origin)
            wrist, _ = pose(state['human_body_states'][report['human_body_names'].index(side + '_Wrist')])
            if step == 0:
                offsets[side] = offset.copy()
                initial_points[side] = (center.copy(), origin.copy(), wrist.copy())
            reconstructed = origin + rotate(q, offsets[side])
            points[side] = {'body': name, 'body_origin_world_m': origin.tolist(),
                'source_hull_volume_center_world_m': center.tolist(), 'local_offset_m': offset.tolist(),
                'offset_difference_m': float(np.linalg.norm(offset - offsets[side])),
                'reconstruction_error_m': float(np.linalg.norm(reconstructed - center)),
                'center_displacement_m': float(np.linalg.norm(center - initial_points[side][0])),
                'body_origin_displacement_m': float(np.linalg.norm(origin - initial_points[side][1])),
                'wrist_origin_displacement_m': float(np.linalg.norm(wrist - initial_points[side][2]))}
        records.append({'physics_step': step, 'time_s': step / report['physics_hz'], 'palms': points})
    env = InitialEnvironment(read(args.settings))
    try:
        before = native_state(env)
        target, props, rest = env.target.copy(), env.gym.get_actor_dof_properties(env.env, env.human).copy(), env.rest_length
        descriptor = env.gym.acquire_jacobian_tensor(env.sim, 'human')
        if descriptor is None:
            raise RuntimeError('initial Jacobian descriptor unavailable; no warm-up step allowed')
        # Use the installed supported CPU tensor bridge, after importing Gym.
        from isaacgym import gymtorch
        wrapped = gymtorch.wrap_tensor(descriptor)
        env.gym.refresh_jacobian_tensors(env.sim)
        jac = wrapped.cpu().numpy().copy()
        after = native_state(env)
        expected = (1, len(env.human_bodies) - 1, 6, len(env.names))
        layout = jac.shape == expected
        rows = {side: env.human_bodies.index(prefix + ':palm') - 1 for side, prefix in (('L', 'LH'), ('R', 'RH'))}
        checks = {'saved_source_offsets_consistent': all(p['offset_difference_m'] < 1e-7 and p['reconstruction_error_m'] < 1e-7 for r in records for p in r['palms'].values()),
            'native_initial_state_matches_saved': before == states[0],
            'query_preserves_all_body_dof_states': before == after,
            'query_preserves_targets_PD_and_length': bool(np.array_equal(target, env.target) and np.array_equal(props, env.gym.get_actor_dof_properties(env.env, env.human)) and rest == env.rest_length),
            'no_physics_steps': env.steps == 0, 'fixed_root_tensor_shape': layout,
            'tensor_finite': bool(np.isfinite(jac).all()), 'tensor_CPU': wrapped.device.type == 'cpu'}
        readiness = {side: bool(np.abs(jac[0, row]).max() > 1e-12) if layout else False for side, row in rows.items()}
        tensor = {'shape': list(jac.shape), 'expected_fixed_root_shape': list(expected), 'device': str(wrapped.device),
            'dtype': str(wrapped.dtype), 'palm_rows': rows, 'palm_rows_nonzero': readiness,
            'joint_names': list(env.names), 'body_names': env.human_bodies, 'values': jac.tolist()}
        (args.out / 'jacobian.json').write_text(json.dumps(tensor, indent=2, allow_nan=False) + '\n')
    finally:
        env.close()
    helpers = ['audit_palm_frames.py', 'environment.py', 'plot_joint_hold.py', 'plot_neck_palm.py', 'replay_contact_geometry.py', 'initial_overlap.py', 'strap.py', 'run_physx_contacts.py']
    paths = [Path(__file__).with_name(n) for n in helpers] + geometry_asset_paths() + [args.settings, args.run / 'report.json', args.run / 'states.json', Path(__file__).resolve().parents[1] / 'isaacgym/docs/programming/tensors.html']
    paths += [Path(p) for p in report['source_sha256']]
    result = {'scope': 'point-frame and initial tensor readiness only; no FK/Jacobian validation or new controller',
        'checks': checks, 'palm_rows_nonzero': readiness, 'saved_points': records,
        'semantics': 'source convex-hull volume center, not surface contact/anatomical center/native COM; row nonzero does not prove correct Jacobian frame or point',
        'input_sha256': {str(p.resolve()): sha(p) for p in paths}}
    (args.out / 'audit.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'checks': checks, 'palm_rows_nonzero': readiness, 'points': records}, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
