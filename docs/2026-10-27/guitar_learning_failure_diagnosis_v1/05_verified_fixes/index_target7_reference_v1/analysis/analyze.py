"""One source7 translated-wrist hypothesis: CPU analysis after root actual exit only."""
import argparse
import csv
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value


def check_launcher(value):
    assert value['completed'] and value['returncode']==0 and len(value['children'])==1
    child=value['children'][0]
    assert child['finger']=='index' and child['control']=='reference' and child['returncode']==0
    return child


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root-completed',action='store_true');args=parser.parse_args()
    if not args.root_completed:
        print('준비만 완료: root 실제 종료 통보 전 자료·모델·결과를 읽지 않습니다.');return
    probe=module('target7_analysis_probe',BASE/'probe.py');grid,cap=probe.grid,probe.cap
    sys.path.insert(0,str(grid.ROOT));out=HERE/'results_v1';cap.reject_existing(out)
    inputs,verified={},{}
    def track(path):
        path=Path(path);inputs[str(path)]=grid.sha(path);return path
    def read(path):return grid.read(track(path))
    def pins(mapping):
        for path,digest in mapping.items():
            if path not in verified:verified[path]=grid.sha(path)
            assert verified[path]==digest,path
    seal,paths=probe.gate()
    for path in paths:track(path)
    pins(seal['input_pins']);read(BASE/'preparation_seal.json')
    review=read(BASE/'review.json');assert review['verdict']=='PASS' and not review['findings'];pins(review['reviewed_sha256'])
    launcher=read(BASE/'01_launcher.json');child=check_launcher(launcher)
    separate=read(BASE/'01_index_launcher.json');assert separate['returncode']==0
    command=read(BASE/'cpu_inputs/commands.json')[0]['argv'];assert child['argv']==separate['argv']==command
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    from dataclasses import asdict
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    folder=BASE/'runs/index';config=read(folder/'settings.json');expected=read(BASE/'cpu_inputs/index_settings.json')
    assert config==expected;short=config['song']['short_learning'];view=short['view'];source=view['source_target']
    definition=read(BASE/'cpu_inputs/task_definition.json');geometry=read(BASE/'cpu_inputs/geometry_derivation.json')
    assert view==definition['view'] and view['duration_ticks']==257 and view['source_index']==7
    assert short['teacher']['source_target_id']==probe.B_ID and source['string']==1 and source['fret']==5 and source['finger']==1
    np.testing.assert_allclose([view['local_press_s'],view['local_onset_s'],view['local_end_s'],source['end_s']-source['onset_s']], [2.88,3.,3.7779,.7779],rtol=0,atol=1e-9)
    assert definition['schedule']['source_release_s']==5.1548 and definition['schedule']['source_end_s']==4.1796
    scope=read(folder/'target7_scope_report.json');assert scope['completed'] and scope['failure'] is None and scope['task_verified'] and scope['aliases_restored'] and not scope['cleanup_errors']
    task=read(folder/'target7_native_task.json');assert task['expected_environment_exact'] and task['view']==view and task['source_target_id']==probe.B_ID
    report,scene=read(folder/'report.json'),read(folder/'gpu_scene_final.json')
    assert all(report[k] for k in ('completed','closed','scene_valid','loader_restored')) and report['failure'] is None
    assert report.get('close_failure') is None and not report.get('close_errors',[]) and not report['changed_inputs'] and not report['unpinned_project_sources']
    assert report['assigned_first_attempts']==4 and report['cap_Nm']==.25 and report['no_NN_checkpoint_training']
    assert scene['closed'] and scene['environment_count']==4 and scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
    assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==4
    assert scene['physics_steps']==report['resources']['physics_steps']==4*report['resources']['control_ticks'] and report['resources']['control_ticks']<=257
    native=read(folder/'native_effort_readback.json');assert native==read(probe.prior.FRESH/'runs/index/native_effort_readback.json')
    contract=read(folder/'training_contract.json');assert contract['native_backend']['diagnostic_native_effort']==native and contract['task']['short_learning']==short
    before,after=read(folder/'inputs_before.json'),read(folder/'inputs_after.json');pins(before)
    assert after['verified'] and before==after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
    evaluation=read(folder/'evaluation.json');episodes=evaluation['episodes']
    assert grid.complete(episodes,4) and evaluation['assigned_quotas']==[1]*4 and evaluation['policy_performance'] is False and evaluation['condition']=='reference'
    assert evaluation['summary']==summary(episodes)
    assert all(e['target_id']==probe.B_ID and e['selected_target_count']==1 and e['steps']<=257 and len(e['reward_components'])==9 for e in episodes)
    acceptance=cap.repro.acceptance(episodes);provider=read(folder/'action_provider.json');assert provider['control']=='reference' and provider['NN'] is False and provider['training_updates']==0
    additional=read(folder/'target7_reference_audit.json');recomputed=probe.postcheck(folder);assert additional==recomputed and recomputed['acceptance']==acceptance
    metadata,_=fixture(1);meta=read(folder/'trace_metadata.json')
    assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
    metadata['action_contract']=contract['action']['target_contract']
    env=ShortEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
    assert env.contract==read(BASE/'cpu_inputs/expected_environment.json') and asdict(env.task.targets[env.selected_index])==source
    trace_path=track(folder/'trace_env0_episode0.npz')
    with np.load(trace_path) as saved:t=dict(saved)
    helper=module('target7_trace_helper',probe.PRE/'analysis/analyze.py')
    arm_helper=module('target7_arm_helper',BASE.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py')
    trace=helper.trace_audit(t,metadata,config,episodes,'reference',contract['action']['target_contract'])
    finite=all(np.isfinite(t[key]).all() for key in ('q','target','body_state','net_body_force_n'))
    arm=arm_helper.arm_audit(t,metadata,config,contract['action']['target_contract']) if finite else None
    track(probe.PRE/'analysis/analyze.py');track(BASE.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py')
    track(Path(__file__).resolve());track(HERE/'PLAN.md')
    result=dict(acceptance=acceptance,summary=evaluation['summary'],episodes=episodes,env0_trace=trace,env0_arm=arm,source7_definition=definition,geometry_derivation=geometry,postcheck=recomputed,
        scope='새 B7 단일 translated-wrist 가설의 실제4시도; 원 A 긍정사례/실제 B sourcepose/정책학습 아님')
    out.mkdir();grid.write(out/'comparison.json',result)
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,first_attempts=4,source7_ticks=257,
        launcher_exit0=True,all_native105_cap90pairs_unchanged=True,all_scenes_closed=True,expected_B_environment_exact=True,
        scope='env0 저장60Hz; 다른3환경 상세힘/nativeqd/240Hz 기하추정 없음; actual4원장/9보상 보존',
        known_limits=['nearest sample/normalcos 미저장 및 원 tie 한계/CPU scalar 불일치 보존','몸체 순힘은 접촉쌍/현압력/구동 torque가 아님',
        'A actual source 증거는 빌린 자세의 출처이며 새 B 도달 증거와 구분','실패는 B 불가능 증명 아님; 성공도 A→B 전환/NN/자유기타/J33/전곡 증명 아님']))
    with (out/'attempts.csv').open('x',newline='') as file:
        rows=[dict(env_id=e['env_id'],achieved=e['achieved'],clean=e['clean_fraction'],wrong=e['audible_wrong_fraction'],physical_failure=e['termination']['physical_failure'],wrist_failure=e['termination']['wrist_failure'],steps=e['steps'],reward=e['reward'],reward_components=str(e['reward_components']),note=str(e['note'])) for e in episodes]
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    a=acceptance
    lines=['# 검지 source7 단일 평행이동 가설 실제 결과','',f"원 기준 달성 {a['achieved']}/4, clean {a['mean_clean']:.6f}, wrong {a['mean_wrong']:.6f}, 물리/손목실패 {a['physical_failures']}/{a['wrist_failures']}. 원 acceptance 통과: {a['passed']}.",'',
        '4분모는 실패를 포함하며 같은 seed7의4환경이다. 선택4·arm12·quaternion은 A112를 빌렸고 손목 위치만 원 셀 중심차29.523457mm 이동했다. 원 source7 음중0.7779초/257tick·원 판정·9보상을 유지했다. 원 음끝4.1796초를 공유 release5.1548초로 늘리지 않았다.','',
        '| env0 60Hz 구간 | 표본 | 선택 body1/2/3 평균N | actual4 ° | target4 ° | wrist mm/° | candidate/wrong | CPU6gate |','|---|---:|---|---|---|---|---|---|']
    fmt=lambda values:', '.join('%.4f'%v for v in values)
    for phase in ('before','audible','after'):
        phase_data=trace.get('phases',{}).get(phase,{});m=phase_data.get('metric_mean')
        lines.append('| %s | %s | %s | %s | %s | %s | %s | %s |'%(phase,phase_data.get('samples','미확인'),fmt(m[12:15]) if m else '미확인',fmt(m[:4]) if m else '미확인',fmt(m[4:8]) if m else '미확인',fmt(m[15:17]) if m else '미확인',str(phase_data.get('saved_candidate_wrong_counts')),str(phase_data.get('CPU_gate_counts'))))
    lines+=['','CPU6gate 순서는 loaded/position/position_facing/positive/candidate/wrong이다. 원 trace_audit 재사용으로 saved candidate/wrong 및 scalar 잔차·nearest tie 한계를 comparison.json에 보존했다. 실제240Hz note/9보상은60Hz CPU 기하로 다시 지급하지 않는다. 상세는 env0뿐이고 다른3환경 상세힘은 미확인이다.','',
        '요청팔/실제제출target/actual의 원 actionbounds 체류·관절오차는 comparison.json의 env0_arm에 분리했다. 몸체 resultant는 접촉쌍/실제현압력이 아니며 cap0.25Nm는 몸체힘 상한을 보장하지 않는다. 손목/관절 추종과 기하/loaded gate를 분리해 읽어야 한다.','',
        '이 실행은 빌린 A 자세에서 파생한 B7 가설의 단음 진단이다. 실패를 B 불가능으로, 성공을 A→B→B 전환·NN학습·자유기타/J33·전곡·자연성·생산채택으로 확대하지 않는다. 새 GPU/조건변경/원자료 수정은 수행하지 않았다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print({key:acceptance[key] for key in ('passed','attempts','achieved','mean_clean','mean_wrong')})


if __name__=='__main__':main()
