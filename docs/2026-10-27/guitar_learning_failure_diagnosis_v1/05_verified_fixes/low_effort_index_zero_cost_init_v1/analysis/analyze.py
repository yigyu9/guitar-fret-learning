"""Prepared B analysis guard and preregistered criteria; no actual data reads yet."""
import argparse
from collections import Counter
import copy
import csv
import importlib.util
from pathlib import Path
import json
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
UPDATES=(0,50,100,150,200,250,300)
JOBS=('train',)+tuple('evaluate_%06d'%u for u in UPDATES)


def passed(summary):
    return (summary['achieved_fraction']>=.9 and summary['mean_clean_fraction']>=.9
        and summary['mean_audible_wrong_fraction']<=.1 and summary['physical_failure_fraction']==0
        and summary['wrist_failure_fraction']==0)


def acceptance(cases):
    trained=UPDATES[1:]
    pairs=[[a,b] for a,b in zip(trained,trained[1:]) if passed(cases[a]['summary']) and passed(cases[b]['summary'])]
    return dict(consecutive_music_pass=bool(pairs),passing_pairs=pairs,
        late_maintenance_pass=all(passed(cases[u]['summary']) for u in (200,250,300)),
        late_maintenance_updates=[200,250,300])


def selection(cases):
    def rank(u):
        c=cases[u];s=c['summary']
        return s['achieved_fraction'],s['mean_clean_fraction'],-s['mean_audible_wrong_fraction'],-c['physical_or_wrist_fraction'],u
    best=max(UPDATES,key=rank)
    return dict(best_update=best,latest_update=300,video_updates=sorted({best,300}))


def completed_launcher(launcher):
    if (launcher.get('completed') is not True or launcher.get('returncode')!=0
            or [c.get('job') for c in launcher.get('children',[])]!=list(JOBS)
            or any(c.get('returncode')!=0 for c in launcher.get('children',[]))):
        raise ValueError('Root actual eight-stage completion required')


def self_test():
    good=dict(achieved_fraction=.9,mean_clean_fraction=.9,mean_audible_wrong_fraction=.1,physical_failure_fraction=0.,wrist_failure_fraction=0.)
    def case(s=None):return dict(summary=dict(good if s is None else s),physical_or_wrist_fraction=0.)
    cases={u:case() for u in UPDATES};assert passed(good)
    assert acceptance(cases)['late_maintenance_pass'] and len(acceptance(cases)['passing_pairs'])==5
    assert selection(cases)==dict(best_update=300,latest_update=300,video_updates=[300])
    for key,value in (('achieved_fraction',.899),('mean_clean_fraction',.899),('mean_audible_wrong_fraction',.101),('physical_failure_fraction',1/128),('wrist_failure_fraction',1/128)):
        bad=dict(good);bad[key]=value;assert not passed(bad)
    for u in (200,250,300):
        late={v:case() for v in UPDATES};late[u]=case(dict(good,achieved_fraction=0.))
        assert not acceptance(late)['late_maintenance_pass']
    early={u:case(dict(good,achieved_fraction=0.)) for u in UPDATES}
    early[0]=case();early[50]=case();assert not acceptance(early)['consecutive_music_pass']
    cases[200]=case(dict(good,achieved_fraction=0.));assert acceptance(cases)['consecutive_music_pass']
    cases[150]=case(dict(good,achieved_fraction=1.));assert selection(cases)['video_updates']==[150,300]
    for new,old in (({'a':2,'cost_critic.weight':0,'cost_critic.bias':0},{'a':1,'cost_critic.weight':2,'cost_critic.bias':3}),
                    ({'a':1,'cost_critic.weight':1,'cost_critic.bias':0},{'a':1,'cost_critic.weight':2,'cost_critic.bias':3})):
        try:state_comparison(new,old,lambda a,b:a==b,lambda v:v==0)
        except AssertionError:pass
        else:raise AssertionError('Invalid B state comparison admitted')
    for key,value in (('achieved_fraction',.91),('mean_clean_fraction',.91),('mean_audible_wrong_fraction',.09)):
        tied={u:case() for u in UPDATES};tied[50]['summary'][key]=value;assert selection(tied)['best_update']==50
    tied={u:case() for u in UPDATES};tied[300]['physical_or_wrist_fraction']=1/128;assert selection(tied)['best_update']==250
    old_read=Path.read_text
    def unfinished(path,*args,**kwargs):
        assert path==BASE/'02_train_eval_launcher.json'
        return json.dumps(dict(completed=False,returncode=None,children=[]))
    Path.read_text=unfinished
    try:
        try:actual_main()
        except ValueError:pass
        else:raise AssertionError('Actual main bypassed incomplete launcher')
    finally:Path.read_text=old_read
    launcher=dict(completed=True,returncode=0,children=[dict(job=j,returncode=0) for j in JOBS]);completed_launcher(launcher)
    bads=[dict(launcher,completed=False),dict(launcher,returncode=1),dict(launcher,children=launcher['children'][:-1]),
        dict(launcher,children=list(reversed(launcher['children']))),dict(launcher,children=[dict(c,returncode=1) if i==2 else c for i,c in enumerate(launcher['children'])])]
    for bad in bads:
        try:completed_launcher(bad)
        except ValueError:pass
        else:raise AssertionError('Invalid launcher accepted')
    assert state_comparison({'a':1,'cost_critic.weight':0,'cost_critic.bias':0},{'a':1,'cost_critic.weight':2,'cost_critic.bias':3},lambda a,b:a==b,lambda v:v==0)==dict(state_tensor_count=3,equal_original_state_tensors=1,changed_state_names=['cost_critic.bias','cost_critic.weight'],cost_parameters_exact_zero=True)
    assert not any(m.split('.')[0] in ('torch','numpy','isaacgym') for m in sys.modules)
    return dict(CPU_only=True,actual_raw_model_read=False,criteria_and_completion_guard=True,
        whole_fixed_evaluation_denominator=896,training_raw_transitions=1228800)


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m


def state_comparison(new,old,equal,zero):
    assert set(new)==set(old)
    changed=sorted(k for k in new if not equal(new[k],old[k]))
    assert changed==['cost_critic.bias','cost_critic.weight']
    assert all(zero(new[k]) for k in changed)
    return dict(state_tensor_count=len(new),equal_original_state_tensors=len(new)-2,changed_state_names=changed,cost_parameters_exact_zero=True)


def flatten(value,prefix=''):
    result={}
    for k,v in value.items():
        key=prefix+k
        if isinstance(v,dict):result.update(flatten(v,key+'.'))
        elif isinstance(v,(float,int)) or v is None:result[key]=v
    return result


def actual_main():
    # This first read is stdlib only; unfinished eight-stage launcher blocks every
    # producer import, checkpoint/log read, numerical dependency and output write.
    launcher_path=BASE/'02_train_eval_launcher.json'
    launcher=json.loads(launcher_path.read_text());completed_launcher(launcher)
    probe=module('B_actual_analysis_probe',BASE/'probe.py');grid=probe.grid
    sys.path.insert(0,str(grid.ROOT));out=HERE/'results_v1';probe.cap.reject_existing(out)
    inputs,verified={},{}
    def track(p):p=Path(p);inputs[str(p.resolve())]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(mapping):
        for p,h in mapping.items():
            if p not in verified:verified[p]=grid.sha(p)
            assert verified[p]==h,p
    track(launcher_path);seal,paths=probe.gate('train')
    assert len(seal['input_pins'])==1267; pins(seal['input_pins'])
    for p in paths:track(p)
    original=module('B_frozen_baseline_analysis',probe.BASE/'learning_analysis/analyze.py')
    helper=module('B_frozen_arm_analysis',probe.BASE/'precheck_analysis/analyze.py')
    trace_helper=module('B_frozen_trace_analysis',helper.HELPER)
    for p in (Path(original.__file__),Path(helper.__file__),Path(trace_helper.__file__),Path(__file__),HERE/'PLAN.md'):track(p)
    prior=read(probe.BASE/'learning_analysis/results_v1/comparison.json')
    prior_metrics=[json.loads(x) for x in track(probe.BASE/'train/metrics.jsonl').read_text().splitlines()]
    config=read(BASE/'cpu_inputs/settings.json');assert config==read(probe.BASE/'cpu_inputs/settings.json')
    declaration=read(BASE/'cpu_inputs/effort_declaration128.json');descriptor=read(BASE/'cpu_inputs/initialization.json')
    assert descriptor==probe.variants.descriptor(probe.VARIANT)
    cpu_init=read(BASE/'cpu_verification.json')['initialization']
    assert cpu_init['state_tensor_count']==73 and cpu_init['equal_original_state_tensors']==71 and cpu_init['cost_parameters_exact_zero']
    assert all(cpu_init[k] for k in ('RNG_and_actor_reward_exact','initial_std_exact','optimizer_config_and_grouping_exact','baseline_actual_initial73_exact'))
    commands=read(BASE/'cpu_inputs/commands.json');expected_commands=[commands['train']]+commands['evaluate']
    assert [c['argv'] for c in launcher['children']]==expected_commands
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    metadata,_=fixture(1);cases={};attempts=[];phases=[];stage_checks=[];identities=[];heads=[]
    baseline_contract=read(probe.BASE/'train/training_contract.json');expected_contract=copy.deepcopy(baseline_contract);probe.tag(expected_contract)
    for job in JOBS:
        train=job=='train';u=0 if train else int(job.split('_')[1]);folder=probe.output('train' if train else 'evaluate',update=u)
        child=read(BASE/('02_'+job+'_launcher.json'));parent=next(c for c in launcher['children'] if c['job']==job)
        assert child['job']==job and child['argv']==parent['argv'] and child['returncode']==0
        assert read(folder/'settings.json')==config
        report=read(folder/'report.json');diag=read(folder/'diagnostic_report.json');z=read(folder/'zero_cost_diagnostic.json');scene=read(folder/'gpu_scene_final.json')
        assert report['completed'] and report['closed'] and report['failure'] is None and not report['changed_inputs'] and not report['unpinned_project_sources']
        assert all(diag[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored')) and diag['failure'] is None and not diag['cleanup_errors']
        assert not diag['changed_inputs'] and not diag['unpinned_project_sources'] and diag['native_environment_count']==128
        assert all(z[k] for k in ('completed','base_aliases_restored','initialization_aliases_restored','initialization_contract_tagged','original_diagnostic_report_preserved'))
        assert z['failure'] is None and z['variant']==probe.VARIANT and z['fresh_initialization']==train
        init_decl=read(folder/'initialization_declaration.json');assert init_decl['descriptor']==descriptor and init_decl['fresh']==train
        assert scene['closed'] and scene['environment_count']==128 and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and scene['diagnostic_guitar_mode']=='fixed'
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
        assert scene['physics_steps']==diag['physics_steps'] and (scene['physics_steps']==38400 if train else scene['physics_steps']<=4*config['song']['short_learning']['view']['duration_ticks'])
        assert read(folder/'native_effort_readback.json')==declaration
        contract=read(folder/'training_contract.json');assert contract==expected_contract
        before=read(folder/'inputs_before.json');pins(before)
        for name in ('inputs_after.json','diagnostic_inputs_after.json'):
            after=read(folder/name);assert after['verified'] and after['input_pins']==before and not after['changed_paths'] and not after['unpinned_project_sources']
        stage_checks.append(dict(job=job,source_pins=len(before),closed=True,physics_steps=scene['physics_steps'],native128cap_exact=True,B_tag_and_fresh_scope=True))
        if train:continue
        evaluation=read(folder/'evaluation.json');es=evaluation['episodes']
        assert evaluation['condition']=='policy' and evaluation['policy_performance'] is True and evaluation['assigned_quotas']==[1]*128 and grid.complete(es,128)
        assert evaluation['summary']==runner.summary(es)
        either=sum(e['termination']['physical_failure'] or e['termination']['wrist_failure'] for e in es)/128
        cases[u]=dict(update=u,summary=evaluation['summary'],physical_or_wrist_fraction=either,passed=original.passed(evaluation['summary']))
        assert cases[u]['passed']==passed(evaluation['summary'])
        for e in es:
            assert e['selected_target_count']==1 and e['target_id']==config['song']['short_learning']['teacher']['source_target_id'] and set(e['reward_components'])==set(original.TERMS)
            attempts.append(dict(update=u,env_id=e['env_id'],achieved=e['achieved'],clean=e['clean_fraction'],wrong=e['audible_wrong_fraction'],physical_failure=e['termination']['physical_failure'],wrist_failure=e['termination']['wrist_failure'],reason=e['reason'],reward=e['reward'],cost=e['cost'],**e['reward_components'],angles=json.dumps(e['angles']),note=json.dumps(e['note'])))
        meta=read(folder/'trace_metadata.json');assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
        t=dict(np.load(track(folder/'trace_env0_episode0.npz')));trace=trace_helper.trace_audit(t,metadata,config,es,'policy',contract['action']['target_contract'])
        cases[u]['env0_trace']=trace
        if 'unavailable_reason' not in trace:
            cases[u]['env0_arm']=helper.arm_audit(t,meta,config,contract['action']['target_contract'])
            ctl=contract['action']['target_contract'];names=config['song']['short_learning']['learned_action_names'];qids=[metadata['joint_names'].index(n) for n in names];ai=[ctl['action_order'].index(n) for n in names]
            lo=np.asarray(ctl['action_lower_rad'])[ai];hi=np.asarray(ctl['action_upper_rad'])[ai];target=t['target'][:,qids];actual=t['q'][:,qids];joint=[]
            source=config['song']['short_learning']['view']['source_target'];audible=grid.phase_masks(t['source_time_s'],source['onset_s'],source['end_s'])[1]
            for i,n in enumerate(names):
                ids=np.flatnonzero(target[:,i]>=hi[i]-1e-6)
                joint.append(dict(name=n,upper_deg=float(np.rad2deg(hi[i])),first_upper_local_s=float(t['time_s'][ids[0]]) if len(ids) else None,first_upper_source_s=float(t['source_time_s'][ids[0]]) if len(ids) else None,upper_count=int(len(ids)),audible_upper_count=int((target[audible,i]>=hi[i]-1e-6).sum()),audible_actual_at_upper_count=int((actual[audible,i]>=hi[i]-1e-6).sum()),lower_deg=float(np.rad2deg(lo[i])),audible_lower_count=int((target[audible,i]<=lo[i]+1e-6).sum()),audible_actual_at_lower_count=int((actual[audible,i]<=lo[i]+1e-6).sum())))
            cases[u]['env0_selected_target_upper']=joint
        for phase,v in trace['phases'].items():phases.append(dict(update=u,phase=phase,**v,arm=cases[u].get('env0_arm',{}).get('phases',{}).get(phase)))
        payload=torch.load(track(probe.checkpoint(u)),map_location='cpu',weights_only=False)
        assert payload['updates']==u and payload['metadata']['settings']==config and payload['identity']['architecture']['contract']==contract
        pins(payload['metadata']['input_pins']);identities.append(payload['identity'])
        assert all(torch.isfinite(v).all() for v in payload['model'].values())
        heads.append(dict(update=u,parameters={k:dict(nonzero=int(torch.count_nonzero(v)),max_abs=float(v.abs().max()),l2=float(v.double().norm())) for k,v in payload['model'].items() if k.startswith('cost_critic.')}))
        if u==0:
            torch.manual_seed(7);fresh=probe.variants.policy_type(probe.VARIANT,fresh=True)(contract=contract,size=config['size'])
            expected_identity=DecisionPPOTrainer(fresh,PPOConfig(**config['ppo']))._identity()
            assert payload['identity']==expected_identity and len(payload['model'])==73 and set(payload['model'])==set(fresh.state_dict())
            assert all(torch.equal(v,payload['model'][k]) for k,v in fresh.state_dict().items())
            old_path=probe.BASE/'train/initial.pt';old=torch.load(track(old_path),map_location='cpu',weights_only=False)
            init=state_comparison(payload['model'],old['model'],torch.equal,lambda v:not torch.count_nonzero(v))
            assert init==probe.initial_comparison(payload['model'],old['model']) and init['state_tensor_count']==73 and init['equal_original_state_tensors']==71
            saved=read(BASE/'train/initial_model_comparison.json')
            for k,v in init.items():assert saved[k]==v
            assert saved['new_initial']==str(probe.checkpoint(0)) and saved['new_initial_sha256']==grid.sha(probe.checkpoint(0))
            assert saved['baseline_initial']==str(old_path) and saved['baseline_initial_sha256']==grid.sha(old_path)
            initialization=dict(B_expected73_exact=True,baseline71_exact_and_cost2zero=init,CPU_model_only=True,native_strict_full_load='original evaluator seven scenes; no CPU CUDA-RNG full load bypass')
            del old
        del payload
    assert len(attempts)==896 and len(stage_checks)==8 and all(x==identities[0] for x in identities)
    metrics=[json.loads(x) for x in track(BASE/'train/metrics.jsonl').read_text().splitlines()]
    episodes=[json.loads(x) for x in track(BASE/'train/episodes.jsonl').read_text().splitlines()]
    assert [m['update'] for m in metrics]==list(range(1,301)) and all(m['transitions']==4096 and m['total_transitions']==4096*m['update'] and m['cost_weight']==1 for m in metrics)
    assert all(m['diagnostics']['physical_transitions']==4096 and m['diagnostics']['valid_decisions']==4096 and set(m['reward_component_means'])==set(original.TERMS) for m in metrics)
    assert all(0<=e['env_id']<128 and 1<=e['update']<=300 and set(e['reward_components'])==set(original.TERMS) for e in episodes)
    training=dict(updates=300,raw_transitions=1228800,global_control_ticks=9600,physics_steps=38400,completed_episodes=len(episodes),remaining_open_episode_steps=1228800-sum(e['steps'] for e in episodes),reason_counts=dict(Counter(e['reason'] for e in episodes)),
        failures=[dict(line=i+1,episode=e) for i,e in enumerate(episodes) if e['cost'] or e['termination']['physical_failure'] or e['termination']['wrist_failure']],
        cost_signal=dict(immediate_nonzero_updates=[m['update'] for m in metrics if m['mean_failure_cost']!=0],GAE_nonzero_updates=[m['update'] for m in metrics if any(m['diagnostics']['advantages']['cost_raw'][k]!=0 for k in ('mean','std','min','max'))],loss_nonzero_updates=[m['update'] for m in metrics if m['cost_value_loss']!=0]),
        raw_cost_sum=sum(m['mean_failure_cost']*m['transitions'] for m in metrics),completed_episode_cost_sum=sum(e['cost'] for e in episodes),checkpoints_cost_heads=heads,
        completed_episode_steps=sum(e['steps'] for e in episodes),
        cost_critic_nonzero_updates=[m['update'] for m in metrics if m['diagnostics']['post_update']['critics']['cost']['mse']!=0 or any(m['diagnostics']['post_update']['critics']['cost'][k][v]!=0 for k in ('value','target') for v in ('mean','std','min','max'))],
        cost_critic_EV_counts=dict(Counter(str(m['diagnostics']['post_update']['critics']['cost']['explained_variance']) for m in metrics)),
        KL_retry_updates=[m['update'] for m in metrics if m['kl_retries']],actor_LR_changes=[dict(update=m['update'],actor_lr=m['actor_lr']) for i,m in enumerate(metrics) if i==0 or m['actor_lr']!=metrics[i-1]['actor_lr']],
        reward_component_raw_transition_sums={k:sum(m['reward_component_means'][k]*m['transitions'] for m in metrics) for k in original.TERMS},
        reward_component_completed_episode_sums={k:sum(e['reward_components'][k] for e in episodes) for k in original.TERMS})
    assert training['remaining_open_episode_steps']>=0
    chosen=selection(cases);assert chosen['best_update']==max(cases.values(),key=original.rank)['update']
    metric_rows=[]
    for m in metrics:
        row={k:m[k] for k in ('update','total_transitions','mean_reward','mean_failure_cost','cost_value_loss','actor_lr','analytic_kl','max_attempted_kl','kl_retries')}
        row.update(m['reward_component_means']);row['reward_component_mean_residual']=m['mean_reward']-sum(m['reward_component_means'].values())
        row.update(flatten(m['diagnostics']['advantages'],'advantages.'));row.update(flatten(m['diagnostics']['post_update'],'post_update.'));metric_rows.append(row)
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    out.mkdir();comparison=dict(cases=cases,acceptance=acceptance(cases),selection=chosen,training=training,initialization=initialization,
        baseline_cases=prior['cases'],baseline_training=prior['training'],baseline_acceptance=prior['acceptance'],baseline_late_maintenance_pass=all(passed(prior['cases'][str(u)]['summary']) for u in (200,250,300)),
        noNN_precheck_random=prior['noNN_precheck_random'],comparison_scope='same seed/settings/PPO/physics and fresh71 exact, only two initial cost tensors zero plus explicit tag/source pins; one controlled run, not multi-seed causal proof')
    grid.write(out/'comparison.json',comparison)
    policy_rows=[dict(update=u,passed=cases[u]['passed'],physical_or_wrist_fraction=cases[u]['physical_or_wrist_fraction'],**cases[u]['summary']) for u in UPDATES]
    for name,table in (('performance.csv',policy_rows),('attempts.csv',attempts),('metrics300.csv',metric_rows),('env0_tracking.csv',phases)):
        if table:
            with (out/name).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    plot(out,cases,prior,metrics,prior_metrics,original.TERMS)
    write_report(out,comparison)
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,stages=stage_checks,policy_first_attempts=896,training_updates=300,raw_transitions=1228800,
        initialization=initialization,acceptance=acceptance(cases),selection=chosen,source_contract_difference='exact original B descriptor only; settings exact baseline',
        env0_candidate_wrong_mismatches={u:cases[u]['env0_trace'].get('candidate_wrong_mismatches',[]) for u in UPDATES},
        env0_nearest_height_residuals_over_1um={u:cases[u]['env0_trace'].get('height_residuals_over_1um',[]) for u in UPDATES},
        limits=['whole128 ledgers vsenv0 60Hz detailedforce; not128seeds','cost signal vsGAE/critic separated; positive failure costs retained','nearest scalar notanysample witness; CPUgates not240Hz ledger replay','Bexpected73 vsbaseline71+2zero; no CPU relaxed strictfull-load','no naturalness/release/transition/freeguitar/J33 certification']))
    print('B actual CPU results written:',out)


def plot(out,cases,prior,metrics,prior_metrics,terms):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(11,3))
    for ax,key,label,threshold in zip(axes,('achieved_fraction','mean_clean_fraction','mean_audible_wrong_fraction'),('Achieved','Clean','Wrong'),(.9,.9,.1)):
        ax.plot(UPDATES,[cases[u]['summary'][key] for u in UPDATES],'o-',label='B cost head zero init')
        ax.plot(UPDATES,[prior['cases'][str(u)]['summary'][key] for u in UPDATES],'o--',label='baseline')
        ax.axhline(threshold,color='gray',ls=':');ax.set(title=label,xlabel='update',ylim=(-.02,1.03))
    axes[0].legend(fontsize=7);fig.tight_layout();fig.savefig(out/'performance.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(3,3,figsize=(12,8))
    for ax,key in zip(axes.flat,terms):
        ax.plot(range(1,301),[m['reward_component_means'][key] for m in metrics],label='B')
        ax.plot(range(1,301),[m['reward_component_means'][key] for m in prior_metrics],alpha=.6,label='baseline');ax.set(title=key,xlabel='update')
    axes.flat[0].legend();fig.tight_layout();fig.savefig(out/'rewards9.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(10,6))
    for label,data,style in (('B',metrics,'-'),('baseline',prior_metrics,'--')):
        axes[0,0].plot(range(1,301),[m['diagnostics']['advantages']['cost_raw']['std'] for m in data],style,label=label)
        axes[0,1].plot(range(1,301),[m['cost_value_loss'] for m in data],style,label=label)
    axes[0,0].set(title='Cost GAE std',xlabel='update');axes[0,1].set(title='Cost value loss',xlabel='update')
    for ax,j,name in ((axes[1,0],2,'PIP'),(axes[1,1],3,'DIP')):
        for label,data,style in (('B',cases,'-'),('baseline',{u:prior['cases'][str(u)] for u in UPDATES},'--')):
            def value(u,k):
                m=data[u]['env0_trace']['phases'].get('audible',{}).get('metric_mean');return m[k] if m else float('nan')
            ax.plot(UPDATES,[value(u,j) for u in UPDATES],style,label=label+' actual')
            ax.plot(UPDATES,[value(u,4+j) for u in UPDATES],style,alpha=.5,label=label+' target')
        ax.set(title='env0 audible '+name+' degrees',xlabel='update')
    for ax in axes.flat:ax.legend(fontsize=6)
    fig.tight_layout();fig.savefig(out/'cost_and_tracking.png',dpi=150);plt.close(fig)


def write_report(out,c):
    lines=['# B 비용 head 0 초기화: 실제 비교','',
        'B의 전체7평가 달성수는 %s/128이다. 기존 연속 기준과 후반 유지기준을 아래에서 별도로 보고한다.'%str([round(c['cases'][u]['summary']['achieved_fraction']*128) for u in UPDATES]),'',
        '이 비교는 원 검지 seed7 설정/physics/PPO를 유지하고 fresh cost head 두 tensor만0으로 시작한 B다. B expected73과 baseline71exact+cost2zero를 각각 확인했다. 단일 seed의 통제 대조이며 자연성이나 보편 인과를 인증하지 않는다.','',
        '| update | baseline 달성/128 | B 달성/128 | B clean/wrong | B 물리/손목실패 | B 단일기준 |','|---:|---:|---:|---|---|---|']
    for u in UPDATES:
        a=c['baseline_cases'][str(u)]['summary'];b=c['cases'][u]['summary'];lines.append('| %d | %d | %d | %.6f / %.6f | %.6f / %.6f | %s |'%(u,round(a['achieved_fraction']*128),round(b['achieved_fraction']*128),b['mean_clean_fraction'],b['mean_audible_wrong_fraction'],b['physical_failure_fraction'],b['wrist_failure_fraction'],c['cases'][u]['passed']))
    lines+=['','원 연속2음악기준: %s, 통과쌍%s. 별도후반유지(200/250/300 모두원단일기준): %s; baseline후반유지는%s.'%(c['acceptance']['consecutive_music_pass'],c['acceptance']['passing_pairs'],c['acceptance']['late_maintenance_pass'],c['baseline_late_maintenance_pass']),
        'best=%d/latest300, 영상후보%s. 전체7평가/896첫시도와실패를포함했다. noNN precheck random31/128은재사용자료이며 NN initial과다르고 새384실행처럼합산하지않는다.'%(c['selection']['best_update'],c['selection']['video_updates']),'',
        '전체300회/1,228,800 raw전이·종료episode%d·남은open전이%d. 실제비용nonzero update%d회, 실패/cost episode%d건; costGAE/loss nonzero는%d/%d회다. 실제비용합%.9g/완료episode비용합%.9g를구분한다. truefailure이후학습을허위비용으로부르지않으며 원costhead는계속학습가능하다.'%(c['training']['completed_episodes'],c['training']['remaining_open_episode_steps'],len(c['training']['cost_signal']['immediate_nonzero_updates']),len(c['training']['failures']),len(c['training']['cost_signal']['GAE_nonzero_updates']),len(c['training']['cost_signal']['loss_nonzero_updates']),c['training']['raw_cost_sum'],c['training']['completed_episode_cost_sum']),'',
        '| B update | env0 음중끝점 | actual4° | target4° | 몸체1/2/3평균N | 손목mm/° | CPU6gate |','|---:|---:|---|---|---|---|---|']
    fmt=lambda xs:', '.join('%.4f'%x for x in xs)
    for u in UPDATES:
        p=c['cases'][u]['env0_trace']['phases'].get('audible',{});m=p.get('metric_mean');lines.append('| %d | %d | %s | %s | %s | %s | %s |'%(u,p.get('samples',0),fmt(m[:4]) if m else '미확인',fmt(m[4:8]) if m else '미확인',fmt(m[12:15]) if m else '미확인',fmt(m[15:17]) if m else '미확인',p.get('CPU_gate_counts')))
    lines+=['','cost critic value/target의 mean·std·min·max 또는MSE nonzero는%d/300회이며 EV기록은%s다. target분산0의EV None을성능값0으로바꾸지않는다. 7저장본head값은comparison에모두보존했고 평가fresh=False/strict복원경로를확인했다. baseline은실제비용0인데GAE/loss가300회nonzero였으며 B의비용추정경로차이와음악유지는이번조건의통제대조관찰이다.'%(len(c['training']['cost_critic_nonzero_updates']),str(c['training']['cost_critic_EV_counts'])),
        'B의KL재시도update는%s,LR변경은%s다. cost초기화개입후같은seed설정에서후반퇴행이재현됐는지는전체표로판단하며 다른seed/조건의단일원인으로일반화하지않는다.'%(str(c['training']['KL_retry_updates']),str(c['training']['actor_LR_changes'])),'',
        '| 후반update | baseline PIP actual/target° | B PIP actual/target° | baseline DIP actual/target° | B DIP actual/target° | B target4 상한/하한 음중끝점 |',
        '|---:|---|---|---|---|---|']
    for u in (200,250,300):
        a=c['baseline_cases'][str(u)]['env0_trace']['phases'].get('audible',{}).get('metric_mean');b=c['cases'][u]['env0_trace']['phases'].get('audible',{}).get('metric_mean');bounds=c['cases'][u].get('env0_selected_target_upper',[])
        lines.append('| %d | %s | %s | %s | %s | %s |'%(u,fmt([a[2],a[6]]) if a else '미확인',fmt([b[2],b[6]]) if b else '미확인',fmt([a[3],a[7]]) if a else '미확인',fmt([b[3],b[7]]) if b else '미확인',str([(j['audible_upper_count'],j['audible_lower_count']) for j in bounds])))
    last=c['cases'][300]['env0_trace']['phases'].get('audible',{}).get('metric_mean')
    if last:
        lines+=['','B300 env0음중 PIP actual%.5f°/target%.5f°(차%.5f°), DIP actual%.5f°/target%.5f°다. MCPz target%.5f°이며 몸체3합력평균%.5fN·손목평균%.5fmm/%.5f°가남는다. 음악기준유지가큰목표추종차이·마지막관절극단굴곡을해결했다는뜻은아니다. 상한/하한분류1e−6rad는보고수치허용이며성공문턱변경0이다.'%(last[2],last[6],last[10],last[3],last[7],last[5],last[14],last[15],last[16])]
    lines+=['','선택4상한최초시각/팔bounds·request/target/actual은comparison.json, 전체128원9보상·각도원장은attempts.csv,300회advantage/critic/value/target/MSE/EV·entropy/ratio/KL/LR는metrics300.csv에보존했다. 후반PIP/DIP 목표와실제차이를 비용추정결과와별개로읽어야한다.','',
        'env0은사전고정첫시도의60Hz끝점이며나머지127의힘/기하원인을대변하지않는다. 몸체합력은압력·접촉쌍·모터torque·240Hz극값이아니다. nearest잔차/CPUcandidatewrong불일치는verification에그대로남기며원음원장을재분류하지않는다. 미노출·비유한trace는미확인으로남긴다.','',
        '원native105/16cap/90pairs·8scene닫기·실제strict평가/입력SHA/alias·Btag를검증했다. CPU에서는model-only73/71/2비교와identity를확인했으며 CUDA RNG full-load를우회하거나학습을재개하지않았다. 고정기타단음결과를해제/다음음/자유기타/J33 성과로확대하지않는다.','',
        '![고정평가](performance.png)','![원9보상](rewards9.png)','![비용과추종](cost_and_tracking.png)']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group()
    group.add_argument('--self-test',action='store_true');group.add_argument('--root-completed',action='store_true');args=parser.parse_args()
    if args.self_test:print(json.dumps(self_test()));return
    if args.root_completed:actual_main();return
    print('Prepared only. No raw/model read or results generated; wait for root full eight-stage completion.')


if __name__=='__main__':main()
