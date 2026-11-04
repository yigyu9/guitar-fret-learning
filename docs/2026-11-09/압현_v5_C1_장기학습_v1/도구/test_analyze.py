"""분모·재개 중복·동시 유지·해제 반복의 작은 반례를 검사한다."""
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('c1_analysis', Path(__file__).with_name('analyze.py'))
a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)


def fixture():
    sections = json.loads(a.SOURCE.read_text())['metadata']['sections']
    schedule = [dict(target_id='n'+str(i), mapping_note_index=i, source_string=2,
        string=3, fret=5, finger=2, onset_s=i*2., end_s=i*2.+1.5) for i in range(20)]
    values = {key: [0.]*20 for key in ('left', 'contact_done', 'clean', 'best_clean_streak',
        'wrong', 'missing', 'surface_min', 'exposure_time', 'geometry_time',
        'loaded_target_time', 'facing_time', 'rejected_target_time', 'own_wrong_fret_time',
        'own_wrong_string_time', 'other_higher_time')}
    for key in ('left', 'contact_done', 'exposure_time', 'geometry_time', 'loaded_target_time'):
        values[key] = [1.]*20
    values['clean'] = values['best_clean_streak'] = [1.5]*20
    episode = dict(reason='timeline_complete', reward=1., cost=0., song=dict(left_success_count=20),
        left_note_ledger=dict(values=values, target_ids=[r['target_id'] for r in schedule], focus_mask=[True]*20),
        press_coordination=dict(notes=[dict(target_id=r['target_id'], strict_success=True) for r in schedule],
            groups=[dict(target_ids=['n11','n12'], strict_success=True),
                    dict(target_ids=['n11','n13'], strict_success=True)]),
        press_completion=dict(safe=True, timeline_complete=True, completion_success=True, full_hold_success=True,
            notes=[dict(target_id=r['target_id'], release_required=True, release_status='released') for r in schedule]))
    return episode, schedule, sections


def test_resume_duplicates_replaced_by_explicit_order(tmp_path):
    paths = [tmp_path/'original', tmp_path/'resume']
    for path, numbers in zip(paths, ([1,2,3], [3,4])):
        path.mkdir()
        (path/'learning_metrics.jsonl').write_text(''.join(json.dumps(dict(
            optimizer_updates=n, update_index=n-1, transitions=32))+'\n' for n in numbers))
    chosen = a.metric_selection(paths)
    assert len(chosen) == 4
    assert chosen[3][0] == paths[1]
    assert sum(row['transitions'] for _, row in chosen.values()) == 128


def test_selected_exposed_and_complete_episode_denominators():
    episode, schedule, sections = fixture()
    episode['left_note_ledger']['values']['exposure_time'][19] = 0
    episode['left_note_ledger']['values']['loaded_target_time'][19] = 0
    agg = a.Aggregate(schedule, sections)
    agg.add(episode)
    report = agg.report()
    assert report['episodes'] == 1
    assert report['selected_opportunities'] == 20
    assert report['exposed_opportunities'] == 19
    assert report['notes'][19]['failure_evidence'] == {'not_exposed': 1}
    assert 'surface_min_m' not in report['notes'][19]
    assert report['sections'][-1]['covered'] == 0


def test_p7_individual_holds_do_not_prove_simultaneous_transition():
    episode, schedule, sections = fixture()
    episode['press_coordination']['groups'][1]['strict_success'] = False
    notes = a.episode_notes(episode, schedule)
    p7 = a.section_results(episode, notes, sections)[6]
    assert p7['strict_hold']
    assert p7['overlap_group_count'] == 2
    assert not p7['simultaneous']
    assert not p7['completion']


def test_p9_release_required_and_never_acquired_not_release_mechanics():
    episode, schedule, sections = fixture()
    episode['press_completion']['notes'][18]['release_status'] = 'pending'
    notes = a.episode_notes(episode, schedule)
    p9 = a.section_results(episode, notes, sections)[8]
    assert p9['strict_hold'] and not p9['completion'] and not p9['release']
    episode['left_note_ledger']['values']['loaded_target_time'][18] = 0
    episode['press_completion']['notes'][18]['release_status'] = 'missed'
    notes = a.episode_notes(episode, schedule)
    assert notes[18]['failure_evidence'] == 'no_loaded_pad_candidate'
    assert not notes[18]['release_exercised']


def test_model_selection_prefers_fixed_denominator_performance_to_idle_safety():
    initial = dict(completion_rate=0., full_hold_rate=0., achieved_per_episode=0.,
        clean_fraction=0., safe_timeline_rate=1., optimizer_updates=0)
    final = dict(initial, achieved_per_episode=3., clean_fraction=.1,
        safe_timeline_rate=31/32., optimizer_updates=2000)
    assert a.ranking(final) > a.ranking(initial)
    assert a.ranking(dict(final, optimizer_updates=3000)) > a.ranking(final)
