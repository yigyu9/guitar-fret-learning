"""Completed fixed-grid oracle audit; CPU replay and descriptive plots only."""
import argparse
import csv
import importlib.util
import itertools
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
spec=importlib.util.spec_from_file_location('finger_only_oracle_probe',BASE/'probe.py')
probe=importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)


def audit_rows(document,evaluation):
    """All valid first attempts; retain full225 declaration, never choose a best fallback."""
    valid=[r for r in document['rows'] if r['valid']]
    episodes=evaluation['episodes']
    assert len(document['rows'])==225 and evaluation['assigned_quotas']==[1]*len(valid)
    assert probe.complete(episodes,len(valid))
    assert document['rows'][112]['valid'] and document['baseline_grid_index']==112
    for row in episodes:
        expected=valid[row['env_id']]
        assert row['grid_index']==expected['grid_index'] and row['selected_target_count']==1
        assert row['target_id']==document['source_target_id']
    return probe.choose(episodes,document)


def clean_heatmap(document,evaluation):
    import numpy as np
    values=np.full((25,9),np.nan)
    for row in evaluation['episodes']:
        i=row['grid_index']; assert document['rows'][i]['valid']
        values[i//9,i%9]=row['clean_fraction']
    assert np.isfinite(values).sum()==document['valid_count']
    return values


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed',action='store_true')
    args=parser.parse_args()
    if not args.root_completed:
        print('Preparation only; no result read. Wait for both root GPU exits.')
        return
    sys.path.insert(0,str(probe.ROOT))
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    torch.set_num_threads(1)
    out=HERE/'results_v1'; probe.reject_existing(out)
    hashes,verified={},{}
    def remember(path):
        hashes[str(path)]=probe.sha(path)
        return probe.read(path)
    launcher=remember(BASE/'01_launcher.json'); assert launcher['completed'] and launcher['returncode']==0
    assert [j['finger'] for j in launcher['jobs']]==['index','middle'] and all(j['returncode']==0 for j in launcher['jobs'])
    seal=remember(BASE/'preparation_seal.json')
    assert seal['independent_review']=='passed_no_findings' and len(seal['input_pins'])==690
    def pins(values):
        for p,h in values.items():
            if p not in verified: verified[p]=probe.sha(p)
            assert verified[p]==h,p
    pins(seal['input_pins'])
    metadata,_=fixture(1)
    cases,trace_checks,plot_values={},{},{}
    table=[]
    for finger in ('index','middle'):
        folder=BASE/'runs'/finger
        local_launcher=remember(BASE/('01_'+finger+'_launcher.json')); assert local_launcher['returncode']==0
        document=remember(BASE/'cpu_inputs'/(finger+'_grid.json'))
        config=remember(folder/'settings.json'); assert config==remember(BASE/'cpu_inputs'/(finger+'_settings.json'))
        assert config==probe.settings(finger,document['valid_count']) and config['song']['short_learning']['wrist_control']['schema'].endswith('.v3')
        short=config['song']['short_learning']; source=short['view']['source_target']
        ref=remember(Path(document['reference_path'])); assert probe.sha(document['reference_path'])==document['reference_sha256']
        recomputed=probe.grid(ref['selected_targets_rad'],document['joint_names'],document['native_lower_rad'],document['native_upper_rad'])
        assert all(document[k]==v for k,v in recomputed.items())
        report,scene=remember(folder/'report.json'),remember(folder/'gpu_scene_final.json')
        before,after=remember(folder/'inputs_before.json'),remember(folder/'inputs_after.json')
        assert report['completed'] and report['closed'] and report['failure'] is None and report['close_failure'] is None
        assert not report['changed_inputs'] and not report['unpinned_project_sources']
        assert before==after['input_pins'] and after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
        pins(before)
        count=document['valid_count']; assert count==dict(index=135,middle=180)[finger]
        assert scene['closed'] and scene['environment_count']==count and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and scene['diagnostic_guitar_mode']=='fixed'
        assert report['assigned_valid_attempts']==count and report['grid_rows']==225 and report['no_NN_or_checkpoint']
        assert report['resources']['physics_steps']==scene['physics_steps']==4*report['resources']['control_ticks']
        assert report['resources']['control_ticks']<=short['view']['duration_ticks'] and not list(folder.glob('*.pt'))
        remember(folder/'training_contract.json')
        evaluation=remember(folder/'evaluation.json'); assert evaluation['policy_performance'] is False
        selection=audit_rows(document,evaluation); assert selection==remember(folder/'selection.json')
        episodes=evaluation['episodes']; bygrid={r['grid_index']:r for r in episodes}
        # Independent selection ranking from the full assigned ledger, separate from probe.choose.
        eligible=[r for r in episodes if r['achieved'] and r['clean_fraction']>=.7 and r['audible_wrong_fraction']<=.1
            and not r['termination']['physical_failure'] and not r['termination']['wrist_failure']]
        order=sorted((r['grid_index'] for r in eligible),key=lambda i:(sum(d*d for d in document['rows'][i]['offset_deg']),max(abs(d) for d in document['rows'][i]['offset_deg']),i))
        assert selection['eligible_grid_indices']==order and selection['selected_grid_index']==(order[0] if order else None)
        summary=dict(attempts=count,excluded=225-count,achieved=sum(r['achieved'] for r in episodes),eligible=len(eligible),
            mean_clean=sum(r['clean_fraction'] for r in episodes)/count,mean_wrong=sum(r['audible_wrong_fraction'] for r in episodes)/count,
            physical_failures=sum(r['termination']['physical_failure'] for r in episodes),wrist_failures=sum(r['termination']['wrist_failure'] for r in episodes),
            selected=selection['selected_grid_index'],all_timeline_complete=all(r['reason']=='timeline_complete' for r in episodes))
        for key,value in (('achieved_fraction',summary['achieved']/count),('mean_clean_fraction',summary['mean_clean']),
                          ('mean_audible_wrong_fraction',summary['mean_wrong']),('physical_failure_fraction',summary['physical_failures']/count),('wrist_failure_fraction',summary['wrist_failures']/count)):
            assert abs(evaluation['summary'][key]-value)<1e-12
        statistics=remember(folder/'statistics.json'); assert statistics['phase_scope']=='source_time<source_onset; source_onset<=source_time<source_end; source_time>=source_end'
        stats={r['grid_index']:r for r in statistics['rows']}; assert len(stats)==count
        for r in episodes:
            assert stats[r['grid_index']]['env_id']==r['env_id']
            assert sum(p['samples'] for p in stats[r['grid_index']]['phases'].values())==r['steps']
        focus={i:dict(declaration=document['rows'][i],episode=bygrid[i],statistics=stats[i],detailed_trace_available=i in document['executed_detail_grid_indices'])
            for i in dict.fromkeys([112,*([order[0]] if order else [])])}
        cases[finger]=dict(summary=summary,selected_criterion=selection,focus=focus,metric_order=statistics['metric_order'],gate_order=statistics['gate_order'],resources=report['resources'])
        plot_values[finger]=clean_heatmap(document,evaluation)
        for declared in document['rows']:
            i=declared['grid_index']; r=bygrid.get(i); p=stats[i]['phases']['audible'] if r else None
            table.append(dict(finger=finger,grid_index=i,env_id=declared['env_id'],valid=declared['valid'],
                excluded_reasons=json.dumps(declared['excluded_reasons']),offset_deg=json.dumps(declared['offset_deg']),target_rad=json.dumps(declared['target_rad']),
                baseline=i==112,selected=i==summary['selected'],eligible=i in order,rank=order.index(i)+1 if i in order else None,
                achieved=r['achieved'] if r else None,clean=r['clean_fraction'] if r else None,wrong=r['audible_wrong_fraction'] if r else None,
                physical_failure=r['termination']['physical_failure'] if r else None,wrist_failure=r['termination']['wrist_failure'] if r else None,
                audible_samples=p['samples'] if p else None,body123_mean_N=json.dumps(p['mean'][12:15]) if p and p['samples'] else None,
                body123_max_N=json.dumps(p['max'][12:15]) if p and p['samples'] else None,
                actual_selected_mean_deg=json.dumps(p['mean'][:4]) if p and p['samples'] else None,
                target_selected_mean_deg=json.dumps(p['mean'][4:8]) if p and p['samples'] else None))
        meta=remember(folder/'trace_metadata.json'); assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
        assert meta['grid_indices']==document['executed_detail_grid_indices'] and len(meta['grid_indices'])==8
        assert sorted(p.name for p in folder.glob('trace_grid*.npz'))==['trace_grid%06d.npz'%i for i in sorted(meta['grid_indices'])]
        qids=[meta['joint_names'].index(n) for n in document['joint_names']]
        bodies=[meta['body_names'].index('human/LH:'+finger+str(i)) for i in (1,2,3)]
        wrist,guitar=[meta['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')]
        env=ShortEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
        for i in meta['grid_indices']:
            path=folder/('trace_grid%06d.npz'%i); hashes[str(path)]=probe.sha(path); t=np.load(path)
            assert len(t['time_s'])==bygrid[i]['steps'] and abs(t['time_s'][0]-1/60)<1e-6
            masks=probe.phase_masks(t['source_time_s'],source['onset_s'],source['end_s'])
            instrument=Rotation.from_quat(t['body_state'][:,guitar,3:7])
            position=t['body_state'][:,guitar,:3]+instrument.apply(t['wrist_goal_G_m'])-t['body_state'][:,wrist,:3]
            rotation=(instrument*Rotation.from_quat(t['wrist_goal_G_xyzw'])*Rotation.from_quat(t['body_state'][:,wrist,3:7]).inv()).magnitude()
            data=np.c_[np.rad2deg(t['q'][:,qids]),np.rad2deg(t['target'][:,qids]),np.rad2deg((t['target']-t['q'])[:,qids]),
                np.linalg.norm(t['net_body_force_n'][:,bodies],axis=-1),1000*t['surface_distance_m'],1000*t['surface_height_m'],np.zeros(len(t['time_s'])),
                1000*np.linalg.norm(position,axis=-1),np.rad2deg(rotation)]
            def snapshot(k):
                return dict(q=torch.tensor(t['q'][k:k+1]),qd=torch.zeros(1,105),target=torch.tensor(t['target'][k:k+1]),
                    body_state=torch.tensor(t['body_state'][k:k+1]),contact_force=torch.tensor(t['net_body_force_n'][k:k+1]))
            env.reset([0],snapshot(0)); gates=[]
            for k,now in enumerate(t['time_s']):
                env.clock[0]=round(now*240); env._snapshot(snapshot(k)); j=env.selected_index
                assert bool(env.candidate[0,j])==bool(t['candidate'][k]) and bool(env.wrong[0,j])==bool(t['wrong'][k])
                assert abs(float(env.surface_distance[0,j])-t['surface_distance_m'][k])<1e-6
                assert abs(float(env.surface_height[0,j])-t['surface_height_m'][k])<1e-6
                data[k,17]=float(env.surface_alignment[0,j])
                gates.append([bool(v[0,j]) for v in (env.surface_body_loaded,env.contact_geometry,env.contact_facing,env.contact_loaded_target,env.candidate,env.wrong)])
            errors=np.zeros(20)
            for phase,mask in zip(('before','audible','after'),masks):
                p=stats[i]['phases'][phase]; assert int(mask.sum())==p['samples']
                assert np.array_equal(np.asarray(gates)[mask].sum(0),p['gate_counts'])
                if p['samples']:
                    for key,value in (('min',data[mask].min(0)),('max',data[mask].max(0)),('mean',data[mask].mean(0)),('rms',np.sqrt((data[mask]**2).mean(0)))):
                        np.testing.assert_allclose(value,p[key],rtol=5e-6,atol=5e-5)
                        errors=np.maximum(errors,abs(value-np.array(p[key])))
            trace_checks[finger+'_'+str(i)]=dict(endpoints=len(t['time_s']),all_predicates_match=True,all_phase_gate_counts_match=True,
                max_statistic_abs_residual_by_metric=errors.tolist(),statistic_tolerance=dict(rtol=5e-6,atol=5e-5),
                scope='independent NumPy statistics versus original float32 streaming summaries; no240Hz extrema')
    assert len(table)==450 and sum(c['summary']['attempts'] for c in cases.values())==315 and not torch.cuda.is_initialized()
    hashes[str(Path(__file__).resolve())]=probe.sha(Path(__file__).resolve()); hashes[str(HERE/'PLAN.md')]=probe.sha(HERE/'PLAN.md')
    out.mkdir()
    def write(name,value): probe.write(out/name,value)
    write('comparison.json',dict(cases=cases,scope='scripted grid acquisition only; each valid row one first attempt; fresh4attempt reproduction not performed'))
    write('verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,CUDA_initialized=False,
        current_preparation_pins=690,actual_input_paths_verified=len(verified),input_sha256=hashes,verified_input_sha256=verified,
        total_declared_rows=450,total_valid_first_attempts=315,all_out_of_native_range_rows_explicit=True,
        trace_checks=trace_checks,total_detailed_endpoints=sum(r['endpoints'] for r in trace_checks.values()),
        predicate_helper_sha256={str(probe.ROOT/'guitar_learning'/p):verified[str(probe.ROOT/'guitar_learning'/p)] for p in
            ('gpu/environment.py','gpu/simplified_finger_environment.py','gpu/fingertip_pad.py','gpu/wrong_press.py','tool/experiments/short_finger_learning/runtime.py')},
        no_candidate_fallback_or_new_force_criterion=True,overall_launcher_wall_s=launcher['wall_s']))
    with (out/'full_grid.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(table[0])); writer.writeheader(); writer.writerows(table)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    fig,axes=plt.subplots(1,2,figsize=(12,11))
    cmap=plt.get_cmap('viridis').copy(); cmap.set_bad('#d4d4d4')
    for finger,ax in zip(('index','middle'),axes):
        image=ax.imshow(np.ma.masked_invalid(plot_values[finger]),vmin=0,vmax=1,cmap=cmap,aspect='auto')
        for i in np.flatnonzero(~np.isfinite(plot_values[finger].ravel())): ax.text(i%9,i//9,'x',ha='center',va='center',color='#888',fontsize=7)
        ax.plot(112%9,112//9,'s',ms=10,mfc='none',mec='white',mew=1.4)
        selected=cases[finger]['summary']['selected']
        if selected is not None: ax.plot(selected%9,selected//9,'o',ms=13,mfc='none',mec='red',mew=1.5)
        ax.set_xticks(range(9)); ax.set_xticklabels(['%s/%s'%p for p in itertools.product(probe.AXES[2],probe.AXES[3])],fontsize=8)
        ax.set_yticks(range(25)); ax.set_yticklabels(['%s/%s'%p for p in itertools.product(probe.AXES[0],probe.AXES[1])],fontsize=8)
        ax.set_title('%s clean: %d valid / 225 declared'%(finger,cases[finger]['summary']['attempts']))
        ax.set_xlabel('PIP/DIP offset (deg)'); ax.set_ylabel('MCP x/z offset (deg)')
    axes[0].legend(handles=[Line2D([],[],marker='s',color='white',mfc='none',label='baseline112'),Line2D([],[],marker='o',color='red',mfc='none',label='predeclared-rank selection')],loc='lower left',fontsize=8,facecolor='#888')
    fig.subplots_adjust(left=.08,right=.86,bottom=.08,top=.94,wspace=.3)
    colorbar=fig.add_axes([.90,.14,.018,.72])
    fig.colorbar(image,cax=colorbar,label='original clean fraction')
    fig.savefig(out/'clean_grid.png',dpi=140); plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(11,7))
    for row,finger in enumerate(('index','middle')):
        for j,(i,focus) in enumerate(cases[finger]['focus'].items()):
            p=focus['statistics']['phases']['audible']; mean=np.array(p['mean']); maximum=np.array(p['max']); x=np.arange(3)
            axes[row,0].bar(x+(j-.5)*.3,mean[12:15],.28,yerr=[np.zeros(3),maximum[12:15]-mean[12:15]],capsize=2,label='grid'+str(i))
            axes[row,1].plot(range(4),mean[:4],marker='o',label='grid%s actual'%i)
            axes[row,1].plot(range(4),mean[4:8],marker='x',ls='--',label='grid%s target'%i)
        axes[row,0].set_xticks(range(3)); axes[row,0].set_xticklabels(['body1','body2','body3'])
        axes[row,0].set_ylabel(finger+' resultant N'); axes[row,0].legend(fontsize=8)
        axes[row,1].set_xticks(range(4)); axes[row,1].set_xticklabels(['1_x','1_z','2','3'])
        axes[row,1].set_ylabel(finger+' q-position deg'); axes[row,1].legend(fontsize=7)
        for ax in axes[row]: ax.grid(alpha=.2)
    fig.suptitle('Audible60Hz mean; force whiskers=stored60Hz max, not240Hz extremes')
    fig.tight_layout(); fig.savefig(out/'baseline_selected.png',dpi=140); plt.close(fig)
    text=['# 손가락4축 oracle grid 실제 결과','',
        '**검지135개 중21개, 중지180개 중4개가 사전 기준을 통과했다. 고정 순위로 검지115·중지114가 선정됐다. 각 행은 한 번의 scripted 시도이며 새4시도 재현·힘/자세 검토는 아직 미완료다. 정책 학습 성과가 아니다.**','',
        '| 손가락 | 선언/범위외/실행 | 달성/eligible | 선정 | offset 1x/1z/2/3 (도) | clean/wrong | 물리/손목 실패 |','|---|---:|---:|---:|---|---:|---:|']
    for finger,c in cases.items():
        s=c['summary']; f=c['focus'][s['selected']] if s['selected'] is not None else None
        text.append('| %s | 225/%d/%d | %d/%d | %s | %s | %s | %d/%d |'%(finger,s['excluded'],s['attempts'],s['achieved'],s['eligible'],str(s['selected']),
            ', '.join(str(v) for v in f['declaration']['offset_deg']) if f else '없음',
            '%.2f%%/%.2f%%'%(100*f['episode']['clean_fraction'],100*f['episode']['audible_wrong_fraction']) if f else '없음',s['physical_failures'],s['wrist_failures']))
    text += ['', '전체450선언행과 제외사유는 full_grid.csv에 있으며 모든315유효행 첫 시도와 baseline112를 포함했다. 범위외는 검지90·중지45행으로 사전 명시했고 조용히 clamp하지 않았다. 새 성공 문턱이나 힘 eligibility를 추가하지 않았으며 순위는 perturbation 제곱합→최대 절대 변화→grid index다.','',
        '![전체225 clean grid](clean_grid.png)','',
        '회색x는 범위외, 흰 사각형은 baseline112, 붉은 원은 사전 순위의 선정 행이다. 열9개와 행25개를 모두 유지했다. 각 셀은 같은 seed7의 서로 다른 scripted 목표 한 시도로, 반복성이나 전체 도달성을 인증하지 않는다.','',
        '![baseline와 사전 선정 후보](baseline_selected.png)','',
        '아래 힘과 각도는 원 source onset≤source time<end의60Hz 요약이다. mean/max를 median이나240Hz 최대·현별압력으로 읽지 않는다.','',
        '| 손가락/grid | body1 mean/max N | body2 mean/max N | body3 mean/max N | actual q mean 도 | native target mean 도 |','|---|---:|---:|---:|---|---|']
    for finger,c in cases.items():
        for i,f in c['focus'].items():
            p=f['statistics']['phases']['audible']; m=p['mean']; maximum=p['max']
            text.append('| %s/%s | %.4f/%.4f | %.4f/%.4f | %.4f/%.4f | %s | %s |'%(finger,i,m[12],maximum[12],m[13],maximum[13],m[14],maximum[14],
                ', '.join('%.3f'%x for x in m[:4]),', '.join('%.3f'%x for x in m[4:8])))
    text += ['', '같은 음 중60Hz 구간의 손목/패드 평균과 gate 끝점 수다. gate 순서는 loaded/위치/위치+facing/positive/candidate/wrong다.','',
        '| 손가락/grid | 손목 mm/도 | nearest 거리/높이 mm | gate 끝점 수 |','|---|---:|---:|---|']
    for finger,c in cases.items():
        for i,f in c['focus'].items():
            p=f['statistics']['phases']['audible']; m=p['mean']
            text.append('| %s/%s | %.4f/%.4f | %.4f/%.4f | %s |'%(finger,i,m[18],m[19],m[15],m[16],'/'.join(str(x) for x in p['gate_counts'])))
    text += ['', '검지115는 사전 상세trace에 있어 baseline과 함께 원 helper 재생이 가능하다. 중지114는 사전 상세8행 밖이므로 새 원시trace가 없으며 위의 native 경량통계·원 ledger만 보고한다. 성공 뒤 그 행의 원시값을 추가 저장한 것처럼 다루지 않았다.','',
        '선정 후보의 음악 기준 통과와 하중/자연스러움은 분리된다. 검지의 proximal body1 합력이 큰 채 남고, body3의 작은 순힘도 기존 loaded 기준으로 판정된 접촉 후보일 뿐이다. 몸체 순힘은 특정 충돌쌍·끼임·현별힘·실제압력·음향을 인증하지 않는다. 후보는 정해진 perturbation 순위를 그대로 따른다.','',
        '상세16trace의 저장60Hz 끝점 candidate/wrong/거리/높이 및 phase gate/20metric 통계를 현재 원 helper와 독립 NumPy 계산으로 검산했다. 원 float32 streaming 통계와 재계산의 허용 오차는 verification.json에 명시했다. 전체315행의240Hz 음악 ledger 집계와16개 상세trace 재생을 구분하며, 미저장 모든 행의240Hz 자세/힘을 재구성하지 않았다.','',
        '검지·중지 두 scene 완료/닫힘·outer exit0·현재690준비핀·각 실제 입력·설정·native 범위·기준행·원 순위를 확인했다. no-NN/no-checkpoint scripted 실행이며 CPU 분석에서 새 GPU/native는 실행하지 않았다. 이 결과는 같은 후보의 새4시도 재현과 별도 힘/자세 확인을 거친 뒤 후속 학습 여부를 판단할 근거다. 해제·전환·자유 기타·전곡 성능은 미완료다.']
    with (out/'RESULTS.md').open('x') as stream: stream.write('\n'.join(text)+'\n')
    print(json.dumps(dict(completed=True,attempts=315,selections={f:c['summary']['selected'] for f,c in cases.items()},detailed_endpoints=sum(r['endpoints'] for r in trace_checks.values()))))


if __name__=='__main__': main()
