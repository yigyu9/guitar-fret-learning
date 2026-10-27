#!/usr/bin/env python3
"""Create FILES_v2 with binary links free of false line numbers."""
import hashlib,json,re
from pathlib import Path
A=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1')
SRC=A/'FILES_v1.md'; OUT=A/'FILES_v2.md'; PIN=A/'correction_pin_v1.json'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
if not PIN.is_file():raise RuntimeError('correction pin missing')
pin=json.loads(PIN.read_text());selfp=Path(__file__).resolve()
if pin['producer_path']!=str(selfp) or pin['producer_sha256_before']!=sha(selfp):raise RuntimeError('producer pre-pin mismatch')
for path,h in pin['inputs_before'].items():
 if sha(path)!=h:raise RuntimeError('pinned input changed: '+path)
source=SRC.read_text(encoding='utf-8')
lines=source.splitlines(); edits=[];out=[]
link=re.compile(r'\]\((/[^)]+)\)')
for line in lines:
 def fix(m):
  target=m.group(1)
  if target.endswith(('.png:1','.mp4:1')):
   new=target[:-2]
   edits.append({'from':target,'to':new})
   return ']('+new+')'
  return m.group(0)
 out.append(link.sub(fix,line))
if len(edits)!=8:raise RuntimeError(f'expected 8 binary line-number fixes, found {len(edits)}')
fixed='\n'.join(out)+'\n'
if '{A}' in fixed or '{V}' in fixed:raise RuntimeError('template token found')
# Validate every local link: binary links have no line suffix; text links use real line 1.
checked=[]
for m in link.finditer(fixed.replace('](','](')):
 target=m.group(1)
 if target.endswith(('.png','.mp4')):
  p=Path(target)
  if not p.is_absolute() or not p.is_file():raise RuntimeError('bad binary link '+target)
  checked.append({'path':target,'kind':'binary','line_number':None})
 else:
  mm=re.fullmatch(r'(.+):(\d+)',target)
  if not mm:raise RuntimeError('text link lacks line number '+target)
  p=Path(mm.group(1));n=int(mm.group(2))
  if not p.is_absolute() or not p.is_file() or n<1 or n>len(p.read_text(encoding='utf-8').splitlines()):raise RuntimeError('invalid text link line '+target)
  checked.append({'path':str(p),'kind':'text','line_number':n})
with OUT.open('x',encoding='utf-8') as f:f.write(fixed)
if OUT.read_text(encoding='utf-8')!=fixed:raise RuntimeError('output readback mismatch')
for path,h in pin['inputs_before'].items():
 if sha(path)!=h:raise RuntimeError('input changed during correction: '+path)
after=sha(selfp)
if after!=pin['producer_sha256_before']:raise RuntimeError('producer changed during execution')
obj={'schema':'binary_link_line_correction_v1','producer':str(selfp),'producer_sha256_before':pin['producer_sha256_before'],'producer_sha256_after':after,'inputs_before':pin['inputs_before'],'inputs_after':{p:sha(p) for p in pin['inputs_before']},'output':{'path':str(OUT),'sha256':sha(OUT),'size_bytes':OUT.stat().st_size},'binary_link_edits':edits,'links_checked':checked,'note':'FILES_v1.md is preserved. FILES_v2.md removes :1 only from eight PNG/MP4 links; text link line references are retained and range-checked.'}
with (A/'correction_provenance_v1.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'binary_fixes':len(edits),'links_checked':len(checked),'output_sha256':sha(OUT)}))
