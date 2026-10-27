"""Post-run streaming music/PPO analysis with the preceding frozen definitions."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import torch

OUT=Path(__file__).resolve().parent
RUN=OUT/'run_v1'
OLD=OUT.parent/'guitar_learning_long_B_8env_dense_v2_analysis_v1'
BASE=OUT.parent/'guitar_learning_long_B_8env_dense_v2_20261018_130137'


def read(p):return json.loads(p.read_text())


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def write(name,d):
    with (OUT/name).open('x') as f:json.dump(d,f,indent=2,ensure_ascii=False,allow_nan=False)


def main():
    # Reading a mutable/open gzip log would give an incomplete prefix. Only the
    # final canonical report, including lifecycle evidence, starts this analysis.
    assert (RUN/'core_report.json').is_file() and (RUN/'persistent_audit.json').is_file()
    inputs={Path(__file__).resolve(),OLD/'analyze.py',OLD/'analysis.json',
        OUT/'resume_selection.json',BASE/'checkpoint_000024.pt'}
    for pattern in ('report.json','core_report.json','settings.json','training_contract.json','inputs_before.json',
                    'persistent_audit.json','transitions.jsonl.gz','update_*.json','initial.pt','final.pt','failure_last_valid.pt'):
        inputs.update(RUN.glob(pattern))
    pins={str(p):sha(p) for p in sorted(inputs)};write('learning_inputs_before.json',pins)
    spec=importlib.util.spec_from_file_location('frozen_music_analysis',OLD/'analyze.py')
    helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
    report=read(RUN/'report.json');updates=report['updates'];n=len(updates);h=report['settings']['horizon']
    assert n>=1,'No completed update; inspect original report instead of claiming a learning result'
    per=[helpers.bucket() for _ in range(n+1)]
    groups={k:helpers.bucket() for k in ('committed','discarded','first_five_updates','last_five_updates')}
    frames=0
    with gzip.open(RUN/'transitions.jsonl.gz','rt') as f:
        for frame,line in enumerate(f):
            row=json.loads(line);index=frame//h;assert index<=n
            for info,reward in zip(row['infos'],row['reward']):
                helpers.add(per[index],info,reward)
                helpers.add(groups['committed' if index<n else 'discarded'],info,reward)
                if index<min(5,n):helpers.add(groups['first_five_updates'],info,reward)
                if max(0,n-5)<=index<n:helpers.add(groups['last_five_updates'],info,reward)
            frames+=1
    def summarize(b):
        row=helpers.summary(b)
        row['completed_episode_matched50']=sum(e['music']['matched50'] for e in b['episodes'])
        row['completed_episode_matched100']=sum(e['music']['matched100'] for e in b['episodes'])
        row['completed_episodes_with_strict_match']=sum(e['music']['matched50']>0 for e in b['episodes'])
        row['completed_episode_held_total_s']=sum(e['music']['held_total_s'] for e in b['episodes'])
        return row
    summaries={name:summarize(b) for name,b in groups.items() if b['count']}
    assert summaries['committed']['count']==report['transitions']
    per_update=[dict(update_index=i,committed=i<n,**summarize(b)) for i,b in enumerate(per) if b['count']]
    for i,u in enumerate(updates):
        assert len(per[i]['episodes'])==len(u['completed_episodes'])
        assert abs(per[i]['reward']-sum(per[i]['terms'].values()))<1e-6
    old_model=torch.load(BASE/'checkpoint_000024.pt',map_location='cpu',weights_only=False)
    initial=torch.load(RUN/'initial.pt',map_location='cpu',weights_only=False)
    # Metadata names this new run; all trainer/RNG payload fields must restore.
    restored={k:helpers.equal(old_model[k],initial[k]) for k in (
        'identity','model','actor_optimizer','value_optimizer','cost_weight','updates','torch_rng','cuda_rng','python_rng')}
    old_np,new_np=old_model['numpy_rng'],initial['numpy_rng']
    restored['numpy_rng']=(old_np[0]==new_np[0] and np.array_equal(old_np[1],new_np[1]) and old_np[2:]==new_np[2:])
    assert all(restored.values()) and initial['updates']==25
    model_file=RUN/('final.pt' if (RUN/'final.pt').is_file() else 'failure_last_valid.pt')
    final=torch.load(model_file,map_location='cpu',weights_only=False)
    assert final['updates']==25+n
    std=torch.cat([v.exp().flatten() for k,v in final['model'].items() if k.endswith('log_std')])
    result=dict(run=str(RUN),completed=report['completed'],stopped=report['stopped'],frames=frames,
        completed_updates=n,groups=summaries,per_update=per_update,
        partial_collection=dict(logged_discarded_transitions=groups['discarded']['count'],
            reported_discarded_transitions=(report.get('partial_collection') or {}).get('discarded_transitions',0),
            counts_consistent=groups['discarded']['count']==(report.get('partial_collection') or {}).get('discarded_transitions',0)),
        baseline_last_five_updates=read(OLD/'analysis.json')['groups']['last_five_updates'],
        ppo=dict(analytic_kl_max=max(u['analytic_kl'] for u in updates),
            max_attempted_kl=max(u['max_attempted_kl'] for u in updates),
            kl_retries=sum(u['kl_retries'] for u in updates),actor_lr_values=sorted({u['actor_lr'] for u in updates})),
        checkpoint=dict(restored_fields_identical=restored,initial_updates=25,final_updates=final['updates'],
            final_path=str(model_file),sha256=sha(model_file),
            finite=all(torch.isfinite(v).all().item() for v in final['model'].values()),
            std_mean=std.mean().item(),std_min=std.min().item(),std_max=std.max().item()),
        scope='60Hz endpoints for geometry/contact; actual 240Hz integrated music and failure union. Continuation comparison, not a controlled causal performance study.')
    write('learning_analysis.json',result)
    changed=[p for p,v in pins.items() if sha(Path(p))!=v]
    write('learning_verification.json',dict(completed=not changed,input_count=len(pins),changed_inputs=changed))
    assert not changed


if __name__=='__main__':main()
