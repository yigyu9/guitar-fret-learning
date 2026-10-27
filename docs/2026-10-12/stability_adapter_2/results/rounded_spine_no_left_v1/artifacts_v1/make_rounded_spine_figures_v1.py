#!/usr/bin/env python3
"""Create native-frame panels and root-motion plots from sealed v2 data only."""
from pathlib import Path
import hashlib, json, os
os.environ.setdefault('MPLCONFIGDIR','/tmp/mpl_rounded_spine_no_left')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageOps, ImageDraw, ImageFont

ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-12')
P=ROOT/'stability_adapter_2/results/rounded_spine_no_left_v1'
RUN=P/'native_v2'; OUT=P/'artifacts_v1'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
FONT_SHA='48a28e97b34fc8e5b157657633670cd1b7de126cfc414da65ce9c3d5bc8be733'
CASES=[('rounded3_left_away','분산 전경 3° · 왼손 철수'),('rounded9_left_support','분산 전경 9° · 왼손 지지'),('rounded9_left_away','분산 전경 9° · 왼손 철수'),('rounded12_left_away','분산 전경 12° · 왼손 철수')]
FONT_PROP=FontProperties(fname=str(FONT))

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def verify_sources():
 v=json.loads((P/'verification_v1.json').read_text());s=json.loads((P/'search_v2/selected.json').read_text())
 if not v['passed'] or len(v['checks'])!=33:raise RuntimeError('Root native verification is not passed')
 for source,want in v['input_sha256'].items():
  if sha(source)!=want:raise RuntimeError(f'Verification source changed: {source}')
 for source,want in s['input_sha256'].items():
  if sha(source)!=want:raise RuntimeError(f'Selected source changed: {source}')
 if sha(FONT)!=FONT_SHA:raise RuntimeError('Pinned Nanum font changed')
 return v,s

def frames(view,outfile):
 steps=[(0,0.0),(480,2.0),(1200,5.0)]
 tw,th,hh,pad=480,270,58,16
 canvas=Image.new('RGB',(pad+(tw+pad)*3,pad+(th+hh+pad)*4),(248,249,251));draw=ImageDraw.Draw(canvas)
 fhead=ImageFont.truetype(str(FONT),24)
 for ri,(label,korean) in enumerate(CASES):
  for ci,(physics_step,seconds) in enumerate(steps):
   x=pad+ci*(tw+pad);y=pad+ri*(th+hh+pad)
   draw.text((x,y),f'{korean} · {seconds:g}초',font=fhead,fill=(20,28,40))
   source=RUN/label/'media/frames'/view/f'{physics_step//8:05d}.png'
   capture=json.loads((RUN/label/'media/capture.json').read_text())
   fr=next(f for f in capture['frames'] if f['physics_step']==physics_step)
   if sha(source)!=fr['image_sha256'][str(source)]:raise RuntimeError(f'Native source frame changed: {source}')
   im=ImageOps.fit(Image.open(source).convert('RGB'),(tw,th),method=Image.Resampling.LANCZOS)
   canvas.paste(im,(x,y+hh));draw.rectangle((x,y+hh,x+tw-1,y+hh+th-1),outline=(145,155,170),width=2)
 canvas.save(OUT/outfile,optimize=True)

def plot(out):
 from scipy.spatial.transform import Rotation
 import numpy as np
 fig,axes=plt.subplots(2,2,figsize=(15,9));colors=['#333333','#1878a8','#dc7617','#25844c']
 for (label,korean),color in zip(CASES,colors):
  rows=json.loads((RUN/label/'trace.json').read_text())
  t=[r['time_s'] for r in rows]
  p=[r['position_change_m']*1000 for r in rows]
  q=[r['rotation_change_deg'] for r in rows]
  axes[0,0].plot(t,p,label=korean,color=color,lw=1.7)
  axes[0,1].plot(t,q,label=korean,color=color,lw=1.7)
  start=next(r for r in rows if r['time_s']==2.0)
  p2=np.array(start['position_W_m']);q2=Rotation.from_quat(start['quaternion_xyzw'])
  late=[r for r in rows if r['time_s']>=2.0]
  axes[1,0].plot([r['time_s'] for r in late],[np.linalg.norm(np.array(r['position_W_m'])-p2)*1000 for r in late],color=color,lw=1.7)
  axes[1,1].plot([r['time_s'] for r in late],[np.rad2deg((q2.inv()*Rotation.from_quat(r['quaternion_xyzw'])).magnitude()) for r in late],color=color,lw=1.7)
 axes[0,0].set(title='Actor-root 위치 변화 · 전체 0–5초',xlabel='물리 시간 (초)',ylabel='초기 위치 대비 거리 (mm)')
 axes[0,1].set(title='Actor-root orientation 변화 · 전체 0–5초',xlabel='물리 시간 (초)',ylabel='초기 quaternion 대비 SO(3) (°)')
 axes[1,0].set(title='후기 위치 변화 · 2–5초',xlabel='물리 시간 (초)',ylabel='2초 위치 대비 거리 (mm)')
 axes[1,1].set(title='후기 orientation 변화 · 2–5초',xlabel='물리 시간 (초)',ylabel='2초 quaternion 대비 SO(3) (°)')
 for ax in axes.flat:
  ax.grid(True,alpha=.25)
  ax.title.set_fontproperties(FONT_PROP);ax.xaxis.label.set_fontproperties(FONT_PROP);ax.yaxis.label.set_fontproperties(FONT_PROP)
  for tick in ax.get_xticklabels()+ax.get_yticklabels():tick.set_fontproperties(FONT_PROP)
 handles,labels=axes[0,0].get_legend_handles_labels()
 fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.94),ncol=2,prop=FONT_PROP,frameon=False)
 fig.suptitle('분산 전경 및 왼손 초기 목표 조건 · 고정 q_ref PD native 5초',fontproperties=FONT_PROP,fontsize=17,y=.99)
 fig.tight_layout(rect=(0,.02,1,.89));fig.savefig(OUT/out,dpi=150,bbox_inches='tight');plt.close(fig)

def main():
 verify_sources();frames('whole_body','native_whole_body_frames_v1.png');frames('hands','native_hands_frames_v1.png');plot('root_motion_traces_v1.png')
 print('Created 3 figures from pinned native frames/traces; no simulation or video encoding run.')
if __name__=='__main__':main()
