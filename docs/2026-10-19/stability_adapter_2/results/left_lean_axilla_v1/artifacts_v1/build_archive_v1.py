from pathlib import Path
import hashlib, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
matplotlib.rcParams['font.family']='NanumGothic'
matplotlib.rcParams['axes.unicode_minus']=False

P = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1')
OUT = P / 'artifacts_v1'
V = Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1')
FONT_PATH = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
FONT = ImageFont.truetype(str(FONT_PATH), 24)
SMALL = ImageFont.truetype(str(FONT_PATH), 18)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def snap(path):
    p=Path(path); st=p.stat()
    return {'sha256':sha(p),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
def absframe(path):
    return Image.open(path).convert('RGB')
def fit(im, w, h):
    im=im.copy(); im.thumbnail((w,h),Image.Resampling.LANCZOS)
    canvas=Image.new('RGB',(w,h),'#f4f4f4'); canvas.paste(im,((w-im.width)//2,(h-im.height)//2)); return canvas

search=P/'search_v1/search.json'
source=json.loads(search.read_text())
inputs=set([search, P/'search_v2/search.json', P/'search_v3/search.json',
 P/'analysis_v2/verification.json', P/'analysis_v3/verification.json',
 P/'native_v1/left4deg/report.json',P/'native_v1/left4deg/media/capture.json',
 P/'native_v1/left4deg/media/initial_native.png',P/'native_v1/left4deg/media/whole_body.mp4',P/'native_v1/left4deg/media/hands.mp4',
 P/'native_v2/left4_nearbody/report.json',P/'native_v2/left4_nearbody/media/capture.json',
 P/'native_v2/left4_nearbody/media/initial_native.png',P/'native_v2/left4_nearbody/media/whole_body.mp4',P/'native_v2/left4_nearbody/media/hands.mp4',
 P/'native_v1/left4deg/media/frames/whole_body/00000.png',P/'native_v1/left4deg/media/frames/whole_body/00060.png',P/'native_v1/left4deg/media/frames/whole_body/00150.png',
 P/'native_v2/left4_nearbody/media/frames/whole_body/00000.png',P/'native_v2/left4_nearbody/media/frames/whole_body/00060.png',P/'native_v2/left4_nearbody/media/frames/whole_body/00150.png',
 Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v2/front160mm/media/initial_native.png'),FONT_PATH])
# Pin additional initial-state comparison capture.
baseimg=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v2/front160mm/media/initial_native.png')
before={str(p):snap(p) for p in sorted(inputs)}
before[str(Path(__file__))]=snap(__file__)
# Exact-copy the four completed native videos.
copy_rows=[]
for run,label in [('native_v1/left4deg','기타 4° 좌측 기울임'),('native_v2/left4_nearbody','좌측 기울임 + 기타 근접 이동')]:
    srcbase=P/run/'media'
    tag='left4deg' if run.startswith('native_v1') else 'left4_nearbody'
    for view in ['whole_body','hands']:
        src=srcbase/f'{view}.mp4'; dst=V/f'{tag}_{view}.mp4'
        if dst.exists():
            assert sha(src)==sha(dst), f'Existing archive copy differs: {dst}'
        else:
            shutil.copyfile(src,dst)
        assert sha(src)==sha(dst)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)]))['streams'][0]
        copy_rows.append({'source':str(src),'source_sha256':sha(src),'destination':str(dst),'copy_sha256':sha(dst),'label':label,'view':view,'ffprobe':probe})
# Source analytic capsule-to-convex gap chart from the search JSON.
rows={r['requested_chest_player_left_lean_deg']:r for r in source['rows']}
x=[0,4,8]
metrics=[('R_Shoulder','R_Shoulder capsule'),('proximal_upper_arm65_witness','Upper arm at 65%'),('R_Elbow','Forearm / elbow capsule')]
fig,ax=plt.subplots(figsize=(11,6.2),dpi=170)
colors=['#355c7d','#c06c84','#6c9a8b']
for (key,label),color in zip(metrics,colors):
    vals=[rows[a]['capsule_body'][key]['gap_m']*1000 if key in rows[a]['capsule_body'] else rows[a][key]['gap_m']*1000 for a in x]
    ax.plot(x,vals,marker='o',linewidth=2.8,markersize=8,label=label,color=color)
    for j,(xx,yy) in enumerate(zip(x,vals)):
        offset=(-24,11) if key=='R_Shoulder' and j==0 else ((25,11) if key=='R_Elbow' and j==0 else (0,9))
        ax.annotate(f'{yy:.3f}',(xx,yy),xytext=offset,textcoords='offset points',ha='center',fontsize=9)
ax.set_xlim(-0.55,8.45); ax.set_xticks(x,['0°','4°','8°']); ax.set_xlabel('추가 Chest 좌측 world 회전 (도)')
ax.set_ylabel('Source analytic gap (mm)'); ax.set_title('초기 자세에서의 source capsule–기타 표면 간격')
ax.grid(True,alpha=.25); ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),frameon=False)
fig.text(.01,.01,'Source 형상 분석만 표시합니다. Cooked PhysX 접촉·관통·겨드랑이 지지의 native 측정값이 아닙니다.',fontsize=9)
fig.tight_layout(rect=[0,.045,.80,1]); gap_png=OUT/'source_gap_comparison.png'; fig.savefig(gap_png,bbox_inches='tight'); plt.close(fig)
# Compose qualitative three-way initial native-render comparison.
initials=[baseimg,P/'native_v1/left4deg/media/initial_native.png',P/'native_v2/left4_nearbody/media/initial_native.png']
labels=['기준: natural_right_arm\nnative2 초기 자세','Pure left4 · native1\n초기 자세','Coupled · left4_nearbody\nnative2 초기 자세']
ims=[absframe(p) for p in initials]
w,h=520,293; band=70; title_h=42; gap=18
canvas=Image.new('RGB',(3*w+4*gap, h+band+title_h+3*gap),'white'); d=ImageDraw.Draw(canvas)
for i,(im,label) in enumerate(zip(ims,labels)):
    x0=gap+i*(w+gap); y0=gap+title_h+band
    canvas.paste(fit(im,w,h),(x0,y0)); d.multiline_text((x0,y0-band+2),label,font=SMALL,fill='#111111',spacing=5)
    d.rectangle((x0,y0,x0+w,y0+h),outline='#777777',width=2)
d.text((gap,8),'초기 native 렌더 3장 정성 비교',font=FONT,fill='#111111')
d.text((gap,36),'카메라와 기타 초기 위치가 달라 직접 치수 비교는 아닙니다.',font=SMALL,fill='#333333')
initial_png=OUT/'initial_pose_three_conditions.png'; canvas.save(initial_png)
# Compose actual native 0/2/5 s whole-body frames for two completed runs.
fig,axs=plt.subplots(2,3,figsize=(13.5,7.2),dpi=140)
for ri,(run,title) in enumerate([('native_v1/left4deg','native1 · left4deg'),('native_v2/left4_nearbody','native2 · left4_nearbody')]):
    for ci,(sec,idx) in enumerate([(0,'00000'),(2,'00060'),(5,'00150')]):
        im=absframe(P/run/f'media/frames/whole_body/{idx}.png')
        axs[ri,ci].imshow(im); axs[ri,ci].set_title(f'{title} · {sec}초',fontproperties=matplotlib.font_manager.FontProperties(fname=str(FONT_PATH),size=11))
        axs[ri,ci].axis('off')
fig.suptitle('실제 native whole_body 캡처 (0·2·5초)',fontproperties=matplotlib.font_manager.FontProperties(fname=str(FONT_PATH),size=16))
fig.text(.5,.01,'두 실행 모두 5초 완료. 프레임은 native camera 렌더이며, 화면상 겹침은 cooked clearance를 증명하지 않습니다.',ha='center',fontproperties=matplotlib.font_manager.FontProperties(fname=str(FONT_PATH),size=9))
fig.tight_layout(rect=[0,.04,1,.94]); timeline=OUT/'native_timeline_comparison.png'; fig.savefig(timeline,bbox_inches='tight'); plt.close(fig)
# Read-only hash verification for all pinned inputs.
after={k:snap(k) for k in before if k!=str(Path(__file__))}
after[str(Path(__file__))]=snap(__file__)
assert before==after, 'An input changed during postprocessing'
# Create Korean docs and manifest with exact-copy evidence.
manifest={'schema_version':1,'videos':copy_rows,'scope':'native1/native2 완료 5초 영상만 byte-exact 복사; 재인코딩/추가 native 실행 0회'}
(V/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
index='''# 영상 색인

## 기타 4° 좌측 기울임 · native1 (whole_body / hands)

![전신 영상: 실제 native camera, strap OFF, 5초 물리 구간](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/left4deg_whole_body.mp4)

![손 영상: 실제 native camera와 비물리 6현 overlay](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/left4deg_hands.mp4)

## 좌측 기울임 + 기타 근접 이동 · native2 (whole_body / hands)

![전신 영상: 실제 native camera, strap OFF, 5초 물리 구간](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/left4_nearbody_whole_body.mp4)

![손 영상: 실제 native camera와 비물리 6현 overlay](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/left4_nearbody_hands.mp4)

- [복사 SHA 및 ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/manifest_v1.json)
'''
(V/'INDEX.md').write_text(index)
readme=f'''# Left-lean axilla · source 분석과 native 비교

이번 보관본은 확정된 source 비교와 완료된 native1/native2 두 조건만 다룹니다. 추가 native3 조건은 이 문서에서 평가하거나 결론 내리지 않습니다.

![초기 native 장면 3조건 정성 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/initial_pose_three_conditions.png)

![source analytic capsule 간격 그래프](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/source_gap_comparison.png)

## Source 간격과 해석

Source search의 0°·4°·8° 추가 Chest 좌측 world 회전 비교에서 R_Shoulder capsule gap은 0.466·27.126·53.611 mm, upper arm 근위 65% witness gap은 18.523·42.256·65.897 mm, R_Elbow/전완 capsule gap은 1.315·12.402·28.496 mm였습니다. 이는 source analytic capsule와 convex 기타 표면 사이 간격이며 cooked native 접촉, 관통 여유, 겨드랑이 지지의 증거가 아닙니다. 66개 관절 scalar 값이 유지돼도 body의 world 회전으로 팔 world 위치는 변합니다.

초기 native 장면 세 장은 카메라와 기타 초기 위치가 다르므로 정성 비교입니다. pure left4°와 coupled 조건의 기타 초기 변위도 서로 다릅니다.

## 완료된 native 조건

![두 완료 native의 실제 0·2·5초 전신 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/native_timeline_comparison.png)

| 결과 | pure left4° · native1 | left4_nearbody · native2 |
|---|---:|---:|
| body bbox 중심 이동 | 187.876 mm | 205.134 mm |
| actor-root 이동 | 258.387 mm | 323.030 mm |
| 초기 대비 전체 SO(3) 회전 | 73.904° | 50.178° |
| 2→5초 body 중심 이동 / 회전 변화 | 0.614 mm / 0.237° | 35.083 mm / 13.212° |
| R_Shoulder 접촉 표본 | 0/1200 | 0/1200 |
| R_Forearm 접촉 표본 | 173/1200 | 346/1200 |
| Head 접촉 표본 | 782/1200 | 0/1200 |
| 왼팔·손 접촉 표본 | 0/1200 | 0/1200 |

두 조건은 각각 1200 physics step, 300 control, 5초 완료, strap OFF, policy/music 0입니다. 접촉 표본은 240 Hz endpoint count이며 force가 아닙니다. native1은 Head 접촉으로 거절됐습니다. native2는 Head 접촉과 왼팔 접촉은 없지만 R_Shoulder 접촉은 0/1200이고 기타 이동·회전도 커 유지에 실패했습니다. 작은 2→5초 변화만으로 목표 자세 유지라고 해석하지 않습니다.

영상의 6현은 실제 native camera 장면에 추가된 depth-tested 시각 overlay이며 물리 현이나 진동 모델이 아닙니다. [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX.md) · [SHA/ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/manifest_v1.json)

## 근거 자료

- [source search v1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/search_v1/search.json)
- [native1 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v2/verification.json) · [native2 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v3/verification.json)
- [native1 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/native_v1/left4deg/report.json) · [native2 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/native_v2/left4_nearbody/report.json)
'''
(OUT/'README_V1.md').write_text(readme)
# Pin outputs and changes.
changed=f'''# 변경 파일 색인

- [README_V1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/README_V1.md:1) — source 분석과 두 native 결과 설명
- [source_gap_comparison.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/source_gap_comparison.png) — source analytic gap 그래프
- [initial_pose_three_conditions.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/initial_pose_three_conditions.png) — 세 초기 native 캡처
- [native_timeline_comparison.png](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/native_timeline_comparison.png) — 두 native의 0·2·5초 캡처
- [provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/provenance_v1.json:1) — 입력·출력 SHA와 exact-copy 기록
- [INDEX.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX.md:1) — 영상 링크 색인
- [manifest_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/manifest_v1.json:1) — 4개 영상의 source/copy SHA와 ffprobe
- [build_archive_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/build_archive_v1.py:1) — 재현 가능한 후처리 producer
'''
(OUT/'CHANGED_FILES.md').write_text(changed)
outputs=[OUT/'source_gap_comparison.png',OUT/'initial_pose_three_conditions.png',OUT/'native_timeline_comparison.png',OUT/'README_V1.md',OUT/'CHANGED_FILES.md',V/'INDEX.md',V/'manifest_v1.json']+[Path(r['destination']) for r in copy_rows]
outinfo={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs}
# Include pinned input record (script itself is producer, self hash after final write).
provenance={'schema_version':1,'scope':'Source 분석과 native1/native2 완료 자료의 사후 시각화/바이트 exact 영상 보관; 물리/native/training 0회','inputs_before':before,'inputs_after':after,'input_hashes_unchanged':before==after,'producer_sha256':sha(__file__),'font_sha256':sha(FONT_PATH),'video_copies':copy_rows,'outputs_sha256_bytes':outinfo,'source_gaps_mm':{str(a):{'R_Shoulder':rows[a]['capsule_body']['R_Shoulder']['gap_m']*1000,'upper_arm_65pct':rows[a]['proximal_upper_arm65_witness']['gap_m']*1000,'R_Elbow_forearm':rows[a]['capsule_body']['R_Elbow']['gap_m']*1000} for a in x},'self_hash_note':'provenance는 자체 해시를 저장하지 않습니다.'}
prov=OUT/'provenance_v1.json'; prov.write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')

print(json.dumps({'video_count':len(copy_rows),'all_exact':all(v['source_sha256']==v['copy_sha256'] for v in copy_rows),'outputs':outinfo,'provenance_sha256':sha(prov),'readme_lines':len(readme.splitlines()),'index_lines':len(index.splitlines()),'changed_lines':len(changed.splitlines())},ensure_ascii=False,indent=2))
