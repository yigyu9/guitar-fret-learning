"""Bounded t=0 search: fresh native scene per candidate, no physics rollout."""
import argparse
import hashlib
import json
from pathlib import Path

from .environment import InitialEnvironment, gymapi, np
from .initial_overlap import build_probe, query_pairs, query_ground
from .trial_settings import source_hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    if any(args.out.iterdir()):
        raise FileExistsError('use an empty search directory')
    common = {'guitar_initial_z_offset_m':.005,'strap_rest_length_m':1.0891851746440693}
    hashes = source_hashes()
    env = InitialEnvironment(common)
    try:
        base,lower,upper = env.initial_q.copy(),env.lower.copy(),env.upper.copy()
        names,main,torso = list(env.names),list(env.main_indices),list(env.torso_indices)
        indices = [i for i in env.leg_indices if lower[i]<upper[i]]
        ref_human,ref_guitar = env.bodies(env.human),env.bodies(env.guitar)
        fixed_bodies = [i for i,n in enumerate(env.human_bodies) if n not in
            {side+'_'+body for side in ('L','R') for body in ('Hip','Knee','Ankle','Toe')}]
        ref_props = env.gym.get_actor_dof_properties(env.env,env.human).copy()
    finally:
        env.close()
    history,cache = [],{}

    def evaluate(angles):
        angles = {n:v for n,v in angles.items() if v!=float(base[names.index(n)])}
        key = tuple(sorted(angles.items()))
        if key in cache:
            return cache[key]
        env = InitialEnvironment(dict(common,joint_angles_rad=angles))
        try:
            human,guitar = env.bodies(env.human),env.bodies(env.guitar)
            dofs = env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL).copy()
            model,data,shapes = build_probe(env,include_ground=True)
            geometry,ground = query_pairs(model,data,shapes),query_ground(model,data,shapes)
            changed = [i for i in range(len(base)) if env.initial_q[i]!=base[i]]
            checks = {'changed_only_effective_lower':set(changed)<=set(indices),
                'native_initial_dof_matches_target':bool(np.array_equal(dofs['pos'],env.initial_q) and (dofs['vel']==0).all()),
                'approved_lower_offset_bounds':bool(np.abs(env.initial_q-base).max()<=.05+2e-7),
                'upper_body_and_root_states_unchanged':bool(np.array_equal(human[fixed_bodies],ref_human[fixed_bodies])),
                'all_guitar_states_unchanged':bool(np.array_equal(guitar,ref_guitar)),
                'native_pd_and_limits_unchanged':bool(np.array_equal(ref_props,env.gym.get_actor_dof_properties(env.env,env.human))),
                'main66_torso9_unchanged':list(env.main_indices)==main and list(env.torso_indices)==torso,
                'absolute_strap_length_unchanged':env.rest_length==common['strap_rest_length_m'],
                'no_physics_steps':env.steps==0}
            if not all(checks.values()):
                raise AssertionError(checks)
            row = {'evaluation_id':len(history),'settings':dict(common,joint_angles_rad=angles),
                'checks':checks,'actual_lower_offsets_rad':{names[i]:float(env.initial_q[i]-base[i]) for i in indices},
                'human_guitar_geometry':geometry,'ground_geometry':ground,
                'native_initial_state_sha256':hashlib.sha256(human.tobytes()+guitar.tobytes()+dofs.tobytes()).hexdigest()}
            history.append(row);cache[key]=row
            return row
        finally:
            env.close()

    def rank(row):
        ground = row['ground_geometry']
        change = sum(abs(v) for v in row['actual_lower_offsets_rad'].values())
        return (-ground['negative_gap_pair_count'],min(ground['minimum_gap_m'],.001),-change)

    baseline = best = evaluate({})
    for sweep in range(2):
        previous = best['evaluation_id']
        for i in indices:
            candidates = [best]
            for offset in (-.05,-.025,0.,.025,.05):
                angle = float(np.clip(float(base[i])+offset,lower[i],upper[i]))
                angles = dict(best['settings']['joint_angles_rad']);angles[names[i]]=angle
                row = evaluate(angles)
                if row['human_guitar_geometry']['negative_gap_pair_count']<=baseline['human_guitar_geometry']['negative_gap_pair_count']:
                    candidates.append(row)
            best = max(candidates,key=rank)
            print(json.dumps({'sweep':sweep,'joint':names[i],'evaluations':len(history),
                'best_id':best['evaluation_id'],'minimum_ground_gap_m':best['ground_geometry']['minimum_gap_m']}),flush=True)
            if best['ground_geometry']['minimum_gap_m']>=.001:
                break
        if best['ground_geometry']['minimum_gap_m']>=.001 or best['evaluation_id']==previous:
            break
    improved = [row for row in history if rank(row)>rank(baseline) and
        row['human_guitar_geometry']['negative_gap_pair_count']<=baseline['human_guitar_geometry']['negative_gap_pair_count']]
    selected = sorted(improved,key=rank,reverse=True)[:3]
    checks = {'all_evaluation_contracts':all(all(row['checks'].values()) for row in history),
        'runtime_sources_unchanged':hashes==source_hashes(),
        'selected_at_most_three':len(selected)<=3}
    output = {'scope':'static source geometry search at native t=0; no native clearance/stability success',
        'checks':checks,'source_sha256':hashes,'baseline_id':baseline['evaluation_id'],
        'effective_lower_joint_names':[names[i] for i in indices],
        'selected_ids':[row['evaluation_id'] for row in selected],'evaluations':history}
    (args.out/'search.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    for number,row in enumerate(selected,1):
        (args.out/f'candidate_{number:02d}.json').write_text(json.dumps(row['settings'],indent=2)+'\n')
    print(json.dumps({'checks':checks,'evaluation_count':len(history),'selected_ids':output['selected_ids']},indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__=='__main__':
    main()
