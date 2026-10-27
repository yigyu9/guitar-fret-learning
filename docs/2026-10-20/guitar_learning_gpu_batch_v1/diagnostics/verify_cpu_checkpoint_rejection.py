"""Check that equal-dimensional historical CPU physics cannot strict-resume."""
import argparse
import json
from pathlib import Path
import torch
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.training.ppo import PPOTrainer, PPOConfig

parser = argparse.ArgumentParser()
parser.add_argument('cpu_checkpoint', type=Path)
parser.add_argument('gpu_contract', type=Path)
parser.add_argument('out', type=Path)
args = parser.parse_args()
old = torch.load(args.cpu_checkpoint, map_location='cpu', weights_only=False)
architecture = old['identity']['architecture']
contract = json.loads(args.gpu_contract.read_text())
# Match the historical PPO config deliberately: only the new contracts differ.
policy = SpecialistPolicy(architecture['state_dim'], size=architecture['size'],
    contract=contract, role=architecture['role'], frozen_partner=False)
trainer = PPOTrainer(policy, PPOConfig(**old['identity']['config']))
try:
    trainer.load(args.cpu_checkpoint)
except ValueError as error:
    result = dict(passed=True, message=str(error), state_dim=architecture['state_dim'],
        same_model_size=architecture['size'], ppo_config_matches=True,
        cpu_native_backend=architecture['contract'].get('native_backend'),
        gpu_native_backend=contract.get('native_backend'),
        cpu_checkpoint=str(args.cpu_checkpoint.resolve()), gpu_contract=str(args.gpu_contract.resolve()))
else:
    result = dict(passed=False, message='Unexpected CPU physics checkpoint acceptance')
with args.out.open('x') as stream:
    json.dump(result, stream, indent=2)
print(json.dumps({k:result[k] for k in ('passed','message')}, indent=2))
raise SystemExit(not result['passed'])
