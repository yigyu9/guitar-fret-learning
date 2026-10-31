"""16개 목표의 실제 압현 기록과 손목 추종 오차를 CPU에서 분석한다."""
import argparse
import csv
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent/'guitar_learning').is_dir())
FINGERS = {1: '검지', 2: '중지', 3: '약지', 4: '소지'}


def summarize(values):
    """유효 표본이 없는 구간을0으로 오인하지 않도록 None으로 남긴다."""
    import numpy as np
    values = np.asarray(values, dtype=float)
    if not len(values):
        return dict(samples=0, mean=None, rms=None, maximum=None)
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite analysis samples')
    return dict(samples=len(values), mean=float(values.mean()),
                rms=float(np.sqrt(np.mean(values**2))), maximum=float(values.max()))


def required_clean_seconds(target, left_fraction=.4):
    """현행 TensorSongEnvironment.required 식. ScoreTarget에 해당 필드는 없다."""
    duration = target.end_s-target.onset_s
    return min(duration, max(.05, left_fraction*duration))


def wrist_measurements(poses, slot, metadata, settings, goal, fk, prepared_guitar):
    """요청각 FK 오차와 실제각 FK 모델오차를 별도로 계산한다."""
    import numpy as np
    from scipy.spatial.transform import Rotation
    valid = poses['valid'][:, slot].astype(bool)
    valid_count = int(valid.sum())
    if not valid[:valid_count].all() or valid[valid_count:].any():
        raise ValueError('Noncontiguous safe pose prefix')
    wrist = metadata['body_names'].index('human/L_Wrist')
    guitar = metadata['body_names'].index('guitar/guitar')
    gp0, gr0 = prepared_guitar
    final_p, final_r = fk(np.asarray(goal['q_target105']))['L_Wrist']
    goal_local = gr0.inv().apply(final_p-gp0)
    goal_local_rotation = gr0.inv()*final_r
    values = {key: [] for key in ('request_position_m', 'request_rotation_rad',
        'actual_q_fk_position_m', 'actual_q_fk_rotation_rad',
        'final_goal_live_guitar_position_m', 'final_goal_live_guitar_rotation_rad')}
    times = poses['tick'][valid]/60.
    for frame in np.flatnonzero(valid):
        actual = poses['body_state'][frame, slot, wrist]
        ar = Rotation.from_quat(actual[3:7])
        for label, q in (('request', poses['target'][frame, slot]), ('actual_q_fk', poses['q'][frame, slot])):
            p, r = fk(q)['L_Wrist']
            values[label+'_position_m'].append(np.linalg.norm(p-actual[:3]))
            values[label+'_rotation_rad'].append((r.inv()*ar).magnitude())
        gb = poses['body_state'][frame, slot, guitar]
        gr = Rotation.from_quat(gb[3:7])
        values['final_goal_live_guitar_position_m'].append(np.linalg.norm(gb[:3]+gr.apply(goal_local)-actual[:3]))
        values['final_goal_live_guitar_rotation_rad'].append(((gr*goal_local_rotation).inv()*ar).magnitude())
    hold_start = settings['initial_hold_s']+settings['ramp_s']
    late = times >= hold_start+settings['hold_s']/2
    return dict(safe_frames=valid_count, last_safe_time_s=float(times[-1]) if len(times) else None,
        late_hold_start_s=hold_start+settings['hold_s']/2,
        interpretation='Request FK is a source-model expectation, not an independently certified world target; actual_q_fk measures model/readback mismatch separately',
        all_valid={key: summarize(value) for key, value in values.items()},
        late_hold={key: summarize(np.asarray(value)[late]) for key, value in values.items()})


def analyze(root):
    import numpy as np
    from scipy.spatial.transform import Rotation
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.song.task import make_task
    geometry = json.loads((root/'geometry/candidates.json').read_text(encoding='utf-8'))
    task = make_task(Path(geometry['bundle']))
    contract = load_gpu_prepared_reset_contract('left')
    state = contract['state']
    fk = full_fk(SimpleNamespace(names=contract['initial']['joint_names'],
        human_bodies=contract['initial']['human_body_names'],
        q_ref=np.array([row['pos'] for row in state['human_dof_states']])), state)
    g = state['guitar_body_states'][0]['pose']
    prepared_guitar = (np.array([g['p'][axis] for axis in 'xyz']),
                       Rotation.from_quat([g['r'][axis] for axis in 'xyzw']))
    records, conditions = [], []
    for path in sorted((root/'replay').glob('*/report.json')):
        report = json.loads(path.read_text(encoding='utf-8'))
        source = path.parent
        metadata = json.loads((source/'metadata.json').read_text(encoding='utf-8'))
        with np.load(source/'poses60.npz', allow_pickle=False) as archive:
            poses = {key: archive[key] for key in archive.files}
        with np.load(source/'trace240.npz', allow_pickle=False) as archive:
            trace = {key: archive[key] for key in archive.files}
        rows = report['settings']['representative_rows']
        if len(report['goals']) != 16 or len(rows) != 16 or poses['valid'].shape[1] != 16 or trace['valid'].shape[1] != 16:
            raise ValueError('Full16-goal physical records required: '+str(source))
        conditions.append(dict(name=source.name, settings=report['settings'],
            source_fk_readback=report['source_fk_readback'], source_unchanged=report['source_unchanged']))
        for goal in report['goals']:
            slot = rows.index(goal['row'])
            valid = trace['valid'][:, slot].astype(bool)
            trace_best = float(np.max(trace['streak'][valid, slot], initial=0.))
            if abs(trace_best-goal['best_contact_streak_s']) > 1e-8:
                raise ValueError('Report best contact does not match accepted physics samples')
            for key, seconds in goal['seconds'].items():
                if abs(float(np.count_nonzero(valid & trace[key][:, slot])/240.)-seconds) > 1e-8:
                    raise ValueError('Report contact component does not match physical trace: '+key)
            target = task.targets[goal['source_note_index']]
            if (target.string, target.fret, target.finger) != (goal['string'], goal['fret'], goal['finger']):
                raise ValueError('Target no longer agrees with the original score')
            required = required_clean_seconds(target)
            wrist = wrist_measurements(poses, rows.index(goal['row']), metadata, report['settings'],
                                       goal, fk, prepared_guitar)
            record = dict(condition=source.name, row=goal['row'], finger=goal['finger'],
                finger_name=FINGERS[goal['finger']], physical_string=goal['physical_string'], fret=goal['fret'],
                source_note_index=goal['source_note_index'], source_note_duration_s=target.end_s-target.onset_s,
                required_clean_s=required, static_streak_meets_note_duration_threshold=goal['best_contact_streak_s']+1e-12 >= required,
                song_timing_achievement_measured=False,
                trace240_report_verified=True, accepted_physics_samples=int(valid.sum()),
                minimum_distance_m=goal['minimum_distance_m'],
                best_contact_streak_s=goal['best_contact_streak_s'], first_contact_50ms=goal['first_contact_50ms'],
                diagnostic_hold_100ms=goal['diagnostic_hold_100ms'], failure=goal['failure'],
                seconds=goal['seconds'], maximum_target_error_rad=goal['maximum_target_error_rad'],
                wrist=wrist)
            records.append(record)
    if not conditions:
        raise ValueError('No completed physical replay reports found')
    result = dict(scope='Static physical goal diagnostics, not policy evaluation or original song timing achievement',
        required_clean_formula='min(end-onset,max(0.05,0.4*(end-onset))); same replay left_fraction=0.4',
        conditions=conditions, records=records)
    analysis = root.parent/'analysis'
    analysis.mkdir(parents=True, exist_ok=True)
    (analysis/'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    fields = ['condition', 'row', 'finger_name', 'physical_string', 'fret', 'minimum_distance_m',
        'best_contact_streak_s', 'required_clean_s', 'static_streak_meets_note_duration_threshold',
        'diagnostic_hold_100ms', 'failure', 'position_s', 'facing_s', 'loaded_s', 'wrong_s',
        'wrist_request_rms_m', 'wrist_request_rotation_rms_rad', 'late_wrist_request_mean_m', 'late_wrist_request_max_m']
    with (analysis/'analysis.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in records:
            flat = {key: row[key] for key in fields if key in row}
            flat['failure'] = json.dumps(row['failure'], ensure_ascii=False)
            flat.update({key+'_s': row['seconds'][key] for key in ('position', 'facing', 'loaded', 'wrong')})
            flat.update(wrist_request_rms_m=row['wrist']['all_valid']['request_position_m']['rms'],
                wrist_request_rotation_rms_rad=row['wrist']['all_valid']['request_rotation_rad']['rms'],
                late_wrist_request_mean_m=row['wrist']['late_hold']['request_position_m']['mean'],
                late_wrist_request_max_m=row['wrist']['late_hold']['request_position_m']['maximum'])
            writer.writerow(flat)
    lines = ['# 손가락별 압현 가능성 분석', '',
        '실제 물리 기록의 정적 목표 검사다. 100ms 접촉, 원곡 음 길이 기준 충족, 원곡 시간창 내 달성은 서로 다르다. 여기서는 마지막 항목을 측정하지 않았다.', '',
        '손목 요청각 FK와 실제 손목의 차이는 소스 운동학 모델 오차도 포함한다. 실제각 FK와 실제 pose의 오차를 analysis.json에 별도로 기록했으므로 제어 오차와 혼동하지 않는다.', '',
        '| 조건 | 손가락 | 줄/프렛 | 최근접 mm | 최대 연속접촉 s | 원곡 기준 s | 기준길이 충족 | 100ms | 안전실패 |',
        '|---|---|---|---:|---:|---:|---|---|---|']
    for row in records:
        distance = '-' if row['minimum_distance_m'] is None else '%.2f'%(1000*row['minimum_distance_m'])
        failure = '-' if row['failure'] is None else ', '.join(row['failure']['reasons'])
        lines.append('| %s | %s | %d / %d | %s | %.3f | %.3f | %s | %s | %s |'%(
            row['condition'], row['finger_name'], row['physical_string'], row['fret'], distance,
            row['best_contact_streak_s'], row['required_clean_s'],
            'O' if row['static_streak_meets_note_duration_threshold'] else '-',
            'O' if row['diagnostic_hold_100ms'] else '-', failure))
    lines += ['', '100ms 성공 중 안전한 자세 기록으로 확인 가능한 영상은 process/rendering/의 조건별 manifest.json에 모은다.', '',
        '고정 기타 성공은 자유 기타 성공으로 상속하지 않는다. 탐색 실패는 도달 불가능성의 증명이 아니다.', '',
        'analysis.csv는 전체 목표의 접촉 조건별 시간과 손목 오차 요약, analysis.json은 후반 홀드 및 모델 오차를 포함한다. 후반 홀드 도달 전 안전 종료된 경우 해당 통계는 null이다.', '']
    (analysis/'RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.path.insert(0, str(ROOT))
    result = analyze(args.root.resolve())
    print('Analyzed %d conditions, %d goal records'%(len(result['conditions']), len(result['records'])))


if __name__ == '__main__':
    main()
