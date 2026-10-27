"""Native actor-only F to J transition at a committed run boundary."""
from pathlib import Path
import sys
sys.path.insert(0, '/home/ajou/yigyu/3')
import isaacgym
import json
import torch
from guitar_learning.training.finger_skill_runner import _train_phase, phase_budgets
from guitar_learning.training.finger_skill_curriculum import FingerSkillCurriculum

root = Path(__file__).resolve().parents[1]
source = root/'correlated_F3/F/final.pt'
settings = json.loads((source.parent/'settings.json').read_text())
settings['finger_skill'].update(phase='J', scope='full_song')
settings['updates'] = 1
curriculum = FingerSkillCurriculum('J', budgets=phase_budgets(settings))
result = _train_phase(settings, root/'phase_transfer_J', curriculum, transfer=source, updates=1)
a = torch.load(source, map_location='cpu', weights_only=False)
b = torch.load(root/'phase_transfer_J/initial.pt', map_location='cpu', weights_only=False)
keys = [k for k in a['model'] if k.startswith(('support_encoder.', 'support_head.', 'finger_encoder.', 'finger_heads.')) or k in ('support_log_std', 'finger_log_std')]
assert all(torch.equal(a['model'][k],b['model'][k]) for k in keys)
assert not b['actor_optimizer']['state'] and not b['value_optimizer']['state']
assert b['updates'] == 0
assert any(not torch.equal(a['model'][k], b['model'][k]) for k in a['model'] if k.startswith(('value_encoder.', 'reward_critic.', 'cost_critic.')))
report = dict(completed=result['report']['completed'], actors_exact=True, critics_fresh=True, optimizers_fresh=True, copied_actor_tensors=len(keys), scope=settings['finger_skill']['scope'])
(root/'support/phase_transfer_verification.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report), flush=True)
