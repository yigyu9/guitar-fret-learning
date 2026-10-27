"""Saved-pose60Hz geometry and time comparison; no load/contact reconstruction."""
import json
from pathlib import Path
import numpy as np
import torch
from guitar_learning.gpu.finger_reward import finger_posture_reward, finger_preparation_reward
from guitar_learning.gpu.fingertip_pad import load_fingertip_pad, pad_target_geometry
from guitar_learning.gpu.press_surface import load_press_surface, project_press_strings
from guitar_learning.gpu.geometry import apply, conjugate

torch.set_num_threads(1)
root = Path(__file__).resolve().parents[4]
phase = Path(__file__).resolve().parents[1]
evaluation = root/'docs/2026-10-24/guitar_learning_long_training_v17/evaluation_update_1000_1024'
metadata = json.loads((evaluation/'capture_metadata.json').read_text())
targets = json.loads((evaluation/'targets.json').read_text())
with np.load(evaluation/'poses_env0000.npz') as data:
    body = torch.tensor(data['body_state'])
    now = torch.tensor(data['clock'], dtype=torch.float64)/240.
strings = torch.tensor([t['string'] for t in targets])
frets = torch.tensor([t['fret'] for t in targets])
fingers = torch.tensor([t['finger'] for t in targets])
onset, end, press = (torch.tensor([t[k] for t in targets], dtype=torch.float64) for k in ('onset_s','end_s','press_s'))
names = metadata['body_names']
posture = metadata['posture_reconstruction']
pad = load_fingertip_pad()
plane = torch.tensor(load_press_surface(strings.numpy(), frets.numpy())['plane_G'])
indices = [names.index('human/'+name) for name in pad['contract']['body_names']]
start_ids = [names.index('guitar/G:string%d'%i) for i in range(1,7)]
end_ids = [names.index('guitar/G:string%d_end'%i) for i in range(1,7)]
fret_ids = [names.index('guitar/G:nut')]+[names.index('guitar/G:fret%d'%i) for i in range(1,23)]
distances = []
for i in range(0, len(body), 64):
    b = body[i:i+64]
    g = b[:, names.index('guitar/guitar')]
    local = apply(conjugate(g[:,None,3:7]), b[:,:,:3]-g[:,None,:3])
    tips = b[:,indices]
    world = tips[:,:,None,:3]+apply(tips[:,:,None,3:7], torch.tensor(pad['points_local'])[None].float())
    points = apply(conjugate(g[:,None,None,3:7]), world-g[:,None,None,:3])
    normals = apply(conjugate(g[:,None,None,3:7]), apply(tips[:,:,None,3:7], torch.tensor(pad['normals_local'])[None].float()))
    starts, ends = project_press_strings(local[:,start_ids], local[:,end_ids], plane)
    fret_y = local[:,fret_ids,1]
    low = torch.minimum(fret_y[:,frets-1],fret_y[:,frets])
    high = torch.maximum(fret_y[:,frets-1],fret_y[:,frets])
    measured = pad_target_geometry(points,normals,torch.zeros_like(points),torch.tensor(pad['valid']),
        starts,ends,low,high,strings,fingers,torch.zeros(len(b),4,dtype=torch.bool),plane)
    distances.append(measured['distance'])
distance = torch.cat(distances)
args = (now,onset,end,press,fingers,body[:,posture['palm_body_index'],3:7].double(),
        body[:,torch.tensor(posture['segment_body_indices']),3:7].double())
old = finger_posture_reward(*args)
new = finger_preparation_reward(*args,torch.zeros(len(body),4,dtype=torch.bool),distance)
assigned = fingers[None] == torch.arange(1,5)[:,None]
old_near = ((distance<=.04)[:,None]&assigned[None]).any(-1)
old_gate = old['idle_weight']*~old_near
result = dict(scope='Same recorded v17 best env0 geometry at60Hz endpoints excluding reset. New gate is an upper bound: missing contact forces/candidate/wrong prevent exact240Hz reward reconstruction. No policy re-training or new physics.',
    sample_count=len(body)-1,fingers=['index','middle','ring','pinky'],
    old_time_idle_fraction=(old['idle_weight'][1:]>0).double().mean(0).tolist(),
    new_time_idle_fraction=(new['idle_weight'][1:]>0).double().mean(0).tolist(),
    old_time_geometry_eligible_fraction=(old_gate[1:]>0).double().mean(0).tolist(),
    new_time_geometry_eligible_fraction=(new['gate'][1:]>0).double().mean(0).tolist(),
    samples=[])
for second in (0,4,8,12,16,20,24,28,32):
    i=int(torch.argmin((now-second).abs()))
    result['samples'].append(dict(time_s=float(now[i]),old_time_idle=old['idle_weight'][i].tolist(),
        new_time_idle=new['idle_weight'][i].tolist(),new_geometry_gate=new['gate'][i].tolist(),
        actual_flexion_degrees=(old['angles'][i]*180/np.pi).tolist()))
(phase/'saved_pose_gate_comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='samples'},indent=2))
