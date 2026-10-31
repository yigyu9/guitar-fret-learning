"""CPU fixtures only: no native scene, no fitting, no PPO update."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0,str(ROOT))
spec = importlib.util.spec_from_file_location('reward_gradient_audit_fixture',HERE/'audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def check():
    import numpy as np
    import torch
    from guitar_learning.training.ppo import PPOConfig
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    torch.set_num_threads(1)
    torch.manual_seed(7)
    shape = (5,3)
    terms = torch.randn(*shape,9)
    buffer = dict(audit_terms=terms,reward=terms.sum(-1),cost=torch.rand(*shape),
        reward_value=torch.randn(*shape),next_reward_value=torch.randn(*shape),cost_value=torch.randn(*shape),
        next_cost_value=torch.randn(*shape),terminated=torch.zeros(shape,dtype=torch.bool),
        truncated=torch.zeros(shape,dtype=torch.bool),duration=torch.ones(shape,dtype=torch.long),
        valid=torch.ones(shape,dtype=torch.bool))
    buffer['terminated'][1,0] = True
    buffer['truncated'][2,1] = True
    buffer['valid'][-1,2] = False
    config = PPOConfig()
    components,advantage = audit.decompose(buffer,config,1.)
    torch.testing.assert_close(components.sum(0),advantage,rtol=3e-5,atol=3e-5)
    # Actual strict-loaded V6 network, original 557D observation fixtures, H2 gradient identity.
    exp = audit.experiment()
    with exp.local_modules(include_learn=True) as modules:
        rt,learn = modules['runtime'],modules['learn']
        impl = learn.parent
        settings = exp.base.read(audit.V6/'inputs/settings.json')
        contract = exp.base.read(audit.V6/'runs/fit/training_contract.json') if (audit.V6/'runs/fit/training_contract.json').exists() else None
        if contract is None:
            payload = torch.load(audit.CASES['fit'],map_location='cpu',weights_only=False)
            contract = payload['identity']['architecture']['contract']
        policy = rt.GoalPolicy(contract=contract,size=settings['size']).cpu()
        trainer = learn.DecisionPPOTrainer(policy,learn.PPOConfig(**settings['ppo']))
        try:
            learn.load(trainer,audit.CASES['fit'],settings)
        except ValueError as error:
            assert str(error) == 'CUDA RNG topology mismatch'
        else:
            raise AssertionError('CPU must reject GPU training resume')
        audit.cpu_load(trainer,audit.CASES['fit'],settings,learn,rt)
        capture = audit.V6.parent/'index_release_reference_learning_v4/capture/runs/candidate/observations4.npz'
        with np.load(capture,allow_pickle=False) as archive:
            inputs = {k:torch.from_numpy(archive[k][:6].copy()) for k in audit.FIELDS}
        with torch.no_grad(): result = policy.act(*(inputs[k] for k in audit.FIELDS))
        h,n = 2,3
        small = {k:v[:h].clone() for k,v in buffer.items()}
        small['audit_phase'] = torch.tensor([[0,1,2],[1,2,3]])
        small.update({k:v.reshape(h,n,*v.shape[1:]) for k,v in inputs.items()})
        for old,new in [('latent','latent'),('logp','logp'),('mean','old_mean'),('log_std','old_log_std')]:
            small[new] = result[old].reshape(h,n,*result[old].shape[1:])
        before = impl.fingerprint(trainer)
        rng = torch.get_rng_state().clone()
        accumulator = {}
        report = audit.gradient_report(policy,small,trainer.config,trainer.cost_weight,accumulator)
        aggregate = audit.aggregate_gradients(accumulator)
        assert before == impl.fingerprint(trainer) and torch.equal(rng,torch.get_rng_state())
        assert all(p.grad is None for p in policy.parameters())
    # Wrapper must restore inherited methods after an exception, and must clone term tensors.
    class Environment:
        def __init__(self):
            self.press = self.onset = self.end = torch.arange(9,dtype=torch.float64)
            self.clock = torch.zeros(3,dtype=torch.long)
            self.note = {k:torch.ones(3,9) for k in ('wrong_source_time','wrong_supported_time','wrong_ambiguous_time','wrong_next_preparation_time')}
            for k in ('wrong_source_flags','wrong_source_fret_min','wrong_source_fret_max','wrong_supported',
                      'wrong_ambiguous','wrong_next_preparation','contact_geometry','contact_facing',
                      'surface_body_loaded','candidate','wrong','surface_distance','surface_height'):
                setattr(self,k,torch.ones(3,9))
            self.components = {k:torch.ones(3) for k in audit.TERMS}
        def _score_time(self): return self.clock.double()/240
        def _local_time(self): return self._score_time()
        def _reward_components(self,components): return components
    class Pool:
        def __init__(self):
            self.environment = Environment()
            self.scene = SimpleNamespace(q=torch.zeros(3,105),target=torch.zeros(3,105))
        def step(self,action):
            result = self.environment._reward_components(self.environment.components)
            self.environment.clock += 4
            return None,sum(result.values()),None,None,None,[]
    pool = Pool()
    old = (pool.step,pool.environment._reward_components)
    try:
        with audit.capture(pool) as (rows,bounds):
            pool.step(torch.zeros(3,39))
            assert len(rows) == 1 and rows[0]['terms'].sum() == 27
            pool.environment.components[audit.TERMS[0]].zero_()
            pool.environment.note['wrong_source_time'].zero_()
            assert rows[0]['terms'].sum() == 27 and rows[0]['note_wrong_source_time'].sum() == 9
            raise RuntimeError('fixture')
    except RuntimeError: pass
    assert pool.step == old[0] and pool.environment._reward_components == old[1]
    assert 'step' not in pool.__dict__ and '_reward_components' not in pool.environment.__dict__
    paths,aliases = list(sys.path),{k:sys.modules.get(k) for k in ('runtime','learn')}
    try:
        with exp.local_modules(include_learn=True): raise RuntimeError('fixture')
    except RuntimeError: pass
    assert paths == sys.path and all(sys.modules.get(k) is v for k,v in aliases.items())
    fixture_rows = [dict(env_id=i,valid=True,notes=[dict(source_index=k) for k in (4,7,8)]) for i in range(128)]
    assert audit.first_attempts(fixture_rows) == 384
    for wrong in (fixture_rows[:-1],fixture_rows[:-1]+[fixture_rows[0]]):
        try: audit.first_attempts(wrong)
        except AssertionError: pass
        else: raise AssertionError('invalid denominator accepted')
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        evidence = root/'input'
        evidence.write_text('before')
        inputs = {str(evidence):audit.sha(evidence)}
        with audit.analysis_audit(root/'success',inputs): pass
        assert json.loads((root/'success/verification.json').read_text())['completed']
        try:
            with audit.analysis_audit(root/'mutation',inputs): evidence.write_text('changed')
        except RuntimeError: pass
        else: raise AssertionError('input mutation accepted')
        assert not json.loads((root/'mutation/verification.json').read_text())['completed']
        evidence.write_text('before')
        try:
            with audit.analysis_audit(root/'failure',inputs): raise ValueError('primary failure fixture')
        except ValueError as error: assert str(error) == 'primary failure fixture'
        else: raise AssertionError('primary exception lost')
        assert json.loads((root/'failure/verification.json').read_text())['failure']['type'] == 'ValueError'
        original_write = audit.write
        def broken_write(path,value):
            if Path(path).name == 'verification.json': raise OSError('secondary fixture')
            return original_write(path,value)
        audit.write = broken_write
        try:
            try:
                with audit.analysis_audit(root/'cleanup_failure',inputs): raise ValueError('preserved primary')
            except ValueError as error: assert str(error) == 'preserved primary'
            else: raise AssertionError('secondary cleanup replaced primary')
        finally: audit.write = original_write
    result = dict(CPU_only=True,GPU_executed=False,native_scene_created=False,fit_steps=0,PPO_updates=0,
        strict_V6_model_tensor_audit=True,CPU_trainer_resume_rejected=True,GAE_terminal_truncation_padding=True,joint_centered_components=True,
        full_actor_and_phase_gradient_identity=True,wrapper_exception_restoration=True,final_reward_and_ledger_clone=True,
        alias_exception_restoration=True,model_optimizer_parameter_grad_RNG_unchanged=True,gradient_fixture=report,weighted_aggregate_fixture=aggregate,denominator_reject_cases=2,analysis_success_failure_mutation_cleanup=True)
    audit.write(HERE/'cpu_verification.json',result)
    print(json.dumps(result,indent=2))

if __name__ == '__main__': check()
