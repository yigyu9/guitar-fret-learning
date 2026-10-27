#!/usr/bin/env python3
"""Fix the footer overlap on the just-created, not-yet-reviewed native2/native3 panel."""
from pathlib import Path
import hashlib
from PIL import Image, ImageDraw, ImageFont
ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1'
OUT=P/'artifacts_v1/native2_native3_timeline_comparison.png'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
BASES=[P/'native_v2/front160mm',P/'native_v3/front160mm_lift12mm']
IDX=['00000','00060','00150']; TIMES=['0초','2초','5초']
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def font(n):return ImageFont.truetype(str(FONT),n)
def center(d,x,y,text,ft,fill):
 b=d.textbbox((0,0),text,font=ft);d.text((x-(b[2]-b[0])/2,y),text,font=ft,fill=fill)
inputs=[FONT]
imgs=[]
for base in BASES:
 row=[]
 for name in IDX:
  p=base/f'media/frames/whole_body/{name}.png';inputs.append(p);row.append(Image.open(p).convert('RGB'))
 imgs.append(row)
before={str(p):sha(p) for p in inputs}
if len({im.size for row in imgs for im in row})!=1:raise RuntimeError('native image sizes differ')
iw,ih=imgs[0][0].size;cw=640;ch=round(ih*cw/iw);gap=18;outer=28;left=275
row_label=32;time_label=28;between_rows=22;footer=120;title=72
W=outer*2+left+3*cw+2*gap
row_block=row_label+time_label+ch+between_rows
H=outer+title+2*row_block+footer+outer
canvas=Image.new('RGB',(W,H),(247,249,252));d=ImageDraw.Draw(canvas)
center(d,W//2,16,'실제 native 2 / native 3 whole_body 비교',font(34),(24,38,58))
y=outer+title
row_names=['native 2 · front160mm','native 3 · front160mm_lift12mm (+12 mm target)']
for r in range(2):
 d.text((outer+2,y+2),row_names[r],font=font(24),fill=(34,49,67));y+=row_label
 for c in range(3):
  x=outer+left+c*(cw+gap);center(d,x+cw//2,y,TIMES[c],font(21),(34,49,67))
 y+=time_label
 for c in range(3):
  x=outer+left+c*(cw+gap)
  canvas.paste(imgs[r][c].resize((cw,ch),Image.Resampling.LANCZOS),(x,y))
 y+=ch+between_rows
fy=y-between_rows+12
d.rounded_rectangle((outer,fy,W-outer,fy+footer-8),radius=12,fill=(229,235,243))
d.text((outer+16,fy+12),'각 프레임은 저장된 native 렌더입니다. 5초 시점에도 기타 위치·회전 및 접촉 상태를 함께 해석해야 합니다.',font=font(19),fill=(31,44,62))
d.text((outer+16,fy+51),'native 3은 큰 초기 이탈 뒤 2→5초 변화가 작아졌지만, Head 접촉과 큰 전체 회전으로 후보에서 거절됐습니다.',font=font(19),fill=(31,44,62))
if fy+footer-8>H:raise RuntimeError('footer exceeds image canvas')
OUT.parent.mkdir(parents=True,exist_ok=True);OUT_TMP=OUT.with_suffix('.tmp.png');canvas.save(OUT_TMP,optimize=True)
# Atomic replace of the just-created v2 image owned by this phase.
OUT_TMP.replace(OUT)
after={str(p):sha(p) for p in inputs}
if before!=after:raise RuntimeError('a source frame or font changed during rendering')
print({'source_sha_before_after_equal':before==after,'old_image_sha256':sha(OUT),'image_size':canvas.size,'footer_y':fy,'canvas_height':H})
