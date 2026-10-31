"""목표각의 소유 범위를 정의한다: 왼손 33축과 오른팔 팔꿈치·손목 6축은 제어하고 나머지 42축은 유지한다.

유지는 리셋 기준의 구동기 목표를 뜻하며 실제 상태를 덮어쓰지 않는다.
이 모듈은 사전 설정·자산·시뮬레이터·체크포인트를 불러오지 않는다.

읽는 순서: 축 이름·프로필 → JointTargetContract의 초기화·목표 변환 → 범위·변화율 설정.
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
    """제한된 기준각 오프셋 → 평활화 → 변화율 제한 → 81축 목표각 순으로 변환한다.
    
    행동 순서는 축의 의미를 나타내는 ACTIVE_NAMES를 따르며 네이티브 자유도
    순서와 독립적이다. 전달된 이름으로 각 목표를 네이티브 81축에 배치한다.
    직전의 유지 대상 목표는 q_ref와 정확히 같아야 하며 오염되면 오류로 처리한다.
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
        if not np.isscalar(control_hz) or not np.isfinite(control_hz) or control_hz<=0:
            raise ValueError('positive control_hz and smoothing_alpha in (0,1] required')
        alpha = (float(smoothing_alpha) if np.isscalar(smoothing_alpha) else
                 _vector(smoothing_alpha,39,'smoothing_alpha'))
        if not np.isfinite(alpha).all() or np.any(np.asarray(alpha)<=0) or np.any(np.asarray(alpha)>1):
            raise ValueError('smoothing_alpha must be scalar or39 values in (0,1]')
        self.control_hz,self.alpha = float(control_hz),alpha
        if isinstance(self.alpha,np.ndarray): self.alpha.setflags(write=False)
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
            control_hz=self.control_hz,smoothing_alpha=(self.alpha.tolist() if isinstance(self.alpha,np.ndarray) else self.alpha),
            q_ref_rad=self.q_ref.tolist(),native_lower_rad=self.lower.tolist(),
            native_upper_rad=self.upper.tolist(),rates_rad_s=self.rates.tolist(),
            half_range_rad=self.half_range.tolist(),
            action_lower_rad=self.action_lower.tolist(),action_upper_rad=self.action_upper.tolist())
        # 호출 측이 입력 배열을 바꿔도 계약은 변하지 않는다.
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


def default_profile():
    return dict(schema='guitar_learning.flexible_left_fingers.v1',
                finger_rate_rad_s=4., finger_smoothing_alpha=.45,
                finger_stiffness=12., finger_damping=1.5,
                thumb_stiffness=8., thumb_damping=1.25,
                scope='left21_native_joint_limits')


def validate_profile(value):
    """기록된 고정 프로필만 받아들이고 JSON에 저장 가능한 독립 사본을 반환한다."""
    expected = default_profile()
    if (not isinstance(value, dict) or set(value) != set(expected) or
            any(type(value[key]) is not type(item) or value[key] != item
                for key, item in expected.items())):
        raise ValueError('exact flexible left finger profile required')
    return expected


def profile_control_settings(names, q_ref, lower, upper, half_ranges, rates, smoothing):
    """제어 설정을 복사하고 왼손 21축만 비대칭 네이티브 한계의 양 끝까지 확장한다.
    
    반범위 값은 기존 부호별 변환에 들어가는 기준각 중심 입력으로 유지한다.
    기준각에서 두 한계까지의 거리 중 큰 값을 택하면 기존 클리핑으로 양쪽
    한계에 도달하며, 정규화 행동 0은 계속 준비 기준각을 뜻한다.
    """
    names = tuple(names)
    if len(set(names)) != len(names) or not set(LEFT_HAND_NAMES) <= set(names):
        raise ValueError('unique native names including all left21 required')
    arrays = [np.array(value, dtype=float, copy=True)
              for value in (q_ref, lower, upper, rates)]
    if any(value.shape != (len(names),) or not np.isfinite(value).all()
           for value in arrays):
        raise ValueError('finite aligned native reference, bounds and rates required')
    reference, low, high, rate = arrays
    half = np.array(half_ranges, dtype=float, copy=True)
    alpha = np.array(smoothing, dtype=float, copy=True)
    if alpha.ndim == 0:
        alpha = np.full(39, float(alpha))
    if (half.shape != (39,) or not np.isfinite(half).all() or np.any(half <= 0.) or
            alpha.shape != (39,) or not np.isfinite(alpha).all() or
            np.any(alpha <= 0.) or np.any(alpha > 1.) or
            np.any(low > high) or np.any(reference < low) or
            np.any(reference > high) or np.any(rate < 0.)):
        raise ValueError('valid native bounds and39 channel controls required')
    profile = default_profile()
    for name in LEFT_HAND_NAMES:
        native, action = names.index(name), ACTIVE_NAMES.index(name)
        if low[native] >= high[native]:
            raise ValueError('left finger native joint must have positive range')
        half[action] = max(reference[native]-low[native], high[native]-reference[native])
        rate[native] = profile['finger_rate_rad_s']
        alpha[action] = profile['finger_smoothing_alpha']
    return half, rate, alpha


ZERO_RANGE_NAMES = frozenset(side + '_' + part + '_' + axis for side in ('L', 'R') for part in ('Knee', 'Toe') for axis in 'yz')


def target_rates(names):
    lower = tuple(side + '_' + part + '_' for side in ('L', 'R') for part in ('Hip', 'Knee', 'Ankle', 'Toe'))
    return np.array([.4 if name.startswith(lower) else .1 if name.startswith(('Torso_', 'Spine_', 'Chest_')) else .5 if name.startswith(('Neck_', 'Head_')) else 1.5 if name.startswith(('LH:', 'RH:')) else 3. for name in names])
