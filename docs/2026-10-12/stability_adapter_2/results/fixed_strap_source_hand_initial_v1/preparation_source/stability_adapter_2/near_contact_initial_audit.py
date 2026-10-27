"""Read-only native initial no-overlap/FK diagnostics with robust source distance bounds."""
import xml.etree.ElementTree as ET

from .environment import ROOT, np
from .build_fixed_lower_asset import pose
from .initial_overlap import build_probe
from .palm_side_source_checks import source_checks, intersection
from .run_joint_hold import native_state
from .search_multi_face_grip import nearest_face, read, PROPOSAL
from .source_patch_interval import certified_distance
from scipy.spatial.transform import Rotation


def audit_initial(env, search, row):
    before = native_state(env)
    model, data, shapes = build_probe(env)
    meshes, overlaps, crosshands = source_checks((model, data, shapes))
    xml = ET.parse(ROOT / env.config['humanoid_asset']).getroot()
    parents = {c.get('name'): p.get('name') for p in xml.iter('body') for c in p.findall('body')}
    def distance(a, b):
        chain = []; current = a
        while current in parents: chain.append(current); current = parents[current]
        chain.append(current); steps = 0; current = b
        while current not in chain and current in parents: steps += 1; current = parents[current]
        return steps + chain.index(current) if current in chain else 99
    hand = [s for s in shapes if s['body'].startswith('LH:') or s['body'] in ('L_Wrist', 'L_Elbow')]
    self_cross = []
    for i, a in enumerate(hand):
        for b in hand[i + 1:]:
            if distance(a['body'], b['body']) <= 2: continue
            radius = intersection(meshes[a['geom_id']], meshes[b['geom_id']])
            if radius > 1e-7:
                self_cross.append({'a': a['body'], 'b': b['body'], 'common_radius_m': radius})
    gp, gq = pose(before['guitar_body_states'][0]); gr = Rotation.from_quat(gq)
    regions = search['regions_G_m']
    metrics = {}
    hull_gaps = {}
    for name, facet in search['facets'].items():
        p, q = pose(before['human_body_states'][env.human_bodies.index(name)])
        point = gr.inv().apply(p + Rotation.from_quat(q).apply(facet['point_local_m']) - gp)
        face = 'palm' if name == 'LH:palm' else 'thumb' if name == 'LH:thumb3' else 'front'
        clear = row['target_clearance_m'] if row else .0003
        target, normal = nearest_face(point, face, search['front_outer_source_z_G_m'], clear, regions)
        direction = gr.inv().apply(Rotation.from_quat(q).apply(facet['normal_local']))
        metrics[name] = {'face': face, 'point_G_m': point.tolist(), 'distance_to_offset_patch_m': float(np.linalg.norm(point - target)),
                         'inward_alignment_dot': float(direction @ -normal)}
        poly = np.array(regions[face])
        if face == 'front': poly[:, 2] = search['front_outer_source_z_G_m']
        mesh = meshes[next(s['geom_id'] for s in shapes if s['body'] == name)]
        hull_gaps[name] = dict(certified_distance(mesh, gr.apply(poly) + gp), face=face)
    proxy = np.array(read(ROOT / 'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/initial_audit_v2/audit.json')['palmar_normal_proxy_local'])
    palm = before['human_body_states'][env.human_bodies.index('LH:palm')]
    up = float(Rotation.from_quat(pose(palm)[1]).apply(proxy)[2])
    position_error = 0.; rotation_error = 0.
    if row:
        for name in env.human_bodies:
            p, q = pose(before['human_body_states'][env.human_bodies.index(name)])
            pp, qq = pose(row['source_state']['human_body_states'][env.human_bodies.index(name)])
            position_error = max(position_error, float(np.linalg.norm(p - pp)))
            rotation_error = max(rotation_error, float((Rotation.from_quat(q) * Rotation.from_quat(qq).inv()).magnitude()))
    checks = {'zero_steps_and_queries_preserve_states': env.steps == 0 and native_state(env) == before,
              'source_human_guitar_clear': not overlaps, 'source_cross_hands_clear': not crosshands,
              'source_nonadjacent_left_hand_clear': not self_cross, 'palm_up_proxy': up > 0,
              'FK_pose_matches_proposal': position_error <= .0001 and rotation_error <= .001}
    return {'checks': checks, 'metrics': metrics, 'source_hull_to_faces': hull_gaps,
            'source_face_distance_upper_bounds_under3mm': max(v['distance_m'] for v in hull_gaps.values()) <= .003,
            'palm_up_proxy_z': up, 'source_intersections': overlaps,
            'cross_hand_intersections': crosshands, 'nonadjacent_left_hand_intersections': self_cross,
            'max_FK_position_error_m': position_error, 'max_FK_rotation_error_rad': rotation_error,
            'scope': 'fresh native poses, no-overlap source/FK admission and feasible source distance intervals; original support search gates remain unmet; not cooked clearance, contact or anatomical pad certification; graph-distance<=2 self pairs excluded'}
