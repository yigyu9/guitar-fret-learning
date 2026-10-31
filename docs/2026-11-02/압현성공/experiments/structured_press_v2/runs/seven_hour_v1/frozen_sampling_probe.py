"""고정 체크포인트의 원래 Gaussian을 표본화한다. 평균 정책 평가/학습이 아니다."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import sys
import reward_trace_probe as trace

ROOT=Path(__file__).resolve().parent


@contextmanager
def sampling_context(sp, official):
    from noise_probe import sampling_override
    original=official._pins
    def pins(settings,out,extra=()):
        return original(settings,out,list(extra)+[Path(__file__).resolve()])
    official._pins=pins
    try:
        with sampling_override(sp,official,1.):yield
    finally:
        official._pins=original


def annotate(out, before):
    """완료와 원래 SHA를 검사한 뒤 진단 표기를 추가하고 report 출력 SHA를 갱신한다."""
    path=out/'summary.json'
    if not path.exists():return
    summary=json.loads(path.read_text());native_path=out/'native/report.json'
    facts=dict(policy_mode='stochastic_frozen_checkpoint',sampling_scale=1.,
        saved_mean_and_std_unchanged=True,weights_frozen_during_evaluation=True,
        sampling_scope='all33 active axes; exact saved Gaussian including original forward std floors',
        interpretation='first32 episodes of one frozen stochastic policy; not mean policy or changing-policy training block')
    try:
        if any(trace.digest(Path(p))!=h for p,h in before.items()):raise ValueError('source helper/checkpoint changed')
        if summary.get('completed'):
            for p,h in summary['output_sha256'].items():
                if trace.digest(Path(p))!=h:raise ValueError('native output changed before annotation')
        if native_path.exists():
            native=json.loads(native_path.read_text())
            if summary.get('completed') and (not native.get('completed') or not native.get('lifecycle_verified') or
                    any(native.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'))):
                raise ValueError('original native lifecycle incomplete')
            facts['original_native_report_sha256']=trace.digest(native_path)
            native.update(facts);native_path.write_text(json.dumps(native,ensure_ascii=False,indent=2)+'\n')
            if summary.get('completed'):summary['output_sha256'][str(native_path)]=trace.digest(native_path)
        summary.update(facts);summary.setdefault('input_sha256',{}).update(before)
    except BaseException as error:
        summary.update(completed=False,annotation_failure=type(error).__name__+': '+str(error))
        raise
    finally:
        path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        (out/'SUMMARY.md').write_text('# 고정 확률 정책의 원본 보상 진단\n\n완료: '+str(summary.get('completed',False))+
            '\n\n저장된 Gaussian 전체 활성33축을 원래 scale1로 표본화했다. 평균 정책 평가가 아니다. '
            '가중치와분포규칙은고정되며 학습update는없다. 실패도최초32 episode분모에포함한다. '
            '원래native완료·trace대조·source검사를통과한자료만비교한다.\n')


def run(checkpoint,out):
    sys.path.insert(0,str(trace.STUDY/'runtime'))
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    # 정적 준비 입력 경로를 읽는 모듈보다 먼저 경로 매핑을 적용한다.
    with nested_input_paths():return _run(checkpoint,out)


def _run(checkpoint,out):
    if out.exists():raise FileExistsError(str(out))
    import torch
    import noise_probe
    from guitar_learning.tool.experiments import structured_press as sp
    from guitar_learning.training import finger_skill_runner as official
    payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
    config=payload['metadata']['settings']['structured_press']
    if config['stage']!='free_v9' or config['active_axes']!=list(range(33)):
        raise ValueError('saved base free_v9 all33 checkpoint required')
    paths=(checkpoint,Path(__file__).resolve(),Path(trace.__file__).resolve(),Path(noise_probe.__file__).resolve(),trace.PROTOCOL)
    before={str(p):trace.digest(p) for p in paths}
    try:
        with sampling_context(sp,official):trace.run(checkpoint,out,'base')
    finally:
        annotate(out,before)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    import isaacgym
    run(args.checkpoint.resolve(),args.out.resolve())
