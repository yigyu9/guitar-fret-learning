"""팔 bias 초기 prior 제거 비교. 완료 raw 평가만 CPU에서 재사용 집계한다."""
import os
for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[key] = '1'
import json
from pathlib import Path
from datetime import datetime, timezone
import compare_variance as comparison

ROOT = Path(__file__).resolve().parent
CONTROL = ROOT/'index_full33_seed7_v1'
VARIANT = ROOT/'no_alignment_prior_variant/runs'


def equal(a, b):
    """실제 tensor/배열/Adam/RNG 중첩 자료를 값까지 정확히 비교한다."""
    import torch
    import numpy as np
    if type(a) is not type(b):
        return False
    if isinstance(a, torch.Tensor):
        return a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return a.dtype == b.dtype and np.array_equal(a, b)
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def load_pair(a, b, pins):
    if not a.is_file() or not b.is_file():
        return None
    import torch
    torch.set_num_threads(1)
    for path in (a, b):
        pins[str(path)] = comparison.digest(path)
    return [torch.load(str(path), map_location='cpu', weights_only=False) for path in (a, b)]


def initial_proof(pins):
    pair = load_pair(CONTROL/'100/train/J/initial.pt', VARIANT/'100/train/J/initial.pt', pins)
    if pair is None:
        return dict(status='pending')
    a, b = pair
    key = 'core.support_head.bias'
    expected = type(a['model'])((k, v.clone()) for k, v in a['model'].items())
    original = expected[key][:12].clone()
    expected[key][:12] = 0
    checks = dict(model_exact_except_zeroed_arm_bias=equal(expected, b['model']),
        cpu_rng_equal=equal(a['torch_rng'], b['torch_rng']),
        cuda_rng_equal=equal(a['cuda_rng'], b['cuda_rng']),
        numpy_rng_equal=equal(a['numpy_rng'], b['numpy_rng']),
        python_rng_equal=equal(a['python_rng'], b['python_rng']),
        original_bias_nonzero=bool(original.abs().max().item() > 0),
        variant_bias_zero=bool(b['model'][key][:12].abs().max().item() == 0))
    report_path = VARIANT/'100/train/report.json'
    audit = comparison.read(report_path).get('initial_prior_audit') if report_path.exists() else None
    if report_path.exists():
        pins[str(report_path)] = comparison.digest(report_path)
    audit_verified = bool(audit and all(audit.get(k) is True for k in
        ('model_exact_except_zeroed_arm_bias', 'cpu_rng_equal', 'cuda_rng_equal'))
        and audit.get('control_initial_sha256') == pins[str(CONTROL/'100/train/J/initial.pt')])
    return dict(status='verified' if all(checks.values()) and audit_verified else 'unverified',
        checks=checks, native_initial_prior_audit=audit, native_audit_verified=audit_verified,
        original_bias12=original.tolist(), variant_bias12=b['model'][key][:12].tolist(),
        changed_model_tensors=[k for k in a['model'] if not equal(a['model'][k], b['model'][k])])


def resume_proof(base, pins):
    pair = load_pair(base/'100/train/J/final.pt', base/'200/train/J/initial.pt', pins)
    if pair is None:
        return dict(status='pending')
    a, b = pair
    keys = ('identity', 'model', 'actor_optimizer', 'value_optimizer', 'updates', 'cost_weight',
            'torch_rng', 'cuda_rng', 'numpy_rng', 'python_rng')
    checks = {key:equal(a[key], b[key]) for key in keys}
    for key in ('curriculum', 'sampler'):
        checks[key] = equal(a['metadata'].get(key), b['metadata'].get(key))
    return dict(status='verified' if all(checks.values()) else 'mismatch', checks=checks,
        source_updates=a['updates'], target_updates=b['updates'],
        scope='model/Adam/RNG/identity/curriculum/sampler exact; fresh episode resets are separate')


def raw_diagnostics(path):
    rows = list(comparison.analysis.iter_episode_rows(path))
    episodes = [row['episode'] for row in rows]
    names = ('wrong', 'missing', 'own_wrong_string_time', 'own_wrong_fret_time', 'other_higher_time',
             'geometry_time', 'loaded_target_time', 'body_load_time', 'facing_time', 'contact_time')
    return {name:sum(float(e['left_note_ledger']['values'][name][0]) for e in episodes)/len(episodes)
            for name in names}


def collect():
    pins = {str(Path(comparison.__file__)):comparison.digest(comparison.__file__),
            str(Path(comparison.analysis.__file__)):comparison.digest(comparison.analysis.__file__)}
    result = dict(schema='structured_press.no_alignment_prior_analysis.v1',
        updated_utc=datetime.now(timezone.utc).isoformat(), evaluations={}, training={},
        input_sha256=pins, pending=[], reset_pair_proof='not established by identical CLI/settings',
        interpretation='완료 평가 및 초기/재개 증거가 모두 갖추어지기 전 효과 판단 보류')
    for group, base in (('control', CONTROL), ('no_prior', VARIANT)):
        for label, suffix in (('initial', '100/evaluate_initial'), ('100', '100/evaluate_final'), ('200', '200/evaluate_final')):
            name = group+'_'+label
            row = comparison.collect_run(base/suffix, True, pins)
            if row['status'] == 'completed':
                report = comparison.read(base/suffix/'report.json')
                if any(report.get(k) for k in ('changed_inputs', 'missing_import_pins', 'cleanup_errors')):
                    raise ValueError('완료 평가 입력 무결성 실패: '+name)
                row['raw_note_means_s'] = raw_diagnostics(base/suffix)
                row['actual_reset_evidence'] = report.get('initial_conditions')
                row['checkpoint_sha256'] = report['checkpoint_sha256']
            result['evaluations'][name] = row
        for updates in ('100', '200'):
            result['training'][group+'_'+updates] = comparison.collect_run(base/updates/'train/J', False, pins)
    result['initial_proof'] = initial_proof(pins)
    result['resume_proof'] = {group:resume_proof(base, pins) for group, base in (('control', CONTROL), ('no_prior', VARIANT))}
    result['pending'] = [group+'/'+name for group in ('evaluations', 'training')
        for name, row in result[group].items() if row['status'] != 'completed']
    result['comparison_ready'] = (not result['pending'] and result['initial_proof']['status'] == 'verified'
        and all(row['status'] == 'verified' for row in result['resume_proof'].values()))
    if result['comparison_ready']:
        result['interpretation'] = '완료: 수치 비교 가능. 단일 seed·reset 비대응 비교이므로 인과·일반화 판단은 제한한다.'
    for path, expected in pins.items():
        if comparison.digest(path) != expected:
            raise ValueError('분석 중 입력 변경: '+path)
    result['analysis_script_sha256'] = comparison.digest(__file__)
    return result


def write(result):
    lines = ['# 팔 출력의 초기 정렬 bias 제거 비교', '', '집계 시각: '+result['updated_utc'], '',
        '기존 full33 fresh seed7과 팔 support_head.bias[:12]만 0으로 초기화한 변형을 비교한다. '
        '관측의 목표·기하 안내와 기존 초기 자세는 유지된다. 따라서 안내가 전혀 없는 학습이 아니다. '
        '학습은 64환경/H32/100회 블록, 고정 평균 정책 평가는 최초32개 episode이며 실패도 분모에 포함한다.', '',
        '| 조건 | 완료 상태 | 평가 분모 | 안전 성공 | clean 평균(초) | 최장 연속 평균(초) | 보상 | 비용 |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for name, row in result['evaluations'].items():
        m = row.get('metrics', {})
        lines.append('| {} | {} | {} | {} | {} | {} | {} | {} |'.format(name, row['status'],
            *[m.get(k) for k in ('count', 'safe_success', 'mean_safe_clean_s', 'mean_best_clean_s', 'mean_reward', 'mean_cost')]))
    lines += ['', '## 증거 통과 조건', '', '초기 직접 텐서/RNG 검증: `'+json.dumps(result['initial_proof'], ensure_ascii=False)+'`', '',
        'strict resume 검증: `'+json.dumps(result['resume_proof'], ensure_ascii=False)+'`', '',
        '동일 명령·설정은 실제 초기 q/hold가 짝지어 같다는 증거가 아니다. 기본 native 평가에 실제 reset 기록이 없으면 paired 비교라고 부르지 않는다. '
        '100회와 200회는 서로 다른 체크포인트 평가이며 100회 최고 성과와 200회 마지막 성과를 별도로 보존한다.', '', '## 각 보상·비용·오압현', '']
    for name, row in result['evaluations'].items():
        if row['status'] == 'completed':
            lines += ['- '+name+': 보상9항 `'+json.dumps(row['metrics']['reward_components_mean'], ensure_ascii=False)+'`; 비용 `'+json.dumps(row['metrics']['cost_components_mean'], ensure_ascii=False)+'`; raw note 초 `'+json.dumps(row['raw_note_means_s'], ensure_ascii=False)+'`']
    lines += ['', '학습 중 집계는 변화하는 확률 정책의 완료 episode이며 고정32환경 평가와 합산하지 않는다. '
        '전체 집계·LR·원시 SHA는 JSON에 저장한다.', '', '판단 가능: '+str(result['comparison_ready']), '',
        '대기: '+(', '.join(result['pending']) or '없음'), '', result['interpretation']]
    (ROOT/'NO_ALIGNMENT_PRIOR_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'NO_ALIGNMENT_PRIOR_ANALYSIS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    result = collect()
    write(result)
    print(json.dumps(dict(pending=result['pending'], comparison_ready=result['comparison_ready'])))
