"""Explicit legacy song/CPU/right-hand and v24 R/F/J training."""
import argparse
import copy
from functools import partial
import os
from pathlib import Path
import sys
from unittest.mock import patch


from guitar_learning.training.launch_settings import DEFAULT_SONG, settings_document as build_settings


def settings_document(hand, *, learning_family='song', **options):
    if learning_family not in ('song', 'finger-skill-v24'):
        raise ValueError('Current finger-skill training uses python -m guitar_learning.train')
    return build_settings(hand, learning_family=learning_family, **options)


def run(settings, args):
    """Bind the chosen hand to the shared collector/PPO for this process only."""
    # Isaac Gym must precede imports of torch in the runner and policy.
    import isaacgym
    if 'physics_backend' in settings:
        from guitar_learning.tool.training.legacy_gpu_runner import run as run_gpu
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
    parser.add_argument('--finger-action-mode', choices=('position', 'incremental'),
                        help='GPU left: incremental targets (default); position is an experimental comparison arm')
    parser.add_argument('--learning-family', choices=('song', 'finger-skill-v24'), default='song',
                        help='legacy song (default) or split R/F/J v24; current training uses guitar_learning.train')
    parser.add_argument('--skill-phase', choices=('auto', 'R', 'F', 'J'), default='auto',
                        help='new family: automatic R/F/J or one explicit diagnostic phase')
    parser.add_argument('--skill-exploration', choices=('independent', 'correlated'), default='independent')
    parser.add_argument('--skill-hold-ticks', type=int, choices=(1, 3, 6), default=1,
                        help='new family F only: maximum decision ticks, shortened at score boundaries')
    parser.add_argument('--skill-scope', choices=('phrases', 'full_song'),
                        help='explicit single-phase comparison scope; automatic stages choose their own')
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import isaacgym
    settings = settings_document(args.hand, song=args.song, updates=args.updates, num_envs=args.num_envs,
        device=args.device, seed=args.seed, horizon=args.horizon, size=args.size, physics=args.physics,
        checkpoint_every=args.checkpoint_every, finger_standby_rate=args.finger_standby_rate,
        finger_shape=args.finger_shape, finger_action_mode=args.finger_action_mode,
        learning_family=args.learning_family, skill_phase=args.skill_phase,
        skill_exploration=args.skill_exploration, skill_hold_ticks=args.skill_hold_ticks,
        skill_scope=args.skill_scope)
    return run(settings, args)


if __name__ == '__main__':
    main()
