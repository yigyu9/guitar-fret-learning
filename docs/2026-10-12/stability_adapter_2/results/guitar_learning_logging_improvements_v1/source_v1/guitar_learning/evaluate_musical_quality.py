"""Evaluate the versioned clean-contact/prepared-strike quality contract."""
import argparse
import json
import os
from pathlib import Path
from unittest.mock import patch


def evaluate(settings, args):
    from . import evaluate_timing, timing_environment, timing_transfer, train_timing
    from .musical_quality_environment import build_environment
    from .musical_quality_transfer import apply_actor_initialization
    from .train_musical_quality import compact
    with patch.object(timing_environment, 'build_environment', build_environment), \
            patch.object(timing_transfer, 'apply_actor_initialization', apply_actor_initialization), \
            patch.object(train_timing, 'timing_compact', compact):
        result = evaluate_timing.evaluate(settings, args)
    from .recording import write
    write(args.out/'musical_quality_result.json', dict(result, schema='guitar_learning.musical_quality_evaluation.v1',
        scope='new clean-contact/prepared-crossing/release-recovery criteria; not prior timing-only success or pressure/audio'))
    import torch
    from .recording import digest
    checkpoint=Path(result['checkpoint'])
    payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
    episodes=result['episodes']
    write(args.out/'evaluation_metrics.json',dict(schema='guitar_learning.evaluation_metrics.v1',
        mode='deterministic_evaluation',checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),
        optimizer_updates=payload.get('updates') if result['kind']=='strict_PPO' else 0,
        source_checkpoint_optimizer_updates=payload.get('updates'),policy_initialization_mode=result['kind'],
        configured_seed=settings['seed'],
        seed_scope='settings provenance only; evaluator does not explicitly reseed, strict PPO load restores checkpoint RNG',
        role=result['role'],timing=settings['timing'],
        completed_episodes=len(episodes),requested_episodes=args.episodes,
        quality_successful_episodes=result['successful_episodes'],
        timing_only_successful_episodes=sum(e['timing']['timing_only_stage_success'] for e in episodes),
        physical_failure_episodes=sum(e['reason']=='terminal_failure' for e in episodes),
        metrics=[e['musical_quality'] for e in episodes],
        scope='fixed first score target and prepared start; separate from stochastic training; no generalization claim'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--run', type=Path)
    source.add_argument('--initialization', type=Path)
    parser.add_argument('--settings', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--episodes', type=int, default=2)
    args = parser.parse_args()
    if args.settings is None:
        if args.run is None: parser.error('--initialization requires --settings')
        args.settings = args.run/'settings.json'
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'): os.environ[name] = '1'
    import isaacgym
    from .train_musical_quality import settings_document
    evaluate(settings_document(json.loads(args.settings.read_text())), args)


if __name__ == '__main__': main()
