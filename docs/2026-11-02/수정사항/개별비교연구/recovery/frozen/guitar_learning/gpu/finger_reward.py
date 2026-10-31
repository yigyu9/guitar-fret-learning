"""왼손 목표 추종·실제 자세·대기 권고의 유한한 보상률을 계산한다.

손가락별 목표 선택 → 표면 추종 → 실제 각도 → B 대기 허용 구간 순서로 읽는다.
보상 계산은 제어 명령이나 물리 상태를 변경하지 않는다."""
import math
import torch

from guitar_learning.gpu.control import apply, conjugate, multiply


FINGER_TARGET_CONTRACT = dict(
    schema='guitar_learning.left_finger_targets.v1',
    slots=['index_tracking', 'index_next', 'middle_tracking', 'middle_next',
           'ring_tracking', 'ring_next', 'pinky_tracking', 'pinky_next'],
    index_shape='N,4,2; index/middle/ring/pinky, tracking/next', invalid_index=-1,
    tracking='assigned finger: audible earliest end, else preparation earliest onset',
    next='different from tracking; assigned finger future onset>now, preparation earliest onset',
    audible_window='onset<=now<end', preparation_window='press-2<=now<end',
    preparation_s=2., ties='first original score index',
    scope='shared reward/observation target selection; no control or note-state mutation')


def finger_target_indices(now, onset, end, press, finger, target_mask=None):
    """indices long[N,4,2]와 valid bool[N,4,2] 사전을 반환하며 무효 인덱스는 -1이다."""
    n, m = now.numel(), onset.numel()
    if (now.shape != (n,) or any(t.shape != (m,) for t in (onset, end, press, finger)) or
            finger.dtype != torch.long):
        raise ValueError('Aligned now[N], onset/end/press/finger[M] required')
    if not m:
        return dict(indices=torch.full((n, 4, 2), -1, device=now.device, dtype=torch.long),
                    valid=torch.zeros(n, 4, 2, device=now.device, dtype=torch.bool))
    # 목표 M축을 손가락 4축에 배정한다. 선택 결과는 [N,4,2]의 tracking/next 순서다.
    assigned = finger[None] == torch.arange(1, 5, device=finger.device)[:, None]
    if target_mask is not None:
        if target_mask.shape != (n, m) or target_mask.dtype != torch.bool:
            raise ValueError('target_mask must be bool[N,M]')
        assigned = assigned[None] & target_mask[:, None]
    else:
        assigned = assigned[None]
    audible = assigned & ((onset <= now[:, None]) & (now[:, None] < end))[:, None]
    preparing = assigned & ((press-2 <= now[:, None]) & (now[:, None] < end))[:, None]
    current = end.expand(n, 4, m).masked_fill(~audible, torch.inf).argmin(-1)
    upcoming = onset.expand(n, 4, m).masked_fill(~preparing, torch.inf).argmin(-1)
    first = torch.where(audible.any(-1), current, upcoming)
    future = (preparing & (onset[None, None] > now[:, None, None]) &
              (torch.arange(m, device=finger.device) != first[..., None]))
    second = onset.expand(n, 4, m).masked_fill(~future, torch.inf).argmin(-1)
    valid = torch.stack((audible.any(-1) | preparing.any(-1), future.any(-1)), -1)
    indices = torch.stack((first, second), -1)
    return dict(indices=torch.where(valid, indices, -1), valid=valid)


FINGER_REWARD_CONTRACT = dict(
    schema='guitar_learning.gpu_finger_tracking_rate.v5',
    preparation_s=2., distance_scale_m=.04,
    base_rate_per_s=2., candidate_multiplier=2.,
    selection='one per present finger: audible earliest end, else press-2..end earliest onset; original-order ties',
    target_selector_schema=FINGER_TARGET_CONTRACT['schema'],
    window='onset<=now<end for audible; press-2<=now<end for preparation',
    error='target minus selected physical finger surface',
    quality='(1+distance/0.04)^-2*(1+candidate)',
    rate='2/s * sum(valid selected qualities) / song-present finger count',
    rate_bounds_per_s=[0., 4.], integration='caller integrates actual physics dt; helper returns rate only',
    motion_cost='none; no requested-motion or surface-velocity suppression',
    legacy_arguments='velocity and actions are shape-checked only; neither changes quality',
    limitation='geometric/load candidate; no contact pair, pressure or acoustic certification')


def finger_tracking_reward(now, onset, end, press, finger, delta, velocity,
                           candidate, actions, target_mask=None):
    """rate[N]와 손가락별 indices/valid/quality[N,4]를 반환한다. 무효 인덱스는 -1이다.
    
    velocity와 actions는 기존 호출 인터페이스를 유지하지만 보상에는 영향을 주지 않는다.
    행동·관절 목표·입력 텐서를 변경하지 않는다. 현재 시간창에 목표가 없어도
    곡에 등장하는 손가락은 분모에 포함한다."""
    n, m = now.numel(), onset.numel()
    if (now.shape != (n,) or any(t.shape != (m,) for t in (onset, end, press, finger)) or
            delta.shape != (n, m, 3) or velocity.shape != delta.shape or
            candidate.shape != (n, m) or candidate.dtype != torch.bool or
            finger.dtype != torch.long or actions.shape != (n, 21)):
        raise ValueError('Aligned now[N], song[M], surface[N,M,3], candidate bool[N,M], LH21 actions required')
    if not m:
        return dict(rate=delta.new_zeros(n), quality=delta.new_zeros(n, 4),
                    indices=torch.full((n, 4), -1, device=delta.device, dtype=torch.long),
                    valid=torch.zeros(n, 4, device=delta.device, dtype=torch.bool))
    targets = finger_target_indices(now, onset, end, press, finger, target_mask)
    valid = targets['valid'][..., 0]
    selected = targets['indices'][..., 0].clamp_min(0)
    selected_delta = delta.gather(1, selected[..., None].expand(-1, -1, 3))
    selected_candidate = candidate.gather(1, selected)
    distance = torch.linalg.vector_norm(selected_delta, dim=-1)
    quality = (1+distance/.04).pow(-2)*(1+selected_candidate.to(delta.dtype))
    quality = torch.where(valid, quality, 0.)
    assigned = finger[None] == torch.arange(1, 5, device=finger.device)[:, None]
    present_fingers = (assigned.any(-1).sum().clamp_min(1) if target_mask is None else
        (assigned[None] & target_mask[:, None]).any(-1).sum(-1).clamp_min(1))
    return dict(rate=2*quality.sum(-1)/present_fingers, quality=quality,
                indices=torch.where(valid, selected, -1), valid=valid)


FINGER_COORDINATION_CONTRACT = dict(
    schema='guitar_learning.gpu_finger_posture_rate.v2',
    fingers=['index', 'middle', 'ring', 'pinky'], angles=['MCP', 'PIP', 'DIP'],
    quaternion_order='xyzw',
    geometry='actual parent-child rotation applies source segment direction(0,-1,0); signed atan2(-z,-y) after projection perpendicular to source flex axis+x',
    invalid_projection_norm_below=1e-6,
    invalid_credit='any invalid joint projection/quaternion zeros both posture qualities for that finger; returned invalid angles are0 with valid=False',
    scale_degrees=30.,
    coordination_violations_degrees=['relu(DIP-PIP-20)', 'relu(DIP-MCP-60)',
        'relu(-MCP-20)*clamp((DIP-30)/15,0,1)', 'relu(min(PIP,DIP)-60)'],
    coordination_quality='exp(-sum(violation_rad^2)/radians(30)^2)',
    standby_bands_degrees=[[-15., 110.], [15., 75.], [-10., 45.]],
    standby_quality='exp(-sum(distance_to_band_rad^2)/radians(30)^2)',
    idle_window='idle0 on each assigned note[press-2,end]; linear busy fade over0.25s outside each boundary; maximum busy over overlapping notes; absent fingers/empty score idle1',
    idle_fade_s=.25, preparation_s=2.,
    coordination_rate_per_s=.05, standby_rate_per_s=.05,
    rates='coordination=.05*mean4(quality); standby=.05*mean4(idle_weight*quality)',
    each_rate_bounds_per_s=[0., .05], integration='caller integrates actual physics dt',
    scope='experimental soft posture prior, not anatomical range certification; no thumb prior, fixed rest pose, control coupling, joint-limit or gain changes')


def finger_posture_reward(now, onset, end, press, finger, palm_quaternion,
                          segment_quaternion):
    """실제 굽힘을 측정하고 입력 변경 없이 두 개의 유한한 보상률을 반환한다.
    
    마디 순서는 검지·중지·약지·소지 × finger1/2/3이다. 각도는 원본 몸체 좌표계의
    기하 정의이며 native 구면 관절 자유도 좌표가 아니다. 설정 단계에서 원본 좌표계가
    source_finger_frame_contract() 검사를 먼저 통과해야 한다."""
    n, m = now.numel(), onset.numel()
    if (now.shape != (n,) or any(t.shape != (m,) for t in (onset, end, press, finger)) or
            finger.dtype != torch.long or palm_quaternion.shape != (n, 4) or
            segment_quaternion.shape != (n, 4, 3, 4)):
        raise ValueError('Aligned now[N], song[M], palm[N,4], segments[N,4,3,4] xyzw required')
    parent = torch.cat((palm_quaternion[:, None, None].expand(-1, 4, 1, -1),
                        segment_quaternion[:, :, :2]), 2)
    parent_ok = torch.isfinite(parent).all(-1) & (parent.square().sum(-1) > 1e-24)
    child_ok = torch.isfinite(segment_quaternion).all(-1) & (segment_quaternion.square().sum(-1) > 1e-24)
    parent = torch.where(torch.isfinite(parent), parent, 0.)
    child = torch.where(torch.isfinite(segment_quaternion), segment_quaternion, 0.)
    direction = apply(multiply(conjugate(parent), child), child.new_tensor([0., -1., 0.]))
    projected_norm = torch.linalg.vector_norm(direction[..., 1:], dim=-1)
    valid = parent_ok & child_ok & (projected_norm >= 1e-6)
    angles = torch.where(valid, torch.atan2(-direction[..., 2], -direction[..., 1]), 0.)
    mcp, pip, dip = angles.unbind(-1)
    rad = math.pi/180.
    violations = torch.stack((torch.relu(dip-pip-20*rad), torch.relu(dip-mcp-60*rad),
        torch.relu(-mcp-20*rad)*((dip-30*rad)/(15*rad)).clamp(0, 1),
        torch.relu(torch.minimum(pip, dip)-60*rad)), -1)
    coordination = torch.exp(-violations.square().sum(-1)/(30*rad)**2)
    bands = angles.new_tensor(FINGER_COORDINATION_CONTRACT['standby_bands_degrees'])*rad
    outside = torch.relu(bands[:, 0]-angles)+torch.relu(angles-bands[:, 1])
    standby = torch.exp(-outside.square().sum(-1)/(30*rad)**2)
    usable = valid.all(-1)
    coordination = torch.where(usable, coordination, 0.)
    standby = torch.where(usable, standby, 0.)
    idle = angles.new_ones(n, 4)
    if m:
        busy = torch.minimum(((now[:, None]-(press[None]-2-.25))/.25).clamp(0, 1),
                             ((end[None]+.25-now[:, None])/.25).clamp(0, 1))
        assigned = finger[None] == torch.arange(1, 5, device=finger.device)[:, None]
        idle = (1-(busy[:, None]*assigned[None]).amax(-1)).to(angles.dtype)
    return dict(angles=angles, valid=valid, idle_weight=idle,
                coordination_quality=coordination, standby_quality=standby,
                coordination_rate=.05*coordination.mean(-1),
                standby_rate=.05*(idle*standby).mean(-1))


B_PREPARATION_INPUT_DEGREES = [[25., 35., 12.], [28., 38., 14.],
                               [31., 41., 16.], [34., 44., 18.]]
B_PREPARATION_SPREAD_DEGREES = [-14., -3., 3., 10.]
# finger_posture_reward와 같은 전방 벡터 투영으로 측정한다.
# MCP Exp([x,0,z])의 기하 굽힘각은 입력 x와 정확히 같지 않다.
B_PREPARATION_ANGLES_DEGREES = [
    [math.degrees(math.atan2(x/math.hypot(x, z)*math.sin(math.radians(math.hypot(x, z))),
                            math.cos(math.radians(math.hypot(x, z))))), pip, dip]
    for (x, pip, dip), z in zip(B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES)]

FINGER_RECOVERY_SCHEMA = 'guitar_learning.left_finger_recovery.v1'


def finger_recovery_config(value=None):
    """명시적으로 검증한 유한한 회복 실험 옵션을 정규화한다."""
    default = dict(schema=FINGER_RECOVERY_SCHEMA, standby_rate_per_s=.02,
                   shape_rate_per_s=0.)
    if value is None:
        return default
    if not isinstance(value, dict) or set(value) != set(default):
        raise ValueError('Recovery config requires exactly schema, standby_rate_per_s, shape_rate_per_s')
    if value['schema'] != FINGER_RECOVERY_SCHEMA:
        raise ValueError('Unsupported finger recovery schema')
    for key, allowed in (('standby_rate_per_s', (.02, .04)),
                         ('shape_rate_per_s', (0., .004))):
        rate = value[key]
        if (isinstance(rate, bool) or not isinstance(rate, (int, float)) or
                not math.isfinite(rate) or rate not in allowed):
            raise ValueError('Unsupported finger recovery '+key)
    return dict(schema=FINGER_RECOVERY_SCHEMA,
                standby_rate_per_s=float(value['standby_rate_per_s']),
                shape_rate_per_s=float(value['shape_rate_per_s']))


FINGER_PREPARATION_CONTRACT = dict(
    schema='guitar_learning.gpu_finger_preparation_rate.v5',
    measurement_schema=FINGER_COORDINATION_CONTRACT['schema'],
    reference='user-selected static B; flexion preference only, never a joint target or required waypoint',
    reference_input_degrees=B_PREPARATION_INPUT_DEGREES,
    reference_spread_degrees=B_PREPARATION_SPREAD_DEGREES,
    reference_geometric_degrees=B_PREPARATION_ANGLES_DEGREES,
    half_band_degrees=15., outside_scale_degrees=30.,
    quality='1/(1+sum((relu(abs(actual-reference)-15deg)/30deg)^2)); invalid fingers zero',
    gate='score-only per-finger active union; release grace0.05s then0.1s fade; next press preparation0.35s with0.1s fade; short gaps direct, medium gaps partial recovery',
    preparation_s=.35, fade_s=.1, release_grace_s=.05, relevant_preparation_s=2.,
    gap_s=[.25, .6], medium_preparation='min(0.35,0.4*gap)',
    tracking='quality multiplied by1-idle_weight; wrist and arm lookahead remains2s',
    contact_veto='none outside protected press..end; residual candidate/wrong cannot block recovery',
    proximity_veto_m=None,
    proximity_veto='distance never suppresses recovery; nonfinite own relevant distances still invalidate that finger',
    empty_score_rate_per_s=0., coordination_rate_per_s=0., standby_rate_per_s=.02,
    allowed_standby_rates_per_s=[.02, .04], shape_rate_per_s=0.,
    rate='standby_rate_per_s * mean4(per_finger_gate * quality); fixed four-finger denominator',
    rate_bounds_per_s=[0., .02], integration='actual240Hz dt, existing approach stage weight',
    scope='optional independent finger idle bonus only; no thumb/spread target, movement cost, penalty, control/reset change or success prerequisite')


FINGER_SHAPE_CONTRACT = dict(
    schema='guitar_learning.gpu_finger_shape_rate.v1',
    measurement_schema=FINGER_COORDINATION_CONTRACT['schema'],
    target_selector_schema=FINGER_TARGET_CONTRACT['schema'],
    active='valid selected tracking target, including candidate/clean contact',
    shape_error='relu(DIP-PIP-50deg)/30deg',
    quality='1/(1+shape_error^2); invalid fingers zero',
    default_rate_per_s=0., allowed_rates_per_s=[0., .004],
    rate='shape_rate_per_s * mean4(active * quality); fixed four-finger denominator',
    rate_bounds_per_s=[0., .004],
    scope='optional weak preference, no thumb/spread/MCP target, coupling, action or velocity cost')


def finger_preparation_gate(now, onset, end, press, finger, contact, distance, target_mask=None):
    """관측과 보상이 공유하는 끝점 기준의 순수 B 대기 허용도를 구한다."""
    n, m = now.numel(), onset.numel()
    if (now.shape != (n,) or any(t.shape != (m,) for t in (onset, end, press, finger)) or
            finger.dtype != torch.long or contact.shape != (n, 4) or
            contact.dtype != torch.bool or distance.shape != (n, m)):
        raise ValueError('Aligned now[N], song[M], contact bool[N,4], pad distance[N,M] required')
    assigned = finger[None] == torch.arange(1, 5, device=finger.device)[:, None]
    if target_mask is not None and (target_mask.shape != (n, m) or target_mask.dtype != torch.bool):
        raise ValueError('target_mask must be bool[N,M]')
    relevant = (now[:, None] >= press[None]-2.) & (now[:, None] <= end[None])
    if target_mask is not None:
        relevant &= target_mask
    own_relevant = relevant[:, None] & assigned[None]
    near = torch.zeros(n, 4, dtype=torch.bool, device=now.device)
    nonfinite = ((~torch.isfinite(distance))[:, None] & own_relevant).any(-1)
    contact_veto = torch.zeros_like(near)
    idle = now.new_ones(n, 4)
    if m:
        owned = assigned[None].expand(n, -1, -1)
        if target_mask is not None:
            owned = owned & target_mask[:, None]
        active = (owned & ((press[None] <= now[:, None]) &
                          (now[:, None] <= end[None]))[:, None]).any(-1)
        past = owned & (end[None, None] < now[:, None, None])
        future = owned & (press[None, None] > now[:, None, None])
        previous_end = end.expand(n, 4, m).masked_fill(~past, -torch.inf).amax(-1)
        next_press = press.expand(n, 4, m).masked_fill(~future, torch.inf).amin(-1)
        gap = next_press-previous_end
        # 처음·마지막의 무한 간격은 inf-inf 없이 통상적인 준비 시간을 사용한다.
        finite_gap = torch.isfinite(gap)
        amount = torch.where(finite_gap, ((gap-.25)/.35).clamp(0, 1), 1.)
        lead = torch.where(finite_gap & (gap < .6), .4*gap, .35)
        releasing = ((now[:, None]-previous_end-.05)/.1).clamp(0, 1)
        preparing = ((next_press-now[:, None]-lead)/.1).clamp(0, 1)
        idle = torch.where(active, 0., amount*releasing*preparing).to(now.dtype)
    gate = idle*~(contact_veto | near | nonfinite)
    if not m:
        gate = torch.zeros_like(gate)
    return dict(gate=gate, idle_weight=idle, near_veto=near,
                nonfinite_veto=nonfinite, contact_veto=contact_veto,
                relevant_targets=relevant, tracking_weight=1-idle)


def finger_preparation_reward(now, onset, end, press, finger, palm_quaternion,
                              segment_quaternion, contact, distance, rate_per_s=.02,
                              target_mask=None):
    """제어·음 상태를 바꾸지 않고 손가락별 B 자세 선호 보상을 계산한다."""
    config = finger_recovery_config(dict(schema=FINGER_RECOVERY_SCHEMA,
        standby_rate_per_s=rate_per_s, shape_rate_per_s=0.))
    measured = finger_posture_reward(now, onset, end, press, finger,
                                     palm_quaternion, segment_quaternion)
    gated = finger_preparation_gate(now, onset, end, press, finger, contact, distance, target_mask)
    angles = measured['angles']
    reference = angles.new_tensor(B_PREPARATION_ANGLES_DEGREES)*math.pi/180.
    outside = torch.relu((angles-reference).abs()-math.radians(15.))
    quality = (1+outside.square().sum(-1)/math.radians(30.)**2).reciprocal()
    usable = measured['valid'].all(-1)
    quality = torch.where(usable, quality, 0.)
    per_finger_rate = config['standby_rate_per_s']*gated['gate']*quality/4
    return dict(quality=quality, rate=per_finger_rate.sum(-1),
                per_finger_rate=per_finger_rate,
                band_inside=usable & (outside == 0).all(-1),
                angles=angles, valid=measured['valid'], **gated)


def finger_shape_reward(now, onset, end, press, finger, angles, valid, rate_per_s=0.,
                        target_mask=None):
    """기존 목표 선택기를 유지하며 선택적 추종 구간 DIP/PIP 자세 선호를 계산한다."""
    config = finger_recovery_config(dict(schema=FINGER_RECOVERY_SCHEMA,
        standby_rate_per_s=.02, shape_rate_per_s=rate_per_s))
    if angles.shape != (now.numel(), 4, 3) or valid.shape != angles.shape or valid.dtype != torch.bool:
        raise ValueError('Aligned angles[N,4,3] and valid bool[N,4,3] required')
    targets = finger_target_indices(now, onset, end, press, finger, target_mask)
    usable = valid.all(-1) & torch.isfinite(angles).all(-1)
    safe_angles = torch.where(torch.isfinite(angles), angles, 0.)
    shape_error = torch.relu(safe_angles[..., 2]-safe_angles[..., 1]-math.radians(50.))/math.radians(30.)
    shape_error = torch.where(usable, shape_error, 0.)
    quality = torch.where(usable, (1+shape_error.square()).reciprocal(), 0.)
    active = targets['valid'][..., 0]
    per_finger_rate = quality*active*config['shape_rate_per_s']/4
    return dict(rate=per_finger_rate.sum(-1), quality=quality,
                per_finger_rate=per_finger_rate, active=active,
                shape_error=shape_error)


def _verify_source_frames(xml):
    """이 네 손가락에만 적용되는 원본 좌표계 정의를 무효화하는 자산 변경을 거부한다."""
    bodies = {body.get('name'): body for body in xml.findall('.//body')}
    parents = {child.get('name'): body.get('name') for body in bodies.values() for child in body.findall('body')}
    for finger in FINGER_COORDINATION_CONTRACT['fingers']:
        names = ['LH:'+finger+str(i) for i in (1, 2, 3)]+['LH:'+finger+'_top']
        for i, name in enumerate(names):
            body = bodies.get(name)
            if body is None or parents.get(name) != ('LH:palm' if i == 0 else names[i-1]):
                raise ValueError('Expected source palm/finger1/2/3/top chain: '+name)
            q = [float(x) for x in body.get('quat', '1 0 0 0').split()]
            if (len(q) != 4 or any(not math.isfinite(x) for x in q) or
                    abs(abs(q[0])-1) > 1e-10 or any(abs(x) > 1e-10 for x in q[1:]) or
                    any(key in body.attrib for key in ('euler', 'axisangle', 'xyaxes', 'zaxis'))):
                raise ValueError('Identity source body rest rotation required: '+name)
            if i:
                pos = [float(x) for x in body.get('pos', '').split()]
                if (len(pos) != 3 or any(not math.isfinite(x) for x in pos) or
                        abs(pos[0]) > 1e-10 or not pos[1] < 0 or abs(pos[2]) > 1e-10):
                    raise ValueError('Source segment forward must be negative y: '+name)
            if i < 3:
                joint = body.find("joint[@name='"+'LH:'+finger+('1_x' if i == 0 else str(i+1))+"']")
                axis = [] if joint is None else [float(x) for x in joint.get('axis', '').split()]
                if (len(axis) != 3 or any(not math.isfinite(x) for x in axis) or
                        any(abs(x-y) > 1e-10 for x, y in zip(axis, (1., 0., 0.)))):
                    raise ValueError('Source flex axis must be positive x: '+name)


def source_finger_frame_contract():
    """호출자 설정 시 봉인된 준비 인체 XML을 한 번 검증하며 시뮬레이터는 사용하지 않는다."""
    import hashlib
    import xml.etree.ElementTree as ET
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.native.paths import resolve_input_path
    source = resolve_input_path(load_prepared_reset_contract()['initial']['loaded_assets'][0]['path']).resolve()
    _verify_source_frames(ET.parse(source).getroot())
    return dict(schema='guitar_learning.source_finger_flex_frames.v1', source_xml=str(source),
        source_sha256={str(source): hashlib.sha256(source.read_bytes()).hexdigest()},
        palm_body='LH:palm', finger_body_names=[['LH:'+f+str(i) for i in (1, 2, 3)]
            for f in FINGER_COORDINATION_CONTRACT['fingers']],
        neutral_segment_direction=[0., -1., 0.], positive_flex_axis=[1., 0., 0.],
        rest_rotation='identity for palm-relative finger1 and consecutive finger2/3/top',
        attachment='palm-to-finger1 position may vary; segment direction is defined by child2/3/top offsets',
        limitation='actual source-body geometric flexion; not native spherical coordinates or anatomical range certification')
