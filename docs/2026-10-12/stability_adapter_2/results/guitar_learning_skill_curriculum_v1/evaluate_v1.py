"""Deterministic same-goal native policy evaluation, separate from PPO samples."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[name]='1'
import isaacgym
import argparse,json,gzip,sys
from pathlib import Path
import numpy as np
import torch
from guitar_learning.skill_environment_v2 import build_skill_environment
from guitar_learning.specialist_policy import SpecialistPolicy
from guitar_learning.ppo import PPOTrainer,PPOConfig
from guitar_learning.recording import write,digest,project_source_paths
from guitar_learning.parallel import FIELDS
from guitar_learning.specialist_parallel import specialist_compact

ROOT=Path('/home/ajou/yigyu/3')
CONFIG=ROOT/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json'
BUNDLE=ROOT/'data/song_bundles/05_BN2-131-B_solo'

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--episodes',type=int,default=2);a=p.parse_args()
 a.out.mkdir(parents=True,exist_ok=False)
 settings=json.loads((a.run/'settings.json').read_text());checkpoint=a.run/'final.pt'
 payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
 paths={str(checkpoint.resolve()),str((a.run/'settings.json').resolve()),str(Path(__file__).resolve()),str(CONFIG)}|project_source_paths(list(sys.modules.items()))
 pinned={x:digest(x) for x in sorted(paths)};write(a.out/'inputs.json',pinned)
 env=build_skill_environment(CONFIG,a.out/'environment',role=settings['specialist']['role'],skill=settings['skill'],bundle=BUNDLE)
 episodes=[];rows=[]
 try:
  for episode in range(a.episodes):
   observation,reset=env.reset();write(a.out/('reset_%02d.json'%episode),reset)
   if episode==0:
    arch=payload['identity']['architecture'];model=SpecialistPolicy(len(observation['state']),size=arch['size'],role=arch['role'],frozen_partner=arch['frozen_partner'],contract=env.contract).to('cuda:0')
    trainer=PPOTrainer(model,PPOConfig(**payload['identity']['config']));trainer.load(checkpoint);model.eval()
   if env.contract!=model.architecture['contract']:raise RuntimeError('evaluation contract changed')
   for tick in range(240):
    inputs=[torch.as_tensor(observation[k],device='cuda:0').unsqueeze(0) for k in FIELDS]
    with torch.no_grad():action=model.act(*inputs,deterministic=True)['action'][0].cpu().numpy()
    observation,reward,done,truncated,info=env.step(action)
    rows.append(dict(episode=episode,tick=tick,reward=reward,info=specialist_compact(env,info,action)))
    if done or truncated:
     episodes.append(info['episode']);break
  write(a.out/'transitions.json.gz',rows,compressed=True)
  write(a.out/'result.json',dict(completed=len(episodes)==a.episodes,role=settings['specialist']['role'],skill=settings['skill'],cost_weight=settings['ppo']['cost_weight'],episodes=episodes,
    source_unchanged=all(digest(x)==sha for x,sha in pinned.items()),scope='deterministic current goal only; same prepared start, repeated persistent reset, not unseen-song generalization'))
 finally:env.close()

if __name__=='__main__':main()
