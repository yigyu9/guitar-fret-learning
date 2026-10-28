"""CPU comparison of the same declared finite grid; no result read before root handoff."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
spec=importlib.util.spec_from_file_location('effort_grid_analysis_probe',BASE/'probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
grid=probe.grid
spec=importlib.util.spec_from_file_location('reviewed_original_grid_analysis',grid.HERE/'analysis/analyze.py')
original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed',action='store_true');args=parser.parse_args()
    if not args.root_completed:
        print('Prepared only; wait for root actual exits. No result read.');return
    sys.path.insert(0,str(grid.ROOT))
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    torch.set_num_threads(1)
    out=HERE/'results_v1';probe.cap.reject_existing(out)
    inputs,verified={},{}
    def track(p):
        p=Path(p);inputs[str(p)]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(values):
        for p,h in values.items():
            if p not in verified:verified[p]=grid.sha(p)
            assert verified[p]==h,p
    for p in probe.actual_gate():track(p)
    for root in (probe.CAP_ROOT/'analysis/results_v1',grid.HERE/'analysis/results_v1'):
        review=read(root/'review.json');assert review['verdict']=='PASS' and not review['findings'];pins(review['reviewed_sha256'])
        v=read(root/'verification.json')
        for key in ('input_sha256','verified_input_sha256'):pins(v[key])
    seal=read(BASE/'preparation_seal.json');assert seal['independent_review']=='passed_no_findings';pins(seal['input_pins'])
    prep_review=read(BASE/'review.json');assert prep_review['verdict']=='PASS' and not prep_review['findings'];pins(prep_review['reviewed_sha256'])
    launcher=read(BASE/'01_launcher.json');assert launcher['completed'] and launcher['returncode']==0
    assert [j['finger'] for j in launcher['children']]==['index','middle'] and all(j['returncode']==0 for j in launcher['children'])
    metadata,_=fixture(1)
    cases,trace_checks,table,heatmaps={}, {}, [], {}
    for finger,count in probe.COUNTS.items():
        folder=BASE/'runs'/finger;oldfolder=grid.HERE/'runs'/finger
        assert read(BASE/('01_'+finger+'_launcher.json'))['returncode']==0
        doc=read(grid.HERE/'cpu_inputs'/(finger+'_grid.json'))
        assert len(doc['rows'])==225 and doc['valid_count']==count
        config=read(folder/'settings.json');assert config==read(oldfolder/'settings.json')==grid.settings(finger,count)
        source=config['song']['short_learning']['view']['source_target']
        ref=read(Path(doc['reference_path']));assert grid.sha(doc['reference_path'])==doc['reference_sha256']
        assert all(doc[k]==v for k,v in grid.grid(ref['selected_targets_rad'],doc['joint_names'],doc['native_lower_rad'],doc['native_upper_rad']).items())
        report,scene=read(folder/'report.json'),read(folder/'gpu_scene_final.json')
        lifecycle=read(folder/'effort_grid_lifecycle.json')
        assert lifecycle['scene_valid'] and lifecycle['pool_restored'] and not lifecycle['cleanup_errors'] and lifecycle['native_effort_cap_Nm']==.25
        assert report['completed'] and report['closed'] and report['failure'] is None and report['close_failure'] is None
        assert not report['changed_inputs'] and not report['unpinned_project_sources'] and report['no_NN_or_checkpoint']
        assert report['assigned_valid_attempts']==count and report['grid_rows']==225
        oldscene=read(oldfolder/'gpu_scene_final.json')
        assert all(scene[k]==oldscene[k] for k in scene if k not in ('physics_steps','rigid_property_readback_max_abs_error'))
        assert scene['closed'] and scene['environment_count']==count and scene['hand_collision']['enabled_distinct_finger_pairs']==90
        assert scene['hand_collision_native_readback_environments']==count and scene['physics_steps']==report['resources']['physics_steps']==4*report['resources']['control_ticks']
        before,after=read(folder/'inputs_before.json'),read(folder/'inputs_after.json');pins(before)
        assert after['verified'] and before==after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
        native=read(folder/'native_effort_readback.json');reviewed_native=read(probe.CAP_ROOT/'runs'/finger/'native_effort_readback.json')
        for k in ('actual_native_PD105','original_profile_native_PD105','changed_native_field_indices','native_indices','joint_names','source_sha256'):
            assert native[k]==reviewed_native[k]
        assert native['environment_count']==count and native['expected_readback_exact']
        contract=read(folder/'training_contract.json');assert contract['native_backend'].pop('diagnostic_native_effort')==native
        assert contract==read(oldfolder/'training_contract.json')
        evaluation=read(folder/'evaluation.json');old_eval=read(oldfolder/'evaluation.json')
        selection=original.audit_rows(doc,evaluation);assert selection==read(folder/'selection.json')
        old_selection=original.audit_rows(doc,old_eval);assert old_selection==read(oldfolder/'selection.json')
        stats=read(folder/'statistics.json');old_stats=read(oldfolder/'statistics.json')
        assert all(stats[k]==old_stats[k] for k in ('metric_order','gate_order','phase_order','phase_scope','scope'))
        bygrid={e['grid_index']:e for e in evaluation['episodes']};oldby={e['grid_index']:e for e in old_eval['episodes']}
        bystat={r['grid_index']:r for r in stats['rows']};oldstat={r['grid_index']:r for r in old_stats['rows']}
        assert set(bygrid)==set(oldby)==set(bystat)==set(oldstat)=={r['grid_index'] for r in doc['rows'] if r['valid']}
        eligible=[e['grid_index'] for e in evaluation['episodes'] if e['achieved'] and e['clean_fraction']>=.7 and e['audible_wrong_fraction']<=.1 and not e['termination']['physical_failure'] and not e['termination']['wrist_failure']]
        rank=sorted(eligible,key=lambda i:(sum(x*x for x in doc['rows'][i]['offset_deg']),max(abs(x) for x in doc['rows'][i]['offset_deg']),i))
        assert rank==selection['eligible_grid_indices'] and selection['selected_grid_index']==(rank[0] if rank else None)
        summaries={}
        for label,ev,st in [('baseline20',old_eval,oldstat),('cap025',evaluation,bystat)]:
            episodes=ev['episodes'];assert len(episodes)==count and ev['policy_performance'] is False
            for e in episodes:assert sum(p['samples'] for p in st[e['grid_index']]['phases'].values())==e['steps']
            summaries[label]=dict(attempts=count,achieved=sum(e['achieved'] for e in episodes),mean_clean=sum(e['clean_fraction'] for e in episodes)/count,
                mean_wrong=sum(e['audible_wrong_fraction'] for e in episodes)/count,physical_failures=sum(e['termination']['physical_failure'] for e in episodes),wrist_failures=sum(e['termination']['wrist_failure'] for e in episodes))
            groups={}
            for name,group in [('all',episodes),('achieved',[e for e in episodes if e['achieved']]),('unachieved',[e for e in episodes if not e['achieved']])]:
                exposed=[st[e['grid_index']]['phases']['audible'] for e in group if st[e['grid_index']]['phases']['audible']['samples']]
                means=np.asarray([p['mean'] for p in exposed])
                groups[name]=dict(attempts=len(group),audible_exposed_attempts=len(exposed),
                    metric_mean_of_attempt_means=means.mean(0).tolist() if len(exposed) else None,
                    metric_p95_of_attempt_means=np.percentile(means,95,axis=0).tolist() if len(exposed) else None,
                    metric_largest_recorded_max=np.asarray([p['max'] for p in exposed]).max(0).tolist() if len(exposed) else None,
                    scope='equal-weight perattempt audible means; unexposed attempts remain count, not synthetic zero force; p95 is across attempt means, not240Hz or pooled endpoints')
            summaries[label]['audible_groups']=groups
        cases[finger]=dict(summaries=summaries,baseline_selection=old_selection,cap_selection=selection,
            baseline_selected_at_cap=bygrid[old_selection['selected_grid_index']] if old_selection['selected_grid_index'] is not None else None,
            cap_selected_at_baseline=oldby[selection['selected_grid_index']] if selection['selected_grid_index'] is not None else None)
        heatmaps[finger]=(original.clean_heatmap(doc,old_eval),original.clean_heatmap(doc,evaluation))
        for r in doc['rows']:
            i=r['grid_index'];row=dict(finger=finger,grid_index=i,valid=r['valid'],excluded_reasons=json.dumps(r['excluded_reasons']),offset_deg=json.dumps(r['offset_deg']),target_rad=json.dumps(r['target_rad']))
            for label,es,ss in [('baseline20',oldby,oldstat),('cap025',bygrid,bystat)]:
                e=es.get(i);p=ss[i]['phases']['audible'] if e else None
                row[label+'_episode']=json.dumps(e);row[label+'_audible']=json.dumps(p)
            table.append(row)
        meta=read(folder/'trace_metadata.json');oldmeta=read(oldfolder/'trace_metadata.json');assert meta==oldmeta
        assert len(meta['grid_indices'])==8 and meta['grid_indices']==doc['executed_detail_grid_indices']
        assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
        qids=[meta['joint_names'].index(n) for n in doc['joint_names']]
        bids=[meta['body_names'].index('human/LH:'+finger+str(i)) for i in (1,2,3)]
        wrist,guitar=[meta['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')]
        env=ShortEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
        for i in meta['grid_indices']:
            t=dict(np.load(track(folder/('trace_grid%06d.npz'%i))));old=dict(np.load(track(oldfolder/('trace_grid%06d.npz'%i))))
            assert len(t['time_s'])==bygrid[i]['steps'] and np.all(np.diff(np.rint(t['time_s']*240))==4)
            masks=grid.phase_masks(t['source_time_s'],source['onset_s'],source['end_s'])
            rg=Rotation.from_quat(t['body_state'][:,guitar,3:7]);pos=t['body_state'][:,guitar,:3]+rg.apply(t['wrist_goal_G_m'])-t['body_state'][:,wrist,:3]
            rot=(rg*Rotation.from_quat(t['wrist_goal_G_xyzw'])*Rotation.from_quat(t['body_state'][:,wrist,3:7]).inv()).magnitude()
            data=np.c_[np.rad2deg(t['q'][:,qids]),np.rad2deg(t['target'][:,qids]),np.rad2deg((t['target']-t['q'])[:,qids]),np.linalg.norm(t['net_body_force_n'][:,bids],axis=-1),t['surface_distance_m']*1000,t['surface_height_m']*1000,np.zeros(len(t['time_s'])),np.linalg.norm(pos,axis=-1)*1000,np.rad2deg(rot)]
            def snapshot(k):return dict(q=torch.tensor(t['q'][k:k+1]),qd=torch.zeros(1,105),target=torch.tensor(t['target'][k:k+1]),body_state=torch.tensor(t['body_state'][k:k+1]),contact_force=torch.tensor(t['net_body_force_n'][k:k+1]))
            env.reset([0],snapshot(0));gates=[];height=[];cosine={}
            for k,now in enumerate(t['time_s']):
                env.clock[0]=round(now*240);env._snapshot(snapshot(k));j=env.selected_index
                assert bool(env.candidate[0,j])==bool(t['candidate'][k]) and bool(env.wrong[0,j])==bool(t['wrong'][k])
                assert abs(float(env.surface_distance[0,j])-t['surface_distance_m'][k])<1e-6
                height.append(float(env.surface_height[0,j])-float(t['surface_height_m'][k]));data[k,17]=float(env.surface_alignment[0,j])
                gates.append([bool(v[0,j]) for v in (env.surface_body_loaded,env.contact_geometry,env.contact_facing,env.contact_loaded_target,env.candidate,env.wrong)])
            for phase,mask in zip(stats['phase_order'],masks):
                p=bystat[i]['phases'][phase];assert int(mask.sum())==p['samples']
                assert np.array_equal(np.asarray(gates)[mask].sum(0),p['gate_counts'])
                if not p['samples']:continue
                for key,value in [('mean',data[mask].mean(0)),('min',data[mask].min(0)),('max',data[mask].max(0)),('rms',np.sqrt((data[mask]**2).mean(0)))]:
                    ix=[k for k in range(20) if k!=17];np.testing.assert_allclose(value[ix],np.asarray(p[key])[ix],rtol=5e-6,atol=5e-5)
                    cosine[phase+'_'+key]=dict(CPU=float(value[17]),saved=p[key][17],residual=float(value[17]-p[key][17]))
            common,a,b=np.intersect1d(np.rint(t['time_s']*240).astype(int),np.rint(old['time_s']*240).astype(int),return_indices=True)
            assert np.array_equal(t['target'][a][:,qids],old['target'][b][:,qids])
            trace_checks[finger+'_'+str(i)]=dict(endpoints=len(data),candidate_wrong_each_endpoint_match=True,six_phase_gate_counts_match=True,non_cosine_statistics_match=True,
                shared_clock_selected_target_exact=True,shared_clock_count=len(common),baseline_endpoints=len(old['time_s']),
                height_residuals_over_1um=[dict(endpoint=k,local_time_s=float(t['time_s'][k]),CPU_minus_saved_m=v) for k,v in enumerate(height) if abs(v)>1e-6],max_height_residual_m=max(map(abs,height)),normal_cos_statistics=cosine,
                scope='CPU argmin diagnosis only; native sample index/normalcos perendpoint missing; raw saved height aggregate preserved; no samepoint pressure certification')
    assert len(table)==450 and sum(r['valid'] for r in table)==315 and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    track(Path(__file__).resolve());track(HERE/'PLAN.md');track(grid.HERE/'analysis/analyze.py')
    out.mkdir();grid.write(out/'comparison.json',dict(cases=cases,scope='same315 declared valid first attempts per condition; all failures kept, noNN'))
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,
        total_declared_rows=450,total_valid_first_attempts_per_condition=315,excluded_count=135,trace_checks=trace_checks,
        original_selection_and_exclusions_preserved=True,same_settings_and_target_declarations=True,native105_and90pairs=True,
        known_limits=['60Hz only; detailed8rows per finger, no inferred other raw','native qd not recorded by grid; no qpos derivative substitution','nearest argmin/normalcos sample unrecorded; residuals retained','arm teacher feedback can differ; no contactpair or naturalness/production claim']))
    with (out/'full_grid.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(8,9))
    for r,finger in enumerate(probe.COUNTS):
        for c,values in enumerate(heatmaps[finger]):
            im=axes[r,c].imshow(np.ma.masked_invalid(values),vmin=0,vmax=1,aspect='auto');axes[r,c].set_title(finger+' '+('20Nm' if c==0 else '.25Nm'));axes[r,c].set_xlabel('PIP/DIP grid');axes[r,c].set_ylabel('MCP x/z grid')
    fig.colorbar(im,ax=axes.ravel().tolist(),label='original clean fraction');fig.savefig(out/'clean_comparison.png',dpi=140);plt.close(fig)
    lines=['# 동일 유한목표 effort 비교','', '전체 유효315개 첫시도씩을 원기준으로 비교했다. 제외135개를 성과분모에 끼워 넣거나 실패시도를 빼지 않았다. 정책성과·접촉쌍 압력·자유손 개선 인증이 아니다.','', '| 손가락/조건 | 달성/시도 | 평균clean/wrong | 물리/손목실패 |','|---|---:|---:|---:|']
    for finger,c in cases.items():
        for label,s in c['summaries'].items():lines.append('| %s/%s | %d/%d | %.4f/%.4f | %d/%d |'%(finger,label,s['achieved'],s['attempts'],s['mean_clean'],s['mean_wrong'],s['physical_failures'],s['wrist_failures']))
    for finger,c in cases.items():
        lines.append('\n%s 원랭킹 선정:20Nm %s → .25Nm %s. 전체450행의 원장·음중세마디힘/각/손목/gate는 full_grid.csv에 보존했다.'%(finger,c['baseline_selection']['selected_grid_index'],c['cap_selection']['selected_grid_index']))
    lines+=['','| 손가락/조건/집단 | 시도/음중노출 | body1/2/3 평균 N | actual4 평균 ° | wrist mm/° |','|---|---:|---|---|---|']
    for finger,c in cases.items():
        for label,s in c['summaries'].items():
            for group,g in s['audible_groups'].items():
                m=g['metric_mean_of_attempt_means'];fmt=lambda values:', '.join('%.4f'%x for x in values)
                lines.append('| %s/%s/%s | %d/%d | %s | %s | %s |'%(finger,label,group,g['attempts'],g['audible_exposed_attempts'],fmt(m[12:15]) if m else '미노출',fmt(m[:4]) if m else '미노출',fmt(m[18:20]) if m else '미노출'))
    lines+=['','힘·각도·손목 집계는 각시도 audible 평균의 동일가중 평균이다. 미노출시도는 전체분모에 유지하되 힘0을 대입하지 않는다. 비교 JSON은 전체20지표의 시도평균 p95와 저장60Hz 최고값도 구분한다.']
    lines+=['','![clean comparison](clean_comparison.png)','','상세16 trace는60Hz이며 nearest height/cosine 잔차는 verification에 그대로 남겼다. native nearest sample이 저장되지 않아 CPU argmin을 native witness로 인증하지 않는다. 선택 target은 공통clock에서 exact 대조했고 actual state 동일성은 가정하지 않았다. effort16 변경은 비선택손가락과 wrist teacher feedback도 바꾸므로 개별접촉·원인을 단정하거나 기본채택하지 않는다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print('Actual CPU comparison written:',out)


if __name__=='__main__':main()
