import sys
sys.dont_write_bytecode=True
import datetime, hashlib, importlib, json
from pathlib import Path
import numpy as np
import torch

torch.set_num_threads(1);torch.set_num_interop_threads(1)
root=Path('/home/ajou/yigyu/3');base=root/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1';out=base/'analysis_v1';frozen=base/'frozen_execution_view_v2';manifest=json.loads((frozen/'manifest.json').read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def frozen_input(relative):
 original=str(root/relative);copy=Path(manifest['external_copies'][original]);assert sha(copy)==manifest['input_pins'][original];return copy
baseline=frozen_input('docs/2026-10-12/stability_adapter_2/results/guitar_learning_contact_recovery_v1/reference_provenance_migration_v1/checkpoint_evaluation_only.pt')
current=base/'training_long_v1/checkpoint_000031.pt'
data=frozen_input('docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_long_v1/single_a_contact_v1/case_000/demonstration.npz')
contract_path=frozen_input('docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_long_v1/single_a_contact_v1/case_000/contract.json')
case_result=frozen_input('docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_long_v1/single_a_contact_v1/case_000/result.json')
# Import package from the immutable view. No production/native imports occur.
sys.path.insert(0,str(frozen))
policy_module=importlib.import_module('guitar_learning.transition_refinement.policy')
assert frozen in Path(policy_module.__file__).parents
source_paths={name:Path(module.__file__) for name,module in sys.modules.items() if name.startswith('guitar_learning') and getattr(module,'__file__',None)}
assert all(frozen in path.parents for path in source_paths.values())
assert not any(name.startswith('isaacgym') for name in sys.modules)
files=[baseline,current,data,contract_path,case_result,*source_paths.values()];pins={str(path):sha(path) for path in files}
a=torch.load(baseline,map_location='cpu',weights_only=False);b=torch.load(current,map_location='cpu',weights_only=False)
assert a['identity']==b['identity'] and a['updates']==32 and b['updates']==64
architecture=a['identity']['architecture'];contract=architecture['contract'];data_contract=json.loads(contract_path.read_text())
assert data_contract['observation']==contract['observation']
assert data_contract['action']==contract['action']
models=[]
for payload in [a,b]:
 exp={key:architecture['exploration'][key] for key in ['min_std','max_std','initial_std']}
 model=policy_module.SpecialistPolicy(state_dim=architecture['state_dim'],event_dim=architecture['event_dim'],size=architecture['size'],contract=contract,exploration=exp)
 assert model.architecture==architecture
 model.load_state_dict(payload['model'],strict=True);model.eval();models.append(model)
with np.load(data,allow_pickle=False) as arrays:
 indices=np.arange(0,len(arrays['state']),4,dtype=np.int64)
 inputs={key:torch.from_numpy(arrays[key][indices].copy()) for key in ['state','events','mask','priority_events','priority_mask']}
 times=arrays['task_time_s'][indices].copy()
 shapes={key:{'source_shape':list(arrays[key].shape),'selected_shape':list(value.shape),'dtype':str(value.dtype)} for key,value in inputs.items()}
 state_range=[float(inputs['state'].min()),float(inputs['state'].max())]
with torch.no_grad():
 outputs=[model.act(**inputs,deterministic=True) for model in models]

def metric(delta):
 v=delta.double()
 return {'count':v.numel(),'rms':float(v.square().mean().sqrt()),'mean_abs':float(v.abs().mean()),'max_abs':float(v.abs().max()),'exact_equal_fraction':float((v==0).double().mean())}
summary={}
for name,sl in [('active_left',slice(0,33)),('inactive_right',slice(33,39))]:
 latent_delta=outputs[1]['mean'][:,sl]-outputs[0]['mean'][:,sl]
 action_delta=outputs[1]['action'][:,sl]-outputs[0]['action'][:,sl]
 summary[name]={'latent_mean_delta':metric(latent_delta),'deterministic_tanh_action_delta':metric(action_delta)}
 if name=='active_left':
  sigma=outputs[0]['log_std'][:,sl].double().exp()
  summary[name]['latent_mean_delta_over_baseline_sigma']=metric(latent_delta.double()/sigma)
  summary[name]['baseline_sigma_range']=[float(sigma.min()),float(sigma.max())]
phase={}
for name,mask in [('preparation_before_2s',times<2),('audible_2_to_2_5s',(times>=2)&(times<2.5)),('post_note_at_least_2_5s',times>=2.5)]:
 phase[name]={'observations':int(mask.sum()),'active_latent_mean_delta':metric((outputs[1]['mean']-outputs[0]['mean'])[mask,:33]),'active_action_delta':metric((outputs[1]['action']-outputs[0]['action'])[mask,:33])}
result={'schema':'guitar_learning.fixed_observation_actor_delta.v1','captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'CPU deterministic forward only on selected frozen teacher BC observations; no simulation, PPO update, native/GPU evaluation, or full training-state coverage.','source_pins':pins,'baseline_updates':a['updates'],'current_updates':b['updates'],'identities_equal':True,'strict_model_state_load':True,'constructed_architecture_exact_equal':True,'data_observation_and_action_contract_exact_equal':True,'data_selection':{'source_rows':240,'indices':indices.tolist(),'stride':4,'selected_rows':len(indices),'task_time_s':times.tolist(),'time_range_s':[float(times.min()),float(times.max())],'shapes':shapes,'state_range':state_range,'capture_success_recorded':json.loads(case_result.read_text())['success']},'summary':summary,'phase_summary':phase,'imported_guitar_learning_sources':{k:str(v) for k,v in source_paths.items()},'torch_threads':torch.get_num_threads(),'torch_interop_threads':torch.get_num_interop_threads(),'helper_sha256':sha(Path(__file__)),'noise_comparison_scope':'Baseline sigma is latent Gaussian std. Only latent mean delta/sigma is dimensionally matched; tanh action noise is not constant sigma.'}
assert all(sha(Path(path))==digest for path,digest in pins.items());result['source_unchanged_after_analysis']=True
(out/'actor_output_mid32.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'summary':summary,'phase_summary':phase,'data_shapes':shapes,'state_range':state_range},indent=2))
