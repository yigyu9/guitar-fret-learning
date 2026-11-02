"""v3 분석의 후보 검증만 발음 시간·오압현 의미에 맞게 정정한다.

정정 조항: raw candidate 두 개는 소리의 동시 성공을 뜻하지 않는다. 동일 중지의
6/7프렛 접촉이 함께 있을 때 A가 발음하는 3<=t<4.5초에만 A wrong 표시를
요구한다. B 발음 5.25<=t<6.75초의 낮은 프렛 부수 접촉과 발음 구간 밖 접촉은
허용한다. 평가 분모, lifecycle, 원장, 보상 및 rejection 계산은 원본 그대로다.
과거 평가를 분석할 때 result_path를 새 경로로 지정하여 원본 출력을 보존한다.
"""
import gzip
import importlib.util
import json
from pathlib import Path
import statistics

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
STUDY_PATH = ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3/tools/study.py'
spec = importlib.util.spec_from_file_location('recovery_original_study', STUDY_PATH)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
first_episodes = study.first_episodes
write = study.write


def analyze(out, count, *, result_path=None):
    out = Path(out)
    report = json.loads((out/'report.json').read_text())
    if (report.get('episodes') != count or not report.get('failed_episodes_in_denominator')
            or not report.get('completed') or not report.get('lifecycle_verified')
            or not report.get('first_episode_per_env_per_batch')):
        raise ValueError('실패 포함 평가 분모 검증 실패')
    rows = first_episodes(out, count)
    result = dict(episodes=count, A=0, B=0, AB=0, full_duration_pair=0,
                  physical=0, wrist=0, clean_s=[0., 0.], wrong_s=[0., 0.],
                  thumb_distance_m=0., thumb_contact_candidate_s=0., reward_terms={})
    ids = [row['finger_control_diagnostics']['episode_id'] for row in rows]
    for row in rows:
        ledger = row['left_note_ledger']['values']
        success = [bool(x) for x in ledger['left']]
        if len(success) != 2:
            raise ValueError('AB 두 음 필요')
        physical = bool(row['termination']['physical_failure'])
        wrist = bool(row['termination']['wrist_failure'])
        result['physical'] += physical
        result['wrist'] += wrist
        result['A'] += success[0]
        result['B'] += success[1]
        result['AB'] += all(success) and row['valid'] and not physical and not wrist
        result['full_duration_pair'] += all(v >= 1.5-1e-8 for v in ledger['clean']) and row['valid'] and not physical and not wrist
        for i in range(2):
            result['clean_s'][i] += ledger['clean'][i]/count
            result['wrong_s'][i] += ledger['wrong'][i]/count
        # 실제 진단 위치는 원장을 그대로 보존하고, 없는 값을 0으로 채우지 않는다.
        for key, value in row['reward_components'].items():
            result['reward_terms'][key] = result['reward_terms'].get(key, 0.)+value/count
        if abs(sum(row['reward_components'].values())-row['reward']) > 1e-4:
            raise ValueError('보상 성분 합계 불일치')
    rejection = dict(position=0, facing=0, load=0, wrong=0, clean=0)
    samples = 0
    tail = [[] for _ in range(count)]
    onset = [None for _ in range(count)]
    with gzip.open(out/'finger_control_trace.jsonl.gz', 'rt') as stream:
        for line in stream:
            extra = json.loads(line)['natural_preparation']['transition']
            for env in range(count):
                if extra['all_env_episode_ids'][env] != ids[env]:
                    continue
                candidate = extra['all_env_candidate'][env]
                t = extra['all_env_episode_time_s'][env]
                # 높은 프렛 후보가 낮은 프렛의 유효 소리를 막는 A 발음 구간만 검사한다.
                # B 발음 중의 낮은 프렛 접촉 및 발음 구간 밖의 기하 후보는 허용한다.
                if 3. <= t < 4.5 and all(candidate) and not extra['all_env_wrong'][env][0]:
                    raise ValueError('A 발음 중 높은7프렛 접촉에도 낮은6프렛이 clean인 모순')
                clean = [c and not w for c, w in zip(candidate, extra['all_env_wrong'][env])]
                if 4.45-1e-8 <= t < 4.5-1e-8:
                    tail[env].append(clean[0])
                if onset[env] is None and t >= 5.25-1e-8:
                    onset[env] = t <= 5.25+1/240+1e-8 and clean[1]
                if not 5.25 <= t < 6.75:
                    continue
                samples += 1
                if not extra['all_env_position_geometry'][env][1]:
                    key = 'position'
                elif not extra['all_env_facing_geometry'][env][1]:
                    key = 'facing'
                elif not extra['all_env_assigned_loaded'][env][1]:
                    key = 'load'
                elif extra['all_env_wrong'][env][1]:
                    key = 'wrong'
                else:
                    key = 'clean'
                rejection[key] += 1
    result.pop('thumb_distance_m')
    result.pop('thumb_contact_candidate_s')
    result['B_endpoint_count'] = samples
    result['B_rejection_partition'] = rejection
    result['on_time_with_previous_tail'] = sum(len(a) >= 11 and all(a) and bool(b) for a, b in zip(tail, onset))
    # 엄지 기존 진단은 원래 위치를 찾은 뒤 수치가 있는 항목만 평균한다.
    def find(value, key):
        if isinstance(value, dict):
            if key in value:
                return value[key]
            for child in value.values():
                found = find(child, key)
                if found is not None:
                    return found
        return None
    thumb = [find(row, 'thumb_support') for row in rows]
    if all(isinstance(x, dict) and 'contact_candidate_s' in x for x in thumb):
        result['thumb_contact_candidate_s'] = statistics.mean(x['contact_candidate_s'] for x in thumb)
        result['thumb_signed_gap_m'] = statistics.mean(x['mean_signed_gap_m'] for x in thumb)
        result['thumb_normal_load_N'] = statistics.mean(x['normal_load_mean_N'] for x in thumb)
    result['evaluation'] = str(out)
    write(Path(result_path) if result_path is not None else out/'analysis.json', result)
    return result

