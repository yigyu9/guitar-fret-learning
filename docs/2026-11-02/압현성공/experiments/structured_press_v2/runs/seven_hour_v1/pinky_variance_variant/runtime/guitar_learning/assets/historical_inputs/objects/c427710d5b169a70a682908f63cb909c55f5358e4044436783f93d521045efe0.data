"""Timing PPO with a stable compact logger binding in fresh native workers."""
from unittest.mock import patch
from guitar_learning.tool.training import train_timing

_BASE_WORKER = train_timing.timing_native_environment


def timing_native_environment(spec, worker_id):
    import isaacgym  # Native imports must precede numpy/torch.
    # Capture parallel's original logger before v1 installs timing_compact.
    # Lazy-importing this module after installation would capture the wrapper
    # itself as base_compact, causing unbounded recursion on the first step.
    from guitar_learning.skills.specialist_parallel import specialist_compact
    return _BASE_WORKER(spec, worker_id)


def run(settings, args):
    with patch.object(train_timing, 'timing_native_environment', timing_native_environment):
        return train_timing.run(settings, args)


def main():
    import argparse
    import json
    import os
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume', type=Path)
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import isaacgym
    run(train_timing.settings_document(json.loads(args.settings.read_text())), args)


if __name__ == '__main__':
    main()
