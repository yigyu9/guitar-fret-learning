"""Summarize saved total DOF forces and completed-step target gaps."""
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
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = read(args.run/'force_report.json')
    sensors = read(args.run/'sensors.json')
    states = read(args.run/'native/states.json')
    controls = read(args.run/'native/controls.json')
    native = read(args.run/'native/report.json')
    inputs = dict(report['input_sha256'])
    paths = [Path(__file__).resolve(), args.run/'force_report.json', args.run/'sensors.json']
    inputs.update({str(p.resolve()):sha(p) for p in paths})
    if not all(report['checks'].values()) or not all(sha(p)==h for p,h in inputs.items()):
        raise ValueError('sensor contracts or source hashes differ')
    names, arm = report['human_joint_names'], native['arm_indices']
    if len(names)!=105 or len(arm)!=24 or len(sensors)!=120 or len(states)!=121 or len(controls)!=120:
        raise ValueError('saved sample/layout coverage differs')
    if (report['t0_force_measurement'] is not None or
        [s['physics_step'] for s in sensors]!=list(range(1,121)) or
        [s['time_s'] for s in sensors]!=[k/240 for k in range(1,121)] or
        [s['physics_step'] for s in states]!=list(range(121)) or
        [c['physics_step'] for c in controls]!=list(range(120))):
        raise ValueError('completed-step/preceding-target alignment differs')
    force = np.array([s['native_total_DOF_force'] for s in sensors])
    actual = np.array([[q['pos'] for q in s['human_dof_states']] for s in states[1:]])
    targets = np.array([c['final_arm_targets_rad'] for c in controls])
    if force.shape!=(120,105) or actual.shape!=(120,105) or targets.shape!=(120,24):
        raise ValueError('force/state/target shapes differ')
    if not all(np.isfinite(a).all() for a in (force,actual,targets)):
        raise ValueError('finite saved numeric values required')
    selected = {}
    for name in ('L_Shoulder_x','R_Shoulder_z'):
        i = names.index(name)
        values = force[:,i]
        gap = np.degrees(np.abs(targets[:,arm.index(i)]-actual[:,i]))
        selected[name] = {'native_DOF_unit':report['native_DOF_units'][i],
            'native_total_DOF_force':values.tolist(), 'post_step_scalar_target_gap_deg':gap.tolist(),
            'force_min':float(values.min()), 'force_max':float(values.max()),
            'force_abs_peak':float(np.abs(values).max()),
            'force_abs_peak_step':int(np.abs(values).argmax()+1),
            'post_step_gap_max_deg':float(gap.max()), 'post_step_gap_final_deg':float(gap[-1])}
    result = {'checks':{'sensor_contracts_pass':True,'saved_coverage_alignment':True,
        'finite_shapes':True,'inputs_current':True},'input_sha256':inputs,
        'time_s':[s['time_s'] for s in sensors], 'selected':selected,
        'scope':'native total DOF force; scalar post-step target gap, not physical rotation angle or actuator-only torque',
        'guitar_position_max_mm':report['max_guitar_position_error_mm'],
        'guitar_rotation_max_deg':report['max_guitar_rotation_error_deg'],
        'left_palm_displacement_max_mm':report['max_left_palm_displacement_mm']}
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({n:{k:v for k,v in s.items() if not isinstance(v,list)} for n,s in selected.items()},indent=2))


if __name__=='__main__':
    main()
