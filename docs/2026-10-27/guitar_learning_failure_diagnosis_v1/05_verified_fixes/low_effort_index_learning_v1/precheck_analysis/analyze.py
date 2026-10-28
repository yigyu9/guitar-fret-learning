"""CPU audit of index128 no-NN precheck; root completion handoff required."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
spec=importlib.util.spec_from_file_location('index128_analysis_probe',BASE/'probe.py')
probe=importlib.util.module_from_spec(spec);sys.modules[spec.name]=probe;spec.loader.exec_module(probe)
grid=probe.grid
HELPER=probe.PRE/'analysis/analyze.py'


def differences(a,b,prefix=''):
    if isinstance(a,dict) and isinstance(b,dict):
        return [v for k in sorted(set(a)|set(b)) for v in differences(a.get(k),b.get(k),prefix+'.'+k if prefix else k)]
    return [] if a==b else [dict(path=prefix,old4=a,new128=b)]


def arm_audit(t,meta,config,controller):
    import numpy as np
    from guitar_learning.core.control import LEFT_ARM_NAMES
    names=list(LEFT_ARM_NAMES);qids=[meta['joint_names'].index(n) for n in names]
    ai=[controller['action_order'].index(n) for n in names]
    low=np.asarray(controller['action_lower_rad'])[ai];high=np.asarray(controller['action_upper_rad'])[ai]
    source=config['song']['short_learning']['view']['source_target'];result={}
    masks=grid.phase_masks(t['source_time_s'],source['onset_s'],source['end_s'])
    for phase,mask in zip(('before','audible','after'),masks):
        result[phase]={};request=t['wrist_requested_arm_rad'][mask]
        target=t['target'][mask][:,qids];actual=t['q'][mask][:,qids]
        for label,values in (('request',request),('target',target),('actual',actual)):
            result[phase][label+'_bounds']=[dict(joint=n,lower_count=int((values[:,i]<=low[i]+1e-6).sum()),
                upper_count=int((values[:,i]>=high[i]-1e-6).sum())) for i,n in enumerate(names)
                if (values[:,i]<=low[i]+1e-6).any() or (values[:,i]>=high[i]-1e-6).any()]
        for label,error in (('request_minus_target',request-target),('target_minus_actual',target-actual)):
            values=np.rad2deg(abs(error));result[phase][label+'_mean_abs_deg']=values.mean(0).tolist() if len(values) else None
            result[phase][label+'_max_abs_deg']=values.max(0).tolist() if len(values) else None
    return dict(joint_names=names,phases=result,scope='env0 poststep60Hz; bounds use original arm action intervals; no body/collision causality')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root-completed',action='store_true');args=parser.parse_args()
    if not args.root_completed:
        print('Prepared only; wait for root complete3scene exit; no actual raw read.');return
    sys.path.insert(0,str(grid.ROOT));out=HERE/'results_v1';probe.cap.reject_existing(out)
    inputs,verified={},{}
    def track(path):path=Path(path);inputs[str(path)]=grid.sha(path);return path
    def read(path):return grid.read(track(path))
    def pins(mapping):
        for p,h in mapping.items():
            if p not in verified:verified[p]=grid.sha(p)
            assert verified[p]==h,p
    seal,paths=probe.gate('precheck')
    for p in paths:track(p)
    pins(seal['input_pins']);assert len(seal['input_pins'])==1075
    review=read(BASE/'review.json');assert review['verdict']=='PASS' and not review['findings'];pins(review['reviewed_sha256'])
    launcher=read(BASE/'01_precheck_launcher.json')
    assert launcher['completed'] and launcher['returncode']==0 and len(launcher['children'])==3
    assert [c['control'] for c in launcher['children']]==['reference','zero','random'] and all(c['returncode']==0 for c in launcher['children'])
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    helper_spec=importlib.util.spec_from_file_location('reviewed_index_trace_audit',HELPER)
    helper=importlib.util.module_from_spec(helper_spec);helper_spec.loader.exec_module(helper);track(HELPER)
    metadata,_=fixture(1);canonical=read(BASE/'cpu_inputs/settings.json');native_expected=read(BASE/'cpu_inputs/effort_declaration128.json')
    old=read(probe.PRE/'analysis/results_v1/comparison.json')['cases']
    cases,rows,traces,attempts,phase_rows,bound_rows={},{},{},[],[],[]
    for control in ('reference','zero','random'):
        folder=probe.output('precheck',control,0);config=read(folder/'settings.json');assert config==canonical
        report=read(folder/'diagnostic_report.json');scene=read(folder/'gpu_scene_final.json')
        assert all(report[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored'))
        assert report['failure'] is None and not report['cleanup_errors'] and not report['changed_inputs'] and not report['unpinned_project_sources']
        assert report['phase']=='precheck' and report['control']==control and report['native_environment_count']==128 and report['update']==0
        assert scene['closed'] and scene['environment_count']==128 and scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
        assert scene['physics_steps']==report['physics_steps'] and scene['physics_steps']%4==0 and scene['physics_steps']//4<=config['song']['short_learning']['view']['duration_ticks']
        native=read(folder/'native_effort_readback.json');assert native==native_expected and native['explicit_DOF105_readback_environments']==128 and native['controller_caps_exact']
        contract=read(folder/'training_contract.json');assert contract['native_backend']['diagnostic_native_effort']==native
        assert contract['task']['short_learning']==config['song']['short_learning']
        before,after=read(folder/'inputs_before.json'),read(folder/'diagnostic_inputs_after.json');pins(before)
        assert after['verified'] and before==after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
        evaluation=read(folder/'evaluation.json');episodes=evaluation['episodes'];rows[control]=episodes
        assert evaluation['condition']==control and evaluation['policy_performance'] is False and evaluation['assigned_quotas']==[1]*128 and grid.complete(episodes,128)
        assert evaluation['summary']==summary(episodes)
        provider=read(folder/'action_provider.json');assert provider['NN'] is False and provider['updates']==0 and provider['seed']==7 and provider['std']==probe.pre.STD
        residuals=[]
        for e in episodes:
            assert e['target_id']==config['song']['short_learning']['teacher']['source_target_id'] and e['selected_target_count']==1
            assert set(e['reward_components'])=={'song_left_approach','song_left_contact','song_clean_hold','song_left_success','song_wrong_press','song_performance_deficit','song_finger_standby','song_thumb_support','action_change'}
            assert np.isfinite([e['reward'],*e['reward_components'].values()]).all()
            residuals.append(e['reward']-sum(e['reward_components'].values()))
            attempts.append(dict(control=control,env_id=e['env_id'],achieved=e['achieved'],clean=e['clean_fraction'],wrong=e['audible_wrong_fraction'],
                physical_failure=e['termination']['physical_failure'],wrist_failure=e['termination']['wrist_failure'],reason=e['reason'],steps=e['steps'],reward=e['reward'],
                **e['reward_components'],reward_component_sum_residual=residuals[-1],note=json.dumps(e['note']),angles=json.dumps(e['angles'])))
        meta=read(folder/'trace_metadata.json');assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
        assert meta['wrist_control']==config['song']['short_learning']['wrist_control']
        t=dict(np.load(track(folder/'trace_env0_episode0.npz')));traces[control]=t
        trace=helper.trace_audit(t,metadata,config,episodes,control,contract['action']['target_contract'])
        arm=arm_audit(t,meta,config,contract['action']['target_contract'])
        for phase,value in trace['phases'].items():
            phase_rows.append(dict(control=control,phase=phase,**value))
            bound_rows.append(dict(control=control,phase=phase,**arm['phases'][phase]))
        baseline=old['index_'+control];oldconfig=read(Path(baseline['source'])/'settings.json')
        assert config['song']['short_learning']==oldconfig['song']['short_learning']
        cases[control]=dict(summary=evaluation['summary'],episodes=episodes,source=str(folder),
            old4_source=baseline['source'],old4_summary=baseline['summary'],settings_differences_4_to_128=differences(oldconfig,config),
            env0_trace=trace,env0_arm=arm,reward_component_sum_max_abs_residual=max(map(abs,residuals)),
            reward_component_totals={k:sum(e['reward_components'][k] for e in episodes) for k in episodes[0]['reward_components']})
    acceptance=probe.acceptance(rows)
    assert len(attempts)==384 and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    track(Path(__file__).resolve());track(HERE/'PLAN.md');out.mkdir()
    grid.write(out/'comparison.json',dict(cases=cases,acceptance=acceptance,first_attempts=384,NN=False))
    for name,table in (('attempts.csv',attempts),('phase_tracking.csv',phase_rows),('arm_tracking.csv',bound_rows)):
        with (out/name).open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    controls=list(cases);x=np.arange(3);fig,axes=plt.subplots(1,3,figsize=(10,3))
    for ax,key,label in zip(axes,('achieved_fraction','mean_clean_fraction','mean_audible_wrong_fraction'),('Achieved','Clean','Wrong')):
        ax.bar(x-.18,[cases[c]['old4_summary'][key] for c in controls],.36,label='reviewed4')
        ax.bar(x+.18,[cases[c]['summary'][key] for c in controls],.36,label='new128')
        ax.set(xticks=x,xticklabels=controls,ylim=(0,1.05),title=label)
    axes[0].legend();fig.tight_layout();fig.savefig(out/'summary.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(9,5),sharex=True)
    from scipy.spatial.transform import Rotation
    wrist,guitar=[metadata['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')]
    index1=metadata['body_names'].index('human/LH:index1')
    for control,t in traces.items():
        rg=Rotation.from_quat(t['body_state'][:,guitar,3:7]);goal=t['body_state'][:,guitar,:3]+rg.apply(t['wrist_goal_G_m'])
        axes[0].plot(t['time_s'],np.linalg.norm(goal-t['body_state'][:,wrist,:3],axis=1)*1000,label=control)
        axes[1].plot(t['time_s'],np.linalg.norm(t['net_body_force_n'][:,index1],axis=1),label=control)
    axes[0].set_ylabel('Wrist error mm');axes[1].set_ylabel('Index body1 resultant N');axes[1].set_xlabel('env0 local seconds')
    for ax in axes:ax.axvline(3,color='gray',ls=':');ax.legend()
    fig.tight_layout();fig.savefig(out/'env0_trace.png',dpi=150);plt.close(fig)
    gate_mismatch={c:cases[c]['env0_trace']['candidate_wrong_mismatches'] for c in controls}
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,
        scenes=3,first_attempts=384,all_scenes_closed=True,native128x105_readback_90pairs=True,aliases_loader_restored=True,
        acceptance=acceptance,env0_candidate_wrong_replay_mismatches=gate_mismatch,
        limits=['env0first60Hz only; other127 detailedforce unavailable','CPU6gates reconstructed,notnative240Hz integration',
            'native nearestsample/normalcos absent; residuals preserved','4vs128 comparison isnotcausal or128seeds','bodyresultant isnotpairpressure/torque/240Hzmaximum']))
    lines=['# 검지128환경 낮은 상한 사전 대조','', '| 명령 | 달성/전체128 | 평균clean | 평균wrong | 물리/손목실패 | 기존4 달성 |','|---|---:|---:|---:|---:|---:|']
    for c in controls:
        s=cases[c]['summary'];old4=cases[c]['old4_summary'];lines.append('| %s | %d/128 | %.8f | %.8f | %d/%d | %d/4 |'%(c,sum(e['achieved'] for e in rows[c]),s['mean_clean_fraction'],s['mean_audible_wrong_fraction'],sum(e['termination']['physical_failure'] for e in rows[c]),sum(e['termination']['wrist_failure'] for e in rows[c]),round(old4['achieved_fraction']*4)))
    lines+=['','원PLAN 사전 수용기준: **%s**. 원384첫시도·실패를 모두 포함하고 random은 문턱/선별 없이 전부 공개했다. 이 판정은 봉인된 probe.acceptance의 원기준 재계산이며 실제 독립검수 PASS와 별개다.'%('통과' if acceptance['passed'] else '미달'),'',
        '| env0 명령 | 음중끝점 | actual4 ° | target4 ° | body1/2/3 평균N | 손목평균 mm/° | CPU6gate |','|---|---:|---|---|---|---|---|']
    fmt=lambda v:', '.join('%.5f'%x for x in v)
    for c in controls:
        p=cases[c]['env0_trace']['phases']['audible'];m=p['metric_mean']
        lines.append('| %s | %d | %s | %s | %s | %s | %s |'%(c,p['samples'],fmt(m[:4]),fmt(m[4:8]),fmt(m[12:15]),fmt(m[15:17]),str(p['CPU_gate_counts'])))
    ref=cases['reference']['env0_trace']['phases']['audible']['metric_mean']
    lines+=['','reference env0 음중 index1_z actual평균%.5f°/target평균%.5f°로추종차이%.5f°가남는다. 원음달성과요청각완전추종은별개이며이값을보편적인관절상한으로해석하지않는다.'%(ref[1],ref[5],ref[5]-ref[1]),
        'reference/zero env0 음중 L_Wrist_y의request와target은11끝점모두원하한에있지만actual은하한체류가없다. zero는해당env0의위치/방향11끝점통과에도distal합력0으로loaded/positive/candidate0이다. 이것은env0의관찰이며나머지127의실패원인이나접촉쌍인과를확정하지않는다.',
        'random31/128은비NN Gaussian명령의실제기준선이며후속NN initial정책과exact가아니다. 기존4와의설정차이는num_envs/updates및파생planned_transitions/full_song_after로모두JSON에기록했고진단환경의원음·손목·판정은동일하다.','',
        'CPU6gate 순서는loaded/position/position_facing/positive/candidate/wrong이다. gate와bounds·request→target·target→actual 차이는 comparison.json/CSV에세phase별저장했다. 이것은저장된env0 60Hz끝점의기하/몸체합력재구성이며240Hz음원장/보상을재지급하지않는다. nearest 잔차나candidate/wrong불일치는숨기지않고verification/comparison에남겼다.','',
        '원9보상은전체384원장의각항및합산잔차를attempts.csv에보존했다. native105속성은각128환경직접readback·controllercaps·90쌍과같고전체3scene의실제exit0/닫기/입력/alias복원을확인했다. NN/checkpoint/학습은없다.','',
        '같은seed7의128환경이지128seed가아니다. 기존4대비는분모/배치확대의관찰이며단일인과효과가아니다. env0 body1/2/3합력은실제접촉쌍압력·motor torque·240Hz최대하중이아니고나머지127환경상세하중은미저장이다. 제한과제사전통과를정책학습/자연스러움/자유기타/다른손가락/전곡성과로확대하지않는다.','',
        '독립검수뒤이분석소스·PLAN·결과·review를동결한다. 후속학습분석은별도learning_analysis/에작성하며root만GPU를실행한다.','',
        '![전체분모 비교](summary.png)','![env0 끝점 추종과합력](env0_trace.png)']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print('Actual CPU results written:',out)


if __name__=='__main__':main()
