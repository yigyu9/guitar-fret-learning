"""Map stored native contact features to finite source patches; no simulation."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
PHASE = BASE / 'three_face_native_feature_map_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    if (PHASE / 'analysis.json').exists():
        raise FileExistsError('preserve consumed analysis')
    manifest = read(PHASE / 'input_manifest.json')
    hashes = manifest['input_sha256']
    if not all(sha(path) == expected for path, expected in hashes.items()):
        raise AssertionError('sealed inputs changed')
    hashes[str(PHASE / 'input_manifest.json')] = sha(PHASE / 'input_manifest.json')
    if hashes[str(Path(__file__).resolve())] != sha(__file__):
        raise AssertionError('sealed producer changed')
    import numpy as np
    from scipy.spatial.transform import Rotation
    from .initial_overlap import build_probe
    from .face_referenced_geometry import face_geometry

    def vector(value):
        return np.array([value[k] for k in 'xyz'], dtype=float)

    def pose(value):
        return vector(value['pose']['p']), Rotation.from_quat(
            [value['pose']['r'][k] for k in 'xyzw'])

    def patch_metrics(point, normal, polygon, outward):
        origin = polygon[0]
        axis = np.cross(polygon[1] - origin, polygon[2] - origin)
        axis /= np.linalg.norm(axis)
        if np.dot(axis, outward) < 0:
            axis = -axis
        signed = float(np.dot(point - origin, axis))
        projected = point - signed * axis
        edges = np.roll(polygon, -1, axis=0) - polygon
        side = np.array([np.dot(np.cross(e, projected - p), axis)
                         for p, e in zip(polygon, edges)])
        inside = bool(np.all(side >= -1e-12) or np.all(side <= 1e-12))
        fractions = np.clip(np.sum((projected - polygon) * edges, axis=1)
                            / np.sum(edges * edges, axis=1), 0, 1)
        boundary = float(np.min(np.linalg.norm(
            projected - (polygon + fractions[:, None] * edges), axis=1)))
        return {'projection_inside': inside, 'signed_plane_distance_mm': signed * 1000,
                'projected_boundary_distance_mm': boundary * 1000,
                'finite_patch_distance_mm': abs(signed) * 1000 if inside else
                float(np.hypot(signed, boundary) * 1000),
                'outward_normal_dot_post_pose': float(np.dot(normal, axis))}

    proposal = read(BASE / 'three_face_finger_target_hold_v1/proposal.json')
    regions = {k: np.array(v) for k, v in proposal['regions_G_m'].items()}
    outer = regions['front'].copy()
    outer[:, 2] = proposal['front_outer_source_z_G_m']
    polygons = dict(regions, front_outer=outer)
    outward = {'front': [0, 0, 1], 'front_outer': [0, 0, 1],
               'thumb': [0, 0, -1], 'palm': [1, 0, 0]}
    shapes = read(BASE / 'three_face_support_loss_v1/native/saved_finger_targets/shape_properties.json')
    guitar_names = [row['body'] for row in shapes['actors']['guitar']['body_ranges']]
    folders = {'stored_reference': BASE / 'three_face_support_loss_v1/native/saved_finger_targets',
               'half_slack': BASE / 'three_face_half_strap_slack_v1/native/half_slack',
               'zero_slack': BASE / 'three_face_half_strap_slack_v1/native/zero_slack'}
    reference = read(folders['stored_reference'] / 'initial_values.json')
    human_names = reference['human_body_names']
    human_xml = ET.parse(ROOT / 'stability_adapter_2/assets/humanoid_fixed_lower.xml')
    source_com = {b.get('name'): np.fromstring(b.find('inertial').get('pos'), sep=' ')
                  for b in human_xml.iter('body') if b.find('inertial') is not None}
    config = read(ROOT / 'stability_adapter_2/config.json')
    config['humanoid_asset'] = str(ROOT / 'stability_adapter_2/assets/humanoid_fixed_lower.xml')
    state0 = reference['native_initial_state']
    scene = SimpleNamespace(config=config, human=0, guitar=1, env=None,
        gym=SimpleNamespace(get_actor_rigid_body_names=lambda env, actor:
                            human_names if actor == 0 else guitar_names),
        bodies=lambda actor: state0['human_body_states'] if actor == 0 else state0['guitar_body_states'])
    model, data, source_shapes = build_probe(scene)
    gp0, gr0 = pose(state0['guitar_body_states'][0])
    source_geometry = []
    for shape in source_shapes:
        if shape['actor'] != 'guitar' or not (shape['body'] == 'guitar' or
                shape['body'].startswith('G:fret') or shape['body'] == 'G:nut'):
            continue
        mesh = face_geometry(model, data, shape)
        vertices = gr0.inv().apply(mesh.vertices - gp0)
        source_geometry.append({'body': shape['body'], 'geom_id': shape['geom_id'],
                                'vertices_G_m': vertices.tolist(), 'faces': mesh.faces.tolist()})
    samples, summary = [], {}
    for label, folder in folders.items():
        init = read(folder / 'initial_values.json')
        states = [json.loads(line) for line in (folder / 'states.jsonl').read_text().splitlines()]
        contacts = [json.loads(line) for line in (folder / 'contacts.jsonl').read_text().splitlines()]
        if len(states) != 1201 or len(contacts) != 1200 or init['human_body_names'] != human_names:
            raise AssertionError('full5s/native body mapping')
        if init['physics_parameters'].get('substeps', 1) != 1:
            raise AssertionError('recorded preset is not single-substep')
        if [s['physics_step'] for s in states] != list(range(1201)) or \
                [s['physics_step'] for s in contacts] != list(range(1, 1201)):
            raise AssertionError('raw sequence')
        cached = []
        relative_drift, relative_rot_drift = 0., 0.
        relatives0 = [(gr0.inv().apply(pose(b)[0] - gp0), gr0.inv() * pose(b)[1])
                      for b in state0['guitar_body_states']]
        for state in states:
            hs = [pose(b) for b in state['human_body_states']]
            gs = [pose(b) for b in state['guitar_body_states']]
            cached.append({'human': hs, 'guitar': gs})
            gp, gr = gs[0]
            for (p, r), (rp0, rr0) in zip(gs, relatives0):
                relative_drift = max(relative_drift, float(np.linalg.norm(gr.inv().apply(p - gp) - rp0)))
                relative_rot_drift = max(relative_rot_drift, float((gr.inv() * r * rr0.inv()).magnitude()))
        rows = []
        for record in contacts:
            step = record['physics_step']
            for row_index, contact in enumerate(record['contacts']):
                names = [contact['body0_name'], contact['body1_name']]
                if not any(n.startswith('guitar/') for n in names) or \
                        not any(n.startswith('human/LH:') for n in names):
                    continue
                gside = next(j for j, name in enumerate(names) if name.startswith('guitar/'))
                hside = 1 - gside
                worlds = []
                for at in (step - 1, step):
                    positions = []
                    for j, name in enumerate(names):
                        actor, body = name.split('/', 1)
                        index = (guitar_names if actor == 'guitar' else human_names).index(body)
                        expected_id = index + (len(human_names) if actor == 'guitar' else 0)
                        if contact['body' + str(j)] != expected_id:
                            raise AssertionError('native body id/name mismatch')
                        p, r = cached[at][actor][index]
                        positions.append(p + r.apply(vector(contact['localPos' + str(j)])))
                    worlds.append(positions)
                pair_post = worlds[1][1] - worlds[1][0]
                pair_pre = worlds[0][1] - worlds[0][0]
                gp, gr = cached[step]['guitar'][0]
                point = gr.inv().apply(worlds[1][gside] - gp)
                raw_normal = vector(contact['normal'])
                normal = gr.inv().apply(raw_normal if gside == 0 else -raw_normal)
                metrics = {k: patch_metrics(point, normal, poly, outward[k]) for k, poly in polygons.items()}
                near = [k for k in regions if metrics[k]['projection_inside'] and
                        abs(metrics[k]['signed_plane_distance_mm']) <= 2.]
                classification = 'unclassified'
                if len(near) > 1:
                    classification = 'ambiguous_multi_face'
                elif len(near) == 1:
                    m = metrics[near[0]]
                    if m['projected_boundary_distance_mm'] <= 1.:
                        classification = 'boundary'
                    elif m['outward_normal_dot_post_pose'] >= .5:
                        classification = near[0] + '_proxy_compatible'
                # A numeric reconstruction check, not anatomical or cooked-surface certification.
                residual = float(np.linalg.norm(pair_post))
                if residual > 1e-6:
                    classification = 'frame_unverified'
                gi = guitar_names.index(names[gside].split('/', 1)[1])
                gbody = names[gside].split('/', 1)[1]
                if not (gbody == 'guitar' or gbody.startswith('G:fret') or gbody == 'G:nut'):
                    classification = 'other_guitar_body'
                offset = vector(contact['offset' + str(gside)])
                surface = point + gr.inv().apply(cached[step]['guitar'][gi][1].apply(offset))
                hn = names[hside].split('/', 1)[1]
                hp, hr = cached[step]['human'][human_names.index(hn)]
                com_hypothesis = hr.apply(source_com.get(hn, np.zeros(3)))
                com_residual = float(np.linalg.norm(worlds[1][hside] + com_hypothesis - worlds[1][gside]))
                sample = {'label': label, 'physics_step': step, 'time_s': step / 240.,
                    'contact_row_index': row_index, 'human_body': hn, 'guitar_body': gbody,
                    'raw_lambda': contact['lambda'], 'feature_G_m': point.tolist(),
                    'feature_plus_offset_G_m': surface.tolist(), 'outward_normal_G_post_pose': normal.tolist(),
                    'pair_post_residual_mm': residual * 1000,
                    'pair_previous_residual_mm': float(np.linalg.norm(pair_pre) * 1000),
                    'human_source_COM_shift_hypothesis_residual_mm': com_residual * 1000,
                    'previous_signed_pair_gap_mm': float(np.dot(pair_pre, raw_normal) * 1000),
                    'raw_initial_overlap_mm': contact['initialOverlap'] * 1000,
                    'raw_min_dist_mm': contact['minDist'] * 1000,
                    'guitar_offset_norm_mm': float(np.linalg.norm(offset) * 1000),
                    'patch_metrics': metrics, 'classification': classification}
                rows.append(sample)
        grouped = {}
        for row in rows:
            key = row['human_body']
            grouped.setdefault(key, {'rows': 0, 'positive_rows': 0, 'positive_steps': set(),
                                    'positive_classification': {}, 'positive_guitar_body': {}})
            group = grouped[key]
            group['rows'] += 1
            if row['raw_lambda'] <= 0:
                continue
            group['positive_rows'] += 1
            group['positive_steps'].add(row['physics_step'])
            for field, output in [('classification', 'positive_classification'), ('guitar_body', 'positive_guitar_body')]:
                value = row[field]
                group[output][value] = group[output].get(value, 0) + 1
        for group in grouped.values():
            group['positive_steps'] = sorted(group['positive_steps'])
            group['last_positive_step'] = max(group['positive_steps'], default=None)
        summary[label] = {'mapped_rows': len(rows), 'body_counts': grouped,
            'pair_post_max_residual_mm': max(r['pair_post_residual_mm'] for r in rows),
            'pair_previous_max_residual_mm': max(r['pair_previous_residual_mm'] for r in rows),
            'human_source_COM_shift_median_residual_mm': float(np.median([r['human_source_COM_shift_hypothesis_residual_mm'] for r in rows])),
            'guitar_child_relative_max_position_drift_mm': relative_drift * 1000,
            'guitar_child_relative_max_rotation_drift_rad': relative_rot_drift,
            'max_guitar_offset_norm_mm': max(r['guitar_offset_norm_mm'] for r in rows)}
        samples.extend(rows)
    checks = {'sealed_inputs_unchanged': all(sha(p) == h for p, h in hashes.items()),
              'three_full5s_contact_state_sequences': True, 'body_id_name_checked_every_mapped_row': True,
              'source_geometry_and_finite_patch_metrics_computed': True, 'new_native_and_physics_calls_zero': True}
    if not all(checks.values()):
        raise AssertionError(checks)
    save(PHASE / 'analysis.json', {'checks': checks, 'input_sha256': hashes, 'summary': summary,
        'patches_G_m': {k: v.tolist() for k, v in polygons.items()}, 'source_geometry': source_geometry,
        'samples': samples, 'diagnostic_thresholds': {'plane_distance_mm': 2., 'boundary_mm': 1.,
            'normal_dot_min': .5, 'pair_reconstruction_residual_m': 1e-6},
        'counts': {'stored_runs': 3, 'contact_records': 3600, 'native_initializations': 0, 'physics_steps': 0},
        'scope': 'poststep body-origin reconstruction is a numerical observation; source COM shift is only an alternative hypothesis, native COM not queried; source finite-patch compatibility is not cooked/anatomical face certification; normals use postpose, initialOverlap belongs to start; raw lambda not converted to N; front skin9.3mm and outer11.230006mm reported separately; no continuous support or stability success'})
    print(json.dumps({'checks': checks, 'summary': summary}, indent=2), flush=True)


if __name__ == '__main__':
    main()
