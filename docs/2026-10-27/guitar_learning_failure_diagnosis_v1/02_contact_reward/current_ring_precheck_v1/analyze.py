"""저장된12시도만 재계산한다. native/Torch/NN/체크포인트를 읽거나 실행하지 않는다."""
import importlib.util
import itertools
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ring_precheck_analysis_inputs', HERE/'experiment.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


def run():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '' and 'torch' not in sys.modules and 'isaacgym' not in sys.modules
    seal = e.gate(HERE/'preparation_seal.json')
    reviews = seal['review_documents_sha256']; assert len(reviews) == 2
    e.verify_pins(reviews)
    files = {Path(p) for p in seal['input_pins']} | {Path(p) for p in reviews} | {HERE/'preparation_seal.json', Path(__file__)}
    files.update(p for p in (HERE/'runs').rglob('*') if p.is_file())
    files.update(HERE.glob('execution_*'))
    before = {str(p): e.sha(p) for p in sorted(files)}
    out = HERE/'analysis/results_v1'; out.mkdir(parents=True,exist_ok=False)
    failure = None; completed = False
    try:
        import numpy as np
        from scipy.spatial.transform import Rotation
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        initial_paths = [p for p,h in seal['input_pins'].items() if h == '5b84e68b085ef63133bb1834c65d25c5413584d36a7998b31c9253beaac75e1b']
        assert len(initial_paths) == 1
        prepared_paths = [p for p,h in seal['input_pins'].items() if h == '49631241132d303e36ae02cc40a3a6e035f68d3dd54982f8a4a2c3b50e0970db']; assert len(prepared_paths) == 1
        prepared = e.read(prepared_paths[0])
        reset_q = np.array([r['pos'] for r in prepared['sample']['native']['human_dof_states']],dtype=np.float32)
        reset_target = np.array(prepared['metadata']['prepared_target105_rad'],dtype=np.float32)
        initial = e.read(initial_paths[0]); shapes = initial['actual_shape_properties']['human']
        fig, axes = plt.subplots(2,2,figsize=(12,8)); cases = {}; total = 0; maximum_reward_error = 0.
        table = ['| 조건 | 달성/4 | clean | wrong | missing | 물리/손목 실패 |', '|---|---:|---:|---:|---:|---:|']
        for ci, control in enumerate(e.CONTROLS):
            folder = HERE/'runs'/control
            process = e.read(HERE/('execution_'+control+'_process.json')); terminal = e.read(HERE/('execution_'+control+'_exit.json'))
            assert all(terminal[k] == v for k,v in process.items()) and process['pid'] > 0 and process['start_ticks'] > 0
            assert process['control'] == control and process['review_pins'] == reviews and process['cwd'] == str(e.ROOT)
            assert process['argv'] == ['/home/ajou/miniconda3/envs/rl38/bin/python','-B',str(HERE/'experiment.py'),'execute','--control',control]
            assert terminal['returncode'] == 0 and terminal['process_terminal'] and terminal['changed_review_inputs'] == [] and terminal['finished_utc'] > terminal['started_utc']
            report = e.read(folder/'report.json'); assert all(report[k] for k in ('completed','closed','scene_valid','loader_restored'))
            assert report['failure'] is None and report['close_failure'] is None and report['changed_inputs'] == report['unpinned_project_sources'] == []
            assert all(report[k] == 0 for k in ('actual_NN_constructions','NN_forward','checkpoint_loads','fit_steps','PPO_updates'))
            pins = e.read(folder/'inputs_before.json'); after = e.read(folder/'inputs_after.json'); e.verify_pins(pins)
            assert after['verified'] and after['input_pins'] == pins and after['changed_paths'] == after['unpinned_project_sources'] == []
            assert all(pins[p] == h for p,h in {**seal['input_pins'], **reviews}.items())
            contract = e.read(folder/'training_contract.json'); config = e.read(folder/'settings.json'); task = config['song']['short_learning']
            assert config == e.read(HERE/'inputs/settings.json') and contract['observation']['dimension'] == 557
            assert contract['task']['finger_skill']['schema'] == 'guitar_learning.finger_skill.v3' and contract['task']['finger_skill']['phase'] == 'J'
            assert task['view']['source_index'] == 54 and task['teacher']['source_row'] == 16 and task['learned_action_indices'] == [25,26,27,28]
            evaluation = e.read(folder/'evaluation.json'); rows = evaluation['episodes']; first = e.read(folder/'first_attempts.json')
            assert first['completed'] and first['assigned_quotas'] == evaluation['assigned_quotas'] == [1]*4 and first['episodes'] == rows
            assert len(rows) == 4 and sorted(r['env_id'] for r in rows) == list(range(4)) and evaluation['condition'] == control and evaluation['policy_performance'] is False
            duration = task['view']['source_target']['end_s']-task['view']['source_target']['onset_s']
            fractions = np.array([[min(1., r['note'][k]/duration) for k in ('clean','wrong','missing')] for r in rows])
            for i,r in enumerate(rows):
                assert r['valid'] and r['target_id'] == 'event-000053/string-3/note-54' and r['selected_target_count'] == 1
                np.testing.assert_allclose(fractions[i], [r[k] for k in ('clean_fraction','audible_wrong_fraction','missing_fraction')],rtol=0,atol=1e-14)
                assert abs(sum(r['note'][k] for k in ('clean','wrong','missing'))-duration) < 1e-12
                assert len(r['reward_components']) == 9 and abs(sum(r['cost_components'].values())-r['cost']) < 1e-7
                maximum_reward_error = max(maximum_reward_error,abs(sum(r['reward_components'].values())-r['reward']))
            assert maximum_reward_error < 1e-5
            s = dict(episodes=4,denominator='all assigned evaluation attempts, including failures',achieved_fraction=sum(r['achieved'] for r in rows)/4,
                mean_clean_fraction=float(fractions[:,0].mean()),mean_audible_wrong_fraction=float(fractions[:,1].mean()),
                physical_failure_fraction=sum(r['termination']['physical_failure'] for r in rows)/4,wrist_failure_fraction=sum(r['termination']['wrist_failure'] for r in rows)/4,any_failure_fraction=sum(r['reason']=='terminal_failure' for r in rows)/4)
            assert s == evaluation['summary']; total += len(rows)
            pd = e.read(folder/'native_effort_readback.json'); ids = pd['native_indices']; assert len(ids) == 16 and pd['unchanged_other_axes'] == 89
            baseline = pd['original_profile_native_PD105']; actual = pd['actual_native_PD105']; assert len(actual) == len(baseline) == 10
            for k in actual:
                assert len(actual[k]) == len(baseline[k]) == 105
                changed = np.flatnonzero(np.array(actual[k]) != np.array(baseline[k])).tolist()
                assert changed == pd['changed_native_field_indices'][k] == (ids if k == 'effort' else [])
            assert all(actual['effort'][i] == .25 and baseline['effort'][i] == 20 for i in ids)
            collision = pd['hand_collision']; changes = {(r['body'],r['shape']):r for r in collision['changed_filters']}
            shape_rows = [(n,i,r['filter']) for n in initial['human_body_names'] for i,r in enumerate(shapes[n])]
            filters = [changes.get((n,i),{}).get('after',v) for n,i,v in shape_rows]
            pairs_changed = sum(((a[2]&b[2])==0) != ((filters[i]&filters[j])==0) for (i,a),(j,b) in itertools.combinations(enumerate(shape_rows),2))
            assert pairs_changed == collision['enabled_distinct_finger_pairs'] == 90
            assert len(pd['direct_readback_environments']) == 4 and sorted(r['env_id'] for r in pd['direct_readback_environments']) == list(range(4))
            for direct in pd['direct_readback_environments']:
                assert direct['native_PD105'] == actual and direct['human_shape_filters'] == filters
            scene = e.read(folder/'gpu_scene_final.json'); assert scene['closed'] and scene['hand_collision'] == collision and scene['hand_collision_native_readback_environments'] == 4
            assert scene['environment_count'] == 4 and scene['diagnostic_guitar_mode'] == 'fixed' and scene['physics_steps'] == report['resources']['physics_steps'] == 880
            trace = np.load(folder/'trace_env0_episode0.npz',allow_pickle=False); velocity = np.load(folder/'selected_native_velocity_env0.npz',allow_pickle=False)['qd']
            metadata = e.read(folder/'trace_metadata.json'); names = metadata['joint_names']; body_names = metadata['body_names']
            joints = task['learned_action_names']; native = [names.index(n) for n in joints]; assert native == [64,65,66,67]
            times = trace['time_s']; np.testing.assert_allclose(times,np.arange(1,221)/60,atol=1e-12,rtol=0)
            assert trace['q'].shape == trace['target'].shape == (220,105) and velocity.shape == (220,4)
            q = trace['q'][:,native]; target = trace['target'][:,native]
            env0 = next(r for r in rows if r['env_id']==0); slots = [env0['angles']['joint_names'].index(n) for n in joints]
            for key,array,reset in [('actual_range_rad',q,reset_q),('target_range_rad',target,reset_target)]:
                combined = np.vstack([reset[native],array]).astype(float)
                np.testing.assert_allclose(np.ptp(combined,axis=0),np.array(env0['angles']['values'][key])[slots],atol=1e-7,rtol=0)
            np.testing.assert_allclose(np.sqrt(np.mean((q.astype(float)-target)**2,axis=0)),np.array(env0['angles']['values']['tracking_error_rms_rad'])[slots],atol=1e-12,rtol=0)
            state = trace['body_state'].astype(float); wrist = state[:,body_names.index('human/L_Wrist')]; guitar = state[:,body_names.index('guitar/guitar')]
            ring_names = ['human/LH:ring'+str(i) for i in (1,2,3)]
            relative = np.stack([Rotation.from_quat(wrist[:,3:7]).inv().apply(state[:,body_names.index(n),:3]-wrist[:,:3]) for n in ring_names],axis=1)
            wrist_G = Rotation.from_quat(guitar[:,3:7]).inv().apply(wrist[:,:3]-guitar[:,:3])
            ring_delta = np.linalg.norm(relative-relative[0],axis=2)*1000; wrist_delta = np.linalg.norm(wrist_G-wrist_G[0],axis=1)*1000
            audible = (times > 3.) & (times <= 3.+duration+1e-12)
            motion = dict(native_indices=native,endpoint_only_q_range_rad=np.ptp(q,axis=0).tolist(),endpoint_only_target_range_rad=np.ptp(target,axis=0).tolist(),
                reset_inclusive_q_range_rad=np.ptp(np.vstack([reset_q[native],q]).astype(float),axis=0).tolist(),
                reset_inclusive_target_range_rad=np.ptp(np.vstack([reset_target[native],target]).astype(float),axis=0).tolist(),
                tracking_RMS_rad=np.sqrt(np.mean((q-target)**2,axis=0)).tolist(),native_qd_RMS_rad_s=np.sqrt(np.mean(velocity**2,axis=0)).tolist(),
                ring_body_names=ring_names,ring_origin_in_actual_wrist_displacement_max_mm=ring_delta.max(axis=0).tolist(),
                wrist_origin_in_G_displacement_max_mm=float(wrist_delta.max()),audible_ring_relative_mean_mm=ring_delta[audible].mean(axis=0).tolist(),
                audible_wrist_G_mean_mm=float(wrist_delta[audible].mean()),all4_selected_motion=[dict(env_id=r['env_id'],values={k:[v[j] for j in slots] for k,v in r['angles']['values'].items()}) for r in rows])
            cases[control] = dict(summary=s,mean_missing_fraction=float(fractions[:,2].mean()),duration_s=duration,env0_motion=motion,process=terminal)
            table.append('| %s | %d | %.3f | %.3f | %.3f | %d/%d |'%(control,sum(r['achieved'] for r in rows),*fractions.mean(axis=0),sum(r['termination']['physical_failure'] for r in rows),sum(r['termination']['wrist_failure'] for r in rows)))
            color = ['tab:blue','tab:orange','tab:green'][ci]; x = np.arange(4)+(ci-1)*.24
            axes[0,0].bar(x,np.ptp(q,axis=0),width=.23,label=control,color=color); axes[0,1].bar(x,np.sqrt(np.mean(velocity**2,axis=0)),width=.23,label=control,color=color)
            for bi in range(3): axes[1,0].plot(times,ring_delta[:,bi],color=color,linestyle=['-', '--', ':'][bi],label=control+' ring'+str(bi+1))
            axes[1,1].plot(times,wrist_delta,color=color,label=control)
        assert total == 12 and 'torch' not in sys.modules and 'isaacgym' not in sys.modules
        for ax,title,unit in zip(axes.flat,['Env0 joint range (220 endpoints only)','Env0 native qd RMS','Body origins relative to actual wrist','Actual wrist origin relative to guitar'],['rad','rad/s','mm from first stored endpoint','mm from first stored endpoint']):
            ax.set_title(title); ax.set_ylabel(unit); ax.legend(fontsize=7,ncol=2); ax.grid(alpha=.2)
        for ax in axes[0]: ax.set_xticks(range(4)); ax.set_xticklabels(['ring1_x','ring1_z','ring2','ring3'])
        for ax in axes[1]: ax.axvspan(3,3+duration,color='gray',alpha=.15); ax.set_xlabel('Local time (s); shade = audible window')
        fig.tight_layout(); fig.savefig(out/'motion.png',dpi=150); plt.close(fig)
        e.write(out/'analysis.json',dict(schema='diagnostic.current_ring.actual_analysis.v1',attempts=total,cases=cases,max_reward_component_sum_error=maximum_reward_error,
            raw_scope='All4 per control: stored compact note durations, reward9/cost components. Full67 raw ledgers were not saved. Pose/q/target/qd traces are env0 only; all4 motion summaries retained.',
            motion_scope='Stored actual native body origins, not pad contact points; scipy quaternion inverse rotation, no FK/oracle. Displacement starts at first60Hz endpoint, not reset. Native qd is not asserted to equal derivative of qpos. Nonlinear path differences are not a causal or additive percentage decomposition.'))
        lines = ['# 현재557 약지 scripted 대조: 실제12시도','',*table,'',
            '현재 source54 약지 한 목표에서 reference는4/4·clean1, zero/random은0/4·clean0이다. 모든 조건의 wrong·물리 실패·손목 실패는0이다. 이 seed7/4환경의 한 평가에서 지원 제어만으로 성공했다고 볼 근거는 없으며, 약지 선택 행동을 추가한 조건에서 성공이 관찰됐다. 네 환경은 네 seed가 아니다.', '',
            '전체12시도 원분모·원장 시간·9보상/비용 합·각4환경의 native PD105×10속성·16축 effort20→0.25와 다른89축 보존·90충돌쌍·scene close·실제종료0·542입력과 별도검수2문서 SHA를 확인했다. source54/row16·557/Jv3이며 과거561 결과를 상속하지 않았다. 교사의 세 CAS 경로 번역 외 모든 숫자는 원문과 같다.', '',
            '## 실제 움직임 (env0)', '', '| 조건 | 약지3 몸체의 손목 기준 최대 이동 mm | 손목의 기타 기준 최대 이동 mm |', '|---|---|---:|']
        for c,v in cases.items():
            m=v['env0_motion']; lines.append('| %s | %s | %.3f |'%(c,', '.join('%.3f'%x for x in m['ring_origin_in_actual_wrist_displacement_max_mm']),m['wrist_origin_in_G_displacement_max_mm']))
        lines += ['', '![저장된 실제 움직임](motion.png)', '', '그림과 수치는 첫60Hz 저장 끝점부터 계산했다. 회색은 local3초부터 원음길이 %.4f초다. 실제 ring1/2/3 **몸체 원점**을 실제 손목 좌표로 회전·이동 변환했으며 패드 점이나 접촉 압력이 아니다. 손목의 기타 기준 이동은 별도다. 두 움직임의 비선형 경로 차이를 인과100%% 분해나 성공 기여율로 해석하지 않는다. 그림의 선택4축 범위는220끝점만 포함하며 환경 요약은reset을 포함한221점이다. 원reset q/target을 더한 범위와 요약을 대조했다. 선택4축 q/target 범위·추종오차·native qd RMS와 전체4환경 motion summary는 analysis.json에 보존했다.'%duration, '',
            'full67 raw 원장은 저장되지 않아 각4 compact에 남은 원누적 clean/wrong/missing 시간으로 재합산했다. q/target/qd/pose 상세는 env0 첫시도만 있다. 다른 환경은 저장된 motion summary다. 이번 재계산은 GPU/native/NN/모델load0이다.', '',
            '원80%달성·70%clean·wrong10%이하·실패5%이하를 연속2평가하는 수용기준과 seed17/27·나머지 손가락·자유기타/J33·67음·RL·실제 해제 검증은 남아 있다. 이번 scripted 한 평가의4/4를 학습성과나 전체과제 성공으로 확대하지 않는다.']
        (out/'RESULTS.md').write_text('\n'.join(lines)+'\n'); completed = True
    except BaseException as error:
        failure = e.error_info(error)
        raise
    finally:
        try:
            changed = [p for p,h in before.items() if not Path(p).is_file() or e.sha(p)!=h]
            e.write(out/'verification.json',dict(completed=completed and not changed,failure=failure,input_sha256=before,changed_inputs=changed,
                output_sha256={str(p):e.sha(p) for p in out.iterdir() if p.name!='verification.json' and p.is_file()},
                execution_counts=dict(GPU=0,native=0,NN=0,checkpoint_load=0)))
            if failure is None and changed: raise RuntimeError('Analysis inputs changed')
        except BaseException:
            if failure is None: raise


if __name__ == '__main__':
    run()
