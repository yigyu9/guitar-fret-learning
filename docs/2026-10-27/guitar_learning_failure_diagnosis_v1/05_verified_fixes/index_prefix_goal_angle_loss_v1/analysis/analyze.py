"""Read-only angle-loss fit/NN audit after both root jobs complete."""
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

def complete(v,commands):
    assert v['completed'] and v['returncode']==0 and len(v['children'])==2
    for child,job in zip(v['children'],('fit','evaluate')):assert child['job']==job and child['returncode']==0 and child['argv']==commands[job]

def self_check():
    c={s:[s] for s in ('fit','evaluate')};children=[dict(job=s,argv=c[s],returncode=0) for s in c];v=dict(completed=True,returncode=0,children=children);complete(v,c)
    bads=[dict(v,completed=False),dict(v,returncode=1),dict(v,children=children[:1])]
    for key,val in [('job','reference'),('returncode',1),('argv',['wrong'])]:
        a=[dict(x) for x in children];a[0][key]=val;bads.append(dict(v,children=a))
    for a in bads:
        try:complete(a,c)
        except AssertionError:pass
        else:raise AssertionError('Incomplete/foreign job admitted')
    assert not any(n in sys.modules for n in ('numpy','torch','isaacgym'));print('자가검증 PASS: 두job완료 guard; raw/model 읽기0')

def actual():
    complete(read(BASE/'01_launcher.json'),read(BASE/'cpu_inputs/commands.json'))
    out=HERE/'results_v1';assert not out.exists() and not out.is_symlink()
    probe=module('angle_actual_probe',BASE/'probe.py');sys.path.insert(0,str(probe.grid.ROOT));source=probe.source;codec=source.support();impl=probe.support();old=probe.parent.HERE
    inputs={};verified={};maps=[]
    def track(path):p=Path(path);inputs[str(p)]=probe.grid.sha(p);return p
    def load(path):return read(track(path))
    for p in (Path(__file__),HERE/'PLAN.md',BASE/'probe.py',BASE/'fit.py',BASE/'preparation_seal.json',BASE/'review.json',BASE/'01_launcher.json'):track(p)
    for stage in ('fit','evaluate'):
        folder=probe.output(stage);after=load(folder/('inputs_after.json' if stage=='fit' else 'diagnostic_inputs_after.json'));before=load(folder/'inputs_before.json')
        assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources'] and before==after['input_pins'];maps.append(before)
        assert load(folder/'settings.json')==probe.parent.settings()
    fit=probe.output('fit');folder=probe.output('evaluate');report=load(fit/'angle_loss_fit_report.json');probe.fitted(report,fit/'initial.pt')
    execution=load(folder/'angle_loss_execution.json');assert execution['completed'] and execution['failure'] is None and all(execution['checks'].values()) and execution['procedure']==probe.descriptor()
    goal=load(folder/'goal_codec_report.json');assert goal['completed'] and goal['failure'] is None and all(goal['checks'].values()) and goal['NN_constructors']==1 and goal['reference_calls']==0 and goal['policy_before']==goal['policy_after']
    native=load(folder/'diagnostic_report.json');assert all(native[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored')) and native['failure'] is None
    assert not any(native[k] for k in ('changed_inputs','unpinned_project_sources','cleanup_errors'))
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
    config=read(folder/'settings.json');short=config['song']['short_learning'];ev=load(folder/'evaluation.json');rows=ev['episodes']
    assert ev['assigned_quotas']==[1]*128 and probe.grid.complete(rows,128) and ev['policy_performance'] and ev['summary']==runner.summary(rows)
    acceptance=probe.parent.acceptance(rows);assert load(folder/'prefix_acceptance.json')==acceptance
    pre=module('angle_actual_precheck',track(old/'precheck_analysis/analyze.py'));arm=module('angle_actual_arm',track(old.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py'))
    assert all(acceptance[k]==v for k,v in pre.acceptance(rows).items());residual=[]
    for row in rows:
        c=row['reward_components'];assert set(c)==set(REWARD_TERMS) and np.isfinite([row['reward'],*c.values()]).all();residual.append(row['reward']-sum(c.values()))
    contract=load(folder/'training_contract.json');assert contract==load(source.output('reference')/'training_contract.json')
    payload=torch.load(track(fit/'initial.pt'),map_location='cpu',weights_only=False);probe.check_metadata(payload['metadata']);assert payload['updates']==0 and not payload['actor_optimizer']['state'] and not payload['value_optimizer']['state']
    original=torch.load(track(probe.parent.checkpoint(0)),map_location='cpu',weights_only=False);GoalPolicy=codec.policy_type(source);torch.manual_seed(7);fresh=GoalPolicy(contract=contract,size='large',fresh=True)
    initial=fresh.state_dict();assert len(initial)==73 and all(torch.equal(v,original['model'][n]) for n,v in initial.items());del fresh
    policy=GoalPolicy(contract=contract,size='large',fresh=False);policy.load_state_dict(payload['model'],strict=True);assert policy.architecture==payload['identity']['architecture']
    invariant=source.source.source.support().invariants(initial,policy);assert invariant['frozen_state_tensors']==54 and invariant['frozen_state_exact'] and invariant['cost2zero'];assert load(fit/'parameter_invariants.json')==invariant
    track(source.source.COLLECT/'observations4.npz');track(source.source.COLLECT/'training_contract.json');track(probe.parent.base.pre.INPUTS['index'][1])
    data,buckets,rawlabels,desired,bounds,labelcontract,evidence=impl.dataset(probe);assert labelcontract==contract and evidence['source_requested_reference_bitexact']
    with torch.no_grad():pred=policy(*(torch.as_tensor(data[k]) for k in runner.FIELDS))['mean'][:,17:21].tanh();offline_cpu=impl.errors(codec,pred,rawlabels,desired,bounds,data)
    offline=load(fit/'offline_errors.json');assert offline['loss_units']=='rad^2' and len(offline['losses'])==1000 and np.isfinite(offline['losses']).all() and offline['procedure']==probe.descriptor()
    for split in offline_cpu:
        for a,b in zip(offline_cpu[split],offline['errors'][split]):
            assert a['phase']==b['phase'] and a['samples']==b['samples']
            for k in ('normalized_goal_rms4','angle_rms_rad4','angle_rms_deg4'):np.testing.assert_allclose(a[k],b[k],rtol=0,atol=2e-5 if k.endswith('deg4') else 2e-6)
    target=contract['action']['target_contract'];meta,_=fixture(1);meta['action_contract']=target;tm=load(folder/'trace_metadata.json');assert tm['joint_names']==meta['joint_names'] and tm['body_names']==meta['body_names']
    t=dict(np.load(track(folder/'trace_env0_episode0.npz'),allow_pickle=False));g=dict(np.load(track(folder/'current_goal_DIP60.npz'),allow_pickle=False));d=dict(np.load(track(folder/'observations4.npz'),allow_pickle=False));side=dict(np.load(track(folder/'goal_codec_env0.npz'),allow_pickle=False))
    assert (d['source_control']==1).all() and d['first_attempt'].all();np.testing.assert_array_equal(d['requested_NN_action'],d['executed_action'])
    for i in range(4):
        m=d['env_id']==i;episode=next(r for r in rows if r['env_id']==i);steps=episode['steps'];np.testing.assert_array_equal(d['start_clock'][m],np.arange(steps)*4);np.testing.assert_array_equal(d['clock'][m],np.arange(1,steps+1)*4)
        assert not d['prior_failure'][m].any() and not d['post_failure'][m][:-1].any();assert bool(d['post_failure'][m][-1])==bool(episode['termination']['physical_failure'] or episode['termination']['wrist_failure'])
        np.testing.assert_array_equal(d['current_goal'][m],g['current_goal'][:steps,i])
    m=d['env_id']==0;ids=short['learned_action_indices'];qids=[meta['joint_names'].index(n) for n in short['learned_action_names']]
    for k in side:np.testing.assert_array_equal(side[k],d[k][m])
    np.testing.assert_array_equal(d['requested_NN_action'][m],t['policy_action'][:,ids]);np.testing.assert_array_equal(d['old_target_rad'][m][1:],t['target'][:-1,qids]);np.testing.assert_array_equal(d['final_target_rad'][m],t['target'][:,qids])
    active=torch.tensor([target['joint_names'].index(n) for n in target['action_order']]);ref=torch.tensor(target['reference105_rad'],dtype=torch.float32);oldtarget=ref[None].repeat(len(d['clock']),1);oldtarget[:,active[ids]]=torch.from_numpy(d['old_target_rad']);mask=torch.zeros(39,dtype=torch.bool);mask[17:33]=True
    fake=SimpleNamespace(spec=short,teacher_reference=ref[active],incremental_mask=mask,controller=SimpleNamespace(reference=ref,target=oldtarget,active=active,action_low=torch.tensor(target['action_lower_rad']),action_high=torch.tensor(target['action_upper_rad'])),environment=SimpleNamespace(_local_time=lambda:torch.from_numpy(d['start_clock']).to(torch.float64)/240.))
    raw=torch.zeros(len(d['clock']),39);raw[:,ids]=torch.from_numpy(d['raw_goal_normalized']);physical,decoded=codec.convert(fake,raw)
    with torch.no_grad():pred=policy(*(torch.as_tensor(d[k]) for k in runner.FIELDS))['mean'][:,ids].tanh().numpy()
    reference=runner.read_reference(probe.parent.base.pre.INPUTS['index'][1],short);planned=codec.desired_reference(source,fake,reference)[:,ids].numpy();N=np.asarray(short['reference_release_schedule']['negative_selected_rad']);details=[]
    for k in np.flatnonzero(d['phase']==2):
        i=int(d['env_id'][k]);control=int(d['start_clock'][k])//4;z=dict(env_id=i,start_clock=int(d['start_clock'][k]),clock=int(d['clock'][k]),current_goal=int(d['current_goal'][k]),raw_goal4=d['raw_goal_normalized'][k].tolist(),decoded_minus_N_deg=np.rad2deg(d['decoded_goal_rad'][k]-N).tolist(),decoded_minus_scheduled_deg=np.rad2deg(d['decoded_goal_rad'][k]-planned[k]).tolist(),physical_requested4=d['requested_NN_action'][k].tolist(),oldtarget_minus_N_deg=np.rad2deg(d['old_target_rad'][k]-N).tolist(),finaltarget_minus_N_deg=np.rad2deg(d['final_target_rad'][k]-N).tolist(),blocked=bool(g['blocked'][control,i]))
        if i==0:z['env0_postcontrol_candidate3']=t['candidate'][int(d['clock'][k])//4-1].tolist()
        details.append(z)
    cross={str(a):{str(r):sum(bool(v['notes'][0]['achieved'])==a and bool(v['notes'][0]['released'])==r for v in rows) for r in (False,True)} for a in (False,True)}
    norm=load(source.HERE/'analysis/results_recovery_v1/comparison.json');corrective=load(BASE.parent/'index_prefix_corrective_imitation_v1/analysis/results_v1/comparison.json')
    history=dict(incremental1000=norm['original_incremental1000_acceptance'],reference_only2000=corrective['cases']['reference_only']['acceptance'],mixed2000=corrective['cases']['corrective_mixed']['acceptance'],goal_raw1000=norm['acceptance'])
    result=dict(acceptance=acceptance,A_achieved_release_cross=cross,historical_acceptance=history,offline=offline,offline_CPU_recompute=offline_cpu,parameter_invariants=invariant,release_controls=details,
        raw_goal_CPU_max_abs_residual=float(abs(pred-d['raw_goal_normalized']).max()),decoded_goal_CPU_max_abs_residual_rad=float(abs(decoded.numpy()-d['decoded_goal_rad']).max()),physical_request_CPU_max_abs_residual=float(abs(physical[:,ids].numpy()-d['requested_NN_action']).max()),
        trace=pre.trace_audit(t,meta,config,rows,target,probe.parent.support(),arm,'policy'),guard=pre.guard_audit(g,rows,short['view']),reward9_mean={k:float(np.mean([r['reward_components'][k] for r in rows])) for k in REWARD_TERMS},scope='128 new attempts/384notes; same fresh1000 budget, loss-only; detailed physical env0 60Hz/preobs4; historical fit1/recovery remains separate')
    for mapping in maps:
        for p,h in inputs.items():
            if p in mapping:assert mapping[p]==h;verified[p]=h
    out.mkdir();probe.grid.write(out/'comparison.json',result);probe.grid.write(out/'acceptance.json',acceptance)
    probe.grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,native_verified_execution_pin_counts=[len(v) for v in maps],CPU_rehash_scope='direct inputs only; native before/after full audit preserved',attempts=128,note_opportunities=384,reward9_sum_max_abs_residual=float(max(map(abs,residual)))))
    lines=['# 각도 손실1000회 NN 실제 비교','','| 조건,각128 | A/B7/B8 달성 | all3 | A 해제 | 음악/해제/AND |','|---|---|---:|---:|---|']
    for name,a in list(history.items())+[('goal_angle1000',acceptance)]:lines.append('| %s | %s | %.6f | %.6f | %s/%s/%s |'%(name,','.join('%.6f'%n['achieved_fraction'] for n in a['per_note']),a['all3_achieved_fraction'],a['A_released_fraction'],a['music_passed'],a['release_passed'],a['stage_ready']))
    lines+=['','새128/384·실패·9항을 모두 보존했다. 원goal raw 모델의 fit종료1/별도회복평가는 정상fit으로 고치지 않았다. raw/각도/물리요청을구분하며 상세각/기하/힘은env0 60Hz·precontrol4환경 한정이다. body 순힘은접촉쌍 압력이 아니고 단독인과/자연성/자유기타/PPO효과를증명하지않는다. AND 미달이면100PPO0·계수/예산자동탐색0이다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print(json.dumps(acceptance,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-check',action='store_true');p.add_argument('--root-completed',action='store_true');a=p.parse_args()
    if a.self_check:self_check()
    elif a.root_completed:actual()
    else:print('각도loss 분석 준비만: 두job종료 전 raw/model 읽기·결과 생성0')
