"""Stream the saved1300 + resumed700 policy path, keeping the lost branch separate.

CPU-only, no policy inference/native context. Historical close and full EOF are
not inferred; the resumed process starts new prepared physical episodes.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import math
from pathlib import Path
import numpy as np
import analyze_training as core
import verify_recovery as recovery
from verify_training import (read, lines, require, finite, digest, torch, json_io,
    verify_codec, verify_motion, MOTION_FIELDS, BASE_FIELDS, BASE_NAMES, LEFT_HAND_NAMES)
from analyze_training import FINGERS, Summary, episode_features, update_features, checkpoint_summary


def chain_memory(segments, phase, relocation):
    result=dict(cache_boundaries=[],RAM_samples=[],disk_samples=[],processes=[])
    for run,count,offset in segments:
        value=core.memory_summary(run,count,True,phase)
        disk=[]
        progress=phase/'progress.jsonl'
        equivalent={str(run.resolve())}
        if offset==0:equivalent.add(str(Path(relocation['source']).resolve()))
        if progress.is_file():
            for row in lines(progress,live_tail=True):
                if row.get('run') is None or str(Path(row['run']).resolve()) not in equivalent:continue
                update=row.get('optimizer_updates')
                if update is not None and offset < update <= offset+count:
                    disk.append({key:row.get(key) for key in ('optimizer_updates','elapsed_s','disk_free_bytes','local_disk_free_bytes','run_bytes')})
        value['disk_samples']=disk
        value['minimum_observed_disk_free_GiB']=min((r['disk_free_bytes']/1024**3 for r in disk if r['disk_free_bytes'] is not None),default=None)
        value['minimum_observed_local_disk_free_GiB']=min((r['local_disk_free_bytes']/1024**3 for r in disk if r['local_disk_free_bytes'] is not None),default=None)
        result['processes'].append(dict(run=str(run),optimizer_offset=offset,selected_local_updates=count,**value))
        for key in ('cache_boundaries','RAM_samples'):
            for row in value[key]:
                mapped=dict(row,run=str(run),optimizer_offset=offset,local_update_index=row['update_index'])
                if mapped['update_index'] is not None:mapped['update_index']+=offset
                result[key].append(mapped)
        result['disk_samples'].extend(dict(row,run=str(run)) for row in disk)
    result['cache_release_reasons']=dict(sum((Counter(v['cache_release_reasons']) for v in result['processes']),Counter()))
    for key,rows,field in (('minimum_post_cache_free_GiB',result['cache_boundaries'],'free_GiB'),
                           ('minimum_RAM_free_GiB',result['RAM_samples'],'free_GiB')):
        result[key]=min((r[field] for r in rows),default=None)
    result['minimum_observed_disk_free_GiB']=min((r['disk_free_bytes']/1024**3 for r in result['disk_samples'] if r['disk_free_bytes'] is not None),default=None)
    result['minimum_observed_local_disk_free_GiB']=min((r['local_disk_free_bytes']/1024**3 for r in result['disk_samples'] if r['local_disk_free_bytes'] is not None),default=None)
    result['scope']='Selected samples only, global update axis. CUDA free+reserved residual has an independent baseline per process, never summed as native leak growth. Wall elapsed remains local to each process. disk_free_bytes refers to each run filesystem (historical external versus resumed local); startup RAM samples without an update index are retained in JSON and omitted from the update-axis plot. Only explicit run-matching progress or manifest-proved original path is used; legacy disk rows stay unknown.'
    return result


def analyze(phase, old_run=None, run=None, copy_manifest=None, prefix=None, verification_path=None):
    old_run=(old_run or phase/'recovered_train2000_restart1').resolve()
    run=(run or phase/'train_resume700').resolve()
    copy_manifest=copy_manifest or phase/'recovery_copy_manifest.json'
    limit=2000 if prefix is None else prefix
    require(type(limit) is int and 1300<=limit<=2000,'Selected global update count1300..2000')
    verification_path=verification_path or phase/('recovery_verification.json' if prefix is None else 'recovery_verification_prefix_%06d.json'%prefix)
    proof=read(verification_path) if verification_path.is_file() else recovery.verify(phase,old_run,run,copy_manifest,prefix)
    require(proof['schema']=='guitar_learning.long_training_v6_recovery_verification.v1' and
            proof['old_run']==str(old_run) and proof['run']==str(run) and
            proof['copy_manifest_sha256']==digest(copy_manifest) and
            proof['source_manifest_sha256']==digest(phase/'training_source_manifest.json'), 'Recovery proof identity')
    require(proof['committed_updates']==limit and proof['committed_transitions']==limit*32768 and
            (proof['completed'] if prefix is None else proof['prefix_verified']), 'Recovery proof selected budget')
    contract=read(old_run/'training_contract.json');control=verify_codec(contract)
    settings=read(old_run/'settings.json')
    require(digest(old_run/'training_contract.json')==proof['segments'][0]['training_contract_sha256'],'Historical contract proof SHA')
    segments=[(old_run,1300,0)]
    if limit>1300:
        require(read(run/'training_contract.json')==contract and
                digest(run/'training_contract.json')==proof['segments'][1]['training_contract_sha256'],'Resumed contract proof')
        segments.append((run,limit-1300,1300))
    schedule=contract['task']['provenance']['song']['schedule']
    require(len(schedule)==67,'Expected67-note schedule')
    lengths=np.asarray([t['end_s']-t['onset_s'] for t in schedule])
    groups,update_buckets,curve,changes={},defaultdict(list),[],[]
    previous=None
    for path,count,offset in segments:
        metrics=iter(lines(path/'learning_metrics.jsonl'))
        for local in range(count):
            row=next(metrics,None);index=offset+local
            require(row is not None and row['update_index']==local and row['optimizer_updates']==index+1,'Segment update/global optimizer order')
            require(row['journal']['committed']==(local+1)*32768,'Segment commit count')
            finite(row);point=update_features(row)
            point.update(update_index=index,local_update_index=local,optimizer_offset=offset)
            curve.append(point)
            if point['progress']!=previous:
                changes.append(dict(update_index=index,committed_updates=index+1,committed_transitions=(index+1)*32768,
                    **{key:row['left_curriculum'][key] for key in ('progress','stage','weights','recent_safe_fraction','recent_fingers')}))
                previous=point['progress']
            for width in (100,250):update_buckets[(width,index//width)].append(point)
            for episode in row['completed_episodes']:
                verify_motion(episode,control)
                features,note_values,safe=episode_features(episode,lengths)
                for cohort in ('all_ended','full_safe' if safe else 'physical_failure'):
                    names=['overall/'+cohort]+['updates_%d/%04d_%04d/%s'%(width,index//width*width,min((index//width+1)*width,limit)-1,cohort) for width in (100,250)]
                    for name in names:
                        if name not in groups:groups[name]=Summary(notes=name.startswith('overall/'))
                        groups[name].add(episode,features,index,note_values)
    compact={}
    scalar_keys=[key for key in curve[0] if key not in ('update_index','local_update_index','optimizer_offset','reward_components')]
    for (width,group),points in update_buckets.items():
        mean={key:float(np.mean([p[key] for p in points if p[key] is not None])) if any(p[key] is not None for p in points) else None for key in scalar_keys}
        compact['%d/%04d_%04d'%(width,group*width,min((group+1)*width,limit)-1)]=dict(updates=len(points),mean=mean,
            actor_lr_min=min(p['actor_lr'] for p in points),actor_lr_max=max(p['actor_lr'] for p in points),
            max_attempted_kl=max(p['max_attempted_kl'] for p in points),
            reward_component_means={k:math.fsum(p['reward_components'][k] for p in points)/len(points) for k in points[0]['reward_components']})
    summaries={}
    for name,group in sorted(groups.items()):
        summaries[name]=group.result(schedule)
        if name.startswith('updates_'):
            first,last=(int(v) for v in name.split('/')[1].split('_'))
            summaries[name].update(bucket_first=first,bucket_last=last)
    models=[checkpoint_summary(old_run/'initial.pt',contract),checkpoint_summary(Path(proof['checked_checkpoint_path']),contract)]
    require(models[-1]['sha256']==proof['checked_checkpoint_sha256'] and models[-1]['optimizer_updates']<=limit,'Selected checkpoint proof')
    if prefix is None:require(models[-1]['optimizer_updates']==2000,'Final optimizer2000 checkpoint')
    relocation=read(copy_manifest)
    return dict(schema='guitar_learning.long_training_v6_recovery_analysis.v1',generated_at_utc=datetime.now(timezone.utc).isoformat(),
        mode='final_completed' if prefix is None else 'committed_prefix',run=str(run),old_run=str(old_run),
        selected_committed_updates=limit,last_update_index=limit-1,committed_transitions=limit*32768,
        final_completed=prefix is None,final_execution_verified=prefix is None and proof['completed'],execution_verification=proof,
        settings=settings,segment_settings=[dict(run=str(p),optimizer_offset=o,selected_updates=n,settings=read(p/'settings.json')) for p,n,o in segments],
        action_codec=control['action_codec'],training_contract_sha256=digest(old_run/'training_contract.json'),
        source_manifest_sha256=digest(phase/'training_source_manifest.json'),previous_fixed_evaluation_reference=core.baseline_reference(phase),
        curriculum_changes=changes,update_buckets=compact,update_curve=curve,episode_groups=summaries,checkpoint_parameters=models,
        memory=chain_memory(segments,phase,relocation),
        physical_episode_boundaries=[dict(optimizer_update=1300,new_prepared_episodes=True,unfinished_old_episodes_not_joined=True)] if limit>1300 else [],
        limitations=[
            'Selected policy path is old local0..1299 plus resumed local0..699/global1300..1999. Old1300+ branch is excluded, not added to final transitions or cohort means.',
            'At1300, model/two optimizer/RNG/3331 restore exactly; physics and ongoing songs restart from prepared035/v14. No continuous2000-update native process or historical normal close is claimed.',
            'Historical raw is checked only through1300 CRC-complete updates; resumed final raw alone has full EOF/CRC and native close certification.',
            'Changing-policy training collections are not fixed-checkpoint evaluations. Repeated environments are not independent seeds or controlled causal evidence.',
            'All ended/failure cohorts retain67-note denominators; full-safe cohorts contain1969ticks. End progress may differ from progress during the song.',
            'Geometry/target-load/body-load overlap and do not establish contact pairs, pressure or sound. Near is not clean success; success uses accumulated eligible clean time.',
            'Motion/base RMS/max are equal episode means of60Hz diagnostics, not pooled RMS or240Hz extrema. Full544/8-slot policy inputs and all posture angles are not stored in standard raw logs.',
            'Memory baselines and wall clocks remain process-local. Disk rows require explicit matching run identity or verified historical path relocation; missing disk data stay unknown.' ])


def plot(value, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    curve = value['update_curve']
    x = [row['update_index']+1 for row in curve]
    subtitle = '%s: %d committed updates; training collections' % (value['mode'], value['selected_committed_updates'])
    groups = value['episode_groups']
    def centers(rows):
        return [(g['bucket_first']+g['bucket_last'])/2+1 for g in rows]
    fig, axes = plt.subplots(2, 3, figsize=(16, 8))
    for cohort in ('all_ended', 'full_safe', 'physical_failure'):
        selected = [g for name, g in groups.items() if name.startswith('updates_100/') and name.endswith('/'+cohort)]
        selected.sort(key=lambda g: g['update_first'])
        axes[0, 0].plot(centers(selected),
                        [g['mean']['achieved_notes'] for g in selected], marker='.', label=cohort)
        axes[0, 1].plot(centers(selected),
                        [100*g['mean']['clean_fraction'] for g in selected], marker='.', label=cohort)
    axes[0, 0].set(title='Achieved notes /67,100-update ended-song cohorts', ylim=(0, 67))
    axes[0, 1].set(title='Mean clean-time fraction /67 notes', ylabel='Percent', ylim=(0, 100))
    ended = [g for name, g in groups.items() if name.startswith('updates_100/') and name.endswith('/all_ended')]
    ended.sort(key=lambda g: g['update_first'])
    for key in ('full_safe', 'physical_failure'):
        axes[0, 2].plot(centers(ended),
                        [100*g['mean'][key] for g in ended], marker='.', label=key)
    axes[0, 2].set(title='Outcome / all ended songs', ylabel='Percent', ylim=(0, 100))
    safe = [g for name, g in groups.items() if name.startswith('updates_100/') and name.endswith('/full_safe')]
    safe.sort(key=lambda g: g['update_first'])
    for ax, field, title in ((axes[1, 0], 'near_fraction', 'Near10mm achievement: full-safe songs'),
                              (axes[1, 1], 'contact_fraction', 'Contact achievement: full-safe songs'),
                              (axes[1, 2], 'success_fraction', 'Note achievement: full-safe songs')):
        for name in FINGERS:
            ax.plot(centers(safe),
                    [100*g['mean'][name+'.'+field] for g in safe], marker='.', label=name)
        ax.set(title=title, ylabel='Percent', ylim=(0, 100))
        if not safe:
            ax.text(.5, .5, 'No full-safe ended songs in this snapshot', transform=ax.transAxes, ha='center')
    for ax in axes.flat:
        ax.set_xlabel('Optimizer update'); ax.grid(alpha=.25); ax.legend(fontsize=8)
    if value['selected_committed_updates'] > 1300:
        for axis in fig.axes:axis.axvline(1300,color='gray',linestyle=':',alpha=.5)
    fig.suptitle(subtitle); fig.tight_layout()
    for suffix in ('png', 'svg'):
        fig.savefig(output/('training.'+suffix), dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(3, 2, figsize=(12, 11))
    for key in ('mean_reward', 'mean_cost'):
        axes[0, 0].plot(x, [p[key] for p in curve], label=key)
    axes[0, 0].set_title('Per-transition collection means')
    for key in ('progress', 'recent_safe_fraction'):
        axes[0, 1].plot(x, [p[key] for p in curve], label=key)
    axes[0, 1].set_title('Curriculum and recent256-song safety')
    for key in ('actor_grad_preclip_mean', 'value_grad_preclip_mean'):
        axes[1, 0].plot(x, [p[key] for p in curve], label=key)
    axes[1, 0].set_yscale('log'); axes[1, 0].axhline(value['settings']['ppo']['max_grad_norm'], color='gray', ls='--', label='clip threshold')
    for key in ('analytic_kl', 'max_attempted_kl'):
        axes[1, 1].plot(x, [p[key] for p in curve], label=key)
    axes[1, 1].axhline(value['settings']['ppo']['target_kl'], color='gray', ls='--', label='target KL')
    axes[2, 0].plot(x, [p['actor_lr'] for p in curve], label='actor LR'); axes[2, 0].set_yscale('log')
    twin = axes[2, 0].twinx(); twin.plot(x, [p['cost_weight'] for p in curve], color='tab:red', label='cost weight'); twin.set_ylabel('Cost weight')
    for key in ('std_min', 'std_mean', 'std_max'):
        axes[2, 1].plot(x, [p[key] for p in curve], label=key)
    axes[2, 1].set_title('Active33 latent Gaussian std')
    for ax in axes.flat:
        ax.set_xlabel('Optimizer update'); ax.grid(alpha=.25); ax.legend(fontsize=8)
    handles, labels = axes[2, 0].get_legend_handles_labels()
    extra_handles, extra_labels = twin.get_legend_handles_labels()
    axes[2, 0].legend(handles+extra_handles, labels+extra_labels, fontsize=8)
    if value['selected_committed_updates'] > 1300:
        for axis in fig.axes:axis.axvline(1300,color='gray',linestyle=':',alpha=.5)
    fig.suptitle(subtitle); fig.tight_layout()
    for suffix in ('png', 'svg'):
        fig.savefig(output/('ppo.'+suffix), dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(4, 1, figsize=(12, 11))
    caches, ram = value['memory']['cache_boundaries'], value['memory']['RAM_samples']
    for key in ('free_GiB', 'reserved_GiB', 'allocated_GiB'):
        axes[0].plot([r['update_index']+1 for r in caches], [r[key] for r in caches], label=key)
    axes[0].set_title('GPU after optimizer-boundary cache release')
    axes[1].plot([r['update_index']+1 for r in caches], [r['estimated_nonTorch_growth_GiB'] for r in caches], label='free+reserved residual growth estimate')
    axes[1].set_title('Independent process baselines; not SDK allocation attribution')
    indexed_ram=[r for r in ram if r['update_index'] is not None]
    for key in ('free_GiB', 'parent_RSS_GiB'):
        axes[2].plot([r['update_index']+1 for r in indexed_ram], [r[key] for r in indexed_ram], label=key)
    axes[2].set_xlabel('Global optimizer update; process-local samples')
    disk=value['memory']['disk_samples']
    for field,label in (('disk_free_bytes','run filesystem available'),('local_disk_free_bytes','project available'),('run_bytes','run files')):
        samples=[r for r in disk if r[field] is not None]
        axes[3].plot([r['optimizer_updates'] for r in samples],[r[field]/1024**3 for r in samples],label=label)
    axes[3].set_xlabel('Observed optimizer update');axes[3].set_title('External monitor samples only; not an enforced runner disk guard')
    for ax in axes:
        ax.set_ylabel('GiB'); ax.grid(alpha=.25); ax.legend(fontsize=8)
    for ax in axes[:2]:
        ax.set_xlabel('Optimizer update')
    if value['selected_committed_updates'] > 1300:
        for axis in fig.axes:axis.axvline(1300,color='gray',linestyle=':',alpha=.5)
    fig.suptitle(subtitle); fig.tight_layout()
    for suffix in ('png', 'svg'):
        fig.savefig(output/('memory.'+suffix), dpi=150)
    plt.close(fig)


    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    motion_panels = (('actual_range_rad', 'Actual range: mean episode-axis rad'),
                     ('target_range_rad', 'Target range: mean episode-axis rad'),
                     ('tracking_error_rms_rad', 'Mean episode tracking RMS, rad'),
                     ('limit_outward_command_fraction', 'Outward commands at target limit, fraction'))
    for ax, (field, title) in zip(axes.flat, motion_panels):
        for name in ('thumb', *FINGERS):
            ax.plot(centers(safe), [g['mean']['motion.'+name+'.'+field] for g in safe], marker='.', label=name)
        ax.set(title=title, xlabel='Optimizer update'); ax.grid(alpha=.25); ax.legend(fontsize=8)
    fig.suptitle(subtitle+'; full-safe songs,60Hz diagnostics'); fig.tight_layout()
    for suffix in ('png', 'svg'):
        fig.savefig(output/('finger_motion.'+suffix), dpi=150)
    plt.close(fig)


    fig,axes=plt.subplots(2,3,figsize=(15,8))
    for ax,field in zip(axes.flat,BASE_FIELDS):
        for name in FINGERS:
            ax.plot(centers(safe),[g['mean']['base_pose.'+name+'.'+field] for g in safe],marker='.',label=name)
        ax.set(title=field.replace('zero_y_command_','').replace('_rad',''),xlabel='Optimizer update',ylabel='Rad')
        ax.grid(alpha=.25);ax.legend(fontsize=8)
    fig.suptitle(subtitle+'; full-safe equal episode means,60Hz diagnostic reference');fig.tight_layout()
    for suffix in ('png','svg'):fig.savefig(output/('finger_base_pose.'+suffix),dpi=150)
    plt.close(fig)


    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for name in ('coordination','standby'):
        key='song_finger_'+name
        axes[0].plot(x,[r['reward_components'][key]*60 for r in curve],label=name)
        axes[1].plot(centers(safe),[g['mean']['posture.'+name+'.realized_reward_per_s'] for g in safe],marker='.',label=name)
    for ax in axes:
        ax.axhline(.05,color='gray',linestyle='--',label='each rate upper bound')
        ax.set(xlabel='Optimizer update',ylabel='Realized reward / second');ax.grid(alpha=.25);ax.legend(fontsize=8)
    axes[0].set_title('Update mean reward x60 (all sampled ticks)')
    axes[1].set_title('Full-safe ended songs: equal episode mean')
    fig.suptitle(subtitle+'; experimental soft posture credits, not note success');fig.tight_layout()
    for suffix in ('png','svg'):fig.savefig(output/('finger_posture_reward.'+suffix),dpi=150)
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--old-run',type=Path)
    parser.add_argument('--run',type=Path)
    parser.add_argument('--copy-manifest',type=Path)
    parser.add_argument('--verification',type=Path)
    parser.add_argument('--prefix',type=int,help='Global selected committed updates1300..2000')
    parser.add_argument('--plots',action='store_true')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args();phase=args.phase.resolve()
    out=args.out or phase/('analysis_recovery_final' if args.prefix is None else 'analysis_recovery_prefix_%06d'%args.prefix)
    require(not out.exists(),'Use a new analysis output directory')
    torch.set_num_threads(1)
    result=analyze(phase,args.old_run,args.run,args.copy_manifest,args.prefix,args.verification)
    out.mkdir(parents=True,exist_ok=False)
    if args.plots:plot(result,out)
    with (out/'analysis.json').open('x') as stream:json_io.dump(result,stream,indent=2,allow_nan=False)
    print(json_io.dumps(dict(mode=result['mode'],updates=result['selected_committed_updates'],output=str(out))))


if __name__=='__main__':main()
