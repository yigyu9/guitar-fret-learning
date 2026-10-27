"""Per-episode deterministic evaluation and native replay reproducibility."""
from pathlib import Path
import json,gzip,hashlib
import numpy as np
BASE=Path(__file__).resolve().parent

def read(path):
 with (gzip.open(path,'rt') if path.suffix=='.gz' else path.open()) as stream:return json.load(stream)
rows=[]
for mode in ['before','after']:
 folder=BASE/('eval_'+mode+'_v1');contract=read(folder/'training_contract.json');target=contract['task']['targets'][0]
 signatures=[]
 for episode in sorted(folder.glob('episode_*')):
  prepared=read(episode/'prepared.json');measure=prepared['music'];key=target['target_id'];best=None;minimum=float('inf');min_audible=None
  native_hash=hashlib.sha256();action_peak=0.;pick_min=float('inf');sumreward=0.;sumcost=0.
  for path in sorted(episode.glob('transition_*.json.gz')):
   row=read(path);info=row['info'];sumreward+=row['reward'];sumcost+=info['cost'];action_peak=max(action_peak,float(np.abs(row['action']).max()))
   for sample,metric in zip(info['native_control']['physics_samples240'],info['physics_measurements']):
    music=metric['music'];t=music['task_time_s'];geometry=music['geometry'][key];distance=float(np.linalg.norm(geometry['delta']))
    native_hash.update(json.dumps(dict(native=sample['native'],action=row['action'],music=music),sort_keys=True,allow_nan=False,separators=(',',':')).encode())
    error=abs(t-target['onset_s'])
    if best is None or error<best[0]:best=(error,t,distance)
    minimum=min(minimum,distance);pick_min=min(pick_min,float(np.linalg.norm(geometry['pick_delta'])))
    if target['onset_s']<=t<target['end_s']:min_audible=distance if min_audible is None else min(min_audible,distance)
  summary=read(episode/'summary.json');assert np.isclose(sumreward,summary['reward'],rtol=0,atol=1e-12);assert np.isclose(sumcost,summary['cost'],rtol=0,atol=1e-12)
  signature=native_hash.hexdigest();signatures.append(signature)
  rows.append(dict(mode=mode,episode=episode.name,summary=summary,native_action_music_sha256=signature,
    initial_proxy_distance_m=float(np.linalg.norm(measure['geometry'][key]['delta'])),
    onset_proxy_distance_m=best[2] if best[0]<=1/240 else None,onset_nearest_physics_time_s=best[1],onset_sampling_error_s=best[0],
    min_proxy_distance_m=minimum,min_audible_proxy_distance_m=min_audible,min_pick_to_selected_string_zone_point_m=pick_min,
    max_normalized_action=action_peak))
 rows[-1]['two_episode_native_action_music_exact']=len(set(signatures))==1
result=dict(episodes=rows,scope='One seed, two deterministic native episodes per checkpoint; marker distances do not certify contact or sound')
with (BASE/'policy_comparison.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps(rows,indent=2))
