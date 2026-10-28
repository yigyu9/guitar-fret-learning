"""Original reference label replay and one fixed extra supervised budget per condition."""
import random
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np
import torch
from guitar_learning.tool.experiments.short_finger_learning import runner
from guitar_learning.training.decision_ppo import DecisionPPOTrainer
from guitar_learning.training.ppo import PPOConfig


def datasets(probe):
    result=[]
    for stage in ('collect','evaluate'):
        folder=probe.base.output(stage);data=dict(np.load(folder/'observations4.npz',allow_pickle=False));assert len(data['env_id'])==1416
        assert data['first_attempt'].all() and not data['prior_failure'].any() and not data['post_failure'].any()
        assert (data['source_control']==(0 if stage=='collect' else 1)).all()
        for i in range(4):
            m=data['env_id']==i;np.testing.assert_array_equal(data['start_clock'][m],np.arange(354)*4);np.testing.assert_array_equal(data['clock'][m],np.arange(1,355)*4)
        result.append(data)
    for key in ('env_id','start_clock','clock','phase'):np.testing.assert_array_equal(result[0][key],result[1][key])
    return result


def requested_reference(probe,data):
    # Same selected-axis seam independently reviewed in the frozen label_replay.py.
    source=probe.source;short=source.parent.settings()['song']['short_learning'];ids=short['learned_action_indices']
    c=probe.grid.read(probe.base.COLLECT/'training_contract.json')['action']['target_contract']
    active=torch.tensor([c['joint_names'].index(n) for n in c['action_order']]);ref=torch.tensor(c['reference105_rad'],dtype=torch.float32)
    target=ref[None].repeat(len(data['env_id']),1);target[:,active[ids]]=torch.from_numpy(data['old_target_rad'])
    incremental=torch.zeros(39,dtype=torch.bool);incremental[17:33]=True
    fake=SimpleNamespace(spec=short,teacher_reference=ref[active],incremental_mask=incremental,
        controller=SimpleNamespace(target=target,active=active,action_low=torch.tensor(c['action_lower_rad'],dtype=torch.float32),action_high=torch.tensor(c['action_upper_rad'],dtype=torch.float32)),
        environment=SimpleNamespace(_local_time=lambda:torch.from_numpy(data['start_clock']).to(torch.float64)/240.))
    reference=runner.read_reference(source.parent.base.pre.INPUTS['index'][1],short)
    return source.parent.support().reference_action(fake,reference)[:,ids].numpy()


def make_labels(probe,out):
    ref,nn=datasets(probe);expected=requested_reference(probe,ref);np.testing.assert_array_equal(expected,ref['requested_reference_action'])
    shadow=requested_reference(probe,nn);assert np.isfinite(shadow).all() and abs(shadow).max()<=1
    with (out/'labels.npz').open('xb') as f:np.savez_compressed(f,native_reference_request4=expected,shadow_reference_request4=shadow,
        NN_actual_requested4=nn['requested_NN_action'],NN_actual_executed4=nn['executed_action'],env_id=ref['env_id'],phase=ref['phase'],start_clock=ref['start_clock'])
    probe.grid.write(out/'label_manifest.json',dict(schema='diagnostic.saved_NN_shadow_labels.v1',reference_exact=True,rows_per_source=1416,
        reference=dict(path=str(probe.base.COLLECT/'observations4.npz'),sha256=probe.grid.sha(probe.base.COLLECT/'observations4.npz'),label='native_reference_request4',origin='actual native reference request'),
        counterfactual=dict(path=str(probe.base.output('evaluate')/'observations4.npz'),sha256=probe.grid.sha(probe.base.output('evaluate')/'observations4.npz'),label='shadow_reference_request4',origin='offline request at saved NN observation clock/oldtarget; never executed'),
        actual_NN_fields=['NN_actual_requested4','NN_actual_executed4'],source_function='original Prefix reference_action/trajectory_actions, unchanged',
        original_label_replay_sha256=probe.grid.sha(probe.base.HERE/'analysis/label_replay.py'),
        scope='No new physics/observation, no label guard-zeroing, no native success inherited; source/currentgoal gate unchanged'))


def batches(condition,rng,ref,nn):
    assert condition in ('reference_only','corrective_mixed')
    ids=[];N=len(ref['env_id'])
    for j in range(6):
        a=np.flatnonzero((ref['env_id']<3)&(ref['phase']==j));b=np.flatnonzero((nn['env_id']<3)&(nn['phase']==j))
        assert len(a)==len(b)>0
        ids.extend(rng.choice(a,16,replace=True));second=rng.choice(b if condition=='corrective_mixed' else a,16,replace=True)
        ids.extend(second+(N if condition=='corrective_mixed' else 0))
    return np.asarray(ids,dtype=np.int64)


def errors(policy,inputs,labels,data):
    with torch.no_grad():pred=policy(*(inputs[k] for k in runner.FIELDS))['mean'][:,17:21].tanh().cpu().numpy()
    delta=pred-labels;result={}
    for source,name in ((0,'native_reference'),(1,'saved_NN_shadow')):
        d=data[source];base=sum(len(v['env_id']) for v in data[:source]);part=delta[base:base+len(d['env_id'])]
        result[name]={}
        for split,envmask in [('train',d['env_id']<3),('heldout_same_scene',d['env_id']==3)]:
            result[name][split]=[dict(phase=j,samples=int((envmask&(d['phase']==j)).sum()),rms4=np.sqrt(np.mean(part[envmask&(d['phase']==j)]**2,axis=0)).tolist(),
                max_abs4=abs(part[envmask&(d['phase']==j)]).max(0).tolist()) for j in range(6)]
    return result


def fit(probe,condition,paths):
    out=probe.output(condition,'fit');out.mkdir(parents=True,exist_ok=False);identity=(out.stat().st_dev,out.stat().st_ino)
    completed=False;failure=None;checks={};pins={}
    try:
        config=probe.source.parent.settings();runner.write(out/'settings.json',config);pins=runner._pins(config,out,paths);runner.write(out/'inputs_before.json',pins)
        data=datasets(probe);labels=dict(np.load(probe.HERE/'cpu_inputs/labels.npz',allow_pickle=False))
        np.testing.assert_array_equal(labels['NN_actual_requested4'],data[1]['requested_NN_action']);np.testing.assert_array_equal(labels['NN_actual_executed4'],data[1]['executed_action'])
        y=np.concatenate([labels['native_reference_request4'],labels['shadow_reference_request4']]);extra=probe.source.parent.support();impl=probe.source.support()
        random.seed(7);np.random.seed(7);torch.manual_seed(7);torch.set_num_threads(1);torch.backends.cuda.matmul.allow_tf32=False
        start=torch.load(probe.START,map_location='cpu',weights_only=False);contract=start['identity']['architecture']['contract']
        policy=extra.PrefixPolicy(contract=contract,size='large',fresh=False).to(config['device']);trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']))
        metadata=trainer.load(probe.START)  # Complete original identity/config/RNG load; no actor transplant or relaxed load.
        assert metadata['schema']==probe.base.SCHEMA and metadata['actual_initialization']==probe.base.descriptor()
        assert trainer.updates==0 and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
        assert len(start['model'])==73 and all(torch.equal(v.cpu(),start['model'][n]) for n,v in policy.state_dict().items())
        initial={n:v.detach().clone() for n,v in policy.state_dict().items()};del start,trainer
        inputs={k:torch.as_tensor(np.concatenate([d[k] for d in data]),device=config['device']) for k in runner.FIELDS};target=torch.as_tensor(y,device=config['device'])
        flags={n:p.requires_grad for n,p in policy.named_parameters()};chosen=impl.trainable(policy)
        for n,p in policy.named_parameters():p.requires_grad_(n in chosen)
        opt=torch.optim.Adam(list(chosen.values()),lr=3e-4);rng=np.random.RandomState(7);losses=[]
        for _ in range(1000):
            ids=torch.as_tensor(batches(condition,rng,*data),device=config['device'])
            prediction=policy(*(inputs[k][ids] for k in runner.FIELDS))['mean'][:,17:21].tanh();loss=(prediction-target[ids]).square().mean();assert torch.isfinite(loss)
            opt.zero_grad();loss.backward();norm=torch.nn.utils.clip_grad_norm_(list(chosen.values()),.5);assert torch.isfinite(norm);opt.step();losses.append(float(loss))
        invariant=impl.invariants(initial,policy)
        runner.write(out/'offline_errors.json',dict(condition=condition,additional_steps=1000,total_supervised_steps=2000,losses=losses,errors=errors(policy,inputs,y,data),parameter_invariants=invariant))
        for n,p in policy.named_parameters():p.requires_grad_(flags[n])
        trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']));assert trainer.updates==0 and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
        metadata=dict(schema=probe.SCHEMA,settings=config,input_pins=pins,fresh_only=False,actual_initialization=probe.descriptor(condition),
            starting_checkpoint_sha256=probe.START_SHA,source_settings_initialization=config['simple_start']['initialization'],
            settings_scope='Unchanged source configuration; actual_initialization declares additional supervised continuation',scope='2000supervised steps total; no PPO updates; NN-only verification pending')
        trainer.save(out/'initial.pt',metadata=metadata)
        checks=dict(starting73_exact=True,original_full_strict_load=True,only_declared_modules_changed=invariant['frozen_state_exact'],cost2zero=invariant['cost2zero'],PPO_empty0=True,
            same_additional_1000x192=True,heldout_env3_never_sampled=True,actual_and_shadow_labels_separate=True,new_metadata_condition=True)
        completed=all(checks.values())
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        try:
            probe.cap.owned(out,identity);changed=[p for p,h in pins.items() if not Path(p).is_file() or probe.grid.sha(p)!=h];missing=sorted(runner.project_source_paths(list(sys.modules.items()))-set(pins))
            runner.write(out/'inputs_after.json',dict(verified=not changed and not missing,input_pins=pins,changed_paths=changed,unpinned_project_sources=missing))
            runner.write(out/'corrective_fit_report.json',dict(completed=completed and not changed and not missing,failure=failure,condition=condition,checks=checks,procedure=probe.descriptor(condition),
                checkpoint_path=str(out/'initial.pt'),checkpoint_sha256=probe.grid.sha(out/'initial.pt') if (out/'initial.pt').is_file() else None,scene_created=False))
            if failure is None and (changed or missing or not completed):raise RuntimeError('Corrective fit audit failed; output preserved')
        except BaseException as error:
            if failure is None:raise
            print('Secondary corrective fit cleanup error: '+repr(error),file=sys.stderr)
