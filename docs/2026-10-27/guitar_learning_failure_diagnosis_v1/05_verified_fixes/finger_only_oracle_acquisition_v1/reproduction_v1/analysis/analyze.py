"""CPU audit of the completed selected-target fresh4 reproduction; no native import."""
import argparse
import csv
import importlib.util
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
spec=importlib.util.spec_from_file_location('oracle_reproduction_probe',BASE/'probe.py')
probe=importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
parent=probe.parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed',action='store_true'); args=parser.parse_args()
    if not args.root_completed:
        print('Prepared only; wait for both actual root GPU exits. No result read.'); return
    sys.path.insert(0,str(parent.ROOT))
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    from guitar_learning.gpu.geometry import apply,conjugate
    from guitar_learning.gpu.press_surface import project_press_strings
    torch.set_num_threads(1)
    out=HERE/'results_v1'; parent.reject_existing(out)
    inputs,verified={},{}
    def read(path):
        inputs[str(path)]=parent.sha(path); return parent.read(path)
    def pins(values):
        for p,h in values.items():
            value=parent.sha(p); assert value==h,p; verified[p]=value
    seal=read(BASE/'preparation_seal.json'); assert seal['independent_review']=='passed_no_findings' and len(seal['input_pins'])==750
    pins(seal['input_pins'])
    launcher=read(BASE/'01_launcher.json'); assert launcher['completed'] and launcher['returncode']==0
    assert [r['finger'] for r in launcher['jobs']]==['index','middle'] and all(r['returncode']==0 for r in launcher['jobs'])
    cases,checks,plots={},{},{}; rows=[]
    metadata,_=fixture(1)
    for finger,selected in probe.SELECTED.items():
        folder=BASE/'runs'/finger; gridfolder=parent.HERE/'runs'/finger
        launch=read(BASE/('01_'+finger+'_launcher.json')); assert launch['returncode']==0
        doc=read(BASE/'cpu_inputs'/(finger+'_targets.json'))
        assert doc==probe.document_for(finger,read(parent.HERE/'cpu_inputs'/(finger+'_grid.json')))
        config=read(folder/'settings.json'); assert config==read(BASE/'cpu_inputs'/(finger+'_settings.json'))==parent.settings(finger,4)
        contract=read(folder/'training_contract.json'); assert contract==read(gridfolder/'training_contract.json')
        report,scene=read(folder/'report.json'),read(folder/'gpu_scene_final.json')
        assert report['completed'] and report['closed'] and report['scene_valid'] and report['failure'] is None and report['close_failure'] is None
        assert not report['changed_inputs'] and not report['unpinned_project_sources'] and report['assigned_first_attempts']==4 and report['selected_grid_index']==selected
        assert report['no_NN_or_checkpoint'] and not list(folder.glob('*.pt'))
        assert scene['closed'] and scene['environment_count']==4 and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and scene['diagnostic_guitar_mode']=='fixed'
        assert scene['hand_collision']==read(gridfolder/'gpu_scene_final.json')['hand_collision']
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==4
        assert scene['physics_steps']==report['resources']['physics_steps']==4*report['resources']['control_ticks']
        assert report['resources']['control_ticks']<=config['song']['short_learning']['view']['duration_ticks']
        before,after=read(folder/'inputs_before.json'),read(folder/'inputs_after.json'); pins(before)
        assert after['verified'] and before==after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
        evaluation=read(folder/'evaluation.json'); statistics=read(folder/'statistics.json')
        episodes=evaluation['episodes']; stats=statistics['rows']
        assert evaluation['assigned_quotas']==[1]*4 and evaluation['policy_performance'] is False
        assert parent.complete(episodes,4) and sorted(s['env_id'] for s in stats)==list(range(4))
        for e,s in zip(episodes,stats):
            expected=doc['rows'][e['env_id']]
            assert e['env_id']==s['env_id'] and e['grid_index']==s['grid_index']==selected
            assert e['attempt_id']==s['attempt_id']==expected['attempt_id']
            assert e['selected_target_count']==1 and e['target_id']==doc['source_target_id']
            assert sum(p['samples'] for p in s['phases'].values())==e['steps']
        assert len({e['attempt_id'] for e in episodes})==4
        accept=probe.acceptance(episodes); assert accept==evaluation['acceptance']
        assert evaluation['summary']==summary(episodes)
        original=read(gridfolder/'statistics.json'); assert all(statistics[k]==original[k] for k in ('phase_order','phase_scope','gate_order','metric_order','scope'))
        old=next(s for s in original['rows'] if s['grid_index']==selected)
        old_episode=next(e for e in read(gridfolder/'evaluation.json')['episodes'] if e['grid_index']==selected)
        assert read(gridfolder/'selection.json')['selected_grid_index']==selected
        cases[finger]=dict(acceptance=accept,unachieved_env_ids=[e['env_id'] for e in episodes if not e['achieved']],document=doc,episodes=episodes,statistics=stats,parent_grid_selected=dict(episode=old_episode,statistics=old),
            comparison_scope='same target and control contract; grid pool envcount/envID differs from fresh4; env-origin floating-point variation possible; not four seeds')
        for s in stats:
            e=episodes[s['env_id']]
            for phase,p in s['phases'].items():
                rows.append(dict(finger=finger,grid_index=selected,env_id=s['env_id'],attempt_id=s['attempt_id'],phase=phase,
                    samples=p['samples'],achieved=e['achieved'],clean=e['clean_fraction'],wrong=e['audible_wrong_fraction'],reason=e['reason'],
                    physical_failure=e['termination']['physical_failure'],wrist_failure=e['termination']['wrist_failure'],
                    gate_counts=json.dumps(p['gate_counts']),mean=json.dumps(p['mean']),maximum=json.dumps(p['max'])))
        meta=read(folder/'trace_metadata.json'); assert meta['env_id']==0 and meta['grid_index']==selected and meta['attempt_id']==doc['rows'][0]['attempt_id']
        assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
        assert meta['wrist_control']==config['song']['short_learning']['wrist_control']
        assert sorted(p.name for p in folder.glob('trace*.npz'))==[meta['file']]
        path=folder/meta['file']; inputs[str(path)]=parent.sha(path); t=np.load(path)
        assert len(t['time_s'])==episodes[0]['steps'] and abs(t['time_s'][0]-1/60)<1e-6
        qids=[meta['joint_names'].index(n) for n in doc['joint_names']]
        bodies=[meta['body_names'].index('human/LH:'+finger+str(i)) for i in (1,2,3)]
        wrist,guitar=[meta['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')]
        instrument=Rotation.from_quat(t['body_state'][:,guitar,3:7])
        position=t['body_state'][:,guitar,:3]+instrument.apply(t['wrist_goal_G_m'])-t['body_state'][:,wrist,:3]
        angle=(instrument*Rotation.from_quat(t['wrist_goal_G_xyzw'])*Rotation.from_quat(t['body_state'][:,wrist,3:7]).inv()).magnitude()
        data=np.c_[np.rad2deg(t['q'][:,qids]),np.rad2deg(t['target'][:,qids]),np.rad2deg((t['target']-t['q'])[:,qids]),
            np.linalg.norm(t['net_body_force_n'][:,bodies],axis=-1),1000*t['surface_distance_m'],1000*t['surface_height_m'],np.zeros(len(t['time_s'])),
            1000*np.linalg.norm(position,axis=-1),np.rad2deg(angle)]
        env=ShortEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
        def snapshot(k):
            return dict(q=torch.tensor(t['q'][k:k+1]),qd=torch.zeros(1,105),target=torch.tensor(t['target'][k:k+1]),
                body_state=torch.tensor(t['body_state'][k:k+1]),contact_force=torch.tensor(t['net_body_force_n'][k:k+1]))
        env.reset([0],snapshot(0)); gates=[]; nearest_differences=[]; height_residuals=[]; distance_residuals=[]
        for k,now in enumerate(t['time_s']):
            env.clock[0]=round(now*240); env._snapshot(snapshot(k)); j=env.selected_index
            assert bool(env.candidate[0,j])==bool(t['candidate'][k]) and bool(env.wrong[0,j])==bool(t['wrong'][k])
            assert abs(float(env.surface_distance[0,j])-t['surface_distance_m'][k])<1e-6
            height_residual=float(env.surface_height[0,j])-t['surface_height_m'][k]
            height_residuals.append(float(height_residual)); distance_residuals.append(float(env.surface_distance[0,j])-float(t['surface_distance_m'][k]))
            if abs(height_residual)>1e-6:
                # Diagnose nearest argmin arithmetic only; do not choose a new native/candidate witness.
                minima={}
                for dtype,label in ((torch.float32,'float32'),(torch.float64,'float64')):
                    body=env.body[:,env.pad_indices].to(dtype); g=env.guitar_body.to(dtype)
                    world=body[:,:,None,:3]+apply(body[:,:,None,3:7],env.pad_local[None].to(dtype))
                    points=apply(conjugate(g[:,None,None,3:7]),world-g[:,None,None,:3])
                    slot=int(env.finger[j])-1; point=points[0,slot]
                    starts,ends=project_press_strings(env.starts.to(dtype),env.ends.to(dtype),env.press_plane.to(dtype))
                    start=starts[0,env.string[j]]; line=ends[0,env.string[j]]-start
                    low=torch.minimum(env.frets[:,:-1,1],env.frets[:,1:,1])[0,env.fret[j]-1].to(dtype)+.002
                    high=torch.maximum(env.frets[:,:-1,1],env.frets[:,1:,1])[0,env.fret[j]-1].to(dtype)-.002
                    bounds=torch.stack(((low-start[1])/line[1],(high-start[1])/line[1]))
                    fraction=(((point-start)*line).sum(-1)/line.square().sum()).clamp(bounds.min().clamp_min(0),bounds.max().clamp_max(1))
                    distance=torch.linalg.vector_norm(start+fraction[:,None]*line-point,dim=-1).masked_fill(~env.pad_valid[slot],torch.inf)
                    ids=distance.argsort()[:3]
                    minima[label]=dict(sample_indices=ids.tolist(),distances_m=distance[ids].tolist(),gap_first_two_m=float(distance[ids[1]]-distance[ids[0]]))
                nearest_differences.append(dict(endpoint=k,local_time_s=float(now),source_time_s=float(t['source_time_s'][k]),
                    saved_height_m=float(t['surface_height_m'][k]),CPU_height_m=float(env.surface_height[0,j]),height_residual_m=height_residual,
                    distance_residual_m=float(env.surface_distance[0,j])-float(t['surface_distance_m'][k]),CPU_surface_sample=int(env.surface_sample[0,j]),CPU_minima=minima))
            data[k,17]=float(env.surface_alignment[0,j])
            gates.append([bool(v[0,j]) for v in (env.surface_body_loaded,env.contact_geometry,env.contact_facing,env.contact_loaded_target,env.candidate,env.wrong)])
        source=config['song']['short_learning']['view']['source_target']
        masks=parent.phase_masks(t['source_time_s'],source['onset_s'],source['end_s']); residual=np.zeros(20); cosine_statistics={}
        for phase,mask in zip(('before','audible','after'),masks):
            p=stats[0]['phases'][phase]; assert int(mask.sum())==p['samples']
            assert np.array_equal(np.asarray(gates)[mask].sum(0),p['gate_counts'])
            if p['samples']:
                for key,value in (('min',data[mask].min(0)),('max',data[mask].max(0)),('mean',data[mask].mean(0)),('rms',np.sqrt((data[mask]**2).mean(0)))):
                    indices=[n for n in range(20) if n!=17]
                    np.testing.assert_allclose(value[indices],np.asarray(p[key])[indices],rtol=5e-6,atol=5e-5)
                    cosine_statistics[phase+'_'+key]=dict(CPU=float(value[17]),saved=float(p[key][17]),residual=float(value[17]-p[key][17]))
                    residual=np.maximum(residual,abs(value-np.array(p[key])))
        checks[finger]=dict(endpoints=len(t['time_s']),candidate_wrong_each_endpoint_match=True,six_phase_gate_counts_match=True,
            all_non_cosine_phase_statistics_match=True,max_abs_residual_by_metric=residual.tolist(),rtol=5e-6,atol=5e-5,
            nearest_height_CPU_differences=nearest_differences,nearest_normal_cos_statistics=cosine_statistics,
            max_nearest_height_abs_residual_m=max(map(abs,height_residuals)),max_nearest_distance_abs_residual_m=max(map(abs,distance_residuals)),
            nearest_difference_listing_threshold_m=1e-6,listing_threshold_scope='diagnostic listing only; no tolerance enlargement or predicate change',
            max_normal_cos_statistic_residual=max(abs(v['residual']) for v in cosine_statistics.values()),
            raw_dtypes={key:str(t[key].dtype) for key in ('body_state','q','net_body_force_n','surface_height_m','time_s')},
            scalar_trace_dtype_scope='body/q/forces originate float32; saved scalar height uses Python float/NumPy float64, not extra native precision; float64 diagnostic promotes frozen float32 geometry parameters',
            nearest_scope='native sample index/normal cosine per endpoint not stored; CPU minima are arithmetic diagnosis only, not native or positive witness identification; raw saved height aggregation remains separate')
        plots[finger]=(t['time_s'],data,np.asarray(gates),masks[1])
    assert len(rows)==24 and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    inputs[str(Path(__file__).resolve())]=parent.sha(Path(__file__).resolve()); inputs[str(HERE/'PLAN.md')]=parent.sha(HERE/'PLAN.md')
    out.mkdir(); parent.write(out/'comparison.json',dict(cases=cases,scope='eight first attempts scripted reproduction only; no policy learning or naturalness certification'))
    parent.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,CUDA_initialized=False,preparation_pins=750,
        actual_input_paths_verified=len(verified),overall_launcher_wall_s=launcher['wall_s'],input_sha256=inputs,verified_input_sha256=verified,total_first_attempts=8,scenes_closed=2,
        trace_checks=checks,total_env0_endpoints=sum(c['endpoints'] for c in checks.values()),phase_scope=statistics['phase_scope'],metric_order=statistics['metric_order'],gate_order=statistics['gate_order'],
        helper_source_sha256={p:h for p,h in verified.items() if any(p.endswith('/'+n) for n in ('gpu/environment.py','gpu/simplified_finger_environment.py','gpu/fingertip_pad.py','gpu/wrong_press.py','tool/experiments/short_finger_learning/runtime.py'))}))
    with (out/'attempts.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(12,6))
    for r,finger in enumerate(probe.SELECTED):
        times,data,gates,audible=plots[finger]
        for i in range(3): axes[r,0].plot(times,data[:,12+i],label='body'+str(i+1))
        axes[r,1].plot(times,data[:,18],label='wrist mm'); axes[r,1].plot(times,data[:,15],label='nearest mm')
        for i in range(4): axes[r,2].plot(times,data[:,8+i],label=cases[finger]['document']['joint_names'][i].split(':')[-1])
        for c in range(3):
            ax=axes[r,c]
            if audible.any(): ax.axvspan(times[audible][0],times[audible][-1],color='gray',alpha=.15)
            ax.set_xlabel('local seconds'); ax.grid(alpha=.2); ax.legend(fontsize=7)
        axes[r,0].set_ylabel(finger+' resultant N'); axes[r,1].set_ylabel('distance mm'); axes[r,2].set_ylabel('native target - actual deg')
    fig.suptitle('env0 first attempt60Hz endpoints; shaded=audible; body resultants are not string pressure')
    fig.tight_layout(); fig.savefig(out/'tracking_load.png',dpi=140); plt.close(fig)
    text=['# 선정 목표4환경 재현 실제 결과','', '**검지115는 %d/4 달성으로 사전 재현 기준 %s, 중지114는 %d/4 달성으로 %s. 원각도+사전 offset의 동일 목표를 각4환경에서 새로 실행했다. NN/정책 학습이 아니며, 음악 판정 재현과 고proximal하중·자연스러움은 별개다.**'%(cases['index']['acceptance']['achieved'],'통과' if cases['index']['acceptance']['passed'] else '미달',cases['middle']['acceptance']['achieved'],'통과했다' if cases['middle']['acceptance']['passed'] else '미달했다'),'',
        '| 손가락/grid | 달성/첫시도 | 평균clean/wrong | 물리/손목실패 | 사전재현기준 |','|---|---:|---:|---:|---|']
    for finger,c in cases.items():
        a=c['acceptance']; text.append('| %s/%d | %d/4 | %.3f%%/%.3f%% | %d/%d | %s |'%(finger,probe.SELECTED[finger],a['achieved'],100*a['mean_clean'],100*a['mean_wrong'],a['physical_failures'],a['wrist_failures'],'통과' if a['passed'] else '미통과'))
    text+=['','분모는 서로 다른env_id의첫시도각1개·총8개이며 조기실패도 제외하지 않는다. 4/4달성·평균clean≥70%·평균wrong≤10%·물리/손목실패0을 재계산했다. 같은seed7의4환경이며4seed가 아니다. 실패 뒤 후보 교체나 기준 완화는 하지 않았다.','',
        '| 손가락 | 원reference각도 | 사전offset도 | 선정최종각도 |','|---|---|---|---|']
    for finger,c in cases.items():
        d=c['document']; text.append('| %s | %s | %s | %s |'%(finger,', '.join('%.4f'%x for x in map(math.degrees,d['original_reference_target_rad'])),str(d['selected_offset_deg']),', '.join('%.4f'%x for x in map(math.degrees,d['selected_target_rad']))))
    for finger,c in cases.items():
        for env_id in c['unachieved_env_ids']:
            e=c['episodes'][env_id]; phase=c['statistics'][env_id]['phases']['audible']; m=phase['mean']
            text+=['','%s env%d는 %s로 첫 시도를 끝냈으나 달성하지 못했다. missing %.1f%%, wrong %.1f%%이며 물리/손목 실패는 없었다. 음중 %d개의60Hz 끝점 gate는%s다. body1/2/3 합력평균%sN은 마디별로 구분하며, 높은 body1 합력을 distal loaded로 대체하지 않는다. 이 환경은 원장과 경량통계만 있고 상세 raw는 없으므로 매끝점 witness나 접촉쌍·인과를 확정하지 않는다.'%(finger,env_id,e['reason'],100*e['missing_fraction'],100*e['audible_wrong_fraction'],phase['samples'],'/'.join(str(x) for x in phase['gate_counts']),', '.join('%.4f'%v for v in m[12:15]) if m else '노출없음')]
    text+=['','각도순서는1_x/1_z/2/3이다. source teacher/reference는 원본 그대로이며 새선정각도를 원source목표라고 바꾸어 쓰지 않았다.','',
        '| 손가락/구분 | audible body1/2/3 평균N | 60Hz 최대N | actual4평균도 | native target4평균도 | 손목mm/도 | nearest mm | gate 끝점 |','|---|---|---|---|---|---|---:|---|']
    for finger,c in cases.items():
        for name,s in [('parent grid env'+str(c['parent_grid_selected']['statistics']['env_id']),c['parent_grid_selected']['statistics'])]+[('fresh env'+str(s['env_id']),s) for s in c['statistics']]:
            p=s['phases']['audible']; m=p['mean']; maximum=p['max']
            if not p['samples']:
                text.append('| %s/%s | 음중노출0 | — | — | — | — | — | %s |'%(finger,name,'/'.join(str(x) for x in p['gate_counts']))); continue
            text.append('| %s/%s | %s | %s | %s | %s | %.4f/%.4f | %.4f | %s |'%(finger,name,', '.join('%.4f'%x for x in m[12:15]),', '.join('%.4f'%x for x in maximum[12:15]),', '.join('%.3f'%x for x in m[:4]),', '.join('%.3f'%x for x in m[4:8]),m[18],m[19],m[15],'/'.join(str(x) for x in p['gate_counts'])))
    text+=['','gate순서는loaded/위치/위치+facing/positive/candidate/wrong다. `attempts.csv`는전체8행의음전/음중/음후24구간을포함한다. 부모grid의선정행과동일목표·제어계약이나 pool환경수와env_id가다르며 env-origin 부동소수점수치변이가능성을포함한다. 차이를정책학습이나단일원인효과로해석하지않는다.','',
        '![env0 추종과 하중](tracking_load.png)','',
        '두env0의새60Hz raw로현재원helper의candidate/wrong·거리·phase별6gate와선택각/힘/추종통계를재계산했다. 저장nearest높이의집계와CPUnearest선택의동일성은분리했다. middle114는이번에env0상세를새로확보했으며부모grid때없던raw를소급작성한것이아니다. 나머지6환경은원ledger와경량통계만있다. nearest 패드값은any-sample positive/candidate witness와동일점을보장하지않는다.240Hz음악원장과60Hz힘/각도끝점의범위를구분하며240Hz최대힘을주장하지않는다.','',
        '몸체1/2/3순힘은현별압력·특정충돌쌍·끼임·음향·자연스러운자세를인증하지않는다. 검지의높은proximal하중은별도문제로남고4/4음악판정통과와분리한다. 원PD/effort·충돌90쌍·범위·속도·손목v3·2초ramp/3초onset·원음길이/말미를그대로유지했다. 해제/전환·자유기타·전곡이나학습성과로확대하지않는다.','',
        '두실제launcher exit0·scene종료와750준비핀/실제전후입력·설정·contract·할당분모·clock을검증했다. CPU분석에서GPU/native/NN/checkpoint를실행하거나생성하지않았다. 입력SHA와helper재생허용오차는verification.json에남겼다.']
    text+=['','CPU nearest 선택의 별도 검증한계:']
    for finger,check in checks.items():
        differences=check['nearest_height_CPU_differences']
        text.append('- %s: 높이차이>1µm는%d끝점이며 전체끝점 최대%.9fmm, 1µm초과 시각은%s다. candidate/wrong는매끝점일치,positive포함6gate는저장phase count와일치했다(positive의별도끝점bool은미저장). nearest normal cosine 통계 최대잔차는 %.8f다.'%(finger,len(differences),1000*check['max_nearest_height_abs_residual_m'],', '.join('%.6f초'%v['local_time_s'] for v in differences) or '없음',check['max_normal_cos_statistic_residual']))
    text+=['','검지의일부끝점에서는CPU계산상거의같은거리의패드샘플들이있으며, CPU/GPU 산술에따른 argmin분기차이가능성과정합한다. 실제native선택샘플은미확인으로남기며 높이/normal cosine의완전일치를인증하지않는다. 원native sample index가저장되지않아실제선택샘플을확정할수없다. float32/64 CPU최소3점거리·gap과원자료dtype(몸체/각/힘float32,저장scalar는Python float→float64이며추가native정밀도아님),nearest normal통계의잔차는verification.json에전부보존했다. 저장높이값을다른샘플로대체하거나허용오차를확대해통과시키지않았으며판정기준을변경하지않았다. 이차이는달성한env0의CPU재생에서발견됐으며, 상세raw가없는실패env2의압현실패원인으로연결하지않는다.']
    (out/'RESULTS.md').write_text('\n'.join(text)+'\n')
    print(json.dumps(dict(completed=True,attempts=8,acceptance={f:c['acceptance'] for f,c in cases.items()},env0_endpoints=sum(c['endpoints'] for c in checks.values()))))


if __name__=='__main__': main()
