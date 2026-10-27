from __future__ import annotations
import csv, hashlib, json, math, shutil, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageDraw, ImageFont

ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1'
ART=P/'artifacts_v1'; V=ROOT/'docs/2026-10-19/stability_adapter_2/video/chest_left_grip_cycle_v1'
N=P/'native_v1'; M=N/'media'
TIMES=[3.5,6.5,10.5,14.0]
FRAMES=[105,195,315,420]
CAPTIONS=['3.5초 · A 지점 잡기 유지','6.5초 · A 지점 열린 손, 이동 전','10.5초 · B 지점 잡기 유지','14.0초 · B 지점 열린 손, 안정 관찰']

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()
def read(path):return json.loads(Path(path).read_text())
def pins():
 analysis=read(P/'analysis_v1.json')
 paths={Path(x) for x in analysis['input_sha256']}
 paths.update([P/'analysis_v1.json',P/'log_scope_notes_v1.json',N/'report.json',N/'attempt.json',N/'initial_values.json',N/'actual_contacts.json',M/'capture.json',M/'videos.json',M/'left_cycle_contacts.json',M/'physics_endpoint_contacts.json',M/'left_cycle_efforts.json',M/'left_cycle_targets.json'])
 paths.update(M/'frames'/'hands'/f'{i:05d}.png' for i in FRAMES)
 paths.update(M/f'{v}.mp4' for v in ['whole_body','hands','chest_arm_close'])
 return sorted(paths)
def pxyz(d):return np.array([d['x'],d['y'],d['z']],dtype=float)
def quat(d):return np.array([d['x'],d['y'],d['z'],d['w']],dtype=float)
def rotate(q,v):
 xyz=q[:3];return v+2*np.cross(xyz,np.cross(xyz,v)+q[3]*v)
def run():
 ART.mkdir(parents=True,exist_ok=True);V.mkdir(parents=True,exist_ok=True)
 before=read(ART/'artifact_before_v1.json'); expected={x['path']:x['sha256'] for x in before['inputs']}
 if before['producer']['sha256']!=sha(ART/'artifact_producer_v1.py'):raise SystemExit('producer sha changed after pre-pin')
 if {str(p) for p in pins()}!=set(expected):raise SystemExit('input set differs from pre-pin')
 mismatch=[p for p,h in expected.items() if sha(p)!=h]
 if mismatch:raise SystemExit(f'input changed before run: {mismatch}')
 report=read(N/'report.json'); analysis=read(P/'analysis_v1.json'); measured=analysis['measured']; cap=read(M/'capture.json')
 if not report['completed'] or report['physics_steps']!=3840 or report['physics_seconds']!=16 or not report['inputs_unchanged'] or report['forbidden_calls']:
  raise SystemExit('native completion guard failed')
 # Copy the three native videos and four selected native hand frames, preserving bytes.
 copies=[]
 for view in ['whole_body','hands','chest_arm_close']:
  src=M/f'{view}.mp4';dst=V/f'{view}.mp4';shutil.copy2(src,dst)
  want=report['videos'][view]['sha256']
  if sha(dst)!=want:raise SystemExit(f'video copy hash mismatch: {view}')
  copies.append({'kind':'native_video','source':str(src),'copy':str(dst),'sha256':want,'expected_sha256_from_report':want})
 frame_dir=ART/'native_hand_frames_v1';frame_dir.mkdir(exist_ok=True)
 chosen=[]
 for t,i,caption in zip(TIMES,FRAMES,CAPTIONS):
  src=M/'frames'/'hands'/f'{i:05d}.png';dst=frame_dir/f'hands_{t:04.1f}s.png'
  record=next(x for x in cap['frames'] if x['time_s']==t)
  want=record['image_sha256'][str(src.resolve())]
  if sha(src)!=want:raise SystemExit(f'capture hash mismatch: {src}')
  shutil.copy2(src,dst)
  if sha(dst)!=want:raise SystemExit(f'frame copy mismatch: {dst}')
  copies.append({'kind':'native_hand_frame','time_s':t,'physics_step':i*8,'source':str(src),'copy':str(dst),'sha256':want,'expected_sha256_from_capture':want})
  chosen.append(dst)
 # Contact sheet captions stay outside the unchanged native image regions.
 font_path='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
 font=ImageFont.truetype(font_path,22,index=0) if Path(font_path).exists() else ImageFont.load_default()
 thumb=(700,394); pad=18; caption_h=44; cols=2; rows=2
 sheet=Image.new('RGB',(cols*(thumb[0]+pad)+pad,rows*(thumb[1]+caption_h+pad)+pad),'white')
 draw=ImageDraw.Draw(sheet)
 for j,(src,caption) in enumerate(zip(chosen,CAPTIONS)):
  img=Image.open(src).convert('RGB');img.thumbnail(thumb,Image.Resampling.LANCZOS)
  x=pad+(j%cols)*(thumb[0]+pad)+(thumb[0]-img.width)//2
  y=pad+(j//cols)*(thumb[1]+caption_h+pad)
  sheet.paste(img,(x,y));draw.text((pad+(j%cols)*(thumb[0]+pad),y+thumb[1]+7),caption,font=font,fill='black')
 sheet.save(ART/'hands_cycle_four_moments_v1.png',format='PNG',optimize=False)
 # Reconstruct guitar BB-centre trajectory from actual 240Hz actor endpoints and configured local BB centre.
 init=read(N/'initial_values.json'); idx=init['guitar_body_names'].index('G:body')
 body_offset=np.array(measured['body_center_G_m'],dtype=float)
 state=init['native_initial_state']['guitar_body_states'][0]
 p0=pxyz(state['pose']['p']);q0=quat(state['pose']['r']);center0=p0+rotate(q0,body_offset)
 times=[0.0];bb=[0.0];so3=[0.0]
 for row in read(M/'physics_endpoint_contacts.json')['rows']:
  state=row['guitar_body_states']['guitar'];p=pxyz(state['pose']['p']);q=quat(state['pose']['r'])
  center=p+rotate(q,body_offset)
  times.append(float(row['time_s']));bb.append(float(np.linalg.norm(center-center0)*1000))
  dot=min(1.0,abs(float(np.dot(q0,q))));so3.append(float(2*math.acos(dot)*180/math.pi))
 maxbb=max(bb);maxso=max(so3)
 if abs(maxbb-measured['maximum_body_from_initial_mm'])>0.0001 or abs(maxso-measured['maximum_rotation_from_initial_deg'])>0.001:
  raise SystemExit(f'analysis metric assertion failed: {maxbb=} {maxso=}')
 with (ART/'motion_samples_240Hz_v1.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['time_s','guitar_BB_center_displacement_from_initial_mm','guitar_SO3_rotation_from_initial_deg'])
  w.writerows(zip(times,bb,so3))
 fontprop=FontProperties(fname=font_path) if Path(font_path).exists() else None
 fig,axs=plt.subplots(2,1,figsize=(10,6.4),sharex=True)
 axs[0].plot(times,bb,color='#0072B2',lw=1.2);axs[0].set_ylabel('기타 BB 중심 변위 (mm)',fontproperties=fontprop)
 axs[1].plot(times,so3,color='#D55E00',lw=1.2);axs[1].set_ylabel('SO(3) 회전거리 (deg)',fontproperties=fontprop);axs[1].set_xlabel('시간 (s)',fontproperties=fontprop)
 boundaries=[2,3,4.5,6,7,8.5,10,11.5,13]
 for ax in axs:
  ax.set_xlim(0,16);ax.grid(True,alpha=.25)
  for x in boundaries:ax.axvline(x,color='gray',lw=.55,alpha=.35)
 fig.tight_layout();fig.savefig(ART/'guitar_motion_240Hz_v1.png',dpi=180);plt.close(fig)
 # Documentation links are absolute for app preview.
 A=str(ART);VP=str(V)
 (ART/'README.md').write_text(f'''# 왼손 기타 잡기·놓기 한 사이클

16초 native 실행이 3,840 physics step 완료됐다. 기타는 자유 동역학이며 strap·인위적 기타 힘·상태 덮어쓰기 없이 root와 하체를 고정했고 self-collision을 켰다. 오른손 타현은 끄고 오른쪽/몸통 목표는 유지했다. 왼팔 12개와 왼손 21개 target만 사이클 중 변경했다. 실제 구동 모드는 POSITION 48개와 EFFORT 33개이며, 상속된 POSITION 57 라벨은 현재 명령 구성을 나타내지 않는다.

| 시간 | 단계 | 측정 접촉 |
|---|---|---|
| 0–2 s | 준비 | 잡기 접촉 전 |
| 2–3 s | A 닫기 | 접촉 전환 구간 |
| 3–4.5 s | A 유지 | 엄지+다른 손가락 양의 raw lambda 360/360 |
| 4.5–6 s | A 놓기 | 해제 전환, 구간 최대 16.522 mm / 14.717° (4.5 s 기준) |
| 6–7 s | A 열린 손 | 왼팔·손 접촉 없음 240/240; 구간 최대 13.903 mm / 8.433° (6 s 기준) |
| 7–8.5 s | 열린 채 B로 이동 | 접촉 없음 360/360; B−A 평균 손목 이동 neck축 41.418 mm (요청 40 mm) |
| 8.5–10 s | B 닫기 | 접촉 전환 구간 |
| 10–11.5 s | B 유지 | 엄지+다른 손가락 양의 raw lambda 360/360 |
| 11.5–13 s | B 놓기 | 전환 구간 |
| 13–16 s | B 열린 손 관찰 | 왼팔·손 접촉 없음 720/720; 구간 최대 0.445 mm / 0.213° (13 s 기준) |

놓기 동작은 각 지점에서 G=[0.070, 0.080, 0] m 대각 방향 목표(norm 106.3 mm)를 사용했다. 초기 기준 전체 최대 기타 BB 중심 변위는 {measured['maximum_body_from_initial_mm']:.3f} mm, SO(3) 회전은 {measured['maximum_rotation_from_initial_deg']:.3f}°였다. 2초 기준 최대는 {measured['maximum_body_from2s_mm']:.3f} mm / {measured['maximum_rotation_from2s_deg']:.3f}°다. 따라서 손을 실제로 잡고 놓는 동작과 마지막 열린 손 구간의 정착은 관찰됐지만, 정적 유지보다 큰 전환기 기타 자세 변화가 있었다. 시작 자세 불변, 강한 안정성, force closure 또는 음악 연주 성공을 뜻하지 않는다.

B 지점 열린 손 구간 말기에도 오른쪽 위팔과 오른쪽 허벅지의 양의 접촉은 각각 720/720 표본이며 Chest는 716/720 표본이다. 왼쪽 허벅지 접촉 가능성을 배제하지 않으며 지지가 오른쪽 접촉만으로 이뤄졌다고 단정하지 않는다. raw lambda는 보정된 힘(N)이 아니다.

## 프레임과 움직임

아래 네 장은 native 손 카메라 원본 프레임을 그대로 축소·배치했으며 설명 문구는 영상 바깥에 있다.

![3.5초 A 유지, 6.5초 A 열린 손, 10.5초 B 유지, 14초 B 열린 손 native frame 비교]({A}/hands_cycle_four_moments_v1.png)

[240 Hz 기타 BB 중심·SO(3) 그래프]({A}/guitar_motion_240Hz_v1.png) · [시계열 CSV]({A}/motion_samples_240Hz_v1.csv)

## 실제 native 영상

각 영상은 16초 native Isaac Gym 카메라 캡처다. [전체 보기와 링크]({VP}/README.md).
''',encoding='utf-8')
 lines=['# 왼손 잡기·놓기 사이클 native 영상','', '16초, 3,840 physics step 실행의 실제 native 카메라 영상. 오른손 타현은 꺼져 있다. 상세 측정과 한계는 [요약]('+str(ART)+'/README.md)에서 확인한다.','']
 for view,label in [('whole_body','전신'),('hands','손'),('chest_arm_close','가슴·팔 확대')]:lines += ['## '+label,'',f'![{label} native cycle]({V}/{view}.mp4)','']
 (V/'README.md').write_text('\n'.join(lines),encoding='utf-8')
 # Verify pinned inputs unchanged after generation and inventory all outputs.
 after={str(p):sha(p) for p in pins()}; bad=[p for p,h in expected.items() if after[p]!=h]
 if bad:raise SystemExit(f'input changed during artifact generation: {bad}')
 if any(sha(x['copy'])!=x['sha256'] for x in copies):raise SystemExit('copy hash verification failed')
 outputs=[ART/'hands_cycle_four_moments_v1.png',ART/'guitar_motion_240Hz_v1.png',ART/'motion_samples_240Hz_v1.csv',ART/'README.md',V/'README.md']
 manifest={'schema':'chest_left_grip_cycle_artifact_manifest_v1','producer':{'path':str(ART/'artifact_producer_v1.py'),'sha256':sha(ART/'artifact_producer_v1.py')},'inputs_before':before['inputs'],'inputs_after':[{'path':p,'sha256':h} for p,h in after.items()],'inputs_unchanged':True,'copies':copies,'derived_artifacts':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs],'motion_assertions':{'computed_max_BB_mm':maxbb,'analysis_max_BB_mm':measured['maximum_body_from_initial_mm'],'computed_max_SO3_deg':maxso,'analysis_max_SO3_deg':measured['maximum_rotation_from_initial_deg'],'passed':True}}
 (ART/'copy_manifest_v1.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'videos':len([x for x in copies if x['kind']=='native_video']),'frames':len([x for x in copies if x['kind']=='native_hand_frame']),'maxbb':maxbb,'maxso':maxso,'inputs':len(expected),'input_unchanged':True},ensure_ascii=False))
if __name__=='__main__':run()
