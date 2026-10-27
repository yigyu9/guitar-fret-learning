"""Show production source surface samples and nearest points at a frozen reset."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.font_manager import FontProperties

from guitar_learning.core.geometry_v1 import frame
from guitar_learning.gpu.geometry import apply, conjugate, finger_mesh_surface_samples, surface_target_geometry
from guitar_learning.gpu.finger_reward import finger_target_indices
from guitar_learning.gpu.press_surface import load_press_surface, project_press_strings
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.native.paths import resolve_input_path
from guitar_learning.song.task import make_task

HERE, OUT = Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent
FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
FP = FontProperties(fname=str(FONT))
FINGERS = ['index', 'middle', 'ring', 'pinky']
KOREAN = ['검지', '중지', '약지', '소지']
CYAN, GOLD, MAGENTA, ORANGE = '#17c9e8', '#ffe068', '#f943cb', '#ff8c25'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def project(points, prepared, camera):
    initial, state = prepared['initial'], prepared['state']
    gp, gr = frame(state['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
    p = Rotation.from_quat(camera['quaternion_xyzw']).inv().apply(gp+gr.apply(points)-camera['eye_W_m'])
    assert np.all(p[..., 2] < 0)
    f = camera['focal_px']
    return np.stack((640+f*p[..., 0]/-p[..., 2], 360-f*p[..., 1]/-p[..., 2]), -1)


def meshes(prepared):
    """Actual source triangles, including source scale/geom and saved body pose."""
    initial, state = prepared['initial'], prepared['state']
    path = resolve_input_path(initial['loaded_assets'][0]['path']).resolve()
    xml = ET.parse(path).getroot()
    folder = path.parent/xml.find('compiler').get('meshdir', '.')
    assets = {m.get('name'):m for m in xml.findall('./asset/mesh')}
    bodies = {b.get('name'):b for b in xml.findall('.//body')}
    gp, gr = frame(state['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
    result, pins = {}, {str(path):sha(path)}
    for finger in FINGERS:
        for segment in (1, 2, 3):
            name = 'LH:'+finger+str(segment)
            geom = bodies[name].find('geom'); mesh = assets[geom.get('mesh')]
            source = (folder/mesh.get('file')).resolve(); payload = source.read_bytes()
            count = struct.unpack_from('<I', payload, 80)[0]
            assert len(payload) == 84+count*50
            layout = np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
            triangles = np.frombuffer(payload, dtype=layout, count=count, offset=84)['vertices'].astype(float)
            vertices = triangles.reshape(-1, 3)*np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
            q = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
            vertices = Rotation.from_quat(np.r_[q[1:], q[:1]]).apply(vertices)+np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
            bp, br = frame(state['human_body_states'][initial['human_body_names'].index(name)])
            result[name] = gr.inv().apply(bp+br.apply(vertices)-gp).reshape(-1, 3, 3)
            pins[str(source)] = sha(source)
    return result, pins


def extract():
    torch.set_num_threads(1)
    prepared = load_prepared_reset_contract(); initial, state = prepared['initial'], prepared['state']
    names = ['LH:'+f+str(s) for f in ['thumb']+FINGERS for s in (2, 3)]
    local, valid = finger_mesh_surface_samples(names)
    poses = [frame(state['human_body_states'][initial['human_body_names'].index(n)]) for n in names]
    pos = torch.tensor(np.array([p for p, r in poses]), dtype=torch.float32)
    rot = torch.tensor(np.array([r.as_quat() for p, r in poses]), dtype=torch.float32)
    gp, gr = frame(state['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
    gq = torch.tensor(gr.as_quat(), dtype=torch.float32)
    gpos = torch.tensor(gp, dtype=torch.float32)
    points = apply(conjugate(gq), pos[:, None]+apply(rot[:, None], torch.tensor(local))-gpos)[None]
    marker_names = ['G:string%d'%i for i in range(1,7)]+['G:string%d_end'%i for i in range(1,7)]+['G:nut']+['G:fret%d'%i for i in range(1,23)]
    marker_world = torch.tensor(np.array([frame(state['guitar_body_states'][initial['guitar_body_names'].index(n)])[0] for n in marker_names]), dtype=torch.float32)
    markers = apply(conjugate(gq), marker_world-gpos)
    starts, ends, frets = markers[:6][None], markers[6:12][None], markers[12:]
    bundle = ROOT/'data/song_bundles/05_BN2-131-B_solo'
    task = make_task(bundle, pre_roll_s=3., tail_s=.5)
    onset, end, press = [torch.tensor([getattr(t, key) for t in task.targets], dtype=torch.float64) for key in ['onset_s','end_s','press_s']]
    fingers = torch.tensor([t.finger for t in task.targets]); strings = torch.tensor([t.string for t in task.targets]); target_frets = torch.tensor([t.fret for t in task.targets])
    times = torch.arange(task.provenance['song']['control_ticks']+1, dtype=torch.float64)/60
    selection = finger_target_indices(times, onset, end, press, fingers)
    frame_index = int(selection['valid'][..., 0].all(-1).nonzero()[0])
    chosen = selection['indices'][frame_index, :, 0].tolist()
    plane = load_press_surface(strings.tolist(), target_frets.tolist())
    projected_start, projected_end = project_press_strings(starts, ends, torch.tensor(plane['plane_G'], dtype=torch.float32))
    a, b = frets[target_frets-1, 1][None], frets[target_frets, 1][None]
    low, high = torch.minimum(a, b), torch.maximum(a, b)
    delta, velocity, distance, sample = surface_target_geometry(points, torch.zeros_like(points), torch.tensor(valid),
        projected_start, projected_end, low, high, strings, fingers, -.002)
    rows = []
    for f, target_index in enumerate(chosen, start=1):
        index = int(sample[0, target_index]); body_index, local_index = divmod(index, local.shape[1])
        selected_point = points[0, body_index, local_index]
        closest = selected_point+delta[0, target_index]
        t = task.targets[target_index]
        line = projected_end[0,t.string]-projected_start[0,t.string]
        u = [(float(v)-float(projected_start[0,t.string,1]))/float(line[1]) for v in [low[0,target_index]+.002,high[0,target_index]-.002]]
        segment = projected_start[0,t.string]+torch.tensor(u)[:,None]*line
        # Independent all-valid-sample distance-to-segment check in float64.
        candidates = points[0,2*f:2*f+2].reshape(-1,3).numpy()[valid[2*f:2*f+2].reshape(-1)]
        aa, bb = segment.numpy().astype(float); direction = bb-aa
        fraction = np.clip((candidates-aa)@direction/(direction@direction), 0, 1)
        minimum = np.linalg.norm(aa+fraction[:,None]*direction-candidates, axis=1).min()
        assert abs(minimum-float(distance[0,target_index])) < 1e-7
        assert 2*f <= body_index < 2*f+2 and valid[body_index,local_index]
        rows.append(dict(finger=f,name=KOREAN[f-1],target_index=target_index,target_id=t.target_id,
            string=t.string+1,fret=t.fret,phase='현재 음' if t.onset_s <= frame_index/60 < t.end_s else '준비 음',
            selected_body=names[body_index],selected_local_sample=local_index,selected_flat_index=index,
            selected_G_m=selected_point.tolist(),closest_target_G_m=closest.tolist(),target_segment_G_m=segment.tolist(),
            distance_mm=float(distance[0,target_index])*1000,independent_distance_mm=minimum*1000,
            middle_count=int(valid[2*f].sum()),distal_count=int(valid[2*f+1].sum())))
    triangles, pins = meshes(prepared)
    pins.update(prepared['source_sha256']); pins.update(plane['source_sha256'])
    for path in [Path(__file__),HERE/'fixed_neck.jpg',HERE/'camera.json',FONT,
                 ROOT/'guitar_learning/gpu/geometry.py',ROOT/'guitar_learning/gpu/finger_reward.py',ROOT/'guitar_learning/gpu/environment.py',ROOT/'guitar_learning/gpu/press_surface.py',bundle/'manifest.json',bundle/'training/hand_position_targets.json']:
        pins[str(path)] = sha(path)
    pins.update({t['path']:t['sha256'] for t in task.provenance['provenance']})
    return prepared, points[0].numpy(), valid, triangles, rows, frame_index, pins


def overview(prepared, points, valid, rows, frame_index):
    camera = json.loads((HERE/'camera.json').read_text())
    image = Image.open(HERE/'fixed_neck.jpg').convert('RGB')
    crop = (515, 235, 860, 520); scale = 2.8
    zoom = image.crop(crop).resize((966, 798), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(zoom)
    def px(p):
        return (project(np.asarray(p), prepared, camera)-np.array(crop[:2]))*scale
    for f in range(1,5):
        for segment,color in [(2,CYAN),(3,GOLD)]:
            index=2*f+segment-2
            for x,y in px(points[index,valid[index]]):
                draw.ellipse((x-2.2,y-2.2,x+2.2,y+2.2),fill=color)
    for row in rows:
        line=px(row['target_segment_G_m']); draw.line(tuple(map(tuple,line)),fill=ORANGE,width=5)
        selected,closest=px([row['selected_G_m'],row['closest_target_G_m']])
        draw.line((tuple(selected),tuple(closest)),fill=MAGENTA,width=3)
        x,y=selected;draw.ellipse((x-8,y-8,x+8,y+8),fill=MAGENTA,outline='white',width=2)
        draw.text((x+12,y-16),str(row['finger']),font=ImageFont.truetype(str(FONT),26),fill='white',stroke_width=2,stroke_fill='#242833')
    canvas=Image.new('RGB',(1600,1010),'#161b22');canvas.paste(zoom,(20,120));d=ImageDraw.Draw(canvas)
    title=ImageFont.truetype(str(FONT),32);font=ImageFont.truetype(str(FONT),24);small=ImageFont.truetype(str(FONT),21)
    d.text((25,15),'현재 표면 접근에 실제 사용되는 점',font=title,fill='white')
    d.text((25,65),f'초기 자세 고정 | 정책 시각 {frame_index/60:.3f}초의 목표만 적용 | 손가락 번호 1검지·2중지·3약지·4소지',font=small,fill='#cbd8e5')
    x=1020
    for y,color,text in [(130,CYAN,'중간마디 메시 표면점'),(178,GOLD,'끝마디 메시 표면점'),(226,MAGENTA,'실제로 선택된 최근접 점'),(274,ORANGE,'목표 현·프렛의 압현면 선분')]:
        d.ellipse((x,y+8,x+15,y+23),fill=color);d.text((x+27,y),text,font=small,fill='white')
    for i,row in enumerate(rows):
        y=355+i*120;part='중간마디' if row['selected_body'].endswith('2') else '끝마디'
        d.text((x,y),f"{row['finger']}. {row['name']}  ·  {row['phase']}",font=font,fill='white')
        d.text((x,y+34),f"{row['string']}번 현 F{row['fret']} → {part}",font=small,fill='#e3ecf5')
        d.text((x,y+65),f"후보 {row['middle_count']+row['distal_count']}점 · 거리 {row['distance_mm']:.2f}mm",font=small,fill='#b9c9d8')
    d.text((25,940),'가려진 점도 겹쳐 표시 · 실제 피부 전체가 아닌 유한한 메시 정점 샘플 · 접촉·압력 판정 이미지가 아님',font=small,fill='#d3dfeb')
    d.text((25,973),'엄지와 손가락 첫마디는 이 표면 접근 거리의 선택 대상에서 제외 · 몸체·기타·학습 코드 변경 없음',font=small,fill='#d3dfeb')
    canvas.save(OUT/'finger_surface_samples_overview.png')


def details(points, valid, triangles, rows):
    fig,axes=plt.subplots(4,2,figsize=(15,15),layout='constrained')
    for i,row in enumerate(rows):
        finger=FINGERS[i];root=triangles['LH:'+finger+'1'].reshape(-1,3).mean(0)
        for col,ax in enumerate(axes[i]):
            def projection(p):
                q=(np.asarray(p)-root)*1000
                return np.stack((q[...,1] if col==0 else -q[...,2],-q[...,0]),-1)
            for segment,color in [(1,'#8293a6'),(2,CYAN),(3,GOLD)]:
                mesh=projection(triangles['LH:'+finger+str(segment)])
                ax.add_collection(PolyCollection(mesh,facecolors=color,edgecolors='none',alpha=.16))
                if segment>1:
                    index=2*(i+1)+segment-2;p=projection(points[index,valid[index]])
                    ax.scatter(p[:,0],p[:,1],s=13,c=color,edgecolors='#334352',linewidths=.2,zorder=3)
            segment=projection(row['target_segment_G_m']);pair=projection([row['selected_G_m'],row['closest_target_G_m']])
            ax.plot(*segment.T,color=ORANGE,linewidth=4,zorder=4)
            ax.plot(*pair.T,color=MAGENTA,linestyle='--',linewidth=1.7,zorder=4)
            ax.scatter(*pair[0],s=110,c=MAGENTA,edgecolors='white',linewidths=1.5,zorder=5)
            part='중간마디' if row['selected_body'].endswith('2') else '끝마디'
            ax.set_title(f"{row['name']} · {'정면 투영' if col==0 else '깊이 투영'} | {row['string']}현 F{row['fret']} {row['phase']}\n중간 {row['middle_count']}점 / 끝 {row['distal_count']}점 · 선택 {part} · 거리 {row['distance_mm']:.2f}mm",fontproperties=FP,fontsize=12)
            ax.autoscale_view();ax.margins(.14);ax.set_aspect('equal',adjustable='box');ax.grid(alpha=.2);ax.set_facecolor('#f4f7fa')
            ax.set_xlabel('넥 길이 방향 (mm)' if col==0 else '지판 뒤 연주자 방향 (mm)',fontproperties=FP,fontsize=10)
            ax.set_ylabel('넥 위 방향 (mm)',fontproperties=FP,fontsize=10)
    fig.suptitle('실제 초기 메시와 표면 샘플의 두 방향 투영\n청록=중간마디 · 노랑=끝마디 · 자홍=선택점 · 주황=목표선분 · 회색 첫마디는 선택 제외\n좌표 원점은 각 손가락 첫마디 메시 중심 · 모든 점을 가림 없이 표시',fontproperties=FP,fontsize=15)
    fig.savefig(OUT/'finger_surface_samples_detail.png',dpi=150);plt.close(fig)


def main():
    prepared,points,valid,triangles,rows,f,pins=extract()
    overview(prepared,points,valid,rows,f);details(points,valid,triangles,rows)
    assert all(sha(path)==value for path,value in pins.items())
    result=dict(schema='guitar_learning.finger_surface_visual.v1',policy_frame=f,policy_time_s=f/60,score_time_s=f/60-3,
        frozen_pose='agreed035/v14 reset; no humanoid motion or physics',selection='earliest policy frame with tracking slot0 valid for all four fingers',
        sampling='production finger_mesh_surface_samples: support vertices in64 fixed sphere directions plus6 axes; valid mask excludes padding',
        sample_body_names=['LH:'+finger+str(segment) for finger in ['thumb']+FINGERS for segment in (2,3)],
        valid_counts=valid.sum(1).tolist(),surface_points_G_m=points.tolist(),valid_mask=valid.tolist(),rows=rows,
        notes=['not a fixed fingertip/pad center; selected point changes with target/pose','all sides of middle/distal source mesh are eligible, no palm-side filter','thumb samples exist in the shared buffer but are excluded by the four-finger approach selector','nearest surface to finite projected target segment; no contact/load/pressure inferred'],source_sha256=pins)
    (HERE/'finger_surface_samples.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(frame=f,rows=rows),ensure_ascii=False))


if __name__=='__main__':
    main()
