"""Source hull and coherent thumb-patch audit of real recorded native poses."""
import hashlib,importlib.util,json,os
from pathlib import Path
os.environ['MUJOCO_GL']='osmesa';os.environ['PYOPENGL_PLATFORM']='osmesa'
import numpy as np
import torch
from guitar_learning.gpu.hand_collision import SEGMENT_FINGER
from guitar_learning.gpu.thumb_support import load_thumb_support,thumb_support_geometry
from guitar_learning.gpu.geometry import apply,conjugate
from guitar_learning.gpu.press_surface import load_press_surface
from guitar_learning.gpu.wrist_region import load_wrist_region_track
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model,set_body_poses

ROOT=Path.cwd();PHASE=ROOT/'docs/2026-10-26/guitar_learning_hand_contact_v21'
torch.set_num_threads(1)
helper_path=ROOT/'docs/2026-10-26/시각화/생성자료/render_finger_preparation_candidates_v1.py'
spec=importlib.util.spec_from_file_location('static_convex_helper',helper_path);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
prepared=load_prepared_reset_contract();model,data,mapping,_=build_model(prepared['initial'])
thumb=load_thumb_support()
patch={k:torch.tensor(thumb[k]) for k in ('points_local','normals_local','valid','rear_vertices','plane')}
from guitar_learning.song.task import make_task
bundle=ROOT/'data/song_bundles/05_BN2-131-B_solo';task=make_task(bundle,pre_roll_s=3.,tail_s=.5)
region=load_wrist_region_track(bundle,load_press_surface([t.string for t in task.targets],[t.fret for t in task.targets]))
outputs={}
for label,folder in [('old','action_tape_source_filters'),('selective','action_tape_selective_filters')]:
 run=PHASE/folder;raw=np.load(run/'physics_env0000.npz');report=json.loads((run/'report.json').read_text());names=report['body_names']
 body=raw['body_state'];times=raw['time_s'];g=names.index('guitar/guitar');th=names.index('human/LH:thumb3')
 center_track=.5*(np.array(region['lower_G_m'])[:,1]+np.array(region['upper_G_m'])[:,1])
 center=np.interp(times-3.,region['times_s'],center_track)
 qualities=[];near=[];gaps=[];facing=[];excess=[]
 for low in range(0,len(body),128):
  b=torch.tensor(body[low:low+128],dtype=torch.float64);t=b[:,th];gb=b[:,g]
  p=t[:,None,:3]+apply(t[:,None,3:7],patch['points_local'].double()[None])
  points=apply(conjugate(gb[:,None,3:7]),p-gb[:,None,:3])
  normals=apply(conjugate(gb[:,None,3:7]),apply(t[:,None,3:7],patch['normals_local'].double()[None]))
  r=thumb_support_geometry(points,normals,patch['valid'],torch.tensor(center[low:low+128]),patch['rear_vertices'],patch['plane'])
  qualities.extend(r['quality'].tolist());near.extend(r['near_geometry'].tolist());gaps.extend(r['signed_gap'].tolist());facing.extend(r['normal_cos'].tolist());excess.extend(r['region_excess'].tolist())
 frames={}
 for time_s in (5.,15.,float(times[-1])):
  i=int(np.abs(times-time_s).argmin());state={a+'_body_states':[] for a in ('human','guitar','chair')}
  for name,row in zip(names,body[i]):state[name.split('/')[0]+'_body_states'].append(dict(pose=dict(p=dict(zip('xyz',row[:3].tolist())),r=dict(zip('xyzw',row[3:7].tolist())))))
  readback=set_body_poses(model,data,mapping,state)
  rows=[r for r in helper.separation_check(model,data) if all(n.split('/',1)[-1] in SEGMENT_FINGER for n in r['bodies'])]
  frames[str(float(times[i]))]=dict(readback=readback,intersections=[r for r in rows if r['overlap_over_1um']],checked_pairs=len(rows))
 outputs[label]=dict(samples=len(body),hz=240,thumb=dict(mean_quality=float(np.mean(qualities)),near_geometry_fraction=float(np.mean(near)),final_quality=qualities[-1],final_gap_m=gaps[-1],final_normal_cos=facing[-1],final_region_excess_m=excess[-1]),source_convex_frames=frames,
  raw_sha256=hashlib.sha256((run/'physics_env0000.npz').read_bytes()).hexdigest())
result=dict(results=outputs,thumb_measurement=thumb['contract'],limitation='Native poses and net forces are separate evidence; source convex intersection inradius is not cooked penetration depth or body-pair pressure; identical action tape is not policy performance or learned thumb guidance comparison.')
(PHASE/'support/native_geometry_comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False))
for label,row in outputs.items():print(label,row['thumb'],[(t,len(s['intersections'])) for t,s in row['source_convex_frames'].items()])
