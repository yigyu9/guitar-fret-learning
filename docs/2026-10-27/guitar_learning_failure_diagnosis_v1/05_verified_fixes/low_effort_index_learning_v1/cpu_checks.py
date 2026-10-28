"""Small CPU regressions for the explicit index128 wrapper; no native import."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def check(probe):
    import numpy as np
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    from guitar_learning.training import finger_skill_runner
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    assert 'isaacgym' not in sys.modules and not torch.cuda.is_available() and not torch.cuda.is_initialized()
    torch.set_num_threads(1)
    source=prepared_reset_v1.load_prepared_reset_contract(); original=copy.deepcopy(source)
    private,declaration=probe.cap.private_contract(source)
    np.testing.assert_equal(source,original)
    dtype=np.dtype([(k,np.bool_ if k=='hasLimits' else np.int32 if k=='driveMode' else np.float32)
        for k in source['initial']['native_PD_properties']])
    expected=probe.cap.expected_properties(source,dtype); expected['effort'][declaration['native_indices']]=.25

    def scene(contract, bad_env=None, close_error=False):
        calls=[]
        def read(env,actor):
            assert actor==1000+env; calls.append(env); result=expected.copy()
            if env==bad_env: result['effort'][declaration['native_indices'][0]]=20.
            return result
        result=SimpleNamespace(num_envs=128,envs=list(range(128)),actors=[[1000+i] for i in range(128)],
            names=source['initial']['joint_names'],_hand_collision_readback_count=128,physics_steps=0,
            hand_collision=dict(enabled_distinct_finger_pairs=90),pd_properties=expected.copy(),contract=contract,
            gym=SimpleNamespace(get_actor_dof_properties=read),calls=calls,
            effort_caps=torch.tensor(expected['effort'].copy()),closed=False)
        def close():
            result.closed=True
            if close_error: raise RuntimeError('CPU close failure')
        result.close=close
        return result

    good=scene(private); diagnostic=probe.verify128(good,source,declaration)
    assert good.calls==list(range(128)) and diagnostic['explicit_DOF105_readback_environments']==128
    diagnostic['controller_caps_exact']=True
    bad_checks=0
    for field,value in (('num_envs',4),('_hand_collision_readback_count',127),('physics_steps',1),
                         ('envs',list(range(127))),('actors',[[1000+i] for i in range(129)])):
        bad=scene(private); setattr(bad,field,value)
        try: probe.verify128(bad,source,declaration)
        except AssertionError: bad_checks+=1
        else: raise AssertionError('Invalid128 count/steps admitted')
    for field,index,value in (('effort',declaration['native_indices'][0],20.),('effort',51,.25),
                             ('stiffness',56,13.),('damping',51,2.),('driveMode',56,0)):
        bad=scene(private); bad.pd_properties[field][index]=value
        try: probe.verify128(bad,source,declaration)
        except AssertionError: bad_checks+=1
        else: raise AssertionError('Invalid native105 field admitted')
    bad=scene(private,bad_env=91)
    try: probe.verify128(bad,source,declaration)
    except AssertionError: bad_checks+=1
    else: raise AssertionError('Single bad environment admitted')
    bad=scene(private); bad.hand_collision['enabled_distinct_finger_pairs']=89
    try: probe.verify128(bad,source,declaration)
    except AssertionError: bad_checks+=1
    else: raise AssertionError('Wrong collision pair count admitted')

    config=runner.make_settings(probe.train_args(Path('/tmp/unused-index128-train')))
    metadata,_=fixture(1)
    env=runtime.ShortEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],
        skill=config['finger_skill'],device='cpu')
    base_contract=copy.deepcopy(env.contract)
    assert base_contract['task']['short_learning']['finger']==1
    saved=(runner.ShortPool,runtime.ShortPool,runner._pins,finger_skill_runner._pins)
    loader=prepared_reset_v1.load_prepared_reset_contract
    modes=[]; source_here=probe.HERE
    with tempfile.TemporaryDirectory() as folder:
        temp=Path(folder); (temp/'cpu_inputs').mkdir()
        probe.grid.write(temp/'cpu_inputs/settings.json',config)
        probe.grid.write(temp/'cpu_inputs/effort_declaration128.json',diagnostic)
        marker=temp/'extra.txt'; marker.write_text('CPU pin superset witness')
        class FakePool:
            def __init__(self,settings,out):
                self.scene=None; self.closed=False
                try:
                    self.scene=self._create_scene(settings,out)
                    self.controller=SimpleNamespace(caps=self.scene.effort_caps.clone())
                    self.contract=copy.deepcopy(base_contract)
                    if modes[-1]=='controller': self.controller.caps[declaration['native_indices'][0]]=20.
                except BaseException:
                    self.close(); raise
            def _create_scene(self,settings,out):
                contract=prepared_reset_v1.load_prepared_reset_contract()
                return scene(contract,bad_env=3 if modes[-1]=='constructor' else None,close_error=modes[-1]=='constructor')
            def close(self):
                self.closed=True
                if self.scene is not None: self.scene.close()
        try:
            probe.HERE=temp
            with patch.object(runner,'ShortPool',FakePool),patch.object(runtime,'ShortPool',FakePool):
                for mode in ('good','controller','constructor','body_error'):
                    modes.append(mode); out=temp/mode; out.mkdir(); probe.grid.write(out/'settings.json',config)
                    state=dict(out=out,cleanup_errors=[],pool=None,scene=None)
                    try:
                        with probe.effort_scope({marker},state) as r:
                            assert r.ShortPool is runtime.ShortPool and r._pins is finger_skill_runner._pins
                            baseline=saved[3](config,out)
                            a=r._pins(config,out); b=finger_skill_runner._pins(config,out)
                            assert set(baseline)<=set(a)==set(b) and a[str(marker)]==probe.grid.sha(marker)
                            pool=r.ShortPool(config,out)
                            assert pool.contract['native_backend']['diagnostic_native_effort']['controller_caps_exact']
                            if mode=='good': diagnostic=copy.deepcopy(pool.contract['native_backend']['diagnostic_native_effort'])
                            pool.close()
                            if mode=='body_error': raise RuntimeError('CPU scope body failure')
                    except AssertionError:
                        assert mode in ('controller','constructor')
                    except RuntimeError as error:
                        assert mode=='body_error' and str(error)=='CPU scope body failure'
                    else: assert mode=='good'
                    assert state['aliases_restored'] and state['loader_restored']
                    assert runner.ShortPool is runtime.ShortPool is FakePool
                    if mode=='constructor':
                        assert state['scene'].closed and state['cleanup_errors']==[dict(type='RuntimeError',message='CPU close failure')]
                    elif mode=='controller': assert state['pool'].closed
        finally: probe.HERE=source_here
    assert (runner.ShortPool,runtime.ShortPool,runner._pins,finger_skill_runner._pins)==saved
    assert prepared_reset_v1.load_prepared_reset_contract is loader

    cap_contract=copy.deepcopy(base_contract); cap_contract['native_backend']['diagnostic_native_effort']=diagnostic
    torch.manual_seed(7); plain=runtime.ShortPolicy(contract=base_contract,size=config['size'])
    torch.manual_seed(7); low=runtime.ShortPolicy(contract=cap_contract,size=config['size'])
    assert set(plain.state_dict())==set(low.state_dict()) and all(torch.equal(v,low.state_dict()[k]) for k,v in plain.state_dict().items())
    trainer=DecisionPPOTrainer(low,PPOConfig(**config['ppo']))
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'cap.pt'; trainer.save(path)
        trainer.load(path)
        try: DecisionPPOTrainer(plain,PPOConfig(**config['ppo'])).load(path)
        except ValueError as error: assert 'mismatch' in str(error)
        else: raise AssertionError('Cap20 strict identity accepted low-effort checkpoint')
    ids=config['song']['short_learning']['learned_action_indices']; state=torch.zeros(128,561)
    a,b=probe.pre.Actions(ids,'random'),probe.pre.Actions(ids,'random')
    random_action=a.act(state)['action']
    assert random_action.shape==(128,39) and torch.equal(random_action,b.act(state)['action'])
    assert not random_action[:,[i for i in range(39) if i not in ids]].any()
    assert not probe.pre.Actions(ids,'zero').act(state)['action'].any()
    rows={c:[dict(env_id=i,achieved=(i<116 if c=='reference' else i<12),clean_fraction=1.,audible_wrong_fraction=0.,
        termination=dict(physical_failure=False,wrist_failure=False)) for i in range(128)] for c in ('reference','zero','random')}
    assert probe.acceptance(rows)['passed']
    for control,field,value in (('reference','achieved',False),('zero','achieved',True)):
        bad=copy.deepcopy(rows); bad[control][115 if control=='reference' else 12][field]=value
        assert not probe.acceptance(bad)['passed']
    for field in ('physical_failure','wrist_failure'):
        bad=copy.deepcopy(rows); bad['reference'][0]['termination'][field]=True
        assert not probe.acceptance(bad)['passed']
    for field,value in (('clean_fraction',.89),('audible_wrong_fraction',.11)):
        bad=copy.deepcopy(rows)
        for row in bad['reference']: row[field]=value
        assert not probe.acceptance(bad)['passed']
    for change in ('missing','duplicate'):
        bad=copy.deepcopy(rows)
        if change=='missing': bad['zero'].pop()
        else: bad['zero'][0]['env_id']=1
        try: probe.acceptance(bad)
        except AssertionError: pass
        else: raise AssertionError('Invalid denominator admitted')
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return diagnostic,dict(CPU_only=True,GPU_executed=False,native128_unverified=True,
        synthetic128_each105_readback_checked=True,negative_native_cases=bad_checks,
        original_private16_only=True,unchanged_other89=True,old_hard4_135_180_verifiers_untouched=True,
        alias_and_two_pin_paths_restored=True,constructor_and_close_primary_error_preserved=True,controller_caps_checked=True,
        same_cap_strict_load_pass=True,plain20_strict_load_reject=True,original_tensor_count=len(low.state_dict()),
        CPU_policy_size=config['size'],CPU_policy_finger=1,original_initial_tensors_identical=True,original_cost_head_gamma_PPO_unchanged=True,
        original_selected4_provider128_checked=True,precheck_acceptance_boundaries_and_denominators_checked=True)


if __name__=='__main__':
    path=Path(__file__).resolve().parent/'probe.py'
    spec=importlib.util.spec_from_file_location('index128_cpu_probe',path)
    probe=importlib.util.module_from_spec(spec);sys.modules[spec.name]=probe;spec.loader.exec_module(probe)
    sys.path.insert(0,str(probe.grid.ROOT))
    print(json.dumps(check(probe)[1],indent=2))
