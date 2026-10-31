"""Calibrated arm/hand initial-pose search; source geometry, not dynamics."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation as R
from scipy.spatial import ConvexHull
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT/'docs/2026-10-12/stability_adapter_2/results'
BASE = RESULTS/'initial_middle3_alignment_v1/native/initial_values.json'
STATE = RESULTS/'horizontal_neck_initial_v1/native/initial_state.json'
POSE = RESULTS/'horizontal_neck_initial_v1/native/scene/candidate_001/pose.json'
FACETS = RESULTS/'multi_face_grip_v3/search.json'


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, d): Path(p).write_text(json.dumps(d, indent=2, allow_nan=False)+'\n')
def pose(d): return np.array([d['pose']['p'][a] for a in 'xyz']), R.from_quat([d['pose']['r'][a] for a in 'xyzw'])


def calibrated_fk(names, bodies, state, q0):
    xml = ET.parse(ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml').getroot()
    parents = {c.get('name'): p.get('name') for p in xml.iter('body') for c in p.findall('body')}
    original = {n: pose(s) for n, s in zip(bodies, state['human_body_states'])}
    rows = []
    for side in ('L', 'R'):
        limb = next(b for b in xml.iter('body') if b.get('name') == side+'_Thorax')
        for body in limb.iter('body'):
            n = body.get('name'); parent = parents[n]
            pp, pr = original[parent]; bp, br = original[n]
            joints = body.findall('joint'); idx = [names.index(j.get('name')) for j in joints]
            basis = np.column_stack([np.fromstring(j.get('axis'), sep=' ') for j in joints]) if joints else np.zeros((3, 0))
            rel = pr.inv()*br
            zero = R.from_rotvec(basis@q0[idx]).inv()*rel if idx else rel
            rows.append((n, parent, pr.inv().apply(bp-pp), zero, basis, idx))
    def fk(q):
        poses = dict(original)
        for n, parent, t, zero, basis, idx in rows:
            pp, pr = poses[parent]
            rel = R.from_rotvec(basis@q[idx])*zero if idx else zero
            poses[n] = (pp+pr.apply(t), pr*rel)
        return poses
    return fk, parents


def source_scene(state, base, gp, gr):
    state = copy.deepcopy(state)
    oldp, oldr = pose(state['guitar_body_states'][0])
    for s in state['guitar_body_states']:
        bp, br = pose(s)
        s['pose'] = {'p': dict(zip('xyz', (gp+gr.apply(oldr.inv().apply(bp-oldp))).tolist())),
                     'r': dict(zip('xyzw', (gr*oldr.inv()*br).as_quat().tolist()))}
    config = read(ROOT/'stability_adapter_2/config.json')
    config['humanoid_asset'] = 'stability_adapter_2/assets/humanoid_fixed_lower.xml'
    names = [base['human_body_names'], []]
    # Source body XML traversal is also the native order for this preserved asset.
    guitar_names = [b.get('name') for b in ET.parse(ROOT/config['guitar_asset']).getroot().findall('./worldbody//body')]
    if len(guitar_names) != len(state['guitar_body_states']):
        raise AssertionError('guitar body mapping length')
    names[1] = guitar_names
    gym = SimpleNamespace(get_actor_rigid_body_names=lambda env, actor: names[actor])
    return SimpleNamespace(config=config, human=0, guitar=1, env=None, gym=gym,
        bodies=lambda actor: state['human_body_states'] if actor==0 else state['guitar_body_states']), state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--arm-width', type=float, default=.6)
    parser.add_argument('--z-lift', type=float, default=0.)
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=False)
    from .environment import gymapi  # Load Gym before MuJoCo USD dependencies.
    from .initial_overlap import build_probe
    from .face_referenced_geometry import face_geometry
    from .palm_side_source_checks import intersection
    from .trial_settings import source_hashes
    import sys
    files = [Path(m.__file__) for n,m in sys.modules.items() if n.startswith('stability_adapter_2') and getattr(m,'__file__',None)]
    files += [Path(__file__).resolve(), BASE, STATE, POSE, FACETS, ROOT/'stability_adapter_2/UNDERNECK_INITIAL_BUILD.md', ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml']
    hashes = source_hashes(); hashes.update({str(p.resolve()):sha(p) for p in files})
    save(args.out/'attempt.json', {'input_sha256':hashes, 'arm_width_rad':args.arm_width, 'guitar_z_lift_m':args.z_lift,'native_initializations':0,'physics_steps':0})
    base, initial, guitar = read(BASE), read(STATE), read(POSE)
    names, bodies = base['human_joint_names'], base['human_body_names']
    q0 = np.array([s['pos'] for s in initial['human_dof_states']])
    fk, parents = calibrated_fk(names, bodies, initial, q0)
    gp = np.array(guitar['position_W_m']); gp[2] += args.z_lift
    gr = R.from_quat(guitar['quaternion_xyzw'])
    scene, gstate = source_scene(initial, base, gp, gr)
    probe = build_probe(scene); model, data, shapes = probe
    meshes = {s['geom_id']:face_geometry(model,data,s) for s in shapes}
    left = [s for s in shapes if s['body'].startswith('LH:') or s['body'] in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist')]
    guitar_shapes = [s for s in shapes if s['actor']=='guitar']
    neck = next(s for s in guitar_shapes if s['body']=='guitar' and gr.inv().apply(meshes[s['geom_id']].vertices-gp)[:,1].min()<0)
    nv = gr.inv().apply(meshes[neck['geom_id']].vertices-gp); ne = ConvexHull(nv).equations
    locals_ = {}
    for s in left:
        bp, br = pose(initial['human_body_states'][bodies.index(s['body'])])
        v = br.inv().apply(meshes[s['geom_id']].vertices-bp)
        locals_[s['geom_id']] = (s['body'], v, ConvexHull(v).equations)
    low, high = np.array(base['PD_properties']['lower']), np.array(base['PD_properties']['upper'])
    li = np.array([i for i,n in enumerate(names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:'))])
    ri = np.array([i for i,n in enumerate(names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
    lo, hi = low.copy(), high.copy()
    arm = np.r_[li[:12],ri]; lo[arm] = np.maximum(lo[arm],q0[arm]-args.arm_width); hi[arm] = np.minimum(hi[arm],q0[arm]+args.arm_width)
    right_goal = fk(q0)['R_Wrist'][0]+np.array([.08,-.10,.25])
    def right_res(v):
        q=q0.copy(); q[ri]=v
        return np.r_[1000*(fk(q)['R_Wrist'][0]-right_goal), .3*(v-q0[ri])]
    right_fit = least_squares(right_res,np.clip(q0[ri],lo[ri]+1e-8,hi[ri]-1e-8),bounds=(lo[ri],hi[ri]),max_nfev=100)
    fixed = q0.copy(); fixed[ri]=right_fit.x
    facets = read(FACETS)['facets']
    front_z = .0093
    for s in guitar_shapes:
        verts = gr.inv().apply(meshes[s['geom_id']].vertices-gp)
        near=verts[(verts[:,1]>-.06)&(verts[:,1]<.14)&(abs(verts[:,0])<.03)]
        if len(near): front_z=max(front_z,float(near[:,2].max()))
    def gap(a,ae,b,be):
        return max(np.min(a@be[:,:3].T+be[:,3],axis=0).max(), np.min(b@ae[:,:3].T+ae[:,3],axis=0).max())
    def evaluate(q, station):
        poses=fk(q); res=[]; metrics={}; transformed={}
        # Different stations permit ordinary spread instead of gathering all tips at one point.
        stations={'LH:index3':station+.024,'LH:middle3':station+.008,'LH:ring3':station-.008,'LH:pinky3':station-.024}
        for n,facet in facets.items():
            bp,br=poses[n]; pt=gr.inv().apply(bp+br.apply(facet['point_local_m'])-gp)
            is_palm=n=='LH:palm'; is_thumb=n=='LH:thumb3'
            y=float(np.clip(pt[1],station-.04,station+.04)) if is_palm or is_thumb else stations[n]
            width=.027908-.01631590413943356*(y+.241803)
            normal=np.array([1.,.01631590413943356,0.]) if is_palm else np.array([0.,0.,-1. if is_thumb else 1.])
            normal/=np.linalg.norm(normal)
            target=np.array([width,y,0.00065]) if is_palm else np.array([np.clip(pt[0],-width,width),y,-.008 if is_thumb else front_z])
            target += .0003*normal
            direction=gr.inv().apply(br.apply(facet['normal_local']))
            res.extend((2000 if is_palm else 1000)*(pt-target)); res.extend((25 if is_palm else 12)*(direction+normal))
            metrics[n]={'face':'palm' if is_palm else 'thumb' if is_thumb else 'front','point_G_m':pt.tolist(),'target_G_m':target.tolist(),'distance_m':float(np.linalg.norm(pt-target)),'alignment_dot':float(direction@-normal)}
        for geom,(n,v,e) in locals_.items():
            bp,br=poses[n]; rotation=gr.inv()*br; origin=gr.inv().apply(bp-gp)
            vertices=origin+rotation.apply(v); normals=rotation.apply(e[:,:3]); equations=np.column_stack((normals,e[:,3]-normals@origin))
            transformed[geom]=(vertices,equations)
            res.append(10000*max(0.,.0001-gap(vertices,equations,nv,ne)))
        handgeoms=[s for s in left if s['body'].startswith('LH:')]
        def distance(a,b):
            chain=[]; c=a
            while c in parents:chain.append(c);c=parents[c]
            chain.append(c);steps=0;c=b
            while c not in chain and c in parents:steps+=1;c=parents[c]
            return steps+chain.index(c) if c in chain else 99
        for j,a in enumerate(handgeoms):
            for b in handgeoms[j+1:]:
                if distance(a['body'],b['body'])<=2:continue
                av,ae=transformed[a['geom_id']];bv,be=transformed[b['geom_id']]
                if np.any(np.minimum(av.max(0),bv.max(0))<np.maximum(av.min(0),bv.min(0))):res.append(0.)
                else:res.append(2000*max(0.,.0001-gap(av,ae,bv,be)))
        up=poses['LH:palm'][1].apply(facets['LH:palm']['normal_local'])[2]
        res.append(100*max(0.,-up));res.extend(.15*(q[li]-q0[li]))
        return np.array(res),metrics,poses
    rows=[]
    for seed,station in enumerate((.064,.02,.11)):
        start=fixed.copy()
        if seed:
            for i,n in enumerate(names):
                if n.startswith('LH:') and ('2' in n or '3' in n): start[i]=.5
        arm_target=np.array([.027908-.01631590413943356*(station+.241803)+.0003,station,.00065])
        def arm_residual(v):
            q=start.copy();q[li[:12]]=v;poses=fk(q)
            p,r=poses['LH:palm'];point=gr.inv().apply(p+r.apply(facets['LH:palm']['point_local_m'])-gp)
            normal=gr.inv().apply(r.apply(facets['LH:palm']['normal_local']))
            direction=gr.inv().apply(poses['LH:middle1'][0]-poses['L_Wrist'][0]);direction/=np.linalg.norm(direction)
            return np.r_[1000*(point-arm_target),40*(normal+np.array([1,0,0])),25*(direction-np.array([0,0,1])),.15*(v-q0[li[:12]])]
        arm_fit=least_squares(arm_residual,np.clip(start[li[:12]],lo[li[:12]]+1e-8,hi[li[:12]]-1e-8),bounds=(lo[li[:12]],hi[li[:12]]),max_nfev=150)
        start[li[:12]]=arm_fit.x
        def residual(v):
            q=fixed.copy();q[li]=v
            return evaluate(q,station)[0]
        fit=least_squares(residual,np.clip(start[li],lo[li]+1e-8,hi[li]-1e-8),bounds=(lo[li],hi[li]),max_nfev=160,ftol=1e-7,xtol=1e-7,gtol=1e-7)
        q=fixed.copy();q[li]=fit.x
        res,metrics,poses=evaluate(q,station)
        transformed_meshes=dict(meshes)
        for shape in shapes:
            if shape['actor']!='human':continue
            n=shape['body'];bp,br=pose(initial['human_body_states'][bodies.index(n)]);np_,nr=poses[n]
            mesh=meshes[shape['geom_id']].copy();mesh.vertices=np_+nr.apply(br.inv().apply(mesh.vertices-bp));transformed_meshes[shape['geom_id']]=mesh
        overlaps=[]
        for a in [s for s in shapes if s['actor']=='human']:
            for b in guitar_shapes:
                radius=intersection(transformed_meshes[a['geom_id']],meshes[b['geom_id']])
                if radius>1e-7:overlaps.append({'human':a['body'],'guitar':b['body'],'common_radius_m':radius})
        # Exact source overlap first; complete right-hand distances are measured in fresh native audit.
        row={'seed':seed,'station_G_m':station,'fit_success':bool(fit.success),'cost':float(fit.cost),'nfev':fit.nfev,'metrics':metrics,'source_intersections':overlaps,
             'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),
             'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in poses.items()},
             'strap_force_enabled':False,'strap_visible':False,'right_hand_noncontact_required':True,
             'scope':'source FK initial proposal; fresh native checks required'}
        save(args.out/('candidate_%02d.json'%seed),row);rows.append(row)
        print(json.dumps({'seed':seed,'cost':row['cost'],'gaps_mm':{n:round(v['distance_m']*1000,3) for n,v in metrics.items()},'overlaps':overlaps}),flush=True)
    checks={'inputs_unchanged':all(sha(p)==h for p,h in hashes.items()),'candidate_count':len(rows)==3,'physics_steps_zero':True}
    save(args.out/'search.json',{'checks':checks,'input_sha256':hashes,'candidates':[str((args.out/('candidate_%02d.json'%i)).resolve()) for i in range(len(rows))],'physics_steps':0,'native_initializations':0,'front_outer_source_z_G_m':front_z})
    if not all(checks.values()):raise AssertionError(checks)


if __name__=='__main__':main()
