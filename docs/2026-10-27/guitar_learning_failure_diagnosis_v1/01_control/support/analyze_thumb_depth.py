"""Compare predeclared common time window; no active package imports."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1] / 'thumb'
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
records = {}
fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
for name, label in [('limited_rear_probe', '요청 깊이 최대 0.3mm'),
                    ('deeper_rear_probe', '요청 깊이 최대 0.9mm')]:
    path = ROOT / name / 'physics_env0000.npz'
    with np.load(path) as data:
        common = data['time_s'] <= 15 + 1e-7
        windows = {}
        for window, mask in [('common_first_15s', common), ('complete_run', np.ones(len(common), bool))]:
            windows[window] = dict(samples=int(mask.sum()),
                witness_gap_min_mm=float(data['control_witness_gap'][mask].min()*1000),
                witness_gap_last_mm=float(data['control_witness_gap'][mask][-1]*1000),
                selected_gap_last_mm=float(data['thumb_signed_gap'][mask][-1]*1000),
                geometry_quality_mean=float(data['thumb_quality'][mask].mean()),
                candidate_samples=int(data['thumb_contact_candidate'][mask].sum()),
                thumb3_force_max_N=float(np.linalg.norm(data['thumb_force_G'][mask], axis=-1).max()),
                rear_normal_load_max_N=float(data['thumb_normal_load'][mask].max()))
        records[name] = dict(trace_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), windows=windows)
        time = data['time_s'][common]
        for ax, key, scale in zip(axes, ['control_witness_gap', 'thumb_quality', 'thumb_normal_load'], [1000, 1, 1]):
            ax.plot(time, data[key][common]*scale, label=label)
axes[0].set_ylabel('고정한 제어 표본 깊이 [mm]')
axes[1].set_ylabel('기하 안내 품질')
axes[2].set_ylabel('후면 법선 하중 [N]')
axes[2].set_xlabel('실제 물리 시간 [초]')
axes[0].legend()
for ax in axes:
    ax.grid(alpha=.25)
fig.suptitle('엄지: 기하 안내 품질 1이어도 실제 부하·접촉 후보는 0\n동일한 첫 15초 비교, 서로 다른 실행의 시간축 정렬')
fig.tight_layout()
fig.savefig(ROOT / 'depth_comparison.png', dpi=150)
(ROOT / 'depth_comparison.json').write_text(json.dumps(dict(
    interpretation='Both limited-range probes have zero actual thumb3 resultant and candidate. This does not establish full-range infeasibility or cooked-mesh fault.',
    common_window_s=15, records=records), indent=2) + '\n')
