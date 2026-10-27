from pathlib import Path
import hashlib,json,math,shutil,subprocess
from PIL import Image,ImageDraw,ImageFont

P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1')
OUT=P/'artifacts_v1'; V=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1')
FONT_PATH=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf'); FONT=ImageFont.truetype(str(FONT_PATH),22); SMALL=ImageFont.truetype(str(FONT_PATH),17); TINY=ImageFont.truetype(str(FONT_PATH),14)
CASES=[('native_v1/right4_upper35','right4_upper35','Chest4° + point 상완35%'),('native_v2/right6_upper35','right6_upper35','Chest6° + point 상완35%'),('native_v3/right6_gentle_press','right6_gentle_press','Chest6° + gentle press')]
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def snap(p):
 p=Path(p);st=p.stat();return {'sha256':sha(p),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
def load(p):return json.loads(Path(p).read_text())
def rgb(p):return Image.open(p).convert('RGB')
def fit(im,w,h):
 im=im.copy();im.thumbnail((w,h),Image.Resampling.LANCZOS);c=Image.new('RGB',(w,h),'#f2f2f2');c.paste(im,((w-im.width)//2,(h-im.height)//2));return c

def vec(d,keys):return [float(d[k]) for k in keys]
def qrotate(q,v):
 x,y,z,w=q; qv=[x,y,z]
 def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
 c1=cross(qv,v); c2=cross(qv,[c1[i]+w*v[i] for i in range(3)])
 return [v[i]+2*c2[i] for i in range(3)]
def project(point,cam,width,height):
 vm=cam['view_matrix'];pm=cam['projection_matrix']; camera=[sum([point[0],point[1],point[2],1.0][k]*vm[k][j] for k in range(4)) for j in range(4)]
 clip=[sum(camera[k]*pm[k][j] for k in range(4)) for j in range(4)]
 if clip[3]==0:raise ValueError('clip w is zero')
 ndc=[clip[0]/clip[3],clip[1]/clip[3]];px=((ndc[0]+1)*width/2,(1-ndc[1])*height/2)
 valid=camera[2]<-.001 and math.isfinite(px[0]) and math.isfinite(px[1]) and 0<=px[0]<width and 0<=px[1]<height
 return [float(px[0]),float(px[1])],float(camera[2]),bool(valid)
def motor_world(body_state,local):
 p=vec(body_state['pose']['p'],['x','y','z']);r=body_state['pose']['r'];q=vec(r,['x','y','z','w']);rot=qrotate(q,local);return [p[i]+rot[i] for i in range(3)]

summary_path=P/'result_summary_v2.json'; region_path=P/'contact_region_v2.json'
summary=load(summary_path); region=load(region_path)
assert summary['native2_and3_full_initial_state_exact'] and summary['same_full_native_guitar_initial_state_between_trials']
files=[Path(__file__),FONT_PATH,summary_path,region_path,P/'analyze_contact_region_v2.py',Path('/home/ajou/yigyu/3/stability_adapter_2/strap_trial_recording.py'),
 P/'analysis_v1/verification.json',P/'analysis_v2/verification.json',P/'analysis_v3/verification.json',
 Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/result_summary_v1.json'),Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/analysis_v3/verification.json'),Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/native_v2/right4_close_support_upper_press/report.json')]
for run,tag,_ in CASES:
 root=P/run
 files += [root/'report.json',root/'initial_values.json',root/'trace.json',root/'media/capture.json',root/'media/physics_endpoint_contacts.json',root/'media/whole_body.mp4',root/'media/hands.mp4',root/'media/axilla_effort_configuration.json']
 files += [root/f'media/frames/whole_body/{f}.png' for f in ['00000','00060','00150']]
# include exact images and JSON that define the annotated weak-case points
weak=P/'native_v3/right6_gentle_press'
files += [weak/'media/axilla_effort_configuration.json',weak/'initial_values.json',weak/'media/physics_endpoint_contacts.json',weak/'media/capture.json']
before={str(f):snap(f) for f in sorted(set(files))};before[str(Path(__file__))]=snap(__file__)
# Produce the native whole-body 0/2/5 timeline, three columns by three conditions.
W,H=420,236;gap=14;head=90;label=34
canvas=Image.new('RGB',(3*W+4*gap,3*H+4*gap+head+3*label),'white');d=ImageDraw.Draw(canvas)
d.text((gap,7),'오른쪽 upper-bout 조건 · 실제 native whole_body 캡처',font=FONT,fill='#111')
d.text((gap,37),'각 실행의 저장 프레임을 표시합니다. 기하/접촉 분류 결과와 화면 겹침은 별개입니다.',font=SMALL,fill='#333')
for ri,(run,tag,labeltext) in enumerate(CASES):
 for ci,(sec,frame) in enumerate([(0,'00000'),(2,'00060'),(5,'00150')]):
  x=gap+ci*(W+gap);y=head+gap+ri*(H+label+gap)
  d.text((x,y-label+1),f'{labeltext} · {sec}초',font=TINY,fill='#111')
  im=rgb(P/run/f'media/frames/whole_body/{frame}.png');canvas.paste(fit(im,W,H),(x,y));d.rectangle((x,y,x+W,y+H),outline='#888',width=2)
timeline=OUT/'native_timeline_0_2_5s.png';canvas.save(timeline)
# Annotate actual native 0s and 5s images for the weak-case (native3).
weak= P/'native_v3/right6_gentle_press'; iv=load(weak/'initial_values.json'); cfg=load(weak/'media/axilla_effort_configuration.json'); cap=load(weak/'media/capture.json')
contact_data=load(region_path)['cases']['right6_gentle_press']; last=contact_data['rows'][-1]
positive=[c for c in last['contacts'] if c.get('positive_raw_lambda')]
assert positive and last['physics_step']==1200
contact=positive[0]; blue_w=contact['contact_feature_W_m']; motor_local=cfg['motor_reference_local_m']
shoulder_idx=iv['human_body_names'].index('R_Shoulder')
initial_body=iv['native_initial_state']['human_body_states'][shoulder_idx]
endrow=load(weak/'media/physics_endpoint_contacts.json')['rows'][-1]
assert endrow['physics_step']==1200
final_body=endrow['human_body_states']['R_Shoulder']
yellow0=motor_world(initial_body,motor_local);yellow5=motor_world(final_body,motor_local)
# World-space endpoint distance is a reference-to-feature separation, not a gap/contact criterion.
distance_mm=1000*math.sqrt(sum((yellow5[i]-blue_w[i])**2 for i in range(3)))
annotated=Image.new('RGB',(1730,1630),'white');ad=ImageDraw.Draw(annotated)
def mark(draw,xy,color,rad=9,shape='circle'):
 x,y=xy
 if shape=='cross':
  draw.line((x-rad,y,x+rad,y),fill='black',width=5);draw.line((x,y-rad,x,y+rad),fill='black',width=5)
  draw.line((x-rad,y,x+rad,y),fill=color,width=3);draw.line((x,y-rad,x,y+rad),fill=color,width=3)
  draw.ellipse((x-3,y-3,x+3,y+3),fill=color,outline='black',width=1)
 else: draw.ellipse((x-rad,y-rad,x+rad,y+rad),fill=color,outline='black',width=2)
def arrow(draw,start,end,color,width=3):
 draw.line([start,end],fill=color,width=width); x0,y0=start;x1,y1=end; ang=math.atan2(y1-y0,x1-x0); L=11
 p1=(x1-L*math.cos(ang-.55),y1-L*math.sin(ang-.55));p2=(x1-L*math.cos(ang+.55),y1-L*math.sin(ang+.55));draw.polygon([end,p1,p2],fill=color)
for rowi,(sec,frame,body,yellow,blue) in enumerate([
 (0,'00000',initial_body,yellow0,None),(5,'00150',final_body,yellow5,blue_w)]):
 ytop=20+rowi*760
 ad.text((20,ytop),f'weak-case native3 · {sec}초 · 실제 native whole_body 이미지',font=FONT,fill='#111')
 raw_path=weak/f'media/frames/whole_body/{frame}.png'; im=rgb(raw_path); width,height=im.size
 camera=cap['frames'][0 if sec==0 else 150]['cameras']['whole_body']
 yellow_xy,_,oky=project(yellow,camera,width,height);assert oky
 blue_xy=None
 if blue is not None: blue_xy,_,okb=project(blue,camera,width,height);assert okb
 # At left, show the original full native image with marker overlays (annotation only).
 overlay=im.copy();od=ImageDraw.Draw(overlay);mark(od,yellow_xy,'#ffd400',11,'cross')
 if blue_xy is not None:mark(od,blue_xy,'#258cff',6,'circle')
 annotated.paste(overlay,(20,ytop+38))
 # At right, magnify a fixed pixel crop around the projected point(s); crop is for readability only.
 points=[yellow_xy]+([blue_xy] if blue_xy is not None else [])
 cx=sum(p[0] for p in points)/len(points);cy=sum(p[1] for p in points)/len(points)
 crop_w=crop_h=180; left=max(0,min(width-crop_w,int(cx-crop_w/2))); top=max(0,min(height-crop_h,int(cy-crop_h/2)))
 crop=im.crop((left,top,left+crop_w,top+crop_h)).resize((420,420),Image.Resampling.NEAREST)
 cropdraw=ImageDraw.Draw(crop)
 def scaled(pt):return ((pt[0]-left)*420/crop_w,(pt[1]-top)*420/crop_h)
 mark(cropdraw,scaled(yellow_xy),'#ffd400',17,'cross')
 if blue_xy is not None:mark(cropdraw,scaled(blue_xy),'#258cff',9,'circle')
 annotated.paste(crop,(1300,ytop+40));ad.rectangle((1300,ytop+40,1720,ytop+460),outline='#555',width=2)
 # Legend and explicit state/time labels on the pane below the zoom crop.
 ad.text((1300,ytop+475),'확대 crop · 원본 픽셀 확대, 실제 크기 아님',font=TINY,fill='#222')
 ad.ellipse((1304,ytop+510,1322,ytop+528),fill='#ffd400',outline='black');ad.text((1330,ytop+507),'shoulder-side 35% human motor-reference point',font=TINY,fill='#222')
 if blue_xy is not None:
  ad.ellipse((1304,ytop+535,1322,ytop+553),fill='#258cff',outline='black');ad.text((1330,ytop+532),'실제 positive-raw-lambda contact feature (t=5)',font=TINY,fill='#222')
  annotated.paste(overlay,(20,ytop+38))
# Add interpretive footer.
ad.text((20,1570),f'점들은 capture camera의 view/projection으로 투영한 사후 주석입니다. t=5 reference↔contact feature 거리={distance_mm:.2f} mm; 이는 motor point–contact feature 간 거리이며 어깨-gap·지지 판정이 아닙니다.',font=TINY,fill='#222')
ad.text((20,1593),'주석은 depth-tested가 아니고 PhysX 상태/영상 원본은 변경하지 않았습니다. 확대 crop은 실제 픽셀의 확대입니다.',font=TINY,fill='#222')
point_png=OUT/'weakcase_motor_reference_vs_contact_v1.png';annotated.save(point_png)
# Exact-copy six media files.
video_rows=[]
for run,tag,labeltext in CASES:
 root=P/run/'media'
 for view in ['whole_body','hands']:
  src=root/f'{view}.mp4';dst=V/f'{tag}_{view}.mp4';
  if dst.exists(): assert sha(src)==sha(dst)
  else: shutil.copyfile(src,dst)
  assert sha(src)==sha(dst)
  stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)]))['streams'][0]
  video_rows.append({'source':str(src),'source_sha256':sha(src),'destination':str(dst),'copy_sha256':sha(dst),'label':labeltext,'view':view,'ffprobe':stream})
manifest={'schema_version':1,'videos':video_rows,'scope':'native1–3 completed videos exact-copy only; re-encoding/native/training 0'}
(V/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
index='''# 영상 색인 · upper-bout axilla

## Native1 · right4_upper35

![전신 영상 · 실제 Isaac Gym native camera](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/right4_upper35_whole_body.mp4)
![손 영상 · 실제 native camera 및 비물리 6현 overlay](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/right4_upper35_hands.mp4)

## Native2 · right6_upper35

![전신 영상 · 실제 Isaac Gym native camera](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/right6_upper35_whole_body.mp4)
![손 영상 · 실제 native camera 및 비물리 6현 overlay](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/right6_upper35_hands.mp4)

## Native3 · right6_gentle_press

![전신 영상 · 실제 Isaac Gym native camera](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/right6_gentle_press_whole_body.mp4)
![손 영상 · 실제 native camera 및 비물리 6현 overlay](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/right6_gentle_press_hands.mp4)

- [6개 영상 source/copy SHA·ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/manifest_v1.json)
'''
(V/'INDEX_V1.md').write_text(index)
readme='''# Upper-bout axilla · native1–3 결과

세 조건 모두 실제 native 5초 완료이며 source v5 geometry 후보를 유지했습니다. root/lower body 고정, strap OFF, 기타 자유, left grip 없음, 기타에 직접 힘 없음입니다. Native1/2는 source right-bout geometry 조건에서 기존 forearm control과 upper-arm motor-point reference를 사용했고, native3은 upper-point effort를 gentle press로 변경했습니다. 여러 controller·기하·몸통 조건이 함께 달라졌으므로 차이를 한 설정의 단독 효과로 귀속하지 않습니다. Full native initial states는 native2/native3 exact match이고 세 조건 guitar initial pose는 같았습니다.

![세 실제 native의 0·2·5초 전신 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/native_timeline_0_2_5s.png)

![Weak-case native3에서 R_Shoulder motor-reference와 t=5 실제 contact feature의 주석 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/weakcase_motor_reference_vs_contact_v1.png)

| 관측값 | native1 · Chest4° / upper35 | native2 · Chest6° / upper35 | native3 · Chest6° / gentle press |
|---|---:|---:|---:|
| 최종 body-bbox 중심 이동 | 303.680 mm | 234.261 mm | 59.465 mm |
| 초기 대비 전체 SO(3) 회전 | 113.813° | 82.276° | 53.935° |
| 최종 neck G+Y elevation | 63.971° | 56.665° | −13.709° |
| R_Shoulder contact endpoints | 135/1200 | 180/1200 | 1075/1200 |
| Head contact endpoints | 796/1200 | 728/1200 | 0/1200 |
| 왼팔·손 contact endpoints | 0/1200 | 0/1200 | 0/1200 |

모든 contact endpoint 수는 240 Hz after-physics query 1200개 기준입니다. Contact/raw lambda는 측정된 힘이 아닙니다. Native3의 2→5초 body 중심 변화는 0.132568 mm, 전체 회전 변화는 0.066829°로 작지만 이미 자세가 크게 바뀐 뒤 정착한 것이므로 초기 자세 유지 성공을 뜻하지 않습니다.

![Weak-case 표시의 뜻](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/weakcase_motor_reference_vs_contact_v1.png)

Weak-case 표시의 노란 점은 R_Shoulder body state와 axilla motor-reference local 좌표를 합성한 shoulder-side 35% 사람 관절 motor-reference 위치입니다. 파란 점은 native3 step1200에서 positive raw lambda가 기록된 실제 R_Shoulder–guitar contact feature입니다. 둘은 t=5에서 33.76 mm 떨어져 있지만 이 수치는 motor-reference와 contact feature 사이의 거리일 뿐 shoulder capsule gap/상완 지지 여부를 나타내지 않습니다. 확대 crop과 화살표는 표시용 사후 주석이며 depth-tested가 아니고 physics를 바꾸지 않습니다. Contact-region 검사에서는 shoulder-side 35%와 upper-bulge 규정 영역의 접촉이 세 조건 모두 0/1200으로 분류됐습니다. 접촉 feature가 있다고 해서 지정된 지지점이라 단정하지 않습니다.

이전 body-side/native2 upper-press baseline도 upper-arm any-contact 256/1200이었지만 source-qualified proximal contact는 0/1200이었습니다. 총 upper-arm contact 수만으로 지정한 겨드랑이 지지를 확인할 수 없습니다.

영상은 151프레임·30fps, encoded duration 5.033333초이며 physics 구간은 5.0초입니다. [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/INDEX_V1.md) · [source/copy SHA·ffprobe](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/manifest_v1.json)

- [결과 summary](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/result_summary_v2.json)
- [contact-region record](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/contact_region_v2.json)
- [verification native1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analysis_v1/verification.json) · [native2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analysis_v2/verification.json) · [native3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analysis_v3/verification.json)
'''
(OUT/'README_V1.md').write_text(readme)
# Verify source inputs and camera projections before recording provenance.
after={k:snap(k) for k in before if k!=str(Path(__file__))};after[str(Path(__file__))]=snap(__file__);assert before==after
changed='''# 변경 파일 색인

- [README_V1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/README_V1.md:1) — 한국어 조건·해석·근거
- [native_timeline_0_2_5s.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/native_timeline_0_2_5s.png) — 실제 세 native × 0·2·5초
- [weakcase_motor_reference_vs_contact_v1.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/weakcase_motor_reference_vs_contact_v1.png) — 실제 이미지와 투영점 주석
- [provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/provenance_v1.json:1) — 입력 전후/출력 SHA
- [build_archive_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/build_archive_v1.py:1) — 후처리 producer
- [INDEX_V1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/INDEX_V1.md:1) — 6개 영상 색인
- [manifest_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/manifest_v1.json:1) — source/copy SHA와 ffprobe
'''
(OUT/'CHANGED_FILES.md').write_text(changed)
outputs=[OUT/'README_V1.md',OUT/'CHANGED_FILES.md',OUT/'native_timeline_0_2_5s.png',OUT/'weakcase_motor_reference_vs_contact_v1.png',V/'INDEX_V1.md',V/'manifest_v1.json']+[Path(r['destination']) for r in video_rows]
outmeta={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs}
prov={'schema_version':1,'scope':'확정 native1–3 영상/캡처 사후 문서화 및 실제 데이터 주석; native/training/re-encoding 0회','inputs_before':before,'inputs_after':after,'input_hashes_unchanged':before==after,'font_sha256':sha(FONT_PATH),'producer_sha256':sha(__file__),'video_copies':video_rows,'weakcase_markers':{'source_image_t0':str(weak/'media/frames/whole_body/00000.png'),'source_image_t5':str(weak/'media/frames/whole_body/00150.png'),'yellow_t0_motor_reference_W_m':yellow0,'yellow_t5_motor_reference_W_m':yellow5,'blue_t5_contact_feature_W_m':blue_w,'projection_t0_px':{'yellow':project(yellow0,cap['frames'][0]['cameras']['whole_body'],1280,720)[0]},'projection_t5_px':{'yellow':project(yellow5,cap['frames'][150]['cameras']['whole_body'],1280,720)[0],'blue':project(blue_w,cap['frames'][150]['cameras']['whole_body'],1280,720)[0]},'motor_reference_to_contact_feature_distance_mm':distance_mm,'annotation_depth_tested':False},'outputs_sha256_bytes':outmeta,'self_hash_note':'provenance 파일 자체의 SHA는 포함하지 않습니다.'}
(OUT/'provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'videos':len(video_rows),'exact':all(x['source_sha256']==x['copy_sha256'] for x in video_rows),'inputs_unchanged':before==after,'marker_distance_mm':distance_mm,'outputs':outmeta,'producer_sha':sha(__file__),'provenance_sha':sha(OUT/'provenance_v1.json')},ensure_ascii=False,indent=2))
