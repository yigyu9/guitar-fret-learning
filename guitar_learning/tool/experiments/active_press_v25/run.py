"""Explicit v25 train/evaluate/render entry point; no changes to legacy defaults."""
import argparse
import copy
import math
import os
from pathlib import Path
from types import SimpleNamespace


def settings(args):
    from guitar_learning.tool.training.train_legacy import settings_document
    from .runtime import SPEC
    result = settings_document('left', physics='gpu', device='cuda:0', size=args.size,
        num_envs=args.num_envs, horizon=32, seed=7, updates=args.updates, checkpoint_every=50,
        learning_family='finger-skill-v24', skill_phase='J', skill_scope='phrases',
        skill_exploration='independent', skill_hold_ticks=3)
    result.update(active_press=copy.deepcopy(SPEC), initial_std=math.exp(-3),
                  max_wall_seconds=args.max_wall_seconds)
    result['song_training']['observation_dimension'] = 559
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('train', 'evaluate', 'render'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--size', choices=('small', 'medium', 'large'), default='large')
    parser.add_argument('--num-envs', type=int, default=128)
    parser.add_argument('--updates', type=int, default=100)
    parser.add_argument('--max-wall-seconds', type=float, default=3600.)
    args = parser.parse_args()
    if args.mode != 'train' and args.checkpoint is None:
        parser.error('evaluate/render require --checkpoint')
    if args.mode != 'train' and args.resume is not None:
        parser.error('--resume applies only to training')
    if not math.isfinite(args.max_wall_seconds) or args.max_wall_seconds <= 0:
        parser.error('positive finite --max-wall-seconds required')
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import isaacgym
    from .runtime import bindings
    from guitar_learning.training import finger_skill_runner
    with bindings():
        if args.mode == 'train':
            report = finger_skill_runner.run(settings(args), SimpleNamespace(out=args.out, resume=args.resume))
            print('v25', report['stopped'], 'updates budget', args.updates)
        elif args.mode == 'evaluate':
            report, _ = finger_skill_runner.evaluate_checkpoint(args.checkpoint, args.out,
                num_envs=args.num_envs, scope='full_song')
            print('v25 whole-song evaluation completed:', report['completed'])
        else:
            from guitar_learning.tool.demonstration.render_finger_skill import render
            report = render(args.checkpoint.resolve(), args.out, scope='full_song', num_envs=args.num_envs)
            print('v25 render completed:', report['completed'])


if __name__ == '__main__':
    main()
