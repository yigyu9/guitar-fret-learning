"""Train a selected hand across a reviewed song from the agreed prepared pose."""
import argparse
import copy
from functools import partial
import os
from pathlib import Path
import sys
from unittest.mock import patch


DEFAULT_SONG = '05_BN2-131-B_solo'


def settings_document(hand, *, song=DEFAULT_SONG, updates=100, num_envs=None,
                      device='cuda:0', seed=7, horizon=None, size='medium', physics='auto',
                      checkpoint_every=250, finger_standby_rate=None, finger_shape=False):
    """Use every source note; a collection boundary never ends the song."""
    if hand not in ('left', 'right'):
        raise ValueError('left/right hand required')
    from guitar_learning.training.runner import settings_document as base_settings
    from guitar_learning.song.task import make_task
    if not isinstance(song, str) or not song or Path(song).name != song or song in ('.', '..'):
        raise ValueError('song must be one registered song identifier')
    bundle = Path(__file__).resolve().parents[2]/'data/song_bundles'/song
    config = dict(schema='guitar_learning.song.v1', pre_roll_s=3., tail_s=.5,
                  window_s=.5, left_fraction=.4)
    task = make_task(bundle, pre_roll_s=config['pre_roll_s'], tail_s=config['tail_s'])
    if any(not target.fret for target in task.targets):
        raise ValueError('song training currently requires fretted notes; open strings are unsupported')
    ticks = task.provenance['song']['control_ticks']
    if device == 'auto':
        import torch
        device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    if physics not in ('auto', 'cpu', 'gpu'):
        raise ValueError('physics must be auto/cpu/gpu')
    gpu = physics == 'gpu' or (physics == 'auto' and device == 'cuda:0')
    if gpu and device != 'cuda:0':
        raise ValueError('GPU physics requires --device cuda:0')
    if type(finger_shape) is not bool:
        raise ValueError('finger_shape must be boolean')
    if (finger_standby_rate is not None or finger_shape) and not (gpu and hand == 'left'):
        raise ValueError('finger recovery options require GPU left training')
    count = (128 if gpu else 2) if num_envs is None else num_envs
    if gpu and (type(count) is not int or not 1 <= count <= 1024):
        raise ValueError('GPU environment count must be an integer in1..1024')
    collection = (32 if gpu else ticks) if horizon is None else horizon
    settings = base_settings(dict(updates=updates, num_envs=min(count, 2) if gpu else count, device=device,
        seed=seed, horizon=collection, size=size, checkpoint_every=checkpoint_every,
        stage='D', phrase_events=task.provenance['song']['source_event_count']))
    # Keep the legacy settings document unchanged outside GPU left training.
    settings['ppo'].pop('advantage_normalization',None)
    if gpu:
        settings['num_envs'] = count
        settings['ppo']['minibatch_size'] = 4096
        settings['physics_backend'] = dict(schema='guitar_learning.gpu_batch.v3',
            engine='GPU PhysX', tensor_pipeline='cuda', control='batched_tensor',
            measurement='gpu_surface_loaded.v1', cpu_checkpoint_compatible=False)
    settings.update(specialist=dict(role=hand, left_checkpoint=None, right_checkpoint=None),
        song=config, song_training=dict(schema='guitar_learning.song_training.v1',
            song_id=song, bundle=str(bundle.resolve()), target_count=len(task.targets),
            control_ticks=ticks, episode_duration_s=task.duration_s,
            score_clock='original_audio_plus_policy_pre_roll', observation_dimension=500),
        simple_start=dict(schema='guitar_learning.song_start.v1', initial_pose='agreed035_v14',
            initialization='fresh_unless_strict_resume'))
    if hand == 'left':
        if gpu:
            from guitar_learning.song.gpu_left_curriculum import default_config
            settings['ppo'].update(advantage_normalization='separate',gae_lambda=.98)
            settings['song']['surface_approach_gamma'] = settings['ppo']['gamma']
            from guitar_learning.gpu.finger_reward import finger_recovery_config
            settings['song']['finger_recovery'] = finger_recovery_config(dict(
                schema='guitar_learning.left_finger_recovery.v1',
                standby_rate_per_s=.02 if finger_standby_rate is None else finger_standby_rate,
                shape_rate_per_s=.004 if finger_shape else 0.))
        else:
            from guitar_learning.song.left_curriculum import default_config
        from guitar_learning.core.finger_control import default_profile
        from guitar_learning.song.wrist_guide import load_anchor_track
        load_anchor_track(bundle)
        settings['song']['left_curriculum'] = default_config()
        settings['song']['finger_control'] = default_profile()
        settings['song_training']['observation_dimension'] = 544 if gpu else 512
    return settings


def run(settings, args):
    """Bind the chosen hand to the shared collector/PPO for this process only."""
    # Isaac Gym must precede imports of torch in the runner and policy.
    import isaacgym
    if 'physics_backend' in settings:
        from guitar_learning.training.gpu_runner import run as run_gpu
        return run_gpu(settings, args)
    from guitar_learning.training import runner as train_parallel
    from guitar_learning.training import parallel, policy
    from guitar_learning.training.persistent_audit import finalize_persistent_run
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.song.runtime import native_environment, summarize_run
    hand = settings['specialist']['role']
    if hand not in ('left', 'right') or any(
            settings['specialist'].get(name+'_checkpoint') is not None for name in ('left', 'right')):
        raise ValueError('single hand without expert checkpoints required')
    base_pool = parallel.Pool

    class HandPool(base_pool):
        def __init__(self, specs, **kwargs):
            specs = copy.deepcopy(specs)
            for spec in specs:
                spec.update(specialist=copy.deepcopy(settings['specialist']),
                    song=copy.deepcopy(settings['song']))
            super().__init__(specs, worker_factory=native_environment, **kwargs)

    out = args.out.resolve()
    argv = [sys.argv[0], '--settings', str(out/'settings.json'), '--out', str(out)]
    if args.resume is not None:
        argv += ['--resume', str(args.resume)]
    existed = out.exists()
    summary = None
    try:
        with patch.object(parallel, 'Pool', HandPool), \
             patch.object(policy, 'Policy', partial(SpecialistPolicy, role=hand, frozen_partner=False)), \
             patch.object(sys, 'argv', argv):
            train_parallel.main(settings=settings)
    finally:
        original_error = sys.exc_info()[1]
        if not existed:
            try:
                passed = finalize_persistent_run(out)
                if (out/'report.json').is_file():
                    summary = summarize_run(out)
                if passed is False and original_error is None:
                    raise RuntimeError('persistent lifecycle audit failed; see report.json')
            except BaseException as audit_error:
                if original_error is None:
                    raise
                print('[training] secondary summary/audit error: '+str(audit_error),
                    file=sys.stderr, flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hand', choices=('left', 'right'), required=True)
    parser.add_argument('--song', default=DEFAULT_SONG,
                        help='reviewed song identifier under data/song_bundles')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--updates', type=int, default=100)
    parser.add_argument('--num-envs', type=int, help='GPU default128; CPU default2')
    parser.add_argument('--device', choices=('auto', 'cpu', 'cuda:0'), default='cuda:0')
    parser.add_argument('--physics', choices=('auto', 'cpu', 'gpu'), default='auto',
                        help='auto uses GPU physics with CUDA, CPU physics with CPU policy')
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--horizon', type=int,
                        help='GPU default32, CPU default whole song; cuts continue the song clock')
    parser.add_argument('--size', choices=('small', 'medium', 'large'), default='medium')
    parser.add_argument('--checkpoint-every', type=int, default=250,
                        help='save an additional checkpoint every N updates (default250)')
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--finger-standby-rate', type=float, choices=(.02, .04), default=None,
                        help='GPU left: B preference maximum rate per second (default0.02)')
    parser.add_argument('--finger-shape', action='store_true',
                        help='GPU left: enable separate experimental0.004/s DIP-PIP shape preference')
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import isaacgym
    settings = settings_document(args.hand, song=args.song, updates=args.updates, num_envs=args.num_envs,
        device=args.device, seed=args.seed, horizon=args.horizon, size=args.size, physics=args.physics,
        checkpoint_every=args.checkpoint_every, finger_standby_rate=args.finger_standby_rate,
        finger_shape=args.finger_shape)
    return run(settings, args)


if __name__ == '__main__':
    main()
