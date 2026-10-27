"""Train the current GPU left-hand finger skill from the agreed initial pose."""
import argparse
import os
from pathlib import Path

from guitar_learning.training.launch_settings import DEFAULT_SONG, settings_document as build_settings


def settings_document(hand='left', *, learning_family='finger-skill', **options):
    if learning_family != 'finger-skill':
        raise ValueError('Legacy families use python -m guitar_learning.tool.training.train_legacy')
    return build_settings(hand, learning_family=learning_family, **options)


def run(settings, args):
    if (settings.get('finger_skill', {}).get('schema') != 'guitar_learning.finger_skill.v2' or
            settings.get('specialist', {}).get('role') != 'left' or
            settings.get('device') != 'cuda:0' or 'physics_backend' not in settings):
        raise ValueError('Default training requires GPU left-hand finger-skill v2; use train_legacy for old settings')
    # Isaac Gym must precede tensor imports in the runner and policy.
    import isaacgym
    from guitar_learning.training.finger_skill_runner import run as run_finger_skill
    return run_finger_skill(settings, args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hand', choices=('left',), default='left')
    parser.add_argument('--song', default=DEFAULT_SONG,
                        help='reviewed song identifier under data/song_bundles')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--updates', type=int, default=100)
    parser.add_argument('--num-envs', type=int, help='GPU environments (default128)')
    parser.add_argument('--device', choices=('cuda:0',), default='cuda:0')
    parser.add_argument('--physics', choices=('auto', 'gpu'), default='auto',
                        help='CUDA policy and GPU physics; no CPU fallback')
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--horizon', type=int,
                        help='control ticks per update (default32); cuts preserve episode state')
    parser.add_argument('--size', choices=('small', 'medium', 'large'), default='medium')
    parser.add_argument('--checkpoint-every', type=int, default=250,
                        help='save an additional checkpoint every N updates (default250)')
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--learning-family', choices=('finger-skill',), default='finger-skill',
                        help='current joint finger skill (default); old families use train_legacy')
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import isaacgym
    options = vars(args).copy()
    options.pop('out')
    options.pop('resume')
    return run(settings_document(**options), args)


if __name__ == '__main__':
    main()
