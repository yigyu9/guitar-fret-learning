"""Approved +/-0.3 rad initial left-arm source proximity search; no dynamics."""
import argparse
import hashlib
import json
from pathlib import Path

from .environment import InitialEnvironment, np, gymapi
from .initial_overlap import build_probe, query_pairs, mujoco
from .pose_strap_inputs import pose_metrics, input_hashes
from .plot_neck_palm import geometry


def palm_neck_gap(probe):
    """Closest points on source convex hulls; wide-margin backend signs are unreliable."""
    from scipy.optimize import minimize, LinearConstraint
    from scipy.linalg import block_diag
    model, data, shapes = probe
    palm = next(s for s in shapes if s['actor']=='human' and s['body']=='LH:palm')
    palm_mesh = geometry(model,data,palm)
    rows = []
    for neck in [s for s in shapes if s['actor']=='guitar' and s['body']=='guitar']:
        neck_mesh = geometry(model,data,neck)
        meshes = (palm_mesh,neck_mesh)
        normals = [m.face_normals for m in meshes]
        rhs = np.concatenate([np.einsum('ij,ij->i',n,m.triangles[:,0]) for n,m in zip(normals,meshes)])
        matrix = block_diag(*normals)
        constraints = LinearConstraint(matrix,-np.inf,rhs)
        def objective(x):
            delta = x[:3]-x[3:]
            return float(delta @ delta), np.concatenate((2*delta,-2*delta))
        result = minimize(objective,np.concatenate([m.center_mass for m in meshes]),
            jac=True,method='SLSQP',constraints=[constraints],options={'ftol':1e-14,'maxiter':200})
        feasibility = float(np.maximum(matrix @ result.x-rhs,0).max())
        if not result.success or not np.isfinite(result.x).all() or feasibility>1e-7:
            raise RuntimeError('source closest-point solve failed: '+str(result.message))
        points = np.zeros(6)
        gap = float(mujoco.mj_geomDistance(model,data,palm['geom_id'],neck['geom_id'],.02,points))
        if not np.isfinite(gap) or not np.isfinite(points).all():
            raise FloatingPointError('nonfinite palm/neck source query')
        rows.append({'source_hull_distance_m':float(np.sqrt(max(result.fun,0))),
            'geom_ids':[palm['geom_id'],neck['geom_id']],
            'hull_witness_points_m':result.x.reshape(2,3).tolist(),
            'solver_feasibility_error_m':feasibility,
            'backend_signed_gap_20mm_cutoff_m':gap})
    return min(rows,key=lambda r:r['source_hull_distance_m'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-settings',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--settings-dir',type=Path,required=True)
    args = parser.parse_args()
    for folder in (args.out,args.settings_dir):
        folder.mkdir(parents=True,exist_ok=True)
        if any(folder.iterdir()):
            raise FileExistsError('preserve existing search/settings; use empty paths')
    common = json.loads(args.base_settings.read_text())
    hashes = input_hashes(args.base_settings)
    script = Path(__file__).resolve()
    hashes[str(script)] = hashlib.sha256(script.read_bytes()).hexdigest()
    env = InitialEnvironment(common)
    try:
        base,names,main,torso = env.initial_q.copy(),list(env.names),env.main_indices.copy(),env.torso_indices.copy()
        lower,upper = env.lower.copy(),env.upper.copy()
        props = env.gym.get_actor_dof_properties(env.env,env.human).copy()
        guitar,goal,human = env.bodies(env.guitar),env.goal_position.copy(),env.bodies(env.human)
        joints = [i for i,n in enumerate(names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist')) and lower[i]<upper[i]]
        unchanged_bodies = [i for i,n in enumerate(env.human_bodies) if not n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:'))]
        nonarm = [i for i in range(len(names)) if i not in joints]
    finally:
        env.close()
    history,cache = [],{}

    def evaluate(offsets):
        angles = dict(common['joint_angles_rad'])
        for i,value in offsets.items():
            angles[names[i]] = float(np.clip(float(base[i])+value,lower[i],upper[i]))
        key = tuple(sorted(angles.items()))
        if key in cache:
            return cache[key]
        env = InitialEnvironment(dict(common,joint_angles_rad=angles))
        try:
            before_h,before_g = env.bodies(env.human),env.bodies(env.guitar)
            before_q = env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL).copy()
            probe = build_probe(env)
            geometry,hand,gap = query_pairs(*probe),pose_metrics(env,probe),palm_neck_gap(probe)
            checks = {'only_approved_arm_initial_targets_changed':bool(np.array_equal(env.initial_q[nonarm],base[nonarm])),
                'bounded_initial_offset':bool(np.abs(env.initial_q-base).max()<=.3+2e-7),
                'initial_dofs_match_target':bool(np.array_equal(before_q['pos'],env.initial_q) and (before_q['vel']==0).all()),
                'unchanged_body_states':bool(np.array_equal(before_h[unchanged_bodies],human[unchanged_bodies])),
                'all_guitar_initial_states_and_goal_unchanged':bool(np.array_equal(before_g,guitar) and np.array_equal(env.goal_position,goal)),
                'native_pd_limits_unchanged':bool(np.array_equal(env.gym.get_actor_dof_properties(env.env,env.human),props)),
                'main66_torso9_unchanged':bool(np.array_equal(env.main_indices,main) and np.array_equal(env.torso_indices,torso)),
                'absolute_length_unchanged':env.rest_length==common['strap_rest_length_m'],
                'read_only_no_steps':bool(env.steps==0 and np.array_equal(before_h,env.bodies(env.human)) and np.array_equal(before_g,env.bodies(env.guitar)) and np.array_equal(before_q,env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL)))}
            if not all(checks.values()):
                raise AssertionError(checks)
            accepted = geometry['negative_gap_pair_count']==0 and hand['palm_normal_valid'] and hand['palm_up_dot']>=0 and hand['neck_projection_in_range'] and hand['palm_height_vs_local_lower_m']<=0
            row = {'id':len(history),'settings':env.initial_settings,'checks':checks,'geometry':geometry,'hand':hand,
                'palm_neck':gap,'accepted_for_diagnostic':bool(accepted),
                'initial_route_length_m':env.initial_route_length,
                'arm_offsets_rad':{names[i]:float(env.initial_q[i]-base[i]) for i in joints},
                'native_initial_state_sha256':hashlib.sha256(before_h.tobytes()+before_g.tobytes()+before_q.tobytes()).hexdigest()}
            history.append(row);cache[key]=row
            return row
        finally:
            env.close()

    def rank(row):
        return (-abs(row['palm_neck']['source_hull_distance_m']-.003),row['hand']['palm_up_dot'],
            -sum(abs(v) for v in row['arm_offsets_rad'].values()))

    baseline = best = evaluate({})
    for sweep in range(2):
        previous = best['id']
        for i in joints:
            offsets = {names.index(n):v for n,v in best['arm_offsets_rad'].items() if abs(v)>1e-7}
            candidates = [best]
            for offset in (-.3,-.2,-.1,-.05,.05,.1,.2,.3):
                row = evaluate({**offsets,i:offset})
                if row['accepted_for_diagnostic']:
                    candidates.append(row)
            best = max(candidates,key=rank)
            print(json.dumps({'sweep':sweep,'joint':names[i],'evaluations':len(history),
                'best_id':best['id'],'palm_neck_hull_distance_m':best['palm_neck']['source_hull_distance_m']}),flush=True)
        if best['id']==previous:
            break
    selected = []
    for row in sorted([r for r in history if r['accepted_for_diagnostic'] and rank(r)>rank(baseline)],key=rank,reverse=True):
        if all(max(abs(row['arm_offsets_rad'][n]-other['arm_offsets_rad'][n]) for n in row['arm_offsets_rad'])>=.05-2e-7 for other in selected):
            selected.append(row)
        if len(selected)==3:
            break
    after = input_hashes(args.base_settings)
    after[str(script)] = hashlib.sha256(script.read_bytes()).hexdigest()
    output = {'scope':'static source palm/neck proximity at native initial pose; no native clearance/support/stability success',
        'ranking':'distance to nominal 3mm source convex-hull palm/neck distance, then soft upward normal, then small angle change; no new mandatory distance gate. Hull distances are unsigned; source gap gate retains 20mm backend cutoff.',
        'checks':{'all_candidate_contracts':all(all(r['checks'].values()) for r in history),'runtime_sources_unchanged':hashes==after},
        'source_sha256':hashes,'baseline_id':baseline['id'],'selected_ids':[r['id'] for r in selected],'evaluations':history}
    (args.out/'search.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    for number,row in enumerate([baseline]+selected):
        (args.settings_dir/('reference.json' if number==0 else f'candidate_{number:02d}.json')).write_text(json.dumps(row['settings'],indent=2)+'\n')
    print(json.dumps({'checks':output['checks'],'evaluations':len(history),'selected_ids':output['selected_ids'],'baseline_hull_distance_m':baseline['palm_neck']['source_hull_distance_m'],'best_hull_distance_m':best['palm_neck']['source_hull_distance_m']},indent=2))
    if not all(output['checks'].values()):
        raise SystemExit(1)


if __name__=='__main__':
    main()
