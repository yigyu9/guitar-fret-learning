"""Read native POSITION targets and compare a four-step, single-axis goal pulse."""
from .underneck_pose_trial_v5 import UnderneckEnvironment, initial_audit, read, save
from .environment import np, gymapi
from .run_joint_hold import native_state
from .native_contacts import plain, body_names, read_contacts
from .gym_trial_recording import GymTrialRecording
from isaacgym import gymtorch
from pathlib import Path
import argparse
import traceback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--axis', choices=('off', 'x', 'y', 'z'), required=True)
    args = parser.parse_args()
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    env = recorder = None; states = []; commands = []; checks = {}; videos = {}; failure = None
    try:
        candidate = read(args.candidate); env = UnderneckEnvironment(candidate)
        audit = initial_audit(env, candidate); save(out/'initial_audit.json', audit)
        if not all(audit['checks'].values()) or not audit['source_clear']:
            raise ValueError('initial audit failed')
        initial = native_state(env)
        props = env.gym.get_actor_dof_properties(env.env, env.human).copy()
        assert np.all(props['driveMode'] == gymapi.DOF_MODE_POS)
        base = env.target.copy(); pulse = base.copy()
        if args.axis != 'off': pulse[env.names.index('R_Shoulder_'+args.axis)] += np.float32(.02)
        assert np.all((pulse >= env.lower) & (pulse <= env.upper))
        before_sensor = native_state(env)
        if not env.gym.enable_actor_dof_force_sensors(env.env, env.human):
            raise RuntimeError('DOF force sensor enable failed')
        assert native_state(env) == before_sensor
        names = body_names(env.gym, env.env)
        checks.update(native_target_readback_exact=True, setters_preserve_state=True,
                      baseline_PD_preserved=True, root_lower_fixed=True, render_readonly=True)
        save(out/'initial_values.json', {'candidate':str(args.candidate.resolve()),
            'native_initial_state':initial, 'joint_names':env.names, 'PD_properties':plain(props),
            'base_targets_rad':base.tolist(), 'pulse_targets_rad':pulse.tolist(),
            'axis':args.axis, 'pulse_rad':0 if args.axis=='off' else .02,
            'pulse_physics_steps':4, 'strap_force_enabled':False})
        before = native_state(env)
        mass_tensor = gymtorch.wrap_tensor(env.gym.acquire_mass_matrix_tensor(env.sim, 'human'))
        env.gym.refresh_mass_matrix_tensors(env.sim)
        mass = mass_tensor.numpy().copy()
        assert mass.shape == (1,81,81) and np.isfinite(mass).all()
        checks['mass_readonly'] = native_state(env) == before
        save(out/'mass_matrix_initial.json', {'matrix':mass.tolist(), 'scope':'read-only diagnostic; not control'})
        recorder = GymTrialRecording(env, out/'images'); recorder.capture()
        def native_vector(getter):
            value = np.asarray(getter(env.env, env.human)).copy()
            if value.shape != (81,) or not np.isfinite(value).all():
                raise ValueError('invalid native DOF vector: '+getter.__name__)
            return value
        def sample():
            states.append({'physics_step':env.steps, 'native_state':native_state(env),
                'native_targets_rad':native_vector(env.gym.get_actor_dof_position_targets).tolist(),
                'contacts':read_contacts(env.gym, env.env, names),
                'total_native_dof_force_Nm':native_vector(env.gym.get_actor_dof_forces).tolist() if env.steps else None})
        def submit(target):
            before = native_state(env); env.target = target.copy(); env._submit_targets()
            measured = native_vector(env.gym.get_actor_dof_position_targets)
            checks['setters_preserve_state'] &= native_state(env) == before
            checks['native_target_readback_exact'] &= bool(np.array_equal(measured, target))
            commands.append({'before_physics_step':env.steps, 'requested_targets_rad':target.tolist(),
                             'native_targets_rad':measured.tolist()})
            if not all(checks.values()): raise ValueError('goal submission audit failed')
        sample(); submit(pulse)
        for step in range(1200):
            env.step_physics(); current = native_state(env)
            values = [v for row in current['human_dof_states'] for v in (row['pos'], row['vel'])]
            for row in current['human_body_states']+current['guitar_body_states']:
                for block in (row['pose']['p'], row['pose']['r'], row['vel']['linear'], row['vel']['angular']):
                    values.extend(block.values())
            if not np.isfinite(values).all() or max(abs(r['vel']) for r in current['human_dof_states'])>50:
                raise ValueError('unsafe native state')
            if env.steps <= 4 or env.steps%8 == 0: sample()
            if env.steps == 4: submit(base)
            if env.steps%8 == 0:
                recorder.capture()
                checks['root_lower_fixed'] &= all(current['human_body_states'][i]==initial['human_body_states'][i]
                    for i,n in enumerate(env.human_bodies) if i==0 or any(k in n for k in ('Hip','Knee','Ankle','Toe')))
            if env.steps%240 == 0: print('POSITION probe seconds',env.steps/240,'axis',args.axis,flush=True)
        checks['baseline_PD_preserved'] = bool(np.array_equal(props, env.gym.get_actor_dof_properties(env.env, env.human)))
        checks['no_forbidden_calls'] = not env.forbidden_calls
        checks['render_readonly'] = all(f['render_preserves_states'] for f in recorder.frames)
    except BaseException as exc:
        failure = {'type':type(exc).__name__, 'message':str(exc), 'traceback':traceback.format_exc()}
        print(failure['traceback'], flush=True)
    finally:
        save(out/'states.json',states); save(out/'commands.json',commands)
        for operation in ('close', 'encode'):
            try:
                if operation=='close' and env: env.close()
                if operation=='encode' and recorder and len(recorder.frames)>1: videos = recorder.encode()
            except BaseException as exc:
                error = {'operation':operation, 'type':type(exc).__name__, 'message':str(exc),
                         'traceback':traceback.format_exc()}
                if failure is None: failure = error.copy()
                failure.setdefault('cleanup_failures', []).append(error)
                print(error['traceback'], flush=True)
        save(out/'report.json', {'completed_5s':bool(env and env.steps==1200 and failure is None and all(checks.values())),
            'physics_steps':env.steps if env else 0,'checks':checks,'failure':failure,
            'frame_count':len(recorder.frames) if recorder else 0,'videos':videos,
            'axis':args.axis,'scope':'native POSITION shoulder pulse; no actor, music success or learning'})
    if failure or not all(checks.values()): raise RuntimeError(failure or checks)


if __name__ == '__main__': main()
