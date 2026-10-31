"""저장된 완료 결과만 읽어 탐색 분산 축소의 대응 비교를 갱신한다. GPU 실행은 없다."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
os.environ.setdefault('MPLCONFIGDIR', '/tmp/variance_comparison_mpl')
from datetime import datetime, timezone
import json
from pathlib import Path
import analyze_all as analysis
from fixed_reset_evaluate import assert_same_initial_conditions

ROOT = Path(__file__).resolve().parent
VARIANT = ROOT/'variance_variant/runs'


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return analysis.sha(path)


def completed_status(report):
    if not report:
        return 'pending'
    return 'completed' if report.get('completed') else 'failed_or_running'


def lr_summary(path):
    """동일한 적응 규칙과 실제 사용된 학습률을 구별한다."""
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
    used = [row.get('structured_lr', {}).get('used_lr', row['actor_lr']) for row in rows]
    return dict(updates=len(rows), used_actor_lr=used,
        minimum_used_actor_lr=min(used) if used else None,
        maximum_used_actor_lr=max(used) if used else None,
        total_retries=sum(row.get('kl_retries', 0) for row in rows),
        analytic_kl=[row.get('analytic_kl') for row in rows],
        first_update={key:rows[0].get(key) for key in ('actor_lr','analytic_kl','kl_retries')} if rows else None)


def collect_run(path, evaluation, pins):
    """미완료 자료는 완결 에피소드 효과 비교에 넣지 않는다."""
    path = Path(path)
    item = dict(path=str(path), status='pending')
    report_path = path/'report.json'
    if not report_path.exists():
        return item
    report = read(report_path)
    pins[str(report_path)] = digest(report_path)
    item.update(status=completed_status(report), completed=report.get('completed'),
        failure=report.get('failure'), optimizer_updates=report.get('optimizer_updates'),
        committed_transitions=report.get('journal', {}).get('committed'), wall_s=report.get('wall_s'))
    if evaluation and report.get('completed'):
        if not (report.get('first_episode_per_env_per_batch') or report.get('first_episode_per_env')) or not report.get('failed_episodes_in_denominator'):
            raise ValueError('평가 최초 episode/실패 분모 계약 누락: '+str(path))
        source = Path(report['checkpoint'])
        source_sha = digest(source)
        if source_sha != report['checkpoint_sha256']:
            raise ValueError('평가 체크포인트 변경: '+str(source))
        pins[str(source)] = source_sha
        item['source_checkpoint_sha256'] = source_sha
        for key in ('optimizer_updates_in_evaluation',):
            if key in report and report[key] != 0:
                raise ValueError('평가에서 optimizer가 변경됨')
        item['initial_conditions'] = report.get('initial_conditions')
        item['reset_seed'] = report.get('reset_seed')
    if report.get('completed'):
        item['metrics'] = analysis.aggregate(path, 'index', evaluation)
        if evaluation and item['metrics']['count'] != 32:
            raise ValueError('평가 분모가 32가 아님')
        for name in ('episodes.jsonl', 'episode_metadata.json'):
            if (path/name).exists():
                pins[str(path/name)] = digest(path/name)
        if (path/'inputs_before.json').exists():
            snapshot = read(path/'inputs_before.json')
            for source_name, expected in snapshot.items():
                source = Path(source_name)
                if digest(source) != expected:
                    raise ValueError('봉인 입력 변경: '+str(source))
                pins[str(source)] = expected
            pins[str(path/'inputs_before.json')] = digest(path/'inputs_before.json')
    if not evaluation:
        events_path = path/'events.jsonl'
        if events_path.exists():
            item['kl_failure_events'] = [json.loads(line) for line in events_path.read_text().splitlines()
                if 'KLGuard' in line or 'kl_guard' in line or 'actor_retry' in line]
        item['lr'] = lr_summary(path/'learning_metrics.jsonl')
        item['learning_rule'] = report.get('settings', {}).get('ppo')
        parent = path.parent/'report.json'
        if parent.exists():
            outer = read(parent)
            item['initial_transfer_audit'] = outer.get('initial_transfer_audit')
            pins[str(parent)] = digest(parent)
    return item


def initial_proof(pins):
    """감사 플래그를 실제 CPU 체크포인트 텐서·RNG와 교차 확인한다."""
    import torch
    manifest = read(ROOT/'variance_variant/copy_manifest.json')
    paths = dict(source=Path(manifest['original_checkpoint']),
        copied=Path(manifest['copied_checkpoint']),
        control=ROOT/'index_B_seed7_v1/100/train/J/initial.pt',
        variant=VARIANT/'index_B_factor010_seed7/J/initial.pt')
    for path in paths.values():
        pins[str(path)] = digest(path)
    saved = {key:torch.load(str(path), map_location='cpu') for key,path in paths.items()}
    source = saved['source']['model']
    exact = all(set(saved[key]['model']) == set(source) and all(
        name == 'active_mask' or torch.equal(saved[key]['model'][name], value)
        for name,value in source.items()) for key in ('control','variant'))
    a,b=saved['control'],saved['variant']
    return dict(source_sha= pins[str(paths['source'])],
        copied_source_equal=pins[str(paths['source'])] == pins[str(paths['copied'])] == manifest['checkpoint_sha256'],
        all_initial_model_tensors_equal_source_except_active_mask=exact,
        control_cpu_torch_rng_equal=torch.equal(a['torch_rng'],b['torch_rng']),
        control_cuda_rng_equal=len(a['cuda_rng']) == len(b['cuda_rng']) and
            all(torch.equal(x,y) for x,y in zip(a['cuda_rng'],b['cuda_rng'])))


def adoption_gate(result, proof):
    """어느 증거라도 없거나 다르면 채택 준비 상태를 열지 않는다."""
    reasons=[]
    for name,row in result['training'].items():
        if row['status'] != 'completed': reasons.append(name+' 학습 미완료')
        settings=read(Path(row['path'])/'settings.json')
        if tuple(settings.get(k) for k in ('num_envs','horizon','updates')) != (64,32,100):
            reasons.append(name+' 블록 예산 불일치')
        if settings.get('structured_transfer',{}).get('sha256') != proof.get('source_sha'):
            reasons.append(name+' 원본 A100 SHA 불일치')
    for key in ('copied_source_equal','all_initial_model_tensors_equal_source_except_active_mask',
                'control_cpu_torch_rng_equal','control_cuda_rng_equal'):
        if proof.get(key) is not True: reasons.append(key+' 미검증')
    audit=result['training']['variant'].get('initial_transfer_audit') or {}
    for key in ('all_initial_model_tensors_equal_source_except_active_mask',
                'control_cpu_torch_rng_equal','control_cuda_rng_equal'):
        if audit.get(key) is not True: reasons.append('학습 보고서 '+key+' 미검증')
    if result['training']['control'].get('learning_rule') != result['training']['variant'].get('learning_rule'):
        reasons.append('학습률 규칙 불일치')
    for name,row in result['evaluations'].items():
        if row['status'] != 'completed' or row.get('metrics',{}).get('count') != 32:
            reasons.append(name+' 32환경 평가 미완료')
    for key in ('control_initial','variant_initial','variant_final'):
        if not result['paired_conditions'].get(key,{}).get('verified'):
            reasons.append(key+' 실제 초기값 대응 미검증')
    if reasons: return dict(ready=False,reasons=reasons,eligible_for_further_experiment=False)
    old,new,free=(result['evaluations'][k]['metrics'] for k in ('control_final','variant_final','variant_free_v9'))
    better=(new['safe_success'],new['mean_safe_clean_s']) > (old['safe_success'],old['mean_safe_clean_s'])
    return dict(ready=True,better_paired_B=better,free_v9_failure_zero=free['failure_episodes']==0,
        eligible_for_further_experiment=better and free['failure_episodes']==0,
        reason='단일 seed·단일 목표 실험이며 자동 생산 반영 근거가 아님')


def collect():
    pins = {}
    result = dict(schema='structured_press.variance_comparison.v1',
        updated_utc=datetime.now(timezone.utc).isoformat(), evaluations={}, training={}, smoke={},
        paired_conditions={}, input_sha256=pins, pending=[], adoption='experimental_only_production_unchanged',
        smoke_excluded_from_effect=True, reward_labels=analysis.TERMS)
    paths = dict(control_initial=ROOT/'paired_B_initial_seed4242', control_final=ROOT/'paired_B_100_seed4242',
        variant_initial=VARIANT/'eval_factor010_initial_fixed4242',
        variant_final=VARIANT/'eval_factor010_final_fixed4242',
        variant_free_v9=VARIANT/'eval_factor010_final_free_v9')
    for name, path in paths.items():
        result['evaluations'][name] = collect_run(path, True, pins)
    for name, path in dict(control=ROOT/'index_B_seed7_v1/100/train/J',
            variant=VARIANT/'index_B_factor010_seed7/J').items():
        result['training'][name] = collect_run(path, False, pins)
    for factor in ('005','010'):
        result['smoke'][factor] = collect_run(VARIANT/('smoke_factor'+factor+'_u2')/'J', False, pins)
    for name in ('control_initial', 'variant_initial', 'variant_final'):
        a, b = result['evaluations']['control_final'], result['evaluations'][name]
        if a['status'] == b['status'] == 'completed':
            result['paired_conditions'][name] = assert_same_initial_conditions(a, b)
    for category in ('evaluations','training'):
        result['pending'].extend(category+'/'+name for name,row in result[category].items() if row['status'] != 'completed')
    result['initial_checkpoint_proof'] = initial_proof(pins)
    result['adoption_evidence'] = adoption_gate(result, result['initial_checkpoint_proof'])
    for path, expected in pins.items():
        if digest(path) != expected:
            raise ValueError('집계 도중 입력 변경: '+path)
    result['analysis_script_sha256'] = digest(__file__)
    return result


def display(row):
    if 'metrics' not in row:
        return row['status'], '—', '—', '—'
    m = row['metrics']
    return str(m['count']), str(m['safe_success']), '{:.4f}'.format(m['mean_safe_clean_s']), str(m['failure_episodes'])


def write(result):
    lines = ['# 탐색 분산 축소 대응 비교', '', '완료 입력만 집계한 시각: '+result['updated_utc'], '',
        '원래 분포와 목표 손가락 4축 표준편차 ×0.1을 같은 A100 가중치에서 B100으로 이전해 비교한다. '
        '물리·성공 기준·보상·적응 학습률 **규칙**은 유지하지만, KL 재시도로 실제 사용 학습률은 다를 수 있다.', '',
        '## 고정 정책 평가', '', '| 구분 | 분모 | 안전 성공 | 실패를 0초로 처리한 평균 clean(초) | 실패 |',
        '|---|---:|---:|---:|---:|']
    for name,row in result['evaluations'].items():
        lines.append('| {} | {} | {} | {} | {} |'.format(name,*display(row)))
    lines += ['', 'B 초기/최종은 캡처한 32개 환경별 실제 초기 관절값·기하·목표·digest를 정확히 비교한다. '
        'seed가 같다는 사실만으로 대응을 주장하지 않는다. free-v9는 초기 분포 변경·지원 해제·33축 제어 조건이며 B 표와 별도로 해석한다.', '',
        '실제 초기 상태 대응 검증: '+str(all(row.get('verified') for row in result['paired_conditions'].values())
            and len(result['paired_conditions']) == 3)+' (32환경의 전체 q105·유지 목표를 정확히 비교). 세부 SHA는 JSON을 따른다.', '',
        '## 학습 중 확률 정책', '', '| 조건 | 완료 episode | 안전 성공 | 평균 safe clean(초) | 실패 |', '|---|---:|---:|---:|---:|']
    for name,row in result['training'].items():
        lines.append('| {} | {} | {} | {} | {} |'.format(name,*display(row)))
    lines += ['', '| 조건 | 실제 actor LR 최소~최대 | KL 재시도 합계 |', '|---|---|---:|']
    for name,row in result['training'].items():
        lr = row.get('lr', {})
        low, high = lr.get('minimum_used_actor_lr'), lr.get('maximum_used_actor_lr')
        interval = '—' if low is None else '{:.3g}~{:.3g}'.format(low, high)
        lines.append('| {} | {} | {} |'.format(name, interval, lr.get('total_retries', 0)))
    lines += ['', '초기 가중치와 CPU/CUDA 난수 상태의 실제 텐서 비교: `'+
        json.dumps(result['initial_checkpoint_proof'], ensure_ascii=False)+'`', '',
        '학습은 변화하는 확률 정책의 완료 episode이고, 평가는 고정 체크포인트의 결정적 최초 32 episode이다. '
        '미완료 episode를 성공으로 세지 않는다. 같은 기하·단일 검지 목표의 반복이며 새 목표 일반화 검증이 아니다.', '',
        '## 학습 중 완료 에피소드의 평균 보상과 비용', '', '| 항목 | 원래 B100 | 분산 ×0.1 B100 |', '|---|---:|---:|']
    for key,label in list(analysis.TERMS.items())+[('mean_cost','전체 비용'),('mean_reward_minus_cost','보상−비용')]:
        vals=[]
        for name in ('control','variant'):
            m=result['training'][name].get('metrics',{})
            value=m.get(key) if key.startswith('mean_') else m.get('reward_components_mean',{}).get(key)
            vals.append('—' if value is None else '{:.6f}'.format(value))
        lines.append('| {} | {} | {} |'.format(label,*vals))
    for name,row in result['training'].items():
        lines += ['', name+' 세부 비용(물리 실패 포함): `'+json.dumps(row.get('metrics',{}).get('cost_components_mean'),ensure_ascii=False)+'`']
    lines += ['', '## 사전 smoke와 해석 한계', '']
    for factor,row in result['smoke'].items():
        lines.append('- factor {}: 상태 {}, optimizer_updates={}, committed={}, wall_s={}; 효과 비교에서 제외.'.format(
            factor,row['status'],row.get('optimizer_updates'),row.get('committed_transitions'),row.get('wall_s')))
        if row.get('failure'):
            lines.append('  실패: '+row['failure']['type']+' — '+row['failure']['message']+'. 전체 원문은 JSON에 보존한다.')
    lines += ['', '작은 표준편차는 동일한 평균 이동에도 Gaussian KL을 크게 만든다. 기존 KL guard를 우회하지 않는다. '
        '재시도 하한 7.5e-6보다 낮게 시작하는 후속 실험은 하한도 일관되게 낮추어야 재시도가 학습률을 오히려 올리지 않는다. '
        '현재는 ×0.1이 같은 규칙으로 진행되는지를 확인하며 추가 LR 변경은 하지 않는다.', '',
        '대기 입력: '+', '.join(result['pending']) if result['pending'] else '대기 입력 없음.', '',
        '채택 판단: `'+json.dumps(result['adoption_evidence'],ensure_ascii=False)+'`', '',
        '추가 학습 전 B0의 유지 시간은 2.4339초로 ×0.1 학습 후의 2.3729초보다 높다. '
        '따라서 이번 결과는 같은 100회 추가 학습에서의 손실 완화이며 최고 모델 교체의 근거는 아니다. '
        '지원 없는 평가도 원래 A100의 2.4965초와 새 모델의 2.4227초를 구분해 기록한다.', '',
        '결정적 B 개선과 free-v9 실패 0을 추가 실험의 최소 조건으로 삼고 생산 코드는 유지한다. '
        '잠재 Gaussian 평균 μ 유지가 tanh 이후 기대 행동 평균 유지라는 뜻은 아니다.', '',
        '![대응 비교](variance_comparison_chart.png)', '',
        '입력별 SHA·원시 분모·9항 보상·비용·실패·가중치/RNG 감사는 동명 JSON에 기록한다.']
    (ROOT/'VARIANCE_COMPARISON.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'VARIANCE_COMPARISON.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    for name,color in (('control','tab:blue'),('variant','tab:orange')):
        rows=[result['evaluations'][name+'_'+kind] for kind in ('initial','final')]
        for ax,key in zip(axes,('safe_success','mean_safe_clean_s')):
            x=[i*100 for i,row in enumerate(rows) if 'metrics' in row]
            y=[row['metrics'][key] for row in rows if 'metrics' in row]
            ax.plot(x,y,'o-',label=name,color=color)
    axes[0].set(ylabel='Safe success count / 32',ylim=(-1,33))
    axes[1].set(ylabel='Mean safe clean (seconds)')
    for ax in axes:
        ax.set(xlabel='B PPO updates',xticks=[0,100],title='Paired deterministic B evaluation')
        ax.grid(alpha=.25); ax.legend()
    fig.savefig(ROOT/'variance_comparison_chart.png',dpi=160);plt.close(fig)


if __name__ == '__main__':
    result=collect();write(result)
    print(json.dumps(dict(pending=result['pending'],input_files=len(result['input_sha256']))))
