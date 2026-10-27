#!/usr/bin/env python3
"""Byte-exact archive of the accepted current neck-support baseline."""
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1')
A=ROOT/'artifacts_v1'; PIN=A/'preflight_pin_v1.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def ffprobe(path):
 r=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(path)],check=True,capture_output=True,text=True)
 s=json.loads(r.stdout).get('streams',[])
 if len(s)!=1:raise RuntimeError('expected one video stream')
 return s[0]
if not PIN.is_file():raise RuntimeError('preflight pin missing')
pin=json.loads(PIN.read_text());selfp=Path(__file__).resolve()
if pin['producer_path']!=str(selfp) or pin['producer_sha256_before']!=sha(selfp):raise RuntimeError('producer pin mismatch')
for src,h in pin['inputs_before'].items():
 if sha(src)!=h:raise RuntimeError('source changed since preflight: '+src)
# Ensure all expected sources exist and copy only into new archive paths.
records=[]
for item in pin['copy_map']:
 src=Path(item['source']);dst=ROOT/item['destination'];dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as out,src.open('rb') as inp:shutil.copyfileobj(inp,out)
 src_sha=pin['inputs_before'][str(src)]
 if sha(src)!=src_sha or sha(dst)!=src_sha or dst.stat().st_size!=src.stat().st_size:raise RuntimeError('byte copy verification failed: '+str(dst))
 rec={'source':str(src),'destination':str(dst),'source_sha256':src_sha,'output_sha256':sha(dst),'size_bytes':dst.stat().st_size,'kind':item['kind']}
 if item['kind']=='video':
  a=ffprobe(src);b=ffprobe(dst)
  if a!=b:raise RuntimeError('ffprobe source/destination differ')
  if (a.get('width'),a.get('height'),a.get('avg_frame_rate'),a.get('nb_read_frames'),a.get('duration'))!=(1280,720,'30/1','151','5.033333'):raise RuntimeError('unexpected full-run video stream')
  rec['ffprobe']=b
 if item['kind']=='native_frame':
  cap=json.loads(Path(item['capture']).read_text())
  frame=next(x for x in cap['frames'] if x.get('physics_step')==0)
  expected=frame['image_sha256'].get(str(src))
  if expected!=src_sha:raise RuntimeError('native frame capture SHA mismatch')
 records.append(rec)
for src,h in pin['inputs_before'].items():
 if sha(src)!=h:raise RuntimeError('source changed during archive: '+src)
after=sha(selfp)
if after!=pin['producer_sha256_before']:raise RuntimeError('producer changed during run')
obj={'schema':'baseline_archive_provenance_v1','producer':str(selfp),'producer_sha256_before':pin['producer_sha256_before'],'producer_sha256_after':after,'inputs_before':pin['inputs_before'],'inputs_after':{src:sha(src) for src in pin['inputs_before']},'outputs':records,'note':'All archived artifacts are byte-exact copies. Model/assets remain shared external references; this is an initial-state and evidence archive, not a self-contained model bundle.'}
with (A/'provenance_v1.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'copied':len(records),'provenance':str(A/'provenance_v1.json')}))
