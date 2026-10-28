"""하나의 GPU PhysX 시뮬레이터에서 CUDA 상태·제어 텐서와 배치 장면을 소유한다.

자산·충돌 필터 설정 → 물리 진행 → 선택 환경 reset 순서로 읽는다.
상태 쓰기는 에피소드 reset에서만 허용한다. reset 직후 몸체 자세는 봉인된 준비
스냅샷이며 첫 물리 스텝에서 관절 순기구학을 다시 구성한다."""
from pathlib import Path
import hashlib
import json

import numpy as np


def _body_row(record):
    return ([record['pose']['p'][a] for a in 'xyz'] +
            [record['pose']['r'][a] for a in 'xyzw'] +
            [record['vel']['linear'][a] for a in 'xyz'] +
            [record['vel']['angular'][a] for a in 'xyz'])


def _apply_body_properties(properties, rows):
    if len(properties) != len(rows):
        raise ValueError('Pinned rigid-body property count differs from asset')
    for prop, row in zip(properties, rows):
        prop.mass = row['mass_kg']
        for i, axis in enumerate('xyz'):
            setattr(prop.com, axis, row['COM_body_m'][i])
            for j, other in enumerate('xyz'):
                setattr(getattr(prop.inertia, axis), other, row['inertia_COM_kg_m2'][i][j])


class GpuScene:
    def __init__(self, num_envs, hand, device='cuda:0', out=None, *, diagnostic_guitar_mode=None):
        # 실행 진입점에서 Torch보다 Isaac을 먼저 import해야 한다.
        import isaacgym
        from isaacgym import gymapi, gymtorch
        import torch
        from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
        from guitar_learning.native.paths import resolve_input_path
        from guitar_learning.core.control import default_profile

        if type(num_envs) is not int or num_envs < 1 or hand not in ('left', 'right'):
            raise ValueError('Positive environment count and left/right hand required')
        if diagnostic_guitar_mode not in (None, 'fixed', 'free'):
            raise ValueError('Diagnostic guitar mode must be fixed/free or omitted')
        self.diagnostic_guitar_mode = diagnostic_guitar_mode
        self._diagnostic_guitar_asset = None
        self.device = torch.device(device)
        if self.device.type != 'cuda' or not torch.cuda.is_available():
            raise ValueError('GPU scene requires available explicit CUDA device')
        self.num_envs, self.hand = num_envs, hand
        self.out = None if out is None else Path(out)
        self.gym, self.sim = gymapi.acquire_gym(), None
        self.closed, self.physics_steps, self.reset_calls = False, 0, 0
        self._actual_physics = {}
        self._tensor_devices = {}
        self._rigid_readback_max_error = 0.
        self.episode_steps = torch.zeros(num_envs, dtype=torch.long, device=self.device)
        self.contract = load_prepared_reset_contract()
        self.rigid_guitar = RigidGuitar(self.contract, self.device)
        initial, saved = self.contract['initial'], self.contract['state']
        self.hand_collision = None
        self._hand_collision_readback_count = 0
        human_shapes = initial['actual_shape_properties']['human']
        if hand == 'left':
            human_shapes, self.hand_collision = left_hand_collision_properties(human_shapes)
            verify_external_filter_preservation(initial['actual_shape_properties']['human'],
                human_shapes, [0] + [r['filter'] for r in self.rigid_guitar.shape_properties])
        self.names = list(initial['joint_names'])
        if (len(self.names) != 105 or len(set(self.names)) != 105 or
                initial['human_root_fixed'] is not True or initial['guitar_root_fixed'] is not False or
                initial['guitar_gravity_disabled'] is not False):
            raise ValueError('Pinned105 fixed human root and free gravity guitar required')
        self.human_bodies = list(initial['human_body_names'])
        self.guitar_bodies = list(initial['guitar_body_names'])
        self.body_names = (['human/' + n for n in self.human_bodies] +
                           ['guitar/' + n for n in self.guitar_bodies] + ['chair/box'])
        self.body_count = len(self.body_names)
        self.native_body_count = len(self.human_bodies) + 2
        self.envs, self.actors, self.origins = [], [], []
        self._reset_mask = torch.ones(num_envs, dtype=torch.bool, device=self.device)
        self._prepared_bodies = torch.tensor(
            [_body_row(r) for kind in ('human', 'guitar', 'chair')
             for r in saved[kind + '_body_states']], dtype=torch.float32, device=self.device)
        self._prepared_dofs = torch.tensor(
            [[r['pos'], r['vel']] for r in saved['human_dof_states']],
            dtype=torch.float32, device=self.device)
        self.reference105 = torch.tensor(self.contract['target105'], dtype=torch.float32, device=self.device)
        self.native_control_kp = torch.tensor(initial['control_K105'], device=self.device)
        self.native_control_kd = torch.tensor(initial['control_D105'], device=self.device)
        try:
            params = gymapi.SimParams()
            params.dt, params.substeps = 1 / 240., 1
            params.up_axis, params.gravity = gymapi.UP_AXIS_Z, gymapi.Vec3(0, 0, -9.81)
            params.use_gpu_pipeline, params.physx.use_gpu = True, True
            params.physx.solver_type = 1
            params.physx.num_position_iterations, params.physx.num_velocity_iterations = 4, 2
            params.physx.contact_collection = gymapi.ContactCollection.CC_LAST_SUBSTEP
            params.physx.contact_offset, params.physx.rest_offset = .002, 0.
            params.physx.max_depenetration_velocity = 10.
            params.physx.max_gpu_contact_pairs = max(1048576, num_envs * 4096)
            params.physx.default_buffer_size_multiplier = 5.
            compute = self.device.index if self.device.index is not None else torch.cuda.current_device()
            self.sim = self.gym.create_sim(compute, -1, gymapi.SIM_PHYSX, params)
            if self.sim is None:
                raise RuntimeError('GPU PhysX simulator construction failed')
            ground = gymapi.PlaneParams()
            ground.normal = gymapi.Vec3(0, 0, 1)
            self.gym.add_ground(self.sim, ground)
            assets = []
            for asset_index, record in enumerate(initial['loaded_assets']):
                options = gymapi.AssetOptions()
                is_guitar = asset_index == 1
                options.fix_base_link = (diagnostic_guitar_mode == 'fixed' if is_guitar and
                    diagnostic_guitar_mode is not None else record['fixed_base'])
                options.disable_gravity = record['gravity_disabled']
                if is_guitar:
                    options.override_com = options.override_inertia = True
                # 루트 이동 가능 여부에 따라 다른 충돌 자산을 선택하면 안 된다.
                path = self.rigid_guitar.asset_path if is_guitar else resolve_input_path(record['path'])
                asset = self.gym.load_asset(self.sim, str(path.parent), path.name, options)
                if asset is None:
                    raise RuntimeError('Pinned GPU asset failed to load: ' + str(path))
                if is_guitar and diagnostic_guitar_mode is not None:
                    self._diagnostic_guitar_asset = dict(
                        path=str(path.resolve()), asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        requested_fix_base_link=bool(options.fix_base_link),
                        requested_disable_gravity=bool(options.disable_gravity),
                        requested_override_com=bool(options.override_com),
                        requested_override_inertia=bool(options.override_inertia),
                        native_asset_body_count=int(self.gym.get_asset_rigid_body_count(asset)),
                        native_asset_shape_count=int(self.gym.get_asset_rigid_shape_count(asset)))
                assets.append(asset)
            chair_options = gymapi.AssetOptions()
            chair_options.fix_base_link = True
            half = initial['chair_initial_placement']['half_m']
            assets.append(self.gym.create_box(self.sim, *(2 * np.asarray(half)), chair_options))
            self.aggregate = dict(schema='guitar_learning.gpu_env_aggregate.v1',
                max_bodies=sum(self.gym.get_asset_rigid_body_count(a) for a in assets),
                max_shapes=sum(self.gym.get_asset_rigid_shape_count(a) for a in assets),
                self_collisions=True, actors=['human', 'guitar', 'chair'])
            body_rows = initial['human_properties'] + initial['guitar_properties']['applied']
            for index in range(num_envs):
                env = self.gym.create_env(self.sim, gymapi.Vec3(-1.5, -1.5, 0),
                                          gymapi.Vec3(1.5, 1.5, 2.5), int(np.ceil(np.sqrt(num_envs))))
                if env is None:
                    raise RuntimeError('GPU environment construction failed')
                self.envs.append(env)
                origin = self.gym.get_env_origin(env)
                self.origins.append([origin.x, origin.y, origin.z])
                handles = []
                # 모인 액터를 하나의 광역 충돌 검사 묶음에 둔다.
                # 아래 형상별 필터가 선택적 자기 충돌을 정의한다.
                if not self.gym.begin_aggregate(env, self.aggregate['max_bodies'],
                                                self.aggregate['max_shapes'], True):
                    raise RuntimeError('GPU environment aggregate construction failed')
                for kind, asset in zip(('human', 'guitar', 'chair'), assets):
                    row = saved[kind + '_body_states'][0]
                    transform = gymapi.Transform()
                    transform.p = gymapi.Vec3(*[row['pose']['p'][a] for a in 'xyz'])
                    transform.r = gymapi.Quat(*[row['pose']['r'][a] for a in 'xyzw'])
                    actor = self.gym.create_actor(env, asset, transform, kind, index, -1 if kind == 'human' else 0)
                    if actor < 0:
                        raise RuntimeError('GPU actor construction failed')
                    handles.append(actor)
                    if kind in ('human', 'guitar'):
                        rows = initial['human_properties'] if kind == 'human' else self.rigid_guitar.body_properties
                        actual_names = list(self.gym.get_actor_rigid_body_names(env, actor))
                        if actual_names != [r['name'] for r in rows]:
                            raise ValueError('Pinned GPU rigid-body order mismatch')
                        props = self.gym.get_actor_rigid_body_properties(env, actor)
                        _apply_body_properties(props, rows)
                        if self.gym.set_actor_rigid_body_properties(env, actor, props, False) is False:
                            raise RuntimeError('GPU rigid-body properties rejected')
                        readback = self.gym.get_actor_rigid_body_properties(env, actor)
                        for prop, record in zip(readback, rows):
                            actual = [prop.mass] + [getattr(prop.com, a) for a in 'xyz'] + [
                                getattr(getattr(prop.inertia, a), b) for a in 'xyz' for b in 'xyz']
                            expected = [record['mass_kg']] + record['COM_body_m'] + [
                                v for row in record['inertia_COM_kg_m2'] for v in row]
                            # PhysX가 속성 설정 시 관성 행렬을 대각화하므로
                            # 복원 결과는 float32 최소 표현 단위 몇 개만큼 다를 수 있다.
                            error = float(np.max(np.abs(np.asarray(actual) - np.asarray(expected))))
                            self._rigid_readback_max_error = max(self._rigid_readback_max_error, error)
                            if not np.allclose(actual, expected, rtol=2e-6, atol=1e-7 if kind == 'guitar' else 1e-8):
                                raise RuntimeError('GPU rigid mass/COM/inertia readback differs for ' + record['name'])
                        shapes = self.gym.get_actor_rigid_shape_properties(env, actor)
                        spans = self.gym.get_actor_rigid_body_shape_indices(env, actor)
                        for name, span in zip(actual_names, spans):
                            expected = (human_shapes[name] if kind == 'human'
                                        else self.rigid_guitar.shape_properties)
                            if span.count != len(expected):
                                raise ValueError('Pinned GPU collision shape count mismatch')
                            for offset, record in enumerate(expected):
                                prop = shapes[span.start + offset]
                                prop.filter, prop.friction = record['filter'], record['friction']
                                prop.contact_offset = record['contact_offset_m']
                                if kind == 'guitar':
                                    for field in ('rolling_friction', 'torsion_friction', 'restitution',
                                                  'compliance', 'thickness', 'rest_offset'):
                                        setattr(prop, field, 0.)
                        if self.gym.set_actor_rigid_shape_properties(env, actor, shapes) is False:
                            raise RuntimeError('GPU collision properties rejected')
                        readback = self.gym.get_actor_rigid_shape_properties(env, actor)
                        for expected, actual in zip(shapes, readback):
                            if (expected.filter != actual.filter or expected.friction != actual.friction or
                                    expected.contact_offset != actual.contact_offset):
                                raise RuntimeError('GPU collision filter/friction/contact offset readback differs')
                            if kind == 'guitar' and any(getattr(actual, field) != 0. for field in (
                                    'rolling_friction', 'torsion_friction', 'restitution',
                                    'compliance', 'thickness', 'rest_offset')):
                                raise RuntimeError('GPU compound guitar collision properties differ')
                        if kind == 'human' and hand == 'left':
                            self._hand_collision_readback_count += 1
                        if kind == 'guitar' and index == 0 and self._diagnostic_guitar_asset is not None:
                            fields = ('filter', 'friction', 'contact_offset', 'rolling_friction',
                                      'torsion_friction', 'restitution', 'compliance', 'thickness', 'rest_offset')
                            values = [{field: getattr(prop, field) for field in fields} for prop in readback]
                            self._diagnostic_guitar_asset['shape_readback_sha256'] = hashlib.sha256(
                                json.dumps(values, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                            self._diagnostic_guitar_asset['actor_shape_readback_count'] = len(readback)
                            self._diagnostic_guitar_asset['rigid_properties_verified'] = True
                    elif kind == 'chair' and hand == 'left':
                        verify_external_filter_preservation(
                            initial['actual_shape_properties']['human'], human_shapes,
                            [int(p.filter) for p in self.gym.get_actor_rigid_shape_properties(env, actor)])
                    if kind == 'human':
                        if list(self.gym.get_actor_dof_names(env, actor)) != self.names:
                            raise ValueError('Pinned GPU DOF order mismatch')
                        props = self.gym.get_actor_dof_properties(env, actor)
                        for field in props.dtype.names:
                            props[field] = initial['native_PD_properties'][field]
                        if hand == 'left':
                            profile = default_profile()
                            for j, name in enumerate(self.names):
                                if name.startswith('LH:'):
                                    prefix = 'thumb' if name.startswith('LH:thumb') else 'finger'
                                    props['stiffness'][j] = profile[prefix + '_stiffness']
                                    props['damping'][j] = profile[prefix + '_damping']
                        if self.gym.set_actor_dof_properties(env, actor, props) is False:
                            raise RuntimeError('GPU native DOF properties rejected')
                        readback = self.gym.get_actor_dof_properties(env, actor)
                        if not np.array_equal(readback, props):
                            raise RuntimeError('GPU native DOF property readback differs')
                        if self.gym.enable_actor_dof_force_sensors(env, actor) is False:
                            raise RuntimeError('GPU DOF force sensor setup failed')
                        self.pd_properties = readback.copy()
                if not self.gym.end_aggregate(env):
                    raise RuntimeError('GPU environment aggregate finalization failed')
                self.actors.append(handles)
            if not self.gym.prepare_sim(self.sim):
                raise RuntimeError('GPU prepare_sim failed')
            self.origins = torch.tensor(self.origins, dtype=torch.float32, device=self.device)
            self._dof = gymtorch.wrap_tensor(self.gym.acquire_dof_state_tensor(self.sim)).view(num_envs, 105, 2)
            self._roots = gymtorch.wrap_tensor(self.gym.acquire_actor_root_state_tensor(self.sim)).view(num_envs, 3, 13)
            self._bodies = gymtorch.wrap_tensor(self.gym.acquire_rigid_body_state_tensor(self.sim)).view(num_envs, self.native_body_count, 13)
            self._native_contact_force = gymtorch.wrap_tensor(self.gym.acquire_net_contact_force_tensor(self.sim)).view(num_envs, self.native_body_count, 3)
            self.contact_force = torch.zeros(num_envs, self.body_count, 3, device=self.device)
            self.jacobian = gymtorch.wrap_tensor(self.gym.acquire_jacobian_tensor(self.sim, 'human'))
            if any(t.device != self.device for t in (self._dof, self._roots, self._bodies, self._native_contact_force, self.jacobian)):
                raise RuntimeError('GPU pipeline returned non-CUDA tensors')
            self._tensor_devices = {name: str(value.device) for name, value in (
                ('dof', self._dof), ('roots', self._roots), ('bodies', self._bodies),
                ('contact_force', self._native_contact_force), ('jacobian', self.jacobian))}
            self.q, self.qd = self._dof[..., 0], self._dof[..., 1]
            self.target = self.reference105.expand(num_envs, -1).clone()
            self.efforts = torch.zeros_like(self.target)
            self.lower = torch.tensor(self.pd_properties['lower'].copy(), device=self.device)
            self.upper = torch.tensor(self.pd_properties['upper'].copy(), device=self.device)
            if int((self.lower < self.upper).sum()) != 97 or int((self.lower == self.upper).sum()) != 8:
                raise ValueError('GPU native105/effective97/zero8 limits differ')
            self.effort_caps = torch.tensor(self.pd_properties['effort'].copy(), device=self.device)
            chair = self.gym.get_actor_rigid_body_properties(self.envs[0], self.actors[0][2])[0]
            self.mass = torch.tensor([r['mass_kg'] for r in body_rows] + [chair.mass], device=self.device)
            self.com = torch.tensor([r['COM_body_m'] for r in body_rows] +
                                    [[getattr(chair.com, a) for a in 'xyz']], device=self.device)
            self.inertia = torch.tensor([r['inertia_COM_kg_m2'] for r in body_rows] +
                [[[getattr(getattr(chair.inertia, a), b) for b in 'xyz'] for a in 'xyz']], device=self.device)
            self.masses = self.mass
            self.metadata = dict(joint_names=self.names, body_names=self.body_names,
                human_bodies=self.human_bodies, guitar_bodies=self.guitar_bodies,
                body_com=self.com.tolist(), reference105=self.reference105.tolist(),
                position_indices=initial['position_indices'], effort_indices=initial['effort_indices'],
                zero_indices=initial['zero_range_indices'], physics_hz=240, control_hz=60,
                reset_body_source='Pinned035/v14 body snapshot until first actual GPU physics step',
                state_position_frame='Native environment-local coordinates; no environment-origin addition/subtraction',
                synchronization_version='guitar_learning.cuda_gym_torch_barriers.v1',
                environment_aggregate=self.aggregate.copy(),
                guitar_representation=dict(schema=self.rigid_guitar.manifest['schema'], physical_bodies=1,
                    logical_bodies=len(self.guitar_bodies), collision_shapes=89,
                    asset_sha256=self.rigid_guitar.manifest['asset_sha256'],
                    manifest_sha256=self.rigid_guitar.manifest_sha256,
                    proxy_collision_policy=self.rigid_guitar.manifest['proxy_collision_policy']),
                contact_measurement='Native human/chair forces; whole-guitar aggregate on logical root only; marker forces zero; no pair/local witness claim')
            if hand == 'left':
                self.metadata['hand_collision'] = self.hand_collision.copy()
            if diagnostic_guitar_mode is not None:
                self.metadata['diagnostic_only'] = dict(
                    schema='guitar_learning.press_acquisition_scene.v1',
                    guitar_mode=diagnostic_guitar_mode,
                    asset=self._diagnostic_guitar_asset.copy(),
                    training_contract=False, state_writes='prepared episode reset only',
                    root_mobility_evidence='requested AssetOptions.fix_base_link; replay records actual root translation/rotation; no native fixed-base property query')
            actual = self.gym.get_sim_params(self.sim)
            if not actual.use_gpu_pipeline or not actual.physx.use_gpu:
                raise RuntimeError('Native simulator did not enable GPU physics and pipeline')
            self._actual_physics = dict(physx_use_gpu=bool(actual.physx.use_gpu),
                use_gpu_pipeline=bool(actual.use_gpu_pipeline), dt_s=float(actual.dt),
                substeps=int(actual.substeps), gravity=[getattr(actual.gravity, a) for a in 'xyz'],
                position_iterations=int(actual.physx.num_position_iterations),
                velocity_iterations=int(actual.physx.num_velocity_iterations))
            self._refresh()
            self.reset(torch.arange(num_envs, device=self.device))
            self._write_audit()
        except BaseException:
            try:
                self.close()
            except BaseException as error:
                self.lifecycle_write_error = repr(error)
            raise

    @property
    def body_state(self):
        import torch
        value = self.rigid_guitar.expand(self._bodies)
        return torch.where(self._reset_mask[:, None, None], self._prepared_bodies[None], value)

    def _refresh(self):
        import torch
        self.gym.refresh_dof_state_tensor(self.sim)
        self.gym.refresh_actor_root_state_tensor(self.sim)
        self.gym.refresh_rigid_body_state_tensor(self.sim)
        self.gym.refresh_net_contact_force_tensor(self.sim)
        self.gym.refresh_jacobian_tensors(self.sim)
        # Gym CUDA 스트림은 Torch 할당기·현재 스트림과 별개다.
        # Torch가 이 뷰를 읽기 전에 native 버퍼 복사를 끝내야 한다.
        torch.cuda.synchronize(self.device)
        h = len(self.human_bodies)
        self.contact_force.zero_()
        self.contact_force[:, :h] = self._native_contact_force[:, :h]
        self.contact_force[:, h] = self._native_contact_force[:, h]
        self.contact_force[:, -1] = self._native_contact_force[:, -1]

    def snapshot(self):
        import torch
        contact = torch.where(self._reset_mask[:, None, None],
                              torch.zeros_like(self.contact_force), self.contact_force)
        return dict(q=self.q, qd=self.qd, target=self.target, body_state=self.body_state,
                    contact_force=contact, physics_step=self.episode_steps, jacobian=self.jacobian,
                    reset_body_snapshot=self._reset_mask.clone())

    def reset(self, indices):
        import torch
        from isaacgym import gymtorch
        ids = torch.as_tensor(indices, dtype=torch.long, device=self.device).flatten()
        if self.closed or ids.numel() == 0:
            raise ValueError('Live scene and nonempty episode reset indices required')
        if bool(((ids < 0) | (ids >= self.num_envs)).any()) or ids.unique().numel() != ids.numel():
            raise ValueError('Unique in-range reset indices required')
        if getattr(self, '_last_reset_physics_step', None) == self.physics_steps:
            if bool(self._reset_mask[ids].all()):
                return self.snapshot()
            raise RuntimeError('Combine all episode reset indices in one reset per physics step')
        self._dof[ids] = self._prepared_dofs
        self._roots[ids, 1] = self.rigid_guitar.prepared_root
        human_ids = (ids * 3).to(dtype=torch.int32).contiguous()
        guitar_ids = (ids * 3 + 1).to(dtype=torch.int32).contiguous()
        torch.cuda.synchronize(self.device)
        if self.gym.set_dof_state_tensor_indexed(self.sim, gymtorch.unwrap_tensor(self._dof), gymtorch.unwrap_tensor(human_ids), ids.numel()) is False:
            raise RuntimeError('GPU boundary DOF reset failed')
        if self.gym.set_actor_root_state_tensor_indexed(self.sim, gymtorch.unwrap_tensor(self._roots), gymtorch.unwrap_tensor(guitar_ids), ids.numel()) is False:
            raise RuntimeError('GPU boundary guitar root reset failed')
        torch.cuda.synchronize(self.device)
        self.target[ids] = self.reference105
        self.efforts[ids] = 0
        self.episode_steps[ids] = 0
        self._reset_mask[ids] = True
        self.reset_calls += 1
        self._last_reset_physics_step = self.physics_steps
        return self.snapshot()

    def step(self, targets105, efforts105):
        import torch
        if (self.closed or targets105.shape != self.target.shape or efforts105.shape != self.efforts.shape or
                targets105.device != self.device or efforts105.device != self.device):
            raise ValueError('Live scene and aligned batched105 controls required')
        if (not bool(torch.isfinite(targets105).all()) or not bool(torch.isfinite(efforts105).all()) or
                bool(((targets105 < self.lower - 1e-7) | (targets105 > self.upper + 1e-7)).any()) or
                bool((efforts105.abs() > self.effort_caps + 1e-6).any()) or
                bool((efforts105[:, self.metadata['position_indices']] != 0).any()) or
                bool((efforts105[:, self.metadata['zero_indices']] != 0).any())):
            raise ValueError('Finite native-bounded mixed control ownership required')
        from isaacgym import gymtorch
        self.target.copy_(targets105)
        self.efforts.copy_(efforts105)
        # Gym의 별도 native CUDA 스트림에서 Torch가 쓴 값을 볼 수 있게 한다.
        torch.cuda.synchronize(self.device)
        if self.gym.set_dof_position_target_tensor(self.sim, gymtorch.unwrap_tensor(self.target)) is False:
            raise RuntimeError('GPU POSITION target submission failed')
        if self.gym.set_dof_actuation_force_tensor(self.sim, gymtorch.unwrap_tensor(self.efforts)) is False:
            raise RuntimeError('GPU finite effort submission failed')
        self.gym.simulate(self.sim)
        self.gym.fetch_results(self.sim, True)
        self.physics_steps += 1
        self.episode_steps += 1
        self._reset_mask[:] = False
        self._refresh()
        return self.snapshot()

    @property
    def diagnostics(self):
        result = dict(schema='guitar_learning.gpu_scene.v4' if self.hand == 'left' else 'guitar_learning.gpu_scene.v3', num_envs=self.num_envs,
                    device=str(self.device), **self._actual_physics, tensor_devices=self._tensor_devices,
                    simulator_count=1, environment_count=self.num_envs,
                    physics_steps=self.physics_steps, reset_calls=self.reset_calls,
                    rigid_property_readback_max_abs_error=self._rigid_readback_max_error,
                    native_body_count=self.native_body_count, logical_body_count=self.body_count,
                    environment_aggregate=getattr(self, 'aggregate', None),
                    guitar_representation=self.metadata['guitar_representation'] if hasattr(self, 'metadata') else None,
                    diagnostic_guitar_mode=self.diagnostic_guitar_mode,
                    diagnostic_guitar_asset=self._diagnostic_guitar_asset,
                    synchronization_version='guitar_learning.cuda_gym_torch_barriers.v1',
                    state_setter_scope='Episode boundaries only; human DOF and free guitar root',
                    closed=self.closed)
        if self.hand == 'left':
            result['hand_collision'] = self.hand_collision
            result['hand_collision_native_readback_environments'] = self._hand_collision_readback_count
        return result

    def _write_audit(self):
        if self.out is not None:
            self.out.mkdir(parents=True, exist_ok=True)
            path = self.out / ('gpu_scene_final.json' if self.closed else 'gpu_scene_initial.json')
            with path.open('x') as stream:
                json.dump(self.diagnostics, stream, indent=2)

    def close(self):
        if not self.closed:
            if self.sim is not None:
                self.gym.destroy_sim(self.sim)
                self.sim = None
            self.closed = True
            self._write_audit()


# 봉인된 복합 기타 형상과 원래 논리 마커 상태.
import hashlib
import json
from pathlib import Path




_REPO_ROOT = Path(__file__).resolve().parents[2]
_ASSET_DIR = Path(__file__).resolve().parents[1] / 'assets/gpu_rigid_guitar_v1'
_MANIFEST_SHA256 = '8691885f712a687cb3e8d51001a2c9276ce7e9f3539a40ac5dc20afccd7f9ded'


# 파일 해시는 공용 스트리밍 구현으로 계산한다.
from guitar_learning.training.training_log_io import digest as _sha


# 자세·속도 행의 직렬화 순서를 공통 구현과 맞춘다.
_rigid_body_row = _body_row


class RigidGuitar:
    """하나의 물리 기타 몸체를 원래 질량중심 속도를 갖는 39개 논리 몸체로 확장한다."""
    def __init__(self, contract, device):
        import torch

        manifest_path = _ASSET_DIR / 'manifest.json'
        if _sha(manifest_path) != _MANIFEST_SHA256:
            raise ValueError('Compound guitar manifest SHA mismatch')
        self.manifest = json.loads(manifest_path.read_text())
        self.manifest_sha256 = _MANIFEST_SHA256
        self.asset_path = _ASSET_DIR / 'guitar_compound.xml'
        if _sha(self.asset_path) != self.manifest['asset_sha256']:
            raise ValueError('Compound guitar asset SHA mismatch')
        for relative, expected in self.manifest['source_sha256'].items():
            source = (_REPO_ROOT / relative).resolve()
            if _sha(source) != expected or contract['source_sha256'].get(str(source)) != expected:
                raise ValueError('Compound guitar source SHA mismatch: ' + relative)
        initial, saved = contract['initial'], contract['state']
        if (initial['guitar_body_names'] != self.manifest['logical_body_names'] or
                initial['guitar_properties']['applied'] != self.manifest['source_body_properties'] or
                _rigid_body_row(saved['guitar_body_states'][0]) != self.manifest['source_prepared_root']):
            raise ValueError('Compound guitar requires the pinned logical guitar contract')
        self.body_properties = self.manifest['body_properties']
        self.shape_properties = self.manifest['shape_properties']
        self.human_count = len(initial['human_body_names'])
        self.logical_count = len(initial['guitar_body_names'])
        self.device = torch.device(device)
        def tensor(value):
            return torch.tensor(value, dtype=torch.float32, device=self.device)
        self.prepared_root = tensor(self.manifest['prepared_root'])
        self._offsets = tensor(self.manifest['logical_position_root_m'])
        self._rotations = tensor(self.manifest['logical_quaternion_root_xyzw'])
        self._logical_com = tensor([r['COM_body_m'] for r in self.manifest['source_body_properties']])
        self._compound_com = tensor(self.body_properties[0]['COM_body_m'])

    def expand(self, native):
        """호스트 전송이나 native 상태 쓰기 없이 [N,human+guitar1+chair,13]을 확장한다.
        
        native 선형속도는 질량중심 속도다. 따라서 가상 기타 링크마다 원점 대신
        그 링크의 원래 질량중심 위치에서의 속도를 계산한다."""
        import torch
        from guitar_learning.gpu.control import apply, multiply

        if (native.ndim != 3 or native.shape[1:] != (self.human_count + 2, 13) or
                native.device != self.device or native.dtype != self.prepared_root.dtype):
            raise ValueError('Aligned float32 native compound-body state required')
        root = native[:, self.human_count:self.human_count + 1]
        guitar = root.expand(-1, self.logical_count, -1).clone()
        guitar[..., :3] = root[..., :3] + apply(root[..., 3:7], self._offsets[None])
        guitar[..., 3:7] = multiply(root[..., 3:7], self._rotations[None])
        original_com = guitar[..., :3] + apply(guitar[..., 3:7], self._logical_com[None])
        compound_com = root[..., :3] + apply(root[..., 3:7], self._compound_com)
        guitar[..., 7:10] = root[..., 7:10] + torch.cross(
            root[..., 10:13].expand_as(original_com), original_com - compound_com, dim=-1)
        return torch.cat((native[:, :self.human_count], guitar, native[:, -1:]), dim=1)


# 나머지 모든 쌍을 보존하는 선택적 왼손 손가락 사이 충돌 마스크.
import copy
import hashlib
import itertools
import json


FINGERS = ('thumb', 'index', 'middle', 'ring', 'pinky')
FINGER_MASKS = {finger: 1 << (20 + i) for i, finger in enumerate(FINGERS)}
SEGMENT_FINGER = {'LH:' + finger + str(segment): finger
                  for finger in FINGERS for segment in (1, 2, 3)}
NEW_BITS = sum(FINGER_MASKS.values())
SCHEMA = 'guitar_learning.left_inter_finger_collision.v1'


def _rows(shapes):
    return [(name, index, row['filter']) for name, values in shapes.items()
            for index, row in enumerate(values)]


def left_hand_collision_properties(human_shapes):
    """공통 왼손 비트를 손가락별로 겹치지 않는 다섯 비트로 바꾼다.
    
    같은 손가락의 마디와 이전에 제외한 손바닥·팔·대리 형상 쌍은 계속 제외한다.
    서로 다른 손가락 마디의 90쌍만 바뀐다. 물리 형상·마찰·오프셋·원본 입력은 유지한다."""
    before = _rows(human_shapes)
    if any(type(mask) is not int or mask < 0 or mask >= (1 << 20)
           for _, _, mask in before):
        raise ValueError('Pinned low-20-bit human collision masks required')
    if any(len(human_shapes.get(name, [])) != 1 or
           human_shapes[name][0]['filter'] != 128 for name in SEGMENT_FINGER):
        raise ValueError('Pinned 15 physical LH segments with common filter128 required')
    result = copy.deepcopy(human_shapes)
    for name, values in result.items():
        for row in values:
            if name in SEGMENT_FINGER:
                row['filter'] = FINGER_MASKS[SEGMENT_FINGER[name]]
            elif row['filter'] & 128:
                row['filter'] |= NEW_BITS
    after = _rows(result)
    changed, matrix = [], []
    for i, j in itertools.combinations(range(len(before)), 2):
        a, b = before[i], before[j]
        was_enabled = (a[2] & b[2]) == 0
        enabled = (after[i][2] & after[j][2]) == 0
        expected_change = (a[0] in SEGMENT_FINGER and b[0] in SEGMENT_FINGER and
                           SEGMENT_FINGER[a[0]] != SEGMENT_FINGER[b[0]])
        if enabled != (True if expected_change else was_enabled):
            raise ValueError('Selective LH collision pair invariant failed')
        matrix.append([a[0], a[1], b[0], b[1], enabled])
        if was_enabled != enabled:
            changed.append([a[0], b[0]])
    if len(changed) != 90:
        raise ValueError('Exactly 90 distinct-finger pairs must become enabled')
    encoded = json.dumps(matrix, separators=(',', ':')).encode()
    contract = dict(schema=SCHEMA, native_rule='enabled iff (filterA & filterB) == 0',
        finger_masks=FINGER_MASKS.copy(), enabled_distinct_finger_pairs=len(changed),
        preserved_other_human_shape_pairs=len(matrix)-len(changed),
        human_pair_matrix_sha256=hashlib.sha256(encoded).hexdigest(),
        changed_filters=[dict(body=a[0], shape=a[1], before=a[2], after=b[2])
                         for a, b in zip(before, after) if a[2] != b[2]],
        external_pair_preservation='Checked against actual compound-guitar and chair filters; '
            'the two source guitar proxies have no physical shape in the GPU compound asset.')
    return result, contract


def verify_external_filter_preservation(before, after, external_filters):
    """native에 전달하기 전에 실제 기타·의자 필터가 보존됐는지 확인한다."""
    if any(type(mask) is not int or mask < 0 or mask >= (1 << 20)
           for mask in external_filters):
        raise ValueError('External filter overlaps reserved LH finger bits')
    for old, new in zip(_rows(before), _rows(after)):
        for mask in external_filters:
            if ((old[2] & mask) == 0) != ((new[2] & mask) == 0):
                raise ValueError('External collision pair changed')
