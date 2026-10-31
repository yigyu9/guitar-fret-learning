"""CPU-only toy fixtures for original Normal sampling and observer lifecycle; no actual model."""
import copy
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0,str(ROOT))
spec = importlib.util.spec_from_file_location('private_noise_observer_fixture',HERE/'experiment.py')
ex = importlib.util.module_from_spec(spec);sys.modules[spec.name] = ex;spec.loader.exec_module(ex)


def check():
    pins = ex.evidence()  # Parent903 SHA proof before numerical imports.
    import numpy as np
    import torch
    from torch.distributions import Normal
    from guitar_learning.training.policy import FingerSkillPolicy
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    torch.set_num_threads(1)
    contract = dict(schema='guitar_learning.wrong_press_sources.v2',causes=ex.CAUSES)
    ledger = dict(schema='guitar_learning.surface_note_ledger.v8',target_ids=list(range(9)),required_clean_s=[.1]*9,
        values={k:[0.]*9 for k in ('wrong','wrong_supported_time','wrong_ambiguous_time','wrong_next_preparation_time',*[c+'_time' for c in ex.CAUSES])},
        wrong_press_sources=dict(contract=contract,body_names=ex.BODIES,target_strings_1based=[1]*9,
            values=dict(wrong_source_time=np.zeros((9,10,3)).tolist(),wrong_source_fret_min=np.zeros((9,10),dtype=int).tolist(),wrong_source_fret_max=np.zeros((9,10),dtype=int).tolist())))
    raw = dict(env_id=0,steps=1,left_note_ledger=ledger)
    ex.validate_raw_ledger(raw)
    for mutation in ('schema','causes','bodies','missing'):
        wrong = copy.deepcopy(raw);source = wrong['left_note_ledger']['wrong_press_sources']
        if mutation == 'schema': source['contract']['schema'] = 'v1'
        elif mutation == 'causes': source['contract']['causes'] = ['higher','lower','assignment']
        elif mutation == 'bodies': source['body_names'] = list(reversed(ex.BODIES))
        else: del source['values']['wrong_source_time']
        try: ex.validate_raw_ledger(wrong)
        except (ValueError,KeyError): pass
        else: raise AssertionError('Invalid raw source ledger accepted')
    class ToyPolicy(torch.nn.Module):
        def __init__(self):
            super().__init__();self.weight = torch.nn.Parameter(torch.ones(1))
        def _active_mask(self):
            mask = torch.zeros(39,dtype=torch.bool);mask[17:21] = True;return mask
        def forward(self,state,*unused):
            mean = state.new_zeros((128,39))
            return dict(mean=mean,log_std=mean-.4)
        act = FingerSkillPolicy.act
        log_probability = FingerSkillPolicy.log_probability
    class ParentPool:
        def step(self,action):
            self.calls += 1;self.environment.clock += 4
            identity = self.calls-1
            self.first[identity] = False
            self.last_raw = dict(env_id=identity,steps=self.calls,left_note_ledger=copy.deepcopy(ledger))
            return self.environment.clock,None,None,None,None,[self.last_raw]
    class Pool(ParentPool):
        def __init__(self):
            self.calls = 0;self.first = torch.ones(128,dtype=torch.bool)
            self.environment = SimpleNamespace(clock=torch.zeros(128,dtype=torch.long),press=torch.arange(9).double(),
                onset=torch.arange(9).double()+.1,end=torch.arange(9).double()+.8,string=torch.zeros(9,dtype=torch.long),
                fret=torch.ones(9,dtype=torch.long),finger=torch.ones(9,dtype=torch.long))
            self.environment._score_time = lambda:self.environment.clock.double()/240.+2.
            self.contract = dict(diagnostics=dict(wrong_press=contract))
    rt = SimpleNamespace(GoalPolicy=ToyPolicy,GoalPool=Pool)
    inputs = (torch.zeros(128,1),None,None,None,None)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(7);reference = ToyPolicy()
        expected = [reference.act(*inputs)['latent'][:,17:21].clone() for _ in range(2)]
    original_factory,original_step = rt.GoalPolicy,rt.GoalPool.step
    cpu_rng = torch.get_rng_state().clone();np_rng = np.random.get_state();python_rng = random.getstate()
    sample_shapes = []
    original_sample = Normal.sample
    def sample(distribution,*args,**kwargs):
        sample_shapes.append(list(distribution.loc.shape));return original_sample(distribution,*args,**kwargs)
    state = {}
    with patch.object(Normal,'sample',sample):
        with ex.observe(rt,7,state):
            p = rt.GoalPolicy();pool = rt.GoalPool();torch.manual_seed(7)
            for tick in range(2):
                result = p.act(*inputs,deterministic=False)
                np.testing.assert_array_equal(result['latent'][:,17:21].detach().numpy(),expected[tick].numpy())
                returned = pool.step(result['action'])
                assert returned[-1][0] is pool.last_raw
            pool.last_raw['left_note_ledger']['values']['wrong'][0] = 999.
            assert state['raw_ledgers'][-1]['left_note_ledger']['values']['wrong'][0] == 0.
            assert state['actor_rows'][0]['env_id'].shape == (128,) and state['actor_rows'][1]['env_id'].shape == (127,)
            assert 0 not in state['actor_rows'][1]['env_id'] and sample_shapes == [[128,4],[128,4]]
    assert rt.GoalPolicy is original_factory and rt.GoalPool.step is original_step and 'step' not in rt.GoalPool.__dict__
    assert 'act' not in p.__dict__ and state['step_calls'] == pool.calls == state['act_calls'] == 2
    assert torch.equal(cpu_rng,torch.get_rng_state()) and random.getstate() == python_rng
    restored = np.random.get_state();assert np_rng[0] == restored[0] and np.array_equal(np_rng[1],restored[1]) and np_rng[2:] == restored[2:]
    # A second independent private17 stream changes samples, without changing global RNG.
    with ex.observe(rt,17,{}) as other:
        p17 = rt.GoalPolicy();torch.manual_seed(7);r17 = p17.act(*inputs,deterministic=False)
    assert not torch.equal(r17['latent'][:,17:21],expected[0]) and torch.equal(cpu_rng,torch.get_rng_state())
    # No sampling occurs for mean actions, but the same original bound method is delegated.
    with patch.object(Normal,'sample',side_effect=AssertionError('mean must not draw')):
        with ex.observe(rt,None,{}):
            mean = rt.GoalPolicy();torch.manual_seed(7);result = mean.act(*inputs,deterministic=True)
            assert torch.equal(result['latent'],result['mean'])
    # Reject a shifted first seed7 boundary; do not merely relabel a different stream.
    try:
        with ex.observe(rt,7,{}):
            shifted = rt.GoalPolicy();torch.manual_seed(7);torch.rand(1)
            shifted.act(*inputs,deterministic=False)
    except ValueError: pass
    else: raise AssertionError('Wrong post-load seed7 boundary accepted')
    assert torch.equal(cpu_rng,torch.get_rng_state())
    # Constructor, bound-act and inherited-step failures preserve the primary error and restore hooks/RNG.
    sentinel = RuntimeError('primary fixture')
    class BrokenPolicy(ToyPolicy):
        def act(self,*args,**kwargs):
            torch.rand(3);raise sentinel
    for failure in ('factory','act','step'):
        if failure == 'factory':
            def broken_factory(*args,**kwargs): raise sentinel
            fixture_rt = SimpleNamespace(GoalPolicy=broken_factory,GoalPool=Pool)
        elif failure == 'act': fixture_rt = SimpleNamespace(GoalPolicy=BrokenPolicy,GoalPool=Pool)
        else:
            class BrokenPool(Pool):
                def step(self,*args,**kwargs): raise sentinel
            fixture_rt = SimpleNamespace(GoalPolicy=ToyPolicy,GoalPool=BrokenPool)
        old_factory,old_step = fixture_rt.GoalPolicy,fixture_rt.GoalPool.step
        had_step = 'step' in fixture_rt.GoalPool.__dict__
        try:
            with ex.observe(fixture_rt,7,{}):
                broken = fixture_rt.GoalPolicy();torch.manual_seed(7)
                value = broken.act(*inputs,deterministic=False)
                fixture_rt.GoalPool().step(value['action'])
        except RuntimeError as error: assert error is sentinel
        else: raise AssertionError('Primary exception lost')
        assert fixture_rt.GoalPolicy is old_factory and fixture_rt.GoalPool.step is old_step
        assert ('step' in fixture_rt.GoalPool.__dict__) == had_step and torch.equal(cpu_rng,torch.get_rng_state())
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        try: ex.invariance_gate(root)
        except FileNotFoundError: pass
        else: raise AssertionError('Missing det/private7 gate accepted')
    assert all(ex.sha(p) == h for p,h in pins.items())
    assert 'isaacgym' not in sys.modules and not torch.cuda.is_initialized()
    return dict(CPU_only=True,GPU_runs=0,native_runs=0,checkpoint_loads=0,actual_NN_constructors=0,fit_steps=0,PPO_updates=0,
        parent_reviewed_input_count=len(pins),original_bound_Normal_sample_shape=sample_shapes,actual_FingerSkillPolicy_act_code_used_without_model=True,wrong_seed7_boundary_rejected=True,private7_two_tick_samples_exact=True,
        private_noise_continuity_without_reseed=True,private17_different=True,mean_no_sample=True,
        global_Torch_numpy_python_RNG_restored=True,original_factory_step_and_inherited_act_restored=True,
        first_mask_before_original_step=True,completed_rows_still_full128_noise_draws=True,raw_ledger_deepcopy_before_reset=True,
        raw_v2_shape_cause_body_and_missing_field_rejections=4,primary_factory_act_step_errors_preserved=True,
        missing_baseline_invariance_gate_rejected=True)

if __name__ == '__main__':
    result = check();ex.write(HERE/'cpu_verification.json',result);print(json.dumps(result))
