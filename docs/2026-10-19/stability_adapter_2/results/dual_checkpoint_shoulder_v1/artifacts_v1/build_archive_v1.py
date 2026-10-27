from pathlib import Path
import hashlib,json,subprocess,shutil
from PIL import Image,ImageDraw,ImageFont
D=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2');P=D/'results/dual_checkpoint_shoulder_v1';A=P/'artifacts_v1';V=D/'video/dual_checkpoint_shoulder_v1'
R=P/'native_v2';BASE=D/'results/shoulder_forward_v1/native_v2/shoulder_forward10mm';FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def snap(p):return {'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
def probe(p):
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(p)],text=True))['streams'][0]
 return {k:d.get(k) for k in ('width','height','avg_frame_rate','nb_read_frames','duration')}
capture=json.load(open(R/'media/capture.json'))
frames={int(x['physics_step']):i for i,x in enumerate(capture['frames'])}
assert frames[0]==0 and frames[480]==60 and frames[492]==62
frame_idxs={'00000':0,'00060':480,'00062':492}
inputs=[P/'connection_verification_v3.json',P/'connection_verification_v2.json',P/'ANALYSIS_NOTES_V1.md',P/'native_v1/report.json',P/'native_v2/report.json',P/'native_v2/initial_values.json',P/'native_v2/trace.json',P/'native_v2/media/capture.json',P/'native_v2/media/videos.json',P/'native_v2/media/whole_body.mp4',P/'native_v2/media/hands.mp4',P/'native_v2/media/frames/whole_body/00000.png',P/'native_v2/media/frames/whole_body/00060.png',P/'native_v2/media/frames/whole_body/00062.png',P/'native_v2/media/frames/hands/00000.png',P/'native_v2/media/frames/hands/00060.png',P/'native_v2/media/frames/hands/00062.png',BASE/'report.json',BASE/'initial_values.json',BASE/'trace.json',BASE/'media/physics_endpoint_contacts.json',BASE/'media/frames/whole_body/00000.png',BASE/'media/whole_body.mp4',BASE/'media/hands.mp4',FONT]
inputs=list(dict.fromkeys(inputs));before={str(p):snap(p) for p in inputs}

rows=[]
for case,run,label in [('checkpoint_connection',R,'dual checkpoint · first source terminal'),('baseline_shoulder10mm',BASE,'연결 직전 baseline · shoulder forward 10 mm')]:
 for view in ('whole_body','hands'):
  src=run/'media'/f'{view}.mp4';dst=V/case/f'{view}.mp4';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst)
  q=probe(dst)
  rows.append({'case':case,'label':label,'view':view,'source':str(src),'source_sha256':sha(src),'destination':str(dst),'copy_sha256':sha(dst),'bytes':dst.stat().st_size,'ffprobe':q})

# Exact native frames from capture.json physical timestamps: 0, 2.00 and terminal 2.05 s.
font=ImageFont.truetype(str(FONT),23);gap=10;band=48
panel_imgs={}
for view in ('whole_body','hands'):
 for idx,step in frame_idxs.items():
  panel_imgs[(view,step)]=Image.open(R/'media/frames'/view/f'{idx}.png').convert('RGB')
assert all(im.size==(1280,720) for im in panel_imgs.values())
W,H=panel_imgs[('whole_body',0)].size
panel=Image.new('RGB',(3*W+2*gap,2*(H+band)),(248,248,248));draw=ImageDraw.Draw(panel)
for col,(step,label) in enumerate([(0,'0.00초'),(480,'2.00초'),(492,'2.05초 · terminal')]):
 x=col*(W+gap);draw.text((x+12,8),f'전신 · {label}',font=font,fill=(15,15,15));panel.paste(panel_imgs[('whole_body',step)],(x,band))
 y=H+band;draw.text((x+12,H+band+8),f'손 확대 · {label}',font=font,fill=(15,15,15));panel.paste(panel_imgs[('hands',step)],(x,y+band))
panel_path=A/'native_v2_whole_and_hands_0_2_2p05.png';panel.save(panel_path)

after={str(p):snap(p) for p in inputs};assert before==after
manifest=V/'manifest_v1.json';manifest.write_text(json.dumps({'videos':rows},ensure_ascii=False,indent=2)+'\n')
index=['# Dual checkpoint shoulder · 영상 색인','', 'byte-exact 원본 영상 2개입니다. native1은 카메라 키 누락으로 physics 0 step이며 영상이 없습니다. native2의 encoded video는 63 frames/30fps/2.1초이고 native physics는 2.05초에 source terminal로 종료합니다. 파일별 source/copy SHA 및 ffprobe는 [manifest](%s)에 있습니다.'%str(manifest)]
for row in rows:index+=['',f"## {row['case']} · {row['view']}",f"- [{row['label']}]({row['destination']}) — {row['ffprobe']['nb_read_frames']} frames / {row['ffprobe']['avg_frame_rate']} / {row['ffprobe']['duration']} s"]
(V/'INDEX_V1.md').write_text('\n'.join(index)+'\n')

readme='''# 두 checkpoint 연결 및 첫 source terminal 기록\n\n기타 초기값은 현재 shoulder-forward 10 mm 조건과 같게 유지했고, Fret 035000 및 Strike 010000 frozen baseline을 실제 연결했습니다. 이 결과는 초기 연결/전환 smoke test이며 곡 완주가 아닙니다.\n\n![native2 실제 native 전신과 손 0.00초, 2.00초, 2.05초 frame]({panel})\n\n각 패널은 capture.json의 physics step 0/480/492에 해당하는 실제 native renderer frame입니다. 2.05초 terminal frame을 포함하지만, video encode 길이는 2.1초(63 frames×30fps)이며 정지 프레임 연장으로 물리 시간을 늘리지 않았습니다. 손 카메라의 줄은 물리 상호작용 없는 화면 표시입니다.\n\n## Checkpoint와 연결 검증\n\n| Actor | Frozen checkpoint | SHA-256 |\n|---|---|---|\n| Fret | `/home/ajou/yigyu/3/fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt` | `a6f0c303f69686eb02ebed5f7dce743fdc223fd89c8a8fb2b40303d0abeab5ca` |\n| Strike | `/home/ajou/yigyu/3/strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt` | `9244b33c87426afb28c10a1176b88f23832a50a57605586d4e28084a48160e87` |\n\nConnection verification v3 reports actor-action replay errors 0, frozen weights, baseline initial/PD/mass exact, the first 2.0 s of q/root position exact, normalized physical orientation difference 0, and right effort commands exact for 480 preparation ticks. This confirms the state/connection checks only.\n\n## Terminal result and guitar state\n\nNative1 stopped before physics (0 steps) because the camera key `OM_appearance` was missing. It is preserved as setup failure and has no movie. Native2 ran 492 physics steps/123 control ticks: 2.0 s PREP (120 ticks), then only 0.05 s PLAY (3 paired inference ticks) before the first Fret source terminal. Fret wrist-safety and finger-back termination were true; Fret `goal_finished` was false. Strike `done` and `goal_finished` were false, physical target hit false. No music completion, press, joint-resolved event or joint crossing was observed. Therefore this test does not establish any completed musical performance or a failure rate for the whole song.\n\nAt terminal, the left wrist source-local G position was `[0.128451675, -0.093393892, -0.568670034] m`; source wrist safety and finger-back termination were true, with finger-back minimum local z values about −0.470 to −0.462 m. The final hand view shows its guitar-relative placement at the terminal. These are the recorded source detector coordinates/results, not a claim of a native guitar physical press.\n\nThe guitar body bounding-box center changed 9.617284 mm and total SO(3) orientation 2.983343° at the terminal; run maxima were 10.455249 mm and 3.343712°. The observed 2.00→2.05 s changes were 0.037970 mm and 0.012452°. These endpoint values are descriptive and not attributed causally to the actor connection. Upper-arm contact presence was 458/492; left hand, head and distal-arm contact were 0.\n\nStrap OFF, free guitar, root/lower fixed, no direct guitar force, training updates 0. The stopped PLAY window is too short to judge Fret/Strike performance. The planned next step is a guitar-relative left-hand READY/wrist/finger-safe transition during PREP while preserving existing safety and source handoff behavior.\n\nThe corrected analysis authority is [connection_verification_v3.json]({verify}). Earlier analyzer v1 quaternion-representation check and v2 raw-OBJ bounding-box coordinate issue are documented, not used as this conclusion. V3 uses the XML body offset; the guitar body bounding-box center in G is `[0, −0.4, −0.055937985] m`. [Analysis notes]({notes}) · [native1 setup failure report]({r1}) · [native2 report]({r2}) · [video index]({index}) · [SHA/ffprobe manifest]({manifest})\n'''.format(panel=str(panel_path),verify=str(P/'connection_verification_v3.json'),notes=str(P/'ANALYSIS_NOTES_V1.md'),r1=str(P/'native_v1/report.json'),r2=str(P/'native_v2/report.json'),index=str(V/'INDEX_V1.md'),manifest=str(manifest))
readme_path=A/'README_V1.md';readme_path.write_text(readme)

prov={'task':'dual-checkpoint transfer archive and terminal-state explanation','new_physics_or_training_runs':0,'exact_video_copies':2,
 'inputs_before_after':{str(p):{'before':before[str(p)],'after':after[str(p)],'unchanged':before[str(p)]==after[str(p)]} for p in inputs},
 'producer':{'path':str(A/'build_archive_v1.py'),'sha256':sha(A/'build_archive_v1.py'),'bytes':(A/'build_archive_v1.py').stat().st_size},
 'font':{'path':str(FONT),'sha256':sha(FONT)},'capture_frame_map':{str(step):{'frame_file':fname+'.png','frame_index':frames[step],'time_s':capture['frames'][frames[step]]['time_s'],'physics_step':capture['frames'][frames[step]]['physics_step']} for fname,step in frame_idxs.items()},
 'outputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in [panel_path,manifest,V/'INDEX_V1.md',readme_path]},'exact_video_copies':rows}
(A/'provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
