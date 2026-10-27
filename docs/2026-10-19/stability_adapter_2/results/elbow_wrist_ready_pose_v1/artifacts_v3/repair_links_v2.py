#!/usr/bin/env python3
"""Create corrected-link README v3; preserves the consumed v2 source."""
import hashlib,json
from pathlib import Path
P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1')
A2=P/'artifacts_v2'; A3=P/'artifacts_v3'; V=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1')
SRC=A2/'README_v2.md'; OUT=A3/'README_v3.md'; PIN=A3/'preflight_pin_v2.json'
TARGETS={'preflight_pin_v2':A2/'preflight_pin_v2.json','provenance_v2':A2/'provenance_v2.json','index_v1':V/'INDEX_v1.md'}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
if not PIN.is_file():raise RuntimeError('preflight pin missing')
pin=json.loads(PIN.read_text()); selfp=Path(__file__).resolve()
if pin['producer_path']!=str(selfp) or pin['producer_sha256_before']!=sha(selfp):raise RuntimeError('producer pre-pin mismatch')
for path,h in pin['inputs_before'].items():
 if sha(path)!=h:raise RuntimeError('pinned input changed: '+path)
for path in TARGETS.values():
 if not path.is_absolute() or not path.is_file():raise RuntimeError('expected absolute link target missing: '+str(path))
source=SRC.read_text(encoding='utf-8')
fixes={f'[{{A}}/preflight_pin_v2.json]({{A}}/preflight_pin_v2.json)':f'[{A2}/preflight_pin_v2.json]({A2}/preflight_pin_v2.json)',f'[{{A}}/provenance_v2.json]({{A}}/provenance_v2.json)':f'[{A2}/provenance_v2.json]({A2}/provenance_v2.json)',f'[{{V}}/INDEX_v1.md]({{V}}/INDEX_v1.md)':f'[{V}/INDEX_v1.md]({V}/INDEX_v1.md)'}
fixed=source
for old,new in fixes.items():
 if fixed.count(old)!=1:raise RuntimeError('broken source link count mismatch: '+old)
 fixed=fixed.replace(old,new)
if '{A}' in fixed or '{V}' in fixed:raise RuntimeError('unresolved path token remains')
with OUT.open('x',encoding='utf-8') as f:f.write(fixed)
if OUT.read_text(encoding='utf-8')!=fixed:raise RuntimeError('output readback mismatch')
for path,h in pin['inputs_before'].items():
 if sha(path)!=h:raise RuntimeError('pinned input changed during repair: '+path)
after=sha(selfp)
if after!=pin['producer_sha256_before']:raise RuntimeError('producer changed during execution')
obj={'schema':'artifact_link_repair_provenance_v1','producer':str(selfp),'producer_sha256_before':pin['producer_sha256_before'],'producer_sha256_after':after,'inputs_before':pin['inputs_before'],'inputs_after':{p:sha(p) for p in pin['inputs_before']},'targets_checked':{k:{'path':str(v),'exists':v.is_file(),'sha256':sha(v)} for k,v in TARGETS.items()},'output':{'path':str(OUT),'sha256':sha(OUT),'size_bytes':OUT.stat().st_size},'repair_note':'README_v2.md remains unchanged; README_v3.md replaces only three literal link labels/targets with absolute paths.'}
with (A3/'provenance_v2.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'output':str(OUT),'sha256':sha(OUT),'targets':len(TARGETS)}))
