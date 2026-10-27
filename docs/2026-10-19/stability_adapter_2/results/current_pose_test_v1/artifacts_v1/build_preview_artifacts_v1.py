#!/usr/bin/env python3
"""Byte-exact native-camera PNG preview packaging for current_pose_test_v1."""
import hashlib,json,shutil
from pathlib import Path
P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1')
A=P/'artifacts_v1'; N=P/'sessions/20261014_215819_009632/trial_000'; PIN=A/'preflight_pin_v1.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
if not PIN.is_file():raise RuntimeError('preflight pin missing')
pin=json.loads(PIN.read_text()); selfp=Path(__file__).resolve()
if pin['producer_path']!=str(selfp) or pin['producer_sha256_before']!=sha(selfp):raise RuntimeError('producer SHA pre-pin mismatch')
for p,h in pin['inputs_before'].items():
 if sha(p)!=h:raise RuntimeError('input SHA changed: '+p)
report=json.loads((N/'report.json').read_text());capture=json.loads((N/'media/capture.json').read_text())
if not report.get('completed') or report.get('physics_seconds')!=0.2 or report.get('physics_steps')!=48 or report.get('control_steps')!=12 or not report.get('inputs_unchanged') or report.get('forbidden_calls')!=[] or not report.get('initial_exact_to_reference'):
 raise RuntimeError('headless check report does not meet brief')
frame=next((f for f in capture['frames'] if f.get('physics_step')==0),None)
if frame is None or frame.get('time_s')!=0.0:raise RuntimeError('missing native t=0 frame')
records=[]
for view in ('whole_body','hands','thumb_back'):
 src=Path(next(p for p in frame['image_sha256'] if f'/frames/{view}/' in p)); expected=frame['image_sha256'][str(src)]
 if sha(src)!=expected:raise RuntimeError('capture frame SHA mismatch: '+str(src))
 dst=A/f'native_preview_t00_{view}.png'
 with dst.open('xb') as out,src.open('rb') as inp:shutil.copyfileobj(inp,out)
 if sha(dst)!=expected or dst.stat().st_size!=src.stat().st_size:raise RuntimeError('native image byte-copy check failed')
 records.append({'kind':'native_camera_preview','physics_step':0,'time_s':0.0,'view':view,'source':str(src),'destination':str(dst),'sha256':expected,'size_bytes':dst.stat().st_size})
for p,h in pin['inputs_before'].items():
 if sha(p)!=h:raise RuntimeError('input changed during package: '+p)
after=sha(selfp)
if after!=pin['producer_sha256_before']:raise RuntimeError('producer changed during execution')
obj={'schema':'native_camera_preview_provenance_v1','producer':str(selfp),'producer_sha256_before':pin['producer_sha256_before'],'producer_sha256_after':after,'inputs_before':pin['inputs_before'],'inputs_after':{p:sha(p) for p in pin['inputs_before']},'outputs':records,'note':'These are native Isaac Gym camera PNGs, not screenshots of the desktop viewer. GUI integration was not verified because DISPLAY was unavailable. The 0.2-second diagnostic MP4s were left at their original session paths and are not packaged here.'}
with (A/'provenance_v1.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'outputs':len(records),'provenance':str(A/'provenance_v1.json')}))
