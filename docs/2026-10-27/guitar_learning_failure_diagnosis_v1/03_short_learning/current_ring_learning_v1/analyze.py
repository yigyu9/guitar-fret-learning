"""실제 완료 자료만 읽는 순수 CPU 분석. Torch/native/model load 없이 두 그림을 만든다."""
import importlib.util
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ring_learning_analysis_inputs',HERE/'experiment.py')
e=importlib.util.module_from_spec(spec); spec.loader.exec_module(e)
p=e.pre


def summarize(rows):
    n=len(rows)
    if not n: return dict(episodes=0)
    return dict(episodes=n,denominator='all assigned evaluation attempts, including failures',
        achieved_fraction=sum(r['achieved'] for r in rows)/n,mean_clean_fraction=sum(r['clean_fraction'] for r in rows)/n,
        mean_audible_wrong_fraction=sum(r['audible_wrong_fraction'] for r in rows)/n,
        physical_failure_fraction=sum(r['termination']['physical_failure'] for r in rows)/n,
        wrist_failure_fraction=sum(r['termination']['wrist_failure'] for r in rows)/n,
        any_failure_fraction=sum(r['reason']=='terminal_failure' for r in rows)/n)


def rows_check(rows,duration):
    error=0.
    for r in rows:
        assert r['target_id']=='event-000053/string-3/note-54' and r['selected_target_count']==1
        for name,field in [('clean','clean_fraction'),('wrong','audible_wrong_fraction'),('missing','missing_fraction')]:
            assert abs(min(1.,r['note'][name]/duration)-r[field])<1e-12
        assert len(r['reward_components'])==9 and abs(sum(r['cost_components'].values())-r['cost'])<1e-5
        error=max(error,abs(sum(r['reward_components'].values())-r['reward']))
    assert error<1e-4
    return error


def run(out=None):
    assert sys.version_info[:2]==(3,8) and os.environ.get('CUDA_VISIBLE_DEVICES')==''
    assert not {'torch','isaacgym'} & set(sys.modules)
    # 결과가 없거나 GPU 감독이 끝나지 않았다면 출력 폴더도 만들지 않는다.
    schedule=HERE/'execution_schedule'; done=p.read(schedule/'completed.json')
    assert done['completed'] and done['jobs']==11
    seal,_=e.gate('evaluate')
    files={Path(x) for x in seal['input_pins']}|{Path(x) for x in seal['review_documents_sha256']}|{HERE/'preparation_seal.json',Path(__file__)}
    files.update(x for folder in (HERE/'runs',schedule) for x in folder.rglob('*') if x.is_file())
    before={str(x):p.sha(x) for x in sorted(files)}
    out=Path(out) if out is not None else HERE/'analysis/results_v1'
    out.mkdir(parents=True,exist_ok=False); failure=None; complete=False
    try:
        import numpy as np
        from scipy.spatial.transform import Rotation
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        baseline=p.read(e.PRE/'runs/reference/native_effort_readback.json')
        config=p.read(HERE/'inputs/settings.json'); task=config['song']['short_learning']
        duration=task['view']['source_target']['end_s']-task['view']['source_target']['onset_s']
        names=['reference','zero','train',*['evaluation_%06d'%u for u in e.UPDATES],'evaluation_000300_stochastic']
        for name in names:
            process=p.read(schedule/(name+'_process.json')); end=p.read(schedule/(name+'_exit.json'))
            assert process['pid']>0 and process['start_ticks']>0 and process['cwd']==str(e.ROOT)
            assert process['argv'][:4]==['/home/ajou/miniconda3/envs/rl38/bin/python','-B',str(HERE/'experiment.py'),'execute']
            assert end['returncode']==0 and end['process_terminal'] and end['failure'] is None and end['cleanup_errors']==[] and end['finished_utc']>process['started_utc']
            p.verify_pins(process['input_pins'])
            folder=HERE/'runs'/('preflight_'+name if name in ('reference','zero') else name)
            report=p.read(folder/'diagnostic_report.json'); after=p.read(folder/'diagnostic_inputs_after.json')
            assert report['completed'] and report['closed'] and report['scene_valid'] and report['aliases_restored'] and report['loader_restored']
            assert report['failure'] is None and not report['cleanup_errors'] and report['changed_inputs']==report['unpinned_project_sources']==[]
            assert report['fit_steps']==report['critic_warmup_steps']==0 and report['NN_constructions']==int(name not in ('reference','zero'))
            assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
            p.verify_pins(after['input_pins']); p.verify_pins(report['result_sha256'])
            assert all(after['input_pins'][x]==h for x,h in seal['input_pins'].items())
            contract=p.read(folder/'training_contract.json'); scene=p.read(folder/'gpu_scene_final.json')
            assert contract['observation']['dimension']==557 and contract['task']['finger_skill']['schema']=='guitar_learning.finger_skill.v3' and contract['task']['finger_skill']['phase']=='J'
            assert scene['closed'] and scene['environment_count']==128 and scene['diagnostic_guitar_mode']=='fixed' and scene['hand_collision_native_readback_environments']==128
            native=p.read(folder/'native_effort_readback.json')
            for key in ('native_indices','changed_native_field_indices','actual_native_PD105','original_profile_native_PD105','hand_collision'):
                assert native[key]==baseline[key]
            assert len(native['actual_native_PD105'])==10 and all(len(v)==105 for v in native['actual_native_PD105'].values())
            assert len(native['native_indices'])==16 and native['unchanged_other_axes']==89 and native['hand_collision']['enabled_distinct_finger_pairs']==90
            assert len(native['direct_readback_environments'])==128 and sorted(r['env_id'] for r in native['direct_readback_environments'])==list(range(128))
            for r in native['direct_readback_environments']:
                assert r['native_PD105']==baseline['actual_native_PD105'] and r['human_shape_filters']==baseline['direct_readback_environments'][0]['human_shape_filters']
        metrics=[__import__('json').loads(x) for x in (HERE/'runs/train/metrics.jsonl').read_text().splitlines()]
        episodes=[__import__('json').loads(x) for x in (HERE/'runs/train/episodes.jsonl').read_text().splitlines()]
        assert [r['update'] for r in metrics]==list(range(1,301))
        assert all(r['transitions']==4096 and r['total_transitions']==r['update']*4096 and r['cost_weight']==1 for r in metrics)
        assert all(r['diagnostics']['physical_transitions']==4096 for r in metrics)
        for r in metrics: assert summarize([x for x in episodes if x['update']==r['update']])==r['episodes']
        reward_error=rows_check(episodes,duration); steps=[sum(r['steps'] for r in episodes if r['env_id']==i) for i in range(128)]
        assert all(x<=9600 for x in steps)
        training=dict(summary=summarize(episodes),completed_steps=sum(steps),open_transitions=1228800-sum(steps),transitions=1228800,
            mean_reward=float(np.mean([r['mean_reward'] for r in metrics])),mean_cost=float(np.mean([r['mean_failure_cost'] for r in metrics])),
            max_analytic_kl=max(r['analytic_kl'] for r in metrics),max_attempted_kl=max(r['max_attempted_kl'] for r in metrics),
            total_kl_retries=sum(r['kl_retries'] for r in metrics),reward_component_means={k:float(np.mean([r['reward_component_means'][k] for r in metrics])) for k in metrics[0]['reward_component_means']},
            scope='Changing-policy training episodes; all failures included. Open transitions are budget minus completed episode steps, not discarded episodes.')
        training['cost_signals_by_update']=[dict(update=r['update'],measured_mean_cost=r['mean_failure_cost'],raw_cost_advantage=r['diagnostics']['advantages']['cost_raw'],post_update_cost_critic=r['diagnostics']['post_update']['critics']['cost'],cost_value_loss=r['cost_value_loss']) for r in metrics]
        training['cost_advantage_range']=[min(r['diagnostics']['advantages']['cost_raw']['min'] for r in metrics),max(r['diagnostics']['advantages']['cost_raw']['max'] for r in metrics)]
        training['post_update_cost_value_range']=[min(r['diagnostics']['post_update']['critics']['cost']['value']['min'] for r in metrics),max(r['diagnostics']['post_update']['critics']['cost']['value']['max'] for r in metrics)]
        evaluations={}; motion={}
        for name in names[3:]:
            folder=HERE/'runs'/name; value=p.read(folder/'evaluation.json'); rows=value['episodes']; report=p.read(folder/'diagnostic_report.json')
            assert value['condition']=='policy' and value['policy_performance'] and value['assigned_quotas']==[1]*128 and len(rows)==128 and sorted(r['env_id'] for r in rows)==list(range(128))
            assert value['summary']==summarize(rows); reward_error=max(reward_error,rows_check(rows,duration))
            stochastic=name.endswith('_stochastic'); update=300 if stochastic else int(name[-6:])
            assert report['phase']=='evaluate' and report['update']==update and report['sampling']==('stochastic' if stochastic else 'mean')
            assert report['policy_noise_seed']==(7 if stochastic else None)
            evaluations[name]=dict(update=update,sampling=report['sampling'],summary=value['summary'],
                mean_missing_fraction=sum(r['missing_fraction'] for r in rows)/128,mean_cost=sum(r['cost'] for r in rows)/128,
                reward_component_means={k:sum(r['reward_components'][k] for r in rows)/128 for k in rows[0]['reward_components']})
            joint_stats={}
            for key in ('actual_native_limit_fraction','target_native_limit_fraction','tracking_error_rms_rad','tracking_error_max_abs_rad'):
                assert all([r['angles']['joint_names'][j] for j in (13,14,15,16)]==task['learned_action_names'] for r in rows)
                values=np.array([[r['angles']['values'][key][j] for j in (13,14,15,16)] for r in rows])
                joint_stats[key]=dict(mean_by_axis=values.mean(axis=0).tolist(),max_by_axis=values.max(axis=0).tolist(),mean_all_axes=float(values.mean()),max_all_axes=float(values.max()))
            evaluations[name]['selected_joint_diagnostics']=dict(joint_names=task['learned_action_names'],statistics=joint_stats,scope='Equal weight per first attempt (128); means/maxima of stored episode summaries, not pooled endpoint RMS or shape/causal attribution.')
            trace=np.load(folder/'trace_env0_episode0.npz',allow_pickle=False); meta=p.read(folder/'trace_metadata.json'); t=trace['time_s']
            ids=[meta['joint_names'].index(n) for n in task['learned_action_names']]; assert ids==[64,65,66,67]
            assert len(t)==next(r['steps'] for r in rows if r['env_id']==0)
            np.testing.assert_allclose(t,np.arange(1,len(t)+1)/60,rtol=0,atol=1e-12)
            body=trace['body_state'].astype(float); bn=meta['body_names']; wrist=body[:,bn.index('human/L_Wrist')]; guitar=body[:,bn.index('guitar/guitar')]
            relative=np.stack([Rotation.from_quat(wrist[:,3:7]).inv().apply(body[:,bn.index('human/LH:ring'+str(i)),:3]-wrist[:,:3]) for i in (1,2,3)],axis=1)
            wrist_G=Rotation.from_quat(guitar[:,3:7]).inv().apply(wrist[:,:3]-guitar[:,:3])
            q=trace['q'][:,ids].astype(float); target=trace['target'][:,ids].astype(float)
            motion[name]=dict(time_s=t.tolist(),ring_origin_in_actual_wrist_displacement_mm=(np.linalg.norm(relative-relative[0],axis=2)*1000).tolist(),
                wrist_origin_in_guitar_displacement_mm=(np.linalg.norm(wrist_G-wrist_G[0],axis=1)*1000).tolist(),
                endpoint_only_q_range_rad=np.ptp(q,axis=0).tolist(),endpoint_only_target_range_rad=np.ptp(target,axis=0).tolist(),tracking_RMS_rad=np.sqrt(np.mean((q-target)**2,axis=0)).tolist())
        fixed=[evaluations['evaluation_%06d'%u] for u in e.UPDATES]
        passed=[v['summary']['achieved_fraction']>=.8 and v['summary']['mean_clean_fraction']>=.7 and v['summary']['mean_audible_wrong_fraction']<=.1 and v['summary']['physical_failure_fraction']<=.05 for v in fixed]
        pairs=[[a,b] for a,b,pa,pb in zip(e.UPDATES,e.UPDATES[1:],passed,passed[1:]) if pa and pb]
        fig,ax=plt.subplots(2,3,figsize=(16,8)); x=list(e.UPDATES); last=evaluations['evaluation_000300_stochastic']
        for key,label,threshold in [('achieved_fraction','achieved',.8),('mean_clean_fraction','clean',.7)]:
            ax[0,0].plot(x,[v['summary'][key] for v in fixed],'-o',label=label); ax[0,0].axhline(threshold,linestyle=':',alpha=.5); ax[0,0].scatter([300],[last['summary'][key]],marker='D',label=label+' last stochastic')
        for key,label in [('mean_audible_wrong_fraction','wrong'),('physical_failure_fraction','physical failure'),('wrist_failure_fraction','wrist failure')]: ax[0,1].plot(x,[v['summary'][key] for v in fixed],'-o',label=label)
        ax[0,1].axhline(.1,linestyle=':',color='gray'); ax[0,1].axhline(.05,linestyle=':',color='black')
        for key in fixed[0]['reward_component_means']: ax[0,2].plot(x,[v['reward_component_means'][key] for v in fixed],label=key.replace('song_',''))
        u=np.arange(1,301); ax[1,0].plot(u,[r['mean_reward'] for r in metrics],label='reward'); ax[1,0].plot(u,[r['mean_failure_cost'] for r in metrics],label='cost')
        ax[1,1].plot(u,[r['analytic_kl'] for r in metrics],label='accepted KL'); ax[1,1].plot(u,[r['max_attempted_kl'] for r in metrics],alpha=.6,label='max attempted KL'); ax[1,1].axhline(.02,linestyle=':',color='black')
        ax[1,2].plot(u,[r['episodes']['episodes'] for r in metrics],label='completed episodes'); ax[1,2].plot(u,[r['kl_retries'] for r in metrics],label='KL retries')
        for a,title in zip(ax.flat,['Fixed evaluation (+ last stochastic)','Fixed wrong/failure fractions','Fixed reward9 means','Changing-policy training reward/cost','Training KL (threshold .02)','Training completions and retries']): a.set_title(title); a.set_xlabel('PPO update'); a.legend(fontsize=6); a.grid(alpha=.2)
        fig.tight_layout(); fig.savefig(out/'learning.png',dpi=150); plt.close(fig)
        fig,ax=plt.subplots(2,2,figsize=(12,8)); selected=['evaluation_000000','evaluation_000300','evaluation_000300_stochastic']
        for i,name in enumerate(selected):
            m=motion[name]; label=['initial mean','final mean','final stochastic'][i]; pos=np.arange(4)+(i-1)*.24
            ax[0,0].bar(pos,m['endpoint_only_q_range_rad'],width=.23,label=label); ax[0,1].bar(pos,m['tracking_RMS_rad'],width=.23,label=label)
            for b in range(3): ax[1,0].plot(m['time_s'],np.array(m['ring_origin_in_actual_wrist_displacement_mm'])[:,b],color=['tab:blue','tab:orange','tab:green'][i],linestyle=['-', '--', ':'][b],label=label+' ring'+str(b+1))
            ax[1,1].plot(m['time_s'],m['wrist_origin_in_guitar_displacement_mm'],label=label)
        for a,title in zip(ax.flat,['Env0 joint range (endpoints only), rad','Env0 target tracking RMS, rad','Body origins relative to actual wrist, mm','Wrist origin relative to guitar, mm']): a.set_title(title); a.legend(fontsize=6,ncol=2); a.grid(alpha=.2)
        for a in ax[0]: a.set_xticks(range(4)); a.set_xticklabels(['ring1_x','ring1_z','ring2','ring3'])
        for a in ax[1]: a.axvspan(3,3+duration,color='gray',alpha=.15); a.set_xlabel('Local time (s); shaded = original audible window')
        fig.tight_layout(); fig.savefig(out/'motion.png',dpi=150); plt.close(fig)
        result=dict(schema='diagnostic.current_ring_learning.analysis.v1',evaluated_attempts=1024,evaluations=evaluations,training=training,
            fixed_acceptance_by_update=dict(zip(map(str,e.UPDATES),passed)),consecutive_fixed_pass_pairs=pairs,passes_consecutive_two=bool(pairs),max_reward_sum_error=reward_error,env0_motion=motion,
            scope='Compact note-duration/reward9/cost records for all episodes; full67 raw ledgers not stored. Actual q/target/body origins are env0 first attempt only. No pad point/FK/causal decomposition; displacement from first stored endpoint, ranges exclude reset. Original 80/70/10/5 criterion unchanged.')
        p.write(out/'analysis.json',result)
        lines=['# 현행 약지 fresh300 실제 비교','', '| 평가 | 달성/128 | clean | wrong | 물리/손목 실패 |','|---|---:|---:|---:|---:|']
        for name,v in evaluations.items():
            s=v['summary']; lines.append('| %s | %d | %.3f | %.3f | %d/%d |'%(name,round(s['achieved_fraction']*128),s['mean_clean_fraction'],s['mean_audible_wrong_fraction'],round(s['physical_failure_fraction']*128),round(s['wrist_failure_fraction']*128)))
        lines += ['', '선택4축의 전체128 첫시도 요약(시도별 동일 가중). RMS는 시도별 RMS의 평균·최대이며 전체끝점을 합친 RMS가 아니다. 한계 점유와 오차만으로 당시 형상이나 성공의 원인을 단정하지 않는다.', '', '| 평가 | 실제 한계 mean/max | 목표 한계 mean/max | 추종 RMS mean/max rad | 추종 절대오차 max rad |', '|---|---:|---:|---:|---:|']
        for name,v in evaluations.items():
            d=v['selected_joint_diagnostics']['statistics']; joint_stat_rows=[d[k] for k in ('actual_native_limit_fraction','target_native_limit_fraction','tracking_error_rms_rad')]
            lines.append('| %s | %s | %.6g |'%(name,' | '.join('%.6g/%.6g'%(x['mean_all_axes'],x['max_all_axes']) for x in joint_stat_rows),d['tracking_error_max_abs_rad']['max_all_axes']))
        lines += ['', '원80/70/10/5 기준의 연속2 고정평가: **%s**. 해당 쌍: %s.'%('통과' if pairs else '미통과',pairs), '',
            '학습은1,228,800전이·완료%d에피소드이며 진행 중 전이%d개를 별도로 남겼다. 학습 중 바뀌는 정책의 성과와 고정 저장본 평가를 합산하지 않는다. 평균 실제비용%.6g, 최대 accepted KL%.6g, 최대 attempted KL%.6g, KL재시도%d회다.'%(len(episodes),training['open_transitions'],training['mean_cost'],training['max_analytic_kl'],training['max_attempted_kl'],training['total_kl_retries']), '',
            '실제비용과 신경망의 비용예측/비용advantage는 별개다. 전체학습 raw cost advantage 범위는%s, 업데이트 후 cost value 범위는%s다. 원fresh ShortPolicy의 비용head 기본초기화를 유지했으며 V7 비용head0 조건을 상속하지 않았다. V7과의 성과 우열이나 인과 비교를 하지 않는다.'%(training['cost_advantage_range'],training['post_update_cost_value_range']), '',
            '![학습과 평가](learning.png)','', '![실제 움직임](motion.png)','',
            '선택 약지4축은 native64..67이다. 몸체 그림은 실제 ring1/2/3 원점을 실제 손목 frame으로 변환했으며 패드 접촉점이 아니다. 손목의 기타 기준 이동은 별도다. 첫60Hz 저장 끝점을 기준으로 하며 local3초부터 원음길이 %.4f초를 음영으로 표시했다. 그림의 q범위는 저장 끝점만 포함하므로 reset을 더한 환경 집계와 직접 동일시하지 않는다. 비선형 동역학의 경로 차이를 인과 기여율로 분해하지 않는다.'%duration, '',
            '전체8평가×128첫시도·9보상/비용·원분모·실제11자식 종료0·입력불변·모든128환경의105×10 native readback과90충돌쌍을 확인했다. 분석은 CPU 수치처리이며 GPU/native/NN/모델load0이다. full67 raw 원장은 없고 compact의 원누적시간을 재합산했다. 상세 q/target/몸체는 env0뿐이다.', '',
            '고정기타·유한 교사·source54 한 목표·학습seed7의 결과다. 마지막 확률 평가는 별도 정책잡음seed7이며 새 학습seed가 아니다. seed17/27·다른 손가락·실제 해제·loaded-facing negative·자유기타/J33·원67음과 영상 요건은 남아 있다. 생산 기본이나 보상을 이 분석에서 바꾸지 않았다.']
        (out/'RESULTS.md').write_text('\n'.join(lines)+'\n'); assert not {'torch','isaacgym'} & set(sys.modules); complete=True
    except BaseException as error:
        failure=p.error_info(error); raise
    finally:
        try:
            changed=[x for x,h in before.items() if not Path(x).is_file() or p.sha(x)!=h]
            p.write(out/'verification.json',dict(completed=complete and not changed,failure=failure,input_sha256=before,changed_inputs=changed,
                output_sha256={str(x):p.sha(x) for x in out.iterdir() if x.is_file() and x.name!='verification.json'},execution_counts=dict(GPU=0,native=0,NN=0,checkpoint_load=0)))
            if failure is None and changed: raise RuntimeError('Analysis inputs changed')
        except BaseException:
            if failure is None: raise


if __name__=='__main__': run()
