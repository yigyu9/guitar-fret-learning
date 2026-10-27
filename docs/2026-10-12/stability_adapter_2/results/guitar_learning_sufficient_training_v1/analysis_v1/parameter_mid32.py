import hashlib, json, math, datetime
from pathlib import Path
import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
root=Path('/home/ajou/yigyu/3')
base=root/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1'
out=base/'analysis_v1'
original=root/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/long_training_v2/checkpoint_000031.pt'
baseline=base/'frozen_execution_view_v2/inputs/docs/2026-10-12/stability_adapter_2/results/guitar_learning_contact_recovery_v1/reference_provenance_migration_v1/checkpoint_evaluation_only.pt'
current=base/'training_long_v1/checkpoint_000031.pt'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
pins={str(path):sha(path) for path in [original,baseline,current]}
assert pins[str(original)]=='ed4408f945b47732988927428a2228281abe777ac13a2b0ad797e0e64e6ffde7'
assert pins[str(baseline)]=='8bedd8d9affc16406b3fb82667429615b8f13ec5e894d1dc576e940549edfd67'
a=torch.load(baseline,map_location='cpu',weights_only=False);b=torch.load(current,map_location='cpu',weights_only=False);o=torch.load(original,map_location='cpu',weights_only=False)
schema=lambda d:{k:{'shape':list(v.shape),'dtype':str(v.dtype)} for k,v in d['model'].items()}
assert schema(a)==schema(b)==schema(o)
assert all(torch.equal(v,o['model'][k]) for k,v in a['model'].items())
assert a['updates']==o['updates']==32 and b['updates']==64
assert a['identity']==b['identity']

def calculate(names,sl=None):
 reference=[];changed=[]
 for name in names:
  x=a['model'][name].detach().cpu();y=b['model'][name].detach().cpu()
  if sl is not None:x=x[sl];y=y[sl]
  assert torch.isfinite(x).all() and torch.isfinite(y).all()
  reference.append(x.reshape(-1).double());changed.append(y.reshape(-1).double())
 x=torch.cat(reference);y=torch.cat(changed);delta=y-x
 n=x.numel();l2=float(torch.linalg.vector_norm(delta));ref=float(torch.linalg.vector_norm(x))
 return {'tensor_count':len(names),'element_count':n,'exact_equal_elements':int((x==y).sum()),'exact_equal_fraction':float((x==y).double().mean()),'exact_equal_tensors':sum(torch.equal(a['model'][k] if sl is None else a['model'][k][sl],b['model'][k] if sl is None else b['model'][k][sl]) for k in names),'mean_abs_delta':float(delta.abs().mean()),'max_abs_delta':float(delta.abs().max()),'rms_delta':l2/math.sqrt(n),'l2_delta':l2,'baseline_rms':ref/math.sqrt(n),'relative_l2_delta':l2/ref if ref else None}
groups={
 'active_left_actor':[k for k in a['model'] if k.startswith(('actor_encoders.left.','actor_heads.left.'))],
 'inactive_right_actor':[k for k in a['model'] if k.startswith(('actor_encoders.right.','actor_heads.right.'))],
 'shared_value_encoder':[k for k in a['model'] if k.startswith('value_encoder.')],
 'reward_critic_head':[k for k in a['model'] if k.startswith('reward_critic.')],
 'cost_critic_head':[k for k in a['model'] if k.startswith('cost_critic.')],
}
summary={name:calculate(names) for name,names in groups.items()}
summary['active_left_log_std']=calculate(['log_std'],slice(0,33));summary['inactive_right_log_std']=calculate(['log_std'],slice(33,39))
per_tensor={k:calculate([k]) for k in a['model'] if k!='partner_initialized'}
std={}
for name,d in [('baseline',a),('additional32',b)]:
 v=d['model']['log_std'][:33].double().exp();std[name]={'mean':float(v.mean()),'min':float(v.min()),'max':float(v.max())}
result={'schema':'guitar_learning.parameter_delta_mid32.v1','captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'CPU tensor comparison only, no model forward/native/GPU evaluation; active run not finalized.','source_pins':pins,'baseline_used_by_run':str(baseline),'baseline_original':str(original),'current':str(current),'baseline_optimizer_updates':a['updates'],'current_optimizer_updates':b['updates'],'additional_updates':b['updates']-a['updates'],'original_vs_migrated_model_exact_equal':True,'tensor_schemas_equal':True,'identities_equal':True,'tensor_schema':schema(a),'tensor_schema_sha256':hashlib.sha256(json.dumps(schema(a),sort_keys=True).encode()).hexdigest(),'groups':summary,'per_tensor':per_tensor,'active_latent_std':std,'partner_initialized_buffer_exact_equal':torch.equal(a['model']['partner_initialized'],b['model']['partner_initialized']),'definitions':{'rms_delta':'sqrt(sum((current-baseline)^2)/number_of_elements)','relative_l2_delta':'L2(current-baseline)/L2(baseline); null if baseline norm zero','exact_equal_fraction':'number of exactly unchanged scalar elements / group elements','grouping':'Actor L/R separated; critic heads separated from their shared value encoder. log_std split active33/inactive6.'},'torch_threads':torch.get_num_threads(),'torch_interop_threads':torch.get_num_interop_threads(),'torch_version':str(torch.__version__),'helper_sha256':sha(Path(__file__))}
assert all(sha(Path(p))==value for p,value in pins.items());result['source_unchanged_after_analysis']=True
(out/'parameter_mid32.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'groups':summary,'active_latent_std':std,'identities_equal':True,'source_unchanged':True},indent=2))
