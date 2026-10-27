#!/usr/bin/env python3
"""Rebuild native11 panel with a measured footer band; copy existing comparison as-is."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1')
V=Path('/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1')
A1=P/'artifacts_candidate_v1';A2=P/'artifacts_candidate_v2'; D=V/'candidate_v1'
OLD_PROV=A1/'provenance_v1.json'
OLD_PANEL=A1/'native11_initial_and_timeline.png'
OLD_COMPARE=A1/'native11_zero_to_five_comparison.png'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
N11=P/'native_v11/upper_arm_neck_side'
INITIALS=[('초기 native',N11/'media/initial_native.png'),('초기 strings',N11/'media/initial_strings.png'),('초기 side',N11/'media/initial_support_side.png')]
TIMES=[('0초',0,N11/'media/frames/whole_body/00000.png'),('0.5초',15,N11/'media/frames/whole_body/00015.png'),('2초',60,N11/'media/frames/whole_body/00060.png'),('5초',150,N11/'media/frames/whole_body/00150.png')]

def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def fit(im,w,h):
 im=im.convert('RGB');scale=min(w/im.width,h/im.height)
 return im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)

def main():
 old=json.loads(OLD_PROV.read_text(encoding='utf-8'))
 # Pin all original inputs plus producer/font and every consumed v1 output/document.
 pins=set(old['inputs_before_sha256'])
 pins.update([str(OLD_PROV),str(A1/'build_candidate_v1.py'),str(FONT),str(OLD_PANEL),str(OLD_COMPARE),str(A1/'README.md'),str(V/'manifest_v3.json'),str(D/'README.md'),str(D/'INDEX.md')])
 before={p:sha(Path(p)) for p in sorted(pins)}
 for path,expected in old['inputs_before_sha256'].items():
  if before[path]!=expected:raise RuntimeError(f'consumed v1 input changed: {path}')
 for path,expected in [(str(A1/'build_candidate_v1.py'),old['producer']['sha256']),(str(FONT),old['font']['sha256']),(str(OLD_PANEL),old['outputs_sha256'][str(OLD_PANEL)]),(str(OLD_COMPARE),old['outputs_sha256'][str(OLD_COMPARE)])]:
  if before[path]!=expected:raise RuntimeError(f'consumed v1 artifact changed: {path}')
 new_panel=A2/'native11_initial_and_timeline_v2.png'
 new_compare=A2/'native11_zero_to_five_comparison_v2.png'
 if new_panel.exists() or new_compare.exists():raise RuntimeError('refusing to overwrite existing v2 output')
 margin=30;gap=18;title_h=100;band=48;initial_w=560;initial_h=420;time_w=420;time_h=236
 width=3*initial_w+2*gap+2*margin
 height=title_h+initial_h+band+gap+time_h+band+148 # +50 px versus consumed v1 panel
 canvas=Image.new('RGB',(width,height),(246,248,251));draw=ImageDraw.Draw(canvas)
 titlefont=ImageFont.truetype(str(FONT),32);captionfont=ImageFont.truetype(str(FONT),24);footfont=ImageFont.truetype(str(FONT),21)
 draw.text((margin,20),'Native 11 · 초기 자료와 5초 whole_body 프레임',font=titlefont,fill=(24,39,58))
 draw.text((margin,64),'각 프레임은 실제 native 캡처에서 가져온 정지 이미지입니다.',font=footfont,fill=(55,68,84))
 y=title_h
 for col,(label,path) in enumerate(INITIALS):
  x=margin+col*(initial_w+gap);canvas.paste(fit(Image.open(path),initial_w,initial_h),(x,y));draw.text((x+6,y+initial_h+8),label,font=captionfont,fill=(24,39,58))
 y2=y+initial_h+band+gap
 for col,(label,idx,path) in enumerate(TIMES):
  x=margin+col*(time_w+gap);canvas.paste(fit(Image.open(path),time_w,time_h),(x,y2));draw.text((x+4,y2+time_h+8),label,font=captionfont,fill=(24,39,58))
 footer_y=y2+time_h+band+5
 footer_bottom=height-margin
 draw.rectangle((margin,footer_y,width-margin,footer_bottom),fill=(229,235,242))
 footer_lines=[(margin+12,footer_y+10,'영상 캡처 시각 참고용입니다. 힘 분포·접촉력·관통을 보여주거나 인증하지 않습니다.'),(margin+12,footer_y+45,'두 trial은 동일한 초기조건의 5초 유지 후보이며, 움직이는 연주 강건성·학습 성공을 뜻하지 않습니다.')]
 for xy in footer_lines:
  draw.text(xy[:2],xy[2],font=footfont,fill=(24,39,58))
  bbox=draw.textbbox(xy[:2],xy[2],font=footfont)
  if bbox[0]<margin or bbox[2]>width-margin or bbox[1]<footer_y or bbox[3]>footer_bottom:
   raise RuntimeError(f'footer text outside background rectangle: {bbox} vs {footer_y,footer_bottom}')
 canvas.save(new_panel,optimize=True)
 # The already-validated comparison is copied byte-for-byte; its content/captions do not change.
 shutil.copyfile(OLD_COMPARE,new_compare)
 if sha(new_compare)!=before[str(OLD_COMPARE)]:raise RuntimeError('comparison copy SHA mismatch')
 after={p:sha(Path(p)) for p in sorted(pins)}
 if before!=after:raise RuntimeError('an input changed during processing')
 print(json.dumps({'inputs_before_sha256':before,'inputs_after_sha256':after,'old_producer_sha256':before[str(A1/'build_candidate_v1.py')],'font_sha256':before[str(FONT)],'old_panel_sha256':before[str(OLD_PANEL)],'old_comparison_sha256':before[str(OLD_COMPARE)],'outputs':{str(new_panel):sha(new_panel),str(new_compare):sha(new_compare)},'panel_size_px':list(canvas.size),'footer_textboxes':[draw.textbbox(xy[:2],xy[2],font=footfont) for xy in footer_lines],'footer_background_bounds':[margin,footer_y,width-margin,footer_bottom]},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
