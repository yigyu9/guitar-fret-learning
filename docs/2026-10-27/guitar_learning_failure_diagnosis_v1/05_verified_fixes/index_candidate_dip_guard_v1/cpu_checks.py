"""Small CPU regressions of the real DIP hook, first-attempt mask and alias scope."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import sys


def check(probe):
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    torch.set_num_threads(1)
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    n,dip,ai=10,3,3
    target=torch.zeros(n,105);target[:,dip]=.5
    c=SimpleNamespace(target=target,lower=torch.full((105,),-2.),upper=torch.full((105,),2.),
        action_low=torch.full((39,),-2.),action_high=torch.full((39,),2.),active=torch.arange(39),rate=torch.full((105,),4.))
    s=dict(q=torch.zeros(n,105),qd=torch.zeros(n,105),body_state=torch.zeros(n,1,13),contact_force=torch.zeros(n,1,3),reset_body_snapshot=torch.zeros(n,dtype=torch.bool))
    first=torch.ones(n,dtype=torch.bool);candidate=torch.ones(n,dtype=torch.bool);wrong=torch.zeros_like(first);failed=torch.zeros_like(first)
    first[6]=False;candidate[3]=False;wrong[4]=True;s['reset_body_snapshot'][5]=True;failed[7]=True;s['q'][8,0]=float('nan')
    action=torch.zeros(n,39);action[:,dip]=.4;action[1,dip]=-.4;action[2,dip]=0
    def original(a,snapshot):
        c.target[:,0]+=.001
        c.target[:,dip]=(c.target[:,dip]+a[:,ai]*(4/60)).clamp(c.lower[dip],c.upper[dip]);return c.target
    before=action.clone();q_before=s['q'].clone();old=c.target.clone()
    raw,row=probe.target_filter(c,original,action,s,first,candidate,wrong,failed,dip,ai,True)
    assert raw.data_ptr()==c.target.data_ptr() and row['blocked'].tolist()==[True,False,False,False,False,False,False,False,False,True]
    assert torch.equal(c.target[:,0],old[:,0]+.001)
    assert c.target[0,dip]==old[0,dip] and c.target[1,dip]<old[1,dip]
    assert torch.equal(action,before) and torch.equal(torch.isnan(s['q']),torch.isnan(q_before))
    assert torch.equal(torch.nan_to_num(s['q']),torch.nan_to_num(q_before))
    assert not row['other104_error_rad'].any() and not row['memory_error_rad'].any()
    # Live off/on: suppressed increments are discarded, never caught up later.
    c.target.fill_(0);s['q'].zero_();s['reset_body_snapshot'].zero_();first.fill_(True);failed.zero_();wrong.zero_();action.fill_(0);action[:,dip]=.5
    for active in (True,False,True):
        candidate.fill_(active);probe.target_filter(c,original,action,s,first,candidate,wrong,failed,dip,ai,True)
    assert torch.allclose(c.target[:,dip],torch.full((n,),.5*(4/60)))
    # Passthrough, native upper/zero increment, and negative opening at that upper.
    candidate.fill_(True);probe.target_filter(c,original,action,s,first,candidate,wrong,failed,dip,ai,False)
    assert torch.allclose(c.target[:,dip],torch.full((n,),1.*(4/60)))
    c.target[:,dip]=2.;raw,row=probe.target_filter(c,original,action,s,first,candidate,wrong,failed,dip,ai,True);assert not row['blocked'].any()
    action[:,dip]=-.5;raw,row=probe.target_filter(c,original,action,s,first,candidate,wrong,failed,dip,ai,True);assert (raw[:,dip]<2).all() and not row['blocked'].any()
    def no_alias(a,snapshot):return original(a,snapshot).clone()
    try:probe.target_filter(c,no_alias,action,s,first,candidate,wrong,failed,dip,ai,True)
    except ValueError:pass
    else:raise AssertionError('Non-alias native target accepted')
    # Observer scope must restore the current runner/runtime aliases on body error.
    aliases=(runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer)
    audit=dict(rows=[])
    try:
        with probe.observer_scope(runner,probe.MODES[1],audit):
            assert runner.ShortPool is runtime.ShortPool and runner.ShortPool is not aliases[0]
            raise RuntimeError('CPU observer body error')
    except RuntimeError as error:assert str(error)=='CPU observer body error'
    assert aliases==(runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer) and audit['observer_aliases_restored']
    # Real nested Pool.step with scalar synthetic scene: no native simulator.
    class FakePool:
        def __init__(self,config,out):
            self.num_envs=128;self.calls=0;self.corrupt=None
            self.spec=dict(finger=1,mode='incremental',learned_action_names=['a','b','c','LH:index3'],learned_action_indices=[0,1,2,3],view=dict(duration_ticks=3))
            self.contract=dict(observation=dict(fields=['target_error.LH:index3']))
            target=torch.zeros(128,105)
            self.controller=SimpleNamespace(target=target,active=torch.arange(39),rate=torch.full((105,),4.),lower=torch.full((105,),-2.),upper=torch.full((105,),2.),action_low=torch.full((39,),-2.),action_high=torch.full((39,),2.))
            names=['q'+str(i) for i in range(105)];names[3]='LH:index3'
            target[:,3]=.5
            self.scene=SimpleNamespace(device=torch.device('cpu'),names=names,target=target.clone(),q=torch.zeros_like(target));self.scene.q[:,3]=.15
            self.environment=SimpleNamespace(selected_index=0,candidate=torch.ones(128,1,dtype=torch.bool),wrong=torch.zeros(128,1,dtype=torch.bool),failure=torch.zeros(128,1,dtype=torch.bool),wrist_failure=torch.zeros(128,dtype=torch.bool),wrist_severe_failure=torch.zeros(128,dtype=torch.bool),clock=torch.zeros(128,dtype=torch.long),scales=torch.ones(1))
            self.scene.snapshot=lambda:dict(q=self.scene.q,qd=torch.zeros_like(target),body_state=torch.zeros(128,1,13),contact_force=torch.zeros(128,1,3),reset_body_snapshot=torch.zeros(128,dtype=torch.bool))
            def native(a,snapshot):
                self.controller.target[:,3]+=a[:,3]*(4/60);return self.controller.target
            self.controller.targets=native
        def step(self,a):
            self.calls+=1;t=self.controller.targets(a,self.scene.snapshot());self.scene.target=t.clone();self.environment.clock+=4
            if self.corrupt=='submit':self.scene.target[:,3]+=.1
            done=[dict(env_id=0)] if self.calls==1 else [dict(env_id=0),dict(env_id=1)] if self.calls==2 else []
            if self.calls==2:self.environment.failure[1,0]=True
            return dict(state=(t[:,3]-self.scene.q[:,3])[:,None]+(1 if self.corrupt=='observation' else 0)),None,None,None,None,done
        def close(self):pass
    audit=dict(rows=[])
    with patch.object(runner,'ShortPool',FakePool),patch.object(runtime,'ShortPool',FakePool):
        with probe.observer_scope(runner,probe.MODES[1],audit):
            pool=runner.ShortPool({},None);a=torch.zeros(128,39);a[:,3]=.5
            for _ in range(3):pool.step(a)
            assert audit['rows'][0]['first_attempt'].all()
            assert not audit['rows'][1]['first_attempt'][0] and audit['rows'][1]['first_attempt'][1] and audit['rows'][1]['post_failure'][1]
            assert not audit['rows'][2]['first_attempt'][:2].any()
            assert not audit['rows'][2]['old_target_rad'][:2].any()  # retry values masked, never counted
            assert all(not r['submit_error_rad'].any() and not r['observation_error'].any() for r in audit['rows'])
            try:pool.step(a)
            except ValueError:pass
            else:raise AssertionError('Tick budget bypassed')
            assert pool.calls==3
    for corrupt in ('submit','observation'):
        with patch.object(runner,'ShortPool',FakePool),patch.object(runtime,'ShortPool',FakePool):
            with probe.observer_scope(runner,probe.MODES[1],dict(rows=[])):
                pool=runner.ShortPool({},None);pool.corrupt=corrupt
                try:pool.step(torch.zeros(128,39))
                except ValueError as error:assert 'Scene/observation' in str(error)
                else:raise AssertionError('Wrong submitted target/observation accepted')
    class BadPool:
        def __init__(self,*args):self.num_envs=127
        def close(self):raise RuntimeError('CPU close error')
    audit=dict(rows=[])
    with patch.object(runner,'ShortPool',BadPool),patch.object(runtime,'ShortPool',BadPool):
        with probe.observer_scope(runner,probe.MODES[1],audit):
            try:runner.ShortPool({},None)
            except AssertionError:pass
            else:raise AssertionError('Original constructor error masked')
    assert audit['cleanup_errors'][0]['message']=='CPU close error'
    # Exercise the real launch finally without native import or a scene.
    outer=(probe.B.base.output,probe.B.base.checkpoint,probe.B.base.HERE,probe.B.base.gate,probe.B.base.effort_scope)
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);out=root/'runs'/probe.MODES[0];out.mkdir(parents=True);(out/'keep').write_bytes(b'unchanged')
        with patch.object(probe,'HERE',root),patch.object(probe,'gate',side_effect=AssertionError('Must reject before gate')):
            try:probe.launch(probe.MODES[0])
            except FileExistsError:pass
            else:raise AssertionError('Existing output accepted')
            assert (out/'keep').read_bytes()==b'unchanged'
            (out/'keep').unlink();out.rmdir();out.symlink_to(root/'missing')
            try:probe.launch(probe.MODES[0])
            except (ValueError,FileExistsError):pass
            else:raise AssertionError('Dangling output accepted')
            out.unlink()
        def fail(*args):raise RuntimeError('CPU original evaluator error')
        with patch.object(probe,'HERE',root),patch.object(probe,'gate',return_value=({},set())),patch.object(probe.B.base,'launch',fail),patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}):
            try:probe.launch(probe.MODES[0])
            except RuntimeError as error:assert str(error)=='CPU original evaluator error'
            else:raise AssertionError('Original exception suppressed')
    assert outer==(probe.B.base.output,probe.B.base.checkpoint,probe.B.base.HERE,probe.B.base.gate,probe.B.base.effort_scope)
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(CPU_only=True,GPU_executed=False,positive_only_blocked=True,negative_zero_unblocked=True,other104_exact=True,
        live_gate_no_backlog=True,invalid_reset_failure_retry_passthrough=True,alias_memory_rate_range=True,input_immutable=True,
        observer_and_outer_aliases_restored=True,scene_observation_exact=True,first_attempt_failure_endpoint_and_retry_mask=True,constructor_and_close_errors_preserved=True,output_and_symlink_rejected_before_gate=True,original_error_preserved=True,
        limits='No native scene, B policy evaluation or actual outcome certified')
