"""원본 계측 helper 세 파일의 경로만 보존하는 no-prior 외부 어댑터."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import sys
import reward_trace_probe as probe

FILES=(Path(probe.__file__).resolve(),probe.PROTOCOL,Path(__file__).resolve())


@contextmanager
def adapter_context(paths,official):
    allowed={str(p):p for p in FILES}
    if any(not p.is_file() for p in allowed.values()):raise FileNotFoundError('explicit helper file missing')
    original,pins=paths.resolve_input_path,official._pins
    def resolve(path):
        lexical=paths._lexical(path)
        if str(lexical) in paths._mapping()[0]:return original(path)
        return allowed.get(str(lexical)) or original(path)
    def extra(settings,out,extra=()):
        return pins(settings,out,list(extra)+[Path(__file__).resolve()])
    paths.resolve_input_path,official._pins=resolve,extra
    try:yield
    finally:paths.resolve_input_path,official._pins=original,pins


def run(checkpoint,out):
    if out.exists():raise FileExistsError(str(out))
    runtime=probe.ROOT/'no_alignment_prior_variant/runtime'
    sys.path.insert(0,str(runtime))
    from guitar_learning.native import paths
    from guitar_learning.training import finger_skill_runner as official
    before={str(p):probe.digest(p) for p in FILES+(checkpoint,)}
    facts=dict(path_adapter='exact_existing_helper_whitelist_v1',helper_whitelist=[str(p) for p in FILES],
        path_adapter_sha256=before[str(Path(__file__).resolve())],source_identity='original no-prior strict identity unchanged')
    try:
        with adapter_context(paths,official):probe.run(checkpoint,out,'no_prior')
    finally:
        summary_path=out/'summary.json'
        if summary_path.exists():
            summary=json.loads(summary_path.read_text())
            try:
                if any(probe.digest(Path(p))!=h for p,h in before.items()):raise ValueError('adapter/source changed')
                native=out/'native/report.json'
                if summary.get('completed'):
                    for p,h in summary['output_sha256'].items():
                        if probe.digest(Path(p))!=h:raise ValueError('original output changed before annotation')
                    report=json.loads(native.read_text())
                    if not report.get('completed') or not report.get('lifecycle_verified'):raise ValueError('native incomplete')
                    facts['original_native_report_sha256']=probe.digest(native)
                    report.update(facts);native.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
                    summary['output_sha256'][str(native)]=probe.digest(native)
                summary.update(facts);summary.setdefault('input_sha256',{}).update(before)
            except BaseException as error:
                summary.update(completed=False,adapter_failure=type(error).__name__+': '+str(error))
                raise
            finally:summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    import isaacgym
    run(args.checkpoint.resolve(),args.out.resolve())
