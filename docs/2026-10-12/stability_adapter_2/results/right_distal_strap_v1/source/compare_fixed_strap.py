"""Audit saved fixed-length PI trials; no rollout or stability certificate."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir',type=Path,required=True)
    parser.add_argument('--reference-dir',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve existing comparison')
    audit = read(args.results_dir/'strap_inputs.json')
    base_run = args.results_dir/'short/load_00n/off'
    base = read(base_run/'report.json')
    state0 = read(base_run/'states.json')[0]
    rows = []
    for group in ('short','hold_05s','hold_1s'):
        for run in sorted((args.results_dir/group).glob('*/*')):
            if not (run/'report.json').exists():
                continue
            report,trace,states,contacts,controls = [read(run/(n+'.json')) for n in ('report','trace','states','contacts','controls')]
            matched = [r for r in audit['records'] if r['settings']==report['initial_settings']]
            q = np.array([[v['pos'] for v in s['human_dof_states']] for s in states])
            target = np.array(report['initial_joint_targets_rad']);arm = report['arm_indices']
            command = np.array([r['final_arm_targets_rad'] for r in controls])
            counts,steps,up = {},{},[]
            for s in states:
                body = s['human_body_states'];names = report['human_body_names']
                p = {n:np.array([body[names.index(n)]['pose']['p'][a] for a in ('x','y','z')]) for n in ('L_Wrist','LH:middle1','LH:index1','LH:pinky1')}
                normal = np.cross(p['LH:middle1']-p['L_Wrist'],p['LH:index1']-p['LH:pinky1'])
                up.append(float(normal[2]/np.linalg.norm(normal)))
            for sample in contacts:
                for c in sample['contacts']:
                    pair = (c['body0_name'],c['body1_name'])
                    if any(n.startswith('guitar/') for n in pair):
                        for n in pair:
                            if n.startswith('human/'):
                                counts[n] = counts.get(n,0)+1
                                steps.setdefault(n,set()).add(sample['physics_step'])
            checks = {'native_checks':all(report['checks'].values()),
                'accepted_input':bool(matched) and all(r['accepted_for_diagnostic'] for r in matched),
                'initial_native_state_same':states[0]==state0,
                'first_law_tension_matches_input':bool(matched) and all(abs(trace[1]['last_applied_tension_n']-r['initial_law_tension_n'])<1e-9 for r in matched),
                'fixed_rest_length':all(s['strap_rest_length_m']==report['absolute_rest_length_m'] for s in trace),
                'target_bounds':bool(((command>=np.array(report['diagnostic_lower_rad'])-2e-7)&(command<=np.array(report['diagnostic_upper_rad'])+2e-7)).all() and (np.abs(command-target[arm])<=.15+2e-7).all()),
                'schedule':sum(c['updated_before_step'] for c in controls)==(0 if report['mode']=='off' else (report['physics_steps']+3)//4),
                'sample_counts':len(states)==len(trace)==report['physics_steps']+1 and len(contacts)==len(controls)==report['physics_steps'],
                'execution_sources_current':all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in report['source_sha256'].items())}
            for key in ('initial_joint_targets_rad','native_pd_kp','native_pd_kd','native_drive_modes','native_effort_caps_nm','physics_parameters','guitar_goal_position_m','guitar_goal_quaternion_xyzw','diagnostic_lower_rad','diagnostic_upper_rad','initial_route_length_m','controller'):
                checks[key+'_same'] = report[key]==base[key]
            if group!='short':
                short = args.results_dir/'short'/run.parent.name/run.name
                checks['short_prefix_exact'] = all(read(run/(n+'.json'))[:25 if n in ('states','trace','leg_torques') else 24]==read(short/(n+'.json')) for n in ('states','trace','contacts','controls','leg_torques'))
            rows.append({'run':str(run.resolve()),'group':group,'length_id':run.parent.name,'mode':report['mode'],'duration_s':trace[-1]['time_s'],'checks':checks,
                'rest_length_m':report['absolute_rest_length_m'],'initial_law_tension_n':trace[1]['last_applied_tension_n'],
                'max_position_error_m':max(s['position_error_m'] for s in trace),'max_rotation_error_deg':max(s['rotation_error_deg'] for s in trace),
                'end_position_error_m':trace[-1]['position_error_m'],'end_rotation_error_deg':trace[-1]['rotation_error_deg'],
                'end_linear_speed_mps':trace[-1]['linear_speed_mps'],'end_angular_speed_rad_s':trace[-1]['angular_speed_rad_s'],
                'max_applied_tension_n':max(s['last_applied_tension_n'] for s in trace[1:]),
                'max_arm_raw_drift_deg':float(np.rad2deg(np.abs(q[:,arm]-target[arm])).max()),
                'max_arm_scalar_limit_violation_deg':float(np.rad2deg(np.maximum(np.maximum(np.array(report['native_joint_lower_rad'])[arm]-q[:,arm],q[:,arm]-np.array(report['native_joint_upper_rad'])[arm]),0)).max()),
                'min_left_palm_up_dot':min(up),'saturated_physics_samples':sum(any(c['saturated']) for c in controls),
                'contact_rows_by_human_body':counts,'contact_physics_samples_by_human_body':{n:len(v) for n,v in steps.items()},
                'contact_first_last_step_by_human_body':{n:[min(v),max(v)] for n,v in steps.items()}})
    checks = {'initial_audit_sources_unchanged':audit['runtime_sources_unchanged'],
        'zero_load_modes_reproduce_previous_raw':all(read(args.results_dir/'short/load_00n'/mode/(n+'.json'))==read(args.reference_dir/'short'/mode/(n+'.json')) for mode in ('off','on') for n in ('states','trace','contacts','leg_torques'))}
    paths = list(args.results_dir.rglob('*.json'))+[args.reference_dir/'short'/mode/(n+'.json') for mode in ('off','on') for n in ('states','trace','contacts','leg_torques')]+[Path(__file__).resolve()]
    out = {'scope':'fixed absolute strap lengths, same humanoid pose and existing PI; no stability success','reference_dir':str(args.reference_dir.resolve()),'checks':checks,'rows':rows,
        'semantics':'T0 is initial law tension, not constant runtime force. Contact rows are not force or cause; first/last are not continuity. Saturation is held 240Hz samples.',
        'input_sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    args.out.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'failed_rows':{r['run']:[k for k,v in r['checks'].items() if not v] for r in rows if not all(r['checks'].values())}}))
    if not rows or not all(checks.values()) or not all(all(r['checks'].values()) for r in rows):
        raise SystemExit(1)


if __name__=='__main__':
    main()
