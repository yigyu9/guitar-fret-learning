"""Verify loaded initial state exactly against the approved100-update checkpoint."""
from pathlib import Path
import json,hashlib
import numpy as np
import torch
P=Path(__file__).resolve().parents[1];launch=json.loads((P/'support/launch_inputs.json').read_text());source=Path(launch['resume'])
def equal(a,b):
 if torch.is_tensor(a):return torch.is_tensor(b) and torch.equal(a,b)
 if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and np.array_equal(a,b)
 if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(v,b[k]) for k,v in a.items())
 if isinstance(a,(tuple,list)):return type(a)==type(b) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return type(a)==type(b) and a==b
assert hashlib.sha256(source.read_bytes()).hexdigest()==launch['sha256']
a=torch.load(source,map_location='cpu',weights_only=False);b=torch.load(P/'train/initial.pt',map_location='cpu',weights_only=False)
keys=['identity','model','actor_optimizer','value_optimizer','cost_weight','updates','torch_rng','numpy_rng','python_rng','cuda_rng']
checks={k:equal(a[k],b[k]) for k in keys};assert all(checks.values())
result=dict(completed=True,resume=str(source),source_sha256=launch['sha256'],initial_sha256=hashlib.sha256((P/'train/initial.pt').read_bytes()).hexdigest(),initial_optimizer_updates=b['updates'],exact_restore=checks,scope='Physical episodes restart from035/v14; model, optimizers, RNG and registered training state restore strictly')
(P/'resume_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
