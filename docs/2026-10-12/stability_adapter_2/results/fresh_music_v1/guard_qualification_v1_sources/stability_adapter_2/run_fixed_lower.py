"""Reuse the established arm PI runner with a physically fixed lower model."""
import argparse
import json
from pathlib import Path
import sys

from .fixed_lower_environment import FixedLowerEnvironment
from .build_fixed_lower_asset import ASSET, MANIFEST, REFERENCE, LOWER_BODIES, read, sha, pose
from .environment import np
from . import run_joint_hold as runner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--physics-steps',type=int,choices=(24,240),required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    settings = Path(__file__).with_name('trials')/'left_palm_boundary_v1/l_wrist_x_minus0125.json'
    inputs = [Path(__file__).resolve(),Path(__file__).with_name('fixed_lower_environment.py'),ASSET,MANIFEST]
    hashes = {str(p):sha(p) for p in inputs}
    hashes.update(read(MANIFEST)['input_sha256'])
    old_env, old_argv = runner.InitialEnvironment, sys.argv
    runner.InitialEnvironment = FixedLowerEnvironment
    sys.argv = [str(Path(runner.__file__)), '--mode','on','--settings',str(settings),
        '--out',str(args.out),'--physics-steps',str(args.physics_steps)]
    try:
        runner.main()
    finally:
        runner.InitialEnvironment,sys.argv = old_env,old_argv
    env = FixedLowerEnvironment.instance
    report,states = read(args.out/'report.json'),read(args.out/'states.json')
    measured = {}
    for name in LOWER_BODIES:
        index = report['human_body_names'].index(name)
        p0,q0 = pose(states[0]['human_body_states'][index]); q0 /= np.linalg.norm(q0)
        movement,rotation,linear,angular = [],[],[],[]
        for state in states:
            body = state['human_body_states'][index]; p,q = pose(body); q /= np.linalg.norm(q)
            movement.append(float(np.linalg.norm(p-p0)))
            rotation.append(float(np.degrees(2*np.arccos(np.clip(abs(q@q0),0,1)))))
            linear.append(float(np.linalg.norm([body['vel']['linear'][a] for a in 'xyz'])))
            angular.append(float(np.linalg.norm([body['vel']['angular'][a] for a in 'xyz'])))
        measured[name] = dict(max_position_change_m=max(movement),max_rotation_change_deg=max(rotation),
            max_linear_speed_mps=max(linear),max_angular_speed_rad_s=max(angular))
    previous = read(REFERENCE/'report.json')
    previous_targets = dict(zip(previous['human_joint_names'],previous['initial_joint_targets_rad']))
    pd_fields = ('native_pd_kp','native_pd_kd','native_drive_modes','native_effort_caps_nm',
        'native_joint_lower_rad','native_joint_upper_rad')
    upper_pd_same = all(report[field]==[previous[field][previous['human_joint_names'].index(n)]
        for n in report['human_joint_names']] for field in pd_fields)
    checks = {**env.lock_checks,
        'upper_initial_targets_unchanged':all(v==previous_targets[n] for n,v in zip(report['human_joint_names'],report['initial_joint_targets_rad'])),
        'remaining_PD_limits_and_drive_modes_unchanged':upper_pd_same,
        'all_lower_links_stationary':all(v['max_position_change_m']<=1e-6 and v['max_rotation_change_deg']<=.001
            and v['max_linear_speed_mps']<=1e-6 and v['max_angular_speed_rad_s']<=1e-6 for v in measured.values()),
        'extra_sources_unchanged':all(sha(Path(p))==h for p,h in hashes.items())}
    report.update(lower_body_condition='physical fixed links with no lower DOFs; no runtime pose writes',
        previous_dynamic_lower_run=str(REFERENCE),fixed_lower_asset=str(ASSET),
        requested_initial_settings=read(settings),
        fixed_lower_checks=checks,initial_body_pose_errors=env.initial_pose_errors,lower_link_measurements=measured)
    report['source_sha256'].update(hashes)
    (args.out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'fixed_lower_checks':checks,'lower_link_measurements':measured},indent=2))
    if not all(checks.values()):
        raise AssertionError(checks)


if __name__=='__main__':
    main()
