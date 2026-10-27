from pathlib import Path
import hashlib,json,shutil,subprocess
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1')
OLD=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/native_v2/static_cradle')
ART=ROOT/'artifacts_v1'; VID=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/neckward_torso_turn_v1')
PRODUCER=ART/'build_archive_v1.py'; FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
CASES=[('old_axilla_static',OLD,'이전 static 기준 · 다른 초기 상태'),('neck_yaw_static',ROOT/'native_v1/static_neckyaw12','새 neck-yaw static'),('neck_yaw_motion',ROOT/'native_v2/elbow_neckyaw12','새 neck-yaw + R_Elbow_y 구동')]
VIEWS=('whole_body','hands')
FRAMES=(('00000.png','0초'),('00150.png','5초'))

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def snap(p):
 p=Path(p);s=p.stat();return {'sha256':sha(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
def probe(p):
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,nb_read_frames,duration','-of','json',str(p)],text=True))
 return d['streams'][0]
def run(cmd): subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

ART.mkdir(parents=True,exist_ok=True); VID.mkdir(parents=True,exist_ok=True)
source_videos=[]; used_frames=[]
for label,folder,title in CASES:
 for view in VIEWS:
  source_videos.append(folder/'media'/f'{view}.mp4')
  if view=='whole_body':
   used_frames.extend(folder/'media'/'frames'/view/fn for fn,_ in FRAMES)
source_initial=ROOT/'native_v1/static_neckyaw12/media/initial_native.png'
old_initial=OLD/'media/initial_native.png'
inputs=[*source_videos,*used_frames,source_initial,old_initial,ROOT/'result_summary_v1.json',ROOT/'torso_posture_v2.json',ROOT/'elbow_comparison_v1.json',ROOT/'elbow_comparison_trace_v1.json',ROOT/'contact_region_v1.json',ROOT/'search_v1/search.json',ROOT/'analysis_v1/static_neckyaw12/verification.json',ROOT/'analysis_v2/elbow_neckyaw12/verification.json',OLD/'report.json',OLD/'media/capture.json',ROOT/'native_v1/static_neckyaw12/media/capture.json',ROOT/'native_v2/elbow_neckyaw12/media/capture.json',ROOT/'compare_elbow_motion_v1.py',ROOT/'measure_torso_posture_v2.py',FONT,Path('/usr/bin/ffmpeg'),Path('/usr/bin/ffprobe'),PRODUCER]
inputs=[p for p in inputs if p.exists()]
before={str(p):snap(p) for p in sorted(set(inputs))}

# Exact-copy six native source videos and verify stream metadata.
manifest_rows=[]
for label,folder,title in CASES:
 for view in VIEWS:
  src=folder/'media'/f'{view}.mp4'
  dst=VID/f'{label}_{view}.mp4'
  shutil.copyfile(src,dst)
  if sha(src)!=sha(dst):raise RuntimeError(f'non-exact copy {src}')
  info=probe(dst)
  if info.get('nb_read_frames')!='151' or info.get('avg_frame_rate')!='30/1':raise RuntimeError(f'unexpected video stream {info}')
  manifest_rows.append({'label':title,'view':view,'source':str(src),'destination':str(dst),'source_sha256':sha(src),'copy_sha256':sha(dst),'ffprobe':info})

# Actual same-view whole-body stills at t=0 and t=5, plus actual new initial support camera view.
font=ImageFont.truetype(str(FONT),22); small=ImageFont.truetype(str(FONT),19)
canvas=Image.new('RGB',(1220,1320),(245,247,250));draw=ImageDraw.Draw(canvas)
draw.text((24,16),'실제 native whole-body 캡처 · 각 조건 0초 / 5초',font=font,fill=(25,35,50))
for r,(label,folder,title) in enumerate(CASES):
 y=62+r*410; draw.text((24,y),title,font=font,fill=(25,35,50))
 for c,(fn,tlabel) in enumerate(FRAMES):
  im=Image.open(folder/'media'/'frames'/'whole_body'/fn).convert('RGB'); im.thumbnail((570,320),Image.Resampling.LANCZOS)
  x=24+c*590; yy=y+36; canvas.paste(im,(x,yy));draw.rectangle((x,yy,x+im.width,yy+im.height),outline=(135,145,160),width=1)
  draw.text((x+6,yy+im.height+4),tlabel,font=small,fill=(30,40,55))
canvas.save(ART/'native_wholebody_old_new_timeline.png')

# Same pixel-space crop across old/new static native frames; this is a 2D crop, not a new view.
crop_canvas=Image.new('RGB',(1460,1370),(245,247,250));d=ImageDraw.Draw(crop_canvas)
d.text((20,12),'이전/새 static · 같은 native 전신 카메라 좌표를 자른 2D 확대',font=font,fill=(25,35,50))
for row,(label,folder,title) in enumerate(CASES[:2]):
 y=52+row*640; d.text((20,y),title,font=font,fill=(25,35,50))
 for col,(fn,tlabel) in enumerate(FRAMES):
  im=Image.open(folder/'media'/'frames'/'whole_body'/fn).convert('RGB')
  if im.size!=(1280,720):raise RuntimeError(f'camera frame size changed: {im.size}')
  crop=im.crop((400,100,900,500)).resize((700,560),Image.Resampling.LANCZOS)
  x=20+col*720; yy=y+34; crop_canvas.paste(crop,(x,yy));d.rectangle((x,yy,x+700,yy+560),outline=(135,145,160),width=1)
  d.text((x+6,yy+562),tlabel,font=small,fill=(30,40,55))
crop_canvas.save(ART/'native_wholebody_samecrop_old_new.png')
shutil.copyfile(source_initial,ART/'neck_yaw_static_initial_support_view.png')

# Actual torso orientation chart, with legend above the axes.
post=json.loads((ROOT/'torso_posture_v2.json').read_text())['cases']
old=post['static_cradle']['final']; new=post['static_neckyaw12']['final']
plt.rcParams['font.family']='NanumGothic';plt.rcParams['axes.unicode_minus']=False;matplotlib.font_manager.fontManager.addfont(str(FONT))
fig,ax=plt.subplots(figsize=(10,5),constrained_layout=False)
labels=['Chest→Neck 앞쪽 기울기','정면 heading (+Y to -X)']
oldvals=[old['chest_to_neck_forward_inclination_deg'],old['chest_facing_yaw_from_guitar_front_deg']]
newvals=[new['chest_to_neck_forward_inclination_deg'],new['chest_facing_yaw_from_guitar_front_deg']]
import numpy as np
x=np.arange(2);width=.34
b1=ax.bar(x-width/2,oldvals,width,label='이전 static 기준')
b2=ax.bar(x+width/2,newvals,width,label='새 neck-yaw static')
ax.set_xticks(x,labels);ax.set_ylabel('실제 native Chest–Neck 자세 측정 (°)');ax.grid(axis='y',alpha=.25)
ax.bar_label(b1,fmt='%.2f°',padding=3);ax.bar_label(b2,fmt='%.2f°',padding=3)
fig.suptitle('이전 static과 새 neck-yaw static의 실제 몸통 자세',fontsize=15,y=.99)
fig.legend(loc='upper center',bbox_to_anchor=(.5,.91),ncol=2)
fig.subplots_adjust(top=.80,left=.12,right=.98,bottom=.16)
fig.savefig(ART/'torso_posture_old_vs_neckyaw.png',dpi=170);plt.close(fig)

# Side-by-side actual whole-body videos, re-encoded only as a viewing aid; source videos stay exact.
oldcopy=VID/'old_axilla_static_whole_body.mp4'; newcopy=VID/'neck_yaw_static_whole_body.mp4'
derived=ART/'old_vs_neckturn_static.mp4'; fontfile=FONT.as_posix()
graph=(f"[0:v]scale=640:360:force_original_aspect_ratio=decrease,pad=640:434:(ow-iw)/2:74:color=black,drawtext=fontfile={fontfile}:text='이전 static · 다른 초기 상태':fontcolor=white:fontsize=21:box=1:boxcolor=black@0.6:boxborderw=8:x=14:y=8[a];"
       f"[1:v]scale=640:360:force_original_aspect_ratio=decrease,pad=640:434:(ow-iw)/2:74:color=black,drawtext=fontfile={fontfile}:text='새 neck-yaw static':fontcolor=white:fontsize=21:box=1:boxcolor=black@0.6:boxborderw=8:x=14:y=8[b];[a][b]hstack=inputs=2[v]")
run(['ffmpeg','-y','-i',str(oldcopy),'-i',str(newcopy),'-filter_complex',graph,'-map','[v]','-an','-c:v','libx264','-crf','20','-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart',str(derived)])

manifest={'videos':manifest_rows}
(VID/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
index=['# Neckward torso turn · native videos','', '아래 native 원본 영상 6개는 원본 bytes 그대로 복사했습니다. 5초 물리 구간, 151프레임, 30fps입니다. 이전 static 기준은 새 native와 초기 상태가 다릅니다.','']
for label,folder,title in CASES:
 index += [f'## {title}','',f'- [Whole-body video]({VID}/{label}_whole_body.mp4)',f'- [Hands video]({VID}/{label}_hands.mp4)','']
index += [f'[원본·사본 SHA-256 및 ffprobe]({VID}/manifest_v1.json)','']
(VID/'INDEX_V1.md').write_text('\n'.join(index),encoding='utf-8')

readme=f'''# Neckward torso turn · 실제 native 진단

새 neck-yaw static과 elbow-motion native는 초기 상태와 2.5초까지 trace가 정확히 같습니다. 이전 stable baseline은 다른 초기 상태이므로 이전/새 static 영상을 같은 초기조건 비교로 해석하지 않습니다. 세 native는 각 5초·1200 physics steps, 300 controls, 151 native frame으로 끝까지 계산했습니다. strap OFF, left grip 없음, 기타 direct force 없음, root/lower 고정이며 기존 human effort controller를 유지했습니다(상완 motor-point 10 N cap, 추가 forearm point force 0 N). Elbow motion은 단일 scalar R_Elbow_y target이며 world rotation axis가 아닙니다.

![이전 static 및 새 두 조건의 실제 native whole-body 0초·5초 캡처]({ART}/native_wholebody_old_new_timeline.png)

![이전/새 static의 동일좌표 upper-body 2D crop]({ART}/native_wholebody_samecrop_old_new.png)

![새 neck-yaw static의 actual initial native support view]({ART}/neck_yaw_static_initial_support_view.png)

## 실제 Chest–Neck 자세

![이전 및 새 static의 실제 몸통 자세 비교]({ART}/torso_posture_old_vs_neckyaw.png)

Source 목표와 native 측정 자세는 서로 다른 수치입니다. Search candidate source 요청은 body-right 6°, 추가 forward bend 2°, neck 방향 world-Z guitar yaw 12° 및 head yaw 7.2°(60% goal)였습니다. Actual native Chest–Neck basis 기준으로 이전 static→새 static은 forward inclination 53.575657°→48.347770° (−5.227887°), +Y에서 −X로 향하는 heading 12.643226°→22.198890° (+9.555664° toward neck), total inclination 53.590252°→48.762687°였습니다. Side inclination은 2.534570°→−10.951170°로 변했으므로 실제 torso가 source의 “body-right 6°” scalar 목표를 유지했다고 말하지 않습니다. 이들은 scalar q 목표나 source angle이 아니라 native Chest–Neck frame에서 계산한 실제 자세입니다.

## 작은 elbow-motion 비교

![새 neck-yaw 조건의 5° elbow command와 posture 측정]({ART}/neck_yaw_elbow_motion_response.png)

- 새 static: final body-bbox centre 3.944391 mm / total rotation 1.472679°.
- 새 elbow-motion: 3.876188 mm / 1.454971°.
- 2.5–5초 elbow 절대 moving q range 10.083668°; static-referenced incremental range 10.099138°.
- 최대 same-time guitar body-bbox-centre difference 0.099629 mm, rotation difference 0.053043°; incremental response RMSE 0.048544°, absolute q-vs-target RMSE 0.131056°.

모든 native physics는 1200 step 동안 계속 계산됐습니다. 새 elbow-motion 결과는 작은 elbow 영향 진단 1회이지, 전체 연주 안정성·반복성 인증이 아닙니다. 실제 contact endpoint 표본은 1200회 기준이며 upper-arm any-contact 1169, R_Hip 1193, Head/left arm/right distal arm 0입니다. Native declared support-region 분류는 0/1200입니다. Observed upper-arm fractions 0.3538–0.5089는 proximal 0–35% 목표 밖이며, 겨드랑이 해부학적 지지나 contact force share를 입증하지 않습니다. Raw lambda는 힘 측정값이 아닙니다.

Source-only geometry candidate는 proximal30 gap 2.279 mm, forearm 13.998 mm, thigh 0.199 mm, torso 32.929 mm를 기록했습니다. 이것은 source geometry 분석이고 cooked PhysX clearance가 아닙니다. Hands 영상은 왼손/기타 넥 쪽 카메라이므로 오른쪽 upper-arm contact evidence로 해석하지 않습니다. 전체 native physics는 중간에 멈추지 않았습니다.

## 영상

이전 static과 새 neck-yaw static native whole-body 영상은 나란히 볼 수 있습니다. 이전 조건은 다른 초기 상태입니다.

![이전 static과 새 neck-yaw static native whole-body 영상]({ART}/old_vs_neckturn_static.mp4)

새 motion 조건 native 전체 영상:

![새 neck-yaw elbow-motion native whole-body 영상]({VID}/neck_yaw_motion_whole_body.mp4)

[영상 색인]({VID}/INDEX_V1.md) · [복사 SHA-256 및 ffprobe manifest]({VID}/manifest_v1.json)

- [결과 summary]({ROOT}/result_summary_v1.json)
- [실제 몸통 자세 측정]({ROOT}/torso_posture_v2.json)
- [Elbow comparison 및 trace]({ROOT}/elbow_comparison_v1.json) · [trace JSON]({ROOT}/elbow_comparison_trace_v1.json)
- [Native contact-region 분류]({ROOT}/contact_region_v1.json)
- [Search source candidates]({ROOT}/search_v1/search.json)
'''
# Generate response chart before writing README link.
trace=json.loads((ROOT/'elbow_comparison_trace_v1.json').read_text())
plt.rcParams['font.family']='NanumGothic';plt.rcParams['axes.unicode_minus']=False;matplotlib.font_manager.fontManager.addfont(str(FONT))
fig,axs=plt.subplots(3,1,figsize=(10,8),sharex=True,constrained_layout=False)
pt=trace['physics_time_s'];t=trace['time_s']
a,=axs[0].plot(pt,trace['elbow_command_delta_deg'],label='명령 변화',lw=2)
b,=axs[0].plot(pt,trace['elbow_actual_moving_minus_static_deg'],label='실제 incremental R_Elbow_y',lw=1.5)
axs[0].set_ylabel('Elbow 변화 (°)');axs[0].grid(alpha=.25)
axs[1].plot(t,trace['same_time_body_centre_delta_mm'],color='#c44e52');axs[1].set_ylabel('동시점 body-bbox\n중심 차이 (mm)');axs[1].grid(alpha=.25)
axs[2].plot(t,trace['same_time_rotation_delta_deg'],color='#4c72b0');axs[2].set_ylabel('동시점 전체 SO(3)\n차이 (°)');axs[2].set_xlabel('물리 시간 (초)');axs[2].grid(alpha=.25)
axs[-1].set_xlim(2.5,5)
fig.suptitle('새 neck-yaw static vs motion · 2.5–5초 실제 trace',y=.99,fontsize=15)
fig.legend([a,b],[a.get_label(),b.get_label()],loc='upper center',bbox_to_anchor=(.5,.955),ncol=2)
fig.subplots_adjust(top=.89,left=.13,right=.98,bottom=.08,hspace=.18)
fig.savefig(ART/'neck_yaw_elbow_motion_response.png',dpi=170);plt.close(fig)
(ART/'README_V1.md').write_text(readme,encoding='utf-8')

# Verify all source inputs unchanged after image/video/document generation.
after={str(p):snap(p) for p in sorted(set(inputs))}
if before!=after:raise RuntimeError('source input changed during archive generation')
outputs={}
for p in [ART/'README_V1.md',ART/'native_wholebody_old_new_timeline.png',ART/'native_wholebody_samecrop_old_new.png',ART/'neck_yaw_static_initial_support_view.png',ART/'torso_posture_old_vs_neckyaw.png',ART/'neck_yaw_elbow_motion_response.png',derived,VID/'manifest_v1.json',VID/'INDEX_V1.md']+[Path(r['destination']) for r in manifest_rows]:outputs[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
prov={'scope':'native evidence archive and presentation only; no native or training execution', 'inputs_before':before,'inputs_after':after,'input_unchanged':True,'producer':{str(PRODUCER):snap(PRODUCER)},'font':{str(FONT):snap(FONT)},'video_copy_records':manifest_rows,'derived_side_by_side_video':{'path':str(derived),'sha256':sha(derived),'ffprobe':probe(derived),'filtergraph':graph},'outputs':outputs}
(ART/'provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'video_copies':len(manifest_rows),'input_count':len(inputs),'outputs':outputs,'provenance':str(ART/'provenance_v1.json')},ensure_ascii=False))
