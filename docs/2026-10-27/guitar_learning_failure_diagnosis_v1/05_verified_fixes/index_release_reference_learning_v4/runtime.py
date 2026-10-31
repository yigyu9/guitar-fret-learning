"""Fresh current Jv3 NN goals on four selected axes; unchanged native control."""
import copy
import importlib.util
from pathlib import Path
import sys

import torch
from guitar_learning.training.policy import FingerSkillPolicy

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'index_release_close_lead_v2'
spec = importlib.util.spec_from_file_location('reference_learning_v2_source', SOURCE/'probe.py')
v2 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v2
spec.loader.exec_module(v2)
base = v2.base
shared = base.support()
SCHEMA = 'diagnostic.release_reference_learning.v4'
ADAPTER = dict(schema=SCHEMA, selected_actions=[17,18,19,20],
    output='selected4 tanh Gaussian absolute normalized goals',
    affine='reference+where(raw>=0,upper-reference,reference-lower)*raw',
    likelihood='selected4 normalized_goal_tanh_latents_only',
    native_conversion='unchanged trajectory_actions rate4 then original controller and DIP guard',
    selected_teacher_blending=False, phase='J', state_dimension=557)


def sigma4():
    return torch.tensor(base.read(base.EXPLORATION)['candidate_sigma4'], dtype=torch.float32).log().clamp(-5,2).exp()


def attach(contract):
    result = copy.deepcopy(contract)
    result['action']['policy_output_adapter'] = copy.deepcopy(ADAPTER)
    result['task']['short_learning']['policy_output_adapter'] = copy.deepcopy(ADAPTER)
    result['diagnostics']['short_learning']['scope'] = 'fresh Jv3 557 NN-selected4 goal policy; original native guards and nine rewards'
    return result


def settings():
    result = base.read(SOURCE/'cpu_inputs/candidate.json')
    result.update(seed=7, size='large', num_envs=128, horizon=32, updates=300, checkpoint_every=50)
    result['simple_start']['initialization'] = 'fresh seed7 current Jv3 NN; normalized-goal supervised1000 then PPO300; no old checkpoint'
    return result


class GoalPolicy(FingerSkillPolicy):
    schema = SCHEMA+'.goal_policy'

    def __init__(self, *, contract, size='large'):
        if contract['action'].get('policy_output_adapter') != ADAPTER:
            raise ValueError('Fresh V4 normalized-goal contract required')
        if contract['task']['short_learning'].get('policy_output_adapter') != ADAPTER:
            raise ValueError('Matching selected4 task adapter required')
        super().__init__(557, size=size, contract=contract)
        self.architecture.update(learned_action_indices=[17,18,19,20], likelihood=ADAPTER['likelihood'],
                                 policy_output_adapter=copy.deepcopy(ADAPTER))
        self.support_encoder.requires_grad_(False)
        self.support_head.requires_grad_(False)
        self.support_log_std.requires_grad_(False)
        for name, head in self.finger_heads.items():
            head.requires_grad_(name == 'index')
        with torch.no_grad():
            self.finger_log_std[:4].copy_(torch.tensor(base.read(base.EXPLORATION)['candidate_sigma4']).log().clamp(-5,2))

    def _active_mask(self):
        mask = torch.zeros(39, dtype=torch.bool, device=self.support_log_std.device)
        mask[17:21] = True
        return mask


class GoalPool(shared.Pool):
    def __init__(self, config, out, *, training=False):
        self.record_first_controls = not training
        self.learning_trace = []
        self.learning_episodes = []
        self.capture_learning_trace = not training
        super().__init__(config, out)
        try:
            self.contract = attach(self.contract)
            self.environment.selected_index = 4  # Current common evaluator's single-note trace only.
        except BaseException:
            try: self.close()
            except BaseException as error: self.cleanup_errors.append(dict(message=repr(error)))
            raise

    def step(self, raw):
        if raw.shape != (128,39) or not bool(torch.isfinite(raw).all()) or bool((raw.abs() > 1).any()):
            raise ValueError('Finite full39 NN goal output required')
        selected = torch.zeros_like(raw)
        selected[:,17:21] = raw[:,17:21]
        request, goal = shared.convert(self, selected)
        first = bool(self.first[0])
        first_rows = self.first.clone() if self.capture_learning_trace else None
        result = super().step(request)
        if first_rows is not None:
            for episode in result[-1]:
                if bool(first_rows[episode['env_id']]):
                    self.learning_episodes.append(shared.compact_episode(episode,self.spec))
        if self.capture_learning_trace and first:
            env = self.environment
            values = dict(raw_goal_normalized=selected[0,17:21], decoded_goal_rad=goal[0],
                requested_action=request[0], executed_action=self.last_executed_action[0],
                q=self.scene.q[0], target=self.scene.target[0], body_state=self.scene.body_state[0],
                net_body_force_n=self.scene.snapshot()['contact_force'][0], reward=result[1][0],
                candidate=env.candidate[0,[4,7,8]], wrong=env.wrong[0,[4,7,8]],
                surface_distance_m=env.surface_distance[0,[4,7,8]], surface_height_m=env.surface_height[0,[4,7,8]],
                released=env.note['released'][0,[4,7,8]], release_s=env.note['release_s'][0,[4,7,8]])
            row = {k: v.detach().cpu().numpy().copy() for k,v in values.items()}
            row.update(time_s=float(env._local_time()[0]), source_time_s=float(env._score_time()[0]))
            self.learning_trace.append(row)
        return result
