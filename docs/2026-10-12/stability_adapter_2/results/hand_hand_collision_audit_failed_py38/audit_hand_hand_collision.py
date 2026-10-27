"""Read saved hand geometry and native collision masks without a rollout."""
import json
from pathlib import Path

from .fixed_lower_environment import FixedLowerEnvironment
from .environment import ROOT, np
from .replay_contact_geometry import recorded_probe
from .render_best_run_video import set_saved_pose
from .build_fixed_lower_asset import sha, read
import mujoco

RUN = ROOT/'docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s'
OUT = ROOT/'docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1'


def side(name):
    if name.startswith('LH:') or name=='L_Wrist':
        return 'L'
    if name.startswith('RH:') or name=='R_Wrist':
        return 'R'
    return None


def main():
    if OUT.exists():
        raise FileExistsError('preserve audit outputs')
    OUT.mkdir(parents=True)
    report,states,contacts = (read(RUN/(n+'.json')) for n in ('report','states','contacts'))
    model,data,shapes = recorded_probe(RUN,0)
    left = [s for s in shapes if s['actor']=='human' and side(s['body'])=='L']
    right = [s for s in shapes if s['actor']=='human' and side(s['body'])=='R']
    samples = []
    for state in states:
        set_saved_pose(model,mujoco,report,state)
        mujoco.mj_forward(model,data)
        pairs = []
        for a in left:
            for b in right:
                points = np.zeros(6)
                gap = float(mujoco.mj_geomDistance(model,data,a['geom_id'],b['geom_id'],.1,points))
                if gap < .1:
                    pairs.append({'left':a['body'],'right':b['body'],'signed_gap_m':gap,
                        'witness_points_m':points.reshape(2,3).tolist()})
        pairs.sort(key=lambda p:p['signed_gap_m'])
        samples.append({'physics_step':state['physics_step'],'time_s':state['physics_step']/240,
            'minimum_pair':pairs[0] if pairs else None,
            'negative_pairs':[p for p in pairs if p['signed_gap_m'] < -1e-7]})
    native_rows = [{'physics_step':s['physics_step'],'contact':c} for s in contacts for c in s['contacts']
        if {side(c['body0_name'].removeprefix('human/')),side(c['body1_name'].removeprefix('human/'))}=={'L','R'}
        and c['body0_name'].startswith('human/') and c['body1_name'].startswith('human/')]
    env = FixedLowerEnvironment(read(ROOT/'stability_adapter_2/trials/left_palm_boundary_v1/l_wrist_x_minus0125.json'))
    try:
        props = env.gym.get_actor_rigid_shape_properties(env.env,env.human)
        ranges = env.gym.get_actor_rigid_body_shape_indices(env.env,env.human)
        filters = {name:[int(props[i].filter) for i in range(ranges[j].start,ranges[j].start+ranges[j].count)]
            for j,name in enumerate(env.human_bodies) if side(name)}
        shared_bit = all(a&b != 0 for name,values in filters.items() if side(name)=='L' for a in values
            for other,others in filters.items() if side(other)=='R' for b in others)
        native_steps = env.steps
    finally:
        env.close()
    negative = [s for s in samples if s['negative_pairs']]
    worst = min(samples,key=lambda s:s['minimum_pair']['signed_gap_m'] if s['minimum_pair'] else .1)
    inputs = [RUN/(n+'.json') for n in ('report','states','contacts')]
    inputs += [Path(__file__).resolve(),Path(__file__).with_name('initial_overlap.py'),Path(__file__).with_name('replay_contact_geometry.py'),Path(__file__).with_name('render_best_run_video.py')]
    result = {'native_contact_rows':len(native_rows),'native_hand_shape_filters':filters,
        'all_hand_shape_pairs_share_exclusion_bit':shared_bit,'audit_native_initializations':1,'audit_explicit_physics_steps':native_steps,
        'source_left_shapes':len(left),'source_right_shapes':len(right),'source_pair_count_per_state':len(left)*len(right),
        'source_negative_state_count':len(negative),'first_negative_state':negative[0] if negative else None,
        'worst_source_state':worst,'selected_samples':[samples[s] for s in (0,120,240)],
        'gap_semantics':'MuJoCo source convex-shape signed query; negative supports geometric overlap, magnitude is not calibrated PhysX penetration depth.',
        'input_sha256':{str(p):sha(p) for p in inputs},'native_scene_source_sha256':report['source_sha256']}
    (OUT/'report.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (OUT/'samples.json').write_text(json.dumps(samples,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('native_contact_rows','all_hand_shape_pairs_share_exclusion_bit','source_negative_state_count','first_negative_state','worst_source_state')},indent=2))


if __name__=='__main__':
    main()
