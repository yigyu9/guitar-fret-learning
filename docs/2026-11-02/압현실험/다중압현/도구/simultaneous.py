"""Offline 240Hz simultaneous-clean integration; never starts physics."""
import argparse
import json
import math
from pathlib import Path

from inputs import STUDY, sha, verify, write


def finite_vector(value, count):
    if (not isinstance(value, list) or len(value) != count or
            any(type(v) not in (int, float) or not math.isfinite(v) for v in value)):
        raise ValueError('Finite vector length '+str(count)+' required')
    return value


def quaternion_angle(a, b):
    na = math.sqrt(sum(v*v for v in a)); nb = math.sqrt(sum(v*v for v in b))
    if min(na, nb) < 1e-10 or abs(na-1) > 1e-3 or abs(nb-1) > 1e-3:
        raise ValueError('Unit xyzw quaternion required')
    dot = abs(sum(x*y for x, y in zip(a, b))/(na*nb))
    return 2*math.acos(min(1., dot))


def summarize(rows, metadata):
    """No per-target latch can substitute for simultaneous time intersection."""
    onset, end = metadata['audible_window_s']
    if (onset, end) != (3., 4.5) or metadata.get('schema') != 'multi_press.trace.v1':
        raise ValueError('Fixed multi_press.trace.v1 window [3,4.5] required')
    if metadata.get('evidence_kind') not in ('synthetic', 'native_declared'):
        raise ValueError('Explicit evidence kind required')
    finger, arm = metadata['assigned_indices'], metadata['arm_indices']
    if (len(finger) != 8 or len(arm) != 12 or len(set(finger+arm)) != 20 or
            any(type(i) is not int or not 0 <= i < 105 for i in finger+arm)):
        raise ValueError('Distinct assigned8/arm12 q105 indices required')
    if len(metadata['target_ids']) != 2 or len(set(metadata['target_ids'])) != 2:
        raise ValueError('Exactly two unique targets required')
    duration = end-onset
    clean_s = [0., 0.]; streak = [0., 0.]; best = [0., 0.]; wrong_s = [0., 0.]
    joint_s = joint_streak = joint_best = wrong_any_s = 0.
    failed = dict(physical_failure=False, wrist_failure=False, guitar_escape=False)
    tracking = {k: dict(max_rad=0., square_sum=0., samples=0) for k in ('assigned', 'arm')}
    motion = dict(assigned_actual_max_change_rad=0., arm_actual_max_change_rad=0.,
                  arm_target_max_change_rad=0., wrist_relative_translation_max_m=0.,
                  wrist_relative_rotation_max_rad=0., guitar_translation_max_m=0., guitar_rotation_max_rad=0.)
    previous = reference = None
    clean_previous = None
    for row in rows:
        if type(row['physics_step']) is not int or row['physics_step'] < 0:
            raise ValueError('Integer physical endpoint identity required')
        now = row['score_time_s']
        if type(now) not in (float, int) or not math.isfinite(now):
            raise ValueError('Finite score time required')
        for name in ('candidate', 'wrong'):
            if not isinstance(row[name], list) or len(row[name]) != 2 or any(type(v) is not bool for v in row[name]):
                raise ValueError('Two explicit boolean target flags required')
        for name in failed:
            if type(row[name]) is not bool:
                raise ValueError('Explicit failure flags required')
            failed[name] |= row[name]
        q = finite_vector(row['actual_q105'], 105); target = finite_vector(row['target105'], 105)
        wrist = finite_vector(row['wrist_G_pose7'], 7); guitar = finite_vector(row['guitar_world_pose7'], 7)
        quaternion_angle(wrist[3:], wrist[3:]); quaternion_angle(guitar[3:], guitar[3:])
        safe = not any(row[name] for name in failed)
        clean = [c and not w and safe for c, w in zip(row['candidate'], row['wrong'])]
        if previous is None:
            if abs(now) > 1e-12:
                raise ValueError('Trace must begin at policy time0, including left endpoint')
        else:
            if row['physics_step'] != previous['physics_step']+1 or abs(now-previous['score_time_s']-1/240.) > 1e-9:
                raise ValueError('Missing, duplicate or nonconsecutive actual 240Hz endpoint')
            dt = max(0., min(now, end)-max(previous['score_time_s'], onset))
            both = [a and b for a, b in zip(clean_previous, clean)]
            for i in range(2):
                good = dt if both[i] else 0.
                clean_s[i] += good
                streak[i] = streak[i]+good if good > 0 else 0.
                best[i] = max(best[i], streak[i])
                wrong_s[i] += dt*.5*(previous['wrong'][i]+row['wrong'][i])
            good = dt if all(both) else 0.
            joint_s += good
            joint_streak = joint_streak+good if good > 0 else 0.
            joint_best = max(joint_best, joint_streak)
            wrong_any_s += dt*.5*(any(previous['wrong'])+any(row['wrong']))
        # Use the exact pre-motion actual arrival, not first contact, for motion attribution.
        if reference is None and now >= .5-1e-12:
            reference = row
        if reference is not None:
            for group, indices in (('assigned', finger), ('arm', arm)):
                errors = [abs(q[i]-target[i]) for i in indices]
                tracking[group]['max_rad'] = max(tracking[group]['max_rad'], max(errors))
                tracking[group]['square_sum'] += sum(e*e for e in errors)
                tracking[group]['samples'] += len(errors)
                key = group+'_actual_max_change_rad'
                motion[key] = max(motion[key], max(abs(q[i]-reference['actual_q105'][i]) for i in indices))
            motion['arm_target_max_change_rad'] = max(motion['arm_target_max_change_rad'],
                max(abs(target[i]-reference['target105'][i]) for i in arm))
            for name, pose, base in (('wrist_relative', wrist, reference['wrist_G_pose7']),
                                      ('guitar', guitar, reference['guitar_world_pose7'])):
                key = name+'_translation_max_m'
                motion[key] = max(motion[key], math.sqrt(sum((a-b)**2 for a, b in zip(pose[:3], base[:3]))))
                key = name+'_rotation_max_rad'
                motion[key] = max(motion[key], quaternion_angle(pose[3:], base[3:]))
        previous, clean_previous = row, clean
    complete = previous is not None and previous['score_time_s'] >= end-1e-12
    threshold = min(duration, max(.05, .4*duration))
    achieved = [value >= threshold-1e-12 for value in best]
    ready = metadata.get('preparation_status') == 'ready'
    fit = metadata.get('arrival_fit_status') == 'found'
    if not ready:
        outcome = {'failed': 'preparation_failed', 'geometry_unresolved': 'preparation_geometry_unresolved'}.get(
            metadata.get('preparation_status'), 'inspection_error')
    elif not fit:
        outcome = 'arrival_geometry_unresolved' if metadata.get('arrival_fit_status') == 'unresolved' else 'inspection_error'
    elif any(failed.values()):
        outcome = 'physical_or_wrist_failure'
    elif not complete or metadata.get('execution_completed') is not True:
        outcome = 'inspection_error'
    elif not all(achieved):
        outcome = 'individual_press_failed'
    elif joint_s >= duration-1e-9 and joint_best >= duration-1e-9 and wrong_any_s == 0:
        outcome = 'simultaneous_hold_success'
    else:
        outcome = 'simultaneous_hold_failed'
    for value in tracking.values():
        value['rms_rad'] = math.sqrt(value.pop('square_sum')/value['samples']) if value['samples'] else None
        if not value['samples']:
            value['max_rad'] = None
    return dict(schema='multi_press.simultaneous_metrics.v1', outcome=outcome,
        evidence_kind=metadata['evidence_kind'], physical_success_certified=False,
        scope='Input trace integration only; synthetic data never proves physics. Native origin/lifecycle require runner audit.',
        trace_covers_full_audible_window=complete, planned_duration_s=duration,
        per_target=[dict(target_id=identity, clean_s=clean_s[i], clean_fraction=clean_s[i]/duration,
                        longest_clean_s=best[i], achieved=achieved[i], wrong_s=wrong_s[i])
                    for i, identity in enumerate(metadata['target_ids'])],
        simultaneous_clean_s=joint_s, simultaneous_fraction=joint_s/duration,
        longest_simultaneous_clean_s=joint_best, wrong_any_s=wrong_any_s,
        failures=failed, tracking=tracking, motion=motion,
        motion_scope='Geometric changes, not causal force shares; no palm-push exclusion from net loads alone')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', required=True)
    parser.add_argument('--metadata', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        pins = {str(Path(p).resolve()): sha(p) for p in (args.trace, args.metadata, __file__)}
        metadata = json.loads(Path(args.metadata).read_text())
        verify(metadata['source_sha256'])
        with Path(args.trace).open() as stream:
            report = summarize((json.loads(line) for line in stream), metadata)
        verify(pins); verify(metadata['source_sha256'])
        report['inputs_sha256'] = pins
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report = dict(outcome='inspection_error', error=str(exc), physical_success_certified=False)
    write(args.out, report)
    print(json.dumps(report, ensure_ascii=False))
