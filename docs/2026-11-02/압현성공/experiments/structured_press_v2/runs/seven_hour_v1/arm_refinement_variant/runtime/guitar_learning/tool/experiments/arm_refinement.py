"""손가락의 학습된 관측→행동 함수를 보존하고 팔·지지 가중치만 세부 학습한다."""
if __name__ == '__main__':
    import isaacgym
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    _entry = nested_input_paths(); _entry.__enter__()

from contextlib import contextmanager
import copy
from pathlib import Path
import sys
import torch
from guitar_learning.tool.experiments import variance_variant as v

BASE_VARIANCE = v.VariancePolicy
CONTROL_INITIAL = v.STUDY.parent/'variance_variant/runs/index_B_factor010_seed7/J/initial.pt'
CONFIG = dict(schema='guitar_learning.arm_only_refinement.v1',
    train_actor=['core.support_encoder', 'core.support_head', 'core.support_log_std'],
    freeze_actor=['core.finger_encoder', 'core.finger_heads', 'core.finger_log_std', 'actor_extra'],
    value='기존 독립 가치망 학습 유지', angles='고정하지 않음', factor=.1)


class ArmRefinementPolicy(BASE_VARIANCE):
    schema = 'guitar_learning.arm_refinement_policy.v1'

    def __init__(self, *args, factor, **kwargs):
        if factor != .1: raise ValueError('arm refinement requires factor .1')
        super().__init__(*args, factor=factor, **kwargs)
        for module in (self.core.finger_encoder, self.core.finger_heads, self.actor_extra):
            module.requires_grad_(False)
        self.core.finger_log_std.requires_grad_(False)
        self.architecture['arm_only_refinement'] = copy.deepcopy(CONFIG)

    def actor_parameters(self):
        return [p for module in (self.core.support_encoder, self.core.support_head)
                for p in module.parameters() if p.requires_grad]+[self.core.support_log_std]

    def initialize_from(self, *args, **kwargs):
        # 엄격한 B→free 이전 내부의 이전 모델 생성도 같은 새 schema여야 한다.
        previous = v.VariancePolicy
        v.VariancePolicy = ArmRefinementPolicy
        try: return super().initialize_from(*args, **kwargs)
        finally: v.VariancePolicy = previous


@contextmanager
def refinement_context():
    previous = v.VariancePolicy, v.train_settings, v.variant_runtime, v.initial_audit, v.official._pins
    def settings(factor, updates=100, seed=7):
        result = previous[1](factor, updates, seed)
        result['arm_only_refinement'] = copy.deepcopy(CONFIG)
        return result
    @contextmanager
    def runtime(settings, source=None):
        if settings.get('arm_only_refinement') != CONFIG:
            raise ValueError('explicit arm_only_refinement settings required')
        with previous[2](settings, source): yield
    def pins(settings, out, extra=()):
        return previous[4](settings, out, list(extra)+[Path(__file__).resolve()])
    def audit(out):
        result = previous[3](out)
        a = torch.load(CONTROL_INITIAL, map_location='cpu', weights_only=False)
        b = torch.load(out/'J/initial.pt', map_location='cpu', weights_only=False)
        result.update(variance_control_initial_checkpoint=str(CONTROL_INITIAL),
            variance_control_initial_sha256=v.digest(CONTROL_INITIAL),
            variance_control_model_exact_equal=all(torch.equal(x,b['model'][k]) for k,x in a['model'].items()),
            variance_control_cpu_rng_equal=torch.equal(a['torch_rng'],b['torch_rng']),
            variance_control_cuda_rng_equal=len(a['cuda_rng'])==len(b['cuda_rng']) and
                all(torch.equal(x,y) for x,y in zip(a['cuda_rng'],b['cuda_rng'])))
        if not all(result[k] for k in ('variance_control_model_exact_equal',
                'variance_control_cpu_rng_equal','variance_control_cuda_rng_equal')):
            raise ValueError('variance control initialization mismatch')
        return result
    v.VariancePolicy, v.train_settings, v.variant_runtime = ArmRefinementPolicy, settings, runtime
    v.initial_audit, v.official._pins = audit, pins
    try: yield
    finally:
        v.VariancePolicy, v.train_settings, v.variant_runtime, v.initial_audit, v.official._pins = previous


def main():
    # 자유 v9도 saved flag를 요구한다. 원래 CLI의 strict identity 검사는 그대로 이어진다.
    if '--checkpoint' in sys.argv:
        path=Path(sys.argv[sys.argv.index('--checkpoint')+1])
        saved=torch.load(path,map_location='cpu',weights_only=False)
        settings=v.localize(saved['metadata']['settings'])
        if settings.get('arm_only_refinement') != CONFIG:
            raise ValueError('arm refinement checkpoint/settings required')
    with refinement_context(): v.main()


if __name__ == '__main__':
    try: main()
    finally: _entry.__exit__(None,None,None)
