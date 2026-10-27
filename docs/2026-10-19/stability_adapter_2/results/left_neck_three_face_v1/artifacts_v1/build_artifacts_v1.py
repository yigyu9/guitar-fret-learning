#!/usr/bin/env python3
"""Byte-exact packaging of approved left-neck three-face native artifacts."""
import hashlib,json,shutil,subprocess
from pathlib import Path
P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1')
A=P/'artifacts_v1'; V=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_three_face_v1')
N=P/'native_off_v1'; PIN=A/'preflight_pin_v1.json'

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def probe(p):
 r=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(p)],check=True,capture_output=True,text=True)
 streams=json.loads(r.stdout).get('streams',[])
 if len(streams)!=1:raise RuntimeError('expected one video stream: '+str(p))
 return streams[0]
if not PIN.is_file():raise RuntimeError('preflight pin missing')
pin=json.loads(PIN.read_text()); selfp=Path(__file__).resolve()
if pin['producer_path']!=str(selfp) or pin['producer_sha256_before']!=sha(selfp):raise RuntimeError('producer pin mismatch')
for path,h in pin['inputs_before'].items():
 if sha(path)!=h:raise RuntimeError('input SHA mismatch before copy: '+path)
report=json.loads((N/'report.json').read_text()); cap=json.loads((N/'media/capture.json').read_text())
if not report.get('completed') or report.get('physics_steps')!=1200 or report.get('control_steps')!=300 or report.get('physics_seconds')!=5.0:raise RuntimeError('native run not complete 5s')
frames={int(f['physics_step']):f for f in cap['frames']}
for step,t in ((0,0.0),(480,2.0),(1200,5.0)):
 if step not in frames or frames[step]['time_s']!=t:raise RuntimeError('native capture mapping mismatch')
records=[]
for view in ('whole_body','hands','thumb_back'):
 src=N/'media'/f'{view}.mp4'; expected=report['videos'][view]['sha256']
 if sha(src)!=expected:raise RuntimeError('report MP4 sha mismatch')
 stream=probe(src)
 if (stream.get('width'),stream.get('height'),stream.get('avg_frame_rate'),stream.get('nb_read_frames'),stream.get('duration'))!=(1280,720,'30/1','151','5.033333'):raise RuntimeError('unexpected MP4 metadata')
 dst=V/f'native_off_v1_{view}.mp4'
 with dst.open('xb') as out,src.open('rb') as inp:shutil.copyfileobj(inp,out)
 if sha(dst)!=expected or dst.stat().st_size!=src.stat().st_size or probe(dst)!=stream:raise RuntimeError('MP4 copy verification failed')
 records.append({'kind':'video','view':view,'source':str(src),'destination':str(dst),'sha256':expected,'size_bytes':dst.stat().st_size,'ffprobe':stream})
selections=[(0,'whole_body'),(0,'hands'),(0,'thumb_back'),(480,'thumb_back'),(1200,'thumb_back')]
for step,view in selections:
 f=frames[step]; src=Path(next(p for p in f['image_sha256'] if f'/frames/{view}/' in p)); expected=f['image_sha256'][str(src)]
 if sha(src)!=expected:raise RuntimeError('capture frame SHA mismatch: '+str(src))
 t=int(f['time_s']); dst=A/f'native_off_t{t:02d}_{view}.png'
 with dst.open('xb') as out,src.open('rb') as inp:shutil.copyfileobj(inp,out)
 if sha(dst)!=expected or dst.stat().st_size!=src.stat().st_size:raise RuntimeError('PNG copy verification failed')
 records.append({'kind':'frame','physics_step':step,'time_s':t,'view':view,'source':str(src),'destination':str(dst),'sha256':expected,'size_bytes':dst.stat().st_size})
for path,h in pin['inputs_before'].items():
 if sha(path)!=h:raise RuntimeError('input changed during package: '+path)
after=sha(selfp)
if after!=pin['producer_sha256_before']:raise RuntimeError('producer changed during execution')
obj={'schema':'native_artifact_provenance_v1','producer':str(selfp),'producer_sha256_before':pin['producer_sha256_before'],'producer_sha256_after':after,'inputs_before':pin['inputs_before'],'inputs_after':{p:sha(p) for p in pin['inputs_before']},'outputs':records,'note':'All media are byte-exact copies of the single closed native_off_v1 run. Physics time is 5.0 s; MP4 duration is 5.033333 s. No rendering or annotation was performed.'}
with (A/'provenance_v1.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'outputs':len(records),'provenance':str(A/'provenance_v1.json')}))
