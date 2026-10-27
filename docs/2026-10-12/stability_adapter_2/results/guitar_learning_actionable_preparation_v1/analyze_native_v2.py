"""Analyze actual actionable-preparation traces without importing native code."""
import argparse
from datetime import datetime, timezone
import gc
import gzip
import importlib.util
import hashlib
import json
import math
from pathlib import Path

PHASE=Path(__file__).resolve().parent
OLD=PHASE.parent/'guitar_learning_timing_training_v1'
INPUTS={}


def read(path):
    path=Path(path).resolve();raw=path.read_bytes()
    INPUTS[str(path)]=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    return json.loads(raw)


def sha(path):
    path=Path(path).resolve();h=hashlib.sha256()
    with path.open('rb') as s:
        for data in iter(lambda:s.read(1024*1024),b''):h.update(data)
    INPUTS[str(path)]=dict(sha256=h.hexdigest(),bytes=path.stat().st_size)


def norm(values):return math.sqrt(sum(v*v for v in values))


def safety(rows):
    flags=[r['stability']['flags'] for r in rows]
    return dict(samples=len(rows),guitar_max_m=max(norm(r['stability']['guitar_delta_m']) for r in rows),
        guitar_rotation_max_rad=max(norm(r['stability']['guitar_rotation_vector_rad']) for r in rows),
        feet_max_m=max(norm(v) for r in rows for v in r['stability']['foot_delta_m']),
        any_support_fraction=sum(any(f[:3]) for f in flags)/len(flags),
        triple_fraction=sum(all(f[:3]) for f in flags)/len(flags),
        feet_fraction=sum(all(f[8:]) for f in flags)/len(flags),
        individual_contact_fraction=[sum(bool(f[i]) for f in flags)/len(flags) for i in range(10)],
        failure_reasons=sorted({x for r in rows for x in r['stability']['failure_reasons']}),
        cost_integral=sum(r['stability']['cost'] for r in rows))


def analyze(folder,role,old):
    result=read(folder/'result.json')
    if not result['completed']:raise ValueError('native evaluation incomplete')
    sha(folder/'transitions.json.gz');sha(result['checkpoint'])
    with gzip.open(folder/'transitions.json.gz','rt') as stream:rows=json.load(stream)
    episodes=[]
    for index,summary in enumerate(result['episodes']):
        reset=read(folder/('reset_%02d.json'%index));contract=reset['training_contract']
        initial=reset['prepared_reset']['actual_initial_state'];persist=reset['prepared_reset']['persistent_reset']
        target=contract['task']['targets'][0];identity=target['target_id']
        ticks=[r for r in rows if r['episode']==index]
        physics=[p for r in ticks for p in r['physics_measurements']]
        native=[p for r in ticks for p in r['native_physics_samples240']]
        first=[r for r in ticks if r['tick']<120]
        early=physics[:480]
        names=contract['observation']['joint_order'];active=contract['action']['names']
        selected=active[:33] if role=='left' else active[33:]
        indices=[names.index(name) for name in selected]
        initialq=[r['pos'] for r in initial['human_dof_states']]
        moved={name:max(abs(p['native']['human_dof_states'][i]['pos']-initialq[i]) for p in native[:480])
               for name,i in zip(selected,indices)}
        inactive=slice(33,39) if role=='left' else slice(0,33)
        active_slice=slice(0,33) if role=='left' else slice(33,39)
        previous=bool(reset['specialist']['left']['targets'][identity]['candidate'])
        previous_time=0.;contact_duration=0.;early_duration=0.;audible_duration=0.
        current=0.;longest=0.;early_first=None;credit=0.;credit_errors=[];first_positive_credit=None
        crossings=[]
        for tick in ticks:
            expected_tick=0.
            unsafe=bool(tick['info']['failure_reasons'])
            for p in tick['physics_measurements']:
                measured=p['music'];now=measured['task_time_s']
                candidate=bool(measured['targets'][identity]['candidate'])
                both=previous and candidate
                duration=max(0.,min(now,2.)-max(previous_time,0.)) if both else 0.
                early_duration+=duration
                audible_duration+=max(0.,min(now,target['end_s'])-max(previous_time,target['onset_s'])) if both else 0.
                current=current+now-previous_time if both else 0.;longest=max(longest,current)
                if candidate and now<=2. and early_first is None:early_first=now
                expected=.2*duration if role=='left' and not unsafe else 0.
                actual=p['preparation_contact_reward'];credit_errors.append(abs(actual-expected))
                expected_tick+=expected;credit+=actual
                if actual>0 and first_positive_credit is None:first_positive_credit=now
                contact_duration+=now-previous_time if both else 0.
                crossings.extend(measured['crossings'])
                previous,previous_time=candidate,now
            credit_errors.append(abs(expected_tick-tick['info']['reward_terms']['preparation_contact']))
        for c in crossings:c['error_s']=c['task_time_s']-target['onset_s']
        matching=[c for c in crossings if c['string_number']==target['string']+1 and c['direction']==target['direction'] and c['valid']]
        first_cross=matching[0] if matching else None
        early_terms={}
        for tick in first:
            for key,value in tick['info']['reward_terms'].items():early_terms[key]=early_terms.get(key,0.)+value
        safe=safety(physics);early_safe=safety(early)
        visible=[];goals=[]
        for tick in first:
            obs=tick['observation'];tokens=[v for v,m in zip(obs['events'],obs['mask']) if m]
            visible.append(bool(tokens))
            goals.append(any(abs(v[3]*6-(target['string']+1))<1e-5 and abs(v[4]*22-target['fret'])<1e-5 and
                abs(v[5]*4-target['finger'])<1e-5 and abs(v[6]-target['direction'])<1e-5 for v in tokens))
        baseline=old['roles'][role]['native_evaluation']['episodes'][min(index,1)]
        old_reset=read(OLD/(role+'_stage1_final_eval_v1')/'reset_00.json')
        old_contract=old_reset['training_contract'];old_target=old_contract['task']['targets'][0]
        absolute_comparison={key:dict(old=old_target[key]+old_reset['preparation_seconds'],new=target[key])
                             for key in ('press_s','onset_s','end_s')}
        timing=summary['timing']
        errors=[abs(c['error_s']) for c in matching]
        checks=dict(ticks420=len(ticks)==420,physics1680=len(physics)==1680,
            first2ticks120=len(first)==120,first2physics480=len(early)==480,
            native_count_matches=len(native)==len(physics),each_tick4=all(len(r['physics_measurements'])==len(r['native_physics_samples240'])==4 for r in ticks),
            reset_native0=reset['preparation_seconds']==0.,reset_local_step0=reset['prepared_physics_step']==initial['physics_step']==persist['episode_local_physics_steps']==0,
            first_sim_clock0_or_accumulated=abs(persist['native_sim_time_s']-index*7.)<1e-5,
            consecutive_native_steps=all(p['native']['physics_step']==i+1 for i,p in enumerate(native)),
            clock240=all(abs(p['music']['task_time_s']-(i+1)/240.)<1e-9 for i,p in enumerate(physics)),
            policy_clock_starts0=ticks[0]['tick']==0 and abs(reset['score_time_s']+3.)<1e-9,
            prefix505_fields=contract['observation']['fields'][:505]==old_contract['observation']['fields'][:505],
            prefix505_scales=contract['observation']['scales'][:505]==old_contract['observation']['scales'][:505],
            absolute_score_times=all(abs(pair['new']-pair['old'])<1e-12 for pair in absolute_comparison.values()),
            physical_total7=contract['task']['duration_s']==old_contract['task']['duration_s']+old_reset['preparation_seconds']==7.,
            original_score_metadata=contract['task']['timing']['original_targets']==old_contract['task']['timing']['original_targets'],
            first2_target_visible=all(visible) and all(goals),
            first2_active_nonzero=all(any(abs(v)>1e-8 for v in r['action'][active_slice]) for r in first),
            inactive_exact0=all(v==0 for r in ticks for v in r['action'][inactive]),
            actions_bounded=all(math.isfinite(v) and abs(v)<=1 for r in ticks for v in r['action']),
            actual_active_movement=max(moved.values())>1e-6,
            preparation_credit=max(credit_errors)<1e-12,
            total_cost=abs(safe['cost_integral']-summary['cost'])<1e-8,
            first2_reward_terms=abs(sum(r['reward'] for r in first)-sum(early_terms.values()))<1e-8,
            audible_integral=abs(audible_duration-timing['audible_valid_s'])<1e-9,
            joint_music_untouched=summary['music']==ticks[-1]['info']['music'],
            crossing_eligibility=all(c['valid'] and not c['reason_flags'] and .001<=c['depth_m']<=.015 and abs(c['across_speed_m_s'])>=.05 for c in crossings))
        episodes.append(dict(episode=index,stage_success=timing['stage_success'],reason=summary['reason'],
            native_sim_clock_at_reset_s=persist['native_sim_time_s'],
            first2=dict(active_action_nonzero_ticks=sum(any(abs(v)>1e-8 for v in r['action'][active_slice]) for r in first),
                active_action_max_abs=max(abs(v) for r in first for v in r['action'][active_slice]),
                actual_active_joint_max_delta_rad=moved,first_candidate_s=early_first,
                candidate_positive_samples=sum(bool(p['music']['targets'][identity]['candidate']) for p in early),
                candidate_valid_duration_s=early_duration,preparation_contact_reward=credit,
                first_positive_credit_s=first_positive_credit,credit_max_error=max(credit_errors),
                total_reward=sum(r['reward'] for r in first),reward_terms=early_terms,safety=early_safe),
            full=dict(safety=safe,candidate_longest_s=longest,audible_valid_s=audible_duration,
                audible_hold_fraction=timing['audible_hold_fraction'],first_target_crossing=first_cross,
                best_target_abs_error_s=min(errors) if errors else None,
                down_crossings=sum(c['direction']==1 for c in crossings),up_crossings=sum(c['direction']==-1 for c in crossings),
                extra_target_direction_crossings=max(0,len(matching)-1),crossings=crossings,
                timing=timing,joint_music=summary['music']),
            comparison=dict(absolute_score_times=absolute_comparison,
                old_first_abs_error_s=baseline['first_target_down_abs_error_s'],
                new_first_abs_error_s=abs(first_cross['error_s']) if first_cross else None,
                first_abs_error_delta_s=abs(first_cross['error_s'])-baseline['first_target_down_abs_error_s'] if first_cross else None),checks=checks))
    del rows;gc.collect()
    return dict(completed=result['completed'],source_unchanged=result['source_unchanged'],kind=result['kind'],
        checkpoint=result['checkpoint'],successful_episodes=result['successful_episodes'],episodes=episodes)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',required=True)
    parser.add_argument('--ppo',action='store_true')
    args=parser.parse_args()
    if not args.name.replace('_','').isalnum():raise ValueError('simple new basename required')
    out=PHASE/(args.name+'.json');md=PHASE/(args.name+'.md')
    if out.exists() or md.exists():raise FileExistsError('preserve earlier analysis')
    old=read(OLD/'stage1_final_analysis_v1.json')
    initial=read(PHASE/'initial_native_analysis_v1.json') if args.ppo else None
    roles={r:analyze(PHASE/(r+('_ppo_eval_v1' if args.ppo else '_initial_eval_v1')),r,old) for r in ('left','right')}
    if args.ppo:
        # Reuse only the sealed read-only training-log parser, never native code.
        parser_path=OLD/'analyze_stage0_v5.py'
        spec=importlib.util.spec_from_file_location('sealed_training_reader',parser_path)
        helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        sha(parser_path)
        import torch
        torch.set_num_threads(1)
        for role,r in roles.items():
            train=helper.training(PHASE/(role+'_ppo_smoke_v1'),role)
            INPUTS.update(helper.INPUTS)
            payload=torch.load(r['checkpoint'],map_location='cpu',weights_only=False)
            metadata=dict(schema=payload['identity']['schema'],updates=payload['updates'],
                role=payload['identity']['architecture']['role'])
            r['training']=train;r['evaluated_checkpoint_metadata']=metadata
            r['training_checks']=dict(completed=train['report_completed'],
                counter_one=metadata['updates']==train['committed_updates']==train['settings']['updates']==1,
                transition420=train['committed_transitions']==420,
                source_unchanged=not train['report']['changed_inputs'],
                gzip_complete=train['transition_stream']['gzip_complete'],
                integrals=all(train['checks'].values()))
            del payload
            r['initial_new_evaluation']=initial['roles'][role]
            for e in r['episodes']:
                baseline=initial['roles'][role]['episodes'][0]
                before=baseline['comparison']['new_first_abs_error_s']
                after=e['comparison']['new_first_abs_error_s']
                e['comparison']['same_new_contract_initial_episode0']=dict(
                    initial_first_abs_error_s=before,final_first_abs_error_s=after,
                    delta_s=after-before if before is not None and after is not None else None,
                    initial_audible_fraction=baseline['full']['audible_hold_fraction'],
                    final_audible_fraction=e['full']['audible_hold_fraction'],
                    scope='one final episode vs first of two initial same-contract episodes; descriptive only')
    sha(Path(__file__))
    valid=all(r['source_unchanged'] and all(all(e['checks'].values()) for e in r['episodes']) and
        (not args.ppo or all(r['training_checks'].values())) for r in roles.values())
    result=dict(schema='guitar_learning.actionable_native_analysis.v2',created_utc=datetime.now(timezone.utc).isoformat(),
        mode='post_PPO' if args.ppo else 'initial_actor_migration',evidence_checks_passed=valid,roles=roles,input_snapshots=INPUTS,
        limits=['First2s actual actions and movements establish actionable control, not isolated causal effect of each joint.',
            'Source policy success is not inherited; changed initial physical/time distributions require separate validation.',
            'Relaxed single-hand timing stage is separate from strict joint music, pressure, sound and generalization.',
            'Reset local clock0 is separate from cumulative simulator clock on repeated resets.',
            'Long contact is not evidence of precise release or next-fret transition.'])
    with out.open('x') as s:json.dump(result,s,indent=2);s.write('\n')
    lines=['# 정책 준비시간 전환: 실제 native 결과', '',
        '원자료 검사 통과: **%s**. native 정착0초·정책 pre-roll3초·총7초이며 첫2초에도 음악 목표를 관측하고 행동한다. 반복 reset의 episode 시각0과 누적 시뮬레이터 시각을 구분했다.'%valid, '',
        '| 손 | 회차 | 단계 성공 | 첫2초 행동 tick | 첫2초 실제 관절 최대변화(rad) | 접촉 준비보상 | audible 유지율 | 첫 목표 down 오차(ms) | 기타 최대 이동(mm) |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for role,r in roles.items():
        for e in r['episodes']:
            cross=e['full']['first_target_crossing'];first=e['first2'];full=e['full']
            lines.append('| %s | %d | %s | %d/120 | %.6f | %.6f | %s | %s | %.6f |'%(role,e['episode']+1,e['stage_success'],first['active_action_nonzero_ticks'],max(first['actual_active_joint_max_delta_rad'].values()),
                first['preparation_contact_reward'],'%.6f'%full['audible_hold_fraction'] if role=='left' else '해당 없음',
                '%.6f'%(cross['error_s']*1000) if cross else '해당 없음',full['safety']['guitar_max_m']*1000))
    if args.ppo:
        lines+=['', '학습은 각 손 N1/H420/1 update·420전이의 연결 스모크다. 확률적 학습 episode와 각1회 결정적 최종평가를 구분한다. 이것만으로 충분한 학습량이나 수렴을 주장하지 않는다.', '',
            '| 손 | 실제 actor LR | accepted KL | 최대 시도 KL | retry | reward critic loss | cost critic loss |',
            '|---|---:|---:|---:|---:|---:|---:|']
        for role,r in roles.items():
            u=r['training']['updates'][0]
            lines.append('| %s | %s | %.8f | %.8f | %d | %.8f | %.8f |'%(role,u['actor_lr'],u['analytic_kl'],u['max_attempted_kl'],u['kl_retries'],u['reward_value_loss'],u['cost_value_loss']))
            e=r['episodes'][0];c=e['comparison']['same_new_contract_initial_episode0']
            if role=='right':
                lines+=['', '오른손 동일 새 계약 initial회차1 대비: %.6f→%.6fms(변화%+.6fms). 초기 두 회차의 변동도 보존하며, 단회 스모크 결과를 일반적 개선으로 해석하지 않는다.'%(c['initial_first_abs_error_s']*1000,c['final_first_abs_error_s']*1000,c['delta_s']*1000)]
    lines+=['', '기존 native2초+정책5초와 새 정책7초의 절대 목표 press/onset/end 시각은 같으며 onset4.12초다. 관측 앞505개 필드·scale도 보존했다. 이것이 행동 성능 보존을 뜻하지는 않는다.', '',
        '오른손은 새로운 실제 시작상태와 시간 입력에서 오차가 달라졌다. 동일 stage의 성공 여부와 첫 crossing 오차·추가 down/up을 별도로 평가하며 이전 성공을 상속하지 않는다. 첫2초의 접촉 보상은 원 candidate 이전/현재가 모두 양성인 실제 구간만 .2/s로 적분했다. 거리 proxy·현 압력·음향 성공으로 확대하지 않는다.', '',
        '각 episode420 tick·1680 physics, 첫2초120 tick·480 physics에서 반대손0·실제 관절 변화·비용·보상·시계·접촉 적분을 확인했다. 자세 안전과 음악 단계의 성공은 원 JSON의 별도 지표다. 가슴·삼중 접촉률은 진단이다.', '',
        '[모든 수치와 입력 SHA](%s)'%out]
    with md.open('x') as s:s.write('\n'.join(lines)+'\n')
    print(json.dumps(dict(output=str(out),checks_passed=valid,roles={r:[dict(success=e['stage_success'],failed_checks=[k for k,v in e['checks'].items() if not v],first2credit=e['first2']['preparation_contact_reward'],first_cross=e['full']['first_target_crossing']['error_s'] if e['full']['first_target_crossing'] else None) for e in d['episodes']] for r,d in roles.items()})))


if __name__=='__main__':main()
