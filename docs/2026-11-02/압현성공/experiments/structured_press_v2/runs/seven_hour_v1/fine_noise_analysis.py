"""고정 A 모델의 목표 손가락 잡음 배율 진단을 검증하고 표·그래프로 정리한다."""
import os
for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[name] = '1'
os.environ.setdefault('MPLCONFIGDIR', '/tmp/structured_press_analysis_mpl')
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys
import research

ROOT, RUNTIME = research.ROOT, research.RUNTIME
FACTORS = dict(index=(0., .05, .1, .25, .5, 1.), middle=(0., .25, .5, 1.))


def sha(path):
    return research.digest(path)


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def pin(inputs, path, expected=None):
    path = Path(path).resolve()
    identifier = str(path)
    if identifier not in inputs:
        inputs[identifier] = sha(path)
    if expected is not None and inputs[identifier] != expected:
        raise ValueError('입력 SHA 불일치: '+identifier)
    return inputs[identifier]


def verify_evaluator_no_optimizer_steps(inputs):
    path = RUNTIME/'guitar_learning/training/finger_skill_runner.py'
    pin(inputs, path)
    tree = ast.parse(path.read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'evaluate_checkpoint')
    operations = [node.func.attr for node in ast.walk(function) if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                  and node.func.value.id == 'trainer']
    if 'load' not in operations or any(name in operations for name in ('update', '_update', 'save')):
        raise ValueError('평가기의 optimizer 비갱신 계약을 확인할 수 없음')
    return dict(source=str(path), sha256=inputs[str(path)], observed_trainer_calls=operations,
                optimizer_update_or_save_calls=False)


def verify_point(path, finger, factor, inputs, attestation=None):
    report_path = path/'report.json'; report_sha = pin(inputs, report_path)
    report = research.read(report_path)
    if report.get('schema') != 'diagnostic_sampling_override.v1' or report.get('scale') != factor:
        raise ValueError('진단 schema/배율 불일치')
    for name in ('completed', 'first_episode_per_env', 'failed_episodes_in_denominator',
                 'policy_mean_unchanged', 'model_parameters_unchanged', 'original_identity_validated_before_sampling'):
        if report.get(name) is not True:
            raise ValueError('평가 검증 항목 실패: '+name)
    if report.get('new_checkpoint_saved') is not False or list(path.glob('*.pt')):
        raise ValueError('새 학습 모델이 저장된 진단은 허용하지 않음')
    expected_mode = 'deterministic_mean' if factor == 0 else 'stochastic_latent_gaussian'
    if report['sampling_mode'] != expected_mode or report['original_saved_distribution'] != (factor == 1):
        raise ValueError('표본화 방식/저장 분포 표시 불일치')
    settings, contract = report['settings'], report['training_contract']
    config = settings['structured_press']
    expected_song = 'virtual_finger_v9_'+finger+'_s3_f'+('4' if finger == 'index' else '6')
    if (config['stage'] != 'A' or config['finger'] != finger or config['song'] != expected_song or
            config['initial_distribution']['v9_fraction'] != 0 or settings['num_envs'] != 32):
        raise ValueError('A 정렬 지원 조건·목표 손가락·32환경 계약 불일치')
    axes = list(range(17+4*('index', 'middle', 'ring', 'pinky').index(finger),
                      21+4*('index', 'middle', 'ring', 'pinky').index(finger)))
    if config['active_axes'] != axes or report['active_noise_axes'] != axes:
        raise ValueError('목표 손가락4축만 활성인 진단이 아님')
    checkpoint = Path(report['source_checkpoint'])
    pin(inputs, checkpoint, report['source_sha256'])
    if report['checkpoint_sha256'] != report['source_sha256']:
        raise ValueError('공식 평가와 진단 source SHA 불일치')
    pins_path = path/'inputs_before.json'; pin(inputs, pins_path)
    source_pins = research.read(pins_path)
    for identifier, expected in source_pins.items(): pin(inputs, identifier, expected)
    script_matches = [name for name, expected in source_pins.items()
                      if expected == report['diagnostic_script_sha256'] and name.endswith('.py')]
    if not script_matches: raise ValueError('원 진단 스크립트 봉인 누락')
    for name in ('episodes.jsonl', 'episode_metadata.json'): pin(inputs, path/name)
    if attestation:
        for field, name in (('report_sha256', 'report.json'), ('episodes_sha256', 'episodes.jsonl'),
                            ('metadata_sha256', 'episode_metadata.json')):
            if inputs[str((path/name).resolve())] != attestation[field]:
                raise ValueError('완료된 기존 batch의 산출물 SHA와 불일치')
    metrics = research.aggregate(path)  # compact 원장을 복원하고 중복·분모32·raw/report 수치를 검증한다.
    if str(RUNTIME) not in sys.path: sys.path.insert(0, str(RUNTIME))
    from guitar_learning.training.training_log_io import iter_episode_rows
    distributions = [row['episode']['structured_press']['initial_distribution'] for row in iter_episode_rows(path)]
    if distributions != ['aligned']*32:
        raise ValueError('고정 정렬 초기 기하 조건이 아님')
    return dict(finger=finger, factor=factor, path=str(path), report_sha256=report_sha,
        source_checkpoint=str(checkpoint), source_sha256=report['source_sha256'],
        settings_sha256=canonical_sha(settings), training_contract_sha256=canonical_sha(contract),
        metrics=metrics, sampling_mode=expected_mode, active_axes=axes,
        initial_distribution='aligned', prior_batch_hash_attestation=bool(attestation),
        current_optimizer_updates=0, new_checkpoint_saved=False,
        checkpoint_training_seed=report['checkpoint_training_seed'], sampling_rng=report['sampling_rng'])


def collect():
    inputs = {}; batch_path = ROOT/'diagnostic_summary.json'; pin(inputs, batch_path)
    batch = research.read(batch_path)
    if batch['status'] != 'completed' or batch['completed_jobs'] != 13 or len(batch['jobs']) != 13:
        raise ValueError('원래13개 진단 batch의 완료 증거가 필요함')
    if any(job['status'] != 'completed' for job in batch['jobs']):
        raise ValueError('원래 batch에 미완료 진단이 남아 있음')
    if len({str(Path(job['output']).resolve()) for job in batch['jobs']}) != 13:
        raise ValueError('원래 batch의 서로 다른 진단 경로13개가 필요함')
    attestations = {Path(job['output']).name:job for job in batch['jobs']}
    batch_validation = []
    for job in batch['jobs']:
        path = Path(job['output'])
        for field, name in (('report_sha256', 'report.json'), ('episodes_sha256', 'episodes.jsonl'),
                            ('metadata_sha256', 'episode_metadata.json')):
            pin(inputs, path/name, job[field])
        report = research.read(path/'report.json')
        pin(inputs, job['source']['checkpoint'], job['source']['sha256'])
        if report['checkpoint_sha256'] != job['source']['sha256']:
            raise ValueError('원래 batch의 모델 SHA 불일치')
        pins_path = path/'inputs_before.json'; pin(inputs, pins_path)
        for identifier, expected in research.read(pins_path).items(): pin(inputs, identifier, expected)
        metrics = research.aggregate(path)
        if any(metrics[key] != job['metrics'][key] for key in ('count', 'safe_success', 'failure_episodes', 'mean_safe_clean_s')):
            raise ValueError('원래 batch의 원시 재집계 수치 불일치')
        if job['kind'] == 'free_v9' and report.get('evaluation_stage') != 'free_v9':
            raise ValueError('자유 평가 조건 표시 불일치')
        batch_validation.append(dict(label=job['label'], kind=job['kind'], metrics=metrics,
                                     report_sha256=job['report_sha256']))
    evaluator = verify_evaluator_no_optimizer_steps(inputs)
    points = []
    for finger, factors in FACTORS.items():
        group = []
        for factor in factors:
            label = 'noise_{}_scale{:03d}'.format(finger, round(factor*100))
            group.append(verify_point(ROOT/'probes'/label, finger, factor, inputs, attestations.get(label)))
        for key in ('source_sha256', 'source_checkpoint', 'settings_sha256', 'training_contract_sha256',
                    'checkpoint_training_seed', 'sampling_rng'):
            if len({point[key] for point in group}) != 1:
                raise ValueError('동일 모델·조건을 유지한 배율 비교가 아님: '+finger+'/'+key)
        points.extend(group)
    previous = ROOT/'FINE_NOISE_REPORT.json'
    if previous.is_file():
        for name, expected in research.read(previous)['input_sha256'].items():
            if name in inputs and inputs[name] != expected:
                raise ValueError('이전 분석 이후 원 진단 입력이 변경됨: '+name)
    for name, expected in inputs.items():
        if sha(name) != expected: raise ValueError('분석 도중 입력 변경: '+name)
    return dict(schema='structured_press.fine_noise_analysis.v1', completed=True,
        updated_utc=datetime.now(timezone.utc).isoformat(), points=points, input_sha256=inputs,
        analysis_script_sha256=sha(__file__), evaluator_no_optimizer_updates=evaluator,
        raw_episode_denominator_per_point=32, selected_noise_points=len(points), total_selected_episodes=len(points)*32,
        original_batch_validation=batch_validation, total_validated_unique_diagnostic_episodes=15*32,
        no_new_training=True, latent_gaussian_mean_unchanged=True,
        expected_tanh_action_mean_unchanged_claimed=False,
        initial_condition_scope='A의 같은 정렬 기하와 같은 목표를32환경에서 반복; 기하/목표 일반화 아님',
        comparison_scope='손가락별 동일 체크포인트에서 잡음 배율만 비교; 학습 중 정책 변화 없음')


def plot(result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
    factors = [0, .05, .1, .25, .5, 1]
    for finger, color in (('index', '#2474b5'), ('middle', '#ce6b19')):
        rows = {point['factor']:point for point in result['points'] if point['finger'] == finger}
        success = [rows[f]['metrics']['safe_success']/32 if f in rows else float('nan') for f in factors]
        clean = [rows[f]['metrics']['mean_safe_clean_s'] if f in rows else float('nan') for f in factors]
        label = 'Index: string3/fret4' if finger == 'index' else 'Middle: string3/fret6'
        for axis, values in zip(axes, (success, clean)):
            axis.plot(range(6), values, 'o-', color=color, label=label, linewidth=2)
        for i, factor in enumerate(factors):
            if factor in rows:
                count = rows[factor]['metrics']['safe_success']
                axes[0].annotate(str(count)+'/32', (i, success[i]), xytext=(0, 10 if finger == 'index' else -17),
                                 textcoords='offset points', ha='center', fontsize=8, color=color)
    for axis, title, ylabel in zip(axes, ('Safe note achievement', 'Clean contact time'),
            ('Safe successes / 32', 'Mean clean seconds (failed episodes = 0)')):
        axis.set(title=title, ylabel=ylabel, xlabel='Sigma multiplier (0 = deterministic; equally spaced categories)')
        axis.set_xticks(range(6)); axis.set_xticklabels(['0', '.05', '.10', '.25', '.50', '1.00'])
        axis.grid(alpha=.25); axis.legend(fontsize=8, loc='upper right')
    axes[0].set_ylim(-.08, 1.12)
    axes[1].set_ylim(bottom=0)
    fig.suptitle('Fixed A policies, aligned/support condition; middle .05/.10 not measured', fontsize=11)
    fig.savefig(ROOT/'chart.png', dpi=170)
    plt.close(fig)


def document(result):
    lines = ['# 고정 A 모델의 미세 탐색 잡음 진단', '', '갱신 UTC: '+result['updated_utc'], '',
        '검지·중지 각각 동일 체크포인트의 목표 손가락4축 latent Gaussian 표준편차 배율만 바꾼 결과다. '
        '새 학습을 진행한 실험이 아니며 정책이 학습 도중 바뀌는 효과를 제거한 고정 모델 진단이다. '
        'scale0은 결정적 평균 행동이고 scale1은 저장된 Gaussian 분포이다.', '',
        '|손가락|sigma 배율|안전 달성 /32|실패 /32|clean 평균(실패0점,초)|최장 연속 clean의 에피소드 평균(초)|',
        '|---|--:|--:|--:|--:|--:|']
    for point in result['points']:
        m = point['metrics']
        lines.append('|{}|{}|{}|{}|{:.6f}|{:.6f}|'.format('검지' if point['finger']=='index' else '중지',
            point['factor'], m['safe_success'], m['failure_episodes'], m['mean_safe_clean_s'], m['mean_best_clean_s']))
    index = {p['factor']:p['metrics'] for p in result['points'] if p['finger']=='index'}
    middle = {p['factor']:p['metrics'] for p in result['points'] if p['finger']=='middle'}
    lines += ['', '![잡음 배율 비교](chart.png)', '', '## 해석', '',
        '검지의 안전 달성은 결정적 평가 {}/32, .05배 {}/32, .1배 {}/32, .25배 {}/32였다. '
        '중지는 .25배 {}/32, .5배 {}/32, 저장 잡음1배 {}/32였다. '
        '이 고정 모델에서 잡음 배율에 따른 압현 유지 차이를 확인한 결과다. '
        '검지3번줄4프렛과 중지3번줄6프렛의 기하·목표가 다르므로 손가락 자체의 우열로 해석하지 않는다.'.format(
            index[0.]['safe_success'], index[.05]['safe_success'], index[.1]['safe_success'], index[.25]['safe_success'],
            middle[.25]['safe_success'], middle[.5]['safe_success'], middle[1.]['safe_success']), '',
        '검지 .05배의 clean 평균은 {:.6f}초로 결정적 {:.6f}초와 가까웠다. '
        '이 결과는 낮은 잡음을 학습 실험으로 검토할 근거이며, 낮은 잡음으로 학습하면 더 좋아진다는 결론은 아니다. '
        '그 학습 효과는 동일 A100에서 같은 seed·갱신 예산으로 시작하는 별도 paired 학습 비교로 확인해야 한다.'.format(
            index[.05]['mean_safe_clean_s'], index[0.]['mean_safe_clean_s']), '',
        '이 진단에서 보존한 평균은 latent Gaussian 평균 μ이다. 확률적 실행 행동의 평균 E[tanh(z)]는 '
        '일반적으로 tanh(μ)와 다르고 분산에 따라 달라질 수 있다. 따라서 실행 행동의 기댓값까지 동일했다고 주장하지 않는다.', '',
        '## 검증과 범위', '',
        '원래13개 batch와 추가2개를 합친 고유15조건·480개 원시 에피소드를 복원해 조건마다 env0~31의 첫 에피소드가 정확히 한 번씩 존재하고 '
        '실패도 분모32에 포함됐음을 검증했다. 이 중 표·그래프에 사용한 잡음 진단은10조건·320개다. '
        '원래13개 batch 전체의 완료 및 기존 report/episodes/metadata SHA와 원시 재집계 수치를 대조했다. '
        '추가 .05/.1 진단은 현재 원시 산출물 SHA를 새 분석 입력 스냅샷으로 봉인했다. '
        '각 조건의 inputs_before.json에 기록된 원본 코드·설정·체크포인트 SHA도 현재 파일과 대조했다.', '',
        '공식 평가 함수의 AST에서 trainer.load 호출과 optimizer update/save 호출 부재를 확인했다. '
        '진단 보고서의 new_checkpoint_saved=False, 원본 source SHA 및 동일 설정/물리 계약도 검증했다. '
        '원래13개 batch에는 별도의 자유 v9 평가5개가 있으나 이 표와 그래프에는 혼합하지 않는다.', '',
        'A의 정렬·지원 조건이며 같은 기하와 같은 목표를32환경에서 반복한 결과다. '
        '새 프렛/줄/곡이나 새로운 초기 기하에 대한 일반화 성과가 아니다. '
        '저장 체크포인트의 RNG 복원을 재사용한 단일 난수 상태 진단으로 여러 seed에서의 재현성과는 구분한다. '
        '중지의 .05/.1은 측정하지 않았으며 그래프의 빈 구간은 미측정이다.', '', '## 원본 모델', '']
    for finger in FACTORS:
        point = next(p for p in result['points'] if p['finger']==finger)
        lines += ['- '+('검지' if finger=='index' else '중지')+': `'+point['source_checkpoint']+'`',
                  '  SHA256: `'+point['source_sha256']+'`']
    lines += ['', '모든 입력 SHA·조건별 원시 집계와 분모·평가기 소스 검증은 FINE_NOISE_REPORT.json에 기록했다.']
    (ROOT/'FINE_NOISE_REPORT.md').write_text('\n'.join(lines)+'\n')


def main():
    result = collect()
    research.write(ROOT/'FINE_NOISE_REPORT.json', result)
    plot(result); document(result)
    print(json.dumps(dict(completed=True, conditions=len(result['points']),
        raw_episodes=result['total_selected_episodes'], validated_input_files=len(result['input_sha256'])), ensure_ascii=False))


if __name__ == '__main__':
    main()
