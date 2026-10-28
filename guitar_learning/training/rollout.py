"""GPU 환경 묶음을 진행하고 정책 학습에 쓸 전이를 수집한다.

GpuPool이 물리·제어·학습 환경을 연결하며, 수집기는 매 60Hz tick의 공동 행동과 전이를 모은다."""
import copy
import time
import torch


FIELDS = ('state', 'events', 'mask', 'priority_events', 'priority_mask')


class GpuPool:
    """song 공용 GPU 실행 기반이며, 기본 J 설정이면 FingerSkillEnvironment를 만든다."""
    environment_class_override = None

    def _create_scene(self, settings, out):
        from guitar_learning.gpu.scene import GpuScene
        return GpuScene(self.num_envs, settings['specialist']['role'],
                        device=settings['device'], out=out)

    def __init__(self, settings, out):
        from guitar_learning.gpu.control import BatchedController
        from guitar_learning.gpu.environment import TensorSongEnvironment
        self.num_envs = settings['num_envs']
        self.scene = None
        self.closed = False
        self.valid = True
        try:
            if ('finger_skill' in settings and
                    settings['finger_skill']['schema'] != 'guitar_learning.finger_skill.v3'):
                raise ValueError('J-only finger_skill.v3 settings required')
            self.scene = self._create_scene(settings, out)
            self.controller = BatchedController(self.scene,
                finger_action_mode=settings['song'].get('finger_action_mode', 'incremental'))
            metadata = copy.deepcopy(self.scene.metadata)
            metadata['action_contract'] = copy.deepcopy(self.controller.contract)
            environment_class = TensorSongEnvironment
            extra = {}
            if 'finger_skill' in settings:
                from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
                environment_class = FingerSkillEnvironment
                extra['skill'] = settings['finger_skill']
            environment_class = self.environment_class_override or environment_class
            self.environment = environment_class(metadata,
                bundle=settings['song_training']['bundle'], song=settings['song'],
                hand=settings['specialist']['role'], device=settings['device'], **extra)
            self.contract = copy.deepcopy(self.environment.contract)
            self.contract['native_backend'].update(dict(
                schema='guitar_learning.gpu_batch.v3', physics='GPU PhysX',
                tensor_pipeline='cuda', simulator_count=1,
                control=copy.deepcopy(self.controller.contract),
                guitar_representation=copy.deepcopy(self.scene.metadata['guitar_representation']),
                environment_aggregate=copy.deepcopy(self.scene.metadata['environment_aggregate']),
                reset=self.scene.metadata['reset_body_source']))
            if settings['specialist']['role'] == 'left':
                self.contract['native_backend']['hand_collision'] = copy.deepcopy(
                    self.scene.metadata['hand_collision'])
            self.last_valid_efforts = self.scene.efforts.clone()
            self.observation = self.reset()[0]
        except BaseException:
            self.close()
            raise

    def reset(self, indices=None):
        import torch
        if self.closed:
            raise RuntimeError('Cannot reset a closed GPU pool')
        ids = (torch.arange(self.num_envs, device=self.scene.device) if indices is None
               else torch.as_tensor(indices, device=self.scene.device, dtype=torch.long))
        if ids.numel() == 0:
            return self.observation, []
        sample = self.scene.reset(ids)
        self.last_valid_efforts[ids] = 0
        self.controller.reset(ids, sample)
        self.observation = self.environment.reset(ids, sample)
        return self.observation, []

    def step(self, actions):
        if self.closed or not self.valid:
            raise RuntimeError('Live valid GPU pool required')
        try:
            sample = self.scene.snapshot()
            self.environment.begin_control(actions)
            target = self.controller.targets(actions, sample)
            # 정책 60Hz 한 tick 동안 같은 목표로 물리 240Hz를 네 번 진행한다.
            for _ in range(4):
                efforts = self.controller.efforts(sample)
                checks = self.controller.diagnostics
                certified = checks['finite'] & checks['chest_witness_certified']
                if not bool(certified.all()):
                    bad = (~certified).nonzero().flatten()[:8]
                    fields = {key: checks[key][bad].tolist()
                              for key in ('finite', 'chest_witness_certified')}
                    raise RuntimeError('GPU support control is nonfinite or its surface witness is uncertified: '
                                       + str(dict(env_ids=bad.tolist(), checks=fields)))
                invalid_normal = ~checks['chest_normal_defined']
                self.environment.invalidate_control(invalid_normal)
                # 기하학적으로 방향을 정의할 수 없으면 에피소드 실패로 처리한다.
                # 이번 tick이 끝날 때까지 해당 환경의 마지막 유효한 제한 범위 내 제어를 유지한다.
                # 이후 수집기가 종료 가치를 기록하고 해당 환경을 초기화한다.
                failed = self.environment.control_invalid
                efforts = efforts.where(~failed[:, None], self.last_valid_efforts)
                self.last_valid_efforts.copy_(efforts)
                sample = self.scene.step(target, efforts)
                self.environment.substep(sample)
            result = self.environment.end_control()
            self.observation = result[0]
            return result
        except BaseException:
            self.valid = False
            raise

    def set_curriculum(self, progress):
        self.observation = self.environment.set_curriculum(progress)
        return self.observation

    def set_training_progress(self, committed_transitions):
        self.environment.set_training_progress(committed_transitions)

    def close(self):
        if not self.closed:
            self.closed = True
            if self.scene is not None:
                self.scene.close()


class TensorCollector:
    """기존 song 경로의 전이 수집기. 종료 관측의 가치를 계산한 뒤 끝난 환경만 초기화한다."""
    def __init__(self, policy, pool):
        self.policy, self.pool = policy, pool
        self.observation = pool.observation
        self.valid = True

    def collect(self, horizon, *, progress_callback=None, transition_callback=None):
        import torch
        if type(horizon) is not int or horizon < 1 or not self.valid:
            raise ValueError('Valid collector and positive integer horizon required')
        rows, completed = [], []
        started = time.monotonic()
        try:
            for tick in range(horizon):
                inputs = [self.observation[key].detach().clone() for key in FIELDS]
                with torch.no_grad():
                    result = self.policy.act(*inputs)
                    observation, reward, cost, terminated, truncated, episodes = self.pool.step(result['action'])
                    next_values = self.policy(*(observation[key] for key in FIELDS))
                if (not bool(torch.isfinite(reward).all()) or
                        not bool(torch.isfinite(cost).all()) or bool((cost < 0).any())):
                    raise FloatingPointError('Finite GPU rewards and nonnegative costs required')
                row = dict(zip(FIELDS, inputs))
                row.update(latent=result['latent'], logp=result['logp'], old_mean=result['mean'],
                    old_log_std=result['log_std'], reward_value=result['reward_value'],
                    cost_value=result['cost_value'], reward=reward, cost=cost,
                    terminated=terminated, truncated=truncated,
                    next_reward_value=next_values['reward_value'] * ~terminated,
                    next_cost_value=next_values['cost_value'] * ~terminated)
                rows.append({key: value.detach().clone() for key, value in row.items()})
                completed.extend(copy.deepcopy(episodes))
                if transition_callback is not None:
                    transition_callback(tick, reward, cost, terminated, truncated, episodes)
                if progress_callback is not None:
                    progress_callback(dict(ticks=tick+1, horizon=horizon,
                        num_envs=self.pool.num_envs, transitions=(tick+1)*self.pool.num_envs,
                        elapsed_s=time.monotonic()-started, phase='gpu_step_complete'))
                done = (terminated | truncated).nonzero().flatten()
                self.observation = self.pool.reset(done)[0] if done.numel() else observation
            return {key: torch.stack([row[key] for row in rows]) for key in rows[0]}, completed
        except BaseException:
            self.valid = False
            self.pool.valid = False
            raise


class DecisionCollector:
    """기본 J 정책을 매 tick 표본화하고 종료 관측의 가치를 초기화 전에 저장한다.

    반환 buffer는 [H, N, ...]다. H는 수집 tick 수, N은 병렬 환경 수이며
    PPO 경계에서도 장면·에피소드는 이어지고 buffer만 새로 만든다.
    """
    def __init__(self, policy, pool, *, gamma=.99, cost_gamma=1.):
        if not 0 <= gamma <= 1 or not 0 <= cost_gamma <= 1:
            raise ValueError('discounts must be in [0,1]')
        self.policy, self.pool = policy, pool
        # 모든 결정은 한 tick이므로 결정 내부 할인은 없고 PPO가 tick 사이를 할인한다.
        self.gamma, self.cost_gamma = gamma, cost_gamma
        self.observation = pool.observation
        self.valid = True
        self.control_ticks = 0
        self.episode_ids = torch.zeros(pool.num_envs, dtype=torch.long,
                                      device=self.observation['state'].device)

    @torch.no_grad()
    def collect(self, horizon, *, progress_callback=None, transition_callback=None,
                decision_callback=None, policy_version=None):
        if type(horizon) is not int or horizon < 1 or not self.valid:
            raise ValueError('valid collector and positive integer horizon required')
        environment_count, device = self.pool.num_envs, self.observation['state'].device
        rows, completed = [], []
        started = time.monotonic()
        try:
            for tick in range(horizon):
                inputs = [self.observation[key].detach().clone() for key in FIELDS]
                result = self.policy.act(*inputs)
                action = result['action'].clone()
                action[:, 33:] = 0
                observation, reward, cost, terminated, truncated, episodes = self.pool.step(action)
                if (not bool(torch.isfinite(reward).all()) or not bool(torch.isfinite(cost).all())
                        or bool((cost < 0).any())):
                    raise FloatingPointError('finite rewards and nonnegative finite costs required')
                # 정상 시간 종료는 마지막 상태로 bootstrap하고, 물리 실패 등의 종료만 0으로 한다.
                next_values = self.policy(*(observation[key] for key in FIELDS))
                start_control_tick = self.control_ticks+tick
                row = dict(zip(FIELDS, inputs))
                row.update(
                    latent=result['latent'], logp=result['logp'],
                    old_mean=result['mean'], old_log_std=result['log_std'],
                    reward_value=result['reward_value'], cost_value=result['cost_value'],
                    reward=reward, cost=cost, terminated=terminated, truncated=truncated,
                    next_reward_value=next_values['reward_value'] * ~terminated,
                    next_cost_value=next_values['cost_value'] * ~terminated,
                    duration=torch.ones(environment_count, dtype=torch.long, device=device),
                    valid=torch.ones(environment_count, dtype=torch.bool, device=device),
                    start_control_tick=torch.full(
                        (environment_count,), start_control_tick, dtype=torch.long, device=device,
                    ),
                    episode_id=self.episode_ids,
                )
                # 환경의 reset과 다음 tick의 재사용 버퍼가 이미 모은 자료를 바꾸지 못하게 한다.
                rows.append({key: value.detach().clone() for key, value in row.items()})
                if decision_callback is not None:
                    for identity in range(environment_count):
                        decision_callback(dict(
                            env_id=identity,
                            episode_id=int(self.episode_ids[identity]),
                            policy_version=policy_version, start_control_tick=start_control_tick,
                            end_control_tick=start_control_tick+1, duration=1,
                            discounted_reward=float(reward[identity]),
                            discounted_cost=float(cost[identity]),
                            terminated=bool(terminated[identity]), truncated=bool(truncated[identity]),
                            raw_control_ticks=[start_control_tick],
                        ))
                completed.extend(copy.deepcopy(episodes))
                if transition_callback is not None:
                    transition_callback(tick, reward, cost, terminated, truncated, episodes)
                if progress_callback is not None:
                    progress_callback(dict(ticks=tick+1, horizon=horizon, num_envs=environment_count,
                        transitions=(tick+1)*environment_count, elapsed_s=time.monotonic()-started,
                        phase='gpu_step_complete'))
                done = (terminated | truncated).nonzero().flatten()
                if done.numel():
                    self.episode_ids[done] += 1
                    self.observation = self.pool.reset(done)[0]
                else:
                    self.observation = observation
            self.control_ticks += horizon
            return {key: torch.stack([row[key] for row in rows]) for key in rows[0]}, completed
        except BaseException:
            self.valid = False
            self.pool.valid = False
            raise
