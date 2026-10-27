"""Measure actual deterministic residuals and latent exploration from saved states."""
import hashlib,json
from pathlib import Path
import numpy as np
import torch
P=Path(__file__).resolve().parent;Q=P.parent/'stability_support_nominal_v1';inputs={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):inputs[str(p)]=sha(p);return json.loads(Path(p).read_text())
inputs[str(Path(__file__).resolve())]=sha(__file__)
analysis=read(P/'analysis_v1.json');label=analysis['label'];out={}
for source in ['stability_adapter_2/joint_policy_v1.py','stability_adapter_2/deadline_bounded_residual_v1.py','tab2body/learning/models.py']:
 path=Path('/home/ajou/yigyu/3')/source;inputs[str(path)]=sha(path)
for name,cp_path,base in [('CP1',Q/'smoke_on_v2/checkpoints/update_000001.pt',Q/'smoke_on_v2/evaluations/update_000001/native/episode_0001'),('new_checkpoint',Q/'long_on_v1/checkpoints'/(label+'.pt'),Q/'long_on_v1/evaluations'/label/'native/episode_0001')]:
 inputs[str(cp_path)]=sha(cp_path);cp=torch.load(cp_path,map_location='cpu',weights_only=True)
 rows=read(base/'controls.json');groups=np.array(cp['abi']['groups']);caps=np.array([cp['abi']['residual_caps_rad'][g] for g in groups])
 std=cp['model']['log_std'].double().clamp(-5,1).exp().numpy()
 action=np.array([r['policy_action81'] for r in rows]);nominal=np.array([r['nominal81_rad'] for r in rows]);requested=np.array([r['requested81_rad'] for r in rows])
 mu0=np.arctanh(action[0]);halfwidth95=caps*(np.tanh(mu0+1.95996398454*std)-np.tanh(mu0-1.95996398454*std))/2
 out[name]={g:{'max_actual_requested_residual_rad':float(np.max(np.abs(requested-nominal)[:,groups==g])),
  'max_actual_requested_residual_deg':float(np.degrees(np.max(np.abs(requested-nominal)[:,groups==g]))),
  'max_fraction_of_available_residual_cap':float(np.max((np.abs(requested-nominal)/caps)[:,groups==g])),
  'latent_std_min':float(min(std[groups==g])),'latent_std_max':float(max(std[groups==g])),
  't0_95percent_requested_noise_halfwidth_deg_min':float(np.degrees(min(halfwidth95[groups==g]))),
  't0_95percent_requested_noise_halfwidth_deg_max':float(np.degrees(max(halfwidth95[groups==g])))} for g in sorted(set(groups))}
result={'evaluations':out,'input_sha256':inputs,'inputs_unchanged':all(sha(p)==h for p,h in inputs.items()),
 'scope':'saved deterministic PD-request residual amplitudes and state-independent Gaussian latent std; t0 transformed noise intervals before native clipping/rate owner, not actual joint movement; no causal attribution or new trial'}
with (P/'action_scale_diagnosis_v1.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(out['new_checkpoint']))
if not result['inputs_unchanged']:raise SystemExit('diagnostic input changed')
