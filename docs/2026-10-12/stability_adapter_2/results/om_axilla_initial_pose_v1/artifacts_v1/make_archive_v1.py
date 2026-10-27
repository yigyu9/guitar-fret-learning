#!/usr/bin/env python3
"""Archive completed OM axilla native views and exact-copy source videos."""
from pathlib import Path
import hashlib,json,shutil,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-12')
P=ROOT/'stability_adapter_2/results/om_axilla_initial_pose_v1'; A=P/'artifacts_v1';V=ROOT/'video/om_axilla_initial_pose_v1'
CASES=[('clear_reference','native_v1/clear_reference','초기 기준'),('lean18_back30','native_v1/lean18_back30','기울임 18°·후방 30° · hold OFF'),('lean18_back30_hold_pi','native_v2/lean18_back30_hold_pi','기울임 18°·후방 30° · hold ON')]
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def pin(ps):return {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in ps}
def fnt(n):return ImageFont.truetype(str(FONT),n)
def captured(case,view,t):
 native=P/case[1];cap=json.loads((native/'media/capture.json').read_text());fr=next(x for x in cap['frames'] if x['time_s']==float(t))
 p=Path(next(k for k in fr['image_sha256'] if f'/{view}/' in k));assert sha(p)==fr['image_sha256'][str(p)]
 return p,fr

inputs=[Path('/home/ajou/yigyu/3/stability_adapter_2/OM_AXILLA_INITIAL_POSE_PLAN_V2.md'),FONT]
for label,path,title in CASES:
 n=P/path; inputs += [n/'report.json',n/'initial_values.json',n/'trace.json',n/'contacts.json',n/'native_properties.json',n/'inputs_verified.json',n/'media/capture.json',n/'media/initial_strings.png',n/'media/whole_body.mp4',n/'media/hands.mp4']
 if label=='lean18_back30_hold_pi':inputs += [n/'media/initial_axilla_side.png',n/'media/joint_hold_correction.json',n/'media/strap_state_samples.json']
 for t in (0,2,5):
  for view in ('whole_body','hands'):inputs.append(captured((label,path,title),view,t)[0])
before=pin(inputs)
for label,path,title in CASES:assert json.loads((P/path/'report.json').read_text()).get('completed') is True
A.mkdir(parents=True,exist_ok=True);V.mkdir(parents=True,exist_ok=True)
# 3 rows are 0/2/5 seconds; columns identify each evaluated condition.
imgs=[[Image.open(captured(case,'whole_body',t)[0]).convert('RGB') for case in CASES] for t in (0,2,5)]
w=max(im.width for row in imgs for im in row);h=max(im.height for row in imgs for im in row);gap=12;head=84;left=56
out=Image.new('RGB',(left+3*(w+gap)+gap,head+3*(h+gap)+gap),(248,248,248));d=ImageDraw.Draw(out)
for ci,c in enumerate(CASES):d.text((left+ci*(w+gap)+3,12),c[2],font=fnt(19),fill=(15,15,15))
for ri,t in enumerate((0,2,5)):
 d.text((7,head+ri*(h+gap)+8),f'{t}초',font=fnt(20),fill=(15,15,15))
 for ci,im in enumerate(imgs[ri]):out.paste(im,(left+ci*(w+gap),head+ri*(h+gap)))
out.save(A/'whole_body_conditions_0_2_5s.png')
# Initial string overlays: one per condition in a single labelled comparison.
ims=[Image.open(P/case[1]/'media/initial_strings.png').convert('RGB') for case in CASES]
w=max(i.width for i in ims);h=max(i.height for i in ims);gap=12;head=60
out=Image.new('RGB',(3*w+4*gap,h+head+gap),(248,248,248));d=ImageDraw.Draw(out)
for i,(im,c) in enumerate(zip(ims,CASES)):
 x=gap+i*(w+gap);out.paste(im,(x,head));d.text((x+6,12),c[2],font=fnt(18),fill=(15,15,15))
out.save(A/'initial_strings_conditions.png')
# Captioned copy of the requested ON side view; original remains untouched.
src=P/'native_v2/lean18_back30_hold_pi/media/initial_axilla_side.png';im=Image.open(src).convert('RGB');band=58
cap=Image.new('RGB',(im.width,im.height+band),(248,248,248));cap.paste(im,(0,band));ImageDraw.Draw(cap).text((12,12),'hold ON · 초기 겨드랑이 측면 native camera',font=fnt(20),fill=(15,15,15));cap.save(A/'hold_on_initial_axilla_side_captioned.png')
manifest={'videos':[]}
for label,path,title in CASES:
 for view in ('whole_body','hands'):
  src=P/path/'media'/f'{view}.mp4';dst=V/f'{label}_{view}.mp4';shutil.copyfile(src,dst);assert sha(src)==sha(dst)
  stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)],text=True))['streams'][0]
  manifest['videos'].append({'condition':label,'view':view,'source':str(src),'destination':str(dst),'source_sha256':sha(src),'copy_sha256':sha(dst),'bytes':dst.stat().st_size,'ffprobe':stream})
(V/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
after=pin(inputs);assert before==after
outputs=[A/'make_archive_v1.py',A/'whole_body_conditions_0_2_5s.png',A/'initial_strings_conditions.png',A/'hold_on_initial_axilla_side_captioned.png',V/'manifest_v1.json']+[V/f'{label}_{view}.mp4' for label,_,_ in CASES for view in ('whole_body','hands')]
(A/'provenance_v1.json').write_text(json.dumps({'inputs_before':before,'inputs_after':after,'producer_sha256':sha(A/'make_archive_v1.py'),'outputs':pin(outputs),'native_reruns':0,'video_recopies_after_archive':0},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'input_count':len(inputs),'video_count':len(manifest['videos']),'outputs':{str(x):sha(x) for x in outputs if x.suffix=='.png'}},ensure_ascii=False))
