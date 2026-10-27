#!/usr/bin/env python3
"""Compare same initial hands frame with strap-only and six-line overlay."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path("/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1")
M=ROOT/"native_v1/media"
A=ROOT/"artifacts_v2"
FONT="/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
left=Image.open(M/"strap/frames/hands/00000.png").convert("RGB")
right=Image.open(M/"frames/hands/00000.png").convert("RGB")
w,h=left.size; gap=12; head=78; foot=46
out=Image.new("RGB",(2*w+3*gap,h+head+foot),(248,248,248)); d=ImageDraw.Draw(out)
f=ImageFont.truetype(FONT,23); s=ImageFont.truetype(FONT,18)
for i,(im,label) in enumerate(((left,"현 표시 OFF: native + strap"),(right,"현 표시 ON: native + strap + 6현"))):
 x=gap+i*(w+gap); out.paste(im,(x,head)); d.text((x+7,13),label,font=f,fill=(15,15,15))
d.text((gap,head+h+8),"동일 초기 hands camera frame · 우측 여섯 현은 밝은 회색 2 px 시각 오버레이이며 물리 현이 아님",font=s,fill=(25,25,25))
out.save(A/"hands_sameframe_strap_vs_sixline_v2.png")
