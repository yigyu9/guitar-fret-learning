"""Re-evaluate preserved FK proposals using only face-referenced neck vertices."""
import json
from pathlib import Path
from types import SimpleNamespace

from .audit_palm_side_target import PHASE, PROPOSAL, closest_polygon
from .search_palm_neck_side import REFERENCE
from .environment import ROOT,np
from .build_fixed_lower_asset import read,sha,pose
from .replay_contact_geometry import recorded_probe
from .render_best_run_video import set_saved_pose
from .face_referenced_geometry import face_geometry
from .plot_neck_palm import geometry
from .pose_strap_inputs import pose_metrics
from .thigh_palm_support import intersection
from scipy.spatial.transform import Rotation
import mujoco


def main():
    out=PHASE/'face_audit';out.mkdir(exist_ok=False)
    source_path=PHASE/'fk_search/search.json';audit_path=PHASE/'initial_audit_v2/audit.json'
    source,audit=read(source_path),read(audit_path)
    report=read(REFERENCE/'report.json')
    files=[Path(__file__).resolve(),source_path,audit_path,PROPOSAL,REFERENCE/'report.json',REFERENCE/'states.json']
    files += [Path(p) for p in audit['input_sha256']]
    files += [Path(__file__).with_name(n) for n in ('face_referenced_geometry.py','search_palm_neck_side.py',
        'thigh_palm_support.py','replay_contact_geometry.py','render_best_run_video.py','plot_neck_palm.py',
        'pose_strap_inputs.py','initial_overlap.py','build_fixed_lower_asset.py')]
    hashes={str(p):sha(p) for p in files}
    model,data,shapes=recorded_probe(REFERENCE,0)
    rows=[];neck_geometry=[]
    for candidate in source['rows']:
        state=candidate['source_state']
        set_saved_pose(model,mujoco,report,state);mujoco.mj_forward(model,data)
        meshes={s['geom_id']:face_geometry(model,data,s) for s in shapes}
        overlaps=[];crosshands=[]
        for a in [s for s in shapes if s['actor']=='human']:
            for b in [s for s in shapes if s['actor']=='guitar']:
                radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
                if radius>1e-7:overlaps.append({'human':a['body'],'guitar':b['body'],'common_radius_m':radius})
        for a in [s for s in shapes if s['body'].startswith('LH:') or s['body']=='L_Wrist']:
            for b in [s for s in shapes if s['body'].startswith('RH:') or s['body']=='R_Wrist']:
                radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
                if radius>1e-7:crosshands.append({'left':a['body'],'right':b['body'],'common_radius_m':radius})
        palm=meshes[next(s['geom_id'] for s in shapes if s['body']=='LH:palm')]
        gap=closest_polygon(palm,np.array(audit['target_polygon_W_m']))
        row={'name':candidate['name'],'settings_path':candidate['settings_path'],
            'settings_sha256':sha(Path(candidate['settings_path'])),
            'source_hull_to_blue_polygon':gap,'face_used_intersections':overlaps,'cross_hand_intersections':crosshands,
            'all_vertex_intersections_preserved':candidate['source_intersections'],
            'face_used_clear':not overlaps and not crosshands,
            'hand_proxy_from_preserved_candidate':candidate['hand'],
            'scope':'face-used source geometry, not a native admission gate or cooked contact certification'}
        rows.append(row)
        print(json.dumps(row,indent=2),flush=True)
    gp,gq=pose(audit['initial_state']['guitar_body_states'][0]);gr=Rotation.from_quat(gq)
    for s in [s for s in shapes if s['actor']=='guitar' and s['body']=='guitar']:
        geom=s['geom_id'];mesh_id=model.geom_dataid[geom]
        used=face_geometry(model,data,s);all_vertices=geometry(model,data,s)
        neck_geometry.append({'geom_id':geom,'compiled_all_vertex_count':int(model.mesh_vertnum[mesh_id]),
            'compiled_face_used_vertex_count':int(len(np.unique(model.mesh_face[model.mesh_faceadr[mesh_id]:model.mesh_faceadr[mesh_id]+model.mesh_facenum[mesh_id]]))),
            'face_used_bounds_G_m':[gr.inv().apply(used.vertices-gp).min(0).tolist(),gr.inv().apply(used.vertices-gp).max(0).tolist()],
            'all_vertex_bounds_G_m':[gr.inv().apply(all_vertices.vertices-gp).min(0).tolist(),gr.inv().apply(all_vertices.vertices-gp).max(0).tolist()]})
    checks={'inputs_unchanged':all(sha(Path(p))==h for p,h in hashes.items()),
            'distinct_face_used_neck_bounds':neck_geometry[0]['face_used_bounds_G_m']!=neck_geometry[1]['face_used_bounds_G_m']}
    (out/'audit.json').write_text(json.dumps({'checks':checks,'rows':rows,'neck_source_geometry':neck_geometry,
        'input_sha256':hashes,'native_initializations':0,'physics_steps':0,
        'scope':'post-hoc helper seal and new face-used comparison; not evidence of previously absent production hashes'},indent=2,allow_nan=False)+'\n')
    if not all(checks.values()):raise AssertionError(checks)


if __name__=='__main__':main()
