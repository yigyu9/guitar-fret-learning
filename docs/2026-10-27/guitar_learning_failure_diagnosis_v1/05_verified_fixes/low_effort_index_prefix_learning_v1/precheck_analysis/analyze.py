"""CPU-only prefix precheck audit; actual reads require root completion handoff."""
import argparse
import copy
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
CONTROLS=('reference','zero','random')
INDICES=(4,7,8)


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value


def acceptance(rows):
    assert len(rows)==128 and sorted(r['env_id'] for r in rows)==list(range(128))
    assert all(r['selected_target_count']==len(r['notes'])==3 for r in rows)
    assert all(bool(r['achieved'])==all(n['achieved'] for n in r['notes']) for r in rows)
    per=[]
    for col,index in enumerate(INDICES):
        notes=[r['notes'][col] for r in rows];assert all(n['source_index']==index for n in notes)
        a=sum(n['achieved'] for n in notes)/128;c=sum(n['clean_fraction'] for n in notes)/128;w=sum(n['audible_wrong_fraction'] for n in notes)/128
        per.append(dict(source_index=index,achieved_fraction=a,mean_clean_fraction=c,mean_wrong_fraction=w,passed=a>=.9 and c>=.9 and w<=.1))
    a=sum(r['achieved'] for r in rows)/128;p=sum(r['termination']['physical_failure'] for r in rows);w=sum(r['termination']['wrist_failure'] for r in rows)
    released=sum(r['notes'][0]['released'] for r in rows)/128;music=all(n['passed'] for n in per) and a>=.9 and p==w==0
    return dict(attempts=128,note_opportunities=384,per_note=per,all3_achieved_fraction=a,physical_failures=p,wrist_failures=w,
        A_released_fraction=released,music_passed=music,release_passed=released>=.9,stage_ready=music and released>=.9)


def launcher_check(value,commands):
    assert value['completed'] and value['returncode']==0 and len(value['children'])==3
    assert [c['control'] for c in value['children']]==list(CONTROLS)
    assert all(c['returncode']==0 and c['argv']==a for c,a in zip(value['children'],commands))


def self_check():
    rows=[dict(env_id=i,selected_target_count=3,achieved=True,termination=dict(physical_failure=False,wrist_failure=False),
        notes=[dict(source_index=j,achieved=True,clean_fraction=1.,audible_wrong_fraction=0.,released=True) for j in INDICES]) for i in range(128)]
    assert acceptance(rows)['stage_ready']
    for i in range(13):rows[i]['notes'][0]['released']=False
    assert acceptance(rows)['music_passed'] and not acceptance(rows)['release_passed']
    rows[12]['notes'][0]['released']=True;assert acceptance(rows)['stage_ready']
    rows[0]['termination']['physical_failure']=True;assert not acceptance(rows)['music_passed'] and acceptance(rows)['release_passed']
    for r in rows:
        r['achieved']=False;r['notes'][1]['achieved']=False
    assert not acceptance(rows)['stage_ready'] and acceptance(rows)['attempts']==128
    try:acceptance(rows[:-1])
    except AssertionError:pass
    else:raise AssertionError('Incomplete quota admitted')
    command=[['case',c] for c in CONTROLS];value=dict(completed=True,returncode=0,children=[dict(control=c,returncode=0,argv=a) for c,a in zip(CONTROLS,command)])
    launcher_check(value,command);value['children'][2]['returncode']=1
    try:launcher_check(value,command)
    except AssertionError:pass
    else:raise AssertionError('Failed launcher admitted')
    assert not any(k in sys.modules for k in ('numpy','torch','isaacgym'))
    import numpy as np
    shape=(3,128);flags=('first_attempt','candidate','wrong','prior_failure','reset','finite','eligible','blocked','post_failure')
    g={k:np.zeros(shape,bool) for k in flags};g['first_attempt'][:]=True;g['finite'][:]=True
    g['start_clock']=np.broadcast_to(np.arange(3)[:,None]*4,shape).copy();g['clock']=g['start_clock']+4;g['current_goal']=np.full(shape,4)
    for k in ('old_target_rad','raw_target_rad','final_target_rad','other104_error_rad','memory_error_rad','submit_error_rad','observation_error','box_rate_excess_rad','numerical_tolerance_rad'):g[k]=np.zeros(shape)
    for k in ('candidate','eligible','blocked'):g[k][0,0]=True
    g['raw_target_rad'][0,0]=.01;rows=[dict(env_id=i,steps=3) for i in range(128)]
    view=dict(source_targets=[dict(end_s=t) for t in (3.1,4.7,5.7)],score_offset_s=0.)
    assert guard_audit(g,rows,view)['by_goal']['4']['blocked']==1
    for key in ('first_attempt','current_goal','blocked','final_target_rad','box_rate_excess_rad'):
        bad={k:v.copy() for k,v in g.items()};bad[key][1,1]=False if key=='first_attempt' else 9
        try:guard_audit(bad,rows,view)
        except AssertionError:pass
        else:raise AssertionError('Invalid guard '+key+' admitted')
    assert not any(k in sys.modules for k in ('torch','isaacgym'))
    print('자가검증 PASS: 128분모/음악·해제분리/원실패/90%경계/launcher·guard경계; actual 읽기0')


def guard_audit(g,rows,view):
    import numpy as np
    first=np.asarray(g['first_attempt'],bool);assert first.ndim==2 and first.shape[1]==128 and first.shape[0]<=354
    lengths=np.array([next(r['steps'] for r in rows if r['env_id']==i) for i in range(128)])
    np.testing.assert_array_equal(first,np.arange(len(first))[:,None]<lengths[None])
    expected=np.broadcast_to(np.arange(len(first))[:,None]*4,first.shape)
    np.testing.assert_array_equal(g['start_clock'][first],expected[first]);np.testing.assert_array_equal(g['clock'][first],expected[first]+4)
    end=np.array([n['end_s'] for n in view['source_targets']]);score=g['start_clock']/240+view['score_offset_s']
    available=score[...,None]<end;goal=np.where(available.any(-1),np.array(INDICES)[available.argmax(-1)],-1)
    np.testing.assert_array_equal(g['current_goal'][first],goal[first])
    eligible=first & g['candidate'] & ~g['wrong'] & ~g['prior_failure'] & ~g['reset'] & g['finite']
    np.testing.assert_array_equal(g['eligible'][first],eligible[first])
    blocked=eligible & (g['raw_target_rad']>g['old_target_rad']);np.testing.assert_array_equal(g['blocked'][first],blocked[first])
    np.testing.assert_array_equal(g['final_target_rad'][first],np.where(blocked,g['old_target_rad'],g['raw_target_rad'])[first])
    valid=first & g['finite']
    for key in ('other104_error_rad','memory_error_rad','submit_error_rad','observation_error'):assert (g[key][valid]==0).all(),key
    assert (g['box_rate_excess_rad'][valid]<=g['numerical_tolerance_rad'][valid]).all()
    return dict(first_controls=int(first.sum()),by_goal={str(j):dict(controls=int((first&(goal==j)).sum()),blocked=int((blocked&(goal==j)).sum()),
        negative=int((first&(goal==j)&(g['raw_target_rad']<g['old_target_rad'])).sum())) for j in (*INDICES,-1)},
        prior_failed_controls=int((first&g['prior_failure']).sum()),same_endpoint_failure_controls=int((first&g['post_failure']).sum()),
        scope='first-attempt60Hz only; failure endpoint retained, precontrol eligibility and post-failure labels separate; report whole-episode counts include retries')


def trace_audit(t,metadata,config,rows,contract,extra,arm,control):
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    e0=next(r for r in rows if r['env_id']==0);short=config['song']['short_learning'];view=short['view']
    assert len(t['time_s'])==e0['steps']<=354 and t['candidate'].shape==t['wrong'].shape==(e0['steps'],3)
    np.testing.assert_allclose(t['time_s'],np.arange(1,e0['steps']+1)/60,rtol=0,atol=1e-8)
    np.testing.assert_allclose(t['source_time_s'],t['time_s']+view['score_offset_s'],rtol=0,atol=1e-8)
    for j,n in enumerate(e0['notes']):assert n['released']==bool(t['released'][-1,j]) and n['release_s']==float(t['release_s'][-1,j])
    ids=short['learned_action_indices'];np.testing.assert_array_equal(t['executed_action'][:,ids],t['policy_action'][:,ids])
    if control=='zero':assert not t['policy_action'].any()
    if control=='random':
        assert np.isfinite(t['policy_action']).all() and (abs(t['policy_action'])<1).all()
        assert not t['policy_action'][:,[i for i in range(39) if i not in ids]].any()
    if not all(np.isfinite(t[k]).all() for k in ('q','target','body_state','net_body_force_n')):
        return dict(unavailable='nonfinite saved state; failed first attempt retained; no fabricated geometry/pose',endpoints=e0['steps'])
    env=extra.PrefixLearningEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
    snap=lambda k:dict(q=torch.tensor(t['q'][k:k+1]),qd=torch.zeros(1,105),target=torch.tensor(t['target'][k:k+1]),body_state=torch.tensor(t['body_state'][k:k+1]),contact_force=torch.tensor(t['net_body_force_n'][k:k+1]))
    env.reset([0],snap(0));gates=[];wrong=[];residuals=[];mismatches=[]
    for k,now in enumerate(t['time_s']):
        env.clock[0]=round(now*240);env._snapshot(snap(k))
        cg=env.candidate[0,list(INDICES)].numpy();wg=env.wrong[0,list(INDICES)].numpy()
        if not np.array_equal(cg,t['candidate'][k]) or not np.array_equal(wg,t['wrong'][k]):mismatches.append(k)
        gates.append(np.array([v[0,list(INDICES)].numpy() for v in (env.surface_body_loaded,env.contact_geometry,env.contact_facing,env.contact_loaded_target,env.candidate,env.wrong)]).T)
        wrong.append(env.wrong_source_flags[0,list(INDICES)].numpy().copy())
        for name,field in (('height','surface_height'),('distance','surface_distance')):
            for j,value in enumerate(getattr(env,field)[0,list(INDICES)].numpy()-t['surface_'+name+'_m'][k]):
                if abs(value)>1e-6:residuals.append(dict(endpoint=k,column=j,field=name,CPU_minus_saved_m=float(value)))
    qids=[metadata['joint_names'].index(n) for n in short['learned_action_names']];bodies=[metadata['body_names'].index('human/LH:index'+str(i)) for i in (1,2,3)]
    ai=[contract['action_order'].index(n) for n in short['learned_action_names']]
    low=np.asarray(contract['action_lower_rad'])[ai];high=np.asarray(contract['action_upper_rad'])[ai]
    assert (t['target'][:,qids]>=low-2e-6).all() and (t['target'][:,qids]<=high+2e-6).all()
    assert (abs(np.diff(t['target'][:,qids],axis=0))<=4/60+2e-6).all()
    wrist,guitar=[metadata['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')];rg=Rotation.from_quat(t['body_state'][:,guitar,3:7])
    position=np.linalg.norm(t['body_state'][:,guitar,:3]+rg.apply(t['wrist_position_goal_G_m'])-t['body_state'][:,wrist,:3],axis=-1)*1000
    angle=np.rad2deg((rg*Rotation.from_quat(t['wrist_quaternion_goal_G_xyzw'])*Rotation.from_quat(t['body_state'][:,wrist,3:7]).inv()).magnitude())
    values=np.c_[np.rad2deg(t['q'][:,qids]),np.rad2deg(t['target'][:,qids]),np.rad2deg((t['target']-t['q'])[:,qids]),np.linalg.norm(t['net_body_force_n'][:,bodies],axis=-1),position,angle]
    notes={}
    for j,target in enumerate(view['source_targets']):
        config_one=copy.deepcopy(config);config_one['song']['short_learning']['view']['source_target']=target;phases={}
        masks=(t['source_time_s']<target['onset_s'],(t['source_time_s']>=target['onset_s'])&(t['source_time_s']<target['end_s']),t['source_time_s']>=target['end_s'])
        for phase,mask in zip(('before','audible','after'),masks):
            v=values[mask];phases[phase]=dict(samples=int(mask.sum()),metric_mean=v.mean(0).tolist() if len(v) else None,metric_max=v.max(0).tolist() if len(v) else None,
                body_p95_N=np.percentile(v[:,12:15],95,axis=0).tolist() if len(v) else None,CPU_gate_counts=np.asarray(gates)[mask,j].sum(0).tolist(),
                CPU_wrong_source_counts=np.asarray(wrong)[mask,j].sum(0).tolist(),saved_candidate_wrong=[int(t['candidate'][mask,j].sum()),int(t['wrong'][mask,j].sum())],A_candidate=int(t['candidate'][mask,0].sum()))
        notes[str(target['target_id'])]=dict(phases=phases,arm=arm.arm_audit(t,metadata,config_one,contract))
    return dict(endpoints=e0['steps'],notes=notes,CPU_candidate_wrong_mismatches=mismatches,scalar_residuals_over_1um=residuals,
        metric_order=['actual4_deg','target4_deg','target_minus_actual4_deg','body1_2_3_resultant_N','wrist_mm_deg'],CPU_gate_order=['loaded','position','position_facing','positive','candidate','wrong'],
        wrong_body_order=['thumb2','thumb3','index2','index3','middle2','middle3','ring2','ring3','pinky2','pinky3'],wrong_cause_order=['other_higher','own_wrong_fret','own_wrong_string'],
        scope='env0 first60Hz; other127 detailedforce/nativeqd unavailable; CPU gates do not replay240Hz note integration; native nearestsample/normalcos missing/ties retained')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--self-check',action='store_true');parser.add_argument('--root-completed',action='store_true');args=parser.parse_args()
    if args.self_check:self_check();return
    if not args.root_completed:print('준비만 완료: root 전체 종료 전 actual 자료를 읽거나 결과를 생성하지 않습니다.');return
    out=HERE/'results_v1';assert not out.exists() and not out.is_symlink(),'Existing output refused'
    probe=module('prefix_precheck_analysis_probe',BASE/'probe.py');grid=probe.grid;sys.path.insert(0,str(grid.ROOT));inputs={};verified={}
    def track(p):p=Path(p);inputs[str(p)]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(mapping):
        for p,h in mapping.items():assert grid.sha(p)==h,p;verified[p]=h
    seal,paths=probe.gate('precheck');pins(seal['input_pins'])
    for p in paths:track(p)
    review=read(BASE/'review.json');assert review['verdict']=='PASS' and not review['findings'];pins(review['reviewed_sha256'])
    launcher_check(read(BASE/'01_precheck_launcher.json'),read(BASE/'cpu_inputs/commands.json')['precheck'])
    import numpy as np
    import torch
    from dataclasses import asdict
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    from guitar_learning.gpu.simplified_finger_environment import REWARD_TERMS
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    extra=probe.support();metadata,_=fixture(1);config=read(BASE/'cpu_inputs/settings.json');view=config['song']['short_learning']['view'];assert view['source_indices']==list(INDICES) and view['duration_ticks']==354
    arm_path=BASE.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py';arm=module('prefix_existing_arm_audit',track(arm_path))
    track(BASE/'learning.py');native_expected=read(BASE/'cpu_inputs/effort_declaration128.json');cases={};accepts={};notes=[];attempts=[];residuals=[]
    for control in CONTROLS:
        folder=probe.output('precheck',control);assert read(folder/'settings.json')==config
        report=read(folder/'diagnostic_report.json');scene=read(folder/'gpu_scene_final.json');scope=read(folder/'prefix_learning_report.json')
        assert all(report[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored')) and report['failure'] is None
        assert not any(report[k] for k in ('cleanup_errors','changed_inputs','unpinned_project_sources')) and report['phase']=='precheck' and report['control']==control and report['native_environment_count']==128
        assert scope['completed'] and scope['failure'] is None and all(scope['checks'].values()) and scope['NN_constructors']==0 and scope['reference_N_injected']==(control=='reference')
        assert scene['closed'] and scene['environment_count']==128 and scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128
        assert scene['physics_steps']==report['physics_steps'] and scene['physics_steps']%4==0 and scene['physics_steps']<=354*4
        native=read(folder/'native_effort_readback.json');assert native==native_expected and native['explicit_DOF105_readback_environments']==128 and native['controller_caps_exact']
        contract=read(folder/'training_contract.json');assert contract['task']['short_learning']==config['song']['short_learning'] and contract['native_backend']['diagnostic_native_effort']==native
        before,after=read(folder/'inputs_before.json'),read(folder/'diagnostic_inputs_after.json');pins(before)
        assert after['verified'] and before==after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
        evaluation=read(folder/'evaluation.json');rows=evaluation['episodes'];assert evaluation['condition']==control and evaluation['policy_performance'] is False and evaluation['assigned_quotas']==[1]*128 and grid.complete(rows,128)
        assert evaluation['summary']==summary(rows)
        a=acceptance(rows);original=probe.acceptance(rows);assert all(original[k]==v for k,v in a.items());assert read(folder/'prefix_acceptance.json')==original;accepts[control]=original
        for e in rows:
            components=e['reward_components'];assert set(components)==set(REWARD_TERMS) and np.isfinite([e['reward'],*components.values()]).all()
            residual=e['reward']-sum(components.values());residuals.append(residual)
            attempts.append(dict(control=control,env_id=e['env_id'],achieved=e['achieved'],steps=e['steps'],termination=json.dumps(e['termination']),reward=e['reward'],reward_sum_residual=residual,**components))
            for n in e['notes']:
                if n['released']:
                    target=view['source_targets'][INDICES.index(n['source_index'])];assert target['end_s']<=n['release_s']<=target['end_s']+.1
                    np.testing.assert_allclose((n['release_s']-view['score_offset_s'])*240,round((n['release_s']-view['score_offset_s'])*240),rtol=0,atol=1e-8)
                notes.append(dict(control=control,env_id=e['env_id'],source_index=n['source_index'],target_id=n['target_id'],achieved=n['achieved'],clean=n['clean_fraction'],wrong=n['audible_wrong_fraction'],released=n['released'],release_s=n['release_s'],physical_failure=e['termination']['physical_failure'],wrist_failure=e['termination']['wrist_failure']))
        meta=read(folder/'trace_metadata.json');assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names'] and meta['source_indices']==list(INDICES)
        metadata['action_contract']=contract['action']['target_contract'];env=extra.PrefixLearningEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
        assert env.contract==read(BASE/'cpu_inputs/expected_environment.json') and [asdict(t) for t in env.task.targets]==read(BASE/'cpu_inputs/source_task.json')['targets']
        with np.load(track(folder/'trace_env0_episode0.npz')) as saved:t=dict(saved)
        with np.load(track(folder/'current_goal_DIP60.npz')) as saved:g=dict(saved)
        cases[control]=dict(acceptance=original,summary=evaluation['summary'],episodes=rows,env0=trace_audit(t,metadata,config,rows,contract['action']['target_contract'],extra,arm,control),guard=guard_audit(g,rows,view),reported_guard_all_episode_counts=scope['guard_counts_by_goal'])
        provider=read(folder/'action_provider.json');assert provider['NN'] is False and provider['updates']==0 and provider['seed']==7 and provider['std']==probe.base.pre.STD
    assert len(attempts)==384 and len(notes)==1152 and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    track(Path(__file__).resolve());track(HERE/'PLAN.md');out.mkdir()
    grid.write(out/'comparison.json',dict(cases=cases,attempts=384,note_attempts=1152,NN=False))
    grid.write(out/'acceptance.json',accepts)
    for name,table in (('attempts.csv',attempts),('notes.csv',notes)):
        with (out/name).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,scenes=3,attempts=384,note_attempts=1152,original67_targets=True,native128x105_cap90pairs=True,all_scenes_closed=True,reward_nine_original_keys_finite=True,reward_component_sum_max_abs_residual=max(map(abs,residuals)),limits=['env0 detail60Hz only; other127 detailedforce/nativeqd unavailable','CPU6gates not native240 note replay; nearest tie/absent nativepoint residuals retained','guard report includes retries; first NPZ separately audited','body resultant not pairpressure/torque; no fullskin separation or learned/freeguitar/J33 claim']))
    lines=['# 검지 3음 학습 전 실제 대조','', '| 명령 | source4/7/8 달성률 | 전체3음 달성률 | A release | 음악/해제/AND | 물리/손목실패 |','|---|---|---:|---:|---|---|']
    for c,a in accepts.items():lines.append('| %s | %s | %.6f | %.6f | %s/%s/%s | %d/%d |'%(c,', '.join('%.6f'%n['achieved_fraction'] for n in a['per_note']),a['all3_achieved_fraction'],a['A_released_fraction'],a['music_passed'],a['release_passed'],a['stage_ready'],a['physical_failures'],a['wrist_failures']))
    lines+=['','384첫시도·1152음 모두 실패 포함 원분모다. reference만 학습 진입 판정에 쓰며 zero/random 달성0·실패0을 강제하지 않았다. 원9보상은 episode별 그대로 기록하고 음별로 재배분하지 않았다. 음악과 원native A 해제는 별도이며 AND는 부모 사전계약을 따른다.','', 'env0의 음창별각/목표gap·3마디순힘·손목·팔bounds·CPU6gate·wrong원인은 comparison.json에 보존했다. nearest sample/normalcos와 다른127환경 상세힘은 미저장이며 추정하지 않는다. 실패끝점은 원장과 trace에 남기고 guard의 사전실패와 동일끝점실패를 구분했다.','', '참고 N 명령은 reference에만 쓰며 zero/random은 NN 초기정책과 다르다. same seed128환경이고 자유기타/J33/원곡67음·자연성의 개선 증거로 확대하지 않는다. 몸체순힘은 접촉쌍압력·토크가 아니고 candidate-off/native release는 피부전체분리 인증이 아니다.','', 'actual source+수치 통합 독립검수 전에는 train gate를 열지 않는다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print('CPU actual 분석 완료:',out)


if __name__=='__main__':main()
