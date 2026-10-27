"""Read-only A500 training/evaluation analysis; never run physics or optimize.

All1024 first episodes supply actual240Hz diagnostics. Joint-pattern occupancy
and the comparable v19 fixed-window posture sample use predeclared env0..7 at
60Hz only. Missing diagnostics remain unknown rather than passing a criterion.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

PHASE = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[4]
BASELINE = ROOT/'docs/2026-10-25/guitar_learning_finger_recovery_v20/baseline_v19/evaluation_update_0500_1024'
FINGERS = ('index', 'middle', 'ring', 'pinky')
EXPOSURE_FIELDS=('planned_audible_s','observed_audible_s','approach_exposure_s','clean_s','wrong_s','missing_s')


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def ratio(numerator, denominator):
    return float(numerator/denominator) if denominator > 0 else None


def values(episodes, *keys):
    rows = []
    for episode in episodes:
        value = episode
        for key in keys:
            value = value[key]
        rows.append(value)
    return np.asarray(rows, dtype=np.float64)


def music_summary(report, targets):
    episodes = report['episodes']
    require(len(episodes) == 1024 and {r['env_id'] for r in episodes} == set(range(1024)),
        'Exact1024 first episodes required')
    safe = [r['reason'] == 'timeline_complete' and r['left_curriculum']['full_safe'] for r in episodes]
    score = values(episodes, 'song', 'left_success_count')
    require(np.isfinite(score).all() and ((score>=0)&(score<=67)&(score==np.floor(score))).all(),
        'Invalid integer achieved-note count')
    result = dict(episodes=len(episodes), achieved_mean=float(score.mean()),
        achieved_quantiles=dict(zip(('p10','p50','p90'), np.quantile(score, [.1,.5,.9]).tolist())),
        safe_complete_count=sum(safe), safe_complete_fraction=float(np.mean(safe)),
        failure_reasons=dict(Counter(flag for r in episodes for flag in r['failure_reasons'])), fingers={})
    require(len(targets) == len(report['per_note']) == 67, 'All67 note denominators required')
    for f, name in enumerate(FINGERS, 1):
        selected = [j for j, t in enumerate(targets) if t['finger'] == f]
        require(len(selected) == (25,18,12,12)[f-1], 'Per-finger target denominator differs')
        duration = sum(targets[j]['end_s']-targets[j]['onset_s'] for j in selected)
        row = dict(targets_per_song=len(selected), audible_s_per_song=duration)
        for key in ('near_fraction','contact_fraction','success_fraction','clean_fraction'):
            row[key] = float(np.mean([e['left_curriculum']['finger_metrics'][f-1][key] for e in episodes]))
        for key,field in (('near_fraction','near_done_fraction'),('contact_fraction','contact_done_fraction'),
                ('success_fraction','left_fraction')):
            exact=float(np.mean([report['per_note'][j]['all_first'][field] for j in selected]))
            require(abs(exact-row[key])<1e-6,'Per-note/finger musical summary differs')
            row[key]=exact
        row['mean_achieved_notes'] = row['success_fraction']*len(selected)
        for key in ('wrong','missing'):
            seconds = sum(report['per_note'][j]['all_first']['mean_'+key+'_s'] for j in selected)
            row[key+'_mean_s'] = seconds
            row[key+'_audible_fraction'] = ratio(seconds, duration)
        result['fingers'][name] = row
    result['wrong_audible_fraction'] = ratio(sum(r['wrong_mean_s'] for r in result['fingers'].values()),
        sum(r['audible_s_per_song'] for r in result['fingers'].values()))
    result['missing_audible_fraction'] = ratio(sum(r['missing_mean_s'] for r in result['fingers'].values()),
        sum(r['audible_s_per_song'] for r in result['fingers'].values()))
    return result


def exposure_result(count, sums):
    def row(numbers):
        result=dict(zip(EXPOSURE_FIELDS,map(float,numbers)))
        result['audible_coverage_fraction']=ratio(result['observed_audible_s'],result['planned_audible_s'])
        result['unobserved_audible_s']=max(0.,result['planned_audible_s']-result['observed_audible_s'])
        for key in ('clean','wrong','missing'):
            result[key+'_fraction_planned_audible']=ratio(result[key+'_s'],result['planned_audible_s'])
            result[key+'_fraction_observed_audible']=ratio(result[key+'_s'],result['observed_audible_s'])
        return result
    return dict(episodes=count,evaluable=count>0,
        fingers={name:row(sums[f]) for f,name in enumerate(FINGERS)},all_notes=row(sums.sum(axis=0)))


def audible_summary(episodes, targets):
    """One streaming ledger pass; approach exposure is NOT audible exposure."""
    onset=np.asarray([t['onset_s'] for t in targets])
    end=np.asarray([t['end_s'] for t in targets])
    start=np.asarray([max(0.,t['press_s']-2.) for t in targets])
    assignment=np.asarray([t['finger'] for t in targets])
    ids=[t['target_id'] for t in targets]
    require(len(targets)==67 and ((end-onset)>0).all(),'67 positive audible intervals required')
    groups={key:dict(count=0,sums=np.zeros((4,len(EXPOSURE_FIELDS))))
        for key in ('all','full_safe','failed')}
    seen=set()
    for episode in episodes:
        require(episode['env_id'] not in seen,'Duplicate first episode in ledger stream')
        seen.add(episode['env_id'])
        require(episode['valid'] and episode['left_note_ledger']['target_ids']==ids,'Valid aligned first ledger required')
        ledger=episode['left_note_ledger']['values']
        measured={key:np.asarray(ledger[key],dtype=np.float64) for key in ('exposure_time','clean','wrong','missing')}
        require(all(v.shape==(67,) and np.isfinite(v).all() and (v>=0).all() for v in measured.values()),
            'Malformed audible/approach ledger')
        duration=episode['task_time_s']
        audible=np.clip(duration-onset,0.,end-onset)
        approach=np.clip(duration-start,0.,end-start)
        require(np.allclose(measured['exposure_time'],approach,atol=1e-7,rtol=0),
            'Ledger exposure_time must match observed press-2..end, not onset..end')
        require(all((measured[k]<=audible+1e-7).all() for k in ('clean','wrong','missing')),
            'Audible metric exceeds observed interval')
        full=episode['reason']=='timeline_complete' and episode['left_curriculum']['full_safe']
        require(full or episode['reason']=='terminal_failure','Unexpected unsafe timeline episode')
        table=np.stack((end-onset,audible,measured['exposure_time'],
            measured['clean'],measured['wrong'],measured['missing']),axis=-1)
        sums=np.stack([table[assignment==f].sum(axis=0) for f in range(1,5)])
        for group in ('all','full_safe' if full else 'failed'):
            groups[group]['count']+=1
            groups[group]['sums']+=sums
    require(seen==set(range(1024)),'Exact1024 unique first ledgers required')
    return dict(scope='One read-only ledger pass. Audible exposure is overlap[0,episode_end] with onset..end; approach exposure_time covers press-2..end and is reported separately. Unobserved post-failure time remains in planned denominators. Clean/wrong/missing need not be disjoint during endpoint transitions. Zero-group denominators are None.',
        groups={key:exposure_result(value['count'],value['sums']) for key,value in groups.items()})


def pooled_exposure(summaries):
    groups={}
    for key in ('all','full_safe','failed'):
        count=sum(s['groups'][key]['episodes'] for s in summaries)
        sums=np.asarray([[sum(s['groups'][key]['fingers'][name][field] for s in summaries)
            for field in EXPOSURE_FIELDS] for name in FINGERS])
        groups[key]=exposure_result(count,sums)
    return dict(scope=summaries[0]['scope'],groups=groups)


def compare_exposure(current,baseline):
    groups={}
    for group in ('all','full_safe','failed'):
        rows={}
        for name in FINGERS:
            new,old=(s['groups'][group]['fingers'][name] for s in (current,baseline))
            changes={}
            for kind in ('clean','wrong','missing'):
                key=kind+'_fraction_observed_audible'
                changes[kind+'_observed_fraction_delta']=(new[key]-old[key]
                    if new[key] is not None and old[key] is not None else None)
            required=[changes[key+'_observed_fraction_delta'] for key in ('wrong','missing')]
            changes['status']='unknown' if any(v is None for v in required) else 'pass' if all(v<=.05 for v in required) else 'fail'
            rows[name]=changes
        groups[group]=rows
    # Both all-observed and safe-only guard against reduced post-failure exposure.
    passed=all(row['status']=='pass' for group in ('all','full_safe') for row in groups[group].values())
    return dict(groups=groups,all_and_full_safe_point_comparison_pass=passed,
        failed_scope='Failure-only rows are reported separately; absence of failures is unknown/N/A, not an automatic metric pass.')


def recovery_summary(episodes):
    """Sum scheduled denominators, including windows lost to early failure."""
    if not all('recovery' in e['left_episode_diagnostics'] for e in episodes):
        return dict(known=False, reason='Historical cohort has no fixed-window/initial-decline/run diagnostics; no automatic pass.')
    result = dict(known=True, episodes=len(episodes), fingers={})
    diagnostics = [e['left_episode_diagnostics'] for e in episodes]
    for f, name in enumerate(FINGERS):
        rows = [d['recovery']['by_finger'][f] for d in diagnostics]
        keys = ('planned_windows','planned_s','observed_s','valid_s','in_band_s','complete_windows',
            'incomplete_or_unobserved_windows','started_outside_windows','return_within3s_windows',
            'started_inside_windows','initially_unobserved_or_invalid_windows')
        totals = {k:sum(r[k] for r in rows) for k in keys}
        require(totals['complete_windows']+totals['incomplete_or_unobserved_windows']==totals['planned_windows'] and
            0<=totals['return_within3s_windows']<=totals['started_outside_windows'] and
            -1e-8<=totals['in_band_s']<=totals['valid_s']+1e-6 and
            totals['valid_s']<=totals['observed_s']+1e-6<=totals['planned_s']+2e-6,
            'Recovery coverage/success denominator mismatch')
        require(totals['planned_windows'] == totals['started_outside_windows']+
            totals['started_inside_windows']+totals['initially_unobserved_or_invalid_windows'],
            'Recovery initial-window denominator mismatch')
        totals.update(coverage_fraction=ratio(totals['observed_s'], totals['planned_s']),
            credited_in_band_fraction=ratio(totals['in_band_s'], totals['planned_s']),
            observed_in_band_fraction=ratio(totals['in_band_s'], totals['observed_s']),
            evaluable=totals['planned_windows'] > 0,
            return_fraction_known_outside=ratio(totals['return_within3s_windows'], totals['started_outside_windows']),
            return_fraction_unknown_as_nonreturn=ratio(totals['return_within3s_windows'],
                totals['started_outside_windows']+totals['initially_unobserved_or_invalid_windows']))
        tails = [r['post_last_ge5s'] for r in rows]
        tail = {k:sum(r[k] for r in tails) for k in ('planned_windows','complete_windows',
            'incomplete_or_unobserved_windows','started_outside_windows','started_inside_windows',
            'initially_unobserved_or_invalid_windows','return_within3s_windows')}
        outside, unknown, returned = (tail[k] for k in ('started_outside_windows',
            'initially_unobserved_or_invalid_windows','return_within3s_windows'))
        tail.update(return_fraction_known_outside=ratio(returned, outside),
            return_fraction_unknown_as_nonreturn=ratio(returned, outside+unknown),
            evaluable=tail['planned_windows'] > 0,
            criterion70_status=('unknown' if not outside or unknown else 'pass' if returned/outside >= .7 else 'fail'))
        require(tail['planned_windows'] == outside+unknown+tail['started_inside_windows'],
            'Post-last initial-window denominator mismatch')
        initial = [d['standby']['initial_quality_decline'] for d in diagnostics]
        observed = sum(r['observed_s'][f] for r in initial)
        declined = sum(r['declined_s'][f] for r in initial)
        initial_decline = dict(observed_full_gate_s=observed, declined_s=declined,
            declined_fraction=ratio(declined, observed),
            evaluable_episodes=sum(bool(r['evaluable'][f]) for r in initial),
            unevaluable_episodes=sum(not bool(r['evaluable'][f]) for r in initial),
            valid_reset_reference_episodes=sum(bool(r['reference_valid'][f]) for r in initial),
            reset_reference_quality_mean=(float(np.mean([r['reference_quality'][f] for r in initial
                if r['reference_valid'][f]])) if any(r['reference_valid'][f] for r in initial) else None),
            scope='Actual fullgate==1 valid240Hz samples before own first press-2; invalid/missing samples are excluded and reported.')
        runs = {}
        for kind in ('actual_gate_runs','full_gate_runs'):
            records = [d['standby'][kind] for d in diagnostics]
            total = sum(r['total_s'][f] for r in records)
            band = sum(r['in_band_s'][f] for r in records)
            long_total = np.sum([r['long_total_s'][f] for r in records], axis=0)
            long_band = np.sum([r['long_in_band_s'][f] for r in records], axis=0)
            runs[kind] = dict(count=sum(r['count'][f] for r in records),
                total_s=total, in_band_s=band, in_band_fraction=ratio(band,total),
                mean_max_run_s=float(np.mean([r['max_s'][f] for r in records])),
                max_run_s=max(r['max_s'][f] for r in records),
                thresholds_s=[.5,1.,3.],
                long_count=np.sum([r['long_count'][f] for r in records], axis=0).tolist(),
                long_total_s=long_total.tolist(), long_in_band_s=long_band.tolist(),
                long_in_band_fraction=[ratio(b,t) for b,t in zip(long_band,long_total)])
        angles = {}
        for condition in ('idle','press'):
            seconds = np.asarray([d[condition+'_angles']['valid_weighted_s'][f] for d in diagnostics])
            means = np.asarray([d[condition+'_angles']['mean_rad'][f] for d in diagnostics])
            weight = seconds.sum(axis=0)
            angles[condition] = dict(valid_weighted_s=weight.tolist(),
                mean_degrees=[float(np.degrees((seconds*means).sum(axis=0)[j]/weight[j]))
                    if weight[j] else None for j in range(3)])
        result['fingers'][name] = dict(fixed_score_windows=totals, post_last_ge5s=tail,
            initial_quality_decline=initial_decline, **runs, angles=angles)
    return result


def fixed_windows(targets, duration_s):
    """Independent score-only complement of merged own press-2..end intervals."""
    result = []
    for finger in range(1,5):
        own = [t for t in targets if t['finger'] == finger]
        last = max((t['end_s'] for t in own), default=None)
        cursor = 0.
        for low, high in sorted((max(0., t['press_s']-2.), min(duration_s,t['end_s'])) for t in own):
            if low > cursor:
                result.append(dict(finger=finger,start_s=cursor,end_s=low,post_last_ge5s=False))
            cursor = max(cursor,high)
        if cursor < duration_s:
            result.append(dict(finger=finger,start_s=cursor,end_s=duration_s,
                post_last_ge5s=last is not None and cursor >= last and duration_s-cursor >= 5.))
    return result


def geometric_angles(body_state, metadata):
    """NumPy quaternion reconstruction of the pinned source signed projection."""
    q = body_state[...,3:7].astype(np.float64)
    segments = q[:,metadata['segment_body_indices']]
    palm = np.broadcast_to(q[:,metadata['palm_body_index'],None,None], segments[:,:,:1].shape)
    parent = np.concatenate((palm,segments[:,:,:-1]), axis=2)
    normp,norms = np.linalg.norm(parent,axis=-1),np.linalg.norm(segments,axis=-1)
    validq = np.isfinite(parent).all(-1)&np.isfinite(segments).all(-1)&(normp>1e-12)&(norms>1e-12)
    parent = parent/np.maximum(normp,1e-30)[...,None]
    segments = segments/np.maximum(norms,1e-30)[...,None]
    pvec,pw = -parent[...,:3],parent[...,3:]
    svec,sw = segments[...,:3],segments[...,3:]
    vec = pw*svec+sw*pvec+np.cross(pvec,svec)
    w = pw*sw-(pvec*svec).sum(-1,keepdims=True)
    forward = np.broadcast_to([0.,-1.,0.],vec.shape)
    uv = np.cross(vec,forward)
    direction = forward+2*(w*uv+np.cross(vec,uv))
    projection = np.sqrt(direction[...,1]**2+direction[...,2]**2)
    valid = validq&(projection>=1e-6)&np.isfinite(direction).all(-1)
    angles = np.where(valid,np.arctan2(-direction[...,2],-direction[...,1]),0.)
    return angles,valid


def sampled_posture(evaluation, report, targets, pins):
    """Comparable60Hz posture samples; not full-cohort/actual gate evidence."""
    path = evaluation/'capture_metadata.json'
    metadata = json.loads(path.read_text())
    pins[str(path)] = sha(path)
    require(metadata['capture_envs'] == list(range(8)) and
        [r['env_id'] for r in metadata['captures']] == list(range(8)), 'Predeclared env0..7 required')
    pm = metadata['posture_reconstruction']
    contract = pm['contract']
    require(contract['frame_source']['neutral_segment_direction'] == [0.,-1.,0.] and
        contract['frame_source']['positive_flex_axis'] == [1.,0.,0.], 'Supported pinned source frame required')
    reference = np.radians(contract['reference_geometric_degrees'])
    task_path=Path(report['training_chain']['run'])/'training_contract.json'
    pins[str(task_path)]=sha(task_path)
    duration_s=json.loads(task_path.read_text())['task']['duration_s']
    require(duration_s>0 and all(e['task_time_s']<=duration_s+1e-8 for e in report['episodes']),
        'Pinned whole-song duration required')
    windows = fixed_windows(targets,duration_s)
    totals = {name:dict(press_samples=0, press_pattern_samples=0, press_invalid_samples=0,
        fixed_s=0.,fixed_in_band_s=0.,fixed_observed_s=0.,
        press_angle_hist_counts=[[0]*38 for _ in range(3)]) for name in FINGERS}
    captures = []
    for row in metadata['captures']:
        path = evaluation/row['path']
        require(sha(path) == row['sha256'], 'Captured posture source SHA differs')
        pins[str(path)] = sha(path)
        episode = next(e for e in report['episodes'] if e['env_id'] == row['env_id'])
        with np.load(path,allow_pickle=False) as archive:
            clock, body = archive['clock'],archive['body_state']
            require(len(clock) == episode['steps']+1 and np.array_equal(clock,np.arange(len(clock))*4),
                'Expected first-episode60Hz capture including t0')
            require(abs(clock[-1]/240-episode['task_time_s'])<1e-8,'Capture duration mismatch')
            angles,valid = geometric_angles(body,pm)
        now = clock[1:]/240.
        degrees = np.degrees(angles[1:])
        good = valid[1:].all(-1)
        band = good&(np.abs(angles[1:]-reference)<=np.radians(15.)).all(-1)
        details = dict(env_id=row['env_id'], full_safe=episode['left_curriculum']['full_safe'],fingers={})
        for f,name in enumerate(FINGERS,1):
            own = [t for t in targets if t['finger'] == f]
            pressing = np.any([(now>=t['press_s'])&(now<=t['end_s']) for t in own],axis=0)
            selected = pressing&good[:,f-1]
            pattern = (degrees[:,f-1,1]<=10)&(degrees[:,f-1,2]>=60)
            target = totals[name]
            target['press_samples'] += int(selected.sum())
            target['press_pattern_samples'] += int((pattern&selected).sum())
            target['press_invalid_samples'] += int((pressing&~good[:,f-1]).sum())
            for j in range(3):
                # Include overflow bins; geometric flexion is always in[-180,180].
                hist = np.histogram(degrees[selected,f-1,j],bins=np.r_[-np.inf,np.arange(-180,181,10),np.inf])[0]
                target['press_angle_hist_counts'][j] = (np.asarray(target['press_angle_hist_counts'][j])+hist).tolist()
            planned=observed=inside=0.
            for win in windows:
                if win['finger'] != f or win['end_s']-win['start_s'] < 1.:
                    continue
                dt = np.clip(np.minimum(now,win['end_s'])-np.maximum(now-1/60.,win['start_s']),0.,1/60.)
                planned += win['end_s']-win['start_s']
                observed += float(dt.sum())
                inside += float(np.sum(dt*band[:,f-1]))
            target['fixed_s'] += planned
            target['fixed_observed_s'] += observed
            target['fixed_in_band_s'] += inside
            details['fingers'][name] = dict(press_valid_samples=int(selected.sum()),
                pattern_fraction=ratio((pattern&selected).sum(),selected.sum()),
                press_mean_degrees=degrees[selected,f-1].mean(0).tolist() if selected.any() else None,
                fixed_window_credited_occupancy=ratio(inside,planned),
                initial_degrees=np.degrees(angles[0,f-1]).tolist(), final_degrees=degrees[-1,f-1].tolist())
        captures.append(details)
    for row in totals.values():
        row.update(press_pattern_fraction=ratio(row['press_pattern_samples'],row['press_samples']),
            fixed_window_credited_occupancy=ratio(row['fixed_in_band_s'],row['fixed_s']),
            fixed_window_coverage=ratio(row['fixed_observed_s'],row['fixed_s']))
    return dict(scope='Only8 predeclared env IDs at60Hz completed endpoints, not1024cohort or240Hz extrema. PIP<=10deg/DIP>=60deg is diagnostic, not an anatomical/pressure/sound criterion. Fixed score windows use exact interval overlap with60Hz endpoint geometry; no actualgate inferred.',
        angle_hist_edges_degrees=['-infinity']+list(range(-180,181,10))+['infinity'],
        fingers=totals,captures=captures)


def compare_music(current,baseline):
    result = dict(achieved_delta=current['achieved_mean']-baseline['achieved_mean'],
        safe_fraction_delta=current['safe_complete_fraction']-baseline['safe_complete_fraction'],fingers={})
    result['achieved_status'] = 'pass' if result['achieved_delta']>=-1. else 'fail'
    result['safe_status'] = 'pass' if result['safe_fraction_delta']>=-.02 else 'fail'
    for name in FINGERS:
        new,old = current['fingers'][name],baseline['fingers'][name]
        changes = {key:new[key]-old[key] for key in ('success_fraction','contact_fraction',
            'wrong_audible_fraction','missing_audible_fraction')}
        changes['status'] = 'pass' if all(changes[k]>=-.05 for k in ('success_fraction','contact_fraction')) and all(
            changes[k]<=.05 for k in ('wrong_audible_fraction','missing_audible_fraction')) else 'fail'
        result['fingers'][name]=changes
    result['point_comparison_pass'] = result['achieved_status']==result['safe_status']=='pass' and all(
        r['status']=='pass' for r in result['fingers'].values())
    return result


def pooled_music(summaries):
    """Episode-weighted descriptive pooling, never independent-training inference."""
    n=sum(s['episodes'] for s in summaries)
    require(n>0,'Nonempty music summaries required')
    def mean(key):
        return sum(s[key]*s['episodes'] for s in summaries)/n
    result=dict(episodes=n,achieved_mean=mean('achieved_mean'),
        safe_complete_count=sum(s['safe_complete_count'] for s in summaries),
        safe_complete_fraction=mean('safe_complete_fraction'),fingers={},
        wrong_audible_fraction=mean('wrong_audible_fraction'),missing_audible_fraction=mean('missing_audible_fraction'),
        scope='Episode-weighted descriptive aggregation of3 GPU inference repeats of one learned policy; not3 training seeds.')
    for name in FINGERS:
        rows=[s['fingers'][name] for s in summaries]
        result['fingers'][name]={key:sum(r[key]*s['episodes'] for r,s in zip(rows,summaries))/n
            for key in rows[0]}
    return result


def recovery_comparison(current,baseline):
    result={}
    for name in FINGERS:
        new,old=(r['fingers'][name] for r in (current,baseline))
        new_fraction,old_fraction=(r['fixed_score_windows']['credited_in_band_fraction'] for r in (new,old))
        delta=new_fraction-old_fraction if new_fraction is not None and old_fraction is not None else None
        result[name]=dict(credited_occupancy_delta=delta,
            occupancy_plus20pp_status='unknown' if delta is None else 'pass' if delta>=.2 else 'fail',
            current_return70_status=new['post_last_ge5s']['criterion70_status'],
            current_unknown_initial_windows=new['post_last_ge5s']['initially_unobserved_or_invalid_windows'],
            baseline_unknown_initial_windows=old['post_last_ge5s']['initially_unobserved_or_invalid_windows'])
    return result


def update_summary(rows):
    require(len(rows)==500 and [r['update_index'] for r in rows]==list(range(500)), 'Exactly500 metrics required')
    require(sum(r['transitions'] for r in rows)==16_384_000, 'Committed transition total differs')
    groups = {}
    for name,start,stop in [('first100',0,100),('last100',400,500)]+[
            ('bin100_%03d'%start,start,start+100) for start in range(0,500,100)]:
        chosen=rows[start:stop]
        count=sum(r['episode_summary']['count'] for r in chosen)
        safe=sum(r['episode_summary']['timeline_complete'] for r in chosen)
        total=sum(r['episode_summary']['count']*(r['episode_summary']['mean_left_success_count'] or 0.) for r in chosen)
        groups[name]=dict(start=start,stop_exclusive=stop,ended_episodes=count,
            mean_achieved=ratio(total,count),safe_complete_fraction=ratio(safe,count))
    return dict(scope='Online ended training episodes, including failures; not fixed-policy evaluation.',
        optimizer_updates=500,committed_transitions=16_384_000,groups=groups,
        kl_retries=sum(r['kl_retries'] for r in rows),maximum_accepted_kl=max(r['analytic_kl'] for r in rows),
        final_curriculum=rows[-1]['left_curriculum'])


def markdown(result):
    baseline=result['baseline_pooled']['music']
    anchor=result['historical_anchor']['music']
    lines=['# v20 A 500회 학습·평가 결과','',
        '기본 A(.02/초, shape0)로 large/1024환경/H32/seed7 새500회를 학습했다. 새 정책과 v19의500회 정책을 각각 고정 평가3회 반복했다. 자동복귀 제어 C는 적용하지 않았다.','',
        '학습은16,384,000전이를 PPO에 반영했다. 학습 중 종료곡 집계와 아래 고정 정책 평가는 구분한다.','',
        '| 평가 | 평균 달성음 /67 | 안전 완주 | v19 대비 달성음 | 음악·안전 점검 |','|---|---:|---:|---:|---|',
        '| v19 과거 원본 | %.4f | %d/1024 | — | 보존한 기준점 |'%(anchor['achieved_mean'],anchor['safe_complete_count'])]
    for repeat in result['baselines']:
        music=repeat['music']
        lines.append('| v19 재평가%d | %.4f | %d/1024 | — | 비교 정책 |'%(
            repeat['repeat'],music['achieved_mean'],music['safe_complete_count']))
    for repeat in result['repeats']:
        music=repeat['music']; comparison=repeat['comparison_to_v19']
        passed=comparison['point_comparison_pass'] and repeat['exposure_comparison_to_v19']['all_and_full_safe_point_comparison_pass']
        lines.append('| v20 A 반복%d | %.4f | %d/1024 | %+.4f | %s |'%(
            repeat['repeat'],music['achieved_mean'],music['safe_complete_count'],comparison['achieved_delta'],
            '기준 내' if passed else '악화 기준 초과·판정 불가'))
    lines+=['','v20 각 행의 변화는 v19 재평가3회 전체 평균에 대한 값이다. 최종 판정 자료에는 각 버전3회 전체 분모와 반복 범위를 함께 기록했다. 달성음은 현 모델의 연속 clean 기하 후보 판정이며 실제 압력·음향 성공을 뜻하지 않는다.','',
        '## 손가락별 음악성과','',
        '| 평가 | 손가락 | 달성 | 접촉 | 오압현 시간/음 길이 | 누락 시간/음 길이 |',
        '|---|---|---:|---:|---:|---:|']
    for label,music in [('v19 3회 집계',baseline),('A 3회 집계',result['current_pooled']['music'])]:
        for name,row in music['fingers'].items():
            lines.append('| %s | %s | %.1f%% | %.1f%% | %.1f%% | %.1f%% |'%(
                label,name,100*row['success_fraction'],100*row['contact_fraction'],
                100*row['wrong_audible_fraction'],100*row['missing_audible_fraction']))
    def pct(value):
        return '판정 불가' if value is None else '%.1f%%'%(value*100)
    lines+=['','중도 실패하면 뒤 음의 오압현·누락을 관측하지 못하므로 위 계획 음 길이 분모만으로 좋아졌다고 판단하지 않는다. 아래는 전체·안전 완주·물리 실패를 나누고 **실제로 관측한 onset~end 시간**으로 다시 정규화한 값이다. 전체와 안전 완주 양쪽에서 손가락별 오압현·누락 악화5%p 이내를 확인한다. 실패 표본이 없으면 판정 불가로 표시한다.','',
        '| 평가 | 종료 구분 | 손가락 | 관측/계획 음 길이(초) | clean/관측 | 오압현/관측 | 누락/관측 |',
        '|---|---|---|---:|---:|---:|---:|']
    for label,pooled in [('v19',result['baseline_pooled']),('A',result['current_pooled'])]:
        for key,title in [('all','전체'),('full_safe','안전 완주'),('failed','물리 실패')]:
            group=pooled['audible_exposure']['groups'][key]
            for name,row in group['fingers'].items():
                lines.append('| %s | %s %d곡 | %s | %.1f/%.1f | %s | %s | %s |'%(
                    label,title,group['episodes'],name,row['observed_audible_s'],row['planned_audible_s'],
                    pct(row['clean_fraction_observed_audible']),pct(row['wrong_fraction_observed_audible']),
                    pct(row['missing_fraction_observed_audible'])))
    lines+=['','원장 `exposure_time`은 press−2초부터 end까지의 접근 노출이며 음 길이 분모가 아니다. 접근 노출과 음이 울리는 onset~end 노출을 분리했다. 계획 음 길이와 실패 후 미관측 시간도 분석 JSON에 보존했다.','']
    lines+=['','## 대기 복귀와 끝관절 편중','',
        '악보로 고정한1초 이상 대기창은 정책 행동에 따라 분모가 바뀌지 않는다. 중도 실패 후 관측하지 못한 시간도 예정 분모에 남겨 점유율을 과대평가하지 않는다. 초기 자세가 유효하지 않거나 창에 도달하지 못한 경우는 unknown으로 별도 기록했다.','',
        '| 반복 | 손가락 | 고정창 B점유 | 관측 범위 | 마지막 음 후 복귀 성공/대역밖 시작 | 시작 미관측·무효 | 초기 품질 저하 시간비 |',
        '|---|---|---:|---:|---:|---:|---:|']
    for repeat in [dict(repeat='v19 집계',recovery=result['baseline_pooled']['recovery']),
            dict(repeat='A 집계',recovery=result['current_pooled']['recovery'])]:
        for name,row in repeat['recovery']['fingers'].items():
            fixed,tail,initial=(row[k] for k in ('fixed_score_windows','post_last_ge5s','initial_quality_decline'))
            lines.append('| %s | %s | %s | %s | %d/%d | %d | %s |'%(
                repeat['repeat'],name,pct(fixed['credited_in_band_fraction']),pct(fixed['coverage_fraction']),
                tail['return_within3s_windows'],tail['started_outside_windows'],
                tail['initially_unobserved_or_invalid_windows'],pct(initial['declined_fraction'])))
    lines+=['','복귀 성공은 대역 밖에서 시작해3초 안에 B대역으로 돌아와0.2초 유지하고 해당 창이 끝까지 관측된 경우다. 시작 미관측·무효가 있으면70% 목표를 자동 통과시키지 않는다.','',
        '과거 v19 원본에는 새 복귀 진단이 없으므로 기존 체크포인트를 별도 어댑터에서 재평가했다. 당시 정책·idle 입력·곡 시계를 보존하고 현재와 같은 물리·음악 판정·관찰용 진단을 사용했다. 여기서 재계산한 보상은 과거 학습 보상으로 비교하지 않는다. 각 버전3×1024환경의 고정창 점유율·복귀는 비교할 수 있지만 과거 학습의 인과 효과로 단정하지 않는다.','',
        '| 손가락 | 고정창 점유율 변화 | +20%p 목표 | A 마지막 음 후70% 복귀 목표 |','|---|---:|---|---|']
    for name,row in result['pooled_recovery_comparison'].items():
        delta=row['credited_occupancy_delta']
        lines.append('| %s | %s | %s | %s |'%(name,'판정 불가' if delta is None else '%+.1f%%p'%(delta*100),
            row['occupancy_plus20pp_status'],row['current_return70_status']))
    lines+=['','각도 편중 표는 사전지정0..7환경의60Hz 표본이다. 이8개 표본을 전체1024환경이나240Hz 극값으로 확대하지 않는다.','',
        '| 평가 | 손가락 | 압현 표본 중 PIP≤10°·DIP≥60° | 8환경 고정창 B점유 |','|---|---|---:|---:|']
    for label,sample in [('v19 과거',result['historical_anchor']['sampled_posture'])]+[
            ('v19 재평가%d'%r['repeat'],r['sampled_posture']) for r in result['baselines']]+[
            ('A 반복%d'%r['repeat'],r['sampled_posture']) for r in result['repeats']]:
        for name,row in sample['fingers'].items():
            lines.append('| %s | %s | %s | %s |'%(
                label,name,pct(row['press_pattern_fraction']),pct(row['fixed_window_credited_occupancy'])))
    lines+=['','## 해석과 다음 단계','',result['recommendation']['text'],'',
        '과거 원본 기준점은1회이며 새 비교 평가는 각3회다. 각 버전의 학습 seed는1개이므로 반복 평가는 같은 모델의 GPU 실행 변동만 보여주고 독립 학습3회의 통계적 신뢰도를 제공하지 않는다. 관절 편중은 사전지정8환경의60Hz 표본이며240Hz 극값·해부학 인증·오압현 원인의 증명이 아니다.','',
        '개별 고정창 분모·미관측 수·actual/full gate 연속구간·초기 품질·각도 히스토그램·입력 SHA는 [분석 JSON](analysis.json)에 기록했다. 자동으로3,000회 학습을 채택하거나 보상 설정을 변경하지 않는다.','']
    return '\n'.join(lines)


def analyze(phase):
    pins={str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
    def read(path):
        pins[str(path)]=sha(path)
        return json.loads(path.read_text())
    def exposure(evaluation,targets,music):
        path=evaluation/'first_episodes.jsonl'
        pins[str(path)]=sha(path)
        with path.open() as stream:
            summary=audible_summary((json.loads(line) for line in stream),targets)
        require(summary['groups']['full_safe']['episodes']==music['safe_complete_count'],
            'Report/stream safe denominator differs')
        return summary
    train=read(phase/'train500/report.json')
    audit=read(phase/'log_inspection.json')
    require(train['completed'] and train['optimizer_updates']==500 and train['failure'] is None and
        not train['changed_inputs'] and train['lifecycle_verified'] and not train['cleanup_errors'],
        'Completed audited500 training required')
    require(audit['verified'] and audit['transitions']==16_384_000 and
        audit['raw_crc']['complete'] and audit['raw_crc']['completed_members']==500 and
        audit['raw_crc']['valid_prefix_rows']==16000 and not audit['raw_crc']['error'] and
        audit['raw_crc']['discarded_unverified_bytes']==0,'Whole training audit required')
    metrics_path=phase/'train500/learning_metrics.jsonl'
    pins[str(metrics_path)]=sha(metrics_path)
    metrics=[json.loads(line) for line in metrics_path.open()]
    baseline_report=read(BASELINE/'report.json')
    baseline_targets=read(BASELINE/'targets.json')
    baseline_music=music_summary(baseline_report,baseline_targets)
    require(abs(baseline_music['achieved_mean']-6.9375)<1e-12 and baseline_music['safe_complete_count']==1018,
        'Predeclared v19 500 baseline differs')
    anchor=dict(directory=str(BASELINE),music=baseline_music,
        audible_exposure=exposure(BASELINE,baseline_targets,baseline_music),
        recovery=recovery_summary(baseline_report['episodes']),
        sampled_posture=sampled_posture(BASELINE,baseline_report,baseline_targets,pins))
    collections={}
    episode_groups={}
    schedule=None
    for kind in ('baseline','evaluation'):
        repeats=[]
        episodes=[]
        checkpoint=None
        for index in range(1,4):
            evaluation=phase/('%s_repeat%d'%(kind,index))
            report=read(evaluation/'report.json')
            targets=read(evaluation/'targets.json')
            require(report['completed'] and report['source_optimizer_updates']==500 and report['repeat']==index and
                report['num_envs']==1024 and report['deterministic'] and report['gpu_scene']['closed'] and
                report['gpu_scene']['physx_use_gpu'] and report['gpu_scene']['use_gpu_pipeline'] and
                report['gpu_scene']['environment_count']==1024 and
                report['gpu_scene']['physics_steps']==report['ticks']*4, 'Completed GPU repeat required')
            required_restoration={'model','actor_optimizer','value_optimizer','torch_rng','cuda_rng','numpy_rng','python_rng','3331_curriculum'}
            require(required_restoration.issubset(report['restoration_verified']),'Checkpoint restoration audit required')
            if kind=='baseline':
                require(report['training_chain']['schema']=='guitar_learning.v19_checkpoint500_current_physics_adapter.v1' and
                    report['training_chain']['source_optimizer_updates']==500,
                    'Explicit old-policy/current-physics adapter required')
            else:
                require(report['training_chain']['schema']=='guitar_learning.fresh_v20_A500.v1' and
                    report['training_chain']['fresh_policy'] and report['training_chain']['run_completed'],
                    'Fresh completed v20 training chain required')
            schedule=schedule or targets
            require(targets==schedule,'Six-repeat target schedule differs')
            checkpoint=checkpoint or report['checkpoint']
            require(report['checkpoint']==checkpoint,'Repeat checkpoint differs')
            recovery=recovery_summary(report['episodes'])
            require(recovery['known'],'Current bounded recovery diagnostics missing')
            music=music_summary(report,targets)
            repeats.append(dict(repeat=index,directory=str(evaluation),music=music,
                audible_exposure=exposure(evaluation,targets,music),
                recovery=recovery,sampled_posture=sampled_posture(evaluation,report,targets,pins)))
            episodes.extend(report['episodes'])
        collections[kind]=repeats
        episode_groups[kind]=episodes
    baselines,repeats=(collections[k] for k in ('baseline','evaluation'))
    baseline_pooled=dict(music=pooled_music([r['music'] for r in baselines]),
        audible_exposure=pooled_exposure([r['audible_exposure'] for r in baselines]),
        recovery=recovery_summary(episode_groups['baseline']))
    current_pooled=dict(music=pooled_music([r['music'] for r in repeats]),
        audible_exposure=pooled_exposure([r['audible_exposure'] for r in repeats]),
        recovery=recovery_summary(episode_groups['evaluation']))
    for row in repeats:
        row['comparison_to_v19']=compare_music(row['music'],baseline_pooled['music'])
        row['exposure_comparison_to_v19']=compare_exposure(row['audible_exposure'],baseline_pooled['audible_exposure'])
    for row in baselines:
        row['comparison_to_historical_anchor']=compare_music(row['music'],baseline_music)
    pooled_comparison=compare_music(current_pooled['music'],baseline_pooled['music'])
    exposure_comparison=compare_exposure(current_pooled['audible_exposure'],baseline_pooled['audible_exposure'])
    posture_comparison=recovery_comparison(current_pooled['recovery'],baseline_pooled['recovery'])
    music_pass=sum(r['comparison_to_v19']['point_comparison_pass'] and
        r['exposure_comparison_to_v19']['all_and_full_safe_point_comparison_pass'] for r in repeats)
    posture_pass=all(r['occupancy_plus20pp_status']==r['current_return70_status']=='pass'
        for r in posture_comparison.values())
    if not pooled_comparison['point_comparison_pass'] or not exposure_comparison['all_and_full_safe_point_comparison_pass'] or music_pass<3:
        recommendation='음악·안전 또는 손가락별 품질이 악화 기준을 넘은 평가가 있다. 3,000회 연장 전 해당 손가락과 대기 보상의 영향을 확인하는 것을 권한다.'
    elif posture_pass:
        recommendation='음악·안전의 점 비교와 복귀 목표가 기준 안이다. 반복 변동·표본 영상·미관측 범위를 검토한 뒤 같은 A 설정의3,000회 연장을 검토할 수 있다. 독립 학습 seed 비교는 아직 없다.'
    else:
        recommendation='음악·안전의 점 비교는 기준 안이지만 자세 점유율 또는 복귀 목표가 실패하거나 판정 불가인 손가락이 남아 있다. 학습 추세와 손가락별 영상을 보고 A 연장, .04 비교 또는 선택 분담 B 비교를 구분하는 것을 권한다. 보상만으로 복귀가 가능한지 아직 결론 내리지 않는다.'
    ranges={}
    for kind,rows in collections.items():
        ranges[kind]=dict(achieved_mean=[min(r['music']['achieved_mean'] for r in rows),
            max(r['music']['achieved_mean'] for r in rows)],
            safe_complete_count=[min(r['music']['safe_complete_count'] for r in rows),
                max(r['music']['safe_complete_count'] for r in rows)])
    result=dict(schema='guitar_learning.v20_A500_analysis.v1',training=update_summary(metrics),
        historical_anchor=anchor,baselines=baselines,repeats=repeats,
        baseline_pooled=baseline_pooled,current_pooled=current_pooled,
        pooled_music_comparison=pooled_comparison,pooled_recovery_comparison=posture_comparison,
        pooled_exposure_comparison=exposure_comparison,
        evaluation_repeat_range=ranges,
        recommendation=dict(automatic_3000_adoption=False,music_point_comparisons_pass=music_pass,
            pooled_music_point_comparison_pass=pooled_comparison['point_comparison_pass'],
            pooled_exposure_point_comparison_pass=exposure_comparison['all_and_full_safe_point_comparison_pass'],
            pooled_posture_point_comparison_pass=posture_pass,text=recommendation),
        limitations=['One training seed per version;3 inference repeats per version are not independent training seeds.',
            'Old v19 checkpoint runs through an explicit current-physics observation adapter; recalculated v20 rewards are not v19 training rewards or used for reward comparisons.',
            'Historical v19 original6.9375/safe1018 is a one-repeat anchor, distinct from the3 repeated adapter evaluations.',
            'PIP/DIP pattern occupancy sampled only for8predeclared IDs per repeat at60Hz, not full1024cohort or240Hz extrema.',
            'Wrong/missing and clean are loaded geometric candidate diagnostics, not calibrated pressure or sound.'],
        inputs_sha256=pins)
    require(all(sha(path)==expected for path,expected in pins.items()),'Analysis inputs changed during reading')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',type=Path,default=PHASE)
    args=parser.parse_args()
    phase=args.phase.resolve()
    require(not (phase/'analysis.json').exists() and not (phase/'RESULTS.md').exists(), 'Preserve previous derived reports')
    result=analyze(phase)
    with (phase/'analysis.json').open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
        stream.write('\n')
    with (phase/'RESULTS.md').open('x') as stream:
        stream.write(markdown(result))
    print(json.dumps(dict(completed=True,output=str(phase/'analysis.json'),
        repeat_range=result['evaluation_repeat_range'],recommendation=result['recommendation']),ensure_ascii=False))


if __name__=='__main__':
    main()
