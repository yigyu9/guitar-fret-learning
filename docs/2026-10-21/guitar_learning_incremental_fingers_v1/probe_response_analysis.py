"""Independent CPU reading of saved21-axis/four-command native probe traces.

No simulator, policy, force changes, rendering or new physical steps. Signs are
native generalized coordinates, not anatomical flexion/extension labels.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
ROOT = Path(__file__).resolve().parents[3]
PHASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from guitar_learning.training import json_io

AMPLITUDES = (.1, -.1, .2, -.2)
PUSH, HOLD, TOTAL = 30, 10, 70
MOVE_EPS = 1e-4
DIRECTION_EPS = 1e-6


def require(ok, message):
    if not ok: raise ValueError(message)


def trace_metrics(a, c, joint, amplitude):
    names, order = c['joint_names'], c['action_order']
    joints = c['action_codec']['incremental_joint_names']
    native = [names.index(n) for n in joints]
    actions = [order.index(n) for n in joints]
    j, channel = joints.index(joint), order.index(joint)
    frames = len(a['clock'])
    shapes = dict(q=(frames,105),qd=(frames,105),target=(frames,105),action=(frames,39),
                  body_state=(frames,106,13),clock=(frames,),global_physics_step=(frames,))
    require(set(a) == set(shapes) and 1 <= frames <= TOTAL+1, 'Unexpected trace fields/count')
    for key,shape in shapes.items():
        require(a[key].shape == shape and bool(np.isfinite(a[key]).all()), 'Invalid trace '+key)
    require(np.array_equal(a['clock'],np.arange(frames)*4) and
            np.array_equal(np.diff(a['global_physics_step']),np.full(frames-1,4)), 'Actual clock discontinuity')
    require(bool((a['action'][0] == 0).all()), 'Prepared t0 action sentinel mismatch')
    require(float(np.max(np.abs(np.linalg.norm(a['body_state'][...,3:7],axis=-1)-1))) < 1e-3, 'Nonunit body quaternion')
    lo,hi = np.asarray(c['action_lower_rad'])[actions],np.asarray(c['action_upper_rad'])[actions]
    targets = a['target'][:,native].astype(np.float64)
    require(np.allclose(targets[0],np.asarray(c['reference105_rad'])[native],rtol=0,atol=3e-6), 'Prepared target mismatch')
    expected = targets[0].copy();maximum_error=0.
    for k in range(1,frames):
        t=k-1
        command=amplitude if t<PUSH else 0. if t<PUSH+HOLD else -amplitude
        prescribed=np.zeros(39);prescribed[channel]=command
        require(np.allclose(a['action'][k],prescribed,rtol=0,atol=1e-7), 'Prescribed command mismatch')
        expected=np.clip(expected+prescribed[actions]*4/60.,lo,hi)
        maximum_error=max(maximum_error,float(np.max(np.abs(expected-targets[k]))))
    require(maximum_error<=4e-6, 'Independent target recurrence mismatch')
    q=a['q'][:,native[j]].astype(np.float64);target=targets[:,j]
    push=min(PUSH,frames-1);hold=min(PUSH+HOLD,frames-1)
    sign=1 if amplitude>0 else -1
    bound=float(hi[j] if sign>0 else lo[j])
    saturated=int(np.sum(np.abs(target[1:push+1]-bound)<=2e-6))
    reverse=frames>HOLD+PUSH+1
    qreverse=np.diff(q[PUSH+HOLD:]) if reverse else np.empty(0)
    reverse_positions=np.flatnonzero(-sign*qreverse>DIRECTION_EPS)
    first_reverse=int(reverse_positions[0]+1) if len(reverse_positions) else None
    error=q[1:]-target[1:]
    return dict(control_ticks=frames-1,complete_schedule=frames==TOTAL+1,
        target_recurrence_max_error_rad=maximum_error,
        target_push_delta_rad=float(target[push]-target[0]),
        target_hold_delta_rad=float(target[hold]-target[push]),
        target_reverse_delta_rad=float(target[-1]-target[hold]) if reverse else None,
        target_first_reverse_delta_rad=float(target[PUSH+HOLD+1]-target[PUSH+HOLD]) if reverse else None,
        native_lower_rad=float(lo[j]),native_upper_rad=float(hi[j]),push_saturated_endpoints=saturated,
        no_windup_observed=bool(saturated>=2 and reverse and -sign*(target[PUSH+HOLD+1]-target[PUSH+HOLD])>1e-7),
        actual_push_delta_rad=float(q[push]-q[0]),actual_hold_delta_rad=float(q[hold]-q[push]),
        actual_reverse_delta_rad=float(q[-1]-q[hold]) if reverse else None,
        actual_first_reverse_delta_rad=float(q[PUSH+HOLD+1]-q[PUSH+HOLD]) if reverse else None,
        first_detected_reverse_endpoint=first_reverse,
        first_detected_reverse_latency_s=first_reverse/60. if first_reverse is not None else None,
        actual_min_rad=float(q.min()),actual_max_rad=float(q.max()),actual_range_rad=float(np.ptp(q)),
        actual_motion_observed=bool(np.ptp(q)>MOVE_EPS),
        endpoint_tracking_rms_rad=float(np.sqrt(np.mean(error*error))) if len(error) else None,
        endpoint_tracking_max_abs_rad=float(np.max(np.abs(error))) if len(error) else None,
        actual_hold_max_abs_change_rad=float(np.max(np.abs(q[push:hold+1]-q[push]))),
        uncommanded_joint_max_range_rad=float(np.max(np.ptp(a['q'][:,[i for k,i in enumerate(native) if k!=j]],axis=0))))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe',type=Path,default=PHASE/'probe_n4_retry02')
    args=parser.parse_args();folder=args.probe.resolve();inputs={}
    def read(path):
        inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())
    report=read(folder/'report.json');contract=read(folder/'control_contract.json');metadata=read(folder/'capture_metadata.json')
    require(report['completed'] is True, 'Producer did not complete; preserve failed evidence separately')
    codec=contract['action_codec'];joints=codec['incremental_joint_names']
    require(contract['schema']=='guitar_learning.gpu_finite_control.v3' and codec['schema']=='guitar_learning.gpu_left_incremental_fingers.v1' and
            codec['velocity_scale_rad_s']==4. and codec['control_hz']==60 and contract['physics_hz']==240, 'Unexpected control contract')
    require(len(joints)==len(set(joints))==21 and metadata['push_ticks']==PUSH and metadata['hold_ticks']==HOLD and metadata['reverse_ticks']==30, 'Unexpected predeclared probe')
    require(len(report['trials'])==84 and {(t['joint'],t['amplitude']) for t in report['trials']}=={(j,a) for j in joints for a in AMPLITUDES}, 'Predeclared21x4 coverage mismatch')
    scene=report['gpu_scene']
    require(scene['closed'] and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and scene['environment_count']==4 and
            scene['physics_steps']==report['control_ticks']*4, 'Actual closed nativeGPU audit mismatch')
    rows=[];roundtrip_fields=0
    for trial in report['trials']:
        path=folder/trial['path'];digest=hashlib.sha256(path.read_bytes()).hexdigest()
        require(digest==trial['sha256'], 'Raw NPZ SHA mismatch')
        inputs[str(path)]=digest
        with np.load(path,allow_pickle=False) as saved:a={k:saved[k] for k in saved.files}
        own=trace_metrics(a,contract,trial['joint'],trial['amplitude'])
        producer=trial['audit']
        for field,key in (('actual_push_delta_rad','actual_push_delta_rad'),('actual_hold_delta_rad','actual_hold_delta_rad'),
                ('actual_reverse_delta_rad','actual_reverse_delta_rad'),('actual_range_rad','actual_range_rad'),
                ('endpoint_tracking_rms_rad','endpoint_tracking_rms_rad'),('target_recurrence_max_error_rad','max_target_recurrence_error_rad')):
            require(math.isclose(own[field],producer[key],rel_tol=2e-6,abs_tol=1e-8), 'Raw/producer metric mismatch: '+field)
        require(own['no_windup_observed']==producer['no_windup_observed'], 'No-windup coverage mismatch')
        # Exercise built-in JSON on every raw array and reconstruct its original dtype/shape.
        for key,value in a.items():
            restored=np.asarray(json.loads(json.dumps(value.tolist(),allow_nan=False)),dtype=value.dtype)
            require(restored.shape==value.shape and restored.tobytes()==value.tobytes(), 'Built-in JSON raw-array roundtrip failed: '+key)
            roundtrip_fields+=1
        rows.append(dict(joint=trial['joint'],amplitude=trial['amplitude'],env_id=trial['env_id'],
            source=trial['path'],terminal=trial['terminal'],**own))
    counts=collections.Counter()
    for row in rows:
        sign=1 if row['amplitude']>0 else -1
        moving=abs(row['target_push_delta_rad'])>2e-6
        counts['push_target_moving' if moving else 'push_target_held_at_limit']+=1
        if moving:counts['push_actual_along' if sign*row['actual_push_delta_rad']>MOVE_EPS else 'push_actual_other']+=1
        counts['reverse_actual_along' if -sign*row['actual_reverse_delta_rad']>MOVE_EPS else 'reverse_actual_other']+=1
        counts['first_reverse_actual_along' if -sign*row['actual_first_reverse_delta_rad']>DIRECTION_EPS else 'first_reverse_actual_old_direction_or_tiny']+=1
        if sign*row['actual_first_reverse_delta_rad']>DIRECTION_EPS:counts['first_reverse_actual_old_direction']+=1
        elif abs(row['actual_first_reverse_delta_rad'])<=DIRECTION_EPS:counts['first_reverse_actual_tiny']+=1
    for field in ('no_windup_observed','actual_motion_observed','complete_schedule','terminal'):counts[field]=sum(bool(r[field]) for r in rows)
    require(counts['terminal']==report['physical_terminal_rows'] and counts['no_windup_observed']==report['no_windup_observed_trials'] and
            counts['actual_motion_observed']==report['actual_motion_observed_trials'], 'Aggregate producer/raw disagreement')
    fingers=[]
    for finger in ('thumb','index','middle','ring','pinky'):
        selected=[r for r in rows if r['joint'].startswith('LH:'+finger)]
        fingers.append(dict(finger=finger,trials=len(selected),tested_axes=len({r['joint'] for r in selected}),
            actual_range_max_rad=max(r['actual_range_rad'] for r in selected),
            actual_range_mean_rad=float(np.mean([r['actual_range_rad'] for r in selected])),
            tracking_rms_mean_rad=float(np.mean([r['endpoint_tracking_rms_rad'] for r in selected])),
            tracking_rms_max_rad=max(r['endpoint_tracking_rms_rad'] for r in selected),
            no_windup_observed_trials=sum(r['no_windup_observed'] for r in selected)))
    history=[]
    for name in ('probe_n4','probe_n4_retry01'):
        old=PHASE/name;entry=dict(attempt=name,counted_in_84=False,raw_traces=len(list(old.glob('trial_*.npz'))))
        for filename in ('report.json','python_exception.json','gpu_scene_final.json','lifecycle.json'):
            path=old/filename
            if not path.exists():continue
            inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
            try:data=json.loads(path.read_text())
            except json.JSONDecodeError as error:
                entry[filename]=dict(valid_json=False,error=str(error));continue
            entry[filename]=dict(valid_json=True,**{k:data[k] for k in ('completed','passed','control_ticks','stage','type','message','closed','physics_steps') if k in data})
        entry['saved_trace_cpu_audits']=[]
        if entry['raw_traces']:
            old_contract=read(old/'control_contract.json')
            for path in sorted(old.glob('trial_*.npz')):
                inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
                with np.load(path,allow_pickle=False) as saved:arrays={k:saved[k] for k in saved.files}
                nonzero=np.flatnonzero(arrays['action'][1])
                require(len(nonzero)==1, 'Failed-attempt trace has ambiguous command')
                channel=int(nonzero[0]);actual=float(arrays['action'][1,channel])
                amplitude=min(AMPLITUDES,key=lambda value:abs(value-actual))
                require(abs(amplitude-actual)<1e-7,'Failed-attempt amplitude mismatch')
                joint=old_contract['action_order'][channel]
                entry['saved_trace_cpu_audits'].append(dict(path=path.name,joint=joint,amplitude=amplitude,
                    **trace_metrics(arrays,old_contract,joint,amplitude)))
        history.append(entry)
    result=dict(schema='guitar_learning.incremental_finger_probe_response_analysis.v1',completed=True,
        probe_folder=str(folder),producer_completed=report['completed'],producer_passed=report['passed'],
        predeclared_trials=84,observed_trials=len(rows),actual_control_ticks=report['control_ticks'],actual_physics_steps=scene['physics_steps'],
        counts=dict(counts),finger_summaries=fingers,trials=rows,previous_attempts=history,
        actual_hold_drift_max_rad=max(r['actual_hold_max_abs_change_rad'] for r in rows),
        actual_hold_drift_mean_rad=float(np.mean([r['actual_hold_max_abs_change_rad'] for r in rows])),
        builtin_json_raw_array_fields_roundtripped=roundtrip_fields,
        direction_threshold_rad=MOVE_EPS,first_reverse_direction_threshold_rad=DIRECTION_EPS,
        first_detected_reverse_latency_range_s=[min(r['first_detected_reverse_latency_s'] for r in rows if r['first_detected_reverse_latency_s'] is not None),
            max(r['first_detected_reverse_latency_s'] for r in rows if r['first_detected_reverse_latency_s'] is not None)],
        scope='60Hz actual q/command target endpoints; raw clock increments4 actual240Hz steps. Not240Hz extrema. Native coordinate sign only.',
        limitations=['No-windup is observed only when push has>=2 saturated endpoints and first reverse target moves inward; uncovered native limits remain unverified.',
            'Action0 holds the command target, not physical q. Existing gains/inertia/contact can allow drift while tracking; command reversal does not imply immediate physical reversal.',
            '84 predeclared joint-command cases in one four-env probe are not independent policy/generalization trials.',
            'No PPO, pressure, target string contact, acoustic or song-learning success is established.'],inputs_sha256=inputs)
    # Summary contains native Python values; this also guards the prior NumPy-int JSON tool failure.
    require(json.loads(json.dumps(result,allow_nan=False))==result, 'Built-in JSON summary roundtrip failed')
    for path,digest in inputs.items():require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest, 'Analysis input changed')
    out=PHASE/'probe_response_analysis.json';out.write_text(json_io.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=['# 손가락 누적 제어 실측 응답 분석','',
        f'완료된 `probe_n4_retry02`의21축×4명령, **84개 원본 NPZ**를 독립 CPU 수식으로 다시 검산했다. 명령 반복식·정지·반전·한계 clamp가 기록과 일치하고, 물리 종료는{counts["terminal"]}개다. 목표 움직임과 실제 관절 움직임을 분리한다.','',
        '## 명령과 실제 움직임','',
        f'총1470 control tick·5880 native physics step 후 실제 GPU 장면이 정상 종료됐다. 각 시험은 전진30tick(0.5초), 행동0의 목표 유지10tick(0.167초), 반전30tick(0.5초)이며 매 시험 준비 자세로 reset한다. 각 NPZ는 준비 t0+70 endpoint의71프레임이다. 모든21축 목표는 독립식 `clip(이전 목표+행동×4/60,native하한,상한)`과4e−6rad 이내로 일치했다. 다른20축의 명령 목표도 같은 식으로 함께 검사했다.','',
        f'목표가 전진한{counts["push_target_moving"]}/84개에서 실제 q의 전진 순변위 방향도 모두 명령과 일치했다. 반전30tick의 실제 순변위는{counts["reverse_actual_along"]}/84개 모두 새 방향이다. 전체 실제 범위가1e−4rad보다 큰 시험은{counts["actual_motion_observed"]}/84개다. 이 마지막 수에는 전진이 clamp된 뒤 반전에서 움직인 시험도 포함된다.','',
        '전진 목표가0인4개는 `LH:thumb1_x`, `LH:ring3` 각각−0.1/−0.2 명령이다. 이들은 이미 native 하한에 있고 더 바깥으로 지시했으므로 목표가 유지되는 것이 정상이다. 실제 전진 순변위도 약1.7e−7~2.1e−6rad에 그쳤고 반전에서는 움직였다. 이를 손가락 전체가 움직이지 않는 결함으로 세지 않는다.','',
        f'반전 첫60Hz endpoint에서 실제 q가 새 방향으로 움직인 것은{counts["first_reverse_actual_along"]}/84개다. 나머지{counts["first_reverse_actual_old_direction_or_tiny"]}개는 목표가 이미 바뀌어도 잠시 기존 방향으로 움직였다. 실제 반전 검출은 반전 시작 후 {result["first_detected_reverse_latency_range_s"][0]:.3f}~{result["first_detected_reverse_latency_range_s"][1]:.3f}초의 endpoint에서 나타났다(관절 증분1e−6rad 문턱). 이는60Hz 검출 시각이며 연속 물리의 정확한 반전 시각이나 원인 분해가 아니다. **행동0은 목표 유지, 반전은 다음 명령 목표의 반전이며 실제 자세의 즉시 정지·반전이 아니다.**','',
        f'행동0의10tick에서 목표 변화는84개 모두0이었다. 그러나 실제 q는 목표를 추종하며 더 움직였고, 각 시험의 hold 시작점 대비 최대 이동량 평균은{result["actual_hold_drift_mean_rad"]:.6f}rad({math.degrees(result["actual_hold_drift_mean_rad"]):.3f}°), 전체 최대는{result["actual_hold_drift_max_rad"]:.6f}rad({math.degrees(result["actual_hold_drift_max_rad"]):.3f}°)였다. 따라서 이 제어를 실제 자세의 즉각 정지/고정으로 설명하면 안 된다.','',
        '## 손가락별 범위·추종','',
        '| 손가락 | 축/시험 수 | 실제 범위 최대(rad/도) | 시험별 RMS 평균(rad) | 시험 RMS 최대(rad) | no-windup 관측 |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for f in fingers:
        lines.append(f'| {f["finger"]} | {f["tested_axes"]}/{f["trials"]} | {f["actual_range_max_rad"]:.6f}/{math.degrees(f["actual_range_max_rad"]):.3f}° | {f["tracking_rms_mean_rad"]:.6f} | {f["tracking_rms_max_rad"]:.6f} | {f["no_windup_observed_trials"]} |')
    worst=max(rows,key=lambda r:r['endpoint_tracking_rms_rad'])
    lines += ['',f'범위는 t0 포함71개 실제 q의 max−min이고, 추종 RMS는 t0를 제외한70개 `실제q−명령목표` 오차다. RMS가 가장 큰 시험은 `{worst["joint"]}`/행동{worst["amplitude"]:+.1f}의{worst["endpoint_tracking_rms_rad"]:.6f}rad다. native K/D·힘·중력·안전 기준을 변경한 결과가 아니며, 이 오차만으로 특정 gain 변경을 정당화하지 않는다.','',
        f'no-windup을 실제 관측한 시험은{counts["no_windup_observed"]}/84개다. 같은 한계에서2개 이상 전진 endpoint가 포화되고 첫 반전 목표가 즉시 안쪽으로 이동했을 때만 관측으로 센다. 나머지{84-counts["no_windup_observed"]}개는 같은 native 한계 포화 상황을 충분히 만들지 않아 **미검증**이며 성공으로 채우지 않는다. 실제 q의 즉시 반전과 다른 명령 상태의 검사다.','',
        '## 이전 실패와 데이터 범위','',
        '`probe_n4`는 Ninja 의존성 문제로 GPU 생성 전0tick에서 실패했다. `probe_n4_retry01`은 첫70tick·4NPZ를 남기고 NumPy int64의 도구 JSON 직렬화 오류로 중단됐으며 report는 불완전 JSON이다. 보존된 native 최종 감사는 closed=true/280physics step이고 남은4NPZ의 시계·목표 반복식·실제 q도 별도로 CPU 재검산했다. 이를 완료된84시험으로 세지 않는다. 두 실패는 실제 물리 종료·native SIGFPE와 구분해 원본 그대로 보존했다.','',
        f'현재84NPZ의 모든 배열, 총{roundtrip_fields}개 배열을 표준 builtin JSON으로 왕복하고 원래 dtype/shape/바이트로 복원해 일치를 확인했다. 보고서 원래 수치와 독립 수치·집계도 대조했고 모든 사용 파일 SHA가 분석 전후 같았다. 새 분석 결과 역시 builtin JSON 왕복을 통과했다.','',
        '좌표 부호는 native 일반화좌표이며 해부학적 굽힘/폄과 동일시하지 않는다. 이 표는60Hz endpoint이고240Hz 최대각·속도는 아니다. 4환경의84명령은 단일 제어 검증이며 학습 정책, 현 압력·음향·곡 성공·독립 seed 일반화의 증거가 아니다. 실제 영상의 시각 점검과 후속 학습·고정 정책 평가는 별도로 진행한다.','']
    (PHASE/'probe_response_analysis.md').write_text('\n'.join(lines))
    print(json_io.dumps(dict(completed=True,trials=len(rows),counts=dict(counts))))


if __name__=='__main__':main()
