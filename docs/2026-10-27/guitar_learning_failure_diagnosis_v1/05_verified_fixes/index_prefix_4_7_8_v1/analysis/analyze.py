"""CPU-only3note prefix analysis; actual reads require root completion handoff."""
import argparse
import csv
import copy
from dataclasses import asdict
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root-completed',action='store_true');args=parser.parse_args()
    if not args.root_completed:
        print('준비만 완료: root 실제 종료 통보 전 actual 자료·결과를 읽지 않습니다.');return
    probe=module('prefix_analysis_probe',BASE/'probe.py');grid=probe.grid
    sys.path.insert(0,str(grid.ROOT));out=HERE/'results_v1';probe.cap.reject_existing(out)
    inputs,verified={},{}
    def track(path):
        path=Path(path);inputs[str(path)]=grid.sha(path);return path
    def read(path):return grid.read(track(path))
    def pins(mapping):
        for path,digest in mapping.items():
            if path not in verified:verified[path]=grid.sha(path)
            assert verified[path]==digest,path
    seal,paths=probe.gate()
    for path in paths:track(path)
    pins(seal['input_pins']);read(BASE/'preparation_seal.json');review=read(BASE/'review.json');pins(review['reviewed_sha256'])
    assert review['verdict']=='PASS' and not review['findings']
    launcher=read(BASE/'01_launcher.json');assert launcher['completed'] and launcher['returncode']==0 and len(launcher['children'])==1
    child=launcher['children'][0];separate=read(BASE/'01_index_launcher.json');command=read(BASE/'cpu_inputs/commands.json')[0]['argv']
    assert child['finger']=='index' and child['control']=='reference' and child['returncode']==separate['returncode']==0 and child['argv']==separate['argv']==command
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    from guitar_learning.gpu.simplified_finger_environment import REWARD_TERMS
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    folder=BASE/'runs/index';config=read(folder/'settings.json');assert config==read(BASE/'cpu_inputs/index_settings.json')
    short=config['song']['short_learning'];view=short['view'];indices=[4,7,8]
    assert view['source_indices']==indices and view['duration_ticks']==354
    report,scene=read(folder/'report.json'),read(folder/'gpu_scene_final.json')
    assert all(report[k] for k in ('completed','closed','scene_valid','loader_restored','no_NN_checkpoint_training')) and report['failure'] is None and not report['close_errors']
    assert report['assigned_first_attempts']==4 and report['cap_Nm']==.25 and not report['changed_inputs'] and not report['unpinned_project_sources']
    assert scene['closed'] and scene['environment_count']==4 and scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
    assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==4
    assert scene['physics_steps']==report['resources']['physics_steps']==4*report['resources']['control_ticks'] and report['resources']['control_ticks']<=354
    scope=read(folder/'prefix_scope_report.json');assert scope['completed'] and scope['failure'] is None and scope['task_verified'] and scope['aliases_restored'] and not scope['cleanup_errors']
    task=read(folder/'prefix_native_task.json');assert task['expected_environment_exact'] and task['original67_targets_exact'] and task['focus_indices']==indices and task['source_view']==view
    native=read(folder/'native_effort_readback.json');assert native==read(probe.base.FRESH/'runs/index/native_effort_readback.json')
    contract=read(folder/'training_contract.json');assert contract['native_backend']['diagnostic_native_effort']==native and contract['task']['short_learning']==short
    before,after=read(folder/'inputs_before.json'),read(folder/'inputs_after.json');pins(before)
    assert after['verified'] and before==after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
    evaluation=read(folder/'evaluation.json');episodes=evaluation['episodes'];assert grid.complete(episodes,4) and evaluation['assigned_quotas']==[1]*4 and evaluation['policy_performance'] is False
    assert evaluation['summary']==summary(episodes) and all(len(e['notes'])==3 and len(e['reward_components'])==9 and e['selected_target_count']==3 for e in episodes)
    reward_checks=[]
    for episode in episodes:
        components=episode['reward_components'];assert set(components)==set(REWARD_TERMS)
        assert np.isfinite([episode['reward'],*components.values()]).all()
        residual=episode['reward']-sum(components.values())
        scale=float(np.finfo(np.float32).eps)*max(1,4*episode['steps'])*len(REWARD_TERMS)*max(1.,sum(abs(v) for v in components.values()))
        reward_checks.append(dict(env_id=episode['env_id'],reward=episode['reward'],component_sum=sum(components.values()),residual=residual,
            float32_accumulation_reference_scale=scale,within_reference_scale=abs(residual)<=scale,
            scope='roundoff reference scale from dtype/physics count/9terms/totals; not a rigorous cancellation error bound or music gate'))
    provider=read(folder/'action_provider.json');assert provider['control']=='reference' and provider['NN'] is False and provider['training_updates']==0
    recomputed=probe.postcheck(folder);assert recomputed==read(folder/'prefix_acceptance.json')
    metadata,_=fixture(1);meta=read(folder/'trace_metadata.json');assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names'] and meta['source_indices']==indices
    metadata['action_contract']=contract['action']['target_contract'];extra=probe.support()
    env=extra.PrefixEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
    assert env.contract==read(BASE/'cpu_inputs/expected_environment.json')
    assert [asdict(t) for t in env.task.targets]==read(BASE/'cpu_inputs/source_task.json')['targets']
    with np.load(track(folder/'trace_env0_episode0.npz')) as saved:t=dict(saved)
    e0=next(e for e in episodes if e['env_id']==0);assert len(t['time_s'])==e0['steps']<=354 and abs(t['time_s'][0]-1/60)<1e-8
    assert t['candidate'].shape==t['wrong'].shape==(len(t['time_s']),3)
    assert np.all(np.diff(np.rint(t['time_s']*240))==4)
    np.testing.assert_allclose(t['source_time_s'],t['time_s']+view['score_offset_s'],rtol=0,atol=1e-8)
    for col,note in enumerate(e0['notes']):
        assert note['released']==bool(t['released'][-1,col]) and note['release_s']==float(t['release_s'][-1,col])
    arm_helper=module('prefix_arm_helper',BASE.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py')
    track(BASE.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py')
    finite=all(np.isfinite(t[k]).all() for k in ('q','target','body_state','net_body_force_n'))
    notes={};gates=[];height=[];distance=[];mismatches=[];wrong_sources=[]
    if finite:
        def snapshot(k):return dict(q=torch.tensor(t['q'][k:k+1]),qd=torch.zeros(1,105),target=torch.tensor(t['target'][k:k+1]),body_state=torch.tensor(t['body_state'][k:k+1]),contact_force=torch.tensor(t['net_body_force_n'][k:k+1]))
        env.reset([0],snapshot(0))
        expected=torch.zeros_like(env.focus_mask);expected[:,indices]=True;assert torch.equal(expected,env.focus_mask)
        for k,now in enumerate(t['time_s']):
            env.clock[0]=round(now*240);env._snapshot(snapshot(k))
            cg=env.candidate[0,indices].numpy();wg=env.wrong[0,indices].numpy()
            if not np.array_equal(cg,t['candidate'][k]) or not np.array_equal(wg,t['wrong'][k]):mismatches.append(dict(endpoint=k,time_s=float(now),CPU_candidate=cg.tolist(),CPU_wrong=wg.tolist(),saved_candidate=t['candidate'][k].tolist(),saved_wrong=t['wrong'][k].tolist()))
            gates.append(np.array([v[0,indices].numpy() for v in (env.surface_body_loaded,env.contact_geometry,env.contact_facing,env.contact_loaded_target,env.candidate,env.wrong)]).T)
            height.append(env.surface_height[0,indices].numpy()-t['surface_height_m'][k]);distance.append(env.surface_distance[0,indices].numpy()-t['surface_distance_m'][k])
            wrong_sources.append(env.wrong_source_flags[0,indices].numpy().copy())
        qids=[metadata['joint_names'].index(n) for n in short['learned_action_names']]
        bodies=[metadata['body_names'].index('human/LH:index'+str(i)) for i in (1,2,3)]
        wrist,guitar=[metadata['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')]
        rg=Rotation.from_quat(t['body_state'][:,guitar,3:7]);goal=t['wrist_position_goal_G_m']
        position=np.linalg.norm(t['body_state'][:,guitar,:3]+rg.apply(goal)-t['body_state'][:,wrist,:3],axis=-1)*1000
        angle=np.rad2deg((rg*Rotation.from_quat(t['wrist_quaternion_goal_G_xyzw'])*Rotation.from_quat(t['body_state'][:,wrist,3:7]).inv()).magnitude())
        data=np.c_[np.rad2deg(t['q'][:,qids]),np.rad2deg(t['target'][:,qids]),np.rad2deg((t['target']-t['q'])[:,qids]),np.linalg.norm(t['net_body_force_n'][:,bodies],axis=-1),position,angle]
    for col,target in enumerate(view['source_targets']):
        rows=[dict(e['notes'][col],env_id=e['env_id'],termination=e['termination']) for e in episodes]
        acceptance=probe.cap.repro.acceptance(rows);assert acceptance==recomputed['per_note_original_acceptance'][target['target_id']]
        entry=dict(acceptance=acceptance,source_index=indices[col],target=target,phases={},released=[dict(env_id=e['env_id'],released=e['notes'][col]['released'],release_s=e['notes'][col]['release_s']) for e in episodes])
        if finite:
            masks=grid.phase_masks(t['source_time_s'],target['onset_s'],target['end_s'])
            for name,mask in zip(('before','audible','after'),masks):
                values=data[mask];entry['phases'][name]=dict(samples=int(mask.sum()),metric_mean=values.mean(0).tolist() if len(values) else None,metric_max=values.max(0).tolist() if len(values) else None,
                    body_resultant_p95_N=np.percentile(values[:,12:15],95,axis=0).tolist() if len(values) else None,CPU_gate_counts=np.asarray(gates)[mask,col].sum(0).tolist(),saved_candidate_wrong=[int(t['candidate'][mask,col].sum()),int(t['wrong'][mask,col].sum())],CPU_wrong_source_counts=np.asarray(wrong_sources)[mask,col].sum(0).tolist())
            local_config=copy.deepcopy(config);local_config['song']['short_learning']['view']['source_target']=target
            entry['source4_candidate_during_this_audible']=int(t['candidate'][masks[1],0].sum())
            entry['arm']=arm_helper.arm_audit(t,metadata,local_config,contract['action']['target_contract'])
        release=e0['notes'][col];after_end=np.flatnonzero((t['source_time_s']>=target['end_s'])&~t['candidate'][:,col])
        entry['env0_release_vs_saved_candidate']=dict(released=release['released'],native_release_s=release['release_s'],first_saved_off_after_end_s=float(t['source_time_s'][after_end[0]]) if len(after_end) else None,scope='native240Hz latch vs sampled60Hz off; no interpolation or new success gate')
        if release['released']:
            assert target['end_s']<=release['release_s']<=target['end_s']+.1
            np.testing.assert_allclose((release['release_s']-view['score_offset_s'])*240,round((release['release_s']-view['score_offset_s'])*240),rtol=0,atol=1e-8)
        notes[target['target_id']]=entry
    assert recomputed['prefix_passed']==all(n['acceptance']['passed'] for n in notes.values())
    track(Path(__file__).resolve());track(HERE/'PLAN.md');out.mkdir()
    result=dict(prefix=recomputed,reward_checks=reward_checks,summary=evaluation['summary'],episodes=episodes,notes=notes,env0_endpoints=len(t['time_s']),finite_trace=finite,
        CPU_candidate_wrong_mismatches=mismatches,height_residuals_over_1um=[dict(endpoint=k,column=j,residual_m=float(v)) for k,row in enumerate(height) for j,v in enumerate(row) if abs(v)>1e-6],distance_residuals_over_1um=[dict(endpoint=k,column=j,residual_m=float(v)) for k,row in enumerate(distance) for j,v in enumerate(row) if abs(v)>1e-6],
        metric_order=['actual4_deg','target4_deg','target_minus_actual4_deg','body1_2_3_resultant_N','wrist_mm_deg'],CPU_gate_order=['loaded','position','position_facing','positive','candidate','wrong'],
        CPU_wrong_source_body_order=['thumb2','thumb3','index2','index3','middle2','middle3','ring2','ring3','pinky2','pinky3'],
        CPU_wrong_source_cause_order=['other_higher','own_wrong_fret','own_wrong_string'])
    grid.write(out/'comparison.json',result)
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,attempts=4,note_attempts=12,reward_nine_original_keys_finite=True,reward_component_sum_max_abs_residual=max(abs(r['residual']) for r in reward_checks),reward_residuals_within_float32_reference_scale=all(r['within_reference_scale'] for r in reward_checks),original67_targets=True,native105_cap90pairs=True,sceneclosed=True,
        known_limits=['다른finger5/6/9/10 제외 조건부prefix; 고정기타/noNN/동일seed7 4환경','env0 detail60Hz only; nativeqd/other3 detailforce/240Hz geometry not reconstructed','nearest native sample/normalcos missing; tie/scalar residuals preserved','bodyforce notpairpressure; native release vs60Hz off doesnot prove contactpair or acoustic release','single-note positives andactualprefix distinct; no learned/freeguitar/J33/naturalness/adoption claim']))
    with (out/'notes.csv').open('x',newline='') as file:
        rows=[dict(env_id=e['env_id'],source_index=n['source_index'],target_id=n['target_id'],achieved=n['achieved'],clean=n['clean_fraction'],wrong=n['audible_wrong_fraction'],released=n['released'],release_s=n['release_s'],physical_failure=e['termination']['physical_failure'],wrist_failure=e['termination']['wrist_failure']) for e in episodes for n in e['notes']]
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    lines=['# 검지 source4→7→8 실제 prefix 결과','',f"원 각음 수용 기준의3개 AND: **{recomputed['prefix_passed']}**. 네 첫시도 중3음 모두달성 {recomputed['all3_achieved_attempts']}/4.",'', '| 원 source | 달성/4 | clean/wrong | 물리/손목실패 | env0 음중표본 | body1/2/3 평균N | actual4 ° | target4 ° | wrist mm/° | candidate/wrong |','|---|---:|---|---|---:|---|---|---|---|---|']
    fmt=lambda v:', '.join('%.4f'%x for x in v)
    for target,entry in notes.items():
        a=entry['acceptance'];p=entry['phases'].get('audible',{});m=p.get('metric_mean')
        lines.append('| %s | %d/4 | %.6f/%.6f | %d/%d | %s | %s | %s | %s | %s | %s |'%(target,a['achieved'],a['mean_clean'],a['mean_wrong'],a['physical_failures'],a['wrist_failures'],p.get('samples','미확인'),fmt(m[12:15]) if m else '미확인',fmt(m[:4]) if m else '미확인',fmt(m[4:8]) if m else '미확인',fmt(m[15:17]) if m else '미확인',p.get('saved_candidate_wrong')))
    lines+=['','| source | 음중 CPU6gate | 몸체별 wrong flag합계: other_higher/fret/string | 해당음창 source4 candidate |','|---|---|---|---|']
    for target,entry in notes.items():
        phase=entry['phases'].get('audible',{});flags=phase.get('CPU_wrong_source_counts')
        causes=np.asarray(flags).sum(0).tolist() if flags is not None else None
        lines.append('| %s | %s | %s | %s |'%(target,phase.get('CPU_gate_counts'),causes,entry.get('source4_candidate_during_this_audible')))
    lines+=['', '4 episode 원9보상 키/finite 확인; reward−9항합 최대잔차 %.9g. dtype/physics수/9항·합계규모 기반 float32 참고척도 이내: %s(정식상쇄오차증명·새음악gate 아님).'%(max(abs(r['residual']) for r in reward_checks),all(r['within_reference_scale'] for r in reward_checks)),'','wrong flag는10몸체별합계로동시중복가능하며candidate개수/접촉쌍인증이아니다. 원6gate 순서는 loaded/position/position_facing/positive/candidate/wrong이다.','', '원67행과선택3음/offset2.4497/354tick상한을보존했다. 각음수용기준은기존4/4·clean≥.70·wrong≤.10·fail0이고전체는세개AND이다. 다른finger5/6/9/10 제외조건부/noNN/고정기타/동일seed7의4환경이다. 9보상은각episode원합계이며음별재분배하지않았다.','',
        '목표wrist는Aend→B공유press 사이선형전환, 원2초초기ramp/quat/arm12/선택4reference는유지한다. source7/8무음gap에서강제해제하지않았다. 원native released/release_s와60Hz candidate-off는 comparison.json에별도보존했으며해제를새성공gate로쓰지않았다.','',
        'CPU6gate·nearest scalar잔차·팔requested/target/actualbounds·PIP/DIP실제각/목표gap은comparison.json에기록했다. env0의60Hz자료범위이며다른3환경상세힘/nativeqd/240Hz기하나접촉쌍·현압력은추정하지않는다. 단음긍정자료와이번3음전환결과를구분하며NN학습·자유기타/J33·전곡·자연성·생산채택으로확대하지않는다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    if finite:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axes=plt.subplots(3,1,figsize=(8,6),sharex=True)
        for j,label in ((2,'PIP'),(3,'DIP')):
            axes[0].plot(t['time_s'],data[:,j],label=label+' actual');axes[0].plot(t['time_s'],data[:,4+j],'--',label=label+' target')
        for j in range(3):axes[1].plot(t['time_s'],data[:,12+j],label='index'+str(j+1))
        axes[2].plot(t['time_s'],position,label='wrist position error')
        for axis in axes:
            for target in view['source_targets']:axis.axvspan(target['onset_s']-view['score_offset_s'],target['end_s']-view['score_offset_s'],alpha=.08,color='green')
            axis.legend(fontsize=7);axis.grid(alpha=.2)
        axes[0].set_ylabel('deg');axes[1].set_ylabel('body resultant N');axes[2].set_ylabel('wrist error mm');axes[2].set_xlabel('local endpoint seconds')
        fig.tight_layout();fig.savefig(out/'prefix.png',dpi=140);plt.close(fig)
    print(recomputed)


if __name__=='__main__':main()
