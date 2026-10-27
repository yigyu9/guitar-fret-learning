#!/usr/bin/env python3
"""Render a Korean chart from sealed previous_analysis_v1.json only."""
from pathlib import Path
import hashlib
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

ROOT = Path('/home/ajou/yigyu/3')
RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1'
OUT = RESULTS / 'artifacts_native_v1'
ANALYSIS = RESULTS / 'previous_analysis_v1.json'
PLAN = ROOT / 'stability_adapter_2/STABILITY_UPDATE_CORRECTION_V1.md'
VIDEO_ON = ROOT / 'docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/long_on_v1/evaluations/update_000001/native/episode_0001/media/whole_body.mp4'
VIDEO_OFF = ROOT / 'docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/long_off_v1/evaluations/update_000001/native/episode_0001/media/whole_body.mp4'
FIGURE = OUT / 'previous_analysis_summary_v2.png'
OLD_PRODUCER = RESULTS / 'artifacts_v1/make_previous_analysis_v1.py'
OLD_FIGURE = RESULTS / 'artifacts_v1/previous_analysis_summary_v1.png'
OLD_PROVENANCE = RESULTS / 'artifacts_v1/analysis_provenance_v1.json'


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = [ANALYSIS, PLAN, VIDEO_ON, VIDEO_OFF, OLD_PRODUCER, OLD_FIGURE, OLD_PROVENANCE]
    input_records_before = [{'path': str(p), 'sha256': sha256(p), 'bytes': p.stat().st_size} for p in inputs]
    data = json.loads(ANALYSIS.read_text())
    on, off = data['results']['on'], data['results']['off']
    old_groups = on['evaluations'][0]['initial_max_requested_residual_rad_by_group']
    caps = {'body': 0.03, 'head': 0.10, 'arm': 0.30, 'finger': 0.20}

    font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(3, 2, figsize=(15, 12), constrained_layout=True)
    fig.suptitle('이전 학습 결과와 갱신 보정 상한', fontsize=18, fontweight='bold')
    colors = {'ON': '#276FBF', 'OFF': '#D97732'}

    # Completed episode outcomes in the prior long runs.
    ax = axes[0, 0]
    labels = ['ON', 'OFF']
    safety = [on['finite_velocity_safety_episodes'], off['finite_velocity_safety_episodes']]
    horizon = [on['full_horizon_episodes'], off['full_horizon_episodes']]
    y = np.arange(2)
    ax.barh(y, safety, color='#C94C4C', label='유한 속도 안전 종료')
    ax.barh(y, horizon, left=safety, color='#4A9B75', label='전체 horizon 완료')
    for i, (s, h) in enumerate(zip(safety, horizon)):
        ax.text(s / 2 if s else 0.2, i, str(s), ha='center', va='center', color='white', fontweight='bold')
        if h:
            ax.text(s + h / 2, i, str(h), ha='center', va='center', color='white', fontweight='bold')
        ax.text(s + h + 0.5, i, f"완료 {on['completed_episodes'] if i == 0 else off['completed_episodes']}회", va='center')
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 42)
    ax.set_xlabel('완료 episode 수')
    ax.set_title('이전 실행 완료 episode 결과')
    ax.legend(loc='lower right', fontsize=8)
    ax.grid(axis='x', alpha=.2)
    ax.text(0, -0.34, '업데이트: ON 54 · OFF 40 | 매 업데이트 1 optimizer step 후 KL stop | 공동 음악 성공 0', transform=ax.transAxes, fontsize=9)

    # Two saved native evaluations for each condition.
    ax = axes[0, 1]
    x = np.arange(2)
    width = 0.34
    for k, (label, result) in enumerate((('ON', on), ('OFF', off))):
        vals = [e['actual_seconds'] for e in result['evaluations']]
        bars = ax.bar(x + (k - .5) * width, vals, width, color=colors[label], label=label)
        for bar, e in zip(bars, result['evaluations']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+.3,
                    '안전 종료' if not e['full_horizon'] else '완주', ha='center', fontsize=8, rotation=0)
    ax.axhline(16.3667, color='#666', linestyle='--', linewidth=1, label='score horizon 16.37초')
    ax.set_xticks(x, ['초기 정책', 'update 1'])
    ax.set_ylabel('실제 episode 경과 시간 (초)')
    ax.set_title('초기·1회 평가: 실제 경과 시간')
    # Put the upper-right legend fully outside the plotting axes and in reserved figure margin.
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), borderaxespad=0, fontsize=8)
    ax.grid(axis='y', alpha=.2)

    # Position outside fractions.
    ax = axes[1, 0]
    for k, (label, result) in enumerate((('ON', on), ('OFF', off))):
        vals = [e['position_outside_fraction'] * 100 for e in result['evaluations']]
        bars = ax.bar(x + (k - .5) * width, vals, width, color=colors[label], label=label)
        for bar, value in zip(bars, vals):
            ax.text(bar.get_x()+bar.get_width()/2, value+1.1, f'{value:.1f}%', ha='center', fontsize=8)
    ax.set_xticks(x, ['초기 정책', 'update 1'])
    ax.set_ylim(0, 110)
    ax.set_ylabel('위치 허용범위 밖 비율 (%)')
    ax.set_title('초기·1회 평가: 허용범위 밖 비율')
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=.2)

    # Compare old ON initial requested residual maxima with the proposed group caps.
    ax = axes[1, 1]
    groups = ['body', 'head', 'arm', 'finger']
    gx = np.arange(len(groups))
    gw = 0.36
    old_values = [old_groups[g] for g in groups]
    cap_values = [caps[g] for g in groups]
    old_bars = ax.bar(gx-gw/2, old_values, gw, color='#7D6BB3', label='이전 ON 초기 요청 최대')
    cap_bars = ax.bar(gx+gw/2, cap_values, gw, color='#4A9B75', label='새 제안 상한')
    for bars in (old_bars, cap_bars):
        for bar in bars:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+.025, f'{bar.get_height():.2f}', ha='center', fontsize=8)
    ax.set_xticks(gx, groups)
    ax.set_ylabel('요청 보정 크기 (rad)')
    ax.set_title('상체 보정 그룹별 이전 최대 요청과 새 상한')
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=.2)

    # t0 composite KL for the same initial state.
    ax = axes[2, 0]
    kl_values = [on['t0_analytic_Gaussian_KL_initial_to_update1'], off['t0_analytic_Gaussian_KL_initial_to_update1']]
    bars = ax.bar(['ON', 'OFF'], kl_values, color=[colors['ON'], colors['OFF']], width=.55)
    for bar, value in zip(bars, kl_values):
        ax.text(bar.get_x()+bar.get_width()/2, value+10, f'{value:.1f}', ha='center', fontsize=9)
    ax.set_ylabel('초기 관측의 해석적 Gaussian KL')
    ax.set_title('t0 KL: 같은 초기 상태의 actor+RMS 복합 변화')
    ax.grid(axis='y', alpha=.2)
    ax.text(.02, .84, 'rollout 평균 아님 · actor/RMS 기여 분리값 아님', transform=ax.transAxes, fontsize=8,
            bbox={'facecolor':'white','edgecolor':'#aaa','alpha':.9})
    axes[2, 1].axis('off')

    fig.savefig(FIGURE, dpi=170, facecolor='white')
    plt.close(fig)
    input_records_after = [{'path': str(p), 'sha256': sha256(p), 'bytes': p.stat().st_size} for p in inputs]
    if input_records_before != input_records_after:
        raise RuntimeError('이전 분석 source가 생성 중 변경됨')
    manifest = {
        'purpose': '이전 저장 결과의 오프라인 분석 그림; 새 native 실행 결과 아님',
        'producer': {'path': str(Path(__file__).resolve()), 'sha256': sha256(Path(__file__).resolve())},
        'inputs_before': input_records_before,
        'inputs_after': input_records_after,
        'inputs_unchanged_during_render': True,
        'source_analysis_sha256': sha256(ANALYSIS),
        'plot': {'path': str(FIGURE), 'sha256': sha256(FIGURE), 'bytes': FIGURE.stat().st_size},
        'approved_interpretation': {
            'on_updates_episodes': [on['updates'], on['completed_episodes']],
            'off_updates_episodes': [off['updates'], off['completed_episodes']],
            'on_all_completed_episodes_finite_velocity_safety': on['finite_velocity_safety_episodes'] == on['completed_episodes'],
            'off_completed_full_horizon_episodes': off['full_horizon_episodes'],
            'joint_music_success_events': {'on': on['joint_success_events'], 'off': off['joint_success_events']},
            'every_update_one_step_then_kl_stop': {'on': on['every_update_one_step_then_KL_stop'], 'off': off['every_update_one_step_then_KL_stop']},
            't0_kl_is_same_initial_state_actor_plus_rms_composite_not_rollout_average': True,
            'new_caps_rad': caps,
            'on_initial_max_arm_request_rad': old_groups['arm'],
        },
        'candidate_settings': {'learning_rate': 3e-5, 'fixed_rms': True, 'zero_mean_actor': True,
                               'new_critic_and_adam': True, 'guarded_kl': True,
                               'strap': '원래 길이, ON', 'guitar': '자유 기타',
                               'baselines': '두 baseline 유지'},
        'success_assessment': '보정 개선은 아직 판정하지 않음; native 결과 대기',
    }
    (OUT / 'analysis_provenance_v2.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'plot': str(FIGURE), 'sha256': sha256(FIGURE), 'producer_sha256': sha256(Path(__file__).resolve())}, ensure_ascii=False))

if __name__ == '__main__':
    main()
