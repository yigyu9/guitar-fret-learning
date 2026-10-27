#!/usr/bin/env python3
"""Package approved right-block cradle native media, plots, and Korean documentation."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os, json, hashlib, math, shutil, subprocess

BASE=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1')
ART=BASE/'artifacts_v1'
VIDEO=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_block_cradle_v1')
BRIEF=BASE/'artifact_brief_v1.json'
ANALYSIS=BASE/'native_analysis_final_v1.json'
FAIL_AUDIT=BASE/'failure_audit_v2.json'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
RUNS=[
 ('native_static_OFF0','static_OFF0','초기 기준 · Thorax 제어 OFF'),
 ('native_static_ON10','static_ON10','정지 · Thorax cap 10 N'),
 ('native_static_body4_ON10','static_body4_ON10','정지 · body4 reference'),
 ('native_static_body9_effort','static_body9_effort','미완료 · 초기 guard 중단'),
 ('native_static_body9_low','static_body9_low','정지 · body9 낮춤'),
 ('native_static_currentG_body4','static_currentG_body4','정지 · current-G body4'),
 ('native_static_Thorax20','static_Thorax20','정지 · Thorax cap 20 N'),
 ('native_static_Thorax30','static_Thorax30','정지 · Thorax cap 30 N'),
 ('native_static_Thorax40','static_Thorax40','정지 · Thorax cap 40 N'),
 ('native_static_close','static_close','선택된 정지 기준'),
 ('native_elbow5_Thorax40','elbow5_Thorax40','팔꿈치 주기 · Thorax40'),
 ('native_elbow5_close','elbow5_close','선택된 팔꿈치 주기'),
]
SELECTED=BASE/'native_elbow5_close'
STATIC=BASE/'native_static_close'
FRAME_SPECS=[]
for run in [SELECTED,STATIC]:
 for view in ['whole_body','hands']:
  for ix,step,sec in [(0,0,'0초'),(90,720,'3초'),(150,1200,'5초')]:
   FRAME_SPECS.append((run/'media/frames'/view/f'{ix:05d}.png',run.name,view,step,sec))
SUPPORT=SELECTED/'media/initial_support_side.png'


def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def statrec(p):
 p=Path(p);s=p.stat();return {'sha256':sha(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
def ffprobe(p):
 cmd=['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(p)]
 s=json.loads(subprocess.check_output(cmd,text=True))['streams'][0]
 return {k:s[k] for k in ['width','height','avg_frame_rate','nb_read_frames','duration']}
def font(size):return ImageFont.truetype(str(FONT),size)
def file_record(p):return {'sha256':sha(p),'bytes':Path(p).stat().st_size}

# Pin direct source files and the complete input closure sealed by the approved brief.
inputs={}
def add(p):
 p=Path(p)
 if p not in inputs:
  if not p.is_file():raise FileNotFoundError(p)
  inputs[p]=statrec(p)
brief=json.loads(BRIEF.read_text())
for p in [BRIEF,ANALYSIS,FAIL_AUDIT,FONT,BASE/'config_v1/elbow5_close.json',BASE/'config_v1/static_ON10.json']:
 add(p)
for raw,expected in brief['input_sha256'].items():
 p=Path(raw);add(p)
 assert sha(p)==expected, f'brief-pinned SHA mismatch: {p}'
analysis=json.loads(ANALYSIS.read_text())
assert analysis.get('passed') is True
assert len(analysis['cases'])==11
case_names=[x[0] for x in RUNS if x[0]!='native_static_body9_effort']
assert set(case_names)==set(analysis['cases'])
for name,slug,label in RUNS:
 d=BASE/name
 for f in ['report.json','initial_values.json','trace.json','media/capture.json','media/whole_body.mp4','media/hands.mp4']:
  add(d/f)
 report=json.loads((d/'report.json').read_text())
 for view in ['whole_body','hands']:
  assert (d/'media'/f'{view}.mp4').is_file()
  assert report['videos'][view]['path']==str(d/'media'/f'{view}.mp4')
  assert report['videos'][view]['sha256']==sha(d/'media'/f'{view}.mp4')
 cap=json.loads((d/'media/capture.json').read_text())
 for step in ([0,720,1200] if name in ['native_elbow5_close','native_static_close'] else []):
  fr=next(x for x in cap['frames'] if x['physics_step']==step)
  for view in ['whole_body','hands']:
   src=Path(next(p for p in fr['image_sha256'] if p.endswith(f'/{view}/{step//8:05d}.png')))
   add(src);assert sha(src)==fr['image_sha256'][str(src)]
# Selected graph raw trace/qref and initial side view source.
for d in [SELECTED,STATIC]:
 add(d/'initial_values.json');add(d/'trace.json')
add(SUPPORT)
# Includes each report-listed original movie directly in closure.
inputs_before={str(p):v for p,v in inputs.items()}

# Verify trace/body-center math against the canonical final analysis.
body_g=analysis['body_centre_G_m']
def q_rotate(q,v):
 n=math.sqrt(sum(float(a)**2 for a in q));qx,qy,qz,qw=[float(a)/n for a in q]
 t=[2*(qy*v[2]-qz*v[1]),2*(qz*v[0]-qx*v[2]),2*(qx*v[1]-qy*v[0])]
 c=[qy*t[2]-qz*t[1],qz*t[0]-qx*t[2],qx*t[1]-qy*t[0]]
 return [v[i]+qw*t[i]+c[i] for i in range(3)]
def world_center(row):
 offset=q_rotate(row['quaternion_xyzw'],body_g)
 return [float(row['position_W_m'][i])+offset[i] for i in range(3)]
def summarize_trace(directory):
 tr=json.loads((directory/'trace.json').read_text())
 iv=json.loads((directory/'initial_values.json').read_text())
 idx=iv['joint_names'].index('R_Elbow_y');qref=float(iv['q_ref_rad'][idx])
 c0=world_center(tr[0]);q0=tr[0]['quaternion_xyzw']
 times=[];disp=[];rot=[];elbow=[]
 for row in tr:
  times.append(row['physics_step']/240.0)
  c=world_center(row);disp.append(math.sqrt(sum((c[i]-c0[i])**2 for i in range(3)))*1000)
  q=row['quaternion_xyzw'];norm0=math.sqrt(sum(float(x)*float(x) for x in q0));norm=math.sqrt(sum(float(x)*float(x) for x in q))
  dot=abs(sum(float(q0[i])*float(q[i]) for i in range(4))/(norm0*norm));dot=max(-1.0,min(1.0,dot))
  rot.append(math.degrees(2*math.acos(dot)))
  elbow.append(math.degrees(float(row['q_rad'][idx])-qref))
 return {'time_s':times,'body_centre_delta_mm':disp,'SO3_deg':rot,'R_Elbow_y_delta_deg':elbow,'R_Elbow_y_index':idx,'sample_count':len(tr)}
static_series=summarize_trace(STATIC);wave_series=summarize_trace(SELECTED)
assert static_series['sample_count']==wave_series['sample_count']==301
assert abs(max(wave_series['R_Elbow_y_delta_deg'][i] for i,t in enumerate(wave_series['time_s']) if 2.5<=t<=4.5)-min(wave_series['R_Elbow_y_delta_deg'][i] for i,t in enumerate(wave_series['time_s']) if 2.5<=t<=4.5)-10.114130462576542)<1e-7

# Validate each panel frame directly against the per-frame native capture hash.
for p,run,view,step,sec in FRAME_SPECS:
 cap=json.loads((BASE/run/'media/capture.json').read_text())
 fr=next(f for f in cap['frames'] if f['physics_step']==step)
 assert fr['time_s']==float(sec[:-1])
 assert fr['image_sha256'][str(p)]==sha(p)

# Make actual native frame panels with all labels in separate header strips.
def panel(out,title,rows):
 # All captions are placed in strips outside the unmodified captured frames.
 W=1920; pad=30; gap=18; colw=(W-2*pad-2*gap)//3
 frame_h=310; label_h=40; caption_h=38; row_gap=24; title_h=64
 row_h=label_h+caption_h+frame_h+20+row_gap
 H=title_h+2*row_h+12
 canvas=Image.new('RGB',(W,H),'#f1f3f5');draw=ImageDraw.Draw(canvas)
 draw.text((pad,10),title,font=font(31),fill='#14283b')
 for ri,(rlabel,paths,headers) in enumerate(rows):
  top=title_h+ri*row_h
  draw.text((pad,top),rlabel,font=font(24),fill='#173d5c')
  y=top+label_h
  for j,(p,hdr) in enumerate(zip(paths,headers)):
   x=pad+j*(colw+gap)
   draw.rounded_rectangle((x,y,x+colw,y+caption_h+frame_h+10),radius=6,fill='white',outline='#b7c3ce',width=2)
   draw.text((x+10,y+5),hdr,font=font(19),fill='#172533')
   img=Image.open(p).convert('RGB');img.thumbnail((colw-16,frame_h),Image.Resampling.LANCZOS)
   canvas.paste(img,(x+(colw-img.width)//2,y+caption_h+(frame_h-img.height)//2))
 canvas.save(out,format='PNG',optimize=True)

for view in ['whole_body','hands']:
 sel=[SELECTED/'media/frames'/view/f'{i:05d}.png' for i in [0,90,150]]
 sta=[STATIC/'media/frames'/view/f'{i:05d}.png' for i in [0,90,150]]
 panel(ART/f'native_elbow5_close_{view}_0_3_5_v1.png',f'실제 native {"전신" if view=="whole_body" else "손"} 프레임 · 시작 / 3초 / 5초',[
  ('선택 wave 조건 · native_elbow5_close',sel,['0초 · step 0','3초 · step 720','5초 · step 1200']),
  ('선택 정지 기준 · native_static_close',sta,['0초 · step 0','3초 · step 720','5초 · step 1200']),
 ])
shutil.copyfile(SUPPORT,ART/'native_elbow5_close_initial_support_side.png')
assert sha(SUPPORT)==sha(ART/'native_elbow5_close_initial_support_side.png')

# Plot every stored sample. Quaternion convention in the raw trace is xyzw.
os.environ.setdefault('MPLCONFIGDIR','/tmp/mplconfig_right_block_cradle_v1')
Path(os.environ['MPLCONFIGDIR']).mkdir(parents=True,exist_ok=True)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
font_manager.fontManager.addfont(str(FONT));rcParams['font.family']='NanumGothic';rcParams['axes.unicode_minus']=False
fig,axes=plt.subplots(3,1,figsize=(13,12),sharex=True)
fig.suptitle('선택 정지 기준과 elbow5_close · trace 기반 실제값 비교',fontsize=18,y=.99)
fig.legend(handles=[plt.Line2D([0],[0],color='#566b7a',lw=2,label='정지 기준 · native_static_close'),plt.Line2D([0],[0],color='#1676b8',lw=2,label='팔꿈치 주기 · native_elbow5_close')],loc='upper center',bbox_to_anchor=(.5,.966),ncol=2,frameon=False)
plots=[('기타 바디 bounding-box 중심 변위 (mm)', 'body_centre_delta_mm'),('초기 기타 quaternion 대비 전체 SO(3) 변화 (°)','SO3_deg'),('R_Elbow_y 실제 q - q_ref (°)','R_Elbow_y_delta_deg')]
for ax,(label,key) in zip(axes,plots):
 ax.plot(static_series['time_s'],static_series[key],color='#566b7a',lw=1.8,label='정지')
 ax.plot(wave_series['time_s'],wave_series[key],color='#1676b8',lw=1.8,label='팔꿈치 주기')
 ax.axvspan(2.5,4.5,color='#f2b544',alpha=.18,zorder=0)
 ax.set_ylabel(label,fontsize=11);ax.grid(True,alpha=.28);ax.set_xlim(0,5)
axes[0].text(.995,.93,'음영: elbow wave 2.5–4.5초',transform=axes[0].transAxes,ha='right',va='top',fontsize=10,color='#6a4d12')
axes[-1].set_xlabel('물리 경과 시간 (초) = physics_step ÷ 240 Hz')
fig.tight_layout(rect=(0,.025,1,.92),h_pad=1.0)
fig.savefig(ART/'static_vs_elbow5_close_trace_v1.png',dpi=150,bbox_inches='tight');plt.close(fig)

# Exact media copies and manifest: all 12 attempt directories, including the abort clip.
VIDEO.mkdir(parents=True,exist_ok=True);records=[]
for name,slug,label in RUNS:
 d=BASE/name;report=json.loads((d/'report.json').read_text())
 for view in ['whole_body','hands']:
  src=d/'media'/f'{view}.mp4';before=statrec(src)
  outdir=VIDEO/slug;outdir.mkdir(parents=True,exist_ok=True);dest=outdir/f'{view}.mp4'
  shutil.copyfile(src,dest);after=statrec(src);probe=ffprobe(dest);copyhash=sha(dest)
  assert before['sha256']==after['sha256']==copyhash
  assert probe['avg_frame_rate']=='30/1'
  records.append({'case':name,'label':label,'view':view,'source':str(src),'source_sha256':before['sha256'],'destination':str(dest),'copy_sha256':copyhash,'bytes':dest.stat().st_size,'ffprobe':probe,'completed':report['completed'],'physics_seconds':report['physics_seconds']})
(VIDEO/'manifest_v1.json').write_text(json.dumps({'videos':records},ensure_ascii=False,indent=2)+'\n')

# Video index with all 24 entries and separate abort labeling.
idx=['# 오른쪽 두 블록 cradle · native 영상 색인 V1','',
 '12개 native 시도의 전신·손 영상 24개를 byte-exact 복사했습니다. 11개 조건은 5초까지 완료했고, `native_static_body9_effort`는 guard 중단 당시 물리 5 step(0.020833초)만 진행되어 2프레임(0.066667초) 영상으로 별도 표시합니다. 원본·사본 SHA 및 ffprobe 정보는 [manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_block_cradle_v1/manifest_v1.json)에 있습니다.','']
for name,slug,label in RUNS:
 r=json.loads((BASE/name/'report.json').read_text())
 idx += [f'## `{name}` · {label}','',f"물리: {r['physics_steps']} step / {r['physics_seconds']:.6f}초; 완료=`{str(r['completed']).lower()}`."]
 if name=='native_static_body9_effort':idx.append('Guard 중단 clip이며 완료된 5초 영상이 아닙니다.')
 idx.append('')
 for view,ko in [('whole_body','전신'),('hands','손')]:
  rec=next(x for x in records if x['case']==name and x['view']==view);q=rec['ffprobe']
  idx.append(f"- [{ko} MP4]({rec['destination']}) — {q['nb_read_frames']}프레임, {q['avg_frame_rate']}fps, 영상 {q['duration']}초")
 idx.append('')
(VIDEO/'INDEX_V1.md').write_text('\n'.join(idx)+'\n',encoding='utf-8')
video_readme='''# 오른쪽 두 블록 cradle · 영상 보관 안내\n\n각 native 시도의 전신·손 MP4를 원본 바이트 그대로 복사해 총 24개 파일로 모았습니다. 실행 결과를 완료 11개와 guard가 5 physics step 뒤 중단한 짧은 clip 1개로 구분합니다. 중단 clip도 누락하지 않았으며 완료 시험처럼 다루지 않습니다.\n\n- [12개 native 시도별 전신·손 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_block_cradle_v1/INDEX_V1.md)\n- [원본/사본 SHA-256 및 ffprobe 24행 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_block_cradle_v1/manifest_v1.json)\n\n일반 완료 영상은 151프레임·30fps로 5초 물리를 담고 재생 길이는 5.033333초입니다. `native_static_body9_effort` abort는 2프레임·30fps, 물리 0.020833초에 대응하며 영상 길이는 0.066667초입니다. 재인코딩하거나 원본 run 디렉터리를 수정하지 않았습니다.\n'''
(VIDEO/'README_V1.md').write_text(video_readme,encoding='utf-8')

# Build final metrics table from the canonical analysis; keep the guard abort separate.
rows=[]
for name,slug,label in RUNS:
 if name not in analysis['cases']:continue
 c=analysis['cases'][name]
 rows.append(f"| `{name}` | 완료 5초 | {c['final_body_centre_change_mm']} | {c['final_rotation_change_deg']} |")
abort_report=json.loads((BASE/'native_static_body9_effort/report.json').read_text())
# Korean artifact README includes approved limit language and actual video/image links.
README='''# 오른쪽 두 블록 cradle · 정지 기준과 elbow 주기 진단\n\n이 기록은 실제 native 5초 시험 11개와 guard에서 중단된 1회(총 12 native 시도)를 구분해 보관합니다. 본 산출물 생성에서는 추가 물리 실행·학습을 하지 않았습니다. 분석 수치는 `native_analysis_final_v1.json`을 따릅니다.\n\n## 선택된 close 조건: native 프레임\n\n![선택 elbow5_close 전신 실제 native 프레임: 0, 3, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifacts_v1/native_elbow5_close_whole_body_0_3_5_v1.png)\n\n![선택 elbow5_close 손 실제 native 프레임: 0, 3, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifacts_v1/native_elbow5_close_hands_0_3_5_v1.png)\n\n패널은 원본 Isaac Gym native 캡처를 같은 카메라·같은 시점으로 배치했으며 캡션은 이미지 밖에 뒀습니다. 아래 초기 측면 이미지도 원본 native 캡처를 그대로 복사한 별도 2-block 보기입니다. 추가 카메라 투영, 힘 표시, 접촉 overlay는 넣지 않았습니다.\n\n![elbow5_close 실제 native 초기 support-side 2-block 보기](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifacts_v1/native_elbow5_close_initial_support_side.png)\n\n## 모든 완료 시도의 최종 기록\n\n| native 조건 | 상태 | 최종 기타 BB 중심 변위 (mm) | 최종 기타 전체 SO(3) 변화 (°) |\n|---|---|---:|---:|\n'''+ '\n'.join(rows)+'''\n\n별도 abort인 `native_static_body9_effort`는 guard에서 물리 step 5, 즉 0.020833초에 중단됐고 전신·손 영상은 각각 2프레임입니다(재생 0.066667초). 5초 완료 실행이나 분석 최종표에 포함하지 않습니다.\n\n## 정지 기준과 팔꿈치 주기의 trace 비교\n\n![native_static_close와 native_elbow5_close 전체 trace 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifacts_v1/static_vs_elbow5_close_trace_v1.png)\n\n그래프는 두 raw `trace.json`의 모든 저장 표본(각각 301개)을 사용했습니다. 시간은 `physics_step/240`초입니다. 바디 중심은 canonical `body_centre_G_m`을 xyzw quaternion으로 world 회전한 뒤 `position_W_m`에 더하고 초기 위치에서의 이동량을 계산했습니다. SO(3)는 초기와 현재 xyzw quaternion의 상대 각도이며, 팔꿈치는 실제 `R_Elbow_y` scalar `q − q_ref`입니다. 음영은 elbow wave 2.5–4.5초 구간입니다.\n\n선택된 정지 기준 대비 주기 조건은 2.5–4.5초 `R_Elbow_y` 실제 이동 range 10.114130°였습니다. 정지 trace 대비 기타 추가 변화는 최대 중심 0.071023 mm / SO(3) 0.031521°였고, wave 종료 시점의 초기 대비 변화는 중심 4.102109 mm / SO(3) 3.997036°였습니다. 실행 중 최대 중심 변위 5.328657 mm, 최대 SO(3) 변화 4.494762°는 종료값과 구분합니다.\n\n![선택된 elbow5_close 전체 native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_block_cradle_v1/elbow5_close/whole_body.mp4)\n\n## 접촉과 제어의 범위\n\n선택 조건에서 Thorax와 상완 contact presence는 elbow wave 480/480 step, positive raw lambda는 223/480 step이었습니다. 마지막 120 step에서는 각각 presence 120/120, positive 56/120입니다. 왼쪽 `LH:thumb3`와 오른쪽 허벅지 contact가 계속 남아 있으므로 오른쪽만의 지지로 분리된 결과가 아닙니다. raw lambda는 뉴턴 단위 힘이나 지지력 분담이 아닙니다.\n\n이 조건은 현재 기타 G 기준으로 finite/bounded한 사람 관절 토크 제어를 사용합니다. passive hold로 설명하지 않습니다. source face-wrap 4·5는 실패해 실행하지 않았습니다. 이번 조건은 한 축·한 주기만 확인했으며 반복성, 모든 움직임, 연주 안정성 또는 음악 성공을 인증하지 않습니다. 기타를 고정·부착·직접 가압하거나 자세를 덮어쓰지 않았습니다.\n\n## 원자료와 보관 파일\n\n- [12개 실행 전신·손 영상 목록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_block_cradle_v1/INDEX_V1.md)\n- [24개 원본/사본 hash·ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_block_cradle_v1/manifest_v1.json)\n- [canonical analysis](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/native_analysis_final_v1.json)\n- [승인된 artifact brief](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifact_brief_v1.json)\n- [failure audit v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/failure_audit_v2.json)\n\n**보관 산출물:** 위 세 이미지, byte-exact 24개 MP4, 한국어 README/색인, manifest 및 [provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifacts_v1/provenance_v1.json).\n'''
(ART/'README_V1.md').write_text(README,encoding='utf-8')

# Before/after closure: original inputs must stay unchanged.
inputs_after={str(p):statrec(p) for p in inputs}
assert inputs_before==inputs_after
# All generated files except provenance are pinned as output hashes.
outputs=sorted({Path(p) for p in [*ART.iterdir(),VIDEO/'INDEX_V1.md',VIDEO/'README_V1.md',VIDEO/'manifest_v1.json',*[r['destination'] for r in records]] if Path(p).is_file() and Path(p).name!='provenance_v1.json'})
prov={
 'task':'오른쪽 두 블록 cradle: 승인된 native 기록의 시각화/문서/영상 보관만',
 'additional_physics_runs':0,'training_updates':0,'video_reencodes':0,'video_copy_count':len(records),
 'native_attempts':12,'completed_five_second_runs':11,'aborted_partial_run':'native_static_body9_effort',
 'inputs_before_after':{p:{'before':inputs_before[p],'after':inputs_after[p],'unchanged':inputs_before[p]==inputs_after[p]} for p in inputs_before},
 'producer':{'path':str(Path(__file__)),'sha256':sha(Path(__file__)),'bytes':Path(__file__).stat().st_size},
 'font':{'path':str(FONT),'sha256':sha(FONT),'bytes':FONT.stat().st_size},
 'trace_formula':{'body_centre_G_m':body_g,'pose_translation_field':'position_W_m','pose_quaternion_field':'quaternion_xyzw (xyzw)','time':'physics_step/240','joint':'R_Elbow_y','joint_formula':'trace q_rad[index] - initial_values q_ref_rad[index]','sample_counts':{'native_static_close':static_series['sample_count'],'native_elbow5_close':wave_series['sample_count']}},
 'frame_sources':{str(p):{'case':run,'view':view,'physics_step':step,'time_s':float(sec[:-1]),'source_sha256':sha(p)} for p,run,view,step,sec in FRAME_SPECS}|{str(SUPPORT):{'case':'native_elbow5_close','view':'initial_support_side original native image','physics_step':0,'source_sha256':sha(SUPPORT)}},
 'video_manifest_rows':records,
 'outputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs},
}
(ART/'provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'video_copies':len(records),'complete':sum(r['completed'] for r in records[::2]),'artifact_outputs':prov['outputs'],'producer_sha256':sha(Path(__file__)),'provenance_sha256':sha(ART/'provenance_v1.json')},ensure_ascii=False))
