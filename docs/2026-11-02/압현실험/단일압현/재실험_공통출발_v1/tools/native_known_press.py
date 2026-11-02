"""실제 운반 후 고정 손목 교사 아래에서 알려진 손가락 후보를 물리 대조한다.

정책과 학습은 사용하지 않는다. 최초 공통 reset 이후 상태를 재주입하지
않으며, 봉인된 현행 v4 실행기의 운반·제어·물리·압현·종료 판정을 재사용한다.
성공은 하중을 포함한 현행 과제 판정이며 실제 현 압력이나 소리를 뜻하지 않는다.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'guitar_learning/train.py').is_file())
BASE_SHA='f5a32d627c4c8844703fdf30dda62944df005fafd20e5a3430c2c694c262c1c9'
TRANSPORT_SHA='7932983cbc5e6b8f20aea8c64c1c5d5d5699efd45f9cb81261291f56b4f9e932'
SCHEMA='guitar_learning.single18.native_known_press.v1'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def checked_file(path,expected):
    if digest(path)!=expected:raise ValueError('봉인 SHA 불일치: '+str(path))


def ramp(time_s):
    """정책 시계 0.5~2.5초만 이동하고 양끝에서는 정지한다."""
    t=max(0.,min(1.,(time_s-.5)/2.))
    return t*t*t*(10+t*(-15+6*t))


def candidate_values(document,index,case):
    """원시 기하 후보의 동일 목표·한계·비담당 관절 불변을 확인한다."""
    if document['schema']!='fixed_native_arrival_wrist_middle4_kinematic_reach.v1' or document['case']!=case:
        raise ValueError('해당 고정 손목 도달성 문서와 동일 목표 필요')
    if not 0<=index<4 or len(document['attempts'])!=4:raise ValueError('후보 번호 0~3 필요')
    geometry=document['attempts'][index]['geometry']
    if not geometry['geometry_candidate']:raise ValueError('기하 후보로 검증되지 않은 행')
    indices=document['finger_joint_indices'];q=geometry['q105'];before=document['before']['q105']
    if len(indices)!=4 or len(set(indices))!=4 or len(q)!=105 or len(before)!=105:
        raise ValueError('4개 고유 축과 q105 필요')
    if not all(math.isfinite(float(v)) for v in q+before):raise ValueError('유한 q105 필요')
    if any(q[i]!=before[i] for i in range(105) if i not in indices):raise ValueError('비담당 101축 변경')
    for i,lower,upper in zip(indices,document['native_lower_rad'],document['native_upper_rad']):
        if not lower<=q[i]<=upper:raise ValueError('native 관절 한계 이탈')
    return indices,[q[i] for i in indices]


def load_base():
    # import 전에 두 실행 소스를 검증한다. 예전 연구 소스는 import하지 않는다.
    checked_file(HERE/'learning_runtime_v4.py',BASE_SHA)
    checked_file(HERE/'transport_runtime.py',TRANSPORT_SHA)
    spec=importlib.util.spec_from_file_location('single18_known_press_base_v4',HERE/'learning_runtime_v4.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def run(args):
    # Isaac Gym은 Torch를 import하는 현행 실행기보다 먼저 로드해야 한다.
    import isaacgym
    import torch
    sys.path.insert(0,str(ROOT))
    base=load_base()
    paths={key:Path(getattr(args,key)).resolve() for key in ('catalog','provenance','evidence','candidate_json')}
    candidate=json.loads(paths['candidate_json'].read_text())
    indices,angles=candidate_values(candidate,args.candidate_index,args.case)
    for path,expected in candidate['source_sha256'].items():checked_file(path,expected)
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    pool=None;pins=None;episode=None;failure=None;completed=False;trace=[];arrival=None;settings=None
    report=dict(schema=SCHEMA,case=args.case,candidate_index=args.candidate_index,environments=1,
        start_denominator=1,policy_decisions=0,optimizer_updates=0,trace_hz=60,physical_criterion_hz=240,
        success_scope='Current loaded geometric task criterion, not calibrated string pressure or acoustics',
        initialization='One common physical reset and unmodified v4 preparation; no later native state injection',
        execution='Existing arrived-wrist teacher and bounded holds on non-goal axes; only assigned finger4 requested angles change',
        ramp=dict(start_policy_s=.5,end_policy_s=2.5,profile='quintic smoothstep; hold until original task termination'),
        base_runtime_sha256=BASE_SHA,transport_runtime_sha256=TRANSPORT_SHA,
        wrapper_sha256=digest(__file__),candidate_json_sha256=digest(paths['candidate_json']))
    started=__import__('time').monotonic()
    try:
        with base.configuration(paths['catalog'],paths['provenance'],args.case,paths['evidence']) as (config,row):
            if (row['string'],row['fret'])!=(candidate['target_string'],candidate['fret']):
                raise ValueError('기하 후보의 줄·프렛과 실행 목표 불일치')
            settings=base.build_settings(config,row,num_envs=1,seed=7)
            settings['known_press']=dict(report,finger_joint_indices=indices,finger_target_rad=angles,
                candidate_json=str(paths['candidate_json']))
            base.transport.write(out/'settings.json',base.portable(settings))
            with base.runtime(config):
                extra=[Path(__file__).resolve(),HERE/'learning_runtime_v4.py',*paths.values()]
                pins=base.runner._pins(settings,out,extra)
                write(out/'inputs_before.json',pins)
                pool=base.LearningPool(settings,out)
                pool.environment.set_evaluation(True,full_song=True)
                pool.prepare()
                env,control=pool.environment,pool.controller
                snapshot=pool.scene.snapshot();arrival=snapshot['q'][0].clone()
                if [control.active[i].item() for i in config['active_axes']]!=indices:
                    raise ValueError('목표 손가락4축과 현행 활성 행동 축 불일치')
                lower=pool.scene.lower[indices];upper=pool.scene.upper[indices]
                goal=torch.tensor(angles,device=pool.scene.device,dtype=arrival.dtype)
                if not bool(((goal>=lower)&(goal<=upper)).all()):raise ValueError('실행 scene native 한계 불일치')
                maximum_ticks=math.ceil(float(env._episode_duration()[0])*60)+2
                for tick in range(maximum_ticks):
                    elapsed=(tick+1)/60.
                    requested=arrival[indices]+ramp(elapsed)*(goal-arrival[indices])
                    desired=control.target[:,control.active].clone()
                    desired[:,config['active_axes']]=requested
                    actions=base.trajectory_actions(desired,control.reference[control.active],control.action_low,control.action_high)
                    _,reward,cost,terminated,truncated,episodes=pool.step(actions)
                    snapshot=pool.scene.snapshot();score=float(env._score_time()[0])
                    audible=bool((env.onset[0]<=score)&(score<env.end[0]))
                    row_trace=dict(tick=tick+1,policy_time_s=score,native_physics_step=int(snapshot['physics_step'][0]),
                        requested_finger4_rad=requested.cpu().tolist(),actual_q105=snapshot['q'][0].cpu().tolist(),
                        target105=control.target[0].cpu().tolist(),height_m=float(env.surface_height[0,0]),
                        tangent_m=float(torch.linalg.vector_norm(env.surface_delta[0,0,:2])),
                        candidate=bool(env.candidate[0,0]),wrong=bool(env.wrong[0,0]),
                        clean=bool(env.candidate[0,0]&~env.wrong[0,0]) and audible,
                        assigned_body_loaded=bool(env.surface_body_loaded[0,0]),
                        guitar_displacement_m=float(torch.linalg.vector_norm(env.guitar_delta[0])),
                        guitar_rotation_rad=float(torch.linalg.vector_norm(env.guitar_rotation[0])),
                        physical_reasons=[n for n,f in zip(base.FAILURE_REASONS,env.tick_failure[0].cpu().tolist()) if f],
                        terminated=bool(terminated[0]),truncated=bool(truncated[0]),reward=float(reward[0]),cost=float(cost[0]))
                    trace.append(row_trace)
                    with (out/'trace.jsonl').open('a') as stream:stream.write(json.dumps(row_trace,allow_nan=False)+'\n')
                    if episodes:
                        if len(episodes)!=1 or episodes[0]['env_id']!=0:raise RuntimeError('분모1 에피소드 불일치')
                        episode=episodes[0];write(out/'episode.json',episode);completed=True;break
                    if bool(terminated[0]|truncated[0]):raise RuntimeError('종료됐으나 에피소드 원문 없음')
                if not completed:raise RuntimeError('원래 과제 종료까지 에피소드가 완결되지 않음')
    except Exception as exc:
        failure=type(exc).__name__+': '+str(exc)
    finally:
        if pool is not None:
            report['preparation']=pool.preparation_records
            report['reset_calls_before_close']=pool.scene.reset_calls
            try:pool.close()
            except Exception as exc:failure=(failure+'; ' if failure else '')+'정리 오류: '+repr(exc)
            report['pool_closed']=pool.closed;report['scene_closed']=bool(pool.scene.closed)
        else:report.update(pool_closed=True,scene_closed=True)
        if pins is not None:
            from guitar_learning.native.paths import verify
            try:report['source_sha256_match_after']=bool(verify(pins))
            except Exception as exc:report['source_sha256_match_after']=False;report['seal_error']=repr(exc)
            if not report['source_sha256_match_after']:failure=(failure+'; ' if failure else '')+'종료 시 입력 SHA 불일치'
        report.update(completed=completed,failure=failure,ticks=len(trace),elapsed_s=__import__('time').monotonic()-started,
            native_task_success=bool(episode and episode.get('song',{}).get('stage_success')),
            preparation_ready=bool(pool is not None and pool.preparation_records and pool.preparation_records[-1]['ready_count']==1))
        if arrival is not None:
            report['actual_arrival_q105']=arrival.cpu().tolist()
            report['ik_snapshot_arrival_max_q_difference_rad']=max(abs(a-b) for a,b in zip(report['actual_arrival_q105'],candidate['before']['q105']))
        if trace:
            report.update(candidate_control_ticks=sum(r['candidate'] for r in trace),clean_control_ticks=sum(r['clean'] for r in trace),
                wrong_control_ticks=sum(r['wrong'] for r in trace))
        write(out/'report.json',report)
    print(json.dumps({k:report[k] for k in ('completed','failure','native_task_success','preparation_ready','ticks')},ensure_ascii=False))
    return 0 if failure is None else 1


def self_test():
    assert ramp(-1)==ramp(.5)==0 and ramp(2.5)==ramp(10)==1 and abs(ramp(1.5)-.5)<1e-12
    assert all(ramp(i/100)<=ramp((i+1)/100) for i in range(300))
    d=dict(schema='fixed_native_arrival_wrist_middle4_kinematic_reach.v1',case='test',
        finger_joint_indices=[60,61,62,63],native_lower_rad=[-1]*4,native_upper_rad=[1]*4,
        before=dict(q105=[0.]*105),attempts=[dict(geometry=dict(geometry_candidate=True,q105=[0.]*105)) for _ in range(4)])
    assert candidate_values(d,0,'test')==([60,61,62,63],[0.]*4)
    d['attempts'][0]['geometry']['q105'][0]=.1
    try:candidate_values(d,0,'test')
    except ValueError:pass
    else:raise AssertionError('비담당 관절 변경 미검출')
    checked_file(HERE/'learning_runtime_v4.py',BASE_SHA);checked_file(HERE/'transport_runtime.py',TRANSPORT_SHA)
    print('CPU 검사 통과: ramp, 후보 축/한계, 비담당 변경 거부, 봉인 SHA. GPU 실행 없음.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    for name in ('catalog','provenance','evidence','case','candidate-json','out'):parser.add_argument('--'+name)
    parser.add_argument('--candidate-index',type=int,choices=range(4),default=0)
    args=parser.parse_args()
    if args.self_test:self_test();return 0
    if any(getattr(args,k) is None for k in ('catalog','provenance','evidence','case','candidate_json','out')):
        parser.error('catalog/provenance/evidence/case/candidate-json/out 필수')
    return run(args)


if __name__=='__main__':raise SystemExit(main())
