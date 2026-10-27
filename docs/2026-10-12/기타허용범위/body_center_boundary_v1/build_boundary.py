"""Body reference-point boxes on saved native frames; no simulation or training."""
from pathlib import Path
from itertools import product
import hashlib
import json
import re
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/home/ajou/yigyu/3')
OUT = Path(__file__).resolve().parent
SOURCE = ROOT/'docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control'
USER = OUT.parent/'값.txt'
FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
CYAN, ORANGE, PINK = (65,210,240), (255,169,55), (255,105,200)
C = np.array([0., -.4, -.0217])

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')

def font(size):
    return ImageFont.truetype(str(FONT), size)

def text(draw, xy, message, color='white', size=24, max_width=1240):
    f=font(size)
    assert draw.textbbox((0,0),message,font=f)[2] <= max_width, message
    draw.text(xy,message,font=f,fill=color)

def corners(low, high):
    return np.array(list(product(*zip(low,high))))

EDGES = [(i,j) for i in range(8) for j in range(i+1,8) if (i^j) in (1,2,4)]

def project(points, camera, size):
    width,height=size
    world=np.column_stack((points,np.ones(len(points))))
    cam=world@np.asarray(camera['view_matrix'])
    clip=cam@np.asarray(camera['projection_matrix'])
    uv=clip[:,:2]/clip[:,3,None]
    xy=np.column_stack(((uv[:,0]+1)*width/2,(1-uv[:,1])*height/2))
    valid=(cam[:,2]<-.001)&np.isfinite(xy).all(1)&(xy[:,0]>=0)&(xy[:,0]<width)&(xy[:,1]>=0)&(xy[:,1]<height)
    return xy,cam[:,2],valid

def scene(view, box_list):
    image=Image.open(SOURCE/(view+'_raw.png')).convert('RGB')
    draw=ImageDraw.Draw(image);camera=report['cameras'][view]
    depth=np.load(SOURCE/(view+'_depth.npy'))
    assert depth.shape==(image.height,image.width)
    for box,color in box_list:
        for i,j in EDGES:
            a,b=box[i],box[j]
            endpoints,_,_=project(np.array([a,b]),camera,image.size)
            count=max(2,min(4096,int(np.linalg.norm(endpoints[1]-endpoints[0])*2)+1))
            pixels,z,valid=project(a+(b-a)*np.linspace(0,1,count)[:,None],camera,image.size)
            for k in range(count-1):
                if not(valid[k] and valid[k+1]): continue
                xy=pixels[k:k+2].astype(int)
                visible=np.all(z[k:k+2]>=depth[xy[:,1],xy[:,0]]-.002)
                if visible:
                    draw.line([tuple(pixels[k]),tuple(pixels[k+1])],fill=color,width=4)
                elif k//12%2==0:
                    draw.line([tuple(pixels[k]),tuple(pixels[k+1])],fill=tuple(int(c*.7) for c in color),width=2)
    pixels,_,valid=project(np.array([center]),camera,image.size)
    assert valid[0]
    x,y=pixels[0]
    draw.ellipse((x-6,y-6,x+6,y+6),fill=PINK,outline='black',width=2)
    draw.line((x-10,y,x+10,y),fill='black',width=2)
    draw.line((x,y-10,x,y+10),fill='black',width=2)
    return image

inputs=[USER,FONT,ROOT/'tab2body/assets/seated_pose.json',SOURCE/'geometry.json',SOURCE/'report.json']
inputs += [SOURCE/(view+suffix) for view in ('front','side') for suffix in ('_raw.png','_depth.npy')]
inputs += [OUT.parent/'root_position_front_v2.png',OUT.parent/'root_position_side_v2.png']
hashes={str(p):digest(p) for p in inputs}
rows=[line.strip().split() for line in USER.read_text().splitlines() if line.strip()]
position={};angles={};section=None
for row in rows:
    if row[0] in ('position','rotation'): section=row[0];continue
    assert len(row)==3
    (position if section=='position' else angles)[row[0].lower()]=sorted(map(float,row[1:]))
root_low=np.array([position[k][0] for k in 'xyz']);root_high=np.array([position[k][1] for k in 'xyz'])
geometry=json.loads((SOURCE/'geometry.json').read_text())
report=json.loads((SOURCE/'report.json').read_text())
assert all(report['checks'].values()) and report['physics_steps']==0
pose=geometry['initial_state']['guitar_body_states'][0]['pose']
p=np.array([pose['p'][k] for k in 'xyz']);q=np.array([pose['r'][k] for k in 'xyzw'])
rotation=Rotation.from_quat(q)
offset=rotation.apply(C);center=p+offset
old_box=corners(root_low,root_high)+offset
new_low=np.array([.11,.015,.67]);new_high=np.array([.23,.105,.77]);new_box=corners(new_low,new_high)
np.testing.assert_allclose(center,geometry['actual_body_center_W_m'],atol=1e-12)
np.testing.assert_allclose(old_box-offset,corners(root_low,root_high),atol=1e-12)
np.testing.assert_allclose(p+Rotation.from_quat(-q).apply(C),center,atol=1e-12)
assert np.all(center>=new_low) and np.all(center<=new_high)
for view,title in [('front','정면'),('side','측면')]:
    image=scene(view,[(old_box,CYAN),(new_box,ORANGE)])
    canvas=Image.new('RGB',(1280,990),'#131c28');canvas.paste(image,(0,65));draw=ImageDraw.Draw(canvas)
    text(draw,(20,14),f'기타 바디 중심의 위치 허용 박스 · {title}',size=29)
    messages=[('하늘색: 값.txt 범위를 수평 회전에서 바디 중심으로 환산 · 폭 35 × 26 × 25 cm',CYAN),
              ('주황색: 축소 제안 · X 0.110~0.230 / Y 0.015~0.105 / Z 0.670~0.770 m',ORANGE),
              ('분홍 점: 실제 바디 중심 (0.169585, 0.065012, 0.700973) m',PINK),
              ('기타 몸통 전체가 아니라 바디 기준점이 들어갈 영역입니다. 단위·좌표는 환경 기준입니다.','white'),
              ('저장 Isaac Gym 초기 화면 + 설명선 | 회전: 수평 넥 | 새 물리 실행 0회 | 안전·접촉 검증 전 후보','#c4cddd')]
    for i,(message,color) in enumerate(messages):text(draw,(20,802+34*i),message,color,size=22 if i<4 else 20)
    canvas.save(OUT/f'{view}.png')
# The same crop is applied to both old/proposed panels in each camera view.
sheet=Image.new('RGB',(2200,1630),'#131c28');draw=ImageDraw.Draw(sheet)
text(draw,(28,20),'바디 중심 기준: 기존 범위와 축소 후보',size=38,max_width=2140)
text(draw,(28,80),'같은 초기 기타·같은 카메라 · 왼쪽 기존 환산 범위 / 오른쪽 새 후보',size=27,max_width=2140)
for row,(view,label) in enumerate([('front','정면'),('side','측면')]):
    pixels,_,valid=project(np.vstack((old_box,new_box,center)),report['cameras'][view],(1280,720))
    visible=pixels[valid]
    low=np.maximum([0,0],np.floor(visible.min(0)-[90,60])).astype(int)
    high=np.minimum([1280,720],np.ceil(visible.max(0)+[90,70])).astype(int)
    roi=tuple([*low,*high])
    for column,(box,color,name) in enumerate([(old_box,CYAN,'기존 범위 · 35×26×25cm'),(new_box,ORANGE,'축소 제안 · 12×9×10cm')]):
        panel=scene(view,[(box,color)]).crop(roi)
        panel.thumbnail((1060,580),Image.Resampling.LANCZOS)
        scale=min(1060/panel.width,580/panel.height)
        panel=panel.resize((int(panel.width*scale),int(panel.height*scale)),Image.Resampling.LANCZOS)
        x=column*1100+(1100-panel.width)//2;y=205+row*655+(580-panel.height)//2
        sheet.paste(panel,(x,y))
        text(draw,(column*1100+28,150+row*655),f'{label} | {name}',color,size=27,max_width=1040)
text(draw,(28,1490),'분홍: 같은 실제 바디 중심 | 기준점의 허용 영역이며 기타 외곽 bounding box가 아닙니다.',PINK,size=27,max_width=2140)
text(draw,(28,1540),'기존 환산은 이 수평 회전에서만 유효합니다. 새 주황 박스는 환경 좌표의 바디 중심 후보입니다.','#c4cddd',size=26,max_width=2140)
sheet.save(OUT/'boundary_box_comparison.png')
summary={'source_value_file':str(USER),'old_actor_root_bounds_m':position,'old_extrinsic_xyz_bounds_deg':angles,
 'saved_reference_guitar_root_m':p.tolist(),'saved_reference_quaternion_xyzw':q.tolist(),
 'body_reference_local_m':C.tolist(),'reference_body_center_world_m':center.tolist(),
 'old_body_center_bounds_at_reference_rotation_m':{'lower':old_box.min(0).tolist(),'upper':old_box.max(0).tolist()},
 'proposed_body_center_world_bounds_m':{'lower':new_low.tolist(),'upper':new_high.tolist()},
 'old_position_width_cm':((root_high-root_low)*100).tolist(),'proposed_position_width_cm':((new_high-new_low)*100).tolist(),
 'proposed_relative_to_current_center_cm':{'lower':((new_low-center)*100).tolist(),'upper':((new_high-center)*100).tolist()},
 'proposed_rotation_review_only':{'neck_elevation_deg':[-5,25],'azimuth_offset_from_horizontal_reference_deg':[-10,10],'roll_about_neck_offset_from_reference_deg':[-15,15]},
 'scope':'Visual proposal only. Body display reference, not mass COM; old conversion is conditional on saved q; no controller modification or full 6D/contact certification.',
 'physics_steps':0,'learning_updates':0,'input_sha256':hashes}
dump('ranges.json',summary)
checks={'native_center_matches_geometry':True,'old_box_conversion_roundtrip':True,'quaternion_sign_invariant':True,
 'reference_point_inside_proposal':True,'input_hashes_unchanged':all(digest(p)==h for p,h in hashes.items())}
for name,size in [('front.png',(1280,990)),('side.png',(1280,990)),('boundary_box_comparison.png',(2200,1630))]:
    with Image.open(OUT/name) as image:assert image.size==size;image.verify()
assert all(checks.values())
dump('verification.json',{'passed':True,'checks':checks,'output_sha256':{name:digest(OUT/name) for name in ('front.png','side.png','boundary_box_comparison.png','ranges.json')},'physics_steps':0,'learning_updates':0})
print(json.dumps({'passed':True,'center_world_m':center.tolist(),'old_body_bounds':[old_box.min(0).tolist(),old_box.max(0).tolist()],'proposal_width_cm':((new_high-new_low)*100).tolist()},ensure_ascii=False,indent=2))
