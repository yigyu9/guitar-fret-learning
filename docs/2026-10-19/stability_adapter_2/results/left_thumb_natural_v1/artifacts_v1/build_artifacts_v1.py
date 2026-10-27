#!/usr/bin/env python3
"""Byte-exact packaging for the closed left-thumb natural-pose native run."""
import hashlib,json,shutil,subprocess
from pathlib import Path
P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1')
A=P/'artifacts_v1'; V=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_thumb_natural_v1')
E=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/native_pick_feedback_v1')
PIN=A/'preflight_pin_v1.json'; CASE=P/'native_v1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def probe(p):
 r=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(p)],check=True,capture_output=True,text=True)
 ss=json.loads(r.stdout).get('streams',[])
 if len(ss)!=1:raise RuntimeError('expected one video stream: '+str(p))
 return ss[0]
if not PIN.is_file():raise RuntimeError('preflight pin is required')
pin=json.loads(PIN.read_text()); selfp=Path(__file__).resolve()
if pin['producer_path']!=str(selfp) or pin['producer_sha256_before']!=sha(selfp):raise RuntimeError('producer SHA mismatch')
for p,h in pin['inputs_before'].items():
 if sha(p)!=h:raise RuntimeError('input SHA changed before packaging: '+p)
report=json.loads((CASE/'report.json').read_text()); capture=json.loads((CASE/'media/capture.json').read_text())
if not report.get('completed') or report.get('physics_steps')!=1200 or report.get('control_steps')!=300 or report.get('physics_seconds')!=5.0:raise RuntimeError('native run is not closed 5s')
if capture.get('fps')!=30:raise RuntimeError('capture fps mismatch')
frames={int(f['physics_step']):f for f in capture['frames']}
for step,t in ((0,0.0),(480,2.0),(1200,5.0)):
 if step not in frames or frames[step]['time_s']!=t:raise RuntimeError('frame/time mapping mismatch')
records=[]
for view in ('whole_body','hands','thumb_back'):
 src=CASE/'media'/f'{view}.mp4'; expected=report['videos'][view]['sha256']
 if sha(src)!=expected:raise RuntimeError('MP4 report SHA mismatch')
 stream=probe(src)
 if (stream.get('width'),stream.get('height'),stream.get('avg_frame_rate'),stream.get('nb_read_frames'),stream.get('duration'))!=(1280,720,'30/1','151','5.033333'):raise RuntimeError('MP4 stream metadata mismatch')
 dst=V/f'{view}.mp4'
 with dst.open('xb') as out,src.open('rb') as inp:shutil.copyfileobj(inp,out)
 if sha(dst)!=expected or dst.stat().st_size!=src.stat().st_size or probe(dst)!=stream:raise RuntimeError('MP4 byte-copy verification failed')
 records.append({'kind':'video','view':view,'source':str(src),'destination':str(dst),'sha256':expected,'size_bytes':dst.stat().st_size,'ffprobe':stream})
# Current native selected captures: whole-body t=0/5 and hands t=0 plus thumb-back t=0/2/5.
selections=[('current','whole_body',0),('current','whole_body',1200),('current','hands',0),('current','thumb_back',0),('current','thumb_back',480),('current','thumb_back',1200)]
for cohort,view,step in selections:
 f=frames[step]; src=Path(next(x for x in f['image_sha256'] if f'/frames/{view}/' in x)); expected=f['image_sha256'][str(src)]
 if sha(src)!=expected:raise RuntimeError('capture image SHA mismatch: '+str(src))
 t=int(f['time_s']); dst=A/f'current_t{t:02d}_{view}.png'
 with dst.open('xb') as out,src.open('rb') as inp:shutil.copyfileobj(inp,out)
 if sha(dst)!=expected or dst.stat().st_size!=src.stat().st_size:raise RuntimeError('PNG byte-copy verification failed')
 records.append({'kind':'frame','cohort':cohort,'view':view,'physics_step':step,'time_s':t,'source':str(src),'destination':str(dst),'sha256':expected,'size_bytes':dst.stat().st_size})
# Earlier approved comparison: same native front-hands view at initial time.
old_capture=json.loads((E/'media/capture.json').read_text()); old0=next(f for f in old_capture['frames'] if f['physics_step']==0)
old_src=Path(next(x for x in old0['image_sha256'] if '/frames/hands/' in x)); old_sha=old0['image_sha256'][str(old_src)]
if sha(old_src)!=old_sha:raise RuntimeError('baseline initial hands SHA mismatch')
old_dst=A/'baseline_elbow_wrist_pick_feedback_t00_hands.png'
with old_dst.open('xb') as out,old_src.open('rb') as inp:shutil.copyfileobj(inp,out)
if sha(old_dst)!=old_sha or old_dst.stat().st_size!=old_src.stat().st_size:raise RuntimeError('baseline image copy verification failed')
records.append({'kind':'baseline_frame','case':'native_pick_feedback_v1','view':'hands','physics_step':0,'time_s':0.0,'source':str(old_src),'destination':str(old_dst),'sha256':old_sha,'size_bytes':old_dst.stat().st_size})
for p,h in pin['inputs_before'].items():
 if sha(p)!=h:raise RuntimeError('input changed during packaging: '+p)
producer_after=sha(selfp)
if producer_after!=pin['producer_sha256_before']:raise RuntimeError('producer changed during execution')
obj={'schema':'native_artifact_provenance_v1','producer':str(selfp),'producer_sha256_before':pin['producer_sha256_before'],'producer_sha256_after':producer_after,'inputs_before':pin['inputs_before'],'inputs_after':{p:sha(p) for p in pin['inputs_before']},'outputs':records,'scope_note':'All PNG and MP4 outputs are byte-exact native copies. Physics observation is 5.0 s; encoded video duration is 5.033333 s.'}
with (A/'provenance_v1.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'outputs':len(records),'provenance':str(A/'provenance_v1.json')}))
