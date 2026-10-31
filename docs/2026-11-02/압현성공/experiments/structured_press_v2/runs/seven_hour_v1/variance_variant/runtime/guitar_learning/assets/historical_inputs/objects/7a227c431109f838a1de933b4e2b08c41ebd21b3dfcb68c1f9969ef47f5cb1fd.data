"""Audit full source hull proximity to three faces at saved FK proposals."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    out = PHASE / 'face_audit.json'
    if out.exists(): raise FileExistsError('preserve earlier audit')
    p = PHASE / 'search.json'; hashes = {str(p): sha(p)}; search = json.loads(p.read_text())
    paths = [Path(p) for p in search['input_sha256']] + [Path(__file__).resolve(),
        Path(__file__).with_name('audit_palm_side_target.py'), PHASE / 'closest_faces_probe.log', PHASE / 'closest_faces_probe_execution.json']
    paths += [Path(r['trial_path']) for r in search['rows']]
    hashes.update({str(p): sha(p) for p in paths})
    if not all(search['checks'].values()) or any(sha(p) != h for p, h in search['input_sha256'].items()):
        raise AssertionError('source proposal closure')
    from .search_multi_face_grip import INITIAL, read, prepare_geometry
    from .environment import np
    import mujoco
    from .render_best_run_video import set_saved_pose
    from .palm_side_source_checks import source_checks
    from .audit_palm_side_target import closest_polygon
    report, probe, _, _, _, gp, gr, _, z = prepare_geometry(read(INITIAL))
    model, data, shapes = probe
    rows = []
    for row in search['rows']:
        set_saved_pose(model, mujoco, report, row['source_state']); mujoco.mj_forward(model, data)
        meshes, overlaps, crosshands = source_checks(probe)
        gaps = {}
        for name in ('LH:palm', 'LH:thumb3', 'LH:index3', 'LH:middle3', 'LH:ring3', 'LH:pinky3'):
            face = 'palm' if name == 'LH:palm' else 'thumb' if name == 'LH:thumb3' else 'front'
            poly = np.array(search['regions_G_m'][face])
            if face == 'front': poly[:, 2] = z
            mesh = meshes[next(s['geom_id'] for s in shapes if s['body'] == name)]
            gaps[name] = dict(closest_polygon(mesh, gr.apply(poly) + gp), face=face)
        clear = not overlaps and not crosshands and not row['nonadjacent_left_hand_intersections'] and row['palm_up_proxy_z'] > 0
        rows.append({'label': row['label'], 'source_hull_to_faces': gaps,
                     'source_clear': clear, 'all_hull_faces_within3mm': clear and max(v['distance_m'] for v in gaps.values()) <= .003})
    checks = {'source_proposals_rechecked': True, 'trial_hashes_match': all(sha(r['trial_path']) == r['trial_sha256'] for r in search['rows']),
              'inputs_unchanged': all(sha(p) == h for p, h in hashes.items())}
    if not all(checks.values()): raise AssertionError(checks)
    out.write_text(json.dumps({'checks': checks, 'input_sha256': hashes, 'rows': rows,
        'native_initializations': 0, 'physics_steps': 0,
        'scope': 'full collision-hull distance vs finite target faces; not anatomical pad/contact/cooked clearance certification; previous one-off import-order probe exited -11 without native initialization'}, indent=2) + '\n')
    print(json.dumps({'checks': checks, 'rows': [{**r, 'source_hull_to_faces': {n: v['distance_m'] * 1000 for n, v in r['source_hull_to_faces'].items()}} for r in rows]}, indent=2))


if __name__ == '__main__': main()
