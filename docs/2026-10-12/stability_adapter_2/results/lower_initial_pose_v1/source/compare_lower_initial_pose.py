"""Audit bounded lower initial settings and saved 0.1-second native results."""
import argparse
import json
from pathlib import Path

from .replay_contact_geometry import recorded_probe
from .initial_overlap import query_pairs, query_ground
from .environment import np


def load(run,name):
    return json.loads((run/(name+'.json')).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if (args.out/'comparison.json').exists():
        raise FileExistsError('preserve existing comparison')
    search = load(args.out/'search_verified','search')
    baseline = load(args.out/'baseline','report')
    reference = load(args.out/'baseline','states')[0]
    names = baseline['human_joint_names']
    leg_indices = [names.index(n) for n in baseline['leg_torque_joint_names']]
    initial = np.array(baseline['initial_joint_targets_rad'])
    nonleg = [i for i in range(len(names)) if i not in leg_indices]
    leg_bodies = [i for i,n in enumerate(baseline['human_body_names']) if n in
        {side+'_'+body for side in ('L','R') for body in ('Hip','Knee','Ankle','Toe')}]
    fixed_bodies = [i for i in range(len(baseline['human_body_names'])) if i not in leg_bodies]
    checks,rows = {},[]
    for number,name in enumerate(('baseline','c01','c02','c03')):
        run = args.out/name
        report,states,contacts = load(run,'report'),load(run,'states'),load(run,'contacts')
        trace = load(run,'trace')
        probe = recorded_probe(run,0,include_ground=True)
        geometry,ground = query_pairs(*probe),query_ground(*probe)
        static = {'human_guitar':geometry,'ground':ground}
        path = run/'initial_source_geometry.json'
        if path.exists():
            if json.loads(path.read_text())!=static:
                raise FileExistsError('existing source geometry differs')
        else:
            path.write_text(json.dumps(static,indent=2)+'\n')
        row_id = search['baseline_id'] if number==0 else search['selected_ids'][number-1]
        selected = search['evaluations'][row_id]
        q = np.array([[v['pos'] for v in s['human_dof_states']] for s in states])
        target = np.array(report['initial_joint_targets_rad'])
        lower,upper = np.array(report['native_joint_lower_rad']),np.array(report['native_joint_upper_rad'])
        violation = np.maximum(lower-q,q-upper)
        knee_index = report['human_body_names'].index('L_Knee')
        neck_samples = [s for s in contacts if any(
            {p['body0_name'],p['body1_name']}=={'human/L_Knee','guitar/guitar'} for p in s['contacts'])]
        body_angles = []
        for s in states:
            for i in leg_bodies:
                a=np.array([states[0]['human_body_states'][i]['pose']['r'][v] for v in ('x','y','z','w')])
                b=np.array([s['human_body_states'][i]['pose']['r'][v] for v in ('x','y','z','w')])
                dot=abs(np.dot(a/np.linalg.norm(a),b/np.linalg.norm(b)))
                body_angles.append(float(np.rad2deg(2*np.arccos(np.clip(dot,0,1)))))
        audit = {'native_run_checks':all(report['checks'].values()),
            'initial_settings_match_search':report['initial_settings']==selected['settings'],
            'source_queries_match_search':geometry==selected['human_guitar_geometry'] and ground==selected['ground_geometry'],
            'initial_main_torso_targets_unchanged':bool(np.array_equal(target[nonleg],initial[nonleg])),
            'approved_initial_offsets':bool(np.abs(target-initial).max()<=.05+2e-7),
            'upper_body_root_initial_states_unchanged':all(states[0]['human_body_states'][i]==reference['human_body_states'][i] for i in fixed_bodies),
            'all_guitar_initial_states_unchanged':states[0]['guitar_body_states']==reference['guitar_body_states']}
        for key in ('native_pd_kp','native_pd_kd','native_drive_modes','native_effort_caps_nm',
                    'native_joint_lower_rad','native_joint_upper_rad','physics_parameters',
                    'absolute_rest_length_m','guitar_goal_position_m','guitar_goal_quaternion_xyzw','source_sha256'):
            audit[key+'_unchanged']=report[key]==baseline[key]
        checks[name]=audit
        rows.append({'name':name,'search_evaluation_id':row_id,'settings':report['initial_settings'],
            'initial_ground_minimum_gap_m':ground['minimum_gap_m'],
            'initial_ground_negative_pair_count':ground['negative_gap_pair_count'],
            'initial_human_guitar_negative_pair_count':geometry['negative_gap_pair_count'],
            'max_position_error_m':report['max_position_error_m'],
            'max_source_position_error_m':report['max_source_position_error_m'],
            'max_rotation_error_deg':report['max_rotation_error_deg'],
            'max_leg_raw_drift_deg':float(np.rad2deg(np.abs(q[:,leg_indices]-target[leg_indices])).max()),
            'max_leg_native_scalar_limit_violation_deg':float(np.rad2deg(np.maximum(violation[:,leg_indices],0)).max()),
            'max_leg_body_orientation_drift_deg':max(body_angles),
            'left_knee_minimum_z_m':min(s['human_body_states'][knee_index]['pose']['p']['z'] for s in states),
            'left_knee_maximum_z_m':max(s['human_body_states'][knee_index]['pose']['p']['z'] for s in states),
            'first_neck_knee_contact_time_s':neck_samples[0]['time_s'] if neck_samples else None,
            'max_applied_strap_tension_n':report['max_applied_strap_tension_n'],
            'max_torso_drift_deg':max(abs(v) for s in trace for v in s['torso_drift_deg'])})
    historical = args.out.parent/'guitar_z_trial_v1/z5'
    checks['baseline_reproduces_previous_z5']={name:load(args.out/'baseline',name)==load(historical,name)
        for name in ('states','contacts','trace','leg_torques')}
    output={'scope':'bounded initial lower pose diagnostic; no feedback or stability success',
        'checks':checks,'rows':rows,'search_is_local_not_exhaustive':True}
    (args.out/'comparison.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps(output,indent=2))
    if not all(all(v.values()) for v in checks.values()):
        raise SystemExit(1)


if __name__=='__main__':
    main()
