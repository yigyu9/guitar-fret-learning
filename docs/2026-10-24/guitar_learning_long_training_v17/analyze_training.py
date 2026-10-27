"""Stream verified rewardv17 training collections into fresh JSON/Markdown reports.

Uses all ended episodes, with explicit full-safe and failed cohorts. These are
on-policy collections, not frozen-policy evaluations or inherited v8 results.
No simulator, CUDA inference, optimizer or training is executed.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path

import numpy as np
from verify_training import (PHASE, FINGERS, read, lines, require, finite, digest,
    torch, verify, verify_codec, verify_architecture, baseline_reference, json_io, encoded)

CAUSES = ('higher_time','lower_time','assignment_time','geometry_time','loaded_target_time',
    'body_load_time','facing_time','middle_target_time','distal_target_time','rejected_target_time',
    'wrong_supported_time','wrong_ambiguous_time','wrong_next_preparation_time')


def update_features(row):
    diagnostics = row['diagnostics']
    actor = diagnostics['minibatches']['actor_accepted']['sample_weighted_mean']
    value = diagnostics['minibatches']['value']['sample_weighted_mean']
    std = diagnostics['post_update']['active_distribution']['std']
    point = dict(update_index=row['update_index'], mean_reward=row['mean_reward'], mean_cost=row['mean_cost'],
        actor_lr=row['actor_lr'], cost_weight=row['cost_weight'], analytic_kl=row['analytic_kl'],
        max_attempted_kl=row['max_attempted_kl'], kl_retries=row['kl_retries'],
        actor_grad_preclip_mean=actor.get('grad_norm_pre_clip'), value_grad_preclip_mean=value.get('grad_norm_pre_clip'),
        actor_accepted_loss_mean=actor.get('loss'), reward_value_loss_mean=value.get('reward_loss'),
        cost_value_loss_mean=value.get('cost_loss'),
        std_min=std['min'], std_mean=std['mean'], std_max=std['max'],
        action_saturation=diagnostics['post_update']['active_distribution']['collected_action_saturation_fraction'],
        collection_s=row['collection_s'], update_s=row['update_s'],
        progress=row['left_curriculum']['progress'], recent_safe_fraction=row['left_curriculum']['recent_safe_fraction'],
        reward_components=row['reward_component_means'])
    advantages = diagnostics.get('advantages', {})
    for name in ('reward_raw', 'cost_raw', 'reward_normalized', 'cost_normalized',
                 'raw_combined', 'combined_raw', 'combined_normalized'):
        for statistic in ('mean', 'std'):
            point['advantage.'+name+'.'+statistic] = advantages.get(name, {}).get(statistic)
    reward_std = advantages.get('reward_raw', {}).get('std')
    cost_std = advantages.get('cost_raw', {}).get('std')
    point['raw_cost_reward_advantage_std_ratio'] = cost_std/reward_std if reward_std and cost_std is not None else None
    point['accepted_kl_mean'] = actor.get('full_rollout_kl')
    point['actor_accepted_steps'] = diagnostics['minibatches']['actor_accepted'].get('steps')
    point['actor_rejected_steps'] = diagnostics['minibatches'].get('actor_rejected', {}).get('steps')
    point['policy_ratio_clip_fraction'] = diagnostics['post_update'].get('clip_fraction')
    for name in ('reward', 'cost'):
        critic = diagnostics['post_update'].get('critics', {}).get(name, {})
        point[name+'_critic_mse'] = critic.get('mse')
        point[name+'_critic_explained_variance'] = critic.get('explained_variance')
    return point


def checkpoint_summary(path, contract):
    payload = torch.load(path, map_location='cpu', weights_only=False)
    finite(payload)
    verify_architecture(payload['identity']['architecture'])
    require(payload['model']['left_curriculum_state'].shape == (3331,), 'Checkpoint3331 shape')
    require(payload['identity']['architecture']['contract'] == contract, 'Checkpoint incremental contract mismatch')
    std = payload['model']['log_std'][:33].clamp(-5, 2).exp()
    require(bool(torch.isfinite(std).all()), 'Nonfinite checkpoint exploration std')
    return dict(path=str(path.resolve()), sha256=digest(path), optimizer_updates=payload['updates'],
        reward_schema=payload['identity']['architecture']['contract']['reward']['schema'],
        active_latent_std=dict(minimum=float(std.min()), mean=float(std.double().mean()), maximum=float(std.max())),
        curriculum_progress=float(payload['model']['left_curriculum_state'][0]),
        scope='Checkpoint parameters only; no policy inference or song evaluation')


def complete_memory_lines(path,live_tail):
    return lines(path,live_tail=live_tail)


def memory_summary(run, limit, live_tail, phase):
    caches, releases = [], Counter()
    for row in complete_memory_lines(run/'events.jsonl',live_tail):
        index = row.get('update_index')
        if index is not None and index >= limit:
            break
        if row.get('event') == 'cuda_cache_release':
            releases[row['reason']] += 1
            if row['reason'] == 'optimizer_boundary':
                after = row['after']
                caches.append(dict(update_index=index, free_GiB=after['free_bytes']/1024**3,
                    reserved_GiB=after['reserved_bytes']/1024**3, allocated_GiB=after['allocated_bytes']/1024**3))
    ram = []
    for row in complete_memory_lines(run/'resources.jsonl',live_tail):
        index = row.get('update_index')
        if index is not None and index >= limit:
            break
        ram.append(dict(update_index=index, elapsed_s=row['elapsed_s'], free_GiB=row['available_memory_bytes']/1024**3,
                        parent_RSS_GiB=row['parent_memory']['rss_current_bytes']/1024**3))
    disk = []
    progress_path=phase/'progress.jsonl'
    if progress_path.is_file():
        for row in complete_memory_lines(progress_path,live_tail):
            if row.get('run') is None or Path(row['run']).resolve() != run.resolve():
                continue
            count = row.get('optimizer_updates')
            if count is not None and count > limit:break
            if count is not None and count <= limit:
                disk.append({key:row.get(key) for key in ('optimizer_updates','elapsed_s','disk_free_bytes','local_disk_free_bytes','run_bytes')})
    base = caches[0]['free_GiB']+caches[0]['reserved_GiB'] if caches else None
    for row in caches:
        row['estimated_nonTorch_growth_GiB'] = base-row['free_GiB']-row['reserved_GiB']
    return dict(cache_boundaries=caches, RAM_samples=ram, disk_samples=disk, cache_release_reasons=dict(releases),
        minimum_post_cache_free_GiB=min((r['free_GiB'] for r in caches), default=None),
        minimum_observed_disk_free_GiB=min((r['disk_free_bytes']/1024**3 for r in disk if r['disk_free_bytes'] is not None),default=None),
        minimum_observed_local_disk_free_GiB=min((r['local_disk_free_bytes']/1024**3 for r in disk if r['local_disk_free_bytes'] is not None),default=None),
        disk_samples_path=str(progress_path.resolve()),
        disk_scope='disk_free_bytes: external run filesystem; local_disk_free_bytes: project filesystem; run_bytes: run files; only explicit matching run paths are used, legacy rows without run are excluded; missing samples stay unknown',
        minimum_RAM_free_GiB=min((r['free_GiB'] for r in ram), default=None),
        scope='Logged samples only; free+reserved residual does not identify native allocation ownership or prove an SDK leak')


class Summary:
    """Bounded arrays only; never retain ended episodes or double-add cumulative counters."""
    def __init__(self, schedule):
        self.schedule=schedule; self.count=0; self.totals=Counter(); self.reasons=Counter()
        self.environments=set(); self.first=self.last=None
        self.lengths=np.asarray([t['end_s']-t['onset_s'] for t in schedule])
        self.required=np.minimum(self.lengths,np.maximum(.05,.4*self.lengths))
        m=len(schedule)
        keys=('left','near_done','contact_done','clean','wrong','missing','best_clean_streak',
              'clean_streak','contact_streak','contact_time','exposure_time','near_time',*CAUSES)
        self.notes={k:np.zeros(m) for k in keys}
        self.notes.update(deficit=np.zeros(m),observed_audible=np.zeros(m),
            exposed_episodes=np.zeros(m),surface_min_sum=np.zeros(m))
        self.sources=np.zeros((m,10,3));self.source_seen=np.zeros((m,10))
        self.fret_min=np.full((m,10),23);self.fret_max=np.zeros((m,10))
        self.body_names=None

    def add(self, episode, update):
        self.count+=1;self.environments.add(episode['env_id'])
        self.first=update if self.first is None else min(self.first,update)
        self.last=update if self.last is None else max(self.last,update)
        safe=episode['reason']=='timeline_complete';failed=episode['reason']=='terminal_failure'
        self.reasons.update(episode['failure_reasons'])
        self.totals.update(timeline_complete=int(safe),physical_failure=int(failed),
            task_success=int(episode['song']['stage_success']),reward=episode['reward'],cost=episode['cost'],
            task_time_s=episode['task_time_s'],achieved_notes=episode['song']['left_success_count'],
            failure_time_s=episode['task_time_s'] if failed else 0.,
            original_cost=episode['cost_components']['original_physics_and_terminal'],
            remaining_failure_cost=episode['cost_components']['remaining_song_failure'])
        for k,v in episode['reward_components'].items(): self.totals['reward_component.'+k]+=v
        values=episode['left_note_ledger']['values']
        for key in self.notes:
            if key in values: self.notes[key]+=np.asarray(values[key],dtype=float)
        best=np.asarray(values['best_clean_streak'])
        self.notes['deficit']+=1-np.minimum(best/self.required,1.)
        self.notes['observed_audible']+=np.asarray([max(0.,min(episode['task_time_s'],t['end_s'])-t['onset_s']) for t in self.schedule])
        exposed=np.asarray(values['exposure_time'])>0
        self.notes['exposed_episodes']+=exposed
        self.notes['surface_min_sum']+=np.where(exposed,values['surface_min'],0.)
        provenance=episode['left_note_ledger']['wrong_press_sources']
        if self.body_names is None:self.body_names=provenance['body_names']
        require(self.body_names==provenance['body_names'],'Stable source body order')
        source=np.asarray(provenance['values']['wrong_source_time']);seen=source.sum(-1)>0
        self.sources+=source;self.source_seen+=seen
        self.fret_min=np.minimum(self.fret_min,np.where(seen,provenance['values']['wrong_source_fret_min'],23))
        self.fret_max=np.maximum(self.fret_max,np.where(seen,provenance['values']['wrong_source_fret_max'],0))

    def metrics(self, indices):
        n=self.count;ids=np.asarray(indices,dtype=int);count=len(ids)
        scheduled=n*float(self.lengths[ids].sum())
        observed=float(self.notes['observed_audible'][ids].sum())
        summed={k:float(v[ids].sum()) for k,v in self.notes.items()}
        denominator=n*count
        return dict(ended_episodes=n,targets_per_episode=count,note_episode_denominator=denominator,
            scheduled_audible_seconds=scheduled,observed_audible_seconds=observed,
            note_fractions={name:summed[key]/denominator if denominator else None for name,key in
                (('success','left'),('near','near_done'),('contact','contact_done'))},
            mean_clean_fraction_per_scheduled_note=float((self.notes['clean'][ids]/self.lengths[ids]).sum()/denominator) if denominator else None,
            mean_best_streak_fraction_of_required=float((1-self.notes['deficit'][ids]/n).mean()) if n and count else None,
            mean_deficit=summed['deficit']/denominator if denominator else None,
            mean_best_clean_streak_s=summed['best_clean_streak']/denominator if denominator else None,
            wrong_fraction_scheduled=summed['wrong']/scheduled if scheduled else None,
            missing_fraction_scheduled=summed['missing']/scheduled if scheduled else None,
            wrong_fraction_observed=summed['wrong']/observed if observed else None,
            missing_fraction_observed=summed['missing']/observed if observed else None,
            observed_clean_fraction=summed['clean']/observed if observed else None,
            exposure_note_episodes=int(summed['exposed_episodes']),
            surface_min_when_exposed_m=summed['surface_min_sum']/summed['exposed_episodes'] if summed['exposed_episodes'] else None,
            seconds={k:summed[k] for k in ('clean','wrong','missing','contact_time','exposure_time',*CAUSES)})

    def result(self, detailed=False):
        n=self.count
        counts={k:int(self.totals[k]) for k in ('timeline_complete','physical_failure','task_success')}
        result=dict(episodes=n,distinct_environments=len(self.environments),update_first=self.first,update_last=self.last,
            outcomes=counts,outcome_fractions={k:v/n if n else None for k,v in counts.items()},
            failure_reason_occurrences=dict(self.reasons),
            means={k:v/n for k,v in self.totals.items()} if n else {},
            all_notes=self.metrics(range(len(self.schedule))),
            fingers={f:self.metrics([i for i,t in enumerate(self.schedule) if t['finger']==j]) for j,f in enumerate(FINGERS,1)},
            failure_mean_time_s=self.totals['failure_time_s']/counts['physical_failure'] if counts['physical_failure'] else None)
        if detailed:
            result['notes']=[dict(target_id=t['target_id'],finger=t['finger'],string_1based=t['string']+1,
                fret=t['fret'],metrics=self.metrics([i])) for i,t in enumerate(self.schedule)]
        provenance=dict(causes=['higher','lower','assignment'],body_names=self.body_names,
            total_target_body_cause_seconds=self.sources.sum(0).tolist(),
            note_episode_denominator=n*len(self.schedule),
            scope='Seconds of contributing witnesses; bodies/causes overlap, never summed as exclusive wrong probability or penalty. Fret ranges include0 for ambiguous boundaries; absent ranges are null.')
        if detailed:
            provenance['targets']=[dict(target_id=t['target_id'],body_cause_seconds=self.sources[i].tolist(),
                body_observed_episode_counts=self.source_seen[i].astype(int).tolist(),
                source_fret_min=[int(v) if seen else None for v,seen in zip(self.fret_min[i],self.source_seen[i])],
                source_fret_max=[int(v) if seen else None for v,seen in zip(self.fret_max[i],self.source_seen[i])])
                for i,t in enumerate(self.schedule)]
        result['wrong_press_sources']=provenance
        return result


def bucket_updates(points):
    scalar_keys=[k for k in points[0] if k not in ('update_index','reward_components')]
    return dict(updates=len(points),update_first=points[0]['update_index'],update_last=points[-1]['update_index'],
        mean={k:math.fsum(p[k] for p in points if p[k] is not None)/sum(p[k] is not None for p in points)
              if any(p[k] is not None for p in points) else None for k in scalar_keys},
        reward_component_means={k:math.fsum(p['reward_components'][k] for p in points)/len(points)
                                for k in points[0]['reward_components']})


def analyze(run, phase, prefix=None, updates=None, verification_path=None):
    settings,contract=read(run/'settings.json'),read(run/'training_contract.json')
    control=verify_codec(contract)
    require(updates is None or settings['updates']==updates,'Expected run budget')
    limit=settings['updates'] if prefix is None else prefix
    require(type(limit) is int and 0<limit<=settings['updates'],'Selected update range')
    proof=read(verification_path) if verification_path else verify(run,phase,updates,prefix)
    require(proof['schema']=='guitar_learning.long_training_v17_verification.v1' and proof['run']==str(run.resolve()) and
            proof['committed_updates']==limit and proof['training_contract_sha256']==digest(run/'training_contract.json') and
            proof['source_manifest_sha256']==digest(phase/'training_source_manifest.json') and
            (proof['completed'] if prefix is None else proof['prefix_verified']),'Verification selection/identity')
    for name,expected in proof['evidence_sha256'].items():
        require(digest(run/name)==expected,'Verified evidence changed: '+name)
    schedule=contract['task']['provenance']['song']['schedule']
    require(len(schedule)==67,'67-note schedule')
    groups={};curve=[];changes=[];previous=None
    metrics_hash,episodes_hash=hashlib.sha256(),hashlib.sha256()
    for i,row in enumerate(lines(run/'learning_metrics.jsonl',live_tail=prefix is not None)):
        if i==limit:break
        finite(row)
        metrics_hash.update(encoded(row)+b'\n')
        require(row['update_index']==i and row['journal']['committed']==(i+1)*settings['num_envs']*settings['horizon'],'Committed update selection')
        point=update_features(row);curve.append(point)
        if row['left_curriculum']['progress']!=previous:
            changes.append(dict(update_index=i,**row['left_curriculum']))
            previous=row['left_curriculum']['progress']
        for episode in row['completed_episodes']:
            cohort='full_safe' if episode['reason']=='timeline_complete' else 'physical_failure'
            names=['overall/all_ended','overall/'+cohort]
            for width in (100,250):
                span='%04d_%04d'%(i//width*width,min((i//width+1)*width,limit)-1)
                names+=['updates_%d/%s/all_ended'%(width,span),'updates_%d/%s/%s'%(width,span,cohort)]
            for name in names:
                if name not in groups:groups[name]=Summary(schedule)
                groups[name].add(episode,i)
    require(len(curve)==limit,'Selected committed rows fully available')
    require(metrics_hash.hexdigest()==proof['selected_metrics_sha256'],'Verified selected metrics changed')
    for row in lines(run/'episodes.jsonl',live_tail=prefix is not None):
        if row['update_index']>=limit:break
        episodes_hash.update(encoded(row)+b'\n')
    require(episodes_hash.hexdigest()==proof['selected_episodes_sha256'],'Verified selected episode rows changed')
    for name in ('all_ended','full_safe','physical_failure'):
        groups.setdefault('overall/'+name,Summary(schedule))
    buckets={}
    for width in (100,250):
        for start in range(0,limit,width):
            points=curve[start:start+width]
            buckets['%d/%04d_%04d'%(width,start,start+len(points)-1)]=bucket_updates(points)
    checkpoint=Path(proof['checked_checkpoint_path'])
    require(digest(checkpoint)==proof['checked_checkpoint_sha256'],'Verified checkpoint changed')
    models=[checkpoint_summary(run/'initial.pt',contract)]
    if checkpoint!=(run/'initial.pt'):models.append(checkpoint_summary(checkpoint,contract))
    return dict(schema='guitar_learning.long_training_v17_analysis.v1',generated_at_utc=datetime.now(timezone.utc).isoformat(),
        run=str(run.resolve()),mode='final_completed' if prefix is None else 'committed_prefix',
        selected_committed_updates=limit,committed_transitions=limit*settings['num_envs']*settings['horizon'],
        final_completed=prefix is None,execution_verification=proof,
        training_contract_sha256=digest(run/'training_contract.json'),source_manifest_sha256=digest(phase/'training_source_manifest.json'),
        settings=settings,action_codec=control['action_codec'],baseline_implementation=baseline_reference(),
        update_curve=curve,update_buckets=buckets,curriculum_changes=changes,
        episode_groups={name:g.result(detailed=name.startswith('overall/')) for name,g in sorted(groups.items())},
        checkpoint_parameters=models,memory=memory_summary(run,limit,prefix is not None,phase),
        limitations=[
            'On-policy collections only; fixed-policy evaluation/checkpoint selection and videos are separate evidence.',
            'All-ended and failed cohorts retain all67 scheduled notes, including future unvisited notes. Full-safe is an explicitly selected secondary cohort, never the overall denominator.',
            'Pooled scheduled and observed audible denominators are both reported; a short physical failure can have low observed wrong yet poor total task performance.',
            'Update means average equal1024x32 batches. Ended-song summaries average each ended episode once; cumulative counters are not summed across update rows.',
            'best_clean_streak is longest audible continuous clean, not cumulative clean or final current streak. Deficit is1-min(best/required,1), including unvisited notes as1.',
            'Wrong source body/cause seconds may overlap. Supported/ambiguous are source geometry diagnostics, not contact-pair, pressure or sound certification; next preparation grants no exemption.',
            'Curriculum can change within a song; cross-stage total reward is not a fixed-weight performance score. Repeated environments/songs are not independent seeds.',
            'KL/latent std/accepted-minibatch gradients and critic-fit summaries are diagnostics, not causal policy-gradient attribution or naturalness.',
            'Prefix mode certifies only selected committed members; no final EOF, simulator cleanup or whole-run completion claim.',
            'Current source451, sealed implementation delivery and v17/preparation.v2 contracts are checked explicitly. No past v16/v8 scores or cumulative-success invariants are inherited.',
            'B preparation now excludes each finger only for its own idle/contact/assigned-target proximity. Collection ledgers do not log per-finger final B gate/quality, so a standby total alone cannot prove which finger earned it.'
        ])


def markdown(result):
    g=result['episode_groups'];all_ended=g['overall/all_ended'];updates=result['selected_committed_updates']
    out=['# v17 학습 수집 로그 분석','',f"선택 범위: {updates:,} 업데이트 · {result['committed_transitions']:,} 전이 · {result['mode']}",'',
         '고정 정책 평가와 구분한 학습 중 수집 결과다. 물리 안전 완주와 67음 과제 성공은 별도다.','',
         '| 종료곡 집단 | 종료 수 | 안전 시간축 완주 | 물리 실패 | 과제 성공 | 평균 달성음/67 | 평균 비용 |',
         '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name in ('all_ended','full_safe','physical_failure'):
        row=g['overall/'+name];c=row['outcomes'];m=row['means']
        out.append('| %s | %d | %d | %d | %d | %s | %s |'%(name,row['episodes'],c['timeline_complete'],c['physical_failure'],c['task_success'],
            '—' if not row['episodes'] else '%.4f'%m['achieved_notes'],'—' if not row['episodes'] else '%.4f'%m['cost']))
    out+=['','모든 종료곡을 기본 분모로 사용한다. 실패곡의 아직 도달하지 않은 음도 67음 분모에 남는다.','',
          '| 손가락: 전체 종료곡 | 배정음×종료곡 | 달성 | 최초접촉 | near | 평균 부족률 |',
          '| --- | ---: | ---: | ---: | ---: | ---: |']
    for f,row in all_ended['fingers'].items():
        if row['note_episode_denominator']:
            fmt=lambda v:'%.2f%%'%(100*v)
            out.append('| %s | %d | %s | %s | %s | %.4f |'%(f,row['note_episode_denominator'],fmt(row['note_fractions']['success']),fmt(row['note_fractions']['contact']),fmt(row['note_fractions']['near']),row['mean_deficit']))
    out+=['','`analysis.json`에 100/250업데이트 구간별 보상·비용·항별 기여·PPO KL/gradient/std/critic·단계 변화와 전체/안전/실패별 음·몸체 원인 진단을 저장했다.','',
          'wrong/missing 초 진단은 보상과 단위가 다르다. 원인별 몸체 시간은 겹칠 수 있어 합산 비율이나 추가 감점으로 해석하지 않는다. 평균 달성음은 음 끝까지의 완전한 연주율이 아니다.','',
          '이 결과만으로 장기 수렴·자연스러움·다곡/다중 seed 일반화·실제 압력/음향을 입증하지 않는다.']
    return '\n'.join(out)+'\n'


def plot(result, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    curve=result['update_curve'];x=[p['update_index']+1 for p in curve]
    fig,axs=plt.subplots(2,2,figsize=(12,8))
    for k in ('mean_reward','mean_cost'):axs[0,0].plot(x,[p[k] for p in curve],label=k)
    axs[0,0].set_title('All transitions: collection means')
    axs[0,1].plot(x,[p['progress'] for p in curve],label='curriculum progress')
    axs[0,1].plot(x,[p['recent_safe_fraction'] for p in curve],label='recent safety')
    for cohort in ('all_ended','full_safe','physical_failure'):
        rows=[(name,g) for name,g in result['episode_groups'].items() if name.startswith('updates_100/') and name.endswith('/'+cohort)]
        rows.sort(key=lambda item:item[1]['update_first'] if item[1]['update_first'] is not None else -1)
        centers=[(r['update_first']+r['update_last'])/2+1 for _,r in rows]
        axs[1,0].plot(centers,[r['means']['achieved_notes'] for _,r in rows],label=cohort)
        axs[1,1].plot(centers,[r['all_notes']['mean_deficit'] for _,r in rows],label=cohort)
    axs[1,0].set_title('Ended-song achieved notes /67');axs[1,1].set_title('Longest clean streak deficit / all notes')
    for ax in axs.flat:ax.grid(alpha=.25);ax.legend(fontsize=8);ax.set_xlabel('Update')
    fig.suptitle('v17 training collections; fixed-policy evaluation is separate');fig.tight_layout();fig.savefig(output/'training.png',dpi=150);plt.close(fig)
    fig,axs=plt.subplots(2,2,figsize=(12,8))
    for k in ('analytic_kl','max_attempted_kl','accepted_kl_mean'):axs[0,0].plot(x,[p[k] for p in curve],label=k)
    for k in ('std_min','std_mean','std_max'):axs[0,1].plot(x,[p[k] for p in curve],label=k)
    for k in ('actor_grad_preclip_mean','value_grad_preclip_mean'):axs[1,0].plot(x,[p[k] for p in curve],label=k)
    for k in ('reward_critic_explained_variance','cost_critic_explained_variance'):axs[1,1].plot(x,[p[k] for p in curve],label=k)
    for ax in axs.flat:ax.grid(alpha=.25);ax.legend(fontsize=8);ax.set_xlabel('Update')
    fig.suptitle('KL, latent std, accepted gradients and critic fit');fig.tight_layout();fig.savefig(output/'ppo.png',dpi=150);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',type=Path,default=PHASE);parser.add_argument('--run',type=Path)
    parser.add_argument('--updates',type=int);parser.add_argument('--prefix',type=int)
    parser.add_argument('--verification',type=Path);parser.add_argument('--plots',action='store_true')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args();phase=args.phase.resolve();run=(args.run or phase/'train2000').resolve()
    out=args.out or phase/('analysis_final' if args.prefix is None else 'analysis_prefix_%06d'%args.prefix)
    require(not out.exists(),'Use a new analysis output directory');torch.set_num_threads(1)
    result=analyze(run,phase,args.prefix,args.updates,args.verification)
    out.mkdir(parents=True,exist_ok=False)
    with (out/'analysis.json').open('x') as stream:json_io.dump(result,stream,indent=2,allow_nan=False)
    (out/'analysis.md').write_text(markdown(result))
    if args.plots:plot(result,out)
    print(json_io.dumps(dict(mode=result['mode'],updates=result['selected_committed_updates'],out=str(out))))


if __name__=='__main__':main()
