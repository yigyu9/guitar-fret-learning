"""Read-only same-budget comparison, after all four root jobs complete."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
CONDITIONS=('reference_only','corrective_mixed')
def read(path):return json.loads(Path(path).read_text())
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v


def complete(value,commands):
    assert value['completed'] and value['returncode']==0 and len(value['children'])==4
    for child,(stage,condition) in zip(value['children'],[(s,c) for s in ('fit','evaluate') for c in CONDITIONS]):
        assert child['job']==condition+'_'+stage and child['stage']==stage and child['condition']==condition
        assert child['returncode']==0 and child['argv']==commands[condition][stage]


def self_check():
    commands={c:{s:[c,s] for s in ('fit','evaluate')} for c in CONDITIONS}
    children=[dict(job=c+'_'+s,stage=s,condition=c,returncode=0,argv=commands[c][s]) for s in ('fit','evaluate') for c in CONDITIONS]
    good=dict(completed=True,returncode=0,children=children);complete(good,commands)
    bads=[dict(good,completed=False),dict(good,returncode=1),dict(good,children=children[:-1])]
    for key,value in [('returncode',1),('argv',['wrong']),('condition','wrong')]:
        wrong=[dict(v) for v in children];wrong[0][key]=value;bads.append(dict(good,children=wrong))
    for bad in bads:
        try:complete(bad,commands)
        except AssertionError:pass
        else:raise AssertionError('Incomplete/foreign job admitted')
    assert not any(k in sys.modules for k in ('numpy','torch','isaacgym'))
    print('자가검증 PASS: 네 단계 완료/원 argv guard, actual raw/model 읽기0')


def actual():
    complete(read(BASE/'01_launcher.json'),read(BASE/'cpu_inputs/commands.json'))
    out=HERE/'results_v1';assert not out.exists() and not out.is_symlink()
    probe=module('corrective_actual_probe',BASE/'probe.py');source=probe.source;sys.path.insert(0,str(probe.grid.ROOT))
    inputs={};verified={}
    def track(path):p=Path(path);inputs[str(p)]=probe.grid.sha(p);return p
    def load(path):return read(track(path))
    def pins(mapping):
        for p,h in mapping.items():assert probe.grid.sha(p)==h,p;verified[p]=h
    for p in (Path(__file__),HERE/'PLAN.md',BASE/'01_launcher.json',BASE/'preparation_seal.json',BASE/'review.json'):track(p)
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.gpu.simplified_finger_environment import REWARD_TERMS
    from guitar_learning.tool.experiments.short_finger_learning import runner
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    old=source.parent.HERE
    pre=module('corrective_precheck_audit',track(old/'precheck_analysis/analyze.py'))
    learned=module('corrective_phase_audit',track(old/'learning_analysis/analyze.py'))
    arm=module('corrective_arm_audit',track(old.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py'))
    config=load(BASE/'cpu_inputs/settings.json');short=config['song']['short_learning'];extra=source.parent.support();impl=source.support()
    start=torch.load(track(probe.START),map_location='cpu',weights_only=False)
    for stage in ('collect','evaluate'):track(probe.base.output(stage)/'observations4.npz')
    track(BASE/'fit.py');track(BASE/'cpu_inputs/label_manifest.json')
    data=probe.support().datasets(probe);labels=dict(np.load(track(BASE/'cpu_inputs/labels.npz'),allow_pickle=False))
    y=np.concatenate([labels['native_reference_request4'],labels['shadow_reference_request4']])
    cpu_inputs={k:torch.as_tensor(np.concatenate([d[k] for d in data])) for k in runner.FIELDS}
    cases={};reward_residual=[]
    for condition in CONDITIONS:
        seal,paths=probe.gate(condition,'evaluate');pins(seal['input_pins'])
        for p in paths:track(p)
        fit=probe.output(condition,'fit');folder=probe.output(condition,'evaluate')
        fitreport=load(fit/'corrective_fit_report.json');probe.fitted(condition,fitreport,fit/'initial.pt')
        pins(load(fit/'inputs_after.json')['input_pins'])
        report=load(folder/'imitation_report.json');assert report['completed'] and report['failure'] is None and all(report['checks'].values())
        native=load(folder/'diagnostic_report.json');assert all(native[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored'))
        assert native['failure'] is None and not any(native[k] for k in ('changed_inputs','unpinned_project_sources','cleanup_errors'))
        after=load(folder/'diagnostic_inputs_after.json');assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources'];pins(after['input_pins'])
        scene=load(folder/'gpu_scene_final.json');assert scene['closed'] and scene['environment_count']==128 and scene['diagnostic_guitar_mode']=='fixed'
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
        assert load(folder/'native_effort_readback.json')==load(old/'cpu_inputs/effort_declaration128.json')
        assert load(folder/'settings.json')==config
        ev=load(folder/'evaluation.json');rows=ev['episodes'];assert ev['assigned_quotas']==[1]*128 and probe.grid.complete(rows,128)
        assert ev['policy_performance'] and ev['summary']==runner.summary(rows)
        acceptance=source.parent.acceptance(rows);assert load(folder/'prefix_acceptance.json')==acceptance
        for row in rows:
            c=row['reward_components'];assert set(c)==set(REWARD_TERMS) and np.isfinite([row['reward'],*c.values()]).all();reward_residual.append(row['reward']-sum(c.values()))
        payload=torch.load(track(fit/'initial.pt'),map_location='cpu',weights_only=False);probe.check_metadata(payload['metadata'],condition)
        assert payload['identity']==start['identity'] and payload['updates']==0 and not payload['actor_optimizer']['state'] and not payload['value_optimizer']['state']
        policy=extra.PrefixPolicy(contract=payload['identity']['architecture']['contract'],size='large',fresh=False)
        allowed=set(impl.trainable(policy));assert len(payload['model'])==73 and set(payload['model'])==set(start['model'])
        assert all(torch.equal(v,start['model'][n]) for n,v in payload['model'].items() if n not in allowed)
        assert not torch.count_nonzero(payload['model']['cost_critic.weight']) and not torch.count_nonzero(payload['model']['cost_critic.bias'])
        policy.load_state_dict(payload['model'],strict=True)
        offline=load(fit/'offline_errors.json');assert offline['condition']==condition and offline['additional_steps']==1000 and offline['total_supervised_steps']==2000
        assert len(offline['losses'])==1000 and np.isfinite(offline['losses']).all()
        offline_cpu=probe.support().errors(policy,cpu_inputs,y,data)
        for origin in offline_cpu:
            for split in offline_cpu[origin]:
                for a,b in zip(offline_cpu[origin][split],offline['errors'][origin][split]):
                    assert a['phase']==b['phase'] and a['samples']==b['samples']
                    np.testing.assert_allclose(a['rms4'],b['rms4'],rtol=0,atol=2e-6);np.testing.assert_allclose(a['max_abs4'],b['max_abs4'],rtol=0,atol=2e-6)
        contract=load(folder/'training_contract.json');assert contract==load(old/'train/training_contract.json')
        metadata,_=fixture(1);metadata['action_contract']=contract['action']['target_contract'];meta=load(folder/'trace_metadata.json')
        assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
        trace=dict(np.load(track(folder/'trace_env0_episode0.npz'),allow_pickle=False));guard=dict(np.load(track(folder/'current_goal_DIP60.npz'),allow_pickle=False))
        observed=dict(np.load(track(folder/'observations4.npz'),allow_pickle=False));assert (observed['source_control']==1).all() and observed['first_attempt'].all()
        np.testing.assert_array_equal(observed['requested_NN_action'],observed['executed_action'])
        with torch.no_grad():pred=policy(*(torch.as_tensor(observed[k]) for k in runner.FIELDS))['mean'][:,17:21].tanh().numpy()
        replay=float(abs(pred-observed['requested_NN_action']).max())
        qids=[metadata['joint_names'].index(n) for n in short['learned_action_names']]
        for i in range(4):
            m=observed['env_id']==i;episode=next(r for r in rows if r['env_id']==i);steps=episode['steps']
            np.testing.assert_array_equal(observed['start_clock'][m],np.arange(steps)*4);np.testing.assert_array_equal(observed['clock'][m],np.arange(1,steps+1)*4)
            np.testing.assert_array_equal(observed['phase'][m],[source.phase(int(c)/240.,short) for c in observed['clock'][m]])
            assert not observed['prior_failure'][m].any() and not observed['post_failure'][m][:-1].any()
            assert bool(observed['post_failure'][m][-1])==bool(episode['termination']['physical_failure'] or episode['termination']['wrist_failure'])
            np.testing.assert_array_equal(observed['current_goal'][m],guard['current_goal'][:steps,i])
        m=observed['env_id']==0;np.testing.assert_array_equal(observed['requested_NN_action'][m],trace['policy_action'][:,17:21])
        np.testing.assert_array_equal(observed['old_target_rad'][m][1:],trace['target'][:-1,qids]);np.testing.assert_array_equal(observed['final_target_rad'][m],trace['target'][:,qids])
        release_cross={str(achieved):{str(released):sum(bool(r['notes'][0]['achieved'])==achieved and bool(r['notes'][0]['released'])==released for r in rows) for released in (False,True)} for achieved in (False,True)}
        cases[condition]=dict(acceptance=acceptance,A_achieved_release_cross=release_cross,guard=pre.guard_audit(guard,rows,short['view']),
            trace=pre.trace_audit(trace,metadata,config,rows,contract['action']['target_contract'],extra,arm,'policy'),phases=learned.phase_audit(trace,guard,config,contract['action']['target_contract'],metadata),
            reward9_mean={k:float(np.mean([v['reward_components'][k] for v in rows])) for k in REWARD_TERMS},offline=offline,offline_CPU_recompute=offline_cpu,
            NN_CPU_requested_action_max_abs_residual=replay,observations4_samples=len(observed['env_id']),model=dict(state_tensors=73,critic_std_other_state_exact=True,cost2zero=True,PPO_empty_updates0=True,original_identity_same=True))
    historical=load(probe.base.HERE/'analysis/results_v1/comparison.json')
    result=dict(cases=cases,historical_reference_acceptance=historical['cases']['collect']['acceptance'],historical_warmstart_acceptance=historical['cases']['evaluate']['acceptance'],
        scope='256 new NN attempts/768 notes; historical reference/warmstart not added to new denominators; same additional1000x192 budget; no new capture/PPO',
        limits=['상세 각/힘 env0 60Hz·제어 전 관측 env0..3 한정','body 순힘은 접촉쌍 압력/피부 전체 분리가 아님','offline 요청 오차는 물리 도달이 아니며 CPU 모델 재현은 native CUDA strict load가 아님','동일장면 env3 검산은 독립 seed 일반화가 아니며 예산 자동 확장 없음'])
    out.mkdir();probe.grid.write(out/'comparison.json',result)
    probe.grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,attempts=256,note_opportunities=768,reward9_sum_max_abs_residual=float(max(map(abs,reward_residual)))))
    lines=['# 같은 추가 예산의 reference-only / corrective 비교','','| 조건 | A/B7/B8 달성률 | all3 | A release | 음악/해제/AND | 물리/손목 실패 |','|---|---|---:|---:|---|---|']
    for name,v in cases.items():
        a=v['acceptance'];lines.append('| %s | %s | %.6f | %.6f | %s/%s/%s | %s/%s |'%(name,','.join('%.6f'%n['achieved_fraction'] for n in a['per_note']),a['all3_achieved_fraction'],a['A_released_fraction'],a['music_passed'],a['release_passed'],a['stage_ready'],a['physical_failures'],a['wrist_failures']))
    lines+=['','각 조건128시도·384음과 실패를 모두 보존했다. 원 reference/기존 warmstart는 비교 출처이며 새 NN 성과와 합치지 않는다. 두 조건 모두 같은 추가1000×192 예산이다. A 달성/해제 교차표, 원9항, offline6구간, env0 기하·손목·순힘과 실제각은 comparison.json에 기록했다.','', 'body 순힘은 접촉쌍 압력이 아니며 상세 관찰은 env0 60Hz에 한정한다. CPU 모델 재현은 native strict CUDA 복원의 대체가 아니다. 예산·문턱·후속PPO 자동 확장 없음.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:v['acceptance'] for k,v in cases.items()},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-check',action='store_true');p.add_argument('--root-completed',action='store_true');a=p.parse_args()
    if a.self_check:self_check()
    elif a.root_completed:actual()
    else:print('분석 준비만: root 전체 종료 전 actual raw/model 읽기·결과 생성0')
