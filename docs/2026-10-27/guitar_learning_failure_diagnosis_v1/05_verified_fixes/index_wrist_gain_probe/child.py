"""One predeclared wrist correction cap; original CLI and strict runner."""
import copy
from contextlib import contextmanager
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OWNED_INPUTS = ('child.py', 'run_probe.py', 'cpu_check.py', 'PLAN.md',
    'cpu_verification.json', 'dry_run.json', 'review.json', 'REVIEW.md', 'preparation_seal.json')


def control(original):
    result = copy.deepcopy(original)
    result.update(schema='guitar_learning.fixed_wrist_teacher.index_cap_0p1deg.v1',
        correction_step_rad=math.radians(.1), correction_rate_bound_rad_s=math.radians(.1)*60)
    return result


@contextmanager
def patched_control():
    from guitar_learning.tool.experiments.short_finger_learning.wrist import WRIST_CONTROL
    before = copy.deepcopy(WRIST_CONTROL)
    WRIST_CONTROL.clear()
    WRIST_CONTROL.update(control(before))
    try:
        yield copy.deepcopy(WRIST_CONTROL)
    finally:
        WRIST_CONTROL.clear()
        WRIST_CONTROL.update(before)


def main():
    from guitar_learning.tool.experiments.short_finger_learning.__main__ import parser
    args = parser().parse_args()
    if args.command == 'evaluate':
        if args.episodes < 1 or ((args.control == 'reference') != bool(args.reference)):
            raise ValueError('Positive attempts and reference exactly for reference control required')
    import isaacgym  # Must precede Torch/NumPy and runner imports.
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    with patched_control() as expected:
        if args.command == 'evaluate':
            payload = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
            runner._validate_pins(payload['metadata'])
            if payload['metadata']['settings']['song']['short_learning']['wrist_control'] != expected:
                raise ValueError('Own complete wrist correction contract required')
        original = runner._pins
        def pins(settings, out, extra=()):
            return original(settings, out, [*extra, *(HERE/name for name in OWNED_INPUTS)])
        runner._pins = pins
        try:
            runner.run(args)  # Original full identity/config/optimizer strict load.
        finally:
            runner._pins = original


if __name__ == '__main__':
    main()
