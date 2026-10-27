"""Analyze saved Shoulder PD comparisons without creating a simulator."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ('states', 'trace', 'controls', 'contacts', 'hands', 'queries', 'leg_torques')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve previous analysis')
    base_path = ROOT/'docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/on/report.json'
    base = read(base_path)
    inputs = {str(p.resolve()):sha(p) for p in (base_path, Path(__file__))}
    rows = []
    baseline_initial = None
    for group, steps in (('short', 24), ('hold_05s', 120)):
        baseline_pd = None
        for stiffness in (200, 300):
            run = args.run/group/('kp'+str(stiffness))
            report, native = read(run/'report.json'), read(run/'native/report.json')
            data = {n:read(run/'native'/(n+'.json')) for n in RAW}
            forces = read(run/'sensors.json')
            if not all(report['checks'].values()) or len(native['checks']) != 13 or not all(native['checks'].values()):
                raise ValueError('rollout contracts failed')
            if report['stiffness'] != stiffness or report['physics_steps'] != steps or native['mode'] != 'PALM_RATE':
                raise ValueError('comparison identity differs')
            if any(len(data[n]) != (steps if n in ('controls', 'contacts') else steps+1) for n in RAW):
                raise ValueError('raw coverage differs')
            if any([r['physics_step'] for r in data[n]] != list(range(steps+1)) for n in ('states', 'hands', 'queries')):
                raise ValueError('state/query/hand alignment differs')
            if any([r['physics_step'] for r in data[n]] != list(range(1, steps+1)) for n in ('controls', 'contacts')):
                raise ValueError('control/contact alignment differs')
            if ([t['time_s'] for t in data['trace']] != [k/240 for k in range(steps+1)] or
                [c['updated_before_step'] for c in data['controls']] != [k%4 == 0 for k in range(steps)] or
                [f['physics_step'] for f in forces] != list(range(1, steps+1)) or
                [f['time_s'] for f in forces] != [k/240 for k in range(1, steps+1)]):
                raise ValueError('physical/control/force timing differs')
            if baseline_initial is None:
                baseline_initial = data['states'][0]
            if data['states'][0] != baseline_initial:
                raise ValueError('full initial state differs')
            if stiffness == 200:
                baseline_pd = report['PD_after']
            expected = {n:list(v) for n, v in baseline_pd.items()}
            shoulder = [base['human_joint_names'].index(s+'_Shoulder_'+a) for s in ('L', 'R') for a in ('x', 'y', 'z')]
            for i in shoulder:
                expected['stiffness'][i] = stiffness
            if report['shoulder_indices'] != shoulder or report['PD_before'] != baseline_pd or report['PD_after'] != expected:
                raise ValueError('only approved six stiffness fields may differ')
            if group == 'hold_05s':
                short = args.run/'short'/('kp'+str(stiffness))
                if not all(data[n][:24 if n in ('controls', 'contacts') else 25] == read(short/'native'/(n+'.json')) for n in RAW):
                    raise ValueError('same-condition raw short prefix differs')
                if forces[:24] != read(short/'sensors.json'):
                    raise ValueError('same-condition force prefix differs')
            q = np.array([[d['pos'] for d in s['human_dof_states']] for s in data['states']])
            targets = np.array([c['final_arm_targets_rad'] for c in data['controls']])
            force = np.array([f['native_total_DOF_force'] for f in forces])
            if q.shape != (steps+1, 105) or targets.shape != (steps, 24) or force.shape != (steps, 105) or not all(np.isfinite(v).all() for v in (q, targets, force)):
                raise ValueError('finite DOF/target/force layouts required')
            arm = np.array(base['arm_indices'])
            gap = np.degrees(targets-q[1:, arm])
            violation = np.maximum(np.maximum(np.array(base['native_joint_lower_rad'])[arm]-q[:, arm],
                q[:, arm]-np.array(base['native_joint_upper_rad'])[arm]), 0)
            palm = np.array([r['left_source_world_m'] for r in data['queries']])
            palm_error = np.linalg.norm(palm-palm[0], axis=1)*1000
            contact_names = [name for sample in data['contacts'] for c in sample['contacts']
                if any(n.startswith('guitar/') for n in (c['body0_name'], c['body1_name']))
                for name in (c['body0_name'], c['body1_name']) if name.startswith('human/')]
            trace = data['trace']
            position = np.array([[s['guitar_body_states'][0]['pose']['p'][a] for a in ('x', 'y', 'z')]
                                 for s in data['states']])
            quat = np.array([[s['guitar_body_states'][0]['pose']['r'][a] for a in ('x', 'y', 'z', 'w')]
                             for s in data['states']])
            quat = np.array([v/np.linalg.norm(v) for v in quat])
            p_error = np.linalg.norm(position-np.array(base['guitar_goal_position_m']), axis=1)*1000
            r_error = np.array([np.degrees(2*np.arccos(np.clip(abs(v@np.array(base['guitar_goal_quaternion_xyzw'])), 0, 1))) for v in quat])
            if not (np.allclose(p_error, [t['position_error_m']*1000 for t in trace], atol=1e-9, rtol=0) and
                    np.allclose(position, [t['guitar_position_m'] for t in trace], atol=1e-12, rtol=0) and
                    np.allclose(quat, [t['guitar_quaternion_xyzw'] for t in trace], atol=1e-12, rtol=0) and
                    np.allclose(r_error, [t['rotation_error_deg'] for t in trace], atol=1e-8, rtol=0)):
                raise ValueError('trace error fields disagree with recomputed goal errors')
            rows.append({'group':group, 'stiffness':stiffness, 'run':str(run.resolve()),
                'max_guitar_position_mm':float(p_error.max()), 'final_guitar_position_mm':float(p_error[-1]),
                'max_guitar_rotation_deg':float(r_error.max()), 'final_guitar_rotation_deg':float(r_error[-1]),
                'max_left_palm_displacement_mm':float(palm_error.max()), 'final_left_palm_displacement_mm':float(palm_error[-1]),
                'max_actual_arm_scalar_limit_violation_deg':float(np.degrees(violation).max()),
                'max_completed_target_actual_gap_deg':float(np.abs(gap).max()),
                'completed_gap_by_arm_joint_deg':{base['human_joint_names'][i]:float(np.abs(gap[:, k]).max()) for k, i in enumerate(arm)},
                'Shoulder_total_DOF_force_signed_min_max_Nm':{base['human_joint_names'][i]:[float(force[:, i].min()), float(force[:, i].max())] for i in shoulder},
                'LH_contact_rows':sum(n.startswith('human/LH:') for n in contact_names),
                'RH_contact_rows':sum(n.startswith('human/RH:') for n in contact_names),
                'observed_upward_proxy_all_samples':all(h['palm_normal_valid'] and h['palm_up_dot'] >= 0 for h in data['hands']),
                'observed_local_neck_condition_all_samples':all(h['neck_projection_in_range'] and h['palm_height_vs_local_lower_m'] <= 0 for h in data['hands']),
                'max_applied_tension_N':max(t['last_applied_tension_n'] for t in trace[1:])})
            for p, h in report['input_sha256'].items():
                if sha(p) != h or (p in inputs and inputs[p] != h):
                    raise ValueError('source SHA differs or maps conflict')
                inputs[p] = h
            for p in (run/'report.json', run/'sensors.json'):
                inputs[str(p.resolve())] = sha(p)
    result = {'rows':rows, 'input_sha256':inputs,
        'checks':{'four_rollout_contracts_pass':True, 'only_six_stiffness_fields_differ':True,
                  'same_full_initial_states':True, 'exact_sample_schedules':True,
                  'seven_raw_and_force_short_prefixes_exact':True, 'goal_errors_recomputed':True,
                  'all_sources_current':all(sha(p) == h for p, h in inputs.items())},
        'scope':'saved comparison, scalar gaps are native coordinates; total force is not actuator-only torque/PD cause; no guitar stability or playing certificate'}
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'checks':result['checks'], 'rows':rows}, indent=2))
    if not all(result['checks'].values()):
        raise AssertionError(result['checks'])


if __name__ == '__main__':
    main()
