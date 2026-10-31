"""Meaningful checkpoint and optimizer checks; optional CUDA execution."""
import tempfile
from pathlib import Path
import numpy as np
import torch
from .joint_policy_v1 import JointActorCritic
from .deadline_ppo_v1 import DeadlinePPO, PPOConfig


def run(device='cpu'):
    torch.manual_seed(41)
    groups = ['body']*9+['head']*6+['arm']*24+['finger']*42
    model = JointActorCritic(820, groups).to(device)
    abi = {'observation': {'dimension': 820}, 'action_dimension': 81,
           'profile': 'test_only'}
    config = PPOConfig(epochs=2, minibatch_size=32)
    trainer = DeadlinePPO(model, abi, config)
    obs = torch.randn(64, 1, 820, device=device)
    sampled = model.sample(obs)
    reward = sampled['action'][..., 15]+torch.randn(64, 1, device=device)*.1
    batch = dict(obs=obs, **sampled, reward=reward,
                 next_value=torch.zeros(64, 1, device=device),
                 terminated=torch.zeros(64, 1, dtype=torch.bool, device=device),
                 truncated=torch.zeros(64, 1, dtype=torch.bool, device=device))
    batch['terminated'][-1] = True
    before = {k:v.clone() for k,v in model.state_dict().items()}
    update = trainer.update(batch)
    assert update['optimizer_steps'] > 0
    assert any(not torch.equal(v, before[k]) for k,v in model.state_dict().items() if 'actor' in k)
    assert any(not torch.equal(v, before[k]) for k,v in model.state_dict().items() if 'critic' in k)
    with tempfile.TemporaryDirectory() as folder:
        checkpoint = Path(folder)/'policy.pt'
        trainer.save(checkpoint)
        expected = model.sample(obs[:1])['latent']
        fresh = DeadlinePPO(JointActorCritic(820, groups).to(device), abi, config)
        fresh.load(checkpoint)
        actual = fresh.model.sample(obs[:1])['latent']
        assert torch.equal(expected, actual), 'RNG resume not exact'
        assert fresh.updates == trainer.updates and fresh.transitions == trainer.transitions
        assert all(torch.equal(v, fresh.model.state_dict()[k]) for k,v in model.state_dict().items())
        try: fresh.save(checkpoint)
        except FileExistsError: pass
        else: raise AssertionError('checkpoint overwritten')
        bad = DeadlinePPO(JointActorCritic(820, groups).to(device), dict(abi, profile='bad'), config)
        prior = bad.model.actor[-1].weight.clone()
        try: bad.load(checkpoint)
        except ValueError: pass
        else: raise AssertionError('ABI mismatch accepted')
        assert torch.equal(prior, bad.model.actor[-1].weight)
    print({'device': device, 'optimizer_steps': update['optimizer_steps'],
           'actor_and_critic_updated': True, 'RNG_resume_exact': True,
           'immutable_checkpoint': True, 'ABI_rejection_before_restore': True})


if __name__ == '__main__':
    import sys
    torch.set_num_threads(1)
    run(sys.argv[1] if len(sys.argv)>1 else 'cpu')
