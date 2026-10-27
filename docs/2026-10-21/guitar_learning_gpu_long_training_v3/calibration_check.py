"""Offline rate5 absorbing-horizon cost on unchanged, sealed v2 trajectories."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from statistics import mean


def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            value.update(chunk)
    return value.hexdigest()


def lines(path):
    with path.open() as stream:
        for line in stream:
            if not line.endswith('\n'):
                break
            if line.strip():
                yield json.loads(line)


def distribution(values):
    values=sorted(values)
    if not values:
        return dict(count=0)
    def quantile(p):
        x=(len(values)-1)*p
        i=int(x)
        return values[i]+(values[min(i+1,len(values)-1)]-values[i])*(x-i)
    return dict(count=len(values),mean=mean(values),min=values[0],max=values[-1],
                **{'p%d'%int(100*q):quantile(q) for q in (.25,.5,.75,.9,.95,.99)})


def analyze(source,rate):
    run=source/'train1024_large_2000'
    manifest=json.loads((source/'artifact_sha256.json').read_text())['files']
    pins={}
    for name in ('settings.json','learning_metrics.jsonl','episodes.jsonl'):
        path=run/name
        expected=manifest[str(path.relative_to(source))]
        actual=digest(path)
        if actual!=expected:
            raise ValueError('Sealed v2 input changed: '+str(path))
        pins[str(path.resolve())]=actual
    settings=json.loads((run/'settings.json').read_text())
    if settings['ppo']['cost_gamma']!=1.:
        raise ValueError('Absorbing-horizon undiscounted cost requires cost_gamma1')
    duration=settings['song_training']['episode_duration_s']
    weight=settings['ppo']['cost_weight']
    committed={r['update_index'] for r in lines(run/'learning_metrics.jsonl') if r['update_index']<=499}
    groups=defaultdict(list)
    first_safe={}
    for row in lines(run/'episodes.jsonl'):
        u=row['update_index']
        if u not in committed:
            continue
        e=row['episode']
        failed=e['reason']=='terminal_failure'
        extra=rate*max(0.,duration-e['task_time_s']) if failed else 0.
        value=dict(duration_s=e['task_time_s'],cost_before=e['cost'],extra=extra,cost_after=e['cost']+extra,
            reward=e['reward'],undiscounted_R_minus_cost_before=e['reward']-weight*e['cost'],
            undiscounted_R_minus_cost_after=e['reward']-weight*(e['cost']+extra))
        safe=e['reason']=='timeline_complete' and e['left_curriculum']['full_safe']
        if safe:
            first_safe.setdefault(e['env_id'],value)
        if not 400<=u<=499:
            continue
        groups['all'].append(value)
        groups['all_failures' if failed else 'full_safe' if safe else 'other_end'].append(value)
        if failed and e['task_time_s']<1.:
            groups['failures_less_than_1s'].append(value)
    groups['first_safe_song_per_environment']=list(first_safe.values())
    return dict(schema='guitar_learning.remaining_song_cost_offline.v1',rate_cost_per_s=rate,
        source_phase=str(source.resolve()),verified_sealed_inputs=pins,window_updates=[400,499],
        episode_duration_s=duration,cost_gamma=1.,cost_weight=weight,
        groups={name:{field:distribution([row[field] for row in rows]) for field in rows[0]}
                for name,rows in sorted(groups.items()) if rows},
        limitations=[
            'The <1s failure group has2073 episodes; sealed v2 reported2095 episodes at <=1s. Exactly22 episodes lasting1.0s are excluded here.',
            'Unchanged v2 trajectories are re-scored offline; no physics or policy gradient is simulated.',
            'Only complete, committed update400–499 episodes are compared. The first-safe reference is one earliest full-safe song per environment before update500.',
            'Correction is rate*max(0,episode_duration_s-task_time_s) on physical failure only. Existing accumulated physical cost and terminal +5 remain; reward is unchanged.',
            'With cost_gamma1 this is a finite absorbing-state horizon cost hypothesis, not a measurement or calibrated prediction of actual future cost.',
            'Undiscounted R-cost is descriptive. PPO uses reward gamma.99/cost gamma1 and estimated GAE advantages, so these totals do not prove actor-gradient incentives or the cause of collapse.',
            'The original first good safe-song policy already had better descriptive R-cost than recent early failures; failure is not universally optimal.',
            'Changed group ordering under this fixed rate does not establish training stability, preserved motion quality, or successful song learning.'
        ])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-phase',type=Path,default=Path(__file__).parent.with_name('guitar_learning_gpu_long_training_v2'))
    parser.add_argument('--rate',type=float,default=5.)
    parser.add_argument('--out',type=Path,default=Path(__file__).with_name('calibration_check.json'))
    args=parser.parse_args()
    if not math.isfinite(args.rate) or args.rate<0:
        parser.error('--rate must be finite and nonnegative')
    result=analyze(args.source_phase,args.rate)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({name:row['cost_before']['count'] for name,row in result['groups'].items()}))


if __name__=='__main__':
    main()
