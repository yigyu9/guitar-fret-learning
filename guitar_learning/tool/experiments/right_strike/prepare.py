"""Build one explicit right-hand strike task through current CPU compilers."""
import argparse
import hashlib
import json
from pathlib import Path
import wave

ROOT = Path(__file__).resolve().parents[4]
INPUT_ROOT = ROOT/'data/diagnostic_inputs'
DEFAULT_INPUT = INPUT_ROOT/'right_strike_v1'
INPUT_SCHEMA = 'guitar_learning.right_strike_input.v1'
TARGET_SPEC = dict(schema=INPUT_SCHEMA, condition='single_down_string3_v1',
    runtime_string=2, standard_string_1based=3, mapping_string=3,
    string_convention='runtime0=high-e,5=low-E; mapping0=low-E,5=high-e',
    direction=1, direction_name='down', raw_onset_s=0., policy_onset_s=3.,
    pre_roll_s=3., tail_s=.5, audio_duration_s=1.5, episode_duration_s=5.,
    nominal_fret=6, nominal_finger=1, left_clean_required=False,
    scope='Right pick crossing only; nominal fretted mapping is a compiler input, not left-hand pressure or pitch evidence',
    audio='Digital silence provides the clock; no acoustic evidence')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _input_path(path):
    path = Path(path).resolve()
    relative = path.relative_to(INPUT_ROOT.resolve())
    if not relative.parts:
        raise ValueError('A distinct diagnostic bundle directory is required')
    return path


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def validate_inputs(bundle):
    """Verify every bundle file, canonical identity, clock and original direction."""
    from guitar_learning.song.task import make_task
    bundle = _input_path(bundle)
    manifest = json.loads((bundle/'manifest.json').read_text())
    if manifest.get('schema') != 'tab2body.song_bundle.v1' or manifest.get('song_id') != bundle.name:
        raise ValueError('Canonical bundle identity required')
    expected = manifest.get('files')
    if not isinstance(expected, dict) or not expected:
        raise ValueError('Complete nonempty input SHA inventory required')
    actual = {path.relative_to(bundle).as_posix() for path in bundle.rglob('*')
              if path.is_file() and path != bundle/'manifest.json'}
    if actual != set(expected):
        raise ValueError('Unlisted or missing input file')
    for name, record in expected.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Bundle file must stay within its root')
        path = (bundle/relative).resolve()
        path.relative_to(bundle)
        if (type(record.get('bytes')) is not int or path.stat().st_size != record['bytes'] or
                sha(path) != record.get('sha256')):
            raise ValueError('Diagnostic input SHA/size mismatch: '+name)
    if json.loads((bundle/'right_strike_input.json').read_text()) != TARGET_SPEC:
        raise ValueError('Original right-only single downstroke specification required')
    with wave.open(str(bundle/'source/audio.wav'), 'rb') as stream:
        if (stream.getnchannels(), stream.getsampwidth(), stream.getframerate(), stream.getnframes()) != (1, 2, 16000, 24000):
            raise ValueError('Expected1.5-second mono16kHz silent clock')
        if any(stream.readframes(24000)):
            raise ValueError('Clock input must contain digital silence')
    task = make_task(bundle, pre_roll_s=3., tail_s=.5)
    if len(task.targets) != 1:
        raise ValueError('Exactly one canonical target required')
    target = task.targets[0]
    if ((target.target_id, target.string, target.fret, target.finger, target.direction,
         target.onset_s, target.end_s, target.press_s) !=
            ('event-000000/string-3/note-0', 2, 6, 1, 1, 3., 4.2, 3.) or
            task.duration_s != 5. or task.provenance['song']['control_ticks'] != 300 or
            task.provenance['song']['source_event_count'] != 1 or
            task.provenance['song']['source_note_count'] != 1):
        raise ValueError('Canonical target identity, down direction or original clock changed')
    plan = json.loads((bundle/'training/strike_plan.json').read_text())
    events = plan['events']
    if (len(events) != 1 or events[0]['direction'] != 'down' or events[0]['time'] != 0. or
            events[0]['gesture'] != 'single_pick' or events[0]['strings'] != [2] or
            events[0]['traversal_strings'] != [2] or events[0]['traversal_offsets_s'] != [0.]):
        raise ValueError('Unmodified compiler must produce the original single downstroke')
    return task


def prepare(out=DEFAULT_INPUT):
    """Write fresh data only; code sealing is a separate reviewed launch step."""
    from guitar_learning.tool import build_fret_training_data, build_strike_training_data
    from guitar_learning.tool import build_strike_plan, register_song_bundle
    out = _input_path(out)
    out.mkdir(parents=True, exist_ok=False)
    mapping = dict(purpose=INPUT_SCHEMA, convention='string 0 = low-E; runtime string = 5 - mapping string',
        notes=[dict(t_on=0., t_off=1.2, string=3, fret=6, midi=61, finger=1, barre=False, grip=None)],
        presses=[dict(finger=1, string=3, fret=6, barre=False, t_press=0., t_release=1.2, strikes=[0.])],
        hand=[dict(t=0., P=6, grip=None)], stats=dict(dropped_invalid_fret=0), diagnostics=[], violations=[])
    source = out/'mapping/fingering.json'
    _write(source, mapping)
    _write(out/'right_strike_input.json', TARGET_SPEC)
    register_song_bundle.write_tablature_if_missing(out)
    audio = out/'source/audio.wav'
    audio.parent.mkdir()
    with wave.open(str(audio), 'wb') as stream:
        stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(16000)
        stream.writeframes(b'\0\0'*24000)
    training = out/'training'; training.mkdir()
    build_fret_training_data.main(['--fingering', str(source), '--audio', str(audio),
        '--out', str(training/'fret_training.json')])
    build_strike_training_data.main([str(source), '--out', str(training/'strike_training.json')])
    build_strike_plan.main([str(training/'strike_training.json'), '--out', str(training/'strike_plan.json')])
    register_song_bundle.write_manifest(out.name, out, dict(generator=__name__,
        input_schema=INPUT_SCHEMA, compiler='current unmodified fret/strike/plan CPU builders',
        scope=TARGET_SPEC['scope'], code_sealed=False))
    task = validate_inputs(out)
    return dict(schema='guitar_learning.right_strike_preparation.v1', completed=True,
        bundle=str(out), manifest_sha256=sha(out/'manifest.json'), target_ids=[t.target_id for t in task.targets],
        runtime_strings=[t.string for t in task.targets], directions=[t.direction for t in task.targets],
        onsets_s=[t.onset_s for t in task.targets], duration_s=task.duration_s, control_ticks=300,
        left_clean_required=False, code_sealed=False, physical_tests=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False))
