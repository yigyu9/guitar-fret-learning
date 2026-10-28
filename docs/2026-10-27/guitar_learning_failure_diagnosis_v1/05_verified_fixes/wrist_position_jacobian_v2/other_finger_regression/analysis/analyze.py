"""CPU current-source audit; run only after root reports all12 stages exited."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
spec = importlib.util.spec_from_file_location('other_wrist_v2_regression', BASE/'run_regression.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
CONTROLS = ('reference', 'zero', 'random')
LABELS = dict(middle='중지', ring='약지', pinky='소지')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true')
    args = parser.parse_args()
    if not args.root_completed:
        print('Preparation only. Wait for root actual exit0 notification; no run outputs read.')
        return
    sys.path.insert(0, str(run.ROOT))
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary

    torch.set_num_threads(1)
    baseline = run.reused().original()
    for name in ('audit.json','validation.json','conditions.csv','precheck.png','RESULTS.md'):
        run.reject_existing(HERE/name)
    hashes = {}
    def remember(path):
        hashes[str(path)] = baseline.sha(path)
        return baseline.read(path)
    launcher = remember(BASE/'01_launcher.json')
    report = remember(BASE/'runs/report.json')
    seal = remember(BASE/'preparation_seal.json')
    assert launcher['returncode'] == 0 and report['completed'] and report['closed_scenes'] == 12
    plan = run.jobs()
    assert [s['name'] for s in report['stages']] == [j['name'] for j in plan]
    run.verify_seal(seal)
    checked = [dict(name=j['name'], validation=run.validate(j, seal)) for j in plan]
    assert all(s['launcher_returncode'] == 0 and s['validation'] == c['validation']
               for s, c in zip(report['stages'], checked))
    contracts = {}
    for job in plan:
        folder = Path(job['out'])
        for name in ('report.json','inputs_before.json','inputs_after.json','settings.json',
                     'training_contract.json','gpu_scene_final.json','invocation.json'):
            remember(folder/name)
        contract = baseline.read(folder/'training_contract.json')
        assert contract == contracts.setdefault(job['finger'], contract)
        if 'control' not in job:
            hashes[str(folder/'metrics.jsonl')] = baseline.sha(folder/'metrics.jsonl')
            hashes[str(folder/'initial.pt')] = baseline.sha(folder/'initial.pt')
    metadata, _ = fixture(1)
    rows, traces, plot_data = [], {}, {}

    def stat(value):
        value = np.asarray(value)
        return dict(min=value.min(axis=0).tolist(), median=np.median(value, axis=0).tolist(), max=value.max(axis=0).tolist())

    for job in (j for j in plan if 'control' in j):
        folder, name = Path(job['out']), job['name']
        settings = baseline.read(folder/'settings.json')
        short = settings['song']['short_learning']
        evaluation = remember(folder/'evaluation.json')
        assert evaluation['policy_performance'] is False and evaluation['summary'] == summary(evaluation['episodes'])
        rows.append(dict(finger=job['finger'], control=job['control'],
            achieved=sum(e['achieved'] for e in evaluation['episodes']), **evaluation['summary']))
        meta = remember(folder/'trace_metadata.json')
        trace_path = folder/'trace_env0_episode0.npz'
        hashes[str(trace_path)] = baseline.sha(trace_path)
        t = np.load(trace_path)
        assert meta['joint_names'] == metadata['joint_names'] and meta['body_names'] == metadata['body_names']
        assert meta['wrist_control'] == seal['wrist_control']
        selected = [meta['joint_names'].index(n) for n in short['learned_action_names']]
        distal, wrist, guitar = [meta['body_names'].index(n) for n in
            ('human/LH:'+job['finger']+'3', 'human/L_Wrist', 'guitar/guitar')]
        local, view = t['time_s'], short['view']
        assert np.max(abs(t['source_time_s']-local-view['score_offset_s'])) < 1e-9
        instrument = Rotation.from_quat(t['body_state'][:, guitar, 3:7])
        actual_G = instrument.inv().apply(t['body_state'][:, wrist, :3]-t['body_state'][:, guitar, :3])
        actual_R = instrument.inv()*Rotation.from_quat(t['body_state'][:, wrist, 3:7])
        position_mm = np.linalg.norm(t['wrist_goal_G_m']-actual_G, axis=1)*1000
        rotation_deg = np.rad2deg((Rotation.from_quat(t['wrist_goal_G_xyzw']).inv()*actual_R).magnitude())
        force = np.linalg.norm(t['net_body_force_n'][:, distal], axis=1)
        middle_body = meta['body_names'].index('human/LH:'+job['finger']+'2')
        middle_force = np.linalg.norm(t['net_body_force_n'][:, middle_body], axis=1)
        env = ShortEnvironment(metadata, bundle=settings['song_training']['bundle'], song=settings['song'],
            skill=settings['finger_skill'], device='cpu')
        def snapshot(i):
            return dict(q=torch.tensor(t['q'][i:i+1]), qd=torch.zeros(1,105), target=torch.tensor(t['target'][i:i+1]),
                body_state=torch.tensor(t['body_state'][i:i+1]), contact_force=torch.tensor(t['net_body_force_n'][i:i+1]))
        env.reset([0], snapshot(0))
        gates = []
        for i, now in enumerate(local):
            env.clock[0] = round(now*240)
            env._snapshot(snapshot(i))
            j = env.selected_index
            assert bool(env.candidate[0,j]) == bool(t['candidate'][i]) and bool(env.wrong[0,j]) == bool(t['wrong'][i])
            assert abs(float(env.surface_distance[0,j])-t['surface_distance_m'][i]) < 1e-6
            assert abs(float(env.surface_height[0,j])-t['surface_height_m'][i]) < 1e-6
            gates.append(dict(time_s=float(now), loaded=bool(env.surface_body_loaded[0,j]),
                any_sample_position=bool(env.contact_geometry[0,j]),
                any_same_sample_position_and_facing=bool(env.contact_facing[0,j]),
                positive_before_wrong=bool(env.contact_loaded_target[0,j]),
                candidate=bool(env.candidate[0,j]), wrong=bool(env.wrong[0,j]),
                nearest_normal_cos=float(env.surface_alignment[0,j])))
        phases = dict(before=local < view['local_onset_s']-1e-9,
            audible=(local >= view['local_onset_s']-1e-9) & (local <= view['local_end_s']+1e-9),
            after=local > view['local_end_s']+1e-9)
        phase_rows = {}
        for phase, mask in phases.items():
            ids = np.flatnonzero(mask)
            values = dict(endpoint_count=len(ids))
            if len(ids):
                values.update(first_time_s=float(local[ids[0]]), last_time_s=float(local[ids[-1]]),
                    gates={key:sum(gates[i][key] for i in ids) for key in ('loaded','any_sample_position',
                        'any_same_sample_position_and_facing','positive_before_wrong','candidate','wrong')},
                    actual_selected_deg=stat(np.rad2deg(t['q'][mask][:,selected])),
                    target_selected_deg=stat(np.rad2deg(t['target'][mask][:,selected])),
                    target_minus_actual_deg=stat(np.rad2deg((t['target']-t['q'])[mask][:,selected])),
                    wrist_position_error_mm=stat(position_mm[mask]), wrist_rotation_error_deg=stat(rotation_deg[mask]),
                    nearest_pad_distance_mm=stat(1000*t['surface_distance_m'][mask]),
                    nearest_signed_height_mm=stat(1000*t['surface_height_m'][mask]),
                    finger2_body_resultant_N=stat(middle_force[mask]), distal_body_resultant_N=stat(force[mask]))
            phase_rows[phase] = values
        if job['control'] == 'zero':
            assert np.count_nonzero(t['policy_action'][:,short['learned_action_indices']]) == 0
            assert np.max(np.ptp(t['target'][:,selected], axis=0)) == 0
        traces[name] = dict(scope='env0 first attempt; saved60Hz endpoints only', view=view,
            physical_string_1_based=view['source_target']['string']+1, selected_joint_names=short['learned_action_names'],
            phases=phase_rows, gates=gates, note_ledgers=evaluation['episodes'],
            endpoint_count=len(local), qd_scope='joint qd absent; zero solely for contact geometry replay; saved body velocities retained')
        plot_data[name] = (local,1000*t['surface_distance_m'],position_mm)
    assert len(rows) == 9 and sum(r['episodes'] for r in rows) == 36 and not torch.cuda.is_initialized()
    hashes[str(Path(__file__).resolve())] = baseline.sha(Path(__file__).resolve())
    hashes[str(HERE/'PLAN.md')] = baseline.sha(HERE/'PLAN.md')
    helper_paths = ('gpu/environment.py','gpu/simplified_finger_environment.py','gpu/fingertip_pad.py','gpu/wrong_press.py',
        'tool/experiments/short_finger_learning/runtime.py','tool/experiments/short_finger_learning/wrist.py')
    helper_sha = {str(run.ROOT/'guitar_learning'/p): seal['active_source_pins'][str(run.ROOT/'guitar_learning'/p)] for p in helper_paths}
    audit = dict(summary=rows, env0_traces=traces, scope='fixed guitar scripted/zero/initial random only; no old comparison or trained-policy claim')
    baseline.write(HERE/'audit.json', audit)
    baseline.write(HERE/'validation.json', dict(completed=True, launcher_returncode=0, outer_wall_s=launcher['wall_s'],
        stage_checks=checked, scenes_closed=12, evaluation_attempts=36, CPU_initial73_hash_verified=True,
        input_pins=hashes, preparation_pins=len(seal['input_pins']), all_saved_contact_predicates_reproduced=True,
        active_source_pins_verified=len(seal['active_source_pins']), production_helper_sha256=helper_sha,
        same_native_contract_per_finger=True, stored_env0_endpoints=sum(t['endpoint_count'] for t in traces.values()),
        CUDA_initialized=False, GPU_executed=False))
    with (HERE/'conditions.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2,3,figsize=(12,6),sharex='col')
    for col, finger in enumerate(run.FINGERS):
        for control in CONTROLS:
            local,distance,position = plot_data[finger+'_'+control]
            axes[0,col].plot(local,distance,label=control,lw=1)
            axes[1,col].plot(local,position,label=control,lw=1)
        for ax in axes[:,col]:
            ax.axvspan(3,traces[finger+'_reference']['view']['local_end_s'],alpha=.12,color='green')
            ax.grid(alpha=.2)
        axes[0,col].set_title(finger+' / env0 60Hz'); axes[1,col].set_xlabel('time (s)')
    axes[0,0].set_ylabel('nearest pad distance (mm)'); axes[0,0].legend(fontsize=8)
    axes[1,0].set_ylabel('post-step wrist goal error (mm)')
    fig.tight_layout(); fig.savefig(HERE/'precheck.png',dpi=140); plt.close(fig)
    text = ['# 손목 qpos-J v2 중지·약지·소지 실제 회귀', '',
        '**reference 달성은 중지0/4·약지4/4·소지3/4다. zero는0/4·0/4·1/4, random은0/4·0/4·1/4다. 모든36시도는 물리/손목 실패 없이 timeline_complete로 끝났다. 손목 미분 교정만으로 모든 손가락의 기준 압현이 해결되지는 않았다.**', '',
        '이번 고정 기타/팔 teacher 조건의 새 initial scripted·zero·random 9조건36첫시도만 보고한다. bootstrap final.pt는 사용하지 않았다. 과거 중지128 또는 약지/소지 구버전과 비교하지 않는다.', '',
        '| 손가락 | 조건 | 달성/4 | clean | wrong | 물리/손목 실패 |', '|---|---|---:|---:|---:|---:|']
    for row in rows:
        text.append('| %s | %s | %d | %.2f%% | %.2f%% | %d/%d |' % (LABELS[row['finger']],row['control'],row['achieved'],
            100*row['mean_clean_fraction'],100*row['mean_audible_wrong_fraction'],
            round(4*row['physical_failure_fraction']),round(4*row['wrist_failure_fraction'])))
    text += ['', '![env0 거리와 손목 추종](precheck.png)', '',
        '아래는 reference의 음 중 env0 저장 끝점이다. 거리·손목·힘은 중앙값이며 전체4환경 대표값이 아니다.', '',
        '| 손가락 | 끝점 | loaded / 위치 / 위치+facing / positive / candidate / wrong | nearest mm | 손목 mm / 도 | distal 합력 N |',
        '|---|---:|---|---:|---:|---:|']
    for finger in run.FINGERS:
        phase = traces[finger+'_reference']['phases']['audible']
        gates = phase['gates']
        text.append('| %s | %d | %s | %.2f | %.2f / %.2f | %.2f |' % (LABELS[finger],phase['endpoint_count'],
            ' / '.join(str(gates[k]) for k in ('loaded','any_sample_position','any_same_sample_position_and_facing',
                'positive_before_wrong','candidate','wrong')),phase['nearest_pad_distance_mm']['median'],
            phase['wrist_position_error_mm']['median'],phase['wrist_rotation_error_deg']['median'],phase['distal_body_resultant_N']['median']))
    text += ['', '중지 reference는 전체4시도의 평균 wrong이75%이며 clean은0이다. env0 음 중8끝점은 loaded8이지만 원래 any-sample 위치 gate0, positive/candidate0, wrong8이었다. nearest거리 약3mm만으로 원래 유한 위치 조건 통과를 주장할 수 없으며 이 요약만으로 오압현의 손가락·줄·프렛 원인이나 접촉의 인과를 확정하지 않는다. 약지/소지 reference env0의 positive/candidate 통과를 전체4개 시도의 성공으로 확대하지 않았다.', '',
        '선택4축 순서는1_x·1_z·2·3이며 다음도 reference의 음 중 env0 중앙값(도)이다.', '',
        '| 손가락 | actual q | native target |', '|---|---|---|']
    for finger in run.FINGERS:
        phase = traces[finger+'_reference']['phases']['audible']
        text.append('| %s | %s | %s |' % (LABELS[finger],', '.join('%.2f'%v for v in phase['actual_selected_deg']['median']),
            ', '.join('%.2f'%v for v in phase['target_selected_deg']['median'])))
    text += ['',
        '각 조건4환경 전체 첫 시도를 실패 포함 분모로 사용했다. 음악 지표는 원래240Hz 음 원장이며, gate/자세/힘은 env0의 저장60Hz 끝점만 재검산했다. JSON은 음 전·중·후의 선택4 실제/목표각과 차이·손목 위치/회전 오차·nearest 거리/높이·distal 합력 및 loaded/any-sample geometry/facing/positive/candidate/wrong를 포함한다.', '',
        '손목 오차는 post-step body pose와 같은 tick에 저장된 G목표의 차이다. nearest 패드 값은 독립 최근접 표본이며, positive는 같은 한 표본의 원래 위치·facing·loaded gate다. facing gate는 위치 조건도 포함하므로 방향 단독 실패로 해석하지 않는다.', '',
        '몸체 합력은 현별힘·접촉상대·압력·음향 또는 인과기여 인증이 아니며 전체4환경/240Hz 극값으로 확대하지 않는다. loaded gate는 원래 허용 패드 몸체 기준이며 distal 합력 하나와 동일하지 않다. JSON에는 finger2와distal 각각의 합력 표본도 기록했다. joint qd는 미저장이라 CPU 기하 재생에서만0을 사용했고 저장 body velocity는 유지했다. candidate/wrong/거리/높이는 현재 ShortEnvironment._snapshot→_contacts→pad_target_geometry·wrong_press_sources로9trace 총1,995끝점에서 재현했다. 이 helper들의 현재 SHA가 실제 각 실행 입력핀과 일치한다.', '',
        '소지 zero가 성공하더라도 손가락 학습 증거가 아니다. finite 팔/손목 teacher·엄지035·다른 손가락B가 함께 존재한다. 이번 scripted 대조를 전곡·자유 기타·일반 도달/학습성과로 확대하지 않는다. validation.json은 launcher/12scene/현재 source와settings/실제 initial73hash/준비봉인 검증 및 원자료 SHA를 기록한다. CPU 분석에서 새 GPU/native 실행은 없다.']
    with (HERE/'RESULTS.md').open('x') as stream: stream.write('\n'.join(text)+'\n')
    print(json.dumps(dict(completed=True, evaluations=9, attempts=36, CUDA_initialized=False)))


if __name__ == '__main__':
    main()
