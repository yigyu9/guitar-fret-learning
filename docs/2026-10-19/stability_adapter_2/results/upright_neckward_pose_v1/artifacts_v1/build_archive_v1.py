from pathlib import Path
import hashlib, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont

D=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2')
P=D/'results/upright_neckward_pose_v1'
OLD=D/'results/neckward_torso_turn_v1/native_v1/static_neckyaw12'
A=P/'artifacts_v1'; V=D/'video/upright_neckward_pose_v1'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
CASES=[(f'native_v{i}',next((P/f'native_v{i}').iterdir())) for i in range(1,7)]
SOURCES=[('old12',OLD,'기존 기준 · 몸통 neckward yaw 12°')]
SOURCES += [(p.name,p,p.name) for i,p in CASES]

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def snapshot(p):return {'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
def probe(path):
 out=subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(path)],text=True)
 s=json.loads(out)['streams'][0]
 return {k:s.get(k) for k in ('width','height','avg_frame_rate','nb_read_frames','duration')}

# Pin inputs before reading/copying; do not inspect native_v7 (still running).
input_paths=[FONT,P/'torso_posture_v6.json',P/'search_v2/search.json',OLD/'report.json',OLD/'trace.json',OLD/'initial_values.json']
for _,run,_ in SOURCES[1:]:
 input_paths += [run/'report.json',run/'trace.json',run/'initial_values.json',run/'media/capture.json',run/'media/frames/whole_body/00000.png',run/'media/frames/whole_body/00150.png']
input_paths += [OLD/'media/capture.json',OLD/'media/frames/whole_body/00000.png',OLD/'media/frames/whole_body/00150.png']
input_paths=list(dict.fromkeys(input_paths))
before={str(p):snapshot(p) for p in input_paths}

manifest=[]
for key,run,label in SOURCES:
 media=run/'media'
 for view in ('whole_body','hands'):
  src=media/f'{view}.mp4'
  destdir=V/('previous_reference' if key=='old12' else key)
  destdir.mkdir(parents=True,exist_ok=True)
  dst=destdir/f'{view}.mp4'
  shutil.copyfile(src,dst)
  assert sha(src)==sha(dst)
  pr=probe(dst)
  manifest.append({'case':key,'label':label,'view':view,'source':str(src),'source_sha256':sha(src),'destination':str(dst),'copy_sha256':sha(dst),'bytes':dst.stat().st_size,'ffprobe':pr})

# Side-by-side native frame comparison: same recorded camera type, actual frames.
font=ImageFont.truetype(str(FONT),25)
small=ImageFont.truetype(str(FONT),20)
old0=Image.open(OLD/'media/frames/whole_body/00000.png').convert('RGB')
newrun=dict(CASES)['native_v6']
new0=Image.open(newrun/'media/frames/whole_body/00000.png').convert('RGB')
old5=Image.open(OLD/'media/frames/whole_body/00150.png').convert('RGB')
new5=Image.open(newrun/'media/frames/whole_body/00150.png').convert('RGB')
assert old0.size==new0.size==old5.size==new5.size
w,h=old0.size; header=74; gap=12
canvas=Image.new('RGB',(2*w+gap,2*h+header*2+gap),(248,248,248)); draw=ImageDraw.Draw(canvas)
for col,(label,img) in enumerate([('기존 기준 · torso yaw 12°',old0),('새 조건 · torso yaw 19°',new0)]):
 x=col*(w+gap); draw.text((x+12,8),label,font=font,fill=(20,20,20)); canvas.paste(img,(x,header))
for col,(label,img) in enumerate([('기존 기준 · 5.0초',old5),('새 조건 · 5.0초',new5)]):
 x=col*(w+gap); y=header+h+gap+header; draw.text((x+12,header+h+gap+8),label,font=font,fill=(20,20,20)); canvas.paste(img,(x,y))
image=A/'native12_vs_native19_initial_and_5s.png'; canvas.save(image)

# Derived comparison video, deliberately distinct from exact-copy sources.
derived=V/'static12_vs_static19_whole_body_side_by_side.mp4'
cmd=['ffmpeg','-nostdin','-y','-loglevel','error','-i',str(OLD/'media/whole_body.mp4'),'-i',str(newrun/'media/whole_body.mp4'),'-filter_complex','[0:v]scale=960:540:flags=lanczos,drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text=\'기존 기준 · torso yaw 12°\':fontcolor=white:fontsize=25:box=1:boxcolor=black@0.55:x=20:y=18[a];[1:v]scale=960:540:flags=lanczos,drawtext=fontfile=/usr/share/fonts/truetype/nanum/NanumGothic.ttf:text=\'새 조건 · torso yaw 19°\':fontcolor=white:fontsize=25:box=1:boxcolor=black@0.55:x=20:y=18[b];[a][b]hstack=inputs=2[v]','-map','[v]','-frames:v','151','-c:v','libx264','-pix_fmt','yuv420p','-crf','20',str(derived)]
subprocess.run(cmd,check=True)

# No source input may have changed while packaging.
after={str(p):snapshot(p) for p in input_paths}
assert before==after
(A/'manifest_v1.json').write_text(json.dumps({'videos':manifest},ensure_ascii=False,indent=2)+'\n')
index=['# Upright neckward pose · 영상 색인','', '원본 14개 영상은 재인코딩 없이 복사했습니다. 각 원본/사본 경로와 SHA-256, ffprobe 결과는 [manifest](%s)에 있습니다.'%str(A/'manifest_v1.json'),'','## 이전 기준']
index += [f"- {m['view']}: [{m['label']}]({m['destination']}) — {m['ffprobe']['nb_read_frames']} frames, {m['ffprobe']['avg_frame_rate']}" for m in manifest if m['case']=='old12']
for i,run in CASES:
 index += ['',f'## {run.name} · {run.name}']
 index += [f"- {m['view']}: [{m['label']}]({m['destination']}) — {m['ffprobe']['nb_read_frames']} frames, {m['ffprobe']['avg_frame_rate']}" for m in manifest if m['case']==run.name]
(V/'INDEX_V1.md').write_text('\n'.join(index)+'\n')

readme='''# Upright neckward pose · 초기/정지 비교 자료\n\n이 보관본은 이전 neckward torso yaw 12° native와 완료된 native 1–6의 whole-body/hands 영상 14개를 원본 바이트 그대로 보존합니다. 각 source/copy SHA와 ffprobe는 manifest에서 확인할 수 있습니다. native7은 별도 실행 중이므로 이 문서와 보관 범위에는 포함하지 않았습니다.\n\n![이전 12° 기준과 새 19° 조건의 실제 native 초기 및 5초 프레임 비교]({image})\n\n위 그림은 기존 native12와 native6/static_neckyaw19의 실제 0초·5초 whole-body 캡처입니다. 두 실행은 같은 camera 종류를 사용하지만 초기 조건 및 torso posture 목표가 달라 정성적 비교이며 동일 초기상태 반복 비교는 아닙니다. G 초기 quaternion은 유지됩니다. Source yaw 목표, native Chest heading, actor/G 전체회전은 서로 다른 양입니다.\n\n![이전 12° 기준과 새 19°의 전체 native 영상 비교 파생물]({derived})\n\n이 side-by-side 파일은 위 두 원본 whole-body 영상에서 만든 시각 비교용 파생물입니다. 원본 영상은 손대지 않았습니다. 개별 원본은 [영상 색인]({index})에서 확인할 수 있습니다.\n\n현재 승인된 정지 후보 기준: native6/static_neckyaw19의 actual forward inclination 39.846996° (이전 48.347770°), heading 27.986843° (이전 22.198890°), body bbox centre 9.548665 mm, whole actor rotation 2.995398°. Actor-root 이동 25.911055 mm는 bbox-centre 이동과 별도입니다. 최대 body-centre 이동 10.380810 mm, 최대 whole rotation 3.313974°. 접촉 표본은 upper 1173/1200, late upper 120/120, R_Hip1194/1200, head/left/distal0으로 요약됐습니다. 회전 gate 여유가 작아 반복 강건성은 미확인입니다. 이 한 차례 5초 정지 시험은 음악 성공, 자연스러움, 동작 중 유지, 반복성을 검증하지 않습니다.\n\n이 자료는 source/native/actor-root/G 회전을 혼동하지 않으며, source 기하 검사는 PhysX cooked clearance 인증이 아닙니다. Strap OFF, left grip OFF, root/lower fixed, guitar free, guitar에 직접 힘 없음이라는 phase 조건 아래에서 수행됐습니다. 세부 결과는 [phase README]({phase_readme})에서 확인합니다.\n'''.format(image=str(image),derived=str(derived),index=str(V/'INDEX_V1.md'),phase_readme=str(P/'analysis_v6/static_neckyaw19/verification.json'))
(A/'README_DRAFT_V1.md').write_text(readme)

# Provenance records producer source and all unchanged inputs; outputs are pinned after generation.
prov={'task':'upright neckward pose V1 archival and static comparison','native_runs_started':0,'training_runs':0,'exact_video_copies':len(manifest),'derived_video_reencodes':1,
 'inputs_before_after':{str(p):{'before':before[str(p)],'after':after[str(p)],'unchanged':before[str(p)]==after[str(p)]} for p in input_paths},
 'producer':{'path':str(A/'build_archive_v1.py'),'sha256':sha(A/'build_archive_v1.py'),'bytes':(A/'build_archive_v1.py').stat().st_size},
 'outputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in [image,derived,A/'manifest_v1.json',V/'INDEX_V1.md',A/'README_DRAFT_V1.md']},
 'exact_copies':manifest,'derived_video_command':cmd}
(A/'provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
