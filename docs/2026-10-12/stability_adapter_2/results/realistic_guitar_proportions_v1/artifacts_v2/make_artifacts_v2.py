#!/usr/bin/env python3
"""기존 t0 이미지를 재배치하고 실제 치수를 공통 축에 그린다. 물리·영상 처리는 하지 않는다."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1'
A=P/'artifacts_v2'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def fnt(s):return ImageFont.truetype(str(FONT),s)

def pin_json(path, expected=None):
 p=Path(path); h=sha(p)
 if expected is not None: assert h==expected,(p,h,expected)
 inputs[str(p)]=h
 return read(p)

inputs={}
v3=pin_json(P/'verification_v3.json')
abi=pin_json(P/'native_geometry_ABI_verification_v1.json')
geo=pin_json(P/'geometry_build_v1.json')
assert v3['passed'] and all(v3['checks'].values())
assert abi['passed'] and all(abi['checks'].values())
assert geo['checks']['two_convex_bouts_keep_waist'] and geo['checks']['positive_watertight_meshes']
inputs[str(FONT)]=sha(FONT)
# Pin the original frame capture JSON and its direct raw native t0 image plus collision image.
sources=[]
for label,native_name in [('원본','native_baseline_v2'),('새 비율','native_realistic_v2')]:
 n=P/native_name
 capture=pin_json(n/'media/raw/capture.json')
 frame=capture['frames'][0]
 raw=Path(next(k for k in frame['image_sha256'] if '/whole_body/' in k))
 rawsha=frame['image_sha256'][str(raw)]
 inputs[str(raw)]=sha(raw); assert inputs[str(raw)]==rawsha
 collision=n/'initial_collision.png'; inputs[str(collision)]=sha(collision)
 sources.append((label,raw,collision))

# 2x2 t0 panel, raw native render and collision image at identical dimensions/camera framing.
W,H=1920,1160; panel_w,panel_h=900,506; x0,x1=40,980; y0,y1=96,650
canvas=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(canvas)
d.text((40,22),'t0 같은 전신 카메라: native 시각화와 충돌 시각화',font=fnt(34),fill='#17212b')
for row,(label,raw,collision) in enumerate(sources):
 for col,(view,path) in enumerate([('Native 시각화 (raw frame)',raw),('충돌 형상 시각화',collision)]):
  x=x0 if col==0 else x1; y=y0 if row==0 else y1
  d.text((x,y-42),f'{label} · {view}',font=fnt(25),fill='#17212b')
  im=Image.open(path).convert('RGB').resize((panel_w,panel_h),Image.Resampling.LANCZOS)
  canvas.paste(im,(x,y))
canvas.save(A/'native_collision_2x2.png')

# Side-by-side body outlines use identical physical scale and axis range.
S=12 # common pixels per centimetre
W,H=1900,1250; canvas=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(canvas)
d.text((55,24),'기타 몸체 평면 윤곽 — 공통 cm 축 / 동일한 픽셀·cm',font=fnt(36),fill='#17212b')
d.text((55,78),'각 패널의 축 범위와 비율은 동일합니다. 원본은 34×30 cm 경계이며 넥·헤드스톡은 몸체 비교에서 제외합니다.',font=fnt(24),fill='#394550')
profile=geo['half_width_profile_t_m']; body_len_cm=geo['new_body_length_m']*100
for cx,label in [(480,'원본 몸체'),(1400,'새 비율 몸체')]:
 origin_y=1040
 d.text((cx-135,135),label,font=fnt(27),fill='#17212b')
 # Same ±25 cm width and 0–52 cm length axes in both panels.
 for cm in range(-20,21,10):
  x=cx+cm*S; d.line((x,origin_y-52*S,x,origin_y),fill='#e3e8ec',width=1); d.text((x-14,origin_y+12),str(cm),font=fnt(18),fill='#52606d')
 for cm in range(0,51,10):
  y=origin_y-cm*S; d.line((cx-25*S,y,cx+25*S,y),fill='#e3e8ec',width=1); d.text((cx-25*S-36,y-12),str(cm),font=fnt(18),fill='#52606d')
 d.line((cx,origin_y-52*S,cx,origin_y),fill='#bac4cc',width=2)
 if label=='원본 몸체':
  d.rectangle((cx-15*S,origin_y-34*S,cx+15*S,origin_y),outline='#637381',width=7)
  d.text((cx-135,origin_y-34*S-40),'30 cm × 34 cm',font=fnt(23),fill='#43515d')
 else:
  right=[]
  for t,half_m in profile:
   y=origin_y-t*body_len_cm*S; x=cx+half_m*100*S; right.append((round(x),round(y)))
  left=[(2*cx-x,y) for x,y in right]
  closed_outline=right+list(reversed(left))+[right[0]]
  d.line(closed_outline,fill='#148a9c',width=8)
  d.text((cx-130,origin_y-body_len_cm*S-40),f'{body_len_cm:.2f} cm × {geo["new_body_max_width_m"]*100:.2f} cm max',font=fnt(23),fill='#08788a')
# Axis and source notes remain outside plotting area.
d.text((55,1140),f"공통 축 단위: cm; 두 패널 동일 축척. 새 실제 profile 길이 {body_len_cm:.4f} cm, 최대폭 {geo['new_body_max_width_m']*100:.4f} cm.",font=fnt(22),fill='#394550')
d.text((55,1180),f"old 기타 전체 source 종방향 길이 {abi['old_source_total_longitudinal_length_m']*100:.4f} cm는 neck 포함 source bounds로, 몸체 치수와 별개입니다.",font=fnt(21),fill='#394550')
canvas.save(A/'body_outline_common_cm.png')

outputs={str(p):sha(p) for p in sorted(A.glob('*.png'))}
readme=A/'README.md'
if readme.exists(): outputs[str(readme)]=sha(readme)
prov={'schema':'realistic-guitar-artifacts-v2-provenance','processing_only':True,'physics_reruns':0,'video_copies':0,'inputs_sha256_before_after':{p:{'before':h,'after':sha(p)} for p,h in inputs.items()},'authority':{'verification_v3':str(P/'verification_v3.json'),'native_geometry_ABI_verification_v1':str(P/'native_geometry_ABI_verification_v1.json'),'geometry_build_v1':str(P/'geometry_build_v1.json'),'geometry_ABI_checks':abi['checks'],'old_source_total_longitudinal_length_m':abi['old_source_total_longitudinal_length_m']},'font':{'path':str(FONT),'sha256':sha(FONT)},'outputs_sha256':outputs,'producer_sha256':sha(Path(__file__))}
(A/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(prov,ensure_ascii=False,indent=2))
