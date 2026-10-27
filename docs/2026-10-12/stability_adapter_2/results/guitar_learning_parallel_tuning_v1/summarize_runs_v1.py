"""Read-only summaries of completed bounded native trials; compact safety at60Hz."""
from pathlib import Path
import json,gzip,math,statistics,hashlib,argparse
base=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=base/'run_summary.json');args=parser.parse_args()
pins={}
def read(path):
 pins[str(path.resolve())]=hashlib.sha256(path.read_bytes()).hexdigest()
 return json.loads(path.read_text())
rows=[]
for path in sorted(base.glob('*/report.json')):
 d=read(path)
 if 'collection_transitions_per_s' not in d:continue
 samples=[];ends=[];onsets=[];failures={};music_max={};candidates=0;total=0;max_guitar=0.;max_speed=0.
 raw=path.parent/'transitions.jsonl.gz';pins[str(raw.resolve())]=hashlib.sha256(raw.read_bytes()).hexdigest()
 with gzip.open(raw,'rt') as stream:
  for line in stream:
   step=json.loads(line)
   for i,info in enumerate(step['infos']):
    total+=1
    candidates+=any(info.get('fret_candidates',{}).values())
    safety=info.get('stability',{})
    max_guitar=max(max_guitar,math.sqrt(sum(x*x for x in safety.get('guitar_delta_m',[]))))
    max_speed=max(max_speed,safety.get('max_joint_speed_rad_s',0.))
    for key,value in info.get('music',{}).items():
     if isinstance(value,(int,float)):music_max[key]=max(music_max.get(key,0.),value)
    for key in info.get('failure_reasons',[]):failures[key]=failures.get(key,0)+1
    distances=list(info.get('goal_distance_m',{}).values())
    if distances:
     samples.extend(distances)
     if abs(info.get('task_time_s',-10)-1.12)<=.05:onsets.extend(distances)
    if step['terminated'][i] or step['truncated'][i]:ends.append(info.get('music',{}))
 episodes=[e for update in d['updates'] for e in update['completed_episodes']]
 row=dict(run=path.parent.name,completed=d['completed'],num_envs=d['settings']['num_envs'],horizon=d['settings']['horizon'],device=d['settings']['device'],initial_std=d['settings']['initial_std'],ppo=d['settings']['ppo'],updates=len(d['updates']),transitions=d['transitions'],collection_tps=d['collection_transitions_per_s'],wall_s=d['wall_s'],timers=d['timers'],resources=d['resources'],episode_count=len(episodes),failure_episodes=sum(e['reason']=='terminal_failure' for e in episodes),mean_episode_reward=statistics.mean(e['reward'] for e in episodes) if episodes else None,mean_episode_cost=statistics.mean(e['cost'] for e in episodes) if episodes else None,completed_music=dict(matched50=sum(e.get('matched50',0) for e in ends),matched100=sum(e.get('matched100',0) for e in ends),target_count=sum(e.get('target_count',0) for e in ends),held_total_s=sum(e.get('held_total_s',0.) for e in ends),wrong_crossings=sum(e.get('wrong_crossings',0) for e in ends)),partial_music_max=music_max,compact_fret_candidate_fraction=candidates/total if total else None,compact_goal_distance_min_m=min(samples) if samples else None,compact_goal_distance_mean_m=statistics.mean(samples) if samples else None,onset_window_distance_mean_m=statistics.mean(onsets) if onsets else None,compact_max_guitar_delta_m=max_guitar,compact_max_joint_speed_rad_s=max_speed,failure_reasons=failures,max_kl=max((u['analytic_kl'] for u in d['updates']),default=0),kl_retries=sum(u['kl_retries'] for u in d['updates']),actor_lrs=[u['actor_lr'] for u in d['updates']])
 rows.append(row)
result=dict(rows=rows,scope='Measured collection includes inter-episode reset; wall includes initial reset/startup/update/shutdown. Compact distances/safety sampled atlastsubstep60Hz; failure detection itself240Hz. Onset window1.12+-0.05 applies only stageB firsttarget. No success inference from approach reward.',sha256=pins)
args.out.write_text(json.dumps(result,indent=2))
print(json.dumps([{k:r[k] for k in ('run','completed','collection_tps','episode_count','failure_episodes','mean_episode_reward','mean_episode_cost','completed_music','onset_window_distance_mean_m','max_kl','kl_retries')} for r in rows],indent=2))
