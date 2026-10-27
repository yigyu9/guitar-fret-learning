from pathlib import Path
import hashlib,json,subprocess,shutil
from PIL import Image,ImageDraw,ImageFont
D=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2');P=D/'results/shoulder_forward_v1';A=P/'artifacts_v1';V=D/'video/shoulder_forward_v1'
BASE=D/'results/upright_neckward_pose_v1/native_v6/static_neckyaw19'
R20=P/'native_v1/shoulder_forward20mm';R10=P/'native_v2/shoulder_forward10mm'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def snap(p):return {'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
def probe(p):
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(p)],text=True))['streams'][0]
 return {k:d.get(k) for k in ('width','height','avg_frame_rate','nb_read_frames','duration')}
inputs=[FONT,P/'result_summary_v2.json',P/'search_v2/shoulder_forward10mm/candidate.json',P/'search_v2/shoulder_forward20mm/candidate.json',P/'analysis_v1/shoulder_forward20mm/verification.json',P/'analysis_v2/shoulder_forward10mm/verification.json',P/'contact_region_v2.json',P/'native_v1/shoulder_forward20mm/report.json',P/'native_v1/shoulder_forward20mm/initial_values.json',P/'native_v1/shoulder_forward20mm/trace.json',P/'native_v2/shoulder_forward10mm/report.json',P/'native_v2/shoulder_forward10mm/initial_values.json',P/'native_v2/shoulder_forward10mm/trace.json',BASE/'report.json',BASE/'initial_values.json',BASE/'trace.json',BASE/'media/physics_endpoint_contacts.json']
for run in (BASE,R20,R10):
 inputs += [run/'media/capture.json',run/'media/videos.json']
 for sec in (0,150):inputs += [run/'media/frames/whole_body'/f'{sec:05d}.png']
 for view in ('whole_body','hands'):inputs += [run/'media'/f'{view}.mp4']
inputs=list(dict.fromkeys(inputs));before={str(p):snap(p) for p in inputs}

cases=[('baseline',BASE,'기준 · 19° neckward'),('native1',R20,'상완 전방 target 20 mm'),('native2',R10,'상완 전방 target 10 mm')]
rows=[]
for key,run,label in cases:
 for view in ('whole_body','hands'):
  src=run/'media'/f'{view}.mp4';dst=V/key/f'{view}.mp4';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst)
  q=probe(dst);assert q['nb_read_frames']=='151' and q['avg_frame_rate']=='30/1'
  rows.append({'case':key,'label':label,'view':view,'source':str(src),'source_sha256':sha(src),'destination':str(dst),'copy_sha256':sha(dst),'bytes':dst.stat().st_size,'ffprobe':q})

font=ImageFont.truetype(str(FONT),22)
# Paired actual whole-body frames, same camera, exact source frame payloads.
frames=[('00000',0),('00150',5)]
ims={}
for key,run,label in cases:
 if key=='native1':continue
 for frame,_ in frames: ims[(key,frame)]=Image.open(run/'media/frames/whole_body'/(frame+'.png')).convert('RGB')
baseimg=ims[('baseline','00000')]; w,h=baseimg.size; band=48;gap=10
whole=Image.new('RGB',(2*w+gap,2*(h+band)),(248,248,248));dr=ImageDraw.Draw(whole)
for col,(key,name) in enumerate([('baseline','기준 자세'),('native2','새 추천 10 mm')]):
 x=col*(w+gap)
 for row,(frame,t) in enumerate(frames):
  y=row*(h+band)+band; whole.paste(ims[(key,frame)],(x,y));dr.text((x+10,row*(h+band)+9),f'{name} · {t}초 native',font=font,fill=(15,15,15))
whole_path=A/'baseline_vs_forward10_wholebody_timeline.png';whole.save(whole_path)
# Same-camera 2D crop from the actual whole-body frames; crop is an enlargement, not a new camera.
crop_box=(430,150,840,465);cw,ch=crop_box[2]-crop_box[0],crop_box[3]-crop_box[1]
crop=Image.new('RGB',(2*cw+gap,2*(ch+band)),(248,248,248));dr=ImageDraw.Draw(crop)
for col,(key,name) in enumerate([('baseline','기준 · 어깨/팔 crop'),('native2','10 mm · 어깨/팔 crop')]):
 x=col*(cw+gap)
 for row,(frame,t) in enumerate(frames):
  y=row*(ch+band)+band; img=ims[(key,frame)].crop(crop_box);crop.paste(img,(x,y));dr.text((x+8,row*(ch+band)+8),f'{name} · {t}초',font=font,fill=(15,15,15))
crop_path=A/'baseline_vs_forward10_shoulder_crop.png';crop.save(crop_path)

# Side-by-side derivative of whole-body originals. Both original clips are retained above.
derived=V/'baseline_vs_forward10_side_by_side.mp4'
cmd=['ffmpeg','-nostdin','-y','-loglevel','error','-i',str(BASE/'media/whole_body.mp4'),'-i',str(R10/'media/whole_body.mp4'),'-filter_complex',"[0:v]scale=960:540:flags=lanczos,drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='기준 · neckward 19°':fontcolor=white:fontsize=23:box=1:boxcolor=black@0.6:x=18:y=14[a];[1:v]scale=960:540:flags=lanczos,drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text='상완 전방 target 10 mm':fontcolor=white:fontsize=23:box=1:boxcolor=black@0.6:x=18:y=14[b];[a][b]hstack=inputs=2[v]",'-map','[v]','-frames:v','151','-c:v','libx264','-pix_fmt','yuv420p','-crf','20',str(derived)]
subprocess.run(cmd,check=True)

# Document source/output metadata.
manifest=V/'manifest_v1.json';manifest.write_text(json.dumps({'videos':rows},ensure_ascii=False,indent=2)+'\n')
index=['# 어깨 전방 배치 · 영상 색인','', '실제 native 원본 영상 6개를 재인코딩 없이 복사했습니다. 원본·사본 SHA-256 및 ffprobe 정보는 [manifest](%s)에 기록했습니다.'%str(manifest)]
for key,run,label in cases:
 index+=['',f'## {key} · {label}']
 for row in rows:
  if row['case']==key:index += [f"- {row['view']}: [{label}]({row['destination']}) — {row['ffprobe']['nb_read_frames']} frames, {row['ffprobe']['avg_frame_rate']}, encoded {row['ffprobe']['duration']} s"]
index += ['',f'- 비교용 파생 영상: [{derived.name}]({derived})']
(V/'INDEX_V1.md').write_text('\n'.join(index)+'\n')

readme='''# 오른쪽 어깨·팔의 전방 배치 비교\n\n오른쪽 어깨를 조금 앞으로 옮기려는 요청에 대해, baseline과 shoulder target 20 mm / 10 mm 조건을 실제 native 5초 진단으로 비교했습니다. 10 mm 조건을 현재 후보로 권합니다. 이 비교는 자연스러운 연주자세나 반복·장기 안정성을 인증하지 않습니다.\n\n## 실제 native 캡처\n\n![기준 자세와 10 mm 후보의 실제 native whole-body 초기/5초 프레임]({whole})\n\n![같은 whole-body 원본 이미지에서 자른 어깨·팔 확대 crop. 새 카메라 시점이 아님]({crop})\n\n어깨·팔 그림은 실제 native whole-body frame을 같은 좌표 범위로 잘라 확대한 2D crop입니다. 겹침·가림을 물리 관통 판정으로 해석하지 않습니다.\n\n## 초기 target과 실제 위치는 다릅니다\n\n두 조건 모두 초기 기타 81개 q, G position/quaternion, Chest/Torso/Spine 전체 초기 상태를 baseline과 정확히 같게 유지하고 오른쪽 Shoulder의 초기 3 scalar 각도만 바꿨습니다. gain, 중력, 10 N upper-effort cap, strap OFF, left grip OFF, root/lower 고정, 기타 자유·기타 직접힘 없음 조건은 같았습니다. Source 전방 방향은 수평 world +Y이며, target displacement는 관절 scalar 각도나 실제 runtime 이동량과 동일하지 않습니다.\n\n| 조건 | 초기 elbow: baseline 대비 | 5초 elbow: baseline 대비 동시 시각 | 초기 palm: baseline 대비 | 최종 body bbox 중심 / 전체 회전 | 최대 body 중심 / 전체 회전 |\n|---|---:|---:|---:|---:|---:|\n| shoulder target 20 mm | +19.749402 mm | +20.512162 mm | +2.998498 mm | 9.402108 mm / 3.005495° | 10.232100 mm / 3.246177° |\n| shoulder target 10 mm (추천) | +9.893081 mm; world Δ[−3.984809,+9.893082,+0.374317] mm | +10.710865 mm | +1.720963 mm (최종 +2.570061 mm) | 9.425103 mm / 2.887575° | 10.455249 mm / 3.343712° |\n\n20 mm 조건은 최종 전체회전 3° 기준을 넘어 선택하지 않았습니다. 10 mm 결과는 최종 전체회전 2.887575°였고 최대는 3.343712°입니다. 최대 변화와 최종값은 별도 값입니다. elbow 이동과 palm 이동을 구분합니다.\n\n## 접촉과 범위\n\n두 조건은 각각 5초/1200 physics step/300 control step, 영상 151 frames/30 fps/5.033333초로 완료했습니다. 10 mm의 late upper contact는 120/120, total upper 1173/1200, R_Hip1194/1200; head/left/right distal은0입니다. strict 35%+upper-rim contact는1062/1200입니다. 20 mm의 late upper 120/120, total upper1178/1200, R_Hip1195/1200; head/left/distal0, strict region1102/1200입니다. 접촉 표본·raw lambda는 힘 크기나 해부학적 지지의 인증이 아닙니다. 이는 움직임이 없는 5초 native 진단이며 별도 elbow motion, 학습, 음악 평가는 하지 않았습니다.\n\n![기준 whole-body 영상과 10 mm whole-body 영상의 side-by-side 파생 비교]({derived})\n\n개별 원본 전신·손 영상은 [색인]({index})에서 확인할 수 있습니다. 자세/조건 숫자는 [검증 요약]({summary}), [20 mm verification]({verify20}), [10 mm verification]({verify10}), [contact region 분석]({contacts})에 연결했습니다. Source geometry 겹침 검사는 PhysX cooked clearance 인증이 아닙니다.\n'''.format(whole=str(whole_path),crop=str(crop_path),derived=str(derived),index=str(V/'INDEX_V1.md'),summary=str(P/'result_summary_v2.json'),verify20=str(P/'analysis_v1/shoulder_forward20mm/verification.json'),verify10=str(P/'analysis_v2/shoulder_forward10mm/verification.json'),contacts=str(P/'contact_region_v2.json'))
readme_path=A/'README_V1.md';readme_path.write_text(readme)

# Guard source inputs and record full provenance.
after={str(p):snap(p) for p in inputs};assert before==after
prov={'task':'shoulder_forward native archive, actual-frame comparisons and Korean explanation','physics_or_training_runs':0,'exact_video_copies':len(rows),'derived_video_reencodes':1,
 'inputs_before_after':{str(p):{'before':before[str(p)],'after':after[str(p)],'unchanged':before[str(p)]==after[str(p)]} for p in inputs},
 'producer':{'path':str(A/'build_archive_v1.py'),'sha256':sha(A/'build_archive_v1.py'),'bytes':(A/'build_archive_v1.py').stat().st_size},
 'font':{'path':str(FONT),'sha256':sha(FONT)},
 'outputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in [whole_path,crop_path,derived,manifest,V/'INDEX_V1.md',readme_path]},
 'exact_copies':rows,'derived_video_command':cmd,'crop_box_pixels_xyxy':crop_box}
(A/'provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
