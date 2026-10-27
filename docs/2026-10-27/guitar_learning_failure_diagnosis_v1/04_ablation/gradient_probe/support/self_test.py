"""CPU-only independent boundary expectations and surrogate-gradient additivity."""
import json
from pathlib import Path

import torch
from torch import nn

from probe_math import decompose, gradient_probe, check_close
from guitar_learning.training.decision_ppo import compute_decision_gae
from guitar_learning.training.ppo import PPOConfig


class ToyPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.head = nn.Linear(3, 4)
        self.log_std = nn.Parameter(torch.full((4,), -.8))

    def actor_parameters(self):
        return list(self.parameters())

    def evaluate(self, state, events, mask, priority_events, priority_mask, latent):
        mean = self.head(state)
        logp = torch.distributions.Normal(mean, self.log_std.exp()).log_prob(latent).sum(-1)
        return dict(logp=logp)


def run():
    torch.set_num_threads(1)
    torch.manual_seed(20261027)
    # A true terminal removes bootstrap and carry; truncation keeps bootstrap but cuts carry.
    reward = torch.tensor([[1.], [2.], [3.], [4.]], dtype=torch.float64)
    value = torch.tensor([[.1], [.2], [.3], [.4]], dtype=torch.float64)
    nxt = torch.tensor([[.2], [10.], [.4], [.5]], dtype=torch.float64)
    term = torch.tensor([[False], [True], [False], [False]])
    trunc = torch.tensor([[False], [False], [True], [False]])
    duration = torch.ones(4,1,dtype=torch.long)
    valid = torch.ones(4,1,dtype=torch.bool)
    actual = compute_decision_gae(reward,value,nxt,term,trunc,duration,valid,.9,.8)[0]
    expected = torch.tensor([[1+.9*.2-.1+.9*.8*(2-.2)], [2-.2],
                             [3+.9*.4-.3], [4+.9*.5-.4]], dtype=torch.float64)
    # Production's scalar ** integer-tensor powers use float32 even with float64 values.
    boundary = check_close(actual,expected,atol=1e-7,rtol=1e-7)
    t,n=6,3
    pieces=torch.randn(t,n,9)*.03
    b=dict(reward=pieces.sum(-1), cost=torch.rand(t,n)*.02,
        reward_value=torch.randn(t,n)*.2,next_reward_value=torch.randn(t,n)*.2,
        cost_value=torch.randn(t,n)*.2,next_cost_value=torch.randn(t,n)*.2,
        terminated=torch.zeros(t,n,dtype=torch.bool),truncated=torch.zeros(t,n,dtype=torch.bool),
        valid=torch.ones(t,n,dtype=torch.bool),duration=torch.ones(t,n,dtype=torch.long))
    b['terminated'][2,0]=True;b['truncated'][3,1]=True
    b['next_reward_value'][b['terminated']]=0;b['next_cost_value'][b['terminated']]=0
    config=PPOConfig(gae_lambda=.98)
    decomposition=decompose(b,pieces,config,1.)
    # A zero raw cost does not erase the fixed critic residual.
    zero_cost={**b,'cost':torch.zeros_like(b['cost'])}
    cost_residual=decompose(zero_cost,pieces,config,1.)
    assert bool((cost_residual['cost_gae'].abs()>0).any())
    constant={**b,'reward':torch.zeros_like(b['reward']),'cost':torch.zeros_like(b['cost']),
        **{k:torch.zeros_like(b[k]) for k in ('reward_value','next_reward_value','cost_value','next_cost_value')}}
    constant_result=decompose(constant,torch.zeros_like(pieces),config,1.)
    assert bool((constant_result['normalized']==0).all())
    policy=ToyPolicy()
    b['state']=torch.randn(t,n,3)
    for key in ('events','priority_events'):b[key]=torch.zeros(t,n,1,1)
    for key in ('mask','priority_mask'):b[key]=torch.ones(t,n,1,dtype=torch.bool)
    with torch.no_grad():
        b['latent']=policy.head(b['state'])+torch.randn(t,n,4)*policy.log_std.exp()
        b['logp']=policy.evaluate(b['state'].flatten(0,1),None,None,None,None,b['latent'].flatten(0,1))['logp'].reshape(t,n)
    width=sum(p.numel() for p in policy.parameters())
    before={k:v.clone() for k,v in policy.state_dict().items()}
    groups={'all':torch.arange(width)}
    gradient=gradient_probe(policy,b,decomposition,groups,clip_ratio=.2,chunk_size=5)
    whole=gradient_probe(policy,b,decomposition,groups,clip_ratio=.2,chunk_size=18)
    chunk_check=check_close(torch.tensor(gradient['groups']['all']['component_norm']),
        torch.tensor(whole['groups']['all']['component_norm']),atol=1e-6,rtol=1e-6)
    assert all(torch.equal(v,before[k]) for k,v in policy.state_dict().items())
    assert all(p.grad is None for p in policy.parameters())
    # Ragged valid prefixes/durations exercise the same decomposition independently of K1 driver checks.
    ragged={**b,'valid':b['valid'].clone(),'duration':b['duration'].clone()}
    ragged['valid'][4:,2]=False;ragged['duration'][1,0]=3
    ragged_result=decompose(ragged,pieces,config,1.)
    return dict(completed=True,gpu_used=False,boundary_expectations=boundary,
        gae_checks=decomposition['checks'],gradient=gradient,chunked_vs_whole_norms=chunk_check,
        ragged_duration_checks=ragged_result['checks'],zero_cost_critic_residual_nonzero=True,
        constant_zero_variance_normalized_zero=True,model_unchanged=True,parameter_grad_buffers_unchanged=True,
        scope='synthetic CPU arithmetic and Gaussian surrogate only; no native geometry/rollout evidence')


if __name__=='__main__':
    result=run()
    destination=Path(__file__).resolve().parents[1]/'cpu_self_test.json'
    destination.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2,allow_nan=False))
