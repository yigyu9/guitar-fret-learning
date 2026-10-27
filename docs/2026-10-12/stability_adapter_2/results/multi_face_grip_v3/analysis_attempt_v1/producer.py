"""Analyze native five-second grip approaches without running physics."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3'
LABELS = ('baseline', 'seed_1', 'seed_2')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())


def main():
    output = PHASE / 'analysis.json'
    if output.exists(): raise FileExistsError('preserve earlier analysis')
    reports = {}; captures = {}; hashes = {}
    for label in LABELS:
        for name, target in (('report', reports), ('capture', captures)):
            p = PHASE / 'native' / label / (name + '.json'); hashes[str(p)] = sha(p); target[label] = read(p)
    paths = [Path(__file__).resolve(), PHASE / 'execution.json', PHASE / 'environment.json', PHASE / 'search.json', PHASE / 'face_audit.json']
    for label in LABELS:
        paths += [Path(p) for p in reports[label]['input_sha256']]
        paths += [PHASE / 'native' / label / (n + '.jsonl') for n in ('states', 'trace', 'tasks', 'contacts', 'controls')]
        paths += [PHASE / 'native' / label / (n + '.json') for n in ('initial_values', 'initial_grip_audit', 'videos')]
        paths += [Path(p) for f in captures[label]['frames'] for p in f['image_sha256']]
        paths += [Path(v['path']) for v in reports[label]['videos'].values()]
    hashes.update({str(p): sha(p) for p in paths})
    from .environment import np
    from .build_fixed_lower_asset import pose
    from .search_multi_face_grip import REFERENCE
    from scipy.spatial.transform import Rotation
    reference = read(REFERENCE / 'report.json')
    search = read(PHASE / 'search.json')
    initial = {label: read(PHASE / 'native' / label / 'initial_values.json') for label in LABELS}
    baseline = initial['baseline']; names = baseline['human_joint_names']
    left = [i for i, n in enumerate(names) if n.startswith(('L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist', 'LH:'))]
    arm = left[:12]; other = [i for i in range(len(names)) if i not in left]
    summary = []; curves = {}
    for label in LABELS:
        folder = PHASE / 'native' / label; report = reports[label]; init = initial[label]
        raw = {n: [json.loads(line) for line in (folder / (n + '.jsonl')).read_text().splitlines()]
               for n in ('states', 'trace', 'tasks', 'contacts', 'controls')}
        admission = read(folder / 'initial_grip_audit.json')
        if not report['completed'] or not all(report['checks'].values()) or report['physics_steps'] != 1200 or not all(admission['checks'].values()):
            raise AssertionError('native completion/source-FK gate')
        if any(sha(p) != h for p, h in report['input_sha256'].items()): raise AssertionError('native input closure')
        q = np.array([d['pos'] for d in raw['states'][0]['human_dof_states']]); q0 = np.array([d['pos'] for d in baseline['native_initial_state']['human_dof_states']])
        if q.tolist() != init['initial_PD_target_rad'] or not np.array_equal(q[other], q0[other]): raise AssertionError('actual initial q/target/other DOF')
        if not ((q >= init['PD_properties']['lower']) & (q <= init['PD_properties']['upper'])).all() or np.max(abs(q[arm] - q0[arm])) > .300001:
            raise AssertionError('actual initial hard limits/arm box')
        for field in ('PD_properties', 'absolute_strap_rest_length_m', 'physics_parameters', 'guitar_goal_position_W_m', 'guitar_goal_quaternion_xyzw'):
            if init[field] != baseline[field]: raise AssertionError('same property/strap/guitar: ' + field)
        if raw['states'][0]['guitar_body_states'] != baseline['native_initial_state']['guitar_body_states'] or init['input_trial']['main_target_offsets_rad'] != baseline['input_trial']['main_target_offsets_rad']:
            raise AssertionError('same guitar initial state/target offset law')
        if any(len(raw[n]) != 1201 for n in ('states', 'trace', 'tasks')) or any(len(raw[n]) != 1200 for n in ('contacts', 'controls')): raise AssertionError('raw coverage')
        if raw['states'][0] != init['native_initial_state'] or any(s['physics_step'] != i for i, s in enumerate(raw['states'])) or any(abs(t['time_s'] - i / 240) > 1e-9 for i, t in enumerate(raw['trace'])): raise AssertionError('raw initial/time')
        if any(c['physics_step'] != i + 1 or c['updated_before_step'] != (i % 4 == 0) or c['final_target_rad'] != raw['controls'][0]['final_target_rad'] for i, c in enumerate(raw['controls'])) or any(c['physics_step'] != i + 1 for i, c in enumerate(raw['contacts'])):
            raise AssertionError('constant commands/contact sequence')
        frames = captures[label]['frames']
        if len(frames) != 151 or set(report['videos']) != {'whole_body', 'hands'} or any(f['physics_step'] != i * 8 or abs(f['time_s'] - i / 30) > 1e-9 or not f['render_preserves_states'] for i, f in enumerate(frames)): raise AssertionError('camera coverage')
        if any(sha(p) != h for f in frames for p, h in f['image_sha256'].items()): raise AssertionError('actual image SHA')
        for video in report['videos'].values():
            proc = subprocess.run(video['ffprobe_command'], capture_output=True, text=True)
            if proc.returncode: raise RuntimeError('ffprobe failed')
            stream = json.loads(proc.stdout)['streams'][0]
            if stream != video['stream'] or int(stream['nb_read_frames']) != 151 or stream['avg_frame_rate'] != '30/1' or abs(float(stream['duration']) - 151 / 30) > .002 or sha(video['path']) != video['sha256']: raise AssertionError('video metadata/hash')
        groups = {}
        for row in raw['contacts']:
            for c in row['contacts']:
                a, b = c['body0_name'], c['body1_name']
                body = a if a.startswith('human/LH:') and b.startswith('guitar/') else b if b.startswith('human/LH:') and a.startswith('guitar/') else None
                if body:
                    group = groups.setdefault(body, {'rows': 0, 'positive_rows': 0, 'positive_steps': set()})
                    group['rows'] += 1
                    if c['lambda'] > 0: group['positive_rows'] += 1; group['positive_steps'].add(row['physics_step'])
        for group in groups.values(): group['positive_steps'] = sorted(group['positive_steps'])
        def metrics(end):
            trace = raw['trace'][:end + 1]
            return {'max_guitar_position_error_mm': max(t['position_error_m'] for t in trace) * 1000,
                    'max_guitar_rotation_error_deg': max(t['rotation_error_deg'] for t in trace),
                    'end_guitar_position_error_mm': trace[-1]['position_error_m'] * 1000,
                    'end_guitar_rotation_error_deg': trace[-1]['rotation_error_deg'],
                    'max_actual_torso_coordinate_drift_deg': float(np.abs([t['torso_drift_deg'] for t in trace]).max())}
        summary.append({'label': label, 'first_0p1s': metrics(24), 'full_5s': metrics(1200),
                        'initial_hull_gap_mm': {n: v['distance_m'] * 1000 for n, v in admission['source_hull_to_faces'].items()},
                        'three_face_initial_source_approach_satisfied': admission['three_face_source_approach_satisfied'],
                        'max_native_initial_FK_position_error_mm': admission['max_FK_position_error_m'] * 1000,
                        'max_native_initial_FK_rotation_error_rad': admission['max_FK_rotation_error_rad'],
                        'contacts_by_left_body': groups, 'palm_up_proxy_violations': len(report['constraint_violations']), 'stability_success': False})
        curves[label] = {'time_s': [t['time_s'] for t in raw['trace']], 'guitar_position_error_mm': [t['position_error_m'] * 1000 for t in raw['trace']],
                         'guitar_rotation_error_deg': [t['rotation_error_deg'] for t in raw['trace']]}
    execution = read(PHASE / 'execution.json')
    checks = {'three_native_5s_contracts_initial_source_FK': True, 'actual_initial_q_hard_limits_arm_box_other_dofs': True,
              'same_PD_strap_guitar_initial_and_target_offset_law': True, 'continuous_raw_and_actual_videos': True,
              'baseline_first24_exact': reports['baseline']['checks']['first24_five_arrays_exact'],
              'three_exit_zero': len(execution) == 3 and [e['label'] for e in execution] == list(LABELS) and all(e['exit_code'] == 0 for e in execution),
              'inputs_unchanged': all(sha(p) == h for p, h in hashes.items())}
    if not all(checks.values()): raise AssertionError(checks)
    output.write_text(json.dumps({'checks': checks, 'input_sha256': hashes, 'summary': summary, 'curves': curves,
        'counts': {'native_initializations': 3, 'physics_steps': 3600},
        'scope': 'native recorded grip approaches, not complete three-face initial contact or stability certification; named-body contacts are not plane-classified; raw lambda is not N; continuous source self-collision/clearance is not certified; FK tested at these two initial candidates only'}, indent=2) + '\n')
    print(json.dumps({'checks': checks, 'summary': [{**r, 'contacts_by_left_body': {n: {'rows': g['rows'], 'positive_rows': g['positive_rows'], 'last_positive_step': max(g['positive_steps'], default=None)} for n, g in r['contacts_by_left_body'].items()}} for r in summary]}, indent=2))


if __name__ == '__main__': main()
