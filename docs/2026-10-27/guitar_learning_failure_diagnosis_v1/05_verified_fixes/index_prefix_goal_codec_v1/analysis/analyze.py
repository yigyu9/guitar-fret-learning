"""Goal-policy fit/NN actual adapter, guarded by the two completed root jobs."""
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


def complete(value,commands):
    assert value['completed'] and value['returncode']==0 and len(value['children'])==2
    for child,job in zip(value['children'],('fit','evaluate')):
        assert child['job']==job and child['returncode']==0 and child['argv']==commands[job]


def self_check():
    commands={s:[s] for s in ('fit','evaluate')};children=[dict(job=s,argv=commands[s],returncode=0) for s in commands]
    good=dict(completed=True,returncode=0,children=children);complete(good,commands)
    bads=[dict(good,completed=False),dict(good,returncode=1),dict(good,children=children[:1])]
    for key,val in [('job','reference'),('argv',['wrong']),('returncode',1)]:
        copied=[dict(v) for v in children];copied[0][key]=val;bads.append(dict(good,children=copied))
    for bad in bads:
        try:complete(bad,commands)
        except AssertionError:pass
        else:raise AssertionError('Incomplete/foreign fit/evaluate admitted')
    assert not any(n in sys.modules for n in ('numpy','torch','isaacgym'))
    print('자가검증 PASS: 두 단계 완료 guard; actual raw/model 읽기0')


def actual():
    complete(read(BASE/'02_launcher.json'),read(BASE/'cpu_inputs/commands.json'))
    out=HERE/'results_v1';assert not out.exists() and not out.is_symlink()
    probe=module('goal_NN_actual_probe',BASE/'probe.py');sys.path.insert(0,str(probe.grid.ROOT));codec=probe.support();old=probe.parent.HERE
    inputs={};verified={};execution_pins=[]
    def track(path):p=Path(path);inputs[str(p)]=probe.grid.sha(p);return p
    def load(path):return read(track(path))
    for p in (Path(__file__),HERE/'PLAN.md',BASE/'probe.py',BASE/'codec.py',BASE/'PLAN.md',BASE/'preparation_seal.json',BASE/'review.json',BASE/'02_launcher.json'):track(p)
    reference_audit=BASE/'reference_analysis/results_v1';review=load(reference_audit/'review.json');assert review['verdict']=='PASS' and not review['findings']
    for p,h in review['reviewed_sha256'].items():assert probe.grid.sha(p)==h;verified[p]=h
    reference_result=load(reference_audit/'comparison.json');assert load(reference_audit/'acceptance.json')==reference_result['acceptance'] and reference_result['acceptance']['stage_ready']
    fit=probe.output('fit');folder=probe.output('evaluate')
    for stage,location in (('fit',fit),('evaluate',folder)):
        report=load(location/'goal_codec_report.json');assert report['completed'] and report['failure'] is None and report['stage']==stage and all(report['checks'].values())
        after=load(location/('inputs_after.json' if stage=='fit' else 'diagnostic_inputs_after.json'))
        assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
        before=load(location/'inputs_before.json');assert before==after['input_pins'];execution_pins.append(before)
        assert load(location/'settings.json')==probe.parent.settings()
        if stage=='fit':assert report['procedure']==probe.descriptor() and report['checkpoint_sha256']==probe.grid.sha(fit/'initial.pt') and not report['scene_created']
        else:
            assert report['adapter']==codec.ADAPTER and report['NN_constructors']==1 and report['reference_calls']==0 and report['policy_before']==report['policy_after']
    native=load(folder/'diagnostic_report.json');assert all(native[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored'))
    assert native['failure'] is None and not any(native[k] for k in ('changed_inputs','unpinned_project_sources','cleanup_errors'))
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
    config=read(folder/'settings.json');short=config['song']['short_learning']
    ev=load(folder/'evaluation.json');rows=ev['episodes'];assert ev['assigned_quotas']==[1]*128 and probe.grid.complete(rows,128) and ev['policy_performance'] and ev['summary']==runner.summary(rows)
    acceptance=probe.parent.acceptance(rows);assert load(folder/'prefix_acceptance.json')==acceptance
    pre=module('goal_NN_precheck_helper',track(old/'precheck_analysis/analyze.py'));arm=module('goal_NN_arm_helper',track(old.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py'))
    assert all(acceptance[k]==v for k,v in pre.acceptance(rows).items())
    reward_residual=[]
    for row in rows:
        c=row['reward_components'];assert set(c)==set(REWARD_TERMS) and np.isfinite([row['reward'],*c.values()]).all();reward_residual.append(row['reward']-sum(c.values()))
    contract=load(folder/'training_contract.json');assert contract==load(probe.output('reference')/'training_contract.json')
    original=torch.load(track(probe.parent.checkpoint(0)),map_location='cpu',weights_only=False);payload=torch.load(track(fit/'initial.pt'),map_location='cpu',weights_only=False)
    metadata=payload['metadata'];assert metadata['schema']==probe.SCHEMA and metadata['actual_initialization']==probe.descriptor() and metadata['settings']==config and metadata['policy_output_adapter']==codec.ADAPTER
    assert payload['updates']==0 and not payload['actor_optimizer']['state'] and not payload['value_optimizer']['state'] and len(payload['model'])==73
    GoalPolicy=codec.policy_type(probe);torch.manual_seed(7);fresh=GoalPolicy(contract=contract,size='large',fresh=True)
    assert set(fresh.state_dict())==set(original['model']) and all(torch.equal(v,original['model'][n]) for n,v in fresh.state_dict().items());del fresh
    policy=GoalPolicy(contract=contract,size='large',fresh=False);assert policy.architecture==payload['identity']['architecture'] and payload['identity']!=original['identity']
    allowed=set(probe.source.source.support().trainable(policy));assert all(torch.equal(v,original['model'][n]) for n,v in payload['model'].items() if n not in allowed)
    assert not torch.count_nonzero(payload['model']['cost_critic.weight']) and not torch.count_nonzero(payload['model']['cost_critic.bias']);policy.load_state_dict(payload['model'],strict=True)
    track(probe.source.COLLECT/'observations4.npz');track(probe.source.COLLECT/'training_contract.json');track(probe.parent.base.pre.INPUTS['index'][1])
    data,buckets,labels,labelcontract,label_evidence=codec.dataset(probe);assert labelcontract==contract and label_evidence['source_requested_reference_bitexact']
    offline=load(fit/'offline_errors.json');assert len(offline['losses'])==1000 and np.isfinite(offline['losses']).all()
    with torch.no_grad():pred=policy(*(torch.as_tensor(data[k]) for k in runner.FIELDS))['mean'][:,17:21].tanh().numpy()
    delta=pred-labels.numpy();offline_cpu={}
    for split,mask in (('train',data['env_id']<3),('heldout_same_scene',data['env_id']==3)):
        offline_cpu[split]=[dict(phase=j,samples=int((mask&(data['phase']==j)).sum()),normalized_goal_rms4=np.sqrt(np.mean(delta[mask&(data['phase']==j)]**2,axis=0)).tolist()) for j in range(6)]
        for a,b in zip(offline_cpu[split],offline['errors'][split]):
            assert a['phase']==b['phase'] and a['samples']==b['samples'];np.testing.assert_allclose(a['normalized_goal_rms4'],b['normalized_goal_rms4'],rtol=0,atol=2e-6)
    target=contract['action']['target_contract'];meta,_=fixture(1);meta['action_contract']=target;trace_meta=load(folder/'trace_metadata.json')
    assert trace_meta['joint_names']==meta['joint_names'] and trace_meta['body_names']==meta['body_names']
    trace=dict(np.load(track(folder/'trace_env0_episode0.npz'),allow_pickle=False));guard=dict(np.load(track(folder/'current_goal_DIP60.npz'),allow_pickle=False));d=dict(np.load(track(folder/'observations4.npz'),allow_pickle=False));side=dict(np.load(track(folder/'goal_codec_env0.npz'),allow_pickle=False))
    assert (d['source_control']==1).all() and d['first_attempt'].all();np.testing.assert_array_equal(d['requested_NN_action'],d['executed_action'])
    for i in range(4):
        m=d['env_id']==i;episode=next(r for r in rows if r['env_id']==i);steps=episode['steps']
        np.testing.assert_array_equal(d['start_clock'][m],np.arange(steps)*4);np.testing.assert_array_equal(d['clock'][m],np.arange(1,steps+1)*4)
        assert not d['prior_failure'][m].any() and not d['post_failure'][m][:-1].any()
        assert bool(d['post_failure'][m][-1])==bool(episode['termination']['physical_failure'] or episode['termination']['wrist_failure'])
        np.testing.assert_array_equal(d['current_goal'][m],guard['current_goal'][:steps,i])
    m=d['env_id']==0;ids=short['learned_action_indices'];qids=[meta['joint_names'].index(n) for n in short['learned_action_names']]
    for k in side:np.testing.assert_array_equal(side[k],d[k][m])
    np.testing.assert_array_equal(d['requested_NN_action'][m],trace['policy_action'][:,ids]);np.testing.assert_array_equal(d['old_target_rad'][m][1:],trace['target'][:-1,qids]);np.testing.assert_array_equal(d['final_target_rad'][m],trace['target'][:,qids])
    with torch.no_grad():raw_pred=policy(*(torch.as_tensor(d[k]) for k in runner.FIELDS))['mean'][:,ids].tanh().numpy()
    raw_residual=float(abs(raw_pred-d['raw_goal_normalized']).max())
    active=torch.tensor([target['joint_names'].index(n) for n in target['action_order']]);ref=torch.tensor(target['reference105_rad'],dtype=torch.float32);oldtarget=ref[None].repeat(len(d['clock']),1);oldtarget[:,active[ids]]=torch.from_numpy(d['old_target_rad'])
    mask=torch.zeros(39,dtype=torch.bool);mask[17:33]=True
    fake=SimpleNamespace(spec=short,teacher_reference=ref[active],incremental_mask=mask,controller=SimpleNamespace(reference=ref,target=oldtarget,active=active,action_low=torch.tensor(target['action_lower_rad']),action_high=torch.tensor(target['action_upper_rad'])),environment=SimpleNamespace(_local_time=lambda:torch.from_numpy(d['start_clock']).to(torch.float64)/240.))
    raw=torch.zeros(len(d['clock']),39);raw[:,ids]=torch.from_numpy(d['raw_goal_normalized']);physical,decoded=codec.convert(fake,raw)
    physical_residual=float(abs(physical[:,ids].numpy()-d['requested_NN_action']).max());decode_residual=float(abs(decoded.numpy()-d['decoded_goal_rad']).max())
    reference=runner.read_reference(probe.parent.base.pre.INPUTS['index'][1],short);desired=codec.desired_reference(probe,fake,reference)[:,ids].numpy();goalerror=d['decoded_goal_rad']-desired
    phase_errors=[]
    for j in range(6):
        m=d['phase']==j;count=int(m.sum())
        phase_errors.append(dict(phase=j,samples=count,decoded_goal_minus_planned_RMS_deg=np.rad2deg(np.sqrt(np.mean(goalerror[m]**2,axis=0))).tolist() if count else None,
            oldtarget_minus_planned_mean_deg=np.rad2deg(d['old_target_rad'][m]-desired[m]).mean(0).tolist() if count else None))
    historical=load(probe.source.HERE/'analysis/results_v1/comparison.json')
    result=dict(acceptance=acceptance,reference_acceptance=reference_result['acceptance'],original_incremental1000_acceptance=historical['cases']['evaluate']['acceptance'],offline=offline,offline_CPU_recompute=offline_cpu,label_evidence=label_evidence,
        raw_goal_model_CPU_max_abs_residual=raw_residual,decoded_goal_CPU_max_abs_residual_rad=decode_residual,physical_request_CPU_max_abs_residual=physical_residual,onpolicy_phase_goal_errors=phase_errors,
        trace=pre.trace_audit(trace,meta,config,rows,target,probe.parent.support(),arm,'policy'),guard=pre.guard_audit(guard,rows,short['view']),reward9_mean={k:float(np.mean([r['reward_components'][k] for r in rows])) for k in REWARD_TERMS},
        model=dict(state_tensors=73,original_fresh73_CPU_exact=True,genuine_GoalPolicy_architecture_exact=True,old_incremental_identity_distinct=True,critic_std_other_state_exact=True,cost2zero=True,PPO_empty_updates0=True),
        scope='128 new deterministic NN attempts/384 notes; original incremental1000 and new noNN reference are separate evidence; goal-unit RMS is not incremental-action RMS')
    for mapping in execution_pins:
        for p,h in inputs.items():
            if p in mapping:assert mapping[p]==h;verified[p]=h
    out.mkdir();probe.grid.write(out/'comparison.json',result);probe.grid.write(out/'acceptance.json',acceptance)
    probe.grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,native_verified_execution_pin_counts=[len(v) for v in execution_pins],CPU_rehash_scope='directly used inputs only; native before/after full audit preserved',attempts=128,note_opportunities=384,reward9_sum_max_abs_residual=float(max(map(abs,reward_residual)))))
    a=acceptance;lines=['# Goal codec1000회 NN-only 실제 검산','','| A/B7/B8 달성률 | all3 | A 해제 | 음악/해제/AND | 물리/손목 실패 |','|---|---:|---:|---|---|','| %s | %.6f | %.6f | %s/%s/%s | %s/%s |'%(','.join('%.6f'%n['achieved_fraction'] for n in a['per_note']),a['all3_achieved_fraction'],a['A_released_fraction'],a['music_passed'],a['release_passed'],a['stage_ready'],a['physical_failures'],a['wrist_failures']),'','원128시도/384음·실패·9항을 보존했다. genuine GoalPolicy의 새 layered 정체성을 확인했고 이전 PrefixPolicy 정체성으로 로드하지 않았다. raw 정규화 목표·decode 각·변환 물리요청·guard 최종 목표를 구분한다. 기존 incremental1000 및 새 noNN reference는 별도 비교 출처다.','', '상세 힘/각/기하는 env0 60Hz, 제어전관측은4환경이다. body 순힘은 접촉쌍 압력이 아니며 같은 수치 std도 같은 물리 탐색이 아니다. CPU모델 비교와 native strictload 근거를 구분한다.100PPO/자동예산확장/추가GPU 실행 없음.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print(json.dumps(acceptance,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-check',action='store_true');p.add_argument('--root-completed',action='store_true');a=p.parse_args()
    if a.self_check:self_check()
    elif a.root_completed:actual()
    else:print('NN 분석 준비만: root 전체 종료 전 actual raw/model 읽기·결과 생성0')
