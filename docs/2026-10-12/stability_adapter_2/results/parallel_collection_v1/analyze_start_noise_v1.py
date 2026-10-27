"""Report physical reset noise separately from inherited latent policy std."""
import hashlib,json
from pathlib import Path
import torch
P=Path(__file__).resolve().parent
record=json.loads((P/'previous_stop_snapshot_v1.json').read_text())['checkpoint_record'];cp=Path(record['checkpoint'])
before=hashlib.sha256(cp.read_bytes()).hexdigest();assert before==record['sha256']
payload=torch.load(cp,map_location='cpu',weights_only=True)
std=payload['model']['log_std'].exp();groups=payload['abi']['groups']
values={}
for group in ('body','head','arm','finger'):
    selected=std[[i for i,g in enumerate(groups) if g==group]]
    values[group]={'joints':len(selected),'latent_std_min':float(selected.min()),'latent_std_mean':float(selected.mean()),'latent_std_max':float(selected.max())}
assert hashlib.sha256(cp.read_bytes()).hexdigest()==before
with (P/'initial_noise_analysis_v1.json').open('x') as f:json.dump({'checkpoint':str(cp),'sha256':before,'updates':payload['updates'],
    'physical_reset_randomization':False,'policy_training_sample':'Gaussian latent -> tanh -> bounded radian residual',
    'deterministic_video_evaluation':True,'std_by_group':values,
    'units':'dimensionless latent std; not joint-angle rad or deg; action and target noise differ after tanh and residual codec'},f,indent=2)
print(json.dumps(values,indent=2))
