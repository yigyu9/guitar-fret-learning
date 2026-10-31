"""정렬 초기 분포에서 압현을 배우고 원래 v9까지 확장하는 격리 연구 실행기.

공식 물리·접촉·보상·PPO를 재사용한다. 초기 상태는 에피소드 경계에서만
복원하며 목표 손가락의 네 축은 이동/정렬/압현 모든 구간에서 활성이다.
"""
if __name__ == '__main__':
    import isaacgym  # native 라이브러리는 torch보다 먼저 로드한다.
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    # native 모듈이 경로 함수를 바인딩하기 전에 격리 사본 경로를 적용한다.
    _entry_paths = nested_input_paths()
    _entry_paths.__enter__()

import argparse
import copy
import hashlib
import json
import math
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import torch
from torch import nn
from torch.distributions import Normal
from guitar_learning.training.policy import FingerSkillPolicy
from guitar_learning.training.ppo import DecisionPPOTrainer
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.gpu.scene import GpuScene
from guitar_learning.training.rollout import GpuPool
from guitar_learning.core.control import ACTIVE_NAMES

SCHEMA = 'guitar_learning.structured_press.v2'
STAGES = ('A', 'B', 'C50', 'C75', 'C100', 'free_v9')
FINGERS = ('index', 'middle', 'ring', 'pinky')
EXTRA_FIELDS = (['structured.phase.'+name for name in ('move', 'align', 'press')]
    + ['structured.phase_elapsed_s', 'structured.wrist_ready_s', 'structured.aligned_s',
       'structured.transition_elapsed_s']
    + ['structured.hold_action.'+name for name in ACTIVE_NAMES[:33]]
    + ['structured.ready.'+name for name in ('wrist', 'tangent', 'height', 'normal')])
EXTRA_DIM = len(EXTRA_FIELDS)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def active_axes(stage, finger):
    """A=목표4축, B=팔12+목표4축, C=기존 왼손33축."""
    if stage not in STAGES or finger not in FINGERS:
        raise ValueError('explicit stage and nonthumb finger required')
    axes = list(range(17+4*FINGERS.index(finger), 21+4*FINGERS.index(finger)))
    return sorted(set(axes+(list(range(12)) if stage == 'B' else
                        list(range(33)) if stage.startswith('C') or stage == 'free_v9' else [])))


def normalized_action(target, reference, lower, upper):
    """모든 단계에서 같은 v9 기준 비대칭 직접 목표각 역변환."""
    delta = target-reference
    span = torch.where(delta >= 0, upper-reference, reference-lower)
    return torch.where(span.abs() > 1e-12, delta/span.clamp_min(1e-12), torch.zeros_like(delta)).clamp(-1, 1)


def load_configuration(geometry, song, stage, *, allow_unverified=False):
    geometry = Path(geometry).resolve()
    catalog = json.loads(geometry.read_text(encoding='utf-8'))
    matches = [row for row in catalog['goals'] if row['song'] == song]
    if len(matches) != 1 or stage not in STAGES:
        raise ValueError('one catalog goal and explicit stage required')
    row = matches[0]
    if not row['candidate_valid']:
        raise ValueError('initial geometry preparation failed; not a learning result')
    if not allow_unverified and not row.get('native_verified', False):
        raise ValueError('native initial-pose validation required before training')
    if stage == 'B' and not allow_unverified and not any(
            p.get('native_verified', False) and p['candidate_valid'] for p in row['perturbations']):
        raise ValueError('B requires physically validated reachable perturbations')
    finger = row['finger']
    if isinstance(finger, int):
        finger = FINGERS[finger-1]
    return dict(schema=SCHEMA, stage=stage, song=song, finger=finger,
        geometry=str(geometry), geometry_sha256=digest(geometry),
        active_axes=active_axes(stage, finger), allow_unverified=allow_unverified,
        observation_extra_fields=EXTRA_FIELDS,
        finger_initial_std=.15, finger_std_floor=.10, support_initial_std=math.exp(-3),
        initial_distribution=dict(v9_fraction={'A': 0., 'B': 0., 'C50': .5,
            'C75': .75, 'C100': 1., 'free_v9': 1.}[stage],
            rng='torch CPU global RNG; saved by official PPO checkpoint; new episode only'),
        readiness=dict(wrist_axis_excess_m=.010, wrist_continuous_s=.10,
            tangent_m=.010, height_m=[.002, .020], normal_cos=.1, aligned_continuous_s=.10),
        support=dict(pressure_arm_action_delta=.05, transition_s=.20,
            inactive='actual initial applied target, normalized in unchanged v9 codec',
            pressure='latch last applied arm target; permit +/-0.05 raw normalized corrections',
            free_v9='all phase support restrictions removed'),
        lr=dict(floor=7.5e-6, cap=3e-5, retry_factor=.5,
            stable_updates=10, stable_kl_below=.005, recovery_factor=1.25),
        likelihood='active raw tanh latent axes only; physical support is deterministic observed-state transform')


def catalog_goal(config):
    if digest(config['geometry']) != config['geometry_sha256']:
        raise ValueError('geometry bytes changed after configuration')
    catalog = json.loads(Path(config['geometry']).read_text(encoding='utf-8'))
    return catalog, next(row for row in catalog['goals'] if row['song'] == config['song'])


class StructuredPolicy(nn.Module):
    """557열 기존 정책과 명시적 단계 상태 branch를 조합한다.

    출력 형상·v9 각도 의미는 A/B/C 모두 같다. 비활성 출력은 관측된 유지 명령이며
    표본화·logp·entropy·KL 모두 동일한 활성 축만 사용한다.
    """
    schema = 'guitar_learning.structured_press_policy.v2'
    phase, exploration = 'J', 'independent'

    def __init__(self, state_dim, *, size, contract, structured):
        super().__init__()
        if state_dim != 557+EXTRA_DIM or contract.get('structured_press') != structured:
            raise ValueError('explicit structured observation/control identity required')
        self.structured = copy.deepcopy(structured)
        base = copy.deepcopy(contract)
        base.pop('structured_press')
        base['observation']['dimension'] = 557
        base['observation']['fields'] = base['observation']['fields'][:557]
        base['observation']['scales'] = base['observation']['scales'][:557]
        self.core = FingerSkillPolicy(557, size=size, contract=base)
        self.actor_extra = nn.Sequential(nn.Linear(EXTRA_DIM, 64), nn.Tanh(), nn.Linear(64, 33))
        self.value_extra = nn.Sequential(nn.Linear(EXTRA_DIM, 64), nn.Tanh(), nn.Linear(64, 2))
        for branch in (self.actor_extra, self.value_extra):
            nn.init.zeros_(branch[-1].weight); nn.init.zeros_(branch[-1].bias)
        self.register_buffer('active_mask', torch.tensor(
            [i in structured['active_axes'] for i in range(39)], dtype=torch.bool))
        catalog, goal = catalog_goal(structured)
        hold = torch.tensor(goal['hold_target105'])
        ix = torch.tensor(catalog['action_indices'])
        reference = torch.tensor(catalog['reference105'])[ix]
        initial = normalized_action(hold[ix], reference,
            torch.tensor(catalog['action_lower']), torch.tensor(catalog['action_upper']))
        initial_latent = torch.atanh(initial.clamp(-.999999, .999999))
        with torch.no_grad():
            self.core.support_head.bias.copy_(initial_latent[:17])
            for i, finger in enumerate(FINGERS):
                self.core.finger_heads[finger][-1].bias.copy_(initial_latent[17+4*i:21+4*i])
            start = 4*FINGERS.index(structured['finger'])
            self.core.finger_log_std[start:start+4].fill_(math.log(.15))
        if structured['stage'] == 'A':
            self.core.support_encoder.requires_grad_(False)
            self.core.support_head.requires_grad_(False)
            self.core.support_log_std.requires_grad_(False)
        if structured['stage'] in ('A', 'B'):
            for finger, head in self.core.finger_heads.items():
                if finger != structured['finger']:
                    head.requires_grad_(False)
        self.architecture = dict(schema=self.schema,
            state_dim=state_dim, event_dim=24, size=size, phase='J', exploration='independent',
            likelihood=structured['likelihood'], contract=copy.deepcopy(contract),
            core_architecture=copy.deepcopy(self.core.architecture), extra_fields=EXTRA_FIELDS,
            active_axes=structured['active_axes'], structured_press=copy.deepcopy(structured))

    @property
    def support_log_std(self):
        return self.core.support_log_std

    @property
    def finger_log_std(self):
        return self.core.finger_log_std

    def actor_parameters(self):
        return [p for p in self.core.actor_parameters()+list(self.actor_extra.parameters()) if p.requires_grad]

    def value_parameters(self):
        return self.core.value_parameters()+list(self.value_extra.parameters())

    def _active_mask(self):
        return self.active_mask

    def forward(self, state, *inputs):
        if state.shape[-1] != 557+EXTRA_DIM or not torch.isfinite(state).all():
            raise ValueError('finite explicit structured state required')
        result = self.core(state[:, :557], *inputs)
        extra = state[:, 557:]
        correction = self.actor_extra(extra)
        raw = torch.cat((result['mean'][:, :33]+correction, result['mean'][:, 33:]), -1)
        hold = torch.cat((extra[:, 7:40], extra.new_zeros((len(extra), 6))), -1)
        hold_latent = torch.atanh(hold.clamp(-.999999, .999999))
        result['mean'] = torch.where(self.active_mask, raw, hold_latent)
        std = result['log_std'].clone()
        start = 17+4*FINGERS.index(self.structured['finger'])
        result['log_std'] = torch.cat((std[:, :start],
            std[:, start:start+4].clamp_min(math.log(.10)), std[:, start+4:]), -1)
        value = self.value_extra(extra)
        result['reward_value'] = result['reward_value']+value[:, 0]
        result['cost_value'] = result['cost_value']+value[:, 1]
        return result

    log_probability = FingerSkillPolicy.log_probability
    analytic_kl = FingerSkillPolicy.analytic_kl
    act = FingerSkillPolicy.act
    evaluate = FingerSkillPolicy.evaluate

    def initialize_from(self, checkpoint, *, expected_sha256):
        """동일 신구조의 가중치만 명시 이전한다. Adam/RNG/활성 마스크는 옮기지 않는다."""
        if digest(checkpoint) != expected_sha256:
            raise ValueError('explicit transfer checkpoint SHA mismatch')
        payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
        source = payload.get('identity', {}).get('architecture', {})
        source_config = source.get('structured_press', {})
        if (source.get('schema') != self.architecture['schema'] or
                source_config.get('song') != self.structured['song'] or
                source_config.get('geometry_sha256') != self.structured['geometry_sha256'] or
                source.get('size') != self.architecture['size']):
            raise ValueError('same structured policy/song/geometry/size required for explicit weight transfer')
        allowed = {'A': ('B',), 'B': ('C50',), 'C50': ('C75',), 'C75': ('C100',)}
        if (self.structured['stage'] != 'free_v9' and
                self.structured['stage'] not in allowed.get(source_config.get('stage'), ())):
            raise ValueError('explicit adjacent A->B->C50->C75->C100 transfer required')
        from guitar_learning.portability import localize
        from guitar_learning.training.ppo import PPOConfig
        from guitar_learning.training.finger_skill_runner import _validate_pins
        # 이전 모델의 원본 source/input 봉인과 원래 전체 identity를 먼저 확인한다.
        _validate_pins(payload.get('metadata'))
        saved_settings = localize(payload['metadata']['settings'])
        with torch.random.fork_rng(devices=[]):
            source_policy = StructuredPolicy(source['state_dim'], size=source['size'],
                contract=localize(source['contract']), structured=localize(source_config))
            source_trainer = StructuredTrainer(source_policy, PPOConfig(**saved_settings['ppo']))
            if source_trainer._identity() != payload['identity']:
                raise ValueError('original source checkpoint architecture/control/config mismatch')
            source_policy.load_state_dict(payload['model'], strict=True)
        weights = dict(payload['model'])
        weights['active_mask'] = self.active_mask
        if not all(torch.isfinite(value).all() for value in weights.values()):
            raise ValueError('nonfinite transferred weights')
        if digest(checkpoint) != expected_sha256:
            raise ValueError('transfer checkpoint changed during validation')
        self.load_state_dict(weights, strict=True)


class StructuredEnvironment(FingerSkillEnvironment):
    """실제 끝점 시계로 단계를 갱신하며 보상/종료/손가락 권한은 그대로 둔다."""
    structured = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.M != 1:
            raise ValueError('structured skill probe requires one virtual note')
        self.contract['structured_press'] = copy.deepcopy(self.structured)
        observation = self.contract['observation']
        plane = observation['surface_geometry']['press_surface']['plane_G']
        if abs(plane[0])+abs(plane[1]) > 1e-9 or abs(abs(plane[2])-1) > 1e-9:
            raise ValueError('explicit XY-tangent +/-Z press plane required')
        observation['fields'] += EXTRA_FIELDS
        observation['scales'] += [1.]*EXTRA_DIM
        observation['dimension'] += EXTRA_DIM
        self.scales = self._tensor(observation['scales'])

    def _allocate(self, count):
        super()._allocate(count)
        self.motion_phase = torch.zeros(count, dtype=torch.long, device=self.device)
        self.phase_elapsed = torch.zeros(count, device=self.device)
        self.ready_timers = torch.zeros(count, 2, device=self.device)
        self.transition_elapsed = torch.full((count,), .20, device=self.device)
        self.hold_action = torch.zeros(count, 39, device=self.device)
        self.last_applied_action = self.hold_action.clone()
        self.last_phase_time = torch.zeros(count, dtype=torch.float64, device=self.device)
        self.phase_counts = torch.zeros(count, 3, device=self.device)
        self.block_counts = torch.zeros(count, 4, device=self.device)
        self.start_v9 = torch.zeros(count, dtype=torch.bool, device=self.device)
        self.action_min = torch.full((count, 39), float('inf'), device=self.device)
        self.action_max = torch.full((count, 39), -float('inf'), device=self.device)

    def _reset_scope(self, indices):
        super()._reset_scope(indices)
        for value in (self.motion_phase, self.phase_elapsed, self.ready_timers,
                      self.last_phase_time, self.phase_counts, self.block_counts):
            value[indices] = 0
        self.transition_elapsed[indices] = .20
        self.action_min[indices] = float('inf')
        self.action_max[indices] = -float('inf')

    def readiness(self):
        delta = self.surface_delta[:, 0]
        # 생산 press plane +/-Z 계약에서 접선 XY와 signed height를 그대로 쓴다.
        tangent = torch.linalg.vector_norm(delta[:, :2], dim=-1)
        height = self.surface_height[:, 0]
        facing = self.surface_alignment[:, 0]
        wrist = (self.guide['delta'].abs() <= .010).all(-1)
        return torch.stack((wrist, tangent <= .010,
                            (height >= .002) & (height <= .020), facing >= .1), -1)

    def _advance_phase(self):
        if hasattr(self, 'applied_action_getter'):
            self.last_applied_action.copy_(self.applied_action_getter())
        now = self._local_time()
        dt = (now-self.last_phase_time).clamp(0, 1/60.+1e-8).float()
        self.last_phase_time.copy_(now)
        ready = self.readiness()
        conditions = torch.stack((ready[:, 0], ready.all(-1)), -1)
        self.ready_timers.copy_(torch.where(conditions, self.ready_timers+dt[:, None], 0.))
        old = self.motion_phase.clone()
        moved = self.ready_timers[:, 0]+1e-7 >= .10
        aligned = self.ready_timers[:, 1]+1e-7 >= .10
        clean = self.candidate[:, 0] & ~self.wrong[:, 0]
        self.motion_phase.copy_(torch.where(moved, 1, 0))
        self.motion_phase.copy_(torch.where(aligned | clean, 2, self.motion_phase))
        # 압현 중 높이 하한 때문에 phase를 잃지 않는다. 손목 큰 이탈만 재정렬한다.
        keep_press = (old == 2) & (self.guide['delta'].abs().amax(-1) <= .03)
        self.motion_phase[keep_press] = 2
        changed = old != self.motion_phase
        entering = changed & (self.motion_phase == 2)
        self.hold_action[entering, :12] = self.last_applied_action[entering, :12]
        self.transition_elapsed.copy_(torch.where(changed, 0., (self.transition_elapsed+dt).clamp_max(.20)))
        self.phase_elapsed.copy_(torch.where(changed, 0., self.phase_elapsed+dt))
        self.phase_counts.scatter_add_(1, self.motion_phase[:, None], dt[:, None])
        self.block_counts.add_((~ready).float()*dt[:, None])

    def end_control(self):
        self._advance_phase()
        return super().end_control()

    def _observation_state(self, state):
        base = super()._observation_state(state)
        phase = torch.nn.functional.one_hot(self.motion_phase, 3).float()
        extra = torch.cat((phase, self.phase_elapsed[:, None], self.ready_timers,
            self.transition_elapsed[:, None], self.hold_action[:, :33], self.readiness().float()), -1)
        return torch.cat((base, extra), -1)

    def _episode(self, index, failed):
        result = super()._episode(index, failed)
        result['structured_press'] = dict(schema=SCHEMA, stage=self.structured['stage'],
            initial_distribution='v9' if bool(self.start_v9[index]) else 'aligned',
            phase_seconds=self.phase_counts[index].cpu().tolist(),
            blocked_seconds=self.block_counts[index].cpu().tolist(),
            blocked_columns=['wrist', 'tangent', 'height', 'normal'],
            active_axes=self.structured['active_axes'],
            final_hold_action=self.hold_action[index].cpu().tolist(),
            executed_action_min=self.action_min[index].cpu().tolist(),
            executed_action_max=self.action_max[index].cpu().tolist(),
            scope='this completed episode only; reset rows clear counters; no H32 tail from next episode')
        return result


class StructuredScene(GpuScene):
    """에피소드 reset에서만 DOF와 일치하는 body snapshot을 선택한다."""
    def __init__(self, *args, structured, **kwargs):
        self.structured = structured
        self.catalog, self.goal = catalog_goal(structured)
        self._structured_bodies = None
        self._configured = False
        super().__init__(*args, **kwargs)
        self._v9_prepared_dofs = self._prepared_dofs.clone()
        self._v9_prepared_bodies = self._prepared_bodies.clone()
        self._structured_bodies = self._prepared_bodies.expand(self.num_envs, -1, -1).clone()
        self.initial_hold = self.reference105.expand(self.num_envs, -1).clone()
        self.initial_is_v9 = torch.ones(self.num_envs, dtype=torch.bool, device=self.device)
        self._configured = True
        self._last_reset_physics_step = None
        self.reset(torch.arange(self.num_envs, device=self.device))
        self.metadata['reset_body_source'] = dict(schema=SCHEMA,
            stage=structured['stage'], geometry_sha256=structured['geometry_sha256'],
            reference='original v9 reference105 unchanged; per-row aligned FK snapshot only at reset',
            verified=not structured['allow_unverified'])

    @property
    def body_state(self):
        if self._structured_bodies is None:
            return super().body_state
        value = self.rigid_guitar.expand(self._bodies)
        return torch.where(self._reset_mask[:, None, None], self._structured_bodies, value)

    def reset(self, indices):
        if not self._configured:
            return super().reset(indices)
        from guitar_learning.gpu.scene import _body_row
        from guitar_learning.tool.experiments.structured_geometry import snapshot_for_q
        ids = torch.as_tensor(indices, dtype=torch.long, device=self.device).flatten()
        if self._last_reset_physics_step == self.physics_steps and bool(self._reset_mask[ids].all()):
            return self.snapshot()
        fraction = self.structured['initial_distribution']['v9_fraction']
        # CPU torch RNG는 공식 checkpoint의 torch_rng와 함께 저장/복원된다.
        choices = torch.rand(len(ids)).tolist()
        dofs = []
        for index, choice in zip(ids.cpu().tolist(), choices):
            v9 = choice < fraction
            self.initial_is_v9[index] = v9
            if v9:
                dofs.append(self._v9_prepared_dofs)
                self._structured_bodies[index] = self._v9_prepared_bodies
                self.initial_hold[index] = self.reference105
                continue
            state = self.goal['state']
            target = self.goal['hold_target105']
            if self.structured['stage'] == 'B':
                candidates = [p for p in self.goal['perturbations'] if p['candidate_valid'] and
                    (p.get('native_verified', False) or self.structured['allow_unverified'])]
                if not candidates:
                    raise ValueError('no validated reachable B initial state')
                selected = candidates[int(torch.randint(len(candidates), (1,)))]
                state = snapshot_for_q(self.contract, selected['q105'])
                # 오차 초기 자세의 실제 목표를 유지하며 명목 정렬각으로 되돌리지 않는다.
                target = list(target)
                for name in ACTIVE_NAMES[:12]:
                    j = self.names.index(name); target[j] = selected['q105'][j]
            dofs.append(torch.tensor([[r['pos'], r['vel']] for r in state['human_dof_states']],
                                     dtype=torch.float32, device=self.device))
            self._structured_bodies[index] = torch.tensor([_body_row(row)
                for kind in ('human', 'guitar', 'chair') for row in state[kind+'_body_states']],
                dtype=torch.float32, device=self.device)
            self.initial_hold[index] = torch.tensor(target, device=self.device)
        original = self._prepared_dofs
        self._prepared_dofs = torch.stack(dofs)
        try:
            result = super().reset(ids)
            self.target[ids] = self.initial_hold[ids]
            return self.snapshot()
        finally:
            self._prepared_dofs = original


class StructuredPool(GpuPool):
    def _create_scene(self, settings, out):
        self.structured = settings['structured_press']
        return StructuredScene(self.num_envs, 'left', device=settings['device'], out=out,
                               structured=self.structured)

    def __init__(self, settings, out):
        config = copy.deepcopy(settings['structured_press'])
        class Environment(StructuredEnvironment):
            structured = config
        self.environment_class_override = Environment
        super().__init__(settings, out)
        self.contract['structured_press'] = config
        self.environment.applied_action_getter = lambda: normalized_action(
            self.controller.target[:, self.controller.active],
            self.controller.reference[self.controller.active],
            self.controller.action_low, self.controller.action_high)

    def reset(self, indices=None):
        observation, rows = super().reset(indices)
        ids = (torch.arange(self.num_envs, device=self.scene.device) if indices is None else
               torch.as_tensor(indices, device=self.scene.device, dtype=torch.long))
        self.controller.target[ids] = self.scene.initial_hold[ids]
        c = self.controller
        action = normalized_action(self.scene.initial_hold[ids][:, c.active],
            c.reference[c.active], c.action_low, c.action_high)
        self.environment.hold_action[ids] = action
        self.environment.last_applied_action[ids] = action
        # reset 직전 이미 적용된 유지 명령을 행동 이력에도 일치시킨다.
        self.environment.previous_action[ids] = action
        self.environment.start_v9[ids] = self.scene.initial_is_v9[ids]
        self.observation = self.environment.observation()
        return self.observation, rows

    def step(self, actions):
        env = self.environment
        active = torch.tensor([i in self.structured['active_axes'] for i in range(39)],
                              dtype=torch.bool, device=actions.device)
        executed = torch.where(active, actions, env.hold_action)
        if self.structured['stage'] != 'free_v9':
            press = env.motion_phase == 2
            hold = env.hold_action[:, :12]
            near = hold+(executed[:, :12]-hold).clamp(-.05, .05)
            blend = (env.transition_elapsed/.20).clamp(0, 1)[:, None]
            supported = executed[:, :12]+blend*(near-executed[:, :12])
            if self.structured['stage'] == 'A':
                supported = hold
            executed = executed.clone()
            executed[:, :12] = torch.where(press[:, None], supported, executed[:, :12])
        # 기록하는 latch는 rate limit/smoothing 뒤 실제 적용 목표를 사용한다.
        env.action_min.copy_(torch.minimum(env.action_min, executed))
        env.action_max.copy_(torch.maximum(env.action_max, executed))
        result = super().step(executed)
        c = self.controller
        applied = normalized_action(c.target[:, c.active], c.reference[c.active], c.action_low, c.action_high)
        env.last_applied_action.copy_(applied)
        # end_control 직후 갱신된 실제 목표를 다음 관측에 포함한다.
        self.observation = env.observation()
        return (self.observation,)+result[1:]


class StructuredTrainer(DecisionPPOTrainer):
    def __init__(self, policy, config=None):
        if policy.structured.get('allow_unverified', False):
            raise ValueError('PPO requires physically verified initial geometry; probe API is measurement only')
        super().__init__(policy, config)

    def _retry_actor_lr(self, retry):
        for group in self.actor_optimizer.param_groups:
            group['lr'] = max(7.5e-6, group['lr']*.5**(retry+1))
            group['structured_stable_updates'] = 0

    def _update(self, buffer, completed_episodes):
        result = super()._update(buffer, completed_episodes)
        stable = result['kl_retries'] == 0 and result['analytic_kl'] < .005
        for group in self.actor_optimizer.param_groups:
            count = group.get('structured_stable_updates', 0)+1 if stable else 0
            if count >= 10:
                group['lr'] = min(3e-5, group['lr']*1.25); count = 0
            group['structured_stable_updates'] = count
        result['structured_lr'] = dict(used_lr=result['actor_lr'],
            next_lr=self.actor_optimizer.param_groups[0]['lr'], stable_updates=count)
        return result


@contextmanager
def structured_runtime(config, *, initialize_from=None):
    """공식 실행기의 scene/policy/trainer factory만 연구 사본 안에서 교체한다."""
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    with nested_input_paths():
        from guitar_learning.training import finger_skill_runner, rollout, ppo
        original = finger_skill_runner._policy, rollout.GpuPool, ppo.DecisionPPOTrainer
        policies = []
        def policy_factory(settings, pool):
            if settings.get('structured_press') != config:
                raise ValueError('saved structured stage/geometry settings mismatch')
            policy = StructuredPolicy(pool.observation['state'].shape[-1], size=settings['size'],
                contract=pool.contract, structured=config).to(settings['device'])
            if initialize_from is not None:
                transfer = settings.get('structured_transfer', {})
                if transfer.get('source') != str(Path(initialize_from).resolve()):
                    raise ValueError('explicit transfer source path mismatch')
                policy.initialize_from(initialize_from, expected_sha256=transfer.get('sha256'))
            policies.append(policy)
            return policy
        finger_skill_runner._policy = policy_factory
        rollout.GpuPool = StructuredPool
        ppo.DecisionPPOTrainer = StructuredTrainer
        try:
            yield policies
        finally:
            finger_skill_runner._policy, rollout.GpuPool, ppo.DecisionPPOTrainer = original


def build_settings(song, stage, geometry, *, num_envs=64, updates=100, size='large', seed=7,
                   allow_unverified=False):
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    with nested_input_paths():
        from guitar_learning.training.launch import settings_document
        settings = settings_document(song=song, size=size, num_envs=num_envs,
            horizon=32, updates=updates, seed=seed, checkpoint_every=100)
    settings['structured_press'] = load_configuration(geometry, song, stage,
                                                     allow_unverified=allow_unverified)
    settings['ppo']['retry_lr_factor'] = .5
    settings['simple_start']['initial_pose'] = 'structured_press_v2:'+stage
    return settings


def evaluate_free_v9(checkpoint, out, *, num_envs=32):
    """지원 조건 저장본을 검증하고 가중치만 원래 v9/J33 자유 조건에서 평가한다.

    원래 optimizer 재개가 아니며 결과 계약·분모를 지원 조건과 분리한다. 각 환경의
    첫 에피소드만 모으므로 수집창 끝의 다음 에피소드가 통계에 섞이지 않는다.
    """
    from guitar_learning.portability import localize, portable
    from guitar_learning.training import finger_skill_runner as official
    from guitar_learning.training.rollout import DecisionCollector
    from guitar_learning.training.training_log_io import write, EpisodeWriter
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    if type(num_envs) is not int or not 1 <= num_envs <= 1024:
        raise ValueError('evaluation num_envs must be 1..1024')
    checkpoint, out = Path(checkpoint).resolve(), Path(out).resolve()
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    with nested_input_paths():
        official._validate_pins(payload.get('metadata'))
        settings = localize(payload['metadata']['settings'])
        source_stage = settings['structured_press']['stage']
        config = load_configuration(settings['structured_press']['geometry'],
            settings['structured_press']['song'], 'free_v9')
        settings['structured_press'] = config
        settings['num_envs'] = num_envs
        settings['simple_start']['initial_pose'] = 'v9_unassisted_model_only_evaluation'
        settings['structured_transfer'] = dict(source=str(checkpoint), sha256=digest(checkpoint),
            source_stage=source_stage, target_stage='free_v9', optimizer_resume=False,
            initial_distribution='original v9 only; all33 axes free; phase support disabled')
        out.mkdir(parents=True, exist_ok=False)
        write(out/'settings.json', portable(settings))
        pins = official._pins(settings, out, [checkpoint])
        write(out/'inputs_before.json', pins)
        writer = EpisodeWriter(out)
        pool, rows, seen = None, [], set()
        failure, cleanup_errors, source_validated = None, [], False
        try:
            with structured_runtime(config):
                pool = StructuredPool(settings, out)
                pool.environment.set_evaluation(enabled=True, full_song=True)
                pool.observation = pool.reset()[0]
                policy = StructuredPolicy(557+EXTRA_DIM, size=settings['size'],
                    contract=pool.contract, structured=config).to(settings['device'])
                policy.initialize_from(checkpoint, expected_sha256=settings['structured_transfer']['sha256'])
                source_validated = True
                collector = DecisionCollector(official._DeterministicPolicy(policy), pool,
                    gamma=settings['ppo']['gamma'], cost_gamma=settings['ppo']['cost_gamma'])
                def record(tick, reward, cost, terminated, truncated, episodes):
                    for episode in episodes:
                        index = episode['env_id']
                        if index not in seen:
                            seen.add(index); rows.append(copy.deepcopy(episode))
                            writer.append(episode, 0, tick)
                elapsed, maximum = 0, math.ceil(pool.environment.task.duration_s*60)+settings['horizon']
                while len(seen) < num_envs and elapsed < maximum:
                    horizon = min(settings['horizon'], maximum-elapsed)
                    buffer, _ = collector.collect(horizon, transition_callback=record)
                    del buffer
                    elapsed += horizon
                if len(seen) != num_envs:
                    raise RuntimeError('free v9 evaluation did not finish every scheduled first episode')
        except BaseException as error:
            failure = dict(type=type(error).__name__, message=str(error))
            raise
        finally:
            for component, close in (('episodes', writer.close),
                    ('pool', pool.close if pool is not None else lambda: None)):
                try:
                    close()
                except BaseException as error:
                    cleanup_errors.append(dict(component=component, message=str(error)))
            audit = pool.scene.diagnostics if pool and pool.scene else None
            lifecycle = bool(audit and audit['closed'] and audit['physx_use_gpu']
                and audit['use_gpu_pipeline'] and audit['simulator_count'] == 1
                and audit['environment_count'] == num_envs)
            changed = [path for path, sha in pins.items()
                       if not Path(path).is_file() or digest(path) != sha]
            report = dict(schema='guitar_learning.structured_free_v9_evaluation.v2',
                checkpoint=str(checkpoint), checkpoint_sha256=digest(checkpoint),
                source_stage=source_stage, evaluation_stage='free_v9', optimizer_resume=False,
                original_checkpoint_identity_validated=source_validated,
                source_pins_unchanged=not changed, changed_inputs=changed,
                first_episode_per_env=True, failed_episodes_in_denominator=True,
                completed=failure is None and not changed and not cleanup_errors
                    and lifecycle and source_validated and len(seen) == num_envs,
                lifecycle_verified=lifecycle, gpu_scene=audit, cleanup_errors=cleanup_errors,
                failure=failure, episodes=len(rows), summary=official.episode_summary(rows),
                failure_episode_count=sum(bool(row['termination']['physical_failure'] or
                    row['termination']['wrist_failure']) for row in rows),
                settings=portable(settings), training_contract=pool.contract if pool else None)
            write(out/'report.json', report)
            if failure is None and not report['completed']:
                raise RuntimeError('free v9 evaluation source/completion validation failed')
        return report, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('train', 'evaluate', 'render', 'evaluate-free-v9'))
    parser.add_argument('--geometry', type=Path)
    parser.add_argument('--song')
    parser.add_argument('--stage', choices=STAGES)
    parser.add_argument('--updates', type=int, default=100)
    parser.add_argument('--num-envs', type=int)
    parser.add_argument('--size', default='large', choices=('small', 'medium', 'large'))
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--initialize-from', type=Path)
    parser.add_argument('--resume', type=Path)
    args = parser.parse_args()
    if args.operation == 'evaluate-free-v9':
        if not args.checkpoint or args.initialize_from or args.resume:
            parser.error('evaluate-free-v9 requires only source --checkpoint and evaluation options')
        evaluate_free_v9(args.checkpoint, args.out, num_envs=args.num_envs or 32)
        return
    if args.operation == 'train':
        if args.checkpoint:
            parser.error('train uses --resume or --initialize-from, not --checkpoint')
        if not args.song or not args.geometry or not args.stage:
            parser.error('train requires --song --geometry --stage')
        if args.resume and args.initialize_from:
            parser.error('strict resume and explicit weight transfer are separate operations')
        settings = build_settings(args.song, args.stage, args.geometry,
            num_envs=args.num_envs or 64, updates=args.updates, size=args.size, seed=args.seed)
        if args.initialize_from:
            settings['structured_transfer'] = dict(source=str(args.initialize_from.resolve()),
                sha256=digest(args.initialize_from), scope='model weights only; fresh Adam/RNG')
        config = settings['structured_press']
    else:
        if not args.checkpoint or args.initialize_from or args.resume:
            parser.error('evaluate/render require --checkpoint; no resume/transfer')
        from guitar_learning.portability import localize
        payload = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
        settings = localize(payload['metadata']['settings'])
        config = settings['structured_press']
        if args.stage and args.stage != config['stage']:
            parser.error('evaluation uses exact saved support/initial stage')
        catalog_goal(config)
    with structured_runtime(config, initialize_from=args.initialize_from):
        if args.operation == 'train':
            from guitar_learning.training.launch import run
            run(settings, SimpleNamespace(out=args.out, resume=args.resume))
        elif args.operation == 'evaluate':
            from guitar_learning.training.finger_skill_runner import evaluate_checkpoint
            report, rows = evaluate_checkpoint(args.checkpoint, args.out,
                num_envs=args.num_envs or 32, scope='full_song')
            report['failure_episode_count'] = sum(bool(row['termination']['physical_failure'] or
                row['termination']['wrist_failure']) for row in rows)
            # 공식 평가가 생성한 보고서에 진단 합계만 덧붙인다.
            (args.out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n',
                                               encoding='utf-8')
        else:
            from guitar_learning.tool.demonstration.render_finger_skill import render
            render(args.checkpoint, args.out, num_envs=args.num_envs or 4, scope='full_song')


if __name__ == '__main__':
    try:
        main()
    finally:
        _entry_paths.__exit__(None, None, None)
