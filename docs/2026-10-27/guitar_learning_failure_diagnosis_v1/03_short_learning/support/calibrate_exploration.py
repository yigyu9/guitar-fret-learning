"""Pretraining codec-only calibration; actual motion requires a GPU check."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '01_control/fixed/incremental'
report_path = SOURCE / 'report.json'
report = json.loads(report_path.read_text())
cols = [report['joint_names'].index('LH:middle'+suffix) for suffix in ('1_x', '1_z', '2', '3')]
low = np.asarray(report['native_lower'])[cols]
high = np.asarray(report['native_upper'])[cols]
with np.load(SOURCE / 'trace60.npz') as data:
    reference = data['target'][0, 0, cols].astype(float)
noise = np.random.default_rng(123).normal(size=(100000, 4))
step = 4/60
position_std = .01
position_action = np.tanh(noise*position_std)
position_request = reference+position_action*np.where(position_action >= 0, high-reference, reference-low)
position_step = np.clip(position_request-reference, -step, step)
desired_rms = np.sqrt(np.mean(position_step**2))
left, right = np.exp(-5), 1.
for _ in range(60):
    middle = (left+right)/2
    change = np.clip(reference+np.tanh(noise*middle)*step, low, high)-reference
    rms = np.sqrt(np.mean(change**2))
    if rms < desired_rms:
        left = middle
    else:
        right = middle
incremental_std = (left+right)/2
incremental_step = np.clip(reference+np.tanh(noise*incremental_std)*step, low, high)-reference
result = dict(schema='codec_exploration_calibration.v1', seed=123, samples=100000,
    scope='selected middle4; codec-only first tick at prepared reference; not actual joint motion or equal long-term exploration',
    report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
    joint_names=[report['joint_names'][i] for i in cols], reference_rad=reference.tolist(),
    lower_rad=low.tolist(), upper_rad=high.tolist(),
    incremental_std=incremental_std, position_std=position_std,
    incremental_step_rms_deg=float(np.sqrt(np.mean(incremental_step**2))*180/np.pi),
    position_step_rms_deg=float(desired_rms*180/np.pi),
    incremental_per_axis_rms_deg=(np.sqrt(np.mean(incremental_step**2, axis=0))*180/np.pi).tolist(),
    position_per_axis_rms_deg=(np.sqrt(np.mean(position_step**2, axis=0))*180/np.pi).tolist(),
    interpretation='Global RMS matched, per-axis differences remain because native spans differ. Position zero returns prepared reference; incremental zero holds prior target. No outcome-informed std tuning.')
(ROOT/'03_short_learning/exploration_calibration.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
