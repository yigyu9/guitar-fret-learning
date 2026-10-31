"""Train one hand, adapt it with a frozen partner, or jointly tune two experts."""
import argparse
import copy
from functools import partial
import gzip
import json
from pathlib import Path
import sys


def summarize_run(out):
    """Stream role evidence; never replace joint music with single-hand success."""
    from .recording import write, digest
    out = Path(out)
    report = json.loads((out / 'report.json').read_text())
    episodes = []
    transitions = 0
    with gzip.open(out / 'transitions.jsonl.gz', 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            for info in row['infos']:
                transitions += 1
                if 'specialist' not in info:
                    raise ValueError('independent hand evidence missing from transition log')
                if 'episode' in info:
                    episode = info['episode']
                    evidence = episode['specialist']
                    episodes.append(dict(reason=episode['reason'], reward=episode['reward'], cost=episode['cost'],
                        steps=episode['steps'], specialist=evidence, music=episode['music']))
    role = report['settings']['specialist']['role']
    summary = dict(completed=report['completed'], role=role,
        report=dict(path=str(out / 'report.json'), sha256=digest(out / 'report.json')),
        logged_transitions=transitions, committed_transitions=report['transitions'],
        completed_episodes=len(episodes), successful_episodes=sum(e['specialist']['stage_success'] for e in episodes),
        physical_failure_episodes=sum(e['reason'] == 'terminal_failure' for e in episodes), episodes=episodes,
        scope='single-hand contact/geometric stage success is distinct from joint music and acoustic performance')
    write(out / 'specialist_report.json', summary)
    return summary


def run(settings, args):
    # Isaac Gym must be loaded before the policy and shared PPO import torch.
    import isaacgym
    from unittest.mock import patch
    from . import parallel, policy, ppo, train_parallel
    from .recording import write, digest
    from .specialist_policy import SpecialistPolicy
    from .specialist_parallel import SpecialistPool
    from .specialist_settings import frozen_partner, expert_paths
    from .persistent_audit import finalize_persistent_run
    from stability_adapter_2.lower_body_release_v1 import common
    stage = settings['specialist']
    paths = expert_paths(stage)
    expected = {str(p): digest(p) for p in paths}
    original_pin = common.pin
    original_trainer = ppo.PPOTrainer

    def pin_with_experts(config, extra=()):
        result = original_pin(config, extra=set(extra) | set(paths))
        if any(result.get(p) != sha for p, sha in expected.items()):
            raise RuntimeError('expert checkpoint changed before run pin')
        return result

    class SpecialistTrainer(original_trainer):
        def __init__(self, model, config=None):
            transfers = []
            # The core applies initial_std before constructing this trainer.
            # Transfer thereafter preserves each expert's learned exploration.
            if args.resume is None:
                for hand in ('left', 'right'):
                    path = stage.get(hand + '_checkpoint')
                    if path is not None:
                        transfer = model.transfer_actor(path, hand)
                        transfers.append(dict(path=path, sha256=expected[path], **transfer))
            super().__init__(model, config)
            write(args.out.resolve() / 'expert_initialization.json',
                dict(mode='strict_resume' if args.resume else 'actor_only_warm_start_new_critics_and_optimizers',
                     transfers=transfers, strict_resume=str(args.resume.resolve()) if args.resume else None))

    class ConfiguredPool(SpecialistPool):
        def __init__(self, specs, **kwargs):
            super().__init__(specs, specialist=stage, **kwargs)

    existed = args.out.exists()
    try:
        # These CLI-only bindings are process-private and restored on failure.
        # The original executors/sources and checkpoint identity stay intact.
        with patch.object(train_parallel, 'settings_document', lambda _: copy.deepcopy(settings)), \
             patch.object(parallel, 'Pool', ConfiguredPool), \
             patch.object(policy, 'Policy', partial(SpecialistPolicy, role=stage['role'], frozen_partner=frozen_partner(stage))), \
             patch.object(ppo, 'PPOTrainer', SpecialistTrainer), \
             patch.object(common, 'pin', pin_with_experts):
            train_parallel.main()
    finally:
        original_error = sys.exc_info()[1]
        if not existed:
            try:
                passed = finalize_persistent_run(args.out.resolve())
                if (args.out / 'report.json').is_file():
                    summarize_run(args.out.resolve())
                if passed is False and original_error is None:
                    raise RuntimeError('specialist persistent lifecycle audit failed; see report.json')
            except BaseException as audit_error:
                if original_error is None:
                    raise
                print('[specialist] secondary audit error: ' + str(audit_error), file=sys.stderr, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume', type=Path)
    args = parser.parse_args()
    # Set numerical thread limits before importing Isaac Gym, NumPy or torch.
    import os
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import isaacgym
    from .specialist_settings import settings_document
    settings = settings_document(json.loads(args.settings.read_text()))
    run(settings, args)


if __name__ == '__main__':
    main()
