"""CPU fixtures only, including exact V6/V7 actor construction and value gradient scope."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0,str(ROOT))
spec = importlib.util.spec_from_file_location('warmup_v7_experiment_fixture',HERE/'experiment.py')
ex = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ex
spec.loader.exec_module(ex)


def check():
    pins = ex.evidence()  # stdlib provenance before numerical imports.
    import numpy as np
    import torch
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    torch.set_num_threads(1)
    paths,aliases = list(sys.path),{k:sys.modules.get(k) for k in ('runtime','learn')}
    with ex.local_modules(include_learn=True) as modules:
        rt,learn = modules['runtime'],modules['learn']
        data,target = learn.dataset()
        assert target.shape == (354,128) and torch.isfinite(target).all()
        bad = [data[k].clone() for k in ('reward','terminated','truncated','valid')]
        for field,index in [(1,(0,0)),(2,(0,0)),(3,(0,0))]:
            changed = [v.clone() for v in bad]
            changed[field][index] = not bool(changed[field][index])
            try: learn.monte_carlo(*changed)
            except ValueError: pass
            else: raise AssertionError('Invalid MC masks accepted')
        short = [v[:-1] for v in bad]
        try: learn.monte_carlo(*short)
        except ValueError: pass
        else: raise AssertionError('Missing MC rows accepted')
        contract6 = ex.base.read(rt.SOURCE/'runs/ppo/training_contract.json')
        contract7 = rt.attach(contract6)
        learn.seed();old = rt.v6.GoalPolicy(contract=contract6,size='large').cpu()
        rng6 = torch.get_rng_state().clone()
        learn.seed();policy = rt.GoalPolicy(contract=contract7,size='large').cpu()
        assert torch.equal(rng6,torch.get_rng_state())
        assert old.state_dict().keys() == policy.state_dict().keys()
        assert all(torch.equal(v,policy.state_dict()[k]) for k,v in old.state_dict().items())
        inputs = [data[k][0,:6] for k in learn.FIELDS]
        rng = torch.get_rng_state().clone()
        with torch.no_grad():
            one = old.act(*inputs)
            torch.set_rng_state(rng)
            two = policy.act(*inputs)
        assert all(torch.equal(one[k],two[k]) for k in ('mean','log_std','latent','action','logp','reward_value','cost_value'))
        chosen = learn.selected_parameters(policy)
        assert chosen and all(n.startswith(('value_encoder.','reward_critic.')) for n in chosen)
        result = learn.value(policy,inputs)
        params = list(policy.named_parameters())
        grads = torch.autograd.grad((result-1).square().mean(),[p for n,p in params if p.requires_grad],allow_unused=True)
        assert all(g is None or n.startswith(('value_encoder.','reward_critic.')) for (n,p),g in zip([(n,p) for n,p in params if p.requires_grad],grads))
        output = policy(*inputs)
        cost_grad = torch.autograd.grad((output['cost_value']-1).square().mean(),list(policy.cost_critic.parameters()))
        assert any(bool(g.abs().sum() > 0) for g in cost_grad)
        trainer = learn.DecisionPPOTrainer(policy,learn.PPOConfig(**rt.settings()['ppo']))
        assert not trainer.actor_optimizer.state and not trainer.value_optimizer.state and trainer.updates == 0
        # Full CUDA resume must remain rejected on CPU; never disguise model reads as resume.
        try: trainer.load(rt.SOURCE/'runs/fit/fit.pt')
        except ValueError: pass
        else: raise AssertionError('V6 or CUDA resume unexpectedly accepted')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'incomplete.pt'
            torch.save(dict(metadata=learn.metadata(rt.settings(),pins,warmup_steps=0)),path)
            try: learn.ready(path)
            except ValueError: pass
            else: raise AssertionError('Incomplete warmup accepted')
        # A tiny independent fixture exercises the complete1000-step routine, not the actual NN.
        class Toy(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.value_encoder = torch.nn.Linear(1,1)
                self.reward_critic = torch.nn.Linear(1,1)
                self.cost_critic = torch.nn.Linear(1,1)
                self.actor = torch.nn.Parameter(torch.tensor(1.))
            def forward(self,*args):
                mean = self.actor.expand(len(args[0]),39)
                return dict(mean=mean,log_std=mean*0)
            def act(self,*args):
                r = self(*args);r['latent'] = r['mean']+torch.randn_like(r['mean'])
                r['action'] = r['latent'].tanh();r['logp'] = r['latent'].sum(-1)
                return r
        toy = Toy()
        # value_encoder accepts five fields in the real policy; toy only needs the state field.
        class ToyEncoder(torch.nn.Linear):
            def forward(self,state,*args): return super().forward(state)
        toy.value_encoder = ToyEncoder(1,1)
        toy_data = {k:torch.ones(354,128,1) for k in learn.FIELDS}
        toy_data['audit_phase'] = torch.arange(354)[:,None].expand(354,128)%10
        report,_,_ = learn.warmup(toy,toy_data,torch.ones(354,128,dtype=torch.float64),SimpleNamespace(value_lr=.01,max_grad_norm=.5))
        assert report['accepted'] and report['actor_std_costhead_exact'] and report['global_RNG_exact']
        assert all(n.startswith(('value_encoder.','reward_critic.')) for n in report['changed_tensor_names'])
    assert sys.path == paths and all(sys.modules.get(k) is v for k,v in aliases.items())
    try:
        with ex.local_modules(include_learn=True): raise RuntimeError('fixture')
    except RuntimeError: pass
    assert sys.path == paths and all(sys.modules.get(k) is v for k,v in aliases.items())
    assert all(ex.base.sha(p) == h for p,h in pins.items())
    result = dict(CPU_only=True,GPU_executed=False,native_runs=0,actual_NN_fit_steps=0,PPO_updates=0,
        actual_fit_dataset_MC_checked=True,invalid_MC_cases=4,initial_V6_V7_all71_tensors_rng_outputs_exact=True,
        value_gradient_scope_exact=True,positive_cost_gradient_preserved=True,incomplete_warmup_rejected=True,
        old_checkpoint_resume_rejected=True,PPO_optimizers_initially_empty=True,toy_fixed1000_warmup=report,
        aliases_restored_on_exception=True,verified_input_count=len(pins))
    ex.base.write(HERE/'cpu_verification.json',result)
    print(json.dumps(dict(CPU_only=True,passed=True,pins=len(pins))))

if __name__ == '__main__': check()
