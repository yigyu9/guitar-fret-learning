"""Clone successful local interventions while anchoring the source policy prefix."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

import numpy as np
import torch

from guitar_learning.imitation.imitation import dataset_manifest, _valid_model_state
from guitar_learning.imitation.imitation_v2 import canonical_contract
from guitar_learning.training.parallel import FIELDS

SCHEMA = 'guitar_learning.local_skill_bc.v1'
SETTINGS_SCHEMA = 'guitar_learning.local_skills.v1'
CAPTURE_SCHEMA = 'guitar_learning.local_skill_probe.v1'
GATE_SCHEMA = 'guitar_learning.local_skill_gate.v1'
SHAPES = dict(state=(563,), events=(64, 24), mask=(64,),
              priority_events=(2, 24), priority_mask=(2,), action=(39,),
              intervention=(), policy_action=(39,), task_time_s=())


def contract_digest(contract):
    value = json.dumps(canonical_contract(contract), sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(value.encode()).hexdigest()


def successful_episode(episode, role):
    timing = episode.get('timing', {})
    quality = episode.get('musical_quality', {})
    return (episode.get('valid') is True and episode.get('reason') == 'timeline_complete'
            and episode.get('steps') == 420 and episode.get('task_time_s') == 7.
            and timing.get('safety_invalidated') is False
            and timing.get('timing_only_stage_success') is True
            and quality.get('role') == role and quality.get('stage_success') is True)


def _contract(contract, role):
    from guitar_learning.quality.musical_quality import metadata
    value = canonical_contract(contract)
    obs = value.get('observation', {})
    if (value.get('schema') != 'guitar_learning.training.v1'
            or obs.get('dimension') != 563 or len(obs.get('fields', [])) != 563
            or len(obs.get('scales', [])) != 563 or obs.get('event_dim') != 24
            or obs.get('capacity') != 64 or obs.get('priority_slots') != 2
            or value.get('action', {}).get('dimension') != 39
            or value.get('task', {}).get('duration_s') != 7.
            or value['task'].get('specialist', {}).get('role') != role
            or value['task'].get('musical_quality') != canonical_contract(metadata())
            or value.get('reward', {}).get('musical_quality') != canonical_contract(metadata())
            or value.get('termination', {}).get('preparation_seconds') != 0.
            or value['termination'].get('physics_hz') != 240
            or value['termination'].get('control_hz') != 60):
        raise ValueError('unchanged native seven-second563 quality contract required')
    return value


def _capture_result(result):
    role = result.get('role')
    if (result.get('schema') != CAPTURE_SCHEMA or role not in ('left', 'right')
            or any(result.get(k) is not True for k in
                   ('completed', 'success', 'source_unchanged', 'physical_flags_ok'))
            or result.get('forbidden_calls') != [] or result.get('failure') is not None
            or result.get('cleanup_error') not in (None, False)
            or result.get('changed_inputs', []) != [] or result.get('missing_import_pins', []) != []
            or not successful_episode(result.get('episode', {}), role)):
        raise ValueError('full original quality and safety successful native capture required')
    return role


def _search(folder, result):
    path=folder.parent/'result.json'
    if not path.is_file():raise ValueError('finalized parent search required; live cases cannot be fitted')
    search=json.loads(path.read_text())
    if (search.get('schema') != 'guitar_learning.local_skill_search.v1'
            or search.get('role') != result['role'] or search.get('source_unchanged') is not True
            or search.get('cleanup_error') not in (None,False) or search.get('failure') is not None
            or result.get('candidate') not in search.get('successful_candidates', [])
            or result not in search.get('candidates', [])):
        raise ValueError('finalized successful case with clean native search shutdown required')
    return path


def _arrays(data):
    role = data['role']
    for key, shape in SHAPES.items():
        value = data.get(key)
        if not isinstance(value, np.ndarray) or value.shape != (420,)+shape:
            raise ValueError('complete420-row563 capture required: '+key)
        if key in ('mask', 'priority_mask', 'intervention'):
            if value.dtype != np.bool_: raise ValueError('boolean masks required: '+key)
        elif value.dtype.kind != 'f' or not np.isfinite(value).all():
            raise ValueError('finite floating capture required: '+key)
    inactive = slice(33, 39) if role == 'left' else slice(0, 33)
    for key in ('action', 'policy_action'):
        if np.any(np.abs(data[key]) > 1) or np.any(data[key][:, inactive] != 0):
            raise ValueError('bounded action39 with exactly zero inactive hand required')
    local = data['intervention']
    if not local.any() or local.all(): raise ValueError('both intervention and preservation rows required')
    if not np.allclose(data['task_time_s'], np.arange(420)/60., atol=1e-8, rtol=0):
        raise ValueError('actual consecutive before-action policy clock required')
    if not np.allclose(data['action'][~local], data['policy_action'][~local], atol=1e-7, rtol=0):
        raise ValueError('nonintervention rows must retain the source policy action')


def construct(architecture, device='cpu'):
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    a = architecture
    if (a.get('schema') != 'guitar_specialists39_v1' or a.get('state_dim') != 563
            or a.get('role') not in ('left', 'right') or a.get('frozen_partner') is not False):
        raise ValueError('own single-hand563 architecture required')
    _contract(a['contract'], a['role'])
    # Creating fresh, unused value networks must not restore or consume source RNG.
    with torch.random.fork_rng(devices=[]):
        model = SpecialistPolicy(563, event_dim=a['event_dim'], size=a['size'],
            role=a['role'], frozen_partner=False, contract=a['contract'])
    if canonical_contract(model.architecture) != canonical_contract(a):
        raise ValueError('complete unchanged architecture required')
    return model.to(device)


def load_capture(folder):
    folder = Path(folder).resolve()
    paths = [folder/name for name in ('result.json', 'reset.json', 'demonstration.npz')]
    first = dataset_manifest(paths)
    result = json.loads(paths[0].read_text()); role = _capture_result(result)
    source = Path(result.get('source_checkpoint', ''))
    if not source.is_absolute() or not source.is_file(): raise ValueError('absolute source checkpoint required')
    paths.append(_search(folder,result))
    manifest = dataset_manifest(paths+[source])
    if any(manifest[p] != sha for p, sha in first.items()): raise RuntimeError('capture changed during loading')
    if manifest[str(source.resolve())] != result.get('source_checkpoint_sha256'):
        raise ValueError('native source checkpoint SHA mismatch')
    contract = json.loads(paths[1].read_text()).get('training_contract')
    canonical = _contract(contract, role)
    if result.get('training_contract_sha256') not in (None, contract_digest(contract)):
        raise ValueError('capture contract SHA mismatch')
    payload = torch.load(source, map_location='cpu', weights_only=False)
    identity = payload.get('identity', {})
    architecture = identity.get('architecture', {})
    if (identity.get('schema') != 'guitar_learning_ppo_v1'
            or type(payload.get('updates')) is not int or payload['updates'] < 1
            or architecture.get('role') != role
            or canonical_contract(architecture.get('contract')) != canonical):
        raise ValueError('same completed563 PPO source and exact native contract required')
    model = construct(architecture)
    _valid_model_state(model, payload.get('model'))
    with np.load(paths[2], allow_pickle=False) as archive:
        if set(archive.files) != set(SHAPES): raise ValueError('exact local capture array fields required')
        data = {key: archive[key].copy() for key in archive.files}
    data.update(role=role, contract=copy.deepcopy(contract), manifest=manifest, result=result,
        capture=str(folder), source_architecture=architecture, source_model=payload['model'])
    _arrays(data)
    model.load_state_dict(payload['model']);model.eval()
    with torch.no_grad():
        inputs=[torch.as_tensor(data[k],dtype=torch.bool if 'mask' in k else torch.float32) for k in FIELDS]
        action=model.act(*inputs,deterministic=True)['action'].cpu().numpy()
    if not np.allclose(action,data['policy_action'],atol=1e-5,rtol=0):
        raise ValueError('policy_action must be the captured source policy on these before-action observations')
    if dataset_manifest(paths+[source]) != manifest: raise RuntimeError('capture/source changed during loading')
    return data


def fit_actor(model, data, *, steps=1000, lr=1e-4, batch_size=120, seed=7, log_callback=None):
    _arrays(data)
    if (type(steps) is not int or not 1 <= steps <= 2000 or type(batch_size) is not int or batch_size < 1
            or type(seed) is not int or isinstance(lr, bool) or not math.isfinite(lr) or lr <= 0):
        raise ValueError('bounded1..2000 BC steps, positive batch/rate and integer seed required')
    if (canonical_contract(model.architecture) != canonical_contract(data['source_architecture'])
            or canonical_contract(model.architecture['contract']) != canonical_contract(data['contract'])):
        raise ValueError('same source architecture and full563 task contract required')
    if any(not torch.equal(v.detach().cpu(), data['source_model'][k]) for k,v in model.state_dict().items()):
        raise ValueError('BC must start from the exact captured source model')
    role = data['role']; selection = model.role_slices[role]; device = next(model.parameters()).device
    inputs = [torch.as_tensor(data[k], device=device, dtype=torch.bool if 'mask' in k else torch.float32) for k in FIELDS]
    teacher = torch.as_tensor(data['action'][:, selection], device=device, dtype=torch.float32)
    policy = torch.as_tensor(data['policy_action'][:, selection], device=device, dtype=torch.float32)
    groups = [torch.from_numpy(np.flatnonzero(data['intervention'])),
              torch.from_numpy(np.flatnonzero(~data['intervention']))]
    parameters = [*model.actor_encoders[role].parameters(), *model.actor_heads[role].parameters()]
    before = {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    rng = torch.get_rng_state().clone()
    optimizer = torch.optim.Adam(parameters, lr=lr)
    generator = torch.Generator().manual_seed(seed); log = []
    def predict(indices):
        return model.actor_heads[role](model.actor_encoders[role](*[v[indices] for v in inputs])).tanh()
    def measure(step):
        with torch.no_grad():
            errors = [predict(g.to(device))-target[g.to(device)] for g,target in zip(groups,(teacher,policy))]
        row = dict(step=step, local_mse=float(errors[0].square().mean()),
            prefix_mse=float(errors[1].square().mean()), local_max_abs_error=float(errors[0].abs().max()),
            prefix_max_abs_error=float(errors[1].abs().max()))
        if not all(math.isfinite(v) for v in row.values()): raise ValueError('nonfinite local BC fit')
        log.append(row)
        if log_callback: log_callback(copy.deepcopy(row))
        return row
    initial = measure(0)
    for step in range(1, steps+1):
        chosen = [g[torch.randperm(len(g), generator=generator)[:min(batch_size,len(g))]].to(device) for g in groups]
        loss = .5*sum((predict(i)-target[i]).square().mean() for i,target in zip(chosen,(teacher,policy)))
        if not torch.isfinite(loss): raise ValueError('nonfinite local BC loss')
        optimizer.zero_grad(set_to_none=True); loss.backward(); optimizer.step()
        if step % 100 == 0 or step == steps: final = measure(step)
    optimizer.zero_grad(set_to_none=True)
    changed = [k for k,v in model.state_dict().items() if not torch.equal(before[k],v.detach().cpu())]
    allowed = ('actor_encoders.'+role+'.', 'actor_heads.'+role+'.')
    if any(not k.startswith(allowed) for k in changed) or not torch.equal(rng,torch.get_rng_state()):
        raise RuntimeError('BC changed critic/inactive/std/buffer or global torch RNG')
    _valid_model_state(model, model.state_dict())
    return dict(initial=initial, final=final, steps=steps, learning_rate=lr, batch_size_per_group=batch_size,
        seed=seed, local_rows=len(groups[0]), preservation_rows=len(groups[1]), log=log,
        changed_model_keys=changed, loss='0.5*(local teacher MSE + nonintervention source-policy MSE)',
        scope='action fit only; preservation error is measured, not guaranteed native prefix preservation')


def save_initialization(model, path, *, data, fit_result):
    if dataset_manifest(data['manifest']) != data['manifest']: raise RuntimeError('capture/source changed before save')
    state = {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    _valid_model_state(model,state)
    payload = dict(schema=SCHEMA, architecture=copy.deepcopy(model.architecture), role=data['role'], model=state,
        dataset_manifest=copy.deepcopy(data['manifest']), capture=data['capture'],
        source_checkpoint=data['result']['source_checkpoint'], source_checkpoint_sha256=data['result']['source_checkpoint_sha256'],
        training=copy.deepcopy(fit_result), scope='selected actor/std initialization; no PPO updates/optimizer or native policy success claim')
    path = Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='local-bc-',suffix='.pt',dir=str(path.parent));os.close(descriptor)
    try: torch.save(payload,temporary);os.link(temporary,path)
    finally: os.unlink(temporary)


def load_initialization(path):
    path = Path(path).resolve(); pinned = dataset_manifest([path])
    payload = torch.load(path,map_location='cpu',weights_only=False)
    if (payload.get('schema') != SCHEMA or payload.get('role') not in ('left','right')
            or any(k in payload for k in ('identity','updates','actor_optimizer','value_optimizer'))
            or not isinstance(payload.get('training'),dict) or not payload.get('dataset_manifest')):
        raise ValueError('explicit local563 BC initialization, not PPO state, required')
    model = construct(payload['architecture']);_valid_model_state(model,payload.get('model'))
    if payload['role'] != model.role: raise ValueError('BC role differs from architecture')
    manifest = payload['dataset_manifest']
    if dataset_manifest(manifest) != manifest: raise RuntimeError('BC dataset/source changed')
    capture = Path(payload['capture']).resolve();result_path = capture/'result.json'
    result = json.loads(result_path.read_text());role = _capture_result(result)
    required = [capture/'result.json',capture/'reset.json',capture/'demonstration.npz',_search(capture,result),
                Path(result['source_checkpoint']).resolve()]
    if (any(str(p) not in manifest for p in required) or role != model.role
            or result['source_checkpoint'] != payload['source_checkpoint']
            or result['source_checkpoint_sha256'] != payload['source_checkpoint_sha256']
            or manifest[str(required[-1])] != payload['source_checkpoint_sha256']
            or canonical_contract(json.loads((capture/'reset.json').read_text())['training_contract'])
               != canonical_contract(model.architecture['contract'])):
        raise ValueError('BC capture/source/full contract provenance mismatch')
    if dataset_manifest([path]) != pinned: raise RuntimeError('BC initialization changed while loading')
    if dataset_manifest(manifest) != manifest:raise RuntimeError('BC dataset/source changed while reading provenance')
    return payload


def apply_actor_initialization(model, path, *, kind):
    if kind != 'bc': raise ValueError('explicit local BC kind required')
    manifest=dataset_manifest([path])
    payload = load_initialization(path)
    if canonical_contract(payload['architecture']) != canonical_contract(model.architecture):
        raise ValueError('exact563 architecture/role/native task contract required')
    _valid_model_state(model,payload['model']);expected = model.state_dict();role=model.role
    if dataset_manifest([path]) != manifest:raise RuntimeError('BC initialization changed before actor transfer')
    with torch.no_grad():
        for k,v in payload['model'].items():
            if k.startswith(('actor_encoders.'+role+'.','actor_heads.'+role+'.')):expected[k].copy_(v)
        selection=model.role_slices[role];model.log_std[selection].copy_(payload['model']['log_std'][selection])
    return dict(schema=SCHEMA,path=str(Path(path).resolve()),sha256=manifest[str(Path(path).resolve())],
        source_checkpoint_sha256=payload['source_checkpoint_sha256'],dataset_manifest=payload['dataset_manifest'],
        scope='selected actor/std only; fresh PPO critics/Adam/RNG/counter; native success not inherited')


def settings_document(raw):
    from guitar_learning.tool.training.train_actionable_preparation import settings_document as base_settings
    from guitar_learning.quality.musical_quality import metadata
    if not isinstance(raw,dict):raise ValueError('settings object required')
    value=copy.deepcopy(raw);local=value.pop('local_skills',None);quality=value.pop('musical_quality',None)
    if (not isinstance(local,dict) or set(local)-{'schema','evaluation_gate'}
            or local.get('schema') != SETTINGS_SCHEMA
            or (quality is not None and quality != metadata())):
        raise ValueError('explicit local-skills schema and unchanged quality metadata required')
    if 'evaluation_gate' in local and (not isinstance(local['evaluation_gate'],str) or not Path(local['evaluation_gate']).is_absolute()):
        raise ValueError('absolute evaluation gate path required')
    settings=base_settings(value)
    if settings['actor_initialization_kind'] != 'bc':raise ValueError('local path requires explicit bc initialization kind')
    payload=load_initialization(settings['actor_initialization'])
    architecture=payload['architecture']
    if (architecture['role'] != settings['specialist']['role'] or architecture['size'] != settings['size']
            or canonical_contract(architecture['contract']['task']['timing']['config']) != canonical_contract(settings['timing'])):
        raise ValueError('local BC role/size/timing must match the unchanged native task')
    settings.update(musical_quality=metadata(),local_skills=local)
    return settings


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--steps',type=int,default=1000);parser.add_argument('--learning-rate',type=float,default=1e-4)
    parser.add_argument('--batch-size',type=int,default=120);parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--device',default='cpu');args=parser.parse_args()
    torch.set_num_threads(1);data=load_capture(args.capture);out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    model=construct(data['source_architecture'],args.device);model.load_state_dict(data['source_model'])
    from guitar_learning.training.recording import write, digest
    write(out/'inputs_before.json',data['manifest'])
    with (out/'fit.jsonl').open('x') as stream:
        def log(row):stream.write(json.dumps(row,allow_nan=False)+'\n');stream.flush()
        result=fit_actor(model,data,steps=args.steps,lr=args.learning_rate,batch_size=args.batch_size,seed=args.seed,log_callback=log)
    checkpoint=out/'actor_initialization.pt';save_initialization(model,checkpoint,data=data,fit_result=result)
    write(out/'report.json',dict(completed=True,fit=result,checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),
        source_unchanged=dataset_manifest(data['manifest'])==data['manifest'],ppo_updates=0,
        scope='successful teacher action fit only; independent full-policy native gate required before PPO'))


if __name__=='__main__':main()
