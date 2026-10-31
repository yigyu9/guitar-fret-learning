"""Reward revision wrapper over the frozen, audited whole-score PPO runner."""
import argparse
import copy
import json
import os
from pathlib import Path


def run(settings,args):
    import isaacgym
    from unittest.mock import patch
    from guitar_learning.tool.experiments.song import train, transfer, worker, policy
    from guitar_learning.tool.experiments.song_reward_v2.transfer import validate_experts, apply_experts
    from guitar_learning.tool.experiments.song_reward_v2.worker import native_environment
    from guitar_learning.tool.experiments.song_reward_v2.policy import RewardPolicy
    from guitar_learning.training import recording
    from guitar_learning.training.recording import write, digest
    original_write=recording.write
    initialization_path=(args.out/'song_initialization.json').resolve()
    def revision_write(path,value,*positional,**kwargs):
        if Path(path).resolve()==initialization_path and value.get('mode')=='physical_feature_actor_only':
            value=copy.deepcopy(value)
            value['mode']='whole_score_actor_and_std_reward_v2_fresh_critic_and_Adam'
        return original_write(path,value,*positional,**kwargs)
    # The original song runner retains resource guards, transactional PPO,
    # persistent reset, source pinning and full/partial trajectory accounting.
    with patch.object(transfer,'validate_experts',validate_experts), \
            patch.object(transfer,'apply_experts',apply_experts), \
            patch.object(worker,'native_environment',native_environment), \
            patch.object(policy,'SongPolicy',RewardPolicy),patch.object(recording,'write',revision_write):
        result=train.run(settings,args)
    if result is not None:
        write(args.out/'reward_revision_report.json',dict(schema='guitar_learning.song_reward.v2',
            initialization_checkpoint=settings['reward_revision']['initialization_checkpoint'],
            initialization_checkpoint_sha256=digest(settings['reward_revision']['initialization_checkpoint']),
            report=str((args.out/'song_report.json').resolve()),
            completed=result['completed'],optimizer_updates=result['optimizer_updates'],counts=result['counts'],
            scope='new reward; previous Actor/std only, new critic/Adam; no inherited PPO update or performance'))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--resume',type=Path);args=parser.parse_args()
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    import isaacgym
    from guitar_learning.tool.experiments.song_reward_v2.settings import settings_document
    run(settings_document(json.loads(args.settings.read_text())),args)


if __name__=='__main__':main()
