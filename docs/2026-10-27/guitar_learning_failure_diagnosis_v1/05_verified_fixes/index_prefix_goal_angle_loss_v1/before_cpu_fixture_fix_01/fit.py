"""Fixed original budget; MSE only after original affine decode, in rad^2."""
import random
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from guitar_learning.tool.experiments.short_finger_learning import runner
from guitar_learning.training.decision_ppo import DecisionPPOTrainer
from guitar_learning.training.ppo import PPOConfig


def dataset(probe):
    source=probe.source;codec=source.support();data,buckets,raw_labels,contract,evidence=codec.dataset(source)
    c=contract['action']['target_contract'];short=source.parent.settings()['song']['short_learning'];ids=short['learned_action_indices']
    active=torch.tensor([c['joint_names'].index(n) for n in c['action_order']]);ref=torch.tensor(c['reference105_rad'],dtype=torch.float32)
    fake=SimpleNamespace(spec=short,teacher_reference=ref[active],environment=SimpleNamespace(_local_time=lambda:torch.from_numpy(data['start_clock']).to(torch.float64)/240.))
    reference=runner.read_reference(source.parent.base.pre.INPUTS['index'][1],short);desired=codec.desired_reference(source,fake,reference)[:,ids]
    bounds=(ref[active][ids],torch.tensor(c['action_lower_rad'],dtype=torch.float32)[ids],torch.tensor(c['action_upper_rad'],dtype=torch.float32)[ids])
    assert torch.equal(codec.encode(desired,*bounds),raw_labels) and evidence['source_requested_reference_bitexact']
    return data,buckets,raw_labels,desired,bounds,contract,evidence


def loss(codec,raw,desired,bounds):return (codec.decode(raw,*bounds)-desired).square().mean()


def errors(codec,pred,raw_labels,desired,bounds,data):
    raw=(pred-raw_labels).cpu().numpy();angle=(codec.decode(pred,*bounds)-desired).cpu().numpy();result={}
    for split,keep in (('train',data['env_id']<3),('heldout_same_scene',data['env_id']==3)):
        result[split]=[dict(phase=j,samples=int((keep&(data['phase']==j)).sum()),normalized_goal_rms4=np.sqrt(np.mean(raw[keep&(data['phase']==j)]**2,axis=0)).tolist(),
            angle_rms_rad4=np.sqrt(np.mean(angle[keep&(data['phase']==j)]**2,axis=0)).tolist(),angle_rms_deg4=np.rad2deg(np.sqrt(np.mean(angle[keep&(data['phase']==j)]**2,axis=0))).tolist()) for j in range(6)]
    return result


def finish(probe,out,identity,pins,completed,failure,checks):
    try:
        probe.cap.owned(out,identity);changed=[p for p,h in pins.items() if not Path(p).is_file() or probe.grid.sha(p)!=h]
        missing=sorted(runner.project_source_paths(list(sys.modules.items()))-set(pins))
        runner.write(out/'inputs_after.json',dict(verified=not changed and not missing,input_pins=pins,changed_paths=changed,unpinned_project_sources=missing))
        runner.write(out/'angle_loss_fit_report.json',dict(completed=completed and not changed and not missing,failure=failure,checks=checks,procedure=probe.descriptor(),
            checkpoint_sha256=probe.grid.sha(out/'initial.pt') if (out/'initial.pt').is_file() else None,scene_created=False))
        if failure is None and (changed or missing or not completed):raise RuntimeError('Angle-loss fit audit failed; output preserved')
    except BaseException as error:
        if failure is None:raise
        print('Secondary angle-loss fit audit error: '+repr(error),file=sys.stderr)


def fit(probe,paths):
    out=probe.output('fit');out.mkdir(parents=True,exist_ok=False);identity=(out.stat().st_dev,out.stat().st_ino);pins={};completed=False;failure=None;checks={}
    try:
        source=probe.source;codec=source.support();config=probe.parent.settings();runner.write(out/'settings.json',config)
        pins=runner._pins(config,out,paths);runner.write(out/'inputs_before.json',pins)
        data,buckets,raw_labels,desired,bounds,contract,evidence=dataset(probe)
        assert contract==probe.grid.read(source.output('reference')/'training_contract.json')
        random.seed(7);np.random.seed(7);torch.manual_seed(7);torch.set_num_threads(1);torch.backends.cuda.matmul.allow_tf32=False
        GoalPolicy=codec.policy_type(source);policy=GoalPolicy(contract=contract,size='large',fresh=True).to(config['device'])
        original=torch.load(probe.parent.checkpoint(0),map_location='cpu',weights_only=False);initial={n:v.detach().clone() for n,v in policy.state_dict().items()}
        assert len(initial)==73 and all(torch.equal(v.cpu(),original['model'][n]) for n,v in initial.items());del original
        inputs={k:torch.as_tensor(data[k],device=config['device']) for k in runner.FIELDS};raw_labels=raw_labels.to(config['device']);desired=desired.to(config['device']);bounds=tuple(v.to(config['device']) for v in bounds)
        impl=source.source.source.support();chosen=impl.trainable(policy);flags={n:p.requires_grad for n,p in policy.named_parameters()}
        for n,p in policy.named_parameters():p.requires_grad_(n in chosen)
        opt=torch.optim.Adam(list(chosen.values()),lr=3e-4);rng=np.random.RandomState(7);losses=[]
        for _ in range(1000):
            idx=torch.as_tensor(np.concatenate([rng.choice(b,32,replace=True) for b in buckets]),device=config['device'])
            pred=policy(*(inputs[k][idx] for k in runner.FIELDS))['mean'][:,17:21].tanh();value=loss(codec,pred,desired[idx],bounds);assert torch.isfinite(value)
            opt.zero_grad();value.backward();norm=torch.nn.utils.clip_grad_norm_(list(chosen.values()),.5);assert torch.isfinite(norm);opt.step();losses.append(float(value))
        invariant=impl.invariants(initial,policy)
        with torch.no_grad():pred=policy(*(inputs[k] for k in runner.FIELDS))['mean'][:,17:21].tanh();metrics=errors(codec,pred,raw_labels,desired,bounds,data)
        runner.write(out/'offline_errors.json',dict(loss_units='rad^2',losses=losses,errors=metrics,label_evidence=evidence,procedure=probe.descriptor(),scope='raw goal and physical-angle errors distinct; not native success'))
        for n,p in policy.named_parameters():p.requires_grad_(flags[n])
        trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']));assert trainer.updates==0 and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
        metadata=dict(schema=probe.SCHEMA,settings=config,input_pins=pins,fresh_only=False,actual_initialization=probe.descriptor(),policy_output_adapter=codec.ADAPTER,
            source_settings_initialization=config['simple_start']['initialization'],settings_scope='source environment configuration; new decoded-angle supervised loss declared separately',
            collection_sha256=source.source.DATA_SHA,original_initial_sha256=probe.grid.sha(probe.parent.checkpoint(0)))
        trainer.save(out/'initial.pt',metadata=metadata)
        restored=GoalPolicy(contract=contract,size='large',fresh=False).to(config['device']);loaded=DecisionPPOTrainer(restored,PPOConfig(**config['ppo']));probe.check_metadata(loaded.load(out/'initial.pt'))
        checks=dict(original_fresh73_exact=True,only_declared_parameters_changed=invariant['frozen_state_exact'],cost2zero=invariant['cost2zero'],PPO_empty0=loaded.updates==0 and not loaded.actor_optimizer.state and not loaded.value_optimizer.state,
            same_GoalPolicy_full_strict_load=True,new_loss_metadata_exact=True,source_reference_requests_bitexact=evidence['source_requested_reference_bitexact'],same_1000x192_sixphase=True)
        runner.write(out/'parameter_invariants.json',invariant);completed=all(checks.values())
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:finish(probe,out,identity,pins,completed,failure,checks)
