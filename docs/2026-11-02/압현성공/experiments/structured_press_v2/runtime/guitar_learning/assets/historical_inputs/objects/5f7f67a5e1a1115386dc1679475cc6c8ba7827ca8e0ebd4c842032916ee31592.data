"""Record a fresh 5-second native scene using the physics foundation contract."""
import argparse
import hashlib
import json
from pathlib import Path
import signal


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--mode', choices=('neutral', 'small_motion'), required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    # Isaac must be imported before any dependency can import torch.
    from .learning_scene_v1 import PhysicsEnvironment, np
    from .environment import ROOT
    from .gym_trial_recording import GymTrialRecording
    from .run_joint_hold import native_state
    from .native_contacts import read_contacts, body_names
    from .build_fixed_lower_asset import LOWER_BODIES
    from .environment_contract_v1 import EnvironmentContract, MARKERS
    contract = EnvironmentContract()
    paths = set(contract.inputs)
    paths.update(str(p) for p in (ROOT/'stability_adapter_2').rglob('*')
                 if p.is_file() and p.suffix in ('.py', '.json', '.xml', '.md'))
    paths.update(str(p) for p in (ROOT/'tab2body/assets').rglob('*') if p.is_file())
    paths.add(str(ROOT/'tab2body/_gen/mjcf_gains.json'))
    fixed_manifest = json.loads((ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.json').read_text())
    paths.update(fixed_manifest['input_sha256'])
    hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(paths)}
    save(args.out/'attempt.json', {'mode': args.mode, 'input_sha256': hashes,
        'scope': 'CPU PhysX native cameras; no music/policy/reward/training',
        'requested_physics_steps': 1200})
    environment = PhysicsEnvironment()
    recorder, scene, failure, videos = None, None, None, {}
    rows, commands = [], []
    previous_term = signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt('SIGTERM')))
    try:
        observation = environment.reset()
        scene = environment.scene
        state0 = native_state(scene)
        reference = contract.reference['native_initial_state']
        # Baseline uses the same candidate, gains, fixed lower asset and creation pose.
        if state0 != reference: raise AssertionError('initial native state differs from saved reference')
        pd = scene.pd_properties
        save(args.out/'initial_values.json', {'candidate': scene.contract.candidate,
            'native_initial_state': state0, 'initial_state_exact_reference': True,
            'joint_names': scene.names, 'q_ref_rad': scene.contract.q_ref.tolist(),
            'PD_properties': {k: pd[k].tolist() for k in pd.dtype.names},
            'effective_lower_rad': scene.contract.effective_lower.tolist(),
            'effective_upper_rad': scene.contract.effective_upper.tolist(),
            'target_rates_rad_s': scene.contract.rates.tolist(), 'z_chest_frozen_m': float(scene.z_chest),
            'marker_order': MARKERS, 'observation_manifest': scene.observation_manifest,
            'observation_dimension': observation.size, 'self_collision_policy': scene.self_collision_policy,
            'collision_filters': scene.collision_filters, 'strap_enabled': False,
            'initial_state_write_calls': scene.initial_state_write_calls})
        recorder = GymTrialRecording(scene, args.out/'media')
        names = body_names(scene.gym, scene.env)
        fixed = [scene.human_bodies.index(n) for n in ('Pelvis',)+LOWER_BODIES]
        with (args.out/'states.jsonl').open('w') as states, (args.out/'observations.jsonl').open('w') as observations:
            def observe(obs):
                state = native_state(scene)
                if any(state['human_body_states'][i] != state0['human_body_states'][i] for i in fixed):
                    raise AssertionError('fixed root/lower state changed')
                contacts = read_contacts(scene.gym, scene.env, names)
                if native_state(scene) != state: raise AssertionError('contact query changed state')
                states.write(json.dumps(state, allow_nan=False)+'\n')
                observations.write(json.dumps({'physics_step': scene.steps, 'observation': obs.tolist()}, allow_nan=False)+'\n')
                guitar = scene.bodies(scene.guitar)[0]
                from .environment import vector, quaternion
                rows.append({'physics_step': scene.steps, 'clock': scene.contract.clock(scene.steps),
                    'guitar_position_W_m': vector(guitar['pose']['p']).tolist(),
                    'guitar_quaternion_xyzw': quaternion(guitar['pose']['r']).tolist(),
                    'q_rad': [s['pos'] for s in state['human_dof_states']],
                    'contacts': contacts, 'observation_finite': bool(np.isfinite(obs).all())})
            observe(observation)
            recorder.capture()
            for tick in range(300):
                desired = scene.contract.q_ref.copy()
                if args.mode == 'small_motion' and tick >= 120:
                    wave = np.sin(2*np.pi*(tick/60-2)/3)
                    for name, amplitude in [('Torso_x', .01), ('Head_y', .02), ('R_Shoulder_x', .02), ('LH:index2', .03)]:
                        desired[scene.names.index(name)] += amplitude*wave
                action = (desired-scene.contract.mid)/scene.contract.half
                observation, info = environment.step(action)
                commands.append(dict(info, action_squashed=action.tolist()))
                observe(observation)
                if scene.steps % recorder.interval == 0: recorder.capture()
                if scene.steps % 240 == 0: print('recorded seconds', scene.steps/240, flush=True)
            if scene.forbidden_calls: raise AssertionError(scene.forbidden_calls)
            if not np.array_equal(pd, scene.gym.get_actor_dof_properties(scene.env, scene.human)):
                raise AssertionError('PD properties changed during steps')
    except BaseException as error:
        failure = {'type': type(error).__name__, 'message': str(error)}
    finally:
        signal.signal(signal.SIGTERM, previous_term)
        environment.close()
        if recorder is not None:
            try: videos = recorder.encode()
            except Exception as error:
                if failure is None: failure = {'type': type(error).__name__, 'message': str(error)}
                else: failure['video_error'] = str(error)
        unchanged = all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
        save(args.out/'trace.json', rows)
        save(args.out/'commands.json', commands)
        completed = failure is None and unchanged and scene is not None and scene.steps == 1200
        save(args.out/'report.json', {'completed': completed, 'failure': failure, 'inputs_unchanged': unchanged,
            'physics_steps': getattr(scene, 'steps', 0), 'control_steps': len(commands),
            'simulation_seconds': getattr(scene, 'steps', 0)/240, 'frame_count': len(recorder.frames) if recorder else 0,
            'videos': videos, 'forbidden_calls': getattr(scene, 'forbidden_calls', []),
            'training_ready': False, 'stability_success': False,
            'scope': 'physical initialization/548D observation/81D target smoke test; no music/reward/policy'})
    if not completed: raise RuntimeError(failure or 'input changed')
    print(json.dumps({'completed': True, 'mode': args.mode, 'physics_steps': 1200}), flush=True)


if __name__ == '__main__': main()
