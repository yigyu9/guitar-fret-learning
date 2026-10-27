"""Three approved right-arm initial recipes with Thorax_y returned to reference."""
import argparse
import hashlib
import json
from pathlib import Path

from .environment import InitialEnvironment, np, gymapi
from .initial_overlap import build_probe, query_pairs
from .pose_strap_inputs import pose_metrics, input_hashes
from .search_hand_support import palm_neck_gap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-settings',type=Path,required=True)
    parser.add_argument('--approach-settings',type=Path,required=True)
    parser.add_argument('--settings-dir',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    args.settings_dir.mkdir(parents=True,exist_ok=True)
    if any(args.settings_dir.iterdir()) or args.out.exists():
        raise FileExistsError('preserve prior inputs/audit')
    common = json.loads(args.base_settings.read_text())
    approach = json.loads(args.approach_settings.read_text())
    hashes = input_hashes(args.base_settings)
    for p in (args.approach_settings,Path(__file__).resolve(),Path(__file__).with_name('search_hand_support.py')):
        hashes[str(p.resolve())] = hashlib.sha256(p.read_bytes()).hexdigest()
    env = InitialEnvironment(common)
    try:
        base,names = env.initial_q.copy(),list(env.names)
        lower,upper = env.lower.copy(),env.upper.copy()
        right = [i for i,n in enumerate(names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]
        other = [i for i in range(len(names)) if i not in right]
        human,guitar,goal = env.bodies(env.human),env.bodies(env.guitar),env.goal_position.copy()
        props = env.gym.get_actor_dof_properties(env.env,env.human).copy()
        route = env.initial_route_length
    finally:
        env.close()
    angles = dict(approach['joint_angles_rad'])
    angles.pop('R_Thorax_y')
    recipes = [('reference',dict(common['joint_angles_rad'])),('reset_thorax',angles)]
    for name,sy,ex in (('reset_thorax_sy02',.2,.05),('reset_thorax_sy03_ex10',.3,.1)):
        q = dict(angles)
        for joint,offset in (('R_Shoulder_y',sy),('R_Elbow_x',ex)):
            i=names.index(joint);q[joint]=float(np.clip(base[i]+offset,lower[i],upper[i]))
        recipes.append((name,q))
    records = []
    for number,(name,angles) in enumerate(recipes):
        env = InitialEnvironment(dict(common,joint_angles_rad=angles))
        try:
            h,g,q = env.bodies(env.human),env.bodies(env.guitar),env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL).copy()
            probe = build_probe(env)
            geometry,hand = query_pairs(*probe),pose_metrics(env,probe)
            checks = {'only_right_arm_initial_targets_changed':bool(np.array_equal(env.initial_q[other],base[other])),
                'arm_initial_bounds':bool((np.abs(env.initial_q[right]-base[right])<=.3+2e-7).all() and ((env.initial_q>=lower-2e-7)&(env.initial_q<=upper+2e-7)).all()),
                'right_thorax_y_reference':env.initial_q[names.index('R_Thorax_y')]==base[names.index('R_Thorax_y')],
                'guitar_initial_states_goal_unchanged':bool(np.array_equal(g,guitar) and np.array_equal(env.goal_position,goal)),
                'root_initial_state_unchanged':bool(np.array_equal(h[0],human[0])),
                'native_pd_unchanged':bool(np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human))),
                'absolute_length_route_unchanged':env.rest_length==common['strap_rest_length_m'] and env.initial_route_length==route,
                'initial_dofs_match_target':bool(np.array_equal(q['pos'],env.initial_q) and (q['vel']==0).all()),
                'read_only_no_steps':bool(env.steps==0 and np.array_equal(h,env.bodies(env.human)) and np.array_equal(g,env.bodies(env.guitar)) and np.array_equal(q,env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL)))}
            if not all(checks.values()):raise AssertionError(checks)
            accepted = geometry['negative_gap_pair_count']==0 and hand['palm_normal_valid'] and hand['palm_up_dot']>=0 and hand['neck_projection_in_range'] and hand['palm_height_vs_local_lower_m']<=0
            records.append({'id':number,'name':name,'settings':env.initial_settings,'checks':checks,'geometry':geometry,'hand':hand,
                'palm_neck':palm_neck_gap(probe,'RH:palm','G:body'),'shoulder_body_hulls':palm_neck_gap(probe,'R_Shoulder','G:body'),
                'initial_route_length_m':route,'accepted_for_diagnostic':bool(accepted)})
            if accepted:(args.settings_dir/(name+'.json')).write_text(json.dumps(env.initial_settings,indent=2)+'\n')
        finally:env.close()
    output = {'scope':'four fixed recipes in approved initial-angle range; no new distance gate or feedback',
        'checks':{'all_input_contracts':all(all(r['checks'].values()) for r in records),'sources_unchanged':all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())},
        'source_sha256':hashes,'evaluations':records}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':output['checks'],'recipes':[{'name':r['name'],'accepted':r['accepted_for_diagnostic'],'palm_mm':r['palm_neck']['source_hull_distance_m']*1000,'shoulder_mm':r['shoulder_body_hulls']['source_hull_distance_m']*1000} for r in records]},indent=2))
    if not all(output['checks'].values()):raise SystemExit(1)


if __name__=='__main__':main()
