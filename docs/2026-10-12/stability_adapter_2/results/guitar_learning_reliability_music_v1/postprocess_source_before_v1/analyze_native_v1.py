"""Read only the bounded runs in this phase; never scan prior raw results."""
import gzip
import hashlib
import json
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
import torch

PHASE=Path(__file__).resolve().parent
RUNS=('interrupt_native_v1','resume_native_v1','fake_memory_native_v1','dense_8env_native_v1','dense_8env_native_v2','pool_native_v1','pool_native_v2')
def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def equal_state(left,right):
    if torch.is_tensor(left):return torch.equal(left,right)
    if isinstance(left,np.ndarray):return np.array_equal(left,right)
    if isinstance(left,dict):return left.keys()==right.keys() and all(equal_state(left[k],right[k]) for k in left)
    if isinstance(left,(tuple,list)):return len(left)==len(right) and all(equal_state(a,b) for a,b in zip(left,right))
    return left==right
def summarize(name):
    folder=PHASE/name;r=load(folder/'report.json')
    terms=defaultdict(float);counts=Counter();maxima=defaultdict(float);terminal_music=Counter();left=[];right=[];onset_right=[];goals=Counter();supports=feet=0;n=0;lines=0;early_ticks=0
    with gzip.open(folder/'transitions.jsonl.gz','rt') as stream:
        for line in stream:
            lines+=1
            for info in json.loads(line)['infos']:
                n+=1
                for k,v in info['reward_terms'].items():terms[k]+=v
                m=info['music']
                for key in ('matched50','matched100','missed_strict','held_total_s'):
                    maxima[key]=max(maxima[key],m.get(key,0))
                    if info['termination_reason']:terminal_music[key]+=m.get(key,0)
                counts[info['termination_reason'] or 'active']+=1
                counts['failure_ticks']+=bool(info['failure_reasons'])
                counts['fret_candidate_ticks']+=any(info['fret_candidates'].values())
                flags=info['stability']['flags'];supports+=any(flags[:3]);feet+=all(flags[-2:])
                maxima['guitar_delta_m']=max(maxima['guitar_delta_m'],np.linalg.norm(info['stability']['guitar_delta_m']))
                for v in info['goal_distance_m'].values():left.append(v)
                guide=info.get('pick_guide')
                if guide:
                    right.append(guide['distance_m'])
                    if guide['sweep_active']:onset_right.append(guide['distance_m'])
                if info['reward_terms'].get('dense_left_early',0)>0:early_ticks+=1
                if 'episode_task' in info:goals[str(info['episode_task']['event_index'])]+=1
    resource=[json.loads(line) for line in (folder/'resources.jsonl').read_text().splitlines()]
    current_rss=[];current_pss=[]
    for row in resource:
        memories=[x['memory'] for x in row['workers']]
        current_rss.append(sum(x['rss_current_bytes'] or 0 for x in memories))
        current_pss.append(sum(x['pss_current_bytes'] or 0 for x in memories))
    completed=[e for u in r['updates'] for e in u['completed_episodes']]
    reset_tasks=Counter()
    for p in folder.glob('worker_*/audit_episode_*/episode_task.json'):reset_tasks[str(load(p)['event_index'])]+=1
    check_keys=('changed_inputs','missing_import_pins','original_source_parity_errors','missing_worker_audits','worker_audit_read_errors','guard_violations','worker_failures','physical_flags_errors','cleanup_errors')
    checkpoints={}
    for filename in ('initial.pt','failure_last_valid.pt','final.pt'):
        path=folder/filename
        if path.exists():
            payload=torch.load(path,map_location='cpu',weights_only=False)
            checkpoints[filename]=dict(sha256=sha(path),updates=payload['updates'],finite=all(torch.isfinite(x).all().item() for x in payload['model'].values()))
    return dict(dense_config=load(folder/'training_contract.json')['reward'].get('dense_v2') if (folder/'training_contract.json').exists() else None,completed=r['completed'],stopped=r['stopped'],updates=len(r['updates']),committed_transitions=r['transitions'],logged_ticks=lines,logged_transitions=n,partial=r['partial_collection'],completed_episodes=len(completed),mean_completed_episode_cost=float(np.mean([e['cost'] for e in completed])) if completed else None,mean_completed_episode_reward=float(np.mean([e['reward'] for e in completed])) if completed else None,peak_analytic_kl=max((u['analytic_kl'] for u in r['updates']),default=None),reward_terms=dict(terms),terminal_reasons=dict(counts),music_episode_endpoint_maxima=dict(maxima),logged_terminal_music_totals=dict(terminal_music),early_left_positive_ticks=early_ticks,goal_distance_proxy_m=dict(mean=float(np.mean(left)) if left else None),right_guide_proxy_m=dict(mean=float(np.mean(right)) if right else None,sweep_mean=float(np.mean(onset_right)) if onset_right else None),any_support_endpoint_fraction=supports/n if n else None,both_feet_endpoint_fraction=feet/n if n else None,goal_transition_counts=dict(goals),goal_reset_counts=dict(reset_tasks),collection_transitions_per_s=r['collection_transitions_per_s'],wall_s=r['wall_s'],min_observed_available_gib=min(x['available_memory_bytes'] for x in resource)/1024**3,worker_current_rss_sum_max_gib=max(current_rss)/1024**3,worker_current_pss_sum_max_gib=max(current_pss)/1024**3,checks={k:r[k] for k in check_keys},checkpoints=checkpoints,resource_rows=len(resource),checks_clear=all(not r[k] for k in check_keys),effective_memory_probe='fake 3GiB after >=4 ticks; no actual host pressure' if name.startswith('fake_') else 'real /proc/MemAvailable')

if __name__=='__main__':
    torch.set_num_threads(1)
    result={name:summarize(name) for name in RUNS}
    a=torch.load(PHASE/'interrupt_native_v1/initial.pt',map_location='cpu',weights_only=False)
    b=torch.load(PHASE/'interrupt_native_v1/failure_last_valid.pt',map_location='cpu',weights_only=False)
    c=torch.load(PHASE/'resume_native_v1/initial.pt',map_location='cpu',weights_only=False)
    result['recovery_model_checks']=dict(interrupt_initial_updates=a['updates'],interrupt_recovery_updates=b['updates'],restarted_initial_updates=c['updates'],interrupted_unoptimized_model_equal=all(torch.equal(a['model'][k],b['model'][k]) for k in a['model']),reloaded_model_equal=all(torch.equal(b['model'][k],c['model'][k]) for k in b['model']))
    for key in ('actor_optimizer','value_optimizer'):
        result['recovery_model_checks']['interrupted_'+key+'_equal']=equal_state(a[key],b[key])
        result['recovery_model_checks']['reloaded_'+key+'_equal']=equal_state(b[key],c[key])
    result['recovery_model_checks']['reloaded_rng_equal']=all(equal_state(b[k],c[k]) for k in ('torch_rng','numpy_rng','python_rng','cuda_rng'))
    first=[]
    for name in ('dense_8env_native_v1','dense_8env_native_v2'):
        path=PHASE/name/'worker_000/audit_episode_000000/transition_00000000.json.gz'
        with gzip.open(path,'rt') as stream:first.append(json.load(stream))
    result['first_tick_signal_comparison']=dict(
        first_action_identical=bool(np.array_equal(first[0]['action'],first[1]['action'])),
        guide_distance_m=[x['info']['pick_guide']['distance_m'] for x in first],
        right_guide_reward=[x['info']['reward_terms']['dense_right_guide'] for x in first],
        left_early_reward=[x['info']['reward_terms']['dense_left_early'] for x in first],
        right_reward_ratio=first[1]['info']['reward_terms']['dense_right_guide']/first[0]['info']['reward_terms']['dense_right_guide'],
        scope='same first native action; changed shaping signal, not proof of improved learned motion')
    result['scope']='bounded integration/recovery/learning-signal pilot; not convergence, pressure/sound, full-song or leak-free certification'
    with (PHASE/'native_summary_v1.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    for name in RUNS:
        row=result[name]
        print(name,{k:row[k] for k in ('completed','stopped','updates','logged_transitions','completed_episodes','min_observed_available_gib','checks_clear')})
    print(result['recovery_model_checks'])
