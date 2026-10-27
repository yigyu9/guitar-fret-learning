from pathlib import Path
import hashlib,json,shutil,subprocess
from PIL import Image,ImageDraw,ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1')
OUT=P/'artifacts_v1'; V=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1')
FONT_PATH=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf'); fm.fontManager.addfont(str(FONT_PATH)); matplotlib.rcParams['font.family']='NanumGothic'; matplotlib.rcParams['axes.unicode_minus']=False
FONT=ImageFont.truetype(str(FONT_PATH),23); SMALL=ImageFont.truetype(str(FONT_PATH),18)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def snap(p):
 p=Path(p); s=p.stat(); return {'sha256':sha(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
def image(p):return Image.open(p).convert('RGB')
def fit(im,w,h):
 im=im.copy(); im.thumbnail((w,h),Image.Resampling.LANCZOS); c=Image.new('RGB',(w,h),'#f3f3f3');c.paste(im,((w-im.width)//2,(h-im.height)//2));return c

runs=[('native_v1/right4_close_support','right4_close_support','전완 motor-point 제어'),('native_v2/right4_close_support_upper_press','right4_close_support_upper_press','전완 + 상완 motor-point press')]
files=[Path(__file__),FONT_PATH,P/'result_summary_v1.json',P/'analysis_v2/verification.json',P/'analysis_v3/verification.json',P/'search_v5/search.json',P/'search_v5/right4_close_support/candidate.json',P/'search_v5/right4_close_support/config.json']
for run,_,_ in runs:
 root=P/run
 files += [root/'report.json',root/'initial_values.json',root/'trace.json',root/'media/capture.json',root/'media/whole_body.mp4',root/'media/hands.mp4',root/'media/frames/whole_body/00000.png',root/'media/frames/whole_body/00060.png',root/'media/frames/whole_body/00150.png',root/'media/initial_native.png']
before={str(f):snap(f) for f in sorted(set(files))}; before[str(Path(__file__))]=snap(__file__)
# Paired time panels (actual saved native whole_body frames), with caption bands outside imagery.
W,H=580,326; gap=18; header=78; label=36
canvas=Image.new('RGB',(3*W+4*gap,2*H+3*gap+header+2*label),'white'); d=ImageDraw.Draw(canvas)
d.text((gap,8),'몸통 player-right 기울임 조건 · 실제 native 전신 캡처',font=FONT,fill='#111')
d.text((gap,35),'player-right = 정면 화면 왼쪽 = 기타 몸통 쪽. 각 행은 동일 native 실행의 저장 프레임입니다.',font=SMALL,fill='#333')
for r,(run,tag,desc) in enumerate(runs):
 for c,(sec,frame) in enumerate([(0,'00000'),(2,'00060'),(5,'00150')]):
  x=gap+c*(W+gap); y=header+gap+r*(H+label+gap)
  d.text((x,y-label+2),f'{desc} · {sec}초',font=SMALL,fill='#111')
  src=P/run/f'media/frames/whole_body/{frame}.png'; canvas.paste(fit(image(src),W,H),(x,y)); d.rectangle((x,y,x+W,y+H),outline='#888',width=2)
panel=OUT/'native_timeline_0_2_5s.png'; canvas.save(panel)
# Side-by-side initial image pair (also the first timeline column, shown larger).
ims=[]
for run,_,_ in runs: ims.append(image(P/run/'media/frames/whole_body/00000.png'))
w,h=640,360; gap=20; band=48
pair=Image.new('RGB',(2*w+3*gap,h+band+2*gap),'white'); draw=ImageDraw.Draw(pair)
for i,(im,lab) in enumerate(zip(ims,['초기 자세 · 전완 motor-point','초기 자세 · 전완 + 상완 motor-point press'])):
 x=gap+i*(w+gap); y=band+gap; draw.text((x,8),lab,font=SMALL,fill='#111'); pair.paste(fit(im,w,h),(x,y));draw.rectangle((x,y,x+w,y+h),outline='#888',width=2)
initial=OUT/'initial_native_pair.png'; pair.save(initial)
# Exact copy four video files and probe the resulting streams.
video_rows=[]
for run,tag,label in runs:
 media=P/run/'media'
 for view in ['whole_body','hands']:
  src=media/f'{view}.mp4'; dst=V/f'{tag}_{view}.mp4'
  if dst.exists(): assert sha(src)==sha(dst)
  else: shutil.copyfile(src,dst)
  assert sha(src)==sha(dst)
  info=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)]))['streams'][0]
  video_rows.append({'source':str(src),'source_sha256':sha(src),'destination':str(dst),'copy_sha256':sha(dst),'label':label,'view':view,'ffprobe':info})
manifest={'schema_version':1,'videos':video_rows,'scope':'두 완료 native 영상 4개 바이트 exact-copy; 재인코딩/native/training 0회'}
(V/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
index='''# 영상 색인 · body-side lean axilla

## 전완 motor-point 조건 · native1

![전신 native 카메라 영상 · strap OFF](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/right4_close_support_whole_body.mp4)

![손 native 카메라 영상 · 6현은 비물리 시각 overlay](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/right4_close_support_hands.mp4)

## 전완 + 상완 motor-point press · native2

![전신 native 카메라 영상 · strap OFF](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/right4_close_support_upper_press_whole_body.mp4)

![손 native 카메라 영상 · 6현은 비물리 시각 overlay](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/right4_close_support_upper_press_hands.mp4)

- [source/copy SHA와 ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/manifest_v1.json)
'''
(V/'INDEX_V1.md').write_text(index)
summary=json.loads((P/'result_summary_v1.json').read_text())
cases=[summary['cases']['forearm'],summary['cases']['forearm_upper_press']]
readme='''# Body-side lean axilla · 두 native 조건 기록

두 실행은 확정된 동일 full native initial state에서 각각 5.0 physics초 완료된 진단입니다. 두 MP4는 151프레임·30fps로 인코딩되어 재생 길이는 5.033333초입니다. root/lower body는 고정, strap OFF, 기타는 자유, 왼손 grip 없음, 기타에 직접 힘을 가하지 않았습니다. 기존 source v5 candidate는 그대로 보존했습니다. 방향은 사용자가 확인한 정의인 player-right = 정면 화면 왼쪽 = 기타 몸통 쪽이며, 몸통 추가 회전은 Chest 4°, Torso 1°, Spine 2.5°입니다.

![동일 방향 표기의 초기 native 장면 두 조건](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/artifacts_v1/initial_native_pair.png)

![두 조건의 실제 native 전신 0·2·5초 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/artifacts_v1/native_timeline_0_2_5s.png)

| 관측값 | 전완 motor-point · native1 | 전완 + 상완 motor-point press · native2 |
|---|---:|---:|
| body bbox 중심 최종 이동 | 48.051 mm | 47.501 mm |
| 초기 대비 전체 SO(3) 회전 | 52.174° | 47.662° |
| neck G+Y elevation 최종 | −15.921° | −10.019° |
| 2→5초 body 중심 이동 / 회전 변화 | 0.310 mm / 0.317° | 0.316 mm / 0.494° |
| 오른 상완 접촉 표본, 240 Hz endpoints | 968/1200 | 256/1200 |
| 오른 전완 접촉 표본, 240 Hz endpoints | 1191/1200 | 1149/1200 |
| 왼팔·Head 접촉 표본, 각각 | 0/1200 | 0/1200 |
| R_Shoulder, 60 Hz pre-control presence 표본 | 242/300 | 64/300 |

Neck G+Y elevation은 몸통에서 넥 방향으로 향하는 축의 world 수평 기준 부호 각도이며 전체 SO(3) 크기가 아닙니다. 60 Hz pre-control contact 표본은 별도 관측이며 240 Hz의 1200 after-step endpoint 표본과 합산하지 않습니다. Contact/raw lambda는 접촉 빈도 기록이지 측정힘이 아닙니다.

두 조건 모두 2→5초 변화는 작지만 이미 잘못된 자세 방향으로 이동한 뒤 정착한 상태입니다. 따라서 안정된 초기 자세 유지나 연주 성공으로 판단하지 않습니다. 상완 motor-point 요청은 사람 관절 effort를 통한 상완의 목표 접근이며 실제 측정 힘이 아닙니다. 상완 접촉 감소와 함께 neck elevation·전체 회전이 남아 있어 상완 지지가 해결됐다고 단정할 수 없습니다. Source 기하·capsule 간격은 cooked PhysX 접촉/여유를 증명하지 않습니다.

두 영상의 각 장면은 실제 Isaac Gym native camera입니다. 6현은 물리 추가가 없는 시각 overlay이며 gauge·진동을 모델링하지 않습니다. [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/INDEX_V1.md) · [source/copy SHA 및 ffprobe](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/manifest_v1.json)

- [결과 summary](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/result_summary_v1.json)
- [native1 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/analysis_v2/verification.json) · [native2 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/analysis_v3/verification.json)
'''
(OUT/'README_V1.md').write_text(readme)
# All pinned files must remain unchanged while postprocessing.
after={k:snap(k) for k in before if k!=str(Path(__file__))}; after[str(Path(__file__))]=snap(__file__); assert before==after
changed='''# 변경 파일 색인

- [README_V1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/artifacts_v1/README_V1.md:1) — 확정된 두 native 조건의 한국어 결과 설명
- [initial_native_pair.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/artifacts_v1/initial_native_pair.png) — 실제 0초 native 프레임 비교
- [native_timeline_0_2_5s.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/artifacts_v1/native_timeline_0_2_5s.png) — 실제 0·2·5초 전신 프레임
- [provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/artifacts_v1/provenance_v1.json:1) — 입력 전후와 출력 SHA 기록
- [build_archive_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/artifacts_v1/build_archive_v1.py:1) — 후처리 producer
- [INDEX_V1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/INDEX_V1.md:1) — 영상 색인
- [manifest_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/manifest_v1.json:1) — source/copy SHA 및 ffprobe
'''
(OUT/'CHANGED_FILES.md').write_text(changed)
outputs=[OUT/'README_V1.md',OUT/'CHANGED_FILES.md',OUT/'initial_native_pair.png',OUT/'native_timeline_0_2_5s.png',V/'INDEX_V1.md',V/'manifest_v1.json']+[Path(r['destination']) for r in video_rows]
outmeta={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs}
prov={'schema_version':1,'scope':'두 완료 native trial의 시각화/바이트 exact video archive; native/training/re-encoding 0회','inputs_before':before,'inputs_after':after,'input_hashes_unchanged':before==after,'font_sha256':sha(FONT_PATH),'producer_sha256':sha(__file__),'video_copies':video_rows,'outputs_sha256_bytes':outmeta,'self_hash_note':'이 파일 자체의 해시는 포함하지 않습니다.'}
(OUT/'provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'videos':len(video_rows),'exact':all(r['source_sha256']==r['copy_sha256'] for r in video_rows),'old_inputs_unchanged':before==after,'outputs':outmeta,'producer_sha':sha(__file__),'provenance_sha':sha(OUT/'provenance_v1.json')},ensure_ascii=False,indent=2))
