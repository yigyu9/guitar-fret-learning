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
P = D/'results/left_neck_three_face_v1'
CFG = D/'results/left_thumb_natural_v1/search_v2/back24mm/config.json'
BASE = D/'results/left_thumb_natural_v1/native_v1/initial_values.json'
OLD = D/'results/left_neck_near_initial_v1/search_v1/station20mm_audit.json'
PLAN = A/'LEFT_NECK_THREE_FACE_PLAN_V1.md'


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
    import xml.etree.ElementTree as ET
    out=P/'search_v1';out.mkdir(parents=True,exist_ok=False)
    manifest=A/'assets/om_body_geometry_v3/manifest.json'
    anchors=[Path(__file__).resolve(),PLAN,BASE,CFG,OLD,FACETS,ASSET,manifest,A/'config.json',ROOT/'docs/2026-08-19/정리.txt']+list(A.glob('*.py'))
    discovery={str(p.resolve()):sha(p) for p in anchors};save(out/'discovery_before.json',discovery)
    cfg=read(CFG);geometry=read(manifest);assets=(ASSET,Path(geometry['asset']))
    xml_before={str(p.resolve()):sha(p) for p in assets};save(out/'XML_before.json',xml_before)
    paths=anchors+list(assets)+[Path(cfg['initial_candidate']),Path(cfg['native_reference'])]+[Path(m['path']) for m in geometry['meshes']]
    for asset in assets:
        xml=ET.parse(asset).getroot();meshdir=(asset.parent/xml.find('compiler').get('meshdir')).resolve()
        paths.extend((meshdir/m.get('file')).resolve() for m in xml.findall('./asset/mesh'))
    inputs={str(p.resolve()):sha(p) for p in paths}
    assert all(inputs[p]==h for p,h in discovery.items()) and all(inputs[p]==h for p,h in xml_before.items())
    save(out/'inputs_before.json',inputs)
    c=EnvironmentContract(CFG);assert all(inputs[p]==h for p,h in c.inputs.items())
    seed=read(cfg['initial_candidate']);base=read(BASE);names,bodies=base['joint_names'],base['human_body_names']
    q0=np.array(base['q_ref_rad']);assert np.array_equal(q0,seed['joint_angles_rad'])
    state=base['native_initial_state'];fk,parents=calibrated_upper_fk(names,bodies,state,q0);gp,gr=pose(state['guitar_body_states'][0])
    scene = source_scene(state, bodies, geometry['asset']); model, data, shapes = build_probe(scene)
    meshes = {s['geom_id']: face_geometry(model, data, s) for s in shapes}
    facets = read(FACETS)['facets']; left = left_indices(names)
    frozen = np.ones(81, dtype=bool); frozen[left] = False
    lo, hi = c.lower[left]+1e-6, c.upper[left]-1e-6
    for name,low,high in [('LH:thumb2',0,80),('LH:thumb3',0,55)]:
        j=list(left).index(names.index(name));lo[j]=max(lo[j],np.deg2rad(low));hi[j]=min(hi[j],np.deg2rad(high))
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
    rows, selected = [], []
    for station in (.02, .06):
        print('starting station', station, flush=True)
        def evaluate(v, details=False, collision_weight=1.):
            q = q0.copy(); q[left] = v; poses = fk(q)
            measures = face_measurements(poses, gp, gr, station, front_z, facets)
            for name,m in measures.items():
                gap=.004 if name in ('LH:palm','LH:thumb3') else .006
                m['target_gap_m']=gap;m['target_G_m']=(np.array(m['surface_G_m'])+gap*np.array(m['outward_normal_G'])).tolist()
                m['point_target_error_m']=float(np.linalg.norm(np.array(m['point_G_m'])-m['target_G_m']))
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
            for prefix in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'):
                indices=[names.index(prefix+'_'+axis) for axis in 'xyz']
                residual.append(80*max(0.,np.linalg.norm(q[indices])-np.deg2rad(155)))
            residual.append(2*(q[names.index('LH:thumb3')]-np.deg2rad(20)))
            residual.extend(.3*(v-start[left]))
            return (np.array(residual), measures, poses) if details else np.array(residual)
        fit = least_squares(evaluate, np.clip(start[left], lo+1e-8, hi-1e-8),
                            bounds=(lo, hi), max_nfev=120, diff_step=1e-4)
        q = q0.copy(); q[left] = fit.x; q = q.astype(np.float32).astype(float)
        residual, measures, poses = evaluate(q[left], True)
        predicted = state_from_fk(state, bodies, q, fk)
        audit = source_audit(source_scene(predicted, bodies, geometry['asset']), parents)
        eligible = bool(audit['source_clear'] and np.array_equal(q[frozen], q0[frozen]) and
                        all(m['point_target_error_m'] < .010 and .002 < m['facet_signed_plane_gap_m'] < .012 and
                            m['alignment_dot'] > .3 for m in measures.values()) and
                        measures['LH:palm']['normal_up_W'] > 0 and
                        all(np.linalg.norm(q[[names.index(prefix+'_'+axis) for axis in 'xyz']])<np.deg2rad(160) for prefix in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist')))
        label = 'station%02dmm'%int(station*1000)
        row = {'label': label, 'accepted_for_native': eligible, 'joint_angles_rad': q.tolist(),
               'source_audit': audit, 'face_measurements': measures, 'guitar_axes_W':{axis:gr.apply(vector).tolist() for axis,vector in [('underside',[1,0,0]),('back',[0,0,-1]),('strings_front',[0,0,1])]}, 'station_G_m': station,
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
