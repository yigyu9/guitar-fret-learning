"""NoNN CPU math, active4 Gaussian, original callbacks and scope cleanup only."""
import ast
from contextlib import contextmanager,redirect_stderr
import hashlib
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def check(probe):
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import FIELDS
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    codec=probe.goal.support();extra=probe.parent.support();collector=probe.goal.source.source.support()
    folder=probe.goal.output('reference');saved=dict(np.load(folder/'goal_codec_env0.npz',allow_pickle=False));raw=torch.zeros(354,39);ids=[17,18,19,20];raw[:,ids]=torch.from_numpy(saved['raw_goal_normalized'])
    assert bool((raw[:,ids].abs()<1).all());frozen=raw.clone();std=probe.std4(raw)
    expected=probe.grid.read(probe.on.HERE/'cpu_verification.json')['std_override']['actual_effective_std4'];assert std.tolist()==expected
    with patch.object(torch.nn.Module,'__init__',side_effect=AssertionError('NN constructor forbidden')),patch.object(torch,'load',side_effect=AssertionError('Model load forbidden')):
        zero,residual=probe.perturb(raw,ids,torch.zeros(354,4));assert torch.allclose(zero[:,ids],raw[:,ids],rtol=0,atol=2*torch.finfo(raw.dtype).eps)
        bad=raw.clone();bad[0,17]=1
        try:probe.perturb(bad,ids,torch.zeros(354,4))
        except AssertionError:pass
        else:raise AssertionError('atanh endpoint admitted')
        torch.manual_seed(7);noise=torch.distributions.Normal(torch.zeros(128,4),std.expand(128,4)).sample();after=torch.get_rng_state()
        torch.manual_seed(7);full=torch.zeros(128,39);full[:,ids]=torch.distributions.Normal(torch.zeros_like(full[:,ids]),std.expand_as(full[:,ids])).sample()
        assert torch.equal(noise,full[:,ids]) and torch.equal(after,torch.get_rng_state());assert not full[:,[i for i in range(39) if i not in ids]].any()
        noisy,_=probe.perturb(raw[:128],ids,noise);assert torch.equal(noisy[:,[i for i in range(39) if i not in ids]],raw[:128,[i for i in range(39) if i not in ids]]) and torch.equal(raw,frozen)
    contract=probe.grid.read(folder/'training_contract.json');action=contract['action']['target_contract'];names=action['joint_names'];active=torch.tensor([names.index(n) for n in action['action_order']]);ref=torch.tensor(action['reference105_rad'])
    data=dict(np.load(folder/'observations4.npz',allow_pickle=False));obs={k:torch.from_numpy(data[k][:1].copy()).expand((128,)+data[k].shape[1:]).clone() for k in FIELDS}
    env=SimpleNamespace(clock=torch.zeros(128,dtype=torch.long),failure=torch.zeros(128,1,dtype=torch.bool),wrist_failure=torch.zeros(128,dtype=torch.bool),wrist_severe_failure=torch.zeros(128,dtype=torch.bool))
    pool=SimpleNamespace(num_envs=128,spec=contract['task']['short_learning'],environment=env,first=torch.ones(128,dtype=torch.bool),observation=obs,teacher_reference=ref[active],incremental_mask=torch.tensor([17<=i<33 for i in range(39)]),
        controller=SimpleNamespace(reference=ref,target=ref[None].repeat(128,1),active=active,action_low=torch.tensor(action['action_lower_rad']),action_high=torch.tensor(action['action_upper_rad'])))
    pool.scene=SimpleNamespace(target=pool.controller.target);pool.pending=dict(raw_target_rad=torch.zeros(128),final_target_rad=torch.zeros(128),current_goal=torch.full((128,),4))
    original_ref=extra.reference_action;prior=probe.parent.base.effort_scope;original_exec=codec.execution_scope;observed={};runner=SimpleNamespace(_evaluate=None)
    def reference(*a):observed['reference_calls']=observed.get('reference_calls',0)+1;return raw[:1].expand(128,39).clone()
    def evaluate(current,*unused):
        for _ in range(2):
            r=extra.reference_action(current,None);request,goal=codec.convert(current,r);rows=collector.before(current,request,'collect');env.clock+=4;current.last_executed_action=request
            assert len(collector.after(probe.goal,current,rows))==4
        raise ValueError('original evaluator primary')
    @contextmanager
    def fakecap(*a):yield runner
    @contextmanager
    def fakeexec(*a):
        previous=(extra.reference_action,probe.parent.base.effort_scope,runner._evaluate);extra.reference_action=reference;probe.parent.base.effort_scope=fakecap;runner._evaluate=evaluate
        try:yield
        finally:extra.reference_action,probe.parent.base.effort_scope,runner._evaluate=previous
    audit=dict(calls=0,RNG_advances=0,conversion_calls=0,stream=hashlib.sha256(),noise_rows=[],roundtrip_max_abs_raw=0.,epsilon_sum=np.zeros(4),epsilon_square_sum=np.zeros(4))
    aliases=(probe.goal.output,probe.goal.gate)
    with patch.object(codec,'execution_scope',fakeexec),patch.object(torch.nn.Module,'__init__',side_effect=AssertionError('NN constructor forbidden')),patch.object(torch,'load',side_effect=AssertionError('Model load forbidden')):
        try:
            with probe.execution_scope(({},set()),audit):
                with codec.execution_scope(probe.goal,'reference',{},set(),observed):
                    with probe.parent.base.effort_scope(set(),{}) as current:current._evaluate(pool,None,pool.spec,SimpleNamespace(control='reference',episodes=128),Path('/tmp/not-written'))
        except ValueError as error:assert str(error)=='original evaluator primary'
        else:raise AssertionError('Primary error lost')
    assert (probe.goal.output,probe.goal.gate)==aliases and codec.execution_scope is original_exec and extra.reference_action is original_ref and probe.parent.base.effort_scope is prior
    assert audit['calls']==audit['RNG_advances']==audit['conversion_calls']==observed['reference_calls']==2 and len(audit['noise_rows'])==8 and audit['callback_aliases_restored'] and audit['producer_aliases_restored']
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp);stat=out.stat();(out/'reference_noise4.npz').touch()
        for kind in ('existing','symlink'):
            target=out/kind
            if kind=='existing':target.mkdir()
            else:target.symlink_to(out/'absent')
            with patch.object(probe,'output',return_value=target),patch.object(probe,'gate',side_effect=AssertionError('late gate')) as gate:
                try:probe.launch()
                except FileExistsError:pass
                else:raise AssertionError('Existing output admitted')
                gate.assert_not_called()
        stderr=io.StringIO()
        with patch.object(probe,'output',return_value=out),patch.object(np,'savez_compressed',side_effect=ValueError('typed primary')),patch.object(probe.grid,'write',side_effect=OSError('report secondary')),redirect_stderr(stderr):
            try:probe.finish(audit,False,dict(type='ValueError',message='aborted'))
            except ValueError as error:assert str(error)=='typed primary'
            else:raise AssertionError('Typed primary lost')
        assert 'report secondary' in stderr.getvalue()
    static=probe.on.recovery.module('reference_noise_static',probe.on.recovery.HERE/'audit.py');unresolved={p.name:static.unresolved(p) for p in probe.HERE.glob('*.py')};assert not any(unresolved.values())
    for p in probe.HERE.glob('*.py'):ast.parse(p.read_text(),feature_version=(3,8))
    assert 'isaacgym' not in sys.modules and not torch.cuda.is_initialized()
    return dict(CPU_only=True,GPU_executed=False,NN_constructors=0,model_loads=0,Gaussian_shape=[128,4],effective_std4=std.tolist(),Normal_active4_RNG_exact=True,other35_action_columns_exact=True,
        saved_reference_rows=354,reference_raw_min4=raw[:,ids].amin(0).tolist(),reference_raw_max4=raw[:,ids].amax(0).tolist(),reference_abs_ge1=0,
        sigma0_roundtrip_max_abs_raw=float(residual.max()),reference_input_unchanged=True,original_before_after_callback_exact=True,conversion_once=True,seed_after_pool_ready=True,scope_alias_primary_exact=True,
        typed_primary_report_secondary_preserved=True,output_symlink_before_gate=True,symtable_referenced_globals=unresolved,
        scope='CPU noNN math and callback fixtures only; baseline saved reference reused, no model load/create or epsilon identity claim to unrecorded NN samples; native128/physics unverified')
