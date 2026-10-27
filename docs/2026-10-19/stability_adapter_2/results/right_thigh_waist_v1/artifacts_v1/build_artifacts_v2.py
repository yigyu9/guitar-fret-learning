#!/usr/bin/env python3
"""Create corrected waist XY projection and README V2; preserve every V1 output."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json

BASE=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1')
ART=BASE/'artifacts_v1'
VIDEO=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_thigh_waist_v1')
BRIEF=BASE/'artifact_brief_v1.json'
ANALYSIS=BASE/'analysis_final_v1/analysis.json'
SOURCE_AUDIT=BASE/'search_v4/shift95_front30mm_audit.json'
A_MANIFEST=Path('/home/ajou/yigyu/3/stability_adapter_2/assets/om_body_geometry_v3/manifest.json')
D_MANIFEST=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/guitar/geometry_v3_manifest.json')
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
OUT_PNG=ART/'waist_profile_contacts_v2.png'
OUT_README=ART/'README_V2.md'
OUT_PROV=ART/'provenance_v2.json'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def record(p):
    p=Path(p); s=p.stat()
    return {'sha256':sha(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}

def font(sz): return ImageFont.truetype(str(FONT),sz)
def center(d,x,y,txt,ft,fill):
    b=d.textbbox((0,0),txt,font=ft); d.text((x-(b[2]-b[0])/2,y),txt,font=ft,fill=fill)

brief=json.loads(BRIEF.read_text())
analysis=json.loads(ANALYSIS.read_text())
source_audit=json.loads(SOURCE_AUDIT.read_text())
a_manifest=json.loads(A_MANIFEST.read_text())
# Pin files directly used by the V2 image and document; include the consumed V1 lineage and linked media manifest.
inputs=[BRIEF,ANALYSIS,SOURCE_AUDIT,A_MANIFEST,D_MANIFEST,FONT,
        ART/'build_artifacts_v1.py',ART/'provenance_v1.json',ART/'README_V1.md',ART/'waist_profile_contacts_v1.png',
        ART/'initial_whole_comparison_v1.png',ART/'initial_side_comparison_v1.png',ART/'elbow5_whole_0_3_5_v1.png',ART/'elbow5_hands_0_3_5_v1.png',
        VIDEO/'manifest_v1.json',VIDEO/'INDEX_V1.md',VIDEO/'README_V1.md',
        BASE/'native_elbow5_v1/report.json',BASE/'native_elbow5_v1/initial_values.json',BASE/'native_elbow5_v1/trace.json',BASE/'native_elbow5_v1/media/capture.json',
        BASE/'native_static_v2/report.json',BASE/'native_static_v2/initial_values.json',BASE/'native_static_v2/trace.json',BASE/'native_static_v2/media/capture.json',
        BASE/'native_static_v1/report.json',BASE/'native_static_v1/media/capture.json',
        BASE/'native_elbow5_v1/media/frames/whole_body/00000.png',BASE/'native_elbow5_v1/media/frames/whole_body/00090.png',BASE/'native_elbow5_v1/media/frames/whole_body/00150.png',
        BASE/'native_elbow5_v1/media/frames/hands/00000.png',BASE/'native_elbow5_v1/media/frames/hands/00090.png',BASE/'native_elbow5_v1/media/frames/hands/00150.png',
        BASE/'native_elbow5_v1/media/initial_support_side.png',BASE/'native_static_v2/media/initial_support_side.png']
# Include the V2 producer itself in the before/after closure.
inputs.append(Path(__file__))
inputs_before={str(p):record(p) for p in inputs}
# Check manifest/source audit pins when available from approved brief/canonical outputs.
if str(ANALYSIS) in brief['input_sha256'] and sha(ANALYSIS)!=brief['input_sha256'][str(ANALYSIS)]:
    raise RuntimeError('canonical analysis SHA does not match brief')
L=float(a_manifest['new_body_length_m'])
profile=a_manifest['half_width_profile_t_m']
waist=analysis['waist_regions']['native_elbow5_v1']
ylo,yhi=[float(v) for v in source_audit['waist_G_y_interval_m']]
corelo,corehi=[float(v) for v in source_audit['waist_core_G_y_interval_m']]
if abs(ylo+0.36556297983)>1e-10 or abs(yhi+0.2782405358275)>1e-10:
    raise RuntimeError('source flank interval differs from approved interval')
if abs(corelo+0.3471145761675)>1e-10 or abs(corehi+0.3028384073775)>1e-10:
    raise RuntimeError('source core interval differs from approved interval')
def map_y(t): return -0.4 + L*(0.5-float(t))
assert abs(map_y(0)-(-0.1540212845))<1e-8
assert abs(map_y(1)-(-0.6459787155))<1e-8
assert abs(map_y(.345)-(-0.323746598195))<1e-9

# Full-body plan outline and contacts, in native guitar-local G coordinates.
W,H=1700,1270
im=Image.new('RGB',(W,H),(250,250,250));d=ImageDraw.Draw(im)
center(d,W//2,22,'기타 G 프레임: 원본 반폭 윤곽과 실제 native waist contact 좌표 XY 투영',font(29),(18,18,18))
center(d,W//2,63,'A asset manifest의 t에서 G_Y 역방향 mapping 사용 · XY 좌표 도식 · Z 제외 · native 렌더 아님',font(20),(55,55,55))
xmin,xmax=-.205,.205;ymin,ymax=-.67,-.12
left,right,top,bottom=175,1510,145,1010
def px(x,y): return (left+(x-xmin)/(xmax-xmin)*(right-left),bottom-(y-ymin)/(ymax-ymin)*(bottom-top))
# grid and tick labels
for x in [-.2,-.15,-.1,-.05,0,.05,.1,.15,.2]:
    xx,_=px(x,ymin);d.line((xx,top,xx,bottom),fill=(224,224,224),width=1);center(d,xx,bottom+7,f'{x:.2f}',font(16),(60,60,60))
for y in [-.65,-.6,-.55,-.5,-.45,-.4,-.35,-.3,-.25,-.2,-.15]:
    _,yy=px(xmin,y);d.line((left,yy,right,yy),fill=(224,224,224),width=1);d.text((left-77,yy-10),f'{y:.2f}',font=font(16),fill=(60,60,60))
d.rectangle((left,top,right,bottom),outline=(40,40,40),width=2)
# Convert the plan outline parameter t to local G_Y with tail-to-neck reversal.
prof=[(float(t),float(hw)) for t,hw in profile]
outline_pos=[(hw,map_y(t)) for t,hw in prof]
outline_neg=[(-hw,map_y(t)) for t,hw in prof]
# Shade only horizontal Y bands, inside the positive-GX half (lower-edge side); no outward rings.
flank_poly=[px(0,ylo),px(0,yhi)]+[px(hw,map_y(t)) for t,hw in reversed(prof) if ylo<=map_y(t)<=yhi]
# Build band as an axis-aligned horizontal rectangle clipped visually to the source body outline by scan strips.
# Draw broad flank and narrower core tint only between centerline and the local positive half-width.
for low,high,color in [(ylo,yhi,(250,235,204)),(corelo,corehi,(246,194,110))]:
    steps=240
    for i in range(steps):
        ya=low+(high-low)*i/steps; yb=low+(high-low)*(i+1)/steps
        tmid=.5-(.5*((ya+yb)/2 + .4)/L)
        tmid=max(0,min(1,tmid))
        hw=min(float(v[1]) for v in prof) if not prof else min(prof,key=lambda q:abs(q[0]-tmid))[1]
        xa,ya_px=px(0,ya); xb,yb_px=px(hw,yb)
        d.rectangle((xa,min(ya_px,yb_px),xb,max(ya_px,yb_px)),fill=color)
# Source silhouette after bands so actual edge remains sharp.
d.polygon([px(*q) for q in outline_pos+list(reversed(outline_neg))],fill=(213,218,224),outline=(38,48,58))
# Reapply band shading atop the silhouette, still bounded by local half-width (no ring beyond outline).
for low,high,color in [(ylo,yhi,(249,228,187)),(corelo,corehi,(242,178,78))]:
    steps=240
    for i in range(steps):
        ya=low+(high-low)*i/steps;yb=low+(high-low)*(i+1)/steps;ym=(ya+yb)/2
        tmid=.5-((ym+.4)/L);tmid=max(0,min(1,tmid));hw=min(prof,key=lambda q:abs(q[0]-tmid))[1]
        xa,yap=px(0,ya);xb,ybp=px(hw,yb);d.rectangle((xa,min(yap,ybp),xb,max(yap,ybp)),fill=color)
# redraw source edge on top
for curve in [outline_pos,outline_neg]: d.line([px(*q) for q in curve],fill=(38,48,58),width=3)
# Actual XY contact samples from canonical analysis; show early/late windows and raw-positive state via marker fill.
for row in waist['contact_points_G_m']:
    step=int(row['physics_step'])
    if step<=120: color=(31,101,190); shape='early'
    elif step>=1080: color=(190,48,115); shape='late'
    else: continue
    x,y=float(row['point_G_m'][0]),float(row['point_G_m'][1]); xx,yy=px(x,y);r=3
    if row['positive_raw_lambda']:
        if shape=='early': d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=color,outline=(25,35,45))
        else: d.polygon([(xx,yy-r-1),(xx-r-1,yy+r),(xx+r+1,yy+r)],fill=color,outline=(55,30,45))
    else:
        if shape=='early':d.ellipse((xx-r,yy-r,xx+r,yy+r),outline=color,width=2)
        else:d.polygon([(xx,yy-r-1),(xx-r-1,yy+r),(xx+r+1,yy+r)],outline=color)
# Axis labels and footer legend outside data area.
center(d,(left+right)//2,H-194,'G_X (m) · 양의 G_X가 기타의 아래쪽 edge 방향',font(20),(20,20,20))
label=Image.new('RGBA',(140,38),(250,250,250,0)); ld=ImageDraw.Draw(label); ld.text((0,4),'G_Y (m)',font=font(20),fill=(20,20,20)); label=label.rotate(90,expand=True); im.paste(label,(26,(top+bottom-label.height)//2),label)
# bands are strictly horizontal intervals on positive-X interior, not widened rings outside contour.
ly=H-135
d.rectangle((190,ly+3,211,ly+22),fill=(213,218,224),outline=(38,48,58));d.text((220,ly-1),'A manifest 원본 평면 윤곽',font=font(17),fill=(25,25,25))
d.rectangle((480,ly+3,501,ly+22),fill=(249,228,187));d.text((510,ly-1),'flank: G_Y [-0.365562980, -0.278240536] m · half-width ≤ min+15 mm',font=font(17),fill=(25,25,25))
d.rectangle((1090,ly+3,1111,ly+22),fill=(242,178,78));d.text((1120,ly-1),'core: G_Y [-0.347114576, -0.302838407] m · min+5 mm',font=font(17),fill=(25,25,25))
ly2=H-99
d.ellipse((345,ly2+4,359,ly2+18),fill=(31,101,190),outline=(25,35,45));d.text((368,ly2),'초기 0–0.5 s',font=font(17),fill=(25,25,25))
d.polygon([(540,ly2+2),(532,ly2+18),(548,ly2+18)],fill=(190,48,115),outline=(55,30,45));d.text((557,ly2),'후기 4.5–5 s',font=font(17),fill=(25,25,25))
d.text((190,H-60),'band는 source half-width ≤ minimum+5/+15 mm가 만드는 G_Y 구간을 x≥0 측 안쪽에 수평으로 표시; 윤곽 밖 ring이 아님.',font=font(17),fill=(45,45,45))
d.text((190,H-34),'점은 canonical native contact_points_G_m의 XY 투영(z 제외). 채움=positive raw lambda, 빈 기호=0. 이는 힘(N)/cooked clearance/연속접촉 증명이 아님.',font=font(17),fill=(45,45,45))
im.save(OUT_PNG)

# Build corrected README by preserving the existing text and replacing only incorrect waist/units/range/interpretation passages.
text=(ART/'README_V1.md').read_text(encoding='utf-8')
text=text.replace('# 오른쪽 허벅지·waist 배치 native 보관','# 오른쪽 허벅지·waist 배치 native 보관 · 정정판 V2')
text=text.replace("![기타 G 프레임에서 원본 윤곽과 native contact 좌표 XY 투영](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/waist_profile_contacts_v1.png)","![정정된 기타 G 프레임 윤곽·waist interval·native 접촉좌표 XY 투영](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/waist_profile_contacts_v2.png)")
old_chart='''윤곽은 [geometry manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/guitar/geometry_v3_manifest.json)의 `half_width_profile_t_m`을 이용해 `G_Y = -0.4 + t × 0.491957431 m`로 배치했습니다. 양의 `G_X`는 기타의 아래쪽 edge 방향입니다. 그림의 core `+5 mm`와 flank `+15 mm` 구간 및 실제 native 접촉좌표는 서로 다른 근거로 표시했습니다. 점은 z를 버린 XY 투영이며, 초기 0–0.5초와 후기 4.5–5초 표본만 색을 달리합니다. 이 도식은 native 렌더 이미지가 아니며, cooked 형상·힘·연속 접촉을 인증하지 않습니다.'''
new_chart='''V1 [그림](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/waist_profile_contacts_v1.png)은 t축 방향을 뒤집어 배치하고 core/flank을 윤곽 밖 ring처럼 그려 좌표와 범위가 잘못됐습니다. V1은 오류 이력으로 보존합니다. V2는 A asset manifest(`/home/ajou/yigyu/3/stability_adapter_2/assets/om_body_geometry_v3/manifest.json`)의 `half_width_profile_t_m`과 `G_Y = -0.4 + L × (0.5 - t)`를 사용합니다(L=0.491957431 m: t=0 neck end G_Y≈-0.154021 m, t=1 tail G_Y≈-0.645979 m, t=0.345 waist G_Y=-0.323746598195 m). Source audit의 half-width ≤ minimum+5 mm core 구간은 G_Y [-0.3471145761675,-0.3028384073775] m, +15 mm flank 구간은 [-0.36556297983,-0.2782405358275] m입니다. 이들은 윤곽 밖 ring이 아니라 양의 G_X(아래쪽 edge) 내부의 서로 겹치는 수평 G_Y bands로 표시했습니다. 접촉점은 canonical `waist_regions.native_elbow5_v1.contact_points_G_m`의 원래 G 좌표를 바꾸지 않고 XY로 투영했습니다. 초기 0–0.5초와 후기 4.5–5초만 강조했으며 중간 시간대 점은 그리지 않았습니다. 이 도식은 native 렌더가 아니고, cooked 형상·힘·연속 접촉을 인증하지 않습니다.'''
if old_chart not in text: raise RuntimeError('README V1 chart paragraph not found')
text=text.replace(old_chart,new_chart)
old_range='''각 패널은 native 캡처 프레임을 그대로 배치했고, 캡션은 프레임 밖에 있습니다. wave의 실제 `R_Elbow_y` 이동 범위는 2.5–4.5초에 `10.09574359°`입니다. 실행 길이는 5초이며, wave 분석 구간과 혼동하지 않습니다.'''
new_range='''각 패널은 native 캡처 프레임을 그대로 배치했고, 캡션은 프레임 밖에 있습니다. canonical field `elbow_actual_2p5_to_5s_range_deg`는 2.5–5.0초 구간 `R_Elbow_y` 실제 scalar 범위 `10.09574359°`입니다. 목표 sine-wave 구간은 2.5–4.5초이며 이 명령 구간과 canonical 측정 범위는 서로 다릅니다.'''
if old_range not in text: raise RuntimeError('README V1 elbow range paragraph not found')
text=text.replace(old_range,new_range)
old_support='''승인 분석에서 새 조건은 waist region presence `1198/1200` step, positive raw lambda `1198/1200` step이며, 마지막 120 step은 각각 `120/120`입니다. 이전 튜닝보다 waist 목표 영역 접촉은 개선됐지만 이는 접촉 표본이지 힘(N)이나 지지력 분담을 뜻하지 않습니다. 오른 허벅지 접촉도 `1198/1200` step으로 오목한 측면(flank)을 받치므로 독립된 허리 지지로 볼 수 없습니다. Thorax는 `72/1200` presence, `33/1200` positive이며 마지막 120 step은 presence `0`입니다. 상완과 왼손 손가락 접촉은 계속 남습니다. 왼손 접촉은 엄지가 아니라 `middle2/fret6`, `index2/fret5/root`, `pinky3/root`입니다.'''
new_support='''승인 분석에서 새 조건은 waist region presence `1198/1200` step, positive raw lambda `1198/1200` step이며, 마지막 120 step은 각각 `120/120`입니다. 이는 이전 튜닝보다 waist target 영역에서 접촉 표본이 늘어난 결과이지 힘(N)이나 지지력 분담을 뜻하지 않습니다. 접촉은 오른 허벅지의 오목한 flank, 상완, 왼손 손가락이 함께 있는 환경에서 확인됐습니다. Thorax는 `72/1200` presence, `33/1200` positive이며 마지막 120 step은 presence `0`입니다. 따라서 hip-only 보유는 이 시험에서 검증되지 않았습니다. 왼손 접촉은 엄지가 아니라 `middle2/fret6`, `index2/fret5/root`, `pinky3/root`입니다. raw positive lambda는 힘 단위가 아닙니다.'''
if old_support not in text: raise RuntimeError('README V1 support paragraph not found')
text=text.replace(old_support,new_support)
old_ctrl='''이 단계는 3 native 시도 중 2회 5초 완료, 1회 부분 중단입니다. CPU 후보 검사는 9개 완료(7 거절, 2 수락)됐습니다. 고정 strap/기타 부착/직접 기타 힘/자세 덮어쓰기/학습 checkpoint 연결은 없었고, root와 하체는 고정, strap은 OFF입니다. full 81개 목표는 body 9개와 arm 24개 effort, head 6개와 finger 42개 position으로 구성되며, body 설정은 K=150, D=1, target=40, cap=10입니다. 두 완료 시험은 초기 상태와 첫 2.5초 trace가 exact match입니다. source1의 입력 목록에는 사전 SHA가 없는 손 STL 35개가 누락된 한계가 있으며, source2 이후에는 human mesh 37개를 pin했습니다. source3/helper1의 shape 검수 prototype은 fitting에 실행하지 않았습니다. 한 번의 정지와 한 번의 단일 elbow 주기이므로 임의 동작, 반복성, 음악 성공을 인증하지 않습니다.'''
new_ctrl='''이 단계는 3 native 시도 중 2회 5초 완료, 1회 부분 중단입니다. CPU 후보 검사는 9개 완료(7 거절, 2 수락)됐습니다. 고정 strap/기타 부착/직접 기타 힘/자세 덮어쓰기/학습 checkpoint 연결은 없었고, root와 하체는 고정, strap은 OFF입니다. full 81개 목표는 body 9개와 arm 24개 effort, head 6개와 finger 42개 position으로 구성됩니다. Body PD는 K=150 Nm/rad, D=1 Nms/rad입니다. Thorax motor-reference 목표 접근은 16 mm, 가상 point-force 요청 상한은 40 N입니다. 상완 motor-reference 목표 접근은 4 mm, 가상 point-force 요청 상한은 10 N입니다. 두 상한 모두 접촉에서 측정된 힘이 아닙니다. 두 완료 시험은 초기 상태와 첫 2.5초 trace가 exact match입니다. source1의 입력 목록에는 사전 SHA가 없는 손 STL 35개가 누락된 한계가 있으며, source2 이후에는 human mesh 37개를 pin했습니다. source3/helper1의 shape 검수 prototype은 fitting에 실행하지 않았습니다. 한 번의 정지와 한 번의 단일 elbow 주기이므로 임의 동작, 반복성, 음악 성공을 인증하지 않습니다.'''
if old_ctrl not in text: raise RuntimeError('README V1 controller paragraph not found')
text=text.replace(old_ctrl,new_ctrl)
text += '\n\n> V2 정정 범위: 기존 V1 산출물과 영상은 유지합니다. 이번 버전은 waist 평면 윤곽의 t→G_Y 좌표 변환, core/flank 구간 의미, elbow 측정 시간 범위, 지지 조건 및 제어 단위 설명만 정정하고 새 PNG 하나를 추가했습니다. 물리 실행·학습·영상 복사는 없습니다.\n'
OUT_README.write_text(text,encoding='utf-8')
# Inputs must remain unchanged through generation.
inputs_after={str(p):record(p) for p in inputs}
unchanged=all(inputs_before[k]==inputs_after[k] for k in inputs_before)
if not unchanged: raise RuntimeError('V2 생성 중 source input changed')
provenance={
 'purpose':'waist diagram coordinate and band interpretation correction; README text corrections only',
 'preserved_v1':True,'additional_physics_runs':0,'training_updates':0,'video_copies':0,'video_reencodes':0,
 'correction':{
  'G_Y_mapping':'-0.4 + L * (0.5 - t)',
  'L_m':L,'neck_t0_G_Y_m':map_y(0),'tail_t1_G_Y_m':map_y(1),'waist_t0345_G_Y_m':map_y(.345),
  'flank_G_Y_interval_m':[ylo,yhi],'core_G_Y_interval_m':[corelo,corehi],
  'band_display':'horizontal intervals within positive G_X side and bounded by source outline; no outline-exterior rings',
  'elbow_canonical_metric_interval':'2.5–5.0 s','sine_wave_command_interval':'2.5–4.5 s'
 },
 'inputs_before_after':{k:{'before':inputs_before[k],'after':inputs_after[k],'unchanged':inputs_before[k]==inputs_after[k]} for k in sorted(inputs_before)},
 'native_video_manifest_sha256':sha(VIDEO/'manifest_v1.json'),
 'producer':{'path':str(Path(__file__)),'sha256':sha(Path(__file__)),'bytes':Path(__file__).stat().st_size},
 'outputs':[
  {'path':str(OUT_PNG),'sha256':sha(OUT_PNG),'bytes':OUT_PNG.stat().st_size},
  {'path':str(OUT_README),'sha256':sha(OUT_README),'bytes':OUT_README.stat().st_size}
 ]
}
OUT_PROV.write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'png':str(OUT_PNG),'readme':str(OUT_README),'inputs':len(inputs),'unchanged':unchanged,'coordinates':[map_y(0),map_y(1),map_y(.345)],'intervals':{'flank':[ylo,yhi],'core':[corelo,corehi]}},ensure_ascii=False))
