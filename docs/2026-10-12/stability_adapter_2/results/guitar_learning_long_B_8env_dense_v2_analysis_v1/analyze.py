"""Stream immutable training logs; distinguish committed and discarded data."""
import collections
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

OUT = Path(__file__).resolve().parent
RUN = OUT.parent/'guitar_learning_long_B_8env_dense_v2_20261018_130137'
ROOT = OUT.parents[4]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def write(name, value):
    with (OUT/name).open('x') as f:
        json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)
        f.write('\n')


def bucket():
    return dict(count=0,reward=0.,cost=0.,terms=collections.Counter(),episodes=[],
        matched50_max=0,matched100_max=0,held_max=0.,candidate_count=0,
        failure_count=0,any_support=0,triple_support=0,both_feet=0,
        guitar_max_m=0.,foot_max_m=0.,rotation_max_rad=0.,joint_speed_max=0.,
        metrics=collections.defaultdict(list),action_sum=np.zeros(39),
        action_square_sum=np.zeros(39),action_abs_sum=np.zeros(39),action_saturation=0)


def add(b,info,reward):
    b['count']+=1;b['reward']+=reward;b['cost']+=info['cost'];b['terms'].update(info['reward_terms'])
    for field in ('matched50','matched100'):b[field+'_max']=max(b[field+'_max'],info['music'][field])
    b['held_max']=max(b['held_max'],info['music']['held_total_s'])
    b['candidate_count']+=int(any(info['fret_candidates'].values()))
    b['failure_count']+=int(bool(info['failure_reasons']))
    s=info['stability'];flags=s['flags'];b['any_support']+=int(any(flags[:3]));b['triple_support']+=int(all(flags[:3]));b['both_feet']+=int(all(flags[-2:]))
    b['guitar_max_m']=max(b['guitar_max_m'],float(np.linalg.norm(s['guitar_delta_m'])))
    b['rotation_max_rad']=max(b['rotation_max_rad'],float(np.linalg.norm(s['guitar_rotation_vector_rad'])))
    b['foot_max_m']=max(b['foot_max_m'],float(np.linalg.norm(s['foot_delta_m'],axis=1).max()))
    b['joint_speed_max']=max(b['joint_speed_max'],s['max_joint_speed_rad_s'])
    time=info['task_time_s'];left=min(info['goal_distance_m'].values())
    b['metrics']['left_all_m'].append(left)
    if 1.-1e-9<=time<=1.12+1e-9:b['metrics']['left_press_to_onset_m'].append(left)
    if abs(time-67/60)<1e-9:b['metrics']['left_near_onset_m'].append(left)
    g=info.get('pick_guide')
    if g:
        b['metrics']['right_guide_all_m'].append(g['distance_m'])
        if g['sweep_active']:b['metrics']['right_sweep_m'].append(g['distance_m'])
    a=np.asarray(info['debug']['action']);b['action_sum']+=a;b['action_square_sum']+=a*a;b['action_abs_sum']+=np.abs(a)
    b['action_saturation']+=int((np.abs(a)>.9).sum())
    if 'episode' in info:b['episodes'].append(dict(info['episode'],music=info['music']))


def summary(b):
    n=b['count'];result={k:v for k,v in b.items() if k not in ('metrics','action_sum','action_square_sum','action_abs_sum','episodes')}
    result['terms']=dict(result['terms']);result['episode_count']=len(b['episodes'])
    result['episode_reward_mean']=float(np.mean([e['reward'] for e in b['episodes']])) if b['episodes'] else None
    result['episode_cost_mean']=float(np.mean([e['cost'] for e in b['episodes']])) if b['episodes'] else None
    result['episode_reasons']=dict(collections.Counter(e['reason'] for e in b['episodes']))
    result['completed_episode_missed_strict']=sum(e['music']['missed_strict'] for e in b['episodes'])
    result['metrics']={k:dict(count=len(v),mean=float(np.mean(v)),min=float(np.min(v)),max=float(np.max(v))) for k,v in b['metrics'].items()}
    result['action_channel_mean']=(b['action_sum']/n).tolist()
    result['action_channel_std']=np.sqrt(np.maximum(b['action_square_sum']/n-(b['action_sum']/n)**2,0)).tolist()
    result['action_role_mean_abs']={k:float(np.mean((b['action_abs_sum']/n)[a:z])) for k,a,z in [('left_arm',0,12),('left_fingers',12,33),('right_elbow_wrist',33,39)]}
    return result


def equal(a,b):
    if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return type(a) is type(b) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b


def main():
    inputs={Path(__file__).resolve(),ROOT/'docs/plans/guitar_learning_long_B_8env_analysis_20261018.md'}
    for pattern in ('report.json','settings.json','status.json','training_contract.json','inputs_before.json',
                    'transitions.jsonl.gz','update_*.json','initial.pt','checkpoint_000024.pt','failure_last_valid.pt'):
        inputs.update(RUN.glob(pattern))
    inputs.update(ROOT/'guitar_learning'/name for name in ('parallel.py','ppo.py','training_environment.py','dense_environment.py','safety.py','task_measurement.py','music_task.py'))
    pins={str(p):sha(p) for p in sorted(inputs)};write('inputs_before.json',pins)
    report=read(RUN/'report.json');settings=report['settings'];updates=report['updates'];committed=report['transitions']
    per=[bucket() for _ in range(len(updates)+1)]
    groups={k:bucket() for k in ('committed','discarded','first_five_updates','last_five_updates')}
    frames=0
    with gzip.open(RUN/'transitions.jsonl.gz','rt') as stream:
        for frame,line in enumerate(stream):
            row=json.loads(line);index=frame//settings['horizon'];assert index<len(per)
            for info,reward in zip(row['infos'],row['reward']):
                add(per[index],info,reward)
                add(groups['committed' if index<len(updates) else 'discarded'],info,reward)
                if index<5:add(groups['first_five_updates'],info,reward)
                if len(updates)-5<=index<len(updates):add(groups['last_five_updates'],info,reward)
            frames+=1
    result=dict(run=str(RUN),frames=frames,completed_updates=len(updates),
        groups={k:summary(v) for k,v in groups.items()},per_update=[])
    assert groups['committed']['count']==committed
    assert groups['discarded']['count']==report['partial_collection']['discarded_transitions']
    for i,b in enumerate(per):
        result['per_update'].append(dict(update_index=i,committed=i<len(updates),**summary(b)))
        if i<len(updates):
            assert len(b['episodes'])==len(updates[i]['completed_episodes'])
            assert abs(b['reward']-sum(b['terms'].values()))<1e-6
    result['ppo']=dict(analytic_kl_max=max(u['analytic_kl'] for u in updates),
        max_attempted_kl=max(u['max_attempted_kl'] for u in updates),kl_retries=sum(u['kl_retries'] for u in updates),
        actor_lr_values=sorted({u['actor_lr'] for u in updates}),
        first={k:updates[0][k] for k in ('actor_loss','reward_value_loss','cost_value_loss','actor_grad_norm')},
        last={k:updates[-1][k] for k in ('actor_loss','reward_value_loss','cost_value_loss','actor_grad_norm')})
    models={name:torch.load(RUN/name,map_location='cpu',weights_only=False) for name in ('initial.pt','checkpoint_000024.pt','failure_last_valid.pt')}
    a,b=models['checkpoint_000024.pt'],models['failure_last_valid.pt']
    restored={key:equal(a[key],b[key]) for key in ('identity','model','actor_optimizer','value_optimizer','updates','cost_weight')}
    assert all(restored.values()) and b['updates']==25
    result['checkpoint']=dict(last_regular_and_recovery_identical=restored,files={})
    for name,d in models.items():
        tensors=d['model'];std=torch.cat([v.exp().flatten() for k,v in tensors.items() if k.endswith('log_std')])
        result['checkpoint']['files'][name]=dict(updates=d['updates'],finite=all(torch.isfinite(v).all().item() for v in tensors.values()),
            model_scalar_count=sum(v.numel() for v in tensors.values()),std_mean=std.mean().item(),std_min=std.min().item(),std_max=std.max().item(),sha256=pins[str(RUN/name)])
    write('analysis.json',result)
    changed=[p for p,h in pins.items() if sha(Path(p))!=h]
    write('analysis_verification.json',dict(completed=not changed,changed_inputs=changed,input_count=len(pins)))
    assert not changed


if __name__=='__main__':main()
