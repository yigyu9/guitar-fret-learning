"""Actual right6 control or strict checkpoint replay; no mid-episode state writes."""
import copy
from pathlib import Path

from .runtime import admitted, environment_runtime, read, sha, verify_pins, write


def trajectory(time_s, initial, waypoints):
    """Arrive, prepare, cross once near3s, then lift without a return crossing."""
    import math
    if not math.isfinite(time_s) or not 0 <= time_s <= 5.+1e-9:
        raise ValueError('Finite five-second task clock required')
    pre, post, lift = waypoints
    stages = ((.5, 2.6, initial, pre), (2.9, 3.1, pre, post), (3.3, 3.8, post, lift))
    result = initial
    for start, end, before, after in stages:
        if time_s < start:
            break
        u = min(1., (time_s-start)/(end-start))
        smooth = u**3*(10-15*u+6*u*u)
        result = before+smooth*(after-before)
    return result


def actual_contract(pool):
    """Read the native arrival into a detached CPU FK input, never into a scene."""
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    contract = load_gpu_prepared_reset_contract('right')
    snapshot = pool.scene.snapshot()
    q = snapshot['q'][0].detach().cpu().tolist()
    qd = snapshot['qd'][0].detach().cpu().tolist()
    rows = snapshot['body_state'][0].detach().cpu().tolist()
    contract['state']['physics_step'] = int(snapshot['physics_step'][0])
    for i, row in enumerate(contract['state']['human_dof_states']):
        row['pos'], row['vel'] = q[i], qd[i]
    for kind in ('human', 'guitar', 'chair'):
        body_names = ['box'] if kind == 'chair' else contract['initial'][kind+'_body_names']
        for name, row in zip(body_names, contract['state'][kind+'_body_states']):
            index = pool.scene.body_names.index(kind+'/'+name)
            value = rows[index]
            row['pose'] = dict(p=dict(zip('xyz', value[:3])), r=dict(zip('xyzw', value[3:7])))
            row['vel'] = dict(linear=dict(zip('xyz', value[7:10])), angular=dict(zip('xyz', value[10:13])))
    return contract


def load_policy(checkpoint, pool):
    import torch
    from guitar_learning.portability import localize, portable
    from guitar_learning.training.policy import SpecialistPolicy
    from guitar_learning.training.ppo import PPOTrainer, PPOConfig
    checkpoint = Path(checkpoint).resolve()
    lineage = read(checkpoint.parent/'right_strike_lineage.json')
    if (lineage.get('schema') != 'guitar_learning.right_strike_lineage.v1' or
            lineage.get('completed') is not True or
            lineage['checkpoints'].get(str(checkpoint)) != sha(checkpoint) or
            sha(checkpoint.parent/'settings.json') != lineage['settings_sha256'] or
            sha(checkpoint.parent/'report.json') != lineage['report_sha256']):
        raise ValueError('Own completed training/checkpoint lineage required')
    verify_pins(lineage['pins'])
    payload = torch.load(checkpoint, map_location=pool.scene.device, weights_only=False)
    settings = localize(lineage['settings'])
    if (portable(payload.get('metadata', {}).get('settings')) != portable(settings) or
            payload['identity']['architecture']['contract'] != portable(pool.contract) or
            settings['specialist']['role'] != 'right' or 'right_strike' not in settings):
        raise ValueError('Right6 checkpoint task/settings/full physical contract mismatch')
    policy = SpecialistPolicy(pool.observation['state'].shape[-1], size=settings['size'],
                              contract=pool.contract, role='right', frozen_partner=False).to(pool.scene.device)
    trainer = PPOTrainer(policy, PPOConfig(**settings['ppo']))
    trainer.load(checkpoint)  # Preserve the original full identity and optimizer/RNG checks.
    policy.eval()
    return policy


def close_capture(pool, capture, raw, physics, videos, finish_video, numpy, out):
    """Raw-save/encoder errors must never skip destruction of the native scene."""
    errors, codes = [], {}
    for name, process in videos.items():
        try:
            codes[name], messages = finish_video(process)
            errors.extend(messages)
        except BaseException as exc:
            errors.append('encoder '+name+': '+repr(exc))
    arrays = []
    if capture and capture.samples:
        arrays.extend((('poses.npz', capture.samples), ('observations_before_action.npz', raw)))
    if physics:
        arrays.append(('physics_trace.npz', physics))
    for filename, rows in arrays:
        try:
            numpy.savez_compressed(out/filename, **{k: numpy.stack([row[k] for row in rows]) for k in rows[0]})
        except BaseException as exc:
            errors.append('raw save '+filename+': '+repr(exc))
    if pool:
        try:
            pool.close()
        except BaseException as exc:
            errors.append('close: '+repr(exc))
    return codes, errors


def run(manifest_path, out, *, checkpoint=None):
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError('Fresh right strike capture output required')
    with admitted(manifest_path) as (manifest, resource):
        import isaacgym
        from isaacgym import gymapi
        import numpy as np
        import torch
        from .settings import build_settings
        from .geometry import fit_path
        from guitar_learning.tool.demonstration.render_finger_skill import _encoder, _EnvZeroCapture
        from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym, finish_video
        from guitar_learning.tool.validation.press_acquisition import trajectory_actions
        settings = build_settings(manifest['bundle'], updates=1, num_envs=1)
        if checkpoint:
            checkpoint = Path(checkpoint).resolve()
            lineage = read(Path(checkpoint).parent/'right_strike_lineage.json')
            if (Path(lineage['manifest']).resolve() != Path(manifest_path).resolve() or
                    lineage['manifest_sha256'] != sha(manifest_path)):
                raise ValueError('Evaluation requires the original training manifest')
            settings = copy.deepcopy(read(Path(checkpoint).parent/'settings.json'))
            settings['num_envs'] = 1
        pins = dict(manifest['pins']); pins[str(Path(manifest_path).resolve())] = sha(manifest_path)
        if checkpoint:
            pins[str(checkpoint)] = lineage['checkpoints'][str(checkpoint)]
            pins[str(checkpoint.parent/'right_strike_lineage.json')] = sha(checkpoint.parent/'right_strike_lineage.json')
            pins[str(checkpoint.parent/'settings.json')] = lineage['settings_sha256']
            pins[str(checkpoint.parent/'report.json')] = lineage['report_sha256']
            verify_pins(pins)
        out.mkdir(parents=True)
        write(out/'settings.json', settings)
        torch.set_num_threads(1)
        original = gymapi.acquire_gym
        pool = capture = None
        videos = {}; codes = {}; errors = []; failure = None; fit = None
        policy = None; actor_before = None; episode = None; raw = []; physics = []
        try:
            with environment_runtime() as Pool:
                gymapi.acquire_gym = lambda: GraphicsGym(original())
                try:
                    pool = Pool(settings, out/'scene')
                finally:
                    gymapi.acquire_gym = original
            write(out/'training_contract.json', pool.contract)
            original_substep = pool.environment.substep
            def observe_physics(snapshot):
                original_substep(snapshot)
                env = pool.environment
                physics.append(dict(physics_step=snapshot['physics_step'][0].detach().cpu().numpy().copy(),
                    pick_G_m=env.pick[0].detach().cpu().numpy().copy(),
                    starts_G_m=env.starts[0].detach().cpu().numpy().copy(),
                    ends_G_m=env.ends[0].detach().cpu().numpy().copy(),
                    q_right6=snapshot['q'][0, pool.controller.active[33:]].detach().cpu().numpy().copy(),
                    native_expected_hits=env.strike_quality['native_expected_hits'][0].detach().cpu().numpy().copy(),
                    prepared=env.strike_quality['ready'][0].detach().cpu().numpy().copy(),
                    recovered=env.strike_quality['recovered'][0].detach().cpu().numpy().copy()))
            pool.environment.substep = observe_physics
            if checkpoint:
                policy = load_policy(checkpoint, pool)
                actor_before = {k: v.clone() for k, v in policy.state_dict().items()}
            cameras = {}
            pick_world = pool.scene.snapshot()['body_state'][0, pool.scene.body_names.index('human/RH:pick'), :3].cpu().tolist()
            positions = dict(hand=(tuple(a+b for a, b in zip(pick_world, (.55, .40, .20))), tuple(pick_world)),
                             fullbody=((-.10, 2.7, 1.1), (-.15, -.10, .65)))
            for name, (position, target) in positions.items():
                props = gymapi.CameraProperties()
                props.width, props.height, props.horizontal_fov = 1280, 720, 55.
                camera = pool.scene.gym.create_camera_sensor(pool.scene.envs[0], props)
                if camera < 0:
                    raise RuntimeError('Native right-hand camera unavailable')
                pool.scene.gym.set_camera_location(camera, pool.scene.envs[0],
                                                   gymapi.Vec3(*position), gymapi.Vec3(*target))
                cameras[name] = camera; videos[name] = _encoder(out/(name+'.mp4'))
            capture = _EnvZeroCapture(pool, gymapi, np, cameras, videos)
            ref = pool.controller.reference[pool.controller.active]
            active6 = pool.controller.active[33:]
            initial = waypoints = None
            for tick in range(300):
                if not checkpoint and tick == 30:
                    arrival = actual_contract(pool)
                    fit = fit_path(arrival, pool.environment.starts[0].cpu().numpy(),
                                   pool.environment.ends[0].cpu().numpy())
                    write(out/'actual_arrival.json', arrival)
                    write(out/'geometry_fit.json', fit)
                    if not fit['geometry_candidate']:
                        break
                    initial = pool.scene.snapshot()['q'][0, active6].clone()
                    waypoints = [torch.tensor(q, device=ref.device, dtype=ref.dtype)[active6]
                                 for q in fit['waypoints_q105']]
                before = {k: pool.observation[k].detach().clone() for k in
                          ('state', 'events', 'mask', 'priority_events', 'priority_mask')}
                if policy:
                    with torch.no_grad():
                        action = policy.act(**before, deterministic=True)['action']
                else:
                    desired = ref[None].clone()
                    if waypoints is not None:
                        desired[:, 33:] = trajectory((tick+1)/60., initial, waypoints)
                    action = trajectory_actions(desired, ref, pool.controller.action_low, pool.controller.action_high)
                if bool((action[:, :33] != 0).any()) or bool((action.abs() > 1).any()) or not bool(torch.isfinite(action).all()):
                    raise ValueError('Only bounded finite right6 actions permitted')
                observation, reward, cost, terminated, truncated, episodes = pool.step(action)
                raw.append({k: v[0].cpu().numpy().copy() for k, v in before.items()})
                capture.record(tick, reward, cost, terminated, truncated, episodes)
                if bool(terminated[0] or truncated[0]):
                    break
            episode = capture.episode
            write(out/'episode.json', episode)
            write(out/'metadata.json', dict(joint_names=pool.scene.names, body_names=pool.scene.body_names,
                action_names=pool.contract['action']['names'], frame_times_s=capture.frame_times_s,
                observation_alignment='row i before action i; poses row i after4 actual physics steps',
                physics_trace_hz=240, policy_hz=60, video_fps=30,
                policy_evaluation=bool(checkpoint), diagnostic_only=not bool(checkpoint),
                no_mid_episode_state_injection=True))
            verify_pins(pins)
            if policy and any(not torch.equal(v, actor_before[k]) for k, v in policy.state_dict().items()):
                raise RuntimeError('Evaluation mutated policy')
        except BaseException as exc:
            failure = repr(exc)
            raise
        finally:
            gymapi.acquire_gym = original
            codes, errors = close_capture(pool, capture, raw, physics, videos, finish_video, np, out)
            audit = pool.scene.diagnostics if pool and pool.scene else None
            lifecycle = bool(audit and audit.get('closed') and audit.get('physx_use_gpu') and
                             audit.get('use_gpu_pipeline') and audit.get('environment_count') == 1)
            changed = [name for name, value in pins.items() if not Path(name).is_file() or sha(name) != value]
            complete = failure is None and not errors and not changed and lifecycle and len(codes) == 2 and all(v == 0 for v in codes.values())
            result = dict(schema='guitar_learning.right_strike_capture.v1', completed=complete,
                protocol_completed=bool(episode and episode['reason'] == 'timeline_complete'),
                failure=failure, cleanup_errors=errors,
                native_pixels=bool(capture and capture.frame_times_s), lifecycle_verified=lifecycle,
                encoding_exit_codes=codes, frames=len(capture.frame_times_s) if capture else 0,
                mode='policy' if checkpoint else 'diagnostic', checkpoint=str(checkpoint) if checkpoint else None,
                checkpoint_sha256=pins.get(str(checkpoint)) if checkpoint else None,
                no_mid_episode_state_injection=True, resource_before=resource,
                outcome=outcome(episode, complete, fit, policy is not None),
                episode=episode, pins=pins, source_pins_unchanged=not changed, changed_sources=changed, gpu_scene=audit)
            write(out/'report.json', result)
            if failure is None and not complete:
                raise RuntimeError('Native capture/source lifecycle failed')
        return result


def outcome(episode, complete, fit, policy):
    if not complete:
        return 'inspection_error'
    if fit and not fit['geometry_candidate']:
        return 'geometry_candidate_not_found'
    if not episode:
        return 'incomplete_episode'
    quality = episode.get('right_strike_quality', {})
    if not quality.get('full_safe'):
        return 'physical_or_control_failure'
    if quality.get('success'):
        return 'policy_success' if policy else 'diagnostic_success'
    if not quality.get('prepared'):
        return 'preparation_failed'
    if quality.get('native_expected_hit_count') != 1:
        return 'single_strike_failed'
    if not quality.get('prepared_before_hit'):
        return 'unprepared_strike'
    if not quality.get('recovered'):
        return 'recovery_failed'
    return 'wrong_or_repeated_strike'
