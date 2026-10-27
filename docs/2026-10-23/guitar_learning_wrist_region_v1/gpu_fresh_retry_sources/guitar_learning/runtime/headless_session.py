"""Camera-free prepared native sessions for isolated CPU worker processes.

Only construction is patched, in memory and under a process-local lock. Every
non-graphics Guard operation remains owned by the original Guard. This is not
a batched PhysX environment and must not share a process with another thread
constructing native graphical sessions. Numerical parity after changing PhysX
thread count must be measured by the caller, not assumed by this adapter.
"""
import copy
import importlib
import threading
from contextlib import contextmanager
from unittest.mock import patch
from guitar_learning.runtime.prepared_reset_v1 import PreparedSession

_CONSTRUCTION_LOCK = threading.RLock()


def _native_modules():
    # Isaac Gym must precede native runtime imports (which can import Torch).
    import isaacgym
    return (importlib.import_module('guitar_learning.native.front_facing_ready_v1.runtime_v15'),
            importlib.import_module('guitar_learning.native.lower_body_release_v1.scene_v8'))


def _physics_signature(params):
    physx = params.physx
    return dict(dt=float(params.dt), substeps=int(params.substeps), up_axis=int(params.up_axis),
                gravity=[float(getattr(params.gravity, axis)) for axis in 'xyz'],
                use_gpu_pipeline=bool(params.use_gpu_pipeline),
                physx=dict(use_gpu=bool(physx.use_gpu), solver_type=int(physx.solver_type),
                    num_position_iterations=int(physx.num_position_iterations),
                    num_velocity_iterations=int(physx.num_velocity_iterations),
                    contact_collection=int(physx.contact_collection),
                    contact_offset=float(physx.contact_offset), rest_offset=float(physx.rest_offset),
                    max_depenetration_velocity=float(physx.max_depenetration_velocity)))


def _headless_scene_type(original_scene):
    class HeadlessScene(original_scene):
        def __setattr__(self, name, value):
            if name == 'camera_spec':
                # The original scene iterates this mapping to create cameras.
                # Keep its requested configuration as provenance, while the
                # executable mapping is empty. No dummy handles are returned.
                super().__setattr__('declared_camera_spec', copy.deepcopy(value))
                super().__setattr__('camera_status', 'disabled')
                value = {}
            super().__setattr__(name, value)
    return HeadlessScene


def _headless_guard_type(original_guard, physics_threads):
    class HeadlessGuard(original_guard):
        def __getattr__(self, name):
            if name == 'create_sim':
                def create(compute_device, requested_graphics_device, engine, params):
                    before = _physics_signature(params)
                    if before['use_gpu_pipeline'] or before['physx']['use_gpu']:
                        raise ValueError('Headless CPU workers require original CPU PhysX settings')
                    old_threads = int(params.physx.num_threads)
                    params.physx.num_threads = physics_threads
                    if _physics_signature(params) != before:
                        raise RuntimeError('Headless construction changed physical parameters')
                    self.owner.headless_configuration = dict(
                        graphics='disabled', graphics_device_id=-1,
                        requested_graphics_device_id=int(requested_graphics_device),
                        compute_device_id=int(compute_device),
                        physx_num_threads_before=old_threads,
                        physx_num_threads=physics_threads, physics_parameters=before,
                        thread_count_numerical_parity='requires native comparison; not assumed',
                        guard_scope='Original force/state/property/target restrictions remain active')
                    return self.gym.create_sim(compute_device, -1, engine, params)
                return create
            if ('camera' in name or 'viewer' in name or 'graphics' in name or
                    name in ('start_access_image_tensors', 'end_access_image_tensors')):
                def disabled(*args, **kwargs):
                    raise RuntimeError('Graphics/cameras are disabled in this headless worker: ' + name)
                return disabled
            return super().__getattr__(name)
    return HeadlessGuard


@contextmanager
def _headless_construction(runtime_module, scene_module, physics_threads):
    """Restore module class bindings even if native construction fails."""
    if type(physics_threads) is not int or physics_threads < 1:
        raise ValueError('physics_threads must be a positive integer')
    with _CONSTRUCTION_LOCK:
        with patch.object(runtime_module, 'Scene', _headless_scene_type(runtime_module.Scene)), \
             patch.object(scene_module, 'Guard', _headless_guard_type(scene_module.Guard, physics_threads)):
            yield


class HeadlessPreparedSession(PreparedSession):
    """Original prepared reset/control with graphics disabled; default one CPU thread."""
    def __init__(self, config, out, *, physics_threads=1):
        if type(physics_threads) is not int or physics_threads < 1:
            raise ValueError('physics_threads must be a positive integer')
        runtime_module, scene_module = _native_modules()
        with _headless_construction(runtime_module, scene_module, physics_threads):
            super().__init__(config, out)
        try:
            if self.scene.cameras or self.scene.camera_spec or self.scene.camera_status != 'disabled':
                raise RuntimeError('Headless construction unexpectedly enabled cameras')
            self.headless_description = copy.deepcopy(self.scene.headless_configuration)
            self.headless_description.update(camera_status='disabled', camera_count=0,
                declared_camera_spec=copy.deepcopy(self.scene.declared_camera_spec),
                implementation='one original native scene per worker process; no GPU env batching')
            self.prepared_reset_description['headless'] = copy.deepcopy(self.headless_description)
        except BaseException:
            self.close()
            raise

    def render(self, *args, **kwargs):
        raise RuntimeError('Rendering is disabled in HeadlessPreparedSession')


def headless_session_factory(config, out):
    """Two-argument factory compatible with the existing environment API."""
    return HeadlessPreparedSession(config, out, physics_threads=1)
