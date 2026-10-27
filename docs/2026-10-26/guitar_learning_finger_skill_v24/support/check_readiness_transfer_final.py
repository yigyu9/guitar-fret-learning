"""Native readiness metadata publication and explicit actor-only R-to-F smoke."""
from pathlib import Path
import sys
sys.path.insert(0, '/home/ajou/yigyu/3')
import isaacgym
import json
import numpy as np
import torch
from guitar_learning.training.finger_skill_runner import evaluate_checkpoint, _train_phase, phase_budgets
from guitar_learning.training.finger_skill_curriculum import FingerSkillCurriculum

root=Path(__file__).resolve().parents[1]
source=root/'support_R_final/R/final.pt'
a=torch.load(source,map_location='cpu',weights_only=False)
config=a['metadata']['curriculum']['config']
coordinator=FingerSkillCurriculum(config['initial_phase'],budgets=config['budgets'],thresholds=config['thresholds'])
coordinator.load_state_dict(a['metadata']['curriculum'])
report,rows=evaluate_checkpoint(source,root/'support_R_readiness_final',num_envs=4,scope='phrases',curriculum=coordinator)
b=torch.load(report['readiness_checkpoint'],map_location='cpu',weights_only=False)

def equal(left,right):
    if isinstance(left,torch.Tensor):return torch.equal(left,right)
    if isinstance(left,np.ndarray):return np.array_equal(left,right)
    if isinstance(left,dict):return left.keys()==right.keys() and all(equal(left[k],right[k]) for k in left)
    if isinstance(left,(tuple,list)):return len(left)==len(right) and all(equal(x,y) for x,y in zip(left,right))
    return left==right

preserved={key:bool(equal(a[key],b[key])) for key in ('identity','model','actor_optimizer','value_optimizer','torch_rng','numpy_rng','python_rng','cuda_rng','updates','cost_weight')}
assert all(preserved.values()),preserved
assert equal(a['metadata']['sampler'],b['metadata']['sampler'])
assert b['metadata']['curriculum']['evaluation_transitions']['R']>a['metadata']['curriculum']['evaluation_transitions']['R']
settings=json.loads((source.parent/'settings.json').read_text())
settings['num_envs']=4
settings['finger_skill'].update(phase='F',scope='phrases',hold_ticks=3)
settings['updates']=1
manual=FingerSkillCurriculum('F',budgets=phase_budgets(settings))
result=_train_phase(settings,root/'phase_transfer_F_final',manual,transfer=source,updates=1)
c=torch.load(root/'phase_transfer_F_final/initial.pt',map_location='cpu',weights_only=False)
d=torch.load(root/'phase_transfer_F_final/final.pt',map_location='cpu',weights_only=False)
actor_keys=[key for key in a['model'] if key.startswith(('support_encoder.','support_head.','finger_encoder.','finger_heads.')) or key in ('support_log_std','finger_log_std')]
assert all(torch.equal(a['model'][key],c['model'][key]) for key in actor_keys)
support=[key for key in actor_keys if key.startswith(('support_encoder.','support_head.')) or key=='support_log_std']
assert all(torch.equal(c['model'][key],d['model'][key]) for key in support)
assert not c['actor_optimizer']['state'] and not c['value_optimizer']['state']
output=dict(completed=report['completed'] and result['report']['completed'],readiness=report['readiness'],
    readiness_preserves_training_state=preserved,training_sampler_preserved=True,R_to_F_actor_exact=True,
    F_support_frozen=True,fresh_optimizers=True,
    transfer_scope='explicit diagnostic handoff; not an automatic readiness override')
(root/'support/final_readiness_transfer_verification.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output),flush=True)
