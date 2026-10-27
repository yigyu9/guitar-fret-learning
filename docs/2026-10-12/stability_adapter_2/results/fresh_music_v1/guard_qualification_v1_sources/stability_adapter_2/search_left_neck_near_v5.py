"""Fit only left33 around current neck with small noncontact face gaps."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
from .initial_pose_noise_v1 import read, save, sha, pose
from .upper_arm_static_geometry_v1 import ROOT, ASSET, calibrated_upper_fk, state_from_fk
from .realistic_guitar_geometry_v1 import source_scene, source_audit
from .initial_overlap import build_probe, mujoco
from .face_referenced_geometry import face_geometry
from .left_neck_near_geometry_v1 import FACETS, left_indices, face_measurements

A = ROOT/'stability_adapter_2'
D = ROOT/'docs/2026-10-19/stability_adapter_2'
P = D/'results/left_neck_near_initial_v1'
CFG = D/'results/shoulder_forward_v1/search_v2/shoulder_forward10mm/config.json'
BASE = D/'results/shoulder_forward_v1/native_v2/shoulder_forward10mm/initial_values.json'
OLD = P/'search_v4/station20mm_audit.json'
PLAN = A/'LEFT_NECK_NEAR_INITIAL_PLAN_V5.md'


def hull(vertices):
    equations = ConvexHull(vertices).equations
    return equations[np.unique(np.round(equations, 10), axis=0, return_index=True)[1]]


def separating_gap(a, ae, b, be):
    axis_gap = max((b.min(0)-a.max(0)).max(), (a.min(0)-b.max(0)).max())
    if axis_gap >= .002: return float(axis_gap)
    return max(np.min(a@be[:, :3].T+be[:, 3], axis=0).max(),
               np.min(b@ae[:, :3].T+ae[:, 3], axis=0).max())


def main():
    from .environment_contract_v1 import EnvironmentContract
    c = EnvironmentContract(CFG); cfg = read(CFG); seed = read(cfg['initial_candidate'])
    base = read(BASE); names, bodies = base['joint_names'], base['human_body_names']
    q0 = np.array(seed['joint_angles_rad']); state = base['native_initial_state']
    fk, parents = calibrated_upper_fk(names, bodies, state, q0)
    gp, gr = pose(state['guitar_body_states'][0]); geometry = read(A/'assets/om_body_geometry_v3/manifest.json')
    scene = source_scene(state, bodies, geometry['asset']); model, data, shapes = build_probe(scene)
    meshes = {s['geom_id']: face_geometry(model, data, s) for s in shapes}
    facets = read(FACETS)['facets']; left = left_indices(names)
    frozen = np.ones(81, dtype=bool); frozen[left] = False
    lo, hi = c.lower[left]+1e-6, c.upper[left]-1e-6
    old = read(OLD); assert len(old['joint_angles_rad']) == len(names)
    start = q0.copy(); start[left] = np.array(old['joint_angles_rad'])[left]
    locals_, necks = {}, []
    front_z = .0093
    for shape in shapes:
        vertices = meshes[shape['geom_id']].vertices
        if shape['actor'] == 'human' and shape['body'].startswith(('L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist', 'LH:')):
            locals_[shape['geom_id']] = (shape['body'],)
        if shape['actor'] == 'guitar':
            v = gr.inv().apply(vertices-gp)
            if shape['body'] == 'guitar': necks.append(shape['geom_id'])
            near = v[(v[:, 1] > -.08)&(v[:, 1] < .16)&(np.abs(v[:, 0]) < .032)]
            if len(near): front_z = max(front_z, float(near[:, 2].max()))
    body_ids = {n: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'human/'+n)
                for n, in locals_.values()}
    witness = np.zeros(6)
    def proxy_gap(a, b):
        # Static source query used only for optimization. Final mesh LP audit is independent.
        return float(mujoco.mj_geomDistance(model, data, a, b, .004, witness))
    def tree_distance(a, b):
        chain = [a]
        while a in parents: a = parents[a]; chain.append(a)
        steps = 0
        while b not in chain and b in parents: b = parents[b]; steps += 1
        return steps+chain.index(b) if b in chain else 99
    hand = [g for g, (n,) in locals_.items() if n.startswith('LH:')]
    pairs = [(a, b) for j, a in enumerate(hand) for b in hand[j+1:]
             if tree_distance(locals_[a][0], locals_[b][0]) > 2]
    other_human = [shape for shape in shapes if shape['actor'] == 'human' and shape['geom_id'] not in locals_]
    arm_pairs = [(g, shape['geom_id']) for g, (n,) in locals_.items() for shape in other_human
                 if tree_distance(n, shape['body']) > 2]
    paths = [Path(__file__).resolve(), PLAN, BASE, CFG, OLD, FACETS, ASSET,
             A/'assets/om_body_geometry_v3/manifest.json', Path(geometry['asset'])]
    paths += list(A.glob('*.py'))+[Path(m['path']) for m in geometry['meshes']]
    inputs = {str(p): sha(p) for p in paths}; inputs.update(c.inputs)
    out = P/'search_v5'; out.mkdir(parents=True, exist_ok=False); save(out/'inputs_before.json', inputs)
    rows, selected = [], []
    for station in (.02, .06):
        print('starting station', station, flush=True)
        def evaluate(v, details=False, collision_weight=1.):
            q = q0.copy(); q[left] = v; poses = fk(q)
            measures = face_measurements(poses, gp, gr, station, front_z, facets)
            residual = []
            for n, m in measures.items():
                residual.extend(1000*(np.array(m['point_G_m'])-m['target_G_m']))
                residual.extend((18 if n in ('LH:palm', 'LH:thumb3') else 6)*
                                (np.array(m['facet_normal_G'])+m['outward_normal_G']))
            for n, body_id in body_ids.items():
                p, r = poses[n]
                model.body_pos[body_id] = p
                qxyzw = r.as_quat(); model.body_quat[body_id] = qxyzw[[3, 0, 1, 2]]
            mujoco.mj_kinematics(model, data)
            for geom in locals_:
                for neck in necks:
                    residual.append(collision_weight*8000*max(0., .002-proxy_gap(geom, neck)))
            for a, b in pairs:
                residual.append(collision_weight*25000*max(0., .0005-proxy_gap(a, b)))
            for a, b in arm_pairs:
                residual.append(collision_weight*25000*max(0., .001-proxy_gap(a, b)))
            residual.append(30*max(0., -measures['LH:palm']['normal_up_W']))
            residual.extend(.3*(v-start[left]))
            return (np.array(residual), measures, poses) if details else np.array(residual)
        fit = least_squares(evaluate, np.clip(start[left], lo+1e-8, hi-1e-8),
                            bounds=(lo, hi), max_nfev=160, diff_step=1e-4)
        q = q0.copy(); q[left] = fit.x; q = q.astype(np.float32).astype(float)
        residual, measures, poses = evaluate(q[left], True)
        predicted = state_from_fk(state, bodies, q, fk)
        audit = source_audit(source_scene(predicted, bodies, geometry['asset']), parents)
        eligible = bool(audit['source_clear'] and np.array_equal(q[frozen], q0[frozen]) and
                        all(m['point_target_error_m'] < .015 and m['facet_signed_plane_gap_m'] > .002 and
                            m['alignment_dot'] > .3 for m in measures.values()) and
                        measures['LH:palm']['normal_up_W'] > 0)
        label = 'station%02dmm'%int(station*1000)
        row = {'label': label, 'accepted_for_native': eligible, 'joint_angles_rad': q.tolist(),
               'source_audit': audit, 'face_measurements': measures, 'station_G_m': station,
               'front_z_G_m': front_z, 'frozen48_exact': bool(np.array_equal(q[frozen], q0[frozen])),
               'joint_delta_rad': {names[i]: float(q[i]-q0[i]) for i in left},
               'fit_cost': float(fit.cost), 'fit_nfev': int(fit.nfev)}
        rows.append(row); save(out/(label+'_audit.json'), row)
        print(label, 'accepted', eligible, 'gap mm', [round(m['facet_signed_plane_gap_m']*1000, 3) for m in measures.values()],
              'error mm', [round(m['point_target_error_m']*1000, 3) for m in measures.values()], flush=True)
        if eligible:
            folder = out/label; folder.mkdir()
            candidate = {**seed, 'joint_angles_rad': q.tolist(), 'left_neck_near': row,
                         'predicted_human_poses': {n: {'p': p.tolist(), 'q': r.as_quat().tolist()} for n, (p, r) in poses.items()}}
            save(folder/'candidate.json', candidate)
            save(folder/'config.json', {**cfg, 'initial_candidate': str(folder/'candidate.json'),
                                       'initial_candidate_sha256': sha(folder/'candidate.json')})
            selected.append({'label': label, 'config': str(folder/'config.json')})
    assert all(sha(Path(p)) == h for p, h in inputs.items())
    save(out/'search.json', {'input_sha256': inputs, 'rows': rows, 'selected': selected,
                            'scope': 'source calibrated FK/static geometry query proposal plus final independent full convex-mesh LP audit; not native physics; initial native verification pending', 'native_runs': 0})


if __name__ == '__main__': main()
