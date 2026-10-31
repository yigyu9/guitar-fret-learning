"""봉인된 fresh 분산 도구의 감사 기준만 원본 seed17로 지정한다."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
STUDY=ROOT.parent.parent
CONTROL=STUDY/'full33_seed17/100/train/J/initial.pt'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@contextmanager
def audit_context(f):
    """정책·설정·RNG는 변경하지 않고 생성 계보와 비교 경로만 추가한다."""
    original=f.CONTROL,f.v.official._pins,f.v.official.checkpoint_metadata
    creation=[Path(__file__).resolve(),CONTROL]
    def pins(settings,out,extra=()):return original[1](settings,out,list(extra)+creation)
    def metadata(*args,**kwargs):
        kwargs['lineage']=list(dict.fromkeys([Path(p).resolve() for p in kwargs.get('lineage',())]+creation))
        return original[2](*args,**kwargs)
    f.CONTROL,f.v.official._pins,f.v.official.checkpoint_metadata=CONTROL,pins,metadata
    try:yield
    finally:f.CONTROL,f.v.official._pins,f.v.official.checkpoint_metadata=original


def run():
    # Isaac Gym과 경로 보정은 torch 및 정적 입력을 읽는 최초 모듈보다 앞선다.
    import isaacgym
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    with nested_input_paths():
        from guitar_learning.tool.experiments import fresh_variance as f
        args=sys.argv[1:]
        if '--seed' not in args or args[args.index('--seed')+1]!='17':
            raise ValueError('감사 경로가 seed17이므로 --seed 17을 명시해야 함')
        files=[Path(__file__).resolve(),CONTROL,Path(f.__file__),Path(f.v.__file__),
            ROOT.parent/'source_seal.json']
        for key in ('--checkpoint','--resume'):
            if key in args:files.append(Path(args[args.index(key)+1]).resolve())
        before={str(p):sha(p) for p in files}
        for key in ('--checkpoint','--resume'):
            if key in args:
                payload=f.torch.load(args[args.index(key)+1],map_location='cpu',weights_only=False)
                settings=payload['metadata']['settings']
                if settings['seed']!=17 or 'structured_transfer' in settings:
                    raise ValueError('seed17 fresh 체크포인트만 허용')
        try:
            with audit_context(f):f.main()
        finally:
            if any(sha(p)!=value for p,value in before.items()):raise ValueError('원본/도구 SHA 변경')
        out=Path(args[args.index('--out')+1]).resolve()
        path=out/'report.json';report=json.loads(path.read_text())
        report['seed17_bootstrap']=dict(input_sha256=before,only_audit_control_target_changed=True,
            source_A_transfer=False,policy_settings_rng_mutated_by_bootstrap=False)
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':run()
