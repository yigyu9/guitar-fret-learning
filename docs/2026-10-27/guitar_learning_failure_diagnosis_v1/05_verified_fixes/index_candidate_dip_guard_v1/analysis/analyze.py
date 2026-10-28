"""CPU analysis of two completed DIP-guard scenes; no native execution."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
MODES=('passthrough','candidate_dip_no_positive_increment')


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value


def completed_launcher(value):
    assert value['completed'] and value['returncode']==0
    assert [c['condition'] for c in value['children']]==list(MODES)
    assert all(c['returncode']==0 for c in value['children'])


def sidecar_audit(t,episodes,guard):
    import numpy as np
    first=t['first_attempt'];assert first.dtype==np.bool_ and first.ndim==2 and first.shape[1]==128
    assert all(v.shape==first.shape for v in t.values())
    assert first[0].all() and not ((~first[:-1]) & first[1:]).any()
    steps=np.array([next(e['steps'] for e in episodes if e['env_id']==i) for i in range(128)])
    assert np.array_equal(first.sum(0),steps)
    for k,v in t.items():
        assert not v[~first].any(),k
        if v.dtype!=np.bool_:assert np.isfinite(v[first]).all(),k
    valid=first & t['candidate'] & ~t['wrong'] & ~t['prior_failure'] & ~t['reset'] & t['finite']
    blocked=valid & (t['raw_target_rad']>t['old_target_rad']) & guard
    assert np.array_equal(valid,t['eligible']) and np.array_equal(blocked,t['blocked'])
    assert np.array_equal(t['final_target_rad'],np.where(blocked,t['old_target_rad'],t['raw_target_rad']))
    assert np.array_equal(t['clock'][first],(t['start_clock']+4)[first])
    for i in range(128):assert np.array_equal(t['clock'][:,i][first[:,i]],np.arange(1,steps[i]+1)*4)
    continuous=first[1:] & first[:-1] & ~t['reset'][1:]
    assert np.array_equal(t['old_target_rad'][1:][continuous],t['final_target_rad'][:-1][continuous])
    for k in ('other104_error_rad','memory_error_rad','submit_error_rad','observation_error'):assert not t[k][first].any(),k
    assert (t['box_rate_excess_rad'][first]<=t['numerical_tolerance_rad'][first]).all()
    assert (abs(t['final_target_rad']-t['old_target_rad'])[first]<=4/60+t['numerical_tolerance_rad'][first]).all()
    negative=first & (t['raw_target_rad']<t['old_target_rad'])
    assert np.array_equal(t['final_target_rad'][negative],t['raw_target_rad'][negative])
    rows=[]
    for i in range(128):
        mask=first[:,i];b=blocked[:,i];v=valid[:,i];run=longest=0
        for x in b:
            run=run+1 if x else 0;longest=max(longest,run)
        last=np.flatnonzero(mask)[-1]
        postfailure=bool(t['post_failure'][last,i]);e=next(e for e in episodes if e['env_id']==i)
        assert postfailure==bool(e['termination']['physical_failure'] or e['termination']['wrist_failure'])
        off=mask[1:] & v[:-1] & ~v[1:]
        rows.append(dict(env_id=i,first_attempt_controls=int(mask.sum()),eligible_controls=int(v.sum()),blocked_controls=int(b.sum()),
            blocked_duration_s=float(b.sum()/60),longest_block_s=longest/60,negative_controls=int(negative[:,i].sum()),
            eligible_off_transitions=int(off.sum()),off_positive_controls=int((off & (t['raw_target_rad'][1:,i]>t['old_target_rad'][1:,i])).sum()),
            final_target_deg=float(np.rad2deg(t['final_target_rad'][last,i])),failed_endpoint=postfailure))
    return dict(first_attempt_controls=int(first.sum()),failed_endpoints=sum(r['failed_endpoint'] for r in rows),
        affected_envs=int(blocked.any(0).sum()),blocked_controls=int(blocked.sum()),eligible_controls=int(valid.sum()),
        negative_controls=int(negative.sum()),gate_off_transitions=sum(r['eligible_off_transitions'] for r in rows),
        off_positive_controls=sum(r['off_positive_controls'] for r in rows),first_attempt_mask_exact=True,negative_and_other104_exact=True,
        max_other104_error_rad=float(t['other104_error_rad'][first].max()),max_memory_error_rad=float(t['memory_error_rad'][first].max()),
        max_box_rate_excess_rad=float(t['box_rate_excess_rad'][first].max()),max_scene_error_rad=float(t['submit_error_rad'][first].max()),
        max_observation_error=float(t['observation_error'][first].max()),env_rows=rows,
        scope='60Hz first-attempt controls; perenv durations are controls/60, not240Hz contact residence. Negative pass verifies command freedom, not successful release.')


def self_test():
    import numpy as np
    good=dict(completed=True,returncode=0,children=[dict(condition=m,returncode=0) for m in MODES]);completed_launcher(good)
    for bad in (dict(good,completed=False),dict(good,children=good['children'][:1]),dict(good,returncode=1)):
        try:completed_launcher(bad)
        except AssertionError:pass
        else:raise AssertionError('Incomplete launcher admitted')
    first=np.ones((3,128),bool);first[2,0]=False
    t={k:np.zeros_like(first) for k in ('candidate','wrong','prior_failure','reset','blocked','eligible','post_failure')}
    t.update(first_attempt=first,finite=first.copy())
    t['candidate'][0]=True;t['eligible'][0]=True;t['blocked'][0]=True
    old=np.zeros(first.shape);raw=old.copy();raw[0]=.02;raw[1]=-.02;old[2]=-.02;raw[2]=-.01
    final=raw.copy();final[0]=0
    for k,v in dict(old_target_rad=old,raw_target_rad=raw,final_target_rad=final,clock=np.tile(np.arange(1,4)[:,None]*4,(1,128)),start_clock=np.tile(np.arange(3)[:,None]*4,(1,128))).items():t[k]=np.where(first,v,0)
    for k in ('other104_error_rad','memory_error_rad','submit_error_rad','observation_error','box_rate_excess_rad'):t[k]=np.zeros(first.shape)
    t['numerical_tolerance_rad']=first*1e-6
    es=[dict(env_id=i,steps=2 if i==0 else 3,termination=dict(physical_failure=False,wrist_failure=False)) for i in range(128)]
    result=sidecar_audit(t,es,True);assert result['affected_envs']==128 and result['negative_controls']==128 and result['off_positive_controls']==0
    t['final_target_rad'][0,0]=.01
    try:sidecar_audit(t,es,True)
    except AssertionError:pass
    else:raise AssertionError('Changed held target admitted')
    assert 'torch' not in sys.modules and 'isaacgym' not in sys.modules
    print('Synthetic completion/mask/filter/memory/negative regression PASS; actual raw unread.')


def actual_main():
    # Only this stdlib launcher read precedes the completed-two-scene guard.
    launcher_path=BASE/'01_launcher.json';launcher=json.loads(launcher_path.read_text());completed_launcher(launcher)
    probe=module('dip_actual_probe',BASE/'probe.py');grid=probe.grid
    sys.path.insert(0,str(grid.ROOT));out=HERE/'results_v1';probe.cap.reject_existing(out)
    inputs,verified={},{}
    def track(p):p=Path(p).resolve();inputs[str(p)]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(values):
        for p,h in values.items():
            if p not in verified:verified[p]=grid.sha(p)
            assert verified[p]==h,p
    track(launcher_path);seal,paths=probe.gate();assert len(seal['input_pins'])==1420;pins(seal['input_pins'])
    for p in paths:track(p)
    for p in (Path(__file__),HERE/'PLAN.md'):track(p)
    commands=read(BASE/'cpu_inputs/commands.json');assert [c['argv'] for c in launcher['children']]==[commands[m] for m in MODES]
    helper=module('dip_arm_helper',probe.B.BASE/'precheck_analysis/analyze.py');trace_helper=module('dip_trace_helper',helper.HELPER)
    track(helper.__file__);track(trace_helper.__file__)
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    metadata,_=fixture(1);config=read(BASE/'cpu_inputs/settings.json');oldfolder=probe.B.output('evaluate',update=300)
    oldeval=read(oldfolder/'evaluation.json');oldt=dict(np.load(track(oldfolder/'trace_env0_episode0.npz')))
    expected_contract=read(oldfolder/'training_contract.json');native=read(oldfolder/'native_effort_readback.json')
    model_sha=grid.sha(track(probe.B.checkpoint(300)));cases={};attempts=[];controls=[];phases=[];traces={};trace_diffs={}
    terms={'song_left_approach','song_left_contact','song_clean_hold','song_left_success','song_wrong_press','song_performance_deficit','song_finger_standby','song_thumb_support','action_change'}
    for child,mode in zip(launcher['children'],MODES):
        folder=BASE/'runs'/mode
        assert read(BASE/('01_'+mode+'_launcher.json'))==child
        assert read(folder/'settings.json')==config
        report=read(folder/'report.json');diag=read(folder/'diagnostic_report.json');scene=read(folder/'gpu_scene_final.json');guard=read(folder/'dip_guard_report.json')
        assert report['completed'] and report['closed'] and report['failure'] is None and not report['changed_inputs'] and not report['unpinned_project_sources']
        assert all(diag[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored')) and diag['failure'] is None and not diag['cleanup_errors']
        assert not diag['changed_inputs'] and not diag['unpinned_project_sources'] and diag['native_environment_count']==128 and diag['update']==300
        assert scene['closed'] and scene['environment_count']==128 and scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
        assert scene['physics_steps']==diag['physics_steps'] and scene['physics_steps']%4==0 and scene['physics_steps']//4<=config['song']['short_learning']['view']['duration_ticks']
        assert read(folder/'native_effort_readback.json')==native and read(folder/'training_contract.json')==expected_contract
        assert read(folder/'initialization_declaration.json')==read(oldfolder/'initialization_declaration.json')
        assert guard['completed'] and guard['failure'] is None and not guard['cleanup_errors'] and all(guard['checks'].values())
        assert guard['assigned_first_attempts']==guard['completed_first_attempts']==128 and guard['policy_before']==guard['policy_after']
        assert guard['policy_before']['updates']==300 and guard['policy_before']['cost_weight']==1
        override=read(folder/'execution_override.json');assert override['mode']==mode and override['enabled']==(mode==MODES[1]) and override['fresh'] is False
        assert override['model_checkpoint']==str(probe.B.checkpoint(300)) and override['first_attempt_only'] and override['physics_hz']==240 and override['control_hz']==60
        before=read(folder/'inputs_before.json');pins(before)
        for n in ('inputs_after.json','diagnostic_inputs_after.json'):
            after=read(folder/n);assert after['verified'] and after['input_pins']==before and not after['changed_paths'] and not after['unpinned_project_sources']
        ev=read(folder/'evaluation.json');es=ev['episodes'];assert ev['assigned_quotas']==[1]*128 and grid.complete(es,128) and ev['condition']=='policy' and ev['summary']==summary(es)
        for e in es:
            assert set(e['reward_components'])==terms and e['target_id']==config['song']['short_learning']['teacher']['source_target_id'] and e['selected_target_count']==1
            attempts.append(dict(condition=mode,env_id=e['env_id'],achieved=e['achieved'],clean=e['clean_fraction'],wrong=e['audible_wrong_fraction'],reason=e['reason'],steps=e['steps'],
                physical_failure=e['termination']['physical_failure'],wrist_failure=e['termination']['wrist_failure'],reward=e['reward'],cost=e['cost'],cost_components=json.dumps(e['cost_components']),
                **e['reward_components'],reward_sum_residual=e['reward']-sum(e['reward_components'].values())))
        d=dict(np.load(track(folder/'dip_control60.npz')));audit=sidecar_audit(d,es,mode==MODES[1]);assert guard['control_rows']==len(d['first_attempt'])==scene['physics_steps']//4
        controls.extend(dict(condition=mode,**r) for r in audit.pop('env_rows'))
        meta=read(folder/'trace_metadata.json');assert meta==read(oldfolder/'trace_metadata.json')
        t=dict(np.load(track(folder/'trace_env0_episode0.npz')));traces[mode]=t
        j=metadata['joint_names'].index('LH:index3');e0=next(e for e in es if e['env_id']==0);n=e0['steps']
        assert n==len(t['time_s']) and np.array_equal(t['target'][:,j],d['final_target_rad'][:n,0])
        assert np.allclose(t['time_s'],d['clock'][:n,0]/240,rtol=0,atol=1e-14)
        assert np.array_equal(d['candidate'][1:n,0],t['candidate'][:n-1]) and np.array_equal(d['wrong'][1:n,0],t['wrong'][:n-1])
        ctl=expected_contract['action']['target_contract'];ai=ctl['action_order'].index('LH:index3');lo=np.float32(ctl['action_lower_rad'][ai]);hi=np.float32(ctl['action_upper_rad'][ai])
        raw=np.clip(d['old_target_rad'][:n,0]+t['executed_action'][:,ai]*np.float32(4/60),lo,hi)
        raw_residual=float(abs(raw-d['raw_target_rad'][:n,0]).max());assert raw_residual<=float(d['numerical_tolerance_rad'][:n,0].max())
        trace=trace_helper.trace_audit(t,metadata,config,es,'policy',ctl);arm=helper.arm_audit(t,meta,config,ctl) if 'unavailable_reason' not in trace else None
        cases[mode]=dict(summary=ev['summary'],episodes=es,control=audit,env0_trace=trace,env0_arm=arm,env0_incremental_raw_max_error_rad=raw_residual,
            model_and_RNG_before_after=guard['policy_before'],source=str(folder))
        for phase,v in trace['phases'].items():phases.append(dict(condition=mode,phase=phase,**v))
        if mode==MODES[0]:
            trace_diffs=dict(common_fields={},only_old=sorted(set(oldt)-set(t)),only_new=sorted(set(t)-set(oldt)))
            for k in sorted(set(t)&set(oldt)):
                a,b=oldt[k],t[k];same=a.shape==b.shape and np.array_equal(a,b)
                trace_diffs['common_fields'][k]=dict(shape_old=list(a.shape),shape_new=list(b.shape),exact=same,max_abs=float(np.max(abs(a.astype(float)-b.astype(float)))) if a.shape==b.shape else None)
            cases[mode]['old_B300_evaluation_exact']=ev==oldeval
            cases[mode]['old_B300_summary']=oldeval['summary']
    assert len(attempts)==256 and grid.sha(probe.B.checkpoint(300))==model_sha
    assert cases[MODES[0]]['model_and_RNG_before_after']==cases[MODES[1]]['model_and_RNG_before_after']
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    out.mkdir();comparison=dict(cases=cases,first_attempts=256,old_B300_passthrough_trace_differences=trace_diffs,checkpoint_sha256=model_sha)
    grid.write(out/'comparison.json',comparison)
    for name,rows in (('attempts.csv',attempts),('dip_controls.csv',controls),('phase_tracking.csv',phases)):
        with (out/name).open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    plot(out,cases,traces,metadata)
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,
        scenes=2,first_attempts=256,all_scene_source_contract_native128_closed=True,checkpoint_unchanged=True,execution_override_not_model_contract=True,
        env0_candidate_wrong_mismatches={m:cases[m]['env0_trace'].get('candidate_wrong_mismatches') for m in MODES},
        scope='Full128 original240Hz first-attempt ledgers/rewards; whole128 scalar DIP sidecar60Hz; detailed q/body/force and CPU gate replay only env0.',
        limits=['Closed-loop observations and later NN actions differ; not fixed-tape isolation or learned improvement.',
            'Body resultant is not pair pressure, motor effort or240Hz maximum; other127 detailed forces unavailable.',
            'Negative command pass is not successful release; existing target error and actual motion are not frozen.']))
    write_report(out,cases,trace_diffs);print('Actual CPU analysis written:',out)


def plot(out,cases,traces,metadata):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,1,figsize=(10,7),sharex=True)
    ids=[metadata['joint_names'].index(n) for n in ('LH:index2','LH:index3')];body=metadata['body_names'].index('human/LH:index1')
    for mode,t in traces.items():
        for i,name in zip(ids,('PIP','DIP')):axes[0].plot(t['time_s'],np.rad2deg(t['q'][:,i]),label=mode+' '+name)
        for i,name in zip(ids,('PIP','DIP')):axes[1].plot(t['time_s'],np.rad2deg(t['target'][:,i]),label=mode+' '+name)
        axes[2].plot(t['time_s'],np.linalg.norm(t['net_body_force_n'][:,body],axis=1),label=mode)
    for ax,title in zip(axes,('env0 actual deg','env0 target deg','env0 index body1 resultant N')):ax.set_ylabel(title);ax.legend(fontsize=7)
    axes[-1].set_xlabel('local seconds (60Hz endpoints)');fig.tight_layout();fig.savefig(out/'env0_tracking.png',dpi=150);plt.close(fig)


def write_report(out,cases,diff):
    lines=['# 검지 DIP 양의 추가목표 억제 대조','', '| 조건 | 달성/전체128 | clean | wrong | 물리/손목실패 | 개입환경/controls | 음의증분통과 |','|---|---:|---:|---:|---:|---:|---:|']
    for mode,c in cases.items():
        s=c['summary'];es=c['episodes'];a=c['control'];lines.append('| %s | %d/128 | %.8f | %.8f | %d/%d | %d/%d | %d |'%(mode,sum(e['achieved'] for e in es),s['mean_clean_fraction'],s['mean_audible_wrong_fraction'],sum(e['termination']['physical_failure'] for e in es),sum(e['termination']['wrist_failure'] for e in es),a['affected_envs'],a['blocked_controls'],a['negative_controls']))
    lines+=['','전체256개 첫시도에 실패를 포함하고 완료 뒤 retry는 제외했다. 두 실행 모두 원 B300 strict/fresh=False·128 native105 cap.25·90쌍·설정·원9항보상/비용·원시계·scene종료 및 모델/RNG/업데이트 불변을 검증했다. 보상9항과 실패비용은 attempts.csv에 그대로 남겼다.','',
        '전128 60Hz sidecar에서 원 DIP목표의 추가 양의 증분만 해당 gate에서 old target으로 되돌리고, negative/zero·그 외104열·target메모리/scene제출/관측이 원 경로와 일치하는지 검산했다. 억제된 증분은 저장하지 않고 gate가 꺼지면 새 원제어로 돌아온다. 원래 target−actual 차이는 남으므로 관절자세 고정과 다르다. 음의 명령 통과는 실제 해제 성공 증거가 아니다.','',
        '새 passthrough의 기존 B300 evaluation exact: **%s**. 원trace 필드별 shape/exact/최대차는 comparison.json에 보존했다. 정합 실패나 작은 수치차가 있어도 원파일/허용오차를 바꾸지 않는다.'%cases[MODES[0]]['old_B300_evaluation_exact'],
        '', '| env0 음중 | actual4 ° | target4 ° | body1/2/3 평균N | 손목 mm/° | CPU6gate |','|---|---|---|---|---|---|']
    fmt=lambda v:', '.join('%.5f'%x for x in v)
    for mode,c in cases.items():
        p=c['env0_trace']['phases'].get('audible',{});m=p.get('metric_mean')
        if m:lines.append('| %s | %s | %s | %s | %s | %s |'%(mode,fmt(m[:4]),fmt(m[4:8]),fmt(m[12:15]),fmt(m[15:17]),str(p['CPU_gate_counts'])))
    lines+=['','선택4 actual/target·손목·세마디합력의 음전/음중/음후 표본과 CPU helper의 loaded/position/facing/positive/candidate/wrong 재구성을 JSON/CSV에 보존했다. candidate/wrong 불일치와 nearest 잔차도 숨기지 않는다. gate는 이전 endpoint 상태를 다음 control에 적용하며 저장 env0 clock과 이를 교차검산했다.',
        '전128 통계는 원음원장과 작은 제어sidecar이고 상세힘/기하/추종은 env0 첫시도 60Hz 끝점뿐이다. 몸체합력은 접촉쌍압력·motor torque·240Hz 최대하중이 아니며 나머지127 상세힘을 추정하지 않는다.',
        '이는 frozen B300에 가한 closed-loop 진단개입이다. 관측과 이후 NN행동도 달라질 수 있으므로 fixed-tape 단일인과, 자연스러움, 새 학습성과·기본제어 채택으로 확대하지 않는다. old 중지 normal-projection 시험과 동일조건이라고 주장하지 않는다. 추가 문턱/보상/학습/GPU실험은 없다.','',
        '![env0 추종과 몸체합력](env0_tracking.png)']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true');p.add_argument('--self-test',action='store_true');args=p.parse_args()
    if args.self_test:self_test()
    elif args.root_completed:actual_main()
    else:print('Prepared only; wait for root completed2scene handoff. No actual raw read.')
