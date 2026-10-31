"""실패를 포함한 최초32회 ABAB 평가와 env0 대표 전환 궤적을 분리해 읽는다."""
import argparse
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path

ONSETS = (3., 5., 7., 9.)
ENDS = (4.5, 6.5, 8.5, 10.5)


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('유한 수치가 필요함: '+repr(value))
    return float(value)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''): result.update(chunk)
    return result.hexdigest()


def episodes(path):
    """공유 원장을 복원하며 파일 순서상 각 환경의 첫 episode만 선택한다."""
    path = Path(path)
    metadata = json.loads((path/'episode_metadata.json').read_text())
    first = {}
    for line in (path/'episodes.jsonl').read_text().splitlines():
        row = copy.deepcopy(json.loads(line)['episode'])
        for field in metadata['fields']:
            current = row
            for name in field['path'][:-1]: current = current.setdefault(name, {})
            key = field['path'][-1]
            if key in current and current[key] != field['value']: raise ValueError('공유 원장 충돌')
            current[key] = copy.deepcopy(field['value'])
        env = row['env_id']
        if type(env) is not int or not 0 <= env < 32: raise ValueError('평가 env_id 범위 오류')
        first.setdefault(env, row)
    if set(first) != set(range(32)): raise ValueError('실패 포함 최초32환경 필요')
    return [first[i] for i in range(32)]


def trace_metrics(path, episode, schedule):
    """대표 env0만 분석한다. 조기 종료 뒤 시각/거리는 null이며 성공0이다."""
    rows = []
    with gzip.open(Path(path)/'finger_control_trace.jsonl.gz', 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            if row['env_id'] != 0: continue
            if not rows or row['episode_id'] == rows[0]['episode_id']: rows.append(row)
    if not rows: raise ValueError('env0 대표 trace 누락')
    if rows[0]['episode_id'] != episode['finger_control_diagnostics']['episode_id']:
        raise ValueError('episode/trace ID 불일치')
    times = [finite(row['episode_time_s']) for row in rows]
    duration = finite(episode['task_time_s'])
    if times[0] > .02 or times[-1]+1/240.+1e-5 < duration or any(a >= b for a,b in zip(times,times[1:])):
        raise ValueError('최초 episode 전체 trace 누락 또는 순서 오류')
    for row in rows:
        extra=row.get('natural_preparation',{}).get('transition')
        if not extra or extra.get('schema')!='guitar_learning.virtual_transition.v1':
            raise ValueError('필수 transition trace 누락/schema 오류')
        goals=extra.get('goals',[])
        if len(goals)!=4: raise ValueError('필수4목표 trace 누락')
        for goal,expected in zip(goals,schedule):
            if any(goal.get(k)!=expected[k] for k in ('target_id','onset_s','end_s','fret','string_index')):
                raise ValueError('trace 목표 순서/시간표 오류')
            if type(goal.get('press_candidate')) is not bool: raise ValueError('candidate flag 오류')
            finite(goal['pad_distance_m']); finite(goal['pad_height_m'])
        for key,length in (('arm_actual_rad',12),('arm_requested_rad',12),('arm_applied_rad',12),('wrist_error_m',3)):
            values=extra.get(key)
            if not isinstance(values,list) or len(values)!=length: raise ValueError('필수 trace vector 오류: '+key)
            for value in values: finite(value)
    transitions = []
    for previous, current in zip(range(3), range(1,4)):
        start, onset = ENDS[previous], ONSETS[current]
        segment = [r for r in rows if ONSETS[previous] <= r['episode_time_s'] < ENDS[current]]
        item = dict(previous_note=previous+1, next_note=current+1,
                    interval_s=[start, onset], observed=duration >= start,
                    first_target_contact_s=None, first_target_contact_delay_s=None,
                    previous_cell_release_s=None, minimum_target_pad_distance_m=None,
                    arm_actual_displacement_rad=None, wrist_error_at_onset_m=None,
                    previous_audible_candidate_s=None, next_candidate_before_previous_end_s=None,
                    finger_requested_change_rad=None, finger_applied_change_rad=None, finger_actual_change_rad=None)
        observations = []; arm=[]; old_hold=early=0.; geometry_count=0; wrist_samples=[]; previous_was_contact=False
        for row in segment:
            extra = row.get('natural_preparation', {}).get('transition', row.get('transition'))
            if not extra: continue
            goals = extra.get('goals', [])
            if len(goals) != 4: raise ValueError('4목표 trace 계약 오류')
            goal, old = goals[current], goals[previous]
            t = finite(row['episode_time_s'])
            if goal.get('press_candidate') is True and item['first_target_contact_s'] is None:
                item['first_target_contact_s'] = t
                item['first_target_contact_delay_s'] = t-onset
            previous_was_contact = previous_was_contact or old.get('press_candidate') is True
            if t >= start and previous_was_contact and old.get('press_candidate') is False and item['previous_cell_release_s'] is None:
                item['previous_cell_release_s'] = t
            geometry_count += 1
            if t < start:
                old_hold += int(old.get('press_candidate') is True)/240.
                early += int(goal.get('press_candidate') is True)/240.
            if start <= t <= onset and extra.get('arm_actual_rad') is not None:
                arm.append([finite(v) for v in extra['arm_actual_rad']])
            if extra.get('wrist_error_m') is not None:
                wrist_samples.append((abs(t-onset),[finite(v) for v in extra['wrist_error_m']]))
            distance = goal.get('pad_distance_m')
            if distance is not None: observations.append(finite(distance))
        item['minimum_target_pad_distance_m'] = min(observations) if observations else None
        item['geometry_trace_available'] = bool(observations)
        item['previous_cell_contact_observed_before_release'] = previous_was_contact if geometry_count else None
        if geometry_count:
            item['previous_audible_candidate_s']=old_hold
            item['next_candidate_before_previous_end_s']=early
        if len(arm)>=2 and all(len(v)==12 for v in arm):
            item['arm_actual_displacement_rad']=[b-a for a,b in zip(arm[0],arm[-1])]
        if wrist_samples:
            nearest=min(wrist_samples,key=lambda pair:pair[0])
            if nearest[0] <= 1/240.+1e-6: item['wrist_error_at_onset_m']=nearest[1]
        gap=[r for r in segment if start <= r['episode_time_s'] <= onset]
        if len(gap)>=2:
            for field,label in (('requested_target_rad','requested'),('applied_target_rad','applied'),('actual_rad','actual')):
                if all(field in r for r in (gap[0],gap[-1])):
                    item['finger_'+label+'_change_rad']=[finite(b)-finite(a) for a,b in zip(gap[0][field],gap[-1][field])]
        item['candidate_interpretation']='이전 음 구간의 다음 셀 후보는 관측이며 자동 오답이 아니다. 실제 audible wrong은 음 원장을 사용한다.'
        # A1/A3와 B2/B4는 같은 물리 셀이다. 이벤트별 candidate를 더하지 않는다.
        transitions.append(item)
    return dict(scope='env0 최초 episode 한 궤적; 32환경 평균이 아님',
                episode_id=rows[0]['episode_id'], observed_end_s=times[-1], transitions=transitions,
                missing_observation='미관측 시각·거리 null; 동일 A/B 셀 반복 후보는 중복 합산하지 않음')


def analyze_evaluation(path):
    path = Path(path).resolve()
    report = json.loads((path/'report.json').read_text())
    if (report.get('completed') is not True or report.get('lifecycle_verified') is not True or
        report.get('first_episode_per_env_per_batch') is not True or
        report.get('failed_episodes_in_denominator') is not True or report.get('episodes') != 32 or
        any(report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'))):
        raise ValueError('완료/최초32/실패 포함 평가 계약 불일치')
    schedule=report['settings']['transition']['schedule']
    if len(schedule)!=4 or any((t['onset_s'],t['end_s'],t['fret'],t['finger'],t['string_index']) != (ONSETS[i],ENDS[i],6 if i%2==0 else 7,2,2) for i,t in enumerate(schedule)):
        raise ValueError('승인된 ABAB 시간표 불일치')
    target_ids=[t['target_id'] for t in schedule]
    rows = episodes(path)
    notes = [dict(note=i+1, fret=(6 if i%2 == 0 else 7), onset_s=ONSETS[i], end_s=ENDS[i],
                  success_count=0, observed_onset_count=0, first_contact_s=[], first_achievement_s=[], mean_clean_s=0., mean_wrong_s=0., mean_missing_s=0.) for i in range(4)]
    full = physical = wrist = 0
    rewards = {}
    transitions = [dict(previous_note=i+1, next_note=i+2, both_notes_success_count=0,
                        next_onset_observed_count=0) for i in range(3)]
    for row in rows:
        ledger = row['left_note_ledger']; values = ledger['values']
        if ledger['target_ids'] != target_ids or any(len(values[k]) != 4 for k in ('left','clean','wrong','missing')):
            raise ValueError('4음 원장 필요')
        if row['finger_skill']['scope'] != 'full_song': raise ValueError('구간 평가로 대체할 수 없음')
        termination = row['termination']
        for key in ('physical_failure','wrist_failure'):
            if type(termination[key]) is not bool: raise ValueError('실패 flag 누락')
        physical += termination['physical_failure']; wrist += termination['wrist_failure']
        duration = finite(row['task_time_s']); successes=[]
        observer=row['transition_diagnostics']
        if observer['target_ids']!=target_ids or any(len(observer[k])!=4 for k in ('first_contact_s','first_achievement_s')):
            raise ValueError('최초접촉/달성4음 observer 계약 오류')
        for i, item in enumerate(notes):
            observed = duration >= ONSETS[i]
            item['observed_onset_count'] += observed
            success = observed and bool(values['left'][i]); successes.append(success)
            item['success_count'] += success
            for key in ('first_contact_s','first_achievement_s'):
                value=observer[key][i]
                if value is not None:
                    value=finite(value)
                    if not ONSETS[i]<=value<=min(ENDS[i]+1/60.,duration+1/60.):
                        raise ValueError('최초접촉/달성 관측 시각 범위 오류')
                item[key].append(value)
            if success and observer['first_achievement_s'][i] is None:
                raise ValueError('달성 원장과 최초달성 observer 불일치')
            for source in ('clean','wrong','missing'):
                value = finite(values[source][i])
                if value < 0: raise ValueError('음 시간 음수')
                item['mean_'+source+'_s'] += value/32.
        full += row['valid'] is True and all(successes) and not termination['physical_failure'] and not termination['wrist_failure']
        for i, item in enumerate(transitions):
            item['both_notes_success_count'] += successes[i] and successes[i+1]
            item['next_onset_observed_count'] += duration >= ONSETS[i+1]
        for key, value in row['reward_components'].items(): rewards[key] = rewards.get(key,0.)+finite(value)/32.
        if abs(sum(finite(v) for v in row['reward_components'].values())-finite(row['reward'])) > 1e-4:
            raise ValueError('보상 원장 합계 불일치')
    for item in notes:
        for field,label in (('first_contact_s','contact'),('first_achievement_s','achievement')):
            observed=[v for v in item[field] if v is not None]
            item[label+'_observed_count']=len(observed)
            item['mean_'+label+'_latency_s_observed_only']=sum(v-item['onset_s'] for v in observed)/len(observed) if observed else None
        item['timing_scope']='배열 순서는env0..31; 미관측null. latency평균은관측된횟수만이며 성공분모32와다름.'
    evidence = [path/name for name in ('report.json','episodes.jsonl','episode_metadata.json','finger_control_trace.jsonl.gz')]
    result = dict(schema='guitar_learning.virtual_transition_analysis.v1', path=str(path),
                  episode_denominator=32, note_denominator=128, transition_denominator=96,
                  full_sequence_success_count=full, note_success_count=sum(n['success_count'] for n in notes),
                  physical_failure_count=physical, wrist_failure_count=wrist, notes=notes, transitions=transitions,
                  reward_term_means=rewards, env0_trace=trace_metrics(path,rows[0],schedule),
                  interpretation='목표 시각에 미도달한 음도 분모에 포함한다. 누락 원장은 관측시간이며 미관측 잔여시간을 임의 추가하지 않는다.',
                  input_sha256={str(p):sha(p) for p in evidence})
    json.dumps(result, allow_nan=False)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evaluation', type=Path); parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(); result=analyze_evaluation(args.evaluation)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
