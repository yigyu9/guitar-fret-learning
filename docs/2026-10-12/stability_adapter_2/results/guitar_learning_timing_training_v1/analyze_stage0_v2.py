"""Snapshot local PPO logs and compare final native evaluation to fixed BC baseline.

Writes new artifacts only in this script's phase. Never runs native physics or
imports the training package. An open gzip snapshot is explicitly provisional.
"""
import argparse
import codecs
import gc
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
from datetime import datetime, timezone
import zlib

PHASE = Path(__file__).resolve().parent
BASELINE = PHASE.parent/'guitar_learning_timing_curriculum_v1/runtime_analysis_v1.json'
INPUTS = {}


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def read_bytes(path):
    path = Path(path).resolve()
    value = path.read_bytes()
    INPUTS[str(path)] = dict(sha256=digest_bytes(value), bytes=len(value))
    return value


def read_json(path):
    return json.loads(read_bytes(path))


def write_new(path, value):
    with path.open('x') as stream:
        if isinstance(value, str): stream.write(value)
        else: json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')


def mean(values):
    values = [v for v in values if v is not None]
    return sum(values)/len(values) if values else None


def bounds(values):
    values = [v for v in values if v is not None]
    return dict(count=len(values), mean=mean(values), minimum=min(values) if values else None,
                maximum=max(values) if values else None)


def norm(values):
    return math.sqrt(sum(value*value for value in values))


def jsonl_snapshot(path, metadata):
    raw = read_bytes(path)
    decoder = zlib.decompressobj(31)
    utf8 = codecs.getincrementaldecoder('utf8')()
    pending = ''
    lines = 0
    for offset in range(0, len(raw), 65536):
        pending += utf8.decode(decoder.decompress(raw[offset:offset+65536]))
        pieces = pending.split('\n'); pending = pieces.pop()
        for piece in pieces:
            if not piece: continue
            lines += 1
            yield json.loads(piece)
    metadata.update(gzip_complete=decoder.eof, complete_json_lines=lines,
                    trailing_partial_text_bytes=len(pending.encode('utf8')),
                    compressed_snapshot_bytes=len(raw),
                    scope='closed or open compressed byte snapshot; only complete JSON lines included')


def new_episode():
    return dict(ticks=0, cost_sum=0., reward_sum=0., reward_terms={},
                guitar_endpoint_max_m=0., rotation_endpoint_max_rad=0., feet_endpoint_max_m=0.,
                support_count=0, triple_count=0, both_feet_count=0,
                hold_before_onset_full_ticks=0., hold_after_end_full_ticks=0.,
                hold_boundary_ticks=0., failure_reasons=set())


def append_tick(acc, info, reward, target):
    acc['ticks'] += 1; acc['cost_sum'] += info['cost']; acc['reward_sum'] += reward
    for key, value in info['reward_terms'].items():
        acc['reward_terms'][key] = acc['reward_terms'].get(key, 0.)+value
    safety = info['stability']; flags = safety['flags']
    acc['guitar_endpoint_max_m'] = max(acc['guitar_endpoint_max_m'], norm(safety['guitar_delta_m']))
    acc['rotation_endpoint_max_rad'] = max(acc['rotation_endpoint_max_rad'], norm(safety['guitar_rotation_vector_rad']))
    acc['feet_endpoint_max_m'] = max(acc['feet_endpoint_max_m'], *(norm(p) for p in safety['foot_delta_m']))
    acc['support_count'] += int(any(flags[:3])); acc['triple_count'] += int(all(flags[:3]))
    acc['both_feet_count'] += int(all(flags[8:])); acc['failure_reasons'].update(info['failure_reasons'])
    hold = info['reward_terms'].get('timing_hold', 0.); now = info['task_time_s']
    if now <= target['onset_s']: acc['hold_before_onset_full_ticks'] += hold
    elif now-1/60. >= target['end_s']: acc['hold_after_end_full_ticks'] += hold
    elif not target['onset_s'] <= now-1/60. <= now <= target['end_s']:
        acc['hold_boundary_ticks'] += hold


def timing_metrics(timing, target):
    crosses = timing['crossings']
    targets = [c for c in crosses if (c['string_number'], c['direction']) ==
               (target['string']+1, target['direction'])]
    first = targets[0] if targets else None
    matched = next((c for c in crosses if c['crossing_id'] == timing['first_matched_crossing']), None)
    return dict(first_target_down_error_s=first['error_s'] if first else None,
        first_target_down_abs_error_s=abs(first['error_s']) if first else None,
        first_window_match_error_s=matched['error_s'] if matched else None,
        best_target_abs_error_s=timing['best_abs_error_s'] if timing['role']=='right' else None,
        best_left_press_abs_error_s=timing['best_abs_error_s'] if timing['role']=='left' else None,
        target_direction_crossings=len(targets), up_crossings=sum(c['direction']==-1 for c in crosses),
        down_crossings=sum(c['direction']==1 for c in crosses),
        wrong_crossings=timing['wrong_crossings'], unnecessary_crossings=timing['unnecessary_crossings'],
        duplicate_crossings=timing['duplicate_crossings'], crossings=crosses,
        audible_hold_fraction=timing['audible_hold_fraction'], audible_valid_s=timing['audible_valid_s'],
        audible_longest_dwell_s=timing['audible_longest_dwell_s'],
        window_longest_dwell_s=timing['window_longest_dwell_s'],
        first_success_policy_s=timing['first_success_s'], stage_success=timing['stage_success'])


def training(folder, role):
    settings = read_json(folder/'settings.json'); contract = read_json(folder/'training_contract.json')
    target = contract['task']['targets'][0]; updates=[]; incomplete_updates=[]
    for path in sorted(folder.glob('update_*.json')):
        try: updates.append(read_json(path))
        except json.JSONDecodeError: incomplete_updates.append(path.name)
    updates.sort(key=lambda row:row['update_index'])
    committed_indices = {u['update_index'] for u in updates}
    accumulators = [new_episode() for _ in range(settings['num_envs'])]
    counters = [0]*settings['num_envs']; episodes=[]; stream={}; logged=0
    for tick, row in enumerate(jsonl_snapshot(folder/'transitions.jsonl.gz', stream)):
        update_index = tick//settings['horizon']
        for worker, info in enumerate(row['infos']):
            logged += 1
            append_tick(accumulators[worker], info, row['reward'][worker], target)
            if 'episode' not in info: continue
            acc = accumulators[worker]; episode = info['episode']; timing = episode['timing']
            terms = acc['reward_terms']; hold = terms.get('timing_hold', 0.)
            audible_reward = settings['timing']['held_second']*timing['audible_valid_s']
            evidence = dict(worker=worker, episode_index=counters[worker], update_index=update_index,
                committed=update_index in committed_indices, reason=episode['reason'],
                reward=episode['reward'], cost=episode['cost'], control_ticks=acc['ticks'],
                **timing_metrics(timing,target), reward_terms=terms,
                hold_reward_total=hold, hold_reward_audible_component=audible_reward,
                hold_reward_outside_audible=hold-audible_reward,
                hold_reward_outside_audible_fraction=(hold-audible_reward)/hold if hold else None,
                hold_before_onset_full_tick_reward=acc['hold_before_onset_full_ticks'],
                hold_after_end_full_tick_reward=acc['hold_after_end_full_ticks'],
                hold_boundary_tick_reward=acc['hold_boundary_ticks'],
                safety_endpoint60=dict(guitar_displacement_max_m=acc['guitar_endpoint_max_m'],
                    guitar_rotation_max_rad=acc['rotation_endpoint_max_rad'], feet_displacement_max_m=acc['feet_endpoint_max_m'],
                    any_support_fraction=acc['support_count']/acc['ticks'], triple_fraction=acc['triple_count']/acc['ticks'],
                    both_feet_fraction=acc['both_feet_count']/acc['ticks'], failure_reasons=sorted(acc['failure_reasons']),
                    scope='60Hz returned endpoints; may underestimate within-tick240Hz maxima'),
                joint_music=episode['music'],
                checks=dict(cost_integral_matches=abs(acc['cost_sum']-episode['cost'])<1e-8,
                    reward_sum_matches=abs(acc['reward_sum']-episode['reward'])<1e-8))
            episodes.append(evidence); counters[worker]+=1; accumulators[worker]=new_episode()
    by_update=[]
    for update in updates:
        es=[e for e in episodes if e['update_index']==update['update_index'] and e['committed']]
        row=dict(update)
        row['episode_metrics']={key:bounds([e[key] for e in es]) for key in (
            'reward','cost','audible_hold_fraction','first_target_down_abs_error_s',
            'best_target_abs_error_s','unnecessary_crossings','up_crossings',
            'down_crossings','hold_reward_total','hold_reward_outside_audible')}
        row['episode_successes']=sum(e['stage_success'] for e in es)
        row['episode_count']=len(es); by_update.append(row)
    complete = (folder/'report.json').is_file()
    report = read_json(folder/'report.json') if complete else None
    status = None
    if (folder/'status.json').is_file():
        try:status=read_json(folder/'status.json')
        except json.JSONDecodeError:pass
    committed=[e for e in episodes if e['committed']]
    resources=[]
    if (folder/'resources.jsonl').is_file():
        for line in read_bytes(folder/'resources.jsonl').decode().splitlines():
            try:resources.append(json.loads(line))
            except json.JSONDecodeError:continue
    result=dict(role=role,settings=settings,target=target,completed_report_available=complete,
        report_completed=report['completed'] if report else False,status=status,
        committed_updates=len(updates),committed_transitions=sum(u['transitions'] for u in updates),
        logged_transitions=logged,transition_stream=stream,incomplete_update_files=incomplete_updates,
        updates=by_update,episodes=episodes,
        training_summary=dict(committed_episodes=len(committed),successes=sum(e['stage_success'] for e in committed),
            physical_failures=sum(e['reason']=='terminal_failure' for e in committed),
            accepted_KL=bounds([u['analytic_kl'] for u in updates]),attempted_KL=bounds([u['max_attempted_kl'] for u in updates]),
            retries_total=sum(u['kl_retries'] for u in updates),retry_updates=sum(u['kl_retries']>0 for u in updates),
            actual_actor_lr=bounds([u['actor_lr'] for u in updates]),configured_actor_lr=settings['ppo']['actor_lr'],
            reward_critic_loss=bounds([u['reward_value_loss'] for u in updates]),cost_critic_loss=bounds([u['cost_value_loss'] for u in updates]),
            actor_grad_norm=bounds([u['actor_grad_norm'] for u in updates])),
        checks=dict(update_indices_contiguous=[u['update_index'] for u in updates]==list(range(len(updates))),
            accepted_KL_within_budget=all(u['analytic_kl']<=settings['ppo']['target_kl']+1e-9 for u in updates),
            episode_integrals_match=all(all(e['checks'].values()) for e in episodes)),
        resources_tail=resources[-1] if resources else None,
        report=dict(completed=report['completed'],failure=report['failure'],changed_inputs=report['changed_inputs'],
            persistent_audit=report.get('persistent_audit'),partial_collection=report['partial_collection']) if report else None)
    return result


def native_evaluation(folder, baseline, role):
    if not (folder/'result.json').is_file():return None
    result=read_json(folder/'result.json')
    if not result['completed']:return dict(completed=False,result=result)
    with gzip.open(folder/'transitions.json.gz','rt') as stream:rows=json.load(stream)
    read_bytes(folder/'transitions.json.gz')
    episodes=[]
    for index,episode in enumerate(result['episodes']):
        reset=read_json(folder/('reset_%02d.json'%index));target=reset['training_contract']['task']['targets'][0]
        group=[r for r in rows if r['episode']==index]
        physics=[p for r in group for p in r['physics_measurements']]
        flags=[p['stability']['flags'] for p in physics]
        identity=target['target_id']; previous=reset['specialist']['left']['targets'][identity]['candidate']
        previous_time=0.; audible_valid=0.; audible_current=0.; audible_longest=0.; current=0.; longest=0.
        inactive_zero=True; actions_bounded=True
        for row in group:
            action=row['action']; inactive=action[33:] if role=='left' else action[:33]
            inactive_zero &= all(value==0 for value in inactive)
            actions_bounded &= all(math.isfinite(value) and abs(value)<=1 for value in action)
        for point in physics:
            measured=point['music']; now=measured['task_time_s']; candidate=measured['targets'][identity]['candidate']
            amount=max(0.,min(now,target['end_s'])-max(previous_time,target['onset_s'])) if previous and candidate else 0.
            audible_valid+=amount; audible_current=audible_current+amount if amount>0 else 0.
            audible_longest=max(audible_longest,audible_current)
            current=current+now-previous_time if candidate and previous else 0.
            longest=max(longest,current); previous,previous_time=candidate,now
        metrics=timing_metrics(episode['timing'],target)
        crossings=[]
        for p in physics:
            for c in p['music']['crossings']:
                crossings.append({k:c[k] for k in ('crossing_id','string_number','direction','task_time_s','depth_m','across_speed_m_s')})
        safety=dict(guitar_displacement_max_m=max(norm(p['stability']['guitar_delta_m']) for p in physics),
            guitar_rotation_max_rad=max(norm(p['stability']['guitar_rotation_vector_rad']) for p in physics),
            foot_displacement_max_m=max(norm(v) for p in physics for v in p['stability']['foot_delta_m']),
            any_support_fraction=sum(any(f[:3]) for f in flags)/len(flags),
            triple_support_fraction=sum(all(f[:3]) for f in flags)/len(flags),
            both_feet_fraction=sum(all(f[8:]) for f in flags)/len(flags),
            failure_reasons=sorted({x for p in physics for x in p['stability']['failure_reasons']}),
            cost_integral=sum(p['stability']['cost'] for p in physics),scope='all stored240Hz samples')
        for c in crossings:
            c['error_s']=c['task_time_s']-target['onset_s']
        hold_total=episode['timing']['config']['held_second']*episode['timing']['window_valid_s']
        audible_hold_reward=episode['timing']['config']['held_second']*audible_valid
        base=baseline['episodes'][index]
        episodes.append(dict(episode=index,reason=episode['reason'],cost=episode['cost'],reward=episode['reward'],
            **metrics,safety240=safety,raw_crossings=crossings,joint_music=episode['music'],
            candidate_longest_dwell_s=longest,
            audible_valid_s_recomputed=audible_valid,audible_longest_s_recomputed=audible_longest,
            hold_reward_total_recomputed=hold_total,hold_reward_audible_component=audible_hold_reward,
            hold_reward_outside_audible=hold_total-audible_hold_reward,
            descriptive_change_vs_same_index_BC=dict(first_target_error_abs_s=None if metrics['first_target_down_abs_error_s'] is None else
                metrics['first_target_down_abs_error_s']-abs(base['first_matched_target_crossing']['error_s']),
                audible_hold_fraction=metrics['audible_hold_fraction']-base['audible_hold_fraction'],
                guitar_displacement_max_m=safety['guitar_displacement_max_m']-base['safety']['guitar_displacement_max_m'],
                cost=episode['cost']-base['safety']['cost_integral']),
            checks=dict(ticks300=len(group)==300,physics1200=len(physics)==1200,
                consecutive_physics=all(p['physics_step']==physics[0]['physics_step']+j for j,p in enumerate(physics)),
                clock_240Hz=all(abs(p['music']['task_time_s']-(j+1)/240.)<1e-9 for j,p in enumerate(physics)),
                cost_integral=abs(safety['cost_integral']-episode['cost'])<1e-8,
                action_bounds=actions_bounded,inactive_action_zero=inactive_zero,
                each_tick_four_physics=all(len(row['physics_measurements'])==4 for row in group),
                audible_valid_matches=abs(audible_valid-episode['timing']['audible_valid_s'])<1e-9,
                audible_longest_matches=abs(audible_longest-episode['timing']['audible_longest_dwell_s'])<1e-9,
                candidate_longest_matches=abs(longest-episode['specialist']['skill']['longest_dwell_s'][identity])<1e-9,
                original_joint_music_separate=episode['music']==group[-1]['info']['music'],
                crossing_depth_speed=all(.001<=c['depth_m']<=.015 and abs(c['across_speed_m_s'])>=.05 for c in crossings))))
    del rows;gc.collect()
    return dict(completed=True,source_unchanged=result['source_unchanged'],checkpoint=result['checkpoint'],
        episodes=episodes,scope='two repeated same-start deterministic evaluations; changes are descriptive, not statistical generalization')


def plots(path, roles):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,2,figsize=(12,10),constrained_layout=True)
    for col,(role,run) in enumerate(roles.items()):
        rows=run['training']['updates'];x=[u['update_index']+1 for u in rows]
        axes[0,col].plot(x,[u['analytic_kl'] for u in rows],label='Accepted KL')
        axes[0,col].plot(x,[u['max_attempted_kl'] for u in rows],label='Max attempted KL',alpha=.7)
        axes[0,col].axhline(.02,color='red',linestyle=':',label='KL budget')
        axes[0,col].set_yscale('log');axes[0,col].set_title(role);axes[0,col].legend()
        axes[1,col].plot(x,[u['actor_lr'] for u in rows],label='Actual actor LR')
        axes[1,col].axhline(run['training']['settings']['ppo']['actor_lr'],color='gray',linestyle=':',label='Configured LR')
        axes[1,col].set_yscale('log');axes[1,col].legend()
        axes[2,col].plot(x,[u['reward_value_loss'] for u in rows],label='Reward critic loss')
        axes[2,col].plot(x,[u['cost_value_loss'] for u in rows],label='Cost critic loss')
        axes[2,col].set_yscale('log');axes[2,col].legend()
        for ax in axes[:,col]:ax.grid(alpha=.2);ax.set_xlabel('Completed PPO update')
    fig.savefig(path,dpi=160);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',required=True)
    parser.add_argument('--final',action='store_true')
    parser.add_argument('--eval-left',type=Path)
    parser.add_argument('--eval-right',type=Path)
    args=parser.parse_args()
    if not re.fullmatch(r'[a-z0-9_]+',args.name):raise ValueError('simple new artifact basename required')
    output=PHASE/(args.name+'.json');markdown=PHASE/(args.name+'.md');png=PHASE/(args.name+'.png')
    if any(p.exists() for p in (output,markdown,png)):raise FileExistsError('preserve existing analysis; choose a new name')
    baseline=read_json(BASELINE);roles={}
    for role in ('left','right'):
        train=training(PHASE/(role+'_stage0_v1'),role)
        evaluation=getattr(args,'eval_'+role) or PHASE/(role+'_stage0_eval_v1')
        ev=native_evaluation(evaluation,baseline['roles'][role]['bc_eval_v1'],role)
        roles[role]=dict(training=train,native_evaluation=ev,
            baseline_BC=baseline['roles'][role]['bc_eval_v1'],baseline_one_update=baseline['roles'][role]['ppo_eval_v1'])
    final_ready=all(r['training']['report_completed'] and r['native_evaluation'] and
                    r['native_evaluation']['completed'] for r in roles.values())
    if args.final and not final_ready:raise RuntimeError('final analysis requires closed training reports and both native evaluations')
    read_bytes(Path(__file__))
    analysis=dict(schema='guitar_learning.stage0_training_analysis.v2',created_utc=datetime.now(timezone.utc).isoformat(),
        final_requested=args.final,final_ready=final_ready,roles=roles,input_snapshots=INPUTS,
        limitations=['Stage0 already starts from strong fixed-target BC; success/reward saturation alone is not improvement.',
            'Training safety maxima are60Hz endpoints; final native evaluation uses all240Hz measurements.',
            'Left hold reward outside the audible interval can rise without improved audible coverage.',
            'First RH target/down error, best error and extra crossings are distinct.',
            'Open gzip snapshots are provisional; committed update files are distinguished from incomplete collection.',
            'Two repeated same-start evaluations do not establish generalization or statistical improvement.'])
    write_new(output,analysis)
    lines=['# Stage0 학습 경과 분석', '', '최종 분석' if args.final else '중간 스냅샷 — 최종 평가 전 결론을 내리지 않는다.', '',
        '| 손 | 완료 update | 커밋 전이 | 학습 episode 성공 | KL retry 합계 | 실제 LR 최소 | 실제 LR 최대 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for role,r in roles.items():
        t=r['training'];s=t['training_summary'];lr=s['actual_actor_lr']
        lines.append('| %s | %d | %d | %d/%d | %d | %s | %s |'%(role,t['committed_updates'],t['committed_transitions'],
            s['successes'],s['committed_episodes'],s['retries_total'],lr['minimum'],lr['maximum']))
    lines+=['','설정 LR와 실제 적용 LR, accepted/attempted KL, reward/cost critic loss는 그래프와 JSON에 각각 기록했다. 학습 로그의 완료 episode는 확률적 행동의 결과이며 별도의 결정적 native 평가와 구분한다.','','왼손은 원 audible 구간의 유지율·연속 유지와 확장 시간창의 긴 유지 보상을 분리했다. 전체 hold 보상 중 audible 성분은 held_second×audible_valid_s이고, 나머지는 audible 밖의 유지 보상이다. pre/post 전용60Hz tick 보상과 경계 tick도 따로 기록했다. 보상이 늘어도 audible 유지율이 이미1이면 정밀 수행 개선으로 단정하지 않는다.','','오른손은 최초 목표 down의 signed/absolute error와 후속 최소 오차, 추가 down/up 및 불필요 crossing을 구분했다. 원래 contact-conditioned joint music50/100ms 기록도 유지했다.','','학습 중 안전 수치는60Hz endpoint 집계이며240Hz 내부 최대를 대신하지 않는다. 최종 native 평가는 별도로 저장된1,200개240Hz 표본에서 기타·발 최대 편차, 접촉, 비용, 깊이·속도와 시계 연속성을 재집계한다.']
    for role,r in roles.items():
        ev=r['native_evaluation']
        if not ev:lines+=['',role+': 최종 native 평가 자료가 아직 없다.'];continue
        lines+=['',role+': 최종 native 평가 기록','',
            '| 회차 | 성공 | 첫 목표 down 오차(ms) | best 오차(ms) | audible 유지율 | 불필요 crossing | 기타 최대 이동(mm) |',
            '|---|---:|---:|---:|---:|---:|---:|']
        for e in ev['episodes']:
            first=e['first_target_down_error_s'];best=e['best_target_abs_error_s']
            lines.append('| %d | %s | %s | %s | %.6f | %d | %.6f |'%(e['episode']+1,e['stage_success'],
                None if first is None else first*1000,None if best is None else best*1000,e['audible_hold_fraction'],
                e['unnecessary_crossings'],e['safety240']['guitar_displacement_max_m']*1000))
    lines+=['',f'전체 수치·입력 byte 스냅샷 SHA: [{output.name}]({output})',f'학습 지표: ![KL·LR·critic]({png})']
    plots(png,roles);write_new(markdown,'\n'.join(lines)+'\n')
    print(json.dumps(dict(output=str(output),final_ready=final_ready,roles={role:dict(
        updates=r['training']['committed_updates'],transitions=r['training']['committed_transitions'],
        episodes=r['training']['training_summary']['committed_episodes'],
        retries=r['training']['training_summary']['retries_total'],
        LR=r['training']['training_summary']['actual_actor_lr'],
        gzip_complete=r['training']['transition_stream']['gzip_complete']) for role,r in roles.items()})))


if __name__=='__main__':main()
