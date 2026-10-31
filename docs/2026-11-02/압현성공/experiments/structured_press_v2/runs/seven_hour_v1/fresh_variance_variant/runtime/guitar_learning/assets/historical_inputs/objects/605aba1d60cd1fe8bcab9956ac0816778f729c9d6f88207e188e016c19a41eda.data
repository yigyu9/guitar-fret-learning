"""Pure target ownership: LH33 + right elbow/wrist6 active, other42 held.

Held means a reset-reference actuator target, never an actual-state overwrite.
No preset, asset, simulator or checkpoint is loaded by this module.
"""
import numpy as np


def _triples(parts):
    return tuple(part+'_'+axis for part in parts for axis in 'xyz')


def _hand(side):
    return tuple(side+':'+name for name in (
        'thumb1_x','thumb1_y','thumb1_z','thumb2','thumb3',
        'index1_x','index1_z','index2','index3',
        'middle1_x','middle1_z','middle2','middle3',
        'ring1_x','ring1_z','ring2','ring3',
        'pinky1_x','pinky1_z','pinky2','pinky3'))


LEFT_ARM_NAMES = _triples(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))
LEFT_HAND_NAMES = _hand('LH')
RIGHT_STRIKE_NAMES = _triples(('R_Elbow','R_Wrist'))
ACTIVE_NAMES = LEFT_ARM_NAMES+LEFT_HAND_NAMES+RIGHT_STRIKE_NAMES
SUPPORT_HELD_NAMES = _triples(('Torso','Spine','Chest','R_Thorax','R_Shoulder'))
RIGHT_GRIP_NAMES = _hand('RH')
HEAD_HELD_NAMES = _triples(('Neck','Head'))
HELD_NAMES = SUPPORT_HELD_NAMES+RIGHT_GRIP_NAMES+HEAD_HELD_NAMES
EXPECTED_NAMES = frozenset(ACTIVE_NAMES+HELD_NAMES)


def _vector(value,length,label):
    result = np.array(value,dtype=float,copy=True)
    if result.shape!=(length,) or not np.isfinite(result).all():
        raise ValueError(label+' must be finite shape '+str((length,)))
    return result


class JointTargetContract:
    """Bounded reference offsets -> smoothing -> rate limit -> target81.

    Action order is semantic ACTIVE_NAMES, independent of native DOF ordering.
    The supplied names determine where each target is written in native81.
    Every previous held target must equal q_ref exactly; contamination raises.
    """
    action_dim = 39
    target_dim = 81
    active_names = ACTIVE_NAMES
    held_names = HELD_NAMES

    def __init__(self,names,q_ref,lower,upper,rates_rad_s,*,half_range_rad,
                 control_hz=60.,smoothing_alpha=.2):
        names = tuple(names)
        if (len(names)!=81 or any(not isinstance(name,str) for name in names)
                or len(set(names))!=81 or set(names)!=EXPECTED_NAMES):
            raise ValueError('unique exact named upper-body81 set required; no lower-body DOFs')
        self.names = names
        self.q_ref = _vector(q_ref,81,'q_ref')
        self.lower = _vector(lower,81,'lower')
        self.upper = _vector(upper,81,'upper')
        self.rates = _vector(rates_rad_s,81,'rates_rad_s')
        self.half_range = _vector(half_range_rad,39,'half_range_rad')
        if (np.any(self.lower>=self.upper) or np.any(self.q_ref<self.lower)
                or np.any(self.q_ref>self.upper) or np.any(self.rates<0)
                or np.any(self.half_range<=0)):
            raise ValueError('reference, native bounds, rate or offset range invalid')
        self.active_indices = np.array([names.index(name) for name in ACTIVE_NAMES],dtype=int)
        self.held_indices = np.array([names.index(name) for name in HELD_NAMES],dtype=int)
        if np.any(self.rates[self.active_indices]<=0): raise ValueError('active rates must be positive')
        if (not np.isscalar(control_hz) or not np.isfinite(control_hz) or control_hz<=0
                or not np.isscalar(smoothing_alpha) or not np.isfinite(smoothing_alpha)
                or not 0<smoothing_alpha<=1):
            raise ValueError('positive control_hz and smoothing_alpha in (0,1] required')
        self.control_hz,self.alpha = float(control_hz),float(smoothing_alpha)
        active_ref = self.q_ref[self.active_indices]
        self.action_lower = np.maximum(self.lower[self.active_indices],active_ref-self.half_range)
        self.action_upper = np.minimum(self.upper[self.active_indices],active_ref+self.half_range)
        self.metadata = dict(schema='music_pipeline_v2.target_ownership.v1',action_dim=39,target_dim=81,
            action_order=list(ACTIVE_NAMES),native_order=list(names),held_names=list(HELD_NAMES),
            action_codec='signed normalized offset from reset reference; asymmetric endpoints clipped to native limits',
            held_previous_policy='reject any exact-reference mismatch',
            held_scope='actuator targets only; actual states remain governed by physics',
            support_microadjustment='not present; policy action authority on support-held15 is zero',
            contact_roles=dict(
                chest=dict(rigid_body='Chest',held_target_dofs=list(_triples(('Torso','Spine','Chest')))),
                right_upper_arm=dict(rigid_body='R_Shoulder',segment='shoulder to elbow',
                    held_target_dofs=list(_triples(('R_Thorax','R_Shoulder'))),
                    active_distal_dofs=list(RIGHT_STRIKE_NAMES)),
                thigh=dict(rigid_bodies=['R_Hip','L_Hip'],target_dofs_in_native81=[],
                    scope='lower-body support requires external fixed-lower asset contract; absent from this action vector'),
                left_hand=dict(primary_role='fret press/hold/release',support_requirement='no required guitar support task'),
                right_hand=dict(primary_role='hold reset-reference pick-grip targets',held_target_dofs=list(RIGHT_GRIP_NAMES))),
            control_hz=self.control_hz,smoothing_alpha=self.alpha,
            q_ref_rad=self.q_ref.tolist(),native_lower_rad=self.lower.tolist(),
            native_upper_rad=self.upper.tolist(),rates_rad_s=self.rates.tolist(),
            half_range_rad=self.half_range.tolist(),
            action_lower_rad=self.action_lower.tolist(),action_upper_rad=self.action_upper.tolist())
        # Caller mutation of input arrays cannot change the contract.
        for value in (self.q_ref,self.lower,self.upper,self.rates,self.half_range,
                      self.active_indices,self.held_indices,self.action_lower,self.action_upper):
            value.setflags(write=False)

    def reset_targets(self):
        return self.q_ref.copy()

    def targets(self,action,previous_target):
        action = _vector(action,39,'action')
        previous = _vector(previous_target,81,'previous_target')
        if np.any(np.abs(action)>1): raise ValueError('normalized action must be bounded in [-1,1]')
        if not np.array_equal(previous[self.held_indices],self.q_ref[self.held_indices]):
            raise ValueError('held previous target contaminated; reset-reference target required')
        if (np.any(previous[self.active_indices]<self.action_lower)
                or np.any(previous[self.active_indices]>self.action_upper)):
            raise ValueError('active previous target outside effective bounds')
        reference = self.q_ref[self.active_indices]
        requested = self.q_ref.copy()
        requested[self.active_indices] = reference+np.where(
            action>=0,self.action_upper-reference,reference-self.action_lower)*action
        final = self.q_ref.copy()
        old = previous[self.active_indices]
        smoothed = old+self.alpha*(requested[self.active_indices]-old)
        step = self.rates[self.active_indices]/self.control_hz
        final[self.active_indices] = np.clip(np.clip(smoothed,old-step,old+step),
                                             self.action_lower,self.action_upper)
        return requested,final
