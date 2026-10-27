"""Compare actual fixed-policy first episodes, separately from PPO collection."""
import hashlib
import json
from guitar_learning.training import json_io
import math
from pathlib import Path
import statistics

PHASE = Path(__file__).resolve().parent


def mean(values):
    return statistics.mean(values) if values else None


def group(episodes, targets):
    return dict(episodes=len(episodes),
        mean_achieved_notes=mean([e['song']['left_success_count'] for e in episodes]),
        mean_clean_seconds=mean([math.fsum(e['left_note_ledger']['values']['clean']) for e in episodes]),
        mean_cost=mean([e['cost'] for e in episodes]),
        fingers=[dict(finger=f, target_count=sum(t['finger'] == f for t in targets),
            **{key: mean([e['left_curriculum']['finger_metrics'][f-1][key] for e in episodes])
               for key in ('near_fraction', 'contact_fraction', 'success_fraction', 'clean_fraction')})
            for f in range(1, 5)])


def verify_notes(report, episodes, targets):
    notes = report['per_note']
    assert len(notes) == 67 and [n['target_id'] for n in notes] == [t['target_id'] for t in targets]
    for i, (note, target) in enumerate(zip(notes, targets)):
        assert all(note[key] == target[key] for key in ('finger', 'string', 'fret', 'onset_s', 'end_s', 'press_s'))
        for name, selected in (('all_first', episodes), ('full_safe_first',
                [e for e in episodes if e['left_curriculum']['full_safe']])):
            row = note[name]
            values = [e['left_note_ledger']['values'] for e in selected]
            assert row['episodes'] == len(values)
            assert row['left_success_count'] == sum(v['left'][i] for v in values)
            for field in ('left', 'near_done', 'contact_done'):
                expected = mean([v[field][i] for v in values])
                assert row[field+'_fraction'] == expected
            for field in ('clean', 'wrong', 'missing', 'contact_time', 'near_time'):
                expected = mean([v[field][i] for v in values])
                actual = row['mean_'+field+'_s']
                assert actual is None if expected is None else math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-10)


def main():
    combined = json.loads((PHASE/'checkpoint_evaluation.json').read_text())
    assert combined['completed'] and len(combined['results']) == 2
    reports, episodes, pins = {}, {}, {}
    targets = None
    for name, updates in (('initial', 0), ('final', 2000)):
        folder = PHASE/('evaluation_'+name+'_1024')
        for filename in ('report.json', 'targets.json', 'first_episodes.jsonl', 'inputs_before.json'):
            path = folder/filename
            pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        report = json.loads((folder/'report.json').read_text())
        assert report == combined['results'][0 if name == 'initial' else 1]
        assert report['completed'] and report['deterministic'] and report['source_optimizer_updates'] == updates
        assert report['num_envs'] == 1024 and report['gpu_scene']['closed']
        assert report['gpu_scene']['physx_use_gpu'] and report['gpu_scene']['use_gpu_pipeline']
        for path, expected in json.loads((folder/'inputs_before.json').read_text()).items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
        current_targets = json.loads((folder/'targets.json').read_text())
        assert len(current_targets) == 67
        if targets is None:
            targets = current_targets
        else:
            assert current_targets == targets
        values = [json.loads(line) for line in (folder/'first_episodes.jsonl').read_text().splitlines()]
        assert len(values) == 1024 and {e['env_id'] for e in values} == set(range(1024))
        values.sort(key=lambda e: e['env_id'])
        assert [{k: v for k, v in e.items() if k != 'left_note_ledger'} for e in values] == report['episodes']
        for e in values:
            assert e['valid'] and all(len(v) == 67 for v in e['left_note_ledger']['values'].values())
            assert sum(e['left_note_ledger']['values']['left']) == e['song']['left_success_count']
        verify_notes(report, values, targets)
        reports[name], episodes[name] = report, values
    safe_ids = {name: {e['env_id'] for e in values if e['left_curriculum']['full_safe']}
                for name, values in episodes.items()}
    matched = safe_ids['initial'] & safe_ids['final']
    summaries = {}
    for name, values in episodes.items():
        summaries[name] = dict(optimizer_updates=reports[name]['source_optimizer_updates'],
            curriculum_progress=reports[name]['curriculum_progress'],
            safe_timeline=len(safe_ids[name]), physical_failures=1024-len(safe_ids[name]),
            full_task_successes=sum(bool(e['song']['stage_success']) for e in values),
            all_first=group(values, targets),
            full_safe_first=group([e for e in values if e['env_id'] in safe_ids[name]], targets),
            same_environment_ids_safe_in_both=group([e for e in values if e['env_id'] in matched], targets))
    note_changes = []
    for a, b in zip(reports['initial']['per_note'], reports['final']['per_note']):
        assert a['target_id'] == b['target_id']
        note_changes.append(dict(target_id=a['target_id'], finger=a['finger'],
            string_0_high_e=a['string'], fret=a['fret'],
            initial_fraction=a['all_first']['left_fraction'], final_fraction=b['all_first']['left_fraction'],
            change=b['all_first']['left_fraction']-a['all_first']['left_fraction']))
    result = dict(completed=True, training_chain=combined['results'][0]['training_chain'], checkpoints=summaries, per_note_changes=note_changes,
        matched_safe_environment_count=len(matched),
        mean_achieved_notes_delta_all_first=summaries['final']['all_first']['mean_achieved_notes']-
            summaries['initial']['all_first']['mean_achieved_notes'],
        most_improved=sorted([v for v in note_changes if v['change'] > 0], key=lambda v: v['change'], reverse=True)[:8],
        most_declined=sorted([v for v in note_changes if v['change'] < 0], key=lambda v: v['change'])[:8],
        scope='One first episode per environment,1024 per fixed checkpoint; geometric loaded-surface candidate success, not acoustic success',
        limitations='Same song and prepared pose, each checkpoint own curriculum/observations; correlated environment IDs are not independent seeds or held-out generalization. Safe-only groups can differ; same-safe IDs are descriptive, not statistical randomization.',
        inputs_sha256=pins)
    with (PHASE/'evaluation_analysis.json').open('x') as stream:
        json_io.dump(result, stream, indent=2, allow_nan=False)
    print(json_io.dumps(dict(completed=True, mean_achieved_notes_delta_all_first=result['mean_achieved_notes_delta_all_first'])))


if __name__ == '__main__':
    main()
