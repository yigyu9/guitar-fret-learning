"""Read-only analysis of a failed run; distinguish committed updates and partial sampling."""
from pathlib import Path
import json,gzip,math,statistics,hashlib,re,os,datetime
base=Path(__file__).resolve().parent;root=base.parents[4]
run=root/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_20261018_100545'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
report=read(run/'report.json');updates=[read(f) for f in sorted(run.glob('update_*.json'))];completed_ticks=sum(u['transitions'] for u in updates)//16
pins=read(base/'inputs_before.json');pins[str(base/'kernel_window.txt')]=sha(base/'kernel_window.txt');pins[str(Path(__file__).resolve())]=sha(__file__)
(base/'analysis_inputs_before.json').write_text(json.dumps(pins,indent=2))
def fresh():return dict(samples=0,episode_ends=0,failures=0,matched50=0,matched100=0,held_s=0.,wrong_crossings=0,missed_strict=0,candidate_ticks=0,max_guitar_m=0.,max_speed_rad_s=0.,both_feet_ticks=0,any_support_ticks=0,goal_dist_sum_m=0.,goal_dist_count=0,onset_dist_sum_m=0.,onset_dist_count=0,reward_terms={},cost_sum=0.,reward_sum=0.,worker_rss_peak_sum_kib=0)
groups={};full=fresh();partial=fresh();ticks=0;failure_reasons={}
with gzip.open(run/'transitions.jsonl.gz','rt') as stream:
 for line in stream:
  row=json.loads(line);group=ticks//128;g=groups.setdefault(group,fresh());bucket=full if ticks<completed_ticks else partial
  for i,info in enumerate(row['infos']):
   for z in (g,bucket):
    z['samples']+=1;z['cost_sum']+=info['cost'];z['reward_sum']+=row['reward'][i]
    z['candidate_ticks']+=any(info['fret_candidates'].values())
    for k,v in info['reward_terms'].items():z['reward_terms'][k]=z['reward_terms'].get(k,0.)+v
    s=info['stability'];z['max_guitar_m']=max(z['max_guitar_m'],math.sqrt(sum(v*v for v in s['guitar_delta_m'])));z['max_speed_rad_s']=max(z['max_speed_rad_s'],s['max_joint_speed_rad_s'])
    z['both_feet_ticks']+=all(s['flags'][-2:]);z['any_support_ticks']+=any(s['flags'][:3])
    ds=list(info['goal_distance_m'].values());z['goal_dist_sum_m']+=sum(ds);z['goal_dist_count']+=len(ds)
    if abs(info['task_time_s']-1.12)<=.05:z['onset_dist_sum_m']+=sum(ds);z['onset_dist_count']+=len(ds)
    if row['terminated'][i] or row['truncated'][i]:
     m=info['music'];z['episode_ends']+=1;z['failures']+=info['termination_reason']=='terminal_failure'
     for k in ('matched50','matched100','wrong_crossings','missed_strict'):z[k]+=m[k]
     z['held_s']+=m['held_total_s']
   for reason in info.get('failure_reasons',[]):failure_reasons[reason]=failure_reasons.get(reason,0)+1
  rss=sum(info['resource']['rss_peak_kib'] for info in row['infos'])
  g['worker_rss_peak_sum_kib']=max(g['worker_rss_peak_sum_kib'],rss);bucket['worker_rss_peak_sum_kib']=max(bucket['worker_rss_peak_sum_kib'],rss)
  ticks+=1
for z in [full,partial,*groups.values()]:
 z['goal_origin_mean_m']=z.pop('goal_dist_sum_m')/z['goal_dist_count'] if z['goal_dist_count'] else None
 z['onset_goal_origin_mean_m']=z.pop('onset_dist_sum_m')/z['onset_dist_count'] if z['onset_dist_count'] else None
 z['both_feet_fraction']=z['both_feet_ticks']/z['samples'] if z['samples'] else None;z['any_support_fraction']=z['any_support_ticks']/z['samples'] if z['samples'] else None
rows=[]
for i,u in enumerate(updates):
 es=u['completed_episodes'];r=dict(update_number=i+1,mean_episode_reward=statistics.mean(e['reward'] for e in es),mean_episode_cost=statistics.mean(e['cost'] for e in es),episodes=len(es),metrics={k:v for k,v in u.items() if k!='completed_episodes'},logged=groups[i]);rows.append(r)
rss_by_episode={}
for f in run.glob('worker_*/audit_episode_*/initial_values.json'):
 d=read(f);idx=int(f.parent.name.rsplit('_',1)[1]);rss_by_episode.setdefault(idx,[]).append(d['resource']['rss_peak_kib']/1024)
rss_rows=[dict(episode_index=i,workers=len(v),mean_worker_peak_MiB=statistics.mean(v),min_worker_peak_MiB=min(v),max_worker_peak_MiB=max(v)) for i,v in sorted(rss_by_episode.items())]
text=(base/'kernel_window.txt').read_text();tables=[];current=[]
for line in text.splitlines():
 if '[  pid  ]' in line:
  if current:tables.append(current)
  current=[]
 m=re.search(r'kernel: \[\s*(\d+)\]\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(-?\d+)\s+(\S+)',line)
 if m:
  v=m.groups();current.append(dict(pid=int(v[0]),name=v[11],rss_bytes=int(v[4])*os.sysconf('SC_PAGE_SIZE'),anon_bytes=int(v[5])*os.sysconf('SC_PAGE_SIZE')))
if current:tables.append(current)
kills=[line for line in text.splitlines() if 'Out of memory: Killed process' in line]
changed=[p for p,h in pins.items() if sha(p)!=h]
result=dict(run=str(run),report_completed=report['completed'],report_failure=report['failure'],report_stopped_label=report['stopped'],completed_updates=len(updates),optimizer_updated_samples=report['transitions'],logged_ticks=ticks,completed_update_ticks=completed_ticks,committed_update_log=full,partial_collect_log=partial,per_update=rows,rss_by_reset_episode=rss_rows,global_min_sampled_available_bytes=report['resources']['min_available_memory_bytes'],host_oom_confirmed=bool(kills),kernel_first_oom_trigger=next((l for l in text.splitlines() if 'invoked oom-killer' in l),None),kernel_kills=kills,kernel_last_table_top_rss=sorted(tables[-1],key=lambda r:r['rss_bytes'],reverse=True)[:12],training_worker_pids_in_kernel_kill_list=[p for p in range(3185159,3185175) if any(('Killed process '+str(p)+' ') in line for line in kills)],missing_worker_final_audits=report['missing_worker_audits'],checkpoint=str(run/'checkpoint_000009.pt'),source_or_input_changes=report['changed_inputs'],failure_reasons=failure_reasons,changed_analysis_inputs=changed,scope='Raw compact60Hz endpoints; live musical integration/failurechecks240Hz. Goal distance isdistalbodyorigin to nominalfretpoint, not contactgap. RSS peak is highwater/sharedpages maydoublecount. SystemRAM series notlogged. Partial collection wasnot optimized. No native runor source/config mutation.')
(base/'analysis.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ['per_update','rss_by_reset_episode','report_failure','kernel_last_table_top_rss','kernel_kills']},indent=2))
print('RSS_RESETS',json.dumps(rss_rows));print('PER_UPDATE',json.dumps([dict(update=r['update_number'],cost=r['mean_episode_cost'],reward=r['mean_episode_reward'],onset_origin_mm=r['logged']['onset_goal_origin_mean_m']*1000,rss_peak_GiB=r['logged']['worker_rss_peak_sum_kib']/1024**2) for r in rows]))
if changed:raise SystemExit('Analysis input changed')
