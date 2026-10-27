"""CPU comparison of equal100-update changing-policy training collections.

Old run is a committed prefix of a later failed attempt. New run needs its
actual completed report. Neither is a fixed checkpoint evaluation or causal
control ablation. Open songs at the budget boundary are not ended episodes.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
ROOT=Path(__file__).resolve().parents[3]
PHASE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from guitar_learning.training import json_io

FINGERS=('index','middle','ring','pinky')
BUDGET=100
TRANSITIONS=100*32*1024


def require(ok,message):
    if not ok:raise ValueError(message)


def finite(value):
    if isinstance(value,float):require(math.isfinite(value),'Nonfinite logged number')
    elif isinstance(value,dict):
        for v in value.values():finite(v)
    elif isinstance(value,list):
        for v in value:finite(v)


def episode_features(e,targets):
    v=e['left_note_ledger']['values'];ids=[t['target_id'] for t in targets]
    require(e['valid'] and e['left_note_ledger']['target_ids']==ids and all(len(x)==67 for x in v.values()),'Invalid67-note episode')
    require(sum(v['left'])==e['song']['left_success_count'],'Raw note count mismatch')
    safe=e['reason']=='timeline_complete' and e['left_curriculum']['full_safe']
    require(safe or e['reason']=='terminal_failure','Unexpected episode reason')
    m=dict(duration_s=e['task_time_s'],achieved_notes=e['song']['left_success_count'],
        wrist_ready=e['left_curriculum']['reach_fraction'],reward=e['reward'],cost=e['cost'],
        original_cost=e['cost_components']['original_physics_and_terminal'],
        remaining_cost=e['cost_components']['remaining_song_failure'],progress=e['left_curriculum']['progress'])
    lengths=np.asarray([t['end_s']-t['onset_s'] for t in targets]);clean=np.minimum(np.asarray(v['clean'])/lengths,1)
    m['clean_fraction']=float(clean.mean())
    for f,name in enumerate(FINGERS,1):
        ix=[j for j,t in enumerate(targets) if t['finger']==f]
        fm=e['left_curriculum']['finger_metrics'][f-1]
        require(fm['target_count']==len(ix),'Finger count mismatch')
        for field,key in (('near_fraction','near_done'),('contact_fraction','contact_done'),('success_fraction','left')):
            actual=sum(v[key][j] for j in ix)/len(ix)
            require(math.isclose(actual,fm[field],rel_tol=1e-6,abs_tol=1e-7),'Raw finger metric mismatch')
            m[name+'.'+field]=actual
        m[name+'.achieved_notes']=sum(v['left'][j] for j in ix)
        m[name+'.clean_fraction']=float(clean[ix].mean())
    motion=e.get('left_finger_motion')
    if motion is not None:
        require(motion['endpoint_samples']==e['steps'] and motion['sampling_hz']==60,'Motion endpoint mismatch')
        for finger in ('thumb',*FINGERS):
            ix=[j for j,n in enumerate(motion['joint_names']) if n.startswith('LH:'+finger)]
            for field in ('actual_range_rad','target_range_rad','tracking_error_rms_rad','limit_outward_command_fraction'):
                m['motion.'+finger+'.'+field]=sum(motion['values'][field][j] for j in ix)/len(ix)
    return dict(env_id=e['env_id'],safe=safe,reason=e['reason'],failure_reasons=e['failure_reasons'],metrics=m,
                stage_success=e['song']['stage_success'],motion_available=motion is not None)


class Group:
    def __init__(self):self.rows=0;self.total=Counter();self.reasons=Counter();self.times=[];self.safe=0;self.full=0;self.motion=0
    def add(self,e):
        self.rows+=1;self.total.update(e['metrics']);self.safe+=int(e['safe']);self.full+=int(e['stage_success']);self.motion+=int(e['motion_available'])
        if not e['safe']:self.reasons.update(e['failure_reasons']);self.times.append(e['metrics']['duration_s'])
    def result(self):
        return dict(ended=self.rows,safe=self.safe,physical_failures=len(self.times),safe_fraction=self.safe/self.rows if self.rows else None,
            full67_successes=self.full,means={k:v/self.rows for k,v in self.total.items()} if self.rows else {},
            achieved_notes_total=self.total['achieved_notes'],
            finger_achieved_notes_total={f:self.total[f+'.achieved_notes'] for f in FINGERS},
            failure_reason_occurrences=dict(self.reasons),failure_duration_s=dict(count=len(self.times),mean=float(np.mean(self.times)) if self.times else None,
                minimum=min(self.times,default=None),maximum=max(self.times,default=None),
                below1=sum(x<1 for x in self.times),at_most1=sum(x<=1 for x in self.times)),
            motion_available_episodes=self.motion,motion_scope='Equal ended-episode, equal-axis means of60Hz endpoint diagnostics; old records have no such diagnostics, not zeros')


def summarize(run,label,read):
    settings=read(run/'settings.json');contract=read(run/'training_contract.json')
    if label=='new_completed_smoke100':require(settings['updates']==100,'New run budget must be100')
    require((settings['size'],settings['num_envs'],settings['horizon'],settings['seed'],settings['specialist']['role'])==('large',1024,32,7,'left'),'Expected large1024/H32/seed7 left')
    targets=contract['task']['provenance']['song']['schedule'];require(len(targets)==67,'Expected67 targets')
    groups={k:Group() for k in ('all_ended','safe_ended','failed_ended','first_episode_all','first_episode_safe')}
    first={};hashes=[];curve=[];changes=[];previous=settings['ppo']['actor_lr'];nonfinite=0;committed_duration=TRANSITIONS/60.
    for index in range(BUDGET):
        row=read(run/('update_%06d.json'%index));finite(row)
        require(row['update_index']==index and row['optimizer_updates']==index+1 and row['transitions']==32768 and row['journal']['committed']==(index+1)*32768,'Uncommitted or wrong update prefix')
        d=row['diagnostics'];post=d['post_update'];std=post['active_distribution']['std']
        if row['actor_lr']!=previous:changes.append(dict(update_index=index,optimizer_updates=index+1,before=previous,after=row['actor_lr']));previous=row['actor_lr']
        def count_bad(v):
            if isinstance(v,dict):
                return sum((int(x) if k=='nonfinite_count' else sum(x.values()) if k=='nonfinite_steps' else count_bad(x)) for k,x in v.items())
            return 0
        nonfinite+=count_bad(d)
        curve.append(dict(update_index=index,actor_lr=row['actor_lr'],analytic_kl=row['analytic_kl'],kl_retries=row['kl_retries'],
            max_attempted_kl=row['max_attempted_kl'],std_mean=std['mean'],std_min=std['min'],std_max=std['max'],
            mean_reward=row['mean_reward'],mean_cost=row['mean_cost'],progress=row['left_curriculum']['progress'],
            action_saturation=post['active_distribution']['collected_action_saturation_fraction'],
            reward_critic_mse=post['critics']['reward']['mse'],cost_critic_mse=post['critics']['cost']['mse']))
        for e in row['completed_episodes']:
            feature=episode_features(e,targets);require(0<=feature['env_id']<1024,'Unexpected envID')
            hashes.append((index,hashlib.sha256(json_io.dumps(e,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()))
            groups['all_ended'].add(feature);groups['safe_ended' if feature['safe'] else 'failed_ended'].add(feature)
            if feature['env_id'] not in first:
                first[feature['env_id']]=feature;groups['first_episode_all'].add(feature)
                if feature['safe']:groups['first_episode_safe'].add(feature)
    # Independently match ended stream before100 against committed update payloads.
    ended_path=run/'episodes.jsonl';seen=[]
    with ended_path.open() as stream:
        for line in stream:
            if not line.endswith('\n'):break
            row=json.loads(line)
            if row['update_index']>=BUDGET:break
            seen.append((row['update_index'],hashlib.sha256(json_io.dumps(row['episode'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()))
    require(hashes==seen,'Ended JSONL and committed update episodes differ')
    # Hash the consumed episode prefix, not a live file beyond the authorized budget.
    require(len(first)==1024,'Not all first episodes ended within100 updates')
    result={k:g.result() for k,g in groups.items()}
    result.update(label=label,run=str(run),committed_updates=100,committed_transitions=TRANSITIONS,total_environment_seconds=committed_duration,
        episode_stream_prefix_sha256=hashlib.sha256(json_io.dumps(seen).encode()).hexdigest(),
        all_logged_numbers_finite=True,reported_nonfinite_indicator_sum=nonfinite,actor_lr_events=changes,
        ongoing_episode_time_sum_s=committed_duration-groups['all_ended'].total['duration_s'],
        physical_failures_per1000_environment_seconds=1000*len(groups['all_ended'].times)/committed_duration,
        update_curve=curve,update_means={k:float(np.mean([r[k] for r in curve])) for k in curve[0] if k!='update_index'},
        last_update=curve[-1],minimum_std=min(r['std_min'] for r in curve),maximum_std=max(r['std_max'] for r in curve),
        actor_lr_first=curve[0]['actor_lr'],actor_lr_last=curve[-1]['actor_lr'],kl_retries_sum=sum(r['kl_retries'] for r in curve),
        max_attempted_kl=max(r['max_attempted_kl'] for r in curve))
    extra=groups['all_ended'].total['remaining_cost']/TRANSITIONS
    result['step_cost_components']=dict(remaining_song_failure=extra,
        original_physics_and_terminal=result['update_means']['mean_cost']-extra,
        denominator=TRANSITIONS,scope='All committed step costs, including open songs; subtract all ended failure extras. Residual uses logged float step means.')
    return result,first,settings,contract


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old',type=Path,default=PHASE.parent/'guitar_learning_surface_training_v1/train1024_large_2000')
    parser.add_argument('--new',type=Path,default=PHASE/'smoke100')
    args=parser.parse_args();old=args.old.resolve();new=args.new.resolve();inputs={}
    def read(path):
        inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();return json.loads(path.read_text())
    require((new/'report.json').exists(),'New smoke100 is incomplete; wait for its actual completed report')
    report=read(new/'report.json')
    require(report['completed'] is True and report['optimizer_updates']==100 and len(report['updates'])==100 and
            report['transitions']==TRANSITIONS and report['gpu_scene']['closed'] and report['lifecycle_verified'] and
            report['gpu_scene']['physx_use_gpu'] and report['gpu_scene']['use_gpu_pipeline'] and report['gpu_scene']['environment_count']==1024 and
            report['gpu_scene']['physics_steps']==12800 and not report['failure'] and not report['cleanup_errors'] and
            not report['changed_inputs'] and not report['missing_import_pins'],'New smoke100 not fully completed/closed')
    require((old/'checkpoint_000099.pt').is_file(),'Actual old100 checkpoint absent')
    inputs[str(old/'checkpoint_000099.pt')]=hashlib.sha256((old/'checkpoint_000099.pt').read_bytes()).hexdigest()
    a,af,settings,ac=summarize(old,'old_committed_first100_prefix_of_later_failed_attempt',read)
    b,bf,ns,bc=summarize(new,'new_completed_smoke100',read)
    require(report['settings']==ns,'New report/settings mismatch')
    for key in ('ppo','song','song_training','initial_std','physics_backend'):require(settings[key]==ns[key],'Comparison setting changed: '+key)
    same_semantics={key:ac[key]==bc[key] for key in ('observation','task','reward','termination')}
    require(all(same_semantics.values()),'Reward/observation/task/safety contract differs')
    matched=[i for i in range(1024) if af[i]['safe'] and bf[i]['safe']]
    paired={}
    for name,features in (('old',af),('new',bf)):
        group=Group()
        for i in matched:group.add(features[i])
        paired[name]=group.result()
    result=dict(schema='guitar_learning.incremental_smoke100_training_comparison.v1',completed=True,
        budget_updates=100,budget_transitions_per_run=TRANSITIONS,old=a,new=b,matched_first_safe_ids=len(matched),matched_first_safe=paired,
        unchanged_semantic_contract_sections=same_semantics,
        old_control_schema=ac['action']['target_contract']['schema'],new_control_schema=bc['action']['target_contract']['schema'],
        limitations=['Changing stochastic policies over100 updates; not fixed-checkpoint policy evaluation or control-only causal proof.',
            'All-ended fractions include different episode/cycle mixtures; first1024 fixes the first-episode denominator. Open songs at budget end are excluded from ended metrics.',
            'Old8.301/67 was a separate optimizer2000 fixed evaluation and is not used as a performance delta here.',
            'Finite metrics and reported nonfinite indicators are distinct from natural physical failures.60Hz joint diagnostics do not certify240Hz extrema, contact pressure or sound.',
            'Same single seed/song and prepared initial conditions; not independent-seed or unseen-song generalization.'],inputs_sha256=inputs)
    finite(result)
    require(all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==d for n,d in inputs.items()),'Comparison input changed')
    (PHASE/'smoke_comparison.json').write_text(json_io.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=['# 동일100업데이트 학습 수집 비교','',
        '두 실행의 첫100회·각3,276,800전이를 비교한다. 이전 실행은 나중에 중단된 원본의 저장 checkpoint99까지의 유효 prefix, 새 실행은 실제 완료된 smoke100이다. 서로 계속 변하는 확률 정책의 수집이며 고정 평가나 누적 제어 단독 인과 실험이 아니다.','',
        '| 구분 | 이전 첫100 | 새 smoke100 |','| --- | ---: | ---: |']
    for title,key in [('종료 곡','ended'),('안전 완주','safe'),('물리실패','physical_failures')]:lines.append(f'| {title} | {a["all_ended"][key]} | {b["all_ended"][key]} |')
    for title,path in [('안전곡 평균 달성/67','achieved_notes'),('안전곡 평균 clean 비율','clean_fraction')]:lines.append(f'| {title} | {a["safe_ended"]["means"].get(path,0):.6f} | {b["safe_ended"]["means"].get(path,0):.6f} |')
    for title,key in [('고정 첫1024 중 안전','safe'),('고정 첫1024 중 실패','physical_failures')]:lines.append(f'| {title} | {a["first_episode_all"][key]} | {b["first_episode_all"][key]} |')
    lines+=['',f'전체 종료 분모는 각각{a["all_ended"]["ended"]}/{b["all_ended"]["ended"]}곡이며 실패 후 재시작한 뒤의 종료도 포함한다. 첫 곡1024개는 두 실행 모두 관측됐고 안전 비율은 {100*a["first_episode_all"]["safe_fraction"]:.3f}%/{100*b["first_episode_all"]["safe_fraction"]:.3f}%다. 공통 첫 안전 환경ID {len(matched)}개만 비교해도 평균 달성은 {paired["old"]["means"]["achieved_notes"]:.6f}→{paired["new"]["means"]["achieved_notes"]:.6f}/67이다. 다만 동일 환경ID도 두 정책의 궤적은 다르며 동일 궤적 통제 실험은 아니다. 예산 말에 진행 중이던 곡의 시간 합은 {a["ongoing_episode_time_sum_s"]:.3f}/{b["ongoing_episode_time_sum_s"]:.3f}환경초이며 종료 평균에 넣지 않았다. 각 실행 총54,613.333환경초 기준 실패는 {a["physical_failures_per1000_environment_seconds"]:.3f}/{b["physical_failures_per1000_environment_seconds"]:.3f}회/1000환경초다.','',
        '## 실패 시점과 안전곡의 손가락 지표','',f'이전 실패 사유 발생 횟수는{a["failed_ended"]["failure_reason_occurrences"]}, 새 실행은{b["failed_ended"]["failure_reason_occurrences"]}다. 한 종료에 여러 사유가 겹칠 수 있다. 실패곡 평균 길이는 {a["failed_ended"]["failure_duration_s"]["mean"]:.3f}/{b["failed_ended"]["failure_duration_s"]["mean"]:.3f}초,1초 미만은 {a["failed_ended"]["failure_duration_s"]["below1"]}/{b["failed_ended"]["failure_duration_s"]["below1"]}곡이다.','',
        '| 손가락 | 접근 이전→새(%) | 접촉 이전→새(%) | 달성 이전→새(%) |','| --- | ---: | ---: | ---: |']
    for finger in FINGERS:
        pairs=[(100*a['safe_ended']['means'].get(finger+'.'+k,0),100*b['safe_ended']['means'].get(finger+'.'+k,0)) for k in ('near_fraction','contact_fraction','success_fraction')]
        lines.append('| '+finger+' | '+' | '.join(f'{x:.3f}→{y:.3f}' for x,y in pairs)+' |')
    lines+=['','표는 각 실행 안전 완주곡의 손가락별 배정25/18/12/12음 분모다. 두 안전 집단은 구성과 크기가 다르다. 실패곡·전체종료·첫 곡·공통 첫 안전 ID의 원자료 지표는 JSON에 따로 보존했다. 접근은10mm 근접, 접촉은준비~종료의하중기하후보, 달성은음구간clean누적문턱이며압력/소리가아니다.','',
        f'안전곡 달성 합계는 이전 {a["safe_ended"]["achieved_notes_total"]}음(전부 검지), 새 {b["safe_ended"]["achieved_notes_total"]}음이다. 새 안전곡의 검지/중지/약지/소지 합계는 {"/".join(str(b["safe_ended"]["finger_achieved_notes_total"][f]) for f in FINGERS)}음이다. 중지·약지 달성이 생겼지만 검지 달성 감소가 커 전체 안전곡 평균은 낮아졌다. 이는 종료 안전 집단에서 관측한 분포 변화이며 손가락별 제어 효과의 인과 증명은 아니다.','',
        '## 새 실행의 실제/목표 움직임','',
        '이전 첫100회에는 관절 움직임 진단이 없으므로 아래 표에 이전값0을 채우거나 제어범위 증가량을 계산하지 않는다. 새 실행 안전곡의60Hz 진단만 관절별·곡별 동일 가중으로 요약한다. 실제/목표 범위는t0 포함, RMS는control 종료 지점이다.240Hz 극값이나 압현 힘은 아니다.','',
        '| 새 안전곡 손가락 | 실제 범위 평균(rad) | 명령 범위 평균(rad) | 에피소드 RMS 평균(rad) | 한계 바깥 명령 비율 |',
        '| --- | ---: | ---: | ---: | ---: |']
    for finger in ('thumb',*FINGERS):
        m=b['safe_ended']['means'];prefix='motion.'+finger+'.'
        lines.append(f'| {finger} | {m[prefix+"actual_range_rad"]:.6f} | {m[prefix+"target_range_rad"]:.6f} | {m[prefix+"tracking_error_rms_rad"]:.6f} | {100*m[prefix+"limit_outward_command_fraction"]:.3f}% |')
    lines+=['', '목표는 명령 위치이고 실제 q의 즉각 정지·반전이 아니다. 한계 바깥 비율은 이전 명령 목표가native한계에있고action이바깥을향하는비율이며,실제접촉/관절충돌비율과다르다. 안전곡과실패곡의길이도달라실패곡범위를같은길이의시험처럼비교하지않는다.','',
        '## PPO·수치와 해석 범위','',
        f'같은3,276,800전이에 대한 step평균 reward는{a["update_means"]["mean_reward"]:.6f}/{b["update_means"]["mean_reward"]:.6f},cost는{a["update_means"]["mean_cost"]:.6f}/{b["update_means"]["mean_cost"]:.6f}다. 남은곡 실패비용/전이는 {a["step_cost_components"]["remaining_song_failure"]:.6f}/{b["step_cost_components"]["remaining_song_failure"]:.6f}, 이를 뺀 원래 비용/전이는 {a["step_cost_components"]["original_physics_and_terminal"]:.6f}/{b["step_cost_components"]["original_physics_and_terminal"]:.6f}다. 종료곡 평균과 분모가 다르며 진행 중 곡의 기존 비용도 step평균에 포함한다. 새 reward는 덜 음수지만 안전곡 음 달성은 낮아 보상 평균만으로 정책 향상을 선언할 수 없다. curriculum 마지막진행도는{a["last_update"]["progress"]:.1f}/{b["last_update"]["progress"]:.1f}다.','',f'LR은 이전 {a["actor_lr_first"]:.8g}→{a["actor_lr_last"]:.8g}, 새 {b["actor_lr_first"]:.8g}→{b["actor_lr_last"]:.8g}다. KL retry합은{a["kl_retries_sum"]}/{b["kl_retries_sum"]}, update별 마지막 accepted KL 평균은{a["update_means"]["analytic_kl"]:.6f}/{b["update_means"]["analytic_kl"]:.6f}다. 마지막 활성 latent std 평균은{a["last_update"]["std_mean"]:.6f}/{b["last_update"]["std_mean"]:.6f}다. 전체 수집/모든 minibatch를 한 번에 가중한 KL은 아니다.','',
        f'기록된 모든 숫자는 유한하고 nonfinite 진단 지표합은{a["reported_nonfinite_indicator_sum"]}/{b["reported_nonfinite_indicator_sum"]}이다. 물리실패 증가가 있다면 이를 곧 수치 폭발·native 오류·학습 붕괴라고 단정하지 않는다. 새 누적 제어는 같은 action/std도 시간에 따른 목표 이동으로 해석하므로 이전 절대 residual과 물리 탐색 범위가 같다는 뜻도 아니다. 새 실제/목표 범위·추종·한계 바깥 명령은60Hz 진단으로만 기록됐고 이전 로그에는 해당 진단이 없어 직접 범위 차이를 만들지 않았다.','',
        '보상·관측·과제·안전 계약은 같지만 제어 계약·실제 궤적·PPO 갱신·종료곡 구성은 달라진다. 따라서 이100회 수치만으로 제어 변경이 각 실패나 음 성과를 일으켰다고 확정할 수 없다. 이전2000회 고정 평가8.301음과 새100회 수집 평균을 같은 성과 변화로 비교하지 않는다.','']
    (PHASE/'smoke_comparison.md').write_text('\n'.join(lines))
    print(json_io.dumps(dict(completed=True,old_safe=a['all_ended']['safe'],new_safe=b['all_ended']['safe'])))


if __name__=='__main__':main()
