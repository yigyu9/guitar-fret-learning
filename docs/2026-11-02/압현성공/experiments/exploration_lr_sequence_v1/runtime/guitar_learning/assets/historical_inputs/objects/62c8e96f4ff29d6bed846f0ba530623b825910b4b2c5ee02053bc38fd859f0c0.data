"""BC-initialized PPO with JSON-equivalent contract comparison at transfer only."""
import argparse
import json
from pathlib import Path


def run(settings, args):
    import isaacgym
    from unittest.mock import patch
    from . import imitation, train_imitation_ppo
    from .imitation_v2 import apply_actor_initialization
    with patch.object(imitation, 'apply_actor_initialization', apply_actor_initialization):
        return train_imitation_ppo.run(settings, args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume', type=Path)
    args = parser.parse_args()
    import os
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import isaacgym
    from .train_imitation_ppo import settings_document
    settings = settings_document(json.loads(args.settings.read_text()))
    run(settings, args)


if __name__ == '__main__': main()
