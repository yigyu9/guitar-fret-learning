from pathlib import Path
import hashlib,json
import numpy as np
import torch
P=Path(__file__).resolve().parents[1]
def equal(a,b):
 if torch.is_tensor(a):return torch.is_tensor(b) and torch.equal(a,b)
 if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and np.array_equal(a,b)
 if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(v,b[k]) for k,v in a.items())
 if isinstance(a,(tuple,list)):return type(a)==type(b) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return type(a)==type(b) and a==b
records={}
for name,expected in [('smoke1024',65536),('resume1024',32768)]:
 r=json.loads((P/name/'report.json').read_text());j=r['journal'];assert r['completed'] and r['lifecycle_verified'] and not r['changed_inputs'] and not r['missing_import_pins'];assert all(j[k]==expected for k in ('sampled','logged','durable','committed')) and not j['discarded']
 records[name]=dict(transitions=expected,report_sha256=hashlib.sha256((P/name/'report.json').read_bytes()).hexdigest(),journal={k:j[k] for k in ('sampled','logged','durable','committed','discarded')})
a=torch.load(P/'smoke1024/final.pt',map_location='cpu',weights_only=False);b=torch.load(P/'resume1024/initial.pt',map_location='cpu',weights_only=False)
keys=['model','actor_optimizer','value_optimizer','cost_weight','updates','torch_rng','numpy_rng','python_rng','cuda_rng']
checks={k:equal(a[k],b[k]) for k in keys};assert all(checks.values())
result=dict(completed=True,runs=records,exact_resume_initial=checks,saved_updates=a['updates'],limitation='Two plus one updates; not whole-song stability or performance at1024env')
(P/'integration_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
