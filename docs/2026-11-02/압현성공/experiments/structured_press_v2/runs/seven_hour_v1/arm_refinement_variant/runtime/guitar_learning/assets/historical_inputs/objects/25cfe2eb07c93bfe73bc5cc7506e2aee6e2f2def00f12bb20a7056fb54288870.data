"""Reclassify frozen trajectories without physics, policy inference or rewards.

Only the new fretting classifier and pick preparation/recovery measurement are
replayed. These counterfactual measurements are not a new native policy trial.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from .fretting_quality import classify_fretting, FRETTING_QUALITY_METADATA
from .fretting_v1 import FretContract
from .geometry_v1 import geometry_snapshot
from .music_task import ScoreTarget
from .strike_quality import StrikeQualityDetector, STRIKE_QUALITY_METADATA

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1'


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


class Inputs:
    def __init__(self):self.files={}

    def pin(self,path):
        path=Path(path).resolve()
        actual=dict(sha256=digest(path),bytes=path.stat().st_size)
        if str(path) in self.files and self.files[str(path)]!=actual:
            raise RuntimeError('input changed during audit: '+str(path))
        self.files[str(path)]=actual
        return path

    def read(self,path):return json.loads(self.pin(path).read_text())

    def verify(self):
        return [path for path,value in self.files.items() if digest(path)!=value['sha256']]


def initial_geometry(reset,inputs):
    paths=[Path(p) for p in reset['prepared_reset']['source_sha256'] if Path(p).name=='initial_values.json']
    if len(paths)!=1:raise ValueError('one pinned original body-name input required')
    path=inputs.pin(paths[0])
    if inputs.files[str(path)]['sha256']!=reset['prepared_reset']['source_sha256'][str(path)]:
        raise ValueError('body-name input differs from original reset provenance')
    names=inputs.read(path)
    state=reset['prepared_reset']['actual_initial_state']
    if state['physics_step']!=0 or reset['prepared_physics_step']!=0:
        raise ValueError('actual recorded episode-local native step0 required')
    return geometry_snapshot(state,names['human_body_names'],names['guitar_body_names'])


def analyze_left(folder,inputs):
    result=inputs.read(folder/'result.json');reset=inputs.read(folder/'reset_00.json')
    if not result['completed'] or len(result['episodes'])!=1:raise ValueError('complete one-episode frozen source required')
    target=ScoreTarget(**reset['training_contract']['task']['targets'][0]);identity=target.target_id
    path=inputs.pin(folder/'transitions.json.gz')
    with gzip.open(path,'rt') as stream:rows=json.load(stream)
    counts=Counter();examples={};positive_audible=clean_audible=observed_audible=0.
    post_threshold=target.end_s+.1;post_observed=post_clear=post_contact=0.
    clear_current=clear_longest=0.;previous=None;credit_checks=[];sample_count=0
    for row in rows:
        if row['episode']!=0:raise ValueError('single source episode expected')
        if len(row['physics_measurements'])!=len(row['native_physics_samples240'])!=4:
            raise ValueError('four aligned measured/native samples required')
        for p,sample in zip(row['physics_measurements'],row['native_physics_samples240']):
            measured=p['music'];evidence=measured['targets'][identity]['evidence']
            q=classify_fretting(sample['geometry'],target,evidence,FretContract(**evidence['contract']))
            sample_count+=1;now=measured['task_time_s']
            if p['physics_step']!=sample['native']['physics_step'] or p['physics_step']!=sample_count:
                raise ValueError('consecutive aligned source physics required')
            if abs(now-sample_count/240.)>1e-9:raise ValueError('actual240Hz source clock required')
            counts[q['status']]+=1
            for key in ('positive_target_candidate','clean_target_candidate','wrong_finger','wrong_fret',
                        'higher_fret','wrong_assignment','incidental_other_string','uncertain'):
                counts[key]+=int(q[key])
            counts['target_string_contact']+=bool(q['target_string_contact_evidence_ids'])
            credit_checks.append(q['positive_target_candidate']==measured['targets'][identity]['candidate'])
            for key in ('higher_fret','wrong_assignment','wrong_fret','incidental_other_string','uncertain'):
                if q[key] and key not in examples:
                    examples[key]=dict(physics_step=p['physics_step'],task_time_s=now,quality=q)
            if previous is not None:
                oldtime,oldq=previous
                audible=max(0.,min(now,target.end_s)-max(oldtime,target.onset_s));observed_audible+=audible
                positive_audible+=audible if oldq['positive_target_candidate'] and q['positive_target_candidate'] else 0.
                clean_audible+=audible if oldq['clean_target_candidate'] and q['clean_target_candidate'] else 0.
                after=max(0.,now-max(oldtime,post_threshold));post_observed+=after
                clear=not q['target_string_contact_evidence_ids'];oldclear=not oldq['target_string_contact_evidence_ids']
                post_clear+=after if clear and oldclear else 0.
                post_contact+=after*.5*(float(not clear)+float(not oldclear))
                clear_current=clear_current+after if after>0 and clear and oldclear else 0.
                clear_longest=max(clear_longest,clear_current)
            if now>=post_threshold:
                counts['after_end_plus100ms_samples']+=1
                counts['after_end_plus100ms_clear_samples']+=not q['target_string_contact_evidence_ids']
            previous=(now,q)
    duration=target.end_s-target.onset_s
    checks=dict(source1680=sample_count==1680,source420ticks=len(rows)==420,
        original_candidate_preserved=all(credit_checks),all_samples_partitioned=sum(counts[k] for k in ('correct','wrong','missing'))==sample_count,
        audible_fully_bracketed=abs(observed_audible-duration)<1e-9,
        original_audible_matches_source_ledger=abs(positive_audible-result['episodes'][0]['timing']['audible_valid_s'])<1e-9)
    del rows;gc.collect()
    return dict(source=str(folder),source_native_stage_success=result['episodes'][0]['timing']['stage_success'],
        source_native_success_is_not_reclassified=True,source_unchanged_at_recording=result['source_unchanged'],
        samples=sample_count,status_and_flag_sample_counts=dict(counts),
        audible=dict(interval_s=[target.onset_s,target.end_s],duration_s=duration,observed_interval_s=observed_audible,
            original_positive_s=positive_audible,clean_s=clean_audible,
            original_positive_fraction=positive_audible/duration,clean_fraction=clean_audible/duration,
            integration='both adjacent observed samples positive; clip fractional boundaries; initial contact not invented'),
        after_note=dict(threshold_s=post_threshold,observed_interval_s=post_observed,
            clear_both_endpoints_s=post_clear,contact_occupancy_trapezoid_s=post_contact,
            longest_contiguous_clear_s=clear_longest,has50ms_clear=clear_longest+1e-12>=.05,
            final_target_string_clear=not previous[1]['target_string_contact_evidence_ids'],
            final_fretting_quality=previous[1]),
        initialization='classify stored evidence directly; no synthetic initial contact, original TaskMeasurement or dynamics replay',
        examples=examples,checks=checks)


def analyze_right(folder,inputs):
    result=inputs.read(folder/'result.json');reset=inputs.read(folder/'reset_00.json')
    if not result['completed'] or len(result['episodes'])!=1:raise ValueError('complete one-episode frozen source required')
    target=ScoreTarget(**reset['training_contract']['task']['targets'][0])
    previous=initial_geometry(reset,inputs);detector=StrikeQualityDetector(target)
    path=inputs.pin(folder/'transitions.json.gz')
    with gzip.open(path,'rt') as stream:rows=json.load(stream)
    old_crossings=[];new_events=[];first_ready=None;first_recovered=None;candidate_matches=[];steps=0
    for row in rows:
        if row['episode']!=0 or len(row['physics_measurements'])!=4 or len(row['native_physics_samples240'])!=4:
            raise ValueError('single episode with four aligned samples per tick required')
        for p,sample in zip(row['physics_measurements'],row['native_physics_samples240']):
            current=sample['geometry'];steps+=1
            if current['physics_step']!=steps or p['physics_step']!=steps:
                raise ValueError('actual source sequence must be0 then1..1680')
            update=detector.update(previous,current);quality=detector.summary()
            candidate_matches.append(update['candidates']==p['music']['crossing_candidates'])
            old_crossings.extend(p['music']['crossings'])
            for event in update['events']:
                event=dict(event,task_time_s=event['physics_step_fraction']/240.)
                event['onset_error_s']=event['task_time_s']-target.onset_s;new_events.append(event)
            if quality['ready'] and first_ready is None:first_ready=steps/240.
            if quality['recovered'] and first_recovered is None:first_recovered=steps/240.
            previous=current
    final=detector.summary();fields=reset['training_contract']['observation']['fields'];scales=reset['training_contract']['observation']['scales']
    # The saved actor sees the actual origin of RH:pick; check geometry0 against
    # its independent float32 reset observation as well as named native states.
    geometry0=initial_geometry(reset,inputs)
    observed=np.array([rows[0]['observation']['state'][fields.index('RH:pick_in_guitar.p_'+axis)]*
                       scales[fields.index('RH:pick_in_guitar.p_'+axis)] for axis in 'xyz'])
    initial_pick_error=float(np.max(np.abs(observed-geometry0['pick_G_m'])))
    matching=lambda e:e['string_number']==target.string+1 and e['direction']==target.direction
    old_matching=[e for e in old_crossings if matching(e)];new_matching=[e for e in new_events if matching(e)]
    del rows;gc.collect()
    return dict(source=str(folder),source_native_stage_success=result['episodes'][0]['timing']['stage_success'],
        source_native_success_is_not_reclassified=True,source_unchanged_at_recording=result['source_unchanged'],
        initialization=dict(native_actual_step0=True,geometry0_source='reset.prepared_reset.actual_initial_state + pinned original body names',
            initial_pick_G_m=geometry0['pick_G_m'].tolist(),reset_actor_pick_max_abs_error_m=initial_pick_error,
            no_initial_contact_required=True),
        physics_samples_replayed=steps,original_eligible_crossings=old_crossings,
        new_preparation_filtered_events=new_events,original_matching_crossings=len(old_matching),
        new_accepted_matching_crossings=len(new_matching),original_crossing_count=len(old_crossings),
        new_event_count=len(new_events),first_ready_s=first_ready,first_current_recovery_s=first_recovered,
        final_strike_quality=final,
        checks=dict(source1680=steps==1680,initial_pick_matches_saved_reset_observation=initial_pick_error<1e-7,
            original_raw_candidates_unchanged=all(candidate_matches),unique_accepted_max1=len(final['accepted_crossing_ids'])<=1))


def audit(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    paths=(out/'trace_comparison_v1.json',out/'trace_comparison_v1.md')
    if any(p.exists() for p in paths):raise FileExistsError('preserve previous comparison')
    inputs=Inputs()
    for name in ('audit_musical_quality_v1.py','fretting_quality.py','fretting_v1.py','geometry_v1.py','music_task.py','strike.py','strike_quality.py'):
        inputs.pin(Path(__file__).parent/name)
    left=analyze_left(SOURCE/'left_ppo_eval_v1',inputs)
    right=analyze_right(SOURCE/'right_ppo_eval_v1',inputs)
    changed=inputs.verify()
    if changed:raise RuntimeError('audit inputs changed: '+repr(changed))
    valid=all(left['checks'].values()) and all(right['checks'].values())
    report=dict(schema='guitar_learning.frozen_trace_quality_comparison.v1',created_utc=datetime.now(timezone.utc).isoformat(),
        evidence_checks_passed=valid,roles=dict(left=left,right=right),
        fretting_metadata=FRETTING_QUALITY_METADATA,strike_metadata=STRIKE_QUALITY_METADATA,
        input_sha256=inputs.files,changed_inputs=changed,
        scope='counterfactual measurement of frozen trajectories only; no dynamics, policy inference, model update or new native performance evidence',
        limitations=['Original native stage success and old results remain untouched.',
            'No counterfactual total reward or QualityLedger stage-success certificate computed.',
            'Initial LH contact not reconstructed; first unbracketed interval excluded, audible and post-note intervals fully observed.',
            'Contact feature/geometry labels are not acoustic mistakes or calibrated pressure; incidental other strings are diagnostic.'])
    with paths[0].open('x') as stream:json.dump(report,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    c=left['status_and_flag_sample_counts'];a=left['audible'];p=left['after_note'];s=right['final_strike_quality']
    lines=['# 저장 궤적의 구·신 음악 판정 비교', '',
        '**물리 시뮬레이션·정책 추론을 다시 실행하지 않았다.** 기존 actionable preparation의 왼손·오른손 PPO 평가 각1회, 각1,680개240Hz 표본을 새 분류기와 준비 게이트로 측정한 반사실 분석이다. 원본 실행의 성공·실패 기록을 고치거나 새로운 환경에서의 정책 성능으로 해석하지 않는다.', '',
        '자료·연속 시계·후보 보존 검사: **%s**, 입력 SHA 변경%d개.'%(valid,len(changed)), '',
        '| 왼손 지표 | 결과 |','|---|---:|',
        '| 전체 표본 | %d |'%left['samples'],
        '| 원 positive / 새 clean | %d / %d |'%(c.get('positive_target_candidate',0),c.get('clean_target_candidate',0)),
        '| correct / wrong / missing | %d / %d / %d |'%(c.get('correct',0),c.get('wrong',0),c.get('missing',0)),
        '| higher / assignment / incidental-other / uncertain 표본 | %d / %d / %d / %d |'%(c.get('higher_fret',0),c.get('wrong_assignment',0),c.get('incidental_other_string',0),c.get('uncertain',0)),
        '| audible 원 positive / clean 유지율 | %.6f / %.6f |'%(a['original_positive_fraction'],a['clean_fraction']),
        '| end+100ms 이후 clear 표본 / 전체 | %d / %d |'%(c.get('after_end_plus100ms_clear_samples',0),c.get('after_end_plus100ms_samples',0)),
        '| end+100ms 이후 최장 연속 clear | %.6fs |'%p['longest_contiguous_clear_s'],
        '| 마지막 목표현 clear | %s |'%p['final_target_string_clear'], '',
        'LH는 저장된 원 contact evidence와 같은 시점의 geometry만 사용했다. 원 TaskMeasurement를 다시 돌리지 않았고 초기 접촉을 만들어 넣지 않았다. audible 경계[%.6f,%.6f]초는 앞뒤 실제 표본으로 완전히 관측되며, 전체%.6f초의 유지 시간을 각각 적분했다. 노트 후 해제는 clean=False만으로 인정하지 않고 실제 목표현 접촉 ID가 비었는지 따로 확인했다.'%(a['interval_s'][0],a['interval_s'][1],a['duration_s']), '',
        '| 오른손 지표 | 결과 |','|---|---:|',
        '| 구 eligible event / 새 준비 필터 후 event | %d / %d |'%(right['original_crossing_count'],right['new_event_count']),
        '| 구 목표방향 통과 / 새 accepted 목표통과 | %d / %d |'%(right['original_matching_crossings'],right['new_accepted_matching_crossings']),
        '| 준비 전 / 추가 통과 | %d / %d |'%(s['unprepared_count'],s['extra_count']),
        '| 최초 ready / current recovery 관측시각 | %s / %s |'%(right['first_ready_s'],right['first_current_recovery_s']),
        '| 최종 current recovered / ever recovered | %s / %s |'%(s['recovered'],s['ever_recovered']), '',
        'RH는 실제 reset native step0의 body state와 당시 source SHA에 고정된 body-name 목록으로 geometry0을 구성하고, 저장 geometry1~1680을 순서대로 넣었다. 초기 접촉 정보는 필요하지 않다. geometry0의 피크와 저장된 첫 정책 관측의 차이는 최대%.3g m이며, 원 raw crossing candidate는 그대로 재현되었다. 준비 전·추가 통과는 기존 native 기하 후보를 지우지 않고 별도 이유로 분리했다.'%right['initialization']['reset_actor_pick_max_abs_error_m'], '',
        '이 비교는 어떤 기존 행동이 새 측정에서 걸리는지 확인한다. 새 보상을 받은 정책이 실제로 개선됐다는 증거가 아니며, 압력·진동·음향·전곡 뮤팅·일반화도 인증하지 않는다. feature/sample 수를 음악 오류 횟수로 바꾸어 부르지 않는다.', '',
        '[전체 분모·예시·이벤트·SHA](%s)'%paths[0]]
    with paths[1].open('x') as stream:stream.write('\n'.join(lines)+'\n')
    print(json.dumps(dict(output=str(paths[0]),checks_passed=valid,left_counts=dict(c),left_audible=a,
        right_counts=s['counts'],final_release_clear=p['final_target_string_clear'],final_recovered=s['recovered'])))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();audit(args.out)


if __name__=='__main__':main()
