"""Independent halfspace intersection checks for saved left/right hand hulls."""
import json
from pathlib import Path

from .audit_hand_hand_collision import RUN, OUT, side
from .replay_contact_geometry import recorded_probe
from .render_best_run_video import set_saved_pose
from .plot_neck_palm import geometry
from .environment import np
from .build_fixed_lower_asset import read, sha
import mujoco
from scipy.spatial import ConvexHull
from scipy.optimize import linprog


def main():
    path = OUT/'hull_verification.json'
    if path.exists():
        raise FileExistsError('preserve hull verification')
    report,states = read(RUN/'report.json'),read(RUN/'states.json')
    model,data,shapes = recorded_probe(RUN,0)
    hands = [s for s in shapes if s['actor']=='human' and side(s['body'])]
    local = {}
    for s in hands:
        i=s['geom_id']; rotation=data.geom_xmat[i].reshape(3,3)
        vertices=(geometry(model,data,s).vertices-data.geom_xpos[i])@rotation
        hull=ConvexHull(vertices)
        local[i]=(vertices,hull.equations)
    frames,solves,cutoffs = [],0,[]
    for state in states:
        set_saved_pose(model,mujoco,report,state);mujoco.mj_forward(model,data)
        world={}
        for s in hands:
            i=s['geom_id'];v,e=local[i];r=data.geom_xmat[i].reshape(3,3);p=data.geom_xpos[i]
            vertices=v@r.T+p;normals=e[:,:3]@r.T
            world[i]=(vertices.min(0),vertices.max(0),normals,-e[:,3]+normals@p)
        overlaps=[]
        for a in [s for s in hands if side(s['body'])=='L']:
            for b in [s for s in hands if side(s['body'])=='R']:
                av,bv=world[a['geom_id']],world[b['geom_id']]
                if np.any(np.minimum(av[1],bv[1])-np.maximum(av[0],bv[0])<=1e-7):
                    continue
                normals=np.vstack((av[2],bv[2]));rhs=np.r_[av[3],bv[3]]
                matrix=np.column_stack((normals,np.ones(len(normals))))
                solution=linprog([0,0,0,-1],A_ub=matrix,b_ub=rhs,
                    bounds=[(None,None)]*3+[(0,None)],method='highs')
                solves+=1
                if solution.status==2:
                    continue
                if not solution.success or not np.isfinite(solution.x).all():
                    raise RuntimeError(str(solution.message))
                error=float(np.maximum(matrix@solution.x-rhs,0).max())
                if error>1e-7:
                    raise RuntimeError('infeasible intersection witness')
                if solution.x[3]>1e-7:
                    overlaps.append({'left':a['body'],'right':b['body'],
                        'common_interior_ball_radius_m':float(solution.x[3]),
                        'center_world_m':solution.x[:3].tolist(),'feasibility_error_m':error})
        frames.append({'physics_step':state['physics_step'],'time_s':state['physics_step']/240,'overlaps':overlaps})
        if state['physics_step'] in (0,14,120,161,240):
            row=read(OUT/'samples.json')[state['physics_step']]['minimum_pair']
            a=next(s for s in hands if s['body']==row['left']);b=next(s for s in hands if s['body']==row['right'])
            values={str(limit):float(mujoco.mj_geomDistance(model,data,a['geom_id'],b['geom_id'],limit,np.zeros(6))) for limit in (.02,.1)}
            cutoffs.append({'physics_step':state['physics_step'],'left':row['left'],'right':row['right'],'signed_query_by_cutoff_m':values})
    overlapping=[f for f in frames if f['overlaps']]
    inputs=[RUN/'report.json',RUN/'states.json',OUT/'report.json',OUT/'samples.json',Path(__file__).resolve(),Path(__file__).with_name('plot_neck_palm.py')]
    value={'all_saved_states':len(frames),'cross_pairs_per_state':289,'LP_solves':solves,
        'source_hull_overlap_state_count':len(overlapping),'first_verified_overlap':overlapping[0] if overlapping else None,
        'selected_frames':[frames[i] for i in (0,14,120,161,240)],'cutoff_comparison':cutoffs,
        'method':'Maximize radius of a common ball satisfying both source convex-hull halfspaces; positive radius >1e-7m proves source hull volume intersection.',
        'limitations':'Mesh convex hulls and inner capsule polygon approximation; not PhysX cooked-mesh penetration depth or a contact-force test.',
        'input_sha256':{str(p):sha(p) for p in inputs},'native_initializations':0,'explicit_physics_steps':0}
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    (OUT/'hull_frames.json').write_text(json.dumps(frames,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'overlap_states':len(overlapping),'first':overlapping[0] if overlapping else None,'LP_solves':solves},indent=2))


if __name__=='__main__':
    main()
