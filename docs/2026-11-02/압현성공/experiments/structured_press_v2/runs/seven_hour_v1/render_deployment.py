"""원래 native 영상 생성기에 명시적 확률/기댓값 배포 규칙만 연결한다."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
MODES=('stochastic','latent_mean','normalized_action_mean','requested_angle_mean')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_renderer():
    spec=importlib.util.spec_from_file_location('render_deployment_native',ROOT/'render_policy.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@contextmanager
def mode_context(sp,official,payload,mode):
    if mode=='stochastic':
        from noise_probe import sampling_override
        config=payload['metadata']['settings']['structured_press']
        if config['stage']!='free_v9' or config['active_axes']!=list(range(33)):raise ValueError('saved free33 required')
        with sampling_override(sp,official,1.):yield None
    elif mode=='latent_mean':yield None
    else:
        from expected_angle_probe import codec,deployment_context
        positive,negative,_=codec(payload,sp)
        contract=payload['identity']['architecture']['contract']['action']['target_contract']
        finger=payload['metadata']['settings']['structured_press']['finger']
        goal=[i for i,name in enumerate(contract['action_order']) if name.startswith('LH:'+finger)]
        arm=[i for i,name in enumerate(contract['action_order'][:33]) if not name.startswith('LH:')]
        with deployment_context(official,positive,negative,mode,goal_axes=goal,arm_axes=arm) as record:yield record


def annotate(renderer,label,checkpoint,mode,before,impact):
    """새 출력의 태그를 교정하고 native/public MP4가 byteexact 복사인지 확인한다."""
    out=renderer.ROOT/'renders'/label
    report_path,publication_path=out/'report.json',out/'publication.json'
    report=json.loads(report_path.read_text());publication=json.loads(publication_path.read_text())
    if (not report.get('completed') or report.get('lifecycle_verified') is not True or report.get('training_updates')!=0 or
        report.get('policy_unchanged') is not True or report.get('native_pixels') is not True or
        report.get('source_checkpoint_pins_validated') is not True or report.get('source_pins_unchanged') is not True or
        any(report.get(k) for k in ('failure','changed_inputs','cleanup_errors'))):raise ValueError('native render audit incomplete')
    if report['checkpoint_sha256']!=before[str(checkpoint)] or publication['checkpoint_sha256']!=before[str(checkpoint)]:
        raise ValueError('render selected checkpoint SHA mismatch')
    for name,sha in before.items():
        if digest(name)!=sha:raise ValueError('source/checkpoint changed')
    videos=publication['videos']
    if len(videos)!=2 or {v['kind'] for v in videos}!={'hand','fullbody'}:raise ValueError('two native videos required')
    for video in videos:
        source=out/(video['kind']+'.mp4');target=Path(video['path'])
        if (target.parent.resolve()!=renderer.PUBLIC.resolve() or target.suffix!='.mp4' or
            digest(source)!=video['sha256'] or digest(target)!=video['sha256']):raise ValueError('native/public media mismatch')
    if any(path.is_file() and path.suffix!='.mp4' for path in renderer.PUBLIC.iterdir()):raise ValueError('public video directory contains non-MP4 files')
    evidence=dict(original_report_sha256=digest(report_path),original_publication_sha256=digest(publication_path),
        original_publication_annotations={k:publication.get(k) for k in ('image_source','physics_or_policy_modified')},
        source_sha256=before,observed_request_impact=impact)
    facts=dict(diagnostic_only=True,policy_mode=mode,deployment_rule=mode,physics_unchanged=True,weights_unchanged=True,
        saved_gaussian_distribution_unchanged=True,action_rule_changed=mode!='latent_mean',optimizer_updates_difference=0,
        image_source='native camera pixels; '+mode+' deployment diagnostic',physics_or_policy_modified=mode!='latent_mean',
        policy_unchanged_interpretation='native state_dict preservation audit; deployment rule is separately declared',
        interpretation='native rendering of explicitly selected execution rule; not retraining or official mean-policy evaluation',
        deployment_annotation=evidence)
    report.update(facts);publication.update(facts)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    publication_path.write_text(json.dumps(publication,ensure_ascii=False,indent=2)+'\n')
    return report,publication


def run(checkpoint,label,mode):
    if mode not in MODES:raise ValueError('unknown deployment mode')
    if Path(label).name!=label or label in ('.','..'):raise ValueError('label must be one directory name')
    checkpoint=checkpoint.resolve();sys.path.insert(0,str(ROOT.parents[1]/'runtime'))
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    with nested_input_paths():
        import torch
        from guitar_learning.tool.experiments import structured_press as sp
        from guitar_learning.training import finger_skill_runner as official
        from noise_probe import verify_source_seal
        seal=verify_source_seal();renderer=load_renderer()
        if (renderer.ROOT/'renders'/label).exists():raise FileExistsError('native output already exists')
        if any((renderer.PUBLIC/(label+'_'+kind+'.mp4')).exists() for kind in ('hand','fullbody')):raise FileExistsError('public output already exists')
        payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
        official._validate_metadata_schema(payload['metadata']);official._validate_pins(payload['metadata'])
        config=payload['metadata']['settings']['structured_press']
        if config['stage']!='free_v9' or config['active_axes']!=list(range(33)):raise ValueError('saved base free33 only')
        helpers=[ROOT/name for name in ('render_policy.py','noise_probe.py','expected_angle_probe.py')]
        before={str(path):digest(path) for path in [checkpoint,Path(__file__).resolve()]+helpers}
        original_pins=official._pins
        def pins(settings,out,extra=()):return original_pins(settings,out,list(extra)+[Path(__file__).resolve()]+helpers)
        official._pins=pins;argv=sys.argv
        try:
            with mode_context(sp,official,payload,mode) as impact:
                sys.argv=[str(ROOT/'render_policy.py'),'--checkpoint',str(checkpoint),'--label',label]
                renderer.main()
        finally:sys.argv=argv;official._pins=original_pins
        if verify_source_seal()!=seal:raise ValueError('frozen runtime source seal changed')
        return annotate(renderer,label,checkpoint,mode,before,impact)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True);parser.add_argument('--label',required=True)
    parser.add_argument('--mode',choices=MODES,required=True);args=parser.parse_args()
    import isaacgym
    run(args.checkpoint,args.label,args.mode)
