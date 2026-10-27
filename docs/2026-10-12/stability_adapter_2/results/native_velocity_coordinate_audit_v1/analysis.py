"""Saved native states only: coordinate audit, no simulator imports or execution."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial.transform import Rotation as Rotation


ROOT = Path('/home/ajou/yigyu/3')
OUT = Path(__file__).resolve().parent
TRIAL = ROOT / 'docs/2026-10-12/stability_adapter_2/results/strike_effort_geometry_pi_v1/native/data'
INPUTS = [TRIAL / 'trace.json', TRIAL / 'initial_values.json',
          ROOT / 'stability_adapter_2/assets/humanoid_fixed_lower.xml']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vector(value):
    return np.array([value[axis] for axis in ('x', 'y', 'z')], dtype=float)


def rotation(value):
    return Rotation.from_quat([value[axis] for axis in ('x', 'y', 'z', 'w')])


def left_jacobian(phi):
    angle = np.linalg.norm(phi)
    x, y, z = phi
    cross = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
    if angle < 1e-5:
        return np.eye(3) + .5 * cross + cross @ cross / 6.
    return (np.eye(3) + (1. - np.cos(angle)) / angle**2 * cross
            + (angle - np.sin(angle)) / angle**3 * cross @ cross)


def metrics(error, mask):
    norms = np.linalg.norm(error[mask], axis=1)
    return {'count': int(mask.sum()), 'vector_RMS_rad_s': float(np.sqrt(np.mean(norms**2))),
            'max_vector_error_rad_s': float(norms.max()),
            'median_vector_error_rad_s': float(np.median(norms))}


def main():
    before = {str(path): sha(path) for path in INPUTS}
    trace = json.loads(INPUTS[0].read_text())
    initial = json.loads(INPUTS[1].read_text())
    tree = ET.parse(INPUTS[2])
    parents = {child.get('name'): body.get('name')
               for body in tree.findall('.//body') for child in body.findall('body')}
    joint_axes = {joint.get('name'): np.fromstring(joint.get('axis', '0 0 1'), sep=' ')
                  for joint in tree.findall('.//joint') if joint.get('name')}
    times = np.array([row['time_s'] for row in trace])
    assert len(trace) == 151 and np.all(np.diff(times) > 0)
    groups = [f'{side}_{name}' for side in ('L', 'R')
              for name in ('Thorax', 'Shoulder', 'Elbow', 'Wrist')]
    expressions = {
        'parent_Bv': 'R_parent,W @ B @ v_native',
        'parent_Jleft_Bv': 'R_parent,W @ J_left(Bq) @ B @ v_native',
        'child_Bv': 'R_child,W @ B @ v_native',
        'parent_Iv': 'R_parent,W @ v_native',
        'parent_Jleft_Iv': 'R_parent,W @ J_left(Bq) @ v_native',
        'child_Iv': 'R_child,W @ v_native',
        'parent_Exp_Bv': 'R_parent,W @ Exp(Bq) @ B @ v_native',
        'parent_Exp_Iv': 'R_parent,W @ Exp(Bq) @ v_native',
        'world_Bv': 'B @ v_native',
        'world_Iv': 'v_native',
    }
    summary = {
        'scope': '저장된151개 native snapshot 읽기와 회전 수학만 수행. 물리/정책 실행, A 수정 없음.',
        'input_sha256': before, 'analysis_sha256': sha(Path(__file__)),
        'world_reference': 'omega_child,W - omega_parent,W, same native snapshot vel.angular fields',
        'q_and_v_order': 'Each group uses native named _x,_y,_z scalar channels. q and native v are separately read; v is not assumed dq/dt.',
        'B_definition': 'Columns are XML hinge axis for group _x,_y,_z; B=[[1,0,0],[0,0,1],[0,1,0]] here. Suffix is not a world axis.',
        'J_left_definition': 'I + (1-cos(theta))/theta^2 [phi]x + (theta-sin(theta))/theta^3 [phi]x^2; phi=Bq.',
        'candidate_expressions': expressions,
        'metrics_definition': 'vector RMS=sqrt(mean(||prediction-reference||^2)); max is max Euclidean norm; units rad/s.',
        'nontrivial_mask': '||native v|| > 0.01 rad/s; independent mask ||omega_child,W-omega_parent,W||>0.01 also reported.',
        'sampling': {'count': len(trace), 'physics_steps': [row['physics_step'] for row in trace],
                     'dt_s_min': float(np.diff(times).min()), 'dt_s_max': float(np.diff(times).max()),
                     'finite_difference': 'Interior149 points; log(R_rel[i+1] @ R_rel[i-1]^-1)/(t[i+1]-t[i-1]) in parent axes, mapped by R_parent[i]. q central difference uses same interval. This is sampled8step approximation, not instantaneous equivalence.'},
        'groups': {},
    }
    pooled = {name: [] for name in expressions}
    pooled_masks = []
    for group in groups:
        indices = [initial['joint_names'].index(group + '_' + axis) for axis in ('x', 'y', 'z')]
        child_index = initial['human_body_names'].index(group)
        parent_index = initial['human_body_names'].index(parents[group])
        B = np.column_stack([joint_axes[group + '_' + axis] for axis in ('x', 'y', 'z')])
        q, vel, reference, predictions, relative = [], [], [], {name: [] for name in expressions}, []
        parent_rotations = []
        for row in trace:
            state = row['native_state']
            child, parent = [state['human_body_states'][i] for i in (child_index, parent_index)]
            Rp, Rc = rotation(parent['pose']['r']), rotation(child['pose']['r'])
            qq = np.array([state['human_dof_states'][i]['pos'] for i in indices])
            vv = np.array([state['human_dof_states'][i]['vel'] for i in indices])
            phi = B @ qq
            J = left_jacobian(phi)
            E = Rotation.from_rotvec(phi)
            ref = vector(child['vel']['angular']) - vector(parent['vel']['angular'])
            values = [Rp.apply(B @ vv), Rp.apply(J @ B @ vv), Rc.apply(B @ vv),
                      Rp.apply(vv), Rp.apply(J @ vv), Rc.apply(vv),
                      Rp.apply(E.apply(B @ vv)), Rp.apply(E.apply(vv)), B @ vv, vv]
            for name, value in zip(expressions, values):
                predictions[name].append(value)
            q.append(qq); vel.append(vv); reference.append(ref)
            relative.append(Rp.inv() * Rc); parent_rotations.append(Rp)
        q, vel, reference = map(np.array, (q, vel, reference))
        mask = np.linalg.norm(vel, axis=1) > .01
        refmask = np.linalg.norm(reference, axis=1) > .01
        errors = {name: np.array(values) - reference for name, values in predictions.items()}
        for name, error in errors.items():
            pooled[name].append(error)
        pooled_masks.append(mask)
        ranking = sorted(expressions, key=lambda name: metrics(errors[name], mask)['vector_RMS_rad_s'])
        fdq, fdw, predicted_qdot = [], [], []
        for i in range(1, len(trace) - 1):
            dt = times[i+1] - times[i-1]
            fdq.append((q[i+1] - q[i-1]) / dt)
            omega_parent_fd = (relative[i+1] * relative[i-1].inv()).as_rotvec() / dt
            fdw.append(parent_rotations[i].apply(omega_parent_fd))
            implied_parent = parent_rotations[i].inv().apply(reference[i])
            predicted_qdot.append(np.linalg.solve(B, np.linalg.solve(left_jacobian(B @ q[i]), implied_parent)))
        fdq, fdw, predicted_qdot = map(np.array, (fdq, fdw, predicted_qdot))
        interior_mask = mask[1:-1]
        child_implied_qdot = np.array([
            np.linalg.solve(B, np.linalg.solve(left_jacobian(B @ q[i]),
                relative[i].apply(B @ vel[i])))
            for i in range(1, len(trace) - 1)])
        worst = int(np.argmax(np.linalg.norm(errors['child_Bv'], axis=1)))
        summary['groups'][group] = {
            'parent_body': parents[group], 'joint_indices': indices, 'body_index': child_index,
            'B': B.tolist(), 'nontrivial_count': int(mask.sum()),
            'reference_nontrivial_count': int(refmask.sum()),
            'native_velocity_norm_RMS_rad_s': float(np.sqrt(np.mean(np.sum(vel[mask]**2, axis=1)))),
            'reference_norm_RMS_rad_s': float(np.sqrt(np.mean(np.sum(reference[mask]**2, axis=1)))),
            'ranking': ranking,
            'candidate_metrics_native_v_mask': {name: metrics(error, mask) for name, error in errors.items()},
            'candidate_metrics_reference_mask': {name: metrics(error, refmask) for name, error in errors.items()},
            'child_Bv_max_error_snapshot': {
                'time_s': float(times[worst]), 'q': q[worst].tolist(), 'native_v': vel[worst].tolist(),
                'measured_relative_omega_W': reference[worst].tolist(),
                'predicted_relative_omega_W': predictions['child_Bv'][worst].tolist(),
            },
            'finite_difference': {
                'native_v_as_qdot_error': metrics(vel[1:-1] - fdq, interior_mask),
                'qdot_implied_by_same_snapshot_omega_vs_native_v_error': metrics(predicted_qdot - vel[1:-1], interior_mask),
                'qdot_implied_by_same_snapshot_omega_vs_FD_q_error': metrics(predicted_qdot - fdq, interior_mask),
                'qdot_implied_by_child_Bv_vs_FD_q_error': metrics(child_implied_qdot - fdq, interior_mask),
                'relative_rotation_FD_world_vs_same_snapshot_omega_error': metrics(fdw-reference[1:-1], interior_mask),
                'relative_rotation_FD_vs_candidates': {name: metrics(fdw-np.array(predictions[name])[1:-1], interior_mask) for name in expressions},
            },
        }
    mask = np.concatenate(pooled_masks)
    summary['pooled_nontrivial_metrics'] = {name: metrics(np.concatenate(values), mask)
                                           for name, values in pooled.items()}
    summary['derived_chart_velocity_expression_not_force_contract'] = (
        'If child-local Bv describes relative angular tangent and the verified R_rel(q)=Exp(Bq) C0 '
        'chart holds, then dq/dt = B^-1 J_left(Bq)^-1 R_rel(q) B v_native. '
        'When C0=I, this simplifies to B^-1 J_right(Bq)^-1 Bv_native, J_right(phi)=J_left(-phi). '
        'The central-FD comparison evaluates this derivation only; no torque/Jacobian duality certification.')
    summary['limitations'] = [
        'DOF v와dq/dt 또는 Cartesian tangent의일치여부는이raw에서수치로만판별. torque/Jacobian dual mapping 등가성은검증하지않음.',
        '부모와자식각속도차이는동일worldframe의실제snapshot양. COM/origin선형속도문제와관계없는각속도비교.',
        'central FD는30Hz저장간격(.033333초),양옆총.066667초구간평균. 고주파응답/접촉급변/시점오차때문에snapshot검사보다약한증거.',
        '공개getter의native velocity contract를확정하거나다른asset/run으로일반화하지않음.',
    ]
    after = {str(path): sha(path) for path in INPUTS}
    assert before == after
    summary['input_sha256_unchanged'] = True
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    for group, item in summary['groups'].items():
        best = item['ranking'][0]
        mm = item['candidate_metrics_native_v_mask'][best]
        print(group, 'n', item['nontrivial_count'], 'best', best,
              'RMS/max', mm['vector_RMS_rad_s'], mm['max_vector_error_rad_s'],
              'v=qdot FD RMS', item['finite_difference']['native_v_as_qdot_error']['vector_RMS_rad_s'])
    print('pooled', summary['pooled_nontrivial_metrics'])


if __name__ == '__main__':
    main()
