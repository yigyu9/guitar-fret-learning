#!/usr/bin/env python3
"""기존 native 이미지·영상을 읽고 비교물/보관본을 만든다. 물리 재실행은 없다."""
from pathlib import Path
import hashlib,json,shutil,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1'
OLD=ROOT/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/native_realistic_v2'
A=P/'artifacts_v1'; V=ROOT/'docs/2026-10-12/video/acoustic_guitar_appearance_v1'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def font(n):return ImageFont.truetype(str(FONT),n)
inputs={}
def pin(p,expected=None):
 p=Path(p); h=sha(p)
 if expected is not None: assert h==expected,(str(p),h,expected)
 inputs[str(p)]=h
 return p

build=read(pin(P/'build_v3.json'))
assert all(build['checks'].values())
for q,h in build['input_sha256'].items():
 path=Path(q) if Path(q).is_absolute() else ROOT/q
 pin(path,h)
# pin relevant native evidence and reports before consuming frame/video files
reports={}
for v in ['native_v2','native_v3']:
 reports[v]=read(pin(P/v/'report.json'))
 assert reports[v]['completed'] and reports[v]['physics_steps']==1200 and reports[v]['controls']==300
 assert reports[v]['physics_seconds']==5.0
 pin(P/v/'inputs_verified.json')
 pin(P/v/'initial_values.json')
 pin(P/v/'collision_comparison.json')
 pin(P/v/'media/raw/capture.json')
 pin(P/v/'media/capture.json')
 pin(P/v/'media/videos.json')
for q in [P/'native_exit_v1.json',P/'native_exit_v2.json',P/'native_v1.log']:
 if q.is_file(): pin(q)
# Native t0 render frame from prior run and current appearance-detail image.
oldcap=read(pin(OLD/'media/raw/capture.json'))
oldrow=oldcap['frames'][0]; oldframe=Path(next(k for k in oldrow['image_sha256'] if '/whole_body/' in k)); pin(oldframe,oldrow['image_sha256'][str(oldframe)])
newcap=read(P/'native_v3/media/raw/capture.json'); newrow=newcap['frames'][0]
newframe=Path(next(k for k in newrow['image_sha256'] if '/whole_body/' in k)); pin(newframe,newrow['image_sha256'][str(newframe)])
detail=pin(P/'native_v3/initial_guitar_appearance.png')

# Side-by-side, equal-size native raw frames from the same camera setup.
assert Image.open(oldframe).size==Image.open(newframe).size
ims=[Image.open(q).convert('RGB') for q in [oldframe,newframe]]
w,h=ims[0].size
panel=Image.new('RGB',(2*w+80,h+105),'white'); d=ImageDraw.Draw(panel)
d.text((25,18),'기존 realistic guitar',font=font(26),fill='#17212b'); d.text((w+55,18),'새 acoustic appearance',font=font(26),fill='#17212b')
panel.paste(ims[0],(25,65)); panel.paste(ims[1],(w+55,65)); panel.save(A/'native_t0_appearance_comparison.png')

# Caption card around the native rendered guitar close-up; source picture pixels are preserved.
im=Image.open(detail).convert('RGB'); out=Image.new('RGB',(im.width,im.height+105),'white'); d=ImageDraw.Draw(out)
d.text((24,17),'native_v3 기타 외관 상세 — Isaac Gym native render (AI 생성 이미지 아님)',font=font(25),fill='#17212b')
out.paste(im,(0,85)); out.save(A/'native_v3_appearance_detail.png')

# Copy only the four already-completed MP4s byte-for-byte.
records=[]
for version in ['native_v2','native_v3']:
 for kind,filename in [('전신','whole_body.mp4'),('손','hands.mp4')]:
  src=P/version/'media'/filename; dst=V/f'{version}_{filename}'
  expected=reports[version]['videos'][filename.removesuffix('.mp4')]['sha256'] if isinstance(reports[version].get('videos'),dict) else None
  src_hash=sha(src)
  if expected: assert src_hash==expected
  if dst.exists(): assert sha(dst)==src_hash
  else: shutil.copyfile(src,dst)
  copy_hash=sha(dst); assert src_hash==copy_hash
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(dst)],text=True))['streams'][0]
  assert probe['avg_frame_rate']=='30/1' and probe['nb_read_frames']=='151'
  records.append({'native_run':version,'view':kind,'source':str(src),'destination':str(dst),'bytes':dst.stat().st_size,'source_sha256':src_hash,'copy_sha256':copy_hash,'ffprobe':probe})

manifest={'schema':'acoustic-appearance-video-manifest-v1','video_count':len(records),'videos':records}
(V/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

# Documentation is created before producer runs so its hash is also pinned in the final provenance.
outputs={str(q):sha(q) for q in sorted(A.glob('*.png'))}
for q in [A/'README.md',A/'CHANGED_FILES.md',V/'README.md',V/'manifest.json']:
 if q.exists(): outputs[str(q)]=sha(q)
prov={'schema':'acoustic-appearance-artifacts-provenance-v1','inputs_sha256_before_after':{q:{'before':h,'after':sha(q)} for q,h in inputs.items()},'font':{'path':str(FONT),'sha256':sha(FONT)},'videos':records,'native_scope':{v:{'completed':reports[v]['completed'],'physics_steps':reports[v]['physics_steps'],'controls':reports[v]['controls'],'physics_seconds':reports[v]['physics_seconds'],'music_actors':reports[v]['music_actors'],'policy_calls':reports[v]['policy_calls'],'forbidden_calls':reports[v]['forbidden_calls']} for v in reports},'outputs_sha256':outputs,'producer_sha256':sha(Path(__file__))}
(A/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'video_count':len(records),'video_bytes':sum(x['bytes'] for x in records),'producer_sha256':prov['producer_sha256'],'outputs_sha256':outputs},ensure_ascii=False,indent=2))
