"""Project saved same-time contact features onto original native camera PNGs."""
from pathlib import Path
import hashlib
import json
import math
import sys
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
MEETING=HERE.parent.parent
ROOT=MEETING.parents[2]
sys.path.insert(0,str(ROOT))
from stability_adapter_2.initial_pose_video60_v1.replay_v6 import rows,sha
BASE=ROOT/'paper/initial_pose/current_v3'
RUN=ROOT/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_baseline_v14'
OUT=MEETING/'result/images/current_pose_contacts_22s_v1'
OUT.mkdir(exist_ok=False)
STEP=5280
fontpath=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
paths={Path(__file__).resolve(),Path(rows.__code__.co_filename).resolve(),
 BASE/'pose/prepared_state_baseline_v14_22s.json',BASE/'pose/initial_values_baseline_v14.json',
 RUN/'contacts240.json',RUN/'states240.json',RUN/'camera_frames.json',RUN/'media/capture.json',fontpath}
paths.update(BASE/'images'/('prepared_22s_'+n+'.png') for n in ['whole_body','hands'])
pins={str(p):sha(p) for p in sorted(paths)}
(HERE/'inputs_before.json').write_text(json.dumps(pins,indent=2)+'\n')
prepared=json.loads((BASE/'pose/prepared_state_baseline_v14_22s.json').read_text())
assert prepared['source_sha256']==sha(RUN/'states240.json')
assert prepared['row']['physics_step']==STEP and prepared['row']['time_s']==22
state=prepared['row']['state']
initial=json.loads((BASE/'pose/initial_values_baseline_v14.json').read_text())
contact_row=next(r for r in rows(RUN/'contacts240.json') if r['physics_step']==STEP)
assert contact_row['time_s']==22
camera_row=next(f for f in json.loads((RUN/'camera_frames.json').read_text())['frames'] if f['physics_step']==STEP)
assert camera_row['time_s']==22
capture=next(f for f in json.loads((RUN/'media/capture.json').read_text())['frames'] if f['physics_step']==STEP)
assert capture['time_s']==22 and capture['render_preserves_states']
bodies={actor+'/'+name:body for actor in ['human','guitar']
        for name,body in zip(initial[actor+'_body_names'],state[actor+'_body_states'])}
def transform(pose,local):
    p=np.array([pose['p'][a] for a in 'xyz'])
    q=np.array([pose['r'][a] for a in 'xyzw'])
    return p+Rotation.from_quat(q).apply([local[a] for a in 'xyz'])
def group(name):
    if name=='human/Chest':return '가슴'
    if name=='human/R_Shoulder':return '오른 위팔'
    if name=='human/R_Hip':return '오른 허벅지'
    if name=='human/L_Hip':return '왼 허벅지'
    if name.startswith('human/LH:thumb'):return '왼 엄지'
    if name.startswith('human/LH:'):return '왼손 나머지'
    if name=='human/Spine':return '척추 몸통'
    return '기타 인체 부위'
COLORS={'가슴':(0,192,220),'오른 위팔':(255,146,30),'오른 허벅지':(174,71,230),
        '왼 허벅지':(55,118,240),'왼 엄지':(242,60,60),'왼손 나머지':(255,213,30),
        '척추 몸통':(145,145,145),'기타 인체 부위':(145,145,145)}
contacts=[]
for raw in contact_row['contacts']:
    names=[raw['body0_name'],raw['body1_name']]
    if not any(n.startswith('human/') for n in names) or not any(n.startswith('guitar/') for n in names):continue
    gi=next(i for i,n in enumerate(names) if n.startswith('guitar/'))
    points=[transform(bodies[n]['pose'],raw['localPos'+str(i)]) for i,n in enumerate(names)]
    gap=float(np.linalg.norm(points[0]-points[1]))
    assert gap<1e-5,(names,gap)
    contacts.append({'human_body':names[1-gi],'guitar_body':names[gi],
      'group':group(names[1-gi]),'positive_lambda':raw['lambda']>0,'raw_lambda':raw['lambda'],
      'world_guitar_m':points[gi].tolist(),'world_human_m':points[1-gi].tolist(),
      'two_body_witness_gap_m':gap,'raw_contact':raw})
assert len(contacts)==11 and sum(c['positive_lambda'] for c in contacts)==7
summary={g:{'positive_raw_rows':sum(c['group']==g and c['positive_lambda'] for c in contacts),
            'zero_raw_rows':sum(c['group']==g and not c['positive_lambda'] for c in contacts)}
         for g in dict.fromkeys(c['group'] for c in contacts)}
(HERE/'contact_evidence_22s.json').write_text(json.dumps({'physics_step':STEP,'time_s':22,
 'raw_human_guitar_rows':len(contacts),'positive_raw_rows':7,'zero_raw_rows':4,
 'groups':summary,'contacts':contacts,'camera':camera_row},ensure_ascii=False,indent=2)+'\n')
F=lambda size:ImageFont.truetype(str(fontpath),size)
font,small,title=F(21),F(17),F(26)
width,height=1280,720
panels=[];projections=[]
for camera,label in [('whole_body','정면'),('hands','오른쪽 옆면 · 원래 파일명 hands')]:
    source=BASE/'images'/('prepared_22s_'+camera+'.png')
    expected=[h for p,h in capture['image_sha256'].items() if '/'+camera+'/' in p]
    assert expected==[sha(source)],(camera,expected,sha(source))
    original=Image.open(source).convert('RGB')
    assert original.size==(width,height)
    panel=Image.new('RGB',(width,960),'white')
    panel.paste(original,(0,48))
    draw=ImageDraw.Draw(panel)
    draw.text((18,8),label+' | 준비 완료 22.000초',font=title,fill='black')
    V=np.asarray(camera_row['cameras'][camera]['view_matrix'])
    P=np.asarray(camera_row['cameras'][camera]['projection_matrix'])
    points=[]
    for i,c in enumerate(contacts):
        cam=np.r_[c['world_guitar_m'],1]@V
        clip=cam@P
        assert clip[3]>0
        ndc=clip[:2]/clip[3]
        x,y=float((ndc[0]+1)*width/2),float((1-ndc[1])*height/2)
        assert 0<x<width and 0<y<height,(camera,x,y)
        points.append((x,y))
        projections.append({'camera':camera,'contact_row_index':i,'pixel_xy_original':[x,y],
                            'group':c['group'],'positive_lambda':c['positive_lambda']})
    # Zero-response rings first, then positive points; duplicate records stay in evidence.
    for positive in [False,True]:
        for c,(x,y) in zip(contacts,points):
            if c['positive_lambda']!=positive:continue
            color=COLORS[c['group']]; y+=48;r=6 if positive else 9
            draw.ellipse((x-r-1,y-r-1,x+r+1,y+r+1),outline='black',width=2)
            draw.ellipse((x-r,y-r,x+r,y+r),fill=color if positive else None,outline=color,width=3)
    # Put labels in empty space outside the body with leaders to measured features.
    positions={'가슴':(80,265),'오른 위팔':(80,355),'오른 허벅지':(880,535),
               '왼손 나머지':(880,280),'척추 몸통':(880,400)}
    for g,counts in summary.items():
        selected=[p for c,p in zip(contacts,points) if c['group']==g]
        center=np.mean(selected,axis=0);center[1]+=48
        x,y=positions[g]
        text=g+(' (응답 0 후보)' if counts['positive_raw_rows']==0 else '')
        box=draw.textbbox((x,y),text,font=font)
        anchor=(box[2]+12 if x<640 else x-12,y+15)
        draw.line((float(center[0]),float(center[1]),anchor[0],anchor[1]),fill='black',width=4)
        draw.line((float(center[0]),float(center[1]),anchor[0],anchor[1]),fill=COLORS[g],width=2)
        draw.rounded_rectangle((box[0]-7,box[1]-5,box[2]+7,box[3]+5),radius=4,fill='white')
        draw.text((x,y),text,font=font,fill=COLORS[g],stroke_width=0)
    draw.text((18,787),'원본 Isaac Gym 녹화에 같은 시각의 실제 접촉 기록만 투영 · 새 물리/모델 렌더 없음',font=small,fill='black')
    draw.text((18,818),'채운 원: 양의 raw λ / 빈 원: λ=0 후보 · X-ray 표시로 가려진 지점도 보임',font=small,fill='black')
    draw.text((18,849),'원 크기는 힘·압력·접촉 면적이 아님. 중복 행이 있어 원 개수와 고유 접촉점 수는 다름.',font=small,fill='black')
    legend=[('가슴',30),('오른 위팔',240),('오른 허벅지',480),('왼손 나머지',760),('척추 몸통',1010)]
    for g,x in legend:
        draw.ellipse((x,903,x+14,917),fill=COLORS[g]);draw.text((x+23,895),g,font=small,fill='black')
    dest=OUT/('prepared22_contacts_'+camera+'.png')
    panel.save(dest);panels.append(panel)
canvas=Image.new('RGB',(2560,1020),'white')
draw=ImageDraw.Draw(canvas)
draw.text((22,10),'현재 학습 기준 035/v14 · 준비 완료 22초 · humanoid–guitar 접촉 지점',font=F(30),fill='black')
canvas.paste(panels[0],(0,60));canvas.paste(panels[1],(1280,60))
main=MEETING/'result/current_initial_pose_contacts_22s.png'
assert not main.exists();canvas.save(main)
assert all(sha(Path(p))==h for p,h in pins.items())
report={'renderer':'Original Isaac Gym camera PNGs with saved contact-point projection only',
 'new_physics_steps':0,'new_model_render':False,'physics_step':STEP,'time_s':22,
 'native_original_png_sha_verified':True,'input_hashes_unchanged':True,
 'raw_rows':11,'positive_rows':7,'zero_rows':4,'groups':summary,
 'max_two_body_witness_gap_m':max(c['two_body_witness_gap_m'] for c in contacts),
 'all_projected_points_inside_original_frames':True,'projections':projections,
 'projection_convention':'row-vector world homogeneous @ native view @ native projection; pixel y inverted',
 'main_image':str(main),'images':[str(main),*[str(p) for p in sorted(OUT.glob('*.png'))]],
 'scope':'One 240Hz snapshot; X-ray markers, no inferred force, area, continuous support or new collision geometry'}
(HERE/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['projections','images']},ensure_ascii=False,indent=2))
