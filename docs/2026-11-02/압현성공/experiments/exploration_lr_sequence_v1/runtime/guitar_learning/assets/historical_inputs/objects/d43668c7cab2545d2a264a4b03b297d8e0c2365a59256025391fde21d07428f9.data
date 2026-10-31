"""Compare saved five-second left-arm stiffness trials; no native simulation."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1'
LABELS = ('kp_1', 'kp_1p5', 'kp_2')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    output = PHASE / 'analysis.json'
    if output.exists():
        raise FileExistsError('preserve earlier analysis')
    hashes = {}
    reports = {}
    captures = {}
    for label in LABELS:
        for name, target in (('report', reports), ('capture', captures)):
            path = PHASE / label / (name + '.json')
            hashes[str(path)] = sha(path)
            target[label] = read(path)
    paths = [Path(__file__).resolve(), PHASE / 'execution.json', PHASE / 'environment.json',
             PHASE / 'execution_input_sha256.json', PHASE / 'plan_before_execution.md']
    for label in LABELS:
        paths += [Path(p) for p in reports[label]['input_sha256']]
        paths += [PHASE / label / (n + '.jsonl') for n in ('states', 'trace', 'tasks', 'contacts', 'controls')]
        paths += [PHASE / label / (n + '.json') for n in ('initial_values', 'videos')]
        paths += [Path(p) for frame in captures[label]['frames'] for p in frame['image_sha256']]
        paths += [Path(v['path']) for v in reports[label]['videos'].values()]
    hashes.update({str(p): sha(p) for p in paths})
    from .palm_side_feedback import context, np
    from .palm_normal_task import prepare, error_from_state
    from .build_fixed_lower_asset import pose
    from scipy.spatial.transform import Rotation
    ctx = prepare(context())
    initial = {label: read(PHASE / label / 'initial_values.json') for label in LABELS}
    baseline = initial['kp_1']
    arm = ctx['indices']
    summary = []
    curves = {}
    reference_controls = None
    for label, scale in zip(LABELS, (1, 1.5, 2)):
        report = reports[label]
        raw = {n: [json.loads(line) for line in (PHASE / label / (n + '.jsonl')).read_text().splitlines()]
               for n in ('states', 'trace', 'tasks', 'contacts', 'controls')}
        if not report['completed'] or not all(report['checks'].values()) or report['physics_steps'] != 1200 or report['native_initializations'] != 1:
            raise AssertionError('native completion/contracts')
        if any(sha(p) != h for p, h in report['input_sha256'].items()):
            raise AssertionError('native inputs changed')
        if initial[label]['input_trial']['main_target_offsets_rad'] != baseline['input_trial']['main_target_offsets_rad']:
            raise AssertionError('same named66 target offsets')
        for field in ('effective_initial_settings', 'native_initial_state', 'initial_PD_target_rad',
                      'guitar_goal_position_W_m', 'guitar_goal_quaternion_xyzw', 'absolute_strap_rest_length_m', 'physics_parameters'):
            if initial[label][field] != baseline[field]:
                raise AssertionError('same initial state/strap/physics: ' + field)
        for field, values in baseline['PD_properties'].items():
            expected = [v * scale if field == 'stiffness' and i in arm else v for i, v in enumerate(values)]
            if initial[label]['PD_properties'][field] != expected:
                raise AssertionError('left12 stiffness only: ' + field)
        if any(len(raw[n]) != 1201 for n in ('states', 'trace', 'tasks')) or any(len(raw[n]) != 1200 for n in ('contacts', 'controls')):
            raise AssertionError('raw coverage')
        if reference_controls is None:
            reference_controls = raw['controls']
            if any(row['final_target_rad'] != reference_controls[0]['final_target_rad'] for row in reference_controls):
                raise AssertionError('baseline constant target')
        if any(row['physics_step'] != i + 1 or row['updated_before_step'] != (i % 4 == 0)
               or row['final_target_rad'] != reference_controls[i]['final_target_rad'] for i, row in enumerate(raw['controls'])):
            raise AssertionError('same constant commands')
        if any(row['physics_step'] != i + 1 for i, row in enumerate(raw['contacts'])):
            raise AssertionError('contact time')
        frames = captures[label]['frames']
        if len(frames) != 151 or any(f['physics_step'] != i * 8 or abs(f['time_s'] - i / 30) > 1e-9 or not f['render_preserves_states'] for i, f in enumerate(frames)):
            raise AssertionError('actual frames0..5s')
        expected_views = {'whole_body', 'hands'}
        if set(report['videos']) != expected_views or any(
                {Path(p).parent.name for p in f['image_sha256']} != expected_views
                or any(sha(p) != h for p, h in f['image_sha256'].items()) for f in frames):
            raise AssertionError('two actual native frame views/SHA')
        for video in report['videos'].values():
            proc = subprocess.run(video['ffprobe_command'], capture_output=True, text=True)
            if proc.returncode:
                raise RuntimeError('ffprobe failed')
            stream = json.loads(proc.stdout)['streams'][0]
            if stream != video['stream'] or stream['avg_frame_rate'] != '30/1' or int(stream['nb_read_frames']) != 151 or abs(float(stream['duration']) - 151 / 30) > .002 or sha(video['path']) != video['sha256']:
                raise AssertionError('video coverage/SHA')
        gaps = []
        coordinate_errors = []
        velocities = []
        for i, (state, task, trace) in enumerate(zip(raw['states'], raw['tasks'], raw['trace'])):
            if state['physics_step'] != i or abs(trace['time_s'] - i / 240) > 1e-9 or error_from_state(state, ctx).tolist() != task:
                raise AssertionError('time/task')
            gp, gq = pose(state['guitar_body_states'][0])
            pp, pq = pose(state['human_body_states'][ctx['palm_index']])
            gr = Rotation.from_quat(gq)
            gaps.append(float((pp + Rotation.from_quat(pq).apply(ctx['local_point']) - (gp + gr.apply(ctx['goal_point_G'] - ctx['normal_G'] * .00005))) @ gr.apply(ctx['normal_G'])) * 1000)
            coordinate_errors.append([state['human_dof_states'][j]['pos'] - reference_controls[0]['final_target_rad'][k] for k, j in enumerate(arm)])
            velocities.append([state['human_dof_states'][j]['vel'] for j in arm])
        palm = [(row['physics_step'], c) for row in raw['contacts'] for c in row['contacts']
                if {c['body0_name'], c['body1_name']} == {'human/LH:palm', 'guitar/guitar'}]
        positive = [(step, c) for step, c in palm if c['lambda'] > 0]
        points = [float(np.linalg.norm(t[:3])) * 1000 for t in raw['tasks']]
        def metrics(end):
            traces = raw['trace'][:end + 1]
            return {'max_guitar_position_error_mm': max(t['position_error_m'] for t in traces) * 1000,
                    'max_guitar_rotation_error_deg': max(t['rotation_error_deg'] for t in traces),
                    'end_guitar_position_error_mm': traces[-1]['position_error_m'] * 1000,
                    'end_guitar_rotation_error_deg': traces[-1]['rotation_error_deg'],
                    'end_point_error_mm': points[end], 'end_source_normal_gap_mm': gaps[end],
                    'max_actual_torso_drift_deg': float(np.abs([t['torso_drift_deg'] for t in traces]).max()),
                    'positive_raw_palm_lambda_steps': sorted({s for s, c in positive if s <= end})}
        summary.append({'label': label, 'kp_scale': scale, 'kd_scale': 1, 'first_0p1s': metrics(24), 'full_5s': metrics(1200),
                        'palm_contact_steps': sorted({s for s, c in palm}), 'positive_raw_palm_lambda_rows': len(positive),
                        'palm_up_proxy_violations': len(report['constraint_violations']), 'stability_success': False})
        curves[label] = {'time_s': [t['time_s'] for t in raw['trace']], 'point_error_mm': points, 'source_normal_gap_mm': gaps,
                         'guitar_position_error_mm': [t['position_error_m'] * 1000 for t in raw['trace']],
                         'guitar_rotation_error_deg': [t['rotation_error_deg'] for t in raw['trace']],
                         'native_coordinate_error_rad': coordinate_errors, 'native_velocity_rad_s': velocities}
    execution = read(PHASE / 'execution.json')
    checks = {'three_same_initial_state_and_targets': True, 'left12_stiffness_only_native_readback': True,
              'three_5s_raw_and_actual_videos': True, 'baseline_first24_five_arrays_exact': reports['kp_1']['checks']['first24_five_arrays_exact'],
              'three_exits_zero': len(execution) == 3 and [e['label'] for e in execution] == list(LABELS) and all(e['exit_code'] == 0 for e in execution),
              'execution_inputs_unchanged': all(sha(p) == h for p, h in read(PHASE / 'execution_input_sha256.json').items()),
              'inputs_unchanged': all(sha(p) == h for p, h in hashes.items())}
    if not all(checks.values()):
        raise AssertionError(checks)
    result = {'checks': checks, 'input_sha256': hashes, 'counts': {'native_initializations': 3, 'physics_steps': 3600},
              'summary': summary, 'curves': curves,
              'scope': 'saved data only; same initial pose/strap/targets, stiffness-only diagnosis; source gap is not cooked clearance, raw lambda is not N; scalar coordinates are not whole-joint SO3; no guitar-pose feedback or stability certification'}
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'checks': checks, 'summary': summary}, indent=2))


if __name__ == '__main__':
    main()
