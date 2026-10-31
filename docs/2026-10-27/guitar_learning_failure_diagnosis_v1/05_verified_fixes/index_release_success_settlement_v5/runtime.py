"""원 V4 제어·정책을 재사용하고 A 달성 보상의 지급 시점만 바꾼다."""
import copy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import torch

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'index_release_reference_learning_v4'
spec = importlib.util.spec_from_file_location('settlement_v5_parent_runtime', SOURCE/'runtime.py')
v4 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v4
spec.loader.exec_module(v4)
base, v2, ADAPTER = v4.base, v4.v2, v4.ADAPTER
SCHEMA = 'diagnostic.release_success_settlement.v5'
SETTLEMENT = dict(schema=SCHEMA, source_index=4, final_budget_per_weight=.25,
    clock='original score seconds, 240Hz', deadline='end[4]+0.1 inclusive release window',
    entitlement='original left AND original released with original release_s bounds',
    payment='once at first substep now>=deadline; existing failed-control positive clamp',
    other_eight_terms='unchanged', other_notes='unchanged', terminal_catchup=False)


def attach(contract):
    result = v4.attach(contract)
    result['reward']['diagnostic_success_settlement'] = copy.deepcopy(SETTLEMENT)
    return result


def settings():
    result = v4.settings()
    result['simple_start']['initialization'] = 'fresh V5 seed7 current557/Jv3; same fit1000 then PPO300; A success settlement only'
    return result


class Environment(v4.shared.Environment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contract['reward']['diagnostic_success_settlement'] = copy.deepcopy(SETTLEMENT)

    def _allocate(self, count):
        super()._allocate(count)
        # note 원장에 등록하면 기존 부분 reset이 선택 행만 정확히 초기화한다.
        for name in ('settlement_closed',):
            self.note[name] = torch.zeros_like(self.note['left'])
        for name in ('settlement_removed_raw', 'settlement_entitled_raw', 'settlement_pending_raw',
                     'settlement_paid', 'settlement_suppressed', 'settlement_time_s'):
            self.note[name] = torch.zeros_like(self.note['clean'])

    def substep(self, snapshot):
        before = self.note['left'][:,4].clone()
        super().substep(snapshot)
        # 부모가 원래 달성한 A의 원시 .5만 회수한다. 최종 가중 .5는 부모가 적용한다.
        removed = (.5*(~before & self.note['left'][:,4])*self.finger_weights[:,4]).float()
        self.terms['song_left_success'] -= removed
        self.note['settlement_removed_raw'][:,4] += removed.double()
        now, deadline = self._score_time(), self.end[4]+.1
        close = (~self.note['settlement_closed'][:,4] & self.focus_mask[:,4] & (now >= deadline))
        eligible = (self.note['left'][:,4] & self.note['released'][:,4] &
            (self.note['release_s'][:,4] >= self.end[4]) & (self.note['release_s'][:,4] <= deadline))
        credit = (.5*close*eligible*self.finger_weights[:,4]).float()
        self.terms['song_left_success'] += credit
        self.note['settlement_closed'][:,4] |= close
        self.note['settlement_time_s'][:,4] = torch.where(close, now, self.note['settlement_time_s'][:,4])
        self.note['settlement_entitled_raw'][:,4] += credit.double()
        self.note['settlement_pending_raw'][:,4] += credit.double()

    def _prepare_control_end(self, failed):
        super()._prepare_control_end(failed)
        # 지급 권리와 실제 수령을 구분한다. 실패 tick의 양의 보상은 부모가 억제한다.
        pending = .5*self.note['settlement_pending_raw'][:,4]
        self.note['settlement_paid'][:,4] += torch.where(failed, 0., pending)
        self.note['settlement_suppressed'][:,4] += torch.where(failed, pending, 0.)
        self.note['settlement_pending_raw'][:,4] = 0

    def settlement(self, index):
        return {name: (bool(value[index,4]) if value.dtype == torch.bool else float(value[index,4]))
            for name,value in self.note.items() if name.startswith('settlement_')}

    def _episode(self, index, failed):
        row = super()._episode(index, failed)
        row['success_settlement'] = self.settlement(index)
        return row


def compact_episode(row, spec):
    result = v4.shared.compact_episode(row, spec)
    result['success_settlement'] = copy.deepcopy(row['success_settlement'])
    return result


shared = SimpleNamespace(**dict(vars(v4.shared), compact_episode=compact_episode))
sigma4 = v4.sigma4


class GoalPolicy(v4.GoalPolicy):
    schema = SCHEMA+'.goal_policy'

    def __init__(self, *, contract, size='large'):
        if contract.get('reward',{}).get('diagnostic_success_settlement') != SETTLEMENT:
            raise ValueError('Own V5 success settlement reward contract required')
        super().__init__(contract=contract, size=size)


class GoalPool(v4.GoalPool):
    environment_class_override = Environment

    def step(self, raw):
        count = len(self.learning_trace)
        episode_count = len(self.learning_episodes)
        result = super().step(raw)
        if len(self.learning_trace) != count:
            self.learning_trace[-1].update(self.environment.settlement(0))
        # 부모의 첫 시도 목록에도 동일 원장을 붙인다. 원본 모듈 alias는 바꾸지 않는다.
        for row in result[-1]:
            for compact in self.learning_episodes[episode_count:]:
                if compact['env_id'] == row['env_id']:
                    compact['success_settlement'] = copy.deepcopy(row['success_settlement'])
                    break
        return result
