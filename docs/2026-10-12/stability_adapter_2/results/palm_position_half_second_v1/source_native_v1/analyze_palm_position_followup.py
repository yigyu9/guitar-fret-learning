"""Compare the same approved controls through 0.5s; no new physics or queries."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results-dir', type=Path, required=True)
    parser.add_argument('--reference-run', type=Path, required=True)
    parser.add_argument('--prior-results', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve previous comparison')
    reference = read(args.reference_run/'report.json')
    prior = read(args.prior_results/'comparison.json')
    if not all(prior['checks'].values()) or not all(sha(p)==h for p,h in prior['input_sha256'].items()):
        raise ValueError('prior 0.1s contracts or sources differ')
    inputs, rows, raw = dict(prior['input_sha256']), [], {}
    prefix_checks = {}
    for mode in ('PI', 'RATE_PI', 'PALM_RATE'):
        folder = args.results_dir/mode
        paths = [folder/(n+'.json') for n in ('report', 'trace', 'states', 'controls', 'contacts', 'hands', 'queries', 'initial_source')]
        report, trace, states, controls, contacts, hands, queries, initial = [read(p) for p in paths]
        if not all(report['checks'].values()) or not initial['accepted']:
            raise ValueError('native trial contracts failed: '+mode)
        for name, samples, count, first in (
                ('states', states, 121, 0), ('trace', trace, 121, 0), ('hands', hands, 121, 0),
                ('queries', queries, 121, 0), ('controls', controls, 120, 1), ('contacts', contacts, 120, 1)):
            if len(samples)!=count:
                raise ValueError('trial length differs: '+mode+'/'+name)
            if name!='trace' and [s['physics_step'] for s in samples]!=list(range(first, first+count)):
                raise ValueError('trial step alignment differs: '+mode+'/'+name)
            if name in ('trace', 'queries', 'contacts') and [s['time_s'] for s in samples]!=[k/240 for k in range(first, first+count)]:
                raise ValueError('trial time alignment differs: '+mode+'/'+name)
        if [c['updated_before_step'] for c in controls]!=[k%4==0 for k in range(120)]:
            raise ValueError('thirty control update alignment differs: '+mode)
        for name, samples, count in (('states', states, 25), ('trace', trace, 25),
                ('controls', controls, 24), ('contacts', contacts, 24), ('hands', hands, 25),
                ('queries', queries, 25)):
            path = args.prior_results/mode/(name+'.json')
            prefix_checks[mode+'/'+name] = samples[:count]==read(path)
            inputs[str(path.resolve())] = sha(path)
        torque = read(folder/'leg_torques.json')
        if len(torque)!=121 or not np.isfinite(np.asarray(torque, dtype=float)).all():
            raise ValueError('finite 121-sample leg torque record required: '+mode)
        old_torque_path = args.prior_results/mode/'leg_torques.json'
        prefix_checks[mode+'/leg_torques'] = torque[:25]==read(old_torque_path)
        inputs[str(old_torque_path.resolve())] = sha(old_torque_path)
        inputs[str((folder/'leg_torques.json').resolve())] = sha(folder/'leg_torques.json')
        inputs.update(report['input_sha256'])
        inputs.update({str(p.resolve()):sha(p) for p in paths})
        q0, arm = np.array(report['initial_joint_targets_rad']), np.array(report['arm_indices'])
        q = np.array([[d['pos'] for d in s['human_dof_states']] for s in states])
        native_low, native_high = np.array(reference['native_joint_lower_rad']), np.array(reference['native_joint_upper_rad'])
        violations = np.maximum(np.maximum(native_low[arm]-q[:, arm], q[:, arm]-native_high[arm]), 0)
        updates = [c for c in controls if c['updated_before_step']]
        previous, changes = q0[arm], []
        for update in updates:
            target = np.array(update['final_arm_targets_rad'])
            changes.append(float(np.abs(target-previous).max()))
            previous = target
        native_rows = [c for sample in contacts for c in sample['contacts']
            if any(n.startswith('guitar/') for n in (c['body0_name'], c['body1_name']))]
        def side_rows(prefix):
            return sum(any(n.startswith(prefix) for n in (c['body0_name'], c['body1_name'])) for c in native_rows)
        active = []
        for c in updates:
            delta = np.array(c['applied_delta_rad'])
            lo = np.maximum(-.15, np.array(report['diagnostic_lower_rad'])-q0[arm])
            hi = np.minimum(.15, np.array(report['diagnostic_upper_rad'])-q0[arm])
            if 'delta_lower_rad' in c:
                lo, hi = np.array(c['delta_lower_rad']), np.array(c['delta_upper_rad'])
            active.append(int(((np.abs(delta-lo)<=1e-8)|(np.abs(delta-hi)<=1e-8)).sum()))
        rows.append({'mode':mode, 'max_guitar_position_error_mm':report['max_position_error_m']*1000,
            'max_guitar_rotation_error_deg':report['max_rotation_error_deg'],
            'max_left_palm_displacement_mm':report['max_left_palm_displacement_m']*1000,
            'max_arm_coordinate_deviation_deg':float(np.abs(q[:, arm]-q0[arm]).max()*180/np.pi),
            'max_actual_arm_native_limit_violation_deg':float(violations.max()*180/np.pi),
            'max_final_target_change_per_update_rad':max(changes),
            'target_changes_rad':changes, 'active_bound_axis_counts_at_updates':active,
            'PI_demand_differs_from_applied_physics_samples':sum(any(c['saturated']) for c in controls),
            'left_contact_rows':side_rows('human/LH:'), 'right_contact_rows':side_rows('human/RH:'),
            'max_applied_strap_tension_n':max(t['last_applied_tension_n'] for t in trace[1:]),
            'min_palm_up_dot':report['min_palm_up_dot'],
            'observed_upward_proxy_all_samples':report['observed_upward_proxy_all_samples'],
            'all_local_neck_projections_in_range':all(h['neck_projection_in_range'] for h in hands),
            'max_anti_windup_calculations':max(len(c.get('anti_windup_iterations', [])) for c in controls),
            'source_point_reconstruction_max_error_m':max(float(np.linalg.norm(np.array(h['palm_center_world_m'])-np.array(p['left_source_world_m']))) for h,p in zip(hands,queries))})
        raw[mode] = {'states':states, 'trace':trace, 'controls':controls}
    paths = [Path(__file__).resolve(), args.reference_run/'report.json', args.results_dir/'continuation.json', args.results_dir/'native_execution_v1.json']
    paths.append(args.prior_results/'comparison.json')
    inputs.update({str(p.resolve()):sha(p) for p in paths})
    current = all(sha(p)==h for p,h in inputs.items())
    executions = read(args.results_dir/'native_execution_v1.json')
    checks = {'three_trials_contracts_pass':True, 'consumed_sources_current':current,
        'all_three_prior_0p1s_prefixes_exact':all(prefix_checks.values()),
        'three_actual_native_exits_zero':len(executions)==3 and all(e['returncode']==0 for e in executions),
        'source_point_reconstruction_consistent':all(r['source_point_reconstruction_max_error_m']<1e-8 for r in rows),
        'new_conditions_rate_bound':all(r['max_final_target_change_per_update_rad']<=.02+2e-7 for r in rows[1:])}
    guitar_equal = {mode:all(a['guitar_body_states']==b['guitar_body_states'] for a,b in zip(raw['PI']['states'],raw[mode]['states'])) for mode in ('RATE_PI','PALM_RATE')}
    matched_right_difference = max(float(np.abs(np.array(a['final_arm_targets_rad'])[12:]-np.array(b['final_arm_targets_rad'])[12:]).max()) for a,b in zip(raw['RATE_PI']['controls'],raw['PALM_RATE']['controls']))
    result = {'scope':'three 0.5s target-controller diagnostics, not physical stability/playing success',
        'checks':checks, 'rows':rows, 'all_saved_guitar_body_states_exactly_equal_to_PI':guitar_equal,
        'prior_0p1s_prefix_checks':prefix_checks,
        'max_right_delivered_target_difference_RATE_PI_vs_PALM_RATE_rad':matched_right_difference,
        'semantics':'saturated field counts PI demand/applied mismatch; under position task this is not proof of active bounds. Active bounds are counted separately at updates. Contacts are rows, not force or sustained support. Upper proxy is not calibrated anatomical normal.',
        'input_sha256':inputs, 'stability_success':None}
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'checks':checks, 'rows':rows, 'guitar_body_states_exact':guitar_equal},indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__=='__main__':
    main()
