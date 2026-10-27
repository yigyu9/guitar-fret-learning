"""Checkpoint changes on the same recorded training observations; no new physics/evaluation."""
from pathlib import Path
import json,sys,hashlib,math
base=Path(__file__).resolve().parent;root=base.parents[4]
pins={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
pins[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
import torch
from guitar_learning.policy import Policy
torch.set_num_threads(1);rows=[]
for run in sorted(base.glob('pilot_*/report.json')):
 d=json.loads(run.read_text())
 if not d['completed']:continue
 paths=[run.parent/name for name in ('initial.pt','final.pt','rollout_first.pt')]
 for p in paths:pins[str(p.resolve())]=hashlib.sha256(p.read_bytes()).hexdigest()
 initial,final,buffer=[torch.load(p,map_location='cpu',weights_only=False) for p in paths]
 a=initial['identity']['architecture'];before=Policy(a['state_dim'],size=a['size'],contract=a['contract']);after=Policy(a['state_dim'],size=a['size'],contract=a['contract'])
 before.load_state_dict(initial['model']);after.load_state_dict(final['model'])
 # Compare bounded deterministic actions on the exact same stored states.
 observation={k:buffer[k].flatten(0,1) for k in ('state','events','mask','priority_events','priority_mask')}
 differences=[]
 with torch.no_grad():
  for start in range(0,len(observation['state']),256):
   obs={k:v[start:start+256] for k,v in observation.items()}
   x=before.act(**obs,deterministic=True)['action'];y=after.act(**obs,deterministic=True)['action']
   differences.append((y-x).abs())
 difference=torch.cat(differences);std=final['model']['log_std'].clamp(-5,2).exp()
 rows.append(dict(run=run.parent.name,updates=final['updates'],all_finite=all(torch.isfinite(v).all().item() for v in final['model'].values()),initial_std=d['settings']['initial_std'],final_std_min=std.min().item(),final_std_mean=std.mean().item(),final_std_max=std.max().item(),deterministic_action_mean_abs_change_on_first_training_buffer=difference.mean().item(),deterministic_action_max_abs_change_on_first_training_buffer=difference.max().item(),actual_actor_lr=final['actor_optimizer']['param_groups'][0]['lr']))
changed=[p for p,h in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
(base/'pilot_checkpoint_analysis.json').write_text(json.dumps(dict(rows=rows,input_sha256=pins,changed_inputs=changed,scope='same stored training states only; action changes prove optimizer effect, not independent native musical success'),indent=2))
print(json.dumps(rows,indent=2))
