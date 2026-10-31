"""Single-environment collection preserving final-observation bootstrap semantics."""
import numpy as np
import torch


class RolloutCollector:
    fields = ('state', 'events', 'mask', 'priority_events', 'priority_mask')

    def __init__(self, policy, env, device='cpu'):
        self.policy, self.env = policy, env
        self.device = torch.device(device)
        self.observation = None
        self.episode_cost = 0.
        self.episode_reward = 0.
        self.episode_steps = 0
        self.dataset_valid = True

    def _inputs(self, observation):
        if not isinstance(observation, dict) or any(key not in observation for key in self.fields):
            raise ValueError('complete policy observation required')
        inputs = []
        for key in self.fields:
            value = np.asarray(observation[key])
            expected = np.bool_ if 'mask' in key else np.float32
            if value.dtype != expected:
                raise ValueError('observation dtype mismatch: ' + key)
            inputs.append(torch.as_tensor(value.copy(), device=self.device).unsqueeze(0))
        self.policy._validate(*inputs)
        return inputs

    def collect(self, steps):
        if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
            raise ValueError('positive integer steps required')
        if not self.dataset_valid:
            raise RuntimeError('collector invalid after collection failure')
        rows, completed = [], []
        try:
            if self.observation is None:
                self.observation, _ = self.env.reset()
            for _ in range(steps):
                inputs = self._inputs(self.observation)
                with torch.no_grad():
                    result = self.policy.act(*inputs)
                observation, reward, terminated, truncated, info = self.env.step(result['action'][0].cpu().numpy())
                if not isinstance(terminated, (bool, np.bool_)) or not isinstance(truncated, (bool, np.bool_)):
                    raise ValueError('scalar bool termination flags required')
                cost = float(info['cost'])
                reward = float(reward)
                if not np.isfinite([reward, cost]).all() or cost < 0:
                    raise ValueError('finite reward and nonnegative cost required')
                # Validate final input even when termination zeros its bootstrap.
                final_inputs = self._inputs(info.get('final_observation', observation))
                with torch.no_grad():
                    next_result = self.policy(*final_inputs)
                row = dict(zip(self.fields, inputs))
                row.update(latent=result['latent'], logp=result['logp'], old_mean=result['mean'],
                           old_log_std=result['log_std'], reward_value=result['reward_value'],
                           cost_value=result['cost_value'])
                for key, value in dict(reward=reward, cost=cost, terminated=bool(terminated), truncated=bool(truncated),
                                       next_reward_value=0. if terminated else next_result['reward_value'].item(),
                                       next_cost_value=0. if terminated else next_result['cost_value'].item()).items():
                    row[key] = torch.tensor([value], device=self.device)
                rows.append({key: value.detach().clone() for key, value in row.items()})
                self.episode_cost += cost
                self.episode_reward += reward
                self.episode_steps += 1
                if terminated or truncated:
                    reason = info.get('termination_reason')
                    if reason is not None and not isinstance(reason, str):
                        raise ValueError('termination_reason must be string or None')
                    episode = info.get('episode')
                    if episode is not None and (not isinstance(episode, dict) or episode.get('valid') is not True):
                        raise ValueError('invalid completed episode')
                    completed.append(dict(cost=self.episode_cost, reward=self.episode_reward,
                                          steps=self.episode_steps, valid=True,
                                          reason=reason or ('terminal' if terminated else 'truncated')))
                    self.episode_cost = self.episode_reward = 0.
                    self.episode_steps = 0
                    self.observation, _ = self.env.reset()
                else:
                    self.observation = observation
            return {key: torch.stack([row[key] for row in rows]) for key in rows[0]}, completed
        except BaseException:
            self.dataset_valid = False
            raise
