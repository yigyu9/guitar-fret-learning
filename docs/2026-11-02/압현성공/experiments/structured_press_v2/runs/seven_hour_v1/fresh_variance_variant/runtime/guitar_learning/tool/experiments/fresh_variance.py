"""601열 전축 fresh 학습에서 목표4축 sigma만0.1배로 비교한다."""
if __name__=='__main__':
    import isaacgym
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    _entry=nested_input_paths();_entry.__enter__()

import argparse
from contextlib import contextmanager
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import torch
from guitar_learning.tool.experiments import variance_variant as v

BASE_VARIANCE=v.VariancePolicy
FLAG=dict(schema='guitar_learning.fresh_variance.v1',stage='free_v9',factor=.1,source='fresh; A 가중치 이전 없음')
CONTROL=v.STUDY.parent/'index_full33_seed7_v1/100/train/J/initial.pt'


def policy(*args,**kwargs):
    model=BASE_VARIANCE(*args,**kwargs)
    if model.structured['stage']!='free_v9' or model.variance['factor']!=.1:
        raise ValueError('fresh free_v9 factor .1 required')
    model.architecture['fresh_variance']=copy.deepcopy(FLAG)
    return model


policy.schema=BASE_VARIANCE.schema


def settings(updates=100,seed=7):
    result=v.sp.build_settings('virtual_finger_v9_index_s3_f4','free_v9',
        v.ROOT/'guitar_learning/assets/structured_press_v2/catalog.json',num_envs=64,updates=updates,size='large',seed=seed)
    result.update(variance_variant=v.variance_config(.1,'index'),fresh_variance=copy.deepcopy(FLAG))
    return result


def validate(saved):
    if (saved.get('fresh_variance')!=FLAG or saved.get('structured_press',{}).get('stage')!='free_v9' or
            saved.get('variance_variant')!=v.variance_config(.1,'index')):
        raise ValueError('exact fresh variance settings required; base/B transfer rejected')


@contextmanager
def runtime(saved):
    validate(saved)
    previous=v.VariancePolicy,v.official._pins
    def pins(current,out,extra=()):return previous[1](current,out,list(extra)+[Path(__file__).resolve()])
    v.VariancePolicy,v.official._pins=policy,pins
    try:
        with v.variant_runtime(saved,source=None):yield
    finally:v.VariancePolicy,v.official._pins=previous


def exact(a,b):
    if torch.is_tensor(a):return torch.is_tensor(b) and torch.equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(exact(x,b[k]) for k,x in a.items())
    if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if hasattr(a,'shape'):return type(a)==type(b) and a.shape==b.shape and bool((a==b).all())
    return a==b


def initial_audit(out,resume=None):
    source=resume or CONTROL
    a=torch.load(source,map_location='cpu',weights_only=False)
    b=torch.load(out/'J/initial.pt',map_location='cpu',weights_only=False)
    keys=('model','torch_rng','cuda_rng','python_rng','numpy_rng')
    if resume:keys+=('actor_optimizer','value_optimizer','updates')
    flags={key:exact(a[key],b[key]) for key in keys}
    if not all(flags.values()):raise ValueError('fresh/resume actual initialization mismatch: '+str(flags))
    return dict(source=str(source),source_sha256=v.digest(source),strict_resume=bool(resume),exact_equal=flags)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('train','evaluate','render'))
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--resume',type=Path)
    parser.add_argument('--updates',type=int,default=100)
    parser.add_argument('--seed',type=int,default=7)
    args=parser.parse_args();args.out=args.out.resolve()
    if args.out.exists():raise FileExistsError('existing output must not be overwritten')
    if args.updates<1:parser.error('positive updates required')
    source=args.resume if args.operation=='train' else args.checkpoint
    if args.operation=='train' and args.checkpoint:parser.error('train uses only --resume')
    if args.operation!='train' and (not source or args.resume):parser.error('evaluate/render uses only --checkpoint')
    seal=v.verify_audit();source_sha=v.digest(source) if source else None
    if source:
        payload=torch.load(source,map_location='cpu',weights_only=False)
        v.official._validate_pins(payload['metadata'])
        saved=v.localize(payload['metadata']['settings']);validate(saved)
        if payload['identity']['architecture'].get('fresh_variance')!=FLAG:raise ValueError('fresh architecture marker required')
    else:saved=settings(args.updates,args.seed)
    if args.operation=='train' and (saved['updates']!=args.updates or saved['seed']!=args.seed):
        parser.error('strict resume requires the saved block budget and seed')
    with runtime(saved):
        if args.operation=='train':v.official.run(saved,SimpleNamespace(out=args.out,resume=source))
        elif args.operation=='evaluate':
            v.official.evaluate_checkpoint(source,args.out,num_envs=32,scope='full_song',max_episodes=32)
        else:
            from guitar_learning.tool.demonstration.render_finger_skill import render
            render(source,args.out,num_envs=4,scope='full_song')
    if v.verify_audit()!=seal or (source and v.digest(source)!=source_sha):raise ValueError('source/input changed')
    path=args.out/'report.json';report=json.loads(path.read_text())
    report.update(fresh_variance=FLAG,source_seal_sha256=seal,source_checkpoint_sha256=source_sha)
    if args.operation=='train':report['initial_native_audit']=initial_audit(args.out,args.resume)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    try:main()
    finally:_entry.__exit__(None,None,None)
