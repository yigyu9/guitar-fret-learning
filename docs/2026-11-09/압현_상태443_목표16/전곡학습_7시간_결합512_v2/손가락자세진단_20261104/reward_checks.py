"""봉인된 평가의 E4 실제 대기 보상 기회와 오압현 출처를 CPU로 재집계한다."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch

OUT = Path(__file__).resolve().parent
STUDY = OUT.parent
ROOT = next(p for p in OUT.parents if (p / 'guitar_learning').is_dir())
sys.path.insert(0, str(ROOT))


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


evaluation = STUDY / '최종평가'
pins = read(evaluation / 'inputs_before.json')
# 이번 CPU 재계산에 적용하는 코드와 원곡 입력을 평가 시점의 소스 봉인과 대조한다.
applied = [ROOT / ('guitar_learning/' + name) for name in (
    'gpu/finger_reward.py', 'gpu/finger_skill_environment.py', 'gpu/environment.py',
    'gpu/episode_diagnostics.py', 'gpu/contact.py', 'gpu/control.py',
    'gpu/compact_press.py', 'song/task.py', 'score/canonical.py')]
bundle = ROOT / 'data/song_bundles/05_BN2-131-B_solo'
applied += [p for p in bundle.rglob('*') if p.is_file()]
for path in applied:
    assert pins.get(str(path)) == sha(path), '적용 소스/입력 봉인 불일치: ' + str(path)

from guitar_learning.song.task import make_task
from guitar_learning.gpu.finger_reward import finger_preparation_gate, finger_target_indices

report = read(evaluation / 'report.json')
assert report['completed'] and not report['failure'] and not report['changed_inputs']
episodes = [json.loads(line)['episode'] for line in (evaluation / 'episodes.jsonl').read_text().splitlines()]
assert len(episodes) == 16 and all(e['reason'] == 'timeline_complete' for e in episodes)
metadata = {tuple(row['path']): row['value'] for row in read(evaluation / 'episode_metadata.json')['fields']}
task = make_task(bundle)
ids = [t.target_id for t in task.targets]
assert ids == metadata[('left_note_ledger', 'target_ids')]
assert [t.string + 1 for t in task.targets] == metadata[('left_note_ledger', 'wrong_press_sources', 'target_strings_1based')]
assert all(e['left_note_ledger']['selected_target_ids'] == ids for e in episodes)
assert all(e['natural_preparation']['condition'] == 'E4' for e in episodes)
for episode in episodes:
    standby = episode['left_episode_diagnostics']['standby']
    assert all(not any(standby[k]) for k in ('contact_excluded_s', 'proximity_excluded_s',
        'nonfinite_distance_excluded_s', 'invalid_angle_s'))

onset, end, press = [torch.tensor([getattr(t, key) for t in task.targets], dtype=torch.float64)
                    for key in ('onset_s', 'end_s', 'press_s')]
finger = torch.tensor([t.finger for t in task.targets])
duration = (end - onset).numpy()


def gates(now):
    """접촉/거리 veto가 없는 현행 E4의 악보 전용 실제 지급 gate를 재현한다."""
    scope = torch.ones(len(now), len(task.targets), dtype=torch.bool)
    legacy = finger_preparation_gate(now, onset, end, press, finger,
        torch.zeros(len(now), 4, dtype=torch.bool), torch.zeros(len(now), len(task.targets)), scope)['gate']
    initial = scope & (press[None] == press.min())
    preparing = finger_target_indices(now, onset, end, press, finger,
        scope, preparation_mask=initial)['valid'][..., 0]
    return legacy.numpy(), torch.where(preparing, 0., legacy).numpy()


with gzip.open(evaluation / 'finger_control_trace.jsonl.gz', 'rt') as stream:
    trace = [row for line in stream if (row := json.loads(line))['episode_id'] == 1]
assert len(trace) == 2400 and trace[-1]['score_time_s'] == 10.
assert all(row['env_id'] == 0 for row in trace)
for row in trace:
    for target in row['targets']:
        if target['target_present']:
            assert ids[target['target_index']] == target['target_id']
legacy_trace, actual_trace = gates(torch.tensor([r['score_time_s'] for r in trace], dtype=torch.float64))
recorded_legacy = np.array([[f['observed_standby_gate'] for f in r['natural_preparation']['fingers']] for r in trace])
recorded_actual = np.array([[f['standby_weight'] for f in r['natural_preparation']['fingers']] for r in trace])
errors = [float(np.max(abs(a - b))) for a, b in
          ((legacy_trace, recorded_legacy), (actual_trace, recorded_actual))]
assert max(errors) < 1e-12
steps = episodes[0]['left_episode_diagnostics']['physics_endpoint_count']
assert all(e['left_episode_diagnostics']['physics_endpoint_count'] == steps for e in episodes)
legacy, actual = gates(torch.arange(1, steps + 1, dtype=torch.float64) / 240)
legacy_s, actual_s = legacy.sum(0) / 240, actual.sum(0) / 240
assert np.max(abs(legacy_s - np.array(episodes[0]['left_episode_diagnostics']['standby']['gate_weighted_s']))) < 1e-10
reward = np.mean([e['left_episode_diagnostics']['standby']['raw_standby_reward'] for e in episodes], 0)
rate = read(evaluation / 'settings.json')['song']['finger_recovery']['standby_rate_per_s'] / 4
standby_rows = [dict(finger=i + 1, legacy_weighted_s=float(legacy_s[i]),
    actual_weighted_s=float(actual_s[i]), actual_positive_s=float((actual[:, i] > 0).sum() / 240),
    mean_paid_reward=float(reward[i]), possible_reward=float(rate * actual_s[i]),
    opportunity_weighted_quality=float(reward[i] / (rate * actual_s[i]))) for i in range(4)]

values = [e['left_note_ledger']['values'] for e in episodes]
sources = np.array([e['left_note_ledger']['wrong_press_sources']['values']['wrong_source_time'] for e in episodes])
middle = finger.numpy() == 2
middle_duration = float(duration[middle].sum())
middle_sources = sources[:, middle].sum(1).mean(0)
middle_causes = middle_sources.sum(0)
wrong = float(np.mean([np.array(v['wrong'])[middle].sum() for v in values]))
index = finger.numpy() == 1
index_trace = [r['targets'][0]['pad_distance_m'] for r in trace if r['targets'][0]['target_present']]
result = dict(schema='compact_press_reward_checks.v1',
    scope=dict(episodes=16, episode_selection='완결 평균정책 평가16환경, 환경별 동일 가중',
        timeline_s=episodes[0]['task_time_s'], trace_env_id=0, trace_physics_samples=len(trace),
        trace_until_s=10., physical_hz=240, target_order_asserted=True,
        pins_checked='이번 재계산에 적용한 코드와 원곡 입력만; 전체 checkpoint identity 재평가는 아님'),
    evidence_sha256={str(p.relative_to(ROOT)): sha(p) for p in applied + [
        evaluation / 'inputs_before.json', evaluation / 'report.json', evaluation / 'episode_metadata.json',
        evaluation / 'episodes.jsonl', evaluation / 'finger_control_trace.jsonl.gz']},
    implementation=dict(legacy_gate='guitar_learning/gpu/finger_reward.py:245',
        e4_actual_gate='guitar_learning/gpu/finger_skill_environment.py:337',
        legacy_diagnostics='guitar_learning/gpu/episode_diagnostics.py:300',
        wrong_sources='guitar_learning/gpu/contact.py:919', thumb='guitar_learning/gpu/contact.py:839'),
    gate_trace_validation=dict(legacy_max_abs_error=errors[0], actual_max_abs_error=errors[1]),
    standby=dict(fingers=standby_rows, rate_per_finger_per_s=rate,
        ratio='평균 실제 지급 보상 / (손가락당 최대초당보상 × E4 실제 gate 가중시간)',
        warning='기존 eligible/gate_weighted/actual_gate_runs는 E4 지급 gate가 아닌 legacy gate 기준'),
    middle_wrong=dict(audible_duration_s=middle_duration, target_count=int(middle.sum()),
        mean_wrong_s=wrong, wrong_ratio=wrong / middle_duration,
        causes=['other_higher', 'own_wrong_fret', 'own_wrong_string'],
        mean_source_cause_s=middle_causes.tolist(), source_cause_ratios=(middle_causes / middle_duration).tolist(),
        body_names=metadata[('left_note_ledger', 'wrong_press_sources', 'body_names')],
        body_by_cause_mean_s=middle_sources.tolist(),
        warning='원인/몸체는 동시 발생 가능; 합집합 wrong과 합계가 다름. raw ledger의 준비시간 포함 원인합은 사용하지 않음'),
    index=dict(audible_duration_s=float(duration[index].sum()),
        mean_note_times_s={key: float(np.mean([np.array(v[key])[index].sum() for v in values])) for key in
            ('clean', 'contact_time', 'geometry_time', 'body_load_time', 'facing_time')},
        representative_first10s_active_target_samples=len(index_trace),
        representative_pad_distance_m=dict(mean=float(np.mean(index_trace)), min=float(min(index_trace)), max=float(max(index_trace)))),
    thumb=dict(aggregation='에피소드별 지표의 16환경 단순평균; min은 에피소드별 최소값의 평균',
        **{key: float(np.mean([e['left_episode_diagnostics']['thumb_support'][key] for e in episodes])) for key in
            ('mean_signed_gap_m', 'min_signed_gap_m', 'mean_region_excess_m', 'mean_normal_cos',
             'mean_quality', 'raw_reward', 'near_geometry_fraction', 'contact_candidate_fraction', 'normal_load_mean_N')}))
(OUT / 'reward_checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
print(json.dumps(dict(episodes=16, trace_samples=len(trace), gate_error=errors,
    actual_weighted_s=actual_s.tolist(), middle_wrong_ratio=wrong / middle_duration), ensure_ascii=False))
