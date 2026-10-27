"""CPU inspection of a completed actual GPU2000-to2001 resume."""
import hashlib
import json
import math
import os
from pathlib import Path
os.environ['CUDA_VISIBLE_DEVICES']=''
import numpy as np
import torch

torch.set_num_threads(1)
p=Path(__file__).resolve().parent
main_report=json.loads((p/'train1024_large_2000/report.json').read_text())
assert main_report['completed'] and main_report['optimizer_updates']==2000 and main_report['transitions']==65_536_000
run=p/'resume_after_long_1'
report=json.loads((run/'report.json').read_text())
assert report['completed'] and report['failure'] is None and report['stopped']=='updates_complete'
assert report['optimizer_updates']==2001 and report['transitions']==32768
assert not report['cleanup_errors'] and not report['changed_inputs'] and not report['missing_import_pins']
s=report['settings']
assert (s['size'],s['num_envs'],s['horizon'],s['updates'])==('large',1024,32,1)
assert report['journal']['committed']==32768 and report['journal']['discarded']==0
assert report['journal']['closed'] and not report['journal']['failed']
scene=report['gpu_scene']
assert report['lifecycle_verified'] and scene['closed'] and scene['physics_steps']==128
assert scene['environment_count']==1024 and scene['simulator_count']==1
assert scene['physx_use_gpu'] and scene['use_gpu_pipeline']
assert all(v=='cuda:0' for v in scene['tensor_devices'].values())
pins=json.loads((run/'inputs_before.json').read_text())
source_checkpoint=p/'train1024_large_2000/final.pt'
assert len(pins)==569 and str(source_checkpoint) in pins
assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v for k,v in pins.items())
source=torch.load(source_checkpoint,map_location='cpu',weights_only=False)
initial=torch.load(run/'initial.pt',map_location='cpu',weights_only=False)
final=torch.load(run/'final.pt',map_location='cpu',weights_only=False)

def same(a,b):
    if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a,b)
    if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and np.array_equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    return a==b

assert source.keys()==initial.keys()
assert all(same(v,initial[k]) for k,v in source.items() if k!='metadata')
assert source['updates']==initial['updates']==2000 and final['updates']==2001
assert same(source['identity'],final['identity'])
counts={}
def finite(v,branch):
    if isinstance(v,torch.Tensor):
        assert v.device.type=='cpu' and bool(torch.isfinite(v).all())
        counts[branch]=counts.get(branch,0)+1
    elif isinstance(v,dict):
        for x in v.values():finite(x,branch)
    elif isinstance(v,(list,tuple)):
        for x in v:finite(x,branch)
    elif isinstance(v,float):assert math.isfinite(v)
for branch in ('model','actor_optimizer','value_optimizer'):
    finite(final[branch],branch)
    assert counts.get(branch,0)>0
assert not same(initial['actor_optimizer'],final['actor_optimizer'])
assert not same(initial['value_optimizer'],final['value_optimizer'])
changed=[k for k,v in initial['model'].items() if not same(v,final['model'][k])]
assert any(k.startswith(('actor_encoders.left.','actor_heads.left.')) for k in changed)
assert not any(k.startswith(('actor_encoders.right.','actor_heads.right.')) for k in changed)
assert torch.equal(initial['model']['log_std'][33:],final['model']['log_std'][33:])
result=dict(completed=True,scope='Actual large1024 H32 GPU one-update continuation; prepared scene restarts at a new episode boundary, not a saved mid-song physics state',
    source_optimizer_updates=2000,resumed_optimizer_updates=2001,committed_transitions=32768,
    initial_all_nonmetadata_exact=True,restored_components='model, both optimizers, RNG including CUDA topology, curriculum and trainer state',
    changed_model_keys=changed,changed_both_optimizers=True,inactive_right_actor_unchanged=True,
    final_CPU_finite_tensor_counts=counts,input_pins_verified=len(pins),actual_GPU_scene=scene,
    checkpoint_sha256=hashlib.sha256((run/'final.pt').read_bytes()).hexdigest())
with (p/'resume_verification.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps(result,indent=2))
