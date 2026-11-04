"""Strict per-note/section analysis of immutable H checkpoints and first episodes."""
if not __debug__:raise RuntimeError('optimized Python forbidden')
from pathlib import Path
import sys,json,hashlib,csv,collections,math,datetime
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parents[1];S=D/'작업자료/source_snapshot';sys.path.insert(0,str(S));torch.set_num_threads(1)
from guitar_learning.training.training_log_io import iter_episode_rows
from guitar_learning.tool.experiments.compact_press_v5 import read_checkpoint
A=D/'분석';A.mkdir(exist_ok=True);CMD=json.loads((D/'작업자료/명령목록.json').read_text());META=json.loads((S/'data/song_bundles/press_sequence_c1_v1/mapping/fingering.json').read_text())['metadata'];TOTAL=16777216

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False))
def csvwrite(name,rows):
 if rows:
  with (A/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def section_for(note,pre_roll=3.):
 raw=note['onset_s']-pre_roll
 found=[s['case_id'] for s in META['sections'] if s['first_note']-1e-8<=raw<=s['last_note']+1e-8 and note['end_s']<=s['end']+pre_roll+1e-8]
 assert len(found)==1,(note,found)
 return found[0]
def extract_episode(e,pre_roll=3.):
 ledger=e['left_note_ledger'];ids=ledger['target_ids'];v=ledger['values'];assert len(ids)==20 and len(set(ids))==20
 held={x['target_id']:x for x in e['press_coordination']['notes']};releases={x['target_id']:x for x in e['press_completion']['notes']};assert held.keys()==releases.keys()==set(ledger['selected_target_ids'])
 source_end=e['finger_skill']['source_task_time_s'];safe=bool(e['press_completion']['safe']);out=[]
 for i,tid in enumerate(ids):
  if tid not in held:continue
  x=held[tid];r=releases[tid];audible=source_end>x['onset_s']+1e-12;complete_opportunity=source_end+1e-9>=x['end_s'];strict=x['best_clean_streak_s']+1e-9>=x['duration_s'];assert strict==x['strict_success'];release=r['release_status'] in ('released','not_required');joint=strict and complete_opportunity and release
  out.append(dict(env_id=e['env_id'],target_id=tid,section=section_for(x,pre_roll),selected=True,preparation_goal_observation_exposed=None,surface_diagnostic_window_exposed=v['exposure_time'][i]>0,audible_started=audible,audible_end_observed=complete_opportunity,strict_hold=strict,release_required=r['release_required'],release_status=r['release_status'],hold_and_release=joint,safe_episode=safe,safe_episode_hold_and_release=joint and safe,legacy=bool(v['left'][i]),contact=bool(v['contact_done'][i]),duration_s=x['duration_s'],clean_s=v['clean'][i],wrong_s=v['wrong'][i],missing_s=v['missing'][i]))
 return out

def select_model(models):
 best_notes=max(x['hold_release_notes'] for x in models);candidates=[x for x in models if x['hold_release_notes']==best_notes];fail=min(x['failure_episodes'] for x in candidates);candidates=[x for x in candidates if x['failure_episodes']==fail];clean=max(x['clean_s'] for x in candidates);candidates=[x for x in candidates if abs(x['clean_s']-clean)<=1e-9]
 if len(candidates)==1:return candidates[0],'unique best on predefined criteria'
 return next(x for x in models if x['transitions']==TOTAL),'tied best candidates; prescribed final fallback even if final is outside tied best set'

def main():
 compare=[];sectionrows=[];noterows=[];learning=[];stdrows=[];identities=[];selections={};training_info={};initial_hashes={}
 for c in CMD['conditions']:
  name=c['name'];train=Path(c['train'][c['train'].index('--out')+1]);stage=train/'J';r=json.loads((stage/'report.json').read_text());assert r['completed'] and r['lifecycle_verified'] and r['transitions']==TOTAL
  metrics=[json.loads(z) for z in (stage/'learning_metrics.jsonl').read_text().splitlines()];assert sum(z['transitions'] for z in metrics)==TOTAL
  command=json.loads((D/'작업자료'/(name+'_command.json')).read_text());launch=datetime.datetime.fromisoformat(command['started_at']);events=[json.loads(z) for z in (stage/'events.jsonl').read_text().splitlines()];wall_by_update={x['update_index']:(datetime.datetime.fromisoformat(x['wall_time_utc'])-launch).total_seconds() for x in events if x.get('event')=='phase' and x.get('phase')=='collecting'};receipt=json.loads((D/'작업자료'/(name+'_receipt.json')).read_text())
  elapsed=0.;accepted=value_steps=rejected=0
  for m in metrics:
   dg=m['diagnostics'];elapsed+=m['collection_s']+m['update_s'];actor=dg['minibatches']['actor_accepted'];critic=dg['minibatches']['value'];accepted+=actor['steps'];value_steps+=critic['steps'];rejected+=dg['minibatches']['actor_rejected']['steps'];post=dg['post_update'];row=dict(condition=name,horizon=c['horizon'],optimizer_updates=m['optimizer_updates'],committed_transitions=m['curriculum']['committed_transitions'],collect_opt_elapsed_s=elapsed,collection_s=m['collection_s'],update_s=m['update_s'],transitions_per_s=m['transitions']/(m['collection_s']+m['update_s']),LR=m['actor_lr'],KL=m['analytic_kl'],max_attempted_KL=m['max_attempted_kl'],KL_retries=m['kl_retries'],clip_fraction=post['clip_fraction'],latent_entropy=post['latent_gaussian_entropy']['mean'],reward_EV=post['critics']['reward']['explained_variance'],cost_EV=post['critics']['cost']['explained_variance'],reward_value_loss_last=m['reward_value_loss'],cost_value_loss_last=m['cost_value_loss'],reward_adv_std=m['diagnostics']['advantages']['reward_raw']['std'],cost_adv_std=m['diagnostics']['advantages']['cost_raw']['std'])
   row.update(m['reward_component_means']);learning.append(row)
  training_info[name]=dict(report_wall_s=r['wall_s'],collection_s=sum(m['collection_s'] for m in metrics),optimization_s=sum(m['update_s'] for m in metrics),accepted_actor_steps=accepted,rejected_actor_steps=rejected,value_steps=value_steps,KL_retries=sum(m['kl_retries'] for m in metrics),actual_exposure=r['exposure_transitions'],curriculum=r['curriculum'],source_sha256=sha(stage/'inputs_before.json'))
  manifest={m['path']:m for m in [json.loads(z) for z in (stage/'checkpoint_manifest.jsonl').read_text().splitlines()]};models=[]
  for ev in c['evaluations']:
   cp=Path(ev['checkpoint']);assert sha(cp)==manifest[cp.name]['sha256'];settings=read_checkpoint(cp);payload=torch.load(cp,map_location='cpu',weights_only=False);assert payload['updates']*c['batch_transitions']==ev['transitions']
   if ev['transitions']==0:
    hh=hashlib.sha256()
    for key,tensor in sorted(payload['model'].items()):hh.update(key.encode());hh.update(tensor.detach().contiguous().numpy().tobytes())
    initial_hashes[name]=hh.hexdigest()
   std=payload['model']['log_std'].clamp(-5,2).exp().tolist();assert len(std)==33
   for axis,v in enumerate(std):stdrows.append(dict(condition=name,transitions=ev['transitions'],axis_index=axis,group='support17' if axis<17 else 'finger16',latent_std=v))
   out=Path(ev['argv'][ev['argv'].index('--out')+1]);report=json.loads((out/'report.json').read_text());assert report['completed'] and report['episodes']==32 and report['checkpoint_sha256']==sha(cp) and report['first_episode_per_env_per_batch'] and report['failed_episodes_in_denominator']
   episodes=[x['episode'] for x in iter_episode_rows(out)];assert len(episodes)==32 and {e['env_id'] for e in episodes}==set(range(32));rows=[]
   for e in episodes:
    assert e['finger_skill']['scope']=='full_song' and len(e['left_note_ledger']['selected_target_ids'])==20
    rows+=extract_episode(e,settings['song']['pre_roll_s'])
   assert len(rows)==640
   nt=len(rows);strict=sum(x['strict_hold'] for x in rows);both=sum(x['hold_and_release'] for x in rows);fail=sum(e['termination']['physical_failure'] or e['termination']['wrist_failure'] for e in episodes);clean=sum(x['clean_s'] for x in rows);prefix=[m for m in metrics if m['optimizer_updates']<=payload['updates']];collectopt=sum(m['collection_s']+m['update_s'] for m in prefix)
   result=dict(condition=name,horizon=c['horizon'],transitions=ev['transitions'],checkpoint=str(cp),checkpoint_sha256=sha(cp),episodes=32,note_denominator=nt,strict_hold_notes=strict,hold_release_notes=both,hold_release_rate=both/nt,safe_episode_hold_release_notes=sum(x['safe_episode_hold_and_release'] for x in rows),legacy_notes=sum(x['legacy'] for x in rows),contact_notes=sum(x['contact'] for x in rows),surface_window_exposed_notes=sum(x['surface_diagnostic_window_exposed'] for x in rows),audible_started_notes=sum(x['audible_started'] for x in rows),audible_ended_notes=sum(x['audible_end_observed'] for x in rows),unstarted_notes=sum(not x['audible_started'] for x in rows),exposed_failed_notes=sum(x['audible_started'] and not x['hold_and_release'] for x in rows),episode_completion=sum(e['press_completion']['completion_success'] for e in episodes),physical_failure=sum(e['termination']['physical_failure'] for e in episodes),wrist_failure=sum(e['termination']['wrist_failure'] for e in episodes),failure_episodes=fail,failure_rate=fail/32,clean_s=clean,wrong_s=sum(x['wrong_s'] for x in rows),missing_s=sum(x['missing_s'] for x in rows),collect_opt_elapsed_s=collectopt,actual_training_wall_elapsed_s=receipt['wall_s'] if ev['transitions']==TOTAL else wall_by_update[payload['updates']],evaluation_wall_s=report['wall_s'])
   groups_by_env={}
   for episode in episodes:
    lookup={n['target_id']:section_for(n,settings['song']['pre_roll_s']) for n in episode['press_coordination']['notes']};bysec=collections.defaultdict(list)
    for group in episode['press_coordination']['groups']:
     labels={lookup[tid] for tid in group['target_ids']};assert len(labels)==1,'coordination group spans source sections';bysec[next(iter(labels))].append(group['strict_success'])
    groups_by_env[episode['env_id']]=bysec
   sections_completed=0
   for sid in ('P1','P2','P3','P4','P5','P6','P7','P8','P9'):
    sr=[x for x in rows if x['section']==sid];assert len(sr)==len(next(x for x in META['sections'] if x['case_id']==sid)['note_indices'])*32
    perenv=[[x for x in sr if x['env_id']==i] for i in range(32)];sc=sum(all(x['hold_and_release'] for x in ee) and all(groups_by_env[i][sid]) for i,ee in enumerate(perenv));sections_completed+=sc
    sectionrows.append(dict(condition=name,transitions=ev['transitions'],section=sid,episodes=32,section_hold_release_completed=sc,note_denominator=len(sr),hold_release_notes=sum(x['hold_and_release'] for x in sr),strict_hold_notes=sum(x['strict_hold'] for x in sr),contact_notes=sum(x['contact'] for x in sr),legacy_notes=sum(x['legacy'] for x in sr),surface_window_exposed_notes=sum(x['surface_diagnostic_window_exposed'] for x in sr),audible_started_notes=sum(x['audible_started'] for x in sr),audible_ended_notes=sum(x['audible_end_observed'] for x in sr),clean_s=sum(x['clean_s'] for x in sr),wrong_s=sum(x['wrong_s'] for x in sr),missing_s=sum(x['missing_s'] for x in sr)))
   result.update(section_denominator=288,section_hold_release_completed=sections_completed,section_hold_release_rate=sections_completed/288);compare.append(result);models.append(result);noterows.extend(dict(condition=name,transitions=ev['transitions'],**x) for x in rows);identities.append(dict(condition=name,transitions=ev['transitions'],checkpoint_sha256=sha(cp),architecture_sha256=hashlib.sha256(json.dumps(payload['identity']['architecture'],sort_keys=True).encode()).hexdigest(),strict_official_reader_passed=True))
  # Predefined ranking; final wins an exact tie. No threshold changes or ad hoc cherry-picking.
  best,reason=select_model(models);selections[name]=dict(selection_reason=reason,checkpoint=best['checkpoint'],sha256=best['checkpoint_sha256'],transitions=best['transitions'],criterion='note full hold+required release count, lower failure count, clean time; any tied best set falls back to final; section completion separately',clean_tie_tolerance_s=1e-9,evaluation_used_for_selection=True,independent_test=False)
 assert len(set(initial_hashes.values()))==1,'fresh initial policy weights differ across H'
 csvwrite('비교표.csv',compare);csvwrite('구간별비교.csv',sectionrows);csvwrite('음별원장.csv',noterows);csvwrite('학습지표.csv',learning);csvwrite('탐색표준편차.csv',stdrows);write(A/'요약.json',dict(comparison=compare,training=training_info,identities=identities,initial_model_tensor_sha256=initial_hashes,selections=selections,notes='32parallel envs are not32independent training seeds; per-note completion before later termination is separate from safe whole-episode completion; no pressure or acoustic claim'));write(A/'선정모델.json',selections)
 for key,label in [('hold_release_rate','Full hold + required release /640 scheduled notes'),('section_hold_release_rate','Section completion /288 scheduled sections')]:
  for xaxis,xlabel,filetag in [('transitions','Committed transitions','experience'),('actual_training_wall_elapsed_s','Measured training wall seconds (launch to checkpoint boundary)','time')]:
   fig,ax=plt.subplots(figsize=(9,5))
   for c in CMD['conditions']:
    rr=[r for r in compare if r['condition']==c['name']];ax.plot([r[xaxis] for r in rr],[r[key] for r in rr],marker='o',label=c['name'])
   ax.set_xlabel(xlabel);ax.set_ylabel(label);ax.set_ylim(-.01,1.01);ax.legend();ax.grid(alpha=.25);fig.tight_layout();fig.savefig(A/(filetag+'_'+key+'.png'),dpi=160);plt.close(fig)
 fig,axs=plt.subplots(3,2,figsize=(13,10))
 for ax,key in zip(axs.flat,('LR','KL','clip_fraction','latent_entropy','reward_EV','transitions_per_s')):
  for c in CMD['conditions']:
   rr=[r for r in learning if r['condition']==c['name']];ax.plot([r['committed_transitions'] for r in rr],[r[key] if r[key] is not None else np.nan for r in rr],label=c['name'],alpha=.7)
  ax.set_title(key);ax.grid(alpha=.2);ax.legend(fontsize=7)
 fig.tight_layout();fig.savefig(A/'학습진단.png',dpi=150);plt.close(fig)
 print('15 strict evaluations aggregated, all initial weights identical, selected models written',flush=True)
if __name__=='__main__':main()
