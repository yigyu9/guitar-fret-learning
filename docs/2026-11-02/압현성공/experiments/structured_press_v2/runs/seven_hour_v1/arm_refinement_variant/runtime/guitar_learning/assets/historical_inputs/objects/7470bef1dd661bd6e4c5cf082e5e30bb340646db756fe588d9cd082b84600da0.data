"""Unqualified single-skill Strike transfer diagnostic, no learning or physical resets."""
from .underneck_pose_trial_v5 import UnderneckEnvironment, initial_audit, read, save, sha, pose
from .environment import ROOT, np
from .run_joint_hold import native_state
from .strike_native_view import create_view, refresh_native
from .bounded_arm_hold import BoundedArmHold
from .gym_trial_recording import GymTrialRecording
from scipy.spatial.transform import Rotation
from pathlib import Path
import argparse
import sys
import traceback
import torch
from tab2body.learning.strike_v2_model import StrikeV2ActorCritic

CHECKPOINT = ROOT/'strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt'
GOAL = ROOT/'data/song_bundles/02_Jazz1-200-B_solo/training/strike_plan.json'
GRIP = ROOT/'strike/02_physical_control/pick-grip-reference.json'
CANDIDATE = ROOT/'docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/refine/candidate_w10000.json'


def tensor_plain(x):
    return x.detach().cpu().tolist()


def counterfactual(view, model):
    bodies, roots = view.body_state.clone(), view.root_state.clone()
    observation = view.strict_observation()
    with torch.no_grad(): baseline = model.act(observation, deterministic=True)[0]
    start, end = view.string_segments_g()
    gp, gq = tensor_plain(roots[1, :3]), tensor_plain(roots[1, 3:7])
    base_world = np.array(gp) + Rotation.from_quat(gq).apply(tensor_plain(start[0]))
    cases = []
    for name, all_scene, shift, rotation in (
            ('guitar_translation_10mm', False, np.array([.01, 0, 0]), Rotation.identity()),
            ('guitar_rotation_z_5deg', False, np.zeros(3), Rotation.from_euler('z', 5, degrees=True)),
            ('whole_scene_translation', True, np.array([.2, -.1, .03]), Rotation.identity()),
            ('whole_scene_rotation_z_5deg', True, np.zeros(3), Rotation.from_euler('z', 5, degrees=True))):
        view.body_state.copy_(bodies); view.root_state.copy_(roots)
        ids = range(view._bpe) if all_scene else range(view.n_hbody, view._bpe)
        root_ids = range(2) if all_scene else [1]
        origin = np.zeros(3) if all_scene else np.array(gp)
        def transform(t, indices):
            for i in indices:
                t[i, :3] = torch.tensor(origin + rotation.apply(tensor_plain(t[i, :3])-origin) + shift)
                t[i, 3:7] = torch.tensor((rotation*Rotation.from_quat(tensor_plain(t[i, 3:7]))).as_quat())
                t[i, 7:10] = torch.tensor(rotation.apply(tensor_plain(t[i, 7:10])))
                t[i, 10:13] = torch.tensor(rotation.apply(tensor_plain(t[i, 10:13])))
        transform(view.body_state, ids); transform(view.root_state, root_ids)
        obs = view.strict_observation()
        with torch.no_grad(): action = model.act(obs, deterministic=True)[0]
        seg, _ = view.string_segments_g()
        p, q = tensor_plain(view.root_state[1, :3]), tensor_plain(view.root_state[1, 3:7])
        world = np.array(p) + Rotation.from_quat(q).apply(tensor_plain(seg[0]))
        expected = origin+rotation.apply(base_world-origin)+shift
        cases.append({'case': name, 'obs_max_abs_delta': float((obs-observation).abs().max()),
                      'action_max_abs_delta': float((action-baseline).abs().max()),
                      'string_world_transform_error_m': float(np.max(abs(world-expected))),
                      'observation': tensor_plain(obs), 'actor_action': tensor_plain(action)})
    view.body_state.copy_(bodies); view.root_state.copy_(roots)
    assert torch.equal(view.strict_observation(), observation)
    assert all(c['string_world_transform_error_m'] < 2e-6 for c in cases)
    assert all(c['obs_max_abs_delta'] < 3e-5 for c in cases if 'whole_scene' in c['case'])
    assert cases[0]['obs_max_abs_delta'] > .001 and cases[1]['obs_max_abs_delta'] > .001
    return {'baseline_observation': tensor_plain(observation), 'baseline_action': tensor_plain(baseline),
            'cases': cases, 'scope': 'CPU counterfactual on native t0; not physical rollout', 'passed': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--probe-only', action='store_true')
    args = parser.parse_args(); out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    env = recorder = model = None
    records, trace, videos, checks = [], [], {}, {}
    failure = None; terminated = False; terminal_reasons = {}; hashes = {}
    try:
        checkpoint = torch.load(CHECKPOINT, map_location='cpu', weights_only=True)
        payload = checkpoint['checkpoint_contract']['payload']
        assert sha(GOAL) == payload['inputs']['goal_sha256']
        assert sha(GRIP) == payload['inputs']['grip_reference_sha256']
        env = UnderneckEnvironment(read(CANDIDATE))
        audit = initial_audit(env, read(CANDIDATE)); save(out/'initial_audit.json', audit)
        assert all(audit['checks'].values()) and audit['source_clear']
        view = create_view(env, checkpoint, str(GOAL), str(GRIP))
        assert list(view.controlled_dof_names) == payload['control']['controlled_dof_names']
        assert list(view.observation_manifest) == payload['config']['observation_manifest']
        model = StrikeV2ActorCritic(303, 30, value_dim=1, init_std=payload['model']['policy_init_std'])
        model.load_state_dict(checkpoint['model'], strict=True); model.eval(); model.requires_grad_(False)
        frozen = {k: v.clone() for k, v in model.state_dict().items()}
        files = [Path(m.__file__) for n, m in sys.modules.items() if n.startswith(('stability_adapter_2', 'tab2body')) and getattr(m, '__file__', None)]
        files += [CHECKPOINT, GOAL, GRIP, CANDIDATE, ROOT/'stability_adapter_2/STRIKE_LIVE_GUITAR_PROBE_PLAN.md', ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml']
        hashes = {str(p.resolve()): sha(p) for p in files}
        save(out/'attempt.json', {'input_sha256': hashes, 'checkpoint': str(CHECKPOINT), 'requested_seconds': 0 if args.probe_only else 5,
            'official_G0_qualification': False, 'actuator_difference': 'native implicit position PD at240Hz; source explicit stiffness torque with implicit damping at60Hz/4substeps',
            'contact_force_source': 'get_env_rigid_contact_forces; source303/rewards do not use force buffer',
            'strap_enabled': False, 'learning_updates': 0})
        props = env.gym.get_actor_dof_properties(env.env, env.human).copy()
        initial = native_state(env)
        save(out/'initial_values.json', {'joint_names': env.names, 'actual_angles_rad': env.initial_q.tolist(),
            'initial_targets_rad': env.target.tolist(), 'native_initial_state': initial,
            'native_lower_rad': env.lower.tolist(), 'native_upper_rad': env.upper.tolist(),
            'PD_stiffness': props['stiffness'].tolist(), 'PD_damping': props['damping'].tolist(),
            'training_context': checkpoint['training_context'], 'song_time_s': tensor_plain(view.song_time_s)})
        save(out/'counterfactual.json', counterfactual(view, model))
        arm = np.array([i for i, n in enumerate(env.names) if n.startswith(('L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist', 'R_Thorax', 'R_Shoulder', 'R_Elbow', 'R_Wrist'))])
        left = np.array([i for i, n in enumerate(env.names) if n.startswith(('L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist'))])
        right = view.ctrl_idx.numpy(); other = np.setdiff1d(np.arange(81), np.r_[left, right])
        assert len(left) == 12 and len(right) == 30 and len(other) == 39
        hold = BoundedArmHold(env.initial_q[arm], env.lower[arm], env.upper[arm])
        recorder = GymTrialRecording(env, out/'images'); recorder.capture()
        gp0, gr0 = pose(initial['guitar_body_states'][0])
        def sample():
            s = native_state(env); gp, gr = pose(s['guitar_body_states'][0])
            trace.append({'physics_step': env.steps, 'time_s': env.steps/240, 'position_W_m': gp.tolist(),
                'quaternion_xyzw': gr.as_quat().tolist(), 'position_change_m': float(np.linalg.norm(gp-gp0)),
                'rotation_change_deg': float(np.degrees((gr*gr0.inv()).magnitude()))})
        sample()
        checks.update(commands_preserve_state=True, held_other39=True, target_bounds=True, root_lower_fixed=True)
        def advance(task):
            before = native_state(env)
            actual = np.array([s['pos'] for s in before['human_dof_states']])
            # Right support channels have zero error and are discarded; only left12 PI is used.
            measured = actual[arm].copy()
            measured[[j for j, i in enumerate(arm) if i not in left]] = env.initial_q[arm][[j for j, i in enumerate(arm) if i not in left]]
            arm_goal, _ = hold.update(measured, 1/60)
            previous = env.target.copy()
            desired = tensor_plain(task.pd_target[right])
            env.target = env.initial_q.copy()
            env.target[left] = arm_goal[[j for j, i in enumerate(arm) if i in left]]
            env.target[right] = np.clip(np.clip(desired, previous[right]-.8/60, previous[right]+.8/60), env.lower[right], env.upper[right])
            env._submit_targets()
            task.pd_target.copy_(torch.tensor(env.target.copy()))
            task.prev_action.copy_(task.actions_for_pd_targets(task.pd_target[right][None]))
            checks['commands_preserve_state'] &= native_state(env) == before
            checks['held_other39'] &= bool(np.array_equal(env.target[other], env.initial_q[other]))
            checks['target_bounds'] &= bool(((env.target >= env.lower)&(env.target <= env.upper)).all())
            records[-1].update(final_targets_rad=env.target.tolist(), history=tensor_plain(task.prev_action),
                               max_RH_target_step_rad=float(max(abs(env.target[right]-previous[right]))))
            for _ in range(4):
                env.step_physics()
                if env.steps % 8 == 0:
                    sample(); recorder.capture()
                    s = native_state(env)
                    checks['root_lower_fixed'] &= all(s['human_body_states'][i] == initial['human_body_states'][i] for i, n in enumerate(env.human_bodies) if i == 0 or any(k in n for k in ('Hip','Knee','Ankle','Toe')))
        view.advance_native = advance
        for _ in range(0 if args.probe_only else 300):
            obs = view.strict_observation()
            with torch.no_grad(): action = model.act(obs, deterministic=True)[0]
            if not torch.isfinite(action).all(): raise ValueError('nonfinite actor action')
            records.append({'before_physics_step': env.steps, 'observation': tensor_plain(obs), 'action': tensor_plain(action)})
            _, reward, done, info = view.step(action)
            records[-1].update(info={k: tensor_plain(v) for k, v in info.items() if isinstance(v, torch.Tensor)}, reward=tensor_plain(reward))
            if bool(done.any()):
                terminated = True
                terminal_reasons = {k: tensor_plain(v) for k, v in info.items() if ('termination' in k or k in ('timeout', 'nonfinite', 'velocity_blowup', 'goal_finished')) and isinstance(v, torch.Tensor)}
                break
            if env.steps % 240 == 0: print('native time', env.steps/240, flush=True)
        if recorder.frames[-1]['physics_step'] != env.steps: sample(); recorder.capture()
        checks['weights_and_normalization_frozen'] = all(torch.equal(v, frozen[k]) for k, v in model.state_dict().items())
        checks['no_forbidden_calls'] = not env.forbidden_calls
        checks['PD_unchanged'] = bool(np.array_equal(props, env.gym.get_actor_dof_properties(env.env, env.human)))
        checks['render_readonly'] = all(f['render_preserves_states'] for f in recorder.frames)
    except BaseException as e:
        failure = {'type': type(e).__name__, 'message': str(e), 'traceback': traceback.format_exc()}
        print(failure['traceback'], flush=True)
    finally:
        if env is not None: env.close()
        if recorder is not None and len(recorder.frames)>1: videos = recorder.encode()
        checks['inputs_unchanged'] = all(sha(p)==v for p,v in hashes.items())
        save(out/'controls.json', records); save(out/'trace.json', trace)
        save(out/'report.json', {'failure': failure, 'checks': checks, 'terminated': terminated, 'terminal_reasons': terminal_reasons,
            'physics_steps': env.steps if env else 0, 'control_steps': len(records), 'videos': videos,
            'completed_requested_5s': bool(env and env.steps==1200 and failure is None and all(checks.values())),
            'learning_updates': 0, 'music_success': False, 'input_sha256': hashes})
    if failure or not all(checks.values()): raise RuntimeError(failure or checks)


if __name__ == '__main__': main()
