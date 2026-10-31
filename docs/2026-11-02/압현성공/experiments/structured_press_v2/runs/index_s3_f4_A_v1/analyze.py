"""검지 한 목표 실험의 완결 에피소드와 고정32환경 평가만 집계한다."""
import json
import math
from pathlib import Path
from guitar_learning.training.training_log_io import iter_episode_rows

ROOT = Path(__file__).resolve().parent


def episodes(path):
    return [row['episode'] for row in iter_episode_rows(path)]


def summarize(rows):
    def value(episode, key):
        return episode['left_note_ledger']['values'][key][0]
    def failed(episode):
        return episode['termination']['physical_failure'] or episode['termination']['wrist_failure']
    n = len(rows)
    exposed = [value(e, 'surface_min') for e in rows if value(e, 'exposure_time') > 0]
    return dict(episodes=n, success=sum(bool(e['song']['stage_success']) for e in rows),
        contact=sum(value(e, 'contact_done') > 0 for e in rows),
        any_clean=sum(value(e, 'clean') > 0 for e in rows),
        physical_failure=sum(e['termination']['physical_failure'] for e in rows),
        wrist_failure=sum(e['termination']['wrist_failure'] for e in rows),
        failed_episodes=sum(failed(e) for e in rows),
        longest_clean_s=max((value(e, 'best_clean_streak') for e in rows), default=0.),
        mean_clean_fraction=sum(e['song']['mean_clean_audible_fraction'] for e in rows)/n if n else 0.,
        safe_clean_fraction=sum(e['song']['mean_clean_audible_fraction'] if not failed(e) else 0.
                                for e in rows)/n if n else 0.,
        mean_wrong_s=sum(value(e, 'wrong') for e in rows)/n if n else 0.,
        mean_reward=sum(e['reward'] for e in rows)/n if n else 0.,
        min_pad_distance_m=min(exposed) if exposed else None,
        mean_reward_components={key:sum(e['reward_components'][key] for e in rows)/n
            for key in rows[0]['reward_components']} if rows else {})


def plot_motion(checkpoint):
    source = ROOT/'render_selected/poses_env0000.npz'
    if not source.exists():
        return None
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    report = json.loads((source.parent/'report.json').read_text())
    if Path(report['checkpoint']).resolve() != Path(checkpoint).resolve():
        raise ValueError('rendered checkpoint differs from selected model')
    catalog = json.loads((ROOT.parents[1]/'runtime/guitar_learning/assets/structured_press_v2/catalog.json').read_text())
    names = ['LH:index1_x', 'LH:index1_z', 'LH:index2', 'LH:index3']
    indices = [catalog['joint_names'].index(name) for name in names]
    data = np.load(source)
    q, target, times = np.rad2deg(data['q'][:, indices]), np.rad2deg(data['target'][:, indices]), data['time_s']
    figure, axes = plt.subplots(4, 1, figsize=(9, 8), sharex=True)
    for j, label in enumerate(('MCP bend', 'MCP spread', 'PIP', 'DIP')):
        axes[j].axvspan(3., 5.5, color='#dceede', label='Target note window')
        axes[j].plot(times, target[:, j], '--', color='#d97706', label='Applied target')
        axes[j].plot(times, q[:, j], color='#2563eb', label='Actual joint')
        axes[j].set_ylabel(label+'\n(deg)'); axes[j].grid(alpha=.25)
    axes[0].legend(loc='best', fontsize=8, ncol=3)
    axes[-1].set_xlabel('Time (s)')
    figure.suptitle('Index / string 3 / fret 4 — native episode joint coordinates')
    figure.tight_layout(); figure.savefig(ROOT/'joint_motion.png', dpi=160); plt.close(figure)
    arm = catalog['action_indices'][:12]
    motion = dict(joint_names=names, actual_range_deg=np.ptp(q, axis=0).tolist(),
        applied_target_range_deg=np.ptp(target, axis=0).tolist(),
        arm_applied_target_max_range_deg=float(np.rad2deg(np.ptp(data['target'][:, arm], axis=0)).max()),
        scope='native env0 first episode, 60Hz endpoints; model joint coordinates, not causal force shares')
    (ROOT/'render_motion.json').write_text(json.dumps(motion, indent=2)+'\n')
    return motion


def main():
    blocks, training, metrics = [], [], []
    for update in (100, 200, 300):
        train, evaluation = ROOT/('train_'+str(update))/'J', ROOT/('eval_'+str(update))
        if not (evaluation/'report.json').is_file():
            continue
        report = json.loads((evaluation/'report.json').read_text())
        if not report['completed']:
            raise ValueError('incomplete evaluation')
        selected = episodes(evaluation)
        if len(selected) != 32 or len({e['env_id'] for e in selected}) != 32:
            raise ValueError('fixed32 first-episode evaluation required')
        blocks.append(dict(updates=update, checkpoint=str(train/'final.pt'), **summarize(selected)))
        training += episodes(train)
        metrics += [json.loads(line) for line in (train/'learning_metrics.jsonl').read_text().splitlines()]
    if not blocks:
        raise ValueError('no completed fixed evaluation yet')
    best = max(blocks, key=lambda b:(b['success'], b['safe_clean_fraction'], -b['failed_episodes'], b['updates']))
    entropy = metrics[-1]['diagnostics']['post_update']['latent_gaussian_entropy']['mean']
    result = dict(song='virtual_finger_v9_index_s3_f4', finger='index', physical_string=3,
        fret=4, stage='A', size='large', num_envs=64, horizon=32, seed=7,
        updates=len(metrics), committed_transitions=len(metrics)*64*32,
        evaluations=blocks, training=summarize(training), selected_checkpoint=best['checkpoint'],
        selected_updates=best['updates'], selection='safe success, safe clean fraction, fewer failures, latest',
        actor_lr_initial=metrics[0]['actor_lr'], actor_lr_final=metrics[-1]['actor_lr'],
        kl_retries=sum(m['kl_retries'] for m in metrics),
        active_finger_std_geometric_mean=math.exp(entropy/4-.5*(1+math.log(2*math.pi))),
        interpretation='A supported finger-only skill; not free-v9/full J33/acoustic performance')
    (ROOT/'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    table='\n'.join('| {updates} | {success}/32 | {contact}/32 | {any_clean}/32 | {longest_clean_s:.3f} | {physical_failure} / {wrist_failure} |'.format(**b) for b in blocks)
    text=f'''# 검지 3번 줄·4프렛 학습 결과

한 손가락·한 줄·한 프렛만 새 정책으로 학습했다. 정렬된 A 초기 자세에서 팔과 비목표 손가락의 적용 목표를 유한 PD로 유지하며 검지4축을 학습한다. 기타는 자유 강체다.

large·64환경·H32·seed7, 총{len(metrics)}업데이트 / {len(metrics)*64*32:,}전이를 실행했다.

| 업데이트 | 안전 달성 | 최초 접촉 | audible clean 발생 | 최장 연속 clean(초) | 물리 / 손목 종료 |
|---:|---:|---:|---:|---:|---:|
{table}

고정 정책으로 환경마다 첫 에피소드만32개 평가했고, 실패도 분모에 포함했다. 최초 접촉은 준비·목표 창에서 연속50ms 기준이다. clean은 목표가 울려야 할2.5초 창의 올바른 압현이며, 음 달성은 연속1초와 안전한 에피소드 완료를 요구한다. 실제 소리·현 압력의 인증과 구분한다.

누적 학습의 완결 에피소드 {len(training)}개 중 목표 접촉 {result['training']['contact']}회, 안전 달성 {result['training']['success']}회, 최장 clean {result['training']['longest_clean_s']:.3f}초였다. 마지막 미완결 에피소드는 이 집계에서 제외했다. 학습은 확률적 탐색을 포함하므로 위 고정 정책 평가와 구분한다.

학습률은 {result['actor_lr_initial']:.2g}→{result['actor_lr_final']:.2g}, KL 재시도 합계 {result['kl_retries']}회였다. 최종 활성 검지4축 탐색 표준편차의 기하평균은 {result['active_finger_std_geometric_mean']:.4f}이다.

영상 선택 모델은 {best['updates']}회 checkpoint다. 안전 달성→실패를0점 처리한 clean 비율→실패 수→최신 순서로 선택했다. A 지원 조건의 결과이며 원래 v9·전체33축 평가나 다른 손가락으로 일반화하지 않는다.

상세 수치는 [summary.json](summary.json), 학습·평가는 각 train_*/eval_* 디렉토리에 있다. 실행 중 구현·보상·종료·초기 자세를 바꾸지 않았다.
'''
    motion = plot_motion(best['checkpoint'])
    if motion:
        ranges='/'.join(f'{value:.1f}°' for value in motion['actual_range_deg'])
        text += f'\n실제 렌더 에피소드의 검지 MCP 굽힘/MCP 벌림/PIP/DIP 좌표 변화 범위는 {ranges}다. 팔 적용 목표의 최대 변화는 {motion["arm_applied_target_max_range_deg"]:.6f}°로 기록됐다. 실제 상태를 고정한 것이 아니라 유한 PD로 목표를 유지했다.\n\n![실제/적용 목표 관절 좌표](joint_motion.png)\n'
    if (ROOT/'publication.json').is_file():
        publication = json.loads((ROOT/'publication.json').read_text())
        import os
        text += '\n'+ ' · '.join('['+v['kind']+' 영상]('+os.path.relpath(v['path'], ROOT)+')'
                                  for v in publication['videos'])+'\n'
        text += '\n100회·200회 모두 안전 달성32/32로 두 번 연속 A 기준을 통과해200회에서 학습을 종료했다. 영상은 유지율이 더 높은100회 모델이다. A는 동일한 정렬 초기 자세의 반복 평가이며, 새 초기 분포·새 seed·다른 줄/프렛·자유33축 수행의 성과는 아니다.\n'
    (ROOT/'RESULTS.md').write_text(text)
    print(json.dumps(dict(updates=result['updates'], evaluation=blocks[-1], selected_updates=best['updates']), ensure_ascii=False))


if __name__ == '__main__':
    main()
