if not __debug__:raise RuntimeError('optimization disabled required')
from pathlib import Path
import sys,json,hashlib,gzip,math
import numpy as np,torch
L=Path(__file__).resolve().parents[1];D=L.parent;R=next(p for p in L.parents if (p/'scripts/tab2body.py').exists());sys.path.insert(0,str(R));torch.set_num_threads(1)
from guitar_learning.training.finger_skill_runner import _validate_pins
from guitar_learning.portability import localize
from guitar_learning.training.ppo import PPOConfig
import importlib.util
spec=importlib.util.spec_from_file_location('sealed_runtime',D/'도구/runtime.py');rt=importlib.util.module_from_spec(spec);spec.loader.exec_module(rt)
out={};series={}
for seed in (7,17):
 rows=[]
 for u in (100,200,300):
  ck=D/f'모델/base_seed{seed}_u{u}/J/final.pt';payload=torch.load(ck,map_location='cpu',weights_only=False);_validate_pins(payload['metadata']);arch=localize(payload['identity']['architecture']);m=rt.TransitionPolicy(arch['state_dim'],size=arch['size'],contract=arch['contract'],natural_press=arch['natural_press'],transition=arch['transition']);trainer=rt.natural.NaturalTrainer(m,PPOConfig(**payload['identity']['config']));assert trainer._identity()==payload['identity'],'identity mismatch';m.load_state_dict(payload['model'],strict=True)
  std=torch.cat((m.core.support_log_std[:12].clamp(-5,2).exp(),m.core.finger_log_std[:8].clamp(min=math.log(.10),max=2).exp())).detach().tolist()
  metrics=[json.loads(x) for x in (ck.parent/'learning_metrics.jsonl').read_text().splitlines()];rows+=metrics
  key=f's{seed}_u{u}';out[key]={'checkpoint_sha256':hashlib.sha256(ck.read_bytes()).hexdigest(),'identity_exact':True,'active_axis_names':list(rt.natural.ACTIVE_NAMES[:12])+list(rt.natural.ACTIVE_NAMES[17:25]),'std_latent_by_axis':std,'training_updates_in_block':len(metrics),'first':metrics[0],'last':metrics[-1]}
  # E[requested q] vs q(tanh(mu)) at same deterministic recorded observation; not E[physical q].
  catalog,_=rt.natural.catalog_goal(arch['natural_press']);ix=np.array(catalog['action_indices']);ref=np.array(catalog['reference105'])[ix];lo=np.array(catalog['action_lower']);hi=np.array(catalog['action_upper']);nodes,w=np.polynomial.hermite.hermgauss(32);w=w/np.sqrt(np.pi);deltas=[];actions=[]
  with gzip.open(D/f'진단/base_seed{seed}_u{u}_mean/finger_control_trace.jsonl.gz','rt') as f:
   for line in f:
    v=json.loads(line)
    if not 5.25<=v['episode_time_s']<6.75:continue
    for j,name in enumerate(v['joint_names']):
     if not name.startswith('LH:middle'):continue
     ai=rt.natural.ACTIVE_NAMES.index(name);a=v['action'][j];mu=np.arctanh(np.clip(a,-.999999,.999999));sig=std[12+ai-17];aa=np.tanh(mu+np.sqrt(2)*sig*nodes);qq=ref[ai]+np.where(aa>=0,hi[ai]-ref[ai],ref[ai]-lo[ai])*aa;deltas.append(float((qq*w).sum()-v['requested_target_rad'][j]));actions.append(abs(a)>=.98)
  out[key]['B_env0_expected_requested_minus_mean_requested_deg']={'mean':float(np.mean(deltas)*180/np.pi),'max_abs':float(np.max(np.abs(deltas))*180/np.pi),'scope':'same latent mean,32-node integration across trained marginal std; no physical response expectation'};out[key]['B_env0_mean_action_saturation_fraction']=sum(actions)/len(actions)
 series[str(seed)]=rows
(L/'learning_ledger.json').write_text(json.dumps({'models':out,'series':series,'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2,allow_nan=False));print('six model identities verified; learning ledger written')
