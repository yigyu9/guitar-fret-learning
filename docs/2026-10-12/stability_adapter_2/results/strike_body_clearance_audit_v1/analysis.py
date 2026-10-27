"""Offline source mesh/front-plane audit; no simulator imports or writes."""
import ast
import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial.transform import Rotation as R

ROOT = Path('/home/ajou/yigyu/3')
RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
OUT = Path(__file__).resolve().parent
HUMAN = ROOT / 'stability_adapter_2/assets/humanoid_fixed_lower.xml'
GUITAR = ROOT / 'tab2body/assets/guitar_asset.xml'
GRIP = ROOT / 'strike/02_physical_control/pick-grip-reference.json'
CHECKPOINT = ROOT / 'strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt'
FK_SOURCE = RESULTS / 'strike_effort_geometry_pi_v1/native/source_before/stability_adapter_2/underneck_initial_search.py'
TRIALS = ('strike_timed_wait_rebase_v1', 'strike_effort_geometry_pi_v1')
FOLD = [f'RH:{finger}{segment}' for finger in ('middle', 'ring', 'pinky') for segment in (2, 3)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def pose(state):
    return np.array([state['pose']['p'][a] for a in 'xyz']), R.from_quat([state['pose']['r'][a] for a in 'xyzw'])


def stl_vertices(path):
    raw = path.read_bytes()
    count = struct.unpack('<I', raw[80:84])[0]
    assert len(raw) == 84 + 50 * count
    dtype = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
    return np.ndarray((count,), dtype=dtype, buffer=raw, offset=84)['vertices'].reshape(-1, 3).astype(float)


def meshes(xml):
    assets = {mesh.get('name'): mesh for mesh in xml.findall('./asset/mesh')}
    meshdir = (HUMAN.parent / xml.find('compiler').get('meshdir')).resolve()
    geometries, paths = {}, []
    for body in xml.iter('body'):
        name = body.get('name')
        if not name.startswith('RH:'):
            continue
        for geom in body.findall('geom'):
            assert geom.get('type') == 'mesh', (name, geom.attrib)
            asset = assets[geom.get('mesh')]
            path = meshdir / asset.get('file')
            vertices = stl_vertices(path) * np.fromstring(asset.get('scale', '1 1 1'), sep=' ')
            q = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
            vertices = R.from_quat(np.roll(q, -1)).apply(vertices)
            vertices += np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
            geometries[name] = {'vertices': vertices, 'mesh_file': str(path), 'geom_attributes': geom.attrib,
                                'mesh_attributes': asset.attrib, 'vertex_count': len(vertices)}
            paths.append(path)
    return geometries, paths


def contacts(control):
    rows = []
    for contact in control['contacts']:
        pair = [contact.get('body0_name', ''), contact.get('body1_name', '')]
        if 'guitar/G:body' in pair and any(name.startswith('human/RH:') for name in pair):
            rows.append({'body_pair': pair, 'lambda': contact['lambda'], 'minDist': contact['minDist'],
                         'initialOverlap': contact['initialOverlap']})
    return rows


def audit_poses(poses, guitar_poses, geometries, body_geom):
    gp, gr = guitar_poses['guitar']
    bp, br = guitar_poses['G:body']
    half = np.fromstring(body_geom.get('size'), sep=' ')
    center = np.fromstring(body_geom.get('pos', '0 0 0'), sep=' ')
    normal = br.apply([0, 0, 1])
    front = bp + br.apply(center + [0, 0, half[2]])
    pick = poses['RH:pick'][0]
    rows = {}
    for name, geometry in geometries.items():
        p, r = poses[name]
        world = p + r.apply(geometry['vertices'])
        local = br.inv().apply(world - bp) - center
        clearance = local[:, 2] - half[2]
        k = int(np.argmin(clearance))
        footprint = np.all(abs(local[:, :2]) <= half[:2] + 1e-12, axis=1)
        inside = footprint & (abs(local[:, 2]) <= half[2])
        rows[name] = {'minimum_front_plane_clearance_mm': float(clearance[k] * 1000),
                      'minimum_vertex_G_m': gr.inv().apply(world[k] - gp).tolist(),
                      'minimum_vertex_inside_box_xy_footprint': bool(footprint[k]),
                      'footprint_vertex_count': int(footprint.sum()),
                      'minimum_sampled_vertex_clearance_in_footprint_mm': float(clearance[footprint].min() * 1000) if footprint.any() else None,
                      'source_vertices_inside_box_count': int(inside.sum()),
                      'body_origin_G_m': gr.inv().apply(p - gp).tolist()}
    groups = {}
    for group in ('thumb', 'index', 'middle', 'ring', 'pinky', 'palm'):
        members = [n for n in rows if n.startswith('RH:' + group)]
        worst = min(members, key=lambda n: rows[n]['minimum_front_plane_clearance_mm'])
        groups[group] = {'minimum_front_plane_clearance_mm': rows[worst]['minimum_front_plane_clearance_mm'], 'body': worst}
    pick_gap = float((pick - front) @ normal * 1000)
    for group in groups.values():
        relative = group['minimum_front_plane_clearance_mm'] - pick_gap
        group['minimum_front_support_relative_to_pick_mm'] = relative
        group['rigid_translate_pick_to_nominal_READY_plane_clearance_mm'] = relative + 22.
        group['rigid_translate_pick_to_nominal_ENTRY_EXIT_plane_clearance_mm'] = relative + 12.5
    return {'pick_origin_G_m': gr.inv().apply(pick - gp).tolist(),
            'pick_front_plane_clearance_mm': pick_gap,
            'Gbody_front_center_G_m': gr.inv().apply(front - gp).tolist(),
            'Gbody_front_normal_G': gr.inv().apply(normal).tolist(),
            'groups': groups, 'bodies': rows}


def main():
    xml = ET.parse(HUMAN).getroot()
    gx = ET.parse(GUITAR).getroot()
    gbody = next(b for b in gx.iter('body') if b.get('name') == 'G:body')
    body_geom = gbody.find('geom')
    assert body_geom.get('type') == 'box' and body_geom.get('quat') is None
    geometries, mesh_paths = meshes(xml)
    data_paths = [RESULTS / trial / 'native/data' / filename for trial in TRIALS
                  for filename in ('initial_values.json', 'trace.json', 'controls.json', 'checkpoint_connection.json')]
    source_paths = [HUMAN, GUITAR, GRIP, CHECKPOINT, FK_SOURCE, Path(__file__).resolve(),
                    ROOT / 'stability_adapter_2/underneck_initial_search.py',
                    ROOT / 'tab2body/env/tasks/task_strike.py', ROOT / 'stability_adapter_2/environment.py',
                    ROOT / 'isaacgym/docs/programming/assets.html']
    paths = list(dict.fromkeys(source_paths + data_paths + mesh_paths))
    before = {str(p): sha(p) for p in paths}
    # Extract only the frozen pure FK function, avoiding all simulator/environment imports.
    module = ast.parse(FK_SOURCE.read_text())
    function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'calibrated_fk')
    namespace = {'ET': ET, 'ROOT': ROOT, 'pose': pose, 'np': np, 'R': R}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(FK_SOURCE), 'exec'), namespace)
    calibrated_fk = namespace['calibrated_fk']
    current_ast = ast.parse((ROOT / 'stability_adapter_2/underneck_initial_search.py').read_text())
    current_function = next(node for node in current_ast.body if isinstance(node, ast.FunctionDef) and node.name == 'calibrated_fk')
    function_dump = ast.dump(function, include_attributes=False)
    grip = read(GRIP)
    free = grip['groups']['free']
    reference = grip['joint_targets_rad']
    # Loading checkpoint CPU data is read-only; no model or simulator is instantiated.
    import torch
    checkpoint = torch.load(CHECKPOINT, map_location='cpu', weights_only=True)
    trajectory = checkpoint['checkpoint_contract']['payload']['config']['strike']['trajectory']
    surface_z = float(next(b for b in gx.iter('body') if b.get('name') == 'G:string1').get('pos').split()[2])
    front_z = float(gbody.get('pos').split()[2]) + float(body_geom.get('size').split()[2])
    result = {'scope': 'source mesh vertex support and static FK only; no native geometry/contact equivalence or causal claim',
              'physics_steps': 0, 'native_initializations': 0,
              'source_Gbody': {'body_attributes': gbody.attrib, 'geom_attributes': body_geom.attrib,
                               'front_G_z_m': front_z, 'footprint_G_x_m': [-.15, .15], 'footprint_G_y_m': [-.57, -.23]},
              'source_waypoints': {n: {'G_z_m': z, 'front_plane_clearance_mm': (z - front_z) * 1000}
                  for n, z in [('string_surface', surface_z), ('READY', surface_z + trajectory['ready_height_m']),
                               ('ENTRY', surface_z - trajectory['crossing_depth_m']), ('EXIT', surface_z - trajectory['crossing_depth_m']),
                               ('recovery_lift', surface_z + trajectory['clearance_height_m'])]},
              'source_geometry': {n: {k: v for k, v in geometry.items() if k != 'vertices'} for n, geometry in geometries.items()},
              'virtual_pick': grip['semantics'], 'trajectory': trajectory, 'trials': {}}
    result['calibrated_fk_function_ast_sha256'] = hashlib.sha256(function_dump.encode()).hexdigest()
    result['current_calibrated_fk_ast_matches_frozen'] = function_dump == ast.dump(current_function, include_attributes=False)
    free_residual = checkpoint['checkpoint_contract']['payload']['config']['strike']['grip_control']['free_residual_rad']
    for trial in TRIALS:
        directory = RESULTS / trial / 'native/data'
        initial, trace, controls = [read(directory / name) for name in ('initial_values.json', 'trace.json', 'controls.json')]
        hn, gn, names = [initial[k] for k in ('human_body_names', 'guitar_body_names', 'joint_names')]
        assert len(trace) in (151, 152) and len(names) == 81
        snapshots = []
        for row in trace:
            state = row['native_state']
            poses = {n: pose(s) for n, s in zip(hn, state['human_body_states'])}
            guitars = {n: pose(s) for n, s in zip(gn, state['guitar_body_states'])}
            audited = audit_poses(poses, guitars, geometries, body_geom)
            control = min(controls, key=lambda c: abs(c['time_s'] - row['time_s']))
            audited.update(time_s=row['time_s'], physics_step=row['physics_step'], phase=row['phase'],
                           native_contacts=contacts(control), contact_sample_time_s=control['time_s'])
            phase = control.get('phase_target_residual')
            audited['source_motor_phase'] = phase.get('source_motor_phase') if phase else None
            audited['target_geometry_index'] = phase.get('target_geometry_index') if phase else None
            audited['target_G_m'] = phase.get('target_G_m') if phase else None
            snapshots.append(audited)
        selected = []
        for requested in (0., 1., 1.1666666667, 1.2, 1.3333333333, 1.35, 1.3666666667, 1.4, 2., 5.):
            row = min(snapshots, key=lambda s: abs(s['time_s'] - requested))
            selected.append({'requested_time_s': requested, **row})
        all_contacts = [{'time_s': c['time_s'], 'rows': contacts(c)} for c in controls if contacts(c)]
        first_positive = next((c for c in all_contacts if any(r['lambda'] > 0 for r in c['rows'])), None)
        minimums = {group: min(({'time_s': s['time_s'], **s['groups'][group]} for s in snapshots),
                              key=lambda s: s['minimum_front_plane_clearance_mm']) for group in ('thumb', 'index', 'middle', 'ring', 'pinky', 'palm')}
        result['trials'][trial] = {'state_count': len(trace), 'control_count': len(controls), 'selected_snapshots': selected,
                                 'minimums_over_all_saved_states': minimums, 'first_positive_RH_Gbody_contact': first_positive,
                                 'snapshots': snapshots}
        state = min(trace, key=lambda s: abs(s['time_s'] - 1.2))['native_state']
        q = np.array([s['pos'] for s in state['human_dof_states']])
        fold_indices = [names.index(n) for n in FOLD]
        qnew = q.copy()
        low, high = [np.array(initial[k]) for k in ('native_lower_rad', 'native_upper_rad')]
        qnew[fold_indices] = np.clip(q[fold_indices] + .2, low[fold_indices], high[fold_indices])
        actual_fk, _ = calibrated_fk(names, hn, state, q)
        guitars = {n: pose(s) for n, s in zip(gn, state['guitar_body_states'])}
        base_audit = audit_poses(actual_fk(q), guitars, geometries, body_geom)
        fold_audit = audit_poses(actual_fk(qnew), guitars, geometries, body_geom)
        initial_fk, _ = calibrated_fk(names, hn, initial['native_initial_state'], np.array(initial['initial_angles_rad']))
        p0, r0 = pose(initial['native_initial_state']['human_body_states'][hn.index('Chest')])
        cp, cr = pose(state['human_body_states'][hn.index('Chest')])
        delta = cr * r0.inv()
        def align(qvalue):
            return {n: (cp + delta.apply(p - p0), delta * r) for n, (p, r) in initial_fk(qvalue).items()}
        initial_base = align(q)
        initial_fold = align(qnew)
        actual_poses = actual_fk(q)
        errors = {n: {'position_mm': float(np.linalg.norm(initial_base[n][0] - actual_poses[n][0]) * 1000),
                      'rotation_deg': float(np.degrees((initial_base[n][1] * actual_poses[n][1].inv()).magnitude()))}
                  for n in geometries}
        fi = [names.index(n) for n in free]
        ref = np.array([reference[n] for n in free])
        individual = {}
        for n, i in zip(FOLD, fold_indices):
            one = q.copy()
            one[i] = qnew[i]
            audited_one = audit_poses(actual_fk(one), guitars, geometries, body_geom)
            individual[n] = {g: {'before_mm': base_audit['groups'][g]['minimum_front_plane_clearance_mm'],
                                'after_mm': audited_one['groups'][g]['minimum_front_plane_clearance_mm'],
                                'delta_mm': audited_one['groups'][g]['minimum_front_plane_clearance_mm'] - base_audit['groups'][g]['minimum_front_plane_clearance_mm']}
                             for g in ('middle', 'ring', 'pinky')}
        result['trials'][trial]['static_plus_0_2_rad_six_free_hinges_at_1_2s'] = {
            'coordinate_changes': {n: {'actual_rad': float(q[i]), 'candidate_rad': float(qnew[i]), 'delta_rad': float(qnew[i] - q[i])} for n, i in zip(FOLD, fold_indices)},
            'candidate_in_native_bounds': bool(np.all((qnew[fold_indices] >= low[fold_indices]) & (qnew[fold_indices] <= high[fold_indices]))),
            'other75_unchanged': bool(np.array_equal(qnew[np.setdiff1d(np.arange(81), fold_indices)], q[np.setdiff1d(np.arange(81), fold_indices)])),
            'pinch9_unchanged': bool(np.array_equal(qnew[[names.index(n) for n in grip['groups']['pinch']]], q[[names.index(n) for n in grip['groups']['pinch']]])),
            'actual_free12_RMS_from_reference_rad': float(np.sqrt(np.mean((q[fi] - ref) ** 2))),
            'candidate_free12_RMS_from_reference_rad': float(np.sqrt(np.mean((qnew[fi] - ref) ** 2))),
            'success_free_RMS_threshold_rad': grip['reward']['success_free_rms_rad'],
            'baseline_actual_snapshot_calibrated_FK': base_audit, 'candidate_actual_snapshot_calibrated_FK': fold_audit,
            'original_initial_calibration_chest_aligned_baseline': audit_poses(initial_base, guitars, geometries, body_geom),
            'original_initial_calibration_chest_aligned_candidate': audit_poses(initial_fold, guitars, geometries, body_geom),
            'original_initial_calibration_pose_errors_vs_actual': errors,
            'single_hinge_plus_0_2_rad_front_support_changes': individual,
            'semantics': 'Pure existing calibrated_fk, recalibrated at saved actual 1.2s for exact static baseline; original native-initial calibration independently reported. No native candidate state/contact prediction.'}
        four_names = FOLD[:4]
        four_indices = [names.index(n) for n in four_names]
        four_rows = []
        for selected_row in selected:
            native_row = next(r for r in trace if r['physics_step'] == selected_row['physics_step'])
            saved = native_row['native_state']
            actual_q = np.array([s['pos'] for s in saved['human_dof_states']])
            proposed = actual_q.copy()
            proposed[four_indices] = np.clip(actual_q[four_indices] + .2, low[four_indices], high[four_indices])
            snapshot_fk, _ = calibrated_fk(names, hn, saved, actual_q)
            saved_guitar = {n: pose(s) for n, s in zip(gn, saved['guitar_body_states'])}
            proposed_audit = audit_poses(snapshot_fk(proposed), saved_guitar, geometries, body_geom)
            four_rows.append({'requested_time_s': selected_row['requested_time_s'], 'actual_saved_time_s': native_row['time_s'],
                              'physics_step': native_row['physics_step'],
                              'joint_changes': {n: {'actual_rad': float(actual_q[i]), 'candidate_rad': float(proposed[i]),
                                                    'delta_rad': float(proposed[i] - actual_q[i])} for n, i in zip(four_names, four_indices)},
                              'actual_free12_RMS_from_reference_rad': float(np.sqrt(np.mean((actual_q[fi] - ref) ** 2))),
                              'candidate_free12_RMS_from_reference_rad': float(np.sqrt(np.mean((proposed[fi] - ref) ** 2))),
                              'source_free_residual_cap_rad': free_residual,
                              'candidate_free_coordinates_beyond_source_reference_plusminus_residual': {n: float(proposed[i] - reference[n]) for n, i in zip(free, fi) if abs(proposed[i] - reference[n]) > free_residual + 1e-12},
                              'actual_baseline_groups': selected_row['groups'], 'candidate': proposed_audit,
                              'pick_origin_displacement_mm': float(np.linalg.norm(snapshot_fk(proposed)['RH:pick'][0] - snapshot_fk(actual_q)['RH:pick'][0]) * 1000),
                              'other77_unchanged': bool(np.array_equal(proposed[np.setdiff1d(np.arange(81), four_indices)], actual_q[np.setdiff1d(np.arange(81), four_indices)]))})
        result['trials'][trial]['static_plus_0_2_rad_middle2_3_ring2_3_selected_snapshots'] = four_rows
    result['front_support_translation_semantics'] = 'Same whole-hand orientation/finger pose, rigid normal translation until virtual pick reaches nominal READY gap22mm or ENTRY/EXIT gap12.5mm; infinite front plane only, not triangle-box intersection, reachable arm motion, or native contact prediction.'
    result['reference_only_four_hinge_plus_0_2_free12_RMS_rad'] = float(np.sqrt(4 * .2 ** 2 / 12))
    result['input_sha256'] = before
    result['checks'] = {'input_files_unchanged': all(sha(Path(p)) == h for p, h in before.items()),
                        'zero_physics': True, 'RHpick_has_no_geom': not next(b for b in xml.iter('body') if b.get('name') == 'RH:pick').findall('geom'),
                        'all15_finger_meshes_and_palm': len(geometries) == 16}
    assert all(result['checks'].values())
    (OUT / 'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'checks': result['checks'], 'source_waypoints': result['source_waypoints'],
                      'fold': {trial: {'free_RMS_rad': result['trials'][trial]['static_plus_0_2_rad_six_free_hinges_at_1_2s']['candidate_free12_RMS_from_reference_rad'],
                                      'groups': result['trials'][trial]['static_plus_0_2_rad_six_free_hinges_at_1_2s']['candidate_actual_snapshot_calibrated_FK']['groups']} for trial in TRIALS}}, indent=2))


if __name__ == '__main__':
    main()
