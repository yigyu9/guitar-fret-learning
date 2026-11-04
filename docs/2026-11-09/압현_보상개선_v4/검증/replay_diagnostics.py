"""검증된 과거 기록으로 실제 대기 지급과 이상 자세 진단을 CPU 재생한다."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning').is_dir())
sys.path.insert(0, str(ROOT))
from guitar_learning.gpu.compact_press_v4 import (
    actual_reward_posture, geometric_posture_flags, standby_posture_quality,
)
from guitar_learning.gpu.episode_diagnostics import LeftEpisodeDiagnostics
from guitar_learning.gpu.finger_reward import finger_posture_reward

torch.set_num_threads(1)
OUT = Path(__file__).resolve().parent
STUDY = ROOT/'docs/2026-11-09/압현_상태443_목표16/전곡학습_7시간_결합512_v2'
EVAL = STUDY/'최종평가'
CAPTURE = STUDY/'결과검토_20261104/영상재검증'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = read(CAPTURE/'report.json')
assert report['completed'] and not report['failure'] and not report['changed_inputs']
old_checks = read(STUDY/'손가락자세진단_20261104/reward_checks.json')
trace_path = EVAL/'finger_control_trace.jsonl.gz'
assert sha(trace_path) == old_checks['evidence_sha256'][str(trace_path.relative_to(ROOT))]
old_pins = read(EVAL/'inputs_before.json')
for relative in ('guitar_learning/gpu/finger_reward.py', 'guitar_learning/gpu/episode_diagnostics.py'):
    path = ROOT/relative
    assert sha(path) == old_pins[str(path)], relative

old = LeftEpisodeDiagnostics(1, 'cpu')
corrected = LeftEpisodeDiagnostics(1, 'cpu')
zeros = torch.zeros(1, 4, dtype=torch.float64)
flags = zeros.bool()
recorded_actual = zeros.clone()
recorded_rate = zeros.clone()
rows = 0
with gzip.open(trace_path, 'rt') as stream:
    for line in stream:
        row = json.loads(line)
        if row['episode_id'] != 1:
            continue
        assert row['env_id'] == 0
        fingers = row['natural_preparation']['fingers']
        gate = torch.tensor([[f['observed_standby_gate'] for f in fingers]], dtype=torch.float64)
        actual = torch.tensor([[f['standby_weight'] for f in fingers]], dtype=torch.float64)
        rate = torch.tensor([[f['standby_rate_per_s'] for f in fingers]], dtype=torch.float64)
        quality = torch.where(actual > 0, rate/(.005*actual).clamp_min(1e-30), 0.)
        posture = dict(gate=gate, idle_weight=gate, standby_reward_gate=actual,
            quality=quality, per_finger_rate=rate, shape_per_finger_rate=zeros,
            contact_veto=flags, near_veto=flags, nonfinite_veto=flags,
            valid=torch.ones(1, 4, 3, dtype=torch.bool),
            angles=torch.zeros(1, 4, 3, dtype=torch.float64), band_inside=flags)
        wrist = torch.zeros(1, 3)
        old.physics(posture, flags, wrist)
        corrected.physics(actual_reward_posture(posture), flags, wrist)
        recorded_actual += actual/240.
        recorded_rate += rate/240.
        rows += 1
assert rows == 2400
torch.testing.assert_close(corrected.values['gate_weighted_s'], recorded_actual, rtol=0, atol=1e-12)
torch.testing.assert_close(corrected.values['raw_standby_reward'], recorded_rate, rtol=0, atol=1e-12)
torch.testing.assert_close(old.values['raw_standby_reward'], recorded_rate, rtol=0, atol=1e-12)
assert corrected.values['gate_weighted_s'][0, 2] == 0
assert old.values['gate_weighted_s'][0, 2] > 6

metadata = read(CAPTURE/'capture_metadata.json')
poses = np.load(CAPTURE/'poses_env0000.npz')
bodies = metadata['body_names']
body = torch.from_numpy(poses['body_state']).float()
palm = body[:, bodies.index('human/LH:palm'), 3:7]
segments = torch.stack([body[:, [bodies.index('human/LH:'+finger+str(j)) for j in (1, 2, 3)], 3:7]
                       for finger in ('index', 'middle', 'ring', 'pinky')], 1)
times = torch.from_numpy(poses['time_s']).double()
empty = torch.empty(0, dtype=torch.float64)
posture = finger_posture_reward(times, empty, empty, empty,
    torch.empty(0, dtype=torch.long), palm, segments)
shape = geometric_posture_flags(posture['angles'], posture['valid'])
assert shape[:, 0, 0].float().mean() > .5
assert shape[:, 2, 1].float().mean() > .5
old_quality = standby_posture_quality(posture['angles'], posture['valid'], narrow=False)['quality']
new_quality = standby_posture_quality(posture['angles'], posture['valid'], narrow=True)['quality']
assert torch.isfinite(new_quality).all() and (new_quality <= old_quality+1e-7).all()

inputs = [trace_path, CAPTURE/'poses_env0000.npz', CAPTURE/'capture_metadata.json',
    CAPTURE/'report.json', ROOT/'guitar_learning/gpu/compact_press_v4.py',
    ROOT/'guitar_learning/gpu/finger_reward.py', ROOT/'guitar_learning/gpu/episode_diagnostics.py']
result = dict(completed=True, scope='저장된 대표 환경0의 오프라인 진단 재생; 새 학습 성능 아님',
    trace_samples=rows, trace_hz=240, trace_seconds=10,
    legacy_gate_s=old.values['gate_weighted_s'][0].tolist(),
    corrected_gate_s=corrected.values['gate_weighted_s'][0].tolist(),
    unchanged_raw_payment=recorded_rate[0].tolist(),
    pose_samples=len(times), pose_hz=60,
    shape_names=['mcp_hyperextension', 'mcp_dominance', 'dip_dominance'],
    shape_sample_fraction=shape.float().mean(0).tolist(),
    old_quality_mean=old_quality.mean(0).tolist(), new_quality_mean=new_quality.mean(0).tolist(),
    quality_scope='모든 저장 자세의 단순 품질 평균; 실제 gate나 지급액으로 해석하지 않음',
    thumb_and_tracking='기존 물리 기록 보존; 도달 가능성이나 제어 원인을 새로 검증하지 않음',
    input_sha256={str(p.relative_to(ROOT)): sha(p) for p in inputs})
(OUT/'과거기록_재생검증.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
