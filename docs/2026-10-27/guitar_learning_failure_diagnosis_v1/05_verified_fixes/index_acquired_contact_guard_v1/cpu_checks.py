"""Small synthetic checks of memory/target seam and original alias lifecycle."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def check(probe):
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runtime
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    extra=probe.parent.support();N=8;dip=20
    def create():
        end=torch.zeros(67);end[list(probe.INDICES)]=torch.tensor([3.,4.,5.])
        env=SimpleNamespace(end=end,_score_time=lambda:torch.tensor([2.,2.,2.,2.,2.,2.,5.,3.]),clock=torch.zeros(N,dtype=torch.long),
            candidate=torch.zeros(N,67,dtype=torch.bool),wrong=torch.zeros(N,67,dtype=torch.bool),failure=torch.zeros(N,67,dtype=torch.bool),
            wrist_failure=torch.zeros(N,dtype=torch.bool),wrist_severe_failure=torch.zeros(N,dtype=torch.bool))
        env.candidate[:,4]=True;env.candidate[1,4]=False;env.candidate[1,7]=True;env.candidate[7,7]=True;env.wrong[2,4]=True;env.failure[5,4]=True
        ctl=SimpleNamespace(target=torch.full((N,105),.5),lower=torch.full((105,),-2.),upper=torch.full((105,),2.),
            action_low=torch.full((39,),-2.),action_high=torch.full((39,),2.),rate=torch.full((105,),4.))
        snap=dict(q=torch.zeros(N,105),qd=torch.zeros(N,105),body_state=torch.zeros(N,1,13),contact_force=torch.zeros(N,1,3),reset_body_snapshot=torch.zeros(N,dtype=torch.bool))
        snap['reset_body_snapshot'][3]=True;snap['q'][4,0]=float('nan')
        pool=SimpleNamespace(num_envs=N,scene=SimpleNamespace(device=torch.device('cpu')),environment=env,controller=ctl,dip=dip,ai=dip,
            acquired=torch.zeros(N,3,dtype=torch.bool),first=torch.ones(N,dtype=torch.bool),pending=None,native_calls=0)
        pool.acquired[6,0]=True
        def native(action,snapshot):
            pool.native_calls+=1;ctl.target[:,dip]=(ctl.target[:,dip]+action[:,dip]*(4/60)).clamp(-2,2);ctl.target[:,0]+=.001;return ctl.target
        pool.native_targets=native
        return pool,snap
    def original(pool,action,snapshot):
        env=pool.environment;col,present=extra.current_goal(env._score_time(),env.end[list(probe.INDICES)]);rows=torch.arange(N)
        goal=col.new_tensor(probe.INDICES)[col];failed=env.failure.any(-1)|env.wrist_failure|env.wrist_severe_failure
        target,pool.pending=probe.parent.guard.target_filter(pool.controller,pool.native_targets,action,snapshot,torch.ones(N,dtype=torch.bool),
            env.candidate[rows,goal]&present,env.wrong[rows,goal],failed,pool.dip,pool.ai,True)
        pool.pending.update(first_attempt=pool.first.clone(),current_goal=torch.where(present,goal,-torch.ones_like(goal)),start_clock=env.clock.clone())
        return target
    action=torch.zeros(N,39);action[:,dip]=.3
    baseline,s=create();direct,ds=create();out=probe.filtered_targets(baseline,action,s,probe.MODES[0],original,extra);ref=original(direct,action,ds)
    assert torch.equal(out,ref) and baseline.native_calls==direct.native_calls==1
    for k,v in direct.pending.items():assert torch.equal(v,baseline.pending[k]),k
    p,s=create();old=p.controller.target.clone();out=probe.filtered_targets(p,action,s,probe.MODES[1],original,extra);r=p.pending
    assert out.data_ptr()==p.controller.target.data_ptr() and p.native_calls==1
    assert r['blocked'].tolist()==[True,False,False,False,False,False,True,True]
    assert p.acquired.tolist()==[[True,False,False],[False,False,False],[False,False,False],[False,False,False],[False,False,False],[False,False,False],[True,False,False],[False,True,False]]
    assert r['memory_extended_block'].tolist()==[False]*6+[True,False]
    assert not r['other104_error_rad'].any() and not r['memory_error_rad'].any()
    assert torch.equal(out[:,0],old[:,0]+.001)
    # Goal moves to B while only the formerly acquired A is valid; future-only B never acquired before current.
    p.environment._score_time=lambda:torch.full((N,),3.)
    out=probe.filtered_targets(p,action,s,probe.MODES[1],original,extra);assert p.acquired[0,0] and p.acquired[1,1]
    p.environment.wrong[0,4]=True;p.environment.candidate[6,4]=False
    probe.filtered_targets(p,action,s,probe.MODES[1],original,extra);assert not p.acquired[0].any() and not p.acquired[6].any()
    # Negative/zero passes even under memory gate; unsafe/reset clear acquired memory.
    p,s=create();p.acquired[:]=True;action[:,dip]=torch.tensor([-.3,0.,.3,.3,.3,.3,-.3,.3]);old=p.controller.target.clone()
    out=probe.filtered_targets(p,action,s,probe.MODES[1],original,extra)
    assert torch.equal(out[:2,dip],old[:2,dip]+action[:2,dip]*(4/60)) and not p.acquired[2:6].any()
    assert all(v.shape==(N,) for v in p.pending.values()),'Parent scalar-only sidecar incompatible'
    for bound,sign in ((2.,1.),(-2.,-1.)):
        p,s=create();p.controller.target[:,dip]=bound;action[:,dip]=sign
        out=probe.filtered_targets(p,action,s,probe.MODES[1],original,extra)
        assert (out[:,dip]==bound).all() and not p.pending['blocked'].any() and not p.pending['box_rate_excess_rad'].any()
    # Exercise the observer subclass's virtual reset, sidecar naming and finally restoration without native.
    created=[]
    class ToyPool:
        def __init__(self,*args):
            q,self.snapshot=create();self.__dict__.update(q.__dict__);del self.acquired
            self.guard_rows=[];self.reset();created.append(self)
        def reset(self,indices=None):
            ids=list(range(N)) if indices is None else indices;self.environment.clock[ids]=0;return 'reset'
        def targets(self,action,snapshot):return original(self,action,snapshot)
        def step(self,action):
            self.targets(action,self.snapshot);self.environment.clock+=4
            self.guard_rows.append({k:v.detach().numpy().copy() for k,v in self.pending.items()});return 'step'
        def close(self):self.closed=True
    runner=SimpleNamespace(ShortPool=ToyPool,_evaluate=lambda *a:None,DecisionPPOTrainer=lambda *a:None)
    old=(runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer);audit={}
    with probe.observer_scope(runner,probe.MODES[1],audit):
        q=runner.ShortPool(None,None);assert not q.acquired.any();q.acquired[:]=True;q.reset([1]);assert q.acquired[0].all() and not q.acquired[1].any()
        action.zero_();q.step(action);assert 'effective_candidate' in q.guard_rows[-1] and 'candidate' not in q.guard_rows[-1]
        assert all(v.shape==(N,) for v in q.guard_rows[-1].values())
    assert (runner.ShortPool,runtime.ShortPool,runner._evaluate,runner.DecisionPPOTrainer)==old and audit['observer_aliases_restored']
    # Primary evaluation/allocation errors survive secondary fingerprint/close errors.
    audit={};runner._evaluate=lambda *a:(_ for _ in ()).throw(RuntimeError('evaluation primary'))
    with patch.object(probe.parent.guard,'fingerprints',side_effect=[{'model':'same'},RuntimeError('fingerprint secondary')]):
        with probe.observer_scope(runner,probe.MODES[1],audit):
            runner.DecisionPPOTrainer()
            try:runner._evaluate(None,None,None,None,None)
            except RuntimeError as error:assert str(error)=='evaluation primary'
            else:raise AssertionError('Evaluation primary swallowed')
    assert audit['cleanup_errors'][0]['message']=='fingerprint secondary' and audit['observer_aliases_restored']
    closed=[]
    class BarePool:
        def __init__(self,*a):self.num_envs=N;self.scene=SimpleNamespace(device=torch.device('cpu'))
        def close(self):closed.append(True);raise RuntimeError('close secondary')
    runner.ShortPool=BarePool;audit={}
    with probe.observer_scope(runner,probe.MODES[1],audit),patch.object(torch,'zeros',side_effect=RuntimeError('memory primary')):
        try:runner.ShortPool(None,None)
        except RuntimeError as error:assert str(error)=='memory primary'
        else:raise AssertionError('Memory primary swallowed')
    assert closed==[True] and audit['cleanup_errors'][0]['message']=='close secondary' and audit['observer_aliases_restored']
    # Output refusal occurs before gate/native import and leaves existing bytes untouched.
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);folder=root/'runs'/probe.MODES[0];folder.mkdir(parents=True);sentinel=folder/'sentinel';sentinel.write_bytes(b'unchanged')
        with patch.object(probe,'HERE',root),patch.object(probe,'gate',side_effect=AssertionError('Gate reached')) as called:
            try:probe.launch(probe.MODES[0])
            except FileExistsError:pass
            else:raise AssertionError('Existing output admitted')
            assert not called.called and sentinel.read_bytes()==b'unchanged'
            link=root/'runs'/probe.MODES[1];link.symlink_to(root/'absent',target_is_directory=True)
            try:probe.launch(probe.MODES[1])
            except (FileExistsError,ValueError):pass
            else:raise AssertionError('Dangling symlink admitted')
            assert not called.called and link.is_symlink()
    # Native current checkpoint is not loaded through a relaxed contract or new tag.
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    config=probe.parent.settings();payload=torch.load(probe.parent.checkpoint(300),map_location='cpu',weights_only=False)
    policy=extra.PrefixPolicy(contract=payload['identity']['architecture']['contract'],size=config['size'],fresh=False)
    assert DecisionPPOTrainer(policy,PPOConfig(**config['ppo']))._identity()==payload['identity'];policy.load_state_dict(payload['model'],strict=True)
    assert len(payload['model'])==73 and all(torch.equal(v,payload['model'][k]) for k,v in policy.state_dict().items())
    assert 'isaacgym' not in __import__('sys').modules
    return dict(CPU_only=True,GPU_executed=False,memory_future_current_transition_wrong_none_unsafe=True,
        baseline_original_function_exact=True,codec_once_alias_bounds_rate_negative_zero_other104=True,
        virtual_partial_reset_scalar_sidecar_finally=True,existing_output_and_symlink_before_gate_preserved=True,
        primary_evaluation_and_constructor_errors_preserved=True,
        original_checkpoint73_identity_and_model_values=True,model_only_CPU_not_full_native_trainer_load=True)
