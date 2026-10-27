"""Only add the reviewed graphics-isolation sources to an unchanged control ABI."""
import copy
import hashlib
import json
from pathlib import Path

ADDED_FILES = ('deadline_graphics_v1.py','deadline_native_v8.py','deadline_graphics_migration_v1.py',
               'run_deadline_training_v9.py','test_deadline_graphics_v1.py','run_graphics_reset_probe_v1.py')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def migrate_payload(payload, abi, config, allowed_additions):
    if payload['schema']!='deadline_pilot_ppo_v1' or digest(payload['abi'])!=payload['abi_sha256']:
        raise ValueError('source checkpoint schema/digest invalid')
    if payload['ppo_config']!=config: raise ValueError('PPO configuration changed')
    old=copy.deepcopy(payload['abi']);new=copy.deepcopy(abi)
    old_sources=old.pop('source_sha256');new_sources=new.pop('source_sha256')
    if old!=new: raise ValueError('physics/reward/observation/control ABI changed')
    if any(new_sources.get(p)!=h for p,h in old_sources.items()):
        raise ValueError('existing source changed or disappeared')
    if set(new_sources)-set(old_sources)!=set(allowed_additions):
        raise ValueError('unreviewed added source')
    result=dict(payload,abi=copy.deepcopy(abi),abi_sha256=digest(abi),
                resume_scope='model/Adam/RMS/RNG/counters preserved; reviewed graphics-only source addition; fresh physical episode')
    return result


def adopt_checkpoint(path, trainer, output):
    import torch
    path=Path(path);output=Path(output)
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    original=torch.load(path,map_location='cpu',weights_only=True)
    from dataclasses import asdict
    root=Path(__file__).resolve().parent
    additions=[str(root/n) for n in ADDED_FILES]
    result=migrate_payload(original,trainer.abi,asdict(trainer.config),additions)
    with output.open('xb') as f: torch.save(result,f)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=before:raise AssertionError('source checkpoint modified')
    return {'source_checkpoint':str(path.resolve()),'source_sha256':before,
        'adopted_checkpoint':str(output.resolve()),'adopted_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'source_updates':original['updates'],'source_transitions':original['transitions'],
        'changed_payload_fields':['abi','abi_sha256','resume_scope'],'added_sources':additions,
        'scope':'graphics resource implementation only; original numerical policy/optimizer/RNG retained; code ABI adoption, not unchanged-ABI resume'}
