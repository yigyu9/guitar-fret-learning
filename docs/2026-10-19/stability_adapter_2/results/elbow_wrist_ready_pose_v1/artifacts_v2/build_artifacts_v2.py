#!/usr/bin/env python3
"""Byte-exact package for slow-up and pick-feedback native runs."""
import hashlib,json,shutil,subprocess
from pathlib import Path
P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1')
A=P/'artifacts_v2'
V=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1')
PIN=A/'preflight_pin_v2.json'
CASES=('native_slow_up_v1','native_pick_feedback_v1')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def probe(p):
 r=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(p)],check=True,capture_output=True,text=True)
 s=json.loads(r.stdout)['streams']
 if len(s)!=1:raise RuntimeError('expected exactly one video stream')
 return s[0]
if not PIN.is_file():raise RuntimeError('preflight missing')
pin=json.loads(PIN.read_text())
selfp=Path(__file__).resolve()
if pin['producer_path']!=str(selfp) or pin['producer_sha256_before']!=sha(selfp):raise RuntimeError('producer pin mismatch')
for p,h in pin['inputs_before'].items():
 if sha(p)!=h:raise RuntimeError('input changed before execution: '+p)
records=[]
for case in CASES:
 d=P/case
 report=json.loads((d/'report.json').read_text())
 cap=json.loads((d/'media/capture.json').read_text())
 if not report.get('completed') or report.get('physics_steps')!=1200 or report.get('control_steps')!=300 or report.get('physics_seconds')!=5.0:raise RuntimeError('not a closed 5s run: '+case)
 fs={int(x['physics_step']):x for x in cap['frames']}
 for step,t in ((0,0.0),(480,2.0),(1200,5.0)):
  if step not in fs or fs[step]['time_s']!=t:raise RuntimeError('capture frame mapping mismatch')
 for kind in ('whole_body','hands'):
  src=d/'media'/f'{kind}.mp4'; expected=report['videos'][kind]['sha256']
  if sha(src)!=expected:raise RuntimeError('report MP4 SHA mismatch')
  st=probe(src)
  if st.get('width')!=1280 or st.get('height')!=720 or st.get('avg_frame_rate')!='30/1' or st.get('nb_read_frames')!='151' or st.get('duration')!='5.033333':raise RuntimeError('unexpected encoded stream metadata')
  dst=V/f'{case}_{kind}.mp4'
  with dst.open('xb') as o,src.open('rb') as i:shutil.copyfileobj(i,o)
  if sha(dst)!=expected or dst.stat().st_size!=src.stat().st_size or probe(dst)!=st:raise RuntimeError('MP4 copy verification failed')
  records.append({'type':'video','case':case,'view':kind,'source':str(src),'destination':str(dst),'sha256':expected,'size_bytes':dst.stat().st_size,'ffprobe':st})
 for step,t in ((0,0),(480,2),(1200,5)):
  f=fs[step]
  for view in ('whole_body','hands'):
   src=Path(next(p for p in f['image_sha256'] if f'/frames/{view}/' in p)); expected=f['image_sha256'][str(src)]
   if sha(src)!=expected:raise RuntimeError('capture frame SHA mismatch: '+str(src))
   dst=A/f'{case}_t{t:02d}_{view}.png'
   with dst.open('xb') as o,src.open('rb') as i:shutil.copyfileobj(i,o)
   if sha(dst)!=expected or dst.stat().st_size!=src.stat().st_size:raise RuntimeError('PNG copy verification failed')
   records.append({'type':'frame','case':case,'step':step,'time_s':t,'view':view,'source':str(src),'destination':str(dst),'sha256':expected,'size_bytes':dst.stat().st_size})
for p,h in pin['inputs_before'].items():
 if sha(p)!=h:raise RuntimeError('input changed while packaging: '+p)
after=sha(selfp)
if after!=pin['producer_sha256_before']:raise RuntimeError('producer changed during run')
obj={'schema':'native_artifact_provenance_v2','producer':str(selfp),'producer_sha256_before':pin['producer_sha256_before'],'producer_sha256_after':after,'inputs_before':pin['inputs_before'],'inputs_after':{p:sha(p) for p in pin['inputs_before']},'outputs':records,'note':'Only two closed native 5.0-second runs are packaged. PNG and MP4 files are byte-exact copies; no transformation or re-encoding was performed.'}
with (A/'provenance_v2.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'outputs':len(records),'provenance':str(A/'provenance_v2.json')}))
