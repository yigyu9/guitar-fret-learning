"""One planned coefficient-only comparison: full v21 with B0.04/s."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import isaacgym
from guitar_learning.tool.validation.hand_contact_comparison import install_ablation
from guitar_learning.training.start import settings_document,run
install_ablation('full')
s=settings_document('left',updates=100,num_envs=128,device='cuda:0',physics='gpu',size='large',seed=7,horizon=32,finger_standby_rate=.04)
s['song'].update(thumb_support_rate_per_s=.02,hand_contact_comparison='full')
s['comparison_launcher']=dict(path=str(Path(__file__).resolve()),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
run(s,SimpleNamespace(out=Path('/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_hand_contact_v21/train_full_B04_100'),resume=None))
