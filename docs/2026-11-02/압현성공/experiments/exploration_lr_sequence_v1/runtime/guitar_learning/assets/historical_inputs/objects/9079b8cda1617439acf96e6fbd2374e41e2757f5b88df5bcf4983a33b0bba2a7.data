"""Explicit teacher support-nominal guard; actual upper81 remains PD controlled."""
import copy
from unittest.mock import patch
from . import deadline_native_v5 as previous
from .deadline_support_nominal_v1 import ARM_CAP_RAD, LEFT_THUMB_CAP_RAD, support_nominal

PROFILE = copy.deepcopy(previous.PROFILE)
PROFILE['name'] = 'stability_support_nominal_pilot_v1'
RULE = {'reference': 'fixed reset preload, never updated from actual q',
        'arm24_cap_rad': ARM_CAP_RAD, 'left_thumb5_cap_rad': LEFT_THUMB_CAP_RAD,
        'other_fingers': 'unchanged dynamic baseline nominal',
        'teacher_scope': 'source/native intersection target, before this explicit guard'}


class NativeDeadlineEnvironment(previous.NativeDeadlineEnvironment):
    def reset(self):
        self.close()
        self.teacher_requests = {}
        self.last_source_actions = None
        with patch.object(previous, 'PROFILE', PROFILE):
            observation = super().reset()
        self.metadata['baseline_nominal_guard'] = RULE.copy()
        return observation

    def _nominal(self):
        teacher = super()._nominal()
        c = self.scene.contract
        self.current_teacher_nominal = teacher.copy()
        return support_nominal(teacher, self.preload, c.effective_lower, c.effective_upper, c.groups, c.names)

    def abi(self):
        with patch.object(previous, 'PROFILE', PROFILE):
            abi = super().abi()
        abi.update(version='stability_support_nominal825_v1', baseline_nominal_guard=RULE.copy())
        return abi

    def step(self, action):
        if self.recording:
            self.teacher_requests[self.tick] = {'nominal': self.current_teacher_nominal.tolist(),
                                                'source_actions': copy.deepcopy(self.last_source_actions)}
        with patch.object(previous, 'PROFILE', PROFILE):
            return super().step(action)

    def _finish(self, reason):
        if self.recording:
            for row in getattr(self, 'rows', []):
                teacher = self.teacher_requests[row['control_tick']]
                row['teacher_nominal81_rad'] = teacher['nominal']
                row['baseline_source_actions'] = teacher['source_actions']
                row['nominal_guard_delta81_rad'] = [n-t for n,t in zip(row['nominal81_rad'],teacher['nominal'])]
        return super()._finish(reason)

    def close(self):
        with patch.object(previous, 'PROFILE', PROFILE):
            return super().close()
