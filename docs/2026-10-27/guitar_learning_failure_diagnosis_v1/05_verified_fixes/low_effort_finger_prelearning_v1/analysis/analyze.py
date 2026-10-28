"""CPU audit of ten new no-NN scenes plus two explicitly reused references."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
spec=importlib.util.spec_from_file_location('prelearning_analysis_probe',BASE/'probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
grid=probe.grid


def trace_audit(t,metadata,config,episodes,control,controller=None):
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    short=config['song']['short_learning'];qids=[metadata['joint_names'].index(n) for n in short['learned_action_names']]
    finger={1:'index',2:'middle',3:'ring',4:'pinky'}[short['finger']]
    bodyids=[metadata['body_names'].index('human/LH:'+finger+str(i)) for i in (1,2,3)]
    wrist,guitar=[metadata['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')]
    e0=next(e for e in episodes if e['env_id']==0)
    assert len(t['time_s'])==e0['steps'] and abs(t['time_s'][0]-1/60)<1e-6 and np.all(np.diff(np.rint(t['time_s']*240))==4)
    result=dict(endpoints=len(t['time_s']),other_envs_detailed_force=None,native_qd=t.get('selected_native_qd',None),
        gate_scope='six gates CPU reconstructed from60Hz saved geometry/force, not saved native six-gate trace; anycandidate not nearestpoint witness',phases={})
    if result['native_qd'] is not None:result['native_qd']=dict(scope='reused reference only; native velocity coordinate, not MCP2 qpos derivative',mean=result['native_qd'].mean(0).tolist())
    if not all(np.isfinite(t[k]).all() for k in ('q','target','body_state','net_body_force_n')):
        result['unavailable_reason']='Nonfinite native state in first-attempt trace; ledger/failure denominator retained, no fabricated geometry.';return result
    rg=Rotation.from_quat(t['body_state'][:,guitar,3:7]);pos=t['body_state'][:,guitar,:3]+rg.apply(t['wrist_goal_G_m'])-t['body_state'][:,wrist,:3]
    angle=(rg*Rotation.from_quat(t['wrist_goal_G_xyzw'])*Rotation.from_quat(t['body_state'][:,wrist,3:7]).inv()).magnitude()
    data=np.c_[np.rad2deg(t['q'][:,qids]),np.rad2deg(t['target'][:,qids]),np.rad2deg((t['target']-t['q'])[:,qids]),np.linalg.norm(t['net_body_force_n'][:,bodyids],axis=-1),np.linalg.norm(pos,axis=-1)*1000,np.rad2deg(angle)]
    env=ShortEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
    def snapshot(k):return dict(q=torch.tensor(t['q'][k:k+1]),qd=torch.zeros(1,105),target=torch.tensor(t['target'][k:k+1]),body_state=torch.tensor(t['body_state'][k:k+1]),contact_force=torch.tensor(t['net_body_force_n'][k:k+1]))
    env.reset([0],snapshot(0));gates=[];mismatch=[];height=[];distance=[];wrong_sources=[];fret_min=[];fret_max=[]
    for k,now in enumerate(t['time_s']):
        env.clock[0]=round(now*240);env._snapshot(snapshot(k));j=env.selected_index
        pair=[bool(env.candidate[0,j]),bool(env.wrong[0,j])]
        if pair!=[bool(t['candidate'][k]),bool(t['wrong'][k])]:mismatch.append(dict(endpoint=k,time_s=float(now),saved=[bool(t['candidate'][k]),bool(t['wrong'][k])],CPU=pair))
        gates.append([bool(v[0,j]) for v in (env.surface_body_loaded,env.contact_geometry,env.contact_facing,env.contact_loaded_target,env.candidate,env.wrong)])
        height.append(float(env.surface_height[0,j])-float(t['surface_height_m'][k]));distance.append(float(env.surface_distance[0,j])-float(t['surface_distance_m'][k]))
        if finger=='pinky':
            wrong_sources.append(env.wrong_source_flags[0,j].tolist());fret_min.append(env.wrong_source_fret_min[0,j].tolist());fret_max.append(env.wrong_source_fret_max[0,j].tolist())
    source=short['view']['source_target'];masks=grid.phase_masks(t['source_time_s'],source['onset_s'],source['end_s'])
    for phase,mask in zip(('before','audible','after'),masks):
        d=data[mask];result['phases'][phase]=dict(samples=int(mask.sum()),metric_mean=d.mean(0).tolist() if len(d) else None,
            metric_max=d.max(0).tolist() if len(d) else None,selected_body_resultant_p95_N=np.percentile(d[:,12:15],95,axis=0).tolist() if len(d) else None,
            CPU_gate_counts=np.asarray(gates)[mask].sum(0).tolist(),saved_candidate_wrong_counts=[int(t['candidate'][mask].sum()),int(t['wrong'][mask].sum())])
        if finger=='pinky':
            flags=np.asarray(wrong_sources)[mask];lo=np.asarray(fret_min)[mask];hi=np.asarray(fret_max)[mask]
            result['phases'][phase]['CPU_wrong_sources']=dict(body_order=['thumb2','thumb3','index2','index3','middle2','middle3','ring2','ring3','pinky2','pinky3'],
                cause_order=['other_higher','own_wrong_fret','own_wrong_string'],counts=flags.sum(0).tolist(),
                active_fret_min=[int(lo[:,b][flags[:,b].any(-1)].min()) if flags[:,b].any() else None for b in range(10)],
                active_fret_max=[int(hi[:,b][flags[:,b].any(-1)].max()) if flags[:,b].any() else None for b in range(10)],
                target_string_0based=int(env.string[j]),target_fret_1based=int(env.fret[j]),scope='CPU cause flags from saved env0 snapshot, not separately logged native provenance; causes may overlap across samples')
    result.update(metric_order=[part+str(i)+'_deg' for part in ('actual_q','target_q','target_minus_actual_q') for i in range(4)]+['body1_resultant_N','body2_resultant_N','body3_resultant_N','wrist_position_mm','wrist_rotation_deg'],
        CPU_gate_order=['loaded','position','position_facing','positive','candidate','wrong'],candidate_wrong_mismatches=mismatch,
        height_residuals_over_1um=[dict(endpoint=k,CPU_minus_saved_m=v) for k,v in enumerate(height) if abs(v)>1e-6],
        distance_residuals_over_1um=[dict(endpoint=k,CPU_minus_saved_m=v) for k,v in enumerate(distance) if abs(v)>1e-6],
        nearest_scope='native sample index/normalcos endpoint missing; residual listings preserve saved scalar values and original tie limitations')
    ids=short['learned_action_indices']
    if 'policy_action' in t:assert np.array_equal(t['executed_action'][:,ids],t['policy_action'][:,ids])
    if control=='zero':assert not t['policy_action'].any()
    if control=='random':
        assert np.isfinite(t['policy_action']).all() and (abs(t['policy_action'])<1).all()
        assert not t['policy_action'][:,[i for i in range(39) if i not in ids]].any()
    if finger=='pinky' and controller is not None and masks[1].any():
        names=[g+'_'+a for g in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist') for a in 'xyz'];q=[metadata['joint_names'].index(n) for n in names];ai=[controller['action_order'].index(n) for n in names]
        low=np.asarray(controller['action_lower_rad'])[ai];high=np.asarray(controller['action_upper_rad'])[ai];audible=masks[1];arm={}
        for kind,values in [('request',t['wrist_requested_arm_rad'][audible]),('target',t['target'][audible][:,q]),('actual',t['q'][audible][:,q])]:
            arm[kind]=[dict(joint=n,lower=int((values[:,i]<=low[i]+1e-6).sum()),upper=int((values[:,i]>=high[i]-1e-6).sum())) for i,n in enumerate(names) if (values[:,i]<=low[i]+1e-6).any() or (values[:,i]>=high[i]-1e-6).any()]
        error=np.rad2deg(abs((t['target']-t['q'])[audible][:,q]));arm['largest_target_minus_actual_deg']=float(error.max());arm['largest_error_axis']=names[np.unravel_index(error.argmax(),error.shape)[1]]
        result['pinky_arm_supplement']=arm
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root-completed',action='store_true');args=parser.parse_args()
    if not args.root_completed:
        print('Prepared only; no actual result read. Wait for root ten-scene exit.');return
    sys.path.insert(0,str(probe.ROOT));out=HERE/'results_v1';probe.cap.reject_existing(out)
    inputs,verified={},{}
    def track(p):p=Path(p);inputs[str(p)]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(values):
        for p,h in values.items():
            if p not in verified:verified[p]=grid.sha(p)
            assert verified[p]==h,p
    seal,paths=probe.gate()
    for p in paths:track(p)
    pins(seal['input_pins']);read(BASE/'preparation_seal.json')
    prep=read(BASE/'review.json');assert prep['verdict']=='PASS' and not prep['findings'];pins(prep['reviewed_sha256'])
    for root in (probe.FRESH/'analysis/results_v1',probe.cap.HERE/'analysis/results_v1'):
        review=read(root/'review.json');assert review['verdict']=='PASS' and not review['findings'];pins(review['reviewed_sha256'])
        v=read(root/'verification.json')
        for k in ('input_sha256','verified_input_sha256'):pins(v[k])
    launcher=read(BASE/'01_launcher.json');assert launcher['completed'] and launcher['returncode']==0 and len(launcher['children'])==10
    assert [(c['finger'],c['control']) for c in launcher['children']]==probe.JOBS and all(c['returncode']==0 for c in launcher['children'])
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    torch.set_num_threads(1);metadata,_=fixture(1)
    baseline_native=read(probe.cap.HERE/'runs/middle/native_effort_readback.json');cases={};table=[];new_count=0
    for finger in probe.INPUTS:
        expected=probe.settings(finger)
        for control in ('reference','zero','random'):
            reused=finger in ('index','middle') and control=='reference'
            folder=(probe.FRESH/'runs/index' if finger=='index' else probe.cap.HERE/'runs/middle') if reused else BASE/'runs'/(finger+'_'+control)
            if not reused:
                launch=read(BASE/('01_'+finger+'_'+control+'_launcher.json'));assert launch['finger']==finger and launch['control']==control and launch['returncode']==0;new_count+=4
            config=read(folder/'settings.json');assert config==expected==read(BASE/'cpu_inputs'/(finger+'_settings.json'))
            report,scene=read(folder/'report.json'),read(folder/'gpu_scene_final.json')
            assert all(report[k] for k in ('completed','closed','scene_valid','loader_restored')) and report['failure'] is None
            assert not report['changed_inputs'] and not report['unpinned_project_sources']
            assert report.get('close_failure') is None and not report.get('close_errors',[])
            assert report['assigned_first_attempts']==4 and report['cap_Nm']==.25
            assert report.get('no_NN_checkpoint_training',report.get('no_NN_checkpoint'))
            assert scene['closed'] and scene['environment_count']==4 and scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
            assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==4
            assert scene['physics_steps']==report['resources']['physics_steps']==4*report['resources']['control_ticks']
            assert report['resources']['control_ticks']<=config['song']['short_learning']['view']['duration_ticks']
            native=read(folder/'native_effort_readback.json');assert native==baseline_native
            contract=read(folder/'training_contract.json');assert contract['native_backend']['diagnostic_native_effort']==native
            assert contract['task']['short_learning']==config['song']['short_learning']
            before,after=read(folder/'inputs_before.json'),read(folder/'inputs_after.json');pins(before)
            assert after['verified'] and before==after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
            evaluation=read(folder/'evaluation.json');episodes=evaluation['episodes'];assert grid.complete(episodes,4) and evaluation['assigned_quotas']==[1]*4 and evaluation['policy_performance'] is False
            assert evaluation['summary']==summary(episodes)
            if not reused:
                assert evaluation['condition']==control
                provider=read(folder/'action_provider.json');assert provider['control']==control and provider['NN'] is False and provider['training_updates']==0
                assert provider['seed']==7 and provider['Gaussian_std']==probe.STD and provider['selected_indices']==config['song']['short_learning']['learned_action_indices']
            for e in episodes:
                assert e['selected_target_count']==1 and e['target_id']==config['song']['short_learning']['teacher']['source_target_id'] and len(e['reward_components'])==9
                table.append(dict(finger=finger,control=control,reused=reused,source=str(folder),env_id=e['env_id'],achieved=e['achieved'],clean=e['clean_fraction'],wrong=e['audible_wrong_fraction'],physical_failure=e['termination']['physical_failure'],wrist_failure=e['termination']['wrist_failure'],reason=e['reason'],reward=e['reward'],reward_components=json.dumps(e['reward_components']),note=json.dumps(e['note']),other_envs_detailed_force=None))
            meta=read(folder/'trace_metadata.json');assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
            filename=meta['file'] if reused else 'trace_env0_episode0.npz';t=dict(np.load(track(folder/filename)))
            trace=trace_audit(t,metadata,config,episodes,control,contract['action']['target_contract'])
            if not reused:assert trace['native_qd'] is None
            accept=probe.cap.repro.acceptance(episodes)
            if reused:assert accept==evaluation['acceptance'] and accept['passed']
            cases[finger+'_'+control]=dict(finger=finger,control=control,reused=reused,source=str(folder),acceptance_same_original_rule=accept,episodes=episodes,summary=evaluation['summary'],env0_trace=trace,
                reused_review=str((probe.FRESH if finger=='index' else probe.cap.HERE)/'analysis/results_v1/review.json') if reused else None)
    assert len(cases)==12 and len(table)==48 and new_count==40 and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    track(Path(__file__).resolve());track(HERE/'PLAN.md');out.mkdir()
    grid.write(out/'comparison.json',dict(cases=cases,new_first_attempts=40,reused_first_attempts=8,total_first_attempts=48))
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,new_scenes=10,new_attempts=40,reused_attempts=8,total_attempts=48,
        same_native105_cap90pairs=True,all_scenes_closed=True,trace_scope='env0firstattempt60Hz; failure endpoint retained; sixgates CPUderived, nativeqd new10missing; other3 detailedforce None',
        random_scope='seed7 selected4 independent Gaussian std.1711710544767014 then tanh; noNN; CPU doesnot replay CUDA RNG exact',
        known_limits=['fixedguitar,4envs seed7 not4seeds; no learned/freeguitar claims','body resultant not contactpair/pressure/motor torque','native nearest sample/normalcos missing; ties/mismatches preserved','CPU geometry gates do not reconstruct actual240Hz note integration or native failure history']))
    with (out/'attempts.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    lines=['# 낮은 상한 학습 전 네손가락 대조','', '| 손가락/명령 | 출처 | 달성/전체4 | clean/wrong | 물리/손목실패 |','|---|---|---:|---:|---:|']
    for key,c in cases.items():
        a=c['acceptance_same_original_rule'];lines.append('| %s | %s | %d/4 | %.4f/%.4f | %d/%d |'%(key,'기존자료 재사용' if c['reused'] else '새실행',a['achieved'],a['mean_clean'],a['mean_wrong'],a['physical_failures'],a['wrist_failures']))
    lines+=['','총48원장은새40+기존reference8이며실패도모두포함한다. 같은seed7의4환경이지4seed가아니다. zero는선택4명령0이며팔teacher·비선택B·엄지는유지된다. random은선택4Gaussian→tanh명령으로NN이나원untrained정책exact가아니다. reference검지/중지는새실행이아니다.','',
        '| env0 손가락/명령 | 음중표본 | body1/2/3 평균N | actual4 ° | target4 ° | wrist mm/° | 저장candidate/wrong | CPU6gate |','|---|---:|---|---|---|---|---|---|']
    for key,c in cases.items():
        p=c['env0_trace']['phases'].get('audible',{});m=p.get('metric_mean');fmt=lambda a:', '.join('%.4f'%x for x in a)
        lines.append('| %s | %s | %s | %s | %s | %s | %s | %s |'%(key,p.get('samples','미확인'),fmt(m[12:15]) if m else '미노출/미확인',fmt(m[:4]) if m else '미노출/미확인',fmt(m[4:8]) if m else '미노출/미확인',fmt(m[15:17]) if m else '미노출/미확인',str(p.get('saved_candidate_wrong_counts')),str(p.get('CPU_gate_counts'))))
    lines+=['','힘·각도·손목·CPUgate 상세값은env0의60Hz끝점만설명한다. 다른3환경 상세힘은None이며새10조건 nativeqd는저장되지않아추정하지않았다. CPU6gate는저장native6gate가아니다. nearest tie/미저장sample·normalcos 및candidate/wrong재구성불일치가있으면comparison.json에그대로남겼고원판정/48원장을바꾸지않았다. 원음시계의240Hz지급보상/음원장은실제기록을쓰며60Hz기하로다시지급하지않는다.','',
        '고정기타/noNN 명령대조의달성을손가락정책학습이나자유기타성과로확대하지않는다. 몸체순힘은접촉쌍·실제현압력·motor torque가아니며0.25Nm상한이몸체하중상한을보장하지않는다. source/준비/기존결과를수정하거나추가GPU를실행하지않았다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print('Actual CPU results written:',out)


if __name__=='__main__':main()
