"""Small read-only adapter; actual outputs only after all three root launchers finish."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ORIGINAL=BASE.parent
def read(path):return json.loads(Path(path).read_text())
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v


def launcher(value,stage,argv):
    assert value['completed'] and value['returncode']==0 and value['stage']==stage and value['argv']==argv


def preflight():
    commands=read(BASE/'cpu_inputs/commands.json')
    for n,stage in ((2,'fit'),(3,'evaluate')):launcher(read(BASE/('%02d_launcher.json'%n)),stage,commands[stage])
    old=read(ORIGINAL/'01_launcher.json');assert old['stage']=='collect' and old['completed'] is False and old['returncode']==1
    recovery=read(BASE/'collection_recovery.json');assert recovery['accepted_for_continuation'] and recovery['original_parent_returncode']==1 and recovery['original_imitation_completed'] is False


def self_check():
    value=dict(completed=True,returncode=0,stage='fit',argv=['fit'])
    launcher(value,'fit',['fit'])
    for key,val in [('completed',False),('returncode',1),('stage','collect'),('argv',['wrong'])]:
        bad=dict(value);bad[key]=val
        try:launcher(bad,'fit',['fit'])
        except AssertionError:pass
        else:raise AssertionError('Incomplete stage admitted')
    assert not any(k in sys.modules for k in ('numpy','torch','isaacgym'))
    print('자가검증 PASS: 후속두완료+원실패 별도수용 guard; actual raw/model 읽기0')


def actual():
    preflight();out=HERE/'results_v1';assert not out.exists() and not out.is_symlink()
    probe=module('warmstart_recovery_actual_probe',BASE/'probe.py');native=probe.source;sys.path.insert(0,str(probe.grid.ROOT));seal,paths=probe.gate('evaluate')
    inputs={};verified={}
    def track(path):p=Path(path);inputs[str(p)]=probe.grid.sha(p);return p
    def load(path):return read(track(path))
    def pins(mapping):
        for p,h in mapping.items():assert probe.grid.sha(p)==h,p;verified[p]=h
    pins(seal['input_pins'])
    for p in paths:track(p)
    for p in (Path(__file__),HERE/'PLAN.md',BASE/'preparation_seal.json',BASE/'review.json',ORIGINAL/'01_launcher.json',BASE/'collection_recovery.json',*[BASE/('%02d_launcher.json'%n) for n in (2,3)]):track(p)
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.gpu.simplified_finger_environment import REWARD_TERMS
    from guitar_learning.tool.experiments.short_finger_learning import runner
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    old=native.parent.HERE;pre=module('warmstart_existing_precheck_audit',track(old/'precheck_analysis/analyze.py'))
    learned=module('warmstart_existing_phase_audit',track(old/'learning_analysis/analyze.py'))
    arm=module('warmstart_existing_arm_audit',track(old.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py'))
    config=load(ORIGINAL/'cpu_inputs/settings.json');short=config['song']['short_learning'];extra=native.parent.support();impl=native.support()
    cases={};datasets={};rewards=[]
    for stage in ('collect','evaluate'):
        folder=probe.output(stage);r=load(folder/'imitation_report.json');assert r['failure'] is None
        if stage=='collect':assert r['completed'] is False and [k for k,v in r['checks'].items() if not v]==['NN_constructors_exact']
        else:assert r['completed'] and all(r['checks'].values())
        report=load(folder/'diagnostic_report.json');assert all(report[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored'))
        assert report['failure'] is None and not any(report[k] for k in ('changed_inputs','unpinned_project_sources','cleanup_errors'))
        scene=load(folder/'gpu_scene_final.json');assert scene['closed'] and scene['environment_count']==128 and scene['diagnostic_guitar_mode']=='fixed'
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
        assert load(folder/'native_effort_readback.json')==load(old/'cpu_inputs/effort_declaration128.json')
        after=load(folder/'diagnostic_inputs_after.json');assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources'];pins(after['input_pins'])
        assert load(folder/'settings.json')==config
        ev=load(folder/'evaluation.json');rows=ev['episodes'];assert ev['assigned_quotas']==[1]*128 and probe.grid.complete(rows,128)
        assert ev['policy_performance']==(stage=='evaluate') and ev['summary']==runner.summary(rows)
        a=pre.acceptance(rows);assert all(native.parent.acceptance(rows)[k]==v for k,v in a.items());assert load(folder/'prefix_acceptance.json')==native.parent.acceptance(rows)
        for row in rows:
            c=row['reward_components'];assert set(c)==set(REWARD_TERMS) and np.isfinite([row['reward'],*c.values()]).all();rewards.append(row['reward']-sum(c.values()))
        contract=load(folder/'training_contract.json');assert contract==load(old/'train/training_contract.json')
        metadata,_=fixture(1);metadata['action_contract']=contract['action']['target_contract']
        controller=contract['action']['target_contract'];meta=load(folder/'trace_metadata.json')
        assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
        trace=dict(np.load(track(folder/'trace_env0_episode0.npz'),allow_pickle=False));guard=dict(np.load(track(folder/'current_goal_DIP60.npz'),allow_pickle=False))
        details=pre.trace_audit(trace,metadata,config,rows,controller,extra,arm,'reference' if stage=='collect' else 'policy')
        phases=learned.phase_audit(trace,guard,config,controller,metadata)
        cases[stage]=dict(acceptance=native.parent.acceptance(rows),guard=pre.guard_audit(guard,rows,short['view']),trace=details,phases=phases,
            reward9_mean={k:float(np.mean([v['reward_components'][k] for v in rows])) for k in REWARD_TERMS})
        data=dict(np.load(track(folder/'observations4.npz'),allow_pickle=False));label='requested_reference_action' if stage=='collect' else 'requested_NN_action'
        assert (data['source_control']==(0 if stage=='collect' else 1)).all() and data[label].shape==(len(data['clock']),4)
        np.testing.assert_array_equal(data[label],data['executed_action']);assert data['first_attempt'].all()
        for i in range(4):
            m=data['env_id']==i;episode=next(v for v in rows if v['env_id']==i);steps=episode['steps']
            np.testing.assert_array_equal(data['start_clock'][m],np.arange(steps)*4);np.testing.assert_array_equal(data['clock'][m],np.arange(1,steps+1)*4)
            np.testing.assert_array_equal(data['phase'][m],[native.phase(int(c)/240.,short) for c in data['clock'][m]])
            assert not data['prior_failure'][m].any() and not data['post_failure'][m][:-1].any()
            assert bool(data['post_failure'][m][-1])==bool(episode['termination']['physical_failure'] or episode['termination']['wrist_failure'])
            np.testing.assert_array_equal(data['current_goal'][m],guard['current_goal'][:steps,i])
        m=data['env_id']==0;np.testing.assert_array_equal(data[label][m],trace['policy_action'][:,17:21])
        qids=[metadata['joint_names'].index(n) for n in short['learned_action_names']]
        np.testing.assert_array_equal(data['old_target_rad'][m][1:],trace['target'][:-1,qids])
        np.testing.assert_array_equal(data['final_target_rad'][m],trace['target'][:,qids])
        for k,gk in [('raw_DIP_target_rad','raw_target_rad'),('final_DIP_target_rad','final_target_rad')]:
            for i in range(4):
                m=data['env_id']==i;np.testing.assert_array_equal(data[k][m],guard[gk][:m.sum(),i])
        datasets[stage]=data;cases[stage]['observations4']=dict(samples=len(data['env_id']),phase_counts_by_env=[np.bincount(data['phase'][data['env_id']==i],minlength=6).tolist() for i in range(4)],
            prior_failure=int(data['prior_failure'].sum()),same_endpoint_failure=int(data['post_failure'].sum()),requested_field=label)
    fit=load(probe.output('fit')/'imitation_report.json');assert fit['completed'] and all(fit['checks'].values())
    pins(load(probe.output('fit')/'inputs_after.json')['input_pins'])
    payload=torch.load(track(probe.output('fit')/'initial.pt'),map_location='cpu',weights_only=False)
    original=torch.load(track(native.parent.checkpoint(0)),map_location='cpu',weights_only=False)
    assert payload['identity']==original['identity'] and payload['metadata']['schema']==probe.SCHEMA and payload['metadata']['actual_initialization']==probe.descriptor()
    assert payload['metadata']['settings']==config and payload['updates']==0 and not payload['actor_optimizer']['state'] and not payload['value_optimizer']['state']
    torch.manual_seed(7);fresh=extra.PrefixPolicy(contract=original['identity']['architecture']['contract'],size='large',fresh=True)
    assert len(fresh.state_dict())==73 and all(torch.equal(v,original['model'][n]) for n,v in fresh.state_dict().items());del fresh
    policy=extra.PrefixPolicy(contract=payload['identity']['architecture']['contract'],size='large',fresh=False)
    allowed=set(impl.trainable(policy));assert set(payload['model'])==set(original['model']) and len(payload['model'])==73
    assert all(torch.equal(v,original['model'][n]) for n,v in payload['model'].items() if n not in allowed)
    assert not torch.count_nonzero(payload['model']['cost_critic.weight']) and not torch.count_nonzero(payload['model']['cost_critic.bias'])
    policy.load_state_dict(payload['model'],strict=True);refdata=datasets['collect'];impl.validate_data(refdata,short,native)
    offline=load(probe.output('fit')/'offline_errors.json');assert offline['steps']==len(offline['losses'])==1000 and np.isfinite(offline['losses']).all()
    # CPU replay residuals are reported; model-only load does not replace native strict validation/CUDA RNG.
    def predict(data):
        values=[]
        with torch.no_grad():
            for start in range(0,len(data['clock']),192):values.append(policy(*(torch.as_tensor(data[k][start:start+192]) for k in runner.FIELDS))['mean'][:,17:21].tanh().numpy())
        return np.concatenate(values)
    nn=datasets['evaluate'];residual=float(np.max(abs(predict(nn)-nn['requested_NN_action'])))
    delta=predict(refdata)-refdata['requested_reference_action'];offline_cpu={}
    for name,envmask in [('train',refdata['env_id']<3),('heldout_same_scene',refdata['env_id']==3)]:
        offline_cpu[name]=[dict(phase=j,rms4=np.sqrt(np.mean(delta[envmask&(refdata['phase']==j)]**2,axis=0)).tolist(),
            max_abs4=np.max(abs(delta[envmask&(refdata['phase']==j)]),axis=0).tolist(),
            integrated_action_error_rad_by_env={str(i):(delta[(refdata['env_id']==i)&(refdata['phase']==j)].sum(0)*(4/60)).tolist() for i in np.unique(refdata['env_id'][envmask])}) for j in range(6)]
    oldref=load(old/'precheck_analysis/results_v1/acceptance.json')['reference'];fresh0=load(old/'evaluation_000000/prefix_acceptance.json')
    result=dict(cases=cases,offline=offline,offline_CPU_recompute=offline_cpu,NN_CPU_requested_action_max_abs_residual=residual,source_reference_acceptance=oldref,fresh0000_acceptance=fresh0,
        model=dict(state_tensors=73,only_declared_modules_changed=True,critic_std_other_state_exact=True,cost2zero=True,new_PPO_empty_updates0=True,original_identity_same=True),
        limits=['256새시도/768음; 기존reference128/fresh0000은비교출처이며새NN성과에합치지않음','상세힘/각도는env0 60Hz·관측env0..3·나머지127힘미저장',
            'bodyforce≠pair압력/피부전체분리; offline요청오차≠물리도달; 동일장면env3≠독립seed일반화','NNdeterministic재현과stochasticPPO유지는별개·100PPO자동실행0'])
    out.mkdir();probe.grid.write(out/'comparison.json',result)
    probe.grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,
        original_collect_returncode=1,original_collect_report_completed=False,collection_separately_accepted=True,fit_evaluate_returncodes=[0,0],attempts=256,note_opportunities=768,reward9_sum_max_abs_residual=float(max(map(abs,rewards)))))
    lines=['# 회복 수용 자료로 초기화한 실제 세 음 재현','','원collect는 종료1/reportfalse이며 단일기록오류에 한해 별도수용했다. 원값을 성공종료로 고치지 않았다. 후속fit/evaluate 종료0과 구분한다.','', '| 조건 | A/B7/B8 달성률 | all3 | A release | 음악/해제/AND | 실패물리/손목 |','|---|---|---:|---:|---|---|']
    for k,v in cases.items():
        a=v['acceptance'];lines.append('| %s | %s | %.6f | %.6f | %s/%s/%s | %s/%s |'%(k,','.join('%.6f'%n['achieved_fraction'] for n in a['per_note']),a['all3_achieved_fraction'],a['A_released_fraction'],a['music_passed'],a['release_passed'],a['stage_ready'],a['physical_failures'],a['wrist_failures']))
    lines+=['','원128×2/3음/실패·9항을 보존했다. reference와NN성과·offline오차를 구분하며 100PPO는 자동실행하지 않았다. 상세 env0 phase·기하/wrong·힘/손목, 4환경 관측 시계, 원모델/학습불변·새metadata 검산은 comparison.json에 기록했다. CPU모델만 읽었으며 native strictload·CUDA RNG를 대신했다고 주장하지 않는다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:v['acceptance'] for k,v in cases.items()},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-check',action='store_true');p.add_argument('--root-completed',action='store_true');a=p.parse_args()
    if a.self_check:self_check()
    elif a.root_completed:actual()
    else:print('준비만 완료: root 세 단계 전체 종료 전 actual 자료/결과 생성0')
