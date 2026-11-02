"""프렛 목표점의 기타 몸통 침범과 손 자세 탐색의 한계를 구분하는 정적 분석.

실제 source convex halfspace 내부 판정만 점 침범 증거로 사용한다. source 형상은
native cooked 형상과 다를 수 있으며, 점이 밖에 있다는 사실은 손의 도달 보장이 아니다.
"""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
import argparse
import hashlib
import inspect
from itertools import product
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
import trimesh

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0,str(ROOT))
HERE=Path(__file__).resolve().parents[1]
ASSET=ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/guitar_compound.xml'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_shapes():
    root=ET.parse(ASSET).getroot();compiler=root.find('compiler')
    folder=ASSET.parent/(compiler.get('meshdir','') if compiler is not None else '')
    meshes={m.get('name'):m for m in root.findall('asset/mesh')}
    pins={str(ASSET):sha(ASSET),str(Path(__file__).resolve()):sha(__file__)};shapes=[]
    for body in root.iter('body'):
        if body.get('pos','0 0 0')!='0 0 0' or body.get('quat','1 0 0 0')!='1 0 0 0':
            raise ValueError('독립 기타 root 외의 body 변환은 명시 구현 필요')
        for i,geom in enumerate(body.findall('geom')):
            if geom.get('contype')=='0' or geom.get('conaffinity')=='0':continue
            if geom.get('type')=='mesh':
                mesh=meshes[geom.get('mesh')];path=(folder/mesh.get('file')).resolve();pins[str(path)]=sha(path)
                vertices=np.array(trimesh.load(str(path),process=False).vertices)
                vertices*=np.fromstring(mesh.get('scale','1 1 1'),sep=' ');name=geom.get('mesh')
                category='neck' if name.startswith('guitar_neck') else 'body' if name.startswith('om_collision') else 'headstock'
            elif geom.get('type')=='box':
                vertices=np.array(list(product((-1.,1.),repeat=3)))*np.fromstring(geom.get('size'),sep=' ')
                name='fret_or_nut_box_'+str(i);category='fret_or_nut'
            else:raise ValueError('Unknown active geom '+str(geom.attrib))
            quat=np.fromstring(geom.get('quat','1 0 0 0'),sep=' ')
            vertices=Rotation.from_quat(quat[[1,2,3,0]]).apply(vertices)+np.fromstring(geom.get('pos','0 0 0'),sep=' ')
            hull=ConvexHull(vertices);planes=hull.equations
            _,ids=np.unique(np.round(planes,10),axis=0,return_index=True)
            shapes.append(dict(name=name,category=category,vertices=vertices,planes=planes[ids],
                minimum=vertices.min(0),maximum=vertices.max(0)))
    return shapes,pins


def classify_point(point,shapes,tolerance_m=1e-6):
    inside=[];boundary=[];nearest=[]
    for shape in shapes:
        planes=shape['planes'];maximum=float((planes[:,:3]@point+planes[:,3]).max())
        if maximum < -tolerance_m:inside.append(shape['name'])
        elif maximum<=tolerance_m:boundary.append(shape['name'])
        nearest.append((maximum,shape['name']))
    return dict(strict_inside_shapes=inside,boundary_shapes=boundary,
        minimum_max_face_signed_m=min(nearest)[0] if nearest else None,
        closest_halfspace_shape=min(nearest)[1] if nearest else None,
        interpretation='strict inside is source convex point occupancy; positive max-face distance is separating halfspace, not exact Euclidean distance')


def vertical_interval(x,y,planes):
    lower,upper=-np.inf,np.inf
    for a,b,c,d in planes:
        rhs=-d-a*x-b*y
        if abs(c)<1e-12:
            if rhs < -1e-9:return None
        elif c>0:upper=min(upper,rhs/c)
        else:lower=max(lower,rhs/c)
    if lower>upper+1e-9 or not np.isfinite([lower,upper]).all():return None
    return float(lower),float(upper)


def analyze(out):
    from guitar_learning.tool.validation.press_acquisition import source_geometry
    shapes,pins=load_shapes()
    p=Path(inspect.getsourcefile(source_geometry)).resolve();pins[str(p)]=sha(p)
    goals=[dict(string=string-1,fret=fret) for fret in range(12,23) for string in (1,3,6)]
    starts,ends,low,high,plane,surface=source_geometry(None,goals);pins.update(surface['source_sha256'])
    body=[s for s in shapes if s['category']=='body'];non_neck=[s for s in shapes if s['category'] not in ('neck','fret_or_nut')]
    rows=[]
    for i,goal in enumerate(goals):
        start=starts[goal['string']];line=ends[goal['string']]-start
        point=start+((low[i]+high[i])/2-start[1])/line[1]*line
        normal=plane[:3]/np.linalg.norm(plane[:3]);hover=point+.010*normal
        press_status=classify_point(point,non_neck);hover_status=classify_point(hover,non_neck)
        slices=[]
        for shape in body:
            interval=vertical_interval(point[0],point[1],shape['planes'])
            if interval is not None:slices.append(dict(shape=shape['name'],lower_z_m=interval[0],upper_z_m=interval[1]))
        top=max((s['upper_z_m'] for s in slices),default=None)
        rows.append(dict(fret=goal['fret'],string_standard_1based=goal['string']+1,
            fret_cell_y_m=[float(low[i]),float(high[i])],press_point_G_m=point.tolist(),hover_point_G_m=hover.tolist(),
            press=press_status,hover=hover_status,body_vertical_intersections=slices,body_top_G_z_m=top,
            press_height_above_body_m=float(point[2]-top) if top is not None else None,
            classification='target_point_inside_non_neck_source_convex' if press_status['strict_inside_shapes'] else
                'target_on_non_neck_boundary' if press_status['boundary_shapes'] else
                'no_target_point_body_intrusion; hand/posture feasibility unproven'))
    report=dict(schema='guitar_learning.fret_access_point_occupancy.v1',completed=True,
        active_shape_count=len(shapes),category_counts={category:sum(s['category']==category for s in shapes) for category in ('neck','body','headstock','fret_or_nut')},
        point_tolerance_m=1e-6,coordinate_frame='guitar root G; real projected press plane',press_plane_G=plane.tolist(),
        body_bounds_G_m=dict(minimum=np.min([s['minimum']for s in body],axis=0).tolist(),maximum=np.max([s['maximum']for s in body],axis=0).tolist()),
        neck_bounds_G_m=[dict(name=s['name'],minimum=s['minimum'].tolist(),maximum=s['maximum'].tolist())for s in shapes if s['category']=='neck'],
        rows=rows,summary=dict(target_count=len(rows),strict_press_inside=sum(bool(r['press']['strict_inside_shapes'])for r in rows),
            strict_hover_inside=sum(bool(r['hover']['strict_inside_shapes'])for r in rows),
            press_boundary=sum(bool(r['press']['boundary_shapes'])for r in rows)),
        limitations=['Point outside body does not establish hand reachability','Source convex occupancy is not native cooked collision certification',
            'Fixed standby, arm action bounds, wrist support and free-guitar stability are separate constraints','No anatomical impossibility conclusion from local optimizer failure'],
        source_sha256=pins)
    for path,expected in pins.items():
        if sha(path)!=expected:raise ValueError('Input changed during analysis '+path)
    out.mkdir(parents=True,exist_ok=True)
    destination=out/'프렛접근가능범위.json'
    if destination.exists():raise FileExistsError('기존 분석을 덮어쓰지 않는다')
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    lines=['# 프렛 목표점과 기타 몸통의 정적 기하','',
        '이 표는 목표점 자체가 기타 몸통 안에 있는지를 검사한다. 손 전체가 접근할 수 있는지는 별도 문제다.','',
        '| 프렛 | 줄 | 목표점 몸통 내부 | hover10mm 내부 | 해당 x/y의 몸통 최고 z(mm) | 압현면과 몸통 높이차(mm) |','|---:|---:|---|---|---:|---:|']
    for r in rows:
        lines.append('| '+str(r['fret'])+' | '+str(r['string_standard_1based'])+' | '+('예' if r['press']['strict_inside_shapes'] else '아니오')+' | '+('예' if r['hover']['strict_inside_shapes'] else '아니오')+' | '+('없음' if r['body_top_G_z_m'] is None else format(r['body_top_G_z_m']*1000,'.3f'))+' | '+('없음' if r['press_height_above_body_m'] is None else format(r['press_height_above_body_m']*1000,'.3f'))+' |')
    lines+=['','압현면은 Gz='+format(plane[3]/(-plane[2])*1000,'.3f')+'mm이다. 실제 convex의 모든 외향 평면을 만족하고 경계보다 1µm 이상 안쪽일 때만 내부로 판정한다.',
        '몸통 높이는 각 목표 x/y에서 실제 convex와 수직선의 교집합으로 계산했다. 음수 proxy 거리만으로 불가능을 판정하지 않았다.',
        '이 결과만으로 13~22프렛의 연주 가능/불가능 범위를 확정할 수 없다. 손목·손바닥·엄지·전완의 충돌, 관절 범위, 고정 대기각과 실제 유지 제어를 추가로 검사해야 한다.',
        '원시 수치와 입력 SHA는 같은 디렉토리의 프렛접근가능범위.json에 보존한다.']
    (out/'프렛접근가능범위.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(shapes=len(shapes),**report['summary'],output=str(destination)),ensure_ascii=False),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'분석')
    analyze(parser.parse_args().out)
