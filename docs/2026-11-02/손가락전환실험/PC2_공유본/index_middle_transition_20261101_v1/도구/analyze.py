if not __debug__:raise RuntimeError('Scientific checks require Python optimization disabled')
import json,gzip,math,pathlib,hashlib
from guitar_learning.training.training_log_io import iter_episode_rows,dumps

def analyze(path):
 path=pathlib.Path(path);r=json.loads((path/'report.json').read_text());n=r['episodes'];assert n in (32,128)
 assert all(r.get(k)is True for k in ('completed','lifecycle_verified','first_episode_per_env_per_batch','failed_episodes_in_denominator'))
 assert not any(r.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'))
 rows=[x['episode'] for x in iter_episode_rows(path)];assert len(rows)==n and {x['env_id'] for x in rows}==set(range(n));rows.sort(key=lambda x:x['env_id']);cfg=r['settings']['transition'];schedule=cfg['schedule'];assert [(x['finger'],x['string_index'],x['fret']) for x in schedule]==[(1,2,4),(2,2,6)]
 notes=[]
 for j,t in enumerate(schedule):
  values=[x['left_note_ledger']['values'] for x in rows];first=[x['transition_diagnostics']['first_contact_s'][j] for x in rows]
  notes.append(dict(finger=t['finger'],fret=t['fret'],denominator=n,contact=sum(bool(x['contact_done'][j]) for x in values),achievement=sum(bool(x['left'][j]) for x in values),mean_clean_s=sum(x['clean'][j] for x in values)/n,mean_best_continuous_clean_s=sum(x['best_clean_streak'][j] for x in values)/n,whole_duration_count=sum(x['clean'][j]>=1.5-1e-8 for x in values),mean_wrong_s=sum(x['wrong'][j] for x in values)/n,mean_missing_s=sum(x['missing'][j] for x in values)/n,first_contact_s=first,onset_count=sum(x is not None and x-t['onset_s']<=1/240+1e-8 for x in first)))
 ids=[x['finger_control_diagnostics']['episode_id'] for x in rows];trace=[[] for _ in rows];duals=0
 with gzip.open(path/'finger_control_trace.jsonl.gz','rt') as stream:
  for line in stream:
   v=json.loads(line);extra=v['natural_preparation']['transition']
   assert len(extra['all_env_episode_ids'])==n
   for i in range(n):
    if extra['all_env_episode_ids'][i]!=ids[i]:continue
    ca=extra['all_env_candidate'][i];wr=extra['all_env_wrong'][i];raw=extra['all_env_raw_candidate'][i];assert len(ca)==len(wr)==len(raw)==2
    duals+=all(ca);trace[i].append((extra['all_env_episode_time_s'][i],ca,wr,raw))
 assert duals==0,'contradictory same-string effective simultaneous candidates'
 transitions=[]
 for i,points in enumerate(trace):
  assert points and points[0][0]<=.02 and points[-1][0]+1/240+1e-7>=rows[i]['task_time_s']
  assert all(abs((b[0]-a[0])-1/240)<2e-6 for a,b in zip(points,points[1:])), 'incomplete first episode trace'
  tail=[x for x in points if 4.45-1e-8<=x[0]<4.5-1e-8];start=next((x for x in points if x[0]>=5.25-1e-8),None)
  kept=len(tail)>=11 and all(x[1][0] and not x[2][0] for x in tail);onset=bool(start and start[0]-5.25<=1/240+1e-8 and start[1][1] and not start[2][1]);release=None;streak=0
  for x in points:
   if x[0]<4.5-1e-8:continue
   streak=streak+1 if not x[3][0] else 0
   if streak>=12:release=x[0]-11/240;break
  transitions.append(dict(env_id=i,previous_last50ms_clean=kept,next_on_time=onset,tail_and_onset=kept and onset,release_proxy_s=release,prior_raw_candidate_at_B_onset=start[3][0] if start else None,release_by_B_onset=bool(start and not start[3][0] and release is not None and release<=5.25),scope='release proxy=assigned loaded geometric pad absent for50ms after A end; no pair-pressure certification'))
 failures=sum(bool(x['termination']['physical_failure'] or x['termination']['wrist_failure']) for x in rows);safe=[not(x['termination']['physical_failure'] or x['termination']['wrist_failure']) for x in rows]
 ab=sum(ok and all(x['left_note_ledger']['values']['left']) for x,ok in zip(rows,safe));hold=[v['mean_clean_s']/1.5 for v in notes];on=sum(x['tail_and_onset'] for x in transitions)
 result=dict(schema='index_middle.evaluation.pc2.v1',episodes=n,notes=notes,AB_achievement_count=ab,full_duration_pair_count=sum(ok and all(v>=1.5-1e-8 for v in x['left_note_ledger']['values']['clean']) for x,ok in zip(rows,safe)),physical_failures=sum(bool(x['termination']['physical_failure']) for x in rows),wrist_failures=sum(bool(x['termination']['wrist_failure']) for x in rows),any_failures=failures,on_time_with_previous_tail_count=on,release_by_B_onset_count=sum(x['release_by_B_onset'] for x in transitions),transitions=transitions,effective_dual_samples=duals,operational_threshold_pass=ab/n>=.9 and min(hold)>=.9 and min(x['onset_count']/n for x in notes)>=.9 and failures/n<=.01,threshold_scope='operational only; release and collision proxies reported separately; no naturalness/generalization claim',reward_terms={k:sum(x['reward_components'][k] for x in rows)/n for k in rows[0]['reward_components']},input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (path/'report.json',path/'episodes.jsonl',path/'episode_metadata.json',path/'finger_control_trace.jsonl.gz')})
 result['safety_diagnostics']=dict(pair=[x['pair_safety_diagnostics'] for x in rows],thumb=[x['left_episode_diagnostics']['thumb_support'] for x in rows],extreme_combinations=[x['left_episode_diagnostics']['extreme_combinations'] for x in rows],wrist=[x['left_episode_diagnostics']['wrist'] for x in rows],force_scope='native net generalized/body forces and submitted efforts are distinct; no pair-pressure or sound claim')
 (path/'metrics.json').write_text(dumps(result,allow_nan=False,indent=2));return result
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('path');a=p.parse_args();v=analyze(a.path);print(dumps({k:v[k] for k in ('AB_achievement_count','any_failures','on_time_with_previous_tail_count','release_by_B_onset_count','operational_threshold_pass')}))
