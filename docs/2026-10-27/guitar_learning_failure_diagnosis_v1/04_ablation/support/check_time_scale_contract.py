"""CPU fixture verifies existing gamma configuration and strict resume rejection."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

# PPO checkpoint serialization conditionally reads CUDA RNG state; isolate this
# standalone arithmetic/configuration check before importing Torch.
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import torch

from guitar_learning.tests.test_short_finger_learning import setup
from guitar_learning.tests.test_gpu_environment import BUNDLE
from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment, ShortPolicy
from guitar_learning.training.decision_ppo import DecisionPPOTrainer
from guitar_learning.training.ppo import PPOConfig


OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[3]


def differences(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for key in sorted(a.keys() | b.keys()):
            result += differences(a.get(key), b.get(key), path+'.'+key)
        return result
    return [] if a == b else [dict(path=path, before=a, after=b)]


def main():
    torch.set_num_threads(1)
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    sources = [Path(__file__)] + [ROOT/'guitar_learning'/name for name in (
        'gpu/environment.py', 'gpu/simplified_finger_environment.py',
        'tool/experiments/short_finger_learning/runtime.py', 'training/ppo.py',
        'training/decision_ppo.py', 'tests/test_short_finger_learning.py', 'tests/test_gpu_environment.py')]
    settings_path = OUT.parent/'03_short_learning/pilot_incremental_seed7_v2_retry2/train/settings.json'
    sources.append(settings_path)
    baseline_ppo = json.loads(settings_path.read_text())['ppo']
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    pins = {str(p): digest(p) for p in sources}
    _, snapshot, _, metadata, song, skill = setup(count=1)
    candidate = math.exp(-1/(60*30))
    environments, configs = [], []
    for gamma in (.99, candidate):
        settings = copy.deepcopy(song); settings['surface_approach_gamma'] = gamma
        env = ShortEnvironment(metadata, bundle=BUNDLE, song=settings, skill=skill, device='cpu')
        env.reset([0], snapshot)
        config = PPOConfig(**dict(baseline_ppo, gamma=gamma))
        assert env.approach_gamma == config.gamma
        assert env.contract['reward']['surface_learning']['approach_gamma'] == gamma
        assert config.cost_gamma == 1. and config.gae_lambda == .98
        environments.append(env); configs.append(config)
    contract_diff = differences(*(env.contract for env in environments))
    config_diff = differences(*(vars(config) for config in configs))
    assert {row['path'] for row in contract_diff} == {
        '.task.song.surface_approach_gamma', '.reward.surface_learning.approach_gamma'}
    assert [row['path'] for row in config_diff] == ['.gamma']
    trainers = [DecisionPPOTrainer(ShortPolicy(contract=env.contract, size='small'), config)
                for env, config in zip(environments, configs)]
    rejection = None
    with tempfile.TemporaryDirectory(prefix='guitar_gamma_contract_') as temporary:
        checkpoint = Path(temporary)/'baseline.pt'
        trainers[0].save(checkpoint)
        trainers[0].load(checkpoint)
        try:
            trainers[1].load(checkpoint)
        except ValueError as error:
            rejection = str(error)
        assert rejection is not None
    assert not torch.cuda.is_initialized()
    assert pins == {str(p): digest(p) for p in sources}
    result = dict(scope='CPU synthetic fixture/configuration guard only; no physical teacher validation or learning evidence',
        gamma_before=.99, gamma_candidate=candidate, tau_candidate_s=30,
        existing_configuration_sufficient=True, active_code_changed=False,
        contract_diff=contract_diff, ppo_config_diff=config_diff,
        cross_gamma_strict_resume_rejected=True, rejection=rejection,
        same_gamma_strict_resume_succeeded=True,
        cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES'], cuda_initialized=False,
        cost_gamma=1., gae_lambda=.98, input_sha256=pins, inputs_unchanged=True)
    (OUT/'time_scale_contract_check.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'input_sha256'}, indent=2))


if __name__ == '__main__':
    main()
