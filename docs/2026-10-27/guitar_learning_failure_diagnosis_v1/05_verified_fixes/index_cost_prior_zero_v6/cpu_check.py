"""실제 Python3.8 CPU에서 초기값·수집·GAE·학습·엄격 계약을 검사한다."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
import numpy as np
import torch
import runtime as rt
import learn
from guitar_learning.training.rollout import DecisionCollector, FIELDS
from guitar_learning.training.ppo import compute_decision_gae


def check():
    assert sys.version_info[:2] == (3,8)
    assert not torch.cuda.is_initialized() and not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    capture = rt.v5.SOURCE/'capture/runs/candidate'
    config = rt.settings(); config['device'] = 'cpu'
    data, buckets, phases, contract = learn.parent.dataset(capture,config)
    baseline_contract = rt.v5.attach(rt.base.read(capture/'training_contract.json'))
    learn.seed(); previous = rt.v5.GoalPolicy(contract=baseline_contract,size='large')
    previous_rng = torch.get_rng_state().clone()
    learn.seed(); own = rt.GoalPolicy(contract=contract,size='large')
    assert torch.equal(previous_rng,torch.get_rng_state())
    unequal = [k for k,v in own.state_dict().items() if not torch.equal(v,previous.state_dict()[k])]
    assert sorted(unequal) == sorted(rt.COST_PRIOR['tensors']) and len(own.state_dict()) == 71
    assert all(p.requires_grad for p in own.cost_critic.parameters())
    # 6구간의 실제 유효 관측을 사용하여 비용 예측과 행동의 동일성을 확인한다.
    index = np.concatenate([b[:8] for b in buckets])
    obs = {k:torch.as_tensor(data[k][index]) for k in FIELDS}
    inputs = [obs[k] for k in FIELDS]
    with torch.no_grad():
        outputs = own(*inputs)
        assert torch.count_nonzero(outputs['cost_value']).item() == 0
        for deterministic in (True,False):
            torch.manual_seed(73); actual = own.act(*inputs,deterministic=deterministic)
            torch.manual_seed(73); expected = previous.act(*inputs,deterministic=deterministic)
            for key in ('mean','log_std','latent','action','logp','reward_value'):
                assert torch.equal(actual[key],expected[key]), key
            a = own.evaluate(*inputs,actual['latent']); b = previous.evaluate(*inputs,actual['latent'])
            assert torch.equal(a['logp'],b['logp']) and torch.equal(a['entropy'],b['entropy'])
    class Pool:
        num_envs = len(index)
        observation = obs
        valid = True
        def step(self,action):
            z = torch.zeros(self.num_envs)
            return self.observation,z,z,torch.zeros_like(z,dtype=torch.bool),torch.zeros_like(z,dtype=torch.bool),[]
    batch, episodes = DecisionCollector(own,Pool()).collect(4)
    advantage, target = compute_decision_gae(batch['cost'],batch['cost_value'],batch['next_cost_value'],
        batch['terminated'],batch['truncated'],batch['duration'],batch['valid'],1.,.95)
    assert not torch.count_nonzero(advantage) and not torch.count_nonzero(target)
    # 양의 비용 target이 실제 head gradient와 갱신을 만든다.
    optimizer = torch.optim.SGD(own.value_parameters(),lr=.01)
    loss = (own(*inputs)['cost_value']-1).square().mean()
    optimizer.zero_grad(); loss.backward()
    gradients = [p.grad for p in own.cost_critic.parameters()]
    assert all(g is not None and torch.isfinite(g).all() and torch.count_nonzero(g) for g in gradients)
    optimizer.step()
    assert float((own(*inputs)['cost_value']-1).square().mean()) < float(loss)
    learn.seed(); own = rt.GoalPolicy(contract=contract,size='large')
    trainer = learn.DecisionPPOTrainer(own,learn.PPOConfig(**config['ppo']))
    assert trainer.cost_weight == 1.
    with tempfile.TemporaryDirectory(dir=str(rt.HERE)) as temp:
        path = Path(temp)/'own.pt'
        pins = {str(Path(__file__).resolve()):rt.base.sha(Path(__file__))}
        trainer.save(path,metadata=learn.metadata(config,pins))
        restored = learn.DecisionPPOTrainer(rt.GoalPolicy(contract=contract,size='large'),learn.PPOConfig(**config['ppo']))
        learn.load(restored,path,config)
        oldtrainer = learn.DecisionPPOTrainer(previous,learn.PPOConfig(**config['ppo']))
        oldtrainer.save(Path(temp)/'old.pt',metadata=dict(learn.metadata(config,pins),schema=rt.v5.SCHEMA))
        try: learn.load(restored,Path(temp)/'old.pt',config)
        except ValueError: pass
        else: raise AssertionError('V5 metadata admitted')
        try: restored.load(Path(temp)/'old.pt')
        except ValueError: pass
        else: raise AssertionError('V5 architecture/contract admitted')
    try: rt.GoalPolicy(contract=baseline_contract,size='large')
    except ValueError: pass
    else: raise AssertionError('V5 contract admitted')
    assert sys.modules['runtime'] is rt and learn.parent.rt is rt
    assert learn.parent.train.__globals__['rt'] is rt
    assert rt.GoalPool.environment_class_override is rt.v5.Environment
    assert rt.Environment is rt.v5.Environment
    import experiment as ex
    paths, aliases = list(sys.path), {name:sys.modules.get(name) for name in ('runtime','learn')}
    for fail in (False,True):
        try:
            with ex.local_modules(include_learn=True) as modules:
                assert modules['learn'].parent.rt is modules['runtime']
                if fail: raise RuntimeError('scoped import fixture')
        except RuntimeError as error: assert fail and str(error) == 'scoped import fixture'
        assert sys.path == paths and all(sys.modules.get(name) is old for name,old in aliases.items())
    original_here = ex.base.HERE
    with patch.object(ex.parent.parent,'capture_ready',return_value={}), patch.object(ex.parent,'gate',return_value={}), \
         patch.object(ex.base,'gate',side_effect=RuntimeError('gate fixture')):
        try: ex.gate()
        except RuntimeError as error: assert str(error) == 'gate fixture'
        else: raise AssertionError('gate error swallowed')
    assert ex.base.HERE == original_here
    import launch_training as launch
    import os
    for broken_record in (False,True):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp); (home/'runs/fit').mkdir(parents=True)
            (home/'runs/fit/fit.pt').write_bytes(b'fixture')
            rt.base.write(home/'runs/fit/initial_tensor_equality.json',{name:dict(full_model_exact=False,unchanged_tensor_count=69,zero_cost_head=True,tensor_count=71,controlled_differences=['cost_critic.bias','cost_critic.weight']) for name in ('fresh.pt','fit.pt')})
            class Child:
                pid, code, terminated = os.getpid(), None, False
                def poll(self): return self.code
                def wait(self): self.code = -15 if self.terminated else 0; return self.code
                def terminate(self): self.terminated = True
            child = Child()
            original_write = launch.ex.base.write
            def write(path,value):
                if broken_record and path.name == 'process.json': raise OSError('process audit fixture')
                return original_write(path,value)
            with patch.object(launch,'HERE',home), patch.object(launch.ex,'gate',lambda:{}), \
                 patch.object(launch.subprocess,'Popen',return_value=child) as popen, \
                 patch.object(launch.ex.base,'write',write):
                try: launch.main()
                except OSError as error: assert broken_record and str(error) == 'process audit fixture'
                else: assert not broken_record
                assert popen.call_count == 1
                assert popen.call_args.kwargs['start_new_session'] is True
                assert set(popen.call_args.kwargs['env']) <= set(launch.ENV_KEYS)
                lock = rt.base.read(home/'execution_training/launch_lock.json')
                assert lock['supervisor_pid'] == os.getpid() and lock['supervisor_start_ticks'] > 0
                result = rt.base.read(home/'execution_training/exit.json')
                assert result['process_terminal'] and not result['changed_inputs']
                assert result['returncode'] == (-15 if broken_record else 0)
                assert bool(result['failure']) == broken_record
                try: launch.main()
                except FileExistsError: pass
                else: raise AssertionError('Duplicate supervisor launched')
                assert popen.call_count == 1
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(CPU_only=True,native_runs=0,full_fit_steps=0,PPO_updates=0,
        python_version=sys.version.split()[0],interpreter=sys.executable,
        full_model_exact=False,unchanged_tensor_count=69,tensor_count=71,controlled_differences=unequal,
        constructor_RNG_exact=True,cost_prediction_zero_on_valid_six_phase_observations=True,
        actual_collector_and_GAE_zero_cost_advantage=True,actor_action_likelihood_exact=True,
        synthetic_positive_cost_finite_nonzero_head_gradient_and_learning=True,
        own_strict_roundtrip_V5_metadata_contract_architecture_rejected=True,
        V5_environment_and_settlement_reused=True,scoped_parent_import_alias_restored=True,paths_and_aliases_restored_on_errors=True,parent_gate_here_restored_on_error=True,
        supervisor_duplicate_lock_and_primary_failure_cleanup=True)


if __name__ == '__main__': print(json.dumps(check(),indent=2))
