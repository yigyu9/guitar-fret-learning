"""Evaluate a frozen reward-v2 checkpoint over the complete score."""
import argparse
import json
import os
from pathlib import Path


def evaluate(settings,args):
    import isaacgym
    from unittest.mock import patch
    from guitar_learning.tool.experiments.song import evaluate as original, policy, transfer, worker
    from guitar_learning.song import environment
    from guitar_learning.song.reward_environment import build_environment
    from guitar_learning.tool.experiments.song_reward_v2.policy import RewardPolicy
    from guitar_learning.tool.experiments.song_reward_v2.transfer import validate_experts, apply_experts
    from guitar_learning.tool.experiments.song_reward_v2.worker import compact
    if args.run is None:raise ValueError('reward-v2 evaluation requires a trained checkpoint')
    with patch.object(environment,'build_environment',build_environment), \
            patch.object(policy,'SongPolicy',RewardPolicy), \
            patch.object(transfer,'validate_experts',validate_experts), \
            patch.object(transfer,'apply_experts',apply_experts),patch.object(worker,'compact',compact):
        return original.evaluate(settings,args)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    import isaacgym
    from guitar_learning.tool.experiments.song_reward_v2.settings import settings_document
    evaluate(settings_document(json.loads(args.settings.read_text())),args)


if __name__=='__main__':main()
