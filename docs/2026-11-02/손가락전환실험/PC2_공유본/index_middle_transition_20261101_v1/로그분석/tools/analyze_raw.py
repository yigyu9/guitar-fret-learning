if not __debug__:raise RuntimeError('optimization disabled required')
from pathlib import Path
import sys,json,gzip,math,collections,csv,hashlib
import numpy as np
L=Path(__file__).resolve().parents[1];D=L.parent;R=next(p for p in D.parents if (p/'scripts/tab2body.py').exists());sys.path.insert(0,str(R))
from guitar_learning.training.training_log_io import iter_episode_rows
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PHASES={'prepare':(0,3),'A':(3,4.5),'gap':(4.5,5.25),'B':(5.25,6.75),'tail':(6.75,7.25)}
def phase(t):return next((n for n,(a,b) in PHASES.items() if a-1e-8<=t<b-1e-8),'tail')
def simultaneous(t,ca,wrong,raw):
 effective=[c and not w for c,w in zip(ca,wrong)];audible=[3<=t<4.5,5.25<=t<6.75]
 return {'raw_dual':all(raw),'effective_dual':all(effective),'audible_dual':all(c and a for c,a in zip(effective,audible)), 'A_audible_B_raw_A_effective':audible[0] and raw[1] and effective[0], 'B_audible_A_lower_raw':audible[1] and raw[0] and effective[1]}
def stats(x):
 x=[float(v) for v in x if v is not None and math.isfinite(v)];return dict(count=len(x),mean=float(np.mean(x)),min=min(x),max=max(x),p05=float(np.quantile(x,.05)),p95=float(np.quantile(x,.95))) if x else dict(count=0)

def main():
 result={};sources={};events=[];source_rows=[];timeline=[]
 folders=[p.parent for p in (D/'진단').glob('*/report.json') if (p.parent/'action_mode.json').exists() and not p.parent.name.startswith('smoke')]
 folders += [p.parent for p in (L/'runs').glob('*/report.json')] if (L/'runs').exists() else []
 for path in sorted(folders):
  report=json.loads((path/'report.json').read_text());assert report['completed'] and report['first_episode_per_env_per_batch'] and report['failed_episodes_in_denominator'];assert not any(report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'))
  n=report['episodes'];eps=[x['episode'] for x in iter_episode_rows(path)];assert len(eps)==n and {e['env_id'] for e in eps}==set(range(n));eps.sort(key=lambda x:x['env_id']);ids=[e['finger_control_diagnostics']['episode_id'] for e in eps];name=path.name
  reward_groups={};outcomes=collections.Counter()
  for e in eps:
   vals=e['left_note_ledger']['values'];safe=not(e['termination']['physical_failure'] or e['termination']['wrist_failure']);ab=all(vals['left']) and safe;outcomes['safe_AB']+=ab;outcomes['physical_failure']+=e['termination']['physical_failure'];outcomes['wrist_failure']+=e['termination']['wrist_failure'];outcomes['whole_pair']+=safe and all(v>=1.5-1e-8 for v in vals['clean'])
   group='AB_success' if ab else 'AB_failure';reward_groups.setdefault(group,[]).append(e['reward_components'])
   w=e['left_note_ledger']['wrong_press_sources'];wv=w['values']
   for j in range(2):
    for body_index,body in enumerate(w['body_names']):
     for ci,cause in enumerate(w['contract']['causes']):
      dur=wv['wrong_source_time'][j][body_index][ci]
      if dur>0:source_rows.append(dict(condition=name,env_id=e['env_id'],phase='A' if j==0 else 'B',body=body,cause=cause,target_string=3,target_fret=4 if j==0 else 6,body_all_causes_fret_min=wv['wrong_source_fret_min'][j][body_index],body_all_causes_fret_max=wv['wrong_source_fret_max'][j][body_index],duration_s=dur,source_string='not logged'))
  counts={p:collections.Counter() for p in PHASES};geom={p:collections.defaultdict(list) for p in PHASES};tseries=[]
  with gzip.open(path/'finger_control_trace.jsonl.gz','rt') as stream:
   for line in stream:
    row=json.loads(line);ex=row['natural_preparation']['transition']
    for i in range(n):
     if ex['all_env_episode_ids'][i]!=ids[i]:continue
     t=ex['all_env_episode_time_s'][i];ph=phase(t);co=counts[ph];co['observed_env_endpoints']+=1;du=simultaneous(t,ex['all_env_candidate'][i],ex['all_env_wrong'][i],ex['all_env_raw_candidate'][i]);co.update({k:int(v) for k,v in du.items()})
     for j in (0,1):
      co[f'goal{j}_raw']+=ex['all_env_raw_candidate'][i][j];co[f'goal{j}_effective']+=ex['all_env_candidate'][i][j] and not ex['all_env_wrong'][i][j];co[f'goal{j}_wrong']+=ex['all_env_wrong'][i][j];co[f'goal{j}_position']+=ex['all_env_position_geometry'][i][j];co[f'goal{j}_facing']+=ex['all_env_facing_geometry'][i][j];co[f'goal{j}_loaded']+=ex['all_env_assigned_loaded'][i][j]
    if row['env_id']!=0 or row['episode_id']!=ids[0]:continue
    t=row['episode_time_s'];ph=phase(t);g=geom[ph];f=row['natural_preparation']['fingers'][1];wrist=ex['wrist_error_m'];g['wrist_max_abs_mm'].append(max(abs(x) for x in wrist)*1000)
    for key in ('height_m','lateral_error_m','along_cell_excess_m','normal_cos','standby_weight','observed_standby_gate','standby_rate_per_s','tracking_weight','sample_index'):
     if key in f:g[key].append(f[key])
    idx=[i for i,j in enumerate(row['joint_names']) if j.startswith('LH:middle')];assert len(idx)==4
    rec={'condition':name,'t':t,'phase':ph,'wrist_mm':max(abs(x) for x in wrist)*1000,'height_mm':f.get('height_m',float('nan'))*1000,'lateral_mm':f.get('lateral_error_m',float('nan'))*1000,'fret_excess_mm':f.get('along_cell_excess_m',float('nan'))*1000,'normal_cos':f.get('normal_cos',float('nan')),'sample_index':f.get('sample_index',-1),'B_raw':ex['all_env_raw_candidate'][0][1],'B_effective':ex['all_env_candidate'][0][1] and not ex['all_env_wrong'][0][1], 'B_clean_streak_s':ex['goals'][1]['clean_streak_s'],'B_wrong':ex['all_env_wrong'][0][1],'B_loaded':ex['all_env_assigned_loaded'][0][1],'B_position':ex['all_env_position_geometry'][0][1],'B_facing':ex['all_env_facing_geometry'][0][1],'standby_weight':f.get('standby_weight',float('nan')),'standby_rate':f.get('standby_rate_per_s',float('nan'))}
    for field,tag in (('requested_target_rad','requested'),('applied_target_rad','applied'),('actual_rad','actual')):
     for j,i in enumerate(idx):rec[f'{tag}_{j}_deg']=row[field][i]*180/math.pi;g[f'{tag}_{j}_deg'].append(rec[f'{tag}_{j}_deg'])
    tseries.append(rec)
  note_summary=[]
  for j in (0,1):note_summary.append({'achievement':sum(bool(e['left_note_ledger']['values']['left'][j]) for e in eps),'contact':sum(bool(e['left_note_ledger']['values']['contact_done'][j]) for e in eps),'mean_clean_s':sum(e['left_note_ledger']['values']['clean'][j] for e in eps)/n,'mean_best_streak_s':sum(e['left_note_ledger']['values']['best_clean_streak'][j] for e in eps)/n})
  entry={'n':n,'outcomes':dict(outcomes),'notes':note_summary,'reward_group_means':{k:{term:sum(v[term] for v in rs)/len(rs) for term in rs[0]} for k,rs in reward_groups.items()},'reward_group_counts':{k:len(v) for k,v in reward_groups.items()},'phase_all_env_endpoints':{p:dict(c) for p,c in counts.items()},'phase_env0_geometry_and_angles':{p:{k:stats(v) for k,v in g.items()} for p,g in geom.items()},'identity':{'checkpoint_sha256':report['checkpoint_sha256'],'settings':report['settings']},'scope':'geometry/phase joint detail env0 only; all-env counters retain failed first episodes; wrong body sources are audible integrated ledger not time-resolved source strings'}
  result[name]=entry
  if tseries:
   with (L/'tables'/f'{name}_env0_timeline.csv').open('w') as out:w=csv.DictWriter(out,fieldnames=list(tseries[0]));w.writeheader();w.writerows(tseries)
  for p in (path/'report.json',path/'episodes.jsonl',path/'episode_metadata.json',path/'finger_control_trace.jsonl.gz'):sources[str(p)]=sha(p)
  print('read',name,flush=True)
 (L/'analysis_ledger.json').write_text(json.dumps({'schema':'raw.analysis.v1','evaluations':result,'source_sha256':sources,'analysis_sha256':sha(Path(__file__))},ensure_ascii=False,indent=2,allow_nan=False))
 with (L/'tables/wrong_sources.csv').open('w') as f:
  if source_rows:w=csv.DictWriter(f,fieldnames=list(source_rows[0]));w.writeheader();w.writerows(source_rows)
if __name__=='__main__':main()
