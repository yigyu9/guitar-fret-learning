"""CPU-only seed17 plan, initialization and unchanged strict-load checks."""
import argparse
import ast
import copy
import json
from pathlib import Path
import pickle
import random
import sys
import tempfile

import numpy as np
import torch

import run_replication as replication
sys.path.insert(0, str(replication.original().ROOT))
from variants import settings_for, policy_type
from guitar_learning.tool.experiments.short_finger_learning.runner import make_settings
from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment, ShortPolicy
from guitar_learning.training.decision_ppo import DecisionPPOTrainer
from guitar_learning.training.ppo import PPOConfig


HERE = Path(__file__).resolve().parent


def seed():
    random.seed(17)
    np.random.seed(17)
    torch.manual_seed(17)


def rng():
    return pickle.dumps((random.getstate(), np.random.get_state()))+torch.get_rng_state().numpy().tobytes()


def main():
    torch.set_num_threads(1)
    assert not torch.cuda.is_available(), 'CPU-only check requires CUDA_VISIBLE_DEVICES empty'
    replication.validate_freeze()
    baseline = replication.original()
    plan = replication.jobs()
    assert len(plan) == 11 and len({j['out'] for j in plan}) == 11
    assert plan[0]['args'][plan[0]['args'].index('--seed')+1] == '17'
    assert all(j['args'][j['args'].index('--variant')+1] == 'B_zero_cost_head' for j in plan)
    assert all(j['args'][j['args'].index('--episodes')+1] == '128' for j in plan[1:])
    args = argparse.Namespace(teacher=str(baseline.TEACHER), mode='incremental',
        initial_std=baseline.STDS['incremental'], song='05_BN2-131-B_solo', size='large',
        num_envs=128, horizon=32, updates=300, save_every=50, seed=17)
    original_settings = make_settings(args)
    settings = settings_for(original_settings, replication.VARIANT)
    normalized = copy.deepcopy(settings)
    normalized['song']['short_learning'].pop('ablation')
    assert normalized == original_settings and settings['ppo']['gamma'] == settings['song']['surface_approach_gamma'] == .99
    metadata = baseline.read(replication.BASE.parents[2]/'02_contact_reward/teacher_fixed_B_export/metadata.json')
    env = ShortEnvironment(metadata, bundle=settings['song_training']['bundle'], song=settings['song'],
        skill=settings['finger_skill'], device='cpu')
    seed()
    normal = ShortPolicy(contract=env.contract, size='large')
    normal_rng = rng()
    seed()
    zero = policy_type(replication.VARIANT, fresh=True)(contract=env.contract, size='large')
    assert rng() == normal_rng
    changed = [k for k, v in normal.state_dict().items() if not torch.equal(v, zero.state_dict()[k])]
    assert changed == ['cost_critic.weight', 'cost_critic.bias'] and len(zero.state_dict()) == 73
    assert all(torch.count_nonzero(zero.state_dict()[k]) == 0 for k in changed)
    trainer = DecisionPPOTrainer(zero, PPOConfig(**settings['ppo']))
    # A nonzero sentinel proves evaluation does not silently re-zero loaded heads.
    with torch.no_grad():
        zero.cost_critic.bias.fill_(.125)
    with tempfile.TemporaryDirectory(dir=str(HERE)) as folder:
        checkpoint = Path(folder)/'probe.pt'
        trainer.save(checkpoint, metadata=dict(cpu_probe=True))
        restored = policy_type(replication.VARIANT, fresh=False)(contract=env.contract, size='large')
        DecisionPPOTrainer(restored, PPOConfig(**settings['ppo'])).load(checkpoint)
        assert torch.equal(restored.cost_critic.bias, zero.cost_critic.bias)
        changed_contract = copy.deepcopy(env.contract)
        changed_contract['task']['short_learning']['view']['source_index'] = 52
        rejected = False
        try:
            other = policy_type(replication.VARIANT, fresh=False)(contract=changed_contract, size='large')
            DecisionPPOTrainer(other, PPOConfig(**settings['ppo'])).load(checkpoint)
        except ValueError:
            rejected = True
        assert rejected
    for path in (HERE/'run_replication.py', Path(__file__)):
        ast.parse(path.read_text(), feature_version=(3, 8))
    assert not torch.cuda.is_initialized()
    verification = dict(scope='CPU-only expected initialization; not native-generated initial checkpoint or GPU performance',
        seed=17, jobs=11, train_updates=300, evaluation_stages=10, attempts_per_evaluation=128,
        initial_model_tensors=73, same_seed17_normal_tensors_exact=71, changed_tensors=changed,
        initial_cost_head_exact_zero=True, initialization_RNG_exact=True,
        settings_only_B_descriptor=True, gamma_and_PBRS_gamma=.99,
        strict_same_contract_load=True, strict_changed_view_rejected=True,
        evaluation_nonzero_cost_head_preserved=True, python38_syntax=True,
        old_frozen_sources_verified=True, CUDA_initialized=False, GPU_executed=False)
    baseline.write(HERE/'cpu_verification.json', verification)
    baseline.write(HERE/'dry_run.json', dict(seed=17, variant=replication.VARIANT,
        output=str(replication.OUTPUT), jobs=plan, GPU_executed=False))
    print(json.dumps(verification, ensure_ascii=False))


if __name__ == '__main__':
    main()
