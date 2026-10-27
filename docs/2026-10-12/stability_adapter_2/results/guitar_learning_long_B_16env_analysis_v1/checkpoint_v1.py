"""Inspect stored weights without creating physics, restoring RNG, or training."""
from pathlib import Path
import hashlib,json
base=Path(__file__).resolve().parent;run=base.parent/'guitar_learning_long_B_16env_20261018_100545'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={str(f.resolve()):sha(f) for f in [Path(__file__),run/'initial.pt',run/'checkpoint_000009.pt']}
(base/'checkpoint_inputs_before.json').write_text(json.dumps(pins,indent=2))
import torch
torch.set_num_threads(1);rows=[]
for name in ('initial.pt','checkpoint_000009.pt'):
 d=torch.load(run/name,map_location='cpu',weights_only=False);std=d['model']['log_std'].clamp(-5,2).exp()
 rows.append(dict(file=str(run/name),updates=d['updates'],identity=d['identity'],model_all_finite=all(torch.isfinite(x).all().item() for x in d['model'].values()),model_parameters=sum(x.numel() for x in d['model'].values()),std_min=std.min().item(),std_mean=std.mean().item(),std_max=std.max().item(),actual_actor_lr=d['actor_optimizer']['param_groups'][0]['lr']))
changed=[p for p,h in pins.items() if sha(p)!=h]
(base/'checkpoint_analysis.json').write_text(json.dumps(dict(rows=rows,changed_inputs=changed,input_sha256=pins,scope='CPU weights-only inspection; not strict resume/physical replay, checkpoint covers10updates only'),indent=2))
print(json.dumps([{k:v for k,v in r.items() if k!='identity'} for r in rows],indent=2))
assert not changed
