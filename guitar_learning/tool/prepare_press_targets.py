"""C1~C6 압현 목표를 공식 번들로 만들고 명시적인 왼손 원본 시계를 적용한다.

공식 canonical/manifest 검증을 먼저 통과한 뒤 압현 onset만 원본 notes 시각으로
복원한다. 타현 계획은 출처 검증용이며 이 번들은 실제 타현 실험용이 아니다.
기존 v5·공용 구현과 원본18파일은 수정하지 않는다.
"""
import argparse
from contextlib import contextmanager, redirect_stdout
import copy
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import shutil
import threading
import wave

from guitar_learning.song import task as task_module
from guitar_learning.tool.song_bundles import SONG_BUNDLES_ROOT

SCHEMA = 'guitar_learning.press_sequence_source_clock.v1'
CASES = {name: 'press_sequence_'+name.lower()+'_v1' for name in ('C1', 'C2', 'C3', 'C4', 'C5', 'C6')}
BUNDLES = SONG_BUNDLES_ROOT
ORIGINALS = Path(__file__).resolve().parents[2]/'docs/2026-11-09/압현_연속목표_손가락조합_v1/입력'
BASE_TASK_FACTORY = task_module.make_task
_RUNTIME_LOCK = threading.Lock()


def _case_id(case_id):
    if case_id in CASES:
        return case_id
    for name, bundle_id in CASES.items():
        if case_id == bundle_id:
            return name
    raise ValueError('등록된 C1~C6 압현 목표만 허용한다: '+str(case_id))


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def catalog():
    """미등록 목표도 포함한 고정6개 목록. ready는 존재 여부이며 검증 성공은 아니다."""
    return [dict(case_id=name, bundle_id=identifier, bundle=str((BUNDLES/identifier).resolve()),
        ready=(BUNDLES/identifier/'manifest.json').is_file(), source_note_count=20,
        source_duration_s=43.75) for name, identifier in CASES.items()]


def _checked_json(root, relative, manifest):
    path = root/relative
    expected = manifest.get('files', {}).get(relative)
    if not isinstance(expected, dict) or not path.is_file():
        raise ValueError('압현 번들 파일·manifest 항목 누락: '+relative)
    if expected.get('sha256') != _sha(path) or expected.get('bytes') != path.stat().st_size:
        raise ValueError('압현 번들 입력 SHA/bytes 불일치: '+relative)
    return json.loads(path.read_text(encoding='utf-8'))


def _clock_inputs(root):
    """런타임에서 docs 원본에 접근하지 않고 번들 내부의 보존 사본을 검증한다."""
    root = Path(root).resolve()
    case = _case_id(root.name)
    if root != (BUNDLES/CASES[case]).resolve():
        raise ValueError('등록된 프로젝트 압현 번들 경로가 필요하다')
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    clock = _checked_json(root, 'left_press_clock.json', manifest)
    if (clock.get('schema') != SCHEMA or clock.get('case_id') != case or
            clock.get('bundle_id') != root.name or clock.get('source_note_count') != 20 or
            clock.get('source_press_count') != 20 or clock.get('source_duration_s') != 43.75 or
            clock.get('purpose') != 'left_press_only_source_onset'):
        raise ValueError('C 압현 전용 clock 계약 불일치')
    expected_originals = {'source/original/'+case+'.'+suffix
                          for suffix in ('fingering.json', 'notes.csv', 'chords.json')}
    if (not isinstance(clock.get('original_sha256'), dict) or
            set(clock['original_sha256']) != expected_originals):
        raise ValueError('보존 원본은 등록된 fingering/CSV/chords3개여야 한다')
    for relative, original_sha in clock['original_sha256'].items():
        path = root/relative
        entry = manifest['files'].get(relative, {})
        if (not path.is_file() or _sha(path) != original_sha or entry.get('sha256') != original_sha or
                entry.get('bytes') != path.stat().st_size):
            raise ValueError('보존 원본 SHA/bytes 불일치: '+relative)
    original = json.loads((root/'source/original'/f'{case}.fingering.json').read_text(encoding='utf-8'))
    mapping = _checked_json(root, 'mapping/fingering.json', manifest)
    if (original['metadata'].get('version_id') != case or len(original['notes']) != 20 or
            len(original['presses']) != 20 or max(note['t_off'] for note in original['notes']) != 43.75):
        raise ValueError('C 원본20음·20press·길이 불일치')
    for field in ('notes', 'presses', 'hand', 'metadata', 'diagnostics'):
        if mapping.get(field) != original.get(field):
            raise ValueError('압현 파생 mapping이 원본 필드를 변경했다: '+field)
    fret = _checked_json(root, 'training/fret_training.json', manifest)
    expected = [{key: press[key] for key in ('finger','string','fret','barre','t_press','t_release','strikes')}
                for press in original['presses']]
    if fret.get('events') != expected:
        raise ValueError('공식 fret 생성기가 원본20 press를 그대로 보존하지 못했다')
    sections = original['metadata']['sections']
    if ([section['case_id'] for section in sections] != ['P'+str(i) for i in range(1, 10)] or
            sorted(index for section in sections for index in section['note_indices']) != list(range(20))):
        raise ValueError('P1~P9 구간의20음 분할이 완전하지 않다')
    p7 = [original['notes'][i] for i in sections[6]['note_indices']]
    p9 = [original['notes'][i] for i in sections[8]['note_indices']]
    if (len(p7) != 3 or p7[0]['finger'] == p7[1]['finger'] or
            p7[1]['finger'] != p7[2]['finger'] or p7[0]['t_on'] != p7[1]['t_on'] or
            p7[0]['t_off'] != p7[2]['t_off'] or p7[1]['t_off'] >= p7[2]['t_on'] or
            (p7[1]['string'],p7[1]['fret']) == (p7[2]['string'],p7[2]['fret'])):
        raise ValueError('P7 유지 손가락·전환 손가락 구조 불일치')
    if (len(p9) != 2 or any(p9[0][key] != p9[1][key] for key in ('finger','string','fret')) or
            p9[0]['t_off'] >= original['presses'][sections[8]['press_indices'][1]]['t_press']):
        raise ValueError('P9 해제 후 같은 목표 재압현 구조 불일치')
    return manifest, clock, original


def source_clock_task(bundle, pre_roll_s=3., tail_s=.5):
    """검증된 canonical Task의 ID·배정을 유지하고 왼손 onset만 원본 시계로 복원한다."""
    root = Path(bundle).resolve()
    _case_id(root.name)
    # 먼저 원래 함수의 canonical/manifest/audio/coverage 검증을 모두 실행한다.
    base = BASE_TASK_FACTORY(root, pre_roll_s=pre_roll_s, tail_s=tail_s)
    manifest, clock, original = _clock_inputs(root)
    schedule = base.provenance['song']['schedule']
    if len(base.targets) != 20 or len(schedule) != 20:
        raise ValueError('C 목표의 canonical20음 대응 불일치')
    indices = [row['mapping_note_index'] for row in schedule]
    if sorted(indices) != list(range(20)):
        raise ValueError('C 목표 원음 coverage 중복 또는 누락')
    metadata = copy.deepcopy(base.provenance)
    targets, changes = [], []
    for old, row in zip(base.targets, metadata['song']['schedule']):
        number = row['mapping_note_index']
        note = original['notes'][number]
        presses = [press for press in original['presses'] if
            (press['string'],press['fret'],press['finger']) == (note['string'],note['fret'],note['finger'])
            and any(abs(time-note['t_on']) <= 1e-9 for time in press['strikes'])]
        if len(presses) != 1:
            raise ValueError('원음의 press 연결이 유일하지 않다')
        press = presses[0]
        if (old.target_id != row['target_id'] or old.event_id != row['event_id'] or
                (old.string,old.fret,old.finger) != (5-note['string'],note['fret'],note['finger']) or
                abs(old.press_s-(press['t_press']+pre_roll_s)) > 1e-9 or
                abs(old.end_s-(min(note['t_off'],press['t_release'])+pre_roll_s)) > 1e-9):
            raise ValueError('canonical ID·배정·press/end 보존 검증 실패')
        onset = float(note['t_on'])
        new = replace(old, onset_s=onset+pre_roll_s, source_onset_s=onset)
        targets.append(new)
        changes.append(dict(mapping_note_index=number, target_id=old.target_id,
            canonical_source_onset_s=old.source_onset_s, source_onset_s=onset,
            correction_s=onset-old.source_onset_s))
        row.update(canonical_source_onset_s=row['source_onset_s'],
            canonical_onset_s=row['onset_s'], source_onset_s=onset, onset_s=onset+pre_roll_s)
    adapter = Path(__file__).resolve()
    metadata['provenance'].append(dict(path=str(adapter), sha256=_sha(adapter), bytes=adapter.stat().st_size))
    metadata['provenance'].append(dict(path=str(root/'left_press_clock.json'),
        sha256=manifest['files']['left_press_clock.json']['sha256'], bytes=(root/'left_press_clock.json').stat().st_size))
    metadata.update(timing_mode='left_press_source_clock',
        temporal_composition='validated canonical note identity, original left note onsets; no inferred strum microtiming for press learning')
    metadata['left_press_clock'] = copy.deepcopy(clock)
    metadata['left_press_clock'].update(canonical_validation='original make_task completed before adaptation',
        clock_contract_sha256=manifest['files']['left_press_clock.json']['sha256'], changes=changes,
        onset_mapping_sha256=hashlib.sha256(json.dumps(changes, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
        adapter_source_sha256=_sha(adapter),
        scope='left pressure only; canonical strike plan is provenance, not actual right-hand timing evidence')
    metadata['song']['derivation'] = 'source note onset+policy pre-roll; canonical string/fret/finger/press/end/ID and audio horizon preserved'
    result = replace(base, targets=tuple(targets), provenance=metadata)
    from guitar_learning.gpu.press_coordination import validate_assignments
    validate_assignments(result.targets)
    return result


@contextmanager
def source_clock_runtime():
    """현재 프로세스의 C 전용 실행 동안 두 task factory를 설치하고 반드시 복원한다.

    공용 원문은 수정하지 않는다. 다른 종류 환경의 동시 구성과 중첩 context는
    허용하지 않으며 타현·일반 곡을 이 context에서 실행하지 않는다.
    """
    if not _RUNTIME_LOCK.acquire(blocking=False):
        raise RuntimeError('압현 원본 clock context는 중첩·동시 실행할 수 없다')
    try:
        from guitar_learning.gpu import environment
        original = (task_module.make_task, environment.make_task)
        if any(factory is not BASE_TASK_FACTORY for factory in original):
            raise RuntimeError('기존 task factory가 이미 다른 실행으로 변경되어 있다')
        task_module.make_task = environment.make_task = source_clock_task
        try:
            yield
        finally:
            task_module.make_task, environment.make_task = original
    finally:
        _RUNTIME_LOCK.release()


def check_target(case_id):
    """공식 검증과 왼손 시계·손목 track 검증을 실행하고 JSON 결과를 반환한다."""
    case = _case_id(case_id)
    root = BUNDLES/CASES[case]
    task = source_clock_task(root)
    from guitar_learning.gpu.contact import load_press_surface, load_wrist_region_track
    surface = load_press_surface([target.string for target in task.targets], [target.fret for target in task.targets])
    region = load_wrist_region_track(root, surface)
    with wave.open(str(root/'source/audio.wav'), 'rb') as audio:
        if (audio.getnchannels(),audio.getsampwidth(),audio.getframerate(),audio.getnframes()) != (1,2,16000,700000):
            raise ValueError('합성 무음 WAV 형식·43.75초 길이 불일치')
        if any(audio.readframes(audio.getnframes())):
            raise ValueError('합성 clock 오디오는 디지털 무음이어야 한다')
    if len(region['times_s']) != 2626:
        raise ValueError('손목 anchor2626프레임 불일치')
    changes = task.provenance['left_press_clock']['changes']
    return dict(case_id=case, bundle_id=root.name, bundle=str(root.resolve()), completed=True,
        source_note_count=20, target_count=len(task.targets),
        canonical_event_count=task.provenance['song']['source_event_count'],
        source_duration_s=43.75, policy_duration_s=task.duration_s,
        control_ticks=round(task.duration_s*60), manifest_sha256=_sha(root/'manifest.json'), clock_schema=SCHEMA,
        clock_contract_sha256=task.provenance['left_press_clock']['clock_contract_sha256'],
        onset_mapping_sha256=task.provenance['left_press_clock']['onset_mapping_sha256'],
        adjusted_note_count=sum(abs(row['correction_s']) > 1e-12 for row in changes),
        max_canonical_onset_correction_s=max(abs(row['correction_s']) for row in changes),
        first_policy_onset_s=min(target.onset_s for target in task.targets),
        last_policy_end_s=max(target.end_s for target in task.targets),
        section_count=9, p7_preserved=True, p9_unmerged=True,
        scope='source-time left fretting; no right-hand performance or physical reachability claim')


def prepare_target(case_id):
    """새 번들만 생성한다. 기존 디렉토리는 내용이 같아도 덮어쓰지 않는다."""
    case = _case_id(case_id)
    root = BUNDLES/CASES[case]
    root.mkdir(parents=True, exist_ok=False)
    try:
        originals = {}
        for suffix in ('fingering.json','notes.csv','chords.json'):
            name = case+'.'+suffix
            destination = root/'source/original'/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ORIGINALS/name, destination)
            originals[destination.relative_to(root).as_posix()] = _sha(destination)
        raw = json.loads((root/'source/original'/f'{case}.fingering.json').read_text(encoding='utf-8'))
        document = copy.deepcopy(raw)
        document.update(convention='string 0 = low-E; Isaac runtime string = 5 - source string',
            stats=dict(dropped_invalid_fret=0), violations=[])
        mapping = root/'mapping/fingering.json'
        _write(mapping, document)
        audio = root/'source/audio.wav'
        with wave.open(str(audio), 'wb') as stream:
            stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(16000)
            stream.writeframes(b'\0\0'*700000)
        from guitar_learning.tool import build_fret_training_data, build_strike_training_data
        from guitar_learning.tool import build_strike_plan, register_song_bundle
        training = root/'training'
        with redirect_stdout(io.StringIO()):
            build_fret_training_data.main(['--fingering',str(mapping),'--audio',str(audio),
                '--out',str(training/'fret_training.json')])
            build_strike_training_data.main([str(mapping),'--out',str(training/'strike_training.json')])
            build_strike_plan.main([str(training/'strike_training.json'),'--out',str(training/'strike_plan.json'),
                                   '--require-original-tempo-feasible'])
        _write(root/'left_press_clock.json', dict(schema=SCHEMA, case_id=case, bundle_id=root.name,
            purpose='left_press_only_source_onset', source_note_count=20, source_press_count=20,
            source_duration_s=43.75, original_sha256=originals,
            source_string_convention='0=low-E; runtime0=high-e; exactly one5-source_string conversion',
            onset='preserve original notes[].t_on, then policy pre-roll; canonical microtiming retained as separate provenance',
            scope='synthetic left fretting only; actual strike execution and physical reachability unverified'))
        register_song_bundle.write_manifest(root.name, root, dict(generator='guitar_learning.tool.prepare_press_targets',
            clock_schema=SCHEMA, original_sha256=originals,
            scope='C1~C6 source-time left fretting; use press_sequence wrapper, not ordinary v5 song execution'))
        return check_target(case)
    except BaseException:
        shutil.rmtree(root)  # 이 호출에서 새로 만든 디렉토리만 정리한다.
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('prepare','check'):
        item = sub.add_parser(command)
        item.add_argument('case', nargs='?', choices=list(CASES))
        item.add_argument('--all', action='store_true')
    args = parser.parse_args(argv)
    if bool(args.case) == args.all:
        parser.error('C1~C6 한 개 또는 --all 중 하나를 지정해야 한다')
    cases = list(CASES) if args.all else [args.case]
    operation = prepare_target if args.command == 'prepare' else check_target
    result = [operation(case) for case in cases]
    print(json.dumps(result if args.all else result[0], ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    main()
