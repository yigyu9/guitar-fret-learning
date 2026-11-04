"""v5 작동 검증 산출물의 원본 보존·체크포인트·재개·평가를 다시 확인한다."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

import torch

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from guitar_learning.tool.experiments.compact_press_v5 import read_checkpoint
from guitar_learning.training.training_log_io import iter_episode_rows


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def episodes(folder):
    return [row['episode'] for row in iter_episode_rows(folder)]


def episode_summary(rows):
    for row in rows:
        assert row['press_completion']['schema'] == 'guitar_learning.press_completion.v5'
    return dict(count=len(rows), failures=dict(Counter(reason for row in rows for reason in row['failure_reasons'])),
        full_hold_success=sum(row['press_completion']['full_hold_success'] for row in rows),
        release_success=sum(row['press_completion']['release_success'] for row in rows),
        completion_success=sum(row['press_completion']['completion_success'] for row in rows),
        timeline_complete=sum(row['press_completion']['timeline_complete'] for row in rows),
        durations_s=[row['task_time_s'] for row in rows],
        achieved_notes=[row['song']['left_success_count'] for row in rows],
        target_counts=[row['song']['target_count'] for row in rows])


summary = dict(scope='functional smoke and regression, not comparative learning performance')
for filename in ('기존소스_SHA.json', 'v5_소스_SHA.json'):
    pins = read(OUT/filename)
    changed = [name for name, value in pins.items() if digest(ROOT/name) != value]
    assert not changed, changed
    summary[filename] = dict(count=len(pins), unchanged=True)

summary['cpu'] = {}
for name in ('기존_CPU_회귀검사.log', 'v5_CPU_회귀검사.log'):
    content = (OUT/name).read_text()
    count, duration = re.search(r'Ran (\d+) tests in ([\d.]+)s', content).groups()
    assert content.rstrip().endswith('OK')
    summary['cpu'][name] = dict(count=int(count), wall_s=float(duration), passed=True)

payloads = {}
summary['training'] = {}
for name in ('corrected_H32', 'corrected_H32_resume', 'combined_H128'):
    folder = OUT/'검증'/name/'J'
    report = read(folder/'report.json')
    assert report['completed'] and report['failure'] is None and report['lifecycle_verified']
    for key in ('changed_inputs', 'missing_import_pins', 'cleanup_errors'):
        assert not report[key], (name, key, report[key])
    checkpoints = {}
    for line in (folder/'checkpoint_manifest.jsonl').read_text().splitlines():
        item = json.loads(line)
        path = folder/item['path']
        assert digest(path) == item['sha256']
        read_checkpoint(path)  # 입력·설정·전체 신경망 계약도 정식 reader로 검증한다.
        payload = torch.load(path, map_location='cpu', weights_only=False)
        assert all(torch.isfinite(value).all() for value in payload['model'].values())
        payloads[(name, item['kind'])] = payload
        std = payload['model']['log_std'].exp()
        checkpoints[item['kind']] = dict(sha256=item['sha256'], updates=payload['updates'],
            support_std=std[:17].tolist(), finger_std=std[17:].tolist())
    contract = read(folder/'training_contract.json')
    assert contract['observation']['dimension'] == 464
    fields = contract['observation']['fields']
    budget_scale = contract['observation']['scales'][fields.index('episode.remaining_negative_note_budget')]
    summary['training'][name] = dict(
        **{key: report[key] for key in ('optimizer_updates', 'updates_in_run', 'transitions', 'wall_s')},
        input_and_lifecycle_checks_passed=True, budget_scale=budget_scale,
        episodes=episode_summary(episodes(folder)), checkpoints=checkpoints)

for name in ('corrected_H32', 'combined_H128'):
    std = payloads[(name, 'initial')]['model']['log_std'].exp()
    torch.testing.assert_close(std[:17], torch.full((17,), .15))
    torch.testing.assert_close(std[17:], torch.full((16,), .35))
final = payloads[('corrected_H32', 'final')]
resumed = payloads[('corrected_H32_resume', 'initial')]
assert final['updates'] == resumed['updates'] == 4
for key, value in final['model'].items():
    torch.testing.assert_close(value, resumed['model'][key], rtol=0, atol=0)
summary['resume_model_exactly_preserved'] = True

summary['evaluation'] = {}
for name in ('corrected_전곡평가', 'combined_구간평가'):
    folder = OUT/'검증'/name
    report = read(folder/'report.json')
    assert report['completed'] and report['failure'] is None
    for key in ('changed_inputs', 'missing_import_pins', 'cleanup_errors'):
        assert not report[key], (name, key, report[key])
    summary['evaluation'][name] = dict(wall_s=report['wall_s'], scope=report['scope'],
        input_checks_passed=True, episodes=episode_summary(episodes(folder)))

summary['completed'] = True
(OUT/'검증요약.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(summary, ensure_ascii=False, indent=2))
