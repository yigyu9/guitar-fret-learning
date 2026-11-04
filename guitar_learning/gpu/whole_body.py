"""목표 없는 전신 지지 학습: 기존 물리 안전 기준과 실제 240Hz 표본을 사용한다.

인간 Root 고정·자유 기타의 준비 자세 유지 과제다. 상태 복원은 소유 Pool의
에피소드 초기화에서만 수행하며 이 모듈은 물리 상태를 쓰지 않는다.
"""
import copy
import math

import torch

from guitar_learning.gpu.control import apply, conjugate, multiply, origin_velocity, relative_point, rotvec
from guitar_learning.gpu.environment import BACKEND_CONTRACT, FAILURE_REASONS, TensorSongEnvironment
from guitar_learning.gpu.whole_body_control import ACTION_NAMES, SCHEMA as CONTROL_SCHEMA


OBSERVATION_SCHEMA = 'guitar_learning.whole_body_observation.v1'
REWARD_SCHEMA = 'guitar_learning.whole_body_reward.v1'
STATE_FIELDS = tuple(
    [kind+'.'+str(i) for kind in ('q_offset', 'qd', 'target_error') for i in range(105)] +
    ['previous_action.'+name for name in ACTION_NAMES] +
    [body+'.'+kind+'.'+str(i) for body in ('guitar_in_pelvis', 'left_wrist_in_guitar', 'right_wrist_in_guitar')
     for kind, count in (('position', 3), ('rotation6', 6), ('velocity', 3), ('omega', 3)) for i in range(count)] +
    ['contact.'+str(i) for i in range(10)] + ['reset_delta.'+str(i) for i in range(12)] +
    ['pelvis.'+kind+'.'+str(i) for kind in ('gravity', 'velocity', 'omega') for i in range(3)] +
    ['pelvis.height'] +
    [side+'_foot_in_pelvis.'+kind+'.'+str(i) for side in ('left', 'right')
     for kind, count in (('position', 3), ('rotation6', 6), ('velocity', 3), ('omega', 3)) for i in range(count)] +
    ['combined_com.'+kind+'.'+str(i) for kind in ('position', 'velocity') for i in range(3)] +
    ['support_force.'+body+'.'+axis for body in ('chest', 'right_upper_arm', 'right_thigh', 'left_foot', 'right_foot') for axis in 'xyz'] +
    ['support_loss_s.'+str(i) for i in range(3)] + ['remaining_s'])
STATE_DIM = len(STATE_FIELDS)
STATE_SCALES = tuple([math.pi]*105 + [10.]*105 + [math.pi]*105 + [1.]*37 +
    ([.5]*3+[1.]*6+[1.]*3+[5.]*3)*3 + [1.]*10 + [.1]*3+[.35]*3+[.04]*6 +
    [1.]*3+[1.]*3+[5.]*3+[1.] + ([1.]*3+[1.]*6+[1.]*3+[5.]*3)*2 +
    [1.]*6 + [100.]*15 + [.25]*3 + [10.])
REWARD_TERMS = ('guitar_pose', 'foot_contact', 'upper_support', 'body_posture', 'action_change')


class WholeBodyEnvironment:
    """480 설계 상태 + 종료에 쓰이는 접촉 상실3·남은 시간1 = 484."""
    _tensor = TensorSongEnvironment._tensor
    _indices = TensorSongEnvironment._indices
    _safety = TensorSongEnvironment._safety
    invalidate_control = TensorSongEnvironment.invalidate_control

    def __init__(self, metadata, *, duration_s=10., device='cuda:0'):
        if (isinstance(duration_s, bool) or not isinstance(duration_s, (int, float)) or
                not math.isfinite(duration_s) or duration_s <= 0 or
                abs(duration_s*60-round(duration_s*60)) > 1e-7):
            raise ValueError('positive episode duration on the 60Hz grid required')
        self.device, self.duration_s = torch.device(device), float(duration_s)
        self.names, self.body_names = tuple(metadata['joint_names']), tuple(metadata['body_names'])
        if len(self.names) != 105 or len(set(self.names)) != 105 or len(set(self.body_names)) != len(self.body_names):
            raise ValueError('unique named native105 and bodies required')
        action = metadata['action_contract']
        if action.get('schema') != CONTROL_SCHEMA or action.get('action_order') != list(ACTION_NAMES):
            raise ValueError('actual whole_body37 control contract required')
        self._index = {name: i for i, name in enumerate(self.body_names)}
        self.com = self._tensor(metadata['body_com'])
        self.mass = self._tensor(metadata['body_mass'])
        self.reference = self._tensor(metadata['reference105'])
        if (self.com.shape != (len(self.body_names), 3) or self.mass.shape != (len(self.body_names),) or
                self.reference.shape != (105,) or not torch.isfinite(self.com).all() or
                not torch.isfinite(self.reference).all() or not torch.isfinite(self.mass).all() or (self.mass < 0).any()):
            raise ValueError('finite COM, nonnegative source mass, reference105 required')
        self.mass_indices = self._indices([n for n in self.body_names if n.startswith(('human/', 'guitar/'))])
        self.com_mass = self.mass[self.mass_indices]
        if self.com_mass.sum() <= 0:
            raise ValueError('positive human and guitar total mass required')
        self.active_joints = self._tensor([self.names.index(n) for n in ACTION_NAMES], torch.long)
        self.guitar_index, self.pelvis_index = self._index['guitar/guitar'], self._index['human/Pelvis']
        self.wrist_indices = tuple(self._index[n] for n in ('human/L_Wrist', 'human/R_Wrist'))
        self.feet_indices = self._indices(['human/L_Ankle', 'human/R_Ankle'])
        self.support_indices = self._indices(['human/Chest', 'human/R_Shoulder', 'human/R_Hip'])
        self.flag_indices = [self._indices(['human/'+n]) for n in ('Chest', 'R_Shoulder', 'R_Hip')]
        self.flag_indices += [self._indices(['human/LH:'+f+str(i) for i in (1, 2, 3)])
                              for f in ('thumb', 'index', 'middle', 'ring', 'pinky')]
        self.flag_indices += [self._indices(['human/'+s+'_'+p for p in ('Ankle', 'Toe')]) for s in ('L', 'R')]
        self.force_indices = self.flag_indices[:3]+self.flag_indices[-2:]
        self.scales = self._tensor(STATE_SCALES)
        self.initialized, self._substeps = False, None
        self.contract = dict(schema='guitar_learning.training.v1',
            observation=dict(schema=OBSERVATION_SCHEMA, dimension=STATE_DIM, fields=list(STATE_FIELDS),
                scales=list(STATE_SCALES), event_dim=0, priority_slots=0, event_capacity=0,
                mass_source='human + logical guitar source masses; chair excluded; no compound mass double count'),
            action=dict(dimension=37, names=list(ACTION_NAMES), minimum=-1., maximum=1.,
                target_contract=copy.deepcopy(action)),
            task=dict(schema='guitar_learning.whole_body_support_task.v1', duration_s=self.duration_s,
                goals='none', hands='prepared references, no hand policies', initial_pose='left_standby_v9'),
            reward=dict(schema=REWARD_SCHEMA, physics_hz=240, control_hz=60,
                rates_per_s=dict(guitar_pose=.5, foot_contact=.2, upper_support=.2, body_posture=.1, action_change=-.01),
                guitar_position_scale_m=.02, guitar_rotation_scale_rad=.15, posture_scale_rad=.20,
                cost='unchanged running physical safety rate; failure once:5+2*remaining_s',
                scope='initial support learning with held hand references; no acoustic or free-root balance claim'),
            termination=dict(guitar_displacement_m=.08, guitar_rotation_rad=.35,
                foot_displacement_m=.04, contact_loss_grace_s=.25, joint_speed_rad_s=50.,
                normal_end='finite support task completed; terminated=True', failure='existing seven physical reasons'),
            native_backend=copy.deepcopy(BACKEND_CONTRACT))

    def reset(self, indices, snapshot):
        if self._substeps is not None:
            raise RuntimeError('reset only at completed control boundary')
        self._validate_snapshot(snapshot)
        count = snapshot['q'].shape[0]
        ids = torch.as_tensor(indices, dtype=torch.long, device=self.device)
        if ids.ndim != 1 or (ids < 0).any() or (ids >= count).any() or ids.unique().numel() != ids.numel():
            raise ValueError('unique in-range reset ids required')
        if not self.initialized:
            if ids.numel() != count:
                raise ValueError('first reset must initialize every environment')
            self.N = count
            self.clock = torch.zeros(self.N, dtype=torch.long, device=self.device)
            self.previous_action = torch.zeros(self.N, 37, device=self.device)
            self.loss = torch.zeros(self.N, 3, device=self.device)
            self.finished = torch.zeros(self.N, dtype=torch.bool, device=self.device)
            self.control_invalid = torch.zeros_like(self.finished)
            self.failure = torch.zeros(self.N, len(FAILURE_REASONS), dtype=torch.bool, device=self.device)
            self.total_reward, self.total_cost = torch.zeros(self.N, device=self.device), torch.zeros(self.N, device=self.device)
            self.error_square_sum, self.error_abs_max = torch.zeros_like(self.previous_action), torch.zeros_like(self.previous_action)
            self.reward_totals = {k: torch.zeros(self.N, device=self.device) for k in REWARD_TERMS}
            self.reference_guitar = snapshot['body_state'][:, self.guitar_index, :7].clone()
            self.reference_feet = snapshot['body_state'][:, self.feet_indices, :3].clone()
            self.initialized = True
        for value in (self.clock, self.previous_action, self.loss, self.finished, self.control_invalid,
                      self.failure, self.total_reward, self.total_cost, self.error_square_sum, self.error_abs_max,
                      *self.reward_totals.values()):
            value[ids] = 0
        self.reference_guitar[ids] = snapshot['body_state'][ids, self.guitar_index, :7]
        self.reference_feet[ids] = snapshot['body_state'][ids[:, None], self.feet_indices[None], :3]
        self._snapshot(snapshot)
        return self.observation()

    def _validate_snapshot(self, snapshot):
        q = snapshot.get('q')
        if not isinstance(q, torch.Tensor) or q.ndim != 2 or q.shape[0] < 1:
            raise ValueError('nonempty native q[N,105] required')
        count = self.N if self.initialized else q.shape[0]
        for key, suffix in (('q', (105,)), ('qd', (105,)), ('target', (105,)),
                            ('body_state', (len(self.body_names), 13)), ('contact_force', (len(self.body_names), 3))):
            value = snapshot.get(key)
            if (not isinstance(value, torch.Tensor) or value.dtype != self.reference.dtype or
                    value.device != self.device or value.shape != (count,)+suffix or not torch.isfinite(value).all()):
                raise ValueError('finite aligned native snapshot required: '+key)
        if (torch.linalg.vector_norm(snapshot['body_state'][..., 3:7], dim=-1)-1).abs().amax() > .01:
            raise ValueError('unit body quaternions required')

    def _snapshot(self, snapshot):
        self._validate_snapshot(snapshot)
        self.snapshot, self.body = snapshot, snapshot['body_state']
        self.guitar_body = self.body[:, self.guitar_index]
        self.guitar_q = self.guitar_body[:, 3:7]
        loaded = torch.linalg.vector_norm(snapshot['contact_force'], dim=-1) >= .01
        self.flags = torch.stack([loaded[:, ids].any(-1) for ids in self.flag_indices], -1)
        support = self.body[:, self.support_indices, :3]-self.guitar_body[:, None, :3]
        self.flags[:, :3] &= torch.linalg.vector_norm(support, dim=-1) < .5

    def _relative_state(self, index, reference_index):
        body, frame = self.body[:, index], self.body[:, reference_index]
        p, v = relative_point(body[:, :3], origin_velocity(body, self.com[index]), frame, self.com[reference_index])
        q = multiply(conjugate(frame[:, 3:7]), body[:, 3:7])
        basis = self._tensor([[1., 0., 0.], [0., 1., 0.]])
        rotation = apply(q[:, None], basis[None]).flatten(1)
        omega = apply(conjugate(frame[:, 3:7]), body[:, 10:13]-frame[:, 10:13])
        return torch.cat((p, rotation, v, omega), -1)

    def observation(self):
        pelvis = self.body[:, self.pelvis_index]
        inverse = conjugate(pelvis[:, 3:7])
        gravity = apply(inverse, self._tensor([0., 0., -1.]))
        pv = apply(inverse, origin_velocity(pelvis, self.com[self.pelvis_index]))
        pw = apply(inverse, pelvis[:, 10:13])
        selected = self.body[:, self.mass_indices]
        world_com = selected[..., :3]+apply(selected[..., 3:7], self.com[self.mass_indices])
        weights = self.com_mass[None, :, None]/self.com_mass.sum()
        com_p, com_v = relative_point((world_com*weights).sum(1), (selected[..., 7:10]*weights).sum(1),
                                     pelvis, self.com[self.pelvis_index])
        forces = torch.stack([self.snapshot['contact_force'][:, ids].sum(1) for ids in self.force_indices], 1)
        forces = apply(inverse[:, None], forces).flatten(1)
        raw = torch.cat((self.snapshot['q']-self.reference, self.snapshot['qd'],
            self.snapshot['target']-self.snapshot['q'], self.previous_action,
            self._relative_state(self.guitar_index, self.pelvis_index),
            *(self._relative_state(i, self.guitar_index) for i in self.wrist_indices), self.flags,
            self.guitar_body[:, :3]-self.reference_guitar[:, :3],
            rotvec(multiply(conjugate(self.reference_guitar[:, 3:7]), self.guitar_q)),
            (self.body[:, self.feet_indices, :3]-self.reference_feet).flatten(1),
            gravity, pv, pw, pelvis[:, 2:3],
            *(self._relative_state(self._index['human/'+s+'_Ankle'], self.pelvis_index) for s in ('L', 'R')),
            com_p, com_v, forces, self.loss,
            (self.duration_s-self.clock.float()/240.).clamp_min(0)[:, None]), -1)
        if raw.shape != (self.N, STATE_DIM):
            raise RuntimeError('whole body observation layout mismatch')
        empty = torch.zeros(self.N, 0, dtype=torch.bool, device=self.device)
        return dict(state=(raw/self.scales).clamp(-10, 10), events=raw.new_zeros(self.N, 0, 0),
                    mask=empty, priority_events=raw.new_zeros(self.N, 0, 0), priority_mask=empty.clone())

    def begin_control(self, action):
        if not self.initialized or self._substeps is not None or self.finished.any():
            raise RuntimeError('reset finished rows before control')
        if (not isinstance(action, torch.Tensor) or action.dtype != self.reference.dtype or
                action.shape != (self.N, 37) or action.device != self.device or
                not torch.isfinite(action).all() or (action.abs() > 1).any()):
            raise ValueError('bounded finite body37 actions required')
        self.action = action.detach().clone()
        self.tick_cost = torch.zeros(self.N, device=self.device)
        self.tick_failure = torch.zeros_like(self.failure)
        self.terms = {key: torch.zeros(self.N, device=self.device) for key in REWARD_TERMS}
        self.control_invalid.zero_()
        self._substeps = 0

    def _running_safety_cost(self, rate):
        self.tick_cost += rate/240.

    def substep(self, snapshot):
        if self._substeps is None or self._substeps >= 4:
            raise RuntimeError('exactly four consecutive physics snapshots required')
        step = snapshot.get('physics_step')
        if (not isinstance(step, torch.Tensor) or step.dtype != torch.long or step.device != self.device or
                step.shape != self.clock.shape or not torch.equal(step, self.clock+1)):
            raise ValueError('consecutive per-environment physics_step required')
        self._snapshot(snapshot)
        self.clock.copy_(step)
        self._safety()
        pose = (self.guitar_delta/.02).square().sum(-1)+(self.guitar_rotation/.15).square().sum(-1)
        posture = ((self.snapshot['q'][:, self.active_joints]-self.reference[self.active_joints])/.20).square().mean(-1)
        self.terms['guitar_pose'] += .5*torch.exp(-pose)/240.
        self.terms['foot_contact'] += .2*self.flags[:, -2:].all(-1)/240.
        self.terms['upper_support'] += .2*self.flags[:, :3].any(-1)/240.
        self.terms['body_posture'] += .1*torch.exp(-posture)/240.
        error = self.snapshot['target'][:, self.active_joints]-self.snapshot['q'][:, self.active_joints]
        self.error_square_sum += error.square()
        self.error_abs_max = torch.maximum(self.error_abs_max, error.abs())
        self._substeps += 1

    def end_control(self):
        if self._substeps != 4:
            raise RuntimeError('four physics snapshots required before end_control')
        self._substeps = None
        failed = self.tick_failure.any(-1)
        for key in REWARD_TERMS[:-1]:
            self.terms[key] = torch.where(failed, 0., self.terms[key])
        self.terms['action_change'] = -.01*(self.action-self.previous_action).square().mean(-1)/60.
        remaining = (self.duration_s-self.clock.float()/240.).clamp_min(0)
        self.tick_cost += failed*(5.+2.*remaining)
        reward = sum(self.terms.values())
        self.previous_action.copy_(self.action)
        self.total_reward += reward
        self.total_cost += self.tick_cost
        self.failure |= self.tick_failure
        for key, value in self.terms.items():
            self.reward_totals[key] += value
        timeline = self.clock >= round(self.duration_s*240)
        done = failed | timeline
        self.finished |= done
        episodes = [dict(env_id=i, duration_s=float(self.clock[i])/240.,
            reward=float(self.total_reward[i]), cost=float(self.total_cost[i]),
            failed=bool(failed[i]), safe_completion=bool(timeline[i] and not failed[i]),
            failures=[name for j, name in enumerate(FAILURE_REASONS) if self.failure[i, j]],
            reward_components={k: float(v[i]) for k, v in self.reward_totals.items()},
            joint_names=list(ACTION_NAMES), tracking_rmse_rad=(self.error_square_sum[i]/self.clock[i].clamp_min(1)).sqrt().tolist(),
            tracking_max_rad=self.error_abs_max[i].tolist()) for i in done.nonzero().flatten().tolist()]
        return self.observation(), reward, self.tick_cost.clone(), done, torch.zeros_like(done), episodes
