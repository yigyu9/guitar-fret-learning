"""Additional read-only reward counter observer; original CLI/strict loader unchanged."""
if not __debug__:raise RuntimeError('optimization disabled required')
import isaacgym
import sys,os,json,gzip,runpy,hashlib
from pathlib import Path
import torch
R=next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file());sys.path.insert(0,str(R))
from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.training.training_log_io import dumps
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
original=TensorSongEnvironment.end_control
original_components=FingerSkillEnvironment._reward_components
out=Path(sys.argv[sys.argv.index('--out')+1]).resolve();out.mkdir(parents=True,exist_ok=False)
# CLI owns the evaluation directory; observer writes to an explicitly separate sibling.
out.rmdir();trace=out.with_name(out.name+'_reward60.jsonl.gz');stream=gzip.open(trace,'xt',encoding='utf-8')
def observed_components(self,*args,**kwargs):
 result=original_components(self,*args,**kwargs)
 self._log_analysis_terms={k:v.clone() for k,v in result.items()}
 return result
def observed(self,*args,**kwargs):
 before={k:v.clone() for k,v in self.episode_reward_terms.items()};episode_ids=self.trace_episode_ids().clone() if hasattr(self,'trace_episode_ids') else torch.zeros(self.N,dtype=torch.long,device=self.device)
 result=original(self,*args,**kwargs)
 counter_delta={k:(self.episode_reward_terms[k]-v).detach().cpu().tolist() for k,v in before.items()}
 terms={k:v.detach().cpu().tolist() for k,v in self._log_analysis_terms.items()}
 del self._log_analysis_terms
 stream.write(dumps(dict(schema='readonly.reward_counter_delta.v1',end_s=self._local_time().cpu().tolist(),episode_ids=episode_ids.cpu().tolist(),reward_terms=terms,counter_delta=counter_delta,returned_reward=result[1].cpu().tolist(),cost=result[2].cpu().tolist(),terminated=result[3].cpu().tolist(),truncated=result[4].cpu().tolist()),allow_nan=False)+'\n')
 return result
TensorSongEnvironment.end_control=observed
FingerSkillEnvironment._reward_components=observed_components
try:
 target=R/'docs/2026-11-02/손가락전환실험/도구/runtime.py';sys.argv=[str(target)]+sys.argv[1:];runpy.run_path(str(target),run_name='__main__')
finally:
 TensorSongEnvironment.end_control=original;FingerSkillEnvironment._reward_components=original_components;stream.close()
