"""전축 fresh 학습에서 팔12축 출력 bias의 초기 정렬 prior만 제거한다."""
if __name__ == '__main__':
    import isaacgym
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    _entry = nested_input_paths(); _entry.__enter__()

from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import sys
import torch
from guitar_learning.tool.experiments import structured_press as sp
from guitar_learning.training import finger_skill_runner as official

ROOT=Path(__file__).resolve().parents[3]
BASE_POLICY=sp.StructuredPolicy
CONFIG=dict(schema='guitar_learning.no_alignment_prior.v1',
    changed_initial_tensor='core.support_head.bias[:12]', initial_value=0,
    initial_pose='변경 없음', reference_geometry_observation='변경 없음')


class NoAlignmentPriorPolicy(BASE_POLICY):
    schema='guitar_learning.no_alignment_prior_policy.v1'
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.structured['stage']!='free_v9':raise ValueError('fresh free_v9 only')
        with torch.no_grad():self.core.support_head.bias[:12].zero_()
        self.architecture['no_alignment_prior']=copy.deepcopy(CONFIG)


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def verify():
    study=ROOT.parent;seal=json.loads((study/'source_seal.json').read_text())
    manifest=json.loads((study/'copy_manifest.json').read_text())
    for base,files in ((ROOT,seal['files']),(Path(manifest['original_runtime']),manifest['base_files'])):
        for name,expected in files.items():
            if digest(base/name)!=expected:raise ValueError('sealed source changed: '+str(base/name))
    return digest(study/'source_seal.json')


@contextmanager
def no_prior_context():
    previous=sp.StructuredPolicy,sp.build_settings,sp.structured_runtime,official._pins
    def build(*args,**kwargs):
        settings=previous[1](*args,**kwargs);settings['no_alignment_prior']=copy.deepcopy(CONFIG)
        return settings
    @contextmanager
    def runtime(config,*,initialize_from=None):
        if initialize_from is not None:raise ValueError('source weight transfer is outside this fresh control')
        with previous[2](config):
            factory=official._policy
            def policy(settings,pool):
                if settings.get('no_alignment_prior')!=CONFIG:raise ValueError('no_alignment_prior flag required')
                return factory(settings,pool)
            official._policy=policy
            try:yield
            finally:official._policy=factory
    def pins(settings,out,extra=()):
        return previous[3](settings,out,list(extra)+[Path(__file__).resolve()])
    sp.StructuredPolicy,sp.build_settings,sp.structured_runtime,official._pins=NoAlignmentPriorPolicy,build,runtime,pins
    try:yield
    finally:sp.StructuredPolicy,sp.build_settings,sp.structured_runtime,official._pins=previous


def main():
    if 'evaluate-free-v9' in sys.argv or '--initialize-from' in sys.argv:
        raise ValueError('fresh free_v9 train/resume and exact saved evaluate/render only')
    seal=verify()
    with no_prior_context():sp.main()
    if verify()!=seal:raise ValueError('source seal changed during run')
    out=Path(sys.argv[sys.argv.index('--out')+1])
    path=out/'report.json';report=json.loads(path.read_text())
    report.update(no_alignment_prior=CONFIG,no_alignment_source_seal_sha256=seal)
    if sys.argv[1]=='train' and '--resume' not in sys.argv:
        source=ROOT.parents[1]/'index_full33_seed7_v1/100/train/J/initial.pt'
        a=torch.load(source,map_location='cpu',weights_only=False)
        b=torch.load(out/'J/initial.pt',map_location='cpu',weights_only=False)
        expected={k:x.clone() for k,x in a['model'].items()};expected['core.support_head.bias'][:12]=0
        audit=dict(control_initial_checkpoint=str(source),control_initial_sha256=digest(source),
            model_exact_except_zeroed_arm_bias=all(torch.equal(x,b['model'][k]) for k,x in expected.items()),
            cpu_rng_equal=torch.equal(a['torch_rng'],b['torch_rng']),
            cuda_rng_equal=len(a['cuda_rng'])==len(b['cuda_rng']) and
                all(torch.equal(x,y) for x,y in zip(a['cuda_rng'],b['cuda_rng'])))
        if not all(audit[k] for k in ('model_exact_except_zeroed_arm_bias','cpu_rng_equal','cuda_rng_equal')):
            raise ValueError('full33 control initialization mismatch')
        report['initial_prior_audit']=audit
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    try:main()
    finally:_entry.__exit__(None,None,None)
