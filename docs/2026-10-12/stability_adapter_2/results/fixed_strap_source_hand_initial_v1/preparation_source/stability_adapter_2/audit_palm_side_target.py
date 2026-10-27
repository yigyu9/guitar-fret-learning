"""Compare the native initial palm source surface with the user-selected neck side."""
import argparse
import json
from pathlib import Path

from .environment import ROOT, np, vector, quaternion
from .self_collision_environment import SelfCollisionEnvironment
from .finger_grip_probe import SUPPORT_PHASE
from .initial_overlap import build_probe
from .plot_neck_palm import geometry
from .pose_strap_inputs import pose_metrics
from .build_fixed_lower_asset import read, sha
from .run_joint_hold import native_state
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from scipy.optimize import minimize, LinearConstraint

PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1'
PROPOSAL=ROOT/'docs/2026-10-12/visualizations/grip_proposal/geometry.json'
BASE=ROOT/'stability_adapter_2/trials/finger_grip_hold_v1/curl_0.json'


def side_target(env):
    polygon=np.array(read(PROPOSAL)['regions_G_m']['palm'])
    body=env.bodies(env.guitar)[env.guitar_bodies.index('guitar')]['pose']
    rotation=Rotation.from_quat(quaternion(body['r']))
    origin=vector(body['p'])
    normal=np.cross(polygon[1]-polygon[0],polygon[2]-polygon[0])
    normal=normal/np.linalg.norm(normal)
    if normal[0]<0:normal=-normal
    return polygon, rotation.apply(polygon)+origin, rotation.apply(normal)


def palm_surface(env,probe):
    model,data,shapes=probe
    mesh=geometry(model,data,next(s for s in shapes if s['body']=='LH:palm'))
    hand=pose_metrics(env,probe)
    direction=np.array(hand['palm_normal_world'])
    center=mesh.center_mass
    planes=ConvexHull(mesh.vertices).equations
    denominator=planes[:,:3]@direction
    index=denominator>1e-9
    t=np.min(-(planes[index,:3]@center+planes[index,3])/denominator[index])
    point=center+direction*t
    pose=env.bodies(env.human)[env.human_bodies.index('LH:palm')]['pose']
    p,r=vector(pose['p']),Rotation.from_quat(quaternion(pose['r']))
    return mesh,hand,point,r.inv().apply(point-p),r.inv().apply(direction)


def closest_polygon(mesh,vertices):
    planes=ConvexHull(mesh.vertices).equations
    matrix=np.column_stack((planes[:,:3],np.zeros((len(planes),4))))
    sum_row=np.r_[np.zeros(3),np.ones(4)][None,:]
    def objective(x):
        delta=x[:3]-x[3:]@vertices
        return float(delta@delta), np.r_[2*delta,-2*vertices@delta]
    result=minimize(objective,np.r_[mesh.center_mass,np.full(4,.25)],jac=True,method='SLSQP',
        bounds=[(None,None)]*3+[(0,1)]*4,
        constraints=[LinearConstraint(matrix,-np.inf,-planes[:,3]),LinearConstraint(sum_row,1,1)],
        options={'ftol':1e-14,'maxiter':300})
    violation=max(float(np.maximum(matrix@result.x+planes[:,3],0).max()),abs(sum(result.x[3:])-1))
    if not result.success or violation>1e-7 or not np.isfinite(result.x).all():raise RuntimeError('side QP failed')
    return {'distance_m':float(np.sqrt(max(result.fun,0))),
            'palm_witness_world_m':result.x[:3].tolist(),'target_witness_world_m':(result.x[3:]@vertices).tolist(),
            'feasibility_error_m':violation}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=PHASE/'initial_audit')
    args=parser.parse_args()
    out=args.out;out.mkdir(parents=True,exist_ok=False)
    search_path=SUPPORT_PHASE/'search_near_touch.json'
    reference=ROOT/'docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/short/baseline'
    inputs=[Path(__file__).resolve(),BASE,PROPOSAL,search_path,reference/'states.json',reference/'report.json']
    inputs += [Path(p) for p in read(reference/'report.json')['source_sha256'] if '/docs/' not in p]
    inputs += [Path(__file__).with_name(n) for n in ('pose_strap_inputs.py','plot_neck_palm.py','build_fixed_lower_asset.py')]
    hashes={str(p):sha(p) for p in inputs}
    env=SelfCollisionEnvironment(read(BASE),read(search_path)['guitar_initial_translation_m'])
    try:
        before=native_state(env)
        probe=build_probe(env)
        mesh,hand,point,local_point,local_normal=palm_surface(env,probe)
        polygon,world,normal=side_target(env)
        pose=env.bodies(env.guitar)[0]['pose']
        origin,r=vector(pose['p']),Rotation.from_quat(quaternion(pose['r']))
        center=world.mean(0)
        checks={'initial_state_exact':before==read(reference/'states.json')[0],
                'zero_steps':env.steps==0,'queries_preserve_states':before==native_state(env),
                'inputs_unchanged':all(sha(Path(p))==h for p,h in hashes.items())}
        result={'checks':checks,'native_initializations':1,'physics_steps':0,'initial_state':before,
            'human_body_names':env.human_bodies,'human_joint_names':env.names,
            'initial_joint_targets_rad':env.initial_q.astype(float).tolist(),
            'native_lower_rad':env.lower.astype(float).tolist(),'native_upper_rad':env.upper.astype(float).tolist(),
            'target_polygon_G_m':polygon.tolist(),'target_polygon_W_m':world.tolist(),
            'target_center_W_m':center.tolist(),'target_outward_normal_W':normal.tolist(),
            'palm_normal_to_inward_target_dot':float(np.array(hand['palm_normal_world'])@(-normal)),
            'palm_centroid_G_m':r.inv().apply(mesh.center_mass-origin).tolist(),
            'palm_surface_point_G_m':r.inv().apply(point-origin).tolist(),
            'palmar_ray_surface_point_W_m':point.tolist(),'palmar_ray_point_local_m':local_point.tolist(),
            'palmar_normal_proxy_local':local_normal.tolist(),'hand':hand,
            'surface_point_to_target_center_delta_W_m':(center-point).tolist(),
            'source_hull_to_blue_polygon':closest_polygon(mesh,world),
            'initial_settings':env.initial_settings,'absolute_rest_length_m':env.rest_length,
            'input_sha256':hashes,'scope':'source palm convex hull at native pose versus illustrated target; not cooked contact certification'}
        (out/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:result[k] for k in ('checks','palm_centroid_G_m','palm_surface_point_G_m','palm_normal_to_inward_target_dot','surface_point_to_target_center_delta_W_m','source_hull_to_blue_polygon')},indent=2))
        if not all(checks.values()):raise AssertionError(checks)
    finally:env.close()


if __name__=='__main__':main()
