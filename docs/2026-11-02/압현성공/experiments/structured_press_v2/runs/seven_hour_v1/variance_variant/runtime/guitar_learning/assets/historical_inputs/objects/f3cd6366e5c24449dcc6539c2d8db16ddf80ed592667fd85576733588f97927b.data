"""Read-only position-coordinate tangent correction of saved initial FK probes."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def left_expmap_tangent(q):
    """SO(3) left Jacobian: rotation-vector rate -> spatial angular rate."""
    q = np.asarray(q, dtype=float)
    x, y, z = q
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    theta2 = float(q @ q)
    if theta2 < 1e-8:
        a, b = .5 - theta2 / 24, 1 / 6 - theta2 / 120
    else:
        theta = np.sqrt(theta2)
        a, b = (1 - np.cos(theta)) / theta2, (theta - np.sin(theta)) / (theta2 * theta)
    return np.eye(3) + a * skew + b * skew @ skew


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--measurements', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve previous coordinate comparison')
    source_path = args.measurements / 'comparison.json'
    raw = json.loads(source_path.read_text())
    base_path = args.measurements / 'baseline.json'
    base = json.loads(base_path.read_text())
    if not all(raw['checks'].values()):
        raise ValueError('fresh FK contracts failed')
    if not all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in raw['input_sha256'].items()):
        raise ValueError('fresh FK consumed-source SHA mismatch')
    rows = raw['rows']
    native = np.column_stack([r['native_linear'] + r['native_angular'] for r in rows])
    corrected = native.copy()
    groups = []
    for k, name in zip(range(0, 12, 3), ('Thorax', 'Shoulder', 'Elbow', 'Wrist')):
        expected = ['L_' + name + '_' + axis for axis in ('x', 'y', 'z')]
        if [r['joint'] for r in rows[k:k+3]] != expected:
            raise ValueError('native three-coordinate block differs')
        q = np.array([base['initial_targets_rad'][r['dof_column']] for r in rows[k:k+3]])
        tangent = left_expmap_tangent(q)
        corrected[:, k:k+3] = native[:, k:k+3] @ tangent
        groups.append({'group': name, 'native_coordinate_vector_rad': q.tolist(),
            'left_expmap_tangent': tangent.tolist(),
            'native_angular_basis_orthogonality_error': float(np.abs(native[3:, k:k+3].T @ native[3:, k:k+3] - np.eye(3)).max())})
    source = np.array(base['source_center_world_m'])
    def source_jacobian(reference):
        x, y, z = source - np.array(base[reference])
        skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
        return corrected[:3] - skew @ corrected[3:]
    predictions = {'origin': corrected[:3], 'COM': corrected[:3], 'angular': corrected[3:],
        'source_from_origin': source_jacobian('palm_origin_world_m'), 'source_from_COM': source_jacobian('palm_com_world_m')}
    fields = {'origin': 'FD_origin_m_per_rad', 'COM': 'FD_COM_m_per_rad', 'angular': 'FD_angular_rad_per_rad',
        'source_from_origin': 'FD_source_m_per_rad', 'source_from_COM': 'FD_source_m_per_rad'}
    comparison = [{'joint': r['joint'], 'method': r['method'], **{name + '_error': float(np.linalg.norm(np.array(r[field]) - predictions[name][:, k])) for name, field in fields.items()}} for k, r in enumerate(rows)]
    maxima = {name: max(r[name + '_error'] for r in comparison) for name in fields}
    paths = [source_path, base_path, Path(__file__).resolve()] + [Path(p) for p in raw['input_sha256']]
    root = Path(__file__).resolve().parents[1]
    paths += [root / 'isaacgym/python/examples/spherical_joint.py', root / 'related_work/guitar/ref_motion.py', root / 'related_work/guitar/utils.py']
    result = {'scope': 'empirical current initial left-arm position-coordinate derivative correction; not runtime/control/stability certificate',
        'checks': {'fresh_FK_contracts': all(raw['checks'].values()), 'finite_corrected_J': bool(np.isfinite(corrected).all()),
            'COM_and_angular_errors_reduced': maxima['COM'] < raw['max_errors']['COM_error_m_per_rad'] and maxima['angular'] < raw['max_errors']['angular_error_rad_per_rad']},
        'groups': groups, 'rows': comparison, 'max_errors': maxima, 'corrected_native_J_at_COM': corrected.tolist(),
        'corrected_J_source_center': predictions['source_from_COM'].tolist(),
        'units': 'position errors m/rad; angular errors rad/rad; norms of 3-vector per column',
        'semantics': 'SDK example supports spherical position expmap; same-body MJCF importer conversion and native DOF velocity state meanings are not proven by that example. Current FK independently supports the tangent map and COM point at this initial pose.',
        'input_sha256': {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'checks': result['checks'], 'max_errors': maxima}, indent=2))
    if not all(result['checks'].values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
