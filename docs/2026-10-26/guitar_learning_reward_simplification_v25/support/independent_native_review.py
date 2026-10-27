"""Independent CPU-only checks of committed native data; never runs physics."""
import collections
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path('/home/ajou/yigyu/3')
sys.path.insert(0, str(ROOT))
RESULT = Path(__file__).resolve().parent.parent


def main():
    import numpy as np
    import torch
    from guitar_learning.training.gpu_log_records import iter_gpu_transitions, iter_episode_rows
    from guitar_learning.training.training_log_io import iter_transitions
    from guitar_learning.song.task import make_task
    torch.set_num_threads(1)
    task = make_task(ROOT/'data/song_bundles/05_BN2-131-B_solo', pre_roll_s=3., tail_s=.5)
    manifest = json.loads((RESULT/'support/source_manifest.json').read_text())
    def pins():
        assert all(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'] for r in manifest)
    pins()
    def same(a,b):
        if isinstance(a,torch.Tensor): return isinstance(b,torch.Tensor) and a.dtype==b.dtype and torch.equal(a,b)
        if isinstance(a,np.ndarray): return isinstance(b,np.ndarray) and a.dtype==b.dtype and np.array_equal(a,b)
        if isinstance(a,dict): return isinstance(b,dict) and a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
        if isinstance(a,(tuple,list)): return type(a)==type(b) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
        return a==b
    def finite(x):
        if isinstance(x,torch.Tensor): return bool(torch.isfinite(x).all())
        if isinstance(x,dict): return all(finite(v) for v in x.values())
        if isinstance(x,(tuple,list)): return all(finite(v) for v in x)
        return not isinstance(x,float) or math.isfinite(x)
    results={}
    requested=sys.argv[1:] or ['large1024','resume1024']
    for name in requested:
        run=RESULT/name/'J'
        report=json.loads((run/'report.json').read_text())
        assert report['completed'] and report['lifecycle_verified'] and not report['changed_inputs'] and not report['missing_import_pins']
        initial=torch.load(run/'initial.pt',map_location='cpu',weights_only=False)
        final=torch.load(run/'final.pt',map_location='cpu',weights_only=False)
        for key in ('model','actor_optimizer','value_optimizer'): assert finite(final[key])
        assert final['metadata']['settings']['ppo']['cost_weight']==final['cost_weight']==1.
        config=final['metadata']['curriculum']['config']
        baseline=initial['metadata']['curriculum']['committed_transitions']
        n=report['settings']['num_envs']; horizon=report['settings']['horizon']
        rawstatus={}; raw=list(iter_gpu_transitions(run,diagnostics=rawstatus))
        assert rawstatus['complete'] and len(raw)*n==report['transitions']
        rewards=np.asarray([r['reward'] for r in raw]); costs=np.asarray([r['cost'] for r in raw]); terms=np.asarray([r['terminated'] for r in raw])
        assert rewards.shape==costs.shape==terms.shape==(len(raw),n)
        assert np.isfinite(rewards).all() and np.isfinite(costs).all()
        assert (costs>=0).all() and ((costs==0)|terms).all()
        episode_ids=np.zeros((len(raw),n),dtype=np.int64); ids=np.zeros(n,dtype=np.int64)
        full=np.full(n,baseline>=config['full_song_after'],dtype=bool)
        exposure=dict(phrases=0,full_song=0)
        initial_updates=initial['updates']
        for tick,row in enumerate(raw):
            assert row['update_index']==initial_updates+tick//horizon and row['tick_in_update']==tick%horizon
            episode_ids[tick]=ids
            exposure['full_song']+=int(full.sum());exposure['phrases']+=n-int(full.sum())
            for e in row['episodes']:
                i=e['env_id'];assert e['finger_skill']['scope']==('full_song' if full[i] else 'phrase')
            done=terms[tick]|np.asarray(row['truncated'])
            ids+=done
            committed_before=baseline+(tick//horizon)*horizon*n
            if committed_before>=config['full_song_after']:full[done]=True
        previous=initial['metadata']['exposure_transitions']
        expected={k:previous[k]+exposure[k] for k in exposure}
        assert expected==final['metadata']['exposure_transitions']==report['exposure_transitions']
        visited=np.zeros((len(raw),n),dtype=bool);status={};max_reward_error=max_cost_error=0.
        for d in iter_transitions(run/'decisions.jsonl.gz',diagnostics=status):
            tick=d['start_control_tick'];i=d['env_id']
            assert 0<=tick<len(raw) and 0<=i<n and not visited[tick,i]
            visited[tick,i]=True
            assert d['update_index']==raw[tick]['update_index'] and d['episode_id']==episode_ids[tick,i]
            assert d['duration']==d['planned_ticks']==1 and d['end_control_tick']==tick+1 and d['raw_control_ticks']==[tick]
            assert d['terminated']==bool(terms[tick,i]) and d['truncated']==raw[tick]['truncated'][i]
            er=abs(d['discounted_reward']-rewards[tick,i]);ec=abs(d['discounted_cost']-costs[tick,i])
            max_reward_error=max(max_reward_error,er);max_cost_error=max(max_cost_error,ec)
        assert status['complete'] and visited.all() and max_reward_error<1e-6 and max_cost_error<1e-6
        reasons=collections.Counter();max_paid_error=max_reward_sum_error=max_performance_error=max_wrong_error=0.
        for record in iter_episode_rows(run):
            e=record['episode'];reasons[e['termination']['primary_reason']]+=1
            ledger=e['left_note_ledger'];v=ledger['values'];mask=ledger['focus_mask'];count=sum(mask)
            finger_counts=collections.Counter(t.finger for t,keep in zip(task.targets,mask) if keep)
            assert ledger['target_ids']==[t.target_id for t in task.targets]
            assert 'weights' not in e['left_curriculum'] and 'progress' not in e['left_curriculum']
            now=e['finger_skill']['source_task_time_s'];budget=wrong_expected=0.
            for i,t in enumerate(task.targets):
                w=count/(len(finger_counts)*finger_counts[t.finger]) if mask[i] else 0.
                missing=min(1.,max(0.,v['missing'][i]/(t.end_s-t.onset_s)))
                deficit=max(0.,1-v['best_clean_streak'][i]/ledger['required_clean_s'][i])
                ending=mask[i] and now+1e-10>=t.end_s
                assert bool(v['performance_settled'][i])==ending
                target=.1*w*(max(missing,deficit) if ending else missing)
                max_paid_error=max(max_paid_error,abs(v['performance_paid'][i]-target))
                if mask[i] and not ending:
                    budget+=.15*w*max(0.,t.end_s-max(now,t.onset_s))/(t.end_s-t.onset_s)+max(0.,.1*w-v['performance_paid'][i])
                wrong_expected-=.15*w*v['wrong'][i]/(t.end_s-t.onset_s)
            max_performance_error=max(max_performance_error,abs(e['reward_components']['song_performance_deficit']+sum(v['performance_paid'])))
            max_wrong_error=max(max_wrong_error,abs(e['reward_components']['song_wrong_press']-wrong_expected))
            max_reward_sum_error=max(max_reward_sum_error,abs(sum(e['reward_components'].values())-e['reward']))
            fail=e['termination']['physical_failure'] or e['termination']['wrist_failure']
            expected_cost=5+2*max(0.,e['finger_skill']['local_duration_s']-e['steps']/60.)+budget if fail else 0.
            assert abs(e['cost']-expected_cost)<1e-4 and abs(sum(e['cost_components'].values())-e['cost'])<1e-4
            assert e['cost_components']['running_physics']==0.
        assert max_paid_error<1e-6 and max_performance_error<1e-5 and max_wrong_error<1e-5 and max_reward_sum_error<1e-4
        for entry in map(json.loads,(run/'checkpoint_manifest.jsonl').read_text().splitlines()):
            assert hashlib.sha256((run/entry['path']).read_bytes()).hexdigest()==entry['sha256']
        groups={prefix:sum(not torch.equal(value,initial['model'][key]) for key,value in final['model'].items() if key.startswith(prefix)) for prefix in ('support_','finger_')}
        assert all(groups.values())
        results[name]=dict(completed=True,raw_transitions=int(visited.size),decisions_exact_raw_coverage=True,max_decision_reward_error=max_reward_error,max_decision_cost_error=max_cost_error,episode_ids_exact=True,exposure_independently_reconstructed=exposure,cumulative_exposure=expected,reasons=dict(reasons),max_performance_paid_formula_error=max_paid_error,max_performance_reward_error=max_performance_error,max_wrong_reward_error=max_wrong_error,max_reward_sum_error=max_reward_sum_error,model_and_both_adam_finite=True,changed_actor_tensors=groups,checkpoint_sha_verified=True)
    a=torch.load(RESULT/'large1024/J/final.pt',map_location='cpu',weights_only=False)
    b=torch.load(RESULT/'resume1024/J/initial.pt',map_location='cpu',weights_only=False)
    fields=['identity','model','actor_optimizer','value_optimizer','cost_weight','updates','torch_rng','numpy_rng','python_rng','cuda_rng']
    assert all(same(a[k],b[k]) for k in fields) and same(a['metadata']['curriculum'],b['metadata']['curriculum'])
    assert a['metadata']['settings']['finger_skill']==b['metadata']['settings']['finger_skill']
    shadow=json.loads((RESULT/'shadow/report.json').read_text())
    correction=shadow['correction']
    original=RESULT/'shadow/original_report.json'
    assert hashlib.sha256(original.read_bytes()).hexdigest()==correction['original_report_sha256']
    assert hashlib.sha256((RESULT/'support/shadow_wrist_original.py').read_bytes()).hexdigest()==correction['executed_harness_sha256']
    assert len(shadow['records'])==24
    for r in shadow['records']:
        assert r['end']['natural']==(not r['end']['physical_failure'] and r['end']['control_ticks']==r['duration_ticks'])
        assert not r['normal_before_3_75']
    scene=json.loads((RESULT/'shadow/gpu_scene_final.json').read_text())
    assert scene['closed'] and scene['simulator_count']==1 and scene['environment_count']==24
    assert scene['physx_use_gpu'] and scene['use_gpu_pipeline']
    pins()
    result=dict(completed=True,review_scope='read-only CPU artifacts, no native simulation',runs=results,strict_resume_exact_fields=fields+['metadata.curriculum','metadata.settings.finger_skill'],shadow=dict(original_bytes_preserved_and_sha_linked=True,corrected_natural_end_verified=True,actual_lifecycle_verified=True,distinct_views=24,normal_would_fail=shadow['normal_would_fail'],severe_would_fail=shadow['severe_would_fail']),source_files=len(manifest),source_sha_unchanged=True)
    target=RESULT/'support'/('native_review_partial.json' if len(requested)==2 else 'native_review_data.json')
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
