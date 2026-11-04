"""실제로 도달한 중지 S3 F6 자세를 에피소드 경계 전용 정렬 입력으로 저장한다.

과거 Python은 실행하지 않고 원본 JSON과 봉인 SHA만 읽는다. 원문 q·몸체·속도를
보존하며 v9 행동 기준각은 바꾸지 않는다. 계산된 압현 각은 별도 oracle 입력으로
분리하므로 학습의 초기 손가락 목표에는 들어가지 않는다.
"""
import argparse
import copy
import hashlib
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import wave

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0,str(ROOT))
STUDY=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/2026-11-09/단일압현_준비와유지개선_v1/로그/실행검증_baseline_s7'
SCHEMA='guitar_learning.native_arrival_aligned_input.v1'
SONG='aligned_middle_s3_f6'
SOURCE_SHA={
    'arrival.json':'f9c1650147f10a3de02adbd47ccc24abcab8cd47344bc0c8adbc4d5ed4721530',
    'report.json':'4d36353bdedc780e35058fbbd2e8b51789541100e465ad5c067d463df57ed761',
    'episode.json':'c10f1dfb59705e9bf257a1a241f1f66c36eba9927309faa641e4202564f72dc7',
    'inputs_before.json':'2a6e776017bbe63501e1362b2f28d3d31a59068fcaa23d3c19d05dc41c62e2ab',
    'press_candidates.json':'97bf8fa984e1014823b7efe83e0402177c005d68b9eeb2802b31a30ffe70950e',
    'inputs/catalog.json':'c4c488b3d98794b8b984d9b94233d873b59e16a3c2173a85b7b38b6c8fc8e6f3'}


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inside(path):
    result=Path(path).resolve(strict=True);result.relative_to(ROOT)
    return result


def write(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def verify_pins(pins):
    for name,expected in pins.items():
        path=inside(name)
        if digest(path)!=expected:raise ValueError('입력 SHA 불일치: '+name)


def source():
    """별도 시뮬레이션 없이 원문 성공과 원문 실제 snapshot의 일관성을 확인한다."""
    import numpy as np
    from scipy.spatial.transform import Rotation
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    files={str(SOURCE/name):sha for name,sha in SOURCE_SHA.items()};verify_pins(files)
    docs={name:json.loads((SOURCE/name).read_text()) for name in SOURCE_SHA}
    report,arrival,episode=docs['report.json'],docs['arrival.json'],docs['episode.json']
    flags=('completed','execution_completed','task_success','source_sha256_match_after','pool_closed','scene_closed','preparation_ready')
    if (report['case']!='middle_s3_f6' or report['condition']!='baseline' or report['failure'] is not None or
            report['outcome']!='press_success' or not all(report[key] is True for key in flags)):
        raise ValueError('원본 native 단일 압현 성공 검증 실패')
    ledger=episode['left_note_ledger']['values']
    if (episode['song']['denominator']!=1 or episode['song']['left_success_count']!=1 or
            episode['song']['safety_invalidated'] or ledger['left']!=[True]):
        raise ValueError('원본 에피소드 압현 원장 불일치')
    pins=dict(docs['inputs_before.json']);verify_pins(pins);pins.update(files)
    contract=load_gpu_prepared_reset_contract('left');pins.update(contract['source_sha256'])
    catalog=docs['inputs/catalog.json'];row=catalog['goals'][0]
    if len(catalog['goals'])!=1 or (row['finger_id'],row['string'],row['fret'])!=(2,2,6):
        raise ValueError('중지 표준3번 줄6프렛만 지원')
    q=np.asarray(arrival['q105'],dtype=float);state=arrival['state']
    if q.shape!=(105,) or not np.isfinite(q).all() or not np.array_equal(q,[d['pos'] for d in state['human_dof_states']]):
        raise ValueError('실제 q105와 실제 DOF snapshot 불일치')
    body=[b for kind in ('human','guitar','chair') for b in state[kind+'_body_states']]
    rows=np.array([[*[b['pose']['p'][a] for a in 'xyz'],*[b['pose']['r'][a] for a in 'xyzw'],
        *[b['vel']['linear'][a] for a in 'xyz'],*[b['vel']['angular'][a] for a in 'xyz']] for b in body])
    if not np.isfinite(rows).all() or not np.allclose(rows,arrival['native_body_state13'],rtol=0,atol=1e-7):
        raise ValueError('몸체 위치·회전·속도의 원문 native 행 불일치')
    names=contract['initial']['human_body_names'];joint_names=contract['initial']['joint_names']
    if joint_names!=catalog['joint_names']:raise ValueError('native105 순서 불일치')
    fk=full_fk(SimpleNamespace(names=joint_names,human_bodies=names,q_ref=q),state)
    reconstructed=fk(q);position_error=0.;angle_error=0.
    for name,body in zip(names,state['human_body_states']):
        p=np.array([body['pose']['p'][a] for a in 'xyz']);r=Rotation.from_quat([body['pose']['r'][a] for a in 'xyzw'])
        position_error=max(position_error,float(np.linalg.norm(reconstructed[name][0]-p)))
        angle_error=max(angle_error,float((reconstructed[name][1].inv()*r).magnitude()))
    if position_error>1e-10 or angle_error>1e-10:raise ValueError('실제 snapshot 기준 FK 재현 실패')
    candidates=docs['press_candidates.json'];indices=candidates['indices'];chosen=report['chosen_candidate']
    lower=np.asarray(candidates['native_lower_rad']);upper=np.asarray(candidates['native_upper_rad']);angles=np.asarray(chosen['finger4_rad'])
    if indices!=[60,61,62,63] or not np.isfinite(angles).all() or np.any(angles<lower) or np.any(angles>upper):
        raise ValueError('원본 담당4축 각도 또는 native 범위 불일치')
    if not any(c['geometry_candidate'] and c['finger4_rad']==chosen['finger4_rad'] for c in candidates['candidates']):
        raise ValueError('선택한 각도가 원본 기하 후보에 없음')
    other=np.setdiff1d(np.arange(105),indices)
    if not np.array_equal(np.asarray(chosen['q105'])[other],q[other]):raise ValueError('oracle 비담당101축 변경')
    for function in (load_gpu_prepared_reset_contract,full_fk):
        path=Path(inspect.getsourcefile(function)).resolve();pins[str(path)]=digest(path)
    pins[str(Path(__file__).resolve())]=digest(__file__)
    validation=dict(source_success=True,new_aligned_pool_verified=False,source_pinned_inputs_verified=len(docs['inputs_before.json']),
        fk_position_max_error_m=position_error,fk_orientation_max_error_rad=angle_error,
        snapshot_state_physics_step_legacy=state['physics_step'],source_transport_raw_physics_steps=report['preparation'][0]['raw_physics_steps'],
        clock_scope='legacy state.physics_step retained verbatim; a new episode starts at0, not5280 or716',
        source_clean_s=ledger['clean'][0],source_best_clean_streak_s=ledger['best_clean_streak'][0],source_wrong_s=ledger['wrong'][0])
    known=dict(schema=SCHEMA+'.oracle',case='middle_s3_f6',song=SONG,indices=indices,
        finger_joint_names=[joint_names[i] for i in indices],finger4_rad=angles.tolist(),
        arrival_finger4_rad=q[indices].tolist(),native_lower_rad=lower.tolist(),native_upper_rad=upper.tolist(),
        source_report_sha256=SOURCE_SHA['report.json'],source_arrival_sha256=SOURCE_SHA['arrival.json'],
        source_candidate_verified=True,new_pool_verified=False,
        scope='원본 성공 동작의4축 요청각. 별도 oracle 대조에만 사용하며 학습 reset/초기 목표에 주입하지 않음')
    return catalog,row,arrival,known,pins,validation


def bundle(path):
    from guitar_learning.tool import build_fret_training_data,build_strike_training_data,build_strike_plan,register_song_bundle
    from guitar_learning.song.task import make_task,load_anchor_track
    path.mkdir(parents=True);(path/'mapping').mkdir();(path/'source').mkdir();(path/'training').mkdir()
    mapping=dict(purpose=SCHEMA,convention='string 0 = low-E',
        notes=[dict(t_on=0.,t_off=1.5,string=3,fret=6,midi=61,finger=2,barre=False,grip=None)],
        presses=[dict(finger=2,string=3,fret=6,barre=False,t_press=0.,t_release=1.5,strikes=[0.])],
        hand=[dict(t=0.,P=5,grip=None)],stats=dict(dropped_invalid_fret=0),diagnostics=[],violations=[])
    fp=path/'mapping/fingering.json';write(fp,mapping);register_song_bundle.write_tablature_if_missing(path)
    audio=path/'source/audio.wav'
    with wave.open(str(audio),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000);out.writeframes(b'\0\0'*24000)
    training=path/'training'
    build_fret_training_data.main(['--fingering',str(fp),'--audio',str(audio),'--out',str(training/'fret_training.json')])
    build_strike_training_data.main([str(fp),'--out',str(training/'strike_training.json')])
    build_strike_plan.main([str(training/'strike_training.json'),'--out',str(training/'strike_plan.json')])
    register_song_bundle.write_manifest(SONG,path,dict(generator=str(Path(__file__).resolve()),generator_sha256=digest(__file__),source='new independent1.5s silent diagnostic'))
    task=make_task(path,pre_roll_s=3.,tail_s=.5);target=task.targets[0];anchors=load_anchor_track(path)
    if (len(task.targets)!=1 or (target.string,target.fret,target.finger,target.onset_s,target.end_s,target.press_s)!=(2,6,2,3.,4.5,3.) or
            task.duration_s!=5. or min(anchors['anchors'])!=5. or max(anchors['anchors'])!=5.):
        raise ValueError('새 독립 단일 압현 번들 compiler 검증 실패')


def generate(out):
    catalog,row,arrival,known,pins,validation=source()
    out=Path(out).resolve();out.relative_to(ROOT);out.mkdir(parents=True,exist_ok=False)
    bp=out/'song_bundles'/SONG;bundle(bp)
    row=copy.deepcopy(row)
    for key in ('transport_waypoints','transport_path_candidate_valid','attempts','path_scope'):
        row.pop(key,None)
    row.update(q105=arrival['q105'],state=arrival['state'],body_snapshot=arrival['state'],
        hold_target105=arrival['q105'],final_hover_q105=arrival['q105'],final_hover_state=arrival['state'],
        song=SONG,bundle=str(bp),candidate_valid=True,native_verified=True,
        native_verification_scope=validation,
        initialization_scope='recorded actual native arrival; episode-boundary reset only; no mid-episode state writes')
    catalog=copy.deepcopy(catalog);catalog.update(schema=SCHEMA+'.catalog',goals=[row],initial_q105=arrival['q105'],
        source_sha256=pins,native_verified=True,native_verification_scope=validation,new_pool_verified=False)
    # reference105를 실제 도착각이나 oracle 각으로 바꾸지 않는다.
    original=json.loads((SOURCE/'inputs/catalog.json').read_text())
    if catalog['reference105']!=original['reference105']:raise ValueError('v9 행동 기준각 변경 금지')
    write(out/'known_press.json',known);write(out/'catalog.json',catalog)
    for path in bp.rglob('*'):
        if path.is_file():pins[str(path.resolve())]=digest(path)
    pins[str((out/'known_press.json').resolve())]=digest(out/'known_press.json')
    write(out/'provenance.json',dict(schema=SCHEMA+'.provenance',catalog_sha256=digest(out/'catalog.json'),
        active_physical_inputs=pins,source=str(SOURCE),source_validation=validation,reset_only=True))
    manifest=dict(schema=SCHEMA+'.manifest',completed=True,catalog_sha256=digest(out/'catalog.json'),
        provenance_sha256=digest(out/'provenance.json'),known_press_sha256=digest(out/'known_press.json'),
        bundle=str(bp),validation=validation,source_files=SOURCE_SHA,new_pool_verified=False)
    write(out/'manifest.json',manifest)
    load_verified(out)
    return manifest


def load_verified(input_dir):
    """독립 입력의 SHA·실측 자세·oracle 범위를 재검증하여 runtime에 전달한다."""
    import numpy as np
    out=inside(input_dir);provenance=json.loads((out/'provenance.json').read_text())
    if provenance['schema']!=SCHEMA+'.provenance':raise ValueError('독립된 정렬 입력 schema 필요')
    if digest(out/'catalog.json')!=provenance['catalog_sha256']:raise ValueError('catalog SHA 불일치')
    verify_pins(provenance['active_physical_inputs'])
    catalog=json.loads((out/'catalog.json').read_text());known=json.loads((out/'known_press.json').read_text())
    row=catalog['goals'][0]
    if len(catalog['goals'])!=1 or (row['finger_id'],row['string'],row['fret'],row['song'])!=(2,2,6,SONG):
        raise ValueError('중지 S3 F6만 지원')
    q=np.array([d['pos'] for d in row['state']['human_dof_states']])
    if q.shape!=(105,) or not np.isfinite(q).all():raise ValueError('유한 q105 필요')
    for key in ('q105','hold_target105','final_hover_q105'):
        if not np.array_equal(q,row[key]):raise ValueError('정렬 snapshot과 '+key+' 불일치')
    original=json.loads((SOURCE/'inputs/catalog.json').read_text())
    if catalog['reference105']!=original['reference105']:raise ValueError('v9 기준각 변경')
    if row['state']!=json.loads((SOURCE/'arrival.json').read_text())['state']:
        raise ValueError('실제 snapshot 원문 변경')
    angles=np.array(known['finger4_rad']);lo=np.array(known['native_lower_rad']);hi=np.array(known['native_upper_rad'])
    if known['indices']!=[60,61,62,63] or not np.isfinite(angles).all() or np.any(angles<lo) or np.any(angles>hi):
        raise ValueError('oracle4축의 native 범위 위반')
    report=json.loads((SOURCE/'report.json').read_text())
    if known['finger4_rad']!=report['chosen_candidate']['finger4_rad']:raise ValueError('oracle 원문 변경')
    manifest=json.loads((out/'manifest.json').read_text())
    for filename,key in (('catalog.json','catalog_sha256'),('provenance.json','provenance_sha256'),('known_press.json','known_press_sha256')):
        if digest(out/filename)!=manifest[key]:raise ValueError('manifest SHA 불일치: '+filename)
    paths={Path(p) for p in provenance['active_physical_inputs']}
    paths.update(out/name for name in ('catalog.json','provenance.json','known_press.json','manifest.json'))
    return catalog,row,known,sorted(paths)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();result=generate(args.out)
    write(STUDY/'검증/입력원장.json',dict(result,completed=True,input_dir=str(args.out.resolve())))
    print(json.dumps(dict(completed=True,input_dir=str(args.out.resolve()),catalog_sha256=result['catalog_sha256']),ensure_ascii=False))
