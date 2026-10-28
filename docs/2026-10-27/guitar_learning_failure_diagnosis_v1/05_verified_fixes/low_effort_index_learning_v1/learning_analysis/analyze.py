"""Prepared CPU analysis of fresh300 plus seven fixed128 evaluations; no live reads."""
import argparse
from collections import Counter
import copy
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
spec=importlib.util.spec_from_file_location('index_learning_analysis_probe',BASE/'probe.py')
probe=importlib.util.module_from_spec(spec);sys.modules[spec.name]=probe;spec.loader.exec_module(probe)
grid=probe.grid
UPDATES=probe.UPDATES
TERMS=('song_left_approach','song_left_contact','song_clean_hold','song_left_success','song_wrong_press',
    'song_performance_deficit','song_finger_standby','song_thumb_support','action_change')


def passed(summary):
    return (summary['achieved_fraction']>=.9 and summary['mean_clean_fraction']>=.9 and summary['mean_audible_wrong_fraction']<=.1
        and summary['physical_failure_fraction']==0 and summary['wrist_failure_fraction']==0)


def rank(case):
    s=case['summary']
    return s['achieved_fraction'],s['mean_clean_fraction'],-s['mean_audible_wrong_fraction'],-case['physical_or_wrist_fraction'],case['update']


def self_test():
    s=dict(achieved_fraction=.9,mean_clean_fraction=.9,mean_audible_wrong_fraction=.1,physical_failure_fraction=0.,wrist_failure_fraction=0.)
    assert passed(s)
    for k,v in (('achieved_fraction',.899),('mean_clean_fraction',.899),('mean_audible_wrong_fraction',.101),('physical_failure_fraction',1/128),('wrist_failure_fraction',1/128)):
        bad=dict(s);bad[k]=v;assert not passed(bad)
    a=dict(update=50,summary=s,physical_or_wrist_fraction=0.)
    b=copy.deepcopy(a);b['update']=300;assert rank(b)>rank(a)
    for key,value in (('achieved_fraction',.901),('mean_clean_fraction',.901),('mean_audible_wrong_fraction',.099)):
        b=copy.deepcopy(a);b['summary'][key]=value;assert rank(b)>rank(a)
    b=copy.deepcopy(a);b['physical_or_wrist_fraction']=1/128;assert rank(a)>rank(b)
    return dict(CPU_only=True,actual_raw_read=False,threshold_and_preregistered_rank_checked=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group()
    group.add_argument('--root-completed',action='store_true');group.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:print(json.dumps(self_test()));return
    if not args.root_completed:print('Prepared only; no actual train/evaluation raw read. Wait for root full8stage exit.');return
    sys.path.insert(0,str(grid.ROOT));out=HERE/'results_v1';probe.cap.reject_existing(out)
    inputs,verified={},{}
    def track(path):path=Path(path);inputs[str(path)]=grid.sha(path);return path
    def read(path):return grid.read(track(path))
    def jsonl(path):return [json.loads(line) for line in track(path).read_text().splitlines()]
    def pins(mapping):
        for p,h in mapping.items():
            if p not in verified:verified[p]=grid.sha(p)
            assert verified[p]==h,p
    seal,paths=probe.gate('train')
    for p in paths:track(p)
    pins(seal['input_pins']);assert len(seal['input_pins'])==1075
    launcher=read(BASE/'02_train_eval_launcher.json');jobs=['train']+['evaluate_%06d'%u for u in UPDATES]
    assert launcher['completed'] and launcher['returncode']==0 and [c['job'] for c in launcher['children']]==jobs and all(c['returncode']==0 for c in launcher['children'])
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    hspec=importlib.util.spec_from_file_location('frozen_precheck_analysis',BASE/'precheck_analysis/analyze.py')
    helper=importlib.util.module_from_spec(hspec);hspec.loader.exec_module(helper);track(BASE/'precheck_analysis/analyze.py')
    tspec=importlib.util.spec_from_file_location('frozen_prelearning_trace',helper.HELPER)
    trace_helper=importlib.util.module_from_spec(tspec);tspec.loader.exec_module(trace_helper);track(helper.HELPER)
    metadata,_=fixture(1);config=read(BASE/'cpu_inputs/settings.json');native_expected=read(BASE/'cpu_inputs/effort_declaration128.json')
    precheck=read(BASE/'precheck_analysis/results_v1/comparison.json')
    cases={};evaluation_rows=[];all_attempts=[];phase_rows=[];stage_checks=[];identities=[];cost_heads=[]
    for job in jobs:
        stage='train' if job=='train' else 'evaluate';update=0 if stage=='train' else int(job.split('_')[1])
        folder=probe.output(stage,None,update)
        child=read(BASE/('02_'+job+'_launcher.json'));assert child['job']==job and child['returncode']==0
        assert read(folder/'settings.json')==config
        report=read(folder/'report.json');diag=read(folder/'diagnostic_report.json');scene=read(folder/'gpu_scene_final.json')
        assert report['completed'] and report['closed'] and report['failure'] is None and not report['changed_inputs'] and not report['unpinned_project_sources']
        assert all(diag[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored')) and diag['failure'] is None and not diag['cleanup_errors']
        assert not diag['changed_inputs'] and not diag['unpinned_project_sources'] and diag['native_environment_count']==128
        assert scene['closed'] and scene['environment_count']==128 and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and scene['diagnostic_guitar_mode']=='fixed'
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
        assert scene['physics_steps']==diag['physics_steps'] and (scene['physics_steps']==38400 if stage=='train' else scene['physics_steps']<=4*config['song']['short_learning']['view']['duration_ticks'])
        native=read(folder/'native_effort_readback.json');assert native==native_expected
        contract=read(folder/'training_contract.json');assert contract['native_backend']['diagnostic_native_effort']==native and contract['task']['short_learning']==config['song']['short_learning']
        before=read(folder/'inputs_before.json');pins(before)
        for name in ('inputs_after.json','diagnostic_inputs_after.json'):
            after=read(folder/name);assert after['verified'] and after['input_pins']==before and not after['changed_paths'] and not after['unpinned_project_sources']
        stage_checks.append(dict(job=job,source_pins=len(before),closed=True,physics_steps=scene['physics_steps'],native128cap_exact=True))
        if stage=='train':continue
        result=read(folder/'evaluation.json');episodes=result['episodes'];assert result['condition']=='policy' and result['policy_performance'] is True
        assert result['assigned_quotas']==[1]*128 and grid.complete(episodes,128) and result['summary']==runner.summary(episodes)
        either=sum(e['termination']['physical_failure'] or e['termination']['wrist_failure'] for e in episodes)/128
        row=dict(update=update,summary=result['summary'],physical_or_wrist_fraction=either,passed=passed(result['summary']))
        evaluation_rows.append(row)
        for e in episodes:
            assert e['selected_target_count']==1 and e['target_id']==config['song']['short_learning']['teacher']['source_target_id'] and set(e['reward_components'])==set(TERMS)
            all_attempts.append(dict(update=update,env_id=e['env_id'],achieved=e['achieved'],clean=e['clean_fraction'],wrong=e['audible_wrong_fraction'],physical_failure=e['termination']['physical_failure'],
                wrist_failure=e['termination']['wrist_failure'],reason=e['reason'],reward=e['reward'],cost=e['cost'],**e['reward_components'],angles=json.dumps(e['angles']),note=json.dumps(e['note'])))
        meta=read(folder/'trace_metadata.json');assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
        t=dict(np.load(track(folder/'trace_env0_episode0.npz')))
        trace=trace_helper.trace_audit(t,metadata,config,episodes,'policy',contract['action']['target_contract'])
        arm=helper.arm_audit(t,meta,config,contract['action']['target_contract'])
        for phase,values in trace['phases'].items():phase_rows.append(dict(update=update,phase=phase,**values,arm=arm['phases'][phase]))
        cases[str(update)]=dict(**row,episodes=episodes,env0_trace=trace,env0_arm=arm)
        payload=torch.load(track(probe.checkpoint(update)),map_location='cpu',weights_only=False)
        assert payload['updates']==update and payload['metadata']['settings']==config
        pins(payload['metadata']['input_pins']);identities.append(payload['identity'])
        assert payload['identity']['architecture']['contract']==contract and all(torch.isfinite(v).all() for v in payload['model'].values())
        cost_heads.append(dict(update=update,parameters={k:dict(nonzero=int(torch.count_nonzero(v)),max_abs=float(v.abs().max()),l2=float(v.double().norm())) for k,v in payload['model'].items() if k.startswith('cost_critic.')}))
        if update==0:
            torch.manual_seed(7);fresh=runtime.ShortPolicy(contract=contract,size=config['size'])
            expected=DecisionPPOTrainer(fresh,PPOConfig(**config['ppo']))._identity()
            assert payload['identity']==expected and set(fresh.state_dict())==set(payload['model'])
            assert all(torch.equal(v,payload['model'][k]) for k,v in fresh.state_dict().items())
            initial_count=len(payload['model'])
        del payload
    assert len(all_attempts)==896 and len(stage_checks)==8 and all(v==identities[0] for v in identities)
    metrics=jsonl(BASE/'train/metrics.jsonl');episodes=jsonl(BASE/'train/episodes.jsonl')
    assert [m['update'] for m in metrics]==list(range(1,301)) and all(m['transitions']==4096 and m['total_transitions']==4096*m['update'] for m in metrics)
    assert metrics[-1]['total_transitions']==1228800 and all(m['diagnostics']['physical_transitions']==4096 and m['diagnostics']['valid_decisions']==4096 for m in metrics)
    assert all(m['cost_weight']==1. and set(m['reward_component_means'])==set(TERMS) for m in metrics)
    assert all(1<=e['update']<=300 and 0<=e['env_id']<128 and set(e['reward_components'])==set(TERMS) for e in episodes)
    failure_rows=[dict(line=i+1,episode=e) for i,e in enumerate(episodes) if e['cost'] or e['termination']['physical_failure'] or e['termination']['wrist_failure']]
    raw_cost=sum(m['mean_failure_cost']*m['transitions'] for m in metrics);episode_cost=sum(e['cost'] for e in episodes)
    nonzero=dict(immediate_failure_cost=[m['update'] for m in metrics if m['mean_failure_cost']!=0],
        cost_GAE=[m['update'] for m in metrics if any(m['diagnostics']['advantages']['cost_raw'][k]!=0 for k in ('mean','std','min','max'))],
        cost_value_loss=[m['update'] for m in metrics if m['cost_value_loss']!=0])
    trained=[r for r in evaluation_rows if r['update']>0]
    pairs=[[a['update'],b['update']] for a,b in zip(trained,trained[1:]) if a['passed'] and b['passed']]
    best=max(evaluation_rows,key=rank)['update'];latest=300
    acceptance=dict(passed=bool(pairs),passing_pairs=pairs,single_pass_updates=[r['update'] for r in trained if r['passed']],initial_pass=cases['0']['passed'])
    training=dict(updates=300,raw_transitions=1228800,global_control_ticks=9600,physics_steps=38400,completed_episodes=len(episodes),
        completed_episode_steps=sum(e['steps'] for e in episodes),remaining_open_episode_steps=1228800-sum(e['steps'] for e in episodes),
        reason_counts=dict(Counter(e['reason'] for e in episodes)),failures=failure_rows,nonzero_cost_updates=nonzero,
        raw_cost_mean_times_count_sum=raw_cost,completed_episode_cost_sum=episode_cost,cost_sum_residual=raw_cost-episode_cost,
        reward_component_raw_transition_sums={k:sum(m['reward_component_means'][k]*m['transitions'] for m in metrics) for k in TERMS},
        reward_component_completed_episode_sums={k:sum(e['reward_components'][k] for e in episodes) for k in TERMS},
        final_cost_diagnostics=metrics[-1]['diagnostics']['post_update']['critics']['cost'],
        checkpoints_cost_heads=cost_heads,actual_initial_default_seed7_identical_tensors=initial_count,
        cost_scope='cost_raw isGAE,notimmediatefailure; instantaneousrawcosttape/minmax absent; originalcosthead/gamma unchanged')
    assert training['remaining_open_episode_steps']>=0 and initial_count==73 and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    track(Path(__file__).resolve());track(HERE/'PLAN.md');out.mkdir()
    selection=dict(best_update=best,latest_update=latest,video_updates=sorted({best,latest}),
        rank=['achieved_fraction','mean_clean_fraction','negative_mean_wrong','negative_physical_or_wrist_fraction','later_update'],scope='All7includinginitial;singlebest isnotconsecutiveacceptance')
    grid.write(out/'comparison.json',dict(cases=cases,acceptance=acceptance,selection=selection,training=training,
        noNN_precheck_random=precheck['cases']['random']['summary'],NN_initial_policy=cases['0']['summary']))
    metric_rows=[dict(update=m['update'],total_transitions=m['total_transitions'],mean_reward=m['mean_reward'],mean_failure_cost=m['mean_failure_cost'],
        cost_value_loss=m['cost_value_loss'],**m['reward_component_means'],reward_component_mean_residual=m['mean_reward']-sum(m['reward_component_means'].values())) for m in metrics]
    policy_rows=[dict(update=r['update'],passed=r['passed'],physical_or_wrist_fraction=r['physical_or_wrist_fraction'],**r['summary']) for r in evaluation_rows]
    for name,table in (('performance.csv',policy_rows),('attempts.csv',all_attempts),('metrics300.csv',metric_rows),('env0_tracking.csv',phase_rows)):
        with (out/name).open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(11,3))
    for ax,key,label,limit in zip(axes,('achieved_fraction','mean_clean_fraction','mean_audible_wrong_fraction'),('Achieved','Clean','Wrong'),(.9,.9,.1)):
        ax.plot(UPDATES,[cases[str(u)]['summary'][key] for u in UPDATES],marker='o',label='NN checkpoint policy')
        ax.axhline(precheck['cases']['random']['summary'][key],color='orange',label='noNN Gaussian128')
        ax.axhline(limit,color='gray',ls=':');ax.set(title=label,xlabel='update',ylim=(-.02,1.03))
    axes[0].legend(fontsize=7);fig.tight_layout();fig.savefig(out/'performance.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(3,3,figsize=(12,8))
    for ax,key in zip(axes.flat,TERMS):
        ax.plot(range(1,301),[m['reward_component_means'][key] for m in metrics]);ax.set(title=key,xlabel='update')
    fig.suptitle('Raw60Hz reward component means; all300 updates, no smoothing');fig.tight_layout();fig.savefig(out/'rewards9.png',dpi=150);plt.close(fig)
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,
        stages=stage_checks,policy_first_attempts=896,training_updates=300,raw_transitions=1228800,initial_default73_exact=True,
        env0_candidate_wrong_replay_mismatches={u:c['env0_trace'].get('candidate_wrong_mismatches',[]) for u,c in cases.items()},
        env0_height_residuals_over_1um={u:c['env0_trace'].get('height_residuals_over_1um',[]) for u,c in cases.items()},
        acceptance=acceptance,selection=selection,limits=['7fixed128allfailuresincluded;128envnot128seeds','NNinitial and noNNGaussian aredifferentcontrols',
            'env0 detailedforce/geometry60Hzonly;other127forceunknown','CPUgates notnative240Hzledger;nearestresiduals preserved','noCUDA RNG load/resume inCPU audit;actualnativeoriginalstrictloaddoneby7evaluations']))
    lines=['# 검지 낮은 상한 fresh300 실제 분석','',
        '중간50/100/150회는각128/128이지만200/250회는0/128로후퇴했다. 최종300회는%d/128·clean%.4f%%·wrong%.4f%%로회복이불완전하다. 중간연속수용통과와최종성능유지는별개다.'%(round(cases['300']['summary']['achieved_fraction']*128),100*cases['300']['summary']['mean_clean_fraction'],100*cases['300']['summary']['mean_audible_wrong_fraction']),'',
        '| update | 달성/128 | clean | wrong | 물리/손목실패 | 단일기준 |','|---:|---:|---:|---:|---:|---|']
    for r in evaluation_rows:
        s=r['summary'];lines.append('| %d | %d/128 | %.6f | %.6f | %.6f/%.6f | %s |'%(r['update'],round(s['achieved_fraction']*128),s['mean_clean_fraction'],s['mean_audible_wrong_fraction'],s['physical_failure_fraction'],s['wrist_failure_fraction'],'통과' if r['passed'] else '미달'))
    lines+=['','| env0 update | 음중60Hz끝점 | actual4 ° | target4 ° | body1/2/3 평균N | 손목평균 mm/° | CPU6gate |',
        '|---:|---:|---|---|---|---|---|']
    fmt=lambda v:', '.join('%.5f'%x for x in v)
    for u in UPDATES:
        p=cases[str(u)]['env0_trace']['phases'].get('audible',{});m=p.get('metric_mean')
        lines.append('| %d | %d | %s | %s | %s | %s | %s |'%(u,p.get('samples',0),fmt(m[:4]) if m else '미노출/미확인',
            fmt(m[4:8]) if m else '미노출/미확인',fmt(m[12:15]) if m else '미노출/미확인',fmt(m[15:17]) if m else '미노출/미확인',str(p.get('CPU_gate_counts'))))
    lines+=['','학습후인접2평가수용: **%s**, 통과쌍%s. 초기0은기준선이며연속학습후쌍에는포함하지않았다.'%('통과' if pairs else '미달',pairs),
        '사전순위best=%d,latest=300,영상대상%s. 7평가/896첫시도와실패를모두보존했고단일best를연속수용으로대체하지않았다.'%(best,selection['video_updates']),
        '비NNGaussian사전대조31/128은기존검수된별도기준선이며실제NN초기정책0회평가와다르다. 이번128/seed7·고정기타·유한팔·손목v3·private16effort0.25의단음결과를자유기타/J33/전곡·다른손가락/자연스러움/해제·전환으로확대하지않는다.','',
        '전체300metrics/1,228,800raw전이/종료episode%d·남은미종료episode전이%d를감사했다. 모든실패원장과원9보상/평균합산잔차를보존했고8scene/실제exit/105native/90쌍/source/alias/닫기를검사했다.'%(len(episodes),training['remaining_open_episode_steps']),
        '원costhead와gamma/PPO를유지했다. 실제initial73tensor는동일seed7/large/index1의원CPU초기화와같으며7저장본identity/source핀을대조했다. CPU에서CUDA RNG불러오기를우회하거나학습을재개하지않았다. rawcost는GAE필드와구분하고순간비용min/max/tape미저장한계를남겼다.','',
        '실제실패비용nonzero는%d/300회,종료실패episode는%d건이며비용평균×전이수합과종료episode비용합의차이는%.9g이다. 반면cost GAE/loss는각%d/%d회nonzero다. 실제실패비용과초기critic/bootstrap의추정오차는다른양이며nonzero GAE를새실패로세지않는다.'%(len(nonzero['immediate_failure_cost']),len(failure_rows),raw_cost-episode_cost,len(nonzero['cost_GAE']),len(nonzero['cost_value_loss'])),'',
        'best150 env0 음중의index2(PIP)는actual평균17.70785°/target90.00019°,index3(DIP)는83.72537°/88.37375°이며distal몸체합력평균6.50917N이다. 음달성에도큰추종차이와극단적인굴곡이남고자연스러움은확인되지않았다. latest300의env0은성공사례지만전체는76/128이므로이trace를전체128의성공으로확대하지않는다. env0은성과로선별하지않은원래고정환경이다.','',
        'env0 60Hz의세phase selectedtarget/actual·body1/2/3합력·손목/6gate·armbounds는comparison.json/env0_tracking.csv에있다. 전체128의원각도통계는attempts.csv에보존하지만나머지127의상세force는없다. 목표추종차이/하한체류와고하중이남아도접촉쌍/원인/보편관절상한으로확정하지않는다. 몸체합력은압력·모터torque·240Hz최대가아니다.','',
        '![고정평가](performance.png)','![원9보상300회](rewards9.png)']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print('Actual CPU learning results written:',out)


if __name__=='__main__':main()
