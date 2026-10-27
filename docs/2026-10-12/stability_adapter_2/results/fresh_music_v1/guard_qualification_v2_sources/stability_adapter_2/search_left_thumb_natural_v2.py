"""Change only thumb5; keep current palm/four fingers and six-joint strike seat."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares
from .initial_pose_noise_v1 import read, save, sha, pose
from .upper_arm_static_geometry_v1 import calibrated_upper_fk, state_from_fk, ROOT, ASSET
from .realistic_guitar_geometry_v1 import source_scene, source_audit
from .initial_overlap import build_probe
from .face_referenced_geometry import face_geometry
from .left_neck_near_geometry_v1 import FACETS, width
from .search_left_neck_near_v1 import hull, separating_gap

A = ROOT/'stability_adapter_2'
D = ROOT/'docs/2026-10-19/stability_adapter_2'
E = D/'results/elbow_wrist_ready_pose_v1'
P = D/'results/left_thumb_natural_v1'
BASE = E/'native_pick_feedback_v1/initial_values.json'
CFG = E/'native_configs_v1/strike.json'
PLAN = A/'LEFT_THUMB_NATURAL_PLAN_V2.md'


def main():
    from .environment_contract_v1 import EnvironmentContract
    out = P/'search_v2'; out.mkdir(parents=True,exist_ok=False)
    manifest = A/'assets/om_body_geometry_v3/manifest.json'
    anchors = [Path(__file__).resolve(),PLAN,BASE,CFG,FACETS,ASSET,manifest,A/'config.json',
               ROOT/'docs/2026-08-19/정리.txt',ROOT/'docs/2026-08-19/fret_joint_limits/joint_limit_ranges.csv']+list(A.glob('*.py'))
    discovery = {str(p.resolve()):sha(p) for p in anchors}
    save(out/'discovery_before.json',discovery)
    cfg = read(CFG); geometry = read(manifest)
    assets = (ASSET,Path(geometry['asset']))
    asset_before = {str(p.resolve()):sha(p) for p in assets}
    save(out/'XML_discovery_before.json',asset_before)
    paths = anchors+[Path(cfg['initial_candidate']),Path(cfg['native_reference'])]+list(assets)+[Path(m['path']) for m in geometry['meshes']]
    for asset in assets:
        xml=ET.parse(asset).getroot();meshdir=(asset.parent/xml.find('compiler').get('meshdir')).resolve()
        paths += [(meshdir/m.get('file')).resolve() for m in xml.findall('./asset/mesh')]
    inputs = {str(p.resolve()):sha(p) for p in paths}
    assert all(inputs[p]==h for p,h in discovery.items()) and all(inputs[p]==h for p,h in asset_before.items())
    save(out/'inputs_before.json',inputs)
    contract=EnvironmentContract(CFG);assert all(inputs[p]==h for p,h in contract.inputs.items())
    seed=read(cfg['initial_candidate']);baseline=read(BASE);state=baseline['native_initial_state']
    names,bodies=baseline['joint_names'],baseline['human_body_names'];q0=np.array(baseline['q_ref_rad'])
    assert np.array_equal(q0,seed['joint_angles_rad'])
    thumb=np.array([i for i,n in enumerate(names) if n.startswith('LH:thumb')]);assert len(thumb)==5
    fixed=np.ones(81,dtype=bool);fixed[thumb]=False
    fk,parents=calibrated_upper_fk(names,bodies,state,q0);gp,gr=pose(state['guitar_body_states'][0])
    model, data, shapes = build_probe(source_scene(state, bodies, geometry['asset']))
    meshes = {s['geom_id']:face_geometry(model,data,s).vertices for s in shapes}
    moving, obstacles = [], []
    for s in shapes:
        vertices = meshes[s['geom_id']]
        if s['actor'] == 'human' and s['body'].startswith('LH:thumb'):
            p,r = pose(state['human_body_states'][bodies.index(s['body'])])
            moving.append((s['body'],r.inv().apply(vertices-p)))
        elif (s['actor'] == 'guitar' and s['body'] == 'guitar') or (s['actor'] == 'human' and s['body'].startswith(('LH:index','LH:middle','LH:ring','LH:pinky'))):
            v = gr.inv().apply(vertices-gp); obstacles.append((v,hull(v)))
    facet = read(FACETS)['facets']['LH:thumb3']
    def measure(poses):
        p,r = poses['LH:thumb3']; point = gr.inv().apply(p+r.apply(facet['point_local_m'])-gp)
        normal = gr.inv().apply(r.apply(facet['normal_local']))
        return point,normal
    original = fk(q0); old_point,old_normal = measure(original)
    palm = gr.inv().apply(original['LH:palm'][0]-gp)
    station = float(np.clip(old_point[1],-.18,.12))
    lo = contract.lower[thumb]+1e-6; hi = contract.upper[thumb]-1e-6
    hi[3] = min(hi[3],np.deg2rad(65)); hi[4] = min(hi[4],np.deg2rad(35))
    lo[1] = max(lo[1],np.deg2rad(-75)); lo[4] = max(lo[4],0.)
    hi[0] = min(hi[0],np.deg2rad(35)); hi[2] = min(hi[2],np.deg2rad(75))
    preferred = np.deg2rad([13,-45,35,45,10])
    rows = []
    for label,gap in [('back16mm',.016),('back24mm',.024)]:
        target = np.array([np.clip(old_point[0],-width(station)+.004,width(station)-.004),station,-.008-gap])
        def evaluate(v):
            q = q0.copy(); q[thumb] = v; poses = fk(q); point,normal = measure(poses)
            residual = list(400*(point-target)) + list(4*(normal-np.array([0,0,1.])))
            residual.extend(8*(v-preferred))
            for body,local in moving:
                p,r = poses[body]; vertices = gr.inv().apply(p+r.apply(local)-gp); equations = hull(vertices)
                for ov,oe in obstacles:
                    residual.append(5000*max(0.,.001-separating_gap(vertices,equations,ov,oe)))
            return np.array(residual)
        fits = [least_squares(evaluate,np.clip(start,lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=120,diff_step=1e-4)
                for start in (preferred,q0[thumb])]
        fit = min(fits,key=lambda f:f.cost); q = q0.copy(); q[thumb] = fit.x.astype(np.float32).astype(float)
        poses = fk(q); point,normal = measure(poses)
        predicted = state_from_fk(state,bodies,q,fk)
        audit = source_audit(source_scene(predicted,bodies,geometry['asset']),parents)
        other_pose_exact = all(np.array_equal(poses[n][0],original[n][0]) and np.array_equal(poses[n][1].as_quat(),original[n][1].as_quat()) for n in bodies if not n.startswith('LH:thumb'))
        accepted = bool(audit['source_clear'] and np.array_equal(q[fixed],q0[fixed]) and other_pose_exact and
                        np.linalg.norm(point-target)<.027 and point[2]<-.010 and normal[2]>.05)
        row = {'label':label,'accepted_for_native':accepted,'joint_angles_rad':q.tolist(),'source_audit':audit,
               'other76_initial_angles_exact':bool(np.array_equal(q[fixed],q0[fixed])),'nonthumb_initial_poses_exact':other_pose_exact,
               'thumb_scalar_deg':dict(zip([names[i] for i in thumb],np.rad2deg(q[thumb]).tolist())),
               'original_thumb_scalar_deg':dict(zip([names[i] for i in thumb],np.rad2deg(q0[thumb]).tolist())),
               'facet_point_G_m':point.tolist(),'facet_normal_G':normal.tolist(),'target_G_m':target.tolist(),
               'point_target_error_m':float(np.linalg.norm(point-target)),'thumb_back_plane_gap_m':float(-.008-point[2]),
               'original_facet_point_G_m':old_point.tolist(),'palm_origin_G_m':palm.tolist(),'fit_cost':float(fit.cost)}
        rows.append(row); save(out/(label+'_audit.json'),row)
        print(label,'accepted',accepted,'degrees',row['thumb_scalar_deg'],'back_gap_mm',row['thumb_back_plane_gap_m']*1000,flush=True)
        if accepted:
            folder = out/label; folder.mkdir()
            candidate = {**seed,'joint_angles_rad':q.tolist(),'left_thumb_natural':row,
                         'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in poses.items()}}
            save(folder/'candidate.json',candidate)
            save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),
                                      'initial_candidate_sha256':sha(folder/'candidate.json')})
    assert all(sha(p)==h for p,h in inputs.items())
    save(out/'report.json',{'input_sha256':inputs,'rows':rows,'scope':'thumb5 only; source facet identity and convex audits, not anatomical certification or native contact proof'})


if __name__ == '__main__': main()
