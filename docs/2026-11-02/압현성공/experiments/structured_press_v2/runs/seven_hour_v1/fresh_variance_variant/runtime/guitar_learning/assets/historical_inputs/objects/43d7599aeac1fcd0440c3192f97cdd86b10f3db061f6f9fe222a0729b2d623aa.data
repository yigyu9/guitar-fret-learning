"""Source-only palm/thumb initial search; native contact remains unverified."""
import argparse
import copy
from pathlib import Path
from scipy.spatial import ConvexHull
from scipy.optimize import least_squares
from .underneck_pose_trial_v5 import read, save, pose, calibrated_fk
from .underneck_initial_search import source_scene, BASE, FACETS
from .initial_overlap import build_probe
from .face_referenced_geometry import face_geometry
from .palm_side_source_checks import intersection
from .environment import np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=False)
    candidate = read(args.candidate); initial = read(args.native/'initial_values.json')
    state = initial['native_initial_state']; names = initial['joint_names']
    bodies = read(BASE)['human_body_names']; q0 = np.array(initial['initial_angles_rad'])
    fk, parents = calibrated_fk(names, bodies, state, q0)
    gp, gr = pose(state['guitar_body_states'][0])
    scene, _ = source_scene(state, read(BASE), gp, gr)
    model, data, shapes = build_probe(scene)
    meshes = {s['geom_id']: face_geometry(model, data, s) for s in shapes}
    moving = [s for s in shapes if s['actor']=='human' and
              s['body'].startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:'))]
    local = {}
    for s in moving:
        p, r = pose(state['human_body_states'][bodies.index(s['body'])])
        v = r.inv().apply(meshes[s['geom_id']].vertices-p)
        local[s['geom_id']] = (s['body'], v, ConvexHull(v).equations)
    static = {s['geom_id']: (meshes[s['geom_id']].vertices,
              ConvexHull(meshes[s['geom_id']].vertices).equations) for s in shapes}
    def distance(a, b):
        chain = []; c = a
        while c in parents: chain.append(c); c = parents[c]
        chain.append(c); steps = 0; c = b
        while c not in chain and c in parents: steps += 1; c = parents[c]
        return steps+chain.index(c) if c in chain else 99
    pairs = [(a,b) for a in moving for b in shapes if b['actor']=='guitar' or
             (b['actor']=='human' and distance(a['body'],b['body'])>2 and
              (b not in moving or a['geom_id']<b['geom_id']))]
    indices = np.array([i for i,n in enumerate(names) if
              n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:thumb'))])
    facets = read(FACETS)['facets']; targets = {}; normals = {}
    for n in ('LH:palm','LH:thumb3'):
        p, r = fk(q0)[n]; point = gr.inv().apply(p+r.apply(facets[n]['point_local_m'])-gp)
        y = float(np.clip(point[1],candidate['station_G_m']-.04,candidate['station_G_m']+.04))
        width = .027908-.01631590413943356*(y+.241803)
        normal = np.array([1.,.01631590413943356,0.]) if n=='LH:palm' else np.array([0.,0.,-1.])
        normal /= np.linalg.norm(normal); normals[n] = normal
        target = np.array([width,y,-.003]) if n=='LH:palm' else np.array([np.clip(point[0],-width,width),y,-.008])
        targets[n] = target+normal*(.00005 if n=='LH:palm' else .00002)
    def transformed(q):
        poses = fk(q); geometry = dict(static)
        for geom,(n,v,e) in local.items():
            p,r = poses[n]; v = p+r.apply(v); normal = r.apply(e[:,:3])
            geometry[geom] = (v,np.column_stack((normal,e[:,3]-normal@p)))
        return poses,geometry
    rows = []
    for width in (.025,.1,.3):
        lo = np.maximum(initial['native_lower_rad'],q0-width)[indices]
        hi = np.minimum(initial['native_upper_rad'],q0+width)[indices]
        def residual(v):
            q = q0.copy(); q[indices] = v; poses,geometry = transformed(q); values = []
            for n in targets:
                p,r = poses[n]; facet = facets[n]
                point = gr.inv().apply(p+r.apply(facet['point_local_m'])-gp)
                normal = gr.inv().apply(r.apply(facet['normal_local']))
                values.extend(1000*(point-targets[n]))
                values.extend((15 if n=='LH:palm' else 4)*(normal+normals[n]))
            for a,b in pairs:
                av,ae = geometry[a['geom_id']]; bv,be = geometry[b['geom_id']]
                if np.any(np.minimum(av.max(0),bv.max(0))<np.maximum(av.min(0),bv.min(0))):
                    values.append(0.); continue
                gap = max(np.min(av@be[:,:3].T+be[:,3],axis=0).max(),
                          np.min(bv@ae[:,:3].T+ae[:,3],axis=0).max())
                values.append(50000*max(0.,.00001-gap))
            up = poses['LH:palm'][1].apply(facets['LH:palm']['normal_local'])[2]
            values.append(100*max(0.,-up)); values.extend(.2*(v-q0[indices]))
            return values
        fit = least_squares(residual,np.clip(q0[indices],lo+1e-9,hi-1e-9),
                            bounds=(lo,hi),max_nfev=100)
        q = q0.copy(); q[indices] = fit.x; poses,geometry = transformed(q)
        moved = dict(meshes)
        for s in moving:
            mesh = meshes[s['geom_id']].copy(); mesh.vertices = geometry[s['geom_id']][0]
            moved[s['geom_id']] = mesh
        overlaps = []
        for a,b in pairs:
            rad = intersection(moved[a['geom_id']],moved[b['geom_id']])
            if rad>1e-7: overlaps.append(dict(a=a['body'],b=b['body'],actor_b=b['actor'],radius_m=rad))
        errors = {}
        for n in targets:
            p,r = poses[n]; point = gr.inv().apply(p+r.apply(facets[n]['point_local_m'])-gp)
            errors[n] = float(np.linalg.norm(point-targets[n]))
        row = copy.deepcopy(candidate)
        row.update(joint_angles_rad=q.tolist(),predicted_human_poses={n:dict(p=p.tolist(),q=r.as_quat().tolist()) for n,(p,r) in poses.items()},
                   palm_thumb_search=dict(width_rad=width,fit_success=bool(fit.success),nfev=fit.nfev,
                   targets_G_m={n:v.tolist() for n,v in targets.items()},point_errors_m=errors,
                   source_intersections=overlaps,palm_up=float(poses['LH:palm'][1].apply(facets['LH:palm']['normal_local'])[2]),
                   only_left17_changed=bool(np.array_equal(q[np.setdiff1d(np.arange(len(q)),indices)],q0[np.setdiff1d(np.arange(len(q)),indices)]))))
        path = args.out/('candidate_'+str(width).replace('.','p')+'.json'); save(path,row)
        rows.append(dict(path=str(path.resolve()),**row['palm_thumb_search']))
        print('source candidate',width,'errors',errors,'overlaps',len(overlaps),flush=True)
    save(args.out/'report.json',dict(rows=rows,physics_steps=0,native_initializations=0,
                                   scope='source geometry; actual native contacts required'))


if __name__=='__main__': main()
