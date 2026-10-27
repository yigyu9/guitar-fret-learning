"""Read-only local neck/palm visualization at native initial simulation poses."""
import argparse
import hashlib
import json
from pathlib import Path

from .environment import InitialEnvironment, ROOT, gymapi, np, vector, quaternion
from .initial_overlap import build_probe, mujoco
from .strap import rotate


def geometry(model, data, shape):
    import trimesh
    i = shape['geom_id']
    kind = model.geom_type[i]
    if kind == mujoco.mjtGeom.mjGEOM_MESH:
        mesh_id = model.geom_dataid[i]
        start, count = model.mesh_vertadr[mesh_id], model.mesh_vertnum[mesh_id]
        mesh = trimesh.convex.convex_hull(model.mesh_vert[start:start+count])
    elif kind == mujoco.mjtGeom.mjGEOM_BOX:
        mesh = trimesh.creation.box(extents=2*model.geom_size[i])
    elif kind == mujoco.mjtGeom.mjGEOM_CAPSULE:
        mesh = trimesh.creation.capsule(radius=model.geom_size[i, 0], height=2*model.geom_size[i, 1], count=[8, 8])
        mesh.apply_translation(-mesh.bounds.mean(0))
    else:
        raise ValueError('unsupported source shape '+str(kind))
    transform = np.eye(4)
    transform[:3, :3], transform[:3, 3] = data.geom_xmat[i].reshape(3, 3), data.geom_xpos[i]
    mesh.apply_transform(transform)
    return mesh


def section(meshes, y):
    """Intersect local convex-hull edges with a plane perpendicular to neck Y."""
    points = []
    for mesh in meshes:
        a, b = mesh.vertices[mesh.edges_unique].transpose(1, 0, 2)
        delta = b[:, 1]-a[:, 1]
        mask = np.abs(delta)>1e-10
        t = (y-a[mask, 1])/delta[mask]
        hit = (t>=-1e-8) & (t<=1+1e-8)
        points.extend(a[mask][hit]+t[hit, None]*(b[mask][hit]-a[mask][hit]))
        points.extend(mesh.vertices[np.abs(mesh.vertices[:, 1]-y)<1e-8])
    if not points:
        raise ValueError('neck cross-section not found')
    return np.array(points)


def draw(meshes, curves, result, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    plt.rcParams.update({'font.family':'NanumGothic', 'axes.unicode_minus':False, 'font.size':11})
    fig = plt.figure(figsize=(14, 6.5))
    ax = fig.add_subplot(121, projection='3d', computed_zorder=False)
    for shape, mesh in meshes:
        color = '#16a34a' if shape['body']=='LH:palm' else '#2563eb' if shape['actor']=='guitar' else '#94a3b8'
        ax.add_collection3d(Poly3DCollection(mesh.triangles, facecolors=color,
            alpha=.45 if shape['actor']=='guitar' or shape['body'].startswith('LH:') else .15,
            edgecolors='none', zorder=1))
    palm = np.array(result['palm_center_world_m'])
    q = np.array(result['axis_projection_world_m'])
    axis = np.array(result['neck_axis_world_m'])
    ax.plot(*axis.T, color='#9333ea', lw=3, label='넥 중심선', zorder=10)
    ax.scatter(*palm, color='#16a34a', s=65, depthshade=False, label='P: 손바닥 형상 중심', zorder=11)
    ax.scatter(*q, color='#9333ea', s=65, depthshade=False, label='Q: 대응 중심선 지점', zorder=11)
    ax.plot(*np.array([palm, q]).T, color='#16a34a', ls='--', lw=2, zorder=10)
    ax.text(*palm, ' P', color='#15803d', zorder=12); ax.text(*q, ' Q', color='#7e22ce', zorder=12)
    points = np.concatenate([mesh.vertices for shape, mesh in meshes if shape['actor']=='guitar']+[palm[None]])
    center = (points.min(0)+points.max(0))/2
    half = np.ptp(points, axis=0).max()/2+.04
    ax.set(xlim=(center[0]-half, center[0]+half), ylim=(center[1]-half, center[1]+half),
           zlim=(center[2]-half, center[2]+half), xlabel='World X (m)', ylabel='World Y (m)', zlabel='World Z (m)')
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=20, azim=110)
    ax.set_title('① 초기 시뮬레이션 위치 + 투영 표시')
    ax.legend(loc='upper left', fontsize=9)
    ax = fig.add_subplot(122)
    s, lower, upper, center_z = curves
    ax.fill_between(s, lower, upper, color='#93c5fd', alpha=.6, label='넥 단면의 world Z 범위')
    ax.plot(s, center_z, color='#9333ea', lw=2, label='넥 중심선 높이')
    ax.axhline(palm[2], color='#16a34a', ls='--', lw=1.3, label='손바닥 중심 높이')
    station = result['projection_s_m']
    ax.axvline(station, color='#f59e0b', lw=2, label='비교할 단면 s*')
    ax.scatter([station, station], [palm[2], q[2]], c=['#16a34a', '#9333ea'], s=65, zorder=5)
    ax.annotate('', xy=(station, q[2]), xytext=(station, palm[2]),
                arrowprops={'arrowstyle':'<->', 'color':'#ea580c', 'lw':2})
    ax.annotate(f"이 단면과만 비교\n중심선 대비 Δh={result['height_vs_axis_m']*1000:+.1f} mm",
                xy=(station, (palm[2]+q[2])/2), xytext=(15, 30), textcoords='offset points',
                color='#9a3412', arrowprops={'arrowstyle':'-', 'color':'#ea580c'})
    distant = upper < palm[2]
    if distant.any():
        ax.fill_between(s, lower, upper, where=distant, color='#64748b', alpha=.55)
        i = np.flatnonzero(distant)[len(np.flatnonzero(distant))//2]
        ax.annotate('손바닥보다 낮은 다른 넥 구간\n이 높이 조건의 비교 대상이 아님',
                    xy=(s[i], center_z[i]), xytext=(s[0]+.01, min(lower)-.035),
                    fontsize=10, arrowprops={'arrowstyle':'->', 'color':'#475569'}, color='#475569')
    ax.set(xlabel='넥 길이 좌표 s (m): 몸체 쪽 → 너트 쪽', ylabel='World Z (m)',
           title='② 같은 길이 위치의 높이 비교', ylim=(min(lower)-.065, max(upper)+.04))
    ax.grid(alpha=.2); ax.legend(loc='upper left', fontsize=9)
    fig.suptitle('기울어진 넥과 왼손: 전체 최저점 대신 손에 대응되는 단면을 비교', fontsize=15)
    fig.text(.5, .025, 'H0 / 추가 물리 step 0 · native pose 기반 CPU 원본 충돌 형상 시각화 · Isaac Gym 렌더/접촉 판정 아님',
             ha='center', fontsize=10)
    fig.tight_layout(rect=(0, .055, 1, .94)); fig.savefig(path, dpi=170); plt.close(fig)


def draw_example(curves, example, path):
    """Same measured neck, explicitly hypothetical palm point; no humanoid pose."""
    import matplotlib.pyplot as plt
    s, lower, upper, center_z = curves
    station, height = example['projection_s_m'], example['world_point_m'][2]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.fill_between(s, lower, upper, color='#93c5fd', alpha=.65, label='현재 기타의 넥 단면 높이 범위')
    ax.plot(s, center_z, color='#9333ea', label='현재 기타의 넥 중심선')
    ax.axhline(height, color='#ea580c', ls='--', label='설명용 가상 손바닥 높이')
    ax.axvline(station, color='#f59e0b', lw=2, label='이 지점의 단면만 비교')
    ax.scatter([station], [height], color='#ea580c', s=80, zorder=5)
    ax.annotate('가상 손바닥 P′\n이 단면 하단보다 10mm 아래', xy=(station,height),
                xytext=(station+.015,height-.035), color='#9a3412',
                arrowprops={'arrowstyle':'->','color':'#ea580c'})
    distant = upper < height
    ax.fill_between(s, lower, upper, where=distant, color='#64748b', alpha=.7)
    i = np.flatnonzero(distant)[len(np.flatnonzero(distant))//2]
    ax.annotate('이 넥 구간은 가상 손바닥보다 낮음\n멀리 있는 구간이므로 이 높이 조건에 영향 없음',
                xy=(s[i],center_z[i]), xytext=(s[0]+.01,min(lower)-.055), color='#475569',
                arrowprops={'arrowstyle':'->','color':'#475569'})
    ax.set(xlabel='넥 길이 좌표 s (m): 몸체 쪽 → 너트 쪽', ylabel='World Z (m)',
           ylim=(min(lower)-.085,max(upper)+.04), title='다른 넥 구간이 손바닥보다 낮아도 되는 이유')
    ax.grid(alpha=.2); ax.legend(loc='upper left', fontsize=9)
    fig.text(.5,.025,'기타 형상/기울기는 실제 H0 · P′는 설명용 가상점 · 관절 자세/지지 성공/허용 간격을 제안하는 실험이 아님',
             ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.055,1,1)); fig.savefig(path,dpi=170); plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if any((args.out/n).exists() for n in ('report.json','neck_palm.png','local_comparison_example.png')):
        raise FileExistsError('use a new run directory')
    scene = InitialEnvironment()
    try:
        before = {a:scene.bodies(a) for a in (scene.human, scene.guitar)}
        dofs = scene.gym.get_actor_dof_states(scene.env, scene.human, gymapi.STATE_ALL).copy()
        model, data, shapes = build_probe(scene)
        meshes = [(s, geometry(model, data, s)) for s in shapes]
        palm = next(m.center_mass for s,m in meshes if s['body']=='LH:palm')
        guitar = before[scene.guitar][scene.guitar_bodies.index('guitar')]['pose']
        origin, quat = vector(guitar['p']), quaternion(guitar['r'])
        quat /= np.linalg.norm(quat)
        rotation = np.column_stack([rotate(quat, v) for v in np.eye(3)])
        neck = [m.copy() for s,m in meshes if s['actor']=='guitar' and s['body']=='guitar']
        for mesh in neck:
            mesh.vertices = (mesh.vertices-origin) @ rotation
        vertices = np.concatenate([m.vertices for m in neck])
        lo, hi = vertices.min(0), vertices.max(0)
        mid = (lo+hi)/2
        axis_local = np.array([[mid[0],lo[1],mid[2]], [mid[0],hi[1],mid[2]]])
        axis = axis_local @ rotation.T+origin
        direction = rotation[:,1]
        station = float(np.dot(palm-axis[0], direction))
        length = float(hi[1]-lo[1])
        q = axis[0]+station*direction
        in_range = 0<=station<=length
        world_section = section(neck, lo[1]+station) @ rotation.T+origin if in_range else None
        ys = np.linspace(lo[1], hi[1], 161)
        slices = [section(neck, y) @ rotation.T+origin for y in ys]
        lower, upper = np.array([(p[:,2].min(),p[:,2].max()) for p in slices]).T
        center_z = (np.column_stack([np.full(len(ys),mid[0]),ys,np.full(len(ys),mid[2])]) @ rotation.T+origin)[:,2]
        unchanged = all(np.array_equal(before[a], scene.bodies(a)) for a in before)
        unchanged &= np.array_equal(dofs, scene.gym.get_actor_dof_states(scene.env, scene.human, gymapi.STATE_ALL))
        assert scene.steps==0 and unchanged
        assert abs(np.dot(palm-q, direction))<1e-10
        result = {'scope':'H0 local neck/palm visualization; no pose change or gate',
            'palm_reference':'LH:palm source collision convex-hull volume centroid; not anatomical surface/contact point',
            'palm_center_world_m':palm.tolist(), 'neck_axis_world_m':axis.tolist(),
            'axis_projection_world_m':q.tolist(), 'projection_s_m':station, 'neck_length_m':length,
            'projection_in_neck_range':in_range, 'height_vs_axis_m':float(palm[2]-q[2]),
            'palm_axis_distance_m':float(np.linalg.norm(palm-q)),
            'local_section_world_z_range_m':None if world_section is None else [float(world_section[:,2].min()),float(world_section[:,2].max())],
            'native_state_unchanged':bool(unchanged), 'additional_native_physics_steps':scene.steps,
            'other_sections_entirely_below_palm_count':int((upper<palm[2]).sum()),
            'sampled_sections':161, 'initial_strap_rest_length_m':scene.rest_length,
            'initial_joint_angles_rad':dict(zip(scene.names,dofs['pos'].astype(float).tolist())),
            'limitations':['CPU source convex-hull geometry, not PhysX cooked mesh or Isaac renderer',
                'Vertical height comparisons are not shortest surface gap or contact/penetration certification',
                'Hand transverse distance, palm orientation, whole-hand clearance and playing workspace require separate checks']}
        example_s = .7*length
        example_q = axis[0]+example_s*direction
        example_section = section(neck,lo[1]+example_s) @ rotation.T+origin
        projected_up = np.array([0.,0.,1.])-direction*direction[2]
        example_height = example_section[:,2].min()-.01
        example_p = example_q+projected_up*(example_height-example_q[2])/projected_up[2]
        assert abs(np.dot(example_p-example_q,direction))<1e-10
        assert (upper<example_height).any()
        result['illustrative_reference'] = {'scope':'hypothetical point only; no humanoid pose or physical support validation',
            'projection_s_m':example_s, 'world_point_m':example_p.tolist(),
            'local_lower_world_z_m':float(example_section[:,2].min()),
            'example_only_height_offset_m':-.01, 'not_a_runtime_tolerance':True}
        paths = [Path(__file__),Path(__file__).with_name('initial_overlap.py'),Path(__file__).with_name('environment.py'),
                 Path(__file__).with_name('config.json')]+[ROOT/scene.config[k] for k in ('humanoid_asset','guitar_asset','pose_source')]
        paths += sorted((ROOT/'tab2body/assets/mesh').glob('*'))
        result['source_sha256'] = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
        draw(meshes, (ys-lo[1],lower,upper,center_z), result, args.out/'neck_palm.png')
        draw_example((ys-lo[1],lower,upper,center_z),result['illustrative_reference'],args.out/'local_comparison_example.png')
        (args.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ('source_sha256','initial_joint_angles_rad')},indent=2))
    finally:
        scene.close()


if __name__=='__main__':
    main()
