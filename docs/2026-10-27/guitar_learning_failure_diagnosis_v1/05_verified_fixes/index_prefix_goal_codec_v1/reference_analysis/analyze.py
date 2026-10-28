"""Read-only raw-goal reference audit; no fit or native execution."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def read(p):return json.loads(Path(p).read_text())
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v


def complete(value,argv):
    assert value['completed'] and value['returncode']==0 and len(value['children'])==1
    child=value['children'][0];assert child['job']=='reference' and child['returncode']==0 and child['argv']==argv


def self_check():
    child=dict(job='reference',argv=['reference'],returncode=0);good=dict(completed=True,returncode=0,children=[child]);complete(good,['reference'])
    bads=[dict(good,completed=False),dict(good,returncode=1),dict(good,children=[])]
    for key,value in [('job','evaluate'),('argv',['wrong']),('returncode',1)]:
        bad=dict(child);bad[key]=value;bads.append(dict(good,children=[bad]))
    for bad in bads:
        try:complete(bad,['reference'])
        except AssertionError:pass
        else:raise AssertionError('Incomplete/foreign job admitted')
    assert not any(n in sys.modules for n in ('numpy','torch','isaacgym'))
    print('자가검증 PASS: reference1child 완료/원argv; actual raw/model 읽기0')


def actual():
    complete(read(BASE/'01_launcher.json'),read(BASE/'cpu_inputs/commands.json')['reference'])
    out=HERE/'results_v1';assert not out.exists() and not out.is_symlink()
    probe=module('goal_reference_actual_probe',BASE/'probe.py');sys.path.insert(0,str(probe.grid.ROOT));codec=probe.support()
    inputs={};verified={}
    def track(path):p=Path(path);inputs[str(p)]=probe.grid.sha(p);return p
    def load(path):return read(track(path))
    for p in (Path(__file__),HERE/'PLAN.md',BASE/'probe.py',BASE/'codec.py',BASE/'PLAN.md',BASE/'preparation_seal.json',BASE/'review.json',BASE/'01_launcher.json',BASE/'01_reference_launcher.json'):track(p)
    assert load(BASE/'01_reference_launcher.json')==read(BASE/'01_launcher.json')['children'][0]
    folder=probe.output('reference');report=load(folder/'goal_codec_report.json')
    assert report['completed'] and report['failure'] is None and report['stage']=='reference' and all(report['checks'].values())
    assert report['adapter']==codec.ADAPTER and report['NN_constructors']==0 and report['reference_calls']>0
    native=load(folder/'diagnostic_report.json');assert all(native[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored'))
    assert native['failure'] is None and not any(native[k] for k in ('changed_inputs','unpinned_project_sources','cleanup_errors'))
    after=load(folder/'diagnostic_inputs_after.json');assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
    before=load(folder/'inputs_before.json');assert before==after['input_pins']
    # Native before/after audit covers all execution pins; CPU rehash only directly used inputs.
    config=load(folder/'settings.json');assert config==probe.parent.settings();old=probe.parent.HERE
    for n in ('settings.json','expected_environment.json','source_task.json','effort_declaration128.json'):
        p=old/'cpu_inputs'/n
        if p.is_file():track(p)
    assert load(folder/'native_effort_readback.json')==read(old/'cpu_inputs/effort_declaration128.json')
    scene=load(folder/'gpu_scene_final.json');assert scene['closed'] and scene['environment_count']==128 and scene['diagnostic_guitar_mode']=='fixed'
    assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
    import numpy as np
    import torch
    from types import SimpleNamespace
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.gpu.simplified_finger_environment import REWARD_TERMS
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    pre=module('goal_reference_precheck_helper',track(old/'precheck_analysis/analyze.py'))
    arm=module('goal_reference_arm_helper',track(old.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py'))
    ev=load(folder/'evaluation.json');rows=ev['episodes'];assert ev['assigned_quotas']==[1]*128 and probe.grid.complete(rows,128)
    assert not ev['policy_performance'] and ev['summary']==runner.summary(rows)
    acceptance=probe.parent.acceptance(rows);assert load(folder/'prefix_acceptance.json')==acceptance
    independently=pre.acceptance(rows);assert all(acceptance[k]==v for k,v in independently.items())
    residual=[]
    for row in rows:
        values=row['reward_components'];assert set(values)==set(REWARD_TERMS) and np.isfinite([row['reward'],*values.values()]).all();residual.append(row['reward']-sum(values.values()))
    oldfolder=probe.source.COLLECT;original_contract=load(oldfolder/'training_contract.json')
    contract=load(folder/'training_contract.json');assert contract==codec.attach(original_contract)
    target=contract['action']['target_contract'];metadata,_=fixture(1);metadata['action_contract']=target
    meta=load(folder/'trace_metadata.json');assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
    trace=dict(np.load(track(folder/'trace_env0_episode0.npz'),allow_pickle=False));guard=dict(np.load(track(folder/'current_goal_DIP60.npz'),allow_pickle=False))
    observed=dict(np.load(track(folder/'observations4.npz'),allow_pickle=False));side=dict(np.load(track(folder/'goal_codec_env0.npz'),allow_pickle=False))
    short=config['song']['short_learning'];ids=short['learned_action_indices'];qids=[metadata['joint_names'].index(n) for n in short['learned_action_names']]
    assert (observed['source_control']==0).all() and observed['first_attempt'].all()
    np.testing.assert_array_equal(observed['requested_reference_action'],observed['executed_action'])
    for i in range(4):
        m=observed['env_id']==i;episode=next(r for r in rows if r['env_id']==i);steps=episode['steps']
        np.testing.assert_array_equal(observed['start_clock'][m],np.arange(steps)*4);np.testing.assert_array_equal(observed['clock'][m],np.arange(1,steps+1)*4)
        assert not observed['prior_failure'][m].any() and not observed['post_failure'][m][:-1].any()
        assert bool(observed['post_failure'][m][-1])==bool(episode['termination']['physical_failure'] or episode['termination']['wrist_failure'])
        np.testing.assert_array_equal(observed['current_goal'][m],guard['current_goal'][:steps,i])
    m=observed['env_id']==0
    for k in side:np.testing.assert_array_equal(side[k],observed[k][m])
    np.testing.assert_array_equal(observed['requested_reference_action'][m],trace['policy_action'][:,ids])
    np.testing.assert_array_equal(observed['old_target_rad'][m][1:],trace['target'][:-1,qids]);np.testing.assert_array_equal(observed['final_target_rad'][m],trace['target'][:,qids])
    active=torch.tensor([target['joint_names'].index(n) for n in target['action_order']]);ref=torch.tensor(target['reference105_rad'],dtype=torch.float32)
    oldtarget=ref[None].repeat(len(observed['clock']),1);oldtarget[:,active[ids]]=torch.from_numpy(observed['old_target_rad'])
    mask=torch.zeros(39,dtype=torch.bool);mask[17:33]=True
    fake=SimpleNamespace(spec=short,teacher_reference=ref[active],incremental_mask=mask,
        controller=SimpleNamespace(reference=ref,target=oldtarget,active=active,action_low=torch.tensor(target['action_lower_rad']),action_high=torch.tensor(target['action_upper_rad'])),
        environment=SimpleNamespace(_local_time=lambda:torch.from_numpy(observed['start_clock']).to(torch.float64)/240.))
    reference=runner.read_reference(track(probe.parent.base.pre.INPUTS['index'][1]),short)
    desired=codec.desired_reference(probe,fake,reference)[:,ids];raw=torch.zeros(len(observed['clock']),39);raw[:,ids]=torch.from_numpy(observed['raw_goal_normalized'])
    decoded_request,decoded=codec.convert(fake,raw);original_request=probe.parent.support().reference_action(fake,reference)[:,ids]
    raw_expected=codec.encode(desired,*codec.bounds(fake))
    replay=dict(raw_goal_max_abs_residual=float(abs(raw_expected.numpy()-observed['raw_goal_normalized']).max()),
        decoded_goal_max_abs_residual_rad=float(abs(decoded.numpy()-observed['decoded_goal_rad']).max()),
        decoded_minus_original_planned_desired_max_abs_rad=float(abs(decoded-desired).max()),
        physical_request_CPU_max_abs_residual=float(abs(decoded_request[:,ids].numpy()-observed['requested_reference_action']).max()),
        physical_request_minus_original_at_same_saved_oldtarget_max_abs=float(abs(decoded_request[:,ids]-original_request).max()))
    recovery=load(probe.source.HERE/'collection_recovery.json');assert recovery['accepted_for_continuation']
    oldrows=load(oldfolder/'evaluation.json')['episodes']
    result=dict(acceptance=acceptance,original_incremental_reference_acceptance=probe.parent.acceptance(oldrows),codec_reference_replay=replay,
        trace=pre.trace_audit(trace,metadata,config,rows,target,probe.parent.support(),arm,'reference'),guard=pre.guard_audit(guard,rows,short['view']),
        reward9_mean={k:float(np.mean([r['reward_components'][k] for r in rows])) for k in REWARD_TERMS},observations4_samples=len(observed['env_id']),NN_constructors=0,
        scope='128 new noNN attempts/384 notes; raw goal traversed GoalPool decode; historical reference separate; env0 physical trace60Hz,4env precontrol only')
    for p,h in inputs.items():
        if p in before:assert before[p]==h;verified[p]=h
    out.mkdir();probe.grid.write(out/'comparison.json',result);probe.grid.write(out/'acceptance.json',acceptance)
    probe.grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,
        native_verified_execution_pin_count=len(before),CPU_rehash_scope='directly used inputs only; full native before/after map equality and verified flag preserved',attempts=128,note_opportunities=384,reward9_sum_max_abs_residual=float(max(map(abs,residual)))))
    a=acceptance;lines=['# Goal codec raw reference128 검산','','새 raw 목표각은 GoalPool decode를 통과했다. 원 reference 요청을 adapter 우회로 넣은 실행이 아니다.','', '| A/B7/B8 달성 | all3 | A 해제 | 음악/해제/AND | 물리/손목 실패 |','|---|---:|---:|---|---|', '| %s | %.6f | %.6f | %s/%s/%s | %s/%s |'%(','.join('%.6f'%n['achieved_fraction'] for n in a['per_note']),a['all3_achieved_fraction'],a['A_released_fraction'],a['music_passed'],a['release_passed'],a['stage_ready'],a['physical_failures'],a['wrist_failures']), '', '전체128시도/384음·실패·원9항을 보존했다. NN0이며 후속 NN 성과는 미측정이다. 원 incremental reference와의 물리 요청 비교는 동일 저장 oldtarget/clock에서 CPU로 재계산했으며 다른 실행의 물리상태 bit exact를 가정하지 않는다. 상세 힘/기하는env0 60Hz, 제어전관측은4환경에 한정하며 body 순힘은 접촉쌍 압력이 아니다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print(json.dumps(acceptance,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-check',action='store_true');p.add_argument('--root-completed',action='store_true');a=p.parse_args()
    if a.self_check:self_check()
    elif a.root_completed:actual()
    else:print('reference 분석 준비만: root 종료 전 actual raw/model 읽기·결과 생성0')
