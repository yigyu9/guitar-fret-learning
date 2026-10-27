"""Episode-boundary prepared-state reset without rebuilding the native scene.

State setters are used only by ``reset_episode``. Normal preparation/control
continues through the original guarded finite controller and fetched physics.
"""
import copy
from pathlib import Path
from unittest.mock import patch
import numpy as np
from . import headless_session
from .headless_session import HeadlessPreparedSession, _physics_signature
from .prepared_reset_v1 import _restore_once, _state_all, load_prepared_reset_contract
from .recording import write


_COUNTED_APIS = ('create_sim', 'create_env', 'load_asset', 'destroy_sim')
_HISTORY_FIELDS = ('target_rows', 'right_target', 'right_info', 'play_latch',
                   'release_origin_W', 'release_rotation_W', 'release_delta_W')


def _history_snapshot(owner, fields):
    return {name: copy.deepcopy(getattr(owner, name)) for name in fields if hasattr(owner, name)}


def _restore_history(owner, fields, initial):
    for name in fields:
        if name in initial:
            setattr(owner, name, copy.deepcopy(initial[name]))
        elif hasattr(owner, name):
            delattr(owner, name)


def _counting_guard_type(original_guard, physics_threads):
    """Count lifecycle calls while retaining every original Guard restriction."""
    base = _ORIGINAL_HEADLESS_GUARD(original_guard, physics_threads)

    class LifecycleGuard(base):
        def __getattr__(self, name):
            native = super().__getattr__(name)
            if name not in _COUNTED_APIS:
                return native
            def counted(*args, **kwargs):
                counts = self.owner.__dict__.setdefault('persistent_native_calls',
                    dict.fromkeys(_COUNTED_APIS, 0))
                counts[name] += 1
                return native(*args, **kwargs)
            return counted
    return LifecycleGuard


_ORIGINAL_HEADLESS_GUARD = headless_session._headless_guard_type


def _rigid_properties(properties):
    rows = []
    for prop in properties:
        rows.append(dict(mass=float(prop.mass),
            com=[float(getattr(prop.com, a)) for a in 'xyz'],
            inertia=[[float(getattr(getattr(prop.inertia, a), b)) for b in 'xyz'] for a in 'xyz'],
            flags=int(prop.flags)))
    return rows


def _physical_signature(scene):
    """Read current native properties rather than trusting cached constructor rows."""
    pd = scene.gym.get_actor_dof_properties(scene.env, scene.human)
    result = dict(pd={key: pd[key].tolist() for key in pd.dtype.names},
        physics=_physics_signature(scene.gym.get_sim_params(scene.sim)),
        physics_threads=int(scene.gym.get_sim_params(scene.sim).physx.num_threads),
        flags=dict(human_root_fixed=bool(scene.human_root_fixed),
            guitar_root_fixed=bool(scene.guitar_root_fixed),
            guitar_gravity_disabled=bool(scene.guitar_gravity_disabled)),
        limits=dict(lower=scene.lower.tolist(), upper=scene.upper.tolist()),
        actors={})
    for label, actor in (('human', scene.human), ('guitar', scene.guitar), ('chair', scene.chair_actor)):
        shapes = scene.gym.get_actor_rigid_shape_properties(scene.env, actor)
        result['actors'][label] = dict(
            bodies=_rigid_properties(scene.gym.get_actor_rigid_body_properties(scene.env, actor)),
            shapes=[{key: getattr(prop, key) for key in (
                'filter', 'friction', 'rolling_friction', 'torsion_friction',
                'restitution', 'compliance', 'thickness', 'contact_offset', 'rest_offset')
                if hasattr(prop, key)}
                for prop in shapes])
    return result


class PersistentHeadlessPreparedSession(HeadlessPreparedSession):
    """Own one scene per worker; reuse its assets, FK and controller references."""
    def __init__(self, config, out, *, physics_threads=1):
        self.closed = False
        self._physics_inflight = False
        self._native_scene = None
        self.episode_index = 0
        self._config = copy.deepcopy(dict(config))
        self._history = None
        self._episode_out = Path(out)
        self._lifecycle_path = self._episode_out.parent / 'persistent_lifecycle.json'
        self._lifecycle_written = False
        self._last_sim_time = None
        try:
            # Construction-only patch under the same process-local lock used by
            # the original headless adapter. Live Guard objects retain the type.
            with headless_session._CONSTRUCTION_LOCK:
                with patch.object(headless_session, '_headless_guard_type', _counting_guard_type):
                    super().__init__(config, out, physics_threads=physics_threads)
            self._native_scene = self.scene
            self._identities = self._native_identities()
            self._properties = _physical_signature(self.scene)
            self._history = _history_snapshot(self.controller, _HISTORY_FIELDS)
            self._prepared_contract = load_prepared_reset_contract()
            self._initial_state_offset = 0
            self._forbidden_offset = 0
            self._describe_reset(previous_steps=None)
            self._write_reset_audit()
        except BaseException:
            self.close()
            raise

    def _native_identities(self):
        return dict(scene=id(self.scene), sim=id(self.scene.sim), env=id(self.scene.env),
                    controller=id(self.controller), fk=id(self.controller.fk))

    @property
    def persistent_reset_diagnostics(self):
        scene = self._native_scene
        if scene is not None and scene.sim is not None:
            self._last_sim_time = float(scene.gym.get_sim_time(scene.sim))
        return dict(episode_index=self.episode_index, closed=self.closed,
            native_identities=copy.deepcopy(getattr(self, '_identities', {})),
            native_calls=copy.deepcopy(getattr(scene, 'persistent_native_calls', {})),
            initial_state_calls_total=len(getattr(scene, 'initial_state_calls', [])),
            forbidden_calls_total=len(getattr(scene, 'forbidden_calls', [])),
            episode_initial_state_offset=getattr(self, '_initial_state_offset', 0),
            episode_forbidden_offset=getattr(self, '_forbidden_offset', 0),
            controller_target_history_length=len(getattr(getattr(self, 'controller', None), 'target_rows', [])),
            native_sim_time_s=self._last_sim_time,
            episode_local_physics_steps=int(getattr(scene, 'steps', 0)),
            reset_scope='Episode boundary only; no scene/asset/controller reconstruction or per-step state writes',
            solver_cache_scope='Native rigid/DOF state restoration; no claim of restoring hidden PhysX solver/contact caches')

    @property
    def persistent_reset_description(self):
        return self.persistent_reset_diagnostics

    def _describe_reset(self, previous_steps):
        self.prepared_reset_description['persistent_reset'] = dict(
            self.persistent_reset_diagnostics, previous_episode_physics_steps=previous_steps,
            native_properties_unchanged=True, history_fields_restored=list(self._history),
            human_effort_cleared_at_boundary=previous_steps is not None)
        self.prepared_reset_description['initialization_scope'] = (
            'One episode-boundary DOF/guitar/target reset; same scene and assets retained; '
            'fixed root/chair unchanged; no per-step state injection')

    def _write_reset_audit(self):
        description = self.prepared_reset_description
        readback = {key: copy.deepcopy(description[key]) for key in (
            'human_DOF_pos_vel_max_error', 'guitar_velocity_max_scalar_error',
            'body_pose_readback', 'state_set_calls')}
        write(self._episode_out / 'persistent_reset.json', dict(
            diagnostics=copy.deepcopy(description['persistent_reset']), readback=readback))

    def reset_episode(self, config, out):
        """Restore the prepared state after the preceding synchronous step ends."""
        try:
            if self.closed or self.scene is None:
                raise RuntimeError('Cannot reset a closed persistent session')
            if self._physics_inflight or self.scene.controlling or self.scene.submitting_targets:
                raise RuntimeError('Persistent reset requires a completed, fetched control step')
            if dict(config) != self._config:
                raise ValueError('Persistent reset cannot change the original baseline config')
            if self._native_identities() != self._identities:
                raise RuntimeError('Persistent native scene/controller identity changed')
            if _physical_signature(self.scene) != self._properties:
                raise RuntimeError('Persistent reset native physical properties changed')
            scene = self.scene
            previous_steps = int(scene.steps)
            self._initial_state_offset = len(scene.initial_state_calls)
            self._forbidden_offset = len(scene.forbidden_calls)
            # The previous integration fetched its results. Clear only the
            # human's finite DOF effort through the original owner/cap guard.
            scene.controlling = True
            try:
                if scene.gym.apply_actor_dof_efforts(scene.env, scene.human, np.zeros(105)) is False:
                    raise RuntimeError('Persistent human effort clear failed')
            finally:
                scene.controlling = False
            scene.steps = 0
            description = _restore_once(scene, self._prepared_contract, _state_all())
            _restore_history(self.controller, _HISTORY_FIELDS, self._history)
            scene.jacobian_mode = 'COM'
            scene.submitting_targets = False
            scene.cfg['attempt_out'] = str(Path(out))
            self._episode_out = Path(out)
            self.seed_target105 = self._prepared_contract['target105'].copy()
            self.episode_index += 1
            self.prepared_reset_description.update(description)
            self._describe_reset(previous_steps)
            self._write_reset_audit()
            return self
        except BaseException:
            # A partial reset is never reused as a valid episode.
            self.close()
            raise

    def integrate(self):
        if self.closed:
            raise RuntimeError('Cannot integrate a closed persistent session')
        self._physics_inflight = True
        diagnostic = super().integrate()
        self._physics_inflight = False
        return diagnostic

    def close(self):
        try:
            if getattr(self, 'scene', None) is not None:
                self.persistent_reset_diagnostics
                super().close()
        finally:
            self.closed = True
            if self._native_scene is not None and not self._lifecycle_written:
                self._lifecycle_written = True
                try:
                    write(self._lifecycle_path, self.persistent_reset_diagnostics)
                except BaseException as error:
                    # Preserve the triggering native/reset error. The parent
                    # audit reports a missing lifecycle artifact as incomplete.
                    self.lifecycle_write_error = repr(error)
