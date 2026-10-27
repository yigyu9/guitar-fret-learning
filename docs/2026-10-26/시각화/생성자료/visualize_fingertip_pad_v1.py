"""CPU-only exact source-mesh illustrations of the production distal patch."""
from pathlib import Path
import hashlib
import json
import os
import struct
import sys
import xml.etree.ElementTree as ET

os.environ.setdefault('MPLCONFIGDIR', '/tmp/fingertip_pad_v1_matplotlib')
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import numpy as np
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from guitar_learning.gpu.fingertip_pad import load_fingertip_pad, _clip_polygon

HERE, OUT = Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent
FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
fontManager.addfont(str(FONT))
FP = FontProperties(fname=str(FONT))
plt.rcParams.update({'font.family': FP.get_name(), 'axes.unicode_minus': False,
                     'font.size': 11, 'figure.facecolor': '#f6f8fb',
                     'savefig.facecolor': '#f6f8fb'})
FINGERS = ['index', 'middle', 'ring', 'pinky']
KOREAN = ['검지', '중지', '약지', '소지']
GREEN, RED, GREY, INK = '#12a778', '#e99292', '#aab5c3', '#203347'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def patch_pieces(triangles):
    """Exact same per-face normal and final-point half-spaces as production."""
    cross = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    size = np.linalg.norm(cross, axis=-1)
    normals = cross/np.maximum(size[:, None], 1e-30)
    ymin, ymax = triangles[..., 1].min(), triangles[..., 1].max()
    result = []
    for triangle, normal, area in zip(triangles, normals, size):
        if area <= 1e-20:
            continue
        if normal[2] <= -.25:
            minimum_u = .25
        elif normal[1] <= -.4 and normal[2] <= 0:
            minimum_u = .75
        else:
            continue
        polygon = _clip_polygon(list(triangle), 2, 0.)
        polygon = _clip_polygon(polygon, 1, ymax-minimum_u*(ymax-ymin))
        for vertex in range(1, len(polygon)-1):
            result.append(np.asarray((polygon[0], polygon[vertex], polygon[vertex+1])))
    return np.asarray(result)


def source_meshes(contract):
    source = Path(contract['frame_source']['source_xml'])
    xml = ET.parse(source).getroot()
    folder = source.parent/xml.find('compiler').get('meshdir', '.')
    assets = {mesh.get('name'): mesh for mesh in xml.findall('./asset/mesh')}
    bodies = {body.get('name'): body for body in xml.findall('.//body')}
    meshes, offsets, pins = {}, {}, {str(source): sha(source)}
    for finger in FINGERS:
        for segment in (1, 2, 3):
            name = 'LH:'+finger+str(segment)
            body = bodies[name]
            geom = body.find('geom'); asset = assets[geom.get('mesh')]
            path = (folder/asset.get('file')).resolve(); payload = path.read_bytes()
            count = struct.unpack_from('<I', payload, 80)[0]
            assert len(payload) == 84+50*count
            layout = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
            triangles = np.frombuffer(payload, dtype=layout, count=count, offset=84)['vertices'].astype(float)
            vertices = triangles.reshape(-1, 3)*np.fromstring(asset.get('scale', '1 1 1'), sep=' ')
            quat = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
            vertices = Rotation.from_quat(np.r_[quat[1:], quat[:1]]).apply(vertices)
            vertices += np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
            meshes[name] = vertices.reshape(-1, 3, 3)
            offsets[name] = np.fromstring(body.get('pos', '0 0 0'), sep=' ')
            pins[str(path)] = sha(path)
    return meshes, offsets, pins


def draw_surface(ax, triangles, project, color, alpha=1., zorder=1):
    ax.add_collection(PolyCollection(project(triangles), facecolors=color,
        edgecolors='none', alpha=alpha, zorder=zorder))


def setup_axis(ax):
    ax.set_facecolor('white')
    ax.set_aspect('equal', adjustable='box')
    ax.grid(alpha=.13)
    for spine in ax.spines.values():
        spine.set_color('#cbd5df')
    ax.tick_params(labelsize=9, colors='#53667a')


def source_patch_image(pad, meshes, offsets, pieces):
    fig, axes = plt.subplots(4, 2, figsize=(14.8, 13.8), gridspec_kw={'width_ratios': [1.35, 1.]})
    fig.subplots_adjust(left=.06, right=.975, top=.86, bottom=.08, hspace=.7, wspace=.22)
    fig.suptitle('압현에 사용할 끝마디 표면 · 실제 메시와 128개 샘플', fontsize=21, color=INK, x=.04, ha='left', y=.985)
    fig.text(.04, .94, '왼쪽: source 중립 체인의 옆면  |  오른쪽: 끝마디만 굴곡 안쪽에서 확대', fontsize=12, color=INK)
    handles = [Patch(facecolor=GREEN, label='정상 접근·접촉에 사용하는 면'),
               Line2D([], [], marker='o', color='none', markerfacecolor='#075f47', markersize=5, label='실제 메시 위 128점'),
               Patch(facecolor=RED, label='끝마디의 제외 부위'), Patch(facecolor=GREY, label='첫·중간마디: 선택 제외')]
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(.035, .925), ncol=2, frameon=False, fontsize=11)
    for finger_index, finger in enumerate(FINGERS):
        row = pad['contract']['fingers_diagnostics'][finger_index]
        points = pad['points_local'][finger_index]
        name = 'LH:'+finger+'3'
        # Native source zero-rotation chain; parent attachments retained exactly.
        origin = np.zeros(3)
        positions = {}
        for segment in (1, 2, 3):
            body = 'LH:'+finger+str(segment)
            if segment > 1:
                origin = origin+offsets[body]
            positions[body] = origin.copy()
        ax = axes[finger_index, 0]
        project = lambda p: np.stack((-np.asarray(p)[..., 1], np.asarray(p)[..., 2]), -1)*1000
        for segment in (1, 2):
            body = 'LH:'+finger+str(segment)
            draw_surface(ax, meshes[body]+positions[body], project, GREY, alpha=.8)
            center = (meshes[body].reshape(-1, 3).mean(0)+positions[body])*1000
            ax.text(-center[1], 10.5, '첫마디' if segment == 1 else '중간마디', ha='center', fontsize=10, color='#68798c')
        draw_surface(ax, meshes[name]+positions[name], project, RED, alpha=.8)
        draw_surface(ax, pieces[finger]+positions[name], project, GREEN, alpha=.95, zorder=2)
        sample = project(points+positions[name])
        ax.scatter(*sample.T, s=7, color='#075f47', alpha=.75, zorder=3)
        center = (meshes[name].reshape(-1, 3).mean(0)+positions[name])*1000
        ax.text(-center[1], 10.5, '끝마디', ha='center', fontsize=10, color=INK)
        ax.set_title(f'{KOREAN[finger_index]} · 중립 체인 옆면', loc='left', fontsize=13, color=INK)
        ax.autoscale_view(); ax.margins(x=.04, y=.35)
        ax.set_ylim(-12, 14)
        ax.set_xlabel('손가락 길이 방향 (mm)', fontsize=9)
        ax.set_ylabel('로컬 z (mm)', fontsize=9)
        setup_axis(ax)
        # Looking from model -z: flexion side. Green is exact clipped surface;
        # the excluded mesh is ghosted so exclusion boundaries remain visible.
        ax = axes[finger_index, 1]
        project = lambda p: np.stack((np.asarray(p)[..., 0], -np.asarray(p)[..., 1]), -1)*1000
        draw_surface(ax, meshes[name], project, RED, alpha=.75)
        draw_surface(ax, pieces[finger], project, GREEN, alpha=.9, zorder=2)
        sample = project(points)
        ax.scatter(*sample.T, s=9, color='#075f47', edgecolors='white', linewidths=.22, zorder=3)
        ax.set_title(f'{KOREAN[finger_index]} · 끝마디 굴곡 안쪽 확대', loc='left', fontsize=13, color=INK)
        ax.autoscale_view(); ax.margins(.12)
        ax.set_xlabel('로컬 x (mm)', fontsize=9); ax.set_ylabel('원위 방향 −y (mm)', fontsize=9)
        ax.text(1.03, .48, f'128점\n면적 {row["patch_area_m2"]*1e6:.1f} mm²\n\n−z 쪽 표면과\n이어진 원위 끝부분', transform=ax.transAxes,
                va='center', fontsize=10, color=INK)
        setup_axis(ax)
    fig.text(.04, .035, '표면 구분은 모델 굴곡 방향을 이용한 공학적 정의입니다. 원본에 피부·손톱의 해부학적 라벨은 없습니다.', fontsize=11, color=INK)
    fig.text(.04, .012, '점은 가림 없이 표시했습니다. 실제 준비 자세·접촉·압력·학습 결과를 재현한 그림이 아닙니다.', fontsize=11, color='#53667a')
    fig.savefig(OUT/'fingertip_pad_surfaces_v1.png', dpi=150)
    plt.close(fig)


def chain_pose(finger, angles, spread, offsets):
    position = offsets['LH:'+finger+'1'].copy()
    parent = Rotation.identity()
    rows = []
    for segment, angle in zip((1, 2, 3), angles):
        name = 'LH:'+finger+str(segment)
        if segment > 1:
            position = position+parent.apply(offsets[name])
        joint = Rotation.from_euler('x', angle, degrees=True)
        if segment == 1:
            joint = Rotation.from_euler('z', spread, degrees=True)*joint
        parent = parent*joint
        rows.append((position.copy(), parent))
    return rows


def kinematic_image(pad, meshes, offsets, pieces):
    poses = [('편 상태', [0., 0., 0.], [0., 0., 0., 0.], False),
             ('가볍게 굽힘', [25., 35., 15.], [0., 0., 0., 0.], False),
             ('많이 굽힘', [55., 65., 30.], [0., 0., 0., 0.], False),
             ('가볍게 굽혀 벌림', [25., 35., 15.], [-12., -4., 5., 15.], False),
             ('손 전체를 뒤집음', [25., 35., 15.], [0., 0., 0., 0.], True)]
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.subplots_adjust(left=.035, right=.97, top=.85, bottom=.145, hspace=.34, wspace=.18)
    fig.suptitle('손가락을 굽히거나 손 전체를 돌려도 같은 표면이 유지됩니다', fontsize=22, color=INK, x=.035, ha='left', y=.98)
    fig.text(.035, .925, 'source 몸체 연결·실제 메시를 사용한 기구학 예제  |  모든 패널은 검지·중지·약지·소지를 포함합니다', fontsize=12, color=INK)
    fig.legend(handles=[Patch(facecolor=GREEN, label='허용 표면'), Patch(facecolor=RED, label='제외 끝마디 표면'),
        Patch(facecolor=GREY, label='첫·중간마디'), Line2D([], [], marker='o', color='none', markerfacecolor='#075f47', label='같은 128점/손가락')],
        loc='upper left', bbox_to_anchor=(.03, .91), ncol=4, frameon=False, fontsize=11)
    metadata = []
    # Fixed oblique projection, identical in every panel.
    camera = Rotation.from_euler('x', -28, degrees=True)
    project = lambda p: camera.apply(np.asarray(p).reshape(-1, 3)).reshape(np.asarray(p).shape)[..., :2]*np.array([1000., -1000.])
    for ax, (title, angles, spreads, flipped) in zip(axes.flat, poses):
        whole = Rotation.from_euler('y', 180 if flipped else 0, degrees=True)
        all_points = []
        for i, finger in enumerate(FINGERS):
            transforms = chain_pose(finger, angles, spreads[i], offsets)
            for segment, (position, rotation) in enumerate(transforms, start=1):
                name = 'LH:'+finger+str(segment)
                moved = whole.apply(position+rotation.apply(meshes[name].reshape(-1, 3))).reshape(-1, 3, 3)
                draw_surface(ax, moved, project, GREY if segment < 3 else RED, alpha=.8)
            position, rotation = transforms[2]
            moved = whole.apply(position+rotation.apply(pieces[finger].reshape(-1, 3))).reshape(-1, 3, 3)
            draw_surface(ax, moved, project, GREEN, alpha=.9, zorder=2)
            sample = whole.apply(position+rotation.apply(pad['points_local'][i]))
            all_points.append(sample.tolist())
            projected = project(sample)
            ax.scatter(*projected.T, s=2, color='#075f47', alpha=.7, zorder=3)
            tip = project(whole.apply(position+rotation.apply(np.array([0., -.035, 0.]))))
            ax.text(*tip, KOREAN[i], ha='center', va='top', fontsize=9, color=INK)
        ax.set_title(title, fontsize=14, color=INK)
        ax.set_xlim((-80, 35) if flipped else (-35, 80)); ax.set_ylim(32, 180)
        ax.set_xlabel('고정 시점 가로 투영 (mm)', fontsize=9)
        ax.set_ylabel('고정 시점 세로 투영 (mm)', fontsize=9)
        setup_axis(ax)
        metadata.append(dict(title=title, flexion_degrees=angles, spread_degrees=spreads,
            whole_hand_rotation_y_degrees=180 if flipped else 0, samples_palm_frame_m=all_points))
    ax = axes.flat[-1]; ax.axis('off')
    ax.text(.05, .92, '확인할 점', fontsize=17, color=INK, transform=ax.transAxes)
    text = ('• 허용 면을 매 프레임의 세계 방향으로\n  다시 고르지 않습니다.\n\n'
            '• 굽힘·벌림·전체 뒤집힘에도\n  같은 몸체 로컬 표면을 사용합니다.\n\n'
            '• 손등 접근은 정상 접촉으로 인정하지 않고,\n  실제 충돌·오압현 검사는 유지합니다.\n\n'
            '• 굽힘 각도는 예시값이며\n  학습된 자세나 자연스러움의 증거가 아닙니다.')
    ax.text(.05, .8, text, fontsize=12, linespacing=1.5, va='top', color=INK, transform=ax.transAxes)
    fig.text(.035, .05, '모든 점은 가림 없이 겹쳐 표시했습니다. source 중립 체인에 회전을 적용한 도해이며 native 물리 실행·훈련 결과가 아닙니다.', fontsize=11, color=INK)
    fig.text(.035, .022, '엄지·손바닥은 생략했습니다. 회전 순서는 설명용 FK 구성으로, native 관절 적분이나 접촉을 재현하지 않습니다.', fontsize=11, color='#53667a')
    fig.savefig(OUT/'fingertip_pad_kinematic_v1.png', dpi=150)
    plt.close(fig)
    return metadata


def main():
    previous_manifest = HERE/'finger_surface_samples_manifest.json'
    previous = json.loads(previous_manifest.read_text())
    previous_checks = {name:sha(OUT/name) == metadata['sha256']
                       for name, metadata in previous['files'].items()}
    assert all(previous_checks.values())
    pad = load_fingertip_pad()
    meshes, offsets, pins = source_meshes(pad['contract'])
    pieces = {finger: patch_pieces(meshes['LH:'+finger+'3']) for finger in FINGERS}
    checks = []
    for index, finger in enumerate(FINGERS):
        p = pieces[finger]
        area = np.linalg.norm(np.cross(p[:, 1]-p[:, 0], p[:, 2]-p[:, 0]), axis=-1).sum()/2
        expected = pad['contract']['fingers_diagnostics'][index]['patch_area_m2']
        assert abs(area-expected) < 1e-15
        checks.append(dict(finger=finger, surface_area_m2=float(area), matches_production=True))
    source_patch_image(pad, meshes, offsets, pieces)
    examples = kinematic_image(pad, meshes, offsets, pieces)
    for path in (Path(__file__), FONT, ROOT/'guitar_learning/gpu/fingertip_pad.py', ROOT/'guitar_learning/gpu/finger_reward.py'):
        pins[str(path)] = sha(path)
    pins.update(pad['contract']['source_sha256'])
    output = dict(schema='guitar_learning.fingertip_pad_visual.v1', production_contract=pad['contract'],
        points_local_m=pad['points_local'].tolist(), normals_local=pad['normals_local'].tolist(),
        valid=pad['valid'].tolist(), patch_triangles_local_m={f:p.tolist() for f,p in pieces.items()},
        kinematic_examples=examples, numerical_checks=checks, source_sha256=pins,
        limitations=['engineering model-frame patch, not an anatomical annotation',
            'all points overlaid without visibility/occlusion filtering',
            'kinematic illustrations only; no native simulation, training, contact or pressure results',
            'source identity-chain FK examples; joint integration and contact are not simulated'])
    (HERE/'fingertip_pad_v1.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
    assert all(sha(path) == value for path, value in pins.items())
    files = [OUT/'fingertip_pad_surfaces_v1.png', OUT/'fingertip_pad_kinematic_v1.png',
             HERE/'fingertip_pad_v1.json', Path(__file__), HERE/'손끝압현면_v1_설명.md']
    manifest = dict(schema='guitar_learning.fingertip_pad_visual_manifest.v1',
        source_sha256=pins, results_sha256={str(path):sha(path) for path in files},
        original_visualizations_modified=False, previous_surface_manifest_sha256=sha(previous_manifest),
        previous_surface_artifacts_sha_match=previous_checks,
        native_simulation=False, learning_results=False)
    (HERE/'fingertip_pad_v1_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(outputs=[str(path) for path in files[:2]], checks=checks), ensure_ascii=False))


if __name__ == '__main__':
    main()
