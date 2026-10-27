"""GPU tensor song measurements with an explicit new loaded-geometry contract.

Net body forces do not identify a contact partner or witness point. This backend
therefore measures loaded source finger-mesh surface samples near finite
string/fret geometry. Its candidates are neither the old pair-feature clean
candidates nor calibrated string pressure or sound.
"""
import copy

import torch

from guitar_learning.core.control import ACTIVE_NAMES, LEFT_HAND_NAMES
from guitar_learning.core.observations import ObservationBuilder, PROXIES, EVENT_SCALES
from guitar_learning.song.left_curriculum import CurriculumState as LegacyCurriculumState
from guitar_learning.song.gpu_left_curriculum import CurriculumState, default_config
from guitar_learning.song.left_environment import LEFT_FIELDS, LEFT_SCALES
from guitar_learning.song.metrics import HISTORY_FIELDS, HISTORY_SCALES
from guitar_learning.song.task import make_task
from guitar_learning.song.wrist_guide import load_anchor_track
from guitar_learning.gpu.geometry import (apply, conjugate, multiply, origin_velocity,
    relative_point, rotvec, finger_mesh_surface_samples, surface_target_geometry)
from guitar_learning.gpu.press_surface import load_press_surface, project_press_strings
from guitar_learning.gpu.finger_reward import (FINGER_REWARD_CONTRACT, FINGER_COORDINATION_CONTRACT,
    FINGER_TARGET_CONTRACT, finger_target_indices, finger_tracking_reward,
    finger_posture_reward, source_finger_frame_contract)


CONTACT_CONTRACT = dict(schema='guitar_learning.gpu_loaded_geometry.v1',
    force_threshold_n=.01, lateral_max_m=.003, height_abs_max_m=.003,
    fret_cell_margin_m=.002, finger_proxies='source finger2/3 collision-mesh surface vertices',
    surface_sampling='support vertices in64 fixed sphere directions plus6 axes; conservative finite surface samples',
    candidate='loaded designated finger mesh surface sample in finite target string/fret cell without confirmed competing fret/assignment',
    evidence='GPU net rigid body contact force and live source-mesh surface geometry',
    limitations='no body pair, contact witness, calibrated string force, pressure, vibration or sound; finite sampling can miss surface contacts',
    compatibility='new measurement; original pair-feature clean success is not inherited')
BACKEND_CONTRACT = dict(schema='guitar_learning.gpu_tensor_song.v1',
    physics='gpu_physx', pipeline='gpu', controller='gpu_tensor_finite',
    measurement=CONTACT_CONTRACT, observation='gpu_tensor', reward='gpu_tensor',
    support_measurement=dict(schema='guitar_learning.gpu_loaded_body_support.v1',
        force_threshold_n=.01, guitar_support_origin_radius_m=.5,
        flags='loaded support bodies near guitar; loaded foot/ankle bodies',
        limitation='net forces do not certify guitar/ground contact partners'),
    control_failure=dict(reason='support_control_invalid',
        trigger='finite certified support witness has an undefined contact normal',
        fallback='last valid bounded105 efforts until this60Hz control boundary; then terminate and reset only affected rows',
        fatal='nonfinite control or uncertified support witness invalidates the whole collection'))
TERMS = ('song_clean_hold', 'song_left_success', 'song_wrong_press', 'song_missing_press',
    'song_left_approach', 'song_left_missed', 'song_right_success', 'song_right_missed',
    'song_wrong_crossing', 'song_repeat_crossing', 'song_wrist_position', 'song_left_contact',
    'song_right_progress', 'action_change', 'terminal_failure')
LEFT_TERMS = TERMS + ('song_finger_tracking', 'song_finger_coordination', 'song_finger_standby')
FAILURE_REASONS = ('guitar_displacement', 'guitar_rotation', 'foot_displacement',
                   'support_lost', 'ground_contact_lost', 'joint_speed', 'support_control_invalid')
LEFT_FAILURE_COST_RATE = 5.  # cost/s; rounded recent safe-song p99, an experimental calibration.
FINGER_BASE_NAMES = ('index', 'middle', 'ring', 'pinky')
FINGER_MOTION_CONTRACT = dict(schema='guitar_learning.gpu_left_finger_motion.v2',
    joint_names=list(LEFT_HAND_NAMES), sampling_hz=60,
    range_samples='prepared reset t0 plus every completed60Hz control endpoint; not240Hz extrema',
    tracking_error='command target minus actual q at completed60Hz endpoints; excludes t0',
    action_samples='one applied action per completed control tick; first action has no change pair',
    action_sign_flip='opposite nonzero signs in adjacent actions; zero transitions are not flips',
    limit_outward='action points outward while preceding command target is at native bound within1e-6rad; not actual joint contact or force',
    scope='diagnostic only; command target is not immediate physical motion, pressure or sound',
    base_rotation=dict(schema='guitar_learning.gpu_left_finger_base_rotation.v1',
        body_names=['human/LH:'+name+'1' for name in FINGER_BASE_NAMES],
        parent='human/LH:palm', sampling_hz=60,
        samples='completed control endpoints only; excludes reset t0; not240Hz extrema',
        actual='rotation log of inverse(palm quaternion)*finger1 quaternion in the source body frames',
        command='diagnostic zero-y reference Exp([target_1_x,0,target_1_z]); source finger1 rest frames are identity',
        local_error='rotation log of inverse(actual relative rotation)*diagnostic command rotation; xz metric is the vector norm of its x/z components',
        scope='pose diagnostics only; neither a certified native drive error/torque nor proof of an extra free axis or musical success'))


class TensorSongEnvironment:
    """Collect four snapshots per control tick without copying batch state to CPU.

    ``reset`` changes measurement state only. The owning scene restores physical
    state before calling it. Completed episode dictionaries are the only normal
    per-episode transfer to the host; all observations/rewards/costs stay tensors.
    """
    def __init__(self, metadata, *, bundle, song, hand, device='cuda:0'):
        if hand not in ('left', 'right'):
            raise ValueError('left/right tensor song hand required')
        self.device = torch.device(device)
        self.hand, self.song = hand, copy.deepcopy(song)
        self.metadata = copy.deepcopy(metadata)
        self.task = make_task(bundle, pre_roll_s=song['pre_roll_s'], tail_s=song['tail_s'])
        if any(not target.fret for target in self.task.targets):
            raise ValueError('GPU song currently requires fretted targets')
        boundaries = [value for target in self.task.targets
                      for value in (target.onset_s-self.task.lookahead_s, target.end_s+.1)]
        if any(sum(t.onset_s <= now+self.task.lookahead_s and now <= t.end_s+.1
                   for t in self.task.targets) > self.task.capacity for now in boundaries):
            raise ValueError('GPU event token capacity overflow')
        self.names = tuple(metadata['joint_names'])
        self.body_names = tuple(metadata['body_names'])
        if len(self.names) != 105 or len(set(self.body_names)) != len(self.body_names):
            raise ValueError('native105 and unique qualified body names required')
        if hand == 'left':
            self.finger_joint_indices = self._tensor([self.names.index(n) for n in LEFT_HAND_NAMES], torch.long)
            self.finger_action_indices = self._tensor([ACTIVE_NAMES.index(n) for n in LEFT_HAND_NAMES], torch.long)
            lower = self._tensor(metadata['action_contract']['action_lower_rad'])
            upper = self._tensor(metadata['action_contract']['action_upper_rad'])
            if (lower.shape != (39,) or upper.shape != (39,) or
                    not torch.isfinite(lower).all() or not torch.isfinite(upper).all() or (lower > upper).any()):
                raise ValueError('finite ordered native action bounds[39] required for left finger diagnostics')
            self.finger_lower = lower[self.finger_action_indices]
            self.finger_upper = upper[self.finger_action_indices]
        self._index = {name: index for index, name in enumerate(self.body_names)}
        if hand == 'left':
            self.finger_base_indices = self._indices(FINGER_MOTION_CONTRACT['base_rotation']['body_names'])
            self.finger_palm_index = self._index['human/LH:palm']
            self.finger_segment_indices = self._indices(['human/LH:'+name+str(joint)
                for name in FINGER_BASE_NAMES for joint in (1, 2, 3)]).reshape(4, 3)
            self.finger_base_joints = self._tensor([[self.names.index('LH:'+name+'1_'+axis)
                for axis in ('x', 'z')] for name in FINGER_BASE_NAMES], torch.long)
        self.com = self._tensor(metadata['body_com'])
        self.reference = self._tensor(metadata['reference105'])
        self.human = [name[6:] for name in self.body_names if name.startswith('human/')]
        self.guitar = [name[7:] for name in self.body_names if name.startswith('guitar/')]
        human_com = {name: self.com[self._index['human/'+name]].cpu().tolist() for name in self.human}
        guitar_com = {name: self.com[self._index['guitar/'+name]].cpu().tolist() for name in self.guitar}
        builder = ObservationBuilder(self.names, self.human, self.guitar,
            human_com, guitar_com, self.reference.cpu().numpy(), self.task)
        observation = copy.deepcopy(builder.spec)
        observation['fields'] += ['song.'+name for name in HISTORY_FIELDS]
        observation['scales'] += list(HISTORY_SCALES)
        observation['dimension'] += len(HISTORY_FIELDS)
        if hand == 'left':
            observation['fields'] += ['left_curriculum.'+name for name in LEFT_FIELDS]
            observation['scales'] += list(LEFT_SCALES)
            observation['dimension'] += len(LEFT_FIELDS)
            observation['fields'] += ['finger_posture.'+finger+'.'+joint+'.'+trig
                for finger in FINGER_BASE_NAMES for joint in ('MCP', 'PIP', 'DIP')
                for trig in ('sin', 'cos')]
            observation['fields'] += ['finger_posture.'+finger+'.'+field
                for field in ('valid', 'idle_weight') for finger in FINGER_BASE_NAMES]
            observation['scales'] += [1.]*32
            observation['dimension'] += 32
            observation['priority_slots'] = 8
            observation['finger_targets'] = copy.deepcopy(FINGER_TARGET_CONTRACT)
            observation['finger_posture'] = dict(schema='guitar_learning.left_finger_posture_observation.v1',
                angles='actual parent-child geometric MCP/PIP/DIP, same source frames as reward.finger_posture',
                encoding='finger-major MCP/PIP/DIP sin,cos24; finger-valid4; idle-weight4',
                invalid='any invalid joint projection zeros all six sin/cos values for that finger; valid0',
                role='idle weights match posture reward at current episode time; not inferred from last action')
        self.scales = self._tensor(observation['scales'])
        self.event_scales = self._tensor(EVENT_SCALES)
        if hand == 'left':
            observation['event_fields'][9:11] = ['surface_candidate_now', 'surface_wrong_now']
            observation['event_fields'][16:22] = ['surface_error_'+a for a in 'xyz'] + ['surface_relative_velocity_'+a for a in 'xyz']
            observation['event_scales'][16:22] = [.03]*3 + [.5]*3
            self.event_scales = self._tensor(observation['event_scales'])
            observation['surface_geometry'] = dict(schema='guitar_learning.left_surface_events.v2',
                error='closest designated finger2/3 mesh sample to finite source neck press-plane segment in the inward fret cell, target minus sample',
                velocity='negative physical sample velocity in the moving guitar frame, not argmin finite difference',
                flags='instantaneous candidate/wrong, not timed note achievement',
                nearest_sample_tie='lowest body/sample index')
        self.contract = dict(schema='guitar_learning.training.v1', observation=observation,
            action=dict(dimension=39, names=list(ACTIVE_NAMES), minimum=-1., maximum=1.,
                        target_contract=copy.deepcopy(metadata['action_contract'])),
            task=dict(provenance=copy.deepcopy(self.task.provenance), duration_s=self.task.duration_s,
                specialist=dict(role=hand, frozen_partner=False),
                song=copy.deepcopy(song), contact_measurement=copy.deepcopy(CONTACT_CONTRACT)),
            reward=dict(schema='guitar_learning.gpu_tensor_song_reward.v1',
                left_curriculum=default_config() if hand == 'left' else None,
                candidate_scope=CONTACT_CONTRACT['limitations'], integration_hz=240,
                safety_cost='original displacement/rotation/foot/joint thresholds; loaded-body support flags'),
            termination=dict(physics_hz=240, control_hz=60, preparation_seconds=0.,
                guitar_displacement_m=.08, guitar_rotation_rad=.35, foot_displacement_m=.04,
                contact_loss_grace_s=.25, joint_speed_rad_s=50., failure_cost=5.,
                additional_failure_reasons=['support_control_invalid']),
            native_backend=copy.deepcopy(BACKEND_CONTRACT))
        if hand == 'left':
            self.contract['diagnostics'] = dict(left_finger_motion=copy.deepcopy(FINGER_MOTION_CONTRACT))
            self.approach_gamma = float(song.get('surface_approach_gamma', .99))
            if not 0 <= self.approach_gamma <= 1:
                raise ValueError('surface approach gamma in0..1 required')
            self.contract['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v8'
            self.contract['reward']['action_change'] = dict(
                coefficient_per_s=.01, normalization_dimensions=39,
                excluded_joint_names=list(LEFT_HAND_NAMES),
                scope='LH21 including thumb excluded; original per-axis coefficient for all remaining actions')
            self.contract['reward']['surface_learning'] = dict(
                schema='guitar_learning.surface_fretting.v3', approach_gamma=self.approach_gamma,
                potential='sum over valid shared-selector tracking slot0 per finger:target_count/(present_fingers*finger_count)*exp(-press_surface_distance/.03)',
                target_selector_schema=FINGER_TARGET_CONTRACT['schema'],
                potential_distance_scale_m=.03,
                approach='gamma*Phi(actual_next_state,time)-Phi(current_state,time); true terminal Phi0; no horizon reset',
                approach_stage_weight=1., contact='0.5 once at original contact_done threshold in press..end',
                hold='2*audible clean increment/note duration; continues after achievement',
                achievement='0.5 once at original required clean threshold',
                finger_balance='positive approach/contact/hold/achievement weighted target_count/(present_fingers*target_count_for_finger)',
                penalties='original wrong/missing/missed formulas and legacy progress-based weights; LH21 action-change excluded; terminal/safety unchanged',
                observation='left_surface_events.v2,544state/24event/8finger-priority; source neck press plane and inward cell')
            self.press_surface = load_press_surface(
                [t.string for t in self.task.targets], [t.fret for t in self.task.targets])
            self.press_plane = self._tensor(self.press_surface['plane_G'])
            self.contract['observation']['surface_geometry']['press_surface'] = copy.deepcopy(self.press_surface)
            self.contract['reward']['surface_learning']['press_surface'] = copy.deepcopy(self.press_surface)
            self.contract['reward']['finger_tracking'] = copy.deepcopy(FINGER_REWARD_CONTRACT)
            self.contract['reward']['finger_posture'] = copy.deepcopy(FINGER_COORDINATION_CONTRACT)
            self.contract['reward']['finger_posture']['frame_source'] = source_finger_frame_contract()
            self.contract['termination']['failure_horizon_cost'] = dict(
                schema='guitar_learning.remaining_song_failure_cost.v1',
                rate_cost_per_s=LEFT_FAILURE_COST_RATE,
                clock='remaining whole-song time after the actual control tick; clamped at zero',
                application='once on physical failure, in addition to original running cost and failure cost5',
                interpretation='fixed-rate absorbing failure model; not measured continuation cost')
        self.M = len(self.task.targets)
        self.onset = self._tensor([t.onset_s for t in self.task.targets], torch.float64)
        self.end = self._tensor([t.end_s for t in self.task.targets], torch.float64)
        self.press = self._tensor([t.press_s for t in self.task.targets], torch.float64)
        self.string = self._tensor([t.string for t in self.task.targets], torch.long)
        self.fret = self._tensor([t.fret for t in self.task.targets], torch.long)
        self.finger = self._tensor([t.finger for t in self.task.targets], torch.long)
        self.finger_counts = [(self.finger == f).sum().item() for f in range(1, 5)]
        self.finger_weights = self._tensor([self.M/(sum(c > 0 for c in self.finger_counts)*self.finger_counts[t.finger-1]) for t in self.task.targets])
        self.direction = self._tensor([t.direction for t in self.task.targets], torch.long)
        ordered_ids = {name: index for index, name in enumerate(sorted(t.target_id for t in self.task.targets))}
        self.tie_rank = self._tensor([ordered_ids[t.target_id] for t in self.task.targets], torch.float64)
        self.required = torch.minimum(self.end-self.onset,
            torch.maximum(torch.full_like(self.onset, .05), (self.end-self.onset)*song['left_fraction']))
        self.release_required = self._tensor([not any(u.target_id != t.target_id and
            (u.string, u.fret, u.finger) == (t.string, t.fret, t.finger) and
            t.onset_s < u.onset_s <= t.end_s+1e-12 for u in self.task.targets)
            for t in self.task.targets], torch.bool)
        self.start_indices = self._indices(['guitar/G:string%d'%i for i in range(1, 7)])
        self.end_indices = self._indices(['guitar/G:string%d_end'%i for i in range(1, 7)])
        self.fret_indices = self._indices(['guitar/G:nut']+['guitar/G:fret%d'%i for i in range(1, 23)])
        self.proxy_indices = self._indices(['human/'+name for name in PROXIES])
        self.finger_indices = self._indices(['human/LH:'+finger+str(segment)
            for finger in ('thumb', 'index', 'middle', 'ring', 'pinky') for segment in (2, 3)])
        surface, surface_valid = finger_mesh_surface_samples(['LH:'+finger+str(segment)
            for finger in ('thumb', 'index', 'middle', 'ring', 'pinky') for segment in (2, 3)])
        self.surface_local = self._tensor(surface)
        self.surface_valid = self._tensor(surface_valid, torch.bool).flatten()
        self.surface_count = self.surface_local.shape[1]
        self.pad_fingers = torch.arange(5, device=self.device).repeat_interleave(2*self.surface_count)
        self.flag_indices = [self._indices(['human/'+name]) for name in ('Chest', 'R_Shoulder', 'R_Hip')]
        self.flag_indices += [self._indices(['human/LH:'+finger+str(i) for i in (1, 2, 3)])
                             for finger in ('thumb', 'index', 'middle', 'ring', 'pinky')]
        self.flag_indices += [self._indices(['human/'+side+'_'+part for part in ('Ankle', 'Toe')])
                              for side in ('L', 'R')]
        self.feet_indices = self._indices(['human/L_Ankle', 'human/R_Ankle'])
        self.guitar_index, self.pelvis_index = self._index['guitar/guitar'], self._index['human/Pelvis']
        self.wrist_index = self._index['human/L_Wrist']
        self.pick_index = self._index['human/RH:pick']
        self.progress = 0.
        track = load_anchor_track(bundle) if hand == 'left' else dict(times_s=[0., 1.], anchors=[5., 5.])
        self.anchor_times = self._tensor(track['times_s'], torch.float64)
        self.anchor_values = self._tensor(track['anchors'])
        self.initialized = False
        self._substeps = None
        self._global_step = None

    def _tensor(self, value, dtype=torch.float32):
        return torch.as_tensor(value, dtype=dtype, device=self.device).detach().clone()

    def _indices(self, names):
        return self._tensor([self._index[name] for name in names], torch.long)

    def _allocate(self, count):
        self.N = count
        self.clock = torch.zeros(count, dtype=torch.long, device=self.device)
        self.steps = torch.zeros_like(self.clock)
        self.previous_action = torch.zeros(count, 39, device=self.device)
        self.total_reward = torch.zeros(count, device=self.device)
        self.total_cost = torch.zeros_like(self.total_reward)
        self.failure_horizon_cost = torch.zeros_like(self.total_reward)
        self.loss = torch.zeros(count, 3, device=self.device)
        self.invalid = torch.zeros(count, dtype=torch.bool, device=self.device)
        self.control_invalid = torch.zeros_like(self.invalid)
        self.finished = torch.ones_like(self.invalid)
        self.failure = torch.zeros(count, len(FAILURE_REASONS), dtype=torch.bool, device=self.device)
        self.armed = torch.ones(count, 6, dtype=torch.bool, device=self.device)
        self.last_hit = torch.full((count, 6), -1000000, dtype=torch.long, device=self.device)
        self.wrong_crossings = torch.zeros_like(self.clock)
        self.repeat_crossings = torch.zeros_like(self.clock)
        self.geometric_crossings = torch.zeros_like(self.clock)
        self.strict_wrong = torch.zeros_like(self.clock)
        self.note = {}
        for name in ('clean', 'wrong', 'missing', 'held', 'dwell', 'release_s', 'reached', 'contact_time', 'error'):
            self.note[name] = torch.zeros(count, self.M, dtype=torch.float64, device=self.device)
        for name in ('left', 'right', 'coupled', 'left_missed', 'right_missed', 'match50',
                     'match100', 'strict_missed', 'released', 'ever', 'reach_done', 'contact_done'):
            self.note[name] = torch.zeros(count, self.M, dtype=torch.bool, device=self.device)
        if self.hand == 'left':
            for name in ('exposure_time', 'near_time', 'surface_min', 'geometry_time', 'loaded_target_time',
                         'body_load_time', 'higher_time', 'lower_time', 'assignment_time'):
                self.note[name] = torch.zeros(count, self.M, dtype=torch.float64, device=self.device)
            self.note['near_done'] = torch.zeros(count, self.M, dtype=torch.bool, device=self.device)
            self.episode_reward_terms = {k: torch.zeros(count, device=self.device) for k in LEFT_TERMS}
            self.reward_window = {k: torch.zeros((), dtype=torch.float64, device=self.device) for k in LEFT_TERMS}
            self.finger_motion = {key: torch.zeros(count, 21, dtype=torch.float64, device=self.device) for key in
                ('actual_min', 'actual_max', 'target_min', 'target_max', 'action_sum', 'action_abs_sum',
                 'action_positive', 'action_negative', 'action_delta_abs_sum', 'action_sign_flips',
                 'limit_outward', 'error_square_sum', 'error_abs_max')}
            self.finger_motion.update({key: torch.zeros(count, 4, dtype=torch.float64, device=self.device)
                for key in ('base_y_square_sum', 'base_y_abs_max', 'base_full_square_sum',
                            'base_full_max', 'base_xz_square_sum', 'base_xz_max')})
        self.initialized = True

    def _snapshot(self, snapshot):
        for key, suffix in (('q', (105,)), ('qd', (105,)), ('target', (105,)),
                            ('body_state', (len(self.body_names), 13)),
                            ('contact_force', (len(self.body_names), 3))):
            value = snapshot[key]
            if value.device != self.device or value.shape != (self.N,)+suffix:
                raise ValueError('GPU snapshot device/shape mismatch: '+key)
            torch._assert_async(torch.isfinite(value).all(), 'nonfinite GPU snapshot: '+key)
        self.snapshot = snapshot
        self.body = snapshot['body_state']
        self.guitar_body = self.body[:, self.guitar_index]
        self.guitar_q = self.guitar_body[:, 3:7]
        self.local_bodies = apply(conjugate(self.guitar_q[:, None]),
                                  self.body[..., :3]-self.guitar_body[:, None, :3])
        self.starts = self.local_bodies[:, self.start_indices]
        self.ends = self.local_bodies[:, self.end_indices]
        self.frets = self.local_bodies[:, self.fret_indices]
        self.pick = self.local_bodies[:, self.pick_index]
        torch._assert_async(((self.ends-self.starts)[..., 1].abs() > 1e-8).all(),
                            'finite GPU strings must span the fret direction')
        self.loaded = torch.linalg.vector_norm(snapshot['contact_force'], dim=-1) >= CONTACT_CONTRACT['force_threshold_n']
        self.flags = torch.stack([self.loaded[:, indices].any(-1) for indices in self.flag_indices], -1)
        # Support flags need both load and a live nearby guitar. A net body force
        # alone can also arise from the chair/other human bodies.
        support = self.local_bodies[:, self._indices(['human/Chest', 'human/R_Shoulder', 'human/R_Hip'])]
        self.flags[:, :3] &= torch.linalg.vector_norm(support, dim=-1) < .5
        line = self.ends[:, self.string]-self.starts[:, self.string]
        y = .5*(self.frets[:, self.fret-1, 1]+self.frets[:, self.fret, 1])
        fraction = (y-self.starts[:, self.string, 1])/line[..., 1]
        self.goals = self.starts[:, self.string]+fraction[..., None]*line
        tips = self.local_bodies[:, self._indices(['human/LH:'+name+'3'
            for name in ('index', 'middle', 'ring', 'pinky')])]
        self.delta = self.goals-tips[:, self.finger-1]
        self.candidate, self.wrong = self._contacts()
        self.guide = self._wrist_guide()

    def _contacts(self):
        bodies = self.body[:, self.finger_indices]
        world = bodies[:, :, None, :3]+apply(bodies[:, :, None, 3:7], self.surface_local[None])
        points = apply(conjugate(self.guitar_q[:, None, None]),
            world-self.guitar_body[:, None, None, :3]).flatten(1, 2)
        line = self.ends-self.starts
        fraction = (points[:, :, None, 1]-self.starts[:, None, :, 1])/line[:, None, :, 1]
        projected = self.starts[:, None]+fraction[..., None]*line[:, None]
        lateral = torch.abs(projected[..., 0]-points[:, :, None, 0])
        nearest = lateral.argmin(-1)
        best = lateral.gather(-1, nearest[..., None]).squeeze(-1)
        unique = (lateral <= best[..., None]+1e-12).sum(-1) == 1
        selected_fraction = fraction.gather(-1, nearest[..., None]).squeeze(-1)
        selected_height = (points[:, :, None, 2]-projected[..., 2]).gather(-1, nearest[..., None]).squeeze(-1)
        loaded = self.loaded[:, self.finger_indices].repeat_interleave(self.surface_count, dim=1)
        geometry = (self.surface_valid[None] & unique &
            (selected_fraction >= 0) & (selected_fraction <= 1) &
            (best <= CONTACT_CONTRACT['lateral_max_m']) &
            (selected_height.abs() <= CONTACT_CONTRACT['height_abs_max_m']))
        qualifies = geometry & loaded
        low = torch.minimum(self.frets[:, :-1, 1], self.frets[:, 1:, 1])
        high = torch.maximum(self.frets[:, :-1, 1], self.frets[:, 1:, 1])
        margin = CONTACT_CONTRACT['fret_cell_margin_m']
        y = points[..., 1]
        interior = (y[..., None] > low[:, None]+margin) & (y[..., None] < high[:, None]-margin)
        assigned = torch.where(interior.any(-1), interior.to(torch.long).argmax(-1)+1, 0)
        same_string = nearest[:, :, None] == self.string
        goal_low, goal_high = low[:, self.fret-1], high[:, self.fret-1]
        in_goal = (y[..., None] >= goal_low[:, None]-margin) & (y[..., None] <= goal_high[:, None]+margin)
        same_finger = self.pad_fingers[:, None] == self.finger
        positive = (qualifies[..., None] & same_string & in_goal & same_finger[None]).any(1)
        # An ambiguous wire can support the designated target within its margin,
        # but does not establish a confirmed different fret.
        higher = (qualifies[..., None] & same_string & (assigned[..., None] > self.fret)).any(1)
        lower = (qualifies[..., None] & same_string & (assigned[..., None] > 0) &
                 (assigned[..., None] < self.fret)).any(1)
        assignment = (qualifies[..., None] & same_string & in_goal & ~same_finger[None]).any(1)
        wrong = higher | (~positive & (lower | assignment))
        if self.hand == 'left':
            self.contact_geometry = (geometry[..., None] & same_string & in_goal & same_finger[None]).any(1)
            self.contact_loaded_target = positive
            self.contact_causes = (higher, lower, assignment)
            origin_v = origin_velocity(bodies, self.com[self.finger_indices])
            world_v = origin_v[:, :, None] + torch.cross(bodies[:, :, None, 10:13], world-bodies[:, :, None, :3], dim=-1)
            guitar_v = origin_velocity(self.guitar_body, self.com[self.guitar_index])
            relative_v = world_v-guitar_v[:, None, None]-torch.cross(
                self.guitar_body[:, None, None, 10:13], world-self.guitar_body[:, None, None, :3], dim=-1)
            velocity = apply(conjugate(self.guitar_q[:, None, None]), relative_v)
            press_starts, press_ends = project_press_strings(self.starts, self.ends, self.press_plane)
            self.surface_delta, self.surface_velocity, self.surface_distance, self.surface_sample = surface_target_geometry(
                points.reshape(self.N, 10, self.surface_count, 3), velocity,
                self.surface_valid.reshape(10, self.surface_count), press_starts, press_ends,
                goal_low, goal_high, self.string, self.finger, -margin)
            self.surface_body_loaded = loaded.gather(1, self.surface_sample)
        return positive & ~wrong, wrong

    def _wrist_guide(self):
        now = self.clock.to(torch.float64)/240.
        timestamp = now-self.song['pre_roll_s']
        upper = torch.searchsorted(self.anchor_times, timestamp).clamp(1, len(self.anchor_times)-1)
        lower = upper-1
        alpha = ((timestamp-self.anchor_times[lower])/
                 (self.anchor_times[upper]-self.anchor_times[lower])).clamp(0, 1).to(torch.float32)
        anchor = self.anchor_values[lower]+alpha*(self.anchor_values[upper]-self.anchor_values[lower])
        a = anchor.floor().to(torch.long).clamp(1, 22)
        b = (a+1).clamp_max(22)
        rows = torch.arange(self.N, device=self.device)
        y = self.frets[rows, a, 1]+(anchor-a)*(self.frets[rows, b, 1]-self.frets[rows, a, 1])
        wrist = self.local_bodies[:, self.wrist_index]
        target = self.reference_wrist.clone() if hasattr(self, 'reference_wrist') else wrist.clone()
        target[:, 1] += y-self.frets[:, 5, 1]
        delta = target-wrist
        relative = multiply(conjugate(self.guitar_q), self.body[:, self.wrist_index, 3:7])
        rotation = rotvec(multiply(conjugate(self.reference_wrist_q), relative)) if hasattr(self, 'reference_wrist_q') else torch.zeros_like(delta)
        distance, angle = torch.linalg.vector_norm(delta, dim=-1), torch.linalg.vector_norm(rotation, dim=-1)
        return dict(delta=delta, rotation=rotation, ready=(distance <= .04) & (angle <= .6),
            position=torch.exp(-(torch.relu(distance-.02)/.04)**2),
            orientation=torch.exp(-(angle/.6)**2))

    def reset(self, indices, snapshot):
        if not self.initialized:
            self._allocate(snapshot['q'].shape[0])
            self.reference_guitar = snapshot['body_state'][:, self.guitar_index, :7].clone()
            self.reference_feet = snapshot['body_state'][:, self.feet_indices, :3].clone()
        indices = torch.as_tensor(indices, dtype=torch.long, device=self.device)
        if self._substeps is not None:
            raise RuntimeError('measurement reset requires a completed control tick')
        for value in (self.clock, self.steps, self.previous_action, self.total_reward,
                      self.total_cost, self.failure_horizon_cost, self.loss, self.invalid, self.control_invalid, self.failure, self.wrong_crossings,
                      self.repeat_crossings, self.geometric_crossings, self.strict_wrong):
            value[indices] = 0
        for value in self.note.values():
            value[indices] = 0
        if self.hand == 'left':
            for value in self.episode_reward_terms.values():
                value[indices] = 0
        self.finished[indices] = False
        self.armed[indices] = True
        self.last_hit[indices] = -1000000
        self.reference_guitar[indices] = snapshot['body_state'][indices, self.guitar_index, :7]
        self.reference_feet[indices] = snapshot['body_state'][indices[:, None], self.feet_indices[None], :3]
        self._snapshot(snapshot)
        if self.hand == 'left':
            for value in self.finger_motion.values():
                value[indices] = 0
            for prefix, key in (('actual', 'q'), ('target', 'target')):
                value = snapshot[key][indices[:, None], self.finger_joint_indices[None]].double()
                self.finger_motion[prefix+'_min'][indices] = value
                self.finger_motion[prefix+'_max'][indices] = value
        wrist = self.local_bodies[:, self.wrist_index]
        rotation = multiply(conjugate(self.guitar_q), self.body[:, self.wrist_index, 3:7])
        if not hasattr(self, 'reference_wrist'):
            self.reference_wrist, self.reference_wrist_q = wrist.clone(), rotation.clone()
            self.previous_candidate = self.candidate.clone()
            self.previous_wrong = self.wrong.clone()
            self.previous_delta = self.delta.clone()
            self.previous_pick = self.pick.clone()
            self.previous_ready = self.guide['ready'].clone()
        self.reference_wrist[indices], self.reference_wrist_q[indices] = wrist[indices], rotation[indices]
        self.guide = self._wrist_guide()
        for old, current in ((self.previous_candidate, self.candidate), (self.previous_wrong, self.wrong),
                             (self.previous_delta, self.delta), (self.previous_pick, self.pick),
                             (self.previous_ready, self.guide['ready'])):
            old[indices] = current[indices]
        self.note['ever'][indices] = self.candidate[indices]
        if not hasattr(self, 'delta_velocity'):
            self.delta_velocity = torch.zeros_like(self.delta)
        self.delta_velocity[indices] = 0
        if self.hand == 'left':
            if not hasattr(self, 'previous_surface_distance'):
                self.previous_surface_distance = self.surface_distance.clone()
            self.previous_surface_distance[indices] = self.surface_distance[indices]
        return self.observation()

    def set_curriculum(self, progress):
        if isinstance(progress, bool) or not isinstance(progress, (int, float)) or not 0 <= progress <= 2:
            raise ValueError('finite left curriculum progress in0..2 required')
        self.progress = float(progress)
        return self.observation()

    def _weights(self):
        state = CurriculumState(self.finger_counts) if self.hand == 'left' else LegacyCurriculumState()
        state.progress = self.progress
        return state.weights()

    def _surface_potential(self):
        now = self.clock.to(torch.float64)/240.
        targets = finger_target_indices(now, self.onset, self.end, self.press, self.finger)
        selected = targets['indices'][..., 0].clamp_min(0)
        valid = targets['valid'][..., 0]
        distance = self.surface_distance.gather(1, selected)
        return (valid*self.finger_weights[selected]*torch.exp(-distance/.03)).sum(-1)

    def reset_reward_window(self):
        if self.hand == 'left':
            for value in self.reward_window.values():
                value.zero_()

    def reward_window_means(self, transitions):
        if self.hand != 'left':
            return {}
        values = torch.stack(list(self.reward_window.values())).cpu().tolist()
        return {key: value/transitions for key, value in zip(self.reward_window, values)}

    def begin_control(self, actions):
        if not self.initialized or self._substeps is not None or self.finished.any():
            raise RuntimeError('reset all finished environments before starting the next control tick')
        if (actions.shape != (self.N, 39) or actions.device != self.device or
                not torch.isfinite(actions).all() or (actions.abs() > 1).any()):
            raise ValueError('finite bounded device actions[N,39] required')
        inactive = actions[:, 33:] if self.hand == 'left' else actions[:, :33]
        if (inactive != 0).any():
            raise ValueError('inactive hand action must be zero residual')
        self.action = actions.detach().clone()
        self.terms = {key: torch.zeros(self.N, device=self.device) for key in TERMS}
        if self.hand == 'left':
            for key in LEFT_TERMS[len(TERMS):]:
                self.terms[key] = torch.zeros(self.N, device=self.device)
        self.tick_cost = torch.zeros(self.N, device=self.device)
        self.tick_failure = torch.zeros(self.N, len(FAILURE_REASONS), dtype=torch.bool, device=self.device)
        self.control_invalid.zero_()
        self.before_progress = self._right_potential()
        if self.hand == 'left':
            self.before_surface_potential = self._surface_potential()
            target = self.snapshot['target'][:, self.finger_joint_indices]
            action = self.action[:, self.finger_action_indices]
            self.finger_outward = ((target <= self.finger_lower+1e-6) & (action < 0) |
                                   (target >= self.finger_upper-1e-6) & (action > 0))
        self._substeps = 0

    def _record_finger_motion(self):
        """Fixed-size GPU accumulators; one sample per completed control tick."""
        stats = self.finger_motion
        q = self.snapshot['q'][:, self.finger_joint_indices].double()
        target = self.snapshot['target'][:, self.finger_joint_indices].double()
        for prefix, value in (('actual', q), ('target', target)):
            stats[prefix+'_min'].copy_(torch.minimum(stats[prefix+'_min'], value))
            stats[prefix+'_max'].copy_(torch.maximum(stats[prefix+'_max'], value))
        action = self.action[:, self.finger_action_indices].double()
        previous = self.previous_action[:, self.finger_action_indices].double()
        paired = self.steps[:, None] > 0
        stats['action_sum'] += action
        stats['action_abs_sum'] += action.abs()
        stats['action_positive'] += action > 0
        stats['action_negative'] += action < 0
        stats['action_delta_abs_sum'] += (action-previous).abs()*paired
        stats['action_sign_flips'] += (action*previous < 0) & paired
        stats['limit_outward'] += self.finger_outward
        error = target-q
        stats['error_square_sum'] += error.square()
        stats['error_abs_max'].copy_(torch.maximum(stats['error_abs_max'], error.abs()))
        relative = multiply(conjugate(self.body[:, None, self.finger_palm_index, 3:7].double()),
                            self.body[:, self.finger_base_indices, 3:7].double())
        angles = self.snapshot['target'][:, self.finger_base_joints].double()
        vector = torch.stack((angles[..., 0], torch.zeros_like(angles[..., 0]), angles[..., 1]), -1)
        size = torch.linalg.vector_norm(vector, dim=-1, keepdim=True)
        desired = torch.cat((vector*(.5*torch.sinc(size/(2*torch.pi))), torch.cos(.5*size)), -1)
        local_error = rotvec(multiply(conjugate(relative), desired))
        y = rotvec(relative)[..., 1]
        full = torch.linalg.vector_norm(local_error, dim=-1)
        xz = torch.linalg.vector_norm(local_error[..., (0, 2)], dim=-1)
        for prefix, value, maximum in (('base_y', y, 'base_y_abs_max'),
                                       ('base_full', full, 'base_full_max'),
                                       ('base_xz', xz, 'base_xz_max')):
            stats[prefix+'_square_sum'] += value.square()
            stats[maximum].copy_(torch.maximum(stats[maximum], value.abs()))

    def invalidate_control(self, mask):
        """Latch invalid support normals as row-local physical failures.

        The owner may use only its last valid bounded effort until this tick's
        boundary. This measurement method never supplies or changes torques.
        Nonfinite/uncertified controller results remain fatal in the owner.
        """
        if self._substeps is None or self._substeps >= 4:
            raise RuntimeError('control invalidation requires an active control tick')
        if mask.shape != (self.N,) or mask.dtype != torch.bool or mask.device != self.device:
            raise ValueError('aligned boolean invalid-control mask required')
        self.control_invalid |= mask
        self.tick_failure[:, -1] |= self.control_invalid

    def _right_potential(self):
        now = self.clock.to(torch.float64)/240.
        eligible = (~self.note['right'] & (now[:, None] < torch.minimum(self.end, self.onset+self.song['window_s'])) &
                    (self.onset <= now[:, None]+self.task.lookahead_s))
        rank = self.onset[None]+self.tie_rank[None]*1e-12
        selected = rank.expand(self.N, -1).masked_fill(~eligible, torch.inf).argmin(-1)
        present = eligible.any(-1)
        rows = torch.arange(self.N, device=self.device)
        s = self.starts[rows, self.string[selected]]
        line = self.ends[rows, self.string[selected]]-s
        goal = s+((-.36-s[:, 1])/line[:, 1])[:, None]*line
        normal = torch.stack((-line[:, 1], line[:, 0]), -1)
        normal = normal/torch.linalg.vector_norm(normal, dim=-1, keepdim=True)
        normal = torch.where(normal[:, :1] < 0, -normal, normal)
        goal[:, :2] -= self.direction[selected, None]*.008*normal
        goal[:, 2] -= .004
        potential = torch.exp(-(torch.linalg.vector_norm(self.pick-goal, dim=-1)/.03)**2)
        return selected, present, potential

    def _strike(self, before, now, both):
        a, b = self.previous_pick, self.pick
        line = self.ends-self.starts
        delta = b-a
        cross = lambda x, y: x[..., 0]*y[..., 1]-x[..., 1]*y[..., 0]
        denominator = cross(delta[:, None, :2], line[..., :2])
        safe = torch.where(denominator.abs() > 1e-12, denominator, torch.ones_like(denominator))
        offset = self.starts-a[:, None]
        alpha = cross(offset[..., :2], line[..., :2])/safe
        fraction = cross(offset[..., :2], delta[:, None, :2])/safe
        point = a[:, None]+alpha[..., None]*delta[:, None]
        stringpoint = self.starts+fraction[..., None]*line
        normal = torch.stack((-line[..., 1], line[..., 0]), -1)
        normal /= torch.linalg.vector_norm(normal, dim=-1, keepdim=True)
        normal = torch.where(normal[..., :1] < 0, -normal, normal)
        speed = (delta[:, None, :2]*normal).sum(-1)*240.
        depth = stringpoint[..., 2]-point[..., 2]
        waiting = ~self.armed
        valid = ((denominator.abs() > 1e-12) & (alpha > 0) & (alpha <= 1) &
            (fraction >= 0) & (fraction <= 1) & (speed.abs() >= .05) &
            (depth >= .001) & (depth <= .015) & (point[..., 1] >= -.385) &
            (point[..., 1] <= -.255) & self.armed)
        self.armed &= ~valid
        self.last_hit = torch.where(valid, self.clock[:, None], self.last_hit)
        near = (((b[:, None]-self.starts)*line).sum(-1)/(line*line).sum(-1)).clamp(0, 1)
        separation = torch.linalg.vector_norm(b[:, None]-(self.starts+near[..., None]*line), dim=-1)
        self.armed |= waiting & (self.clock[:, None]-self.last_hit >= 2) & (separation >= .003)
        order = alpha.masked_fill(~valid, torch.inf).argsort(dim=-1, stable=True)
        rows = torch.arange(self.N, device=self.device)
        for slot in range(6):
            string = order[:, slot]
            hit = valid[rows, string]
            at = before+alpha[rows, string].to(torch.float64)/240.
            direction = speed[rows, string].sign().to(torch.long)
            matching = ((self.string[None] == string[:, None]) &
                (self.direction[None] == direction[:, None]) &
                ((at[:, None]-self.onset).abs() <= self.song['window_s']+1e-12) & (at[:, None] < self.end))
            score = (at[:, None]-self.onset).abs()+self.onset[None]*1e-10+self.tie_rank[None]*1e-13
            available = matching & ~self.note['right']
            chosen = score.masked_fill(~available, torch.inf).argmin(-1)
            success = hit & available.any(-1)
            self.note['right'][rows, chosen] |= success
            self.note['coupled'][rows, chosen] |= success & both[rows, chosen]
            self.note['error'][rows, chosen] = torch.where(success, at-self.onset[chosen], self.note['error'][rows, chosen])
            repeat = hit & ~success & matching.any(-1)
            wrong = hit & ~matching.any(-1)
            self.terms['song_right_success'] += success
            self.terms['song_repeat_crossing'] -= .02*repeat
            self.terms['song_wrong_crossing'] -= .1*wrong
            self.repeat_crossings += repeat
            self.wrong_crossings += wrong
            self.geometric_crossings += hit
            matched_any = torch.zeros_like(hit)
            for tolerance, key in ((.05, 'match50'), (.1, 'match100')):
                eligible = ((self.string[None] == string[:, None]) &
                    (self.direction[None] == direction[:, None]) & both & ~self.note[key] &
                    ((at[:, None]-self.onset).abs() <= tolerance+1e-12))
                target = score.masked_fill(~eligible, torch.inf).argmin(-1)
                matched = hit & eligible.any(-1)
                self.note[key][rows, target] |= matched
                matched_any |= matched
            self.strict_wrong += hit & ~matched_any

    def substep(self, snapshot):
        if self._substeps is None or self._substeps >= 4:
            raise RuntimeError('exactly four native snapshots per control tick required')
        step = snapshot.get('physics_step')
        if isinstance(step, torch.Tensor):
            if step.shape != self.clock.shape or step.device != self.device:
                raise ValueError('per-environment native physics clock shape/device mismatch')
            torch._assert_async((step == self.clock+1).all(),
                                'consecutive actual GPU episode physics snapshots required')
        if isinstance(step, int):
            if self._global_step is not None and step != self._global_step+1:
                raise ValueError('consecutive actual GPU physics snapshots required')
            self._global_step = step
        before = self.clock.to(torch.float64)/240.
        self.clock += 1
        now = self.clock.to(torch.float64)/240.
        self._snapshot(snapshot)
        self.delta_velocity = (self.delta-self.previous_delta)*240.
        both = self.candidate & self.previous_candidate
        audible = (torch.minimum(now[:, None], self.end)-torch.maximum(before[:, None], self.onset)).clamp_min(0)
        press = (torch.minimum(now[:, None], self.end)-torch.maximum(before[:, None], self.press)).clamp_min(0)
        clean = audible*both
        wrong = audible*.5*(self.previous_wrong.to(torch.float64)+self.wrong)
        missing = audible*.5*((~self.previous_candidate & ~self.previous_wrong).to(torch.float64)+
                              (~self.candidate & ~self.wrong))
        self.note['clean'] += clean
        self.note['wrong'] += wrong
        self.note['missing'] += missing
        self.note['held'] += clean
        self.note['dwell'] = torch.where(both, self.note['dwell']+1/240., 0.)
        self.note['ever'] |= self.candidate
        released = (self.previous_candidate & ~self.candidate & (now[:, None] >= self.end) &
                    (now[:, None] <= self.end+.1) & self.note['ever'] & ~self.note['released'])
        self.note['released'] |= released
        self.note['release_s'] = torch.where(released, now[:, None], self.note['release_s'])
        achieved = ~self.note['left'] & (self.note['clean']+1e-12 >= self.required)
        self.note['left'] |= achieved
        missed = ~self.note['left'] & ~self.note['left_missed'] & (now[:, None] > self.end+1e-12)
        self.note['left_missed'] |= missed
        if self.hand == 'left':
            self.terms['song_clean_hold'] += (2*(clean/(self.end-self.onset)*self.finger_weights).sum(-1)).float()
            self.terms['song_left_success'] += (.5*(achieved*self.finger_weights).sum(-1)).float()
        else:
            self.terms['song_clean_hold'] += (2*clean.sum(-1)).float()
            self.terms['song_left_success'] += achieved.sum(-1)
        self.terms['song_wrong_press'] -= wrong.sum(-1).float()
        self.terms['song_missing_press'] -= (.5*missing.sum(-1)).float()
        self.terms['song_left_missed'] -= .5*missed.sum(-1)
        approaching = (before[:, None] <= self.onset) & (self.press-now[:, None] >= 0) & (self.press-now[:, None] <= 2)
        credit = torch.exp(-(torch.linalg.vector_norm(self.delta, dim=-1)/.03)**2)
        if self.hand != 'left':
            self.terms['song_left_approach'] += .2*(credit*approaching).sum(-1)/approaching.sum(-1).clamp_min(1)/240.
        self._strike(before, now, both)
        missed = (~self.note['right'] & ~self.note['right_missed'] &
                  (now[:, None] > torch.minimum(self.end, self.onset+self.song['window_s'])+1e-12))
        self.note['right_missed'] |= missed
        self.note['strict_missed'] |= ~self.note['match50'] & (now[:, None] > self.onset+.05+1e-12)
        self.terms['song_right_missed'] -= .5*missed.sum(-1)
        start = (self.press-2).clamp_min(0)
        reach = (torch.minimum(now[:, None], self.end)-torch.maximum(before[:, None], start)).clamp_min(0)
        self.note['reached'] += reach*(self.previous_ready & self.guide['ready'])[:, None]
        self.note['reach_done'] |= self.note['reached']+1e-12 >= torch.minimum(torch.full_like(start, .1), self.end-start)
        self.note['contact_time'] += press*both
        first = (~self.note['contact_done'] & (self.note['contact_time']+1e-12 >=
            torch.minimum(torch.full_like(self.press, .05), self.end-self.press)))
        self.note['contact_done'] |= first
        if self.hand == 'left':
            self.terms['song_left_contact'] += (.5*(first*self.finger_weights).sum(-1)).float()
            self._surface_history(before, now, press)
            tracking = finger_tracking_reward(now, self.onset, self.end, self.press, self.finger,
                self.surface_delta, self.surface_velocity, self.candidate,
                self.action[:, self.finger_action_indices])
            self.terms['song_finger_tracking'] += tracking['rate']/240.
            posture = finger_posture_reward(now, self.onset, self.end, self.press, self.finger,
                self.body[:, self.finger_palm_index, 3:7],
                self.body[:, self.finger_segment_indices, 3:7])
            self.terms['song_finger_coordination'] += posture['coordination_rate']/240.
            self.terms['song_finger_standby'] += posture['standby_rate']/240.
        else:
            self.terms['song_left_contact'] += (.5*(press*both).sum(-1)+.5*first.sum(-1)).float()
        self.terms['song_wrist_position'] += self.guide['position']*(.8+.2*self.guide['orientation'])*(reach > 0).any(-1)/240.
        self._safety()
        self.previous_candidate = self.candidate.clone()
        self.previous_wrong = self.wrong.clone()
        self.previous_delta = self.delta.clone()
        self.previous_pick = self.pick.clone()
        self.previous_ready = self.guide['ready'].clone()
        self._substeps += 1

    def _surface_history(self, before, now, press):
        start = (self.press-2).clamp_min(0)
        exposure = (torch.minimum(now[:, None], self.end)-torch.maximum(before[:, None], start)).clamp_min(0)
        near = (self.surface_distance <= .01) & (self.previous_surface_distance <= .01)
        self.note['surface_min'] = torch.where(exposure > 0,
            torch.where(self.note['exposure_time'] == 0, self.surface_distance,
                        torch.minimum(self.note['surface_min'], self.surface_distance)), self.note['surface_min'])
        self.note['exposure_time'] += exposure
        self.note['near_time'] += exposure*near
        self.note['near_done'] |= self.note['near_time']+1e-12 >= torch.minimum(torch.full_like(start, .1), self.end-start)
        for key, flag in zip(('geometry_time', 'loaded_target_time', 'body_load_time', 'higher_time', 'lower_time', 'assignment_time'),
                             (self.contact_geometry, self.contact_loaded_target, self.surface_body_loaded, *self.contact_causes)):
            self.note[key] += press*flag
        self.previous_surface_distance.copy_(self.surface_distance)

    def _safety(self):
        self.guitar_delta = self.guitar_body[:, :3]-self.reference_guitar[:, :3]
        self.guitar_rotation = rotvec(multiply(conjugate(self.reference_guitar[:, 3:7]), self.guitar_q))
        self.foot_delta = self.body[:, self.feet_indices, :3]-self.reference_feet
        present = torch.cat((self.flags[:, :3].any(-1, keepdim=True), self.flags[:, -2:]), -1)
        self.loss = torch.where(present, 0., self.loss+1/240.)
        gd = torch.linalg.vector_norm(self.guitar_delta, dim=-1)
        ga = torch.linalg.vector_norm(self.guitar_rotation, dim=-1)
        fd = torch.linalg.vector_norm(self.foot_delta, dim=-1)
        speed = self.snapshot['qd'].abs().amax(-1)
        reasons = torch.stack((gd > .08, ga > .35, fd.amax(-1) > .04,
                               self.loss[:, 0] > .25, (self.loss[:, 1:] > .25).any(-1), speed > 50.), -1)
        reasons = torch.cat((reasons, torch.zeros(self.N, 1, dtype=torch.bool, device=self.device)), -1)
        self.tick_failure |= reasons
        rate = ((gd/.02)**2+(ga/.15)**2+(fd/.02).square().mean(-1)+
                (~present[:, 0]).float()+(~present[:, 1:]).float().mean(-1))
        self.tick_cost += rate/240.

    def end_control(self):
        if self._substeps != 4:
            raise RuntimeError('four actual physics snapshots required before control completion')
        self._substeps = None
        after = self._right_potential()
        same = self.before_progress[1] & after[1] & (self.before_progress[0] == after[0])
        self.terms['song_right_progress'] = torch.where(same,
            .25*(.99*after[2]-self.before_progress[2]), 0.)
        failed = self.tick_failure.any(-1)
        self.invalid |= failed
        self.failure |= self.tick_failure
        timeline = self.clock.to(torch.float64)/240.+1e-9 >= self.task.duration_s
        if self.hand == 'left':
            after_potential = torch.where(failed | timeline, 0., self._surface_potential())
            self.terms['song_left_approach'] = self.approach_gamma*after_potential-self.before_surface_potential
        for key in TERMS[:-2]:
            self.terms[key] = torch.where(failed, self.terms[key].clamp_max(0), self.terms[key])
        if self.hand == 'left':
            for key in LEFT_TERMS[len(TERMS):]:
                self.terms[key] = torch.where(failed, 0., self.terms[key])
        action_change = self.action-self.previous_action
        if self.hand == 'left':
            action_change[:, self.finger_action_indices] = 0
        self.terms['action_change'] = -.01*action_change.square().mean(-1)/60.
        self.terms['terminal_failure'] = -2.*failed
        self.tick_cost += 5.*failed
        if self.hand == 'left':
            remaining = (self.task.duration_s-self.clock.to(torch.float64)/240.).clamp_min(0)
            extra = (LEFT_FAILURE_COST_RATE*remaining*failed).to(self.tick_cost.dtype)
            self.tick_cost += extra
            self.failure_horizon_cost += extra
        if self.hand == 'left':
            self._record_finger_motion()
        self.previous_action = self.action.clone()
        self.steps += 1
        if self.hand == 'left':
            weights = self._weights()
            groups = dict(song_clean_hold='timing', song_left_success='timing',
                song_wrong_press='contact', song_missing_press='timing', song_left_approach='approach',
                song_left_missed='timing', song_wrist_position='wrist', song_left_contact='contact',
                song_finger_tracking='approach', song_finger_coordination='approach',
                song_finger_standby='approach')
            penalty_state = LegacyCurriculumState()
            penalty_state.progress = self.progress
            penalty_weights = penalty_state.weights()
            penalties = ('song_wrong_press', 'song_missing_press', 'song_left_missed')
            components = {key: self.terms[key]*(penalty_weights if key in penalties else weights)[group]
                          for key, group in groups.items()}
            components.update(action_change=self.terms['action_change'], terminal_failure=self.terms['terminal_failure'])
            reward = sum(components.values())
            for key, value in components.items():
                self.episode_reward_terms[key] += value
                self.reward_window[key] += value.double().sum()
        else:
            reward = sum(self.terms[key] for key in ('song_right_success', 'song_right_missed',
                'song_wrong_crossing', 'song_repeat_crossing', 'song_right_progress'))
        if self.hand != 'left':
            reward = reward+self.terms['action_change']+self.terms['terminal_failure']
        self.total_reward += reward
        self.total_cost += self.tick_cost
        timeline = self.clock.to(torch.float64)/240.+1e-9 >= self.task.duration_s
        terminated = failed | timeline
        self.finished |= terminated
        completed = [self._episode(index, bool(failed[index]))
                     for index in terminated.nonzero().flatten().cpu().tolist()]
        return (self.observation(), reward, self.tick_cost.clone(), terminated,
                torch.zeros_like(terminated), completed)

    def _focus(self, prepare=False):
        now = self.clock.to(torch.float64)/240.
        start = self.press if prepare else self.onset
        current = (start <= now[:, None]) & (now[:, None] < self.end)
        upcoming = (start >= now[:, None]) & (start <= now[:, None]+2.)
        rank = self.end[None]+self.tie_rank[None]*1e-12
        current_index = rank.expand(self.N, -1).masked_fill(~current, torch.inf).argmin(-1)
        rank = start[None]+self.tie_rank[None]*1e-12
        upcoming_index = rank.expand(self.N, -1).masked_fill(~upcoming, torch.inf).argmin(-1)
        return torch.where(current.any(-1), current_index, upcoming_index), current.any(-1) | upcoming.any(-1)

    def _history(self):
        now = self.clock.to(torch.float64)/240.
        fraction = (self.note['clean']/(self.end-self.onset)).clamp_max(1)
        values = [now/self.task.duration_s, (self.task.duration_s-now).clamp_min(0)/self.task.duration_s,
            torch.full_like(now, self.M), (self.end < now[:, None]).double().mean(-1)]
        values += [self.note[key].double().mean(-1) for key in ('left', 'right', 'coupled', 'left_missed', 'right_missed')]
        values += [fraction.mean(-1), self.wrong_crossings, self.repeat_crossings,
                   torch.zeros_like(now), self.invalid, self.note['match50'].double().mean(-1),
                   self.note['match100'].double().mean(-1)]
        index, present = self._focus()
        rows = torch.arange(self.N, device=self.device)
        focus = [torch.ones_like(now), (self.onset[index] <= now) & (now < self.end[index]),
            (self.press[index] <= now) & (now < self.onset[index]), self.string[index]+1,
            self.fret[index], self.finger[index], self.direction[index],
            self.onset[index]-now, self.end[index]-now, self.candidate[rows, index], self.wrong[rows, index],
            fraction[rows, index], self.note['left'][rows, index], self.note['right'][rows, index],
            self.note['coupled'][rows, index], self.required[index]/(self.end[index]-self.onset[index])]
        return torch.cat((torch.stack(values, -1), torch.stack(focus, -1)*present[:, None]), -1).float()

    def _events(self):
        now = self.clock.to(torch.float64)/240.
        shape = (self.N, self.M)
        expand = lambda value: value.expand(shape)
        delta = self.surface_delta if self.hand == 'left' else self.delta
        velocity = self.surface_velocity if self.hand == 'left' else self.delta_velocity
        first_flag = self.candidate if self.hand == 'left' else self.note['match50']
        second_flag = self.wrong if self.hand == 'left' else self.note['match100']
        features = torch.stack((self.onset-now[:, None], self.end-now[:, None], self.press-now[:, None],
            expand(self.string+1), expand(self.fret), expand(self.finger), expand(self.direction),
            (self.onset <= now[:, None]) & (now[:, None] < self.end),
            (self.press <= now[:, None]) & (now[:, None] < self.onset), first_flag,
            second_flag, self.note['dwell'], self.note['held'],
            self.note['held']/(self.end-self.onset), self.note['released'],
            torch.where(self.note['released'], self.note['release_s']-now[:, None], 0.),
            *delta.unbind(-1), *velocity.unbind(-1),
            self.onset+.05-now[:, None], self.onset+.1-now[:, None]), -1).float()
        valid = (self.onset <= now[:, None]+self.task.lookahead_s) & (now[:, None] <= self.end+.1)
        indices = torch.arange(self.M, device=self.device).expand(self.N, -1)
        selected = indices.masked_fill(~valid, self.M).sort(-1).values[:, :self.task.capacity]
        selected_mask = selected < self.M
        gathered = features.gather(1, selected.clamp_max(self.M-1)[..., None].expand(-1, -1, 24))
        if selected.shape[1] < self.task.capacity:
            padding = self.task.capacity-selected.shape[1]
            gathered = torch.cat((gathered, torch.zeros(self.N, padding, 24, device=self.device)), 1)
            selected_mask = torch.cat((selected_mask, torch.zeros(self.N, padding, dtype=torch.bool, device=self.device)), 1)
        gathered = torch.where(selected_mask[..., None], (gathered/self.event_scales).clamp(-10, 10), 0.)
        if self.hand == 'left':
            selection = finger_target_indices(now, self.onset, self.end, self.press, self.finger)
            priority_indices = selection['indices'].flatten(1)
            priority_mask = selection['valid'].flatten(1)
            priority = features.gather(1, priority_indices.clamp_min(0)[..., None].expand(-1, -1, 24))
            priority = torch.where(priority_mask[..., None], (priority/self.event_scales).clamp(-10, 10), 0.)
            return gathered, selected_mask, priority, priority_mask
        current = valid & (self.onset <= now[:, None]) & (now[:, None] < self.end)
        deadline = valid & ~self.note['match50'] & (self.onset+.05 >= now[:, None])
        current_rank = self.end[None]+self.tie_rank[None]*1e-12
        deadline_rank = self.onset[None]+.05+self.tie_rank[None]*1e-12
        priority_indices = torch.stack((current_rank.expand(shape).masked_fill(~current, torch.inf).argmin(-1),
            deadline_rank.expand(shape).masked_fill(~deadline, torch.inf).argmin(-1)), -1)
        priority_mask = torch.stack((current.any(-1), deadline.any(-1)), -1)
        priority = features.gather(1, priority_indices[..., None].expand(-1, -1, 24))
        priority = torch.where(priority_mask[..., None], (priority/self.event_scales).clamp(-10, 10), 0.)
        return gathered, selected_mask, priority, priority_mask

    def observation(self):
        guitar, pelvis = self.guitar_body, self.body[:, self.pelvis_index]
        relative, relative_v = relative_point(guitar[:, :3], origin_velocity(guitar, self.com[self.guitar_index]),
                                               pelvis, self.com[self.pelvis_index])
        q = multiply(conjugate(pelvis[:, 3:7]), guitar[:, 3:7])
        x = apply(q, torch.tensor([1., 0., 0.], device=self.device).expand(self.N, -1))
        y = apply(q, torch.tensor([0., 1., 0.], device=self.device).expand(self.N, -1))
        omega = apply(conjugate(pelvis[:, 3:7]), guitar[:, 10:13]-pelvis[:, 10:13])
        proxies = self.body[:, self.proxy_indices]
        p, v = relative_point(proxies[..., :3], origin_velocity(proxies, self.com[self.proxy_indices]),
                              guitar[:, None], self.com[self.guitar_index])
        proxy = torch.cat((p, v), -1).flatten(1)
        gd = guitar[:, :3]-self.reference_guitar[:, :3]
        gr = rotvec(multiply(conjugate(self.reference_guitar[:, 3:7]), guitar[:, 3:7]))
        feet = self.body[:, self.feet_indices, :3]-self.reference_feet
        now = self.clock.to(torch.float64)/240.
        deadlines = (self.onset+.05-now[:, None]).masked_fill(
            self.note['match50'] | (self.onset+.05 < now[:, None]), torch.inf).amin(-1)
        deadlines = torch.where(torch.isfinite(deadlines), deadlines, 0.)
        music = torch.stack(((self.task.duration_s-now).clamp_min(0),
            self.note['match50'].sum(-1), self.note['match100'].sum(-1), torch.full_like(now, self.M),
            self.note['held'].sum(-1), self.note['released'].sum(-1), deadlines, now), -1).float()
        line = self.ends-self.starts
        normal = torch.stack((-line[..., 1], line[..., 0]), -1)
        normal = torch.where(normal[..., :1] < 0, -normal, normal)
        side = ((self.pick[:, None, :2]-self.starts[..., :2])*normal).sum(-1).sign()
        cooldown = (2-(self.clock[:, None]-self.last_hit)).clamp_min(0)
        state = [self.snapshot['q']-self.reference, self.snapshot['qd'],
            self.snapshot['target']-self.snapshot['q'], self.previous_action,
            relative, x, y, relative_v, omega, proxy, self.flags, gd, gr, feet.flatten(1),
            music, self.armed, side, cooldown, self.loss, self._history()]
        if self.hand == 'left':
            index, present = self._focus(prepare=True)
            rows = torch.arange(self.N, device=self.device)
            fraction = (self.note['contact_time'][rows, index]/torch.minimum(
                torch.full_like(self.press[index], .05), self.end[index]-self.press[index])).clamp_max(1)
            weights = self._weights()
            extra = torch.stack((fraction*present, self.note['contact_done'][rows, index]*present,
                self.note['contact_done'].float().mean(-1), torch.full_like(fraction, self.progress),
                torch.full_like(fraction, weights['contact']), torch.full_like(fraction, weights['timing'])), -1)
            state += [self.guide['delta'], self.guide['rotation'], extra]
            posture = finger_posture_reward(now, self.onset, self.end, self.press, self.finger,
                self.body[:, self.finger_palm_index, 3:7],
                self.body[:, self.finger_segment_indices, 3:7])
            valid = posture['valid'].all(-1)
            angle = posture['angles']
            encoded = torch.stack((angle.sin(), angle.cos()), -1)
            encoded = torch.where(valid[..., None, None], encoded, 0.)
            state += [encoded.flatten(1), valid.float(), posture['idle_weight']]
        state = torch.cat([value.float() for value in state], -1)
        if state.shape != (self.N, self.contract['observation']['dimension']):
            raise ValueError('tensor song observation dimension mismatch')
        events, mask, priority, priority_mask = self._events()
        return dict(state=(state/self.scales).clamp(-10, 10), events=events, mask=mask,
                    priority_events=priority, priority_mask=priority_mask)

    def _episode(self, index, failed):
        now = float(self.clock[index].item()/240.)
        left, right = int(self.note['left'][index].sum().item()), int(self.note['right'][index].sum().item())
        wrong, repeat = int(self.wrong_crossings[index].item()), int(self.repeat_crossings[index].item())
        safe = not bool(self.invalid[index])
        full = not failed and now+1e-9 >= self.task.duration_s
        success = safe and (left == self.M if self.hand == 'left' else right == self.M and wrong == repeat == 0)
        song = dict(schema='guitar_learning.gpu_loaded_geometry_song.v1', role=self.hand,
            denominator=self.M, target_count=self.M, left_success_count=left, right_success_count=right,
            coupled_hit_count=int(self.note['coupled'][index].sum().item()),
            left_missed_count=int(self.note['left_missed'][index].sum().item()),
            right_missed_count=int(self.note['right_missed'][index].sum().item()),
            wrong_crossings=wrong, repeat_crossings=repeat, completed=full,
            stage_success=bool(full and success), provisional_success=bool(success),
            safety_invalidated=not safe, task_time_s=now,
            mean_clean_audible_fraction=float((self.note['clean'][index]/(self.end-self.onset)).clamp_max(1).mean().item()),
            strict_music=dict(matched50=int(self.note['match50'][index].sum().item()),
                matched100=int(self.note['match100'][index].sum().item()),
                wrong_crossings=int(self.strict_wrong[index].item()),
                missed_strict=int(self.note['strict_missed'][index].sum().item())),
            contact_measurement=copy.deepcopy(CONTACT_CONTRACT),
            scope='new loaded-body geometric candidates; not original pair-feature clean or acoustic success')
        result = dict(worker_id=index, env_id=index, valid=True,
            reason='terminal_failure' if failed else 'timeline_complete',
            failure_reasons=[name for name, value in zip(FAILURE_REASONS, self.failure[index].cpu().tolist()) if value],
            cost=float(self.total_cost[index].item()), reward=float(self.total_reward[index].item()),
            steps=int(self.steps[index].item()), task_time_s=now, song=song)
        result['musical_quality'] = dict(schema=song['schema'], role=self.hand,
            stage_success=song['stage_success'], provisional_success=song['provisional_success'], song=copy.deepcopy(song))
        if self.hand == 'left':
            extra = float(self.failure_horizon_cost[index].item())
            result['cost_components'] = dict(original_physics_and_terminal=result['cost']-extra,
                remaining_song_failure=extra, failure_rate_cost_per_s=LEFT_FAILURE_COST_RATE)
            result['left_curriculum'] = dict(schema=default_config()['schema'], progress=self.progress,
                weights=self._weights(), full_safe=bool(full and safe),
                reach_fraction=float(self.note['reach_done'][index].float().mean().item()),
                contact_fraction=float(self.note['contact_done'][index].float().mean().item()),
                finger_metrics=self._finger_metrics(index))
            result['left_note_ledger'] = dict(schema='guitar_learning.surface_note_ledger.v2',
                target_ids=[t.target_id for t in self.task.targets],
                values={key: self.note[key][index].cpu().tolist() for key in
                    ('left', 'near_done', 'contact_done', 'clean', 'wrong', 'missing', 'contact_time',
                     'exposure_time', 'near_time', 'surface_min', 'geometry_time', 'loaded_target_time',
                     'body_load_time', 'higher_time', 'lower_time', 'assignment_time')},
                required_clean_s=self.required.cpu().tolist(),
                scope='same order as task schedule; surface_min/near10mm use source neck press plane and inward cell; geometry/load/contact success still use original virtual strings; body_load_time is load on nearest press-surface sample body; cause times may overlap; surface_min=0 when exposure_time=0; no contact pair, pressure or sound')
            values = torch.stack(list(v[index] for v in self.episode_reward_terms.values())).cpu().tolist()
            result['reward_components'] = dict(zip(self.episode_reward_terms, values))
            result['left_finger_motion'] = self._finger_motion_episode(index)
        return result

    def _finger_motion_episode(self, index):
        ticks = int(self.steps[index].item())
        stats = {key: value[index] for key, value in self.finger_motion.items()}
        count, pairs = max(ticks, 1), max(ticks-1, 1)
        values = dict(actual_min_rad=stats['actual_min'], actual_max_rad=stats['actual_max'],
            actual_range_rad=stats['actual_max']-stats['actual_min'],
            target_min_rad=stats['target_min'], target_max_rad=stats['target_max'],
            target_range_rad=stats['target_max']-stats['target_min'],
            action_mean=stats['action_sum']/count, action_mean_abs=stats['action_abs_sum']/count,
            action_positive_fraction=stats['action_positive']/count,
            action_negative_fraction=stats['action_negative']/count,
            action_zero_fraction=(ticks-stats['action_positive']-stats['action_negative'])/count,
            action_mean_abs_change=stats['action_delta_abs_sum']/pairs,
            action_opposite_sign_fraction=stats['action_sign_flips']/pairs,
            limit_outward_command_fraction=stats['limit_outward']/count,
            tracking_error_rms_rad=torch.sqrt(stats['error_square_sum']/count),
            tracking_error_max_abs_rad=stats['error_abs_max'])
        rows = torch.stack(list(values.values())).cpu().tolist()
        base_values = dict(palm_relative_rotvec_y_rms_rad=torch.sqrt(stats['base_y_square_sum']/count),
            palm_relative_rotvec_y_max_abs_rad=stats['base_y_abs_max'],
            zero_y_command_rotation_error_rms_rad=torch.sqrt(stats['base_full_square_sum']/count),
            zero_y_command_rotation_error_max_rad=stats['base_full_max'],
            zero_y_command_local_xz_error_rms_rad=torch.sqrt(stats['base_xz_square_sum']/count),
            zero_y_command_local_xz_error_max_rad=stats['base_xz_max'])
        base_rows = torch.stack(list(base_values.values())).cpu().tolist()
        return dict(schema=FINGER_MOTION_CONTRACT['schema'], joint_names=list(LEFT_HAND_NAMES),
            sampling_hz=60, range_samples=ticks+1, endpoint_samples=ticks,
            action_samples=ticks, action_change_pairs=max(ticks-1, 0),
            values=dict(zip(values, rows)), scope=copy.deepcopy(FINGER_MOTION_CONTRACT),
            base_rotation=dict(schema=FINGER_MOTION_CONTRACT['base_rotation']['schema'],
                body_names=list(FINGER_MOTION_CONTRACT['base_rotation']['body_names']),
                sampling_hz=60, endpoint_samples=ticks, values=dict(zip(base_values, base_rows)),
                scope=copy.deepcopy(FINGER_MOTION_CONTRACT['base_rotation'])))

    def _finger_metrics(self, index):
        metrics = []
        for finger, count in enumerate(self.finger_counts, 1):
            mask = self.finger == finger
            row = dict(target_count=count)
            for name, key in (('near_fraction', 'near_done'), ('contact_fraction', 'contact_done'), ('success_fraction', 'left')):
                row[name] = float(self.note[key][index, mask].float().mean().item()) if count else 0.
            row['clean_fraction'] = float((self.note['clean'][index, mask]/(self.end-self.onset)[mask]).clamp_max(1).mean().item()) if count else 0.
            metrics.append(row)
        return metrics
