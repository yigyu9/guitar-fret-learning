#!/usr/bin/env python3
"""Exact-copy native 11/12 videos and assemble native-11 source-frame panels."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1')
V=Path('/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1')
OUT=V/'candidate_v1'; ART=P/'artifacts_candidate_v1'
VERIFY=P/'effort_verification_v10_cases4.json'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
N11=P/'native_v11/upper_arm_neck_side'
N12=P/'native_v12/upper_arm_neck_side_repeat'
CAPTURE=N11/'media/capture.json'
INITIALS={
 '초기 native':N11/'media/initial_native.png',
 '초기 strings':N11/'media/initial_strings.png',
 '초기 side':N11/'media/initial_support_side.png',
}
FRAMES=[(0,'0초','00000.png'),(15,'0.5초','00015.png'),(60,'2초','00060.png'),(150,'5초','00150.png')]
TRIALS=[('upper_arm_neck_side',11,N11),('upper_arm_neck_side_repeat',12,N12)]

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def fit(im,w,h):
 im=im.convert('RGB')
 scale=min(w/im.width,h/im.height)
 size=(round(im.width*scale),round(im.height*scale))
 return im.resize(size,Image.Resampling.LANCZOS)

def main():
 data=json.loads(VERIFY.read_text(encoding='utf-8'))
 if not data.get('passed'): raise RuntimeError('effort verification is not passed')
 if not {'upper_arm_neck_side','upper_arm_neck_side_repeat'} <= set(data['cases']): raise RuntimeError('expected cases missing')
 source_paths=[VERIFY,CAPTURE,FONT,*INITIALS.values()]
 for _,_,run in TRIALS:
  source_paths.extend([run/'attempt.json',run/'report.json',run/'contacts.json',run/'media/effort_configuration.json'])
 inputs_before={str(p):sha(p) for p in source_paths}
 cap=json.loads(CAPTURE.read_text(encoding='utf-8'))
 if cap['fps']!=30 or len(cap['frames'])!=151: raise RuntimeError('unexpected native11 capture format')
 frame_paths=[]
 for i,t,name in FRAMES:
  fp=N11/f'media/frames/whole_body/{name}'
  frame_paths.append(fp)
  file_hash=cap['frames'][i]['image_sha256'][str(fp)]
  inputs_before[str(fp)]=sha(fp)
  if cap['frames'][i]['time_s']!=float(t.replace('초','')) or sha(fp)!=file_hash: raise RuntimeError(f'frame capture mismatch: {fp}')
 source_paths += frame_paths
 entries=[]
 for key,no,run in TRIALS:
  case=data['cases'][key]
  for view in ['whole_body','hands']:
   meta=case['videos'][view];src=Path(meta['path']);source_paths.append(src)
   sh=sha(src);inputs_before[str(src)]=sh
   if sh!=meta['sha256']: raise RuntimeError(f'verification/video SHA mismatch: {src}')
   dst=OUT/f'native{no}_{view}.mp4'
   if dst.exists(): raise RuntimeError(f'refusing to overwrite {dst}')
   shutil.copyfile(src,dst)
   csh=sha(dst)
   if csh!=sh: raise RuntimeError(f'copy differs: {dst}')
   entries.append({'source':str(src),'source_sha256':sh,'destination':str(dst),'copy_sha256':csh,'label':f'native {no} · upper_arm_neck_side' if no==11 else f'native {no} · upper_arm_neck_side_repeat','view':view})
 initial_and_timeline=ART/'native11_initial_and_timeline.png'
 compare=ART/'native11_zero_to_five_comparison.png'
 if initial_and_timeline.exists() or compare.exists(): raise RuntimeError('refusing to overwrite existing image output')
 # 3 initial illustrations and 4 whole-body timestamps, with separate caption bands.
 margin=30;gap=18; title_h=100; band=48; initial_w=560; initial_h=420; time_w=420;time_h=236
 width=3*initial_w+2*gap+2*margin
 height=title_h+initial_h+band+gap+time_h+band+98
 canvas=Image.new('RGB',(width,height),(246,248,251));draw=ImageDraw.Draw(canvas)
 titlefont=ImageFont.truetype(str(FONT),32); captionfont=ImageFont.truetype(str(FONT),24); footfont=ImageFont.truetype(str(FONT),21)
 draw.text((margin,20),'Native 11 · 초기 자료와 5초 whole_body 프레임',font=titlefont,fill=(24,39,58))
 draw.text((margin,64),'각 프레임은 실제 native 캡처에서 가져온 정지 이미지입니다.',font=footfont,fill=(55,68,84))
 y=title_h
 for col,(label,p) in enumerate(INITIALS.items()):
  x=margin+col*(initial_w+gap);im=fit(Image.open(p),initial_w,initial_h)
  canvas.paste(im,(x,y));draw.text((x+6,y+initial_h+8),label,font=captionfont,fill=(24,39,58))
 y2=y+initial_h+band+gap
 for col,(i,label,name) in enumerate(FRAMES):
  x=margin+col*(time_w+gap);im=fit(Image.open(N11/f'media/frames/whole_body/{name}'),time_w,time_h)
  canvas.paste(im,(x,y2));draw.text((x+4,y2+time_h+8),label,font=captionfont,fill=(24,39,58))
 footer_y=y2+time_h+band+5
 draw.rectangle((margin,footer_y,width-margin,height-margin),fill=(229,235,242))
 draw.text((margin+12,footer_y+10),'영상 캡처 시각 참고용입니다. 힘 분포·접촉력·관통을 보여주거나 인증하지 않습니다.',font=footfont,fill=(24,39,58))
 draw.text((margin+12,footer_y+45),'두 trial은 동일한 초기조건의 5초 유지 후보이며, 움직이는 연주 강건성·학습 성공을 뜻하지 않습니다.',font=footfont,fill=(24,39,58))
 canvas.save(initial_and_timeline,optimize=True)
 # Raw initial and final frames side-by-side; no overlays or pose normalization.
 cmp_w,cmp_h=900,506;cmp_gap=24;cmp_margin=28;cmp_top=104;cmp_band=52;cmp_footer=100
 cmp=Image.new('RGB',(2*cmp_w+3*cmp_gap,cmp_top+cmp_h+cmp_band+cmp_footer),(246,248,251));cd=ImageDraw.Draw(cmp)
 cd.text((cmp_gap,20),'Native 11 · 0초 → 5초 프레임 비교',font=titlefont,fill=(24,39,58))
 for x,idx,label in [(cmp_gap,0,'초기 · 0초'),(2*cmp_gap+cmp_w,150,'종료 프레임 · 5초')]:
  im=fit(Image.open(N11/f'media/frames/whole_body/{idx:05d}.png'),cmp_w,cmp_h);cmp.paste(im,(x,cmp_top));cd.text((x+6,cmp_top+cmp_h+8),label,font=captionfont,fill=(24,39,58))
 fy=cmp_top+cmp_h+cmp_band
 cd.rectangle((cmp_gap,fy,cmp.width-cmp_gap,cmp.height-cmp_gap),fill=(229,235,242))
 cd.text((cmp_gap+12,fy+12),'바디 bounding-box 중심 변화 40.207 mm · actor-root 위치 변화 53.017 mm',font=footfont,fill=(24,39,58))
 cd.text((cmp_gap+12,fy+48),'두 지표는 서로 다릅니다. 비교는 장면 프레임 참조이며 반복·연주 성능 보증이 아닙니다.',font=footfont,fill=(24,39,58))
 cmp.save(compare,optimize=True)
 # Verify immutable inputs after reads/copy/render.
 inputs_after={str(x):sha(x) for x in source_paths}
 for p in inputs_before:
  if inputs_before[p]!=inputs_after[p]: raise RuntimeError(f'input changed: {p}')
 manifest=V/'manifest_v3.json'
 if manifest.exists(): raise RuntimeError('refusing to overwrite existing manifest_v3')
 manifest.write_text(json.dumps({'videos':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 result={'inputs_before_sha256':inputs_before,'inputs_after_sha256':inputs_after,'copies':entries,'frames':[{'path':str(N11/f'media/frames/whole_body/{name}'),'time_s':float(t.replace('초','')),'physics_step':cap['frames'][i]['physics_step'],'sha256':sha(N11/f'media/frames/whole_body/{name}')} for i,t,name in FRAMES],'font':{'path':str(FONT),'sha256':sha(FONT)},'panel_dimensions':{str(initial_and_timeline):list(Image.open(initial_and_timeline).size),str(compare):list(Image.open(compare).size)},'outputs_sha256':{str(initial_and_timeline):sha(initial_and_timeline),str(compare):sha(compare),str(manifest):sha(manifest)}}
 print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
