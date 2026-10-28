"""Read-only CPU adapter for completed prefix300 and seven fixed evaluations."""
import argparse
from collections import Counter
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
UPDATES=(0,50,100,150,200,250,300)
JOBS=('train',)+tuple('evaluate_%06d'%u for u in UPDATES)


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec)
    sys.modules[name]=v;spec.loader.exec_module(v);return v


def completed_launcher(value):
    if value.get('completed') is not True or value.get('returncode')!=0 or [c.get('job') for c in value.get('children',[])]!=list(JOBS) or any(c.get('returncode')!=0 for c in value.get('children',[])):
        raise ValueError('Root actual eight-stage completion required')


def criteria(cases):
    result={}
    for key in ('music_passed','release_passed','stage_ready'):
        pairs=[[a,b] for a,b in zip(UPDATES[1:-1],UPDATES[2:]) if cases[a]['acceptance'][key] and cases[b]['acceptance'][key]]
        result[key]=dict(consecutive_pass=bool(pairs),passing_pairs=pairs,late_maintenance_pass=all(cases[u]['acceptance'][key] for u in (200,250,300)))
    return result


def preflight():
    # First actual read: no producer/numerical imports or checkpoint reads yet.
    paths=[BASE/'02_train_eval_launcher.json',BASE/'train/metrics.jsonl']
    launcher=json.loads(paths[0].read_text());completed_launcher(launcher)
    metrics=[json.loads(s) for s in paths[1].read_text().splitlines()]
    if [m['update'] for m in metrics]!=list(range(1,301)):raise ValueError('All300 metrics required')
    for u in UPDATES:
        path=BASE/('evaluation_%06d'%u)/'evaluation.json';value=json.loads(path.read_text());rows=value['episodes']
        if value['assigned_quotas']!=[1]*128 or len(rows)!=128 or sorted(r['env_id'] for r in rows)!=list(range(128)) or any(len(r['notes'])!=3 for r in rows):raise ValueError('Seven complete128 first-attempt ledgers required')
        paths.append(path)
    return launcher,metrics,paths


def self_check():
    cases={u:dict(acceptance=dict(music_passed=True,release_passed=True,stage_ready=True)) for u in UPDATES}
    assert all(x['consecutive_pass'] and x['late_maintenance_pass'] for x in criteria(cases).values())
    cases[300]['acceptance']['release_passed']=False;cases[300]['acceptance']['stage_ready']=False
    assert criteria(cases)['music_passed']['late_maintenance_pass'] and not criteria(cases)['release_passed']['late_maintenance_pass']
    for u in UPDATES[2:]:cases[u]['acceptance']={k:False for k in cases[u]['acceptance']}
    assert not any(x['consecutive_pass'] for x in criteria(cases).values())  # initial+50 is not a trained pair
    old=Path.read_text;reads=[]
    def unfinished(p,*a,**kw):
        reads.append(p);assert p==BASE/'02_train_eval_launcher.json'
        return json.dumps(dict(completed=False,returncode=None,children=[]))
    Path.read_text=unfinished
    try:
        try:preflight()
        except ValueError:pass
        else:raise AssertionError('Incomplete run admitted')
    finally:Path.read_text=old
    assert reads==[BASE/'02_train_eval_launcher.json'] and not any(k in sys.modules for k in ('torch','numpy','isaacgym'))
    launcher=dict(completed=True,returncode=0,children=[dict(job=j,returncode=0) for j in JOBS])
    def synthetic(p,*a,**kw):
        if p.name=='02_train_eval_launcher.json':return json.dumps(launcher)
        if p.name=='metrics.jsonl':return '\n'.join(json.dumps(dict(update=u)) for u in range(1,301))
        return json.dumps(dict(assigned_quotas=[1]*128,episodes=[dict(env_id=i,notes=[{}, {}, {}]) for i in range(128)]))
    Path.read_text=synthetic
    try:assert len(preflight()[2])==9
    finally:Path.read_text=old
    for missing in ('metrics','quota'):
        def incomplete(p,*a,**kw):
            value=synthetic(p)
            if missing=='metrics' and p.name=='metrics.jsonl':return '\n'.join(value.splitlines()[:-1])
            if missing=='quota' and p.name=='evaluation.json':
                x=json.loads(value);x['episodes'].pop();return json.dumps(x)
            return value
        Path.read_text=incomplete
        try:
            try:preflight()
            except ValueError:pass
            else:raise AssertionError('Incomplete '+missing+' admitted')
        finally:Path.read_text=old
    for bad in (dict(launcher,completed=False),dict(launcher,children=launcher['children'][:-1]),dict(launcher,returncode=1)):
        try:completed_launcher(bad)
        except ValueError:pass
        else:raise AssertionError('Bad launcher admitted')
    b=module('prefix_legacy_B_criteria',BASE.parent/'low_effort_index_zero_cost_init_v1/analysis/analyze.py')
    good=dict(achieved_fraction=.9,mean_clean_fraction=.9,mean_audible_wrong_fraction=.1,physical_failure_fraction=0.,wrist_failure_fraction=0.)
    ranked={u:dict(summary=dict(good),physical_or_wrist_fraction=0.) for u in UPDATES};assert b.selection(ranked)['best_update']==300
    ranked[100]['summary']['achieved_fraction']=1.;assert b.selection(ranked)['video_updates']==[100,300]
    import numpy as np
    n=354;now=np.arange(1,n+1)/60;action=np.zeros((n,39),np.float32);action[:,17:21]=.01;action[(now>=3.17)&(now<3.27),20]=-.01
    target=np.zeros((n,105),np.float32);target[:,:4]=np.cumsum(action[:,17:21]*(4/60),axis=0)
    body=np.zeros((n,5,13));body[:,:,6]=1
    t=dict(time_s=now,q=target.copy(),target=target,policy_action=action,executed_action=action.copy(),body_state=body,net_body_force_n=np.zeros((n,5,3)),wrist_position_goal_G_m=np.zeros((n,3)),wrist_quaternion_goal_G_xyzw=np.tile([0,0,0,1],(n,1)),candidate=np.zeros((n,3),bool),wrong=np.zeros((n,3),bool))
    ts=[dict(onset_s=3.,end_s=3.17,press_s=2.88),dict(onset_s=3.952,end_s=4.73,press_s=3.832),dict(onset_s=5.3568,end_s=5.7051,press_s=3.832)]
    config=dict(song=dict(short_learning=dict(view=dict(source_targets=ts,score_offset_s=0.),learned_action_names=list('abcd'),learned_action_indices=list(range(17,21)))))
    ctl=dict(action_order=list('abcd'),action_lower_rad=[-1]*4,action_upper_rad=[1]*4);meta=dict(joint_names=list('abcd')+['other']*101,body_names=['human/LH:index1','human/LH:index2','human/LH:index3','human/L_Wrist','guitar/guitar'])
    g=dict(final_target_rad=target[:,3:4].copy(),old_target_rad=np.r_[np.float32(0),target[:-1,3]][:,None],raw_target_rad=target[:,3:4].copy())
    phase=phase_audit(t,g,config,ctl,meta);assert sum(p['samples'] for p in phase['phases'].values())==354 and phase['phases']['release_window']['negative_action_count'][3]>0
    t['target'][50,0]+=.1
    try:phase_audit(t,g,config,ctl,meta)
    except AssertionError:pass
    else:raise AssertionError('Wrong NN target codec admitted')
    assert not any(k in sys.modules for k in ('torch','isaacgym'))
    print('자가검증 PASS: 완료guard/음악·해제·AND/인접2·후반유지/사전순위; 실제자료0')


def phase_audit(t,g,config,controller,metadata):
    import numpy as np
    from scipy.spatial.transform import Rotation
    short=config['song']['short_learning'];view=short['view'];now=t['time_s'];targets=view['source_targets'];offset=view['score_offset_s']
    Aon,Aend,Bpress,Bon,Bend,Con,Cend=targets[0]['onset_s']-offset,targets[0]['end_s']-offset,targets[1]['press_s']-offset,targets[1]['onset_s']-offset,targets[1]['end_s']-offset,targets[2]['onset_s']-offset,targets[2]['end_s']-offset
    bounds=[0,2.,Aon,Aend,Aend+.1,Bpress-.12,Bpress,Bon,Bend,Con,Cend,float('inf')]
    names=['initial_ramp','A_preparation','A_audible','release_window','wrist_move','B_preclose','B_preparation','B7_audible','B_shared_gap','B8_audible','tail']
    qids=[metadata['joint_names'].index(n) for n in short['learned_action_names']];ai=[controller['action_order'].index(n) for n in short['learned_action_names']]
    lo=np.asarray(controller['action_lower_rad'])[ai];hi=np.asarray(controller['action_upper_rad'])[ai]
    actual=t['q'][:,qids];target=t['target'][:,qids];action=t['policy_action'][:,short['learned_action_indices']]
    bodies=[metadata['body_names'].index('human/LH:index'+str(i)) for i in (1,2,3)]
    wrist,guitar=[metadata['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')]
    force=np.linalg.norm(t['net_body_force_n'][:,bodies],axis=-1);rg=Rotation.from_quat(t['body_state'][:,guitar,3:7])
    position=np.linalg.norm(t['body_state'][:,guitar,:3]+rg.apply(t['wrist_position_goal_G_m'])-t['body_state'][:,wrist,:3],axis=-1)*1000
    angle=np.rad2deg((rg*Rotation.from_quat(t['wrist_quaternion_goal_G_xyzw'])*Rotation.from_quat(t['body_state'][:,wrist,3:7]).inv()).magnitude())
    np.testing.assert_array_equal(action,t['executed_action'][:,short['learned_action_indices']])
    # Match float32 incremental codec on same actual clocks; first native oldtarget
    # exists only for DIP in sidecar, so the other3 first intervals stay unavailable.
    expected=np.clip(target[:-1]+action[1:]*(4./60),lo,hi).astype(target.dtype)
    raw_dip=np.clip(g['old_target_rad'][:len(now),0]+action[:,3]*(4./60),lo[3],hi[3])
    assert (abs(raw_dip-g['raw_target_rad'][:len(now),0])<=2e-6).all()
    expected[:,3]=g['final_target_rad'][1:len(now),0]
    codec_error=float(abs(expected-target[1:]).max()) if len(now)>1 else None
    if codec_error is not None:assert codec_error<=2e-6
    dq=np.diff(actual,axis=0,prepend=actual[:1]);dt=np.diff(target,axis=0,prepend=target[:1]);phases={}
    for name,start,end in zip(names,bounds,bounds[1:]):
        mask=(now>=start)&(now<end);idx=np.flatnonzero(mask);q=actual[mask];goal=target[mask];raw=action[mask]
        if not len(idx):phases[name]=dict(samples=0);continue
        previous=max(0,int(idx[0])-1)
        phases[name]=dict(samples=len(idx),first_endpoint_s=float(now[idx[0]]),last_endpoint_s=float(now[idx[-1]]),
            actual_start_deg=np.rad2deg(q[0]).tolist(),actual_end_deg=np.rad2deg(q[-1]).tolist(),actual_span_deg=np.rad2deg(np.ptp(q,axis=0)).tolist(),
            actual_change_from_previous_sample_deg=np.rad2deg(actual[idx[-1]]-actual[previous]).tolist(),mean_target_minus_actual_deg=np.rad2deg(goal-q).mean(0).tolist(),
            policy_action_mean=raw.mean(0).tolist(),negative_action_count=(raw<0).sum(0).tolist(),positive_action_count=(raw>0).sum(0).tolist(),
            negative_target_increment_count=(dt[mask]<0).sum(0).tolist(),negative_actual_increment_count=(dq[mask]<0).sum(0).tolist(),
            target_lower_count=(goal<=lo+1e-6).sum(0).tolist(),target_upper_count=(goal>=hi-1e-6).sum(0).tolist(),
            actual_lower_count=(q<=lo+1e-6).sum(0).tolist(),actual_upper_count=(q>=hi-1e-6).sum(0).tolist(),
            body1_2_3_resultant_mean_N=force[mask].mean(0).tolist(),body1_2_3_resultant_p95_N=np.percentile(force[mask],95,axis=0).tolist(),body1_2_3_resultant_max_N=force[mask].max(0).tolist(),
            wrist_position_mean_max_mm=[float(position[mask].mean()),float(position[mask].max())],wrist_rotation_mean_max_deg=[float(angle[mask].mean()),float(angle[mask].max())],
            candidate_counts=t['candidate'][mask].sum(0).tolist(),wrong_counts=t['wrong'][mask].sum(0).tolist())
    return dict(phases=phases,selected_joint_names=short['learned_action_names'],codec_max_abs_rad=codec_error,first_tick_NN_selected_action_exact=True,
        scope='env0postcontrol60Hz; phase uses endpoint time; negative angle/action is native sign, not proof of anatomical opening or skin separation; first3joint increment unavailable')


def actual_main():
    launcher,metrics,early=preflight();out=HERE/'results_v1';assert not out.exists() and not out.is_symlink(),'Existing result refused'
    probe=module('prefix_learning_actual_probe',BASE/'probe.py');grid=probe.grid;sys.path.insert(0,str(grid.ROOT));inputs={};verified={}
    def track(p):p=Path(p).resolve();inputs[str(p)]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(mapping):
        for p,h in mapping.items():assert grid.sha(p)==h,p;verified[p]=h
    for p in early:track(p)
    seal,paths=probe.gate('train');pins(seal['input_pins'])
    for p in paths:track(p)
    pre=module('prefix_reviewed_precheck_helpers',track(BASE/'precheck_analysis/analyze.py'))
    pre_review=read(BASE/'precheck_analysis/results_v1/review.json');assert pre_review['verdict']=='PASS' and not pre_review['findings'];pins(pre_review['reviewed_sha256'])
    pv=read(BASE/'precheck_analysis/results_v1/verification.json');pins(pv['input_sha256']);pins(pv['verified_input_sha256'])
    prior=read(BASE/'precheck_analysis/results_v1/acceptance.json');assert prior['reference']['stage_ready']
    b=module('prefix_reviewed_B_helpers',track(BASE.parent/'low_effort_index_zero_cost_init_v1/analysis/analyze.py'))
    arm=module('prefix_reviewed_arm_helpers',track(BASE.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py'))
    config=read(BASE/'cpu_inputs/settings.json');declaration=read(BASE/'cpu_inputs/effort_declaration128.json');commands=read(BASE/'cpu_inputs/commands.json')
    assert [c['argv'] for c in launcher['children']]==[commands['train']]+commands['evaluate']
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.gpu.simplified_finger_environment import REWARD_TERMS
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    extra=probe.support();metadata,_=fixture(1);cases={};attempts=[];notes=[];stages=[];identities=[];heads=[];common=None
    for job in JOBS:
        train=job=='train';u=0 if train else int(job.split('_')[1]);folder=probe.output('train' if train else 'evaluate',update=u)
        child=read(BASE/('02_'+job+'_launcher.json'));parent=next(c for c in launcher['children'] if c['job']==job)
        assert child['job']==job and child['returncode']==0 and child['argv']==parent['argv']
        assert read(folder/'settings.json')==config
        report=read(folder/'report.json');diag=read(folder/'diagnostic_report.json');scope=read(folder/'prefix_learning_report.json');scene=read(folder/'gpu_scene_final.json')
        assert report['completed'] and report['closed'] and report['failure'] is None and not report['changed_inputs'] and not report['unpinned_project_sources']
        assert all(diag[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored')) and diag['failure'] is None
        assert not any(diag[k] for k in ('cleanup_errors','changed_inputs','unpinned_project_sources')) and diag['native_environment_count']==128
        assert diag['phase']==scope['phase']==('train' if train else 'evaluate') and diag['update']==scope['update']==u
        assert scope['completed'] and scope['failure'] is None and all(scope['checks'].values()) and scope['NN_constructors']==1 and not scope['reference_N_injected'] and scope['fresh_cost_initialization']==train
        assert scene['closed'] and scene['environment_count']==128 and scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
        assert scene['physics_steps']==diag['physics_steps'] and (scene['physics_steps']==38400 if train else scene['physics_steps']%4==0 and scene['physics_steps']<=1416)
        assert read(folder/'native_effort_readback.json')==declaration
        contract=read(folder/'training_contract.json');assert contract['task']['short_learning']==config['song']['short_learning'] and contract['native_backend']['diagnostic_native_effort']==declaration
        if common is None:common=contract
        assert contract==common
        before=read(folder/'inputs_before.json');pins(before)
        for name in ('inputs_after.json','diagnostic_inputs_after.json'):
            after=read(folder/name);assert after['verified'] and after['input_pins']==before and not after['changed_paths'] and not after['unpinned_project_sources']
        stages.append(dict(job=job,physics_steps=scene['physics_steps'],closed=True,NN1_reference_N_injected=False,guard_counts_all_episode_controls=scope['guard_counts_by_goal']))
        if train:
            assert sum(r[0] for r in scope['guard_counts_by_goal'])==1228800
            continue
        value=read(folder/'evaluation.json');rows=value['episodes'];assert grid.complete(rows,128) and value['condition']=='policy' and value['policy_performance'] is True and value['summary']==runner.summary(rows)
        a=probe.acceptance(rows);assert all(a[k]==v for k,v in pre.acceptance(rows).items()) and a==read(folder/'prefix_acceptance.json')
        either=sum(r['termination']['physical_failure'] or r['termination']['wrist_failure'] for r in rows)/128
        cases[u]=dict(update=u,summary=value['summary'],physical_or_wrist_fraction=either,acceptance=a)
        for r in rows:
            assert set(r['reward_components'])==set(REWARD_TERMS) and np.isfinite([r['reward'],r['cost'],*r['reward_components'].values()]).all()
            attempts.append(dict(update=u,env_id=r['env_id'],achieved=r['achieved'],clean=r['clean_fraction'],wrong=r['audible_wrong_fraction'],cost=r['cost'],physical_failure=r['termination']['physical_failure'],wrist_failure=r['termination']['wrist_failure'],steps=r['steps'],reward=r['reward'],reward_sum_residual=r['reward']-sum(r['reward_components'].values()),**r['reward_components']))
            for n in r['notes']:notes.append(dict(update=u,env_id=r['env_id'],source_index=n['source_index'],achieved=n['achieved'],clean=n['clean_fraction'],wrong=n['audible_wrong_fraction'],released=n['released'],release_s=n['release_s'],physical_failure=r['termination']['physical_failure'],wrist_failure=r['termination']['wrist_failure']))
        meta=read(folder/'trace_metadata.json');assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names'] and meta['source_indices']==[4,7,8]
        metadata['action_contract']=contract['action']['target_contract']
        with np.load(track(folder/'trace_env0_episode0.npz')) as saved:t=dict(saved)
        with np.load(track(folder/'current_goal_DIP60.npz')) as saved:g=dict(saved)
        cases[u]['env0']=pre.trace_audit(t,metadata,config,rows,contract['action']['target_contract'],extra,arm,'policy')
        cases[u]['guard']=pre.guard_audit(g,rows,config['song']['short_learning']['view'])
        if 'unavailable' not in cases[u]['env0']:cases[u]['env0_motion']=phase_audit(t,g,config,contract['action']['target_contract'],metadata)
        payload=torch.load(track(probe.checkpoint(u)),map_location='cpu',weights_only=False);pins(payload['metadata']['input_pins'])
        assert payload['updates']==u and payload['metadata']['settings']==config and payload['identity']['architecture']['contract']==contract
        identities.append(payload['identity']);assert len(payload['model'])==73 and all(torch.isfinite(v).all() for v in payload['model'].values())
        heads.append(dict(update=u,cost_head={k:dict(nonzero=int(torch.count_nonzero(v)),max_abs=float(v.abs().max())) for k,v in payload['model'].items() if k.startswith('cost_critic.')}))
        if u==0:
            torch.manual_seed(7);fresh=extra.PrefixPolicy(contract=contract,size=config['size'],fresh=True)
            assert payload['identity']==DecisionPPOTrainer(fresh,PPOConfig(**config['ppo']))._identity()
            assert set(fresh.state_dict())==set(payload['model']) and all(torch.equal(v,payload['model'][k]) for k,v in fresh.state_dict().items())
            old=torch.load(track(probe.B.checkpoint(0)),map_location='cpu',weights_only=False)
            assert set(old['model'])==set(payload['model']) and all(torch.equal(v,old['model'][k]) for k,v in payload['model'].items())
            initialization=dict(new_expected73_exact=True,prior_B73_model_values_exact=True,cost2zero=all(not torch.count_nonzero(payload['model'][k]) for k in ('cost_critic.weight','cost_critic.bias')),scope='CPU model tensor comparison only; different task identity not strict-loaded; original seven native evaluators perform current strictfull-load; no CUDA RNG equality claim')
            assert initialization['cost2zero'];del old,fresh
        del payload
    assert len(attempts)==896 and len(notes)==2688 and all(v==identities[0] for v in identities)
    training_rows=[json.loads(s) for s in track(BASE/'train/episodes.jsonl').read_text().splitlines()]
    assert all(m['transitions']==4096 and m['total_transitions']==m['update']*4096 and m['cost_weight']==1 and m['diagnostics']['physical_transitions']==m['diagnostics']['valid_decisions']==4096 and set(m['reward_component_means'])==set(REWARD_TERMS) for m in metrics)
    assert all(0<=r['env_id']<128 and 1<=r['update']<=300 and r['selected_target_count']==len(r['notes'])==3 and set(r['reward_components'])==set(REWARD_TERMS) for r in training_rows)
    completed_steps=sum(r['steps'] for r in training_rows);assert completed_steps<=1228800
    training=dict(updates=300,raw_transitions=1228800,completed_episodes=len(training_rows),completed_note_opportunities=3*len(training_rows),completed_episode_steps=completed_steps,remaining_open_episode_steps=1228800-completed_steps,reason_counts=dict(Counter(r['reason'] for r in training_rows)),
        completed_physical_failures=sum(r['termination']['physical_failure'] for r in training_rows),completed_wrist_failures=sum(r['termination']['wrist_failure'] for r in training_rows),
        failures=[dict(line=i+1,episode=r) for i,r in enumerate(training_rows) if r['cost'] or r['termination']['physical_failure'] or r['termination']['wrist_failure']],
        raw_cost_sum=sum(m['mean_failure_cost']*4096 for m in metrics),completed_episode_cost_sum=sum(r['cost'] for r in training_rows),cost_heads=heads,
        immediate_cost_nonzero_updates=[m['update'] for m in metrics if m['mean_failure_cost']!=0],cost_GAE_nonzero_updates=[m['update'] for m in metrics if any(m['diagnostics']['advantages']['cost_raw'][k]!=0 for k in ('mean','std','min','max'))],
        cost_loss_nonzero_updates=[m['update'] for m in metrics if m['cost_value_loss']!=0],cost_critic_nonzero_updates=[m['update'] for m in metrics if m['diagnostics']['post_update']['critics']['cost']['mse']!=0 or any(m['diagnostics']['post_update']['critics']['cost'][k][j]!=0 for k in ('value','target') for j in ('mean','std','min','max'))],
        cost_EV_counts=dict(Counter(str(m['diagnostics']['post_update']['critics']['cost']['explained_variance']) for m in metrics)),
        reward_raw_transition_sums={k:sum(m['reward_component_means'][k]*4096 for m in metrics) for k in REWARD_TERMS},reward_completed_episode_sums={k:sum(r['reward_components'][k] for r in training_rows) for k in REWARD_TERMS})
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    track(Path(__file__));track(HERE/'PLAN.md');chosen=b.selection(cases);result=dict(cases=cases,criteria=criteria(cases),selection=chosen,training=training,initialization=initialization,precheck_reference_only=prior,scope='new conditional3note policy; noNN precheck not inherited as NN performance; source67/focus3 fixed guitar/128 same seed')
    out.mkdir();grid.write(out/'comparison.json',result);grid.write(out/'selection.json',chosen)
    metric_rows=[]
    for m in metrics:
        row={k:m[k] for k in ('update','total_transitions','mean_reward','mean_failure_cost','cost_value_loss','actor_lr','analytic_kl','max_attempted_kl','kl_retries')};row.update(m['reward_component_means']);row.update(b.flatten(m['diagnostics']['advantages'],'advantages.'));row.update(b.flatten(m['diagnostics']['post_update'],'post_update.'));metric_rows.append(row)
    for name,table in (('attempts.csv',attempts),('notes.csv',notes),('metrics300.csv',metric_rows)):
        with (out/name).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,stages=stages,policy_first_attempts=896,note_opportunities=2688,training_updates=300,raw_transitions=1228800,all_native128x105_cap90pairs=True,all_scenes_closed=True,reward_component_sum_max_abs_residual=max(abs(r['reward_sum_residual']) for r in attempts),limits=['env0 60Hz detail only; other127force/nativeqd/240Hz reconstructions unavailable','all completed/open transition denominators distinct','bodyforces not pairpressure; action sign not fullskin release','cost tensors CPUcomparison not relaxed strictload; no CUDA RNG equality','reference_N_injected=False currentNN scopes and actualselectedactions/codec checked; precheckreference success not NNscore']))
    lines=['# 검지 3음 정책 학습 실제 결과','', '| 반복 | 각음 달성률4/7/8 | all3 | A release | 음악/해제/AND | 물리/손목실패 |','|---|---|---:|---:|---|---|']
    for u in UPDATES:
        a=cases[u]['acceptance'];lines.append('| %d | %s | %.6f | %.6f | %s/%s/%s | %d/%d |'%(u,', '.join('%.6f'%n['achieved_fraction'] for n in a['per_note']),a['all3_achieved_fraction'],a['A_released_fraction'],a['music_passed'],a['release_passed'],a['stage_ready'],a['physical_failures'],a['wrist_failures']))
    lines+=['', '음악·해제·AND의 초기제외 인접2회 및200/250/300유지는 comparison.json의 criteria에 각각 기록했다. best=%d/latest300·영상후보%s이며 사전순위만 사용한다.'%(chosen['best_update'],chosen['video_updates']),
        '전체896평가·2688음과 완료학습%d episode/열린전이%d를 구분했다. 원9항을 음별 재분배하지 않았고 실제비용과 GAE/critic을 별도로 기록했다.'%(len(training_rows),training['remaining_open_episode_steps']),
        'env0 A→release→move→close→B 음/공유gap phase별 실제4각변화·목표gap·상하계체류·음수/양수 명령과 증분은 env0_motion에 있다. 부호를 실제 피부분리나 자연스러운 동작으로 해석하지 않는다. 상세힘·손목/CPU6gate·wrong은 env0에만 해당하고 미저장240Hz 재접촉이나 다른127힘은 추정하지 않는다.',
        '정책은 첫 tick부터 선택4축을 제어하고 reference N 일정은 주입하지 않았다. 저장policy/executed선택4·guard/codec와 새원계약을 대조했다. 참고128사전성공을 NN성과로 상속하지 않는다. bodyforce는pair압력·토크가 아니며 free guitar/J33/전곡·자연성·생산채택으로 확대하지 않는다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print('CPU 실제 분석 완료:',out)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group();g.add_argument('--self-check',action='store_true');g.add_argument('--root-completed',action='store_true');args=parser.parse_args()
    if args.self_check:self_check()
    elif args.root_completed:actual_main()
    else:print('준비만 완료: root 전체300+7평가 종료 전 actual 결과를 생성하지 않습니다.')
