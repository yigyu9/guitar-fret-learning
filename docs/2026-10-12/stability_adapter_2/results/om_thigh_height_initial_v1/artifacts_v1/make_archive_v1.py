#!/usr/bin/env python3
"""Archive completed OM initial thigh-height comparison media."""
from pathlib import Path
import hashlib,json,shutil,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-12');P=ROOT/'stability_adapter_2/results/om_thigh_height_initial_v1';A=P/'artifacts_v1';V=ROOT/'video/om_thigh_height_initial_v1'
CASES=[('previous_high','/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v1/lean18_back30','이전 높은 기준'),('thigh_gap8mm',str(P/'native_v1/thigh_gap8mm'),'양 Hip 최소 source gap 8 mm'),('thigh_gap3mm',str(P/'native_v1/thigh_gap3mm'),'양 Hip 최소 source gap 3 mm')]
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def pin(ps):return {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in ps}
def font(n):return ImageFont.truetype(str(FONT),n)
def native_path(case):return Path(case[1])
def frame(case,view,t):
 n=native_path(case);cap=json.loads((n/'media/capture.json').read_text());f=next(x for x in cap['frames'] if x['time_s']==float(t))
 p=Path(next(k for k in f['image_sha256'] if f'/{view}/' in k));assert sha(p)==f['image_sha256'][str(p)]
 return p
inputs=[P/'verification_v1.json',P/'search_v2/search.json',P/'search_v2/thigh_gap8mm/config.json',P/'search_v2/thigh_gap3mm/config.json',FONT]
for case in CASES:
 n=native_path(case);inputs += [n/'report.json',n/'initial_values.json',n/'trace.json',n/'contacts.json',n/'media/capture.json',n/'media/initial_strings.png',n/'media/whole_body.mp4',n/'media/hands.mp4']
 for t in (0,2,5):inputs.extend(frame(case,v,t) for v in ('whole_body','hands'))
inputs += [P/'native_v1/thigh_gap8mm/media/initial_thigh_side.png',P/'native_v1/thigh_gap3mm/media/initial_thigh_side.png',Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v2/lean18_back30_hold_pi/media/initial_axilla_side.png')]
before=pin(inputs);assert json.loads((P/'verification_v1.json').read_text())['passed'] is True
# Verify the whole-body view/projection matrices match across all conditions and times.
for t in (0,2,5):
 matrices=[]
 for case in CASES:
  cap=json.loads((native_path(case)/'media/capture.json').read_text());fr=next(x for x in cap['frames'] if x['time_s']==float(t))
  matrices.append((fr['cameras']['whole_body']['view_matrix'],fr['cameras']['whole_body']['projection_matrix']))
 assert matrices[0]==matrices[1]==matrices[2]
for c in CASES:assert json.loads((native_path(c)/'report.json').read_text())['completed'] is True
A.mkdir(parents=True,exist_ok=True);V.mkdir(parents=True,exist_ok=True)
imgs=[[Image.open(frame(c,'whole_body',t)).convert('RGB') for c in CASES] for t in (0,2,5)]
w=max(x.width for row in imgs for x in row);h=max(x.height for row in imgs for x in row);gap=12;head=78;left=54
out=Image.new('RGB',(left+3*(w+gap)+gap,head+3*(h+gap)+gap),(248,248,248));d=ImageDraw.Draw(out)
for j,c in enumerate(CASES):d.text((left+j*(w+gap)+2,12),c[2],font=font(18),fill=(15,15,15))
for i,t in enumerate((0,2,5)):
 d.text((8,head+i*(h+gap)+8),f'{t}초',font=font(20),fill=(15,15,15))
 for j,im in enumerate(imgs[i]):out.paste(im,(left+j*(w+gap),head+i*(h+gap)))
out.save(A/'whole_body_0_2_5s_comparison.png')
ims=[Image.open(native_path(c)/'media/initial_strings.png').convert('RGB') for c in CASES];w=max(x.width for x in ims);h=max(x.height for x in ims);gap=12;head=58
out=Image.new('RGB',(3*w+4*gap,h+head+gap),(248,248,248));d=ImageDraw.Draw(out)
for j,(im,c) in enumerate(zip(ims,CASES)):
 x=gap+j*(w+gap);out.paste(im,(x,head));d.text((x+5,12),c[2],font=font(18),fill=(15,15,15))
out.save(A/'initial_strings_3conditions.png')
side=[Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v2/lean18_back30_hold_pi/media/initial_axilla_side.png'),P/'native_v1/thigh_gap8mm/media/initial_thigh_side.png',P/'native_v1/thigh_gap3mm/media/initial_thigh_side.png']
labels=['이전 높은 기준 · 초기 pose','thigh gap 8 mm · 초기 측면','thigh gap 3 mm · 초기 측면']
ims=[Image.open(x).convert('RGB') for x in side];w=max(x.width for x in ims);h=max(x.height for x in ims);gap=12;head=58
out=Image.new('RGB',(3*w+4*gap,h+head+gap),(248,248,248));d=ImageDraw.Draw(out)
for j,(im,label) in enumerate(zip(ims,labels)):
 x=gap+j*(w+gap);out.paste(im,(x,head));d.text((x+5,12),label,font=font(18),fill=(15,15,15))
d.text((gap,head+h+5),'각 native camera는 기타 기준 follow view: 화면상 픽셀 높이 차는 실제 world z 하강량이 아님',font=font(16),fill=(20,20,20))
out.save(A/'initial_side_comparison.png')
manifest={'videos':[]}
for label,path,title in CASES:
 for view in ('whole_body','hands'):
  src=native_path((label,path,title))/'media'/f'{view}.mp4';dst=V/f'{label}_{view}.mp4';shutil.copyfile(src,dst);assert sha(src)==sha(dst)
  fs=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)],text=True))['streams'][0]
  manifest['videos'].append({'condition':label,'view':view,'source':str(src),'destination':str(dst),'source_sha256':sha(src),'copy_sha256':sha(dst),'bytes':dst.stat().st_size,'ffprobe':fs})
(V/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
after=pin(inputs);assert before==after
outputs=[A/'make_archive_v1.py',A/'whole_body_0_2_5s_comparison.png',A/'initial_strings_3conditions.png',A/'initial_side_comparison.png',V/'manifest_v1.json']+[V/f'{label}_{view}.mp4' for label,_,_ in CASES for view in ('whole_body','hands')]
(A/'provenance_v1.json').write_text(json.dumps({'inputs_before':before,'inputs_after':after,'producer_sha256':sha(A/'make_archive_v1.py'),'outputs':pin(outputs),'native_reruns':0,'video_recopies_after_archive':0},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'input_count':len(inputs),'videos':len(manifest['videos']),'pngs':{str(x):sha(x) for x in outputs if x.suffix=='.png'}},ensure_ascii=False))
