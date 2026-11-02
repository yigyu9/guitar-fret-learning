"""CPU FK audit of a labelled actual native arrival; no state injection or GPU."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time

STUDY = Path(__file__).resolve().parents[1]
MULTI = STUDY.parent
ROOT = next(p for p in STUDY.parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0, str(MULTI/'도구'))
from common_pose import CommonPose, validate_arrival
from inputs import imported_pins, merge_pins, verify
import numpy as np
from scipy.spatial.transform import Rotation
from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
from guitar_learning.core.control import ACTIVE_NAMES

CAPTURE = MULTI/'로그/실제시뮬영상_v1/capture'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    path = Path(path).resolve()
    path.relative_to(STUDY)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def body_row(name, values):
    if np.shape(values) != (13,) or not np.isfinite(values).all():
        raise ValueError('finite xyz/xyzw/linear/angular body13 required')
    return dict(body_name=name, pose=dict(p=dict(zip('xyz', map(float, values[:3]))),
        r=dict(zip('xyzw', map(float, values[3:7])))),
        vel=dict(linear=dict(zip('xyz', map(float, values[7:10]))),
                 angular=dict(zip('xyz', map(float, values[10:13])))))


def make_arrival(raw, metadata, training, contract, pins, target_time=3.3):
    initial = contract['initial']
    names = dict(human=initial['human_body_names'], guitar=initial['guitar_body_names'], chair=['box'])
    ordered = [kind+'/'+name for kind in ('human', 'guitar', 'chair') for name in names[kind]]
    if (metadata['joint_names'] != initial['joint_names'] or metadata['body_names'] != ordered or
            metadata['schema'] != 'guitar_learning.finger_skill_video.v1' or
            metadata['environment'] != 0 or metadata['no_reset_frames'] is not True or
            metadata['capture_hz'] != 60 or metadata['source_physics_hz'] != 240):
        raise ValueError('capture joint/body order or native clock metadata mismatch')
    count = len(raw['time_s'])
    if (raw['q'].shape != (count, 105) or raw['qd'].shape != (count, 105) or
            raw['body_state'].shape != (count, len(ordered), 13) or
            not np.array_equal(raw['control_tick'], np.arange(1, count+1)) or
            not np.array_equal(raw['physics_step'], 4*raw['control_tick']) or
            not np.allclose(raw['time_s'], raw['control_tick']/60., rtol=0, atol=1e-12)):
        raise ValueError('capture arrays/endpoint clocks are not aligned')
    selected = np.flatnonzero(np.isclose(raw['time_s'], target_time, atol=1e-12, rtol=0))
    if len(selected) != 1:
        raise ValueError('one exact recorded requested endpoint required')
    index = int(selected[0])
    schedule = training['task']['provenance']['song']['schedule']
    if [(r['string'], r['fret'], r['finger']) for r in schedule] != [(2, 6, 1), (1, 6, 2)]:
        raise ValueError('native task is not the requested adjacent index/middle F6 pair')
    rows = [dict(target_id=r['target_id'], finger=('index', 'middle')[k],
                 finger_id=r['finger'], string=r['string'], string_standard_1based=r['string']+1,
                 fret=r['fret']) for k, r in enumerate(schedule)]
    case = dict(case_id='index_middle_same', targets=rows)
    state = dict(human_dof_states=[dict(pos=float(q), vel=float(v))
        for q, v in zip(raw['q'][index], raw['qd'][index])])
    offset = 0
    for kind in ('human', 'guitar', 'chair'):
        state[kind+'_body_states'] = [body_row(name, raw['body_state'][index, offset+j])
                                     for j, name in enumerate(names[kind])]
        offset += len(names[kind])
    arrival = dict(schema='multi_press.arrival.v1', case_id=case['case_id'],
        target_ids=[r['target_id'] for r in rows], joint_names=metadata['joint_names'],
        human_body_names=names['human'], body_names=names,
        physics_step=int(raw['physics_step'][index]), scene_id='native_pixels_env0_first_episode',
        evidence_kind='native_declared', q105=raw['q'][index].astype(float).tolist(), state=state,
        source_sha256=pins, source_endpoint_index=index, source_time_s=float(raw['time_s'][index]),
        scope='Read-only conversion of ordered captured actual poses; never submitted to a simulator')
    validate_arrival(arrival, case, contract)
    return arrival, case, index


def finite_distances(planner, q):
    """Same nearest eligible pad -> inset finite string segment distance as contact.py."""
    rows = []
    for k, (points, _) in enumerate(planner.samples(q)):
        target = planner.rows[k]
        start, line = planner.starts[target['string']], planner.lines[target['string']]
        limits = sorted(((planner.low[k]-start[1])/line[1], (planner.high[k]-start[1])/line[1]))
        lower, upper = max(0., limits[0]), min(1., limits[1])
        if lower > upper:
            raise ValueError('inset fret segment empty')
        projection = ((points-start)*line).sum(-1)/(line*line).sum()
        closest = start + np.clip(projection, lower, upper)[:, None]*line
        distances = np.linalg.norm(points-closest, axis=-1)
        j = int(distances.argmin())
        rows.append(dict(target_id=target['target_id'], minimum_distance_m=float(distances[j]),
                         eligible_sample_index=j, delta_G_m=(closest[j]-points[j]).tolist()))
    return rows


def native_reproduction(planner, arrival):
    poses = planner.fk(planner.q0)
    positions, rotations = [], []
    for name, actual in zip(arrival['human_body_names'], arrival['state']['human_body_states']):
        p, r = poses[name]
        positions.append(float(np.linalg.norm(p-[actual['pose']['p'][a] for a in 'xyz'])))
        expected = Rotation.from_quat([actual['pose']['r'][a] for a in 'xyzw'])
        rotations.append(float((expected.inv()*r).magnitude()))
    if max(positions) > 1e-8 or max(rotations) > 1e-8:
        raise ValueError('calibrated FK failed to reproduce actual native body poses')
    return dict(max_position_error_m=max(positions), max_rotation_error_rad=max(rotations),
        scope='FK calibrated at captured actual q/body poses; extrapolated motion remains a source-model prediction')


def command_comparison(planner, candidate, raw, endpoint, contract, model_std):
    reference = np.asarray(contract['target105'], dtype=float)
    rows = []
    for i in planner.arm+planner.finger:
        name = planner.names[i]
        action_index = ACTIVE_NAMES.index(name)
        value = float(candidate[i])
        span = planner.upper[i]-reference[i] if value >= reference[i] else reference[i]-planner.lower[i]
        normalized = float(np.clip((value-reference[i])/span, -1., 1.)) if span > 0 else 0.
        observed = float(raw['action'][endpoint, action_index])
        item = dict(joint=name, q_index=i, action_index=action_index,
            actual_q_rad=float(planner.q0[i]), recorded_target_rad=float(raw['target'][endpoint, i]),
            candidate_q_rad=value, delta_from_actual_rad=float(value-planner.q0[i]),
            native_action_lower_rad=float(planner.lower[i]), native_action_upper_rad=float(planner.upper[i]),
            native_action_span_rad=float(planner.upper[i]-planner.lower[i]),
            candidate_normalized_action=normalized, recorded_normalized_action=observed,
            delta_action=normalized-observed)
        if name.startswith(('LH:index', 'LH:middle')):
            sigma = float(model_std[action_index-17])
            delta_latent = float(np.arctanh(np.clip(normalized, -.999999, .999999))-
                                 np.arctanh(np.clip(observed, -.999999, .999999)))
            item.update(model_latent_std=sigma, delta_latent=delta_latent,
                absolute_latent_delta_in_sigma=abs(delta_latent)/sigma,
                approximate_near_zero_target_std_rad=float(sigma*span),
                latent_at_limit_clipped_for_diagnostic=bool(abs(normalized) >= .999999))
        rows.append(item)
    return rows


def run(out, max_nfev=60):
    if not 1 <= max_nfev <= 80:
        raise ValueError('max_nfev must be 1..80')
    out = Path(out).resolve()
    out.relative_to(STUDY/'로그')
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    files = ['poses_env0000.npz', 'capture_metadata.json', 'episode_env0000.json',
             'training_contract.json', 'settings.json', 'report.json', 'inputs_before.json']
    pins = {str(CAPTURE/name): sha(CAPTURE/name) for name in files}
    merge_pins(pins, json.loads((CAPTURE/'inputs_before.json').read_text()))
    pins[str(Path(__file__).resolve())] = sha(__file__)
    verify(pins)
    metadata = json.loads((CAPTURE/'capture_metadata.json').read_text())
    training = json.loads((CAPTURE/'training_contract.json').read_text())
    capture_report = json.loads((CAPTURE/'report.json').read_text())
    if capture_report['completed'] is not True or capture_report['native_pixels'] is not True:
        raise ValueError('completed actual native capture required')
    checkpoint = Path(metadata['checkpoint'])
    if sha(checkpoint) != metadata['checkpoint_sha256']:
        raise ValueError('captured model fingerprint mismatch')
    pins[str(checkpoint)] = sha(checkpoint)
    import torch
    model = torch.load(checkpoint, map_location='cpu', weights_only=False)
    model_std = model['model']['finger_log_std'].detach().double().exp().numpy()
    contract = load_gpu_prepared_reset_contract('left')
    merge_pins(pins, contract['source_sha256'])
    raw = np.load(str(CAPTURE/'poses_env0000.npz'), allow_pickle=False)
    arrival, case, endpoint = make_arrival(raw, metadata, training, contract, pins)
    planner = CommonPose(case, arrival)
    merge_pins(pins, planner.pins)
    merge_pins(pins, imported_pins())
    verify(pins)
    write(STUDY/'입력/arrival_native_t3p30.json', arrival)
    write(STUDY/'입력/arrival_case.json', case)
    write(out/'inputs_before.json', pins)
    reproduced = native_reproduction(planner, arrival)
    baseline = finite_distances(planner, planner.q0)
    attempts = []
    best_finger = None
    for scope, indices in (('actual_arm_fixed_finger8', planner.finger),
                            ('common_arm12_and_finger8', planner.arm+planner.finger)):
        seed = planner.q0.copy()
        if scope.startswith('common') and best_finger is not None:
            seed[planner.finger] = best_finger[planner.finger]
        candidate, fit = planner.fit(seed, indices, -.0005, max_nfev)
        if scope.startswith('actual'):
            best_finger = candidate.copy()
        distances = finite_distances(planner, candidate)
        item = dict(scope=scope, seed='captured_actual_q' if scope.startswith('actual') else 'finger8_result',
            fit=fit, finite_target_distances=distances,
            distance_reduction_m=[a['minimum_distance_m']-b['minimum_distance_m']
                                  for a, b in zip(baseline, distances)],
            motion=planner.finger_motion(planner.q0, candidate),
            commands=command_comparison(planner, candidate, raw, endpoint, contract, model_std))
        if scope.startswith('actual') and not np.array_equal(candidate[planner.arm], planner.q0[planner.arm]):
            raise ValueError('fixed-arm finger fit moved arm')
        attempts.append(item)
        write(out/(scope+'.json'), item)
        print(scope, fit['both_geometry'], [r['minimum_distance_m'] for r in distances], flush=True)
    verify(pins)
    report = dict(schema='multi_press.actual_arrival_geometry_audit.v1', completed=True,
        source_time_s=arrival['source_time_s'], source_physics_step=arrival['physics_step'],
        actual_endpoint_index=endpoint, case=case, fk_reproduction=reproduced,
        actual_finite_target_distances=baseline, actual_center_measurements=planner.measure(planner.q0, -.0005),
        attempts=attempts, source_sha256=pins, sources_unchanged=True, max_nfev_per_scope=max_nfev,
        scopes=2, elapsed_s=time.monotonic()-started, physics_steps_executed=0,
        cuda_context_initialized=torch.cuda.is_initialized(),
        current_finger_latent_std=model_std.tolist(),
        limitation='Finite source FK search, not collision/load/tracking/physics/pressure/acoustic proof. '
                   'No candidate is not impossibility. Sigma comparisons are per-axis distances, not path probabilities.')
    if report['cuda_context_initialized']:
        raise ValueError('CPU audit unexpectedly initialized CUDA')
    write(out/'inputs_after.json', pins)
    write(out/'report.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=STUDY/'로그/arrival_geometry')
    parser.add_argument('--max-nfev', type=int, default=60)
    args = parser.parse_args()
    result = run(args.out, args.max_nfev)
    print(json.dumps(dict(completed=True, elapsed_s=result['elapsed_s'])))
