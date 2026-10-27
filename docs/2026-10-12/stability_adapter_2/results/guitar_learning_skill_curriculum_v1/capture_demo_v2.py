"""Replay bounded teacher actions and record real505D policy input/action pairs."""
import os
for n in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='1'
import isaacgym
import argparse,gzip,json,sys
from pathlib import Path
import numpy as np
from guitar_learning.skill_environment_v2 import build_skill_environment
from guitar_learning.recording import write,digest
from guitar_learning.prepared_reset_v1 import prepared_input_paths
from guitar_learning.parallel import FIELDS
ROOT=Path('/home/ajou/yigyu/3')
CONFIG=ROOT/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json'
BUNDLE=ROOT/'data/song_bundles/05_BN2-131-B_solo'

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--role',choices=('left','right'),required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 source=a.source/'trace.json.gz'; teacher=json.loads(gzip.decompress(source.read_bytes()))
 paths={Path(__file__).resolve(),source.resolve(),CONFIG}|{x for x in (ROOT/'guitar_learning').glob('*.py')}|{x for x in (ROOT/'stability_adapter_2').rglob('*.py')}
 paths|=prepared_input_paths()
 pinned={str(p):digest(p) for p in sorted(paths)};write(a.out/'inputs_before.json',pinned)
 env=build_skill_environment(CONFIG,a.out/'environment',role=a.role,skill='hold' if a.role=='left' else 'cross',bundle=BUNDLE)
 arrays={k:[] for k in FIELDS};arrays['action']=[];samples=[]
 try:
  obs,reset=env.reset();write(a.out/'reset.json',reset)
  for tick,row in enumerate(teacher):
   for k in FIELDS:arrays[k].append(np.array(obs[k],copy=True))
   action=np.array(row['action'],dtype=float);arrays['action'].append(action)
   obs,reward,done,truncated,info=env.step(action)
   samples.append(dict(tick=tick,action=action,reward=reward,cost=info['cost'],specialist=info['specialist'],music=info['music'],
    samples240=info['native_control']['physics_samples240'],measurements=info['physics_measurements']))
   if done or truncated:break
  np.savez_compressed(a.out/'demonstration.npz',**{k:np.stack(v) for k,v in arrays.items()})
  write(a.out/'trace.json.gz',samples,compressed=True)
  write(a.out/'result.json',dict(role=a.role,ticks=len(samples),success=info['specialist']['stage_success'],episode=info.get('episode'),
   source_unchanged=all(digest(p)==sha for p,sha in pinned.items()),observation_dimension=len(arrays['state'][0]),
   dataset_fields={k:dict(shape=list(np.stack(v).shape),dtype=str(np.stack(v).dtype)) for k,v in arrays.items()},
   scope='scripted trajectory replay in real v2physics, not a learned policy; native success independently measured; input/action dataset for future initialization'))
 finally:env.close()

if __name__=='__main__':main()
