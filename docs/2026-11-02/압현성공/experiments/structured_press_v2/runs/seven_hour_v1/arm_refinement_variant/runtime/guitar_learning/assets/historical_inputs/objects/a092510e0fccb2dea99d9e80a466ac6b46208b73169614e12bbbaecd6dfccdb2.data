"""Original Strike semantics on copied native CPU state; owns no simulator writes."""
from .environment import np  # Isaac Gym must precede Torch.
import inspect
from unittest.mock import patch
import torch
from tab2body.env.base import GuitarEnvBase
from tab2body.env.tasks.task_strike import StrikeTask, pack_strike_v2_blocks
from .run_joint_hold import native_state


def state_rows(rows):
    result = []
    for row in rows:
        p, q, v, w = row['pose']['p'], row['pose']['r'], row['vel']['linear'], row['vel']['angular']
        result.append([p[k] for k in 'xyz'] + [q[k] for k in 'xyzw'] +
                      [v[k] for k in 'xyz'] + [w[k] for k in 'xyz'])
    return torch.tensor(result, dtype=torch.float32)


class ReadonlyGym:
    def __getattr__(self, name):
        raise RuntimeError('Strike view cannot access simulator: ' + name)


def snapshot_backend(env):
    b = GuitarEnvBase.__new__(GuitarEnvBase)
    b.num_envs, b.device = 1, 'cpu'
    b.locked_dof_keywords = ('Hip', 'Knee', 'Ankle', 'Toe')
    b.human_hard_limits_enabled, b.human_hard_limit_path = False, None
    b.pose, b.P, b._gains_src = env.pose, env.pose['params'], {}
    b.gym = ReadonlyGym()
    b.sim = b.asset_human = b.asset_guitar = b.asset_chair = None
    b.envs, b.h_actors, b.g_actors = [], [], []
    b.dof_names, b.body_names, b.gbody_names = list(env.names), list(env.human_bodies), list(env.guitar_bodies)
    b.n_dof, b.n_hbody = len(b.dof_names), len(b.body_names)
    b._bpe = b.n_hbody + len(b.gbody_names)
    b.hbody_index = dict(zip(b.body_names, range(b.n_hbody)))
    b.gbody_index = dict(zip(b.gbody_names, range(len(b.gbody_names))))
    b._dof_props = env.gym.get_actor_dof_properties(env.env, env.human).copy()
    b._init_pose_np = env.initial_q.copy()
    b._kp_np, b._kd_np = b._dof_props['stiffness'].copy(), b._dof_props['damping'].copy()
    b._authored_dof_lower_np, b._authored_dof_upper_np = env.lower.copy(), env.upper.copy()
    b.human_hard_limit_audit = {'enabled': False}
    b.collision_audit = dict(env.self_collision_policy)
    b.dof_state = torch.empty(b.n_dof, 2)
    b.root_state = torch.empty(2, 13)
    b.body_state = torch.empty(b._bpe, 13)
    # Not measured: source observation/reward do not use forces. Keep sentinel NaN
    # until native net-force reading succeeds; never fabricate a zero measurement.
    b.contact_force = torch.full((b._bpe, 3), float('nan'))
    b.locked = torch.zeros(b.n_dof, dtype=torch.bool)
    b._locked_flat, b._zeros_dof = b.locked.clone(), torch.zeros(b.n_dof)
    b.kp, b.tau_limit = torch.tensor(b._kp_np), torch.tensor(b._dof_props['effort'].copy())
    b.applied_tau = torch.zeros(1, b.n_dof)  # unused computation buffer, not measured torque
    b.dof_lower, b.dof_upper = torch.tensor(env.lower.copy()), torch.tensor(env.upper.copy())
    b.authored_dof_lower, b.authored_dof_upper = b.dof_lower.clone(), b.dof_upper.clone()
    b.raw_init_pose, b.init_pose = torch.tensor(env.initial_q.copy()), torch.tensor(env.initial_q.copy())
    b.init_pose_limit_adjustment = torch.zeros(b.n_dof)
    b.pd_target = b.init_pose.clone()
    b.nonlocked_idx, b.n_nonlocked = torch.arange(b.n_dof), b.n_dof
    b.progress_buf = torch.zeros(1, dtype=torch.long)
    refresh_native(b, env)
    b.root_init = b.root_state.clone()
    return b


def refresh_native(view, env):
    s = native_state(env)
    view.dof_state.copy_(torch.tensor([[d['pos'], d['vel']] for d in s['human_dof_states']]))
    h, g = state_rows(s['human_body_states']), state_rows(s['guitar_body_states'])
    view.body_state.copy_(torch.cat([h, g]))
    view.root_state.copy_(torch.stack([h[0], g[0]]))
    forces = env.gym.get_env_rigid_contact_forces(env.env)
    view.contact_force.copy_(torch.tensor([[f['x'], f['y'], f['z']] for f in forces[:view._bpe]]))
    if not torch.isfinite(view.contact_force).all():
        raise ValueError('nonfinite native contact force')


class NativeStrikeView(StrikeTask):
    def _disable_pluck_range_collision(self):
        # Native environment already configures marker filters. Source view cannot mutate them.
        self.native_collision_policy_used = True

    def reset_idx(self, env_ids):
        self.terminal_reset_requested = True  # stop at done, preserve terminal state

    def _compose_reset_observation(self, terminal_obs, env_ids):
        return terminal_obs

    def refresh(self):
        refresh_native(self, self.owner)

    def step_physics(self):
        self.advance_native(self)

    def close(self):
        pass  # only the native owner can close the simulation

    def strict_observation(self):
        return pack_strike_v2_blocks(self._build_strike_v2_blocks(), validate_finite=True)


def create_view(env, checkpoint, goal, grip):
    backend = snapshot_backend(env)
    config = checkpoint['checkpoint_contract']['payload']['config']['strike']
    signature = inspect.signature(StrikeTask.__init__).parameters
    kwargs = {k: v for k, v in config.items() if k in signature}
    original = GuitarEnvBase.__init__
    def shared_init(task, *args, **kw):
        return original(task, *args, **kw, shared_backend=backend)
    with patch.object(GuitarEnvBase, '__init__', shared_init):
        view = NativeStrikeView(goal, grip, num_envs=1, device='cpu', headless=True,
                                random_start=False, **kwargs)
    view.owner, view.terminal_reset_requested = env, False
    # Source constructor applies its grip reference to cached reset targets. Restore actual
    # native initial targets; never apply source reset/reference pose to physical state.
    view.init_pose.copy_(torch.tensor(env.initial_q.copy()))
    view.pd_target.copy_(view.init_pose)
    view.prev_action.copy_(view.actions_for_pd_targets(view.init_pose[view.ctrl_idx][None]))
    context = checkpoint['training_context']
    mapping = {'stage': 'stage', 'tolerance_ms': 'timing_tolerance_ms',
               'tempo_lambda': 'tempo_lambda', 'strum_span': 'strum_span',
               's2_profile_name': 's2_profile_name', 'zone_active': 's2_zone_active',
               'timing_reward_core_ms': 'timing_reward_core_ms',
               'duration_reward_core_ms': 'duration_reward_core_ms',
               'approach_lead_s': 'approach_lead_s', 'timing_early_grace_ms': 'timing_early_grace_ms',
               'timing_early_penalty_scale_ms': 'timing_early_penalty_scale_ms',
               'song_events_per_episode': 'song_events_per_episode'}
    kw = {k: context['curriculum_' + v] for k, v in mapping.items()}
    view.set_curriculum_stage(**kw)
    view.set_evaluation_mode(full_song=True, reset=False)
    view._reset_task_state(torch.tensor([0]))
    view._previous_tip_g.copy_(view.to_guitar_frame(view.hbody_pos('RH:pick')[:, None])[:, 0])
    view._previous_tip_valid.fill_(True)
    return view
