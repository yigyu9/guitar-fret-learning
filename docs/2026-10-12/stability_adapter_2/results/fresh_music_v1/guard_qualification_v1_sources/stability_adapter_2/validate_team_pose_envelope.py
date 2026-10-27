"""Fresh native transfer diagnostics; reconstructed team poses are not source replays."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation as R

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
CANDIDATE = RESULTS / 'underneck_initial_pose_v1/refine/candidate_w10000.json'
BODY_CENTER_G = np.array([0., -.4, -.0217])


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, value): Path(p).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def reconstruct(pelvis_position, pelvis_quaternion, center_rfu, elevation, azimuth, roll):
    """Explicit new convention: body-center pivot, right=-X, forward=-Y in Pelvis."""
    basis = R.from_quat(pelvis_quaternion).apply([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
    right, forward, up = basis
    if np.linalg.norm(up-[0, 0, 1]) > 1e-5:
        raise ValueError('This transfer diagnostic requires an upright fixed Pelvis')
    elev, azim = np.radians([elevation, azimuth])
    neck = np.cos(elev)*(-right*np.cos(azim)-forward*np.sin(azim))+np.sin(elev)*up
    front = forward-neck*(neck @ forward)
    front /= np.linalg.norm(front)
    rotation = R.from_matrix(np.column_stack((np.cross(neck, front), neck, front)))
    rotation = rotation*R.from_rotvec([0., np.radians(roll), 0.])
    center = np.asarray(pelvis_position)+np.asarray(center_rfu) @ basis
    return center-rotation.apply(BODY_CENTER_G), rotation.as_quat()


def source_intersections(env):
    from .initial_overlap import build_probe
    from .face_referenced_geometry import face_geometry
    from .palm_side_source_checks import intersection
    import trimesh
    model, data, shapes = build_probe(env)
    meshes = {s['geom_id']: face_geometry(model, data, s) for s in shapes}
    chair = env.pose['params']['chair']
    box = trimesh.creation.box(extents=2*np.array(chair['half']))
    box.apply_translation([*chair['center_xy'], chair['half'][2]])
    rows = []
    for g in [s for s in shapes if s['actor'] == 'guitar']:
        for h in [s for s in shapes if s['actor'] == 'human']:
            radius = intersection(meshes[h['geom_id']], meshes[g['geom_id']])
            if radius > 1e-7:
                rows.append({'human': h['body'], 'guitar': g['body'], 'guitar_geom_id': g['geom_id'],
                             'common_internal_radius_m': radius})
        radius = intersection(box, meshes[g['geom_id']])
        if radius > 1e-7:
            rows.append({'human': 'chair', 'guitar': g['body'], 'guitar_geom_id': g['geom_id'],
                         'common_internal_radius_m': radius})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('current_control', 'reported_reference', 'reported_center'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    from .underneck_pose_trial_v5 import UnderneckEnvironment
    from .run_joint_hold import native_state
    from .underneck_initial_search import BASE, pose
    from .native_contacts import body_names, read_contacts, plain
    from .gym_trial_recording import GymTrialRecording
    from .environment import gymapi
    from .trial_settings import source_hashes
    from .build_fixed_lower_asset import MANIFEST, REFERENCE
    candidate = copy.deepcopy(read(CANDIDATE))
    base = read(BASE); state = base['native_initial_state']
    pi = base['human_body_names'].index('Pelvis'); pp, pr = pose(state['human_body_states'][pi])
    if args.case != 'current_control':
        rfu, angles = ([.17, .245, .08], [22., 0., 0.]) if args.case == 'reported_reference' else ([.20, .295, .09], [19.5, 0., 10.])
        gp, gq = reconstruct(pp, pr.as_quat(), rfu, *angles)
        candidate.update(position_W_m=gp.tolist(), quaternion_xyzw=gq.tolist())
    paths = list((ROOT/'stability_adapter_2').glob('*.py'))+[CANDIDATE, BASE,
        MANIFEST, REFERENCE/'report.json', REFERENCE/'states.json',
        ROOT/'stability_adapter_2/TEAM_POSE_ENVELOPE_VALIDATION_PLAN.md',
        ROOT/'stability_adapter_2/run_team_pose_envelope_validation.sh',
        RESULTS/'team_pose_envelope_visualization_v1/inputs/guitar_pose_judgments_20261010.csv',
        ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml']
    hashes = source_hashes(); hashes.update({str(p.resolve()): sha(p) for p in paths})
    save(out/'attempt.json', {'case': args.case, 'input_sha256': hashes, 'candidate': candidate,
        'assumption': 'reconstructed using current human angles and body-center pivot; not original team replay',
        'requested_physics_steps_if_source_clear': 1200, 'strap_enabled': False, 'policy_enabled': False})
    env = recorder = None; trace = []; contact_counts = {}; failure = None; videos = {}; checks = {}
    source_rows = []; contacts_file = None
    try:
        env = UnderneckEnvironment(candidate); env.configure_hold()
        initial = native_state(env); props = env.gym.get_actor_dof_properties(env.env, env.human).copy()
        gp0, gr0 = pose(initial['guitar_body_states'][0])
        checks = {'native_position_matches': bool(np.linalg.norm(gp0-candidate['position_W_m']) < 1e-6),
            'native_rotation_matches': bool((gr0*R.from_quat(candidate['quaternion_xyzw']).inv()).magnitude() < 1e-5),
            'initial_q_matches': bool(np.max(abs(env.initial_q-candidate['joint_angles_rad'])) < 2e-7),
            'initial_joint_limits': bool(np.all(env.initial_q >= env.lower) and np.all(env.initial_q <= env.upper)),
            'free_guitar': not env.guitar_root_fixed and not env.guitar_gravity_disabled,
            'root_lower_fixed': True, 'finite_state': True}
        basis = pr.apply([[-1,0,0], [0,-1,0], [0,0,1]])
        save(out/'initial_values.json', {'case': args.case, 'joint_names': env.names, 'body_names': env.human_bodies,
            'actual_initial_state': initial, 'target_rad': env.target.tolist(), 'PD': plain(props),
            'physics': env.physics_parameters, 'self_collision': env.self_collision_policy,
            'strap_enabled': False, 'arm_hold': 'existing bounded PI on 24 arm DOFs',
            'body_center_rfu_m': ((gp0+gr0.apply(BODY_CENTER_G)-pp) @ basis.T).tolist(),
            'neck_elevation_deg': float(np.degrees(np.arcsin(np.clip(gr0.apply([0,1,0])[2],-1,1)))),
            'front_normal_W': gr0.apply([0,0,1]).tolist(),
            'guitar_requested_p': candidate['position_W_m'], 'guitar_requested_q_xyzw': candidate['quaternion_xyzw']})
        source_rows = source_intersections(env)
        save(out/'initial_source_intersections.json', {'intersections': source_rows, 'epsilon_m': 1e-7,
            'scope': 'source convex common internal ball; includes chair; not cooked penetration depth'})
        recorder = GymTrialRecording(env, out/'images'); recorder.capture()
        env.gym.write_camera_image_to_file(env.sim, env.env, env.cameras['hands_collision'], gymapi.IMAGE_COLOR, str(out/'initial_collision.png'))
        fixed = [i for i,n in enumerate(env.human_bodies) if n=='Pelvis' or any(k in n for k in ('Hip','Knee','Ankle','Toe'))]
        def sample(s):
            p,r = pose(s['guitar_body_states'][0])
            trace.append({'step': env.steps, 'time_s': env.steps/240, 'position_W_m': p.tolist(),
                'quaternion_xyzw': r.as_quat().tolist(), 'position_change_m': float(np.linalg.norm(p-gp0)),
                'rotation_change_deg': float(np.degrees((r*gr0.inv()).magnitude())), 'native_state': s})
        sample(initial)
        if not all(checks.values()): raise AssertionError(checks)
        if not source_rows:
            names = body_names(env.gym, env.env); contacts_file = (out/'contacts.jsonl').open('w')
            for step in range(1200):
                env.step_physics(); s = native_state(env)
                checks['root_lower_fixed'] &= all(s['human_body_states'][i] == initial['human_body_states'][i] for i in fixed)
                values = [d['pos'] for d in s['human_dof_states']]+[d['vel'] for d in s['human_dof_states']]
                for row in s['guitar_body_states']:
                    values.extend(row['pose']['p'].values()); values.extend(row['pose']['r'].values())
                    values.extend(row['vel']['linear'].values()); values.extend(row['vel']['angular'].values())
                checks['finite_state'] &= bool(np.isfinite(values).all())
                if not checks['root_lower_fixed'] or not checks['finite_state'] or max(abs(d['vel']) for d in s['human_dof_states']) > 50:
                    raise RuntimeError('unsafe or nonfinite native state')
                contacts = [c for c in read_contacts(env.gym, env.env, names) if any(c[k].startswith('guitar/') for k in ('body0_name','body1_name'))]
                contacts_file.write(json.dumps({'step': env.steps, 'contacts': contacts})+'\n'); contacts_file.flush()
                for pair in {tuple(sorted((c['body0_name'], c['body1_name']))) for c in contacts}:
                    key = ' | '.join(pair); contact_counts[key] = contact_counts.get(key, 0)+1
                if env.steps % 8 == 0: sample(s); recorder.capture()
                if env.steps % 240 == 0: print(args.case, 'seconds', env.steps/240, flush=True)
        checks['PD_unchanged'] = bool(np.array_equal(props, env.gym.get_actor_dof_properties(env.env, env.human)))
        checks['no_forbidden_write_or_force'] = not env.forbidden_calls
        checks['queries_and_renders_readonly'] = all(f['render_preserves_states'] for f in recorder.frames)
    except BaseException as exc:
        failure = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        if contacts_file is not None: contacts_file.close()
        if env is not None: env.close()
        if recorder is not None and len(recorder.frames)>1:
            try: videos = recorder.encode()
            except Exception as exc: failure = {'type': type(exc).__name__, 'message': str(exc)}
        checks['inputs_unchanged'] = all(sha(p)==h for p,h in hashes.items())
        save(out/'trace.json', trace)
        save(out/'controls.json', getattr(env,'controls',[]))
        save(out/'report.json', {'case': args.case, 'failure': failure, 'checks': checks, 'videos': videos,
            'native_initializations': int(env is not None), 'physics_steps': getattr(env,'steps',0),
            'source_intersection_count': len(source_rows), 'dynamic_status': 'rejected_initial_source_overlap' if source_rows else 'completed_5s' if failure is None and getattr(env,'steps',0)==1200 else 'partial',
            'max_position_change_m': max((r['position_change_m'] for r in trace),default=None),
            'max_rotation_change_deg': max((r['rotation_change_deg'] for r in trace),default=None),
            'guitar_contact_step_counts': contact_counts, 'new_learning_updates': 0,
            'scope': 'current humanoid transfer diagnostic, no original-team/full-range/naturalness certification'})
    if failure or not all(checks.values()): raise RuntimeError(failure or checks)
    print(json.dumps({'case': args.case, 'steps': env.steps, 'initial_source_intersections': len(source_rows)}), flush=True)


if __name__ == '__main__': main()
