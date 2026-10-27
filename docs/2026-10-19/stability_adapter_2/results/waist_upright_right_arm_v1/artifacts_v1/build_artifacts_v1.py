from pathlib import Path
import hashlib, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont
ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1'
W=ROOT/'docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/native_static_v2'
A=P/'artifacts_v1'; V=ROOT/'docs/2026-10-19/stability_adapter_2/video/waist_upright_right_arm_v1'
sha=lambda b: hashlib.sha256(b).hexdigest()
file_sha=lambda p: sha(Path(p).read_bytes())
input_paths=[P/'posture_final_v1.json',P/'analysis_final_v1/analysis.json',P/'artifact_brief_v1.md',P/'native_relief4_static/media/capture.json',W/'media/capture.json']
for run in ['native_relief4_static','native_relief2_static','native_relief4_elbow5']:
  input_paths += [P/run/'media'/f'{kind}.mp4' for kind in ['whole_body','hands']]
source_frames=[W/'media/frames/whole_body/00000.png', P/'native_relief4_static/media/frames/whole_body/00000.png']
for run,indices in [('native_relief4_static',[0]),('native_relief4_elbow5',[0,60,150])]:
  for view in ['whole_body','hands']:
    for i in indices: source_frames.append(P/run/'media/frames'/view/f'{i:05d}.png')
producer_paths=[P/'analyze_posture_v1.py', A/'build_artifacts_v1.py']
inputs_before={p:file_sha(p) for p in input_paths+source_frames if p.exists()}
producers_before={p:file_sha(p) for p in producer_paths if p.exists()}
# Copy all six native encodes byte-for-byte.
items=[]
for run,label in [('native_relief4_static','4도 정지'),('native_relief2_static','2도 정지'),('native_relief4_elbow5','4도 + 팔꿈치 ±5도')]:
  for kind,caption in [('whole_body','전신'),('hands','손·기타 확대')]:
    src=P/run/'media'/f'{kind}.mp4'; dest=V/f'{run}_{kind}.mp4'
    shutil.copyfile(src,dest)
    assert file_sha(src)==file_sha(dest)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dest)]))['streams'][0]
    items.append({'run':run,'label':label,'view':caption,'source':str(src),'path':str(dest),'sha256':file_sha(dest),'source_sha256':file_sha(src),'byte_exact_copy':src.stat().st_size==dest.stat().st_size,'bytes':dest.stat().st_size,'ffprobe':probe})
# Camera exactness and frame proof at native captured times.
base_cap=json.loads((W/'media/capture.json').read_text()); new_cap=json.loads((P/'native_relief4_static/media/capture.json').read_text())
cam={}
for view in ['whole_body','hands']:
  x=base_cap['frames'][0]['cameras'][view]; y=new_cap['frames'][0]['cameras'][view]
  cam[view]={'view_matrix_exact':x['view_matrix']==y['view_matrix'],'projection_matrix_exact':x['projection_matrix']==y['projection_matrix']}
# composited native frame gallery; 0/2/5s: frames 0/60/150, captured original PNGs, labels outside images.
font=ImageFont.truetype('/usr/share/fonts/truetype/nanum/NanumGothic.ttf', 18)
def gallery(out, panels, title):
  w,h=520,292; header=42; footer=32; gap=16
  canvas=Image.new('RGB',(gap+(w+gap)*len(panels),header+h+footer),'white'); d=ImageDraw.Draw(canvas); d.text((gap,12),title,fill='black',font=font)
  for i,(path,label) in enumerate(panels):
    im=Image.open(path).convert('RGB').resize((w,h),Image.Resampling.LANCZOS)
    x=gap+i*(w+gap); y=header
    canvas.paste(im,(x,y)); d.text((x,y+h+7),label,fill='black',font=font)
  canvas.save(out)
# Native initial comparison, same whole-body camera matrices verified exact.
wp=W/'media/frames/whole_body/00000.png'; pp=P/'native_relief4_static/media/frames/whole_body/00000.png'
gallery(A/'initial_whole_comparison_v1.png',[(wp,'기준: right_thigh_waist_v1/native_static_v2 · t=0.000 s'),(pp,'완화 4°: native_relief4_static · t=0.000 s')],'실제 Isaac Gym 초기 프레임 · 전신 · 동일 카메라')
# Identical crop from the same whole-body frame source/view: shoulder/elbow/guitar and waist region.
def crop(src,dst):
 im=Image.open(src).convert('RGB'); im.crop((365,190,875,590)).resize((680,534),Image.Resampling.LANCZOS).save(dst)
for src,name in [(wp,'baseline'),(pp,'relief4')]: crop(src,A/f'closeup_{name}_initial_v1.png')
# one paired close-up plate
left=Image.open(A/'closeup_baseline_initial_v1.png'); right=Image.open(A/'closeup_relief4_initial_v1.png')
out=Image.new('RGB',(left.width*2+32,left.height+68),'white'); d=ImageDraw.Draw(out)
d.text((8,8),'기준 · native_static_v2 · t=0.000 s',fill='black',font=font); d.text((left.width+24,8),'완화 4° · native_relief4_static · t=0.000 s',fill='black',font=font)
out.paste(left,(8,36)); out.paste(right,(left.width+24,36)); out.save(A/'initial_closeup_comparison_v1.png')
# Three native wave times at frame index 0,60,150. Separate galleries for whole and hands.
for view,subdir in [('whole_body','whole_body'),('hands','hands')]:
  panels=[]
  for sec,idx in [(0,0),(2,60),(5,150)]:
    path=P/'native_relief4_elbow5/media/frames'/subdir/f'{idx:05d}.png'
    panels.append((path,f'4° elbow5 · t={sec}.000 s · native frame {idx}'))
  gallery(A/f'elbow5_{view}_0_2_5_v1.png',panels,f'실제 Isaac Gym 원프레임 · {"전신" if view=="whole_body" else "손·기타 확대"}')
# Bracket the read-only sources and producer code around artifact construction.
source_inputs=[]
for p,before in inputs_before.items():
  after=file_sha(p)
  source_inputs.append({'path':str(p),'sha256_before':before,'sha256_after':after,'unchanged':before==after})
  assert before==after
producers=[]
for p,before in producers_before.items():
  after=file_sha(p)
  producers.append({'path':str(p),'sha256_before':before,'sha256_after':after,'unchanged':before==after})
  assert before==after
manifest={'purpose':'native visual artifacts; no simulation rerun','camera_comparison':cam,'source_inputs':source_inputs,'producers':producers,'video_copies':items,'derived_images':[]}
for p in sorted(A.glob('*.png')): manifest['derived_images'].append({'path':str(p),'sha256':file_sha(p)})
(V/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(A/'provenance_v1.json').write_text(json.dumps({'purpose':'artifact packaging provenance; source inputs and producer code bracketed during one packaging run','source_inputs':source_inputs,'producers':producers,'output_manifest':str(V/'manifest_v1.json'),'output_manifest_sha256':file_sha(V/'manifest_v1.json')},ensure_ascii=False,indent=2)+'\n')
