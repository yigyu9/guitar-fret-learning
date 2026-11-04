"""중지 S3F5에서 S4F8 전환을 실제 S3F5 도착 snapshot에서 준비한다.

기존 성공 기록은 읽기만 한다. 알려진 압현각은 oracle 재생 자료로 분리하고,
학습 초기각은 실제 도착각 그대로 둔다. 새 장면·전환·동시 압현은 미검증이다.
"""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import wave

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0, str(ROOT))
STUDY = Path(__file__).resolve().parents[1]
SCHEMA = 'guitar_learning.middle_s3f5_s4f8_inputs.v1'
SWEEP = ROOT/'docs/2026-11-02/압현실험/단일압현/전수검증_1-14_v1/로그/sweep_v1'
A, B = 'middle_s3_f5', 'middle_s4_f8'
CASES = {'A0':(A,'arm_and_goals',[(A,3.,4.5),(B,5.5,7.)])}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def inside(path):
    result = Path(path).resolve(strict=True)
    result.relative_to(ROOT)
    return result


def verify_pins(pins):
    for name, expected in pins.items():
        if digest(inside(name)) != expected:
            raise ValueError('봉인 SHA 불일치: '+name)


def endpoint_sources():
    """선택한 끝점의 실측 q·몸체·속도와 원문 성공·현재 입력 봉인을 확인한다."""
    import numpy as np
    # 과거 Python은 실행하지 않고 두 성공 끝점의 JSON과 SHA만 검사한다.
    catalog = json.loads((SWEEP/A/'attempt01/inputs/catalog.json').read_text())
    sources, pins = {}, {}
    for case in sorted({A}|{event[0] for _,_,events in CASES.values() for event in events}|{start for start,_,_ in CASES.values()}):
        folder = SWEEP/case/'attempt01'
        names = ('arrival.json', 'report.json', 'episode.json', 'inputs_before.json',
                 'press_candidates.json', 'inputs/catalog.json')
        docs = {name: json.loads((folder/name).read_text()) for name in names}
        report, ep, arrival = docs['report.json'], docs['episode.json'], docs['arrival.json']
        flags = ('completed', 'execution_completed', 'task_success', 'source_sha256_match_after',
                 'pool_closed', 'scene_closed', 'preparation_ready')
        if (report['case'] != case or report['outcome'] != 'press_success' or
                report['failure'] is not None or not all(report[k] is True for k in flags)):
            raise ValueError('원문 native 끝점 성공 불충분: '+case)
        ledger = ep['left_note_ledger']['values']
        if (ep['song']['denominator'] != 1 or ep['song']['left_success_count'] != 1 or
                ep['song']['safety_invalidated'] or ledger['left'] != [True]):
            raise ValueError('원문 단일 음 원장 불일치: '+case)
        verify_pins(docs['inputs_before.json'])
        pins.update(docs['inputs_before.json'])
        source_files = {str(folder/name): digest(folder/name) for name in names}
        pins.update(source_files)
        q = np.asarray(arrival['q105'], dtype=float)
        state = arrival['state']
        if q.shape != (105,) or not np.isfinite(q).all() or not np.array_equal(
                q, [d['pos'] for d in state['human_dof_states']]):
            raise ValueError('실측 q105·DOF 원문 불일치: '+case)
        bodies = [b for kind in ('human', 'guitar', 'chair') for b in state[kind+'_body_states']]
        body13 = np.array([[*[b['pose']['p'][a] for a in 'xyz'],
            *[b['pose']['r'][a] for a in 'xyzw'], *[b['vel']['linear'][a] for a in 'xyz'],
            *[b['vel']['angular'][a] for a in 'xyz']] for b in bodies])
        if not np.isfinite(body13).all() or not np.allclose(
                body13, arrival['native_body_state13'], rtol=0, atol=1e-7):
            raise ValueError('실측 몸체·속도 native 행 불일치: '+case)
        candidate = docs['press_candidates.json']
        chosen = report['chosen_candidate']
        indices = candidate['indices']
        angles = np.asarray(chosen['finger4_rad'])
        lo, hi = np.asarray(candidate['native_lower_rad']), np.asarray(candidate['native_upper_rad'])
        cat = docs['inputs/catalog.json']
        target = cat['goals'][0]
        finger_name,string_name,fret_name=case.split('_')
        expected_mapping = (('index','middle','ring','pinky').index(finger_name)+1,int(string_name[1:])-1,int(fret_name[1:]))
        if len(cat['goals']) != 1 or (target['finger_id'],target['string'],target['fret']) != expected_mapping:
            raise ValueError('끝점 ID·손가락·줄·프렛 불일치: '+case)
        expected_indices = list(range(52+4*target['finger_id'], 56+4*target['finger_id']))
        if (indices != expected_indices or not np.isfinite(angles).all() or
                np.any(angles < lo) or np.any(angles > hi) or not any(
                    c['geometry_candidate'] and c['finger4_rad'] == chosen['finger4_rad']
                    for c in candidate['candidates'])):
            raise ValueError('원문 압현 후보·native 범위 불일치: '+case)
        other = np.setdiff1d(np.arange(105), indices)
        if not np.array_equal(np.asarray(chosen['q105'])[other], q[other]):
            raise ValueError('oracle의 비담당 관절 변경: '+case)
        if cat['reference105'] != catalog['reference105'] or cat['joint_names'] != catalog['joint_names']:
            raise ValueError('v9 기준각·관절 순서 변경: '+case)
        sources[case] = dict(catalog=cat, row=target, arrival=arrival, source=folder,
            known=dict(indices=indices, finger4_rad=angles.tolist(), arrival_q105=q.tolist(),
                press_q105=chosen['q105'], native_lower_rad=lo.tolist(), native_upper_rad=hi.tolist(),
                source_sha256=source_files),
            validation=dict(source_success=True, source_clean_s=ledger['clean'][0],
                source_best_clean_streak_s=ledger['best_clean_streak'][0],
                source_wrong_s=ledger['wrong'][0], new_pool_verified=False))
    pins[str(Path(__file__).resolve())] = digest(__file__)
    return sources, pins


def build_bundle(path, song, events, sources):
    """현행 builder·compiler로 줄 방향과 중첩 시각까지 검사한다."""
    from guitar_learning.tool import build_fret_training_data, build_strike_training_data
    from guitar_learning.tool import build_strike_plan, register_song_bundle
    from guitar_learning.song.task import load_anchor_track
    path.mkdir(parents=True)
    for name in ('mapping', 'source', 'training'):
        (path/name).mkdir()
    notes, presses, hand, expected = [], [], [], []
    for case, onset, end in events:
        row = sources[case]['row']
        string, fret, finger = row['string'], row['fret'], row['finger_id']
        mapped = 5-string
        notes.append(dict(t_on=onset-3., t_off=end-3., string=mapped, fret=fret,
            midi=(40,45,50,55,59,64)[mapped]+fret, finger=finger, barre=False, grip=None))
        presses.append(dict(finger=finger, string=mapped, fret=fret, barre=False,
            t_press=onset-3., t_release=end-3., strikes=[onset-3.]))
        # 동시 목표는 아래에서 중간 anchor 하나를 공유한다.
        hand.append(dict(t=onset-3., P=max(1, fret-finger+1), grip=None))
        expected.append((string, fret, finger, onset, end, onset))
    grouped={}
    for value in hand:grouped.setdefault(value['t'],[]).append(value['P'])
    hand=[dict(t=t,P=sorted(values)[len(values)//2],grip=None) for t,values in sorted(grouped.items())]
    mapping = dict(purpose=SCHEMA, convention='string 0 = low-E', notes=notes, presses=presses,
        hand=hand, stats=dict(dropped_invalid_fret=0), diagnostics=[], violations=[])
    fp = path/'mapping/fingering.json'
    write(fp, mapping)
    register_song_bundle.write_tablature_if_missing(path)
    with wave.open(str(path/'source/audio.wav'), 'wb') as stream:
        stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(16000)
        stream.writeframes(b'\0\0'*round((max(e[2] for e in events)-3.)*16000))
    training = path/'training'
    build_fret_training_data.main(['--fingering', str(fp), '--audio', str(path/'source/audio.wav'),
        '--out', str(training/'fret_training.json')])
    build_strike_training_data.main([str(fp), '--out', str(training/'strike_training.json')])
    build_strike_plan.main([str(training/'strike_training.json'), '--out', str(training/'strike_plan.json')])
    if any(sum(event[1]==candidate[1] for candidate in events)>1 for event in events):
        # RHS 순차 타격의 최소 오프셋을 0으로 옮겨 음수 원곡 시각을 없앤다.
        # 실제 LH 시계는 아래 전용 어댑터가 mapping 원문에서 독립 복원한다.
        plan_path = training/'strike_plan.json'
        plan = json.loads(plan_path.read_text())
        for event in plan['events']:
            if len(event['source_event_ids']) > 1:
                offset = min(event['traversal_offsets_s'])
                event['traversal_offsets_s'] = [x-offset for x in event['traversal_offsets_s']]
                event['timing_fit_rms_s'] = (sum(x*x for x in event['traversal_offsets_s'])/
                    len(event['traversal_offsets_s']))**.5
        for edge in plan['transitions']:
            previous = plan['events'][edge['from_event_index']]
            following = plan['events'][edge['to_event_index']]
            end = previous['time']+max(previous['traversal_offsets_s'])
            start = following['time']+min(following['traversal_offsets_s'])
            edge.update(traversal_end_time_s=end,next_start_time_s=start,edge_gap_s=start-end)
        plan['metadata']['diagnostic_scope'] = 'inactive RHS starts at first string; LH exact mapping clock is restored independently'
        write(plan_path, plan)
    register_song_bundle.write_manifest(song, path, dict(generator=str(Path(__file__).resolve()),
        generator_sha256=digest(__file__), source='independent silent diagnostic; native unverified'))
    task = make_task(path, pre_roll_s=3., tail_s=.5)
    compiled = [(t.string,t.fret,t.finger,t.onset_s,t.end_s,t.press_s) for t in task.targets]
    if compiled != expected or task.duration_s != max(e[2] for e in events)+.5:
        raise ValueError('compiler 목표·시각·종료 불일치: '+song+str(compiled))
    anchors = load_anchor_track(path)
    return dict(compiled_targets=[dict(target_id=t.target_id, string=t.string, fret=t.fret,
        finger=t.finger, onset_s=t.onset_s, end_s=t.end_s, press_s=t.press_s) for t in task.targets],
        duration_s=task.duration_s, hand_anchors=anchors)


def make_task(bundle, *, pre_roll_s=3., tail_s=.5):
    """왼손 목표 시각을 mapping 원문에서 그대로 복원한다.

    canonical RHS는 유한 시간 strum이므로 정확 동시 LH와 다른 시계다.
    기존 변환기의 원문 coverage·줄·프렛·손가락 검사를 먼저 통과시킨 뒤,
    모든 과제의 onset을 원문으로 복원하고 대응을 provenance에 남긴다.
    단음과 순차 음의 시각은 기존 변환기와 일치한다.
    """
    from guitar_learning.song.task import make_task as original_make_task
    root = Path(bundle).resolve()
    manifest = json.loads((root/'manifest.json').read_text())
    task = chord_task(root, pre_roll_s, tail_s)
    notes = json.loads((root/'mapping/fingering.json').read_text())['notes']
    metadata = copy.deepcopy(task.provenance)
    schedule = metadata['song']['schedule']
    targets, adapted = [], []
    for target, row in zip(task.targets, schedule):
        note = notes[row['mapping_note_index']]
        if (target.target_id != row['target_id'] or
                (target.string, target.fret, target.finger) !=
                (5-note['string'], note['fret'], note['finger'])):
            raise ValueError('동시 LH 원문 목표 ID·줄·프렛·손가락 대응 불일치')
        onset, end = note['t_on']+pre_roll_s, note['t_off']+pre_roll_s
        if target.end_s != end or target.press_s != onset:
            raise ValueError('동시 LH 원문 press/release 시각 불일치')
        adapted.append(dict(target_id=target.target_id, mapping_note_index=row['mapping_note_index'],
            string=target.string, fret=target.fret, finger=target.finger,
            canonical_rhs_onset_s=target.onset_s, left_onset_s=onset, left_end_s=end))
        targets.append(replace(target, onset_s=onset, source_onset_s=note['t_on']))
        row.update(onset_s=onset, source_onset_s=note['t_on'])
    metadata['timing_mode'] = 'exact_mapping_left_clock_inactive_right_hand'
    metadata['song']['left_clock_adapter'] = dict(schema=SCHEMA+'.left_clock',
        source='mapping/fingering.json t_on/t_off; original compiler identity/coverage retained',
        targets=adapted, right_hand_active=False, wrist_anchors_changed=False)
    return replace(task, targets=tuple(targets), provenance=metadata)


def chord_task(root, pre_roll_s, tail_s):
    """단음 사전조건 없이 canonical 전체 이벤트 coverage를 검사한다."""
    from guitar_learning.score.canonical import load_music_task
    from guitar_learning.song.task import SongTask, ScoreTarget, EVENT_FIELDS, STATE_FIELDS
    source = load_music_task(root, stage='D', phrase_events=1, preroll_s=pre_roll_s)
    notes = json.loads((root/'mapping/fingering.json').read_text())['notes']
    manifest = json.loads((root/'manifest.json').read_text())
    targets, schedule = [], []
    all_targets=[(event,target) for event in source.timeline.events for target in event.string_targets]
    for event,target in all_targets:
        onset = event.score_time_s+target.traversal_offset_s
        identity = f'{event.event_id}/string-{target.string+1}/note-{target.mapping_note_index}'
        end = min(target.sustain_until_s, target.release_s)
        direction = 1 if event.strike.direction == 'down' else -1
        targets.append(ScoreTarget(identity,event.event_id,target.string,target.fret,target.finger,
            direction,onset+pre_roll_s,end+pre_roll_s,target.press_start_s+pre_roll_s,onset,end))
        schedule.append(dict(target_id=identity,event_id=event.event_id,mapping_note_index=target.mapping_note_index,
            source_event_id=target.source_event_id,source_string=target.source_string,string=target.string,
            fret=target.fret,finger=target.finger,direction=direction,source_onset_s=onset,
            source_note_on_s=target.note_on_s,source_note_off_s=target.note_off_s,source_end_s=end,
            source_press_s=target.press_start_s,source_release_s=target.release_s,onset_s=onset+pre_roll_s,
            end_s=end+pre_roll_s,press_s=target.press_start_s+pre_roll_s,expanded_restrike=False))
    indices = [r['mapping_note_index'] for r in schedule]
    if sorted(indices) != list(range(len(notes))) or any(not e.supported for e in source.timeline.events):
        raise ValueError('전체 canonical 목표 coverage·지원검사 실패')
    audio = root/'source/audio.wav'
    with wave.open(str(audio),'rb') as stream:
        frames, rate = stream.getnframes(), stream.getframerate()
    audio_entry = manifest['files']['source/audio.wav']
    if digest(audio) != audio_entry['sha256'] or audio.stat().st_size != audio_entry['bytes']:
        raise ValueError('전체 audio manifest 불일치')
    import math
    ticks = math.ceil((pre_roll_s+frames/rate+tail_s)*60)
    metadata = source.content_document()
    metadata.pop('observation_dim'); metadata.pop('lookahead')
    metadata.update(schema='guitar_learning.song_score.v1',stage='full',source_origin_s=0.,event_ids=[event.event_id for event in source.timeline.events],
        timing_mode='source_audio_clock',event_fields=list(EVENT_FIELDS),state_fields=list(STATE_FIELDS),
        lookahead_s=4.,capacity=64,song=dict(source_manifest=manifest,manifest_path=str(root/'manifest.json'),
        manifest_sha256=digest(root/'manifest.json'),audio_path=str(audio),audio_sha256=digest(audio),
        audio_frames=frames,audio_sample_rate=rate,audio_duration_s=frames/rate,pre_roll_s=pre_roll_s,
        tail_s=tail_s,control_hz=60,control_ticks=ticks,policy_duration_s=ticks/60,
        source_event_count=len(source.timeline.events),source_note_count=len(notes),source_mapping_indices=indices,
        coverage=dict(complete=True,unique=True,omitted_indices=[],duplicated_indices=[]),
        expanded_event_ids=[],schedule=schedule,
        derivation='full canonical timeline coverage; no B single-note prerequisite; exact source mapping LH clock'))
    return SongTask(tuple(targets),lookahead_s=4.,provenance=metadata,episode_duration_s=ticks/60)


def generate(out):
    sources, source_pins = endpoint_sources()
    out = Path(out).resolve(); out.relative_to(ROOT)
    out.mkdir(parents=True, exist_ok=False)
    results = {}
    for case_id, (start, control, events) in CASES.items():
        folder = out/case_id; folder.mkdir()
        song = 'middle_s3f5_s4f8_'+case_id.lower()
        bp = folder/'song_bundles'/song
        checked = build_bundle(bp, song, events, sources)
        src = sources[start]
        row = copy.deepcopy(src['row'])
        for key in ('transport_waypoints','transport_path_candidate_valid','attempts','path_scope'):
            row.pop(key, None)
        fingers = sorted({sources[e[0]]['row']['finger_id'] for e in events})
        q, state = src['arrival']['q105'], src['arrival']['state']
        row.update(case_id=case_id, case=case_id, song=song, song_id=song, bundle=str(bp),
            target_fingers=fingers, control_scope=control, q105=q, state=state, body_snapshot=state,
            hold_target105=q, final_hover_q105=q, final_hover_state=state, candidate_valid=True,
            native_verified=True, native_verification_scope=src['validation'],
            new_pool_verified=False, source_endpoint=start, **checked)
        catalog = copy.deepcopy(src['catalog'])
        catalog.update(schema=SCHEMA+'.catalog', goals=[row], initial_q105=q,
            source_sha256=source_pins, new_pool_verified=False,
            initialization_scope='actual recorded arrival; boundary reset only; no oracle angles')
        endpoints = {e[0]:sources[e[0]]['known'] for e in events}
        known = dict(schema=SCHEMA+'.oracle', case_id=case_id, source_endpoint=start,
            endpoint_states=endpoints, events=[dict(endpoint_case=c,onset_s=a,end_s=b,
                press_q105=sources[c]['known']['press_q105']) for c,a,b in events],
            new_pool_verified=False, transition_verified=False, simultaneous_verified=False,
            scope='각 끝점의 별도 기록만. 동시각을 합성하거나 학습 정답으로 주입하지 않음')
        # 기존 단일 손가락 oracle 도구와 연결할 필드는 시작 끝점에 한해서만 둔다.
        known.update({k:src['known'][k] for k in ('indices','finger4_rad','arrival_q105',
            'native_lower_rad','native_upper_rad')})
        write(folder/'known_press.json', known); write(folder/'catalog.json', catalog)
        pins = dict(source_pins)
        pins.update({str(p):digest(p) for p in bp.rglob('*') if p.is_file()})
        pins[str(folder/'known_press.json')] = digest(folder/'known_press.json')
        provenance = dict(schema=SCHEMA+'.provenance', catalog_sha256=digest(folder/'catalog.json'),
            active_physical_inputs=pins, source_endpoint=start,
            source_arrival=str(src['source']/'arrival.json'),
            source_arrival_sha256=digest(src['source']/'arrival.json'), reset_only=True)
        write(folder/'provenance.json', provenance)
        manifest = dict(schema=SCHEMA+'.manifest', completed=True, case_id=case_id,
            catalog_sha256=digest(folder/'catalog.json'), provenance_sha256=digest(folder/'provenance.json'),
            known_press_sha256=digest(folder/'known_press.json'), new_pool_verified=False,
            compiled=checked, target_fingers=fingers, control_scope=control)
        write(folder/'manifest.json', manifest)
        load_verified(folder)
        results[case_id] = manifest
    write(out/'manifest.json', dict(schema=SCHEMA, completed=True, cases=results,
        source_sha256=source_pins, scope='CPU compiler·실측 snapshot·SHA만 검증. 새 native 미검증'))
    return results


def load_verified(input_dir):
    """학습 시작·재개 시 입력과 원문 SHA·실측 snapshot을 다시 확인한다."""
    import numpy as np
    out = inside(input_dir)
    provenance = json.loads((out/'provenance.json').read_text())
    if provenance['schema'] != SCHEMA+'.provenance':
        raise ValueError('복합압현 독립 입력 schema 필요')
    verify_pins(provenance['active_physical_inputs'])
    catalog = json.loads((out/'catalog.json').read_text())
    known = json.loads((out/'known_press.json').read_text())
    manifest = json.loads((out/'manifest.json').read_text())
    for name, key in (('catalog.json','catalog_sha256'), ('provenance.json','provenance_sha256'),
                      ('known_press.json','known_press_sha256')):
        if digest(out/name) != manifest[key]:
            raise ValueError('입력 manifest SHA 불일치: '+name)
    if len(catalog['goals']) != 1 or manifest['case_id'] not in CASES:
        raise ValueError('과제 하나의 정렬 입력 필요')
    row = catalog['goals'][0]
    source = inside(provenance['source_arrival'])
    if digest(source) != provenance['source_arrival_sha256']:
        raise ValueError('실측 arrival 원문 SHA 불일치')
    arrival = json.loads(source.read_text())
    if row['state'] != arrival['state']:
        raise ValueError('실측 snapshot 변경')
    q = np.asarray([d['pos'] for d in row['state']['human_dof_states']])
    if q.shape != (105,) or not np.isfinite(q).all() or any(not np.array_equal(q,row[k])
            for k in ('q105','hold_target105','final_hover_q105')):
        raise ValueError('실측 q105와 초기·유지각 불일치')
    if row['target_fingers'] != manifest['target_fingers'] or row['control_scope'] != manifest['control_scope']:
        raise ValueError('정책 행동 mask 계약 불일치')
    paths = {Path(p) for p in provenance['active_physical_inputs']}
    paths.update(out/name for name in ('catalog.json','provenance.json','known_press.json','manifest.json'))
    return catalog, row, known, sorted(paths)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = generate(args.out)
    print(json.dumps(dict(completed=True, cases=len(result), input_dir=str(args.out.resolve())),ensure_ascii=False))
