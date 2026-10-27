"""Native-calibrated initial RH placement; only source geometry, no integration."""
from .underneck_pose_trial_v5 import UnderneckEnvironment, read, save, sha, pose, calibrated_fk
from .run_strike_live_probe import CHECKPOINT, GOAL, GRIP, CANDIDATE
from .environment import ROOT, np
from .run_joint_hold import native_state
from .strike_native_view import create_view
from .initial_overlap import build_probe
from .face_referenced_geometry import face_geometry
from .palm_side_source_checks import intersection
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
from pathlib import Path
import argparse
import copy
import torch


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    env=UnderneckEnvironment(read(CANDIDATE)); result=[]
    try:
        state=native_state(env);names=env.names;bodies=env.human_bodies;q0=env.initial_q.astype(float)
        checkpoint=torch.load(CHECKPOINT,map_location='cpu',weights_only=True)
        view=create_view(env,checkpoint,str(GOAL),str(GRIP))
        _,_,center,ready,*_=view._current_target_geometry()
        gp,gr=pose(state['guitar_body_states'][0]);target_g=ready[0].numpy()+[0,0,.03]
        target=gp+gr.apply(target_g)
        fk,parents=calibrated_fk(names,bodies,state,q0)
        fixed=q0.copy();fixed[view.grip_reference.indices.numpy()]=view.grip_reference.target.numpy()
        assert ((fixed>=env.lower)&(fixed<=env.upper)).all()
        source_pose=read(ROOT/'tab2body/assets/seated_pose.json')
        source_q=np.clip([source_pose['joints_isaac'][n] for n in names],env.lower,env.upper)
        source_q[view.grip_reference.indices.numpy()]=view.grip_reference.target.numpy()
        w,x,y,z=source_pose['params']['guitar_quat_wxyz_computed']
        relative=Rotation.from_quat([x,y,z,w]).inv()*fk(source_q)['RH:pick'][1]
        desired_r=gr*relative
        indices=np.array([i for i,n in enumerate(names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
        lo=np.maximum(env.lower[indices],q0[indices]-1.2);hi=np.minimum(env.upper[indices],q0[indices]+1.2)
        model,data,shapes=build_probe(env)
        meshes={s['geom_id']:face_geometry(model,data,s) for s in shapes}
        human=[s for s in shapes if s['actor']=='human'];guitar=[s for s in shapes if s['actor']=='guitar']
        moving=[s for s in human if s['body'].startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist','RH:'))]
        locals_={}
        for s in moving:
            p,r=pose(state['human_body_states'][bodies.index(s['body'])]);v=r.inv().apply(meshes[s['geom_id']].vertices-p)
            locals_[s['geom_id']]=(s['body'],v,ConvexHull(v).equations)
        def graph_distance(a,b):
            chain=[];c=a
            while c in parents:chain.append(c);c=parents[c]
            chain.append(c);steps=0;c=b
            while c not in chain and c in parents:steps+=1;c=parents[c]
            return steps+chain.index(c) if c in chain else 99
        pairs=[(a,b) for a in moving for b in shapes if b['actor']=='guitar' or
               (b['actor']=='human' and graph_distance(a['body'],b['body'])>2 and
                (b not in moving or a['geom_id']<b['geom_id']))]
        static={s['geom_id']:(meshes[s['geom_id']].vertices,ConvexHull(meshes[s['geom_id']].vertices).equations) for s in shapes}
        def transformed(q):
            poses=fk(q);geometry=dict(static)
            for geom,(n,v,e) in locals_.items():
                p,r=poses[n];vertices=p+r.apply(v);normal=r.apply(e[:,:3])
                geometry[geom]=(vertices,np.column_stack([normal,e[:,3]-normal@p]))
            return poses,geometry
        def residual(v):
            q=fixed.copy();q[indices]=v;poses,geometry=transformed(q);p,r=poses['RH:pick']
            values=list(1000*(p-target))+list(10*(desired_r.inv()*r).as_rotvec())+list(.15*(v-q0[indices]))
            for a,b in pairs:
                av,ae=geometry[a['geom_id']];bv,be=geometry[b['geom_id']]
                if np.any(np.minimum(av.max(0),bv.max(0))<np.maximum(av.min(0),bv.min(0))):values.append(0.);continue
                gap=max(np.min(av@be[:,:3].T+be[:,3],axis=0).max(),np.min(bv@ae[:,:3].T+ae[:,3],axis=0).max())
                values.append(5000*max(0.,.001-gap))
            return values
        for j,seed in enumerate((q0[indices],source_q[indices])):
            fit=least_squares(residual,np.clip(seed,lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=120)
            q=fixed.copy();q[indices]=fit.x;poses,geometry=transformed(q)
            transformed_meshes=dict(meshes)
            for s in moving:
                mesh=meshes[s['geom_id']].copy();mesh.vertices=geometry[s['geom_id']][0];transformed_meshes[s['geom_id']]=mesh
            overlaps=[]
            for a,b in pairs:
                radius=intersection(transformed_meshes[a['geom_id']],transformed_meshes[b['geom_id']])
                if radius>1e-7:overlaps.append({'a':a['body'],'b':b['body'],'actor_b':b['actor'],'common_radius_m':radius})
            p,r=poses['RH:pick'];error=float(np.linalg.norm(p-target))
            row=copy.deepcopy(read(CANDIDATE))
            row.update(joint_angles_rad=q.tolist(),predicted_human_poses={n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in poses.items()},
                preparation={'target_G_m':target_g.tolist(),'ready_G_m':ready[0].tolist(),'center_G_m':center[0].tolist(),
                    'pick_target_error_m':error,'orientation_soft_error_rad':float((desired_r.inv()*r).magnitude()),
                    'soft_reference_pick_rotation_G_xyzw':relative.as_quat().tolist(), 'source_intersections':overlaps,
                    'grip_reference_applied':True,'accepted_source_candidate':not overlaps and error<.015})
            path=args.out/('candidate_%d.json'%j);save(path,row)
            result.append({'candidate_path':str(path.resolve()),**row['preparation']})
            print('candidate',j,'pick error',error,'intersections',overlaps,flush=True)
        save(args.out/'report.json',{'rows':result,'native_initializations':1,'physics_steps':env.steps,'scope':'native-calibrated CPU FK/source hull; fresh native audit and contacts required'})
    finally:env.close()


if __name__=='__main__':main()
