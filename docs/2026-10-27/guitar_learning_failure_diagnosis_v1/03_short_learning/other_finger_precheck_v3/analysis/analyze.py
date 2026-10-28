"""CPU audit of twelve completed original-CLI precheck stages."""
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
RUNS = BASE/'runs'
FINGERS = ('index', 'ring', 'pinky')
CONTROLS = ('reference', 'zero', 'random')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment

    outputs = ('audit.json', 'validation.json', 'conditions.csv', 'precheck.png', 'RESULTS.md')
    assert not any((HERE/name).exists() for name in outputs)
    torch.set_num_threads(1)
    hashes, verified, checks, summaries, traces = {}, {}, [], [], {}

    def remember(path):
        value = sha(path)
        hashes[str(path)] = value
        return value

    def stat(values):
        values = np.asarray(values, dtype=float)
        return dict(min=values.min(axis=0).tolist(), median=np.median(values, axis=0).tolist(),
            max=values.max(axis=0).tolist())

    launcher = read(BASE/'01_launcher.json')
    assert launcher['returncode'] == 0
    report = read(RUNS/'report.json')
    assert report['completed'] and len(report['stages']) == 12
    expected = {f+'_'+c for f in FINGERS for c in ('initial',)+CONTROLS}
    assert {s['name'] for s in report['stages']} == expected
    for p in (BASE/'01_launcher.json', RUNS/'report.json', BASE/'cpu_verification.json', BASE/'preparation_seal.json'):
        remember(p)
    seal = read(BASE/'preparation_seal.json')
    assert seal['independent_review'] == 'passed_no_findings'
    assert all(sha(path) == value for path, value in seal['input_sha256'].items())
    metadata, _ = fixture(1)
    source_rel = ('guitar_learning/gpu/environment.py', 'guitar_learning/gpu/simplified_finger_environment.py',
        'guitar_learning/gpu/fingertip_pad.py', 'guitar_learning/gpu/wrong_press.py',
        'guitar_learning/tool/experiments/short_finger_learning/runtime.py',
        'guitar_learning/tool/experiments/short_finger_learning/runner.py')
    root = BASE.parents[4]
    assert (root/'guitar_learning').is_dir()
    for rel in source_rel+('guitar_learning/tests/test_gpu_environment.py',):
        remember(root/rel)
    for finger in FINGERS:
        initial = RUNS/(finger+'_initial')
        initial_sha = remember(initial/'initial.pt')
        model = torch.load(initial/'initial.pt', map_location='cpu', weights_only=False)
        assert model['updates'] == 0 and model['metadata']['settings']['updates'] == 1
        del model
        same_settings, same_contract = None, None
        for control in ('initial',)+CONTROLS:
            name = finger+'_'+control
            folder = RUNS/name
            result, after = read(folder/'report.json'), read(folder/'inputs_after.json')
            before, scene = read(folder/'inputs_before.json'), read(folder/'gpu_scene_final.json')
            settings, contract = read(folder/'settings.json'), read(folder/'training_contract.json')
            assert result['completed'] and result['closed'] and result['failure'] is None
            assert not result['changed_inputs'] and not result['unpinned_project_sources']
            assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
            assert before == after['input_pins'] and scene['closed'] and scene['num_envs'] == 4
            for path, value in before.items():
                if path not in verified:
                    verified[path] = sha(path)
                assert verified[path] == value, path
            for rel in source_rel:
                assert before[str(root/rel)] == hashes[str(root/rel)]
            for f in ('report.json', 'inputs_before.json', 'inputs_after.json', 'gpu_scene_final.json', 'settings.json', 'training_contract.json'):
                remember(folder/f)
            checks.append(dict(stage=name, completed=True, closed=True, input_pins=len(before)))
            spec = settings['song']['short_learning']
            assert settings['seed'] == 7 and settings['num_envs'] == 4 and settings['updates'] == 1
            if control == 'initial':
                metrics = [json.loads(l) for l in (folder/'metrics.jsonl').read_text().splitlines()]
                assert len(metrics) == 1 and metrics[0]['total_transitions'] == 128
                remember(folder/'metrics.jsonl')
                continue
            assert before[str(initial/'initial.pt')] == initial_sha
            assert str(initial/'final.pt') not in before
            if same_settings is None:
                same_settings, same_contract = settings, contract
            assert settings == same_settings and contract == same_contract
            evaluation = read(folder/'evaluation.json')
            episodes = evaluation['episodes']
            assert evaluation['condition'] == control and not evaluation['policy_performance']
            assert evaluation['assigned_quotas'] == [1]*4 and len(episodes) == 4
            assert sorted(e['env_id'] for e in episodes) == list(range(4))
            summary = dict(episodes=4, achieved_fraction=sum(bool(e['achieved']) for e in episodes)/4,
                mean_clean_fraction=sum(e['clean_fraction'] for e in episodes)/4,
                mean_audible_wrong_fraction=sum(e['audible_wrong_fraction'] for e in episodes)/4,
                physical_failure_fraction=sum(e['termination']['physical_failure'] for e in episodes)/4,
                wrist_failure_fraction=sum(e['termination']['wrist_failure'] for e in episodes)/4,
                any_failure_fraction=sum(e['reason'] == 'terminal_failure' for e in episodes)/4)
            assert all(abs(evaluation['summary'][key]-value) < 1e-12 for key, value in summary.items())
            summaries.append(dict(finger=finger, control=control, achieved=round(4*summary['achieved_fraction']), **summary))
            remember(folder/'evaluation.json')
            t = np.load(folder/'trace_env0_episode0.npz')
            trace_meta = read(folder/'trace_metadata.json')
            assert trace_meta['joint_names'] == metadata['joint_names'] and trace_meta['body_names'] == metadata['body_names']
            selected_names = spec['learned_action_names']
            selected = [trace_meta['joint_names'].index(n) for n in selected_names]
            body = trace_meta['body_names'].index('human/LH:'+finger+'3')
            guitar, wrist = [trace_meta['body_names'].index(n) for n in ('guitar/guitar', 'human/L_Wrist')]
            local = t['time_s']
            view = spec['view']
            assert np.max(abs(t['source_time_s']-local-view['score_offset_s'])) < 1e-9
            phases = dict(before=local < view['local_onset_s']-1e-9,
                audible=(local >= view['local_onset_s']-1e-9) & (local <= view['local_end_s']+1e-9),
                after=local > view['local_end_s']+1e-9)
            assert np.all(sum(mask.astype(int) for mask in phases.values()) == 1)
            q, target = np.rad2deg(t['q'][:, selected]), np.rad2deg(t['target'][:, selected])
            actual_G = Rotation.from_quat(t['body_state'][:, guitar, 3:7]).inv().apply(
                t['body_state'][:, wrist, :3]-t['body_state'][:, guitar, :3])
            actual_R = Rotation.from_quat(t['body_state'][:, guitar, 3:7]).inv()*Rotation.from_quat(t['body_state'][:, wrist, 3:7])
            position_error = np.linalg.norm(t['wrist_goal_G_m']-actual_G, axis=1)*1000
            rotation_error = np.rad2deg((Rotation.from_quat(t['wrist_goal_G_xyzw']).inv()*actual_R).magnitude())
            feedback_position = np.linalg.norm(t['wrist_pose_error_world'][:, :3], axis=1)*1000
            feedback_rotation = np.rad2deg(np.linalg.norm(t['wrist_pose_error_world'][:, 3:], axis=1)/.1)
            force = np.linalg.norm(t['net_body_force_n'][:, body], axis=1)
            env = ShortEnvironment(metadata, bundle=settings['song_training']['bundle'], song=settings['song'],
                skill=settings['finger_skill'], device='cpu')
            def snapshot(i):
                return dict(q=torch.tensor(t['q'][i:i+1]), qd=torch.zeros(1, 105), target=torch.tensor(t['target'][i:i+1]),
                    body_state=torch.tensor(t['body_state'][i:i+1]), contact_force=torch.tensor(t['net_body_force_n'][i:i+1]))
            env.reset([0], snapshot(0))
            j = env.selected_index
            gate_rows = []
            for i, now in enumerate(local):
                env.clock[0] = round(now*240)
                env._snapshot(snapshot(i))
                assert bool(env.candidate[0, j]) == bool(t['candidate'][i])
                assert bool(env.wrong[0, j]) == bool(t['wrong'][i])
                assert abs(float(env.surface_distance[0, j])-t['surface_distance_m'][i]) < 1e-6
                assert abs(float(env.surface_height[0, j])-t['surface_height_m'][i]) < 1e-6
                gate_rows.append(dict(time_s=float(now), loaded=bool(env.surface_body_loaded[0, j]),
                    any_sample_position=bool(env.contact_geometry[0, j]),
                    any_same_sample_position_and_facing=bool(env.contact_facing[0, j]),
                    positive_before_wrong=bool(env.contact_loaded_target[0, j]),
                    candidate=bool(env.candidate[0, j]), wrong=bool(env.wrong[0, j]),
                    nearest_normal_cos=float(env.surface_alignment[0, j])))
            phase_rows = {}
            for phase, mask in phases.items():
                ids = np.flatnonzero(mask)
                gates = {key:sum(gate_rows[i][key] for i in ids) for key in ('loaded', 'any_sample_position',
                    'any_same_sample_position_and_facing', 'positive_before_wrong', 'candidate', 'wrong')}
                phase_rows[phase] = dict(endpoint_count=len(ids), first_time_s=float(local[ids[0]]), last_time_s=float(local[ids[-1]]),
                    gates=gates, actual_selected_deg=stat(q[mask]), target_selected_deg=stat(target[mask]),
                    target_minus_actual_deg=stat(target[mask]-q[mask]), nearest_pad_distance_mm=stat(t['surface_distance_m'][mask]*1000),
                    nearest_signed_height_mm=stat(t['surface_height_m'][mask]*1000),
                    distal_body_resultant_N=stat(force[mask]), post_step_wrist_position_error_mm=stat(position_error[mask]),
                    post_step_wrist_rotation_error_deg=stat(rotation_error[mask]),
                    pre_control_feedback_position_error_mm=stat(feedback_position[mask]),
                    pre_control_feedback_rotation_error_deg=stat(feedback_rotation[mask]))
            learning = spec['learned_action_indices']
            zero_target_range = np.ptp(t['target'][:, selected], axis=0)
            if control == 'zero':
                assert np.count_nonzero(t['policy_action'][:, learning]) == 0
                assert np.max(zero_target_range) == 0
            traces[name] = dict(scope='env0 first attempt only; native 60Hz endpoints; original production helpers reconstructed on CPU; no new physics',
                original_source_target_id=view['source_target']['target_id'], physical_string_1_based=view['source_target']['string']+1,
                fret=view['source_target']['fret'], selected_joint_names=selected_names, view=view,
                phases=phase_rows, endpoints_recomputed=len(local), gates=gate_rows,
                zero_selected_target_range_rad=zero_target_range.tolist() if control == 'zero' else None,
                native_episode_rows=[dict(env_id=e['env_id'], achieved=e['achieved'], reason=e['reason'], note=e['note']) for e in episodes],
                wrist_error_scope='post-step body_state versus recorded next-tick G goal; separate feedback field is pre-control pose versus next goal, rotation scaled0.1 before unscaling',
                qd_missing_scope='qd set0 solely for CPU geometry replay; saved body velocities preserved; contact position/load/wrong predicates do not use joint qd')
            for f in ('trace_env0_episode0.npz', 'trace_metadata.json'):
                remember(folder/f)
    assert all(r['any_failure_fraction'] == 0 for r in summaries)
    idx = traces['index_reference']['phases']['audible']
    assert idx['endpoint_count'] == 11 and idx['gates']['loaded'] == 11 and idx['gates']['any_sample_position'] == 0
    assert not torch.cuda.is_initialized()
    audit = dict(completed=True, summary=summaries, env0_traces=traces,
        limitations=['All4 musical fractions are native240Hz-integrated note ledger results. Candidate counts are env0 stored60Hz endpoints only.',
            'Nearest distance/height/normal is one independently selected pad sample; positive requires any same sample passing all geometry/facing/load gates.',
            'Body resultant is net body contact load, not identified string force, pressure, pair contact, acoustic success or causal contribution.',
            'Bootstrap trained final.pt is unused; scripted reference/zero/random are not learned policy performance.',
            'Only fixed guitar, finite wrist teacher, source note and four assigned attempts per condition; no free-guitar/full-song/general reachability claim.'])
    validation = dict(completed=True, launcher_returncode=0, outer_wall_s=launcher['wall_s'], stage_checks=checks,
        all12_scenes_closed=True, all9_evaluations_quotas4_failures_included=True,
        same_initial_checkpoint_and_settings_per_finger=True, initial_checkpoints_update0=True,
        unique_current_input_paths_verified=len(verified), preparation_pins_verified=len(seal['input_sha256']),
        all_stored_candidate_wrong_distance_height_endpoints_match_production=True,
        input_sha256=hashes, script_sha256=sha(Path(__file__)), GPU_executed=False, CUDA_initialized=False)
    for name, value in (('audit.json', audit), ('validation.json', validation)):
        with (HERE/name).open('x') as f:
            json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\n')
    with (HERE/'conditions.csv').open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    font = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams['font.family'] = font.get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.7), sharey=True)
    labels = dict(index='검지', ring='약지', pinky='소지')
    for finger, ax in zip(FINGERS, axes):
        for control in CONTROLS:
            t = np.load(RUNS/(finger+'_'+control)/'trace_env0_episode0.npz')
            ax.plot(t['time_s'], t['surface_distance_m']*1000, label=control, lw=1)
        view = traces[finger+'_reference']['view']
        ax.axvspan(3, view['local_end_s'], alpha=.12, color='green')
        ax.set_title('%s · 물리3현%d프렛' % (labels[finger], view['source_target']['fret']))
        ax.set_xlabel('로컬 시간 (초)')
        ax.grid(alpha=.2)
    axes[0].set_ylabel('nearest 패드–목표 거리 (mm)')
    axes[0].legend(fontsize=8)
    fig.suptitle('env0 첫 시도60Hz · 초록: 원래 음 구간 · 거리 단독은 성공 판정이 아님')
    fig.tight_layout()
    fig.savefig(HERE/'precheck.png', dpi=140)
    plt.close(fig)
    text = ['# 다른 세 손가락 실제 사전검사', '',
        '**검지 reference는0/4로 현재 기준 도달을 먼저 해결해야 한다. 약지 reference는4/4이며 zero1/4다. 소지는 reference4/4·zero4/4로 선택 손가락 명령이 없어도 공통 팔 teacher 조건에서 이미 달성되므로 손가락 학습 증거가 아니다.**', '',
        '원자료 선정·teacher/reference·성공 기준을 바꾸지 않고 root가 실행한12단계만 분석했다. bootstrap1업데이트는 초기값 생성용이며 모든 평가는 initial.pt만 사용했다. 아래36시도는 학습된 정책 평가가 아니라 reference/zero/초기 random 대조다.', '',
        '| 손가락 | 조건 | 달성/4 | 음중 유지 | 음중 오압현 | 물리/손목 실패 |',
        '|---|---|---:|---:|---:|---:|']
    for r in summaries:
        text.append('| %s | %s | %d | %.2f%% | %.2f%% | %.0f / %.0f |' % (labels[r['finger']], r['control'], r['achieved'],
            100*r['mean_clean_fraction'], 100*r['mean_audible_wrong_fraction'], 4*r['physical_failure_fraction'], 4*r['wrist_failure_fraction']))
    text += ['', '전체9평가의 배정4환경 첫 시도를 모두 포함했으며36시도는 모두 timeline_complete였다. 음악 유지/오압현/달성은 원래240Hz 음 원장이다. candidate의 전체4환경 시계열은 저장되지 않아 아래 candidate 수는 env0의60Hz 끝점으로 한정한다.', '',
        '![env0 거리 대조](precheck.png)', '',
        '## env0 reference의 음 전·중·후', '',
        '음 전은local t<3초, 음 중은3초≤t≤원래 end, 음 후는end 뒤다. 음 전에는 준비·접근 구간도 포함한다. 각 셀의 scalar는중앙값이며 JSON에는min/median/max와 zero/random의 같은 분해도 있다. 손목 오차는post-step 실제body pose와 해당 tick에 기록된 G목표의 차이다.', '',
        '| 손가락 | 구간 | 끝점 | candidate / wrong | nearest거리 mm | distal합력 N | 손목위치 mm | 손목회전 도 |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for finger in FINGERS:
        for phase, caption in (('before', '음 전'), ('audible', '음 중'), ('after', '음 후')):
            p = traces[finger+'_reference']['phases'][phase]
            text.append('| %s | %s | %d | %d / %d | %.2f | %.2f | %.2f | %.2f |' % (labels[finger], caption,
                p['endpoint_count'], p['gates']['candidate'], p['gates']['wrong'], p['nearest_pad_distance_mm']['median'],
                p['distal_body_resultant_N']['median'], p['post_step_wrist_position_error_mm']['median'], p['post_step_wrist_rotation_error_deg']['median']))
    text += ['', '선택4축의 순서는1_x·1_z·2·3이며 다음은음 중 env0 중앙값(도)이다.', '',
        '| 손가락 | actual q | target |', '|---|---|---|']
    for finger in FINGERS:
        p = traces[finger+'_reference']['phases']['audible']
        text.append('| %s | %s | %s |' % (labels[finger], ', '.join('%.2f' % x for x in p['actual_selected_deg']['median']),
            ', '.join('%.2f' % x for x in p['target_selected_deg']['median'])))
    text += ['', '검지 reference의 원래 음 길이는0.1703초다. 음 중 저장11끝점(3.000~3.1667초)에서 assigned distal loaded는11/11이지만 any-sample position gate는0/11, position+facing도0/11, positive-before-wrong와candidate도0/11, wrong도0/11이었다. 따라서 이 저장 끝점의 실패는 하중 gate 부재보다 목표의 유한 위치 gate 미충족으로 분리된다. 손목/선택관절 추종 오차가 함께 존재하지만 어느 제어·접촉이 이를 유발했는지는 확정하지 않는다.', '',
        'nearest 패드거리·signed height·normal은 독립적으로 고른 가장 가까운 표본의 값이다. positive는 같은 한 표본이 lateral·프렛 내부·높이·facing을 모두 만족하고 assigned body가 loaded여야 한다. nearest 값을 any-sample witness로 사용하지 않았다. JSON의 any-sample gate는 원래 production helper의 반환값이다. facing0은 position을 포함한 gate이므로 방향 단독 실패라고 해석하지 않는다.', '',
        '소지 zero의 선택4축 policy action과 전체 trace target 변동은 정확0이다. 그 조건에서4/4 달성되므로 선택 손가락 명령의 필요성이나 학습효과를 이 단음 과제로 입증하지 못한다. 공통 유한 팔/손목 teacher·엄지035·다른 손가락B·접촉 동역학이 함께 존재하므로 힘의 인과기여를 팔 하나로 확정하지 않는다. 약지4/4 대1/4 차이도4시도짜리 scripted 대조이며 RL 성과·일반 도달가능성으로 확대하지 않는다.', '',
        '## 검증과 범위', '',
        'root launcher 종료코드0·outer wall310.529007초, 12단계 완료와 scene 종료, 각 평가4분모·동일 initial checkpoint/설정·준비봉인·현재 입력 SHA를 확인했다. 판정 소스는 실제 실행의 SHA와 일치한다. 저장 q/body pose/force를 CPU ShortEnvironment._snapshot→_contacts→pad_target_geometry·wrong_press_sources에 넣어 9개 trace의 모든 저장 끝점 candidate/wrong/거리/높이를 재현했다. 함수 위치는 gpu/environment.py:501·547, gpu/simplified_finger_environment.py:117, gpu/fingertip_pad.py:177, gpu/wrong_press.py:21·46이다. joint qd는 미저장이라0으로 두었으며 이 기하·하중·wrong 판정에는 사용되지 않는다. body velocity는 보존했다. 새 물리 실행은 없다.', '',
        'audit.json에는 9조건의 env0 음 전/중/후 실제·목표각·추종오차·거리·distal 합력·gate와 전체4시도의 원래 note 원장을 기록했다. pre-control wrist feedback 오차는 다음 목표에 대한 제어 전 값으로, 별도의 post-step 오차와 구분했다. validation.json은 모든 원자료/소스 SHA와 완료 검증, conditions.csv는 전체36시도 집계다. 전체4환경의240Hz 자세·힘 극값은 저장되지 않아 확대하지 않는다. body 합력은 접촉상대·현별힘·압력·음향·인과기여 인증이 아니다.', '',
        '다음 분기는 검지의 현재 onset3초 조건에서 기준 도달/추종을 먼저 해결하고 같은 판정으로 재검증하는 것이다. 이 보고서는 target source 재선정·teacher 수정·새 성공 문턱을 채택하지 않는다. 기존 원자료의 static positive를 현재3초 조건 성공으로 상속하지 않으며, 소지의 팔 teacher 기준 단음 성공을 손가락 학습 성과로 옮기지 않는다. 기존 소스·봉인·원자료를 보존했고 분석 GPU 실행은0이다.']
    with (HERE/'RESULTS.md').open('x') as f:
        f.write('\n'.join(text)+'\n')
    print(json.dumps(dict(completed=True, summaries=summaries, current_paths=len(verified), CUDA_initialized=False)))


if __name__ == '__main__':
    main()
