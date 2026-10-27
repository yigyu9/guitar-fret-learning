from pathlib import Path
import hashlib,json,subprocess,shutil
from PIL import Image
D=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2')
P=D/'results/upright_neckward_pose_v1'; A=P/'artifacts_v1'; V=D/'video/upright_neckward_pose_v1'
RUN7=P/'native_v7/elbow_neckyaw19'; RUN6=P/'native_v6/static_neckyaw19'
OLD=D/'results/neckward_torso_turn_v1/native_v1/static_neckyaw12'
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

# The 14 V1 copies and their metadata remain untouched. Copy only the new run's two exact MP4s.
input_paths=[A/'build_archive_v1.py',A/'README_DRAFT_V1.md',A/'manifest_v1.json',A/'provenance_v1.json',V/'INDEX_V1.md',
             RUN7/'report.json',RUN7/'trace.json',RUN7/'initial_values.json',RUN7/'media/videos.json',RUN7/'media/capture.json',
             RUN7/'media/whole_body.mp4',RUN7/'media/hands.mp4',RUN7/'media/frames/whole_body/00000.png',RUN7/'media/frames/whole_body/00150.png',
             RUN6/'report.json',RUN6/'trace.json',RUN6/'initial_values.json',RUN6/'media/capture.json',RUN6/'media/frames/whole_body/00000.png',RUN6/'media/frames/whole_body/00150.png',
             OLD/'report.json',OLD/'trace.json',OLD/'initial_values.json',OLD/'media/whole_body.mp4',OLD/'media/hands.mp4',
             P/'analysis_v7/elbow_neckyaw19/verification.json',P/'elbow_comparison_v1.json',P/'elbow_comparison_trace_v1.json',
             P/'contact_region_v1.json',D/'results/neckward_torso_turn_v1/contact_region_v1.json',P/'torso_posture_v7.json',P/'analysis_v6/static_neckyaw19/verification.json',FONT]
input_paths=list(dict.fromkeys(input_paths)); before={str(p):snap(p) for p in input_paths}

rows=json.loads((A/'manifest_v1.json').read_text())['videos']
assert len(rows)==14 and all(x['source_sha256']==x['copy_sha256'] for x in rows)
newrows=[]
for view in ('whole_body','hands'):
 src=RUN7/'media'/f'{view}.mp4'; dest=V/'native_v7'/f'{view}.mp4'; dest.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(src,dest); assert sha(src)==sha(dest)
 q=probe(dest); assert q['nb_read_frames']=='151' and q['avg_frame_rate']=='30/1'
 newrows.append({'case':'elbow_neckyaw19','label':'native7 · torso neckward 정지 + elbow 작은 동작','view':view,
  'source':str(src),'source_sha256':sha(src),'destination':str(dest),'copy_sha256':sha(dest),'bytes':dest.stat().st_size,'ffprobe':q})
allrows=rows+newrows
manifest=V/'manifest_v2.json'; manifest.write_text(json.dumps({'videos':allrows},ensure_ascii=False,indent=2)+'\n')

# Actual same-camera frames: static 19° and its same-initial-state moving diagnostic.
font_path=str(FONT)
from PIL import ImageDraw,ImageFont
font=ImageFont.truetype(font_path,24)
imgs=[]
for run in [RUN6,RUN7]:
 imgs.append([Image.open(run/'media/frames/whole_body'/f'{frame:05d}.png').convert('RGB') for frame in (0,60,150)])
assert all(imgs[0][j].size==imgs[1][j].size for j in range(3))
w,h=imgs[0][0].size; band=48; gap=10; top=50
out=Image.new('RGB',(2*w+gap,top+3*(h+band)),(248,248,248)); draw=ImageDraw.Draw(out)
for col,name in enumerate(('정지 native6 · 19°','elbow-motion native7 · 19°')):
 x=col*(w+gap);draw.text((x+12,10),name,font=font,fill=(18,18,18))
for row,(j,t) in enumerate(zip(range(3),(0,2,5))):
 y=top+row*(h+band)+band
 for col in range(2):
  x=col*(w+gap);out.paste(imgs[col][j],(x,y))
  draw.text((x+12,top+row*(h+band)+8),f'{t}.0초 native 캡처',font=font,fill=(18,18,18))
image=A/'native19_static_vs_elbow_timeline_v2.png';out.save(image)

# Hash every input after processing; source assets must remain unchanged.
after={str(p):snap(p) for p in input_paths}; assert before==after

# Final concise Korean document, with explicit distinctions between source goal, world posture and actor/G pose.
readme='''# Upright neckward pose · 정지 후보 및 작은 동작 진단\n\n새 초기자세 후보는 native6의 torso neckward yaw source goal 19°입니다. 이전 12° 기준의 실제 native 초기/5초 장면은 아래 그림에 포함되어 있습니다. native1–6 및 이전 기준의 전신·손 영상 14개는 먼저 byte-exact 보관했고, 완료된 native7 전신·손 영상 2개도 동일 방식으로 추가해 총 16개를 [manifest V2]({manifest})와 [색인 V2]({index})에 기록했습니다. V1 manifest/index/provenance는 보존했습니다.\n\n![이전 12° 기준과 새 19° static의 초기 및 5초 실제 native 프레임]({initial})\n\n이전 12°와 새 19° 사이의 실제 native 정지 whole-body 비교 영상(파생 side-by-side):\n\n![정지 비교 영상]({staticvideo})\n\n## 정지 후보의 실제 자세 및 gate\n\n새 native6/static_neckyaw19에서 실제 Chest–Neck world 기준 forward inclination은 39.846996°였고, 이전 native neckward12°의 48.347770°보다 8.500774° 작았습니다. 실제 world heading(+Y에서 −X)은 27.986843°(이전 22.198890°), source yaw goal은 19°입니다. 기타 quaternion은 초기값을 유지했습니다. Source yaw, Chest heading, 전체 actor/G 회전은 다른 양입니다.\n\n정지 종료에서 기타 body bounding-box 중심 이동은 9.548665 mm, root actor 이동은 25.911055 mm, 전체 SO(3) 회전은 2.995398°였습니다. 최대치는 body 중심 10.380810 mm, 전체 회전 3.313974°로 회전 gate를 작은 여유로 통과했습니다. 상완 접촉은 1173/1200이고 후기 구간 120/120, R_Hip 1194/1200; head/left/distal은 0이었습니다. 5초 한 번의 정지 시험이며 반복 강건성은 확인하지 않았습니다.\n\n## 같은 초기값의 작은 elbow-motion 진단\n\n![새 19° static과 elbow-motion의 실제 native 0·2·5초 프레임]({timeline})\n\n![native7 실제 elbow-motion 전신 영상]({motionvideo})\n\nNative6 정지와 native7 motion은 같은 초기 상태이며 2.5초까지 trace가 exact하게 같습니다. 작은 동작 구간은 2.5–4.5초의 단일 R_Elbow_y scalar target입니다. Actor world rotation 축이 아닙니다. 실제 moving q 절대 왕복은 10.094022°, 정지 대비 incremental 응답은 10.092677°였습니다(상관 0.999946426, incremental RMSE 0.048328°, absolute target RMSE 0.098600°). 정지 대비 기타 추가 최대차는 중심 0.077660 mm, 전체 회전 0.042115°이며 종료 차이는 0.041240 mm / 0.042115°입니다.\n\n정지 및 motion의 strict 35%+upper-rim 분류는 1117/1200이며, motion raw-positive 표본은 1113/1200입니다. 이전 native12 strict-region은 0/1200이었습니다. 이 분류는 겨드랑이 해부학적 지지나 힘 분담의 인증이 아니며, raw lambda는 힘 단위가 아닙니다. 이 5초 작은 동작 진단은 음악 연주, 장시간 유지, 자연스러움 또는 반복성을 검증하지 않습니다.\n\n## 실행 및 해석 범위\n\n각 native 1–7 실행은 5.0초/1200 physics step/300 control step, 영상 151 frames/30 fps/5.033333초였습니다. 이 영상은 멈춰있는 마지막 프레임의 반복이 아니라 실제 5초 계산 결과입니다. Strap OFF, left grip OFF, root/lower fixed, guitar free, guitar direct force 없음 조건입니다. 실패한 26°/30° 및 follow 진단들도 영상 색인에 원형 그대로 남겼으며, 최종 후보로 표시하지 않습니다. Source/초기 overlap 검사는 PhysX cooked clearance 인증과 다릅니다.\n\n이번 선택은 19° 정지 초기자세의 단일 gate 통과와 별도의 작은 동작 진단에 한정됩니다. 연주·장기 안정·반복 성공은 미확인입니다. [정지 19° 검증]({staticverify}) · [elbow motion 비교자료]({elbowcmp}) · [실제 Chest–Neck 자세 trace]({posture}) · [새 조건 실제 접촉영역 분류]({contact}) · [이전 12° 실제 접촉영역 분류]({oldcontact})\n'''.format(manifest=str(manifest),index=str(V/'INDEX_V2.md'),initial=str(A/'native12_vs_native19_initial_and_5s.png'),staticvideo=str(V/'static12_vs_static19_whole_body_side_by_side.mp4'),timeline=str(image),motionvideo=str(V/'native_v7/whole_body.mp4'),staticverify=str(P/'analysis_v6/static_neckyaw19/verification.json'),elbowcmp=str(P/'elbow_comparison_v1.json'),posture=str(P/'torso_posture_v7.json'),contact=str(P/'contact_region_v1.json'),oldcontact=str(D/'results/neckward_torso_turn_v1/contact_region_v1.json'))
readme_path=A/'README_V1.md';readme_path.write_text(readme)

idx=['# Upright neckward pose · 16개 원본 영상 색인','', '원본 16개 영상은 재인코딩 없이 복사했습니다. 각 영상은 151 frames, 30/1 fps, encoded duration 5.033333초입니다. 각 native physics 구간은 5.0초입니다. 원본/사본 SHA, bytes, ffprobe는 [manifest V2](%s)에 있습니다. V1의 14개 복사본은 보존했고 native7 영상 2개를 더했습니다.'%str(manifest)]
for case in ['old12','static_neckyaw30','static_neckyaw26','follow_neckyaw26','follow20_neckyaw26','static_neckyaw20','static_neckyaw19','elbow_neckyaw19']:
 ms=[x for x in allrows if x['case']==case]
 if not ms:continue
 idx+=['',f'## {case}']
 idx += [f"- {m['view']}: [{m['label']}]({m['destination']}) — {m['ffprobe']['nb_read_frames']} frames / {m['ffprobe']['avg_frame_rate']} / {m['ffprobe']['duration']} s" for m in ms]
(V/'INDEX_V2.md').write_text('\n'.join(idx)+'\n')

# Pin all build inputs, output hashes and completed copy mapping.
prov={'task':'upright neckward pose final media archive and Korean documentation','additional_exact_copies':2,'total_exact_video_copies':16,'new_physics_or_training_runs':0,
 'inputs_before_after':{str(p):{'before':before[str(p)],'after':after[str(p)],'unchanged':before[str(p)]==after[str(p)]} for p in input_paths},
 'producer':{'path':str(A/'build_archive_v2.py'),'sha256':sha(A/'build_archive_v2.py'),'bytes':(A/'build_archive_v2.py').stat().st_size},
 'outputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in [image,manifest,readme_path,V/'INDEX_V2.md']},
 'exact_copies_added':newrows,'all_video_manifest_rows':allrows}
(A/'provenance_v2.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
