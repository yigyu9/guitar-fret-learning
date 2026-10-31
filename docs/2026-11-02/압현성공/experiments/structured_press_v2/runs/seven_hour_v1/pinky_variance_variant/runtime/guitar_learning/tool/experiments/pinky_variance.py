"""같은 소지 A200→B100에서 목표4축 sigma 배율0.1만 비교한다."""
if __name__=='__main__':
    import isaacgym
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    _entry=nested_input_paths();_entry.__enter__()

from contextlib import contextmanager
from pathlib import Path
import sys
import torch
from guitar_learning.tool.experiments import variance_variant as v

TRANSFER=v.ROOT/'transfer_inputs/pinky_A200.pt'
CONTROL=v.STUDY.parent/'pinky_B_seed7_v1/100/train/J/initial.pt'
FLAG=dict(schema='guitar_learning.pinky_variance_experiment.v1',source_stage='A200',factor=.1)


@contextmanager
def pinky_context():
    previous=v.TRANSFER,v.train_settings,v.initial_audit,v.variant_runtime,v.official._pins
    def settings(factor,updates=100,seed=7):
        if factor!=.1:raise ValueError('pinky comparison requires factor .1')
        result=previous[1](factor,updates,seed)
        if result['structured_press']['finger']!='pinky':raise ValueError('pinky source required')
        result['pinky_variance_experiment']=dict(FLAG)
        result['structured_transfer']['scope']='엄격한 소지 A200→분산0.1 B 모델만 이전; 새 Adam/RNG'
        return result
    def audit(out):
        source=torch.load(TRANSFER,map_location='cpu',weights_only=False)
        initial=torch.load(out/'J/initial.pt',map_location='cpu',weights_only=False)
        exact=all(k=='active_mask' or torch.equal(x,initial['model'][k]) for k,x in source['model'].items())
        if not exact:raise ValueError('pinky A200 initial weights mismatch')
        result=dict(all_initial_model_tensors_equal_source_except_active_mask=True,
            source_checkpoint=str(TRANSFER),source_sha256=v.digest(TRANSFER),control_status='pending')
        if CONTROL.exists():
            control=torch.load(CONTROL,map_location='cpu',weights_only=False)
            result.update(control_status='verified',control_initial_checkpoint=str(CONTROL),control_initial_sha256=v.digest(CONTROL),
                control_model_exact_equal=all(torch.equal(x,initial['model'][k]) for k,x in control['model'].items()),
                control_cpu_torch_rng_equal=torch.equal(control['torch_rng'],initial['torch_rng']),
                control_cuda_rng_equal=len(control['cuda_rng'])==len(initial['cuda_rng']) and
                    all(torch.equal(x,y) for x,y in zip(control['cuda_rng'],initial['cuda_rng'])))
            if not all(result[k] for k in ('control_model_exact_equal','control_cpu_torch_rng_equal','control_cuda_rng_equal')):
                raise ValueError('pinky control initialization mismatch')
        return result
    @contextmanager
    def runtime(settings,source=None):
        if settings.get('pinky_variance_experiment')!=FLAG:raise ValueError('pinky experiment flag required')
        with previous[3](settings,source):yield
    def pins(settings,out,extra=()):return previous[4](settings,out,list(extra)+[Path(__file__).resolve()])
    v.TRANSFER,v.train_settings,v.initial_audit,v.variant_runtime,v.official._pins=TRANSFER,settings,audit,runtime,pins
    try:yield
    finally:v.TRANSFER,v.train_settings,v.initial_audit,v.variant_runtime,v.official._pins=previous


def main():
    if '--checkpoint' in sys.argv:
        saved=torch.load(Path(sys.argv[sys.argv.index('--checkpoint')+1]),map_location='cpu',weights_only=False)
        if v.localize(saved['metadata']['settings']).get('pinky_variance_experiment')!=FLAG:
            raise ValueError('pinky experiment checkpoint required')
    with pinky_context():v.main()


if __name__=='__main__':
    try:main()
    finally:_entry.__exit__(None,None,None)
