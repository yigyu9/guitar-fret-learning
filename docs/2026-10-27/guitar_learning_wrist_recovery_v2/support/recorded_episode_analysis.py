import json,numpy as np,torch
from pathlib import Path
from guitar_learning.gpu.geometry import apply,conjugate
from guitar_learning.gpu.press_surface import load_press_surface
from guitar_learning.gpu.wrist_region import load_wrist_region_track,measure_wrist_region
p=Path('/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_reward_simplification_v25/video')
m=json.loads((p/'capture_metadata.json').read_text()); a=np.load(p/'poses_env0000.npz');e=json.loads((p/'episode_env0000.json').read_text())
b=torch.from_numpy(a['body_state']); gi=m['body_names'].index('guitar/guitar');wi=m['body_names'].index('human/L_Wrist'); w=apply(conjugate(b[:,gi,3:7]),b[:,wi,:3]-b[:,gi,:3]);t=torch.from_numpy(a['time_s'])
track=load_wrist_region_track('/home/ajou/yigyu/3/data/song_bundles/05_BN2-131-B_solo',load_press_surface([0],[1]))
g=measure_wrist_region(w,t-3,torch.tensor(track['times_s'],dtype=torch.float64),torch.tensor(track['lower_G_m'],dtype=w.dtype),torch.tensor(track['upper_G_m'],dtype=w.dtype))
d=-g['delta'].numpy();lo=g['lower_G_m'].numpy();hi=g['upper_G_m'].numpy();center=.5*(lo+hi);timer=a['wrist_termination_state']*np.array(m['termination_observation']['scales']);frame=json.load(open('/home/ajou/yigyu/3/data/song_bundles/05_BN2-131-B_solo/training/hand_position_targets.json'))['frames']
def row(i):
 f=frame[max(0,min(len(frame)-1,int(round((float(t[i])-3)*60))))]
 return dict(t=float(t[i]),wrist_G=w[i].tolist(),excess_signed_G=d[i].tolist(),center_G=center[i].tolist(),timer=timer[i].tolist(),anchor_fret=f['anchor_fret'],allowed_fret_range=f['allowed_fret_range'])
r=dict(source=str(p),scope='60Hz endpoints only; timers recorded actual240Hz integrator',max_abs_excess_G=np.abs(d).max(0).tolist(),rows=[row(i) for i in sorted(set([0,179,239,299,311,312,313,329,341,356]))],latch_start_rows=[row(i) for i in np.flatnonzero((timer[:,0]>0)&np.r_[True,timer[:-1,0]==0])],max_clean=float(np.max(e['left_note_ledger']['values']['clean'])),max_contact=float(np.max(e['left_note_ledger']['values']['contact_time'])))
i=311;j=356
r['last_interval']=dict(start_s=float(t[i]),end_s=float(t[j]),wrist_delta_G=(w[j]-w[i]).tolist(),box_center_delta_G=(center[j]-center[i]).tolist(),wrist_delta_world=(b[j,wi,:3]-b[i,wi,:3]).tolist(),guitar_delta_world=(b[j,gi,:3]-b[i,gi,:3]).tolist(),excess_start=d[i].tolist(),excess_end=d[j].tolist())
(Path(__file__).resolve().parents[1]/'recorded_episode_analysis.json').write_text(json.dumps(r,indent=2)); print(json.dumps(r,indent=2))
