"""Saved-state comparison of joint-hold OFF/ON; no native simulation."""
import argparse
import hashlib
import json
from pathlib import Path

from .environment import np
from .compare_pose_strap import load, saved_hand
from .replay_contact_geometry import recorded_probe
from .search_hand_support import palm_neck_gap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir',type=Path,required=True)
    parser.add_argument('--reference-run',type=Path)
    args = parser.parse_args()
    out = args.results_dir/'comparison.json'
    if out.exists():
        raise FileExistsError('preserve existing comparison')
    reference = load(args.results_dir/'short/off/report.json')
    rows = []
    for group in ('short','hold_05s','hold_1s'):
        for mode in ('off','on'):
            run = args.results_dir/group/mode
            report,trace,states,controls,contacts = [load(run/(n+'.json')) for n in ('report','trace','states','controls','contacts')]
            q = np.array([[v['pos'] for v in s['human_dof_states']] for s in states])
            initial,arm = np.array(report['initial_joint_targets_rad']),report['arm_indices']
            normals = []
            for state in states:
                bodies = state['human_body_states']
                points = {n:np.array([bodies[report['human_body_names'].index(n)]['pose']['p'][axis] for axis in ('x','y','z')]) for n in ('L_Wrist','LH:middle1','LH:index1','LH:pinky1')}
                normal = np.cross(points['LH:middle1']-points['L_Wrist'],points['LH:index1']-points['LH:pinky1'])
                normals.append(float(normal[2]/np.linalg.norm(normal)))
            lh = [s['time_s'] for s in contacts for c in s['contacts'] if any(n.startswith('guitar/') for n in (c['body0_name'],c['body1_name'])) and any(n.startswith('human/LH:') for n in (c['body0_name'],c['body1_name']))]
            target = np.array([c['final_arm_targets_rad'] for c in controls])
            checks = {'native_run_checks':all(report['checks'].values()),
                'target_inside_diagnostic_and_delta_bounds':bool(((target>=np.array(report['diagnostic_lower_rad'])-2e-7)&(target<=np.array(report['diagnostic_upper_rad'])+2e-7)).all() and (np.abs(target-initial[arm])<=.15+2e-7).all()),
                'controller_schedule':sum(c['updated_before_step'] for c in controls)==(0 if mode=='off' else (report['physics_steps']+3)//4),
                'runtime_sources_match_current':all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in report['source_sha256'].items()),
                'all_control_samples_finite':bool(np.isfinite(target).all() and all(np.isfinite(c['integral_rad_s']).all() for c in controls))}
            for key in ('initial_settings','initial_joint_targets_rad','native_pd_kp','native_pd_kd','native_drive_modes','native_effort_caps_nm','physics_parameters','guitar_goal_position_m','guitar_goal_quaternion_xyzw','absolute_rest_length_m','source_sha256'):
                checks[key+'_unchanged'] = report[key]==reference[key]
            rows.append({'run':str(run.resolve()),'group':group,'mode':mode,'duration_s':trace[-1]['time_s'],'checks':checks,
                'max_position_error_m':max(s['position_error_m'] for s in trace),'max_rotation_error_deg':max(s['rotation_error_deg'] for s in trace),
                'rms_position_error_m':float(np.sqrt(np.mean([s['position_error_m']**2 for s in trace]))),
                'rms_rotation_error_deg':float(np.sqrt(np.mean([s['rotation_error_deg']**2 for s in trace]))),
                'max_arm_raw_drift_deg':float(np.rad2deg(np.abs(q[:,arm]-initial[arm])).max()),
                'rms_arm_raw_drift_deg':float(np.rad2deg(np.sqrt(np.mean((q[:,arm]-initial[arm])**2)))),
                'max_torso_raw_drift_deg':max(abs(v) for s in trace for v in s['torso_drift_deg']),
                'max_arm_scalar_limit_violation_deg':float(np.rad2deg(np.maximum(np.maximum(np.array(report['native_joint_lower_rad'])[arm]-q[:,arm],q[:,arm]-np.array(report['native_joint_upper_rad'])[arm]),0)).max()),
                'min_left_palm_up_dot_all_physics_samples':min(normals),
                'saturated_physics_samples':sum(any(c['saturated']) for c in controls),
                'blocked_integral_physics_samples':sum(any(c['integral_blocked']) for c in controls),
                'max_applied_delta_rad':float(np.abs(target-initial[arm]).max()),
                'max_applied_strap_tension_n':max(s['last_applied_tension_n'] for s in trace[1:]),
                'left_hand_guitar_contact_rows':len(lh),'first_left_hand_contact_time_s':min(lh) if lh else None,
                'initial_hand':saved_hand(run,report,states[0]),'final_hand':saved_hand(run,report,states[-1]),
                'initial_palm_neck_hulls':palm_neck_gap(recorded_probe(run,0)),
                'final_palm_neck_hulls':palm_neck_gap(recorded_probe(run,report['physics_steps']))})
    reference_runs = [('short',args.reference_run)] if args.reference_run else [('short',args.results_dir.parent/'hand_support_v1/coupled_short/p08_load00'),('hold_05s',args.results_dir.parent/'hand_support_v1/coupled_hold_05s/p08_load00')]
    checks = {'paired_initial_native_states_identical':all(load(args.results_dir/group/'off/states.json')[0]==load(args.results_dir/group/'on/states.json')[0] for group in ('short','hold_05s','hold_1s')),
        'off_reproduces_previous_raw':all(load(args.results_dir/group/'off'/(n+'.json'))==load(old/(n+'.json')) for group,old in reference_runs for n in ('trace','states','contacts','leg_torques')),
        'long_prefix_matches_short':all(load(args.results_dir/group/mode/(n+'.json'))[:25 if n in ('trace','states','leg_torques') else 24]==load(args.results_dir/'short'/mode/(n+'.json')) for group in ('hold_05s','hold_1s') for mode in ('off','on') for n in ('trace','states','contacts','controls','leg_torques'))}
    paths = list(args.results_dir.rglob('*.json'))+[Path(__file__).resolve(),Path(__file__).with_name('run_joint_hold.py'),Path(__file__).with_name('joint_hold_residual.py'),Path(__file__).with_name('compare_pose_strap.py'),Path(__file__).with_name('search_hand_support.py'),Path(__file__).with_name('pose_strap_inputs.py'),Path(__file__).with_name('plot_neck_palm.py'),Path(__file__).with_name('replay_contact_geometry.py')]
    paths += [old/(n+'.json') for _,old in reference_runs for n in ('trace','states','contacts','leg_torques')]
    output = {'scope':'joint-error feedback actuator diagnostic; no guitar-error feedback, FK task rejection, rate limit, learning or stability success',
        'checks':checks,'rows':rows,'sample_semantics':'target/integral record precedes physics step; saturation counts repeated held values at 240Hz, not independent 60Hz control updates',
        'reference_runs':{group:str(old.resolve()) for group,old in reference_runs},
        'input_sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    out.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'failed_row_checks':{r['run']:[k for k,v in r['checks'].items() if not v] for r in rows if not all(r['checks'].values())}},indent=2))
    if not all(checks.values()) or not all(all(r['checks'].values()) for r in rows):
        raise SystemExit(1)


if __name__=='__main__':
    main()
