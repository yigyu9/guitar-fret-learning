"""Bounded left-finger surface/posture reward rates; never change control."""
import math
import torch

from guitar_learning.gpu.geometry import apply, conjugate, multiply


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


def finger_target_indices(now, onset, end, press, finger):
    """Return dict(indices long[N,4,2], valid bool[N,4,2]); invalid=-1."""
    n, m = now.numel(), onset.numel()
    if (now.shape != (n,) or any(t.shape != (m,) for t in (onset, end, press, finger)) or
            finger.dtype != torch.long):
        raise ValueError('Aligned now[N], onset/end/press/finger[M] required')
    if not m:
        return dict(indices=torch.full((n, 4, 2), -1, device=now.device, dtype=torch.long),
                    valid=torch.zeros(n, 4, 2, device=now.device, dtype=torch.bool))
    assigned = finger[None] == torch.arange(1, 5, device=finger.device)[:, None]
    audible = assigned[None] & ((onset <= now[:, None]) & (now[:, None] < end))[:, None]
    preparing = assigned[None] & ((press-2 <= now[:, None]) & (now[:, None] < end))[:, None]
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
                           candidate, actions):
    """Return rate[N], indices/valid/quality[N,4]; invalid indices are -1.

    ``velocity`` and ``actions`` retain the existing aligned calling interface,
    but never affect reward. No action, joint target or input tensor is changed.
    The denominator includes song-present fingers even when they have no target
    in the current window.
    """
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
    targets = finger_target_indices(now, onset, end, press, finger)
    valid = targets['valid'][..., 0]
    selected = targets['indices'][..., 0].clamp_min(0)
    selected_delta = delta.gather(1, selected[..., None].expand(-1, -1, 3))
    selected_candidate = candidate.gather(1, selected)
    distance = torch.linalg.vector_norm(selected_delta, dim=-1)
    quality = (1+distance/.04).pow(-2)*(1+selected_candidate.to(delta.dtype))
    quality = torch.where(valid, quality, 0.)
    assigned = finger[None] == torch.arange(1, 5, device=finger.device)[:, None]
    present_fingers = assigned.any(-1).sum().clamp_min(1)
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
    """Measure actual flexion and return two bounded rates, without mutation.

    Segment order is index/middle/ring/pinky x finger1/2/3. Angles are a source
    body-frame geometric definition, not native spherical DOF coordinates.
    Source frames must first pass ``source_finger_frame_contract()`` at setup.
    """
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
# Measure the same forward-vector projection as finger_posture_reward;
# MCP Exp([x,0,z]) does not give geometric flexion exactly equal to input x.
B_PREPARATION_ANGLES_DEGREES = [
    [math.degrees(math.atan2(x/math.hypot(x, z)*math.sin(math.radians(math.hypot(x, z))),
                            math.cos(math.radians(math.hypot(x, z))))), pip, dip]
    for (x, pip, dip), z in zip(B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES)]

FINGER_PREPARATION_CONTRACT = dict(
    schema='guitar_learning.gpu_finger_preparation_rate.v1',
    measurement_schema=FINGER_COORDINATION_CONTRACT['schema'],
    reference='user-selected static B; flexion preference only, never a joint target or required waypoint',
    reference_input_degrees=B_PREPARATION_INPUT_DEGREES,
    reference_spread_degrees=B_PREPARATION_SPREAD_DEGREES,
    reference_geometric_degrees=B_PREPARATION_ANGLES_DEGREES,
    half_band_degrees=15., outside_scale_degrees=30.,
    quality='exp(-sum(relu(abs(actual-reference)-15deg)^2)/(30deg)^2); mean4, invalid fingers zero',
    gate='min of legacy per-finger idle weights; whole hand zero if any assigned note in press-2..end; fade0.25s outside',
    contact_veto='any current nonthumb finger1/2/3 net load>=0.01N, previous/current candidate or wrong press blocks whole hand',
    proximity_veto_m=.04,
    proximity_veto='any assigned pad-to-song-target distance<=0.04m blocks whole hand; nonfinite distance also blocks',
    empty_score_rate_per_s=0., coordination_rate_per_s=0., standby_rate_per_s=.01,
    rate_bounds_per_s=[0., .01], integration='actual240Hz dt, existing approach stage weight',
    scope='optional whole-hand idle bonus only; no thumb/spread target, movement cost, penalty, control/reset change or success prerequisite')


def finger_preparation_reward(now, onset, end, press, finger, palm_quaternion,
                              segment_quaternion, contact, distance):
    """Weak B preference outside preparation/contact; never modify control.

    ``contact[N]`` conservatively includes nonthumb segment net loads and both
    contact endpoints. ``distance[N,M]`` is the actual pad distance to each
    assigned song target, including targets outside the current time window.
    """
    measured = finger_posture_reward(now, onset, end, press, finger,
                                     palm_quaternion, segment_quaternion)
    if contact.shape != now.shape or contact.dtype != torch.bool or distance.shape != (now.numel(), onset.numel()):
        raise ValueError('Aligned contact bool[N] and pad distance[N,M] required')
    angles = measured['angles']
    reference = angles.new_tensor(B_PREPARATION_ANGLES_DEGREES)*math.pi/180.
    outside = torch.relu((angles-reference).abs()-math.radians(15.))
    quality = torch.exp(-outside.square().sum(-1)/math.radians(30.)**2)
    quality = torch.where(measured['valid'].all(-1), quality, 0.)
    near = ((distance <= .04) | ~torch.isfinite(distance)).any(-1)
    gate = measured['idle_weight'].amin(-1)*~(contact | near)
    if not onset.numel():
        gate = torch.zeros_like(gate)
    return dict(quality=quality, gate=gate, rate=.01*gate*quality.mean(-1))


def _verify_source_frames(xml):
    """Reject source changes that invalidate this specific four-finger frame."""
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
    """Verify the pinned prepared human XML once at caller setup; no simulator."""
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
