"""V5 물리·원장을 재사용하고 마지막 비용 Linear의 초기값만 0으로 둔다."""
import copy
import importlib.util
from pathlib import Path
import sys
import torch

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'index_release_success_settlement_v5'
spec = importlib.util.spec_from_file_location('cost_prior_v6_v5_runtime', SOURCE/'runtime.py')
v5 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v5
spec.loader.exec_module(v5)
base, v2, ADAPTER, shared = v5.base, v5.v2, v5.ADAPTER, v5.shared
SCHEMA = 'diagnostic.cost_prior_zero.v6'
COST_PRIOR = dict(schema=SCHEMA, tensors=['cost_critic.weight','cost_critic.bias'],
    initialization='zero after unchanged parent constructor RNG consumption', learnable=True,
    other_69_tensors='unchanged', cost_weight=1., failure_cost_and_termination='unchanged')


def attach(contract):
    result = v5.attach(contract)
    result['diagnostics']['cost_prior'] = copy.deepcopy(COST_PRIOR)
    return result


def settings():
    result = v5.settings()
    result['simple_start']['initialization'] = 'fresh V6 seed7 current557/Jv3; cost head zero only; same fit1000 then PPO300'
    return result


class GoalPolicy(v5.GoalPolicy):
    schema = SCHEMA+'.goal_policy'

    def __init__(self, *, contract, size='large'):
        if contract.get('diagnostics',{}).get('cost_prior') != COST_PRIOR:
            raise ValueError('Own V6 cost prior contract required')
        super().__init__(contract=contract, size=size)
        # 부모의 모든 난수 소비가 끝난 뒤 두 텐서만 수정한다. gradient는 유지한다.
        with torch.no_grad():
            self.cost_critic.weight.zero_()
            self.cost_critic.bias.zero_()


class GoalPool(v5.GoalPool):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.contract = attach(self.contract)
            self.environment.contract['diagnostics']['cost_prior'] = copy.deepcopy(COST_PRIOR)
        except BaseException:
            self.close()
            raise


Environment = v5.Environment
sigma4 = v5.sigma4
