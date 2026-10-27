#!/usr/bin/env python3
"""Create a mask-clipped waist diagram and README V3 without touching V1/V2 artifacts."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops
import hashlib, json, platform

BASE=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1')
ART=BASE/'artifacts_v1'
BRIEF=BASE/'artifact_brief_v1.json'
ANALYSIS=BASE/'analysis_final_v1/analysis.json'
SOURCE_AUDIT=BASE/'search_v4/shift95_front30mm_audit.json'
A_MANIFEST=Path('/home/ajou/yigyu/3/stability_adapter_2/assets/om_body_geometry_v3/manifest.json')
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
V2_PRODUCER=ART/'build_artifacts_v2.py'
V2_README=ART/'README_V2.md'
V2_PNG=ART/'waist_profile_contacts_v2.png'
V2_PROV=ART/'provenance_v2.json'
OUT_PNG=ART/'waist_profile_contacts_v3.png'
OUT_README=ART/'README_V3.md'
OUT_PROV=ART/'provenance_v3.json'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def record(p):
    p=Path(p);s=p.stat();return {'sha256':sha(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
def font(sz):return ImageFont.truetype(str(FONT),sz)
def center(d,x,y,txt,ft,fill):
    b=d.textbbox((0,0),txt,font=ft);d.text((x-(b[2]-b[0])/2,y),txt,font=ft,fill=fill)

brief=json.loads(BRIEF.read_text()); analysis=json.loads(ANALYSIS.read_text())
source_audit=json.loads(SOURCE_AUDIT.read_text()); asset=json.loads(A_MANIFEST.read_text())
v2prov=json.loads(V2_PROV.read_text())
inputs={}
for p in v2prov['inputs_before_after']:
    inputs[Path(p)]=record(Path(p))
for p in [V2_PRODUCER,V2_README,V2_PNG,V2_PROV,Path(__file__)]:inputs[Path(p)]=record(Path(p))
inputs_before={str(p):v for p,v in inputs.items()}
L=float(asset['new_body_length_m']); profile=asset['half_width_profile_t_m']
waist=analysis['waist_regions']['native_elbow5_v1']
ylo,yhi=map(float,source_audit['waist_G_y_interval_m'])
corelo,corehi=map(float,source_audit['waist_core_G_y_interval_m'])
def gy(t):return -.4+L*(.5-float(t))
assert abs(gy(0)+.1540212845)<1e-8 and abs(gy(1)+.6459787155)<1e-8 and abs(gy(.345)+.323746598195)<1e-9

# Figure canvas and axes.
W,H=1700,1270
im=Image.new('RGB',(W,H),(250,250,250));d=ImageDraw.Draw(im)
center(d,W//2,22,'기타 G 프레임: 원본 반폭 윤곽과 실제 native waist contact 좌표 XY 투영',font(29),(18,18,18))
center(d,W//2,63,'A asset manifest t에서 G_Y 역방향 mapping · XY 도식 · Z 제외 · native 렌더 아님',font(20),(55,55,55))
xmin,xmax=-.205,.205;ymin,ymax=-.67,-.12
left,right,top,bottom=175,1510,145,1010
def xy(x,y):return (left+(x-xmin)/(xmax-xmin)*(right-left),bottom-(y-ymin)/(ymax-ymin)*(bottom-top))
for x in [-.2,-.15,-.1,-.05,0,.05,.1,.15,.2]:
    xx,_=xy(x,ymin);d.line((xx,top,xx,bottom),fill=(224,224,224),width=1);center(d,xx,bottom+7,f'{x:.2f}',font(16),(60,60,60))
for y in [-.65,-.6,-.55,-.5,-.45,-.4,-.35,-.3,-.25,-.2,-.15]:
    _,yy=xy(xmin,y);d.line((left,yy,right,yy),fill=(224,224,224),width=1);d.text((left-77,yy-10),f'{y:.2f}',font=font(16),fill=(60,60,60))
d.rectangle((left,top,right,bottom),outline=(40,40,40),width=2)
prof=[(float(t),float(hw)) for t,hw in profile]
pos=[(hw,gy(t)) for t,hw in prof];neg=[(-hw,gy(t)) for t,hw in prof]
polygon=pos+list(reversed(neg));poly_px=[xy(*pt) for pt in polygon]
# Source outline body fill and the precise pixel mask built from the same polygon.
d.polygon(poly_px,fill=(213,218,224),outline=(38,48,58))
mask=Image.new('L',(W,H),0);ImageDraw.Draw(mask).polygon(poly_px,fill=255)
# Lay horizontal bands on x>=0 and clip their alpha to the source silhouette mask.
bands=Image.new('RGBA',(W,H),(0,0,0,0));bd=ImageDraw.Draw(bands)
xzero,_=xy(0,ymin);_,flank_top=xy(0,yhi);_,flank_bottom=xy(0,ylo);_,core_top=xy(0,corehi);_,core_bottom=xy(0,corelo)
bd.rectangle((xzero,flank_top,right,flank_bottom),fill=(249,228,187,255))
bd.rectangle((xzero,core_top,right,core_bottom),fill=(242,178,78,255))
bands.putalpha(ImageChops.multiply(bands.getchannel('A'),mask))
im=Image.alpha_composite(im.convert('RGBA'),bands).convert('RGB');d=ImageDraw.Draw(im)
# Redraw source edge after the clipped overlays.
d.line([xy(*p) for p in pos],fill=(38,48,58),width=3);d.line([xy(*p) for p in neg],fill=(38,48,58),width=3)
# Preserve every raw native contact point; only show first/last half-second bins as before.
for row in waist['contact_points_G_m']:
    step=int(row['physics_step'])
    if step<=120:color=(31,101,190);shape='early'
    elif step>=1080:color=(190,48,115);shape='late'
    else:continue
    gx,gy0=map(float,row['point_G_m'][:2]);xx,yy=xy(gx,gy0);r=3
    if row['positive_raw_lambda']:
        if shape=='early':d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=color,outline=(25,35,45))
        else:d.polygon([(xx,yy-r-1),(xx-r-1,yy+r),(xx+r+1,yy+r)],fill=color,outline=(55,30,45))
    else:
        if shape=='early':d.ellipse((xx-r,yy-r,xx+r,yy+r),outline=color,width=2)
        else:d.polygon([(xx,yy-r-1),(xx-r-1,yy+r),(xx+r+1,yy+r)],outline=color)
center(d,(left+right)//2,H-194,'G_X (m) · 양의 G_X가 기타의 아래쪽 edge 방향',font(20),(20,20,20))
label=Image.new('RGBA',(140,38),(250,250,250,0));ld=ImageDraw.Draw(label);ld.text((0,4),'G_Y (m)',font=font(20),fill=(20,20,20));label=label.rotate(90,expand=True);im.paste(label,(26,(top+bottom-label.height)//2),label)
ly=H-135
d.rectangle((190,ly+3,211,ly+22),fill=(213,218,224),outline=(38,48,58));d.text((220,ly-1),'A manifest 원본 평면 윤곽',font=font(17),fill=(25,25,25))
d.rectangle((480,ly+3,501,ly+22),fill=(249,228,187));d.text((510,ly-1),'flank: G_Y [-0.365562980, -0.278240536] m · half-width ≤ min+15 mm',font=font(17),fill=(25,25,25))
d.rectangle((1090,ly+3,1111,ly+22),fill=(242,178,78));d.text((1120,ly-1),'core: G_Y [-0.347114576, -0.302838407] m · min+5 mm',font=font(17),fill=(25,25,25))
ly2=H-99
d.ellipse((345,ly2+4,359,ly2+18),fill=(31,101,190),outline=(25,35,45));d.text((368,ly2),'초기 0–0.5 s',font=font(17),fill=(25,25,25))
d.polygon([(540,ly2+2),(532,ly2+18),(548,ly2+18)],fill=(190,48,115),outline=(55,30,45));d.text((557,ly2),'후기 4.5–5 s',font=font(17),fill=(25,25,25))
d.text((190,H-60),'band는 half-width ≤ minimum+5/+15 mm가 만드는 G_Y 구간이며 양의 G_X측 윤곽 안에서만 표시했습니다.',font=font(17),fill=(45,45,45))
d.text((190,H-34),'점은 canonical native contact_points_G_m의 XY 투영(z 제외). 채움=positive raw lambda, 빈 기호=0; 힘(N)/cooked clearance/연속접촉 인증이 아님.',font=font(17),fill=(45,45,45))
im.save(OUT_PNG)

# V3 README reuses all V2 explanations and links, changing only chart and correction history.
text=V2_README.read_text(encoding='utf-8')
text=text.replace('waist_profile_contacts_v2.png','waist_profile_contacts_v3.png')
old='V1은 오류 이력으로 보존합니다. V2는 A asset manifest'
new='V1은 오류 이력으로 보존합니다. V2는 t→G_Y 변환을 바로잡았지만 band 색칠이 source 윤곽 밖으로 일부 번지는 시각 버그가 남았습니다. V3는 같은 band를 source outline 마스크로 잘라 윤곽 내부에만 표시합니다. V2는 오류 이력으로 보존합니다. V3는 A asset manifest'
if old not in text:raise RuntimeError('V2 README correction-history anchor missing')
text=text.replace(old,new)
text=text.replace('V2 정정 범위: 기존 V1 산출물과 영상은 유지합니다. 이번 버전은 waist 평면 윤곽의 t→G_Y 좌표 변환, core/flank 구간 의미, elbow 측정 시간 범위, 지지 조건 및 제어 단위 설명만 정정하고 새 PNG 하나를 추가했습니다. 물리 실행·학습·영상 복사는 없습니다.', 'V3 정정 범위: V1/V2 산출물과 영상은 유지합니다. band를 원본 source 윤곽 mask로 clip해 V2의 바깥쪽 색 번짐을 바로잡은 새 PNG 하나와 이 문서를 추가했습니다. raw contact 좌표·영역 범위·물리/학습 결과는 바꾸지 않았고 물리 실행·학습·영상 복사는 없습니다.')
OUT_README.write_text(text,encoding='utf-8')
inputs_after={str(p):record(p) for p in inputs}
unchanged=all(inputs_before[k]==inputs_after[k] for k in inputs_before)
if not unchanged:raise RuntimeError('V3 생성 중 입력 변경 감지')
prov={
 'purpose':'V2 waist band 색 영역을 원본 윤곽 mask 안에 clip하는 그림/문서 버전',
 'preserved_v1_v2':True,'additional_physics_runs':0,'training_updates':0,'video_copies':0,'video_reencodes':0,
 'mapping':'G_Y = -0.4 + L * (0.5 - t)','L_m':L,'flank_interval_G_Y_m':[ylo,yhi],'core_interval_G_Y_m':[corelo,corehi],
 'band_clipping':'PIL polygon mask generated from the same A-manifest source outline; horizontal bands restricted to positive-GX half inside mask',
 'raw_contact_points_changed':False,
 'inputs_before_after':{k:{'before':inputs_before[k],'after':inputs_after[k],'unchanged':inputs_before[k]==inputs_after[k]} for k in sorted(inputs_before)},
 'producer':{'path':str(Path(__file__)),'sha256':sha(Path(__file__)),'bytes':Path(__file__).stat().st_size},
 'runtime':{'python':platform.python_version(),'Pillow':Image.__version__,'font_path':str(FONT),'font_sha256':sha(FONT)},
 'outputs':[{'path':str(OUT_PNG),'sha256':sha(OUT_PNG),'bytes':OUT_PNG.stat().st_size},{'path':str(OUT_README),'sha256':sha(OUT_README),'bytes':OUT_README.stat().st_size}]
}
OUT_PROV.write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'png':str(OUT_PNG),'readme':str(OUT_README),'input_count':len(inputs),'inputs_unchanged':unchanged},ensure_ascii=False))
