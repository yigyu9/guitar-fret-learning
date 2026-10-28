"""Selected4 goal output, explicit affine/inverse-codec layer; native codec unchanged."""
import copy
from contextlib import contextmanager
import random
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
from guitar_learning.training.decision_ppo import DecisionPPOTrainer
from guitar_learning.training.ppo import PPOConfig

ADAPTER=dict(schema='diagnostic.index_prefix_goal_codec.v1',selected_actions=[17,18,19,20],
    raw_output='tanh(mean) normalized absolute goal; sign selects035-reference side of full native range',
    affine='goal=reference+where(raw>=0,upper-reference,reference-lower)*raw',
    inverse='original trajectory_actions goal,current_target,incremental max_speed4; physical request then original controller/guard',
    unchanged='native incremental codec/rate4/range/PD/cap.25/physics/rewards; adapter other35 action columns exact; original DIP guard other104 target columns unchanged',
    exploration='same numerical std is not equal physical exploration; deterministic evaluation only')


def attach(contract):
    result=copy.deepcopy(contract);result['action']['policy_output_adapter']=copy.deepcopy(ADAPTER)
    result['task']['short_learning']['policy_output_adapter']=copy.deepcopy(ADAPTER)
    return result


def policy_type(probe):
    class GoalPolicy(probe.parent.support().PrefixPolicy):
        schema='diagnostic.index_prefix_goal_policy.v1'
        def __init__(self,*,contract,size='large',fresh=False):
            if contract['action'].get('policy_output_adapter')!=ADAPTER or contract['task']['short_learning'].get('policy_output_adapter')!=ADAPTER:
                raise ValueError('Explicit goal output layer required; incremental identity is incompatible')
            super().__init__(contract=contract,size=size,fresh=fresh)
    return GoalPolicy


def bounds(pool):
    c=pool.controller;ids=pool.spec['learned_action_indices']
    return c.reference[c.active][ids],c.action_low[ids],c.action_high[ids]


def encode(desired,reference,low,high):
    delta=desired-reference;span=torch.where(delta>=0,high-reference,reference-low)
    return torch.where(span>0,delta/span.clamp_min(1e-30),torch.zeros_like(delta))


def decode(raw,reference,low,high):
    if not torch.isfinite(raw).all() or bool((raw.abs()>1).any()):raise ValueError('Finite normalized goal in[-1,1] required')
    return reference+torch.where(raw>=0,high-reference,reference-low)*raw


def desired_reference(probe,pool,reference):
    # Exact original reference schedule; desired before the inverse codec, not inferred from saturated actions.
    extra=probe.parent.support();fraction=((pool.environment._local_time()+1/60)/reference['ramp_s']).clamp(0,1).to(pool.teacher_reference)
    goal=pool.teacher_reference.clone()
    from guitar_learning.core.control import ACTIVE_NAMES
    for name,value in reference['selected_targets_rad'].items():goal[ACTIVE_NAMES.index(name)]=value
    desired=pool.teacher_reference+fraction[:,None]*(goal-pool.teacher_reference)
    schedule=pool.spec['reference_release_schedule'];ids=pool.spec['learned_action_indices']
    weight=extra.timing.negative_weight(pool.environment._local_time()+1/60,pool.spec['view']).to(desired)
    desired[:,ids]+=weight[:,None]*(desired.new_tensor(schedule['negative_selected_rad'])-desired.new_tensor(schedule['reference_selected_rad']))
    return desired


def convert(pool,raw):
    ids=pool.spec['learned_action_indices'];reference,low,high=bounds(pool)
    desired=pool.teacher_reference.expand(len(raw),-1).clone();goal=decode(raw[:,ids],reference,low,high);desired[:,ids]=goal
    c=pool.controller
    request=runtime.trajectory_actions(desired,c.target[:,c.active],pool.teacher_reference,c.action_low,c.action_high,pool.incremental_mask,max_speed=4.)
    result=raw.to(c.target).clone();result[:,ids]=request[:,ids]
    return result,goal


def dataset(probe):
    source=probe.source.source;data=dict(np.load(probe.source.COLLECT/'observations4.npz',allow_pickle=False));short=probe.parent.settings()['song']['short_learning']
    buckets=source.support().validate_data(data,short,source)
    contract=probe.grid.read(probe.source.COLLECT/'training_contract.json')['action']['target_contract']
    names=contract['joint_names'];active=torch.tensor([names.index(n) for n in contract['action_order']]);ids=short['learned_action_indices']
    ref=torch.tensor(contract['reference105_rad'],dtype=torch.float32);low=torch.tensor(contract['action_lower_rad']);high=torch.tensor(contract['action_upper_rad'])
    target=ref[None].repeat(len(data['clock']),1);target[:,active[ids]]=torch.from_numpy(data['old_target_rad'])
    mask=torch.zeros(39,dtype=torch.bool);mask[17:33]=True
    pool=SimpleNamespace(spec=short,teacher_reference=ref[active],incremental_mask=mask,
        controller=SimpleNamespace(reference=ref,target=target,active=active,action_low=low,action_high=high),
        environment=SimpleNamespace(_local_time=lambda:torch.from_numpy(data['start_clock']).to(torch.float64)/240.))
    reference=runner.read_reference(probe.parent.base.pre.INPUTS['index'][1],short)
    desired=desired_reference(probe,pool,reference)
    original=probe.parent.support().reference_action(pool,reference)[:,ids]
    replay=runtime.trajectory_actions(desired,target[:,active],ref[active],low,high,mask,max_speed=4.)[:,ids]
    np.testing.assert_array_equal(replay.numpy(),data['requested_reference_action']);assert torch.equal(replay,original)
    labels=encode(desired[:,ids],*bounds(pool));raw=torch.zeros(len(labels),39);raw[:,ids]=labels
    request,decoded=convert(pool,raw)
    evidence=dict(source_requested_reference_bitexact=True,rows=len(labels),goal_label_source='planned desired(t+1/60), original schedule before inverse codec; no saturated-action inversion',
        desired_roundtrip_max_abs_rad=float((decoded-desired[:,ids]).abs().max()),request_roundtrip_max_abs=float((request[:,ids]-original).abs().max()),
        request_roundtrip_exact=torch.equal(request[:,ids],original),label_min=float(labels.min()),label_max=float(labels.max()))
    return data,buckets,labels,attach(probe.grid.read(probe.source.COLLECT/'training_contract.json')),evidence


@contextmanager
def execution_scope(probe,stage,seal,paths,observed):
    extra=probe.parent.support();old_output=(probe.parent.base.output,probe.parent.base.checkpoint)
    try:
        with probe.parent.execution_scope('precheck' if stage=='reference' else 'evaluate',seal,paths,observed):
            original=probe.parent.base.effort_scope
            @contextmanager
            def scoped_cap(evidence,state):
                with original(evidence,state) as current:
                    old=(current.ShortPool,runtime.ShortPool,current.ShortPolicy,runtime.ShortPolicy,current.SCHEMA,extra.reference_action,current._evaluate,current.DecisionPPOTrainer)
                    trainers=[];GoalPolicy=policy_type(probe)
                    class Pool(old[0]):
                        def __init__(self,config,out):
                            super().__init__(config,out)
                            try:self.contract=attach(self.contract)
                            except BaseException:
                                try:self.close()
                                except BaseException as error:observed.setdefault('cleanup_errors',[]).append(dict(type=type(error).__name__,message=str(error)))
                                raise
                        def step(self,raw):
                            request,goal=convert(self,raw)
                            record=probe.source.source.support().before(self,request,'collect' if stage=='reference' else 'evaluate')
                            selected=self.spec['learned_action_indices'];record['raw_goal_normalized']=raw[:4,selected].detach().cpu().numpy().copy()
                            record['decoded_goal_rad']=goal[:4].detach().cpu().numpy().copy()
                            result=super().step(request)
                            observed['records'].extend(probe.source.source.support().after(probe,self,record))
                            return result
                    def policy(*,contract,size):
                        value=GoalPolicy(contract=contract,size=size,fresh=False);observed['NN_constructors']=observed.get('NN_constructors',0)+1;return value
                    def reference(pool,value):
                        observed['reference_calls']+=1
                        if stage!='reference':raise RuntimeError('Reference goal injection in NN-only evaluation')
                        desired=desired_reference(probe,pool,value);c=pool.controller
                        raw=runtime.trajectory_actions(desired,c.target[:,c.active],pool.teacher_reference,c.action_low,c.action_high,pool.incremental_mask,max_speed=4.)
                        raw[:,pool.spec['learned_action_indices']]=encode(desired[:,pool.spec['learned_action_indices']],*bounds(pool))
                        return raw
                    def trainer(*args,**kwargs):
                        value=old[7](*args,**kwargs);trainers.append(value);return value
                    def evaluate(pool,policy,spec,args,out):
                        before=None if stage=='reference' else probe.parent.guard.fingerprints(policy,trainers[0]);primary=None
                        try:return old[6](pool,policy,spec,args,out)
                        except BaseException as error:primary=error;raise
                        finally:
                            if before is not None:
                                try:
                                    observed['policy_before']=before;observed['policy_after']=probe.parent.guard.fingerprints(policy,trainers[0]);assert observed['policy_after']==before
                                except BaseException as error:
                                    if primary is None:raise
                                    observed.setdefault('cleanup_errors',[]).append(dict(type=type(error).__name__,message=str(error)))
                    current.ShortPool=runtime.ShortPool=Pool;current.ShortPolicy=runtime.ShortPolicy=policy;current.SCHEMA=probe.SCHEMA
                    extra.reference_action=reference;current._evaluate=evaluate;current.DecisionPPOTrainer=trainer
                    try:yield current
                    finally:
                        current.ShortPool,runtime.ShortPool,current.ShortPolicy,runtime.ShortPolicy,current.SCHEMA,extra.reference_action,current._evaluate,current.DecisionPPOTrainer=old
                        observed['goal_aliases_restored']=(current.ShortPool,runtime.ShortPool,current.ShortPolicy,runtime.ShortPolicy,current.SCHEMA,extra.reference_action,current._evaluate,current.DecisionPPOTrainer)==old
            probe.parent.base.effort_scope=scoped_cap
            probe.parent.base.output=lambda *args,**kwargs:probe.output(stage)
            probe.parent.base.checkpoint=lambda update:probe.output('fit')/'initial.pt'
            observed.update(records=[],reference_calls=0)
            try:yield
            finally:probe.parent.base.effort_scope=original
    finally:probe.parent.base.output,probe.parent.base.checkpoint=old_output


def finish(probe,stage,out,observed,completed,failure):
    state=observed.get('state',{});pool=state.get('pool');probe.cap.owned(out,state['identity'])
    rows=observed.get('records',[])
    if rows:
        with (out/'observations4.npz').open('xb') as f:np.savez_compressed(f,**{k:np.asarray([r[k] for r in rows]) for k in rows[0]})
        env0=[r for r in rows if r['env_id']==0]
        with (out/'goal_codec_env0.npz').open('xb') as f:np.savez_compressed(f,**{k:np.asarray([r[k] for r in env0]) for k in ('start_clock','clock','raw_goal_normalized','decoded_goal_rad','requested_reference_action' if stage=='reference' else 'requested_NN_action','old_target_rad','final_target_rad','raw_DIP_target_rad','final_DIP_target_rad','current_goal')})
    if pool is not None and pool.guard_rows:
        with (out/'current_goal_DIP60.npz').open('xb') as f:np.savez_compressed(f,**{k:np.stack([r[k] for r in pool.guard_rows]) for k in pool.guard_rows[0]})
    if (out/'evaluation.json').is_file():probe.grid.write(out/'prefix_acceptance.json',probe.parent.acceptance(probe.grid.read(out/'evaluation.json')['episodes']))
    checks=dict(aliases_restored=observed.get('aliases_restored',False) and observed.get('goal_aliases_restored',False),
        prefix_task_verified=state.get('prefix_task_verified',False),native_closed=probe.grid.read(out/'diagnostic_report.json')['completed'],
        NN_count=observed.get('NN_constructors',0)==(0 if stage=='reference' else 1),
        reference_calls=(observed.get('reference_calls',0)>0 if stage=='reference' else observed.get('reference_calls')==0),
        model_RNG_frozen=stage=='reference' or ('policy_before' in observed and observed.get('policy_before')==observed.get('policy_after')),no_secondary_errors=not observed.get('cleanup_errors'))
    probe.grid.write(out/'goal_codec_report.json',dict(completed=completed and all(checks.values()),failure=failure,checks=checks,stage=stage,adapter=ADAPTER,
        NN_constructors=observed.get('NN_constructors',0),reference_calls=observed.get('reference_calls'),policy_before=observed.get('policy_before'),policy_after=observed.get('policy_after'),
        scope='source settings/environment remain incremental; layered policy output is normalized absolute goal; original trace policy_action/executed_action are physical requests; paired goal_codec_env0 holds raw goal/decoded goal/final target'))
    if failure is None and not all(checks.values()):raise RuntimeError('Goal adapter native/alias/model audit failed')


def fit(probe,paths):
    out=probe.output('fit');out.mkdir(parents=True,exist_ok=False);identity=(out.stat().st_dev,out.stat().st_ino);pins={};completed=False;failure=None;checks={}
    try:
        config=probe.parent.settings();runner.write(out/'settings.json',config);pins=runner._pins(config,out,paths);runner.write(out/'inputs_before.json',pins)
        data,buckets,labels,contract,label_evidence=dataset(probe)
        assert contract==probe.grid.read(probe.output('reference')/'training_contract.json')
        random.seed(7);np.random.seed(7);torch.manual_seed(7);torch.set_num_threads(1);torch.backends.cuda.matmul.allow_tf32=False
        policy=policy_type(probe)(contract=contract,size='large',fresh=True).to(config['device'])
        original=torch.load(probe.parent.checkpoint(0),map_location='cpu',weights_only=False)
        initial={n:v.detach().clone() for n,v in policy.state_dict().items()};assert len(initial)==73 and all(torch.equal(v.cpu(),original['model'][n]) for n,v in initial.items())
        # Different goal contract is intentional: no old incremental trainer.load or actor transplant.
        inputs={k:torch.as_tensor(data[k],device=config['device']) for k in runner.FIELDS};labels=labels.to(config['device'])
        impl=probe.source.source.support();chosen=impl.trainable(policy);flags={n:p.requires_grad for n,p in policy.named_parameters()}
        for n,p in policy.named_parameters():p.requires_grad_(n in chosen)
        opt=torch.optim.Adam(list(chosen.values()),lr=3e-4);rng=np.random.RandomState(7);losses=[]
        for _ in range(1000):
            idx=torch.as_tensor(np.concatenate([rng.choice(b,32,replace=True) for b in buckets]),device=config['device'])
            pred=policy(*(inputs[k][idx] for k in runner.FIELDS))['mean'][:,17:21].tanh();loss=(pred-labels[idx]).square().mean();assert torch.isfinite(loss)
            opt.zero_grad();loss.backward();norm=torch.nn.utils.clip_grad_norm_(list(chosen.values()),.5);assert torch.isfinite(norm);opt.step();losses.append(float(loss))
        invariant=impl.invariants(initial,policy);errors={}
        with torch.no_grad():delta=policy(*(inputs[k] for k in runner.FIELDS))['mean'][:,17:21].tanh()-labels
        delta=delta.cpu().numpy()
        for split,mask in (('train',data['env_id']<3),('heldout_same_scene',data['env_id']==3)):
            errors[split]=[dict(phase=j,samples=int((mask&(data['phase']==j)).sum()),normalized_goal_rms4=np.sqrt(np.mean(delta[mask&(data['phase']==j)]**2,axis=0)).tolist()) for j in range(6)]
        runner.write(out/'offline_errors.json',dict(errors=errors,losses=losses,label_evidence=label_evidence,scope='normalized absolute goal error, not incremental action error or physical success'))
        for n,p in policy.named_parameters():p.requires_grad_(flags[n])
        trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']));assert trainer.updates==0 and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
        metadata=dict(schema=probe.SCHEMA,settings=config,input_pins=pins,fresh_only=False,actual_initialization=probe.descriptor(),policy_output_adapter=ADAPTER,
            source_settings_initialization=config['simple_start']['initialization'],settings_scope='source environment incremental configuration; policy output layer explicit in contract/architecture',
            collection_sha256=probe.source.DATA_SHA,original_initial_sha256=probe.grid.sha(probe.parent.checkpoint(0)))
        trainer.save(out/'initial.pt',metadata=metadata)
        restored=policy_type(probe)(contract=contract,size='large',fresh=False).to(config['device']);loaded=DecisionPPOTrainer(restored,PPOConfig(**config['ppo']));loaded.load(out/'initial.pt')
        checks=dict(original_fresh73_exact=True,only_declared_parameters_changed=invariant['frozen_state_exact'],cost2zero=invariant['cost2zero'],PPO_empty0=loaded.updates==0 and not loaded.actor_optimizer.state and not loaded.value_optimizer.state,
            same_goal_full_strict_load=True,metadata_honest=metadata['policy_output_adapter']==ADAPTER,source_reference_requests_bitexact=label_evidence['source_requested_reference_bitexact'])
        runner.write(out/'parameter_invariants.json',invariant);completed=all(checks.values())
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        try:
            probe.cap.owned(out,identity);changed=[p for p,h in pins.items() if not Path(p).is_file() or probe.grid.sha(p)!=h];missing=sorted(runner.project_source_paths(list(sys.modules.items()))-set(pins))
            runner.write(out/'inputs_after.json',dict(verified=not changed and not missing,input_pins=pins,changed_paths=changed,unpinned_project_sources=missing))
            runner.write(out/'goal_codec_report.json',dict(completed=completed and not changed and not missing,failure=failure,checks=checks,stage='fit',procedure=probe.descriptor(),checkpoint_sha256=probe.grid.sha(out/'initial.pt') if (out/'initial.pt').is_file() else None,scene_created=False))
            if failure is None and (not completed or changed or missing):raise RuntimeError('Goal fit audit failed')
        except BaseException as error:
            if failure is None:raise
            print('Secondary goal fit audit error: '+repr(error),file=__import__('sys').stderr)
