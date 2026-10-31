"""평가 최초32환경과 env0 단일 궤적을 구분하는 stdlib 전용 분석기."""
import argparse
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path

TERMS = ('song_left_approach','song_left_contact','song_clean_hold','song_left_success',
    'song_wrong_press','song_performance_deficit','song_finger_standby','song_thumb_support','action_change')
FINGERS = ('index','middle','ring','pinky')


def number(value):
    if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):
        raise ValueError('유한한 수치가 필요함: '+repr(value))
    return float(value)


def mean(values):return sum(values)/len(values)


def p90(values):
    values = sorted(values);position = .9*(len(values)-1);lower = int(position)
    return values[lower]+(position-lower)*(values[min(lower+1,len(values)-1)]-values[lower])


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):result.update(chunk)
    return result.hexdigest()


def episodes(path):
    """공유 필드를 복원하고 파일 순서상 각 환경의 첫 episode만 반환한다."""
    metadata_path = path/'episode_metadata.json'
    metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else dict(fields=[])
    first = {}
    with (path/'episodes.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line);episode = copy.deepcopy(row['episode'])
            for field in metadata['fields']:
                current = episode
                for name in field['path'][:-1]:current = current.setdefault(name,{})
                key = field['path'][-1]
                if key in current and current[key] != field['value']:raise ValueError('공유 metadata 충돌')
                current[key] = copy.deepcopy(field['value'])
            env = episode['env_id']
            if type(env) is not int or not 0 <= env < 32:raise ValueError('최초32환경 env_id 범위 불일치')
            first.setdefault(env,episode)
    if set(first) != set(range(32)):raise ValueError('실패를 포함한 최초32환경이 모두 필요함')
    return [first[i] for i in range(32)]


def trace_metrics(path,episode,finger):
    rows=[];identity=None
    with gzip.open(path/'finger_control_trace.jsonl.gz','rt') as stream:
        for line in stream:
            row=json.loads(line)
            if row['env_id'] != 0:continue
            if identity is None:identity=row['episode_id']
            if row['episode_id'] == identity:rows.append(row)
    if not rows:raise ValueError('env0 최초 episode trace 관측 누락')
    expected=episode['finger_control_diagnostics']['episode_id']
    if identity != expected:raise ValueError('episode 집계와 env0 trace의 실제 episode ID 불일치')
    times=[number(row['episode_time_s']) for row in rows]
    duration=number(episode['task_time_s'])
    if times[0] > .02 or times[-1]+1/240.+1e-6 < duration or any(a>=b for a,b in zip(times,times[1:])):
        raise ValueError('env0 최초 episode trace 시간 범위/순서 누락')
    names=rows[0]['joint_names'];indices={name:names.index('LH:'+finger+suffix) for name,suffix in (('MCP_x','1_x'),('PIP','2'))}
    if any(row['joint_names']!=names for row in rows):raise ValueError('trace 관절 순서 변경')
    before=[row for row in rows if number(row['episode_time_s'])<3.]
    if not before:raise ValueError('준비 구간 trace 누락')
    result=dict(scope='env0 최초 완료/실패 episode 하나; 32환경 평균이나 reset각 아님',
        episode_id=identity,first_observation_time_s=times[0],last_observation_time_s=times[-1],
        angle_definition='native MCP_x/PIP radians를 degree로 변환; 기하 MCP 아님',
        extension_reference='첫 trace actual_rad; actual/requested 모두 같은 첫 관측 실제각 기준',joints={})
    for name,index in indices.items():
        baseline=number(rows[0]['actual_rad'][index])
        item=dict(first_actual_degrees=math.degrees(baseline),first_requested_degrees=math.degrees(number(rows[0]['requested_target_rad'][index])))
        for field,label in (('actual_rad','actual'),('requested_target_rad','requested')):
            values=[number(row[field][index]) for row in before]
            item[label+'_max_extension_degrees']=math.degrees(max(0.,baseline-min(values)))
        samples=[]
        for timestamp in (59/60.,61/60.):
            row=min(rows,key=lambda r:abs(r['episode_time_s']-timestamp))
            samples.append(row if abs(row['episode_time_s']-timestamp)<=1/480.+1e-6 else None)
        if all(samples):
            item['one_second_samples_s']=[row['episode_time_s'] for row in samples]
            for field,label in (('actual_rad','actual'),('requested_target_rad','requested')):
                delta=math.degrees(number(samples[1][field][index])-number(samples[0][field][index]))
                item[label+'_delta_degrees_at_1s']=delta
                item[label+'_additional_extension_degrees_at_1s']=max(0.,-delta)
        elif duration >= 61/60.:raise ValueError('1초 전후 trace 관측 누락')
        else:item['one_second_window_unavailable']='실제 조기 종료가1.0167초 이전'
        result['joints'][name]=item
    first={key:None for key in ('observation_exposed','preparation_valid','ready','descent_started')}
    for row in rows:
        natural=row['natural_preparation'];matches=[f for f in natural['fingers'] if f['finger']==FINGERS.index(finger)+1]
        if len(matches)!=1:raise ValueError('trace 목표 손가락 진단 누락')
        selected=matches[0]
        for key in ('observation_exposed','preparation_valid'):
            if key not in selected:raise ValueError('관측/준비 노출 관측 누락')
        for key in first:
            value=selected.get('descent_blend',0)>0 if key=='descent_started' else selected.get(key,False)
            if value and first[key] is None:first[key]=number(row['episode_time_s'])
    result['first_observed_times_s']=first
    result['joint_order']=['MCP_x','PIP']
    result['max_actual_initial_extension_deg']=[result['joints'][k]['actual_max_extension_degrees'] for k in result['joint_order']]
    result['max_requested_initial_extension_deg']=[result['joints'][k]['requested_max_extension_degrees'] for k in result['joint_order']]
    return result


def analyze_evaluation(path):
    path=Path(path).resolve();report=json.loads((path/'report.json').read_text())
    if (report.get('completed') is not True or report.get('lifecycle_verified') is not True or
        report.get('first_episode_per_env_per_batch') is not True or report.get('failed_episodes_in_denominator') is not True or
        report.get('episodes')!=32 or any(report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'))):
        raise ValueError('완료·수명주기·실패 포함 최초32 평가 계약 불일치')
    config=report['settings']['natural_press'];finger=config['finger'];slot=FINGERS.index(finger)
    rows=episodes(path);clean=[];wrong=[];missing=[];bad=[];early=[];longest=[];success=physical=wrist=0
    rewards={key:[] for key in TERMS};costs=[];ranges={};rms={};names=rows[0]['left_finger_motion']['joint_names']
    for row in rows:
        termination=row['termination'];physical+=int(termination['physical_failure']);wrist+=int(termination['wrist_failure'])
        if type(termination['physical_failure']) is not bool or type(termination['wrist_failure']) is not bool:raise ValueError('물리/손목 실패 flag 누락')
        success+=int(row['song']['stage_success'] and row['valid'] and not termination['physical_failure'] and not termination['wrist_failure'])
        ledger=row['left_note_ledger']['values']
        if row['song']['target_count']!=1 or any(len(ledger[k])!=1 for k in ('clean','wrong','missing')):
            raise ValueError('검증된 단일 목표 원장 필요')
        for key,values in (('clean',clean),('wrong',wrong),('missing',missing)):values.append(number(ledger[key][0]))
        natural=row['natural_preparation'];columns=natural['columns']
        if natural['condition']!=config['condition']:raise ValueError('평가/episode 준비 조건 불일치')
        for key,values in (('unready_slow_wrist_s',bad),('early_candidate_s',early)):
            values.append(number(natural['per_finger_seconds'][slot][columns.index(key)]))
        longest.append(number(natural['longest_continuous_ready_before_descent_s'][slot]))
        for key in TERMS:rewards[key].append(number(row['reward_components'][key]))
        if abs(sum(rewards[k][-1] for k in TERMS)-number(row['reward']))>1e-4:raise ValueError('9항 reward 원장 대조 실패')
        costs.append(number(row['cost']))
        motion=row['left_finger_motion']
        if motion['joint_names']!=names:raise ValueError('episode 관절 순서 변경')
        for field in ('actual_range_rad','target_range_rad'):
            values=motion['values'][field]
            if len(values)!=len(names):raise ValueError('관절 범위 관측 누락')
            for name,value in zip(names,values):ranges.setdefault(field+'/'+name,[]).append(math.degrees(number(value)))
        diagnostic=row['finger_control_diagnostics']
        if diagnostic['joint_names']!=names:raise ValueError('240Hz 진단/60Hz 관절 순서 불일치')
        for field in ('requested_tracking_error_rad_rms','applied_tracking_error_rad_rms','rate_limit_gap_rad_rms','velocity_rad_s_rms'):
            values=diagnostic['values'][field]
            if len(values)!=len(names):raise ValueError('관절 RMS 관측 누락')
            for name,value in zip(names,values):rms.setdefault(field+'/'+name,[]).append(number(value))
    result=dict(schema='guitar_learning.natural_press_evaluation_analysis.v1',path=str(path),condition=config['condition'],finger=finger,
        episodes=32,success_count=success,physical_failure_count=physical,wrist_failure_count=wrist,
        any_failure_count=sum(r['termination']['physical_failure'] or r['termination']['wrist_failure'] for r in rows),
        mean_clean_s=mean(clean),min_clean_s=min(clean),mean_wrong_s=mean(wrong),mean_missing_s=mean(missing),
        ready_02_count=sum(value+1e-7>=.2 for value in longest),mean_longest_ready_s=mean(longest),
        mean_unready_slow_wrist_s=mean(bad),p90_unready_slow_wrist_s=p90(bad),mean_early_candidate_s=mean(early),p90_early_candidate_s=p90(early),
        reward_term_means={k:mean(v) for k,v in rewards.items()},mean_reward=sum(mean(v) for v in rewards.values()),mean_cost=mean(costs),
        joint_ranges_degrees={k:dict(mean=mean(v),p90=p90(v),maximum=max(v)) for k,v in ranges.items()},
        joint_ranges_scope='32개 episode의60Hz actual/적용 target 범위; requested target 범위가 아님',
        control_rms={k:dict(mean=mean(v),maximum=max(v)) for k,v in rms.items()},
        control_rms_scope='240Hz에서 계산된 각 episode RMS의32개 평균/최대; 순간오차 최대가 아님; velocity 항은 rad/s, 나머지는 rad',
        pressure_performance_sufficient=success==32 and min(clean)>=2.4 and physical==0 and wrist==0,
        interpretation='충족 여부만 기록; 기준 조건과 대조 없이 개선으로 판정하지 않음',
        env0_trace=trace_metrics(path,rows[0],finger),
        input_sha256={str(p):sha(p) for p in (path/'report.json',path/'episodes.jsonl',path/'finger_control_trace.jsonl.gz')})
    if (path/'episode_metadata.json').exists():result['input_sha256'][str(path/'episode_metadata.json')]=sha(path/'episode_metadata.json')
    json.dumps(result,allow_nan=False)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('evaluation',type=Path);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();result=analyze_evaluation(args.evaluation)
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
