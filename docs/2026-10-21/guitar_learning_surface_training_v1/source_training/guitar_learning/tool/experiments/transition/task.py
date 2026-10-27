"""Explicit first-pair curricula derived from the immutable whole-score bundle."""
import copy
from dataclasses import replace
import math

from guitar_learning.song.task import SongTask, make_task as full_task

SCHEMA = 'guitar_learning.transition.v1'
MODES = ('single_a', 'single_b', 'overlap', 'pair')


def validate(transition):
    value = copy.deepcopy(transition)
    if (set(value) != {'schema', 'mode', 'tempo_scale', 'role'} or
            value['schema'] != SCHEMA or value['mode'] not in MODES or
            type(value['tempo_scale']) not in (int, float) or
            value['tempo_scale'] not in (.25, .5, 1.) or
            value['role'] not in ('left', 'joint')):
        raise ValueError('explicit transition schema/mode/tempo_scale/left-or-joint role required')
    return value


def catalog(bundle):
    task = full_task(bundle)
    key = lambda t: (t.string, t.fret, t.finger)
    unique = sorted(set(map(key, task.targets)))
    pairs = sorted(set((key(a), key(b)) for a, b in zip(task.targets, task.targets[1:])))
    return dict(schema=SCHEMA, source_note_count=len(task.targets),
                distinct_target_count=len(unique), distinct_pair_count=len(pairs),
                targets=[dict(string=s, fret=f, finger=i) for s, f, i in unique],
                ordered_pairs=[dict(a=list(a), b=list(b)) for a, b in pairs])


def make_task(bundle, transition):
    config = validate(transition)
    source = full_task(bundle)
    a, b = source.targets[:2]
    if ((a.string, a.fret, a.finger), (b.string, b.fret, b.finger)) != ((1, 7, 3), (1, 5, 1)):
        raise ValueError('reviewed first two target mappings required')
    mode, tempo = config['mode'], config['tempo_scale']
    if mode.startswith('single_'):
        selected = [a if mode == 'single_a' else b]
        targets = [replace(t, onset_s=2., end_s=2.5, press_s=0.) for t in selected]
    elif mode == 'overlap':
        targets = [replace(a, onset_s=2., end_s=3., press_s=0.),
                   replace(b, onset_s=3., end_s=3.5, press_s=2.5)]
    else:
        convert = lambda t: 2. + (t-a.onset_s)/tempo
        targets = [replace(t, onset_s=convert(t.onset_s), end_s=convert(t.end_s),
                           press_s=max(0., convert(t.press_s))) for t in (a, b)]
    duration = math.ceil(max(4., targets[-1].end_s+.8)*60)/60.
    plan = dict(config, clock='policy clock; initial first onset relocated to2s',
                normalization_source='original full_score67 canonical',
                normalization_duration_s=source.duration_s,
                normalization_target_count=len(source.targets),
                source_note_indices=[0 if t.target_id == a.target_id else 1 for t in targets],
                source_first_onset_s=a.source_onset_s,
                timing=('diagnostic fixed times; tempo recorded but not applied' if mode != 'pair'
                        else '2+(source_policy_time-first_source_policy_onset)/tempo_scale'),
                release_grace_s=.3,
                release_windows={t.target_id: [t.end_s+.3, t.end_s+.8] for t in targets},
                hold_fraction=.9 if mode != 'pair' else .4,
                release_absent_fraction=.9,
                overlap_fraction=.9 if mode == 'overlap' else None,
                preparation_window=([targets[1].press_s, targets[1].onset_s]
                                    if len(targets) == 2 else None),
                diagnostic_scope='native qualified contact, not pressure/audio; reset-free transition required')
    provenance = copy.deepcopy(source.provenance)
    provenance['transition'] = plan
    provenance['stage'] = mode
    provenance['timing_mode'] = plan['timing']
    provenance['event_ids'] = [t.event_id for t in targets]
    provenance['song'] = dict(source.provenance['song'],
                              source_schedule_scope='original whole-song reference only; actual targets are task.targets',
                              control_ticks=round(duration*60), policy_duration_s=duration)
    return SongTask(tuple(targets), lookahead_s=4., provenance=provenance,
                    episode_duration_s=duration)
