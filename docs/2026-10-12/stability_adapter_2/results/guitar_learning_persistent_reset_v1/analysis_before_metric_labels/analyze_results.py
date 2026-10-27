"""Read-only native comparison; save new analysis artifacts once all runs finish."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation
from guitar_learning.safety import contact_flags

PHASE = Path(__file__).resolve().parent
CASES = ('fresh_reference_v1', 'reuse_repeat_v1', 'reuse_resume_v1', 'reuse_pool_v1')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (PHASE/name).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def pose(states):
    positions = [[r['pose']['p'][k] for k in 'xyz'] for r in states]
    rotations = [[r['pose']['r'][k] for k in 'xyzw'] for r in states]
    return np.asarray(positions), Rotation.from_quat(rotations)


def difference(reference, value):
    a, b = reference['native']['native'], value['native']['native']
    result = {}
    for field in ('pos', 'vel'):
        qa = np.asarray([r[field] for r in a['human_dof_states']])
        qb = np.asarray([r[field] for r in b['human_dof_states']])
        result['max_DOF_'+field+'_difference'] = float(np.max(np.abs(qa-qb)))
    for label in ('human', 'guitar'):
        pa, ra = pose(a[label+'_body_states'])
        pb, rb = pose(b[label+'_body_states'])
        result[label+'_max_body_position_difference_m'] = float(np.linalg.norm(pa-pb, axis=1).max())
        result[label+'_max_body_rotation_difference_rad'] = float((ra.inv()*rb).magnitude().max())
    result['target105_max_difference_rad'] = float(np.max(np.abs(
        np.asarray(reference['target105_rad'])-np.asarray(value['target105_rad']))))
    result['positive_contact_flags'] = contact_flags(value['native']).tolist()
    return result


def main():
    reports = {case: read(PHASE/case/'report.json') for case in CASES}
    inputs = {Path(__file__).resolve()}
    for case in CASES:
        root = PHASE/case
        inputs.update(root.glob('*.json'))
        inputs.update(root.glob('*.jsonl'))
        inputs.update(root.glob('*.jsonl.gz'))
        for pattern in ('worker_*/audit_episode_*/*.json',
                        'worker_*/environment/episode_*/persistent_reset.json',
                        'worker_*/environment/persistent_lifecycle.json'):
            inputs.update(root.glob(pattern))
    pins = {str(p): sha(p) for p in sorted(inputs)}
    write('analysis_inputs_before.json', pins)
    result = {'cases': {}, 'prepared_state_comparison': {},
              'scope': 'Short concurrent-host comparison, not hidden solver cache equality or long-run leak proof'}
    for case, report in reports.items():
        root = PHASE/case
        checks = {key: report[key] for key in (
            'changed_inputs', 'missing_import_pins', 'original_source_parity_errors',
            'missing_worker_audits', 'worker_audit_read_errors', 'guard_violations',
            'worker_failures', 'physical_flags_errors', 'cleanup_errors')}
        assert report['completed'] and not any(checks.values()), (case, checks)
        rows = []
        with gzip.open(root/'transitions.jsonl.gz', 'rt') as stream:
            for line in stream:
                rows.extend(json.loads(line)['infos'])
        flags = np.asarray([r['stability']['flags'] for r in rows])
        episodes = [e for update in report['updates'] for e in update['completed_episodes']]
        resets = sorted(root.glob('worker_*/audit_episode_*/initial_values.json'))
        resources = [json.loads(line) for line in (root/'resources.jsonl').read_text().splitlines()]
        rss = [sum(w['memory']['rss_current_bytes'] or 0 for w in r.get('workers', []))
               for r in resources]
        row = dict(completed=report['completed'], transitions=report['transitions'],
            recorded_transitions=len(rows), policy_physics_samples=len(rows)*4,
            completed_episodes=episodes, reset_preparation_count=len(resets),
            timers=report['timers'], wall_s=report['wall_s'],
            mean_reset_wall_s_including_initial=report['timers']['reset_s']/len(resets),
            worker_current_rss_sum_max_bytes=max(rss),
            physical_failure_transition_count=sum(bool(r['failure_reasons']) for r in rows),
            endpoint_triple_support_fraction=float(np.all(flags[:, :3]>0, axis=1).mean()),
            endpoint_both_feet_fraction=float(np.all(flags[:, -2:]>0, axis=1).mean()),
            max_guitar_displacement_m=max(float(np.linalg.norm(r['stability']['guitar_delta_m'])) for r in rows),
            max_guitar_rotation_rad=max(float(np.linalg.norm(r['stability']['guitar_rotation_vector_rad'])) for r in rows),
            max_foot_displacement_m=max(float(np.linalg.norm(r['stability']['foot_delta_m'],axis=1).max()) for r in rows),
            matched50_max=max(r['music']['matched50'] for r in rows),
            held_total_s_max=max(r['music']['held_total_s'] for r in rows), checks=checks)
        if case != 'fresh_reference_v1':
            audit = read(root/'persistent_audit.json')
            assert audit['completed'] and not audit['errors']
            row['persistent_workers'] = [w['lifecycle'] for w in audit['workers']]
            assert sha(root/'core_report.json') == report['core_report']['sha256']
        result['cases'][case] = row
    fresh = sorted((PHASE/'fresh_reference_v1').glob('worker_000/audit_episode_*/initial_values.json'))
    reuse = sorted((PHASE/'reuse_repeat_v1').glob('worker_000/audit_episode_*/initial_values.json'))
    reference = read(fresh[0])
    result['prepared_state_comparison']['fresh_to_first'] = [dict(path=str(p), **difference(reference, read(p))) for p in fresh]
    result['prepared_state_comparison']['reuse_to_fresh_first'] = [dict(path=str(p), **difference(reference, read(p))) for p in reuse]
    result['prepared_state_comparison']['paired_first_three'] = [dict(fresh=str(a), reuse=str(b), **difference(read(a),read(b))) for a,b in zip(fresh,reuse)]
    contracts = [read(PHASE/case/'training_contract.json') for case in CASES[:3]]
    result['fixed_task_contracts_identical'] = contracts[0] == contracts[1] == contracts[2]
    assert result['fixed_task_contracts_identical']
    write('analysis.json', result)
    changed = [p for p, digest in pins.items() if not Path(p).is_file() or sha(Path(p)) != digest]
    write('analysis_verification.json', dict(completed=not changed,changed_inputs=changed,input_count=len(pins)))
    assert not changed


if __name__ == '__main__':
    main()
