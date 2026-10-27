"""Read-only v22 same-point thumb geometry/load and fixed release witness audit."""
from pathlib import Path
import hashlib
import json
import numpy as np
import torch
from guitar_learning.gpu.thumb_support import load_thumb_support, thumb_support_geometry
from guitar_learning.gpu.geometry import apply, conjugate
from guitar_learning.gpu.wrist_region import load_wrist_region_track
from guitar_learning.gpu.press_surface import load_press_surface

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT/'docs/2026-10-26/guitar_learning_hand_contact_v22'
OUT = Path(__file__).resolve().parent
run = PHASE/'native_thumb_smooth_tape'
raw = np.load(run/'physics_env0000.npz')
metadata = json.loads((run/'report.json').read_text())
names = metadata['body_names']
thumb, guitar = names.index('human/LH:thumb3'), names.index('guitar/guitar')
patch = load_thumb_support()
track = load_wrist_region_track(ROOT/'data/song_bundles/05_BN2-131-B_solo', load_press_surface([0], [1]))
center = .5*(track['lower_G_m'][0][1]+track['upper_G_m'][0][1])
tensor = lambda key: torch.tensor(patch[key],dtype=torch.bool if key=='valid' else torch.float64)
local, normals, valid = tensor('points_local'), tensor('normals_local'), tensor('valid')
plane, rear = tensor('plane'), tensor('rear_vertices')
times = raw['time_s']
records, all_points = {}, []
torch.set_num_threads(1)
for low in range(0,len(times),128):
    b = torch.tensor(raw['body_state'][low:low+128], dtype=torch.float64)
    t, g = b[:,thumb], b[:,guitar]
    world = t[:,None,:3]+apply(t[:,None,3:7],local[None])
    points = apply(conjugate(g[:,None,3:7]),world-g[:,None,:3])
    face = apply(conjugate(g[:,None,3:7]),apply(t[:,None,3:7],normals[None]))
    force_g = apply(conjugate(g[:,3:7]),torch.tensor(raw['thumb_net_force'][low:low+128,2],dtype=torch.float64))
    measured = thumb_support_geometry(points,face,valid,torch.full((len(b),),center,dtype=torch.float64),rear,plane,net_force_guitar=force_g)
    for key,value in measured.items():
        records.setdefault('thumb_'+key,[]).append(value.numpy())
    all_points.append(points.numpy())
values = {key:np.concatenate(value) for key,value in records.items()}
points = np.concatenate(all_points)
# Fixed release witness chosen before looking at the release phase itself.
before_release = np.flatnonzero(times <= 6.)[-1]
witness = int(values['thumb_sample_index'][before_release])
values.update(time_s=times.copy(),control_witness_gap=points[:,witness]@patch['plane'][:3]+patch['plane'][3],
    control_witness_index=np.full(len(times),witness),
    stage=np.array(['initial_hold' if t<=1. else 'approach' if t<=4. else 'contact_hold' if t<=6.
        else 'release' if t<=9. else 'released_hold' if t<=10. else 'reapproach' if t<=13. else 'final_hold' for t in times]))
np.savez_compressed(OUT/'smooth_tape_measurements.npz',**values)
stages = {}
for stage in np.unique(values['stage']):
    mask = values['stage']==stage
    load = values['thumb_normal_load'][mask]
    gap = values['thumb_signed_gap'][mask]
    stages[stage] = dict(seconds=int(mask.sum())/240.,candidate_fraction=float(values['thumb_contact_candidate'][mask].mean()),
        max_normal_load_N=float(load.max()),mean_normal_load_N=float(load.mean()),gap_min_m=float(gap.min()),gap_final_m=float(gap[-1]),
        fixed_witness_gap_final_m=float(values['control_witness_gap'][mask][-1]))
contact = values['thumb_contact_candidate']
durations = []
start = None
for i,x in enumerate(np.r_[contact,False]):
    if x and start is None:start=i
    if not x and start is not None:
        durations.append(dict(start_s=float(times[start]),end_s=float(times[i-1]),sampled_s=(i-start)/240.));start=None
input_paths=[run/'physics_env0000.npz',run/'report.json',OUT/'smooth_thumb_target_tape.npz',Path(__file__).resolve(),ROOT/'guitar_learning/gpu/thumb_support.py']
result=dict(native_run_complete=metadata['completed'], native_protocol_complete=metadata['protocol_completed'],source_changed=metadata['changed_inputs'],
    input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in input_paths},
    measured_hz=240,samples=len(times),stages=stages,contact_runs=durations,
    fixed_release_witness_index=witness,fixed_release_witness_selection_time_s=float(times[before_release]),
    max_normal_load_N=float(values['thumb_normal_load'].max()),max_normal_load_time_s=float(times[values['thumb_normal_load'].argmax()]),
    max_guitar_translation_m=float(raw['all_env_max_guitar_translation_m'].max()),
    max_guitar_rotation_rad=float(raw['all_env_max_guitar_rotation_rad'].max()),
    limitation='V22 source same-point geometry plus native thumb3 normal resultant is a contact candidate, not a body-pair, calibrated pressure or musical achievement certificate. Smooth targets are an actions-only diagnostic; no policy inference or production control change.')
(OUT/'smooth_tape_measurements.json').write_text(json.dumps(result,indent=2,allow_nan=False))
print(json.dumps({k:result[k] for k in ('native_run_complete','max_normal_load_N','max_normal_load_time_s','stages')},indent=2))
