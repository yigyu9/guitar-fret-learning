"""Analyze negative probe response and half-heldout locality without running physics."""
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1'
LABELS = ('negative_shoulder_y','negative_wrist_z','half_heldout')
OLD = PHASE.parent / 'seed2_guitar_response_v1'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())


def finite_numbers(value):
    if isinstance(value, dict): return all(finite_numbers(v) for v in value.values())
    if isinstance(value, list): return all(finite_numbers(v) for v in value)
    return not isinstance(value, (int, float)) or math.isfinite(value)


def main():
    output = PHASE / 'analysis.json'
    if output.exists(): raise FileExistsError('preserve earlier analysis')
    reports = {}; captures = {}; hashes = {}
    for label in LABELS:
        for name, target in (('report', reports), ('capture', captures)):
            p = PHASE / 'native' / label / (name + '.json'); hashes[str(p)] = sha(p); target[label] = read(p)
    paths = [Path(__file__).resolve(), PHASE / 'execution.json', PHASE / 'environment.json', PHASE / 'proposal.json', OLD / 'probe_analysis.json', OLD / 'heldout_analysis.json', OLD / 'native/base/initial_values.json']
    for label in LABELS:
        paths += [Path(p) for p in reports[label]['input_sha256']]
        paths += [PHASE / 'native' / label / (n + '.jsonl') for n in ('states', 'trace', 'tasks', 'contacts', 'controls')]
        paths += [PHASE / 'native' / label / (n + '.json') for n in ('initial_values', 'initial_grip_audit', 'videos')]
        paths += [Path(p) for f in captures[label]['frames'] for p in f['image_sha256']]
        paths += [Path(v['path']) for v in reports[label]['videos'].values()]
    hashes.update({str(p): sha(p) for p in paths})
    from .environment import np
    from .strap import cable_forces
    from .build_fixed_lower_asset import pose
    from scipy.spatial.transform import Rotation
    reference = read(OLD / 'probe_analysis.json'); heldout = read(OLD / 'heldout_analysis.json')
    if any(not all(a['checks'].values()) or any(sha(p)!=h for p,h in a['input_sha256'].items()) for a in (reference,heldout)): raise AssertionError('previous analyses closure')
    search = read(PHASE / 'proposal.json')
    if search['probe_axes'] != [f'L_{joint}_{axis}' for joint in ('Shoulder','Wrist') for axis in 'xyz']: raise AssertionError('six unique ordered probe axes')
    initial = {label: read(PHASE / 'native' / label / 'initial_values.json') for label in LABELS}
    baseline = read(OLD / 'native/base/initial_values.json')
    reference_raw = {n: [json.loads(line) for line in (OLD / 'native/base' / (n + '.jsonl')).read_text().splitlines()] for n in ('states','trace','tasks','contacts','controls')}
    raw_runs = {}
    summary = []; curves = {}
    for label in LABELS:
        folder = PHASE / 'native' / label; report = reports[label]; init = initial[label]
        raw = {n: [json.loads(line) for line in (folder / (n + '.jsonl')).read_text().splitlines()]
               for n in ('states', 'trace', 'tasks', 'contacts', 'controls')}
        raw_runs[label] = raw
        admission = read(folder / 'initial_grip_audit.json')
        if not all(finite_numbers(value) for value in (raw, init, report, admission, captures[label])):
            raise AssertionError('nonfinite native raw or metadata')
        if not report['completed'] or not all(report['checks'].values()) or report['physics_steps'] != 1200 or not all(admission['checks'].values()):
            raise AssertionError('native completion/source-FK gate')
        if any(sha(p) != h for p, h in report['input_sha256'].items()): raise AssertionError('native input closure')
        q = np.array([d['pos'] for d in raw['states'][0]['human_dof_states']]); q0 = np.array([d['pos'] for d in baseline['native_initial_state']['human_dof_states']])
        if q.tolist() != init['initial_PD_target_rad'] or not np.array_equal(q, q0): raise AssertionError('actual initial q/target/other DOF')
        if not ((q >= init['PD_properties']['lower']) & (q <= init['PD_properties']['upper'])).all(): raise AssertionError('actual initial native bounds')
        for field in ('human_joint_names', 'PD_properties', 'physics_parameters', 'guitar_goal_position_W_m', 'guitar_goal_quaternion_xyzw'):
            if init[field] != baseline[field]: raise AssertionError('same property/strap/guitar: ' + field)
        row = next(r for r in search['rows'] if r['label'] == label)
        residual = row['target_residual_rad']; bias = baseline['input_trial']['main_target_offsets_rad']
        names = init['human_joint_names']; arm = [i for i,n in enumerate(names) if n in bias]
        if len(arm) != 12 or init['declared_target_residual_rad'] != residual or init['declared_support_bias_rad'] != bias or init['input_trial']['main_target_offsets_rad'] != {n: v+residual.get(n,0.) for n,v in bias.items()}:
            raise AssertionError('declared exact left12 startup offsets')
        if raw['states'][0] != baseline['native_initial_state'] or {**init['input_trial'], 'main_target_offsets_rad': bias} != baseline['input_trial']:
            raise AssertionError('same initial state and trial except startup offsets')
        offset = np.array([init['input_trial']['main_target_offsets_rad'].get(n,0.) for n in names], dtype=np.float32)
        expected_target = np.clip(q.astype(np.float32)+offset, np.array(init['PD_properties']['lower'],dtype=np.float32), np.array(init['PD_properties']['upper'],dtype=np.float32))
        submitted = np.array(raw['controls'][0]['final_target_rad'])
        if not np.array_equal(submitted, expected_target[arm]) or not np.all(submitted >= np.array(init['PD_properties']['lower'])[arm]) or not np.all(submitted <= np.array(init['PD_properties']['upper'])[arm]):
            raise AssertionError('actual submitted startup target composition/native bounds')
        delta = submitted - q[arm]; largest = int(np.argmax(np.abs(delta)))
        startup = {'declared_residual_rad': residual, 'left_arm_names': [names[i] for i in arm], 'actual_target_delta_rad': delta.tolist(), 'max_abs_target_delta_deg': float(np.max(np.abs(delta))*180/np.pi), 'largest_target_change_joint': names[arm[largest]], 'native_clipped_coordinates': [names[i] for i in arm if expected_target[i] != (q.astype(np.float32)+offset)[i]]}
        if startup['native_clipped_coordinates']: raise AssertionError('probe target clipped')
        actual_arm_drift = np.array([[d['pos'] for d in state['human_dof_states']] for state in raw['states']])[:,arm] - q[arm]
        if any(len(raw[n]) != 1201 for n in ('states', 'trace', 'tasks')) or any(len(raw[n]) != 1200 for n in ('contacts', 'controls')): raise AssertionError('raw coverage')
        if raw['states'][0] != init['native_initial_state'] or any(s['physics_step'] != i for i, s in enumerate(raw['states'])) or any(abs(t['time_s'] - i / 240) > 1e-9 for i, t in enumerate(raw['trace'])): raise AssertionError('raw initial/time')
        if any(c['physics_step'] != i + 1 or c['updated_before_step'] != (i % 4 == 0) or c['final_target_rad'] != raw['controls'][0]['final_target_rad'] for i, c in enumerate(raw['controls'])) or any(c['physics_step'] != i + 1 for i, c in enumerate(raw['contacts'])):
            raise AssertionError('constant commands/contact sequence')
        frames = captures[label]['frames']
        if any(len(f['image_sha256']) != 2 or {Path(p).parent.name for p in f['image_sha256']} != {'whole_body', 'hands'} for f in frames):
            raise AssertionError('both actual camera views at every frame')
        if len(frames) != 151 or set(report['videos']) != {'whole_body', 'hands'} or any(f['physics_step'] != i * 8 or abs(f['time_s'] - i / 30) > 1e-9 or not f['render_preserves_states'] for i, f in enumerate(frames)): raise AssertionError('camera coverage')
        if any(sha(p) != h for f in frames for p, h in f['image_sha256'].items()): raise AssertionError('actual image SHA')
        for video in report['videos'].values():
            proc = subprocess.run(video['ffprobe_command'], capture_output=True, text=True)
            if proc.returncode: raise RuntimeError('ffprobe failed')
            stream = json.loads(proc.stdout)['streams'][0]
            if stream != video['stream'] or int(stream['nb_read_frames']) != 151 or stream['avg_frame_rate'] != '30/1' or abs(float(stream['duration']) - 151 / 30) > .002 or sha(video['path']) != video['sha256']: raise AssertionError('video metadata/hash')
        coefficients = init['strap_law_parameters']
        if (coefficients['stiffness_n_per_m'], coefficients['damping_n_s_per_m'], coefficients['max_tension_n']) != (6000,120,300): raise AssertionError('unchanged strap law parameters')
        if init['initial_route_length_m'] != baseline['initial_route_length_m'] or init['absolute_strap_rest_length_m'] != next(r['absolute_strap_rest_length_m'] for r in search['rows'] if r['label']==label): raise AssertionError('route/declared LA')
        predicted = [cable_forces(np.array(t['route_points_m']), np.array(t['route_point_velocities_mps']), init['absolute_strap_rest_length_m'], 6000,120,300)[1] for t in raw['trace'][:-1]]
        applied = [t['last_applied_tension_n'] for t in raw['trace'][1:]]
        law_error = float(np.max(np.abs(np.array(predicted)-applied)))
        if law_error > 1e-8 or any(t['strap_rest_length_m'] != init['absolute_strap_rest_length_m'] for t in raw['trace']): raise AssertionError('previous-state strap law/fixed LA')
        groups = {}; all_guitar_groups = {}
        for row in raw['contacts']:
            for c in row['contacts']:
                a, b = c['body0_name'], c['body1_name']
                other_body = a if b.startswith('guitar/') and not a.startswith('guitar/') else b if a.startswith('guitar/') and not b.startswith('guitar/') else None
                if other_body:
                    all_group = all_guitar_groups.setdefault(other_body, {'rows': 0, 'positive_rows': 0, 'positive_steps': set(), 'last_contact_step': 0})
                    all_group['rows'] += 1; all_group['last_contact_step'] = row['physics_step']
                    if c['lambda'] > 0: all_group['positive_rows'] += 1; all_group['positive_steps'].add(row['physics_step'])
                body = a if a.startswith(('human/LH:', 'human/RH:')) and b.startswith('guitar/') else b if b.startswith(('human/LH:', 'human/RH:')) and a.startswith('guitar/') else None
                if body:
                    group = groups.setdefault(body, {'rows': 0, 'positive_rows': 0, 'positive_steps': set(), 'last_contact_step': 0})
                    group['rows'] += 1; group['last_contact_step'] = row['physics_step']
                    if c['lambda'] > 0: group['positive_rows'] += 1; group['positive_steps'].add(row['physics_step'])
        for group in groups.values(): group['positive_steps'] = sorted(group['positive_steps'])
        for group in all_guitar_groups.values():
            group['positive_step_count'] = len(group['positive_steps']); group['last_positive_step'] = max(group['positive_steps'], default=None); group['positive_steps'] = sorted(group['positive_steps'])
        def metrics(end):
            trace = raw['trace'][:end + 1]
            return {'max_guitar_position_error_mm': max(t['position_error_m'] for t in trace) * 1000,
                    'max_guitar_rotation_error_deg': max(t['rotation_error_deg'] for t in trace),
                    'end_guitar_position_error_mm': trace[-1]['position_error_m'] * 1000,
                    'end_guitar_rotation_error_deg': trace[-1]['rotation_error_deg'],
                    'max_actual_torso_coordinate_drift_deg': float(np.abs([t['torso_drift_deg'] for t in trace]).max()),
                    'max_actual_left_arm_coordinate_drift_deg': float(np.max(np.abs(actual_arm_drift[:end+1]))*180/np.pi)}
        summary.append({'label': label, 'startup_target': startup, 'first_0p1s': metrics(24), 'full_5s': metrics(1200),
                        'initial_hull_gap_mm': {n: v['distance_m'] * 1000 for n, v in admission['source_hull_to_faces'].items()},
                        'three_face_initial_source_approach_satisfied': admission['three_face_source_approach_satisfied'],
                        'max_native_initial_FK_position_error_mm': admission['max_FK_position_error_m'] * 1000,
                        'max_native_initial_FK_rotation_error_rad': admission['max_FK_rotation_error_rad'],
                        'contacts_by_any_other_body': all_guitar_groups,
                        'contacts_by_left_body': {n:g for n,g in groups.items() if n.startswith('human/LH:')}, 'contacts_by_right_body': {n:g for n,g in groups.items() if n.startswith('human/RH:')}, 'strap': {'absolute_rest_length_m': init['absolute_strap_rest_length_m'], 'initial_route_length_m': init['initial_route_length_m'], 'first_step_submitted_law_tension_n': applied[0], 'max_submitted_law_tension_n': max(applied), 'end_submitted_law_tension_n': applied[-1], 'first_positive_law_step': next((i+1 for i,t in enumerate(applied) if t>0), None), 'law_reconstruction_max_error_n': law_error}, 'palm_up_proxy_violations': len(report['constraint_violations']), 'stability_success': False})
        curves[label] = {'time_s': [t['time_s'] for t in raw['trace']], 'guitar_position_error_mm': [t['position_error_m'] * 1000 for t in raw['trace']],
                         'guitar_rotation_error_deg': [t['rotation_error_deg'] for t in raw['trace']], 'strap_length_m': [t['strap_length_m'] for t in raw['trace']], 'max_actual_left_arm_coordinate_drift_deg': (np.max(np.abs(actual_arm_drift),axis=1)*180/np.pi).tolist(), 'tension_input_time_s': [t['time_s'] for t in raw['trace'][:-1]], 'submitted_law_tension_n': applied}
        goal_p=np.array(init['guitar_goal_position_W_m']); goal_R=Rotation.from_quat(init['guitar_goal_quaternion_xyzw'])
        errors=[]
        for state,t in zip(raw['states'],raw['trace']):
            p,qg=pose(state['guitar_body_states'][0]); rot=(Rotation.from_quat(qg)*goal_R.inv()).as_rotvec()
            if not np.array_equal(p,np.array(t['guitar_position_m'])) or not np.allclose(qg/np.linalg.norm(qg),t['guitar_quaternion_xyzw'],rtol=0,atol=1e-15): raise AssertionError('state/trace guitar pose')
            if abs(np.linalg.norm(p-goal_p)-t['position_error_m'])>1e-12 or abs(np.degrees(np.linalg.norm(rot))-t['rotation_error_deg'])>1e-4: raise AssertionError('world pose-error norm')
            errors.append(np.concatenate((p-goal_p,rot)).tolist())
        curves[label]['guitar_error_vector_W_m_rad']=errors
    axes=search['probe_axes']; arm_names=summary[0]['startup_target']['left_arm_names']
    base_target=np.array(reference_raw['controls'][0]['final_target_rad'])
    deltas={label:np.array(raw_runs[label]['controls'][0]['final_target_rad'])-base_target for label in LABELS}
    for label,axis in [('negative_shoulder_y','L_Shoulder_y'),('negative_wrist_z','L_Wrist_z')]:
        index=arm_names.index(axis)
        if np.flatnonzero(deltas[label]).tolist()!=[index] or deltas[label][index]>=0: raise AssertionError('actual negative single-axis probe')
    half_delta=np.array([deltas['half_heldout'][arm_names.index(n)] for n in axes])
    full_delta=np.array(heldout['actual_float32_target_difference_rad'])
    if np.any(full_delta==0): raise AssertionError('nonzero heldout axes required for ratio')
    alpha=float((full_delta@half_delta)/(full_delta@full_delta))
    windows={'t0p1':slice(24,25),'t1':slice(240,241),'t5':slice(1200,1201),'last1s_mean':slice(960,1201)}
    pairs={}; half={}
    for name,window in windows.items():
        base_error=np.array(reference['curves']['base']['guitar_error_vector_W_m_rad'])[window].mean(axis=0)
        pair_rows={};central_columns=[]
        for label,positive_label,axis in [('negative_shoulder_y','shoulder_y','L_Shoulder_y'),('negative_wrist_z','wrist_z','L_Wrist_z')]:
            axis_index=axes.index(axis); joint_index=arm_names.index(axis)
            dp=reference['response_identification']['actual_submitted_probe_steps_rad'][axis_index];dm=float(deltas[label][joint_index])
            ep=np.array(reference['curves'][positive_label]['guitar_error_vector_W_m_rad'])[window].mean(axis=0)
            em=np.array(curves[label]['guitar_error_vector_W_m_rad'])[window].mean(axis=0)
            jp=(ep-base_error)/dp;jm=(em-base_error)/dm;jc=(ep-em)/(dp-dm)
            zero_interp=(dp*em-dm*ep)/(dp-dm);interpolation_error=zero_interp-base_error
            pair_rows[axis]={'actual_positive_step_rad':dp,'actual_negative_step_rad':dm,'positive_error_W_m_rad':ep.tolist(),'negative_error_W_m_rad':em.tolist(),'forward_derivative_m_per_rad_rad_per_rad':jp.tolist(),'backward_derivative_m_per_rad_rad_per_rad':jm.tolist(),'central_derivative_m_per_rad_rad_per_rad':jc.tolist(),'zero_interpolation_error_W_m_rad':interpolation_error.tolist(),'zero_interpolation_position_residual_mm':float(np.linalg.norm(interpolation_error[:3])*1000),'zero_interpolation_rotation_vector_residual_deg':float(np.degrees(np.linalg.norm(interpolation_error[3:])))}
            central_columns.append(jc)
        weighted=np.diag([1,1,1,.1,.1,.1])@np.array(central_columns).T;singular=np.linalg.svd(weighted,compute_uv=False);rank=int(np.linalg.matrix_rank(weighted))
        pairs[name]={'baseline_error_W_m_rad':base_error.tolist(),'axes':pair_rows,'central_matrix_6x2_m_per_rad_rad_per_rad':np.array(central_columns).T.tolist(),'provisional_rotation_lever_m':.1,'weighted_rank':rank,'weighted_singular_values_m_per_rad':singular.tolist(),'weighted_condition_number':float(np.linalg.cond(weighted)) if rank==2 else None}
        actual=np.array(curves['half_heldout']['guitar_error_vector_W_m_rad'])[window].mean(axis=0)
        prediction=base_error+np.array(reference['response_identification']['windows'][name]['jacobian_rows_m_per_rad_rad_per_rad'])@half_delta
        full_error=np.array(heldout['comparisons'][name]['actual_error_W_m_rad']);interpolated=base_error+alpha*(full_error-base_error)
        rp=actual-prediction;ri=actual-interpolated
        half[name]={'actual_error_W_m_rad':actual.tolist(),'old_J_predicted_error_W_m_rad':prediction.tolist(),'full_heldout_error_W_m_rad':full_error.tolist(),'actual_target_alpha_interpolated_error_W_m_rad':interpolated.tolist(),'old_J_prediction_residual_W_m_rad':rp.tolist(),'old_J_prediction_position_residual_mm':float(np.linalg.norm(rp[:3])*1000),'old_J_prediction_rotation_vector_residual_deg':float(np.degrees(np.linalg.norm(rp[3:]))),'target_alpha_interpolation_residual_W_m_rad':ri.tolist(),'target_alpha_interpolation_position_residual_mm':float(np.linalg.norm(ri[:3])*1000),'target_alpha_interpolation_rotation_vector_residual_deg':float(np.degrees(np.linalg.norm(ri[3:])))}
    execution = read(PHASE / 'execution.json')
    checks = {'three_native_5s_contracts_initial_source_FK': True, 'all81_initial_q_seed2_exact_native_bounds': True,
              'same_initial_q_PD_guitar_LA_only_sixaxis_declared_residual': True, 'continuous_raw_and_actual_videos': True,
              'three_exit_zero': len(execution) == 3 and [e['label'] for e in execution] == list(LABELS) and all(e['exit_code'] == 0 for e in execution),
              'previous_saved_reference_inputs_unchanged': all(sha(p)==h for a in (reference,heldout) for p,h in a['input_sha256'].items()),
              'previous_state_strap_law_and_fixed_LA': True,
              'inputs_unchanged': all(sha(p) == h for p, h in hashes.items())}
    if not all(checks.values()): raise AssertionError(checks)
    output.write_text(json.dumps({'checks': checks, 'input_sha256': hashes, 'summary': summary, 'curves': curves,
        'reference_seed2': {'summary': next(r for r in reference['summary'] if r['label'] == 'base'), 'curve': reference['curves']['base'], 'path': str(OLD / 'probe_analysis.json'), 'scope': 'previous saved 5s run, not a new initialization'},
        'guitar_first24_pose_exact_vs_saved_base': {label:all(raw_runs[label]['trace'][i][f]==reference_raw['trace'][i][f] for i in range(25) for f in ('guitar_position_m','guitar_quaternion_xyzw')) for label in LABELS},
        'counts': {'native_initializations': 3, 'physics_steps': 3600},
        'locality':{'paired_windows':pairs,'half_heldout_windows':half,'half_actual_target_difference_rad':half_delta.tolist(),'full_heldout_actual_target_difference_rad':full_delta.tolist(),'actual_target_alpha_least_squares':alpha,'half_over_full_target_ratio_per_axis':(half_delta/full_delta).tolist(),'half_minus_alpha_full_target_rad':(half_delta-alpha*full_delta).tolist(),'axes':axes,'rotation_error_definition':'Log(R_current R_goal^-1) in world radians; xyzw raw quaternion','last1s_mean_steps_inclusive':[960,1200],'reference_heldout_summary':{k:heldout[k] for k in ('first_0p1s','full_5s','comparisons')}},
        'scope': 'native negative single-axis/half-heldout locality comparison with unchanged initial q/LA/PD/G; actual coordinate drift is not SO3 joint angle; submitted law scalar reconstructed from previous state is not a native force sensor; tension_input_time_s is the start of each force interval; named-body contacts not plane-classified; raw lambda not N; continuous source clearance and stability not certified'}, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'checks': checks, 'summary': [{**r, 'contacts_by_left_body': {n: {'rows': g['rows'], 'positive_rows': g['positive_rows'], 'last_contact_step': g['last_contact_step'], 'last_positive_step': max(g['positive_steps'], default=None)} for n, g in r['contacts_by_left_body'].items()}} for r in summary]}, indent=2))


if __name__ == '__main__': main()
