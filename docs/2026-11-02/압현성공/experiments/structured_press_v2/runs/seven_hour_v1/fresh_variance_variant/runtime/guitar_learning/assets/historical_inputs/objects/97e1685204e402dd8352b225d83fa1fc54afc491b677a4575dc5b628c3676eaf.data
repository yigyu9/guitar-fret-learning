"""Generate this experiment's initial settings after read-only source pose checks."""
import argparse
import hashlib
import json
from pathlib import Path

from .environment import InitialEnvironment, np, vector, quaternion, gymapi
from .initial_overlap import build_probe, query_pairs
from .plot_neck_palm import geometry, section
from .strap import rotate, cable_forces
from .trial_settings import source_hashes


def input_hashes(base_path):
    hashes = source_hashes()
    for path in (Path(__file__).resolve(),Path(__file__).with_name('plot_neck_palm.py'),base_path.resolve()):
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def pose_metrics(env,probe):
    model,data,shapes = probe
    human = env.bodies(env.human)
    positions = {n:vector(human[env.human_bodies.index(n)]['pose']['p'])
        for n in ('L_Wrist','R_Wrist','LH:index1','LH:middle1','LH:pinky1')}
    normal = np.cross(positions['LH:middle1']-positions['L_Wrist'],
                      positions['LH:index1']-positions['LH:pinky1'])
    valid = np.linalg.norm(normal)>1e-8
    normal = normal/np.linalg.norm(normal) if valid else None
    palm = geometry(model,data,next(s for s in shapes if s['body']=='LH:palm')).center_mass
    state = env.bodies(env.guitar)[env.guitar_bodies.index('guitar')]['pose']
    origin,q = vector(state['p']),quaternion(state['r'])
    q /= np.linalg.norm(q)
    rotation = np.column_stack([rotate(q,v) for v in np.eye(3)])
    neck = [geometry(model,data,s) for s in shapes if s['actor']=='guitar' and s['body']=='guitar']
    for mesh in neck:
        mesh.vertices = (mesh.vertices-origin) @ rotation
    vertices = np.concatenate([m.vertices for m in neck])
    lo,hi = vertices.min(0),vertices.max(0)
    mid = (lo+hi)/2
    start = np.array([mid[0],lo[1],mid[2]]) @ rotation.T+origin
    station = float(np.dot(palm-start,rotation[:,1]))
    in_range = 0<=station<=hi[1]-lo[1]
    lower = float((section(neck,lo[1]+station) @ rotation.T+origin)[:,2].min()) if in_range else None
    return {'palm_normal_valid':bool(valid),'palm_up_dot':None if normal is None else float(normal[2]),
        'palm_normal_world':None if normal is None else normal.tolist(),
        'palm_center_world_m':palm.tolist(),'neck_projection_in_range':bool(in_range),
        'neck_projection_s_m':station,'local_neck_lower_world_z_m':lower,
        'palm_height_vs_local_lower_m':None if lower is None else float(palm[2]-lower),
        'wrist_positions_world_m':{n:positions[n].tolist() for n in ('L_Wrist','R_Wrist')},
        'semantics':'source palm convex-hull centroid / local neck section; normal proxy anatomical sign unverified'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase',choices=('strap','pose'),required=True)
    parser.add_argument('--base-settings',type=Path,required=True)
    parser.add_argument('--settings-dir',type=Path,required=True)
    parser.add_argument('--audit-out',type=Path,required=True)
    parser.add_argument('--rest-length',type=float)
    args = parser.parse_args()
    args.settings_dir.mkdir(parents=True,exist_ok=True)
    if any(args.settings_dir.iterdir()) or args.audit_out.exists():
        raise FileExistsError('preserve existing inputs/audit; use new paths')
    if args.phase=='pose' and args.rest_length is None:
        parser.error('pose phase requires selected absolute rest length')
    base_settings = json.loads(args.base_settings.read_text())
    hashes = input_hashes(args.base_settings)
    env = InitialEnvironment(base_settings)
    try:
        base_q,names = env.initial_q.copy(),list(env.names)
        main,torso,legs = env.main_indices.copy(),env.torso_indices.copy(),env.leg_indices.copy()
        lower,upper = env.lower.copy(),env.upper.copy()
        goal,guitar = env.goal_position.copy(),env.bodies(env.guitar)
        props = env.gym.get_actor_dof_properties(env.env,env.human).copy()
        route,mass = env.initial_route_length,env.guitar_mass
        stiffness = env.config['strap']['stiffness_n_per_m']
    finally:
        env.close()
    candidates = []
    if args.phase=='strap':
        candidates.append(('legacy',base_settings))
        for load in (0,5,10,20):
            candidates.append((f'load_{load:02d}n',dict(base_settings,strap_rest_length_m=route-load/stiffness)))
    else:
        common = dict(base_settings,strap_rest_length_m=args.rest_length)
        candidates.append(('reference',common))
        for name in ('R_Elbow_x','R_Shoulder_x','R_Thorax_y','R_Wrist_y',
                     'L_Elbow_x','L_Shoulder_x','L_Thorax_y','L_Wrist_y'):
            i=names.index(name)
            for sign in (-1,1):
                angle=float(base_q[i])+sign*.025
                if not lower[i]<=angle<=upper[i]:
                    continue
                angles=dict(base_settings['joint_angles_rad']);angles[name]=angle
                candidates.append((name+('_minus' if sign<0 else '_plus'),dict(common,joint_angles_rad=angles)))
    records = []
    for name,settings in candidates:
        env = InitialEnvironment(settings)
        try:
            before = [env.bodies(env.human),env.bodies(env.guitar)]
            dofs = env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL).copy()
            probe=build_probe(env)
            gaps=query_pairs(*probe);hand=pose_metrics(env,probe)
            points,velocities=env.route();strap=env.config['strap']
            _,tension,_,_=cable_forces(points,velocities,env.rest_length,stiffness,
                strap['damping_n_s_per_m'],strap['max_tension_n'])
            checks={'lower_initial_targets_unchanged':bool(np.array_equal(env.initial_q[legs],base_q[legs])),
                'torso_initial_targets_unchanged':bool(np.array_equal(env.initial_q[torso],base_q[torso])),
                'guitar_initial_states_and_goal_unchanged':bool(np.array_equal(env.bodies(env.guitar),guitar) and np.array_equal(env.goal_position,goal)),
                'native_pd_limits_unchanged':bool(np.array_equal(env.gym.get_actor_dof_properties(env.env,env.human),props)),
                'read_only_no_steps':bool(env.steps==0 and all(np.array_equal(a,b) for a,b in zip(before,[env.bodies(env.human),env.bodies(env.guitar)]))
                    and np.array_equal(dofs,env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL))),
                'main66_unchanged':bool(np.array_equal(env.main_indices,main))}
            accepted = gaps['negative_gap_pair_count']==0 and hand['palm_normal_valid'] and hand['palm_up_dot']>=0
            accepted &= hand['neck_projection_in_range'] and hand['palm_height_vs_local_lower_m']<=0
            if not all(checks.values()):
                raise AssertionError(checks)
            records.append({'id':name,'settings':env.initial_settings,'checks':checks,'accepted_for_diagnostic':bool(accepted),
                'initial_route_length_m':env.initial_route_length,'initial_law_tension_n':tension,
                'geometry':gaps,'hand':hand})
            if accepted:
                (args.settings_dir/(name+'.json')).write_text(json.dumps(env.initial_settings,indent=2)+'\n')
        finally:
            env.close()
    output={'phase':args.phase,'guitar_mass_kg':mass,'reference_route_length_m':route,
        'source_sha256':hashes,'runtime_sources_unchanged':hashes==input_hashes(args.base_settings),
        'records':records,'scope':'initial source checks only; no native clearance/playing/stability success'}
    args.audit_out.parent.mkdir(parents=True,exist_ok=True)
    args.audit_out.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'accepted':[r['id'] for r in records if r['accepted_for_diagnostic']],
        'rejected':[r['id'] for r in records if not r['accepted_for_diagnostic']],
        'guitar_mass_kg':mass,'reference_route_length_m':route,'source_hash_check':output['runtime_sources_unchanged']},indent=2))
    if not output['runtime_sources_unchanged']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
