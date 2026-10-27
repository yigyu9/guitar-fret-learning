"""One GPU simulator and a tensor collector; no per-environment processes."""
import copy
import time


FIELDS = ('state', 'events', 'mask', 'priority_events', 'priority_mask')


class GpuPool:
    def __init__(self, settings, out):
        from guitar_learning.gpu.scene import GpuScene
        from guitar_learning.gpu.control import BatchedController
        from guitar_learning.gpu.environment import TensorSongEnvironment
        self.num_envs = settings['num_envs']
        self.scene = None
        self.closed = False
        self.valid = True
        try:
            self.scene = GpuScene(self.num_envs, settings['specialist']['role'],
                                  device=settings['device'], out=out)
            self.controller = BatchedController(self.scene)
            metadata = copy.deepcopy(self.scene.metadata)
            metadata['action_contract'] = copy.deepcopy(self.controller.contract)
            self.environment = TensorSongEnvironment(metadata,
                bundle=settings['song_training']['bundle'], song=settings['song'],
                hand=settings['specialist']['role'], device=settings['device'])
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
                # A geometrically undefined direction is an episode failure.
                # Hold that row's last bounded control until this tick ends;
                # the collector records terminal values and resets it then.
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

    def close(self):
        if not self.closed:
            self.closed = True
            if self.scene is not None:
                self.scene.close()


class TensorCollector:
    """Bootstrap the terminal observation before resetting only finished rows."""
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
                    nxt = self.policy(*(observation[key] for key in FIELDS))
                if (not bool(torch.isfinite(reward).all()) or
                        not bool(torch.isfinite(cost).all()) or bool((cost < 0).any())):
                    raise FloatingPointError('Finite GPU rewards and nonnegative costs required')
                row = dict(zip(FIELDS, inputs))
                row.update(latent=result['latent'], logp=result['logp'], old_mean=result['mean'],
                    old_log_std=result['log_std'], reward_value=result['reward_value'],
                    cost_value=result['cost_value'], reward=reward, cost=cost,
                    terminated=terminated, truncated=truncated,
                    next_reward_value=nxt['reward_value'] * ~terminated,
                    next_cost_value=nxt['cost_value'] * ~terminated)
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
