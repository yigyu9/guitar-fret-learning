"""Fresh native validation and short free-guitar trials of two initial supports."""
import argparse
import json
import sys
from pathlib import Path

from .thigh_palm_support import SupportEnvironment, PHASE, BASE_RUN, BASE_SETTINGS
from .build_fixed_lower_asset import LOWER_BODIES, read, sha, pose
from .environment import np
from .run_physx_contacts import native_state
from . import run_joint_hold as runner
from scipy.spatial.transform import Rotation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', choices=('reference','clear_50um','clear_100um','clear_150um'), required=True)
    parser.add_argument('--physics-steps', type=int, choices=(24,120), required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    search = read(PHASE/'search.json')
    reference = args.candidate=='reference'
    row = None if reference else next(r for r in search['rows'] if r['name']==args.candidate)
    if row is not None and not row['accepted']:
        raise ValueError('static candidate rejected')
    settings = BASE_SETTINGS if reference else Path(row['settings_path'])
    shift = np.zeros(3) if reference else np.array(search['guitar_initial_translation_m'])
    hashes = dict(search['input_sha256'])
    for path in (Path(__file__).resolve(),settings,PHASE/'search.json',Path(__file__).with_name('fixed_lower_environment.py')):
        hashes[str(path)] = sha(path)
    if not all(sha(Path(p))==h for p,h in hashes.items()):
        raise ValueError('trial inputs changed before native initialization')
    baseline_report = read(BASE_RUN/'report.json')
    expected = read(BASE_RUN/'states.json')[0] if reference else row['predicted_state']
    instances = []
    initial_errors = {}

    def factory(initial_settings):
        env = SupportEnvironment(initial_settings,shift)
        instances.append(env)
        if len(instances)==2:
            try:
                state = native_state(env)
                for actor in ('human','guitar'):
                    for name, actual, predicted in zip(baseline_report[actor+'_body_names'],state[actor+'_body_states'],expected[actor+'_body_states']):
                        ap,aq = pose(actual); pp,pq = pose(predicted)
                        initial_errors[actor+'/'+name] = {'position_m':float(np.linalg.norm(ap-pp)),
                            'rotation_deg':float(np.degrees((Rotation.from_quat(aq)*Rotation.from_quat(pq).inv()).magnitude()))}
                if max(e['position_m'] for e in initial_errors.values())>1e-5 or max(e['rotation_deg'] for e in initial_errors.values())>.001:
                    raise AssertionError('fresh native FK differs from proposed geometry')
            except Exception:
                env.close()
                raise
        return env

    old_factory,old_argv = runner.InitialEnvironment,sys.argv
    runner.InitialEnvironment = factory
    sys.argv = [runner.__file__,'--mode','on','--settings',str(settings),'--out',str(args.out),'--physics-steps',str(args.physics_steps)]
    try:
        runner.main()
    finally:
        runner.InitialEnvironment,sys.argv = old_factory,old_argv
    env = instances[-1]
    report,states,contacts = [read(args.out/(n+'.json')) for n in ('report','states','contacts')]
    lower_fixed = all(all(s['human_body_states'][report['human_body_names'].index(n)]==states[0]['human_body_states'][report['human_body_names'].index(n)] for s in states) for n in LOWER_BODIES)
    pd_fields = ('native_pd_kp','native_pd_kd','native_drive_modes','native_effort_caps_nm','native_joint_lower_rad','native_joint_upper_rad')
    checks = {k:v for k,v in env.lock_checks.items() if k!='initial_body_poses_match'}
    checks.update(fresh_initial_FK_match=True,all_lower_states_exact=lower_fixed,
        pd_limits_unchanged=all(report[f]==baseline_report[f] for f in pd_fields),
        sources_unchanged=all(sha(Path(p))==h for p,h in hashes.items()))
    if reference:
        checks['reference_raw_prefix_exact'] = all(read(args.out/(n+'.json'))==read(BASE_RUN/(n+'.json'))[:len(read(args.out/(n+'.json')))] for n in ('states','trace','contacts','leg_torques','controls'))
    support = {'R_Hip':[], 'LH:palm':[], 'simultaneous':[]}
    for frame in contacts:
        found = set()
        for c in frame['contacts']:
            pair = (c['body0_name'],c['body1_name'])
            for name in ('R_Hip','LH:palm'):
                if 'human/'+name in pair and any(p.startswith('guitar/') for p in pair):
                    found.add(name)
        for name in found:
            support[name].append(frame['physics_step'])
        if len(found)==2:
            support['simultaneous'].append(frame['physics_step'])
    report.update(support_candidate=args.candidate,guitar_initial_translation_m=shift.tolist(),
        support_checks=checks,fresh_initial_pose_errors=initial_errors,support_contact_steps=support,
        contact_scope='Native contact rows from step1 onward; no t0 contact-force certification.',
        requested_settings=read(settings),source_sha256={**report['source_sha256'],**hashes})
    (args.out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'support':support,'p_mm':1000*report['max_position_error_m'],'q_deg':report['max_rotation_error_deg']},indent=2))
    if not all(checks.values()):
        raise AssertionError(checks)


if __name__=='__main__':
    main()
