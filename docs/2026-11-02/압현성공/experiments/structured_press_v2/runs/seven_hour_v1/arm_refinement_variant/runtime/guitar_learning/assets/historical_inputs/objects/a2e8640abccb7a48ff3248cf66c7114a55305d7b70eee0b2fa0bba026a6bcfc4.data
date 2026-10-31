"""Evaluate/train the single-A frozen-BC preservation experiment."""
import argparse
import copy
import json
import os
from pathlib import Path


def settings_document(raw):
    from ..recording import digest
    from .train import settings_document as original
    from .anchored_policy import prior_document
    value=copy.deepcopy(raw);prior=prior_document(value.pop('behavior_prior',None))
    parsed=original(value)
    if (parsed['initialization']['mode']!='bc' or parsed['transition']['role']!='left'
            or parsed['transition']['mode']!='single_a'
            or digest(parsed['initialization']['checkpoint'])!=prior['checkpoint_sha256']):
        raise ValueError('exact BC left single_a preservation settings required')
    parsed['behavior_prior']=prior
    return parsed


def source_paths():
    return [Path(__file__).resolve(),Path(__file__).with_name('anchored_policy.py').resolve()]


def initialization_evidence(original,settings,*,require_gate=False):
    from ..imitation import dataset_manifest
    from ..recording import digest
    evidence=original(settings,require_gate=require_gate)
    sources=dataset_manifest(source_paths());pins=dict(evidence['source_pins'])
    if require_gate:
        for folder in settings['initialization']['gate_evaluations']:
            folder=Path(folder);case_settings=folder/'settings.json';inputs=folder/'inputs_before.json'
            if pins.get(str(case_settings))!=digest(case_settings) or pins.get(str(inputs))!=digest(inputs):
                raise ValueError('audited anchored gate settings and source manifest required')
            actual=json.loads(case_settings.read_text());consumed=json.loads(inputs.read_text())
            if actual.get('behavior_prior')!=settings['behavior_prior']:
                raise ValueError('four new native gates must use the exact anchored behavior prior')
            if any(consumed.get(path)!=sha for path,sha in sources.items()):
                raise ValueError('anchored native gates must pin the actual anchored policy and runner')
    for path,sha in sources.items():
        if path in pins and pins[path]!=sha:raise RuntimeError('anchored source evidence changed')
        pins[path]=sha
    return dict(evidence,source_pins=pins)


def run(settings,args):
    import isaacgym
    from unittest.mock import patch
    # Load the original BC reference class before replacing the public policy
    # binding. Its strict archive validator must retain original semantics.
    from . import learning,policy,transfer,train,probe,train_with_teacher_proof
    from .anchored_policy import AnchoredPolicy,initialize_actor
    settings=settings_document(settings)
    if args.mode not in ('eval','train'):raise ValueError('eval/train mode required')
    if (args.mode=='eval' and getattr(args,'resume',None) is not None
            or args.mode=='train' and getattr(args,'checkpoint',None) is not None):
        raise ValueError('eval checkpoint and train resume are separate strict checkpoint paths')
    original=train.initialization_evidence
    def validator(value,*,require_gate=False):
        return initialization_evidence(original,value,require_gate=require_gate)
    class ConfiguredPolicy(AnchoredPolicy):
        def __init__(self,state_dim=500,event_dim=24,size='medium',contract=None):
            super().__init__(state_dim,event_dim,size,contract,behavior_prior=settings['behavior_prior'])
    with patch.object(policy,'SpecialistPolicy',ConfiguredPolicy), \
            patch.object(transfer,'initialize_actor',initialize_actor), \
            patch.object(train,'initialization_evidence',validator):
        if args.mode=='eval':
            args.controller='policy'
            return probe.run(settings,args)
        return train_with_teacher_proof.run(settings,args)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('eval','train'))
    parser.add_argument('--settings',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--episodes',type=int,default=1);parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--resume',type=Path);args=parser.parse_args()
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    import isaacgym
    run(settings_document(json.loads(args.settings.read_text())),args)


if __name__=='__main__':main()
