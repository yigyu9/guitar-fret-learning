"""왼팔 12축의 q-position 손목 Jacobian과 유한 목표각 보정 수학.

구형 단음 학습 실행기는 제거하고, 독립 FK 회귀 검증에 필요한 계산만
유지한다. 시뮬레이터를 실행하거나 관절 상태를 직접 쓰지 않는다.
"""
import math
import torch

from guitar_learning.gpu.control import apply, conjugate, multiply, rotvec
from guitar_learning.tool.validation.thumb_contact_probe import point_jacobian

WRIST_CONTROL = dict(
    rotation_length_scale_m=.1,
    damping=1e-5,
    correction_step_rad=math.radians(.5),
    jacobian_groups=['L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist'])


def _wrist_position_groups(controller, body_names, columns):
    """native 이름 순서대로 검증한 왼팔 4개 회전군을 구성한다."""
    if tuple(body_names[:len(controller.bodies)]) != tuple('human/'+n for n in controller.bodies):
        raise ValueError('Native human body/Jacobian row names differ')
    elements = {b.get('name'): b for b in controller.human_xml.iter('body')}
    parents = {c.get('name'): p.get('name') for p in controller.human_xml.iter('body') for c in p.findall('body')}
    column_ids = columns.cpu().tolist()
    groups, covered = [], []
    for name in WRIST_CONTROL['jacobian_groups']:
        joints = elements[name].findall('joint')
        qids, basis = controller.groups[name]
        ids = qids.cpu().tolist()
        source_names = [j.get('name') for j in joints]
        source_basis = basis.new_tensor([[float(v) for v in j.get('axis').split()] for j in joints]).T
        if (len(ids) != 3 or source_names != [controller.names[i] for i in ids]
                or basis.shape != (3, 3) or not torch.equal(basis, source_basis)
                or abs(float(torch.linalg.det(basis))) < 1e-6):
            raise ValueError('Exact source full-three-axis arm group required: '+name)
        slots = columns.new_tensor([column_ids.index(i) for i in ids])
        groups.append((body_names.index('human/'+parents[name]), body_names.index('human/'+name), qids, basis, slots))
        covered.extend(ids)
    if len(column_ids) != 12 or len(set(column_ids)) != 12 or set(column_ids) != set(covered):
        raise ValueError('Exact named arm12 Jacobian columns required')
    return dict(columns=columns.clone(), groups=tuple(groups))

def _so3_left_jacobian(value):
    x, y, z = value.unbind(-1)
    zero = torch.zeros_like(x)
    skew = torch.stack((zero, -z, y, z, zero, -x, -y, x, zero), -1).reshape(*value.shape[:-1], 3, 3)
    size2 = value.square().sum(-1)[..., None, None]
    size = size2.sqrt()
    a = .5*torch.sinc(size/(2*math.pi)).square()
    b = torch.where(size2 < 1e-4, 1/6-size2/120+size2.square()/5040,
                    (1-torch.sinc(size/math.pi))/size2.clamp_min(1e-12))
    return torch.eye(3, device=value.device, dtype=value.dtype)+a*skew+b*(skew@skew)

def _wrist_position_jacobian(snapshot, wrist, com, position_groups):
    columns = position_groups['columns']
    output = snapshot['q'].new_zeros((len(snapshot['q']), 6, len(columns)))
    ids = (~snapshot['reset_body_snapshot']).nonzero().flatten()
    if ids.numel() == 0:
        return output
    body = snapshot['body_state']
    native = snapshot['jacobian'][ids, wrist-1]
    linear = point_jacobian(native, apply(body[ids, wrist, 3:7], -com))
    origin = torch.cat((linear[:, :, columns], native[:, 3:, columns]), 1)
    converted = torch.empty_like(origin)
    for parent, own, qids, basis, slots in position_groups['groups']:
        value = (basis@snapshot['q'][ids][:, qids, None]).squeeze(-1)
        local = _so3_left_jacobian(value)@basis
        m = apply(body[ids, parent, None, 3:7], local.transpose(-1, -2)).transpose(-1, -2)
        s = snapshot['jacobian'][ids, own-1][:, 3:, qids]
        transform = torch.linalg.solve(s, m)
        converted[:, :, slots] = origin[:, :, slots]@transform
    output[ids] = converted
    return output

def wrist_error_and_jacobian(snapshot, wrist, guitar, com, position_groups, goal_position_G, goal_quaternion_G):
    body = snapshot['body_state']
    current = body[:, wrist]
    instrument = body[:, guitar]
    goal_world = instrument[:, :3]+apply(instrument[:, 3:7], goal_position_G)
    goal_rotation_world = multiply(instrument[:, 3:7], goal_quaternion_G)
    angular_error = rotvec(multiply(goal_rotation_world, conjugate(current[:, 3:7])))
    jacobian = _wrist_position_jacobian(snapshot, wrist, com, position_groups)
    scale = WRIST_CONTROL['rotation_length_scale_m']
    jacobian[:, 3:] *= scale
    error = torch.cat((goal_world-current[:, :3], scale*angular_error), dim=1)
    error = torch.where(snapshot['reset_body_snapshot'][:, None], torch.zeros_like(error), error)
    return error, jacobian

def bounded_wrist_target(base, correction, previous_request, actual_arm_q, jacobian, error, feedback_active,
                         lower, upper, rate):
    # 초기화 중인 행의 과거 Jacobian은 선형 풀이에서 제외한다.
    jacobian = torch.where(feedback_active[:, None, None], jacobian, torch.zeros_like(jacobian))
    error = torch.where(feedback_active[:, None], error, torch.zeros_like(error))
    eye = torch.eye(6, device=base.device, dtype=base.dtype)
    dq = (jacobian.transpose(-1,-2)@torch.linalg.solve(
        jacobian@jacobian.transpose(-1,-2)+WRIST_CONTROL['damping']*eye, error[..., None])).squeeze(-1)
    step = WRIST_CONTROL['correction_step_rad']
    proposal = base+correction
    actual = torch.where(feedback_active[:, None], actual_arm_q, proposal)
    candidate = actual+dq
    delta = torch.where(feedback_active[:, None], (candidate-proposal).clamp(-step, step), torch.zeros_like(proposal))
    desired = proposal+delta
    desired = torch.maximum(torch.minimum(desired, previous_request+rate/60), previous_request-rate/60)
    desired = torch.maximum(torch.minimum(desired, upper), lower)
    return desired, desired-base, delta, candidate
