#!/usr/bin/env python3
"""Render root-verified CP1/CP86 comparisons and stochastic training returns."""
from pathlib import Path
import hashlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from PIL import Image
from scipy.spatial.transform import Rotation
ROOT=Path('/home/ajou/yigyu/3')
R=ROOT/'docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1'
S=ROOT/'docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1'
V=ROOT/'docs/2026-10-12/video'
OUT=R/'artifacts_v1'; ANALYSIS=R/'analysis_v1.json'; REWARD=R/'reward_analysis_v1.json'
EVALS={
 'CP1 · update 000001': S/'smoke_on_v2/evaluations/update_000001/native/episode_0001',
 'CP86 · update 000086': S/'long_on_v1/evaluations/update_000086/native/episode_0001',
}
COLORS=['#E07A5F','#287271']; IDS=[0,60,390,491]
CAPTIONS=['0초','2초','13초','종료 · 16.3667초']
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def entry(p):p=Path(p);return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def frame(ep,view,i):return ep/'media/frames'/view/f'{i:05d}.png'
def plot_frames(view,target):
 fig,axes=plt.subplots(2,4,figsize=(17,7),constrained_layout=True)
 fig.suptitle(f'CP1 · CP86 native {"전신" if view=="whole_body" else "손"} frame 비교',fontsize=17,fontweight='bold')
 for row,(label,ep) in enumerate(EVALS.items()):
  for col,(i,caption) in enumerate(zip(IDS,CAPTIONS)):
   with Image.open(frame(ep,view,i)) as im:axes[row,col].imshow(im.convert('RGB'))
   axes[row,col].set_xticks([]);axes[row,col].set_yticks([])
   if row==0:axes[row,col].set_title(caption)
   if col==0:axes[row,col].set_ylabel(label)
   for sp in axes[row,col].spines.values():sp.set_visible(False)
 fig.savefig(target,dpi=145,facecolor='white');plt.close(fig)
def rot_curve(trace):
 q=np.asarray([r['quaternion_xyzw'] for r in trace],float)
 init=Rotation.from_quat(q[0]); rel=init.inv()*Rotation.from_quat(q)
 sec=np.asarray([r['physics_step']/240.0 for r in trace])
 return sec,np.rad2deg(rel.magnitude())
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 analysis=json.loads(ANALYSIS.read_text());reward=json.loads(REWARD.read_text())
 if not analysis['checks_passed'] or not analysis['checks'].get('analysis_inputs_unchanged',False):raise RuntimeError('root analysis checks failed')
 if not reward['inputs_unchanged']:raise RuntimeError('reward source inputs changed')
 hashes={}
 for src in (analysis,reward):
  for p,expected in src['input_sha256'].items():
   p=Path(p);actual=sha(p)
   if actual!=expected:raise RuntimeError(f'root input hash mismatch: {p}')
   hashes[p]=expected
 helper_paths=[R/'analyze_checkpoint_v3.py',R/'analyze_reward_v2.py',R/'verify_analyzer_functions_v3.py',R/'archive_selected_videos_v1.py',ANALYSIS,REWARD,R/'training_to_checkpoint_v1.jsonl']
 for p in helper_paths:hashes[p]=sha(p)
 frame_paths=[];control_paths=[];trace_paths=[];report_paths=[];video_paths=[]
 for ep in EVALS.values():
  for view in ('whole_body','hands'):
   for fid in IDS:
    p=frame(ep,view,fid)
    if not p.exists():raise FileNotFoundError(p)
    frame_paths.append(p);hashes[p]=sha(p)
  for name,collection in [('controls.json',control_paths),('trace.json',trace_paths),('report.json',report_paths)]:
   p=ep/name;collection.append(p);hashes[p]=sha(p)
  for view in ('whole_body','hands'):
   p=ep/'media'/f'{view}.mp4';video_paths.append(p);hashes[p]=sha(p)
 root_archive_v2=V/'archive_v2'
 root_archive_v3=V/'archive_v3'
 archived=[root_archive_v2/'stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v2/evaluations/update_000001/native/episode_0001/media'/f'{view}.mp4' for view in ('whole_body','hands')]+[root_archive_v3/f'update_000086_{view}.mp4' for view in ('whole_body','hands')]
 for p in archived:hashes[p]=sha(p)
 before=[entry(p) for p in sorted(hashes,key=str)]
 font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';font_manager.fontManager.addfont(font)
 plt.rcParams['font.family']=font_manager.FontProperties(fname=font).get_name();plt.rcParams['axes.unicode_minus']=False
 whole=OUT/'cp1_cp86_whole_body_frames_v1.png';hands=OUT/'cp1_cp86_hands_frames_v1.png'
 outside=OUT/'cp1_cp86_outside_distance_v1.png';so3=OUT/'cp1_cp86_guitar_orientation_v1.png';returns=OUT/'stochastic_episode_returns_v1.png'
 plot_frames('whole_body',whole);plot_frames('hands',hands)
 metrics={k:{'outside_percent':v['outside_percent'],'max_m':v['max_position_outside_norm_m'],'mean_m':v['mean_position_outside_norm_m'],'first_gt_10cm_s':v['first_outside_above_10cm_s'],'so3_max_deg':v['max_SO3_rotation_from_initial_guitar_deg'],'press_frames':v['PLAY_physics_frames_with_diagnostic_press_cells'],'play_frames':v['PLAY_physics_frames'],'music':v['joint_success_events'],'crossings':v['accepted_crossings']} for k,v in analysis['evaluations'].items()}
 fig,ax=plt.subplots(figsize=(9.5,5.2),constrained_layout=False)
 for color,(label,ep),key in zip(COLORS,EVALS.items(),('CP1','new_checkpoint')):
  rows=json.loads((ep/'controls.json').read_text());t=np.array([r['physics_step']/240 for r in rows]);d=np.array([np.linalg.norm(r['position_outside_m']) for r in rows]);m=metrics[key]
  ax.plot(t,d,color=color,lw=2,label=f"{label} · 밖 {m['outside_percent']:.2f}% · max {m['max_m']*100:.1f}cm · mean {m['mean_m']*100:.1f}cm")
 ax.set(xlim=(0,16.3667),xlabel='물리 경과 시간 (초)',ylabel='기타 actor-root 위치 범위 밖 거리 (m)',title='CP1 · CP86 기타 actor-root world-box 이탈')
 ax.grid(alpha=.25);ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),borderaxespad=0);fig.subplots_adjust(left=.12,right=.68,bottom=.14,top=.88);fig.savefig(outside,dpi=170,bbox_inches='tight',facecolor='white');plt.close(fig)
 fig,ax=plt.subplots(figsize=(9.5,5.2),constrained_layout=False)
 for color,(label,ep) in zip(COLORS,EVALS.items()):
  sec,deg=rot_curve(json.loads((ep/'trace.json').read_text()));ax.plot(sec,deg,color=color,lw=2,label=label)
 ax.set(xlim=(0,16.3667),xlabel='물리 경과 시간 (초)',ylabel='초기 기타 root quaternion 대비 SO(3) 회전 (도)',title='CP1 · CP86 기타 orientation 회전')
 ax.grid(alpha=.25);ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),borderaxespad=0);fig.subplots_adjust(left=.12,right=.73,bottom=.14,top=.88);fig.savefig(so3,dpi=170,bbox_inches='tight',facecolor='white');plt.close(fig)
 records=[json.loads(line) for line in (R/'training_to_checkpoint_v1.jsonl').read_text().splitlines() if line.strip()]
 # The final row carries the cumulative list of completed episodes; do not flatten rows.
 eps=[x['return'] for x in records[-1]['completed_episodes']]
 if not eps:raise RuntimeError('no stochastic episode return field')
 fig,ax=plt.subplots(figsize=(10,4.8));ix=np.arange(1,len(eps)+1);ax.plot(ix,eps,'o-',color='#7B2CBF',lw=1.7,ms=4)
 ax.axhline(float(np.mean(eps)),color='#555',ls='--',label=f'22개 평균 {np.mean(eps):.2f}')
 ax.set(xlabel='훈련 episode 순번',ylabel='episode return',title='학습 중 정책이 바뀌는 stochastic rollout episode return')
 ax.grid(alpha=.25);ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),borderaxespad=0);fig.subplots_adjust(left=.12,right=.73,bottom=.14,top=.88);fig.savefig(returns,dpi=170,bbox_inches='tight',facecolor='white');plt.close(fig)
 after=[entry(p) for p in sorted(hashes,key=str)]
 if before!=after:raise RuntimeError('input changed during rendering')
 # Byte-identical archive copies must match the authoritative sources.
 for src,dst in zip(video_paths,archived):
  if sha(src)!=sha(dst):raise RuntimeError(f'archive copy mismatch: {dst}')
 outputs=[entry(p) for p in (whole,hands,outside,so3,returns)]
 provenance={'producer':entry(Path(__file__).resolve()),'analysis_root_json':entry(ANALYSIS),'reward_root_json':entry(REWARD),
  'helpers':[entry(p) for p in helper_paths if p.exists()],'inputs_before':before,'inputs_after':after,'inputs_unchanged_during_render':True,
  'native_videos': [entry(p) for p in video_paths],'archive_video_copies':[entry(p) for p in archived],
  'metrics':metrics,'stochastic_episode_returns':eps,'stochastic_return_mean':float(np.mean(eps)),
  'outputs':outputs,'scope':'86 completed updates in this snapshot (85 new after CP1), 22016 transitions, 22 completed training episodes. Ongoing long training is not claimed complete. Outside metric is guitar actor-root world box; press frames are diagnostic only, not correct pressing; scalar joint q differs from root quaternion SO(3).'}
 (OUT/'followup_comparison_provenance_v1.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'input_count':len(before),'metrics':metrics,'episode_count':len(eps),'outputs':outputs},ensure_ascii=False))
if __name__=='__main__':main()
