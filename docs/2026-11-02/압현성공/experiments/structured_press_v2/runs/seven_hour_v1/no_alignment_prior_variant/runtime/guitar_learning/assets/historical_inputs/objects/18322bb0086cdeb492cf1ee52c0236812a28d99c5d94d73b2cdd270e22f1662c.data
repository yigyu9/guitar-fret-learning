"""Audited refinement eval/train; stochastic evaluation is explicitly recorded."""
import argparse
import json
import os
from pathlib import Path


def run(settings, args):
    import isaacgym
    from unittest.mock import patch
    # Bind the original BC loader before replacing the public policy binding.
    from guitar_learning.tool.experiments.transition import learning, train, transfer, probe, train_with_teacher_proof
    from guitar_learning.tool.experiments.transition import policy as legacy_policy, environment as legacy_env, worker as legacy_worker
    from guitar_learning.training import ppo as shared_ppo
    from guitar_learning.tool.experiments.transition_refinement import evidence
    from guitar_learning.tool.experiments.transition_refinement.settings import settings_document
    from guitar_learning.tool.experiments.transition_refinement.policy import SpecialistPolicy
    from guitar_learning.tool.experiments.transition_refinement.ppo import PPOTrainer, demonstration_digest
    from guitar_learning.tool.experiments.transition_refinement.environment import build_environment
    from guitar_learning.tool.experiments.transition_refinement.worker import native_environment
    from guitar_learning.imitation.imitation import dataset_manifest
    settings = settings_document(settings)
    if args.mode not in ('eval', 'train'):
        raise ValueError('eval/train mode required')
    checkpoint = getattr(args, 'checkpoint', None)
    resume = getattr(args, 'resume', None)
    if args.mode == 'eval' and resume is not None or args.mode == 'train' and checkpoint is not None:
        raise ValueError('evaluation checkpoint and training resume must be separate')
    if args.mode == 'train' and settings['refinement']['evaluation_mode'] != 'deterministic':
        raise ValueError('training configuration uses deterministic native evaluation gates')
    proof = evidence.initialization_evidence(settings, require_gate=args.mode == 'train' or checkpoint is not None)
    data = proof.get('rehearsal_data')
    data_sha = demonstration_digest(data) if data is not None else None
    stochastic = settings['refinement']['evaluation_mode'] == 'stochastic'

    def verified_evidence(value, *, require_gate=False):
        if value != settings or require_gate and data is None:
            raise ValueError('cached evidence belongs to the exact requested configuration/gates')
        if dataset_manifest(proof['source_pins']) != proof['source_pins']:
            raise RuntimeError('fully audited refinement evidence changed')
        return proof

    class ConfiguredPolicy(SpecialistPolicy):
        def __init__(self, state_dim=500, event_dim=24, size='medium', contract=None):
            super().__init__(state_dim, event_dim, size, contract,
                exploration=settings['refinement']['exploration'])

        def act(self, *inputs, deterministic=False):
            return super().act(*inputs, deterministic=deterministic and not stochastic)

    class ConfiguredTrainer(PPOTrainer):
        def __init__(self, model, config=None):
            if data is None:
                raise ValueError('audited new native success replay required for PPO/rehearsal')
            super().__init__(model, config, demonstration=data,
                refinement=settings['refinement']['learning'], demonstration_sha256=data_sha)

    with patch.object(legacy_policy, 'SpecialistPolicy', ConfiguredPolicy), \
            patch.object(transfer, 'initialize_actor', evidence.initialize_actor), \
            patch.object(train, 'initialization_evidence', verified_evidence), \
            patch.object(evidence, 'initialization_evidence', verified_evidence), \
            patch.object(legacy_env, 'build_environment', build_environment), \
            patch.object(legacy_worker, 'native_environment', native_environment), \
            patch.object(shared_ppo, 'PPOTrainer', ConfiguredTrainer):
        if args.mode == 'eval':
            args.controller = 'policy'
            return probe.run(settings, args)
        return train_with_teacher_proof.run(settings, args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('eval', 'train'))
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--episodes', type=int, default=1)
    args = parser.parse_args()
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    import isaacgym
    from guitar_learning.tool.experiments.transition_refinement.settings import settings_document
    run(settings_document(json.loads(args.settings.read_text())), args)


if __name__ == '__main__':
    main()
