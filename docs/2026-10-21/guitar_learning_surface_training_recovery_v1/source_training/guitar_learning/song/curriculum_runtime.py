"""One shared performance schedule, checkpointed with the selected policy."""
import copy
import numpy as np
import torch

from guitar_learning.song.left_curriculum import CurriculumState


class CurriculumCoordinator:
    def __init__(self, policy, pool):
        self.policy, self.pool = policy, pool
        self.gpu_surface = policy.architecture['contract']['reward'].get('schema') == 'guitar_learning.gpu_tensor_song_reward.v3'
        if self.gpu_surface:
            from guitar_learning.song.gpu_left_curriculum import CurriculumState as SurfaceCurriculumState
            self.state = SurfaceCurriculumState(pool.environment.finger_counts)
        else:
            self.state = CurriculumState()
        self.state_size = self.state.state_vector().size
        policy.register_buffer('left_curriculum_state', torch.as_tensor(
            self.state.state_vector(), dtype=torch.float64,
            device=next(policy.parameters()).device))

    def restore(self):
        self.state.load_state(self.policy.left_curriculum_state.detach().cpu().numpy())
        return self.pool.set_curriculum(self.state.progress)

    def advance(self, completed, observation):
        episodes = []
        for row in completed:
            if row.get('valid') is not True or row.get('reason') not in ('timeline_complete', 'terminal_failure'):
                continue
            value = row.get('left_curriculum')
            if not isinstance(value, dict):
                raise ValueError('completed left episode must carry curriculum evidence')
            if self.gpu_surface:
                episodes.append(dict(full_safe=bool(value['full_safe'] and row['reason']=='timeline_complete'),
                    finger_metrics=value['finger_metrics']))
            else:
                episodes.append(dict(full_safe=bool(value['full_safe'] and row['reason']=='timeline_complete'),
                    reach_fraction=value['reach_fraction'], contact_fraction=value['contact_fraction']))
        before = self.state.progress
        result = self.state.observe(episodes)
        vector = self.state.state_vector()
        if vector.shape != (self.state_size,) or not np.isfinite(vector).all():
            raise ValueError('finite curriculum checkpoint state required')
        with torch.no_grad():
            self.policy.left_curriculum_state.copy_(torch.as_tensor(vector,
                dtype=self.policy.left_curriculum_state.dtype,
                device=self.policy.left_curriculum_state.device))
        if before != self.state.progress:
            observation = self.pool.set_curriculum(self.state.progress)
        result.update(completed_episodes_in_update=len(episodes), progress_before=before,
                      boundary='after committed PPO collection; no scene reset')
        return copy.deepcopy(result), observation
