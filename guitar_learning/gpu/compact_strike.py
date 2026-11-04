"""Current free-guitar right27 observation and event-based strike environment.

Only native support/safety measurements are shared with the song environment;
its fretted-note task constructor and independent-note success ledger are not used.
No physical state is written by this class.
"""
import copy
import math

import torch

from guitar_learning.gpu.control import apply, conjugate, multiply, origin_velocity, relative_point, rotvec
from guitar_learning.gpu.environment import BACKEND_CONTRACT, FAILURE_REASONS, TensorSongEnvironment
from guitar_learning.gpu.strike_events import StrikeLedger, STRIKE_LEDGER_CONTRACT
from guitar_learning.gpu.strike_reward import compute_s3_reward, STRIKE_REWARD_CONTRACT
from guitar_learning.song.strike_task import load_strike_task
from guitar_learning.tool.experiments.right27.control import ACTION_NAMES, SCHEMA as CONTROL_SCHEMA


OBSERVATION_SCHEMA = 'guitar_learning.compact_strike_observation.v1'
STATE_FIELDS = tuple(
    [kind+'.'+str(i) for kind in ('joint_angle', 'joint_speed', 'target_error') for i in range(105)] +
    ['previous_action.'+n for n in ACTION_NAMES[12:]] +
    [body+'.'+kind+'.'+str(i) for body in ('guitar_in_pelvis', 'wrist_in_guitar', 'pick_in_guitar')
     for kind, count in (('position', 3), ('rotation6', 6), ('velocity', 3), ('omega', 3)) for i in range(count)] +
    ['contact.'+str(i) for i in range(10)] + ['reset_delta.'+str(i) for i in range(12)] +
    ['string.'+str(i)+'.'+kind for i in range(6) for kind in ('armed', 'signed_distance', 'cooldown_s')] +
    ['ready', 'ready_streak_s', 'recovered', 'recovery_streak_s'] +
    ['pelvis.'+kind+'.'+str(i) for kind in ('gravity', 'velocity', 'omega') for i in range(3)] +
    ['support_loss_s.'+str(i) for i in range(3)] +
    ['remaining_s', 'event_fraction', 'complete_count', 'clean_count', 'missed_count', 'wrong_count', 'unprepared_count'])
STATE_DIM = len(STATE_FIELDS)
BASE_GOAL_FIELDS = (
    'next_string', 'direction', 'onset_delta_s', 'deadline_delta_s',
    'target_delta_x', 'target_delta_y', 'target_delta_z', 'pick_vx', 'pick_vy', 'pick_vz',
    'signed_distance', 'depth_error', 'normal_speed', 'armed', 'clean_complete', 'geometry_valid')
GOAL_FIELDS = BASE_GOAL_FIELDS + ('is_strum', 'sweep_duration_s') + tuple(
    kind+'.'+str(s) for kind in ('traversal', 'audible', 'rank', 'offset_s', 'accepted', 'timing_error_s')
    for s in range(6)) + (
    'next_rank', 'ready', 'ready_streak_s', 'wrong', 'resolved', 'complete',
    'recovery_streak_s', 'recovery_best', 'recovered', 'recovery_required_s', 'handoff',
    'progress', 'unprepared', 'missed', 'phase',
    'clearance_required', 'rearm_required', 'recovery_fresh', 'terminal_best') + tuple('recovery_path.'+str(s) for s in range(6))
GOAL_DIM = len(GOAL_FIELDS)
STATE_SCALES = tuple([math.pi]*105 + [10.]*105 + [math.pi]*105 + [1.]*27 +
    ([.5]*3+[1.]*6+[1.]*3+[5.]*3)*3 + [1.]*10 + [.1]*3+[.35]*3+[.04]*6 +
    [1., .03, 2./240.]*6 + [1., .1, 1., .2] + [1.]*3+[1.]*3+[5.]*3 +
    [.25]*3 + [10., 1., 10., 10., 10., 10., 10.])
GOAL_SCALES = tuple([5., 1., 2., 2.] + [.03]*3+[.5]*3 + [.03, .015, .5, 1., 1., 1.] +
    [1., .1] + [1.]*12+[6.]*6+[.1]*6+[1.]*6+[.05]*6 +
    [6., 1., .1, 1., 1., 1., .2, 1., 1., .2, 1., 1., 1., 1., 2.] + [1.]*10)


class CompactStrikeEnvironment:
    """60Hz decisions, four consecutive actual 240Hz snapshots per decision."""
    _tensor = TensorSongEnvironment._tensor
    _indices = TensorSongEnvironment._indices
    _safety = TensorSongEnvironment._safety
    invalidate_control = TensorSongEnvironment.invalidate_control

    def __init__(self, metadata, *, bundle, song, hand='right', device='cuda:0'):
        if hand != 'right':
            raise ValueError('compact strike owns right27 only')
        self.device, self.hand, self.song = torch.device(device), hand, copy.deepcopy(song)
        self.task = load_strike_task(bundle, pre_roll_s=song['pre_roll_s'], tail_s=song['tail_s'])
        self.names, self.body_names = tuple(metadata['joint_names']), tuple(metadata['body_names'])
        if len(self.names) != 105 or len(set(self.body_names)) != len(self.body_names):
            raise ValueError('native105 and unique qualified bodies required')
        self._index = {n: i for i, n in enumerate(self.body_names)}
        self.com, self.reference = self._tensor(metadata['body_com']), self._tensor(metadata['reference105'])
        self.guitar_index = self._index['guitar/guitar']
        self.pelvis_index = self._index['human/Pelvis']
        self.wrist_index = self._index['human/R_Wrist']
        self.pick_index = self._index['human/RH:pick']
        self.start_indices = self._indices(['guitar/G:string%d'%i for i in range(1, 7)])
        self.end_indices = self._indices(['guitar/G:string%d_end'%i for i in range(1, 7)])
        self.feet_indices = self._indices(['human/L_Ankle', 'human/R_Ankle'])
        self.flag_indices = [self._indices(['human/'+n]) for n in ('Chest', 'R_Shoulder', 'R_Hip')]
        self.flag_indices += [self._indices(['human/LH:'+f+str(i) for i in (1, 2, 3)])
                              for f in ('thumb', 'index', 'middle', 'ring', 'pinky')]
        self.flag_indices += [self._indices(['human/'+s+'_'+p for p in ('Ankle', 'Toe')]) for s in ('L', 'R')]
        self.active_joints = self._tensor([self.names.index(n) for n in ACTION_NAMES[12:]], torch.long)
        self.grip_joints = self.active_joints[:21]
        self.pinch = self._tensor([i for i, n in enumerate(ACTION_NAMES[12:33])
                                  if 'thumb' in n.lower() or 'index' in n.lower()], torch.long)
        self.free = self._tensor([i for i in range(21) if i not in self.pinch.tolist()], torch.long)
        self.scales, self.goal_scales = self._tensor(STATE_SCALES), self._tensor(GOAL_SCALES)
        self.M = len(self.task.events)
        self.onsets = self._tensor([e.onset_s for e in self.task.events], torch.float64)
        self.first_times = self._tensor([e.crossing_times_s[0] for e in self.task.events], torch.float64)
        self.deadlines = self._tensor([e.deadline_s for e in self.task.events], torch.float64)
        self.directions = self._tensor([e.direction for e in self.task.events])
        self.first_strings = self._tensor([e.traversal_strings[0] for e in self.task.events], torch.long)
        self.traversal = torch.zeros(self.M, 6, dtype=torch.bool, device=self.device)
        self.audible = torch.zeros_like(self.traversal)
        self.ranks = torch.zeros(self.M, 6, device=self.device)
        self.offsets = torch.zeros_like(self.ranks)
        self.event_static = self._tensor([[float(e.gesture == 'strum'), e.sweep_duration_s] for e in self.task.events])
        for i, event in enumerate(self.task.events):
            self.traversal[i, list(event.traversal_strings)] = True
            self.audible[i, list(event.audible_strings)] = True
            self.ranks[i, list(event.traversal_strings)] = torch.arange(1, len(event.traversal_strings)+1, device=self.device).float()
            self.offsets[i, list(event.traversal_strings)] = self._tensor(event.traversal_offsets_s)
        self.initialized, self._substeps, self.action_bounds = False, None, None
        self.contract = dict(schema='guitar_learning.training.v1',
            observation=dict(schema=OBSERVATION_SCHEMA, dimension=STATE_DIM, fields=list(STATE_FIELDS),
                scales=list(STATE_SCALES), event_dim=GOAL_DIM, event_fields=list(GOAL_FIELDS),
                event_scales=list(GOAL_SCALES), goal_fields=list(GOAL_FIELDS), goal_scales=list(GOAL_SCALES),
                priority_slots=2, event_capacity=0, slots=['current_event_including_recovery', 'next_event']),
            compact_strike=dict(schema=OBSERVATION_SCHEMA),
            action=dict(dimension=39, names=list(ACTION_NAMES), minimum=-1., maximum=1.,
                active_indices=list(range(12, 39)), inactive_indices=list(range(12)),
                target_contract=copy.deepcopy(metadata['action_contract'])),
            task=dict(provenance=copy.deepcopy(self.task.provenance), duration_s=self.task.duration_s,
                specialist=dict(role='right', frozen_partner=False), song=copy.deepcopy(song), event_count=self.M),
            reward=dict(schema='guitar_learning.compact_strike_s3.v1', control_hz=60, measurement_hz=240,
                legacy_s3=copy.deepcopy(STRIKE_REWARD_CONTRACT), event_ledger=copy.deepcopy(STRIKE_LEDGER_CONTRACT),
                stage='fixed S3; no archived curriculum or action constraints',
                grip_reference='current prepared right21 joint angles, thumb/index pinch; geometry proxy only',
                preparation='first traversal point at y=-.320m,8mm below string,8mm on approach side; initial distance<=10mm and grip>=0.75 for0.1s; acquired readiness persists for this episode, not a fresh0.1s gate per event',
                safety_cost='unchanged current free-guitar running safety cost and failure cost5; separate cost critic'),
            termination=dict(physics_hz=240, control_hz=60, preparation_seconds=0.,
                guitar_displacement_m=.08, guitar_rotation_rad=.35, foot_displacement_m=.04,
                contact_loss_grace_s=.25, joint_speed_rad_s=50., failure_cost=5.),
            native_backend=copy.deepcopy(BACKEND_CONTRACT),
            measurement=dict(schema='guitar_learning.compact_strike_geometry.v1',
                native_crossing='finite XY segment; speed>=.05m/s; depth1..15mm; y=-.385..-.255m',
                rearm='unchanged:2 actual240Hz steps and finite-string separation>=3mm',
                blocked_attempt='same geometric passage during native rearm wait is an event error; never an accepted crossing',
                scope='point-marker crossing and event order; no pick/string contact-force, mute, vibration or acoustic certification'))
        self.contract['native_backend']['measurement'] = copy.deepcopy(self.contract['measurement'])
        if metadata['action_contract'].get('schema') == CONTROL_SCHEMA:
            self.bind_action_contract(metadata['action_contract'])

    def bind_action_contract(self, contract):
        if contract.get('schema') != CONTROL_SCHEMA or contract.get('action_order') != list(ACTION_NAMES):
            raise ValueError('actual unchanged right27 controller contract required')
        low, high = self._tensor(contract['action_lower_rad']), self._tensor(contract['action_upper_rad'])
        if low.shape != (39,) or high.shape != (39,) or not torch.isfinite(low+high).all() or (low >= high).any():
            raise ValueError('finite ordered right27 bounds required')
        self.action_bounds = (low[12:], high[12:])
        self.contract['action']['target_contract'] = copy.deepcopy(contract)

    def _allocate(self, count):
        self.N = count
        self.ledger = StrikeLedger(count, self.task.events, self.device)
        self.clock = torch.zeros(count, dtype=torch.long, device=self.device)
        self.steps = torch.zeros_like(self.clock)
        self.previous_action = torch.zeros(count, 39, device=self.device)
        self.loss = torch.zeros(count, 3, device=self.device)
        self.total_reward, self.total_cost = torch.zeros(count, device=self.device), torch.zeros(count, device=self.device)
        self.finished = torch.zeros(count, dtype=torch.bool, device=self.device)
        self.control_invalid = torch.zeros_like(self.finished)
        self.failure = torch.zeros(count, len(FAILURE_REASONS), dtype=torch.bool, device=self.device)
        self.armed = torch.ones(count, 6, dtype=torch.bool, device=self.device)
        self.last_hit = torch.full((count, 6), -1000000, dtype=torch.long, device=self.device)
        self.blocked_crossings = torch.zeros_like(self.clock)
        self.geometric_crossings = torch.zeros_like(self.clock)
        self.error_square_sum = torch.zeros(count, 27, device=self.device)
        self.error_abs_max = torch.zeros_like(self.error_square_sum)
        self.reward_window, self.episode_reward_terms = {}, {}
        self.initialized = True

    def reset(self, indices, snapshot):
        if self._substeps is not None:
            raise RuntimeError('reset only at completed control boundary')
        if not self.initialized:
            self._allocate(snapshot['q'].shape[0])
            self.reference_guitar = snapshot['body_state'][:, self.guitar_index, :7].clone()
            self.reference_feet = snapshot['body_state'][:, self.feet_indices, :3].clone()
        ids = torch.as_tensor(indices, dtype=torch.long, device=self.device)
        self.ledger.reset(ids)
        for value in (self.clock, self.steps, self.previous_action, self.loss, self.total_reward,
                      self.total_cost, self.finished, self.control_invalid, self.failure,
                      self.blocked_crossings, self.geometric_crossings, self.error_square_sum, self.error_abs_max):
            value[ids] = 0
        for value in self.episode_reward_terms.values():
            value[ids] = 0
        self.armed[ids], self.last_hit[ids] = True, -1000000
        self.reference_guitar[ids] = snapshot['body_state'][ids, self.guitar_index, :7]
        self.reference_feet[ids] = snapshot['body_state'][ids[:, None], self.feet_indices[None], :3]
        self._snapshot(snapshot)
        if not hasattr(self, 'previous_pick'):
            self.previous_pick = self.pick.clone()
        self.previous_pick[ids] = self.pick[ids]
        self.ledger.advance(self._local_time())
        return self.observation()

    def _local_time(self):
        return self.clock.double()/240.

    def _snapshot(self, snapshot):
        for key, suffix in (('q', (105,)), ('qd', (105,)), ('target', (105,)),
                            ('body_state', (len(self.body_names), 13)), ('contact_force', (len(self.body_names), 3))):
            value = snapshot[key]
            if value.device != self.device or value.shape != (self.N,)+suffix:
                raise ValueError('native snapshot device/shape mismatch: '+key)
            torch._assert_async(torch.isfinite(value).all(), 'nonfinite native snapshot: '+key)
        self.snapshot, self.body = snapshot, snapshot['body_state']
        self.guitar_body = self.body[:, self.guitar_index]
        self.guitar_q = self.guitar_body[:, 3:7]
        self.local_bodies = apply(conjugate(self.guitar_q[:, None]), self.body[..., :3]-self.guitar_body[:, None, :3])
        self.pick = self.local_bodies[:, self.pick_index]
        self.starts, self.ends = self.local_bodies[:, self.start_indices], self.local_bodies[:, self.end_indices]
        self.line = self.ends-self.starts
        torch._assert_async((self.line[..., 1].abs() > 1e-8).all(), 'finite strings must span y')
        normal = torch.stack((-self.line[..., 1], self.line[..., 0]), -1)
        normal = normal/torch.linalg.vector_norm(normal, dim=-1, keepdim=True)
        self.normal = torch.where(normal[..., :1] < 0, -normal, normal)
        self.signed = ((self.pick[:, None, :2]-self.starts[..., :2])*self.normal).sum(-1)
        u = (((self.pick[:, None]-self.starts)*self.line).sum(-1)/self.line.square().sum(-1)).clamp(0, 1)
        self.separation = torch.linalg.vector_norm(self.pick[:, None]-self.starts-u[..., None]*self.line, dim=-1)
        loaded = torch.linalg.vector_norm(snapshot['contact_force'], dim=-1) >= .01
        self.flags = torch.stack([loaded[:, ids].any(-1) for ids in self.flag_indices], -1)
        support = self.local_bodies[:, self._indices(['human/Chest', 'human/R_Shoulder', 'human/R_Hip'])]
        self.flags[:, :3] &= torch.linalg.vector_norm(support, dim=-1) < .5
        pick = self.body[:, self.pick_index]
        _, self.pick_velocity = relative_point(pick[:, :3], origin_velocity(pick, self.com[self.pick_index]),
                                               self.guitar_body, self.com[self.guitar_index])

    def _running_safety_cost(self, rate):
        self.tick_cost += rate/240.

    def _geometry_target(self, event, string, preparation=False):
        rows = torch.arange(self.N, device=self.device)
        start, line = self.starts[rows, string], self.line[rows, string]
        target = start+((-.320-start[:, 1])/line[:, 1])[:, None]*line
        target[:, 2] -= .008
        if preparation:
            target[:, :2] -= self.directions[event, None]*.008*self.normal[rows, string]
        return target

    def _grip_quality(self):
        error = self.snapshot['q'][:, self.grip_joints]-self.reference[self.grip_joints]
        pinch = error[:, self.pinch].square().mean(-1)
        free = error[:, self.free].square().mean(-1)
        return .65*torch.exp(-pinch/math.radians(20.)**2)+.35*torch.exp(-free/math.radians(25.)**2)

    def _preparation(self):
        event = self.ledger.active.clamp(0, self.M-1)
        target = self._geometry_target(event, self.first_strings[event], preparation=True)
        distance = torch.linalg.vector_norm(target-self.pick, dim=-1)
        quality = .4*torch.exp(-(distance/.120).square())+.6*torch.exp(-(distance/.025).square())
        return distance, quality, torch.exp(-distance/.010)

    def _phase_target(self, event, string, current):
        rows = torch.arange(self.N, device=self.device)
        ready = self.ledger.history['ready'][rows, event]
        advance = current & ready & (self._local_time() >= self.first_times[event]-.07)
        first = self.first_strings[event]
        preparation = self._geometry_target(event, first, preparation=True)
        crossing = self._geometry_target(event, string)
        crossing[:, :2] += self.directions[event, None]*.008*self.normal[rows, string]
        return torch.where(advance[:, None], crossing, preparation), advance

    def _potential(self):
        event = self.ledger.active
        string = self.ledger.next_string.clamp_min(0)
        target, advancing = self._phase_target(event, string, ~self.ledger.done)
        key = event*16+advancing.long()*8+torch.where(advancing, string, 0)
        return torch.exp(-torch.linalg.vector_norm(target-self.pick, dim=-1)/.010), key

    def begin_control(self, actions):
        if not self.initialized or self._substeps is not None or self.finished.any():
            raise RuntimeError('reset finished rows before another control tick')
        if self.action_bounds is None:
            raise RuntimeError('bind actual right27 controller before stepping')
        if (actions.shape != (self.N, 39) or actions.device != self.device or not torch.isfinite(actions).all()
                or (actions.abs() > 1).any() or (actions[:, :12] != 0).any()):
            raise ValueError('finite right27 actions[N,39] with first12 zero required')
        self.action = actions.detach().clone()
        self.ledger.begin_tick()
        self.tick_cost = torch.zeros(self.N, device=self.device)
        self.tick_failure = torch.zeros_like(self.failure)
        self.control_invalid.zero_()
        self.before_event = self.ledger.active.clone()
        self.before_phi, self.before_potential_key = self._potential()
        self._substeps = 0

    def _crossings(self, before):
        delta = self.pick-self.previous_pick
        cross = lambda a, b: a[..., 0]*b[..., 1]-a[..., 1]*b[..., 0]
        denominator = cross(delta[:, None, :2], self.line[..., :2])
        safe = torch.where(denominator.abs() > 1e-12, denominator, torch.ones_like(denominator))
        offset = self.starts-self.previous_pick[:, None]
        alpha = cross(offset[..., :2], self.line[..., :2])/safe
        fraction = cross(offset[..., :2], delta[:, None, :2])/safe
        point = self.previous_pick[:, None]+alpha[..., None]*delta[:, None]
        stringpoint = self.starts+fraction[..., None]*self.line
        speed = (delta[:, None, :2]*self.normal).sum(-1)*240.
        depth = stringpoint[..., 2]-point[..., 2]
        eligible = ((denominator.abs() > 1e-12) & (alpha > 0) & (alpha <= 1) &
            (fraction >= 0) & (fraction <= 1) & (speed.abs() >= .05) &
            (depth >= .001) & (depth <= .015) & (point[..., 1] >= -.385) & (point[..., 1] <= -.255))
        waiting, valid = ~self.armed, eligible & self.armed
        self.blocked_crossings += (eligible & waiting).sum(-1)
        self.geometric_crossings += valid.sum(-1)
        self.armed &= ~valid
        self.last_hit = torch.where(valid, self.clock[:, None], self.last_hit)
        self.armed |= waiting & (self.clock[:, None]-self.last_hit >= 2) & (self.separation >= .003)
        order = alpha.masked_fill(~eligible, torch.inf).argsort(dim=-1, stable=True)
        rows = torch.arange(self.N, device=self.device)
        for slot in range(6):
            string = order[:, slot]
            blocked = rows[(eligible & waiting)[rows, string]]
            if blocked.numel():
                self.ledger.record_wrong(blocked, torch.ones(blocked.shape, device=self.device))
            ids = rows[valid[rows, string]]
            if ids.numel():
                s = string[ids]
                at = before[ids]+alpha[ids, s].double()/240.
                zone = torch.exp(-((point[ids, s, 1]+.320)/.065).square())
                self.ledger.cross(ids, s, speed[ids, s].sign().long(), at, zone)

    def substep(self, snapshot):
        if self._substeps is None or self._substeps >= 4:
            raise RuntimeError('exactly four actual native snapshots per control tick required')
        step = snapshot.get('physics_step')
        if not isinstance(step, torch.Tensor) or step.dtype != torch.long or step.device != self.device or step.shape != self.clock.shape:
            raise ValueError('per-environment native physics_step long tensor required')
        torch._assert_async((step == self.clock+1).all(), 'consecutive native physics snapshots required')
        before = self._local_time()
        self.clock.copy_(step)
        self._snapshot(snapshot)
        # 교차로 원장을 완료시키기 전에 같은 실제 끝점의 마지막 현→exit 진행을 기록한다.
        rows = torch.arange(self.N, device=self.device)
        event = self.ledger.active
        final_string = self.ranks[event].argmax(-1)
        final_signed = self.signed[rows, final_string]*self.directions[event]
        self.ledger.add_terminal_progress((final_signed/.008).clamp(0, 1))
        self._crossings(before)
        event = self.ledger.active.clamp(0, self.M-1)
        path = self.traversal[event]
        separation = self.separation.masked_fill(~path, torch.inf).amin(-1)
        recovery_path = self.ledger.path_mask
        clearance = self.separation.masked_fill(~recovery_path, torch.inf).amin(-1)
        clearance = torch.where(recovery_path.any(-1), clearance, torch.ones_like(clearance))
        armed = (self.armed | ~path).all(-1)
        self.ledger.update_recovery(clearance, separation >= .003, armed, 1./240.)
        self.ledger.advance(self._local_time())
        self._safety()
        error = snapshot['target'][:, self.active_joints]-snapshot['q'][:, self.active_joints]
        self.error_square_sum += error.square()
        self.error_abs_max = torch.maximum(self.error_abs_max, error.abs())
        self.previous_pick.copy_(self.pick)
        self._substeps += 1

    def end_control(self):
        if self._substeps != 4:
            raise RuntimeError('four actual native snapshots required')
        self._substeps = None
        failed = self.tick_failure.any(-1)
        distance, quality, _ = self._preparation()
        grip = self._grip_quality()
        same_event = (self.before_event == self.ledger.active) & ~self.ledger.done
        self.ledger.update_ready((distance <= .010) & (grip >= .75) & ~failed & same_event, 1./60.)
        phi, potential_key = self._potential()
        event = self.ledger.active.clamp(0, self.M-1)
        rows = torch.arange(self.N, device=self.device)
        history = self.ledger.history
        pending = ~self.ledger.done & ~history['resolved'][rows, event]
        final_string = self.ranks[event].argmax(-1)
        final_signed = self.signed[rows, final_string]*self.directions[event]
        self.ledger.add_terminal_progress((final_signed/.008).clamp(0, 1))
        recovery = (self.ledger.phase == 2) & ~self.ledger.done
        self.ledger.terms['recovery_speed'] += ((torch.linalg.vector_norm(self.pick_velocity, dim=-1)-.20)/.50).clamp(0, 1).square()*recovery
        low, high = self.action_bounds
        usage = (2*(self.snapshot['q'][:, self.active_joints]-low)/(high-low)-1).abs()
        reward, terms = compute_s3_reward(self.ledger.terms, grip_quality=grip,
            phi_before=self.before_phi, phi_after=phi,
            same_target=same_event & pending & (potential_key == self.before_potential_key),
            wait_quality=quality*(self._local_time() < self.first_times[event]-.07)*history['ready'][rows, event]*pending,
            ready_quality=quality, pending_ready=pending & ~history['ready'][rows, event],
            joint_limit_usage=usage, failed=failed)
        self.tick_cost += 5.*failed
        self.failure |= self.tick_failure
        self.previous_action.copy_(self.action)
        self.steps += 1
        self.total_reward += reward
        self.total_cost += self.tick_cost
        for key, value in terms.items():
            if key not in self.episode_reward_terms:
                self.episode_reward_terms[key] = torch.zeros_like(value)
                self.reward_window[key] = torch.zeros((), dtype=torch.float64, device=self.device)
            self.episode_reward_terms[key] += value
            self.reward_window[key] += value.double().sum()
        done = failed | (self._local_time()+1e-9 >= self.task.duration_s)
        self.finished |= done
        episodes = [self._episode(i, bool(failed[i])) for i in done.nonzero().flatten().tolist()]
        return self.observation(), reward, self.tick_cost.clone(), done, torch.zeros_like(done), episodes

    def _relative_state(self, index, reference_index):
        body, frame = self.body[:, index], self.body[:, reference_index]
        p, v = relative_point(body[:, :3], origin_velocity(body, self.com[index]), frame, self.com[reference_index])
        q = multiply(conjugate(frame[:, 3:7]), body[:, 3:7])
        basis = self._tensor([[1., 0., 0.], [0., 1., 0.]])
        rotation = apply(q[:, None].expand(-1, 2, -1), basis.expand(self.N, -1, -1)).flatten(1)
        omega = apply(conjugate(frame[:, 3:7]), body[:, 10:13]-frame[:, 10:13])
        return torch.cat((p, rotation, v, omega), -1)

    def set_curriculum(self, progress):
        return self.observation()

    def set_training_progress(self, committed_transitions):
        pass

    def reset_reward_window(self):
        for value in self.reward_window.values():
            value.zero_()

    def reward_window_means(self, transitions):
        return {key: float(value)/max(1, transitions) for key, value in self.reward_window.items()}

    def _goals(self):
        h, ledger = self.ledger.history, self.ledger
        rows = torch.arange(self.N, device=self.device)
        tokens, masks = [], []
        for slot in range(2):
            index = (ledger.active+slot).clamp_max(self.M-1)
            valid = (ledger.active+slot < self.M) & ~ledger.done
            current = valid & (slot == 0)
            accepted = h['accepted'][rows, index]
            remaining = self.traversal[index] & ~accepted
            rank = self.ranks[index].masked_fill(~remaining, 7.)
            string = torch.where(remaining.any(-1), rank.argmin(-1), self.ranks[index].argmax(-1))
            target, _ = self._phase_target(index, string, current)
            delta = target-self.pick
            normal = self.normal[rows, string]
            speed = (self.pick_velocity[:, :2]*normal).sum(-1)*self.directions[index]
            crossing_target = self._geometry_target(index, string)
            same_string_depth = crossing_target[:, 2]-self.pick[:, 2]
            base = torch.stack((string.float(), self.directions[index],
                (self.onsets[index]-self._local_time()).float(), (self.deadlines[index]-self._local_time()).float(),
                *delta.unbind(-1), *self.pick_velocity.unbind(-1), self.signed[rows, string],
                same_string_depth, speed, self.armed[rows, string], h['clean_complete'][rows, index],
                torch.ones_like(speed)), -1)
            errors = torch.where(accepted, h['times'][rows, index]-self.onsets[index, None]-self.offsets[index], 0.).float()
            event_fields = torch.stack((
                self.ranks[index, string], h['ready'][rows, index], ledger.ready_elapsed*current,
                h['wrong'][rows, index], h['resolved'][rows, index], h['complete'][rows, index],
                ledger.recovery_elapsed*current, ledger.recovery_best*current,
                h['recovered'][rows, index], ledger.recovery_required*current, ledger.handoff*current,
                accepted.sum(-1)/self.traversal[index].sum(-1), h['unprepared'][rows, index],
                h['missed'][rows, index], ledger.phase*current,
                ledger.clearance_required*current, ledger.rearm_required*current,
                ledger._recovery_fresh*current, ledger.terminal_best*current), -1)
            static = self.event_static[index]
            raw = torch.cat((base, static, self.traversal[index], self.audible[index], self.ranks[index],
                self.offsets[index], accepted, errors, event_fields, ledger.path_mask*current[:, None]), -1)
            tokens.append(torch.where(valid[:, None], (raw/self.goal_scales).clamp(-10, 10), 0.))
            masks.append(valid)
        return torch.stack(tokens, 1), torch.stack(masks, 1)

    def observation(self):
        ledger, h = self.ledger, self.ledger.history
        rows = torch.arange(self.N, device=self.device)
        guitar, pelvis = self.guitar_body, self.body[:, self.pelvis_index]
        gd = guitar[:, :3]-self.reference_guitar[:, :3]
        gr = rotvec(multiply(conjugate(self.reference_guitar[:, 3:7]), self.guitar_q))
        feet = self.body[:, self.feet_indices, :3]-self.reference_feet
        cooldown = (2-(self.clock[:, None]-self.last_hit)).clamp_min(0).float()/240.
        strings = torch.stack((self.armed, self.signed, cooldown), -1).flatten(1)
        status = torch.stack((h['ready'][rows, ledger.active], ledger.ready_elapsed,
                              h['recovered'][rows, ledger.active], ledger.recovery_elapsed), -1)
        gravity = apply(conjugate(pelvis[:, 3:7]), self._tensor([0., 0., -1.]).expand(self.N, -1))
        pv = apply(conjugate(pelvis[:, 3:7]), origin_velocity(pelvis, self.com[self.pelvis_index]))
        pw = apply(conjugate(pelvis[:, 3:7]), pelvis[:, 10:13])
        counts = torch.stack(((self.task.duration_s-self._local_time()).clamp_min(0),
            (ledger.active+ledger.done)/self.M, h['complete'].sum(-1), h['clean_complete'].sum(-1),
            h['missed'].sum(-1), sum(h[k].sum(-1) for k in ('unplanned', 'wrong_direction', 'order_violation', 'duplicate')),
            h['unprepared'].sum(-1)), -1).float()
        raw = torch.cat((self.snapshot['q']-self.reference, self.snapshot['qd'],
            self.snapshot['target']-self.snapshot['q'], self.previous_action[:, 12:],
            self._relative_state(self.guitar_index, self.pelvis_index),
            self._relative_state(self.wrist_index, self.guitar_index), self._relative_state(self.pick_index, self.guitar_index),
            self.flags, gd, gr, feet.flatten(1), strings, status, gravity, pv, pw, self.loss, counts), -1)
        goals, mask = self._goals()
        return dict(state=(raw/self.scales).clamp(-10, 10),
            events=raw.new_zeros(self.N, 0, GOAL_DIM), mask=torch.zeros(self.N, 0, dtype=torch.bool, device=self.device),
            priority_events=goals, priority_mask=mask)

    def _episode(self, index, failed):
        h = self.ledger.history
        counts = {key: int(h[key][index].sum()) for key in
                  ('complete', 'timed_complete', 'clean_complete', 'audible_complete', 'ready', 'recovered',
                   'missed', 'unprepared', 'unplanned', 'wrong_direction', 'order_violation', 'duplicate')}
        wrong = sum(counts[k] for k in ('unplanned', 'wrong_direction', 'order_violation', 'duplicate'))
        full = not failed and float(self._local_time()[index])+1e-9 >= self.task.duration_s
        success = bool(full and counts['clean_complete'] == self.M and counts['recovered'] == self.M and wrong == 0)
        events = []
        for j, event in enumerate(self.task.events):
            values = {key: value[index, j].cpu().tolist() for key, value in h.items()}
            values.update(event_id=event.event_id, gesture=event.gesture, traversal=list(event.traversal_strings),
                          audible=list(event.audible_strings), protected=list(event.protected_strings),
                          expected_times=list(event.crossing_times_s))
            events.append(values)
        metrics = dict(schema='guitar_learning.compact_strike_episode.v1', role='right',
            target_count=self.M, right_success_count=counts['clean_complete'], stage_success=success,
            provisional_success=False, completed=full, task_time_s=float(self._local_time()[index]),
            wrong_crossings=wrong, repeat_crossings=counts['duplicate'], **counts)
        return dict(worker_id=index, env_id=index, valid=True,
            reason='terminal_failure' if failed else 'timeline_complete',
            failure_reasons=[n for n, v in zip(FAILURE_REASONS, self.failure[index].tolist()) if v],
            cost=float(self.total_cost[index]), reward=float(self.total_reward[index]), steps=int(self.steps[index]),
            task_time_s=float(self._local_time()[index]), song=metrics,
            musical_quality=dict(schema=metrics['schema'], role='right', stage_success=success, song=copy.deepcopy(metrics)),
            strike_events=events, native_eligible_crossings=int(self.geometric_crossings[index]),
            rearm_blocked_crossings=int(self.blocked_crossings[index]),
            tracking_rmse_rad=(self.error_square_sum[index]/max(1, int(self.clock[index]))).sqrt().tolist(),
            tracking_max_error_rad=self.error_abs_max[index].tolist(),
            reward_components={key: float(value[index]) for key, value in self.episode_reward_terms.items()},
            measurement=copy.deepcopy(self.contract['measurement']))
