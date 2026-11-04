"""기존 타현 판정과 보상을 유지하며 새 오른손 행동 의미를 기록한다."""
import torch

from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.gpu.environment import TensorSongEnvironment
from .control import ACTION_NAMES, SCHEMA


class Right27Environment(TensorSongEnvironment):
    def __init__(self, metadata, *, bundle, song, hand='right', device='cuda:0'):
        if hand != 'right' or metadata['action_contract'].get('schema') != SCHEMA:
            raise ValueError('Explicit right27 controller contract required')
        super().__init__(metadata, bundle=bundle, song=song, hand=hand, device=device)
        self.contract['action'].update(schema='guitar_learning.right27_action.v1',
            names=list(ACTION_NAMES), active_dimensions=27,
            active_indices=list(range(12, 39)), inactive_indices=list(range(12)))
        observation = self.contract['observation']
        replacements = dict(zip(('previous_action.'+n for n in ACTIVE_NAMES),
                                ('previous_action.'+n for n in ACTION_NAMES)))
        observation['fields'] = [replacements.get(name, name) for name in observation['fields']]
        observation['action_history_schema'] = 'guitar_learning.right27_action.v1'
        self.contract['right27'] = dict(schema='guitar_learning.right27.v1',
            action_count=27, container_count=39, right_finger_count=21,
            strike_measurement='unchanged pick-marker crossing; no physical grip assertion')

    def begin_control(self, actions):
        if (actions.shape != (self.N, 39) or actions.device != self.device or
                not torch.isfinite(actions).all() or (actions.abs() > 1).any() or
                (actions[:, :12] != 0).any()):
            raise ValueError('Finite bounded right27 action with inactive first12 required')
        # 부모의 옛 왼손 비활성 검사는 0으로 통과하고 실제 새 행동을 이력에 남긴다.
        base_actions = actions.clone()
        base_actions[:, :33] = 0
        super().begin_control(base_actions)
        self.action = actions.detach().clone()
