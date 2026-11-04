"""단일 압현 대조와 두 음 전환 비교를 위한 실제 학습 번들 6개를 만든다.

기존 builder와 score compiler를 그대로 사용한다. 표준 줄 번호와 mapping의
줄 방향은 서로 다르므로 mapping 생성에서 한 번, compiler에서 한 번 변환한다.
최종 ScoreTarget의 string은 표준 번호-1인지 다시 확인한다. 실제 물리는 실행하지 않는다.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import wave

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0, str(ROOT))
TARGETS = Path(__file__).resolve().parents[1]/'설계/targets.json'
SCHEMA = 'guitar_learning.string_fret_transition_bundles.v1'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    Path(path).write_text(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def checked_document(path, expected):
    if digest(path) != expected:
        raise ValueError('입력 SHA 불일치: '+str(path))
    return json.loads(Path(path).read_text())


def endpoint_evidence(spec):
    """원문 결과·원장·봉인 파일 및 현재 원시 입력 SHA를 재확인한다."""
    index_info, state_info = spec['evidence_index'], spec['evidence_state']
    index_path, state_path = ROOT/index_info['path'], ROOT/state_info['path']
    index = checked_document(index_path, index_info['sha256'])
    state = checked_document(state_path, state_info['sha256'])
    if not index['completed'] or not state['completed'] or state['status'] != 'complete':
        raise ValueError('완료된 원본 전수 검사 필요')
    index_rows = {row['case']:row for row in index['rows']}
    result = {}
    for case, definition in spec['endpoint_evidence'].items():
        documents = {Path(name).name:checked_document(ROOT/name, expected)
                     for name, expected in definition['files'].items()}
        report = documents['report.json']; episode = documents['episode.json']
        state_row = state['results'][case]; index_row = index_rows[case]
        report_path = ROOT/next(name for name in definition['files'] if name.endswith('/report.json'))
        if (state_row['status'] != 'done' or state_row['outcome'] != 'press_success' or
                index_row['outcome'] != 'press_success' or index_row['sha256'] != digest(report_path) or
                Path(state_row['report']).resolve() != report_path.resolve() or
                Path(index_row['report']).resolve() != report_path.resolve()):
            raise ValueError('원문 완료 상태와 결과 색인 불일치: '+case)
        required = ('completed','execution_completed','task_success','source_sha256_match_after',
                    'pool_closed','scene_closed','preparation_ready')
        if (report['case'] != case or not all(report.get(key) is True for key in required) or
                report['outcome'] != 'press_success' or report['failure'] is not None):
            raise ValueError('native 끝점 성공 증거 불충분: '+case)
        for name, expected in documents['inputs_before.json'].items():
            if digest(name) != expected:raise ValueError('원본 봉인 입력 SHA 불일치: '+name)
        song = episode['song']; ledger = episode['left_note_ledger']['values']
        if (song['denominator'] != 1 or song['left_success_count'] != 1 or
                not song['completed'] or song['safety_invalidated'] or ledger['left'] != [True]):
            raise ValueError('단일 압현 원장 성공 불일치: '+case)
        result[case] = dict(native_single_press_verified=True, learned_policy=False,
            source_files=definition['files'], current_pinned_inputs_verified=len(documents['inputs_before.json']),
            clean_s=ledger['clean'][0], best_clean_streak_s=ledger['best_clean_streak'][0],
            wrong_s=ledger['wrong'][0], missing_s=ledger['missing'][0],
            native_transition_verified=False,
            limitation='각 끝점의 별도 native 단일 압현 성공만 확인. 전환 경로·새 정책 학습 성과는 미검증')
    return result


def validate_spec(spec):
    if (spec['schema'] != 'guitar_learning.string_fret_transition_targets.v1' or
            (spec['pre_roll_s'],spec['tail_s'],spec['note_duration_s'],spec['gap_s']) != (3.,.5,1.5,1.) or
            spec['allowed_frets'] != [1,14] or len(spec['cases']) != 6):
        raise ValueError('고정된 여섯 비교 조건과 시계 계약 필요')
    if len({case['song_id'] for case in spec['cases']}) != 6:raise ValueError('중복 song_id')
    for case in spec['cases']:
        if len(case['targets']) not in (1,2):raise ValueError('단일 또는 두 음 비교만 지원')
        for i, target in enumerate(case['targets']):
            standard = target['string_standard_1based']
            if not 1 <= standard <= 6 or not 1 <= target['fret'] <= 14 or not 1 <= target['finger_id'] <= 4:
                raise ValueError('표준 줄1~6, 프렛1~14, 손가락1~4 필요')
            expected = (i*2.5,i*2.5+1.5,i*2.5+3.,i*2.5+4.5)
            if tuple(target[key] for key in ('source_onset_s','source_end_s','policy_onset_s','policy_end_s')) != expected:
                raise ValueError('원곡과 정책 시계가 고정 간격과 다름')
            if (target['string_runtime_0based'] != standard-1 or
                    target['string_mapping_low_e_0based'] != 6-standard or not 1 <= target['hand_P'] <= 14):
                raise ValueError('줄 방향 또는 hand P 규약 불일치')


def build_bundle(bundle, case):
    """mapping→fret/strike builder→manifest 순서로 현행 입력을 만든다."""
    from guitar_learning.tool import build_fret_training_data, build_strike_training_data
    from guitar_learning.tool import build_strike_plan, register_song_bundle
    bundle.mkdir(parents=True, exist_ok=False)
    (bundle/'mapping').mkdir(); (bundle/'source').mkdir(); (bundle/'training').mkdir()
    notes=[]; presses=[]; hand=[]
    for target in case['targets']:
        string=target['string_mapping_low_e_0based']; onset=target['source_onset_s']; end=target['source_end_s']
        notes.append(dict(t_on=onset,t_off=end,string=string,fret=target['fret'],
            midi=(40,45,50,55,59,64)[string]+target['fret'],finger=target['finger_id'],barre=False,grip=None))
        presses.append(dict(finger=target['finger_id'],string=string,fret=target['fret'],
            barre=False,t_press=onset,t_release=end,strikes=[onset]))
        hand.append(dict(t=onset,P=target['hand_P'],grip=None))
    mapping=dict(purpose=SCHEMA,convention='string 0 = low-E',notes=notes,presses=presses,hand=hand,
        stats=dict(dropped_invalid_fret=0),diagnostics=[],violations=[])
    fingering=bundle/'mapping/fingering.json'; write(fingering,mapping)
    register_song_bundle.write_tablature_if_missing(bundle)
    audio=bundle/'source/audio.wav'; duration=case['targets'][-1]['source_end_s']
    with wave.open(str(audio),'wb') as stream:
        stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(16000)
        stream.writeframes(b'\0\0'*round(duration*16000))
    training=bundle/'training'
    build_fret_training_data.main(['--fingering',str(fingering),'--audio',str(audio),'--out',str(training/'fret_training.json')])
    build_strike_training_data.main([str(fingering),'--out',str(training/'strike_training.json')])
    build_strike_plan.main([str(training/'strike_training.json'),'--out',str(training/'strike_plan.json')])
    register_song_bundle.write_manifest(case['song_id'],bundle,
        dict(registration_mode=SCHEMA,generator=str(Path(__file__).resolve().relative_to(ROOT)),
             generator_sha256=digest(__file__),targets_sha256=digest(TARGETS),
             audio='silence for clock only; no acoustic pressure verification'))


def check_bundle(bundle, case):
    """실제 score compiler 결과와 손목 기준 시계·범위·파일 SHA를 검사한다."""
    from guitar_learning.song.task import make_task, load_anchor_track
    task=make_task(bundle,pre_roll_s=3.,tail_s=.5)
    if len(task.targets) != len(case['targets']):raise ValueError('compiler 목표 개수 불일치')
    compiled=[]
    for actual, expected in zip(task.targets,case['targets']):
        values=(actual.string,actual.fret,actual.finger,actual.onset_s,actual.end_s,actual.press_s)
        reference=(expected['string_runtime_0based'],expected['fret'],expected['finger_id'],
                   expected['policy_onset_s'],expected['policy_end_s'],expected['policy_onset_s'])
        if values != reference:raise ValueError('compiler 줄/프렛/손가락/시각 불일치: '+str((values,reference)))
        compiled.append(dict(target_id=actual.target_id,string=actual.string,fret=actual.fret,finger=actual.finger,
            onset_s=actual.onset_s,end_s=actual.end_s,press_s=actual.press_s))
    anchor=load_anchor_track(bundle)
    if not all(1 <= value <= 14 for value in anchor['anchors']):raise ValueError('손목 P 범위 이탈')
    expected_duration=case['targets'][-1]['policy_end_s']+.5
    if task.duration_s != expected_duration:raise ValueError('정책 종료 시각 불일치')
    manifest=json.loads((bundle/'manifest.json').read_text())
    for name, row in manifest['files'].items():
        file=bundle/name
        if digest(file) != row['sha256'] or file.stat().st_size != row['bytes']:
            raise ValueError('번들 파일 SHA 불일치: '+str(file))
    return dict(targets=compiled,policy_duration_s=task.duration_s,
        hand_anchor_min=min(anchor['anchors']),hand_anchor_max=max(anchor['anchors']),
        bundle_manifest_sha256=digest(bundle/'manifest.json'))


def generate(out):
    spec=json.loads(TARGETS.read_text());validate_spec(spec);evidence=endpoint_evidence(spec)
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    cases=[]
    for case in spec['cases']:
        bundle=out/'song_bundles'/case['song_id'];build_bundle(bundle,case)
        checked=check_bundle(bundle,case)
        cases.append(dict(song_id=case['song_id'],kind=case['kind'],bundle=str(bundle),**checked,
            endpoint_native_verified=True,native_transition_verified=False,
            endpoint_evidence={target['case']:evidence[target['case']] for target in case['targets']}))
    files={str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()}
    report=dict(schema=SCHEMA,completed=True,source_sha256={str(Path(__file__).resolve()):digest(__file__),
        str(TARGETS):digest(TARGETS)},cases=cases,files_sha256=files,
        scope='실제 학습 compiler 입력 검사 완료. 단일 끝점 원문 성공만 확인, 새 정책·전환 물리는 미검증')
    write(out/'manifest.json',report)
    return report


def self_test():
    # 실제 writer/compiler, 두 시계, 줄 방향, 손목 궤적, 출력 파일 SHA를 모두 검사한다.
    with tempfile.TemporaryDirectory() as folder:
        out=Path(folder)/'new_inputs'; report=generate(out)
        assert len(report['cases']) == 6
        assert sum(len(row['targets']) for row in report['cases']) == 9
        bad=json.loads(TARGETS.read_text());bad['cases'][0]['targets'][0]['fret']=15
        try:validate_spec(bad)
        except ValueError:pass
        else:raise AssertionError('15프렛 입력을 허용함')
        try:generate(out)
        except FileExistsError:pass
        else:raise AssertionError('기존 입력을 덮어씀')
    return dict(completed=True,cases=6,compiled_targets=9,negative_fret_check=True,overwrite_rejected=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:print(json.dumps(self_test(),ensure_ascii=False))
    else:
        if args.out is None:parser.error('--out 또는 --self-test 필요')
        report=generate(args.out);print(json.dumps(dict(completed=report['completed'],cases=len(report['cases']),out=str(args.out.resolve())),ensure_ascii=False))
