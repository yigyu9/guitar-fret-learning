"""Fresh actor reproduction followed by a bounded reward-value-only warmup."""
import copy
import importlib.util
from pathlib import Path
import sys
import numpy as np
import torch
import runtime as rt

HERE = Path(__file__).resolve().parent
DATA = HERE.parent/'index_reward_gradient_audit_v1/runs/fit'
FIELDS = ('state','events','mask','priority_events','priority_mask')
spec = importlib.util.spec_from_file_location('warmup_v7_original_loop',rt.v6.v5.SOURCE/'learn.py')
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent
old = sys.modules.get('runtime')
try:
    sys.modules['runtime'] = rt
    spec.loader.exec_module(parent)
finally:
    if old is None: sys.modules.pop('runtime',None)
    else: sys.modules['runtime'] = old
original_metadata,original_load = parent.metadata,parent.load
DecisionPPOTrainer,PPOConfig,seed = parent.DecisionPPOTrainer,parent.PPOConfig,parent.seed


def metadata(settings,pins,*,fit_steps=1000,warmup_steps=1000):
    result = original_metadata(settings,pins,fit_steps=fit_steps)
    result.update(cost_prior=copy.deepcopy(rt.COST_PRIOR),reward_value_warmup=copy.deepcopy(rt.WARMUP),
                  value_warmup_steps=warmup_steps,value_warmup_accepted=warmup_steps == 1000)
    return result


def load(trainer,path,settings):
    data = torch.load(path,map_location='cpu',weights_only=False)['metadata']
    if (data.get('cost_prior') != rt.COST_PRIOR or data.get('reward_value_warmup') != rt.WARMUP or
            data.get('value_warmup_steps') not in (0,1000) or
            data.get('value_warmup_accepted') is not (data.get('value_warmup_steps') == 1000)):
        raise ValueError('Own V7 metadata required')
    return original_load(trainer,path,settings)

parent.metadata,parent.load = metadata,load


def ready(path):
    payload = torch.load(path,map_location='cpu',weights_only=False)
    data = payload['metadata']
    if data.get('schema') != rt.SCHEMA or data.get('value_warmup_steps') != 1000 or data.get('value_warmup_accepted') is not True:
        raise ValueError('Completed accepted V7 warmup required before train/evaluate')
    return data


def monte_carlo(reward,terminated,truncated,valid,gamma=.99):
    if reward.shape != (354,128) or any(x.shape != reward.shape for x in (terminated,truncated,valid)):
        raise ValueError('Original354x128 fit data required')
    if any(x.dtype != torch.bool for x in (terminated,truncated,valid)):
        raise ValueError('Boolean original masks required')
    if (not bool(valid.all()) or bool(truncated.any()) or bool(terminated[:-1].any()) or
            not bool(terminated[-1].all()) or not bool(torch.isfinite(reward).all())):
        raise ValueError('Full first attempts ending at actual terminal required; no fabricated bootstrap')
    result = torch.empty_like(reward,dtype=torch.float64)
    carry = torch.zeros(128,dtype=torch.float64)
    for tick in reversed(range(354)):
        carry = reward[tick].double()+gamma*carry*(~terminated[tick])
        result[tick] = carry
    return result


def dataset():
    pieces = []
    paths = sorted(DATA.glob('buffer_*.npz'))
    assert len(paths) == 12
    for index,path in enumerate(paths):
        with np.load(path,allow_pickle=False) as archive:
            piece = {key:torch.from_numpy(archive[key].copy()) for key in
                (*FIELDS,'reward','terminated','truncated','valid','episode_id','audit_phase','start_control_tick')}
        assert piece['reward'].shape == ((32 if index < 11 else 2),128)
        pieces.append(piece)
    data = {k:torch.cat([p[k] for p in pieces]) for k in pieces[0]}
    assert bool((data['episode_id'] == 0).all())
    assert torch.equal(data['start_control_tick'],torch.arange(354)[:,None].expand(354,128))
    target = monte_carlo(*(data[k] for k in ('reward','terminated','truncated','valid')))
    assert set(data['audit_phase'].flatten().tolist()) == set(range(10))
    assert all(bool(torch.isfinite(v).all()) for v in data.values() if v.is_floating_point())
    return data,target


def selected_parameters(policy):
    return {n:p for n,p in policy.named_parameters() if n.startswith(('value_encoder.','reward_critic.'))}


def value(policy,inputs):
    return policy.reward_critic(policy.value_encoder(*inputs)).squeeze(-1)


def evaluate_values(policy,data,target):
    result = {}
    device = next(policy.parameters()).device
    with torch.no_grad():
        predictions = []
        for start in range(0,354*128,512):
            inputs = [data[k].flatten(0,1)[start:start+512].to(device) for k in FIELDS]
            predictions.append(value(policy,inputs).cpu().double())
        prediction = torch.cat(predictions).reshape(354,128)
    error = prediction-target
    for split,ids in [('train',slice(0,96)),('holdout',slice(96,128))]:
        phases = data['audit_phase'][:,ids]
        rows = error[:,ids]
        def stats(x): return dict(count=x.numel(),MSE=float(x.square().mean()),bias=float(x.mean()))
        result[split] = dict(overall=stats(rows),phases={str(p):stats(rows[phases == p]) for p in range(10)})
    return result,prediction


def warmup(policy,data,target,config,*,steps=1000,progress=None):
    if steps != 1000: raise ValueError('Fixed1000-step budget required')
    selected = selected_parameters(policy)
    assert selected and all(n.startswith(('value_encoder.','reward_critic.')) for n in selected)
    device = next(policy.parameters()).device
    # Use a dedicated sampler; preserve the exact global CPU and device RNG boundary.
    rng_cpu = torch.get_rng_state().clone()
    rng_cuda = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
    initial = {k:v.detach().clone() for k,v in policy.state_dict().items()}
    flags = {n:p.requires_grad for n,p in policy.named_parameters()}
    before,prediction_before = evaluate_values(policy,data,target)
    fixed_inputs = [data[k][0,:8].to(device) for k in FIELDS]
    def actor():
        devices = [device.index or 0] if device.type == 'cuda' else []
        with torch.random.fork_rng(devices=devices):
            result = policy.act(*fixed_inputs)
        return {k:result[k].detach().clone() for k in ('mean','log_std','latent','action','logp')}
    with torch.no_grad(): actor_before = actor()
    optimizer = torch.optim.Adam(list(selected.values()),lr=config.value_lr)
    sampler = np.random.RandomState(7)
    losses = []
    try:
        for n,p in policy.named_parameters(): p.requires_grad_(n in selected)
        for step in range(1000):
            # Uniformly sample the complete354x96 train rows; holdout is never eligible.
            indices = torch.from_numpy(sampler.randint(354*96,size=512))
            tick,env = indices//96,indices%96
            inputs = [data[k][tick,env].to(device) for k in FIELDS]
            truth = target[tick,env].to(device=device,dtype=torch.float32)
            loss = (value(policy,inputs)-truth).square().mean()
            assert bool(torch.isfinite(loss))
            optimizer.zero_grad();loss.backward()
            torch.nn.utils.clip_grad_norm_(list(selected.values()),config.max_grad_norm,error_if_nonfinite=True)
            optimizer.step();losses.append(float(loss))
            if progress is not None: progress(step+1,float(loss))
    finally:
        for n,p in policy.named_parameters():
            p.requires_grad_(flags[n]);p.grad = None
    after,prediction_after = evaluate_values(policy,data,target)
    with torch.no_grad(): actor_after = actor()
    unchanged = [k for k in initial if not k.startswith(('value_encoder.','reward_critic.'))]
    assert all(torch.equal(initial[k],policy.state_dict()[k]) for k in unchanged)
    assert all(torch.equal(actor_before[k],actor_after[k]) for k in actor_before)
    assert torch.equal(rng_cpu,torch.get_rng_state())
    if rng_cuda is not None:
        assert all(torch.equal(a,b) for a,b in zip(rng_cuda,torch.cuda.get_rng_state_all()))
    accepted = np.isfinite(after['holdout']['overall']['MSE']) and after['holdout']['overall']['MSE'] < before['holdout']['overall']['MSE']
    return dict(accepted=bool(accepted),steps=1000,batch_size=512,losses=losses,before=before,after=after,
        actor_std_costhead_exact=True,global_RNG_exact=True,temporary_optimizer_discarded=True,
        changed_tensor_names=[k for k in initial if not torch.equal(initial[k],policy.state_dict()[k])]),prediction_before,prediction_after


def fit(capture,settings,pins,out):
    state = dict(counters=dict(fit_steps=0,value_warmup_steps=0,PPO_updates=0,native_runs=0))
    with parent.audit(out,settings,pins,state) as out:
        old_metadata = parent.metadata
        try:
            parent.metadata = lambda settings,pins,fit_steps=1000: metadata(settings,pins,fit_steps=fit_steps,warmup_steps=0)
            parent.fit(capture,settings,pins,out/'actor_fit')
        finally: parent.metadata = old_metadata
        state['counters']['fit_steps'] = 1000
        equality = {}
        for filename in ('fresh.pt','fit.pt'):
            own = torch.load(out/'actor_fit'/filename,map_location='cpu',weights_only=False)['model']
            reference = torch.load(rt.SOURCE/'runs/fit'/filename,map_location='cpu',weights_only=False)['model']
            assert own.keys() == reference.keys() and all(torch.equal(own[k],reference[k]) for k in own)
            equality[filename] = dict(all71tensors_exact=True,reference_sha=rt.base.sha(rt.SOURCE/'runs/fit'/filename))
        rt.base.write(out/'actor_tensor_equality.json',equality)
        data,target = dataset()
        contract = rt.attach(rt.base.read(capture/'training_contract.json'))
        policy = rt.GoalPolicy(contract=contract,size=settings['size']).to(settings['device'])
        trainer = DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']))
        load(trainer,out/'actor_fit/fit.pt',settings)
        assert trainer.updates == 0 and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
        state['fit_losses'] = []
        def progress(step,loss):
            state['counters']['value_warmup_steps'] = step
            state['fit_losses'].append(loss)
        report,before,after = warmup(policy,data,target,trainer.config,progress=progress)
        state['counters']['value_warmup_steps'] = 1000
        rt.base.write(out/'warmup_report.json',report)
        np.savez_compressed(out/'value_predictions.npz',target=target.numpy(),before=before.numpy(),after=after.numpy(),phase=data['audit_phase'].numpy())
        if not report['accepted']: raise RuntimeError('Holdout MSE did not improve; no PPO allowed')
        # Temporary Adam is gone; PPO begins with entirely empty optimizer state.
        trainer = DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']))
        assert not trainer.actor_optimizer.state and not trainer.value_optimizer.state and trainer.updates == 0
        trainer.save(out/'fit.pt',metadata=metadata(settings,pins))


def train(checkpoint,settings,pins,out):
    ready(checkpoint)
    return parent.train(checkpoint,settings,pins,out)


def evaluate(checkpoint,settings,pins,out,*,stochastic=False):
    ready(checkpoint)
    return parent.evaluate(checkpoint,settings,pins,out,stochastic=stochastic)
