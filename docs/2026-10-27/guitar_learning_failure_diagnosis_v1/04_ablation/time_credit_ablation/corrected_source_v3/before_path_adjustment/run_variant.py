"""Existing short-task CLI/runner with one explicit fresh A or B intervention."""
from pathlib import Path
import json

from variants import VARIANTS, settings_for, validate_settings, policy_type


BASE=Path(__file__).resolve().parents[1]
DIAG=BASE.parents[1]
REUSED=DIAG/'03_short_learning/support/run_short_comparison.py'


def watched_sources():
    documents=[DIAG/'02_contact_reward/short_finger_wrist_teacher_middle_row8_v2.json',
               DIAG/'03_short_learning/reference_middle_row8_v2.json']
    evidence=[Path(path) for doc in documents for path in json.loads(doc.read_text())['source_evidence']]
    return [*sorted((BASE/'support').glob('*.py')),REUSED,BASE.parent/'INTERVENTION_PLAN.md',*documents,*evidence]


def main():
    from guitar_learning.tool.experiments.short_finger_learning.__main__ import parser
    value=parser();value.add_argument('--variant',choices=VARIANTS,required=True)
    args=value.parse_args()
    if args.command=='evaluate':
        if args.episodes<1 or ((args.control=='reference')!=bool(args.reference)):
            raise ValueError('Positive episodes and reference exactly for reference control required')
    import isaacgym  # Must precede NumPy/Torch and the actual runner.
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    if args.command=='evaluate':
        payload=torch.load(args.checkpoint,map_location='cpu',weights_only=False)
        runner._validate_pins(payload['metadata'])
        validate_settings(payload['metadata']['settings'],args.variant)
    original_settings,original_policy,original_pins=runner.make_settings,runner.ShortPolicy,runner._pins
    def make_settings(arguments):
        return settings_for(original_settings(arguments),args.variant)
    def pins(settings,out,extra=()):
        return original_pins(settings,out,[*extra,*watched_sources()])
    runner.make_settings=make_settings
    runner.ShortPolicy=policy_type(args.variant,fresh=args.command=='train')
    runner._pins=pins
    try:
        runner.run(args)  # Original strict trainer.load; no evaluation re-zero.
    finally:
        runner.make_settings,runner.ShortPolicy,runner._pins=original_settings,original_policy,original_pins


if __name__=='__main__':main()
