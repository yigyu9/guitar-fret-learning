#!/usr/bin/env python3
"""Render comparison figures from sealed native v2 frames and traces; no simulation or video encoding."""
from pathlib import Path
import hashlib, json, os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/mpl_upper_arm_static_support')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageOps, ImageDraw, ImageFont

ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-12')
P=ROOT/'stability_adapter_2/results/upper_arm_static_support_v1'
RUN=P/'native_v2'
OUT=P/'artifacts_v1'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
FONT_SHA='48a28e97b34fc8e5b157657633670cd1b7de126cfc414da65ce9c3d5bc8be733'
LABELS=[('reference','기준'),('lean0_gap500_z-10','상완 0°'),('lean3_gap500_z-10','상완 3°'),('lean5_gap500_z-10','상완 5°')]
FONT_PROP=FontProperties(fname=str(FONT))

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def pin_inputs():
    verification=json.loads((P/'verification_v2.json').read_text())
    same=json.loads((P/'same_conditions_verification_v1.json').read_text())
    if not verification['passed'] or not same['passed']:
        raise RuntimeError('Root verification inputs are not passed')
    for path,expected in verification['input_sha256'].items():
        if sha(path)!=expected: raise RuntimeError(f'Verification input changed: {path}')
    for path,expected in same['input_sha256'].items():
        if sha(path)!=expected: raise RuntimeError(f'Same-condition input changed: {path}')
    if sha(FONT)!=FONT_SHA: raise RuntimeError('Pinned Nanum font changed')
    return verification,same

def frame_panel(view, outfile):
    labels=[label for label,_ in LABELS]
    times=[(0,0.0),(60,2.0),(150,5.0)]
    tile_w,tile_h=480,270
    header_h=58
    pad=16
    canvas=Image.new('RGB',(pad+(tile_w+pad)*3,pad+(tile_h+header_h+pad)*4),(248,249,251))
    draw=ImageDraw.Draw(canvas)
    ftitle=ImageFont.truetype(str(FONT),24)
    fsmall=ImageFont.truetype(str(FONT),18)
    for ri,(label,korean) in enumerate(LABELS):
        for ci,(frame_idx,seconds) in enumerate(times):
            x=pad+ci*(tile_w+pad); y=pad+ri*(tile_h+header_h+pad)
            draw.text((x,y),f'{korean} · {seconds:g}초',font=ftitle,fill=(20,28,40))
            src=RUN/label/'media/frames'/view/f'{frame_idx:05d}.png'
            cap=json.loads((RUN/label/'media/capture.json').read_text())
            record=next(v for v in cap['frames'] if v['physics_step']==frame_idx*8)
            want=record['image_sha256'][str(src)]
            if sha(src)!=want: raise RuntimeError(f'Native frame SHA changed: {src}')
            image=Image.open(src).convert('RGB')
            image=ImageOps.fit(image,(tile_w,tile_h),method=Image.Resampling.LANCZOS)
            canvas.paste(image,(x,y+header_h))
            draw.rectangle((x,y+header_h,x+tile_w-1,y+header_h+tile_h-1),outline=(150,158,170),width=2)
    canvas.save(OUT/outfile,optimize=True)

def trajectory_panel(outfile):
    fig,axes=plt.subplots(2,2,figsize=(15,9))
    colors=['#333333','#1f77b4','#e07b18','#2b8a4b']
    traces={}
    for (label,korean),color in zip(LABELS,colors):
        rows=json.loads((RUN/label/'trace.json').read_text())
        t=[r['time_s'] for r in rows]
        pos=[r['position_change_m']*1000 for r in rows]
        rot=[r['rotation_change_deg'] for r in rows]
        axes[0,0].plot(t,pos,label=korean,color=color,lw=1.7)
        axes[0,1].plot(t,rot,label=korean,color=color,lw=1.7)
    axes[0,0].set(title='Actor-root 위치 변화 · 전체 0–5초',xlabel='물리 시간 (초)',ylabel='초기 위치 대비 거리 (mm)')
    axes[0,1].set(title='Actor-root 회전 변화 · 전체 0–5초',xlabel='물리 시간 (초)',ylabel='초기 orientation 대비 SO(3) (°)')
    axes[1,0].set(title='위치 변화 · 2–5초 확대',xlabel='물리 시간 (초)',ylabel='2초 상태 대비 거리 (mm)')
    axes[1,1].set(title='회전 변화 · 2–5초 확대',xlabel='물리 시간 (초)',ylabel='2초 orientation 대비 SO(3) (°)')
    # The lower panels show the true trace relative to each case's measured 2s state.
    for (label,_),color in zip(LABELS,colors):
        rows=json.loads((RUN/label/'trace.json').read_text())
        r2=next(r for r in rows if r['time_s']==2.0)
        import numpy as np
        from scipy.spatial.transform import Rotation
        p2=np.array(r2['position_W_m']); q2=Rotation.from_quat(r2['quaternion_xyzw'])
        late=[r for r in rows if r['time_s']>=2.0]
        axes[1,0].plot([r['time_s'] for r in late],[float(np.linalg.norm(np.array(r['position_W_m'])-p2)*1000) for r in late],label=dict(LABELS)[label],color=color,lw=1.7)
        axes[1,1].plot([r['time_s'] for r in late],[float(np.rad2deg((q2.inv()*Rotation.from_quat(r['quaternion_xyzw'])).magnitude())) for r in late],label=dict(LABELS)[label],color=color,lw=1.7)
    axes[1,0].set_ylabel('2초 상태 대비 위치 (mm)')
    axes[1,1].set_ylabel('2초 orientation 대비 SO(3) (°)')
    for ax in axes.flat:
        ax.grid(True,alpha=.25)
        ax.tick_params(labelsize=9)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.94),ncol=4,prop=FONT_PROP,frameon=False)
    for ax in axes.flat:
        ax.title.set_fontproperties(FONT_PROP)
        ax.xaxis.label.set_fontproperties(FONT_PROP)
        ax.yaxis.label.set_fontproperties(FONT_PROP)
        for tick in ax.get_xticklabels()+ax.get_yticklabels(): tick.set_fontproperties(FONT_PROP)
    fig.suptitle('상완 정적 지지 조건 · native q_ref, PD-only, 5초',fontproperties=FONT_PROP,fontsize=17,y=.99)
    fig.tight_layout(rect=(0,.02,1,.89))
    fig.savefig(OUT/outfile,dpi=150,bbox_inches='tight')
    plt.close(fig)

def main():
    pin_inputs()
    frame_panel('whole_body','native_whole_body_frames_v1.png')
    frame_panel('hands','native_hands_frames_v1.png')
    trajectory_panel('root_motion_traces_v1.png')
    print('Rendered 3 figures from pinned native frames/traces; no physics, render API or video encoding executed.')

if __name__=='__main__': main()
