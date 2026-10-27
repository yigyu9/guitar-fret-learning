#!/usr/bin/env python3
"""Corrected byte-exact archive producer; outputs only into fresh v2 paths."""
import hashlib,json,shutil,subprocess
from pathlib import Path
BASE=Path('/home/ajou/yigyu/3/docs/2026-10-19')
I=BASE/'initial/right_shift10_comparison_v1'; P=BASE/'stability_adapter_2/results/right_shift_initial_v1'; A=P/'artifacts_v1'; V=BASE/'stability_adapter_2/video/right_shift_initial_v1'; N=P/'native_right10_v1'; PIN=A/'preflight_pin_v2.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def probe(p):
 r=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(p)],check=True,capture_output=True,text=True)
 s=json.loads(r.stdout).get('streams',[])
 if len(s)!=1:raise RuntimeError('expected one video stream')
 return s[0]
if not PIN.is_file():raise RuntimeError('preflight pin missing')
pin=json.loads(PIN.read_text());selfp=Path(__file__).resolve()
if pin['producer_path']!=str(selfp) or pin['producer_sha256_before']!=sha(selfp):raise RuntimeError('producer pin mismatch')
for src,h in pin['inputs_before'].items():
 if sha(src)!=h:raise RuntimeError('pinned input changed: '+src)
report=json.loads((N/'report.json').read_text());capture=json.loads((N/'media/capture.json').read_text())
if not report.get('completed') or report.get('physics_steps')!=1200 or report.get('control_steps')!=300 or report.get('physics_seconds')!=5.0:raise RuntimeError('native run not complete 5s')
frames={int(f['physics_step']):f for f in capture['frames']}
for step,t in ((0,0.0),(1200,5.0)):
 if step not in frames or frames[step]['time_s']!=t:raise RuntimeError('frame/time mapping mismatch')
face=json.loads((P/'face_audit_v1.json').read_text());strike=json.loads((P/'strike_analysis_v1.json').read_text())['cases']['native_right10_v1']
if face.get('after2s_all6_pass_fraction')!=0.0 or not face.get('initial_three_faces_pass'):raise RuntimeError('three-face audit mismatch')
if not strike.get('six_string_down_pass') or not strike.get('six_string_up_pass'):raise RuntimeError('virtual-pick audit mismatch')
base_img=Path(pin['baseline_image_path']);base_prov=json.loads(Path(pin['baseline_provenance_path']).read_text())
if not any(o.get('destination')==str(base_img) and o.get('output_sha256')==sha(base_img) for o in base_prov.get('outputs',[])):raise RuntimeError('baseline image not attested by preserved archive')
records=[]
def copy(src,dst,kind,capture_path=None,capture_step=None):
 src=Path(src);dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True);expected=pin['inputs_before'][str(src)]
 with dst.open('xb') as out,src.open('rb') as inp:shutil.copyfileobj(inp,out)
 if sha(src)!=expected or sha(dst)!=expected or dst.stat().st_size!=src.stat().st_size:raise RuntimeError('byte-copy failure: '+str(dst))
 rec={'kind':kind,'source':str(src),'destination':str(dst),'source_sha256':expected,'output_sha256':sha(dst),'size_bytes':dst.stat().st_size}
 if kind=='native_frame':
  c=json.loads(Path(capture_path).read_text());f=next(x for x in c['frames'] if x.get('physics_step')==capture_step)
  if f['image_sha256'].get(str(src))!=expected:raise RuntimeError('capture SHA mismatch at requested step: '+str(src))
 if kind=='video':
  a=probe(src);b=probe(dst)
  if a!=b or (a.get('width'),a.get('height'),a.get('avg_frame_rate'),a.get('nb_read_frames'),a.get('duration'))!=(1280,720,'30/1','151','5.033333'):raise RuntimeError('video metadata mismatch: '+str(dst))
  rec['ffprobe']=b
 records.append(rec)
for item in pin['copy_map']:
 rel=item['destination']
 if rel.startswith('archive_v2/'):dst=I/rel
 elif rel.startswith('artifacts_v1/v2/'):dst=P/rel
 elif rel.startswith('video_v2/'):dst=V/rel
 else:raise RuntimeError('unexpected v2 output root: '+rel)
 copy(item['source'],dst,item['kind'],item.get('capture'),item.get('capture_step'))
for src,h in pin['inputs_before'].items():
 if sha(src)!=h:raise RuntimeError('source changed during archive: '+src)
after=sha(selfp)
if after!=pin['producer_sha256_before']:raise RuntimeError('producer changed during execution')
obj={'schema':'right_shift_archive_provenance_v2','producer':str(selfp),'producer_sha256_before':pin['producer_sha256_before'],'producer_sha256_after':after,'inputs_before':pin['inputs_before'],'inputs_after':{src:sha(src) for src in pin['inputs_before']},'outputs':records,'note':'v2 outputs are byte-exact copies in new paths. Prior partial v1 paths were preserved and are not the delivered archive.'}
with (A/'provenance_v2.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'outputs':len(records),'provenance':str(A/'provenance_v2.json')}))
