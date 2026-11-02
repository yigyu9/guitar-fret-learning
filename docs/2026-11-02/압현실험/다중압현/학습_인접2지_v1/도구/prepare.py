"""Prepare six two-finger song bundles through the unmodified CPU compilers."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import wave

STUDY = Path(__file__).resolve().parents[1]
ROOT = next(p for p in STUDY.parents if (p / 'guitar_learning/train.py').is_file())
sys.path.insert(0, str(ROOT))

from guitar_learning.song.task import load_anchor_track, make_task
from guitar_learning.tool import build_fret_training_data, build_strike_training_data
from guitar_learning.tool import build_strike_plan, register_song_bundle
from guitar_learning.training.launch import settings_document
from guitar_learning.training.training_log_io import active_source_paths

CASES_PATH = STUDY / '설계/cases.json'
COMMON_WINDOW_S = (3.30, 4.80)
SOURCE_ONSETS_S = (.24, .30)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inside_study(path):
    path = Path(path).resolve()
    path.relative_to(STUDY)
    return path


def write_new(path, document):
    path = inside_study(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(document, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def verify_pins(pins):
    if not pins:
        raise ValueError('nonempty SHA pins required')
    changed = [name for name, expected in pins.items()
               if not Path(name).is_file() or sha(name) != expected]
    if changed:
        raise ValueError('SHA mismatch: ' + repr(changed[:8]))


def source_pins():
    paths = active_source_paths(ROOT / 'guitar_learning')
    paths.update((Path(__file__).resolve(), CASES_PATH))
    return {str(path): sha(path) for path in sorted(paths)}


def validate_case(case):
    rows = case['targets']
    if (len(rows) != 2 or
            [row['finger_id'] for row in rows] not in ([1, 2], [2, 3], [3, 4]) or
            [row['string'] for row in rows] != [2, 1] or
            [row['fret'] for row in rows] not in ([6, 6], [6, 7])):
        raise ValueError('adjacent fingers, runtime strings 2/1 and frets 6/6 or 6/7 required')
    if any(type(row[key]) is not int for row in rows
           for key in ('finger_id', 'string', 'fret')):
        raise ValueError('integer target coordinates required')
    identity = case['case_id']
    if not isinstance(identity, str) or Path(identity).name != identity or identity in ('.', '..'):
        raise ValueError('safe single-component case_id required')


def load_cases():
    document = json.loads(CASES_PATH.read_text(encoding='utf-8'))
    cases = document['cases']
    if len(cases) != 6 or len({case['case_id'] for case in cases}) != 6:
        raise ValueError('exactly six unique cases required')
    for case in cases:
        validate_case(case)
    expected = {(first, second) for first in (1, 2, 3) for second in (6, 7)}
    actual = {(case['targets'][0]['finger_id'], case['targets'][1]['fret']) for case in cases}
    if actual != expected:
        raise ValueError('case matrix incomplete')
    return cases


def task_for_case(case, bundle):
    """Validate source identity and the complete shared 1.5-second audible window."""
    validate_case(case)
    bundle = inside_study(bundle)
    task = make_task(bundle, pre_roll_s=3., tail_s=.5)
    expected = {(r['string'], r['fret'], r['finger_id']) for r in case['targets']}
    actual = {(r.string, r.fret, r.finger) for r in task.targets}
    if len(task.targets) != 2 or actual != expected:
        raise ValueError('canonical target identity/count differs from case')
    start = max(target.onset_s for target in task.targets)
    end = min(target.end_s for target in task.targets)
    if (start > COMMON_WINDOW_S[0] or end < COMMON_WINDOW_S[1] or
            end - start < 1.5 or task.duration_s != 5.5):
        raise ValueError('canonical audible overlap must contain [3.30,4.80]')
    load_anchor_track(bundle)
    return task


def make_settings(case, bundle, updates=100, num_envs=64, horizon=32,
                  size='medium', seed=7):
    """Use current training defaults and verified external research input only."""
    task = task_for_case(case, bundle)
    settings = settings_document('left', song='virtual_finger_v9_middle_s3_f6',
        updates=updates, num_envs=num_envs, horizon=horizon, size=size, seed=seed,
        device='cuda:0', physics='gpu')
    settings['phrase_events'] = task.provenance['song']['source_event_count']
    settings['song_training'].update(song_id=Path(bundle).name,
        bundle=str(Path(bundle).resolve()), target_count=len(task.targets),
        control_ticks=task.provenance['song']['control_ticks'],
        episode_duration_s=task.duration_s)
    settings['experiment'] = dict(schema='multi_press.adjacent_pair_training.v1',
        case_id=case['case_id'], common_window_s=list(COMMON_WINDOW_S),
        task_schema=task.provenance['schema'],
        target_ids=[target.target_id for target in task.targets],
        success_inherited=False, independent_policy=True)
    return settings


def build(out):
    out = inside_study(out)
    cases = load_cases()
    pins = source_pins()
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    for case in cases:
        bundle = out / case['case_id']
        notes, presses = [], []
        for index, target in enumerate(case['targets']):
            string, fret, finger = 5-target['string'], target['fret'], target['finger_id']
            onset = SOURCE_ONSETS_S[index]
            notes.append(dict(t_on=onset, t_off=1.85, string=string, fret=fret,
                midi=(40, 45, 50, 55, 59, 64)[string]+fret,
                finger=finger, barre=False, grip=None))
            presses.append(dict(finger=finger, string=string, fret=fret, barre=False,
                t_press=0., t_release=1.85, strikes=[onset]))
        mapping = dict(purpose='multi_press.adjacent_pair_training.v1',
            convention='string 0 = low-E; runtime string = 5 - mapping string',
            notes=notes, presses=presses,
            hand=[dict(t=0., P=max(1, 7-notes[0]['finger']), grip=None)],
            stats=dict(dropped_invalid_fret=0), diagnostics=[], violations=[])
        path = bundle / 'mapping/fingering.json'
        write_new(path, mapping)
        register_song_bundle.write_tablature_if_missing(bundle)
        audio = bundle / 'source/audio.wav'
        audio.parent.mkdir()
        with wave.open(str(audio), 'wb') as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(16000)
            stream.writeframes(b'\0\0' * 32000)
        training = bundle / 'training'
        training.mkdir()
        build_fret_training_data.main(['--fingering', str(path), '--audio', str(audio),
            '--out', str(training / 'fret_training.json')])
        build_strike_training_data.main([str(path), '--out', str(training / 'strike_training.json')])
        build_strike_plan.main([str(training / 'strike_training.json'), '--out', str(training / 'strike_plan.json')])
        register_song_bundle.write_manifest(bundle.name, bundle, dict(
            generator=str(Path(__file__).resolve()), generator_sha256=sha(__file__),
            source='explicit two-finger target; no inherited single/multi press success',
            audio='2 seconds digital silence; clock only, no acoustic evidence'))
        task = task_for_case(case, bundle)
        rows.append(dict(case_id=case['case_id'], bundle=str(bundle),
            targets=[asdict(t) for t in task.targets],
            source_onsets_s=list(SOURCE_ONSETS_S), onset_separation_s=.06,
            common_window_s=list(COMMON_WINDOW_S),
            audible_intersection_s=[max(t.onset_s for t in task.targets),
                                    min(t.end_s for t in task.targets)],
            episode_duration_s=task.duration_s,
            control_ticks=task.provenance['song']['control_ticks']))
    verify_pins(pins)
    output_pins = {str(path): sha(path) for path in sorted(out.rglob('*')) if path.is_file()}
    report = dict(schema='multi_press.adjacent_pair_inputs.v1', completed=True,
        rows=rows, source_sha256=pins, output_sha256=output_pins,
        onset_scope='60ms separated canonical single events; simultaneous sustained clean is evaluated, not synchronous acoustic onset',
        physical_tests=0, learned_success=False)
    write_new(out / 'report.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=STUDY / '입력/song_bundles')
    args = parser.parse_args()
    result = build(args.out)
    print(json.dumps(dict(completed=result['completed'], cases=len(result['rows'])), ensure_ascii=False))
