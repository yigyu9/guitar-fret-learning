from pathlib import Path
import hashlib,json,shutil,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/home/ajou/yigyu/3'); P=ROOT/'docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1'; B=ROOT/'docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/native_add8_static'; A=P/'artifacts_v1'; V=ROOT/'docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1'
sha=lambda b:hashlib.sha256(b).hexdigest(); fsha=lambda p:sha(Path(p).read_bytes())
runs=['native_relief12_static','native_relief20_static','native_upper20_static','native_upper40_static','native_wrap40_static','native_wrap55_static','native_wrap55_elbow_wave']
# Direct source files and per-run raw video/frame files consumed by this package.
source=[P/'timelines_final_v1.json',P/'posture_final_v1.json',P/'waist_final_v1.json']
for run in runs:
 d=P/run; source += [d/'initial_values.json',d/'report.json',d/'media/capture.json',d/'media/videos.json']
 source += [d/'media'/f'{v}.mp4' for v in ['whole_body','hands']]
source += [B/'initial_values.json',B/'report.json',B/'media/capture.json',B/'media/initial_support_side.png',B/'media/frames/whole_body/00000.png']
for run,view,indices in [('native_wrap55_static','whole_body',[0,60,150]),('native_wrap55_elbow_wave','whole_body',[0,60,150]),('native_wrap55_static','hands',[0,60,150]),('native_wrap55_elbow_wave','hands',[0,60,150])]:
 source += [P/run/'media/frames'/view/f'{i:05d}.png' for i in indices]
source += [P/'native_wrap55_static/media/initial_support_side.png']
producers=[ROOT/'stability_adapter_2/analyze_right_arm_wrap_timelines_v2.py',ROOT/'stability_adapter_2/analyze_right_arm_wrap_posture_v2.py',A/'build_artifacts_v1.py']
inputs_before={p:fsha(p) for p in source if p.exists()}; producers_before={p:fsha(p) for p in producers if p.exists()}
font=ImageFont.truetype('/usr/share/fonts/truetype/nanum/NanumGothic.ttf',18)
def gallery(path,panels,title,resize=(520,292)):
 w,h=resize; top,bottom,gap=42,32,16
 canvas=Image.new('RGB',(gap+(w+gap)*len(panels),top+h+bottom),'white'); draw=ImageDraw.Draw(canvas); draw.text((gap,12),title,fill='black',font=font)
 for j,(src,label) in enumerate(panels):
  im=Image.open(src).convert('RGB').resize((w,h),Image.Resampling.LANCZOS); x=gap+j*(w+gap); canvas.paste(im,(x,top)); draw.text((x,top+h+6),label,fill='black',font=font)
 canvas.save(path)
# Native whole-body initial camera check against baseline.
capB=json.load(open(B/'media/capture.json')); capS=json.load(open(P/'native_wrap55_static/media/capture.json'))
cameras={}
for view in ['whole_body','hands']:
 x=capB['frames'][0]['cameras'][view]; y=capS['frames'][0]['cameras'][view]
 cameras[view]={'view_matrix_exact':x['view_matrix']==y['view_matrix'],'projection_matrix_exact':x['projection_matrix']==y['projection_matrix']}
wbB=B/'media/frames/whole_body/00000.png'; wbS=P/'native_wrap55_static/media/frames/whole_body/00000.png'
gallery(A/'initial_whole_comparison_v1.png',[(wbB,'waist_add8 기준 · t=0.000 s'),(wbS,'wrap55 선택 · t=0.000 s')],'실제 native 전신 초기 프레임 · 카메라 메타데이터 대조')
# Two side-view native PNGs retain their actual G-relative camera targets; captions disclose view limit.
sideB=B/'media/initial_support_side.png'; sideS=P/'native_wrap55_static/media/initial_support_side.png'
gallery(A/'initial_side_comparison_v1.png',[(sideB,'기준 · native_add8_static · native 초기 side'),(sideS,'선택 · native_wrap55_static · native 초기 side')],'실제 native side 캡처 · G 상대 카메라 목표가 달라 시각 비교',resize=(520,390))
# Same-region crop from identical whole-body camera frames. Shared image-space region.
def crop(src,dst):
 im=Image.open(src).convert('RGB'); im.crop((390,125,930,555)).resize((540,430),Image.Resampling.LANCZOS).save(dst)
for sec,i in [(0,0),(2,60),(5,150)]:
 for run in ['native_wrap55_static','native_wrap55_elbow_wave']:
  crop(P/run/'media/frames/whole_body'/f'{i:05d}.png',A/f'{run}_{sec}s_upper_crop_v1.png')
for mode,run in [('static','native_wrap55_static'),('wave','native_wrap55_elbow_wave')]:
 for view in ['whole_body']:
  panels=[]
  for sec,i in [(0,0),(2,60),(5,150)]:panels.append((P/run/'media/frames'/view/f'{i:05d}.png',f'{mode} · t={sec}.000 s · frame {i}'))
  gallery(A/f'{run}_whole_0_2_5_v1.png',panels,'실제 native 전신 원프레임 · '+('정지' if mode=='static' else '팔꿈치 wave'))
# One upper crop timeline each: crops are native view pixels with fixed bounds; do not synthesize camera.
for mode,run in [('static','native_wrap55_static'),('wave','native_wrap55_elbow_wave')]:
 panels=[(A/f'{run}_{sec}s_upper_crop_v1.png',f'{mode} · t={sec}.000 s · 같은 native frame crop') for sec in [0,2,5]]
 gallery(A/f'{run}_upper_crop_0_2_5_v1.png',panels,'실제 전신 native frame의 같은 상체 영역 crop · '+('정지' if mode=='static' else '팔꿈치 wave'),resize=(360,287))
# Chosen wave actual hands camera timeline.
panels=[]
for sec,i in [(0,0),(2,60),(5,150)]:panels.append((P/'native_wrap55_elbow_wave/media/frames/hands'/f'{i:05d}.png',f'wave · t={sec}.000 s · frame {i}'))
gallery(A/'native_wrap55_elbow_wave_hands_0_2_5_v1.png',panels,'실제 native 손·기타 카메라 원프레임 · elbow wave')
# Copy sixteen source MP4s exactly; keep each true duration including partials.
videos=[]
for run,label in [('baseline_add8_static','직전 기준 waist straighten 추가 8°'),*[(r,r.replace('native_','').replace('_',' ')) for r in runs]]:
 base=B if run=='baseline_add8_static' else P/run
 for view,caption in [('whole_body','전신'),('hands','손·기타 확대')]:
  src=base/'media'/f'{view}.mp4'; dst=V/f'{run}_{view}.mp4'; shutil.copyfile(src,dst); assert fsha(src)==fsha(dst)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)]))['streams'][0]
  report=json.load(open(base/'report.json'))
  videos.append({'run':run,'label':label,'view':caption,'source':str(src),'path':str(dst),'source_sha256':fsha(src),'copy_sha256':fsha(dst),'byte_exact':True,'bytes':dst.stat().st_size,'completed_5s':report.get('completed',False),'physics_steps':report.get('physics_steps'),'control_steps':report.get('control_steps'),'ffprobe':probe})
source_records=[]
for p,before in inputs_before.items():
 after=fsha(p); assert before==after; source_records.append({'path':str(p),'sha256_before':before,'sha256_after':after,'unchanged':True})
producer_records=[]
for p,before in producers_before.items():
 after=fsha(p); assert before==after; producer_records.append({'path':str(p),'sha256_before':before,'sha256_after':after,'unchanged':True})
images=[{'path':str(p),'sha256':fsha(p)} for p in sorted(A.glob('*.png'))]
manifest={'purpose':'native artifact packaging, no new simulation or video re-encode','camera_comparison':cameras,'native_source_inputs':source_records,'producers':producer_records,'video_copies':videos,'derived_images':images}
(V/'manifest_v1.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(A/'provenance_v1.json').write_text(json.dumps({'purpose':'read-only inputs and producers SHA before/after artifact packaging','native_source_inputs':source_records,'producers':producer_records,'manifest_path':str(V/'manifest_v1.json'),'manifest_sha256':fsha(V/'manifest_v1.json')},ensure_ascii=False,indent=2)+'\n')
