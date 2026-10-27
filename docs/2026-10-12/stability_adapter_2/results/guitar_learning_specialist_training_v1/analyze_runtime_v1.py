"""종료된 손별 학습의 자원·재사용·준비 상태 분석. 원자료는 읽기 전용."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation
from guitar_learning.safety import contact_flags

PHASE = Path(__file__).resolve().parent
HELPER = PHASE.parent / 'guitar_learning_persistent_training_v1/analyze_runtime.py'
OLD = PHASE.parent / 'guitar_learning_long_B_8env_dense_v2_20261018_130137'
GIB = 1024 ** 3


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text())


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def pose(row):
    return (np.array([row['pose']['p'][k] for k in 'xyz']),
            Rotation.from_quat([row['pose']['r'][k] for k in 'xyzw']))


def velocity(row, kind):
    return np.array([row['vel'][kind][k] for k in 'xyz'])


def preparation(run):
    refs, rows = {}, []
    for path in sorted(run.glob('worker_*/audit_episode_*/initial_values.json')):
        worker, value = path.parent.parent.name, read(path)
        native = value['native']['native']
        body = native['guitar_body_states'][value['guitar_body_names'].index('guitar')]
        guitar = pose(body)
        feet = np.array([pose(native['human_body_states'][value['human_body_names'].index(s+'_Ankle')])[0]
                         for s in ('L', 'R')])
        q = np.array([r['pos'] for r in native['human_dof_states']])
        qd = np.array([r['vel'] for r in native['human_dof_states']])
        linear, angular = velocity(body, 'linear'), velocity(body, 'angular')
        refs.setdefault(worker, (guitar, feet, q, qd, linear, angular))
        ref, foot0, q0, qd0, lin0, ang0 = refs[worker]
        flags = contact_flags(value['native'])
        rows.append(dict(worker=worker, path=str(path),
            guitar_position_change_m=float(np.linalg.norm(guitar[0]-ref[0])),
            guitar_rotation_change_rad=float((ref[1].inv()*guitar[1]).magnitude()),
            foot_position_change_max_m=float(np.linalg.norm(feet-foot0, axis=1).max()),
            q_change_max_rad=float(np.max(np.abs(q-q0))),
            qd_change_max_rad_s=float(np.max(np.abs(qd-qd0))),
            qd_absolute_max_rad_s=float(np.max(np.abs(qd))),
            guitar_linear_velocity_change_m_s=float(np.linalg.norm(linear-lin0)),
            guitar_angular_velocity_change_rad_s=float(np.linalg.norm(angular-ang0)),
            any_support=bool(flags[:3].any()), triple_support=bool(flags[:3].all()),
            both_feet=bool(flags[-2:].all()),
            physical_contract=bool(len(value['joint_names']) == 105 and len(value['zero_range_indices']) == 8
                and value['human_root_fixed'] and not value['guitar_root_fixed']
                and not value['guitar_gravity_disabled'])))
    numeric = [k for k in rows[0] if k.endswith(('_m', '_rad', '_rad_s', '_m_s'))] if rows else []
    return dict(count=len(rows), per_worker={w:sum(r['worker'] == w for r in rows) for w in refs},
        reference='First prepared state per worker, after physical preparation; quaternions normalized by scipy Rotation.',
        maxima={k:max(r[k] for r in rows) for k in numeric},
        counts={k:sum(r[k] for r in rows) for k in ('any_support', 'triple_support', 'both_feet', 'physical_contract')},
        scope='Native reported qd and body velocities, not derivatives from pose differences. No hidden solver/cache restoration claim.', rows=rows)


def lifecycle(run, audit):
    result = []
    for path in sorted(run.glob('worker_*/environment/persistent_lifecycle.json')):
        value, errors = read(path), []
        resets = sorted(path.parent.glob('episode_*/persistent_reset.json'))
        identities = value['native_identities']
        for index, reset_path in enumerate(resets):
            record = read(reset_path)
            d, r = record['diagnostics'], record['readback']
            checks = dict(index=d['episode_index'] == index,
                identities=d['native_identities'] == identities,
                calls=d['native_calls'] == dict(create_sim=1, create_env=1, load_asset=2, destroy_sim=0),
                initial_calls=d['initial_state_calls_total'] == 4+2*index,
                no_forbidden=d['forbidden_calls_total'] == 0,
                no_hidden_steps=d['episode_local_physics_steps'] == 0,
                properties=d['native_properties_unchanged'] is True,
                boundary_effort=index == 0 or d['human_effort_cleared_at_boundary'] is True,
                state_writes=r['state_set_calls'] == dict(human_DOF=1, guitar_rigid_body=1,
                    human_rigid_body=0, native_POSITION_target=1))
            if not all(checks.values()): errors.append(dict(path=str(reset_path), checks=checks))
        final_checks = dict(closed=value['closed'] is True,
            calls=value['native_calls'] == dict(create_sim=1, create_env=1, load_asset=2, destroy_sim=1),
            resets=len(resets) == value['episode_index']+1,
            no_forbidden=value['forbidden_calls_total'] == 0,
            final_initial_calls=value['initial_state_calls_total'] == 4+2*value['episode_index'])
        result.append(dict(path=str(path), native_calls=value['native_calls'], reset_count=len(resets),
            initial_state_calls_total=value['initial_state_calls_total'], final_checks=final_checks,
            reset_errors=errors, passed=not errors and all(final_checks.values())))
    return dict(workers=result, reset_count=sum(r['reset_count'] for r in result),
        passed=len(result) == 4 and all(r['passed'] for r in result) and audit.get('completed') is True,
        native_audit_completed=audit.get('completed'), native_audit_errors=audit.get('errors'),
        scope='Initial scene/reset has four guarded state calls, each subsequent boundary adds two. Native POSITION target writes are recorded separately. No per-step state overwrite is permitted.')


def main():
    targets = [PHASE/'runtime_analysis_v1.json', PHASE/'runtime_verification_v1.json']
    if any(p.exists() for p in targets): raise FileExistsError('Use a new version for repeated analysis')
    runs = {role:PHASE/(role+'_run_v1') for role in ('left', 'right')}
    for run in runs.values():
        status = read(run/'status.json')
        cmdline = Path('/proc')/str(status['parent_pid'])/'cmdline'
        if cmdline.exists() and b'guitar_learning.train_' in cmdline.read_bytes():
            raise RuntimeError('Both training parents must have exited')
        if not (run/'report.json').is_file(): raise RuntimeError('Canonical report is not finalized')
    paths = [Path(__file__).resolve(), HELPER,
             Path(__import__('guitar_learning.safety', fromlist=['']).__file__),
             Path(__import__('guitar_learning.geometry_v1', fromlist=['']).__file__)]
    paths += [OLD/name for name in ('resources.jsonl', 'report.json', 'status.json')]
    for run in runs.values():
        paths += [run/name for name in ('settings.json', 'status.json', 'report.json', 'core_report.json', 'persistent_audit.json', 'resources.jsonl')]
        paths += sorted(run.glob('worker_*/environment/persistent_lifecycle.json'))
        paths += sorted(run.glob('worker_*/environment/episode_*/persistent_reset.json'))
        paths += sorted(run.glob('worker_*/audit_episode_*/initial_values.json'))
    pins = {str(p):sha(p) for p in paths}
    spec = importlib.util.spec_from_file_location('frozen_runtime_helper', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    output, available, intervals = {}, [], []
    signatures = []
    for role, run in runs.items():
        settings, report, core, audit, status = [read(run/name) for name in ('settings.json', 'report.json', 'core_report.json', 'persistent_audit.json', 'status.json')]
        rows = [json.loads(line) for line in (run/'resources.jsonl').read_text().splitlines() if line.strip()]
        resources = helper.analyze_resources(rows, expected=4)
        resources['complete_same_four_worker_samples'] = resources.pop('complete_same_eight_worker_samples')
        signatures.append(set(pid for _, pid in resources['worker_pid_signature']))
        for row in rows:
            for key in ('available_memory_bytes', 'min_available_memory_bytes'):
                if isinstance(row.get(key), (float, int)): available.append(row[key])
        intervals.append([rows[0]['wall_time_utc'], rows[-1]['wall_time_utc']])
        life, prep = lifecycle(run, audit), preparation(run)
        summary = helper.summarize_report(report, status)
        summary['requested_wall_budget_s'] = settings['max_wall_seconds']
        summary['wall_budget_overshoot_s'] = report['wall_s']-settings['max_wall_seconds']
        summary['resources'] = report.get('resources')
        summary['gpu_scope'] = 'Torch per-process CUDA allocation/reservation peaks only; not device total memory or utilization. Sim physics is CPU; both policy parents share cuda:0.'
        core_sha_ok = report.get('core_report', {}).get('sha256') == pins[str(run/'core_report.json')]
        output[role] = dict(run=str(run), settings=settings, resources=resources, report=summary,
            lifecycle=life, preparation=prep, canonical_core_sha_matches=core_sha_ok,
            canonical_completed=report.get('completed'), core_completed=core.get('completed'),
            embedded_audit_completed=report.get('persistent_audit', {}).get('completed'),
            lifecycle_matches_preparations=life['reset_count'] == prep['count'])
    old_rows = [json.loads(line) for line in (OLD/'resources.jsonl').read_text().splitlines() if line.strip()]
    old = helper.analyze_resources(old_rows, expected=8)
    result = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), inputs_sha256=pins,
        runs=output, historical_eight_worker_resources=old,
        concurrent_accounting=dict(intervals_utc=intervals, worker_pid_sets_disjoint=not bool(signatures[0] & signatures[1]),
            global_MemAvailable_min_GiB=min(available)/GIB,
            global_memory_floor_GiB=4.,
            scope='Each run has four distinct workers. Concurrent global MemAvailable readings are the same host quantity and are never summed; asynchronous per-run memory maxima are not a simultaneous eight-worker maximum.'),
        interpretation_limits=[
            'Historical eight-worker RSS grew from about 5.093 to 13.953 GiB over one hour. Recalculated OLS is observational; environment count, policy, duration and contemporaneous host load differ.',
            'Current RSS includes shared pages; PSS apportions them. Per-process RSS peaks are not simultaneous current usage. Samples after worker exit are excluded, never counted as zero.',
            'OLS slopes after 60 seconds, latter half and last 600 seconds describe overlapping, autocorrelated windows; flat/negative slopes do not establish long-term leak freedom.',
            'Collection includes step and episode reset/preparation. Reset/step/update/startup fractions may be inspected but collection must not be added to nested reset/step durations.',
            'Prepared-state differences are relative to the first prepared state of each worker and reveal reset drift separately from per-episode relative safety costs. These are not a strict V3 pose audit or an EPS0/solver-coordinate proof.'])
    write_new(targets[0], result)
    changed = [p for p, digest in pins.items() if sha(Path(p)) != digest]
    verification = dict(inputs_unchanged=not changed, changed_inputs=changed,
        analysis_sha256=sha(targets[0]), analysis_integrity_passed=not changed,
        worker_pid_sets_disjoint=not bool(signatures[0] & signatures[1]),
        finalization={role:bool(v['canonical_completed'] and v['core_completed'] and v['embedded_audit_completed']
            and v['canonical_core_sha_matches'] and v['lifecycle']['passed'] and v['lifecycle_matches_preparations']
            and v['preparation']['count'] > 0 and v['preparation']['counts']['physical_contract'] == v['preparation']['count'])
            for role,v in output.items()},
        scope='Training completion and analysis integrity are independent; no failure is converted into success.')
    write_new(targets[1], verification)
    print(json.dumps(verification, ensure_ascii=False))


if __name__ == '__main__':
    main()
