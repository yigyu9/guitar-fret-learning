"""Strict short-finger v2 native env0 video; deterministic policy or sealed reference."""
import argparse
import copy
from pathlib import Path
import sys
import time


def render(checkpoint, out, *, num_envs=None, control='policy', reference=None):
    # Isaac's extension must load before NumPy/Torch.
    import isaacgym
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.gpu_pool import FIELDS
    from guitar_learning.training.finger_skill_runner import _pins, _validate_pins
    from guitar_learning.training.recording import digest, write, project_source_paths
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPool, ShortPolicy
    from guitar_learning.tool.experiments.short_finger_learning.spec import SCHEMA, read_teacher, read_reference
    from guitar_learning.tool.experiments.short_finger_learning.runner import compact_episode
    from guitar_learning.tool.validation.press_acquisition import trajectory_actions
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym, finish_video
    from guitar_learning.tool.demonstration import render_finger_skill as native_render

    checkpoint, out = Path(checkpoint), Path(out).resolve()
    if not checkpoint.is_absolute() or not checkpoint.is_file():
        raise ValueError('Existing absolute short-finger checkpoint path required')
    checkpoint = checkpoint.resolve()
    if control not in ('policy', 'reference') or (control == 'reference') != bool(reference):
        raise ValueError('policy or reference; sealed --reference required exactly for reference control')
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    metadata = payload.get('metadata', {}) if isinstance(payload, dict) else {}
    if metadata.get('schema') != SCHEMA or not metadata.get('input_pins'):
        raise ValueError('Own sealed short_finger_learning.v2 checkpoint required')
    _validate_pins(metadata)
    settings = copy.deepcopy(metadata['settings'])
    spec = settings['song']['short_learning']
    if spec.get('schema') != SCHEMA or read_teacher(spec['teacher']['input_path']) != spec['teacher']:
        raise ValueError('Checkpoint short-task/teacher/evidence identity mismatch')
    saved_num_envs = settings['num_envs']
    if num_envs is not None:
        if type(num_envs) is not int or not 1 <= num_envs <= 1024:
            raise ValueError('num-envs must be1..1024')
        settings['num_envs'] = num_envs
    reference_value = read_reference(reference, spec) if reference else None
    out.mkdir(parents=True, exist_ok=False)
    write(out/'settings.json', settings)
    extra = [checkpoint, Path(__file__).resolve(), *map(Path, metadata['input_pins']),
             Path(spec['teacher']['input_path']), *map(Path, spec['teacher']['source_evidence'])]
    if reference:
        extra += [Path(reference).resolve(), *map(Path, reference_value['source_evidence'])]
    pins = _pins(settings, out, extra)
    write(out/'inputs_before.json', pins)
    write(out/'invocation.json', dict(argv=sys.argv, control=control, reference=str(Path(reference).resolve()) if reference else None,
        saved_num_envs=saved_num_envs, actual_num_envs=settings['num_envs'],
        batch_override='only num_envs changes; strict architecture/control/config identity still required'))
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    original_gym = gymapi.acquire_gym
    original_cameras = copy.deepcopy(native_render.CAMERAS)
    camera_settings = copy.deepcopy(original_cameras)
    camera_settings['fullbody'] = ((-.10, 3.4, 1.1), (-.15, -.10, .65))
    pool, capture, policy, model_before = None, None, None, None
    videos, codes, cleanup_errors = {}, {}, []
    failure, unchanged, compact = None, False, None
    started = time.monotonic()
    try:
        gymapi.acquire_gym = lambda: GraphicsGym(original_gym())
        try:
            pool = ShortPool(settings, out/'scene')
        finally:
            gymapi.acquire_gym = original_gym
        write(out/'training_contract.json', pool.contract)
        policy = ShortPolicy(contract=pool.contract, size=settings['size']).to(settings['device'])
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
        if pool.environment.approach_gamma != trainer.config.gamma:
            raise ValueError('Reward shaping/PPO gamma mismatch')
        trainer.load(checkpoint)  # Exact architecture/config/model/control; no relaxed loader.
        model_before = {key: value.detach().clone() for key, value in policy.state_dict().items()}
        policy.eval()
        pool.environment.set_evaluation(True, full_song=False)
        observation = pool.reset()[0]
        reference_goal = None
        if reference_value:
            reference_goal = pool.teacher_reference.clone()
            for name, value in reference_value['selected_targets_rad'].items():
                reference_goal[ACTIVE_NAMES.index(name)] = value
            if bool(((reference_goal < pool.controller.action_low) | (reference_goal > pool.controller.action_high)).any()):
                raise ValueError('Sealed reference exceeds actual native action bounds')
        native_render.CAMERAS = camera_settings
        cameras = native_render._create_cameras(pool.scene, gymapi)
        for name in cameras:
            videos[name] = native_render._encoder(out/(name+'.mp4'))
        capture = native_render._EnvZeroCapture(pool, gymapi, np, cameras, videos)
        with torch.no_grad():
            for tick in range(spec['view']['duration_ticks']):
                checkpoint_action = policy.act(*(observation[key] for key in FIELDS), deterministic=True)['action']
                action = checkpoint_action
                if reference_value:
                    fraction = ((pool.environment._local_time()+1/60)/reference_value['ramp_s']).clamp(0, 1).to(action)
                    desired = pool.teacher_reference+fraction[:, None]*(reference_goal-pool.teacher_reference)
                    action = trajectory_actions(desired, pool.controller.target[:, pool.controller.active],
                        pool.teacher_reference, pool.controller.action_low, pool.controller.action_high,
                        pool.incremental_mask, max_speed=4.)
                observation, reward, cost, terminated, truncated, episodes = pool.step(action)
                capture.record(tick, reward, cost, terminated, truncated, episodes)
                env, scene = pool.environment, pool.scene
                selected = env.selected_index
                capture.samples[-1].update(
                    checkpoint_policy_action=checkpoint_action[0].cpu().numpy().copy(),
                    requested_action=pool.last_policy_action[0].cpu().numpy().copy(),
                    executed_action=pool.last_executed_action[0].cpu().numpy().copy(),
                    source_time_s=np.asarray(float(env._score_time()[0])),
                    candidate=np.asarray(bool(env.candidate[0, selected])), wrong=np.asarray(bool(env.wrong[0, selected])),
                    surface_distance_m=np.asarray(float(env.surface_distance[0, selected])),
                    surface_height_m=np.asarray(float(env.surface_height[0, selected])),
                    reward=np.asarray(float(reward[0])), cost=np.asarray(float(cost[0])),
                    wrist_delta=env.guide['delta'][0].cpu().numpy().copy(),
                    wrist_feedback_active=np.asarray(bool(pool.last_wrist_feedback['active'][0])),
                    wrist_pose_error_world=pool.last_wrist_feedback['pose_error_world'][0].cpu().numpy().copy(),
                    wrist_requested_delta_rad=pool.last_wrist_feedback['requested_delta_rad'][0].cpu().numpy().copy(),
                    wrist_requested_arm_rad=pool.last_wrist_feedback['requested_arm_rad'][0].cpu().numpy().copy(),
                    wrist_goal_G_m=pool.last_wrist_feedback['position_goal_G_m'][0].cpu().numpy().copy(),
                    wrist_goal_G_xyzw=pool.last_wrist_feedback['quaternion_goal_G_xyzw'][0].cpu().numpy().copy(),
                    **{'episode_reward_'+key:np.asarray(float(value[0])) for key, value in env.episode_reward_terms.items()})
                if capture.episode is not None:
                    break
                ids = (terminated | truncated).nonzero().flatten()
                if ids.numel():
                    observation = pool.reset(ids)[0]
        if capture.episode is None:
            raise RuntimeError('env0 first episode did not finish within the original short-task duration')
        unchanged = all(torch.equal(value, model_before[key]) for key, value in policy.state_dict().items())
        if not unchanged:
            raise AssertionError('Rendering changed checkpoint model weights/buffers')
        compact = compact_episode(capture.episode, spec)
        write(out/'episode_env0000.json', capture.episode)
        write(out/'episode_summary.json', compact)
        write(out/'capture_metadata.json', dict(schema='guitar_learning.short_finger_video.v2',
            checkpoint=str(checkpoint), checkpoint_sha256=pins[str(checkpoint)], control=control,
            policy_performance=control == 'policy', reference=reference_value,
            scope=spec['result_scope'], source_target_id=spec['teacher']['source_target_id'],
            environment=0, selection='predeclared env0 first episode; not selected by performance',
            achieved=compact['achieved'], selected_target_count=1, clean_fraction=compact['clean_fraction'],
            native_pixels=True, width=1280, height=720, video_fps=30, capture_hz=60, source_physics_hz=240,
            frames=len(capture.frame_times_s), frame_times_s=capture.frame_times_s,
            video_duration_s=len(capture.frame_times_s)/30., captured_control_duration_s=len(capture.samples)/60.,
            first_physics_step=int(capture.samples[0]['physics_step']), last_physics_step=int(capture.samples[-1]['physics_step']),
            joint_names=pool.scene.names, body_names=pool.scene.body_names,
            learned_action_indices=spec['learned_action_indices'], wrist_control=spec['wrist_control'],
            camera_settings=camera_settings, camera_override='graphics only; fullbody y3.4 for head/feet margin',
            frame_mapping='frame n maps to control endpoint2*(n+1); no t0 frame; odd final endpoint has no frame',
            control_contract='one ShortPool step per60Hz; four actual240Hz substeps; fixed-wrist arm12 and other-finger B from saved contract',
            action_scope='checkpoint_policy_action is deterministic mean output; requested_action is policy or sealed reference; executed_action includes saved arm/B teacher',
            reward_trace_scope='reward/cost are current60Hz increments; episode_reward_* are cumulative episode component sums and must not be summed across endpoints',
            wrist_pose_error_scope='pre-control actual wrist versus next target; world xyz meters then0.1*world rotation-vector radians',
            training_updates=0, checkpoint_training_updates=trainer.updates, no_reset_frames=True))
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        gymapi.acquire_gym = original_gym
        native_render.CAMERAS = original_cameras
        for name, process in videos.items():
            code, errors = finish_video(process)
            codes[name] = code
            cleanup_errors.extend(dict(component=name, message=error) for error in errors)
        trace_finite, clock_contiguous = False, False
        if capture and capture.samples:
            try:
                arrays = {key:np.stack([row[key] for row in capture.samples]) for key in capture.samples[0]}
                trace_finite = all(bool(np.isfinite(value).all()) for value in arrays.values())
                clock_contiguous = bool(np.array_equal(arrays['physics_step'], 4*np.arange(1, len(capture.samples)+1)))
                filename = 'poses_env0000.npz' if failure is None else 'partial_poses_env0000.npz'
                np.savez_compressed(out/filename, **arrays)
            except BaseException as error:
                cleanup_errors.append(dict(component='raw_capture', message=str(error)))
        if model_before is not None:
            unchanged = all(torch.equal(value, model_before[key]) for key, value in policy.state_dict().items())
        if pool:
            try:
                pool.close()
            except BaseException as error:
                cleanup_errors.append(dict(component='scene_close', message=str(error)))
        changed = [path for path, value in pins.items() if not Path(path).is_file() or digest(path) != value]
        missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        write(out/'inputs_after.json', dict(verified=not changed and not missing, changed_paths=changed,
            unpinned_project_sources=missing, input_pins=pins))
        audit = pool.scene.diagnostics if pool and pool.scene else None
        lifecycle = bool(audit and audit.get('closed') and audit.get('physx_use_gpu') and audit.get('use_gpu_pipeline') and
            audit.get('simulator_count') == 1 and audit.get('environment_count') == settings['num_envs'])
        video_files = {name:dict(path=str(out/(name+'.mp4')), bytes=(out/(name+'.mp4')).stat().st_size if (out/(name+'.mp4')).is_file() else 0) for name in codes}
        complete = bool(failure is None and unchanged and lifecycle and not changed and not missing and not cleanup_errors and
            trace_finite and clock_contiguous and capture and capture.episode and capture.frame_times_s and
            len(codes) == 2 and all(code == 0 for code in codes.values()) and all(value['bytes'] > 0 for value in video_files.values()))
        report = dict(schema='guitar_learning.short_finger_render.v2', completed=complete, failure=failure,
            control=control, policy_performance=control == 'policy', checkpoint=str(checkpoint),
            checkpoint_sha256=pins[str(checkpoint)], checkpoint_unchanged=str(checkpoint) not in changed,
            recorded_environment=0, first_episode_only=True, policy_unchanged=unchanged,
            native_pixels=True, frames=len(capture.frame_times_s) if capture else 0,
            trace_finite=trace_finite, physics_clock_contiguous=clock_contiguous,
            encoding_exit_codes=codes, video_files=video_files, cleanup_errors=cleanup_errors, source_pins_unchanged=not changed,
            changed_inputs=changed, unpinned_project_sources=missing, checkpoint_pins_validated=True,
            scene_closed=bool(audit and audit.get('closed')), lifecycle_verified=lifecycle, gpu_scene=audit,
            training_updates=0, wall_s=time.monotonic()-started, episode_summary=compact,
            scope=spec['result_scope'])
        write(out/'report.json', report)
        if failure is None and not complete:
            raise RuntimeError('Native video/source/model/clock/scene audit failed; see report.json')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--num-envs', type=int)
    parser.add_argument('--control', choices=('policy', 'reference'), default='policy')
    parser.add_argument('--reference', type=Path)
    args = parser.parse_args()
    render(args.checkpoint, args.out, num_envs=args.num_envs, control=args.control, reference=args.reference)


if __name__ == '__main__':
    main()
