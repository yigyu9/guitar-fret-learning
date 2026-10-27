"""Decision transitions over unchanged 60 Hz control and 240 Hz physics."""
import copy
import time

import torch

from guitar_learning.training.gpu_pool import FIELDS


class DecisionCollector:
    """Hold only F's sixteen finger commands; close every decision before PPO."""
    def __init__(self, policy, pool, *, gamma=.99, cost_gamma=1.):
        if not 0 <= gamma <= 1 or not 0 <= cost_gamma <= 1:
            raise ValueError('discounts must be in [0,1]')
        self.policy, self.pool = policy, pool
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
        n, device = self.pool.num_envs, self.observation['state'].device
        remaining = torch.zeros(n, dtype=torch.long, device=device)
        counts = remaining.clone()
        held = torch.zeros(n, 39, device=device)
        rows, completed = {}, []
        started = time.monotonic()
        try:
            for tick in range(horizon):
                fresh = (remaining == 0).nonzero().flatten()
                if fresh.numel():
                    planned = self.pool.plan_decisions(horizon-tick)
                    if (planned.shape != (n,) or planned.dtype != torch.long or
                            bool(((planned < 1) | (planned > horizon-tick)).any())):
                        raise ValueError('invalid planned decision lengths')
                    if self.policy.phase != 'F' and bool((planned != 1).any()):
                        raise ValueError('only F may hold decisions')
                    obs = self.pool.decision_observation(planned, self.observation)
                    inputs = [obs[key][fresh].detach().clone() for key in FIELDS]
                    result = self.policy.act(*inputs)
                    values = dict(zip(FIELDS, inputs))
                    values.update(latent=result['latent'], logp=result['logp'],
                        old_mean=result['mean'], old_log_std=result['log_std'],
                        reward_value=result['reward_value'], cost_value=result['cost_value'],
                        planned_ticks=planned[fresh],
                        start_control_tick=torch.full_like(fresh, self.control_ticks+tick),
                        episode_id=self.episode_ids[fresh].clone())
                    if not rows:
                        rows = {key: value.new_zeros((horizon, n)+value.shape[1:])
                                for key, value in values.items()}
                        for key in ('reward', 'cost', 'next_reward_value', 'next_cost_value'):
                            rows[key] = result['reward_value'].new_zeros(horizon, n)
                        for key in ('valid', 'terminated', 'truncated'):
                            rows[key] = torch.zeros(horizon, n, dtype=torch.bool, device=device)
                        rows['duration'] = torch.zeros(horizon, n, dtype=torch.long, device=device)
                    slot = counts[fresh]
                    for key, value in values.items():
                        rows[key][slot, fresh] = value
                    rows['valid'][slot, fresh] = True
                    held[fresh] = result['action']
                    remaining[fresh] = planned[fresh]
                    counts[fresh] += 1
                if self.policy.phase == 'F':
                    # The frozen support reacts to fresh coarse observations every tick.
                    obs = self.pool.decision_observation(remaining, self.observation)
                    action = self.policy(*(obs[key] for key in FIELDS))['mean'].tanh()
                    action[:, 17:33] = held[:, 17:33]
                else:
                    action = held.clone()
                action[:, 33:] = 0
                observation, reward, cost, terminated, truncated, episodes = self.pool.step(action)
                if (not bool(torch.isfinite(reward).all()) or not bool(torch.isfinite(cost).all())
                        or bool((cost < 0).any())):
                    raise FloatingPointError('finite rewards and nonnegative finite costs required')
                env = torch.arange(n, device=device)
                slot = counts-1
                duration = rows['duration'][slot, env]
                rows['reward'][slot, env] += self.gamma**duration * reward
                rows['cost'][slot, env] += self.cost_gamma**duration * cost
                rows['duration'][slot, env] += 1
                remaining -= 1
                done = terminated | truncated
                finish = ((remaining == 0) | done).nonzero().flatten()
                if finish.numel():
                    at = counts[finish]-1
                    # At the rollout cut, the next plan uses the next full horizon.
                    next_plan = self.pool.plan_decisions(horizon-tick-1 if tick+1 < horizon else horizon)
                    nxt_obs = self.pool.decision_observation(next_plan, observation)
                    nxt = self.policy(*(nxt_obs[key][finish] for key in FIELDS))
                    for key in ('reward', 'cost'):
                        rows['next_'+key+'_value'][at, finish] = nxt[key+'_value'] * ~terminated[finish]
                    rows['terminated'][at, finish] = terminated[finish]
                    rows['truncated'][at, finish] = truncated[finish]
                    if decision_callback is not None:
                        for position, identity in zip(at.tolist(), finish.tolist()):
                            start = int(rows['start_control_tick'][position, identity])
                            end = self.control_ticks+tick+1
                            decision_callback(dict(env_id=identity,
                                episode_id=int(rows['episode_id'][position, identity]),
                                policy_version=policy_version, start_control_tick=start,
                                end_control_tick=end, planned_ticks=int(rows['planned_ticks'][position, identity]),
                                duration=int(rows['duration'][position, identity]),
                                discounted_reward=float(rows['reward'][position, identity]),
                                discounted_cost=float(rows['cost'][position, identity]),
                                terminated=bool(terminated[identity]), truncated=bool(truncated[identity]),
                                raw_control_ticks=list(range(start, end))))
                completed.extend(copy.deepcopy(episodes))
                if transition_callback is not None:
                    transition_callback(tick, reward, cost, terminated, truncated, episodes)
                if progress_callback is not None:
                    progress_callback(dict(ticks=tick+1, horizon=horizon, num_envs=n,
                        transitions=(tick+1)*n, elapsed_s=time.monotonic()-started,
                        phase='gpu_step_complete'))
                ids = done.nonzero().flatten()
                if ids.numel():
                    remaining[ids] = 0
                    self.episode_ids[ids] += 1
                    self.observation = self.pool.reset(ids)[0]
                else:
                    self.observation = observation
            self.control_ticks += horizon
            used = int(counts.max())
            return {key: value[:used].detach() for key, value in rows.items()}, completed
        except BaseException:
            self.valid = False
            self.pool.valid = False
            raise
