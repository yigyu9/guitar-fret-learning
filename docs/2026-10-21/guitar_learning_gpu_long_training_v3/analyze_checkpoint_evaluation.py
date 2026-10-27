"""CPU-only reconciliation of completed initial/final first-song evaluations.

Run only after checkpoint_evaluation.json and both closed-scene reports exist.
No simulator, Torch, checkpoint execution, or training-history reconstruction.
"""
import ast
import hashlib
import json
import math
from pathlib import Path


N, M = 1024, 67
BOOL_FIELDS = ('left', 'left_missed', 'ever', 'released', 'reach_done', 'contact_done')
TIME_FIELDS = ('clean', 'wrong', 'missing', 'held', 'dwell', 'release_s', 'reached', 'contact_time')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    if isinstance(value, dict):
        for item in value.values():
            finite(item)
    elif isinstance(value, list):
        for item in value:
            finite(item)
    elif isinstance(value, (int, float)):
        require(math.isfinite(value), 'Nonfinite numeric input')


def read(path):
    value = json.loads(path.read_text())
    finite(value)
    return value


def near(a, b):
    require((a is None and b is None) or
            (a is not None and b is not None and math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)),
            'Numeric reconciliation failed: %r != %r' % (a, b))


def mean(values):
    return sum(values) / len(values) if values else None


def summarize(episodes):
    return dict(episodes=len(episodes),
        mean_wrist_reach_fraction=mean([e['left_curriculum']['reach_fraction'] for e in episodes]),
        mean_contact_candidate_fraction=mean([e['left_curriculum']['contact_fraction'] for e in episodes]),
        mean_achieved_notes_of_67=mean([e['song']['left_success_count'] for e in episodes]),
        full_song_task_successes=sum(e['song']['stage_success'] for e in episodes),
        mean_duration_s=mean([e['task_time_s'] for e in episodes]),
        mean_reward=mean([e['reward'] for e in episodes]), mean_cost=mean([e['cost'] for e in episodes]),
        mean_original_cost=mean([e['cost_components']['original_physics_and_terminal'] for e in episodes]),
        mean_remaining_song_failure_cost=mean([e['cost_components']['remaining_song_failure'] for e in episodes]))


def reconcile(report, raw):
    episodes, ledgers, targets = report['episodes'], raw['episodes'], raw['targets']
    require(len(episodes) == len(ledgers) == N, 'Must contain1024 first episodes')
    require({e['env_id'] for e in episodes} == {e['env_id'] for e in ledgers} == set(range(N)),
            'First-episode env IDs must be unique and complete')
    require(len(targets) == len(report['per_note']) == M, 'Must contain67 notes')
    require(len({t['target_id'] for t in targets}) == M, 'Duplicate target identity')
    require(sorted(t['mapping_note_index'] for t in targets) == list(range(M)), 'Source-note coverage mismatch')
    by_env = {e['env_id']: e for e in episodes}
    for row in ledgers:
        e, ledger = by_env[row['env_id']], row['ledger']
        require(set(ledger) == set(BOOL_FIELDS + TIME_FIELDS), 'Unexpected ledger fields')
        for key, values in ledger.items():
            require(len(values) == M, 'Wrong ledger length')
            require(all(type(v) is bool for v in values) if key in BOOL_FIELDS else
                    all(type(v) in (int, float) and v >= 0 for v in values), 'Wrong ledger value type/range')
        require(row['reason'] == e['reason'] and row['full_safe'] == e['left_curriculum']['full_safe'], 'Episode identity mismatch')
        near(row['end_task_time_s'], e['task_time_s'])
        near(sum(ledger['left']), e['song']['left_success_count'])
        near(mean(ledger['reach_done']), e['left_curriculum']['reach_fraction'])
        near(mean(ledger['contact_done']), e['left_curriculum']['contact_fraction'])
        near(e['cost'], e['cost_components']['original_physics_and_terminal'] + e['cost_components']['remaining_song_failure'])
        require(e['reason'] in ('timeline_complete', 'terminal_failure'), 'Unknown end reason')
        require(e['song']['target_count'] == e['song']['denominator'] == M, 'Song denominator mismatch')
        safe = e['left_curriculum']['full_safe']
        require(safe == (e['reason'] == 'timeline_complete' and not e['song']['safety_invalidated']), 'Full-safe mismatch')
        require(e['song']['stage_success'] == (safe and sum(ledger['left']) == M), 'Task-success mismatch')
        near(e['left_curriculum']['progress'], report['curriculum_progress'])
    for j, (target, row) in enumerate(zip(targets, report['per_note'])):
        require(target['target_index'] == j and target['canonical_string_1based'] == target['string'] + 1, 'Target order/string mismatch')
        require(all(row[k] == v for k, v in target.items()), 'Report/raw target mapping mismatch')
        for group, selected in (('all_first', ledgers), ('full_safe_first', [e for e in ledgers if e['full_safe']])):
            expected = row[group]
            require(expected['episodes'] == len(selected), 'Per-note denominator mismatch')
            near(expected['left_success_count'], sum(e['ledger']['left'][j] for e in selected))
            near(expected['left_success_fraction'], mean([e['ledger']['left'][j] for e in selected]))
            for key in ('clean', 'held', 'contact_time', 'reached'):
                near(expected['mean_' + key + '_s'], mean([e['ledger'][key][j] for e in selected]))
            for key in ('reach_done', 'contact_done'):
                near(expected[key + '_fraction'], mean([e['ledger'][key][j] for e in selected]))
    return targets


def main():
    p = Path(__file__).resolve().parent
    combined = read(p / 'checkpoint_evaluation.json')
    require(combined['completed'] is True and len(combined['results']) == 2, 'Both evaluations must be complete')
    reports, targets, summaries = [], [], {}
    for index, name in enumerate(('initial', 'final')):
        out = p / ('evaluation_' + name + '_1024')
        report, raw = read(out / 'report.json'), read(out / 'first_episode_note_ledgers.json')
        require(report == combined['results'][index], 'Combined and individual reports differ')
        require(report['completed'] is True and report['deterministic'] is True and report['num_envs'] == N, 'Evaluation incomplete or wrong size')
        require(report['source_optimizer_updates'] == (0 if index == 0 else 2000), 'Wrong checkpoint update')
        require(Path(report['checkpoint']) == p / 'train1024_large_2000' / (name + '.pt'), 'Unexpected checkpoint path')
        require(raw['checkpoint'] == report['checkpoint'], 'Raw checkpoint mismatch')
        require(report['first_episode_note_ledger_path'] == 'first_episode_note_ledgers.json', 'Unexpected raw path')
        pins = read(out / 'inputs_before.json')
        require(len(pins) == report['input_pins_verified'] == 571, 'Expected571 verified input pins')
        require(not [f for f, sha in pins.items() if hashlib.sha256(Path(f).read_bytes()).hexdigest() != sha], 'Current input SHA mismatch')
        require(str(Path(report['checkpoint'])) in pins and str((p / 'evaluate_checkpoints.py').resolve()) in pins, 'Missing checkpoint/tool pin')
        scene = report['gpu_scene']
        require(scene == read(out / 'gpu_scene_final.json'), 'Native final audit differs')
        require(scene['closed'] is True and scene['physx_use_gpu'] is True and scene['use_gpu_pipeline'] is True, 'Native GPU scene not closed')
        require(scene['num_envs'] == scene['environment_count'] == N and scene['simulator_count'] == 1, 'Native scene scale mismatch')
        require(scene['physics_steps'] == report['ticks'] * 4, 'Physics/control step mismatch')
        require(read(out / 'lifecycle.json')['stage'] == 'report_written', 'Lifecycle did not finish')
        targets.append(reconcile(report, raw))
        settings = read(out / 'settings.json')
        require(settings['num_envs'] == N and settings['size'] == 'large' and settings['specialist']['role'] == 'left', 'Wrong evaluation scope')
        notes = read(Path(settings['song_training']['bundle']) / 'mapping/fingering.json')['notes']
        require(len(notes) == M, 'Source mapping size mismatch')
        for target in targets[-1]:
            note = notes[target['mapping_note_index']]
            require(target['source_string'] == note['string'] and target['string'] == 5-note['string'] and
                    target['fret'] == note['fret'] and target['finger'] == (note['finger'] or 0), 'Source fingering mismatch')
            near(target['source_note_on_s'], note['t_on'])
            near(target['source_note_off_s'], note['t_off'])
            near(target['required_clean_s'], min(target['end_s']-target['onset_s'], max(.05, (target['end_s']-target['onset_s'])*settings['song']['left_fraction'])))
        episodes = report['episodes']
        safe = [e for e in episodes if e['left_curriculum']['full_safe']]
        failed = [e for e in episodes if e['reason'] == 'terminal_failure']
        summaries[name] = dict(curriculum_progress=report['curriculum_progress'],
            all_first=summarize(episodes), full_safe_first=summarize(safe), physical_failure_first=summarize(failed),
            timeline_complete_count=sum(e['reason'] == 'timeline_complete' for e in episodes),
            physical_failure_count=len(failed), failure_reasons={reason:sum(reason in e['failure_reasons'] for e in failed)
                for reason in sorted({reason for e in failed for reason in e['failure_reasons']})},
            zero_success_note_count={group:sum(row[group]['left_success_count'] == 0 for row in report['per_note'])
                if report['per_note'][0][group]['episodes'] else None for group in ('all_first', 'full_safe_first')})
        reports.append(report)
    require(targets[0] == targets[1], 'Initial/final actual target mappings differ')
    evaluator = ast.parse((p / 'evaluate_checkpoints.py').read_text())
    require(not [node for node in ast.walk(evaluator) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
        (node.func.attr in ('backward', 'step') and isinstance(node.func.value, ast.Name) and node.func.value.id in ('optimizer', 'trainer') or
         node.func.attr == 'update' and isinstance(node.func.value, ast.Name) and node.func.value.id == 'trainer')], 'Unexpected optimization call in evaluation source')
    comparisons = []
    for j, target in enumerate(targets[0]):
        row = dict(target)
        for group in ('all_first', 'full_safe_first'):
            a, b = (report['per_note'][j][group] for report in reports)
            row[group] = dict(initial=a, final=b, success_fraction_change=None if a['left_success_fraction'] is None or b['left_success_fraction'] is None
                else b['left_success_fraction']-a['left_success_fraction'])
        comparisons.append(row)
    rankings = {}
    for group in ('all_first', 'full_safe_first'):
        valid = [row for row in comparisons if row[group]['success_fraction_change'] is not None]
        rankings[group] = dict(top5_increases=[row for row in sorted(valid, key=lambda row: -row[group]['success_fraction_change']) if row[group]['success_fraction_change'] > 0][:5],
            top5_decreases=[row for row in sorted(valid, key=lambda row: row[group]['success_fraction_change']) if row[group]['success_fraction_change'] < 0][:5])
    limitations = ['All-first denominator1024 includes failed/unreached future notes; full-safe-first uses each checkpoint\'s own safe whole first-song cohort, whose membership can differ.',
        'Same song and prepared pose; each checkpoint restores its own curriculum and corresponding observations/weights. Reward is not a common fixed-weight metric.',
        'Not independent seeds, held-out generalization, calibrated string pressure, or acoustic success. Zero-success notes refer only to these evaluation cohorts.',
        'New evaluation ledgers do not reconstruct missing per-note TRAIN history.',
        'No-PPO evidence is limited to static evaluation-source inspection plus unchanged pinned checkpoint files; no independent runtime optimizer trace is available.']
    result = dict(completed=True, schema='guitar_learning.checkpoint_evaluation_analysis.v1', verification=dict(checkpoints=[0,2000], environments=N, targets=M,
        pins_per_checkpoint=571, native_closed=True, raw_report_aggregates_reconciled=True, checkpoint_hashes_unchanged=True),
        summaries=summaries, per_note=comparisons, rankings=rankings, limitations=limitations)
    finite(result)
    lines = ['# 초기·최종 고정 정책 첫 곡 평가', '', '검증을 통과한 실제 평가만 집계한다. 전체 첫 곡은 각1024개이며 안전 완주는 별도 분모다.', '']
    for name, summary in summaries.items():
        lines += ['| 정책/집단 | 곡 수 | 손목 도달 | 접촉 후보 | 달성 음/67 | 전곡 과제 성공 | 원비용 | 남은곡 실패비용 |', '|---|---:|---:|---:|---:|---:|---:|---:|']
        for group in ('all_first', 'full_safe_first', 'physical_failure_first'):
            s = summary[group]
            fmt = lambda value: '—' if value is None else '%.5f' % value
            lines.append('| %s/%s | %s | %s | %s | %s | %s | %s | %s |' % (name, group, s['episodes'],
                fmt(s['mean_wrist_reach_fraction']), fmt(s['mean_contact_candidate_fraction']), fmt(s['mean_achieved_notes_of_67']),
                s['full_song_task_successes'], fmt(s['mean_original_cost']), fmt(s['mean_remaining_song_failure_cost'])))
        lines += ['', '%s: curriculum=%s, 시간축 완주=%s, 물리 실패=%s, 성공 없는 음 수=%s.' % (name, summary['curriculum_progress'], summary['timeline_complete_count'], summary['physical_failure_count'], summary['zero_success_note_count']), '']
    for group, ranking in rankings.items():
        lines += ['## ' + group + ' 음별 변화', '', '| 방향 | 실제 음 ID | 현(1=high-e) | 프렛 | 초기 성공률 | 최종 성공률 | 증감 |', '|---|---|---:|---:|---:|---:|---:|']
        for direction, rows in ranking.items():
            for row in rows:
                s = row[group]
                lines.append('| %s | %s | %s | %s | %.5f | %.5f | %+.5f |' % (direction, row['target_id'], row['canonical_string_1based'], row['fret'], s['initial']['left_success_fraction'], s['final']['left_success_fraction'], s['success_fraction_change']))
        lines.append('')
    lines += ['전체67음 비교와 비용·보상·길이·종료 원인 집계는 evaluation_analysis.json에 있다.', '', '해석 범위:', ''] + ['- ' + line for line in limitations]
    (p / 'evaluation_analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    (p / 'evaluation_analysis.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(dict(completed=True, checkpoints=[0,2000], environments=N, targets=M)))


if __name__ == '__main__':
    main()
