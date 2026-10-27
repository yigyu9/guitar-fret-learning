#!/usr/bin/env python3
"""Re-render OM axilla comparison panels with corrected 30 mm condition caption."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-12')
P=ROOT/'stability_adapter_2/results/om_axilla_initial_pose_v1'; A=P/'artifacts_v2'
CASES=[('clear_reference','native_v1/clear_reference','초기 기준'),('lean18_back30','native_v1/lean18_back30','추가 전경 18° (world 누적) · 기타 뒤 30 mm · hold OFF'),('lean18_back30_hold_pi','native_v2/lean18_back30_hold_pi','추가 전경 18° (world 누적) · 기타 뒤 30 mm · hold ON')]
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(ps):return {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in ps}
def fnt(n):return ImageFont.truetype(str(FONT),n)
def frame(case,view,t):
 cap=json.loads((P/case[1]/'media/capture.json').read_text());row=next(x for x in cap['frames'] if x['time_s']==float(t))
 p=Path(next(k for k in row['image_sha256'] if f'/{view}/' in k));assert sha(p)==row['image_sha256'][str(p)]
 return p

def whole_panel():
 imgs=[[Image.open(frame(c,'whole_body',t)).convert('RGB') for c in CASES] for t in (0,2,5)]
 w=max(im.width for row in imgs for im in row);h=max(im.height for row in imgs for im in row);gap=12;head=84;left=56
 out=Image.new('RGB',(left+3*(w+gap)+gap,head+3*(h+gap)+gap),(248,248,248));d=ImageDraw.Draw(out)
 for ci,c in enumerate(CASES):d.text((left+ci*(w+gap)+3,12),c[2],font=fnt(19),fill=(15,15,15))
 for ri,t in enumerate((0,2,5)):
  d.text((7,head+ri*(h+gap)+8),f'{t}초',font=fnt(20),fill=(15,15,15))
  for ci,im in enumerate(imgs[ri]):out.paste(im,(left+ci*(w+gap),head+ri*(h+gap)))
 out.save(A/'whole_body_conditions_0_2_5s_v2.png')
def strings_panel():
 imgs=[Image.open(P/c[1]/'media/initial_strings.png').convert('RGB') for c in CASES]
 w=max(i.width for i in imgs);h=max(i.height for i in imgs);gap=12;head=60
 out=Image.new('RGB',(3*w+4*gap,h+head+gap),(248,248,248));d=ImageDraw.Draw(out)
 for i,(im,c) in enumerate(zip(imgs,CASES)):
  x=gap+i*(w+gap);out.paste(im,(x,head));d.text((x+6,12),c[2],font=fnt(18),fill=(15,15,15))
 out.save(A/'initial_strings_conditions_v2.png')
def side():
 src=P/'native_v2/lean18_back30_hold_pi/media/initial_axilla_side.png';im=Image.open(src).convert('RGB');band=58
 out=Image.new('RGB',(im.width,im.height+band),(248,248,248));out.paste(im,(0,band))
 ImageDraw.Draw(out).text((12,12),'hold ON · 추가 전경 18° (world 누적) · 기타 뒤 30 mm · 측면 native camera',font=fnt(20),fill=(15,15,15))
 out.save(A/'hold_on_initial_axilla_side_v2.png')

# Pin v1 source artifacts and all native inputs before generating only new v2 outputs.
v1=P/'artifacts_v1'
inputs=[Path('/home/ajou/yigyu/3/stability_adapter_2/OM_AXILLA_INITIAL_POSE_PLAN_V2.md'),FONT,v1/'make_archive_v1.py',v1/'provenance_v1.json',v1/'README.md',v1/'whole_body_conditions_0_2_5s.png',v1/'initial_strings_conditions.png',v1/'hold_on_initial_axilla_side_captioned.png']
for label,path,title in CASES:
 n=P/path;inputs += [n/'report.json',n/'initial_values.json',n/'trace.json',n/'contacts.json',n/'media/capture.json',n/'media/initial_strings.png']
 for t in (0,2,5): inputs.append(frame((label,path,title),'whole_body',t))
inputs += [P/'native_v2/lean18_back30_hold_pi/media/initial_axilla_side.png']
before=pin(inputs);assert len(CASES)==3
A.mkdir(parents=True,exist_ok=True);whole_panel();strings_panel();side()
after=pin(inputs);assert before==after
print('inputs',len(inputs),'equal',before==after)
