from pathlib import Path
import hashlib, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont
ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1'
B=ROOT/'docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/native_relief4_static'
A=P/'artifacts_v1'; V=ROOT/'docs/2026-10-19/stability_adapter_2/video/waist_straighten_v1'
sha=lambda b:hashlib.sha256(b).hexdigest()
fsha=lambda p:sha(Path(p).read_bytes())
input_paths=[P/'artifact_brief_v1.md',P/'posture_final_v1.json',P/'analysis_final_v1/analysis.json',B/'media/capture.json',P/'native_add4_static/media/capture.json',P/'native_add8_static/media/capture.json']
for run in ['native_add4_static','native_add8_static']:
 input_paths += [P/run/f for f in ['initial_values.json','report.json','final_state.json','trace.json','media/capture.json']]
 input_paths += [P/run/'media'/f'{v}.mp4' for v in ['whole_body','hands']]
source_frames=[B/'media/frames/whole_body/00000.png',P/'native_add8_static/media/frames/whole_body/00000.png']
for v in ['whole_body','hands']:
 for i in [0,60,150]:source_frames.append(P/'native_add8_static/media/frames'/v/f'{i:05d}.png')
producer_paths=[P/'analyze_waist_straighten_v1.py',ROOT/'stability_adapter_2/analyze_waist_straighten_v1.py', A/'build_artifacts_v1.py']
inputs_before={p:fsha(p) for p in input_paths+source_frames if p.exists()}
producers_before={p:fsha(p) for p in producer_paths if p.exists()}
font=ImageFont.truetype('/usr/share/fonts/truetype/nanum/NanumGothic.ttf',18)
def gallery(path,panels,title):
 w,h=520,292; header,footer,gap=42,32,16
 im=Image.new('RGB',(gap+(w+gap)*len(panels),header+h+footer),'white'); d=ImageDraw.Draw(im); d.text((gap,12),title,fill='black',font=font)
 for j,(src,label) in enumerate(panels):
  frame=Image.open(src).convert('RGB').resize((w,h),Image.Resampling.LANCZOS); x=gap+j*(w+gap); im.paste(frame,(x,header)); d.text((x,header+h+7),label,fill='black',font=font)
 im.save(path)
# Native initial whole-body exact camera comparison.
capB=json.load(open(B/'media/capture.json')); cap8=json.load(open(P/'native_add8_static/media/capture.json'))
camera={}
for v in ['whole_body','hands']:
 x=capB['frames'][0]['cameras'][v]; y=cap8['frames'][0]['cameras'][v]
 camera[v]={'view_matrix_exact':x['view_matrix']==y['view_matrix'],'projection_matrix_exact':x['projection_matrix']==y['projection_matrix']}
baseframe=B/'media/frames/whole_body/00000.png'; afterframe=P/'native_add8_static/media/frames/whole_body/00000.png'
gallery(A/'initial_whole_comparison_v1.png',[(baseframe,'현재 4° · native_relief4_static · t=0.000 s'),(afterframe,'추가 8° · native_add8_static · t=0.000 s')],'실제 Isaac Gym 초기 프레임 · 전신 · 카메라 행렬 대조')
def crop(src,dst):
 im=Image.open(src).convert('RGB'); im.crop((365,190,875,590)).resize((680,534),Image.Resampling.LANCZOS).save(dst)
crop(baseframe,A/'closeup_current4_initial_v1.png'); crop(afterframe,A/'closeup_add8_initial_v1.png')
l=Image.open(A/'closeup_current4_initial_v1.png'); r=Image.open(A/'closeup_add8_initial_v1.png'); out=Image.new('RGB',(l.width*2+32,l.height+68),'white'); d=ImageDraw.Draw(out)
d.text((8,8),'현재 4° · native_relief4_static · t=0.000 s',fill='black',font=font);d.text((l.width+24,8),'추가 8° · native_add8_static · t=0.000 s',fill='black',font=font);out.paste(l,(8,36));out.paste(r,(l.width+24,36));out.save(A/'initial_closeup_comparison_v1.png')
# Chosen 8° run native frame timeline.
for view in ['whole_body','hands']:
 panels=[]
 for sec,i in [(0,0),(2,60),(5,150)]: panels.append((P/'native_add8_static/media/frames'/view/f'{i:05d}.png',f'추가 8° · t={sec}.000 s · native frame {i}'))
 gallery(A/f'add8_{view}_0_2_5_v1.png',panels,f'실제 Isaac Gym 원프레임 · {"전신" if view=="whole_body" else "손·기타 카메라"}')
# Copy source MP4s without re-encoding.
videos=[]
for run,label in [('native_add4_static','추가 4°'),('native_add8_static','추가 8°')]:
 for view,vlabel in [('whole_body','전신'),('hands','손·기타 카메라')]:
  src=P/run/'media'/f'{view}.mp4'; dst=V/f'{run}_{view}.mp4';shutil.copyfile(src,dst); assert fsha(src)==fsha(dst)
  stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)]))['streams'][0]
  videos.append({'run':run,'condition':label,'view':vlabel,'source':str(src),'path':str(dst),'source_sha256':fsha(src),'copy_sha256':fsha(dst),'byte_exact':fsha(src)==fsha(dst),'bytes':dst.stat().st_size,'ffprobe':stream})
source_records=[]
for p,before in inputs_before.items():
 after=fsha(p); assert before==after
 source_records.append({'path':str(p),'sha256_before':before,'sha256_after':after,'unchanged':True})
producer_records=[]
for p,before in producers_before.items():
 after=fsha(p); assert before==after
 producer_records.append({'path':str(p),'sha256_before':before,'sha256_after':after,'unchanged':True})
images=[{'path':str(p),'sha256':fsha(p)} for p in sorted(A.glob('*.png'))]
manifest={'purpose':'native image and video packaging; no simulation rerun or video re-encode','camera_comparison':camera,'native_source_inputs':source_records,'producers':producer_records,'video_copies':videos,'derived_images':images}
(V/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(A/'provenance_v1.json').write_text(json.dumps({'purpose':'read-only source/producers SHA before and after artifact packaging','native_source_inputs':source_records,'producers':producer_records,'manifest_path':str(V/'manifest_v1.json'),'manifest_sha256':fsha(V/'manifest_v1.json')},ensure_ascii=False,indent=2)+'\n')
