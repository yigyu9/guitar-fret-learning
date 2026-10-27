"""CPU initial overlap report; run with MUJOCO_GL=disable and the Gym setup."""
import argparse
import hashlib
import json
from pathlib import Path

from .environment import InitialEnvironment, ROOT, gymapi, np
from .initial_overlap import build_probe, query_pairs, mujoco


def draw_probe(model, data, shapes, result, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from scipy.spatial import ConvexHull
    import trimesh

    overlapping = {p[k] for p in result['pairs_within_limit'] if p['signed_gap_m'] < -1e-7
                   for k in ('human_geom_id', 'guitar_geom_id')}
    surfaces = []
    for shape in shapes:
        i = shape['geom_id']
        kind = model.geom_type[i]
        if kind == mujoco.mjtGeom.mjGEOM_MESH:
            mesh_id = model.geom_dataid[i]
            start, count = model.mesh_vertadr[mesh_id], model.mesh_vertnum[mesh_id]
            vertices = model.mesh_vert[start:start+count]
            faces = ConvexHull(vertices).simplices
        elif kind == mujoco.mjtGeom.mjGEOM_BOX:
            mesh = trimesh.creation.box(extents=2*model.geom_size[i])
            vertices, faces = mesh.vertices, mesh.faces
        elif kind == mujoco.mjtGeom.mjGEOM_CAPSULE:
            mesh = trimesh.creation.capsule(radius=model.geom_size[i, 0], height=2*model.geom_size[i, 1], count=[8, 8])
            vertices, faces = mesh.vertices-mesh.bounds.mean(0), mesh.faces
        else:
            raise ValueError('unsupported diagnostic drawing shape: '+str(kind))
        vertices = vertices @ data.geom_xmat[i].reshape(3, 3).T + data.geom_xpos[i]
        color = '#ef4444' if i in overlapping else '#2563eb' if shape['actor']=='guitar' else '#94a3b8'
        surfaces.append((vertices[faces], color, shape['actor']))
    fig = plt.figure(figsize=(12, 6))
    for plot, zoom in [(1, False), (2, True)]:
        ax = fig.add_subplot(1, 2, plot, projection='3d')
        for triangles, color, actor in surfaces:
            ax.add_collection3d(Poly3DCollection(triangles, facecolors=color, alpha=.7, edgecolors='none'))
        if zoom:
            points = np.concatenate([triangles.reshape(-1, 3) for triangles, _, actor in surfaces if actor=='guitar'])
        else:
            points = np.concatenate([triangles.reshape(-1, 3) for triangles, _, _ in surfaces])
        center = (points.min(0)+points.max(0))/2
        half = max(points.ptp(0))/2 + .06
        ax.set(xlim=(center[0]-half, center[0]+half), ylim=(center[1]-half, center[1]+half),
               zlim=(center[2]-half, center[2]+half), xlabel='World X (m)', ylabel='World Y (m)', zlabel='World Z (m)')
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=18, azim=110 if zoom else 35)
        ax.set_title('Guitar area' if zoom else 'Whole humanoid + guitar')
    fig.suptitle('Initial source-shape diagnostic (not an Isaac Gym render)')
    fig.text(.5, .03, 'Red: negative-gap pair shapes | Blue: other guitar shapes | Gray: other human shapes', ha='center')
    fig.tight_layout(rect=(0, .06, 1, .94))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if any((args.out/name).exists() for name in ('report.json', 'geometry.png')):
        raise FileExistsError('use a new run directory')
    scene = InitialEnvironment()
    try:
        before = {a:scene.bodies(a) for a in (scene.human, scene.guitar)}
        dof = scene.gym.get_actor_dof_states(scene.env, scene.human, gymapi.STATE_ALL).copy()
        model, data, shapes = build_probe(scene)
        result = query_pairs(model, data, shapes)
        coverage = {}
        for label, actor, other_filter in [('human', scene.human, 2), ('guitar', scene.guitar, 1)]:
            names = scene.gym.get_actor_rigid_body_names(scene.env, actor)
            ranges = scene.gym.get_actor_rigid_body_shape_indices(scene.env, actor)
            native = scene.gym.get_actor_rigid_shape_properties(scene.env, actor)
            for name, body_range in zip(names, ranges):
                active = sum(not (native[i].filter & other_filter)
                    for i in range(body_range.start, body_range.start+body_range.count))
                source = sum(s['actor']==label and s['body']==name for s in shapes)
                if active != source:
                    raise AssertionError('source/native active shape count mismatch: '+label+'/'+name)
            coverage[label] = {'native_total':len(native), 'active_source':result['shape_count'][label],
                               'per_body_active_count_matches':True}
        unchanged = all(np.array_equal(before[a], scene.bodies(a)) for a in before)
        unchanged &= np.array_equal(dof, scene.gym.get_actor_dof_states(scene.env, scene.human, gymapi.STATE_ALL))
        if scene.steps != 0 or not unchanged:
            raise AssertionError('diagnostic changed native initial state')
        result.update({'scope':'CPU H0 source-shape initial diagnostic; no rollout or start gate',
            'native_physics_steps':scene.steps, 'native_state_unchanged':bool(unchanged),
            'shape_coverage':coverage,
            'geometry_backend':'MuJoCo '+mujoco.__version__+' static signed-distance query at native Gym poses',
            'shapes':shapes, 'initial_joint_angles_rad':dict(zip(scene.names, dof['pos'].astype(float).tolist())),
            'initial_strap_rest_length_m':scene.rest_length,
            'limitations':['MuJoCo source shapes have not been validated against PhysX cooked collision geometry',
                'Negative gap magnitude is not calibrated penetration depth; 0.1m analytic box overlap yields -0.05m in this backend',
                'Gaps are not measured contact forces or a final allowed depth',
                'Chair/ground, human self-collision and strap cloth are outside this human-guitar query',
                'Disabled thumb pad/proxy, pluck-range and visual strings are excluded; no automatic reset/controller']})
        paths = [Path(__file__), Path(__file__).with_name('initial_overlap.py'), Path(__file__).with_name('environment.py'),
                 Path(__file__).with_name('config.json')] + [ROOT/scene.config[k] for k in ('humanoid_asset','guitar_asset','pose_source')]
        paths += sorted((ROOT/'tab2body/assets/mesh').glob('*'))
        result['source_sha256'] = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
        draw_probe(model, data, shapes, result, args.out/'geometry.png')
        (args.out/'report.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('shape_count','pair_count','negative_gap_pair_count','native_physics_steps','native_state_unchanged')}, indent=2))
        print(json.dumps(result['pairs_within_limit'][:5], indent=2))
    finally:
        scene.close()


if __name__ == '__main__':
    main()
