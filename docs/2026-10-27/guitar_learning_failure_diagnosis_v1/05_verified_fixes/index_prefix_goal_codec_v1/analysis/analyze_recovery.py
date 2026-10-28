"""Original failed fit, explicit salvage, and new NN evaluation stay distinct."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
RECOVERY=BASE/'recovery_v1'
def read(p):return json.loads(Path(p).read_text())
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v


def complete(original,recovered,oldargv,newargv):
    assert original['completed'] is False and original['returncode']==1 and len(original['children'])==1
    old=original['children'][0];assert old['job']=='fit' and old['returncode']==1 and old['argv']==oldargv
    assert recovered['completed'] and recovered['returncode']==0 and len(recovered['children'])==1
    child=recovered['children'][0];assert child['job']=='evaluate' and child['returncode']==0 and child['argv']==newargv


def self_check():
    old=dict(completed=False,returncode=1,children=[dict(job='fit',returncode=1,argv=['fit'])])
    new=dict(completed=True,returncode=0,children=[dict(job='evaluate',returncode=0,argv=['evaluate'])]);complete(old,new,['fit'],['evaluate'])
    bads=[(dict(old,completed=True),new),(dict(old,returncode=0),new),(dict(old,children=[]),new),(old,dict(new,completed=False)),(old,dict(new,returncode=1)),(old,dict(new,children=[]))]
    for value,other in bads:
        try:complete(value,other,['fit'],['evaluate'])
        except AssertionError:pass
        else:raise AssertionError('Original failure or recovery completion was hidden')
    try:complete(old,new,['wrong'],['evaluate'])
    except AssertionError:pass
    else:raise AssertionError('Foreign command admitted')
    assert not any(n in sys.modules for n in ('numpy','torch','isaacgym'))
    print('자가검증 PASS: 원fit1·회복evaluate0 별도 guard; raw/model 읽기0')


def actual():
    complete(read(BASE/'02_launcher.json'),read(RECOVERY/'01_launcher.json'),read(BASE/'cpu_inputs/commands.json')['fit'],read(RECOVERY/'cpu_inputs/commands.json')['evaluate'])
    out=HERE/'results_recovery_v1';assert not out.exists() and not out.is_symlink()
    recovery=module('goal_recovered_evaluation',RECOVERY/'probe.py');probe=recovery.source;sys.path.insert(0,str(probe.grid.ROOT));codec=probe.support();old=probe.parent.HERE
    inputs={};verified={}
    def track(path):p=Path(path);inputs[str(p)]=probe.grid.sha(p);return p
    def load(path):return read(track(path))
    for p in (Path(__file__),HERE/'PLAN_RECOVERY.md',BASE/'probe.py',BASE/'codec.py',BASE/'02_launcher.json',RECOVERY/'probe.py',RECOVERY/'01_launcher.json',RECOVERY/'01_evaluate_launcher.json'):track(p)
    assert load(RECOVERY/'01_evaluate_launcher.json')==read(RECOVERY/'01_launcher.json')['children'][0]
    audit=load(RECOVERY/'fit_recovery.json');review=load(RECOVERY/'review.json')
    assert review['verdict']=='PASS' and not review['findings'] and audit['accepted_for_evaluate_only'] and audit['original_parent_completed'] is False and audit['original_returncode']==1
    assert audit['PPO_updates']==0 and audit['supervised_steps']==1000 and audit['checkpoint_sha256']==recovery.MODEL_SHA
    for p,h in review['reviewed_sha256'].items():assert probe.grid.sha(p)==h;verified[p]=h
    # Model/fit invariants are the reviewed recovery audit's responsibility, not repeated here.
    for name in audit['unchanged_original_missing_reports']:assert not (probe.output('fit')/name).exists()
    folder=recovery.output('evaluate');r=load(folder/'fit_recovery_report.json')
    assert r['completed'] and r['failure'] is None and all(r['checks'].values()) and r['original_parent_completed'] is False and r['original_returncode']==1
    assert r['metadata_rewritten'] is False and r['checkpoint_sha256']==audit['checkpoint_sha256']
    goal=load(folder/'goal_codec_report.json');assert goal['completed'] and goal['failure'] is None and all(goal['checks'].values()) and goal['stage']=='evaluate'
    assert goal['adapter']==codec.ADAPTER and goal['NN_constructors']==1 and goal['reference_calls']==0 and goal['policy_before']==goal['policy_after']
    native=load(folder/'diagnostic_report.json');assert all(native[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored'))
    assert native['failure'] is None and not any(native[k] for k in ('changed_inputs','unpinned_project_sources','cleanup_errors'))
    after=load(folder/'diagnostic_inputs_after.json');before=load(folder/'inputs_before.json')
    assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources'] and before==after['input_pins']
    config=load(folder/'settings.json');assert config==probe.parent.settings()
    scene=load(folder/'gpu_scene_final.json');assert scene['closed'] and scene['environment_count']==128 and scene['diagnostic_guitar_mode']=='fixed'
    assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
    assert load(folder/'native_effort_readback.json')==load(old/'cpu_inputs/effort_declaration128.json')
    import numpy as np
    import torch
    from types import SimpleNamespace
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.gpu.simplified_finger_environment import REWARD_TERMS
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    ev=load(folder/'evaluation.json');rows=ev['episodes'];assert ev['assigned_quotas']==[1]*128 and probe.grid.complete(rows,128) and ev['policy_performance'] and ev['summary']==runner.summary(rows)
    acceptance=probe.parent.acceptance(rows);assert load(folder/'prefix_acceptance.json')==acceptance
    pre=module('goal_recovered_precheck',track(old/'precheck_analysis/analyze.py'));arm=module('goal_recovered_arm',track(old.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py'))
    assert all(acceptance[k]==v for k,v in pre.acceptance(rows).items())
    reward_residual=[]
    for row in rows:
        c=row['reward_components'];assert set(c)==set(REWARD_TERMS) and np.isfinite([row['reward'],*c.values()]).all();reward_residual.append(row['reward']-sum(c.values()))
    contract=load(folder/'training_contract.json');assert contract==load(probe.output('reference')/'training_contract.json')
    target=contract['action']['target_contract'];meta,_=fixture(1);meta['action_contract']=target;trace_meta=load(folder/'trace_metadata.json')
    assert trace_meta['joint_names']==meta['joint_names'] and trace_meta['body_names']==meta['body_names']
    trace=dict(np.load(track(folder/'trace_env0_episode0.npz'),allow_pickle=False));guard=dict(np.load(track(folder/'current_goal_DIP60.npz'),allow_pickle=False));d=dict(np.load(track(folder/'observations4.npz'),allow_pickle=False));side=dict(np.load(track(folder/'goal_codec_env0.npz'),allow_pickle=False))
    assert (d['source_control']==1).all() and d['first_attempt'].all();np.testing.assert_array_equal(d['requested_NN_action'],d['executed_action'])
    short=config['song']['short_learning'];ids=short['learned_action_indices'];qids=[meta['joint_names'].index(n) for n in short['learned_action_names']]
    for i in range(4):
        m=d['env_id']==i;episode=next(v for v in rows if v['env_id']==i);steps=episode['steps']
        np.testing.assert_array_equal(d['start_clock'][m],np.arange(steps)*4);np.testing.assert_array_equal(d['clock'][m],np.arange(1,steps+1)*4)
        assert not d['prior_failure'][m].any() and not d['post_failure'][m][:-1].any()
        assert bool(d['post_failure'][m][-1])==bool(episode['termination']['physical_failure'] or episode['termination']['wrist_failure'])
        np.testing.assert_array_equal(d['current_goal'][m],guard['current_goal'][:steps,i])
    m=d['env_id']==0
    for k in side:np.testing.assert_array_equal(side[k],d[k][m])
    np.testing.assert_array_equal(d['requested_NN_action'][m],trace['policy_action'][:,ids]);np.testing.assert_array_equal(d['old_target_rad'][m][1:],trace['target'][:-1,qids]);np.testing.assert_array_equal(d['final_target_rad'][m],trace['target'][:,qids])
    active=torch.tensor([target['joint_names'].index(n) for n in target['action_order']]);ref=torch.tensor(target['reference105_rad'],dtype=torch.float32);oldtarget=ref[None].repeat(len(d['clock']),1);oldtarget[:,active[ids]]=torch.from_numpy(d['old_target_rad'])
    mask=torch.zeros(39,dtype=torch.bool);mask[17:33]=True
    fake=SimpleNamespace(spec=short,teacher_reference=ref[active],incremental_mask=mask,controller=SimpleNamespace(reference=ref,target=oldtarget,active=active,action_low=torch.tensor(target['action_lower_rad']),action_high=torch.tensor(target['action_upper_rad'])),environment=SimpleNamespace(_local_time=lambda:torch.from_numpy(d['start_clock']).to(torch.float64)/240.))
    raw=torch.zeros(len(d['clock']),39);raw[:,ids]=torch.from_numpy(d['raw_goal_normalized']);physical,decoded=codec.convert(fake,raw)
    reference=runner.read_reference(track(probe.parent.base.pre.INPUTS['index'][1]),short);desired=codec.desired_reference(probe,fake,reference)[:,ids];expected_raw=codec.encode(desired,*codec.bounds(fake))
    # Genuine GoalPolicy replay only; the separate recovery review owns model/fit invariants.
    path=track(recovery.CHECKPOINT);assert probe.grid.sha(path)==audit['checkpoint_sha256'];payload=torch.load(path,map_location='cpu',weights_only=False)
    policy=codec.policy_type(probe)(contract=contract,size='large',fresh=False);policy.load_state_dict(payload['model'],strict=True)
    assert policy.architecture==payload['identity']['architecture']
    with torch.no_grad():pred=policy(*(torch.as_tensor(d[k]) for k in runner.FIELDS))['mean'][:,ids].tanh().numpy()
    errors=[]
    for j in range(6):
        m=d['phase']==j;count=int(m.sum())
        errors.append(dict(phase=j,samples=count,normalized_goal_RMS4=np.sqrt(np.mean((d['raw_goal_normalized'][m]-expected_raw.numpy()[m])**2,axis=0)).tolist() if count else None,
            decoded_goal_minus_planned_RMS_deg=np.rad2deg(np.sqrt(np.mean((d['decoded_goal_rad'][m]-desired.numpy()[m])**2,axis=0))).tolist() if count else None,
            oldtarget_minus_planned_mean_deg=np.rad2deg(d['old_target_rad'][m]-desired.numpy()[m]).mean(0).tolist() if count else None,
            physical_negative_request_count4=(d['requested_NN_action'][m]<0).sum(0).tolist(),physical_zero_request_count4=(d['requested_NN_action'][m]==0).sum(0).tolist()))
    historical=load(probe.source.HERE/'analysis/results_v1/comparison.json');refaudit=load(BASE/'reference_analysis/results_v1/comparison.json')
    offline=load(probe.output('fit')/'offline_errors.json')
    cross={str(a):{str(rel):sum(bool(v['notes'][0]['achieved'])==a and bool(v['notes'][0]['released'])==rel for v in rows) for rel in (False,True)} for a in (False,True)}
    result=dict(provenance=dict(original_fit_returncode=1,original_fit_completed=False,missing_reports_preserved=audit['unchanged_original_missing_reports'],recovery_accepted_for_evaluate_only=True,new_evaluate_returncode=0,refit=False),
        acceptance=acceptance,A_achieved_release_cross=cross,reference_acceptance=refaudit['acceptance'],original_incremental1000_acceptance=historical['cases']['evaluate']['acceptance'],offline_reviewed_fit_errors=offline,onpolicy_phase_errors=errors,
        raw_goal_model_CPU_max_abs_residual=float(abs(pred-d['raw_goal_normalized']).max()),decoded_goal_CPU_max_abs_residual_rad=float(abs(decoded.numpy()-d['decoded_goal_rad']).max()),physical_request_CPU_max_abs_residual=float(abs(physical[:,ids].numpy()-d['requested_NN_action']).max()),
        trace=pre.trace_audit(trace,meta,config,rows,target,probe.parent.support(),arm,'policy'),guard=pre.guard_audit(guard,rows,short['view']),reward9_mean={k:float(np.mean([v['reward_components'][k] for v in rows])) for k in REWARD_TERMS},
        scope='128 new NN attempts/384 notes; original failed fit, separately reviewed recovery, and native evaluation are distinct; model invariants reused from recovery audit; CPU model replay is not native CUDA strict load')
    for p,h in inputs.items():
        if p in before:assert before[p]==h;verified[p]=h
    out.mkdir();probe.grid.write(out/'comparison.json',result);probe.grid.write(out/'acceptance.json',acceptance)
    probe.grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,native_verified_execution_pin_count=len(before),CPU_rehash_scope='direct inputs only; separate recovery review and native before/after verified map',attempts=128,note_opportunities=384,original_fit_returncode=1,new_evaluate_returncode=0,reward9_sum_max_abs_residual=float(max(map(abs,reward_residual)))))
    a=acceptance;lines=['# Goal codec 회복 평가 실제 검산','','원fit은 종료1이며 감사 보고서가 없는 원상태를 보존했다. 별도 독립검수된 회복 수용과 새 NN 평가 종료0을 구분한다. 새fit/추가1000회는 없다.','', '| A/B7/B8 달성률 | all3 | A 해제 | 음악/해제/AND | 물리/손목 실패 |','|---|---:|---:|---|---|','| %s | %.6f | %.6f | %s/%s/%s | %s/%s |'%(','.join('%.6f'%n['achieved_fraction'] for n in a['per_note']),a['all3_achieved_fraction'],a['A_released_fraction'],a['music_passed'],a['release_passed'],a['stage_ready'],a['physical_failures'],a['wrist_failures']),'','원128시도/384음·실패·9항을 보존했다. raw 정규화목표·decode 각·물리요청·guard 최종목표를 구분하고 genuine GoalPolicy로 CPU 요청만 재현했다. fit 모델 자체 감사는 별도 recovery 검수 근거를 재사용했다.','', '상세 기하/각/힘/손목은env0 60Hz, precontrol 관측은4환경 한정이다. body 순힘은 접촉쌍 압력이 아니며 같은 std도 같은 물리 탐색은 아니다. reference 성공을 NN에 상속하지 않으며100PPO/예산확장/새GPU 실행 없음.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print(json.dumps(acceptance,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-check',action='store_true');p.add_argument('--root-completed',action='store_true');a=p.parse_args()
    if a.self_check:self_check()
    elif a.root_completed:actual()
    else:print('회복 평가 분석 준비만: 실제종료 전 raw/model 읽기·결과 생성0')
