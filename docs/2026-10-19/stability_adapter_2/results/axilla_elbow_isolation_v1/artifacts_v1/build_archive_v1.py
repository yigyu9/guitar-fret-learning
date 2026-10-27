from pathlib import Path
import hashlib, json, shutil, subprocess, os
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1')
OUT=ROOT/'artifacts_v1'
VID=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/axilla_elbow_isolation_v1')
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
CASES=[
 ('static_cradle','native_v2/static_cradle','정적 기준'),
 ('elbow_motion','native_v3/elbow_motion','팔꿈치 구동 2°'),
 ('elbow_motion5','native_v4/elbow_motion5','팔꿈치 구동 5°'),
]
TIMES=[(0,'00000.png'),(2.5,'00075.png'),(5,'00150.png')]

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''): h.update(c)
 return h.hexdigest()
def snap(p):
 p=Path(p); s=p.stat(); return {'sha256':sha(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
def run(cmd): subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def probe(p):
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,nb_read_frames,duration','-of','json',str(p)],text=True))
 return d['streams'][0]

OUT.mkdir(parents=True,exist_ok=True); VID.mkdir(parents=True,exist_ok=True)
producer=OUT/'build_archive_v1.py'
# This file is the executed producer; its digest is recorded below.

srcmedia={label:ROOT/rel/'media' for label,rel,_ in CASES}
sourcevideos=[]
frameinputs=[]
for label,_,_ in CASES:
 for view in ('whole_body','hands'):
  sourcevideos.append(srcmedia[label]/f'{view}.mp4')
  for _,fn in TIMES: frameinputs.append(srcmedia[label]/'frames'/view/fn)
records=[ROOT/'elbow_comparison_v1.json',ROOT/'elbow_comparison_v2.json',ROOT/'elbow_comparison_trace_v2.json',ROOT/'elbow_comparison_trace_v1.json',ROOT/'result_summary_v1.json',ROOT/'result_summary_v2.json',ROOT/'analysis_v3/static_cradle/verification.json',ROOT/'analysis_v4/elbow_motion/verification.json',ROOT/'analysis_v5/elbow_motion5/verification.json',ROOT/'contact_region_v3.json',ROOT/'diagnostic_candidate_v1/candidate.json']
inputs=sourcevideos+frameinputs+records+[producer,FONT,Path('/usr/bin/ffmpeg'),Path('/usr/bin/ffprobe')]
inputs=[p for p in inputs if p.exists()]
before={str(p):snap(p) for p in inputs}

# Copy native whole-body and hands videos byte-for-byte.
video_rows=[]
for label,rel,case_title in CASES:
 for view in ('whole_body','hands'):
  src=srcmedia[label]/f'{view}.mp4'
  dst=VID/f'{label}_{view}.mp4'
  shutil.copyfile(src,dst)
  if sha(src)!=sha(dst): raise RuntimeError(f'copy hash mismatch: {src}')
  stream=probe(dst)
  if stream.get('nb_read_frames')!='151' or stream.get('avg_frame_rate')!='30/1': raise RuntimeError(f'unexpected stream: {stream}')
  video_rows.append({'label':case_title,'view':view,'source':str(src),'source_sha256':sha(src),'destination':str(dst),'copy_sha256':sha(dst),'ffprobe':stream})

# Frame panels use only actual Isaac Gym native captures.
font=ImageFont.truetype(str(FONT),22); small=ImageFont.truetype(str(FONT),19); titlefont=ImageFont.truetype(str(FONT),30)
def timeline(view, filename, title):
 cells=[]
 for label,rel,case_title in CASES:
  row=[]
  for t,fn in TIMES:
   im=Image.open(srcmedia[label]/'frames'/view/fn).convert('RGB')
   im.thumbnail((460,259),Image.Resampling.LANCZOS)
   row.append((im,t,case_title))
  cells.append(row)
 w=1420; pad=24; cw=460; ch=259; hh=54; rowh=340
 canvas=Image.new('RGB',(w,hh+rowh*len(cells)+20),(246,247,249)); d=ImageDraw.Draw(canvas)
 d.text((pad,10),title,font=titlefont,fill=(25,35,50))
 for r,row in enumerate(cells):
  y=hh+r*rowh
  d.text((pad,y+5),row[0][2],font=font,fill=(30,40,55))
  for c,(im,t,_) in enumerate(row):
   x=pad+c*470; yy=y+38
   canvas.paste(im,(x,yy))
   d.rectangle((x,yy,x+im.width,yy+im.height),outline=(160,165,175),width=1)
   d.text((x+6,yy+im.height+5),f'{t:g}초 · native 캡처',font=small,fill=(35,45,60))
 canvas.save(OUT/filename)
timeline('whole_body','native_whole_body_timeline.png','실제 native 전신 캡처: 0 · 2.5 · 5초')
timeline('hands','native_hands_timeline.png','실제 native 손 캡처: 0 · 2.5 · 5초')

# Trace chart: motion-minus-static elbow response and same-time guitar/body differences.
trace=json.loads((ROOT/'elbow_comparison_trace_v2.json').read_text())
plt.rcParams['font.family']='NanumGothic'
plt.rcParams['axes.unicode_minus']=False
matplotlib.font_manager.fontManager.addfont(str(FONT))
fig,axs=plt.subplots(3,1,figsize=(11,9),sharex=True,constrained_layout=True)
t=trace['time_s']
axs[0].plot(trace['physics_time_s'],trace['elbow_command_delta_deg'],label='명령 변화',linewidth=2)
axs[0].plot(trace['physics_time_s'],trace['elbow_actual_moving_minus_static_deg'],label='실제 R_Elbow_y 변화',linewidth=1.5)
axs[0].set_ylabel('각도 변화 (°)'); axs[0].legend(loc='upper left',ncol=2); axs[0].grid(alpha=.25)
axs[1].plot(t,trace['same_time_body_centre_delta_mm'],color='#c44e52',linewidth=1.8)
axs[1].set_ylabel('동시점 body-bbox\n중심 차이 (mm)'); axs[1].grid(alpha=.25)
axs[2].plot(t,trace['same_time_rotation_delta_deg'],color='#4c72b0',linewidth=1.8)
axs[2].set_ylabel('동시점 전체 SO(3)\n차이 (°)'); axs[2].set_xlabel('물리 시간 (초)'); axs[2].grid(alpha=.25)
axs[-1].set_xlim(2.5,5)
fig.suptitle('5° 명령의 native 응답과 같은 시각의 물체 차이 · 2.5–5초',fontsize=15)
chart=OUT/'elbow_5deg_response_and_body_delta.png'; fig.savefig(chart,dpi=170); plt.close(fig)

# Derived comparison video: original native streams are untouched; only this viewing aid is re-encoded.
static=VID/'static_cradle_whole_body.mp4'; motion=VID/'elbow_motion5_whole_body.mp4'; derived=OUT/'static_vs_elbow_motion5_side_by_side.mp4'
fontff=FONT.as_posix()
filtergraph=(
 f"[0:v]scale=640:360:force_original_aspect_ratio=decrease,pad=640:434:(ow-iw)/2:74:color=black,"
 f"drawtext=fontfile={fontff}:text='정적 기준':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.65:boxborderw=8:x=16:y=14[a];"
 f"[1:v]scale=640:360:force_original_aspect_ratio=decrease,pad=640:434:(ow-iw)/2:74:color=black,"
 f"drawtext=fontfile={fontff}:text='팔꿈치 R_Elbow_y · 5°':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.65:boxborderw=8:x=16:y=14,"
 f"drawtext=fontfile={fontff}:text='명령 변화 구간 2.5–4.5초':fontcolor=yellow:fontsize=19:box=1:boxcolor=black@0.55:boxborderw=6:x=16:y=43:enable='between(t,2.5,4.5)'[b];"
 f"[a][b]hstack=inputs=2[v]"
)
run(['ffmpeg','-y','-i',str(static),'-i',str(motion),'-filter_complex',filtergraph,'-map','[v]','-an','-c:v','libx264','-crf','20','-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart',str(derived)])
derived_probe=probe(derived)

# Documents and metadata.
manifest={'videos':video_rows}
(VID/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
index=['# Native 영상 색인','', '세 조건별 원본 whole-body/hands MP4를 바이트 그대로 복사했습니다. 물리 구간은 5.0초이며 각 원본 영상은 151프레임·30fps입니다.','']
for label,rel,title in CASES:
 index += [f'## {title}','',f'- [전신 MP4]({VID}/{label}_whole_body.mp4)',f'- [손 MP4]({VID}/{label}_hands.mp4)','']
index += [f'[복사 SHA-256 및 ffprobe 정보]({VID}/manifest_v1.json)','']
(VID/'INDEX_V1.md').write_text('\n'.join(index),encoding='utf-8')
readme=f'''# 겨드랑이 지지 자세: 팔꿈치 영향 격리 진단

세 native 실행(static cradle, R_Elbow_y 2° 구동, R_Elbow_y 5° 구동)은 초기 native 상태와 2.5초까지 trace가 일치합니다. 각 조건은 5초 완료, 1200 physics step입니다. strap은 OFF, 왼손 그립 없음, 기타에 직접 가한 힘 없음, root/lower body 고정입니다. 사람 상완점은 10 N cap으로 제어했고 전완점은 추가 motor force 0입니다.

![세 조건 실제 native 전신 캡처 0·2.5·5초]({OUT}/native_whole_body_timeline.png)

![세 조건 실제 native 손 캡처 0·2.5·5초]({OUT}/native_hands_timeline.png)

## 5° 구동 비교

![5도 팔꿈치 명령·실제 응답과 동시점 자세 차이]({OUT}/elbow_5deg_response_and_body_delta.png)

아래 영상은 static 기준과 5° 구동 조건의 실제 native whole-body 영상을 나란히 재생하는 파생 비교본입니다. 원본 영상은 별도로 보존했고 재인코딩하지 않았습니다. 노란 안내는 명령 변화 구간(2.5–4.5초)을 표시합니다.

![정적 기준과 팔꿈치 5도 구동 native 영상 비교]({OUT}/static_vs_elbow_motion5_side_by_side.mp4)

최종 5° 조건의 native 영상 원본도 함께 제공합니다.

![5도 팔꿈치 구동 조건 native 전신 영상]({VID}/elbow_motion5_whole_body.mp4)

| 확인 항목 | 실제 관측 |
|---|---:|
| 2° 명령 대비 elbow incremental 응답 peak-to-peak | 4.03339° |
| 5° 명령 대비 elbow incremental 응답 peak-to-peak | 10.08300° |
| 5° 조건 elbow 변화 tracking RMSE¹ | 0.042524° |
| 5° 조건 absolute moving q 대 target RMSE | 0.108712° |
| 최대 same-time body-bbox 중심 차이 | 0.027241 mm |
| 최대 same-time 전체 회전 차이 | 0.009348° |

¹ moving-minus-static 실제 scalar response와 명령 변화 간 오차입니다. 절대 moving q 대 target RMSE는 별도로 0.108712°입니다. 전신과 기타의 physics는 중간 종료 없이 각 1200 step 내내 계산됐습니다. 2.5–5초의 동시점 자세 차이는 작지만 이 결과는 작은 elbow 영향 진단 1회이며, 전체 연주 성능이나 반복성을 입증하지 않습니다. 상완 native 공간분류는 0–35% 구간에서 1171/1200 표본입니다. 이는 source 후보 목표 구간 0–30% 자체가 native 접촉으로 확인됐다는 뜻이 아니며, cooked contact 보증이나 해부학적 겨드랑이 지지 증거도 아닙니다. 오른쪽 허벅지에 해당하는 R_Hip는 1196/1200, 머리·왼팔·원위 오른팔은 0/1200 endpoint 표본입니다. raw lambda는 힘 측정값이 아닙니다.

Search의 source 2bend8 후보에는 proximal30 gap 1.313 mm, forearm 16.88 mm, thigh 0.183 mm, torso 27.511 mm로 기록됐습니다. 이는 source analytic 평가이며 PhysX cooked clearance 인증은 아닙니다. 각 영상은 151프레임·30fps(인코딩 5.033초), 물리 구간 5초입니다.

## 영상 원본

[영상 색인]({VID}/INDEX_V1.md) · [SHA-256 및 ffprobe manifest]({VID}/manifest_v1.json)

- [native 비교 요약]({ROOT}/elbow_comparison_v2.json)
- [native 비교 trace]({ROOT}/elbow_comparison_trace_v2.json)
- [native 검증: static]({ROOT}/analysis_v3/static_cradle/verification.json) · [2°]({ROOT}/analysis_v4/elbow_motion/verification.json) · [5°]({ROOT}/analysis_v5/elbow_motion5/verification.json)
'''
(OUT/'README_V1.md').write_text(readme,encoding='utf-8')

# Snapshot check and provenance.
after={str(p):snap(p) for p in inputs}
if before!=after: raise RuntimeError('source input changed during artifact generation')
outputs={}
for p in [OUT/'README_V1.md',OUT/'native_whole_body_timeline.png',OUT/'native_hands_timeline.png',chart,derived,VID/'manifest_v1.json',VID/'INDEX_V1.md']+[Path(r['destination']) for r in video_rows]:
 outputs[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
prov={'scope':'presentation, exact video copies, and derived side-by-side viewing aid; no native or training execution', 'inputs_before':before,'inputs_after':after,'producer':{str(producer):snap(producer)},'font':{str(FONT):snap(FONT)},'source_video_copy_records':video_rows,'derived_comparison_video':{'path':str(derived),'sha256':sha(derived),'ffprobe':derived_probe,'filtergraph':filtergraph},'outputs':outputs,'input_unchanged':True}
(OUT/'provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'videos':len(video_rows),'outputs':outputs,'provenance':str(OUT/'provenance_v1.json')},ensure_ascii=False))
