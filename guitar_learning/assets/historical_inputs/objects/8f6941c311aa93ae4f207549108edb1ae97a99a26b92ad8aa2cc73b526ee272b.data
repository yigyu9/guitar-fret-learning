"""Small finger-only refinement of a fresh native underneck pose; no physics."""
from .environment import ROOT, np
import argparse
import copy
from pathlib import Path
from scipy.spatial import ConvexHull
from scipy.optimize import least_squares
from .underneck_initial_search import read, save, sha, pose, calibrated_fk, source_scene, BASE
from .initial_overlap import build_probe
from .face_referenced_geometry import face_geometry
from .palm_side_source_checks import intersection


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True);parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    init=read(args.native/'initial_values.json');audit=read(args.native/'initial_audit.json');candidate=read(args.candidate)
    if not all(audit['checks'].values()) or audit['source_intersections']:raise ValueError('fresh FK match and no human-guitar overlap required')
    from .trial_settings import source_hashes
    import sys
    paths=[Path(m.__file__) for n,m in sys.modules.items() if n.startswith('stability_adapter_2') and getattr(m,'__file__',None)]
    paths += [Path(__file__).resolve(),args.native/'initial_values.json',args.native/'initial_audit.json',args.candidate,BASE,ROOT/'stability_adapter_2/UNDERNECK_INITIAL_BUILD.md',ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml']
    hashes=source_hashes();hashes.update({str(p.resolve()):sha(p) for p in paths})
    save(args.out/'attempt.json',{'input_sha256':hashes,'finger_width_rad':.18,'physics_steps':0,'native_initializations':0})
    state=init['native_initial_state'];names=init['joint_names'];bodies=init['human_body_names'];q0=np.array(init['actual_initial_angles_rad'])
    fk,parents=calibrated_fk(names,bodies,state,q0);gp,gr=pose(state['guitar_body_states'][0])
    base=read(BASE);scene,_=source_scene(state,base,gp,gr);model,data,shapes=build_probe(scene)
    meshes={s['geom_id']:face_geometry(model,data,s) for s in shapes}
    human=[s for s in shapes if s['actor']=='human'];guitar=[s for s in shapes if s['actor']=='guitar'];hand=[s for s in human if s['body'].startswith('LH:')]
    locals_={}
    for s in hand:
        p,r=pose(state['human_body_states'][bodies.index(s['body'])]);v=r.inv().apply(meshes[s['geom_id']].vertices-p)
        locals_[s['geom_id']]=(s['body'],v,ConvexHull(v).equations)
    guitar_data={s['geom_id']:(meshes[s['geom_id']].vertices,ConvexHull(meshes[s['geom_id']].vertices).equations) for s in guitar}
    indices=np.array([i for i,n in enumerate(names) if n.startswith('LH:') and not n.startswith('LH:thumb')])
    lo=np.maximum(np.array(base['PD_properties']['lower'])[indices],q0[indices]-.18)
    hi=np.minimum(np.array(base['PD_properties']['upper'])[indices],q0[indices]+.18)
    def distance(a,b):
        chain=[];c=a
        while c in parents:chain.append(c);c=parents[c]
        chain.append(c);steps=0;c=b
        while c not in chain and c in parents:steps+=1;c=parents[c]
        return steps+chain.index(c) if c in chain else 99
    pairs=[(a,b) for i,a in enumerate(hand) for b in hand[i+1:] if distance(a['body'],b['body'])>2]
    witnesses={}
    for digit in ('index','middle','ring','pinky'):
        row=audit['surface_gaps'][digit];n=row['nearest_body'];g=row['member_distances'][n]
        p,r=pose(state['human_body_states'][bodies.index(n)])
        local=r.inv().apply(np.array(g['palm_witness_world_m'])-p)
        goal=np.array(g['target_witness_world_m'])+gr.apply([0,0,.0003])
        witnesses[n]=(local,goal)
    def gap(a,ae,b,be):return max(np.min(a@be[:,:3].T+be[:,3],axis=0).max(),np.min(b@ae[:,:3].T+ae[:,3],axis=0).max())
    def overlap_cost(a,ae,b,be,weight):
        if np.any(np.minimum(a.max(0),b.max(0))<np.maximum(a.min(0),b.min(0))):return 0.
        return weight*max(0.,.0002-gap(a,ae,b,be))
    def evaluate(q,weight):
        poses=fk(q);res=[];transformed={}
        for n,(local,goal) in witnesses.items():
            p,r=poses[n];res.extend(1000*(p+r.apply(local)-goal))
        for geom,(n,v,e) in locals_.items():
            p,r=poses[n];verts=p+r.apply(v);normals=r.apply(e[:,:3]);equations=np.column_stack((normals,e[:,3]-normals@p))
            transformed[geom]=(verts,equations)
            for gv,ge in guitar_data.values():res.append(overlap_cost(verts,equations,gv,ge,weight))
        for a,b in pairs:
            av,ae=transformed[a['geom_id']];bv,be=transformed[b['geom_id']];res.append(overlap_cost(av,ae,bv,be,weight))
        res.extend(.1*(q[indices]-q0[indices]));return np.array(res),poses,transformed
    rows=[]
    for weight in (10000.,50000.):
        def residual(v):
            q=q0.copy();q[indices]=v;return evaluate(q,weight)[0]
        fit=least_squares(residual,np.clip(q0[indices],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=120,ftol=1e-8,xtol=1e-8,gtol=1e-8)
        q=q0.copy();q[indices]=fit.x;_,poses,transformed=evaluate(q,weight)
        hand_mesh={}
        for s in hand:
            mesh=meshes[s['geom_id']].copy();mesh.vertices=transformed[s['geom_id']][0];hand_mesh[s['geom_id']]=mesh
        overlaps=[];self_cross=[]
        for a in hand:
            for b in guitar:
                radius=intersection(hand_mesh[a['geom_id']],meshes[b['geom_id']])
                if radius>1e-7:overlaps.append({'human':a['body'],'guitar':b['body'],'common_radius_m':radius})
        for a,b in pairs:
            radius=intersection(hand_mesh[a['geom_id']],hand_mesh[b['geom_id']])
            if radius>1e-7:self_cross.append({'a':a['body'],'b':b['body'],'common_radius_m':radius})
        row=copy.deepcopy(candidate);row.update(joint_angles_rad=q.tolist(),predicted_human_poses={n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in poses.items()},
            source_intersections=overlaps,source_hand_self_intersections=self_cross,refinement_weight=weight,fit_success=bool(fit.success),refinement_cost=float(fit.cost),
            finger_only_refinement=True,source_clear_refinement=not overlaps and not self_cross)
        path=args.out/('candidate_w%d.json'%int(weight));save(path,row);rows.append(str(path.resolve()))
        print('refinement',int(weight),'overlaps',overlaps,'self',self_cross,flush=True)
    checks={'inputs_unchanged':all(sha(p)==h for p,h in hashes.items()),'physics_steps_zero':True}
    save(args.out/'report.json',{'checks':checks,'input_sha256':hashes,'candidates':rows,'native_initializations':0,'physics_steps':0,'scope':'fixed witness and source hull refinement; fresh native and contacts required'})
    if not all(checks.values()):raise AssertionError(checks)


if __name__=='__main__':main()
