"""Source-mesh presentation figures; CPU only, no training/physics changes."""
from pathlib import Path
import hashlib
import json
import os
import struct
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
ROOT = Path('/home/ajou/yigyu/3')
os.environ['MPLCONFIGDIR'] = str(HERE/'matplotlib')
sys.path.insert(0, str(ROOT))
import numpy as np
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.colors import to_rgb

from guitar_learning.gpu.fingertip_pad import load_fingertip_pad, _clip_polygon
from guitar_learning.gpu.geometry import finger_mesh_surface_samples
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract

FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
fontManager.addfont(str(FONT))
FP = FontProperties(fname=str(FONT))
plt.rcParams.update({'font.family': FP.get_name(), 'axes.unicode_minus': False,
    'svg.fonttype': 'path', 'figure.facecolor': 'white', 'savefig.facecolor': 'white'})
INK, MUTED, GREY = '#172C43', '#62758A', '#C8D2DD'
COLORS = ['#3478D4', '#E39B29', '#11A57D']
FINGERS = ['index', 'middle', 'ring', 'pinky']
LABELS = ['검지', '중지', '약지', '소지']
TITLES = ['끝마디 중심 위치', '손가락 전체 표면', '지문 쪽 끝마디 표면']
SUBTITLES = ['끝마디를 하나의 대표점으로 표현', '중간·끝마디의 모든 방향을 후보로 사용', '굽힘 안쪽 패드만 선별한 현재 방식']
DETAILS = ['중심점은 표면 위의 접촉점과 다릅니다.',
           '손등 쪽·옆면·중간마디도 후보에 포함됩니다.',
           '손등 쪽과 중간마디를 정상 압현 후보에서 제외합니다.']
FILES = ['01_distal_center', '02_full_surface', '03_fingerprint_pad']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_geometry(pad):
    source = Path(pad['contract']['frame_source']['source_xml'])
    xml = ET.parse(source).getroot()
    folder = source.parent/xml.find('compiler').get('meshdir', '.')
    assets = {e.get('name'): e for e in xml.findall('./asset/mesh')}
    bodies = {e.get('name'): e for e in xml.findall('.//body')}
    meshes, offsets, pins = {}, {}, {str(source): digest(source)}
    names = ['LH:palm']+['LH:'+f+str(s) for f in ['thumb']+FINGERS for s in (1, 2, 3)]
    for name in names:
        body = bodies[name]
        assert not any(k in body.attrib for k in ('euler', 'axisangle', 'xyaxes', 'zaxis'))
        if name != 'LH:palm':
            assert body.get('quat', '1 0 0 0') == '1 0 0 0'
        geom = body.find('geom')
        asset = assets[geom.get('mesh')]
        path = (folder/asset.get('file')).resolve()
        payload = path.read_bytes()
        count = struct.unpack_from('<I', payload, 80)[0]
        assert len(payload) == 84+50*count
        layout = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
        triangles = np.frombuffer(payload, dtype=layout, offset=84, count=count)['vertices'].astype(float)
        vertices = triangles.reshape(-1, 3)*np.fromstring(asset.get('scale', '1 1 1'), sep=' ')
        quat = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
        vertices = Rotation.from_quat(np.r_[quat[1:], quat[:1]]).apply(vertices)
        vertices += np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
        meshes[name] = vertices.reshape(-1, 3, 3)
        offsets[name] = np.fromstring(body.get('pos', '0 0 0'), sep=' ')
        pins[str(path)] = digest(path)
    poses = {'LH:palm': np.zeros(3)}
    for f in ['thumb']+FINGERS:
        parent = np.zeros(3)
        for s in (1, 2, 3):
            name = 'LH:'+f+str(s)
            parent = parent+offsets[name]
            poses[name] = parent.copy()
    return meshes, poses, pins


def clipped_patch(triangles):
    cross = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    sizes = np.linalg.norm(cross, axis=-1)
    normals = cross/np.maximum(sizes[:, None], 1e-30)
    low, high = triangles[..., 1].min(), triangles[..., 1].max()
    result = []
    for tri, normal, area in zip(triangles, normals, sizes):
        if area <= 1e-20:
            continue
        if normal[2] <= -.25:
            u = .25
        elif normal[1] <= -.4 and normal[2] <= 0:
            u = .75
        else:
            continue
        polygon = _clip_polygon(list(tri), 2, 0.)
        polygon = _clip_polygon(polygon, 1, high-u*(high-low))
        for i in range(1, len(polygon)-1):
            result.append(np.asarray((polygon[0], polygon[i], polygon[i+1])))
    return np.asarray(result)


def draw_mesh(ax, triangles, color, view, alpha=1., zorder=1):
    if view == 'palm':
        projection = lambda p: np.stack((p[..., 0], -p[..., 1]), -1)*1000
        depth = triangles[..., 2].mean(-1)
        light = np.array([-.25, .35, -.9])
    else:
        projection = lambda p: np.stack((-p[..., 1], p[..., 2]), -1)*1000
        depth = triangles[..., 0].mean(-1)
        light = np.array([-.8, .25, .45])
    normal = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-30)
    light /= np.linalg.norm(light)
    shade = .78+.22*np.maximum(normal@light, 0)
    rgb = np.asarray(to_rgb(color))[None]*shade[:, None]
    order = np.argsort(depth)[::-1]
    collection = PolyCollection(projection(triangles)[order], facecolors=rgb[order],
        edgecolors='none', alpha=alpha, zorder=zorder, rasterized=False)
    ax.add_collection(collection)


def setup(ax, view):
    ax.axis('off')
    ax.set_aspect('equal')
    if view == 'palm':
        ax.set_xlim(-123, 78)
        ax.set_ylim(-18, 181)
    else:
        ax.set_xlim(-15, 102)
        ax.set_ylim(-15, 18)


def main_view(ax, mode, meshes, poses, patch, pad, com, surface, valid):
    setup(ax, 'palm')
    for name, mesh in meshes.items():
        selected = mode == 1 and name.startswith(tuple('LH:'+f for f in FINGERS)) and name[-1] in '23'
        draw_mesh(ax, mesh+poses[name], COLORS[mode] if selected else GREY, 'palm', alpha=.80 if mode == 0 else .93)
    for i, f in enumerate(FINGERS):
        name = 'LH:'+f+'3'
        if mode == 0:
            p = com[name]+poses[name]
            ax.scatter(p[0]*1000, -p[1]*1000, s=165, c=COLORS[0],
                edgecolors='white', linewidths=2, zorder=10)
        elif mode == 1:
            for s in (2, 3):
                k = 2*i+s-2
                p = surface[k, valid[k]]+poses['LH:'+f+str(s)]
                ax.scatter(p[:, 0]*1000, -p[:, 1]*1000, s=4,
                    c='#855006', alpha=.65, linewidths=0, zorder=5)
        else:
            draw_mesh(ax, patch[f]+poses[name], COLORS[2], 'palm', zorder=4)
            p = pad['points_local'][i]+poses[name]
            ax.scatter(p[:, 0]*1000, -p[:, 1]*1000, s=4,
                c='#07664E', alpha=.72, edgecolors='white', linewidths=.12, zorder=5)
        bounds = (meshes[name]+poses[name]).reshape(-1, 3)
        ax.text(bounds[:, 0].mean()*1000, -bounds[:, 1].min()*1000+5.2,
            LABELS[i], fontsize=11, color=INK, ha='center', va='bottom')
    ax.text(-117, -10, '손바닥 쪽에서 본 동일한 중립 손 모형', fontsize=9, color=MUTED)


def detail_view(ax, mode, meshes, poses, patch, pad, com, surface, valid):
    setup(ax, 'side')
    f = 'index'
    origin = poses['LH:index1']
    for s in (1, 2, 3):
        name = 'LH:'+f+str(s)
        selected = mode == 1 and s in (2, 3)
        draw_mesh(ax, meshes[name]+poses[name]-origin,
            COLORS[mode] if selected else GREY, 'side', alpha=.68 if mode == 0 else .92)
    p3 = poses['LH:index3']-origin
    if mode == 0:
        p = p3+com['LH:index3']
        ax.scatter(-p[1]*1000, p[2]*1000, s=105, c=COLORS[0], edgecolors='white', linewidths=1.4, zorder=8)
        ax.scatter(-p3[1]*1000, p3[2]*1000, s=38, facecolors='white', edgecolors=MUTED, linewidths=1.2, zorder=8)
        ax.annotate('중심(COM)', (-p[1]*1000, p[2]*1000), (88, 13),
            fontsize=9, color=COLORS[0], ha='center', arrowprops=dict(arrowstyle='-', color=COLORS[0], lw=.8))
        ax.annotate('몸체 원점', (-p3[1]*1000, p3[2]*1000), (62, -13),
            fontsize=8, color=MUTED, ha='center', arrowprops=dict(arrowstyle='-', color=MUTED, lw=.8))
    elif mode == 1:
        for s in (2, 3):
            k = s-2
            p = surface[k, valid[k]]+poses['LH:index'+str(s)]-origin
            ax.scatter(-p[:, 1]*1000, p[:, 2]*1000, s=6, c='#855006', alpha=.75, linewidths=0, zorder=5)
    else:
        draw_mesh(ax, patch[f]+p3, COLORS[2], 'side', zorder=4)
        p = pad['points_local'][0]+p3
        ax.scatter(-p[:, 1]*1000, p[:, 2]*1000, s=6, c='#07664E', alpha=.75, linewidths=0, zorder=6)
    ax.text(-13, 14.5, '검지 옆면 확대', fontsize=9, color=MUTED, va='bottom')


def save(fig, name):
    fig.savefig(OUT/(name+'.png'), dpi=240)
    fig.savefig(OUT/(name+'.svg'))
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pad = load_fingertip_pad()
    meshes, poses, pins = read_geometry(pad)
    prepared = load_prepared_reset_contract()
    names = prepared['initial']['human_body_names']
    properties = prepared['initial']['human_properties']
    com = {name: np.asarray(properties[names.index(name)]['COM_body_m']) for name in meshes}
    surface_names = ['LH:'+f+str(s) for f in FINGERS for s in (2, 3)]
    surface, valid = finger_mesh_surface_samples(surface_names)
    patch = {f: clipped_patch(meshes['LH:'+f+'3']) for f in FINGERS}
    pins.update(pad['contract']['source_sha256'])
    pins.update(prepared['source_sha256'])
    for f in [ROOT/'guitar_learning/gpu/fingertip_pad.py', ROOT/'guitar_learning/gpu/geometry.py', FONT, Path(__file__)]:
        pins[str(f)] = digest(f)
    validation = []
    for i, f in enumerate(FINGERS):
        pts = pad['points_local'][i].astype(float)
        triangles = meshes['LH:'+f+'3']
        row = pad['contract']['fingers_diagnostics'][i]
        idx = np.asarray(row['source_triangle_indices'])
        bary = np.asarray(row['source_barycentric'])
        error = float(np.max(np.abs(np.einsum('si,sij->sj', bary, triangles[idx])-pts)))
        areas = np.linalg.norm(np.cross(patch[f][:, 1]-patch[f][:, 0], patch[f][:, 2]-patch[f][:, 0]), axis=-1).sum()/2
        assert error < 1e-8 and abs(areas-row['patch_area_m2']) < 1e-12
        assert len(pts) == 128 and (pts[:, 2] <= 1e-8).all()
        validation.append(dict(finger=f,old_surface_counts=valid[2*i:2*i+2].sum(1).tolist(),
            pad_samples=128,patch_area_mm2=float(areas*1e6),max_sample_reconstruction_error_m=error,
            distal_COM_body_m=com['LH:'+f+'3'].tolist()))
    for mode in range(3):
        fig = plt.figure(figsize=(7.4, 9.1))
        fig.text(.06, .955, f'{mode+1:02d}', fontsize=17, color=COLORS[mode], weight='bold')
        fig.text(.17, .955, TITLES[mode], fontsize=21, color=INK)
        fig.text(.06, .91, SUBTITLES[mode], fontsize=11.5, color=MUTED)
        main_view(fig.add_axes([.055, .305, .89, .565]), mode, meshes, poses, patch, pad, com, surface, valid)
        detail_view(fig.add_axes([.07, .135, .86, .14]), mode, meshes, poses, patch, pad, com, surface, valid)
        fig.text(.06, .075, DETAILS[mode], fontsize=10.5, color=INK)
        foot = ['모델에 기록된 끝마디 질량중심 · 관절 원점과 구분',
                '실제 구현: 중간마디+끝마디의 유한한 메시 정점 샘플',
                '실제 구현: 끝마디 패드의 삼각형 표면 위 128점/손가락'][mode]
        fig.text(.06, .04, foot, fontsize=8.7, color=MUTED)
        save(fig, FILES[mode])
    fig = plt.figure(figsize=(18, 10.125))
    fig.text(.035, .95, '왼손 압현 위치 표현의 비교', fontsize=27, color=INK, weight='bold')
    fig.text(.035, .905, '같은 모델·같은 중립 자세  |  파랑: 중심점   ·   주황: 둘레 전체   ·   초록: 굽힘 안쪽 패드', fontsize=12, color=MUTED)
    for mode in range(3):
        x = .035+mode*.325
        fig.text(x, .847, f'{mode+1:02d}  {TITLES[mode]}', fontsize=18, color=COLORS[mode], weight='bold')
        fig.text(x, .807, SUBTITLES[mode], fontsize=10.5, color=MUTED)
        main_view(fig.add_axes([x-.005, .302, .30, .49]), mode, meshes, poses, patch, pad, com, surface, valid)
        detail_view(fig.add_axes([x, .155, .29, .135]), mode, meshes, poses, patch, pad, com, surface, valid)
        fig.text(x, .12, DETAILS[mode], fontsize=10, color=INK)
    fig.text(.035, .063, '① 모델의 끝마디 질량중심(COM). 과거 구현의 몸체 원점은 옆면 확대도에 별도 표시했습니다.  ② 전체 표면은 코드상 중간·끝마디이며 첫마디는 제외합니다.', fontsize=9.5, color=MUTED)
    fig.text(.035, .035, '③ 지문 쪽은 모델의 굽힘 안쪽을 이용한 공학적 패드 정의입니다. 실제 지문 텍스처·피부 라벨·접촉 또는 학습 성공을 나타낸 그림은 아닙니다.', fontsize=9.5, color=MUTED)
    save(fig, 'comparison_3_methods')
    assert all(digest(path) == value for path, value in pins.items())
    manifest = dict(definition='static orthographic source-mesh figures; source neutral chain, no native simulation',
        center='prepared native distal COM in body frame, not body origin and not claimed as historical active pressure proxy',
        old_surface='all sides of finger2/finger3, production support-vertex finite sampling',
        current_pad=pad['contract'],validation=validation,source_sha256=pins,
        outputs={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in OUT.iterdir() if p.suffix in ('.png','.svg')})
    (HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(outputs=list(manifest['outputs']),validation=validation),ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
