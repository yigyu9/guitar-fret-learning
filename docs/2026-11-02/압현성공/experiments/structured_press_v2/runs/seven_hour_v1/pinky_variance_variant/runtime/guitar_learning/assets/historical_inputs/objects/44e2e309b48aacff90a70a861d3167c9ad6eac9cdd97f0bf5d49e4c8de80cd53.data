"""Goal-conditioned cloning of audited native transition demonstrations.

The new format is deliberately separate from the old fixed240-row505/563
loaders. A training fit is not an unassisted native success certificate.
"""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import tempfile

import numpy as np
import torch

from guitar_learning.imitation.imitation import dataset_manifest
from guitar_learning.training.parallel import FIELDS
from guitar_learning.tool.experiments.transition.policy import SpecialistPolicy
from guitar_learning.tool.experiments.transition.transfer import _model_state, apply_source, validate_source

SCHEMA = 'guitar_learning.transition_imitation.v1'
SHAPES = dict(state=(500,), events=(64,24), mask=(64,),
    priority_events=(2,24), priority_mask=(2,), action=(39,))


def _arrays(data, role):
    count = len(data['action'])
    if count < 2:
        raise ValueError('at least two actual native transitions required')
    for key, shape in SHAPES.items():
        value = data.get(key)
        if not isinstance(value, np.ndarray) or value.shape != (count,)+shape:
            raise ValueError('complete500-state native observation/action rows required: '+key)
        if 'mask' in key:
            if value.dtype != np.bool_:
                raise ValueError('boolean masks required')
        elif value.dtype.kind != 'f' or not np.isfinite(value).all():
            raise ValueError('finite floating observations/actions required')
    if np.any(np.abs(data['action']) > 1):
        raise ValueError('normalized bounded action39 required')
    if role == 'left' and np.any(data['action'][:,33:] != 0):
        raise ValueError('inactive right hand must be exactly zero')


def load_dataset(captures, expected_contract=None):
    from guitar_learning.tool.experiments.transition.capture import audit_capture
    if isinstance(captures, (str, Path)):
        captures = [captures]
    if not captures:
        raise ValueError('successful finalized native captures required')
    audited = [audit_capture(Path(path)) for path in captures]
    contract = copy.deepcopy(expected_contract or audited[0]['contract'])
    role = contract.get('task', {}).get('transition', {}).get('role')
    if role not in ('left', 'joint'):
        raise ValueError('transition capture role required')
    pins = {}; contracts = []
    for capture in audited:
        actual = capture['contract']
        if actual['task']['transition']['role'] != role:
            raise ValueError('capture roles must match target policy')
        # Task timelines differ across single-A/single-B/pair captures. Every
        # observation/control/physical/reward definition remains identical.
        projected = copy.deepcopy(actual); projected['task'] = contract['task']
        projected['termination']['time_limit_s'] = contract['termination']['time_limit_s']
        if projected != contract:
            raise ValueError('demonstrations must share exact physical/input/reward semantics')
        _arrays(capture['arrays'], role)
        contracts.append(copy.deepcopy(actual))
        for path, sha in capture['source_pins'].items():
            if path in pins and pins[path] != sha:
                raise ValueError('conflicting demonstration evidence')
            pins[path] = sha
    arrays = {key:np.concatenate([item['arrays'][key] for item in audited], axis=0) for key in SHAPES}
    return dict(arrays, role=role, contract=contract, dataset_contracts=contracts,
        source_pins=pins, captures=[str(Path(path).resolve()) for path in captures])


def fit_actor(model, data, *, steps=2000, lr=3e-4, batch_size=120,
        tolerance=1e-6, seed=7, log_callback=None):
    if (not isinstance(model, SpecialistPolicy) or data['contract'] != model.architecture['contract']
            or data['role'] != model.role):
        raise ValueError('exact transition policy/demonstration contract required')
    _arrays(data, model.role)
    if (type(steps) is not int or steps < 1 or type(batch_size) is not int or batch_size < 1
            or type(seed) is not int or isinstance(lr,bool) or not math.isfinite(lr) or lr<=0
            or isinstance(tolerance,bool) or not math.isfinite(tolerance) or tolerance<0):
        raise ValueError('positive fit budget/rate and nonnegative finite tolerance required')
    device = next(model.parameters()).device
    inputs = {key:torch.as_tensor(data[key],device=device,
        dtype=torch.bool if 'mask' in key else torch.float32) for key in FIELDS}
    active = model._active_mask()
    target = torch.as_tensor(data['action'],device=device,dtype=torch.float32)[:,active]
    parameters = []
    for role in model.trainable_roles:
        parameters += list(model.actor_encoders[role].parameters())+list(model.actor_heads[role].parameters())
    optimizer = torch.optim.Adam(parameters,lr=lr)
    generator = torch.Generator().manual_seed(seed)
    def prediction(indices=None):
        values = [inputs[key] if indices is None else inputs[key][indices] for key in FIELDS]
        return model(*values)['mean'][:,active].tanh()
    log=[]
    def measure(step):
        with torch.no_grad():
            error=prediction()-target
            row=dict(step=step,training_mse=float(error.square().mean()),max_abs_error=float(error.abs().max()))
        if not math.isfinite(row['training_mse']): raise ValueError('nonfinite BC fit')
        log.append(row)
        if log_callback:log_callback(copy.deepcopy(row))
        return row
    final=measure(0);initial=final['training_mse'];count=len(target)
    for step in range(1,steps+1):
        if final['training_mse']<=tolerance:break
        indices=torch.randperm(count,generator=generator)[:min(batch_size,count)].to(device)
        loss=(prediction(indices)-target[indices]).square().mean()
        optimizer.zero_grad(set_to_none=True);loss.backward();optimizer.step()
        if step%100==0 or step==steps:final=measure(step)
    optimizer.zero_grad(set_to_none=True)
    return dict(final,initial_training_mse=initial,converged=final['training_mse']<=tolerance,
        tolerance=tolerance,learning_rate=lr,batch_size=min(batch_size,count),seed=seed,log=log,
        scope='selected actor action fit only; unassisted native validation still required')


def save_initialization(model,path,*,data,fit_result):
    if data['contract']!=model.architecture['contract']:
        raise ValueError('BC target contract required')
    if dataset_manifest(data['source_pins'])!=data['source_pins']:
        raise RuntimeError('capture inputs changed before BC publication')
    state={key:value.detach().cpu().clone() for key,value in model.state_dict().items()}
    _model_state(model,state)
    payload=dict(schema=SCHEMA,architecture=copy.deepcopy(model.architecture),model=state,
        role=model.role,dataset_manifest=copy.deepcopy(data['source_pins']),
        dataset_contracts=copy.deepcopy(data['dataset_contracts']),captures=list(data['captures']),
        source_checkpoint=data.get('source_checkpoint'),
        training=copy.deepcopy(fit_result),scope='Actor/std initialization, fresh critic/Adam/RNG/PPO counters')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,temporary=tempfile.mkstemp(prefix='transition-bc-',suffix='.pt',dir=str(path.parent));os.close(fd)
    try:torch.save(payload,temporary);os.link(temporary,path)
    finally:os.unlink(temporary)


def validate_initialization(path, expected_architecture=None):
    path=Path(path);pins=dataset_manifest([path])
    payload=torch.load(path,map_location='cpu',weights_only=False)
    if (payload.get('schema')!=SCHEMA or 'identity' in payload or 'updates' in payload
            or not isinstance(payload.get('training'),dict)
            or (expected_architecture is not None and payload.get('architecture')!=expected_architecture)):
        raise ValueError('own exact transition BC initialization required')
    with torch.random.fork_rng(devices=[]):
        reference=SpecialistPolicy(500,size=payload['architecture'].get('size'),
            contract=payload['architecture'].get('contract'))
    if reference.architecture!=payload['architecture']:
        raise ValueError('own exact transition BC architecture required')
    _model_state(reference,payload.get('model'))
    data=load_dataset(payload.get('captures',[]),payload['architecture']['contract'])
    original=validate_source(payload.get('source_checkpoint'))
    expected_pins=dict(data['source_pins'],**original['source_pins'])
    if (expected_pins!=payload.get('dataset_manifest')
            or data['dataset_contracts']!=payload.get('dataset_contracts')
            or payload.get('role')!=data['role']):
        raise ValueError('BC capture provenance mismatch')
    if dataset_manifest([path])!=pins:raise RuntimeError('BC checkpoint changed')
    return dict(payload=payload,data=data,source_pins=dict(expected_pins,**pins))


def apply_initialization(model,path):
    evidence=validate_initialization(path,model.architecture);payload=evidence['payload']
    _model_state(model,payload.get('model'));values=model.state_dict()
    with torch.no_grad():
        for role in model.trainable_roles:
            for key in values:
                if key.startswith(('actor_encoders.'+role+'.','actor_heads.'+role+'.')):
                    values[key].copy_(payload['model'][key])
            selection=model.role_slices[role]
            model.log_std[selection].copy_(payload['model']['log_std'][selection])
    return dict(source_pins=evidence['source_pins'],checkpoint=str(Path(path).resolve()),
        role=model.role,critic='fresh',optimizer='fresh',ppo_updates=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,nargs='+',required=True)
    parser.add_argument('--contract',type=Path,required=True)
    parser.add_argument('--source-checkpoint',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--size',choices=('small','medium','large'),default='medium')
    parser.add_argument('--steps',type=int,default=2000);parser.add_argument('--seed',type=int,default=7)
    args=parser.parse_args();torch.set_num_threads(1);torch.manual_seed(args.seed)
    data=load_dataset(args.capture,json.loads(args.contract.read_text()))
    model=SpecialistPolicy(500,size=args.size,contract=data['contract'])
    initialization=apply_source(model,args.source_checkpoint)
    # Source evidence is also consumed by the BC, not just teacher evidence.
    data['source_pins'].update(initialization['source_pins'])
    data['source_checkpoint']=str(args.source_checkpoint.resolve())
    fit=fit_actor(model,data,steps=args.steps,seed=args.seed,
        log_callback=lambda row:print(json.dumps(row),flush=True))
    save_initialization(model,args.out,data=data,fit_result=fit)


if __name__=='__main__':main()
