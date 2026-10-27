"""Compare the approved initial Z trial using saved native states only."""
import argparse
import json
from pathlib import Path

from .replay_contact_geometry import recorded_probe
from .initial_overlap import query_pairs
import numpy as np


def load(run, name):
    return json.loads((run / (name + '.json')).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if (args.out / 'comparison.json').exists():
        raise FileExistsError('preserve existing comparison')
    rows = []
    runs = [args.out / name for name in ('h0', 'z5')]
    reports = [load(run, 'report') for run in runs]
    states = [load(run, 'states') for run in runs]
    for run, report, history in zip(runs, reports, states):
        trace, contacts = load(run, 'trace'), load(run, 'contacts')
        geometry = query_pairs(*recorded_probe(run, 0))
        geometry_path = run / 'initial_source_geometry.json'
        if geometry_path.exists():
            if json.loads(geometry_path.read_text()) != geometry:
                raise FileExistsError('existing source geometry differs; preserve it')
        else:
            geometry_path.write_text(json.dumps(geometry, indent=2) + '\n')
        pairs = geometry['pairs_within_limit']
        initial = np.asarray(report['initial_joint_targets_rad'])
        indices = [report['human_joint_names'].index(name) for name in report['leg_torque_joint_names']]
        q = np.asarray([[s['pos'] for s in h['human_dof_states']] for h in history])
        knee_contacts = [sample for sample in contacts if any(
            {c['body0_name'], c['body1_name']} == {'human/L_Knee', 'guitar/guitar'}
            for c in sample['contacts'])]
        first_guitar = [c for c in contacts[0]['contacts']
            if c['body0_name'].startswith('guitar/') or c['body1_name'].startswith('guitar/')]
        rows.append({'name':run.name,
            'initial_z_offset_m':report['initial_settings']['guitar_initial_z_offset_m'],
            'max_position_error_m':report['max_position_error_m'],
            'max_source_position_error_m':report['max_source_position_error_m'],
            'max_rotation_error_deg':report['max_rotation_error_deg'],
            'max_applied_strap_tension_n':report['max_applied_strap_tension_n'],
            'initial_route_length_m':report['initial_route_length_m'],
            'absolute_rest_length_m':report['absolute_rest_length_m'],
            'max_leg_raw_drift_deg':float(np.rad2deg(np.abs(q[:, indices]-initial[indices])).max()),
            'max_torso_drift_deg':max(abs(v) for s in trace for v in s['torso_drift_deg']),
            'source_initial_negative_pair_count':geometry['negative_gap_pair_count'],
            'source_initial_hip_gap_m':min(p['signed_gap_m'] for p in pairs if p['human_body']=='R_Hip'),
            'source_initial_elbow_gap_m':min(p['signed_gap_m'] for p in pairs if p['human_body']=='R_Elbow'),
            'first_completed_step_guitar_contacts':first_guitar,
            'first_neck_knee_contact_time_s':knee_contacts[0]['time_s'] if knee_contacts else None,
            'first_neck_knee_contacts':knee_contacts[0] if knee_contacts else None})
    a, b = states[0][0], states[1][0]
    guitar_delta = [[bs['pose']['p'][axis]-as_['pose']['p'][axis] for axis in ('x','y','z')]
        for as_, bs in zip(a['guitar_body_states'], b['guitar_body_states'])]
    checks = {'all_native_run_checks':all(all(r['checks'].values()) for r in reports),
        'human_initial_states_identical':a['human_body_states']==b['human_body_states'] and a['human_dof_states']==b['human_dof_states'],
        'all_guitar_bodies_translated_only_z_5mm':bool(np.allclose(guitar_delta,[0,0,.005],atol=2e-7,rtol=0)),
        'guitar_rotations_velocities_identical':all(as_['pose']['r']==bs['pose']['r'] and as_['vel']==bs['vel']
            for as_,bs in zip(a['guitar_body_states'],b['guitar_body_states']))}
    for key in ('initial_joint_targets_rad','native_pd_kp','native_pd_kd','native_drive_modes',
                'native_effort_caps_nm','physics_parameters','absolute_rest_length_m',
                'guitar_goal_quaternion_xyzw','guitar_source_position_m','source_sha256'):
        checks[key+'_identical'] = reports[0][key]==reports[1][key]
    historical = Path(__file__).resolve().parents[1] / 'docs/2026-10-12/stability_adapter_2/results/physx_contact_v1/h0_detailed'
    for name in ('states','contacts'):
        checks['h0_reproduces_historical_'+name] = load(runs[0],name)==load(historical,name)
    old_trace, new_trace = load(historical,'trace'),load(runs[0],'trace')
    checks['h0_reproduces_all_historical_trace_fields'] = len(old_trace)==len(new_trace) and all(
        all(new[k]==v for k,v in old.items()) for old,new in zip(old_trace,new_trace))
    output = {'scope':'paired 0.1-second native diagnostic; no feedback or stability success',
        'checks':checks,'rows':rows,'geometry_semantics':'source-shape MuJoCo signed gaps; not native cooked-mesh clearance or calibrated penetration depth'}
    (args.out / 'comparison.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'rows':[{k:v for k,v in row.items() if 'contacts' not in k} for row in rows]},indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
