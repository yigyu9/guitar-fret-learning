"""CPU checks of the new schema/goal/alias seams; no simulated native success."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def check(probe,config,metadata,env):
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    from guitar_learning.training.gpu_pool import GpuPool
    from guitar_learning.training import finger_skill_runner
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.core.control import ACTIVE_NAMES
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    extra=probe.support();_,snapshot=fixture(128);env.reset(list(range(128)),snapshot)
    assert env.M==67 and env.selected_indices==(4,7,8) and env.focus_mask[:,[4,7,8]].all() and env.focus_mask.sum()==384 and (env.duration_ticks==354).all()
    end=env.end[list(extra.INDICES)];score=torch.stack((end[0]-.01,end[0],end[1],end[2],end[0]-.2))
    column,present=extra.current_goal(score,end);assert column.tolist()==[0,1,2,0,0] and present.tolist()==[True,True,True,False,True]
    env.clock[:3]=torch.tensor([100,800,1300]);env.reset([1],snapshot)
    assert env.clock[:3].tolist()==[100,0,1300]
    # New policy contract is never disguised as the old short-task schema.
    contract=copy.deepcopy(env.contract)
    torch.manual_seed(7);plain=extra.PrefixPolicy(contract=contract,size='large',fresh=False);plain_rng=torch.get_rng_state().clone()
    torch.manual_seed(7);fresh=extra.PrefixPolicy(contract=contract,size='large',fresh=True);zero_rng=torch.get_rng_state().clone()
    a,b=plain.state_dict(),fresh.state_dict();changed=sorted(k for k in a if not torch.equal(a[k],b[k]))
    assert len(a)==len(b)==73 and changed==['cost_critic.bias','cost_critic.weight'] and torch.equal(plain_rng,zero_rng)
    assert all(not torch.count_nonzero(b[k]) for k in changed) and all(v.dtype==torch.float32 for v in fresh.parameters())
    baseline=torch.load(probe.B.checkpoint(0),map_location='cpu',weights_only=False)
    assert set(baseline['model'])==set(b) and all(torch.equal(v,baseline['model'][k]) for k,v in b.items())
    assert fresh._active_mask().nonzero().flatten().tolist()==[17,18,19,20]
    try:runtime.ShortPolicy(contract=contract,size='small')
    except ValueError:pass
    else:raise AssertionError('Old single schema accepted new prefix')
    bad=copy.deepcopy(contract);bad['task']['short_learning']['candidate_dip_guard']['source_indices']=[4]
    try:extra.PrefixPolicy(contract=bad,size='small')
    except ValueError:pass
    else:raise AssertionError('Wrong goal contract accepted')
    cfg=PPOConfig(**config['ppo']);t=DecisionPPOTrainer(fresh,cfg)
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        with torch.no_grad():fresh.cost_critic.bias.fill_(.125)
        t.save(root/'new.pt');loaded=extra.PrefixPolicy(contract=contract,size='large',fresh=False);other=DecisionPPOTrainer(loaded,cfg);other.load(root/'new.pt')
        assert torch.equal(loaded.cost_critic.bias,fresh.cost_critic.bias)
        try:other.load(probe.B.checkpoint(0))
        except ValueError as error:assert 'schema/architecture/input/control/config mismatch' in str(error)
        else:raise AssertionError('Old B task strict-loaded into prefix')
    del plain,loaded,other,t,fresh,a,b,baseline
    # Earliest goal gathered per row; lowlevel guard preserves negative and other104.
    target=torch.zeros(128,105);dip=metadata['joint_names'].index('LH:index3');target[:,dip]=.5
    active=torch.tensor([metadata['joint_names'].index(n) for n in ACTIVE_NAMES]);ai=20
    controller=SimpleNamespace(target=target,active=active,lower=torch.full((105,),-2.),upper=torch.full((105,),2.),
        action_low=torch.full((39,),-2.),action_high=torch.full((39,),2.),rate=torch.full((105,),4.))
    sample=dict(q=torch.zeros(128,105),qd=torch.zeros(128,105),body_state=torch.zeros(128,1,13),contact_force=torch.zeros(128,1,3),reset_body_snapshot=torch.zeros(128,dtype=torch.bool))
    now=torch.full((128,),float(end[0]-.01),dtype=end.dtype);now[1]=end[0];now[2]=end[1];now[3]=end[2]
    candidate=torch.zeros(128,67,dtype=torch.bool);candidate[:,4]=True;candidate[2,8]=True
    fake_env=SimpleNamespace(end=env.end,_score_time=lambda:now,candidate=candidate,wrong=torch.zeros_like(candidate),failure=torch.zeros_like(candidate),
        wrist_failure=torch.zeros(128,dtype=torch.bool),wrist_severe_failure=torch.zeros(128,dtype=torch.bool),clock=torch.zeros(128,dtype=torch.long))
    p=extra.LearningPool.__new__(extra.LearningPool);p.num_envs=128;p.controller=controller;p.scene=SimpleNamespace(device=torch.device('cpu'));p.environment=fake_env;p.dip=dip;p.ai=ai;p.first=torch.ones(128,dtype=torch.bool)
    def original(action,s):controller.target[:,dip]+=action[:,ai]*(4/60);controller.target[:,0]+=.001;return controller.target
    p.native_targets=original;action=torch.zeros(128,39);action[:,ai]=.25;action[2,ai]=-.25
    before=action.clone();p.targets(action,sample)
    assert p.pending['current_goal'][:4].tolist()==[4,7,8,-1] and p.pending['blocked'][:4].tolist()==[True,False,False,False]
    assert torch.equal(action,before) and not p.pending['other104_error_rad'].any()
    p.first.zero_();controller.target[:,dip]=.5;p.targets(action,sample)
    assert p.pending['blocked'][0] and not p.pending['first_attempt'].any()  # new episodes stay guarded after first audit quota
    # Real ShortPool.step mixes teacher only into unselected axes from tick0.
    p.spec=config['song']['short_learning'];p.teacher_reference=torch.zeros(39);p.teacher_final=torch.ones(39)*.1
    p.incremental_mask=torch.zeros(39,dtype=torch.bool);p.incremental_mask[17:33]=True
    p.learn_mask=torch.zeros(39,dtype=torch.bool);p.learn_mask[17:21]=True;p._wrist_feedback=lambda desired,fraction:desired
    p.environment._local_time=lambda:torch.zeros(128)
    with patch.object(GpuPool,'step',lambda self,a:a.clone()):
        executed=runtime.ShortPool.step(p,before)
    assert torch.equal(executed[:,17:21],before[:,17:21]) and torch.equal(p.last_policy_action,before)
    # Inherited real virtual reset is safe before first/guard counters exist.
    created=[];break_names=[False]
    def pool_init(self,config,out):
        self.closed=False;self.num_envs=128;self.spec=config['song']['short_learning'];self.initial_wrist_position=None;self.environment=env;self.contract=copy.deepcopy(env.contract)
        self.last_valid_efforts=torch.zeros(128,105)
        self.controller=SimpleNamespace(active=active,reference=torch.tensor(metadata['reference105']),target=snapshot['target'].clone(),rate=torch.full((105,),4.))
        self.controller.reset=lambda ids,s:None;self.controller.targets=lambda a,s:self.controller.target
        def close():
            self.native_closed=True
            if break_names[0]:raise RuntimeError('CPU close secondary')
        self.scene=SimpleNamespace(device=torch.device('cpu'),names=metadata['joint_names'],q=snapshot['q'],target=snapshot['target'],reset=lambda ids:snapshot,close=close)
        created.append(self);assert not hasattr(self,'first');self.reset()
        if break_names[0]:self.scene.names=[]
    assert 'reset' not in extra.LearningPool.__dict__
    with patch.object(extra.prefix.PrefixPool,'__init__',pool_init):
        initial=extra.LearningPool(config,None);initial.reset([1]);assert initial.wrist_correction.shape==(128,12);initial.close();assert initial.native_closed
        break_names[0]=True
        try:extra.LearningPool(config,None)
        except ValueError:pass
        else:raise AssertionError('Constructor name failure swallowed')
        assert created[-1].native_closed and created[-1].guard_cleanup_error['message']=='CPU close secondary'
    # Compact alias restores on success and error; original music and release gates separate.
    with patch.object(runner,'compact_episode',extra.compact_episode):
        def single(row,spec):return dict(target_id=spec['teacher']['source_target_id'],achieved=True,clean_fraction=1.,audible_wrong_fraction=0.,missing_fraction=0.,note={},env_id=0,termination=dict(physical_failure=False,wrist_failure=False))
        row=dict(prefix_release=dict(values=[dict(source_index=i,released=True,release_s=1.) for i in extra.INDICES]))
        with patch.object(extra,'SINGLE_COMPACT',single):compact=extra.compact_episode(row,p.spec)
        assert compact['selected_target_count']==3 and runner.compact_episode is extra.compact_episode
        with patch.object(extra,'SINGLE_COMPACT',side_effect=RuntimeError('CPU compact')):
            try:extra.compact_episode(row,p.spec)
            except RuntimeError:pass
            else:raise AssertionError('Compact error lost')
        assert runner.compact_episode is extra.compact_episode
    rows=[dict(copy.deepcopy(compact),env_id=i) for i in range(128)]
    full=probe.acceptance(rows);assert full['music_passed'] and full['release_passed'] and full['stage_ready']
    for r in rows:r['notes'][0]['released']=False
    split=probe.acceptance(rows);assert split['music_passed'] and not split['release_passed'] and not split['stage_ready']
    rows[0]['termination']['physical_failure']=True;assert not probe.acceptance(rows)['music_passed']
    # All old cap128 negatives are reused, not weakened; tests write only /tmp.
    cap_checks=probe.module('reused_index128_cap_checks',probe.B.BASE/'cpu_checks.py');declaration,cap_report=cap_checks.check(probe.base)
    assert cap_report
    # New outer aliases and the original cap scope restore even if renderer/runner fails.
    aliases=(runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy,runner.SCHEMA,runner.make_settings,runner.compact_episode,runner._evaluate,runner._pins,finger_skill_runner._pins)
    state={}
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp);cfgpath=out/'cpu_inputs';cfgpath.mkdir();probe.grid.write(cfgpath/'settings.json',config)
        with patch.object(probe,'HERE',out):
            try:
                with probe.execution_scope('precheck',{},set(),state):
                    s=dict(out=out,cleanup_errors=[])
                    with probe.base.effort_scope(set(),s) as current:
                        assert current.ShortPool is runtime.ShortPool and runner._pins is finger_skill_runner._pins
                        assert current.SCHEMA==extra.SCHEMA and extra.prefix.transition_fraction is extra.timing.wrist_weight
                        raise RuntimeError('CPU outer failure')
            except RuntimeError as error:assert str(error)=='CPU outer failure'
    assert state['aliases_restored'] and aliases==(runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy,runner.SCHEMA,runner.make_settings,runner.compact_episode,runner._evaluate,runner._pins,finger_skill_runner._pins)
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(CPU_only=True,GPU_executed=False,original67_focus3_clock_and_partialreset=True,current_goal_boundary_gap_none=True,
        new_policy_schema_no_legacy_bypass=True,state_tensor_count=73,equal_default_tensors=71,cost2zero_and_RNGsame=True,baseline_B_initial_model73exact=True,
        float32_initialization=True,same_contract_strictload_and_nonzero_head_preserved=True,old_B_strict_rejected=True,
        current_goal_filter_other104_negative_exact=True,training_guard_not_first_attempt_limited=True,NN_selected4_from_first_tick=True,
        real_virtual_ctor_reset_and_partialreset=True,ctor_primary_close_secondary_preserved=True,
        compact_nonrecursive_and_finally_restored=True,music_release_stage_separate=True,cap128_original_negative_checks=cap_report,
        outer_runtime_runner_two_pins_and_schema_aliases_restored=True,limits='CPU formulas/contracts only; no native128/release/music/learning/codec result certified')
