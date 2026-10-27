"""Read-only source convex intersections at predeclared native thumb times."""
import os
os.environ['MUJOCO_GL']='osmesa'
os.environ['PYOPENGL_PLATFORM']='osmesa'
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
from guitar_learning.gpu.hand_collision import SEGMENT_FINGER
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model,set_body_poses

ROOT=Path('/home/ajou/yigyu/3')
PHASE=ROOT/'docs/2026-10-26/guitar_learning_hand_contact_v22'
OUT=Path(__file__).resolve().parent
run=PHASE/'native_thumb_smooth_tape'
raw=np.load(run/'physics_env0000.npz')
report=json.loads((run/'report.json').read_text())
helper_path=ROOT/'docs/2026-10-26/시각화/생성자료/render_finger_preparation_candidates_v1.py'
spec=importlib.util.spec_from_file_location('thumb_source_convex_audit',helper_path)
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
model,data,mapping,_=build_model(load_prepared_reset_contract()['initial'])
frames={}
for timestamp in (5.99,9.99,14.99):
    i=int(np.abs(raw['time_s']-timestamp).argmin())
    state={a+'_body_states':[] for a in ('human','guitar','chair')}
    for name,row in zip(report['body_names'],raw['body_state'][i]):
        state[name.split('/')[0]+'_body_states'].append(dict(pose=dict(p=dict(zip('xyz',row[:3].tolist())),r=dict(zip('xyzw',row[3:7].tolist())))))
    readback=set_body_poses(model,data,mapping,state)
    rows=[r for r in helper.separation_check(model,data) if all(n.split('/',1)[-1] in SEGMENT_FINGER for n in r['bodies'])]
    intersections=[r for r in rows if r['overlap_over_1um']]
    frames[str(float(raw['time_s'][i]))]=dict(readback=readback,checked_pairs=len(rows),source_convex_intersections=intersections)
result=dict(frames=frames,input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (run/'physics_env0000.npz',run/'report.json',helper_path,Path(__file__).resolve())},
    limitation='Read-only source convex geometry at actual recorded native poses. Convex intersection inradius is not cooked collision penetration, contact pair, pressure or continuous no-penetration certification. No MuJoCo integration.')
(OUT/'source_overlap_audit.json').write_text(json.dumps(result,indent=2,allow_nan=False))
print(json.dumps(frames,indent=2))
