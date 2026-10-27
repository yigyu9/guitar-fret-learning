#!/usr/bin/env python3
"""Create final-artifact visuals from root-verified Q/P native evaluations."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from PIL import Image

ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1'
Q=ROOT/'docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1'
OUT=Q/'artifacts_v1'
VERIFY=Q/'runtime_verification_v2.json'
COMPARE=Q/'initial_comparison_v1.json'
RUNS={
 'P 초기 (0 update)': P/'smoke_on_v1/evaluations/initial_000000/native/episode_0001',
 'Q 초기 (0 update)': Q/'smoke_on_v2/evaluations/initial_000000/native/episode_0001',
 'Q CP1 (1 update)': Q/'smoke_on_v2/evaluations/update_000001/native/episode_0001',
}
COLORS=['#415A77','#E07A5F','#2A9D8F']
FRAMES=[0,60,491]
CAPTIONS=['0초 · frame 0','2초 · frame 60','16.3667초 · frame 491']

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
 return h.hexdigest()

def entry(path): return {'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size}
def frames_dir(ep,view): return ep/'media/frames'/view

def render_frames(view,path,title):
 fig,axes=plt.subplots(3,3,figsize=(15,10),constrained_layout=True)
 fig.suptitle(title,fontsize=17,fontweight='bold')
 for r,(label,ep) in enumerate(RUNS.items()):
  for c,(fid,caption) in enumerate(zip(FRAMES,CAPTIONS)):
   with Image.open(frames_dir(ep,view)/f'{fid:05d}.png') as im: axes[r,c].imshow(im.convert('RGB'))
   axes[r,c].set_xticks([]);axes[r,c].set_yticks([])
   if r==0: axes[r,c].set_title(caption,fontsize=11)
   if c==0: axes[r,c].set_ylabel(label,fontsize=11)
   for spine in axes[r,c].spines.values(): spine.set_visible(False)
 fig.savefig(path,dpi=145,facecolor='white');plt.close(fig)

def main():
 verify=json.loads(VERIFY.read_text()); compare=json.loads(COMPARE.read_text())
 if not verify['checks_passed']: raise RuntimeError('root runtime verification is not all-pass')
 if not compare['inputs_unchanged'] or not compare['native_initial_state_equal']: raise RuntimeError('initial comparison invariants missing')
 e0=compare['evaluations']['before'];e1=compare['evaluations']['support_guard']; e2=verify['evaluations']['update_000001']
 metrics={
  'P 초기 (0 update)':{'outside_percent':e0['outside_percent'],'max_norm_m':e0['max_position_outside_norm_m'],'music':e0['joint_success_events'],'crossings':e0['accepted_crossings'],'seconds':e0['physics_seconds'],'frames':492},
  'Q 초기 (0 update)':{'outside_percent':e1['outside_percent'],'max_norm_m':e1['max_position_outside_norm_m'],'music':e1['joint_success_events'],'crossings':e1['accepted_crossings'],'seconds':e1['physics_seconds'],'frames':492},
  'Q CP1 (1 update)':{'outside_percent':e2['outside_percent'],'max_norm_m':e2['max_position_outside_norm_m'],'music':e2['joint_success_events'],'crossings':e2['accepted_crossings'],'seconds':e2['physics_seconds'],'frames':e2['frames']},
 }
 inputs={}
 for mapping in (compare.get('input_sha256',{}),verify.get('input_sha256',{})):
  for name,expected in mapping.items():
   p=Path(name)
   if not p.exists(): raise FileNotFoundError(p)
   actual=sha(p)
   if actual!=expected: raise RuntimeError(f'root hash mismatch: {p}')
   inputs[p]=expected
 explicit=[VERIFY,COMPARE,Q/'verify_runtime_v2.py',Q/'source_before_native_v2/manifest.json',
           Q/'source_before_native_v2/deadline_support_nominal_v1.py',
           Q/'source_before_native_v2/run_deadline_training_v8.py',
           Q/'smoke_on_v2/training.jsonl',Q/'smoke_on_v2/report.json',Q/'smoke_on_v2/attempt.json',
           P/'runtime_verification_v2.json']
 for p in explicit:
  if p.exists(): inputs[p]=sha(p)
 frame_inputs=[]
 for ep in RUNS.values():
  for view in ('whole_body','hands'):
   for fid in FRAMES:
    p=frames_dir(ep,view)/f'{fid:05d}.png'
    if not p.exists(): raise FileNotFoundError(p)
    frame_inputs.append(p);inputs[p]=sha(p)
 # Controls are the raw observations used in the outside-over-time plot.
 for ep in RUNS.values():
  p=ep/'controls.json'; inputs[p]=sha(p)
 before=[entry(p) for p in sorted(inputs,key=str)]
 font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
 font_manager.fontManager.addfont(font)
 plt.rcParams['font.family']=font_manager.FontProperties(fname=font).get_name()
 plt.rcParams['axes.unicode_minus']=False
 whole=OUT/'qp_final_whole_body_frames_v1.png';hands=OUT/'qp_final_hands_frames_v1.png';outside=OUT/'qp_final_outside_over_time_v1.png'
 render_frames('whole_body',whole,'P 초기 · Q 초기 · Q CP1 native 전신 비교')
 render_frames('hands',hands,'P 초기 · Q 초기 · Q CP1 native 손 비교')
 fig,ax=plt.subplots(figsize=(9.5,5.3),constrained_layout=False)
 for color,(label,ep) in zip(COLORS,RUNS.items()):
  rows=json.loads((ep/'controls.json').read_text())
  t=np.asarray([r['physics_step']/240.0 for r in rows],float)
  v=np.asarray([r['position_outside_m'] for r in rows],float)
  norm=np.linalg.norm(v,axis=1);m=metrics[label]
  ax.plot(t,norm,color=color,lw=2,label=f"{label} · 범위 밖 {m['outside_percent']:.2f}% · 최대 {m['max_norm_m']:.3f} m")
 ax.set_xlim(0,16.3667);ax.set_xlabel('물리 경과 시간 (초)');ax.set_ylabel('위치 허용범위 밖 거리 벡터 크기 (m)')
 ax.set_title('P 초기 · Q 초기 · Q CP1 위치 범위 이탈')
 ax.grid(alpha=.25);ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),borderaxespad=0)
 fig.subplots_adjust(left=.12,right=.69,bottom=.14,top=.88);fig.savefig(outside,dpi=170,facecolor='white',bbox_inches='tight');plt.close(fig)
 after=[entry(p) for p in sorted(inputs,key=str)]
 if before!=after: raise RuntimeError('source input changed during rendering')
 outputs=[entry(p) for p in (whole,hands,outside)]
 prov={
  'purpose':'Q v2 verified one-update comparison with P/Q initial; final artifact source record',
  'producer':entry(Path(__file__).resolve()),'root_helper':entry(Q/'verify_runtime_v2.py'),
  'root_runtime_verification':entry(VERIFY),'root_initial_comparison':entry(COMPARE),
  'inputs_before':before,'inputs_after':after,'inputs_unchanged_during_render':True,
  'outputs':outputs,'metrics':metrics,
  'training':{'exit_code':0,'updates':1,'transitions':256,'optimizer_steps':6,'final_kl':0.01992567256,'rms_frozen':True},
  'long_on_v1':'별도 장기 실험은 root 안내상 진행 중이며 이 비교에서는 완료·성공을 주장하지 않음',
  'interpretation':'nominal 초기조건과 단일 update 효과를 구분해야 함. CP1 outside 비율은 감소했지만 최대 outside norm은 0.3382m에서 0.4731m로 악화. 모든 평가 music 0, crossings 0; 안정성 성공 아님.'}
 (OUT/'qp_final_comparison_provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'input_files':len(before),'producer_sha256':prov['producer']['sha256'],'metrics':metrics,'outputs':outputs},ensure_ascii=False))
if __name__=='__main__': main()
