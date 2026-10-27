"""Summarize the first finite joint-target prechecks without reclassifying them."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
fig, axes = plt.subplots(2, 2, figsize=(11, 6), sharex='col')
results = {}
for col, row in enumerate((8, 9)):
    folder = ROOT / ('smoke_inc_row%d_reference' % row)
    record = json.loads((folder/'evaluation.json').read_text())
    contract = json.loads((folder/'training_contract.json').read_text())
    view = contract['task']['short_learning']['view']
    with np.load(folder/'trace_env0_episode0.npz') as data:
        t = data['time_s']
        axes[0, col].plot(t, data['surface_distance_m']*1000, label='목표 패드 거리')
        axes[0, col].plot(t, data['surface_height_m']*1000, label='압현 평면 높이')
        axes[1, col].step(t, data['candidate'].astype(float), where='post', label='clean 후보')
        axes[1, col].step(t, data['wrong'].astype(float), where='post', label='오압현')
        axes[1, col].set_ylim(-.05, 1.05)
        for ax in axes[:, col]:
            ax.axvspan(view['local_onset_s'], view['local_end_s'], color='gold', alpha=.25)
            ax.grid(alpha=.25)
        axes[0, col].set_title('중지 목표 row%d: 유한 목표각 reference' % row)
        axes[1, col].set_xlabel('실제 물리 시간 [초]')
        results[str(row)] = dict(summary=record['summary'], view=view,
            first_episode_candidate_samples=int(data['candidate'].sum()),
            first_episode_wrong_samples=int(data['wrong'].sum()),
            last_distance_mm=float(data['surface_distance_m'][-1]*1000),
            last_height_mm=float(data['surface_height_m'][-1]*1000))
axes[0, 0].set_ylabel('거리 [mm]')
axes[1, 0].set_ylabel('판정 (0/1)')
axes[0, 0].legend()
axes[1, 0].legend()
fig.suptitle('학습 전 도달 검사: 두 목표 모두 달성 0/4\n노란 구간은 원래 음 길이, 정책 성과가 아닌 스크립트 대조')
fig.tight_layout()
fig.savefig(ROOT/'precheck_joint_targets.png', dpi=150)
(ROOT/'precheck_joint_targets.json').write_text(json.dumps(results, indent=2)+'\n')
