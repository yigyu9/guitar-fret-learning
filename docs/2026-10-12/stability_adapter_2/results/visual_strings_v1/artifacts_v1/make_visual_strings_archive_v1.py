#!/usr/bin/env python3
"""Archive completed native six-string visualization videos and frame panels."""
from pathlib import Path
import hashlib, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-12')
P=ROOT/'stability_adapter_2/results/visual_strings_v1'
N=P/'native_v1'; M=N/'media'; A=P/'artifacts_v1'; V=ROOT/'video/visual_strings_v1'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def pin(paths): return {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in paths}
def ft(size): return ImageFont.truetype(str(FONT),size)
def caption(src,dst,title,sub=''):
 im=Image.open(src).convert('RGB'); band=76 if sub else 54
 out=Image.new('RGB',(im.width,im.height+band),(248,248,248));out.paste(im,(0,band));d=ImageDraw.Draw(out)
 d.text((14,8),title,font=ft(25),fill=(20,20,20))
 if sub:d.text((14,39),sub,font=ft(17),fill=(45,45,45))
 out.save(dst)
def panel(view):
 capture=json.loads((M/'capture.json').read_text())
 selected=[next(f for f in capture['frames'] if f['time_s']==float(t)) for t in (0,2,5)]
 imgs=[]
 for f in selected:
  path=Path(next(k for k in f['image_sha256'] if f'/{view}/' in k))
  assert sha(path)==f['image_sha256'][str(path)]
  imgs.append(Image.open(path).convert('RGB'))
 w=max(i.width for i in imgs);h=max(i.height for i in imgs);gap=12;head=62
 out=Image.new('RGB',(gap*4+w*3,h+head+gap*2),(248,248,248));d=ImageDraw.Draw(out)
 for i,(im,f) in enumerate(zip(imgs,selected)):
  x=gap+i*(w+gap);out.paste(im,(x,head))
  d.text((x+6,9),f"{view} · {f['time_s']:.0f}초 · {len(f['string_endpoints_W_m'])}개 시각 현",font=ft(22),fill=(18,18,18))
 d.text((gap,head+h+3),'회색 선은 영상 오버레이(2 px); 물리 현 굵기·진동이 아니며 native depth 2 mm 기준으로 가려짐',font=ft(16),fill=(35,35,35))
 out.save(A/f'{view}_strings_0_2_5s.png')

inputs=[N/'report.json',N/'initial_values.json',N/'trace.json',N/'native_properties.json',N/'native_shapes.json',N/'contacts.json',N/'inputs_verified.json',P/'verification_v1.json',M/'capture.json',M/'strap/capture.json',M/'strap/raw/capture.json',M/'videos.json',M/'initial_native.png',M/'initial_strings.png',FONT,Path('/home/ajou/yigyu/3/stability_adapter_2/string_trial_recording_v1.py'),Path('/home/ajou/yigyu/3/stability_adapter_2/run_visual_strings_trial_v1.py')]
for name in ('whole_body.mp4','hands.mp4'):inputs.append(M/name)
cap=json.loads((M/'capture.json').read_text())
for t in (0,2,5):
 f=next(x for x in cap['frames'] if x['time_s']==float(t))
 inputs.extend(Path(k) for k in f['image_sha256'])
rawcap=json.loads((M/'strap/raw/capture.json').read_text())
rframe=rawcap['frames'][0]
inputs.extend(Path(k) for k in rframe['image_sha256'])
before=pin(inputs)
assert json.loads((N/'report.json').read_text()).get('completed') is True
assert len(cap['frames'])==151 and all(f.get('render_preserves_states') is True for f in cap['frames'])
assert len(cap['frames'][0]['string_endpoints_W_m'])==6
verification=json.loads((P/'verification_v1.json').read_text())
assert verification.get('passed') is True and verification.get('new_physics_geometry')==0
A.mkdir(parents=True,exist_ok=True);V.mkdir(parents=True,exist_ok=True)
for view in ('whole_body','hands'):panel(view)
caption(M/'initial_strings.png',A/'initial_strings_captioned.png','초기 native 화면: 6개 밝은 회색 선 오버레이','실제 native renderer + 투영선 · 실물 현 굵기/진동 아님 · 가려진 선은 native depth 기준 숨김')
raw=Path(next(k for k in rframe['image_sha256'] if '/hands/' in k)); final=Path(next(k for k in cap['frames'][0]['image_sha256'] if '/hands/' in k))
assert sha(raw)==rframe['image_sha256'][str(raw)] and sha(final)==cap['frames'][0]['image_sha256'][str(final)]
ims=[Image.open(raw).convert('RGB'),Image.open(final).convert('RGB')];w=max(x.width for x in ims);h=max(x.height for x in ims);gap=12;head=70
out=Image.new('RGB',(w*2+gap*3,h+head+gap),(248,248,248));d=ImageDraw.Draw(out)
for i,(im,title) in enumerate(zip(ims,['원본: native renderer + strap','같은 frame: 여섯 선 시각 오버레이 + strap'])):
 x=gap+i*(w+gap);out.paste(im,(x,head));d.text((x+8,13),title,font=ft(22),fill=(15,15,15))
d.text((gap,head+h+4),'선은 2 px 화면 표시이며 physics에 추가되지 않음; native depth tolerance 2 mm로 가림 처리',font=ft(18),fill=(20,20,20))
out.save(A/'hands_sameframe_raw_vs_sixline.png')
manifest={'videos':[]}
for kind in ('whole_body','hands'):
 src=M/f'{kind}.mp4';dst=V/f'{kind}_sixline.mp4';shutil.copyfile(src,dst);assert sha(src)==sha(dst)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)],text=True))['streams'][0]
 manifest['videos'].append({'source':str(src),'destination':str(dst),'source_sha256':sha(src),'copy_sha256':sha(dst),'bytes':dst.stat().st_size,'ffprobe':probe})
(V/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
after=pin(inputs);assert before==after
outputs=[A/'make_visual_strings_archive_v1.py',A/'whole_body_strings_0_2_5s.png',A/'hands_strings_0_2_5s.png',A/'initial_strings_captioned.png',A/'hands_sameframe_raw_vs_sixline.png',V/'manifest_v1.json']+[V/f'{x}_sixline.mp4' for x in ('whole_body','hands')]
prov={'inputs_before':before,'inputs_after':after,'producer_sha256':sha(A/'make_visual_strings_archive_v1.py'),'outputs':pin(outputs),'native_physics_reruns':0,'visualization':{'line_width_px':2,'color':'bright gray','occluded':'hidden by native depth test','depth_tolerance_m':0.002,'physical_string_gauge_or_vibration':False}}
(A/'provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'input_count':len(inputs),'video_count':len(manifest['videos']),'outputs':{str(x):sha(x) for x in outputs if x.exists()}},ensure_ascii=False))
