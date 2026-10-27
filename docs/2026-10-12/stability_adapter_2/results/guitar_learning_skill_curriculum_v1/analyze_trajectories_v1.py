"""Native240Hz teacher evidence, deliberately separate from learned policies."""
from pathlib import Path
import json,gzip
import numpy as np
from guitar_learning.recording import digest,write
P=Path(__file__).resolve().parent

def main():
 paths={str(Path(__file__)):digest(__file__)};trials={}
 for f in sorted(P.glob('*/result.json')):
  folder=f.parent
  if not (folder/'trace.json.gz').exists() or '_eval_' in folder.name:continue
  for path in (f,folder/'trace.json.gz',folder/'reset.json'):
   if path.exists():paths[str(path)]=digest(path)
  result=json.loads(f.read_text());trace=json.loads(gzip.decompress((folder/'trace.json.gz').read_bytes()));states=[];cross=[];flags=[];guitar=[];foot=[];marker=[];valid=[];candidate=0
  for row in trace:
   for sample,measurement in zip(row['samples240'],row['measurements']):
    s=measurement['stability'];m=measurement['music'];states.append(sample['native']['physics_step']);cross.extend(m['crossings']);flags.append(s['flags']);guitar.append(float(np.linalg.norm(s['guitar_delta_m'])*1000));foot.append(float(np.max(np.linalg.norm(s['foot_delta_m'],axis=1))*1000));marker.extend(float(np.linalg.norm(v['delta'])*1000) for v in m['geometry'].values())
    for t in m['targets'].values():
     candidate+=int(t['candidate']);valid.extend(x for x in t['evidence']['contact_evidence'] if x['valid'])
  a=np.array([r['action'] for r in trace]);role='left' if folder.name.startswith('left') else 'right';flag=np.array(flags);last=trace[-1]['specialist']
  trials[folder.name]=dict(role=role,ticks=len(trace),physics_samples=len(states),consecutive_physics=bool(np.all(np.diff(states)==1)),policy_time_s=len(states)/240.,
   success=last['stage_success'],skill=last['skill'],source_unchanged=result['source_unchanged'],
   inactive_action_max=float(np.max(abs(a[:,33:] if role=='left' else a[:,:33]))),active_action_max=float(np.max(abs(a[:,:33] if role=='left' else a[:,33:]))),
   max_guitar_mm240=max(guitar),max_foot_mm240=max(foot),minimum_distal_origin_mm240=min(marker),
   all_support_presence240=float(np.mean(flag[:,:3].any(axis=1))),both_feet_presence240=float(np.mean(flag[:,-2:].all(axis=1))),triple_support_presence240=float(np.mean(flag[:,:3].all(axis=1))),
   candidate_samples=candidate,valid_fret_evidence=len(valid),valid_fret_lateral_mm_max=max((x['lateral_to_target_string_m']*1000 for x in valid),default=None),
   valid_fret_witness_mm_max=max((x['body_pair_witness_gap_m']*1000 for x in valid),default=None),
   crossings=cross,physical_failure=bool(last['safety_invalidated']),original_music=trace[-1]['music'])
 write(P/'trajectory_analysis_v1.json',dict(trials=trials,inputs=paths,inputs_unchanged=all(digest(p)==s for p,s in paths.items()),
  scope='scripted real native trajectories with unchanged contact/cross eligibility, not learned policies or acoustic performance; per-probe source_unchanged covers explicit pin list only'))
 print(json.dumps({k:{n:v[n] for n in ('success','candidate_samples','max_guitar_mm240','minimum_distal_origin_mm240')} for k,v in trials.items()}))

if __name__=='__main__':main()
