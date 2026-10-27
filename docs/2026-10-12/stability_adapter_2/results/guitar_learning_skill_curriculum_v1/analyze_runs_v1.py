"""Only closed committed runs; endpoint statistics explicitly sampled at60Hz."""
import gzip,json
from pathlib import Path
import numpy as np
from guitar_learning.recording import digest,write
P=Path(__file__).resolve().parent

def main():
 pinned={str(Path(__file__)):digest(__file__)};runs={}
 for role in ('left','right'):
  for cost in ('1p0','0p1'):
   name=role+'_cost'+cost+'_run_v2';p=P/name
   paths=[p/n for n in ('report.json','skill_report.json','transitions.jsonl.gz','persistent_audit.json','final.pt')]+sorted(p.glob('update_*.json'))
   for f in paths:pinned[str(f)]=digest(f)
   report=json.loads((p/'report.json').read_text());skill=json.loads((p/'skill_report.json').read_text())
   if not report['completed'] or not report['persistent_audit']['completed']:raise RuntimeError('unfinished/invalid run '+name)
   updates={};episodes=[];count=0
   with gzip.open(p/'transitions.jsonl.gz','rt') as stream:
    for line_index,line in enumerate(stream):
     r=json.loads(line);u=line_index//report['settings']['horizon'];entry=updates.setdefault(u,dict(reward=[],cost=[],marker_mm=[],guide_mm=[],guitar_mm=[],feet_mm=[],flags=[],episodes=[],action_rms=[]))
     for reward,info in zip(r['reward'],r['infos']):
      count+=1;s=info['stability'];entry['reward'].append(reward);entry['cost'].append(info['cost'])
      entry['marker_mm'].extend(v*1000 for v in info['goal_distance_m'].values())
      if 'pick_guide' in info:entry['guide_mm'].append(info['pick_guide']['distance_m']*1000)
      entry['guitar_mm'].append(float(np.linalg.norm(s['guitar_delta_m'])*1000));entry['feet_mm'].append(float(np.max(np.linalg.norm(s['foot_delta_m'],axis=1))*1000));entry['flags'].append(s['flags'])
      action=np.array(info['debug']['action']);entry['action_rms'].append(float(np.sqrt(np.mean((action[:33] if role=='left' else action[33:])**2))))
      if 'episode' in info:entry['episodes'].append(info['episode']);episodes.append(info['episode'])
   if count!=report['transitions']:raise RuntimeError('log mismatch '+name)
   summarized=[]
   for u,entry in sorted(updates.items()):
    ep=entry['episodes'];flags=np.array(entry['flags'])
    summarized.append(dict(update=u+1,transitions=len(entry['reward']),episodes=len(ep),successes=sum(x['specialist']['stage_success'] for x in ep),failures=sum(x['reason']=='terminal_failure' for x in ep),
     mean_episode_return=float(np.mean([x['reward'] for x in ep])) if ep else None,mean_episode_cost=float(np.mean([x['cost'] for x in ep])) if ep else None,
     mean_marker_mm=float(np.mean(entry['marker_mm'])),mean_guide_mm=float(np.mean(entry['guide_mm'])) if entry['guide_mm'] else None,
     max_guitar_mm60=float(max(entry['guitar_mm'])),mean_guitar_mm60=float(np.mean(entry['guitar_mm'])),max_foot_mm60=float(max(entry['feet_mm'])),
     all_support_presence60=float(np.mean(flags[:,:3].any(axis=1))),both_feet_presence60=float(np.mean(flags[:,-2:].all(axis=1))),triple_support_presence60=float(np.mean(flags[:,:3].all(axis=1))),
     mean_action_rms=float(np.mean(entry['action_rms']))))
   runs[name]=dict(completed=True,role=role,skill=report['settings']['skill'],cost_weight=report['settings']['ppo']['cost_weight'],updates=len(report['updates']),transitions=count,episodes=len(episodes),
    successes=skill['successful_episodes'],physical_failures=skill['physical_failure_episodes'],wall_s=report['wall_s'],
    music_matched50=sum(e['music']['matched50'] for e in episodes),max_guitar_mm60=max(x['max_guitar_mm60'] for x in summarized),
    mean_episode_return=float(np.mean([x['reward'] for x in episodes])),mean_episode_cost=float(np.mean([x['cost'] for x in episodes])),
    update_series=summarized,changed_inputs=report['changed_inputs'],minimum_available_memory_gib=report['resource_monitor']['min_available_memory_bytes']/2**30 if 'min_available_memory_bytes' in report['resource_monitor'] else None)
 write(P/'learning_comparison_v1.json',dict(runs=runs,inputs=pinned,inputs_unchanged=all(digest(p)==sha for p,sha in pinned.items()),
  scope='single seed current-goal preparation pilot; cost is sole between-pair setting;60Hz maxima are not240Hz maxima; reach/ready are not actual contact/strike'))
 print(json.dumps({k:{a:v[a] for a in ('updates','transitions','episodes','successes','physical_failures','mean_episode_return','mean_episode_cost','max_guitar_mm60')} for k,v in runs.items()}))

if __name__=='__main__':main()
