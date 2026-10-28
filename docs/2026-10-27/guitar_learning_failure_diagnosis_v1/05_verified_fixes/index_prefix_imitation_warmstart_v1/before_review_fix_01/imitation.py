"""Bounded precontrol records and fixed-budget supervised fit; original policy/PPO only."""
from contextlib import contextmanager
import copy
import random
import sys
from pathlib import Path
import numpy as np
import torch
from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
from guitar_learning.training.decision_ppo import DecisionPPOTrainer
from guitar_learning.training.ppo import PPOConfig


def before(pool,action,stage):
    ids=slice(0,4);env=pool.environment;selected=pool.spec['learned_action_indices']
    rows={k:pool.observation[k][ids].detach().cpu().numpy().copy() for k in runner.FIELDS}
    rows.update(env_id=np.arange(4),first_attempt=pool.first[ids].cpu().numpy().copy(),
        start_clock=env.clock[ids].cpu().numpy().copy(),source_control=np.full(4,0 if stage=='collect' else 1,dtype=np.int64),
        old_target_rad=pool.controller.target[ids][:,pool.controller.active[selected]].cpu().numpy().copy(),
        prior_failure=(env.failure.any(-1)|env.wrist_failure|env.wrist_severe_failure)[ids].cpu().numpy().copy())
    rows['requested_reference_action' if stage=='collect' else 'requested_NN_action']=action[ids][:,selected].cpu().numpy().copy()
    return rows


def after(probe,pool,rows):
    env=pool.environment;ids=slice(0,4);selected=pool.spec['learned_action_indices']
    rows.update(clock=env.clock[ids].cpu().numpy().copy(),
        post_failure=(env.failure.any(-1)|env.wrist_failure|env.wrist_severe_failure)[ids].cpu().numpy().copy(),
        executed_action=pool.last_executed_action[ids][:,selected].cpu().numpy().copy(),
        final_target_rad=pool.scene.target[ids][:,pool.controller.active[selected]].cpu().numpy().copy(),
        raw_DIP_target_rad=pool.pending['raw_target_rad'][ids].cpu().numpy().copy(),
        final_DIP_target_rad=pool.pending['final_target_rad'][ids].cpu().numpy().copy(),
        current_goal=pool.pending['current_goal'][ids].cpu().numpy().copy())
    assert np.array_equal(rows['clock'][rows['first_attempt']],rows['start_clock'][rows['first_attempt']]+4)
    label='requested_reference_action' if (rows['source_control']==0).all() else 'requested_NN_action'
    assert np.array_equal(rows[label],rows['executed_action'])
    rows['phase']=np.array([probe.phase(int(c)/240.,pool.spec) for c in rows['clock']],dtype=np.int64)
    return [{k:v[i].copy() if isinstance(v[i],np.ndarray) else v[i] for k,v in rows.items()} for i in range(4) if rows['first_attempt'][i]]


@contextmanager
def observer_scope(probe,current,stage,observed):
    extra=probe.parent.support();old=(current.ShortPool,runtime.ShortPool,current.SCHEMA,extra.reference_action,current._evaluate,current.DecisionPPOTrainer)
    trainers=[]
    observed.update(records=[],reference_calls=0,selected4_exact=True)
    class Pool(old[0]):
        def step(self,action):
            row=before(self,action,stage)
            result=super().step(action)
            sel=self.spec['learned_action_indices']
            assert torch.equal(self.last_policy_action[:,sel],self.last_executed_action[:,sel])
            observed['records'].extend(after(probe,self,row))
            return result
    def reference(pool,value):
        observed['reference_calls']+=1
        if stage!='collect':raise RuntimeError('Reference action injection in NN-only evaluation')
        return old[3](pool,value)
    def trainer(*args,**kwargs):
        value=old[5](*args,**kwargs);trainers.append(value);return value
    def evaluate(pool,policy,spec,args,out):
        if stage=='collect':return old[4](pool,policy,spec,args,out)
        previous=probe.parent.guard.fingerprints(policy,trainers[0]);observed['policy_before']=previous;primary=None
        try:return old[4](pool,policy,spec,args,out)
        except BaseException as error:primary=error;raise
        finally:
            try:
                observed['policy_after']=probe.parent.guard.fingerprints(policy,trainers[0])
                assert observed['policy_after']==previous
            except BaseException as error:
                if primary is None:raise
                observed.setdefault('cleanup_errors',[]).append(dict(type=type(error).__name__,message=str(error)))
    current.ShortPool=runtime.ShortPool=Pool;extra.reference_action=reference
    current._evaluate=evaluate;current.DecisionPPOTrainer=trainer
    if stage=='evaluate':current.SCHEMA=probe.SCHEMA  # Metadata procedure schema; original policy architecture is unchanged.
    try:yield
    finally:
        current.ShortPool,runtime.ShortPool,current.SCHEMA,extra.reference_action,current._evaluate,current.DecisionPPOTrainer=old
        observed['observer_aliases_restored']=(current.ShortPool,runtime.ShortPool,current.SCHEMA,extra.reference_action,current._evaluate,current.DecisionPPOTrainer)==old


def finish(probe,stage,out,observed,completed,failure):
    state=observed['state'];pool=state.get('pool');checks={}
    if observed.get('records'):
        rows=observed['records'];assert len(rows)<=354*4
        with (out/'observations4.npz').open('xb') as f:np.savez_compressed(f,**{k:np.asarray([r[k] for r in rows]) for k in rows[0]})
    if pool is not None and pool.guard_rows:
        with (out/'current_goal_DIP60.npz').open('xb') as f:np.savez_compressed(f,**{k:np.stack([r[k] for r in pool.guard_rows]) for k in pool.guard_rows[0]})
    if (out/'evaluation.json').is_file():probe.grid.write(out/'prefix_acceptance.json',probe.parent.acceptance(probe.grid.read(out/'evaluation.json')['episodes']))
    checks.update(aliases_restored=observed.get('aliases_restored',False),observer_aliases_restored=observed.get('observer_aliases_restored',False),
        original_native_closed=probe.grid.read(out/'diagnostic_report.json')['completed'],prefix_task_verified=state.get('prefix_task_verified',False),
        NN_constructors_exact=observed.get('NN_constructors')==(0 if stage=='collect' else 1),selected4_request_not_replaced=observed.get('selected4_exact',False),
        model_RNG_updates_frozen=stage=='collect' or ('policy_before' in observed and observed['policy_before']==observed.get('policy_after')),
        no_secondary_errors=not observed.get('cleanup_errors'),
        reference_only_in_collection=(observed.get('reference_calls',0)>0 if stage=='collect' else observed.get('reference_calls')==0))
    report=dict(completed=completed and all(checks.values()),failure=failure,stage=stage,checks=checks,procedure=probe.descriptor(),
        dataset_sha256=probe.grid.sha(out/'observations4.npz') if (out/'observations4.npz').is_file() else None,
        reference_calls=observed.get('reference_calls'),reference_N_injected=stage=='collect',
        policy_before=observed.get('policy_before'),policy_after=observed.get('policy_after'),
        settings_scope='Original settings initialization text is source configuration only; fit checkpoint actual_initialization declares supervised provenance',
        scope='Collection is noNN reference; evaluate is NN-only current-goal guard, no carry memory or N injection')
    probe.grid.write(out/'imitation_report.json',report)
    if failure is None and not report['completed']:raise RuntimeError('Imitation collection/evaluation audit failed; output preserved')


def validate_data(data,short,probe):
    n=len(data['env_id']);assert 0<n<=354*4
    assert set(data['env_id'])=={0,1,2,3} and data['requested_reference_action'].shape==(n,4)
    assert (data['source_control']==0).all() and 'requested_NN_action' not in data
    assert data['first_attempt'].all() and not data['prior_failure'].any() and not data['post_failure'].any()
    assert np.array_equal(data['clock'],data['start_clock']+4)
    assert np.array_equal(data['requested_reference_action'],data['executed_action']) and np.max(np.abs(data['requested_reference_action']))<=1
    assert np.array_equal(data['phase'],[probe.phase(int(c)/240.,short) for c in data['clock']])
    for k in (*runner.FIELDS,'requested_reference_action'):assert np.isfinite(data[k]).all(),k
    for i in range(4):
        clocks=data['clock'][data['env_id']==i]
        assert np.array_equal(clocks,np.arange(4,1417,4))
        assert set(data['phase'][data['env_id']==i])==set(range(6))
    return [np.flatnonzero((data['env_id']<3)&(data['phase']==j)) for j in range(6)]


def trainable(policy):
    return {n:p for n,p in policy.named_parameters() if n.startswith(('finger_encoder.','finger_heads.index.'))}


def invariants(initial,policy):
    final=policy.state_dict();allowed=set(trainable(policy));assert set(initial)==set(final) and len(final)==73
    frozen=[n for n in final if n not in allowed]
    assert all(torch.equal(initial[n],final[n]) for n in frozen)
    assert not torch.count_nonzero(final['cost_critic.weight']) and not torch.count_nonzero(final['cost_critic.bias'])
    assert all(torch.isfinite(v).all() for v in final.values())
    return dict(state_tensors=73,frozen_state_tensors=len(frozen),frozen_state_exact=True,cost2zero=True,
        changed_names=sorted(n for n in final if not torch.equal(initial[n],final[n])))


def errors(policy,inputs,data):
    result={}
    with torch.no_grad():pred=policy(*(inputs[k] for k in runner.FIELDS))['mean'][:,17:21].tanh().cpu().numpy()
    delta=pred-data['requested_reference_action']
    for name,mask in (('train',data['env_id']<3),('heldout_same_scene',data['env_id']==3)):
        result[name]=[dict(phase=j,samples=int((mask&(data['phase']==j)).sum()),
            rms4=np.sqrt(np.mean(delta[mask&(data['phase']==j)]**2,axis=0)).tolist(),
            max_abs4=np.max(np.abs(delta[mask&(data['phase']==j)]),axis=0).tolist(),
            integrated_action_error_rad_by_env={str(i):(delta[(data['env_id']==i)&(data['phase']==j)].sum(0)*(4/60)).tolist()
                for i in np.unique(data['env_id'][mask])}) for j in range(6)]
    return result


def fit(probe,paths):
    out=probe.output('fit');out.mkdir(parents=True,exist_ok=False);identity=(out.stat().st_dev,out.stat().st_ino)
    completed=False;failure=None;checks={};pins={}
    try:
        config=probe.parent.settings();runner.write(out/'settings.json',config);pins=runner._pins(config,out,paths);runner.write(out/'inputs_before.json',pins)
        source=probe.output('collect');data=dict(np.load(source/'observations4.npz',allow_pickle=False));short=config['song']['short_learning']
        buckets=validate_data(data,short,probe)
        random.seed(7);np.random.seed(7);torch.manual_seed(7);torch.set_num_threads(1);torch.backends.cuda.matmul.allow_tf32=False
        contract=probe.grid.read(source/'training_contract.json');policy=probe.parent.support().PrefixPolicy(contract=contract,size='large',fresh=True).to(config['device'])
        original=torch.load(probe.parent.checkpoint(0),map_location='cpu',weights_only=False)
        assert set(original['model'])==set(policy.state_dict()) and len(original['model'])==73
        assert all(torch.equal(v.cpu(),original['model'][n]) for n,v in policy.state_dict().items())
        initial={n:v.detach().clone() for n,v in policy.state_dict().items()};trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']))
        trainer.load(probe.parent.checkpoint(0))  # Original full strict identity and RNG load; no relaxed actor transplant.
        assert trainer.updates==0 and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
        del trainer,original
        inputs={k:torch.as_tensor(data[k],device=config['device']) for k in runner.FIELDS}
        labels=torch.as_tensor(data['requested_reference_action'],device=config['device'])
        flags={n:p.requires_grad for n,p in policy.named_parameters()};chosen=trainable(policy)
        for n,p in policy.named_parameters():p.requires_grad_(n in chosen)
        opt=torch.optim.Adam(list(chosen.values()),lr=3e-4);rng=np.random.RandomState(7)
        losses=[]
        for _ in range(1000):
            ids=np.concatenate([rng.choice(b,size=32,replace=True) for b in buckets]);idx=torch.as_tensor(ids,device=config['device'])
            pred=policy(*(inputs[k][idx] for k in runner.FIELDS))['mean'][:,17:21].tanh()
            loss=(pred-labels[idx]).square().mean();assert torch.isfinite(loss)
            opt.zero_grad();loss.backward();norm=torch.nn.utils.clip_grad_norm_(list(chosen.values()),.5);assert torch.isfinite(norm);opt.step();losses.append(float(loss))
        invariant=invariants(initial,policy);runner.write(out/'offline_errors.json',dict(errors=errors(policy,inputs,data),steps=1000,losses=losses,
            scope='Integrated action error is an unguarded local request proxy; no penetration or physical success proof'))
        for n,p in policy.named_parameters():p.requires_grad_(flags[n])
        trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']))
        assert trainer.updates==0 and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
        metadata=dict(schema=probe.SCHEMA,settings=config,input_pins=pins,fresh_only=False,
            source_settings_initialization=config['simple_start']['initialization'],settings_scope='Unchanged source configuration, not this checkpoint initialization',
            actual_initialization=probe.descriptor(),collection_sha256=probe.grid.sha(source/'observations4.npz'),
            original_initial_sha256=probe.grid.sha(probe.parent.checkpoint(0)),scope='Supervised warmstart; original policy/environment identity; new PPO empty/updates0')
        trainer.save(out/'initial.pt',metadata=metadata)
        payload=torch.load(out/'initial.pt',map_location=config['device'],weights_only=False)
        checks.update(fresh73_exact=True,original_full_strict_load=True,only_declared_parameters_changed=invariant['frozen_state_exact'],
            critics_std_others_exact=True,cost2zero=invariant['cost2zero'],PPO_empty0=payload['updates']==0 and not payload['actor_optimizer']['state'] and not payload['value_optimizer']['state'],
            new_metadata_schema=payload['metadata']['schema']==probe.SCHEMA,source_settings_not_actual_initialization=payload['metadata']['actual_initialization']==probe.descriptor())
        completed=all(checks.values())
        runner.write(out/'parameter_invariants.json',invariant)
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        probe.cap.owned(out,identity);changed=[p for p,h in pins.items() if not Path(p).is_file() or probe.grid.sha(p)!=h]
        missing=sorted(runner.project_source_paths(list(sys.modules.items()))-set(pins))
        runner.write(out/'inputs_after.json',dict(verified=not changed and not missing,input_pins=pins,changed_paths=changed,unpinned_project_sources=missing))
        runner.write(out/'imitation_report.json',dict(completed=completed and not changed and not missing,failure=failure,stage='fit',checks=checks,procedure=probe.descriptor(),
            checkpoint_sha256=probe.grid.sha(out/'initial.pt') if (out/'initial.pt').is_file() else None,scene_created=False,
            scope='GPU supervised fit only, no native physics; deterministic NN-only execution still unverified'))
        if failure is None and (changed or missing or not completed):raise RuntimeError('Fit audit failed; outputs preserved')
