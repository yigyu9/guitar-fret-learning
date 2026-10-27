from pathlib import Path
import hashlib, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1')
OUT=P/'artifacts_v1'; V=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1')
FONT_PATH=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf'); fm.fontManager.addfont(str(FONT_PATH)); matplotlib.rcParams['font.family']='NanumGothic'; matplotlib.rcParams['axes.unicode_minus']=False
FONT=ImageFont.truetype(str(FONT_PATH),21); SMALL=ImageFont.truetype(str(FONT_PATH),17)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def snap(p):
 p=Path(p); st=p.stat(); return {'sha256':sha(p),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
def readimg(p): return Image.open(p).convert('RGB')
def fit(im,w,h):
 im=im.copy(); im.thumbnail((w,h),Image.Resampling.LANCZOS); c=Image.new('RGB',(w,h),'#f3f3f3'); c.paste(im,((w-im.width)//2,(h-im.height)//2)); return c

cases=[('natural_right_arm reference',Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v2/front160mm/media/initial_native.png')),
 ('native1 · pure left4°',P/'native_v1/left4deg/media/initial_native.png'),
 ('native2 · coupled',P/'native_v2/left4_nearbody/media/initial_native.png'),
 ('native3 · upper press',P/'native_v3/left4_nearbody_upper_press/media/initial_native.png')]
source_files=[Path(__file__),FONT_PATH,P/'search_v1/search.json',P/'search_v2/search.json',P/'search_v3/search.json',P/'analysis_v2/verification.json',P/'analysis_v3/verification.json',P/'analysis_v4/verification.json',P/'native_v3/left4_nearbody_upper_press/report.json',P/'native_v3/left4_nearbody_upper_press/initial_values.json',P/'native_v3/left4_nearbody_upper_press/media/capture.json',P/'native_v3/left4_nearbody_upper_press/media/effort_configuration.json',P/'native_v3/left4_nearbody_upper_press/media/frames/whole_body/00000.png',P/'native_v3/left4_nearbody_upper_press/media/frames/whole_body/00060.png',P/'native_v3/left4_nearbody_upper_press/media/frames/whole_body/00150.png',P/'native_v3/left4_nearbody_upper_press/media/whole_body.mp4',P/'native_v3/left4_nearbody_upper_press/media/hands.mp4',OUT/'README_V1.md',OUT/'CHANGED_FILES.md',OUT/'build_archive_v1.py',OUT/'provenance_v1.json',OUT/'native_timeline_comparison.png',OUT/'initial_pose_three_conditions.png',OUT/'source_gap_comparison.png',V/'manifest_v1.json',V/'INDEX.md',V/'left4deg_whole_body.mp4',V/'left4deg_hands.mp4',V/'left4_nearbody_whole_body.mp4',V/'left4_nearbody_hands.mp4']
source_files += [p for _,p in cases]
source_files += [P/f'native_v{i}/{case}/media/frames/whole_body/{frame}.png' for i,case in [(1,'left4deg'),(2,'left4_nearbody')] for frame in ['00000','00060','00150']]
before={str(p):snap(p) for p in sorted(set(source_files))}; before[str(Path(__file__))]=snap(__file__)
# Construct four-way initial comparison from saved native screenshots.
w,h=400,225; gap=16; band=54; title_h=52
canvas=Image.new('RGB',(4*w+5*gap,h+band+title_h+3*gap),'white'); draw=ImageDraw.Draw(canvas)
draw.text((gap,5),'초기 native 캡처 정성 비교',font=FONT,fill='#111')
draw.text((gap,31),'각 실행의 카메라/초기 기타 위치가 달라 거리·정렬 비교로 해석하지 않습니다.',font=SMALL,fill='#333')
for i,(label,path) in enumerate(cases):
 x=gap+i*(w+gap); y=gap+title_h+band
 canvas.paste(fit(readimg(path),w,h),(x,y)); draw.multiline_text((x,y-band+3),label,font=SMALL,fill='#111',spacing=4); draw.rectangle((x,y,x+w,y+h),outline='#888',width=2)
initial_png=OUT/'initial_pose_four_conditions_v2.png'; canvas.save(initial_png)
# Actual whole-body frames at 0/2/5 sec for all completed native cases.
fig,axs=plt.subplots(3,3,figsize=(13.2,9.2),dpi=135)
for ri,(run,label) in enumerate([('native_v1/left4deg','native1 · pure left4°'),('native_v2/left4_nearbody','native2 · coupled'),('native_v3/left4_nearbody_upper_press','native3 · upper press')]):
 for ci,(sec,frame) in enumerate([(0,'00000'),(2,'00060'),(5,'00150')]):
  p=P/run/f'media/frames/whole_body/{frame}.png'; axs[ri,ci].imshow(readimg(p)); axs[ri,ci].axis('off'); axs[ri,ci].set_title(f'{label} · {sec}초',fontsize=10)
fig.suptitle('세 완료 native 조건의 실제 whole_body 프레임 (0·2·5초)',fontsize=15)
fig.text(.5,.01,'각 실행 5.0 physics초 완료. 영상은 native camera 렌더와 depth-tested 6현 overlay이며, 화면 겹침은 cooked 관통 여부를 증명하지 않습니다.',ha='center',fontsize=9)
fig.tight_layout(rect=[0,.035,1,.96]); timeline=OUT/'native_timeline_comparison_v2.png'; fig.savefig(timeline,bbox_inches='tight'); plt.close(fig)
# Exact copy only the newly completed native3 pair. Existing four V1 copies remain untouched.
oldman=json.loads((V/'manifest_v1.json').read_text()); copy_rows=list(oldman['videos'])
run=P/'native_v3/left4_nearbody_upper_press/media'
for view in ['whole_body','hands']:
 src=run/f'{view}.mp4'; dst=V/f'left4_nearbody_upper_press_{view}.mp4'
 if dst.exists(): assert sha(src)==sha(dst)
 else: shutil.copyfile(src,dst)
 assert sha(src)==sha(dst)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)]))['streams'][0]
 copy_rows.append({'source':str(src),'source_sha256':sha(src),'destination':str(dst),'copy_sha256':sha(dst),'label':'좌측 기울임 + 기타 근접 이동 + 오른 상완 motor-point press · native3','view':view,'ffprobe':probe})
# Docs refer to authoritative records and preserve all prior metrics.
newmanifest={'schema_version':2,'videos':copy_rows,'scope':'native1/native2 기존 영상 4개 유지, native3 whole_body/hands 2개 exact-copy 추가; 재인코딩/native 추가 실행 0회'}
(V/'manifest_v2.json').write_text(json.dumps(newmanifest,ensure_ascii=False,indent=2)+'\n')
index='''# 영상 색인 V2

## Native1 · pure left4°

![전신 영상 · strap OFF, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/left4deg_whole_body.mp4)
![손 영상 · 6현은 비물리 visual overlay](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/left4deg_hands.mp4)

## Native2 · coupled nearbody

![전신 영상 · strap OFF, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/left4_nearbody_whole_body.mp4)
![손 영상 · 6현은 비물리 visual overlay](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/left4_nearbody_hands.mp4)

## Native3 · coupled nearbody + upper motor-point press

![전신 영상 · strap OFF, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/left4_nearbody_upper_press_whole_body.mp4)
![손 영상 · 6현은 비물리 visual overlay](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/left4_nearbody_upper_press_hands.mp4)

- [6개 영상의 source/copy SHA와 ffprobe](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/manifest_v2.json)
'''
(V/'INDEX_V2.md').write_text(index)
readme='''# Left-lean axilla · native1–3 비교

V2는 기존 V1을 보존하고, 완료된 native3 조건과 두 영상을 추가한 후속 문서입니다. Native1=pure left4°, native2=coupled left4_nearbody, native3=같은 coupled 초기 조건에서 기존 전완 motor-point 제어에 상완 motor-point press를 더한 조건입니다. Native2/native3의 initial81, joint q 및 기타 초기 상태는 exact match입니다. 세 실행 모두 1200 physics step·300 control·5.0 physics초 완료, training/policy/music 0, strap OFF입니다. Native3 상완 점은 사람 관절 effort로 작동하며 기타에 직접 힘을 가하지 않습니다. 이 비교는 순수 수동과 능동을 비교하는 시험이 아닙니다. Native2도 전완 controller가 활성화돼 있습니다.

![세 완료 native의 실제 0·2·5초 whole_body 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/native_timeline_comparison_v2.png)

![기준·native1·native2·native3의 초기 native 장면 정성 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/initial_pose_four_conditions_v2.png)

| 관측값 | native1 · pure left4° | native2 · coupled | native3 · upper press |
|---|---:|---:|---:|
| body bbox 중심 이동 | 187.876 mm | 205.134 mm | 203.862 mm |
| actor-root 이동 | 258.387 mm | 323.030 mm | 319.918 mm |
| 초기 대비 전체 SO(3) 회전 | 73.904° | 50.178° | 49.689° |
| 2→5초 body 중심 이동 / 회전 변화 | 0.614 mm / 0.237° | 35.083 mm / 13.212° | 32.609 mm / 12.603° |
| R_Shoulder 접촉 표본 | 0/1200 | 0/1200 | 0/1200 |
| R_Forearm 접촉 표본 | 173/1200 | 346/1200 | 351/1200 |
| Head 접촉 표본 | 782/1200 | 0/1200 | 847/1200 |
| 왼팔·손 접촉 표본 | 0/1200 | 0/1200 | 0/1200 |

접촉 수는 240 Hz endpoint 표본이며 힘 단위가 아닙니다. Native3의 상완 motor-point 최대 요청 norm은 21.392 N이며 point별 cap은 30 N입니다. 실제 R_Shoulder 접촉은 0/1200으로, 상완 motor-point 요청만으로 겨드랑이 접촉 지지가 확인된 것은 아닙니다. Head 접촉 847/1200 (positive raw lambda 846)과 전체 회전 49.689° 때문에 native3은 거절 조건입니다. Raw lambda는 N 단위 힘이 아닙니다. Native1은 Head 접촉으로 거절됐고, native2는 R_Shoulder 접촉 0/1200 및 큰 위치 이동으로 기타 유지에 실패했습니다. 어느 조건도 유지·연주 성공으로 판정하지 않습니다.

이 문서에서 방향 표기는 player-left=넥 쪽(정면 화면 오른쪽)으로 두며, 방향 표현에 대한 사용자 확인은 대기 중입니다. 상완점은 해당 초기 world target에 향하는 사람 관절 effort 점이고, 기타에 직접 힘을 가하지 않습니다. source gap은 source analytic 간격이며 cooked contact/clearance 인증이 아닙니다. 화면상 겹침 역시 cooked 관통을 증명하지 않습니다.

- [V1 source 비교와 이전 두 native 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/README_V1.md)
- [영상 색인 V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX_V2.md) · [6개 영상 SHA/ffprobe manifest V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/manifest_v2.json)
- [Native3 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v4/verification.json) · [native3 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/native_v3/left4_nearbody_upper_press/report.json)
- [V1 source gap comparison](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/source_gap_comparison.png)
'''
(OUT/'README_V2.md').write_text(readme)
# Verify all source inputs stayed byte-unchanged.
after={k:snap(k) for k in before if k!=str(Path(__file__))}; after[str(Path(__file__))]=snap(__file__); assert before==after
# Changed-file index before hashing final outputs.
changed='''# 변경 파일 색인 V2

- [README_V2.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/README_V2.md:1) — 세 native 조건 표와 native3 해석
- [native_timeline_comparison_v2.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/native_timeline_comparison_v2.png) — 3×3 실제 캡처 패널
- [initial_pose_four_conditions_v2.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/initial_pose_four_conditions_v2.png) — 4개 초기 장면
- [provenance_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/provenance_v2.json:1) — SHA 입력/출력 및 복사 근거
- [build_archive_v2.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/build_archive_v2.py:1) — 후처리 producer
- [INDEX_V2.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX_V2.md:1) — 여섯 영상 링크 색인
- [manifest_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/manifest_v2.json:1) — 여섯 영상 source/copy SHA와 ffprobe
'''
(OUT/'CHANGED_FILES_V2.md').write_text(changed)
outputs=[OUT/'README_V2.md',OUT/'CHANGED_FILES_V2.md',OUT/'native_timeline_comparison_v2.png',OUT/'initial_pose_four_conditions_v2.png',V/'INDEX_V2.md',V/'manifest_v2.json']+[Path(r['destination']) for r in copy_rows]
outmeta={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs}
prov={'schema_version':2,'scope':'native3 결과 추가 후처리; 기존 V1 files/4 videos 불변, native/training 0회','inputs_before':before,'inputs_after':after,'existing_inputs_unchanged':before==after,'producer_sha256':sha(__file__),'font_sha256':sha(FONT_PATH),'videos':copy_rows,'outputs_sha256_bytes':outmeta,'native3_summary':{'body_bbox_center_mm':203.86217517681837,'actor_root_mm':319.91792554053956,'total_rotation_deg':49.68852709991474,'body_center_2_to_5_mm':32.60870404560697,'rotation_2_to_5_deg':12.603049681207906,'R_Shoulder_contacts':0,'R_Forearm_contacts':351,'Head_contacts':847,'Head_positive_raw_lambda':846,'upper_point_max_request_norm_N':21.391732088622046,'upper_point_cap_N':30,'physics_steps':1200,'controls':300,'physics_seconds':5.0},'self_hash_note':'이 provenance 파일 자체의 해시는 포함하지 않습니다.'}
provpath=OUT/'provenance_v2.json'; provpath.write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'videos':len(copy_rows),'new_copies':2,'all_exact':all(r['source_sha256']==r['copy_sha256'] for r in copy_rows),'old_inputs_unchanged':before==after,'outputs':outmeta,'provenance_sha256':sha(provpath),'producer_sha256':sha(__file__)},ensure_ascii=False,indent=2))
