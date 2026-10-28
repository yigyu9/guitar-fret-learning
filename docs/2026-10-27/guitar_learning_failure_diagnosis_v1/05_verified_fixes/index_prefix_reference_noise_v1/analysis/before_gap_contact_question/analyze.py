"""Stdlib-only noisy-reference completion/report preparation; actual data remain unread."""
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

MODE='noisy_reference'
HERE=Path(__file__).resolve().parent
BASE=HERE.parent


def read(path):return json.loads(Path(path).read_text())


def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v


def complete(parent,commands):
    assert parent['completed'] is True and parent['returncode']==0 and len(parent['children'])==1
    child=parent['children'][0]
    assert child['job']==MODE and child['returncode']==0 and child['argv']==commands[MODE] and set(commands)=={MODE}


def execution(value):
    assert value['completed'] is True and value['failure'] is None and value['checks'] and all(v is True for v in value['checks'].values())
    n=value['calls'];assert 0<n<=354 and value['RNG_advances']==value['conversion_calls']==n
    assert value['Gaussian_shape_per_call']==[128,4] and value['seed']==7
    assert value['NN_constructors']==value['model_loads']==value['PPO_updates']==value['fit_steps']==0
    assert value['guard_enabled'] is True and value['original_reference_model_RNG_frozen_is_not_sampling_audit'] is True
    assert value['noise_injected_at']=='reference rawgoal after original encode'
    assert len(value['effective_std4'])==4 and all(math.isfinite(x) and x>0 for x in value['effective_std4'])
    for k in ('epsilon_standardized_mean','epsilon_standardized_rms'):
        assert len(value[k])==4 and all(math.isfinite(x) for x in value[k])
    assert all(x>=0 for x in value['epsilon_standardized_rms'])
    assert math.isfinite(value['zero_noise_roundtrip_max_abs_raw']) and value['zero_noise_roundtrip_max_abs_raw']>=0
    assert len(value['normal_noise_stream_sha256'])==64


def self_check():
    c={MODE:['python','probe.py','--execute',MODE]};p=dict(completed=True,returncode=0,children=[dict(job=MODE,argv=c[MODE],returncode=0)])
    complete(p,c)
    bad=[dict(p,completed=False),dict(p,returncode=1),dict(p,children=[]),dict(p,children=p['children']*2)]
    for key,val in (('job','reference'),('argv',['foreign']),('returncode',1)):
        v=copy.deepcopy(p);v['children'][0][key]=val;bad.append(v)
    for v in bad:
        try:complete(v,c)
        except AssertionError:pass
        else:raise AssertionError('Incomplete/foreign native completion admitted')
    v=dict(completed=True,failure=None,checks=dict(all=True),calls=354,RNG_advances=354,conversion_calls=354,Gaussian_shape_per_call=[128,4],seed=7,NN_constructors=0,model_loads=0,PPO_updates=0,fit_steps=0,guard_enabled=True,original_reference_model_RNG_frozen_is_not_sampling_audit=True,noise_injected_at='reference rawgoal after original encode',effective_std4=[.01]*4,epsilon_standardized_mean=[0.]*4,epsilon_standardized_rms=[1.]*4,zero_noise_roundtrip_max_abs_raw=1e-8,normal_noise_stream_sha256='0'*64)
    execution(v)
    for k,val in (('RNG_advances',0),('conversion_calls',353),('Gaussian_shape_per_call',[4,4]),('model_loads',1),('NN_constructors',1),('PPO_updates',1),('completed',False),('guard_enabled',False)):
        a=copy.deepcopy(v);a[k]=val
        try:execution(a)
        except AssertionError:pass
        else:raise AssertionError('Wrong noisy-reference report admitted: '+k)
    assert not any(k in sys.modules for k in ('numpy','torch','isaacgym'))
    print('자가검증 PASS: 한child 완료/NN0·load0·noise/RNG/변환; actual자료읽기·결과생성0')


def actual():
    complete(read(BASE/'01_launcher.json'),read(BASE/'cpu_inputs/commands.json'))
    out=HERE/'results_v1';assert not out.exists() and not out.is_symlink()
    probe=module('noisy_reference_actual_producer',BASE/'probe.py');sys.path.insert(0,str(probe.grid.ROOT));codec=probe.goal.support()
    inputs={};verified={}
    def pin(path):p=Path(path).resolve();inputs[str(p)]=probe.grid.sha(p);return p
    def load(path):return read(pin(path))
    for p in (Path(__file__),HERE/'PLAN.md',BASE/'probe.py',BASE/'review.json',BASE/'preparation_seal.json',BASE/'01_launcher.json',BASE/'cpu_inputs/commands.json',probe.goal.HERE/'codec.py'):pin(p)
    assert load(BASE/'01_noisy_reference_launcher.json')==read(BASE/'01_launcher.json')['children'][0]
    folder=probe.output();report=load(folder/'reference_noise_report.json');execution(report)
    original_report=load(folder/'goal_codec_report.json')
    assert original_report['completed'] and original_report['failure'] is None and all(original_report['checks'].values()) and original_report['stage']=='reference'
    assert original_report['adapter']==codec.ADAPTER and original_report['NN_constructors']==0 and original_report['reference_calls']==report['calls']
    native=load(folder/'diagnostic_report.json');assert all(native[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored')) and native['failure'] is None
    assert not any(native[k] for k in ('changed_inputs','unpinned_project_sources','cleanup_errors'))
    before=load(folder/'inputs_before.json');after=load(folder/'diagnostic_inputs_after.json')
    assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources'] and before==after['input_pins']
    config=load(folder/'settings.json');assert config==probe.parent.settings();old=probe.parent.HERE
    scene=load(folder/'gpu_scene_final.json');assert scene['closed'] and scene['environment_count']==128 and scene['diagnostic_guitar_mode']=='fixed'
    assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
    assert load(folder/'native_effort_readback.json')==load(old/'cpu_inputs/effort_declaration128.json')
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.gpu.simplified_finger_environment import REWARD_TERMS
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    pre=module('noisy_reference_precheck',pin(old/'precheck_analysis/analyze.py'));arm=module('noisy_reference_arm',pin(old.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py'))
    direction=module('noisy_reference_direction',pin(probe.on.HERE/'analysis/analyze.py')).guard_direction
    ev=load(folder/'evaluation.json');rows=ev['episodes'];assert ev['assigned_quotas']==[1]*128 and probe.grid.complete(rows,128) and not ev['policy_performance'] and ev['summary']==runner.summary(rows)
    a=probe.parent.acceptance(rows);assert load(folder/'prefix_acceptance.json')==a and all(a[k]==v for k,v in pre.acceptance(rows).items())
    residual=[]
    for row in rows:
        c=row['reward_components'];assert set(c)==set(REWARD_TERMS) and np.isfinite([row['reward'],*c.values()]).all();residual.append(row['reward']-sum(c.values()))
    contract=load(folder/'training_contract.json');assert contract==load(probe.goal.output('reference')/'training_contract.json')
    target=contract['action']['target_contract'];meta,_=fixture(1);meta['action_contract']=target;tm=load(folder/'trace_metadata.json')
    assert tm['joint_names']==meta['joint_names'] and tm['body_names']==meta['body_names']
    t=dict(np.load(pin(folder/'trace_env0_episode0.npz'),allow_pickle=False));g=dict(np.load(pin(folder/'current_goal_DIP60.npz'),allow_pickle=False))
    d=dict(np.load(pin(folder/'observations4.npz'),allow_pickle=False));side=dict(np.load(pin(folder/'goal_codec_env0.npz'),allow_pickle=False));noise=dict(np.load(pin(folder/'reference_noise4.npz'),allow_pickle=False))
    short=config['song']['short_learning'];ids=short['learned_action_indices'];qi=[meta['joint_names'].index(n) for n in short['learned_action_names']]
    assert (d['source_control']==0).all() and d['first_attempt'].all();np.testing.assert_array_equal(d['requested_reference_action'],d['executed_action'])
    for k in ('env_id','start_clock'):np.testing.assert_array_equal(noise[k],d[k])
    np.testing.assert_array_equal(noise['raw_noisy_goal'],d['raw_goal_normalized'])
    for i in range(4):
        m=d['env_id']==i;episode=next(r for r in rows if r['env_id']==i);steps=episode['steps']
        np.testing.assert_array_equal(d['start_clock'][m],np.arange(steps)*4);np.testing.assert_array_equal(d['clock'][m],np.arange(1,steps+1)*4);np.testing.assert_array_equal(d['current_goal'][m],g['current_goal'][:steps,i])
        assert not d['prior_failure'][m].any() and not d['post_failure'][m][:-1].any();assert bool(d['post_failure'][m][-1])==bool(episode['termination']['physical_failure'] or episode['termination']['wrist_failure'])
    m=d['env_id']==0
    for k in side:np.testing.assert_array_equal(side[k],d[k][m])
    np.testing.assert_array_equal(d['requested_reference_action'][m],t['policy_action'][:,ids]);np.testing.assert_array_equal(d['old_target_rad'][m][1:],t['target'][:-1,qi]);np.testing.assert_array_equal(d['final_target_rad'][m],t['target'][:,qi])
    active=torch.tensor([target['joint_names'].index(n) for n in target['action_order']]);ref=torch.tensor(target['reference105_rad'],dtype=torch.float32);oldtarget=ref[None].repeat(len(d['clock']),1);oldtarget[:,active[ids]]=torch.from_numpy(d['old_target_rad']);mask=torch.zeros(39,dtype=torch.bool);mask[17:33]=True
    fake=SimpleNamespace(spec=short,teacher_reference=ref[active],incremental_mask=mask,controller=SimpleNamespace(reference=ref,target=oldtarget,active=active,action_low=torch.tensor(target['action_lower_rad']),action_high=torch.tensor(target['action_upper_rad'])),environment=SimpleNamespace(_local_time=lambda:torch.from_numpy(d['start_clock']).to(torch.float64)/240.))
    raw=torch.zeros(len(d['clock']),39);raw[:,ids]=torch.from_numpy(d['raw_goal_normalized']);physical,decoded=codec.convert(fake,raw)
    np.testing.assert_array_equal(decoded.numpy(),d['decoded_goal_rad']);np.testing.assert_array_equal(physical[:,ids].numpy(),d['requested_reference_action'])
    reference=runner.read_reference(pin(probe.parent.base.pre.INPUTS['index'][1]),short);desired=codec.desired_reference(probe.goal,fake,reference)[:,ids];raw_reference=codec.encode(desired,*codec.bounds(fake)).numpy()
    std=np.asarray(report['effective_std4'],dtype=np.float32);replayed=np.tanh(np.arctanh(noise['raw_reference'])+noise['scaled_noise']);eps=noise['scaled_noise']/std
    tolerance=8*np.finfo(np.float32).eps
    np.testing.assert_allclose(raw_reference,noise['raw_reference'],rtol=0,atol=tolerance);np.testing.assert_allclose(replayed,noise['raw_noisy_goal'],rtol=0,atol=tolerance);np.testing.assert_allclose(eps,noise['epsilon_standardized'],rtol=0,atol=tolerance)
    clean=load(probe.goal.HERE/'reference_analysis/results_v1/comparison.json');on=load(probe.on.HERE/'analysis/results_v1/comparison.json');off=load(BASE.parent/'index_prefix_goal_guard_off_v1/analysis/results_v1/comparison.json')
    cross={str(x):{str(y):sum(bool(r['notes'][0]['achieved'])==x and bool(r['notes'][0]['released'])==y for r in rows) for y in (False,True)} for x in (False,True)}
    result=dict(acceptance=a,A_achieved_release_cross=cross,execution=report,original_reference_report=original_report,baselines=dict(clean_reference=clean['acceptance'],NN_on_stochastic=on['cases']['stochastic']['acceptance'],NN_off_stochastic=off['cases']['stochastic']['acceptance']),
        noise_replay=dict(bounded_rows=len(d['env_id']),raw_reference_CPU_max_abs=float(abs(raw_reference-noise['raw_reference']).max()),raw_noisy_CPU_max_abs=float(abs(replayed-noise['raw_noisy_goal']).max()),epsilon_division_CPU_max_abs=float(abs(eps-noise['epsilon_standardized']).max()),decoded_physical_CPU_max_abs=0.,float32_arithmetic_tolerance=tolerance,bounded4_epsilon_mean=noise['epsilon_standardized'].mean(0).tolist(),bounded4_epsilon_rms=np.sqrt((noise['epsilon_standardized']**2).mean(0)).tolist(),scope='bounded4 replay only; all128 noise stats/stream digest from native runtime audit; no NN epsilon realization equality claimed'),
        trace=pre.trace_audit(t,meta,config,rows,target,probe.parent.support(),arm,'reference'),guard=pre.guard_audit(g,rows,short['view']),guard_direction=direction(g,np),reward9_mean={k:float(np.mean([r['reward_components'][k] for r in rows])) for k in REWARD_TERMS},scope='128 new noNN noisy-reference attempts/384 notes; historical clean reference and NN on/off separate; no model load/fit/PPO')
    for p,h in inputs.items():
        if p in before:assert before[p]==h;verified[p]=h
    out.mkdir();probe.grid.write(out/'comparison.json',result);probe.grid.write(out/'acceptance.json',a)
    probe.grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,native_verified_execution_pin_count=len(before),CPU_rehash_scope='direct inputs only; native full before/after audit reused',attempts=128,note_opportunities=384,model_loads=0,reward9_sum_max_abs_residual=float(max(map(abs,residual)))))
    print(json.dumps(dict(acceptance=a,A_cross=cross,noise_replay=result['noise_replay']),ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-check',action='store_true');p.add_argument('--root-completed',action='store_true');a=p.parse_args()
    if a.self_check:self_check()
    elif a.root_completed:actual()
    else:print('분석 준비만: root noisy_reference child종료 통보 전 실제자료읽기/결과생성0')
