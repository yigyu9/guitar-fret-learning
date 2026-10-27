"""Engineering proposal for a flat wrist admissible region; no training changes."""
from pathlib import Path
import itertools
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon
from matplotlib.font_manager import FontProperties
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.core.geometry_v1 import geometry_snapshot,frame
from guitar_learning.gpu.press_surface import _extract_plane

HERE=Path(__file__).resolve().parent
OUT=HERE.parent
FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
FP=FontProperties(fname=str(FONT))
plt.rcParams['font.family']=FP.get_name()
plt.rcParams['axes.unicode_minus']=False
PARAMETERS=dict(along_bodyward_cm=[5.,13.],below_lower_edge_cm=[2.,6.],behind_board_cm=[3.,9.])


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def neck_slice(hulls,y):
    """Intersection polygons in actual source hull x/z at fixed guitar y."""
    polygons=[]
    for hull in hulls:
        a=hull[:,[0,2]];b=-(hull[:,1]*y+hull[:,3]);points=[]
        for i,j in itertools.combinations(range(len(hull)),2):
            m=a[[i,j]]
            if abs(np.linalg.det(m))<1e-12:continue
            x=np.linalg.solve(m,b[[i,j]])
            if np.all(a@x<=b+1e-9):points.append(x)
        if points:
            points=np.unique(np.round(points,11),axis=0)
            center=points.mean(0);order=np.argsort(np.arctan2(points[:,1]-center[1],points[:,0]-center[0]))
            polygons.append(points[order])
    return polygons


def bounds(anchor,frets,plane,hulls):
    centers=.5*(frets[:-1,1]+frets[1:,1])
    reference_y=float(np.interp(anchor,np.arange(1,23),centers))
    plane_z=float(-(plane[1]*reference_y+plane[3])/plane[2])
    edge_values=[]
    for hull in hulls:
        low,high=-np.inf,np.inf;ok=True
        for nx,ny,nz,b in hull:
            rest=ny*reference_y+nz*plane_z+b
            if nx>1e-10:high=min(high,-rest/nx)
            elif nx< -1e-10:low=max(low,-rest/nx)
            elif rest>1e-8:ok=False
        if ok and low<=high:edge_values.append(high)
    if not edge_values:raise ValueError('Reference outside actual playing footprint')
    lower_edge=max(edge_values)
    lo=np.array([lower_edge+.02,reference_y-.13,plane_z-.09])
    hi=np.array([lower_edge+.06,reference_y-.05,plane_z-.03])
    return dict(anchor_fret=float(anchor),reference_y_G_m=reference_y,reference_edge_x_G_m=float(lower_edge),
                board_z_G_m=plane_z,lower_G_m=lo.tolist(),upper_G_m=hi.tolist())


def excess(point,b):
    lo,hi=np.array(b['lower_G_m']),np.array(b['upper_G_m'])
    return np.maximum(np.maximum(lo-point,point-hi),0.)


def penalty(point,b,weight=.2):
    e=excess(np.asarray(point),b)
    q=np.sum((e/np.array([.02,.03,.03]))**2)
    return float(-weight*q/(1+q))


def project(points,prepared,camera):
    initial=prepared['initial'];state=prepared['state']
    gp,gr=frame(state['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
    p=Rotation.from_quat(camera['quaternion_xyzw']).inv().apply(gp+gr.apply(points)-camera['eye_W_m'])
    if np.any(p[:,2]>=0):raise ValueError('Region behind camera')
    f=camera['focal_px'];return np.c_[640+f*p[:,0]/(-p[:,2]),360-f*p[:,1]/(-p[:,2])]


def draw_native(scene,prepared,camera,b,frame_index,path):
    image=Image.open(HERE/'fixed_neck.jpg').convert('RGBA')
    layer=Image.new('RGBA',image.size);draw=ImageDraw.Draw(layer)
    font=ImageFont.truetype(str(FONT),23);small=ImageFont.truetype(str(FONT),18)
    lo,hi=np.array(b['lower_G_m']),np.array(b['upper_G_m'])
    vertices=np.array(list(itertools.product(*zip(lo,hi))));pixels=project(vertices,prepared,camera)
    # Transparent true3D faces project depth without moving the source body scene.
    for axis in range(3):
        for end in (0,1):
            ids=[i for i in range(8) if ((i>>(2-axis))&1)==end]
            face=pixels[ids];center=face.mean(0);order=np.argsort(np.arctan2(face[:,1]-center[1],face[:,0]-center[0]))
            draw.polygon([tuple(p) for p in face[order]],fill=(50,208,126,32))
    for i,j in itertools.combinations(range(8),2):
        if bin(i^j).count('1')==1:draw.line((tuple(pixels[i]),tuple(pixels[j])),fill=(61,233,151,235),width=3)
    for cell in scene['cells']:
        quad=[tuple(p) for p in cell['quad_px']];draw.line(quad+[quad[0]],fill=(198,211,219,120),width=1)
        x,y=cell['label_px'];y+=20 if cell['fret']>=15 and cell['fret']%2 else 0
        draw.text((x,y),str(cell['fret']),font=small,anchor='mm',fill='white',stroke_width=2,stroke_fill=(24,30,36))
    now=frame_index/60
    for t in scene['targets']:
        if t['onset_s']<=now<t['end_s']:
            a,c=t['segment_px'];draw.line((tuple(a),tuple(c)),fill=(255,169,50),width=7)
    x,y=scene['wrist_target_px'][frame_index]
    draw.line((x-12,y,x+12,y),fill=(242,92,218),width=3);draw.line((x,y-12,x,y+12),fill=(242,92,218),width=3)
    draw.text((x,y-24),'기존 안내점',font=small,anchor='mm',fill=(255,178,239),stroke_width=2,stroke_fill=(24,30,36))
    x,y=scene['wrist_px'];draw.ellipse((x-5,y-5,x+5,y+5),outline='white',width=2)
    image=Image.alpha_composite(image,layer).convert('RGB');draw=ImageDraw.Draw(image)
    draw.rectangle((0,0,1280,100),fill=(22,27,34));draw.rectangle((0,624,1280,720),fill=(22,27,34))
    draw.text((20,10),f"제안: 손목 자유 영역 | 기준 포지션 F{b['anchor_fret']:.0f} | 초기 자세 고정",font=font,fill='white')
    draw.text((20,49),'초록: 위치 패널티 0 · 주황: 현재 음 목표 · 자홍: 기존 안내점 · 흰 원: 초기 손목',font=small,fill=(215,235,225))
    draw.text((20,636),'높이: 넥 아래 2~6cm · 길이: 기준 프렛에서 바디 쪽 5~13cm · 깊이: 지판 뒤 3~9cm',font=font,fill='white')
    draw.text((20,678),'초기 자세 기준 제안 · 학습 미적용 · 부피는 가림 없이 표시 · 앞뒤 깊이는 단면도 참조',font=small,fill=(215,225,235))
    image.save(path)


def draw_sections(wrist,b,polygons,path):
    # Coordinates relative to the actual reference fret and physical lower edge.
    along=(wrist[1]-b['reference_y_G_m'])*100
    below=(wrist[0]-b['reference_edge_x_G_m'])*100
    behind=(b['board_z_G_m']-wrist[2])*100
    fig,axes=plt.subplots(1,2,figsize=(14,6),layout='constrained')
    for ax in axes:
        ax.set_facecolor('#f7f9fa');ax.grid(alpha=.2);ax.set_aspect('equal',adjustable='box');ax.tick_params(labelsize=12)
        ax.set_ylim(8,-5.5);ax.set_ylabel('넥 아래 테두리부터 아래 방향 (cm)',fontproperties=FP,fontsize=12)
    ax=axes[0];ax.set_title('정면 투영: 넥 길이와 높이',fontproperties=FP,fontsize=16)
    ax.add_patch(Rectangle((-18,-4.5),23,4.5,facecolor='#c5cbd1',alpha=.8));ax.text(4.5,-3,'넥 (개략)',ha='right',fontproperties=FP,fontsize=13)
    ax.axvline(0,color='#d88818',linewidth=2,linestyle='--');ax.text(.3,-4.8,'기준 프렛 셀 중심',fontproperties=FP,fontsize=11)
    ax.add_patch(Rectangle((-13,2),8,4,facecolor='#31bc79',edgecolor='#168250',alpha=.3,linewidth=2))
    ax.text(-9,3,'허용 영역\n바디 쪽 5~13cm\n아래 2~6cm',ha='center',va='center',fontproperties=FP,fontsize=12)
    ax.plot(along,below,'o',color='#274860',markersize=8);ax.annotate('초기 실제 손목',xy=(along,below),xytext=(-17.5,7),arrowprops={'arrowstyle':'->'},fontproperties=FP,fontsize=12)
    ax.set_xlim(-18,5);ax.set_xlabel('기준에서 넥 길이 방향 (cm)  ← 기타 바디 / 너트 →',fontproperties=FP,fontsize=12)
    ax=axes[1];ax.set_title('넥 단면: 앞뒤 깊이와 높이',fontproperties=FP,fontsize=16)
    for p in polygons:
        coords=np.c_[(b['board_z_G_m']-p[:,1])*100,(p[:,0]-b['reference_edge_x_G_m'])*100]
        ax.add_patch(Polygon(coords,facecolor='#c5cbd1',edgecolor='#687783',alpha=.8))
    ax.axvline(0,color='#d88818',linewidth=2,linestyle='--');ax.text(-.25,-4.8,'지판면',ha='right',fontproperties=FP,fontsize=12)
    ax.add_patch(Rectangle((3,2),6,4,facecolor='#31bc79',edgecolor='#168250',alpha=.3,linewidth=2))
    ax.text(6,3,'허용 영역\n지판 뒤 3~9cm\n아래 2~6cm',ha='center',va='center',fontproperties=FP,fontsize=12)
    ax.plot(behind,below,'o',color='#274860',markersize=8);ax.annotate('초기 실제 손목',xy=(behind,below),xytext=(2.2,7),arrowprops={'arrowstyle':'->'},fontproperties=FP,fontsize=12)
    ax.set_xlim(-2,11);ax.set_xlabel('지판면에서 연주자 쪽 깊이 (cm) →',fontproperties=FP,fontsize=12)
    fig.suptitle('손목을 한 점으로 끌지 않고 영역 전체를 같은 상태로 허용',fontproperties=FP,fontsize=18)
    fig.savefig(path,dpi=160);plt.close(fig)


def main():
    scene=json.loads((HERE/'scene.json').read_text());camera=json.loads((HERE/'camera.json').read_text())
    prepared=load_prepared_reset_contract();initial=prepared['initial']
    geometry=geometry_snapshot(prepared['state'],initial['human_body_names'],initial['guitar_body_names'])
    plane,hulls,pins=_extract_plane(ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/guitar_compound.xml',scene['press_plane']['source_sha256'])
    frets=geometry['fret_markers_G_m'];wrist=np.array(scene['wrist_G_m']);frames=[219,int(np.argmin(np.abs(np.array(scene['anchor_fret'])-9)))]
    rows=[]
    for f in frames:
        a=round(scene['anchor_fret'][f],5);b=bounds(a,frets,plane,hulls)
        draw_native(scene,prepared,camera,b,f,OUT/f'wrist_region_anchor{round(a)}_proposal.png')
        old_target=np.array(scene['wrist_target_G_m'][f]);nearest=np.clip(wrist,b['lower_G_m'],b['upper_G_m'])
        rows.append(dict(frame=f,time_s=f/60,region=b,old_point_movement_from_initial_cm=float(np.linalg.norm(old_target-wrist)*100),
                         old_position_full_score_minimum_movement_cm=float(max(np.linalg.norm(old_target-wrist)-.02,0)*100),
                         new_region_minimum_movement_from_initial_cm=float(np.linalg.norm(nearest-wrist)*100)))
    b=rows[0]['region'];polygons=neck_slice(hulls,b['reference_y_G_m']);draw_sections(wrist,b,polygons,OUT/'wrist_region_axes_proposal.png')
    assert not excess(wrist,b).any()
    mid=(np.array(b['lower_G_m'])+np.array(b['upper_G_m']))/2
    for p in [mid,np.array(b['lower_G_m']),np.array(b['upper_G_m']),wrist]:assert penalty(p,b)==0
    p=mid.copy();p[0]=b['upper_G_m'][0]+.01;assert abs(penalty(p,b)+.04)<1e-12
    q=p.copy();q[0]+=.02;assert penalty(q,b)<penalty(p,b)<0
    assert np.isclose(penalty(q,b,weight=.1),penalty(q,b)/2)
    verified_pins=dict(pins)
    for p in [HERE/'scene.json',HERE/'camera.json',HERE/'fixed_neck.jpg',Path(__file__).resolve(),FONT]:verified_pins[str(p)]=sha(p)
    result=dict(schema='guitar_learning.wrist_region_proposal.v1',proposal_only=True,learning_implemented=False,
        parameters=PARAMETERS,reference='anchor fret-cell midpoint, physical lower neck edge at that reference, source press plane; guitar-local moving frame',
        rows=rows,initial_wrist_G_m=wrist.tolist(),initial_coordinates_cm=dict(along_bodyward=(b['reference_y_G_m']-wrist[1])*100,below_edge=(wrist[0]-b['reference_edge_x_G_m'])*100,behind_board=(b['board_z_G_m']-wrist[2])*100),
        penalty=dict(inside=0,excess='max(lower-p,p-upper,0) per G axis',scales_G_xyz_m=[.02,.03,.03],q='sum((excess/scales)^2)',raw_rate_per_s='-q/(1+q)',stage_weights=[.2,.1,.05],stage0_rate_asymptote_per_s=-.2,integration_dt_s=1/240,orientation='omit initial-orientation prior from this position-region term; no new rotation/velocity/action costs'),
        numerical_checks='PASS inclusive boundary0, initial/reset inside anchor5, monotonic negative outside, stage scaling',
        limitations=['Engineering starting ranges tied to current source model, not human ergonomic certification','No humanoid motion, physics, policy or training performed','All corners/fingers/strings have not been proven reachable by IK','Physical lower edge sampled at reference anchor; rectangle is a guidance band, not a collision surface'],source_sha256=verified_pins)
    (HERE/'wrist_region_proposal.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'initial_coordinates_cm':result['initial_coordinates_cm'],'comparison':rows},ensure_ascii=False))


if __name__=='__main__':main()
