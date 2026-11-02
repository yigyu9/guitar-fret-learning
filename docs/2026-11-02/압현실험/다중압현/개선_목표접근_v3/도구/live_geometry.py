"""Fit assigned finger8 to one labelled live arrival, without changing physics.

Importing this module loads only the standard library. The native caller must
load Isaac Gym before calling fit_snapshot, because current CPU geometry
dependencies import Torch. This helper never creates a scene or calls a setter.
"""
import copy
import hashlib
import importlib.util
import json
import numbers
import os
from pathlib import Path
import sys
import time

STUDY = Path(__file__).resolve().parents[1]
MULTI = STUDY.parent
_ENV_KEYS = ('CUDA_VISIBLE_DEVICES', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
             'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS')


def _dependencies():
    """Old CPU helpers temporarily alter visibility; restore the caller exactly."""
    environment = {key: os.environ.get(key) for key in _ENV_KEYS}
    old_path = sys.path[:]
    try:
        sys.path.insert(0, str(MULTI/'도구'))
        import common_pose
        import numpy as np
        from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
        from inputs import merge_pins, verify
        source = MULTI/'미동작_원인검증_v2/도구/arrival_geometry_audit.py'
        name = '_multi_press_arrival_audit_v2_cpu_helpers'
        audit = sys.modules.get(name)
        if audit is None:
            spec = importlib.util.spec_from_file_location(name, str(source))
            audit = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(audit)
            sys.modules[name] = audit
        return common_pose, audit, np, load_gpu_prepared_reset_contract, merge_pins, verify
    finally:
        sys.path[:] = old_path
        for key, value in environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fit_snapshot(q105, qd105, body_state, joint_names, body_names,
                 training_contract, physics_step, pins, height=-.0005,
                 max_nfev=60):
    """Return (strict arrival, case, report); q105 is a target proposal only.

    Inputs are actual ordered CPU arrays at one common endpoint. Invalid input
    raises ValueError; a valid finite search without a candidate returns
    classification='no_candidate'. Only the two assigned fingers may change.
    """
    if (isinstance(physics_step, bool) or not isinstance(physics_step, numbers.Integral)
            or physics_step < 0 or type(max_nfev) is not int or not 1 <= max_nfev <= 60 or
            isinstance(height, bool) or not isinstance(height, numbers.Real) or
            not -.001 <= height <= 0.):
        raise ValueError('nonnegative integer step, max_nfev1..60 and press height[-1,0]mm required')
    common, audit, np, load_contract, merge_pins, verify = _dependencies()
    started = time.monotonic()
    contract = load_contract('left')
    initial = contract['initial']
    q, qd, bodies = [np.asarray(value, dtype=float) for value in (q105, qd105, body_state)]
    names = dict(human=initial['human_body_names'], guitar=initial['guitar_body_names'], chair=['box'])
    expected_bodies = [kind+'/'+name for kind in ('human', 'guitar', 'chair') for name in names[kind]]
    if (list(joint_names) != initial['joint_names'] or list(body_names) != expected_bodies or
            q.shape != (105,) or qd.shape != (105,) or bodies.shape != (106, 13) or
            not all(np.isfinite(value).all() for value in (q, qd, bodies))):
        raise ValueError('actual q105/qd105/body106x13 and exact ordered identities required')
    if (training_contract['action']['target_contract']['joint_names'] != initial['joint_names'] or
            training_contract['task']['provenance']['schema'] != 'guitar_learning.song_score.v1'):
        raise ValueError('current ordered native action and song-score contract required')
    schedule = training_contract['task']['provenance']['song']['schedule']
    if (len(schedule) != 2 or
            [(r['string'], r['fret'], r['finger']) for r in schedule] != [(2, 6, 1), (1, 6, 2)] or
            [r['target_id'] for r in schedule] !=
            ['event-000000/string-3/note-0', 'event-000001/string-2/note-1']):
        raise ValueError('original index/string3/F6 + middle/string2/F6 task required')
    source_pins = copy.deepcopy(pins)
    verify(source_pins)
    merge_pins(source_pins, contract['source_sha256'])
    for path in (Path(__file__).resolve(), Path(common.__file__).resolve(), Path(audit.__file__).resolve()):
        merge_pins(source_pins, {str(path): _sha(path)})
    case = dict(case_id='index_middle_same', targets=[dict(
        target_id=row['target_id'], finger=('index', 'middle')[k], finger_id=row['finger'],
        string=row['string'], string_standard_1based=row['string']+1, fret=row['fret'])
        for k, row in enumerate(schedule)])
    state = dict(human_dof_states=[dict(pos=float(pos), vel=float(vel)) for pos, vel in zip(q, qd)])
    offset = 0
    for kind in ('human', 'guitar', 'chair'):
        state[kind+'_body_states'] = [audit.body_row(name, bodies[offset+k])
                                     for k, name in enumerate(names[kind])]
        offset += len(names[kind])
    snapshot_payload = dict(joint_names=list(joint_names), body_names=list(body_names),
        q105=q.tolist(), qd105=qd.tolist(), body_state=bodies.tolist(), physics_step=int(physics_step))
    snapshot_sha = hashlib.sha256(json.dumps(snapshot_payload, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
    arrival = dict(schema='multi_press.arrival.v1', case_id=case['case_id'],
        target_ids=[r['target_id'] for r in case['targets']], joint_names=list(joint_names),
        human_body_names=names['human'], body_names=names, physics_step=int(physics_step),
        scene_id='live_native_env0_common_endpoint', evidence_kind='native_declared',
        q105=q.tolist(), state=state, source_sha256=source_pins,
        snapshot_content_sha256=snapshot_sha,
        scope='actual caller endpoint; read-only CPU calibration; never physics state injection')
    common.validate_arrival(arrival, case, contract)
    planner = common.CommonPose(case, arrival)
    merge_pins(source_pins, planner.pins)
    reproduction = audit.native_reproduction(planner, arrival)
    candidate, fit = planner.fit(planner.q0, planner.finger, float(height), max_nfev)
    fixed = sorted(set(range(105))-set(planner.finger))
    if not np.array_equal(candidate[fixed], q[fixed]):
        raise ValueError('finger8 fit moved a nonassigned axis')
    verify(source_pins)
    report = dict(schema='multi_press.live_arrival_finger_fit.v1',
        classification='geometry_candidate' if fit['both_geometry'] else 'no_candidate',
        q105=candidate.tolist(), targets=fit['targets'], both_geometry=fit['both_geometry'],
        native_verified=False, optimizer_converged=fit['optimizer_converged'], nfev=fit['nfev'],
        height_m=float(height), max_nfev=max_nfev, snapshot_content_sha256=snapshot_sha,
        actual_physics_step=int(physics_step), fk_reproduction=reproduction,
        assigned_indices=planner.finger, arm_indices=planner.arm,
        nonassigned_q_preserved=True, motion=planner.finger_motion(q, candidate),
        actual_target_distances=audit.finite_distances(planner, q),
        candidate_target_distances=audit.finite_distances(planner, candidate),
        source_sha256=source_pins, sources_unchanged=True, elapsed_s=time.monotonic()-started,
        physical_steps_executed=0,
        limitation='Finite geometry only; no candidate is not impossibility; collision/load/tracking/clean hold require native replay')
    return arrival, case, report
