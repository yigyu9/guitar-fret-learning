"""Readonly Fret metrics and source action semantics on copied native state."""
from .environment import np
import ast
import hashlib
import inspect
import textwrap
from pathlib import Path
import torch
from tab2body.env.base import GuitarEnvBase
from tab2body.env.tasks import task_fret
from tab2body.env.tasks.task_fret import FretTask
from tab2body.env.config import configured_kwargs
from tab2body.env.joint_limits import apply_joint_limit_profile
from tab2body.cfg import FRET
from tab2body.fret_v2_contract import pack_fret_v2_blocks
from tab2body.tools.fret_rollout_contract import rollout_configuration
from .strike_native_view import snapshot_backend, refresh_native

SOURCE_SHA = '095b1860058ebab5d89785a8a99b1fb97cf26a25308be90d48f8d7a3b5dcdd92'


def source_functions():
    """Extract tensor-only seams; leave original shared-physics guards intact."""
    path = Path(inspect.getsourcefile(FretTask))
    if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('Fret source changed; re-review extraction')
    step = ast.parse(textwrap.dedent(inspect.getsource(FretTask.step))).body[0]
    guard = ast.parse('if self._shared_backend is not None: pass').body[0].test
    assert ast.dump(step.body[0].test) == ast.dump(guard)
    expected = ast.parse('self.apply_actions(actions)\nself.step_physics()\nself.refresh()\nself.progress_buf += 1').body
    assert [ast.dump(n) for n in step.body[1:5]] == [ast.dump(n) for n in expected]
    assert ast.dump(step.body[5]) == ast.dump(ast.parse('base_reasons = self.termination_reasons()').body[0])
    step.name = 'evaluate_after_physics'
    step.args.args = step.args.args[:1]
    step.body = step.body[5:]
    action = ast.parse(textwrap.dedent(inspect.getsource(FretTask.apply_actions))).body[0]
    assert isinstance(action.body[0], ast.Expr) and isinstance(action.body[0].value, ast.Constant)
    assert ast.dump(action.body[1].test) == ast.dump(guard)
    assert ast.dump(action.body[-1]) == ast.dump(ast.parse('super().apply_actions(actions)').body[0])
    action.name = 'cache_policy_actions'
    action.body = action.body[2:-1] + ast.parse('GuitarEnvBase.apply_actions(self, actions)').body
    module = ast.fix_missing_locations(ast.Module(body=[step, action], type_ignores=[]))
    namespace = dict(vars(task_fret))
    exec(compile(module, str(path)+':native_tensor_seams', 'exec'), namespace)
    return namespace[step.name], namespace[action.name]


class NativeFretView(FretTask):
    evaluate_after_physics, cache_policy_actions = source_functions()

    def enable_thumb_support_collision(self, preserve_other_filters=False):
        self.native_collision_policy_used = True

    def _load_success_pose_library(self, *args, **kwargs):
        self.native_pose_library_disabled = True

    def reset_idx(self, env_ids):
        self.terminal_reset_requested = True

    def _compose_reset_observation(self, terminal_obs, env_ids):
        return terminal_obs

    def refresh(self):
        refresh_native(self, self.owner)

    def strict_observation(self):
        return pack_fret_v2_blocks(self._build_fret_v2_blocks(), validate_finite=True)

    def step_physics(self):
        raise RuntimeError("only native owner advances physics")

    def close(self):
        pass


def create_fret_view(env, checkpoint, goal, hand_targets):
    config, payload = rollout_configuration(checkpoint, FRET, goal=str(goal),
        hand_targets=str(hand_targets), root=Path(task_fret.__file__).parents[2])
    backend = snapshot_backend(env)
    lower, upper, audit = apply_joint_limit_profile(env.names, env.lower, env.upper,
                                                   config['human_hard_limit_path'])
    # These are source normalization/target ranges, not a claim about native PhysX limits.
    backend.human_hard_limits_enabled = True
    backend.human_hard_limit_path = config['human_hard_limit_path']
    backend.human_hard_limit_audit = dict(audit, physx_verified=False,
                                        scope='source view target ranges; native XML unchanged')
    backend.dof_lower.copy_(torch.tensor(lower)); backend.dof_upper.copy_(torch.tensor(upper))
    view = NativeFretView(**configured_kwargs(FretTask, config, reward_config=config,
        goal_path=str(goal), hand_targets_path=str(hand_targets), num_envs=1, device='cpu',
        headless=True, seed=42, reset_noise=0., random_start=False, shared_backend=backend))
    view.owner, view.terminal_reset_requested = env, False
    view.init_pose.copy_(torch.tensor(env.initial_q.copy()))
    view.pd_target.copy_(torch.tensor(env.target.copy()))
    view.set_curriculum_stage('full_song', reset=False)
    view.goals.reset(torch.tensor([0]))
    view.reward_fn.reset(torch.tensor([0]))
    view.prev_action.copy_(view.actions_for_pd_targets(view.pd_target[view.ctrl_idx][None]))
    return view, payload
