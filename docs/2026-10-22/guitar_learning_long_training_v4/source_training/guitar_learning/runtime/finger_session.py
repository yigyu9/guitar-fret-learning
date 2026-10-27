"""Initial-only left finger PD profile and its matching finite target limiter.

Original sessions and historical prepared inputs retain their own properties.
Only this explicit session derives a new PD expectation from the saved pose.
"""
import copy
from types import MappingProxyType

import numpy as np

from guitar_learning.core.control import LEFT_HAND_NAMES
from guitar_learning.core.finger_control import default_profile, validate_profile
from guitar_learning.runtime.native_session import target_rates
from guitar_learning.runtime.persistent_session import (
    PersistentHeadlessPreparedSession, _physical_signature)
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract


def _left_indices(names):
    if (len(names) != 105 or len(set(names)) != 105 or
            {name for name in names if name.startswith('LH:')} != set(LEFT_HAND_NAMES)):
        raise ValueError('exact native105 and named left21 required')
    return np.array([names.index(name) for name in LEFT_HAND_NAMES], dtype=int)


def _command_finger_targets(scene, named, profile):
    """Versioned final limiter; no original 1.5rad/s finger limiter follows."""
    validate_profile(dict(profile))
    if (not scene.initialization_complete or scene.controlling or scene.submitting_targets or
            isinstance(scene.steps, bool) or not isinstance(scene.steps, (int, np.integer)) or scene.steps < 0):
        raise RuntimeError('finger target submission requires a fetched initialized scene')
    names = tuple(scene.names)
    indices = _left_indices(names)
    if set(named) != set(names) or len(named) != 105:
        raise ValueError('exact named native105 targets required')
    request = np.array([named[name] for name in names], dtype=float)
    if (request.shape != (105,) or not np.isfinite(request).all() or
            np.any(request < scene.lower - 1e-8) or np.any(request > scene.upper + 1e-8)):
        raise ValueError('finite native-bounded finger profile target required')
    previous = np.asarray(scene.target, dtype=float)
    if previous.shape != (105,) or not np.isfinite(previous).all():
        raise ValueError('finite previous native105 target required')
    rates = target_rates(names)
    rates[indices] = profile['finger_rate_rad_s']
    scene.target = np.clip(np.clip(request, previous - rates / 60., previous + rates / 60.),
                           scene.lower, scene.upper).astype(np.float32)
    scene.target[scene.zero_indices] = scene.q_ref[scene.zero_indices]
    before = scene.native()
    scene.submitting_targets = True
    try:
        if scene.gym.set_actor_dof_position_targets(scene.env, scene.human, scene.target) is False:
            raise RuntimeError('native finger POSITION target submission failed')
    finally:
        scene.submitting_targets = False
    actual = scene.gym.get_actor_dof_position_targets(scene.env, scene.human)
    if (not np.array_equal(actual[scene.position_indices], scene.target[scene.position_indices]) or
            scene.native() != before):
        raise RuntimeError('finger native POSITION readback/state parity failed')
    return dict(physics_step_before=int(scene.steps), joint_names=list(names),
                requested105_rad=request.tolist(), final105_rad=scene.target.astype(float).tolist(),
                native105_position_readback_rad=np.asarray(actual, dtype=float).tolist(),
                position_readback_exact=True, native_position_count=len(scene.position_indices),
                finger_control=dict(profile=dict(profile), target_rates_rad_s=rates.tolist(),
                    scope='left21 rate override only; original finite bounds and POSITION owner'))


class FlexibleLeftFingerSession(PersistentHeadlessPreparedSession):
    def __init__(self, config, out, *, physics_threads=1):
        profile = copy.deepcopy(default_profile())
        validate_profile(profile)
        self._finger_profile = MappingProxyType(profile)
        self._finger_profile_applied = False
        try:
            super().__init__(config, out, physics_threads=physics_threads)
            self._apply_finger_profile_once()
            self._describe_reset(previous_steps=None)
            self._write_reset_audit()
        except BaseException:
            self.close()
            raise

    def _write_reset_audit(self):
        # The parent writes with exclusive creation. Defer its first audit until
        # the new explicit PD baseline is established, rather than rewriting it.
        if self._finger_profile_applied:
            super()._write_reset_audit()

    def _describe_reset(self, previous_steps):
        super()._describe_reset(previous_steps)
        if self._finger_profile_applied:
            self.prepared_reset_description['persistent_reset']['finger_control'] = copy.deepcopy(
                self.finger_control_description)

    def _apply_finger_profile_once(self):
        scene = self.scene
        if (self._finger_profile_applied or self.closed or scene is None or scene.steps != 0 or
                self._physics_inflight or scene.controlling or scene.submitting_targets or
                not scene.initialization_complete):
            raise RuntimeError('left finger properties are initial-only and applied once')
        original = load_prepared_reset_contract()
        initial = original['initial']
        if list(scene.names) != initial['joint_names']:
            raise ValueError('left finger native joint order differs from original preparation')
        indices = _left_indices(scene.names)
        actual = scene.gym.get_actor_dof_properties(scene.env, scene.human)
        if (actual.shape != (105,) or actual.dtype != scene.pd_properties.dtype or
                set(actual.dtype.names) != set(initial['native_PD_properties'])):
            raise ValueError('original native finger property layout required')
        expected = actual.copy()
        for field in actual.dtype.names:
            expected[field] = np.asarray(initial['native_PD_properties'][field], dtype=actual[field].dtype)
        if not np.array_equal(actual, expected) or not np.array_equal(scene.pd_properties, expected):
            raise ValueError('left finger profile requires exact original native PD properties')
        if (not np.array_equal(scene.control_kp, initial['control_K105']) or
                not np.array_equal(scene.control_kd, initial['control_D105']) or
                np.any(actual['driveMode'][indices] != 1)):
            raise ValueError('original finite gains and left21 POSITION ownership required')
        desired = expected.copy()
        for index in indices:
            prefix = 'thumb' if scene.names[index].startswith('LH:thumb') else 'finger'
            desired['stiffness'][index] = self._finger_profile[prefix + '_stiffness']
            desired['damping'][index] = self._finger_profile[prefix + '_damping']
        before = scene.native()
        targets = np.asarray(scene.gym.get_actor_dof_position_targets(scene.env, scene.human)).copy()
        scene.initialization_complete = False
        try:
            if scene.gym.set_actor_dof_properties(scene.env, scene.human, desired) is False:
                raise RuntimeError('native left finger PD initialization failed')
        finally:
            scene.initialization_complete = True
        readback = scene.gym.get_actor_dof_properties(scene.env, scene.human)
        if (readback.dtype != desired.dtype or not np.array_equal(readback, desired) or
                scene.native() != before or not np.array_equal(targets,
                    scene.gym.get_actor_dof_position_targets(scene.env, scene.human))):
            raise RuntimeError('native left finger PD/state/target readback mismatch')
        scene.pd_properties = readback.copy()
        self._prepared_contract = copy.deepcopy(self._prepared_contract)
        self._prepared_contract['initial']['native_PD_properties'] = {
            field: readback[field].tolist() for field in readback.dtype.names}
        self._properties = _physical_signature(scene)
        self.finger_control_description = dict(profile=dict(self._finger_profile), applied=True,
            native_pd_before={field: expected[field].tolist() for field in expected.dtype.names},
            native_pd_after={field: readback[field].tolist() for field in readback.dtype.names},
            scope='initial left21 native K/D only; historical prepared pose and all other properties preserved')
        self.prepared_reset_description['finger_control'] = copy.deepcopy(self.finger_control_description)
        self._finger_profile_applied = True

    def submit_policy_target(self, target):
        try:
            if not self._finger_profile_applied or self.closed:
                raise RuntimeError('initialized left finger profile session required')
            scene = self.scene
            target = np.asarray(target, dtype=float)
            if target.shape != (105,) or not np.isfinite(target).all():
                raise ValueError('finite native105 policy target required')
            named, diagnostic = self.controller.apply(dict(zip(scene.names, target.tolist())))
            maintained = np.array([named[name] for name in scene.names], dtype=float)
            upper = [index for index in range(105) if index not in scene.lower_indices]
            if not np.array_equal(maintained[upper], target[upper]):
                raise RuntimeError('Foot maintenance modified policy/held upper channels')
            row = _command_finger_targets(scene, named, self._finger_profile)
            row.update(foot_world_target_IK=diagnostic, stage='policy_handoff')
            self.controller.target_rows.append(row)
            return row
        except BaseException:
            self.close()
            raise
