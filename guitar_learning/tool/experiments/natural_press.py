"""자연스러운 압현 준비 v3: 활성 J 물리·PPO를 재사용하는 명시적 비교 실행기.

과거 정렬 초기 상태 catalog만 검증 데이터로 읽는다. 봉인된 과거 Python을
import하지 않으며 모든 조건에서 phase별 팔 clamp 없이 직접각을 실행한다.
"""
if __name__ == '__main__':
    import isaacgym  # Torch보다 native 라이브러리를 먼저 로드한다.

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
from guitar_learning.training.policy import FingerSkillPolicy
from guitar_learning.training.ppo import DecisionPPOTrainer
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.gpu.scene import GpuScene
from guitar_learning.training.rollout import GpuPool
from guitar_learning.core.control import ACTIVE_NAMES

SCHEMA = 'guitar_learning.natural_press.v3'
CONDITIONS = ('E0', 'E1', 'E2', 'E3', 'E4')
AXES = ('goal4', 'arm16', 'full33')
DISTRIBUTIONS = ('aligned', 'v9')
ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT/'guitar_learning/assets/natural_press_v3'
FINGERS = ('index', 'middle', 'ring', 'pinky')
EXTRA_FIELDS = (['natural_press.phase.'+name for name in ('move', 'align', 'press')]
    + ['natural_press.phase_elapsed_s', 'natural_press.wrist_ready_s', 'natural_press.aligned_s',
       'natural_press.transition_elapsed_s']
    + ['natural_press.hold_action.'+name for name in ACTIVE_NAMES[:33]]
    + ['natural_press.ready.'+name for name in ('wrist', 'tangent', 'height', 'normal')])
EXTRA_DIM = len(EXTRA_FIELDS)



def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_catalog():
    """과거 generator는 실행하지 않고 복사 catalog와 현행 물리 입력144개를 확인한다."""
    provenance = json.loads((ASSETS/'provenance.json').read_text())
    if digest(ASSETS/'catalog.json') != provenance['catalog_sha256']:
        raise ValueError('복사 catalog SHA 불일치')
    for name, expected in provenance['active_physical_inputs'].items():
        if digest(ROOT/name) != expected:
            raise ValueError('검증 catalog의 물리 입력 변경: '+name)
    return provenance


def active_axes(scope, finger):
    if scope not in AXES or finger not in FINGERS:
        raise ValueError('명시적인 목표 손가락과 활성 축 범위 필요')
    goal = list(range(17+4*FINGERS.index(finger), 21+4*FINGERS.index(finger)))
    return sorted(set(goal+(list(range(12)) if scope == 'arm16' else list(range(33)) if scope == 'full33' else [])))


def normalized_action(target, reference, lower, upper):
    delta = target-reference
    span = torch.where(delta >= 0, upper-reference, reference-lower)
    return torch.where(span.abs() > 1e-12, delta/span.clamp_min(1e-12), torch.zeros_like(delta)).clamp(-1, 1)


def load_configuration(song, condition='E0', distribution='aligned', axes='goal4'):
    if condition not in CONDITIONS or distribution not in DISTRIBUTIONS or axes not in AXES:
        raise ValueError('새 v3 조건/초기 분포/활성 범위를 명시해야 함')
    verify_catalog()
    catalog = json.loads((ASSETS/'catalog.json').read_text())
    rows = [row for row in catalog['goals'] if row['song'] == song]
    if len(rows) != 1 or not rows[0]['candidate_valid'] or not rows[0].get('native_verified'):
        raise ValueError('검증된 단일 목표의 정렬 상태 필요')
    finger = rows[0]['finger']; finger = FINGERS[finger-1] if isinstance(finger, int) else finger
    return dict(schema=SCHEMA, condition=condition, distribution=distribution, axes=axes,
        song=song, finger=finger, geometry=str(ASSETS/'catalog.json'), geometry_sha256=digest(ASSETS/'catalog.json'),
        provenance_sha256=digest(ASSETS/'provenance.json'), active_axes=active_axes(axes, finger),
        observation_extra_fields=EXTRA_FIELDS, finger_initial_std=.15, finger_std_floor=.10,
        support_initial_std=math.exp(-3), phase_arm_support=False,
        inactive_execution='reset actual hold; v9 goal4 arm12 uses fixed aligned IK; no phase relatch',
        initial_distribution=dict(v9_fraction=1. if distribution == 'v9' else 0.,
            rng='torch CPU global RNG; official checkpoint restored; episode reset only'),
        readiness=dict(wrist_axis_excess_m=.010, wrist_continuous_s=.10,
            tangent_m=.010, height_m=[.002,.020], normal_cos=.1, aligned_continuous_s=.10),
        lr=dict(floor=7.5e-6, cap=3e-5, retry_factor=.5, stable_updates=10, stable_kl_below=.005, recovery_factor=1.25),
        likelihood='saved active axes Gaussian tanh latent; phase never blocks active actions')


def validate_config(config):
    expected = load_configuration(config['song'],config['condition'],config['distribution'],config['axes'])
    if config != expected:
        raise ValueError('저장된 v3 실험 계약과 현재 설정 불일치')
    return config


def catalog_goal(config):
    if digest(config['geometry']) != config['geometry_sha256']:
        raise ValueError('기하 데이터 SHA 불일치')
    catalog = json.loads(Path(config['geometry']).read_text())
    return catalog, next(row for row in catalog['goals'] if row['song'] == config['song'])


class NaturalPolicy(nn.Module):
    """557열 기존 정책과 명시적 단계 상태 branch를 조합한다.

    출력 형상·v9 각도 의미는 모든 명시 조건에서 같다. 비활성 출력은 관측된 유지 명령이며
    표본화·logp·entropy·KL 모두 동일한 활성 축만 사용한다.
    """
    schema = 'guitar_learning.natural_press_policy.v3'
    phase, exploration = 'J', 'independent'

    def __init__(self, state_dim, *, size, contract, natural_press):
        super().__init__()
        if state_dim != 557+EXTRA_DIM or contract.get('natural_press') != natural_press:
            raise ValueError('explicit natural_press observation/control identity required')
        self.natural_press = copy.deepcopy(natural_press)
        base = copy.deepcopy(contract)
        base.pop('natural_press')
        base['observation']['dimension'] = 557
        base['observation']['fields'] = base['observation']['fields'][:557]
        base['observation']['scales'] = base['observation']['scales'][:557]
        self.core = FingerSkillPolicy(557, size=size, contract=base)
        self.actor_extra = nn.Sequential(nn.Linear(EXTRA_DIM, 64), nn.Tanh(), nn.Linear(64, 33))
        self.value_extra = nn.Sequential(nn.Linear(EXTRA_DIM, 64), nn.Tanh(), nn.Linear(64, 2))
        for branch in (self.actor_extra, self.value_extra):
            nn.init.zeros_(branch[-1].weight); nn.init.zeros_(branch[-1].bias)
        self.register_buffer('active_mask', torch.tensor(
            [i in natural_press['active_axes'] for i in range(39)], dtype=torch.bool))
        catalog, goal = catalog_goal(natural_press)
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
            start = 4*FINGERS.index(natural_press['finger'])
            self.core.finger_log_std[start:start+4].fill_(math.log(.15))
        if natural_press['axes'] == 'goal4':
            self.core.support_encoder.requires_grad_(False)
            self.core.support_head.requires_grad_(False)
            self.core.support_log_std.requires_grad_(False)
        if natural_press['axes'] != 'full33':
            for finger, head in self.core.finger_heads.items():
                if finger != natural_press['finger']:
                    head.requires_grad_(False)
        self.architecture = dict(schema=self.schema,
            state_dim=state_dim, event_dim=24, size=size, phase='J', exploration='independent',
            likelihood=natural_press['likelihood'], contract=copy.deepcopy(contract),
            core_architecture=copy.deepcopy(self.core.architecture), extra_fields=EXTRA_FIELDS,
            active_axes=natural_press['active_axes'], natural_press=copy.deepcopy(natural_press))

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
            raise ValueError('finite explicit natural_press state required')
        result = self.core(state[:, :557], *inputs)
        extra = state[:, 557:]
        correction = self.actor_extra(extra)
        raw = torch.cat((result['mean'][:, :33]+correction, result['mean'][:, 33:]), -1)
        hold = torch.cat((extra[:, 7:40], extra.new_zeros((len(extra), 6))), -1)
        hold_latent = torch.atanh(hold.clamp(-.999999, .999999))
        result['mean'] = torch.where(self.active_mask, raw, hold_latent)
        std = result['log_std'].clone()
        start = 17+4*FINGERS.index(self.natural_press['finger'])
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



class NaturalEnvironment(FingerSkillEnvironment):
    """실제 끝점 시계로 단계를 갱신하며 보상/종료/손가락 권한은 그대로 둔다."""
    natural_press = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.M != 1:
            raise ValueError('natural_press skill probe requires one virtual note')
        self.contract['natural_press'] = copy.deepcopy(self.natural_press)
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
        self.execution_hold_action = self.hold_action.clone()
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
        result['natural_press'] = dict(schema=SCHEMA, condition=self.natural_press['condition'], distribution=self.natural_press['distribution'], axes=self.natural_press['axes'],
            initial_distribution='v9' if bool(self.start_v9[index]) else 'aligned',
            phase_seconds=self.phase_counts[index].cpu().tolist(),
            blocked_seconds=self.block_counts[index].cpu().tolist(),
            blocked_columns=['wrist', 'tangent', 'height', 'normal'],
            active_axes=self.natural_press['active_axes'],
            execution_hold_action=self.execution_hold_action[index].cpu().tolist(),
            final_hold_action=self.hold_action[index].cpu().tolist(),
            executed_action_min=self.action_min[index].cpu().tolist(),
            executed_action_max=self.action_max[index].cpu().tolist(),
            scope='this completed episode only; reset rows clear counters; no H32 tail from next episode')
        return result




class NaturalScene(GpuScene):
    """에피소드 reset에서만 DOF와 일치하는 body snapshot을 선택한다."""
    def __init__(self, *args, natural_press, **kwargs):
        self.natural_press = natural_press
        self.catalog, self.goal = catalog_goal(natural_press)
        self._natural_press_bodies = None
        self._configured = False
        super().__init__(*args, **kwargs)
        self._v9_prepared_dofs = self._prepared_dofs.clone()
        self._v9_prepared_bodies = self._prepared_bodies.clone()
        self._natural_press_bodies = self._prepared_bodies.expand(self.num_envs, -1, -1).clone()
        self.initial_hold = self.reference105.expand(self.num_envs, -1).clone()
        self.initial_is_v9 = torch.ones(self.num_envs, dtype=torch.bool, device=self.device)
        self._configured = True
        self._last_reset_physics_step = None
        self.reset(torch.arange(self.num_envs, device=self.device))
        self.metadata['reset_body_source'] = dict(schema=SCHEMA,
            distribution=natural_press['distribution'], geometry_sha256=natural_press['geometry_sha256'],
            reference='original v9 reference105 unchanged; per-row aligned FK snapshot only at reset',
            verified=True)

    @property
    def body_state(self):
        if self._natural_press_bodies is None:
            return super().body_state
        value = self.rigid_guitar.expand(self._bodies)
        return torch.where(self._reset_mask[:, None, None], self._natural_press_bodies, value)

    def reset(self, indices):
        if not self._configured:
            return super().reset(indices)
        from guitar_learning.gpu.scene import _body_row
        ids = torch.as_tensor(indices, dtype=torch.long, device=self.device).flatten()
        if self._last_reset_physics_step == self.physics_steps and bool(self._reset_mask[ids].all()):
            return self.snapshot()
        fraction = self.natural_press['initial_distribution']['v9_fraction']
        # CPU torch RNG는 공식 checkpoint의 torch_rng와 함께 저장/복원된다.
        choices = torch.rand(len(ids)).tolist()
        dofs = []
        for index, choice in zip(ids.cpu().tolist(), choices):
            v9 = choice < fraction
            self.initial_is_v9[index] = v9
            if v9:
                dofs.append(self._v9_prepared_dofs)
                self._natural_press_bodies[index] = self._v9_prepared_bodies
                self.initial_hold[index] = self.reference105
                continue
            state = self.goal['state']
            target = self.goal['hold_target105']
            dofs.append(torch.tensor([[r['pos'], r['vel']] for r in state['human_dof_states']],
                                     dtype=torch.float32, device=self.device))
            self._natural_press_bodies[index] = torch.tensor([_body_row(row)
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




class NaturalPool(GpuPool):
    def _create_scene(self, settings, out):
        self.natural_press = settings['natural_press']
        return NaturalScene(self.num_envs, 'left', device=settings['device'], out=out,
                               natural_press=self.natural_press)

    def __init__(self, settings, out):
        config = copy.deepcopy(settings['natural_press'])
        class Environment(NaturalEnvironment):
            natural_press = config
            natural_preparation = dict(schema='guitar_learning.natural_preparation.v3', condition=config['condition'])
        self.environment_class_override = Environment
        super().__init__(settings, out)
        self.contract['natural_press'] = config
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
        if not hasattr(self, 'execution_hold_action'):
            self.execution_hold_action = torch.zeros_like(self.environment.hold_action)
            self.environment.execution_hold_action = self.execution_hold_action
        self.execution_hold_action[ids] = action
        if self.natural_press['distribution'] == 'v9' and self.natural_press['axes'] == 'goal4':
            catalog, goal = catalog_goal(self.natural_press)
            aligned = torch.tensor(goal['hold_target105'],device=c.device,dtype=c.reference.dtype)[c.active]
            fixed = normalized_action(aligned,c.reference[c.active],c.action_low,c.action_high)
            self.execution_hold_action[ids, :12] = fixed[:12]
        self.observation = self.environment.observation()
        return self.observation, rows

    def step(self, actions):
        env = self.environment
        active = torch.tensor([i in self.natural_press['active_axes'] for i in range(39)],
                              dtype=torch.bool, device=actions.device)
        executed = torch.where(active, actions, self.execution_hold_action)
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




class NaturalTrainer(DecisionPPOTrainer):
    def _retry_actor_lr(self, retry):
        for group in self.actor_optimizer.param_groups:
            group['lr'] = max(7.5e-6, group['lr']*.5**(retry+1))
            group['natural_press_stable_updates'] = 0

    def _update(self, buffer, completed_episodes):
        result = super()._update(buffer, completed_episodes)
        stable = result['kl_retries'] == 0 and result['analytic_kl'] < .005
        for group in self.actor_optimizer.param_groups:
            count = group.get('natural_press_stable_updates', 0)+1 if stable else 0
            if count >= 10:
                group['lr'] = min(3e-5, group['lr']*1.25); count = 0
            group['natural_press_stable_updates'] = count
        result['natural_press_lr'] = dict(used_lr=result['actor_lr'],
            next_lr=self.actor_optimizer.param_groups[0]['lr'], stable_updates=count)
        return result




def initialize_policy(policy, checkpoint, expected_sha):
    """새 v3의 동일 조건 모델만 엄격 검증한 뒤 mask 외 가중치를 이전한다."""
    from guitar_learning.portability import localize
    from guitar_learning.training import finger_skill_runner as runner
    from guitar_learning.training.ppo import PPOConfig
    if digest(checkpoint) != expected_sha:
        raise ValueError('이전 원본 체크포인트 SHA 불일치')
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    runner._validate_pins(payload['metadata'])
    saved = localize(payload['metadata']['settings'])
    source = validate_config(saved['natural_press'])
    target = policy.natural_press
    if (payload['identity']['architecture']['schema'] != NaturalPolicy.schema or
            any(source[key] != target[key] for key in ('song','finger','condition','geometry_sha256','provenance_sha256'))):
        raise ValueError('동일 새 v3 목표/조건/기하만 명시 이전 가능')
    with torch.random.fork_rng(devices=[]):
        original = NaturalPolicy(payload['identity']['architecture']['state_dim'], size=saved['size'],
            contract=localize(payload['identity']['architecture']['contract']), natural_press=source)
        trainer = NaturalTrainer(original, PPOConfig(**saved['ppo']))
        if trainer._identity() != payload['identity']:
            raise ValueError('원본 정책/PPO/입력 identity 불일치')
        original.load_state_dict(payload['model'], strict=True)
    weights = dict(payload['model']); weights['active_mask'] = policy.active_mask
    if not all(torch.isfinite(value).all() for value in weights.values()):
        raise ValueError('비유한 원본 가중치')
    policy.load_state_dict(weights, strict=True)
    if digest(checkpoint) != expected_sha:
        raise ValueError('이전 중 원본 체크포인트 변경')


@contextmanager
def natural_runtime(config, *, initialize_from=None):
    """공식 실행기의 네 factory를 프로세스 범위에서 연결하고 항상 복원한다."""
    from guitar_learning.training import finger_skill_runner as runner, rollout, ppo
    validate_config(config)
    original = runner._policy, rollout.GpuPool, ppo.DecisionPPOTrainer, runner.checkpoint_metadata, runner._pins
    def factory(settings, pool):
        if settings.get('natural_press') != config:
            raise ValueError('실행 중 저장 설정/환경 조건 불일치')
        result = NaturalPolicy(pool.observation['state'].shape[-1], size=settings['size'],
            contract=pool.contract, natural_press=config).to(settings['device'])
        if initialize_from is not None:
            transfer = settings['natural_press_transfer']
            if transfer['source'] != str(Path(initialize_from).resolve()):
                raise ValueError('명시 이전 source 경로 불일치')
            initialize_policy(result, initialize_from, transfer['sha256'])
        return result
    def metadata(*args, **kwargs):
        if initialize_from is not None:
            kwargs['lineage'] = list(kwargs.get('lineage', ()))+[Path(initialize_from).resolve()]
            kwargs.update(model_only_transition=True, optimizer_updates=0, no_training=True)
        return original[3](*args, **kwargs)
    def pins(settings, out, extra=()):
        creation = [Path(initialize_from).resolve()] if initialize_from is not None else []
        return original[4](settings, out, list(extra)+creation)
    runner._policy, rollout.GpuPool, ppo.DecisionPPOTrainer, runner.checkpoint_metadata = factory, NaturalPool, NaturalTrainer, metadata
    runner._pins = pins
    try:
        yield
    finally:
        runner._policy, rollout.GpuPool, ppo.DecisionPPOTrainer, runner.checkpoint_metadata = original[:4]
        runner._pins = original[4]


def build_settings(song, condition='E0', distribution='aligned', axes='goal4', *, updates=100, seed=7, num_envs=64, size='large'):
    from guitar_learning.training.launch import settings_document
    settings = settings_document(song=song, size=size, num_envs=num_envs, horizon=32,
        updates=updates, seed=seed, checkpoint_every=100)
    settings['natural_press'] = load_configuration(song, condition, distribution, axes)
    settings['ppo']['retry_lr_factor'] = .5
    settings['simple_start']['initial_pose'] = 'natural_press_v3:'+distribution+':'+axes
    return settings


def export_free(checkpoint, settings, out):
    """지원 없는 v9/full33 평가용 모델을0업데이트로 생성한다. 학습 완료가 아니다."""
    from guitar_learning.training import finger_skill_runner as runner
    saved = copy.deepcopy(settings)
    config = saved['natural_press']
    saved['natural_press'] = load_configuration(config['song'],config['condition'],'v9','full33')
    saved['simple_start']['initial_pose'] = 'natural_press_v3:v9:full33:model_only'
    saved['natural_press_transfer'] = dict(source=str(checkpoint), sha256=digest(checkpoint),
        scope='same v3 weights only; fresh Adam; zero updates; no formal training pass')
    spec = saved['finger_skill']
    schedule = runner.ExposureSchedule(spec['planned_transitions'],spec['full_song_after'])
    with natural_runtime(saved['natural_press'], initialize_from=checkpoint):
        result = runner._train_phase(saved,out/'J',schedule,updates=0)
    report = result['report']
    if (not report.get('completed') or report.get('optimizer_updates') != 0 or
            report.get('updates_in_run') != 0 or report.get('gpu_scene',{}).get('physics_steps') != 0):
        raise RuntimeError('0업데이트 모델 이전 미완료')
    path = out/'J/final.pt'
    original = torch.load(checkpoint,map_location='cpu',weights_only=False)['model']
    exported = torch.load(path,map_location='cpu',weights_only=False)
    if exported['updates'] != 0 or any(key != 'active_mask' and not torch.equal(value,exported['model'][key]) for key,value in original.items()):
        raise ValueError('0업데이트 이전의 가중치/업데이트 불일치')
    return path, saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('train','evaluate','render'))
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--song',default='virtual_finger_v9_middle_s3_f6')
    parser.add_argument('--condition',choices=CONDITIONS)
    parser.add_argument('--distribution',choices=DISTRIBUTIONS,default='aligned')
    parser.add_argument('--axes',choices=AXES,default='goal4')
    parser.add_argument('--updates',type=int,default=100)
    parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--num-envs',type=int)
    parser.add_argument('--size',choices=('small','medium','large'),default='large')
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--resume',type=Path)
    parser.add_argument('--free-v9',action='store_true')
    args = parser.parse_args()
    from guitar_learning.training import finger_skill_runner as runner
    from guitar_learning.portability import localize
    out = args.out.resolve()
    if out.exists():raise FileExistsError('기존 출력 덮어쓰기 금지: '+str(out))
    if args.updates < 1:parser.error('updates는 양수여야 함')
    if args.operation == 'evaluate' and args.num_envs not in (None,32):
        parser.error('고정 최초32 평가에는 --num-envs 32만 허용')
    source = args.resume if args.operation == 'train' else args.checkpoint
    if args.operation == 'train' and (args.checkpoint or args.free_v9):parser.error('train은 --resume만 허용')
    if args.operation != 'train' and (not source or args.resume):parser.error('evaluate/render는 --checkpoint 필요')
    if source:
        source = source.resolve();source_sha = digest(source)
        payload = torch.load(source,map_location='cpu',weights_only=False)
        runner._validate_pins(payload['metadata'])
        settings = localize(payload['metadata']['settings'])
        config = validate_config(settings['natural_press'])
        if args.condition is not None and args.condition != config['condition']:
            raise ValueError('저장 조건과 다른 평가/재개 조건')
    else:
        settings = build_settings(args.song,args.condition or 'E0',args.distribution,args.axes,
            updates=args.updates,seed=args.seed,num_envs=args.num_envs or 64,size=args.size)
    if args.operation == 'train':
        if source and (args.seed != settings['seed'] or
                args.num_envs is not None and args.num_envs != settings['num_envs']):
            raise ValueError('strict resume는 저장한 seed/환경 수 유지')
        # 추가 블록 길이는 공식 run의 수동 예산 확장을 따른다. 최초 노출 일정은 보존한다.
        settings['updates'] = args.updates
        with natural_runtime(settings['natural_press']):runner.run(settings,SimpleNamespace(out=out,resume=source))
        report = json.loads((out/'report.json').read_text())
    else:
        target = out
        if args.free_v9:
            out.mkdir(parents=True)
            source, settings = export_free(source,settings,out/'model_only')
            target = out/'evaluation' if args.operation == 'evaluate' else out/'render'
        with natural_runtime(settings['natural_press']):
            if args.operation == 'evaluate':
                report, _ = runner.evaluate_checkpoint(source,target,num_envs=args.num_envs or 32,
                    scope='full_song',max_episodes=32)
            else:
                from guitar_learning.tool.demonstration.render_finger_skill import render
                report = render(source,target,num_envs=args.num_envs or 4,scope='full_song')
    if args.checkpoint and digest(args.checkpoint.resolve()) != source_sha:
        raise ValueError('평가 중 원본 체크포인트 변경')
    if not report.get('completed') or report.get('failure'):
        raise RuntimeError('실행 미완료; report.json 확인')


if __name__ == '__main__':main()
