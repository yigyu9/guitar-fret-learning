"""기존 독립 비교가 GPU를 반환하면 성공 정책의 학습률 비교를 순차 수행한다.

각 조건은 동일 모델 가중치만 이전하고 새 Adam/RNG로 시작한다. 원래 실험과
실패 기록은 수정하지 않으며 모든 결과는 이 연구의 새 출력에만 저장한다.
"""
import argparse
from datetime import datetime, timedelta
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
BASE = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3'
TOOLS = BASE/'tools'
sys.path.insert(0, str(ORIGINAL/'tools'))
import study

RUNTIME = str(TOOLS/'stability_runtime.py')
SOURCE = ORIGINAL/'runs/study_v1/jobs/L_H32_s7_u800_train/J/final.pt'
CONTINUATION = ORIGINAL/'runs/continuation_v1/progress.json'


def update(state, out):
    """현재 블록과 확정한 결과만 기록하며 미완료 반복은 성공에 포함하지 않는다."""
    current = state.get('current_job') or {}
    metrics = Path(current.get('out', '/nonexistent'))/'J/learning_metrics.jsonl'
    partial = 0
    if metrics.is_file() and current.get('operation') == 'train':
        # 쓰는 중인 마지막 JSON 줄은 완료된 줄과 분리한다.
        for line in metrics.read_text().splitlines():
            try:
                json.loads(line)
                partial += 1
            except json.JSONDecodeError:
                pass
    state.update(updated_at=study.now(), current_partial_updates=partial)
    study.write(out/'progress.json', state)
    lines = ['# 자율 개선 진행', '', '- 갱신: '+state['updated_at'], '- 상태: '+state['status'],
             '- 현재: '+current.get('label', state.get('waiting_for', '없음')),
             '- 현재 블록 완료: '+str(partial), '- 실험 창 기준: '+state['budget_end'],
             '- 기준: 동일800회 모델 가중치 이전, 새 Adam/RNG; cap 외 조건 유지.', '',
             '[누적 결과](RESULTS.md)']
    (out/'진행상황.md').write_text('\n'.join(lines)+'\n')
    rows = ['# 성공 정책 보존: 학습률 비교', '',
            '이 표의 반복은 모델 가중치 이전 뒤 추가 반복이다. 원본800회의 strict resume가 아니다.', '',
            '|조건|seed|추가 반복|실행|환경수|A|B|AB|전체 유지|정시|A/B clean초|물리/손목|',
            '|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---|']
    for result in state['results'].values():
        m = result['metrics']
        rows.append(f"|{result['condition']}|{result['seed']}|{result['total']}|{result['mode']}|{m['episodes']}|{m['A']}|{m['B']}|{m['AB']}|{m['full_duration_pair']}|{m['on_time_with_previous_tail']}|{m['clean_s'][0]:.3f}/{m['clean_s'][1]:.3f}|{m['physical']}/{m['wrist']}|")
    rows += ['', '## 해석', '', *['- '+text for text in state.get('interpretations', [])]]
    if state.get('publications'):
        rows += ['', '## 실제 평균 정책 영상', '']
        rows += ['- ['+Path(item['path']).name+']('+item['path']+')' for item in state['publications']]
    if (out/'comparison.png').is_file():
        rows += ['', '![학습률 비교](comparison.png)']
    if state.get('error'):
        rows += ['', '중단: '+state['error']]
    (out/'RESULTS.md').write_text('\n'.join(rows)+'\n')


study.progress = update
# 원본 plot은 L/H/I/T만 그리므로 새 조건의 최종 그래프는 summarize에서 만든다.
study.plot = lambda state, out: None


def wait_for_original(state, out):
    state['status'] = 'waiting_for_native_preflight'
    proof_path=BASE/'validation/preflight.json'
    while True:
        proof=json.loads(proof_path.read_text()) if proof_path.exists() else {}
        state['waiting_for']='새 wrapper의 실제 GPU 학습·재개·평가·영상 검증'
        update(state,out)
        if proof.get('completed') is True:
            if (proof.get('source_unchanged') is not True or proof.get('preceding_driver_resumed') is not True
                    or len(proof.get('operations',[]))!=7
                    or any(row.get('exit_code')!=0 or row.get('completed') is not True for row in proof['operations'])):
                raise RuntimeError('native preflight 검증 불완전')
            study.check_sources(state)
            state['native_preflight']=str(proof_path)
            break
        if proof.get('completed') is False or time.time()-proof.get('paused_at',time.time())>2700:
            raise RuntimeError('native preflight 실패 또는 시간 초과')
        time.sleep(30)
    state['status'] = 'waiting_for_existing_comparison'
    while True:
        previous = json.loads(CONTINUATION.read_text())
        state['waiting_for'] = 'H128/초기분포/엄지 비교 GPU 반환'
        state['preceding_comparison'] = dict(status=previous['status'],
            updated_at=previous.get('updated_at'), current=(previous.get('current_job') or {}).get('label'))
        update(state, out)
        status = previous['status']
        if status in ('complete', 'complete_with_KL_failed_blocks'):
            study.check_sources(previous)
            break
        if status not in ('running',):
            raise RuntimeError('선행 비교 미완료: '+status+'; 자동 성공 처리하지 않음')
        pid = previous['driver_pid']
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            raise RuntimeError('선행 감독 실행이 사라짐; GPU에 다른 작업을 겹치지 않음')
        time.sleep(30)
    for _ in range(12):
        gpu = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).strip()
        if not gpu:
            state.pop('waiting_for', None)
            state['status'] = 'running'
            return
        time.sleep(5)
    raise RuntimeError('선행 비교 완료 후에도 GPU 사용 중')


def protected_kl(state, out, label, previous=None):
    job = state['jobs'][label]
    phase_path = Path(job['out'])/'J/report.json'
    outer_path = Path(job['out'])/'report.json'
    diagnostic_path = Path(job['out'])/'kl_failure.json'
    if not all(path.is_file() for path in (phase_path, outer_path, diagnostic_path)):
        return False
    phase, outer, diagnostic = (json.loads(path.read_text()) for path in (phase_path, outer_path, diagnostic_path))
    if ((phase.get('failure') or {}).get('type') != 'KLGuardError'
            or (outer.get('failure') or {}).get('type') != 'KLGuardError'
            or phase.get('lifecycle_verified') is not True
            or any(phase.get(k) != [] for k in ('changed_inputs', 'missing_import_pins', 'cleanup_errors'))
            or any(outer.get(k) for k in ('changed_inputs', 'missing_import_pins', 'cleanup_errors'))
            or diagnostic.get('finite') is not True):
        return False
    study.check_sources(state)
    state.setdefault('protected_failures', []).append(dict(label=label,
        report=str(phase_path), report_sha256=study.sha(phase_path), diagnostic=diagnostic,
        additional_committed_updates=phase.get('optimizer_updates'),
        last_valid_saved_checkpoint=str(previous) if previous else None,
        last_valid_saved_checkpoint_sha256=study.sha(previous) if previous else None))
    state['interpretations'].append(label+': 유한 KL 제한 중단. 미완료 블록을 실패로 보존하고 다른 독립 군 진행.')
    return True


def train_block(state, out, variant, seed, total, previous, previous_total):
    label = f'{variant}_s{seed}_u{total}_train'
    args = ['--updates', total-previous_total, '--seed', seed, '--num-envs', 64,
            '--size', 'large', '--horizon', 32, '--variant', variant]
    args += ['--resume', previous] if previous else ['--initialize-from', SOURCE]
    try:
        target = study.run(state, out, label, 'train', args, updates=total-previous_total, script=RUNTIME)
    except RuntimeError:
        if protected_kl(state, out, label, previous):
            return None
        raise
    return target/'J/final.pt'


def evaluate(state, out, variant, seed, total, checkpoint, mode='mean', count=32):
    return study.evaluate(state, out, variant, seed, total, checkpoint, mode,
                          count=count, script=RUNTIME)


def wilson(success, count):
    p = success/count
    z = 1.96
    denominator = 1+z*z/count
    centre = (p+z*z/(2*count))/denominator
    width = z*math.sqrt(p*(1-p)/count+z*z/(4*count*count))/denominator
    return [max(0., centre-width), min(1., centre+width)]


def summarize(state, out):
    """최종값과 최고값을 구분하고 두 seed를 통계적 독립환경128개로 과장하지 않는다."""
    means = [r for r in state['results'].values() if r['mode'] == 'mean']
    final = []
    for variant in ('control', 'conservative'):
        for seed in (7, 17):
            rows = [r for r in means if r['condition'] == variant and r['seed'] == seed and r['metrics']['episodes'] == 128]
            if rows:
                row = max(rows, key=lambda r: r['total'])
                m = row['metrics']
                final.append(dict(variant=variant, seed=seed, updates=row['total'],
                    AB_rate=m['AB']/128, full_hold_rate=m['full_duration_pair']/128,
                    on_time_rate=m['on_time_with_previous_tail']/128,
                    descriptive_wilson_AB=wilson(m['AB'],128), metrics=m, checkpoint=row['checkpoint']))
    by_variant = {variant: [r for r in final if r['variant'] == variant] for variant in ('control', 'conservative')}
    complete_pairs = (all(len(rows) == 2 for rows in by_variant.values())
        and all(row['updates'] >= 100 for row in final)
        and not state.get('protected_failures'))
    candidate = complete_pairs and all(r['AB_rate'] >= .9 and r['full_hold_rate'] >= .9
        and r['on_time_rate'] >= .9 and (r['metrics']['physical']+r['metrics']['wrist'])/128 <= .01
        for r in by_variant['conservative'])
    comparative = complete_pairs and all(
        next(r for r in by_variant['conservative'] if r['seed'] == seed)['AB_rate'] >
        next(r for r in by_variant['control'] if r['seed'] == seed)['AB_rate']
        for seed in (7,17))
    learning = {}
    for variant in ('control', 'conservative'):
        for seed in (7,17):
            logs = []
            for job in state['jobs'].values():
                if job['operation']=='train' and job['label'].startswith(f'{variant}_s{seed}_'):
                    path=Path(job['out'])/'J/learning_metrics.jsonl'
                    if path.is_file():
                        logs.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
            if not logs:continue
            def summary_values(values):
                finite=[float(v) for v in values if v is not None and math.isfinite(float(v))]
                return dict(count=len(finite),mean=sum(finite)/len(finite),min=min(finite),max=max(finite)) if finite else None
            learning[f'{variant}_s{seed}']=dict(committed_updates=len(logs),
                actor_lr=summary_values([r['actor_lr'] for r in logs]),
                analytic_kl=summary_values([r['analytic_kl'] for r in logs]),
                retries=sum(r['kl_retries'] for r in logs),
                latent_entropy=summary_values([r['diagnostics']['post_update']['latent_gaussian_entropy']['mean'] for r in logs]),
                reward_critic_EV=summary_values([r['diagnostics']['post_update']['critics']['reward']['explained_variance'] for r in logs]),
                training_reward_components={key:summary_values([r['reward_component_means'][key] for r in logs]) for key in logs[0]['reward_component_means']})
    study.write(out/'learning_diagnostics.json',learning)
    summary = dict(schema='success_retention.comparison.v1', final=final,
        complete_two_seed_pairs=complete_pairs, conservative_meets_90pct_all_three=bool(candidate),
        conservative_AB_better_in_both_seeds=bool(comparative),
        production_default_changed=False, learning_diagnostics=learning,
        scope='two training seeds, one middle-finger transition; environments share GPU simulator; Wilson descriptive only, not independent training replicates',
        protected_failures=state.get('protected_failures', []))
    study.write(out/'summary.json', summary)
    state['interpretations'].append('최종 두 seed 짝 비교 '+('완료.' if complete_pairs else '불완전; 실패 군을 분모에서 제거해 우세 선언하지 않음.'))
    state['interpretations'].append('보수군 90% 삼중 기준 '+('통과.' if candidate else '미통과.'))
    state['interpretations'].append('보수군 AB가 두 seed 모두 대조군보다 '+('높음.' if comparative else '높다고 확인되지 않음.'))
    state['interpretations'].append('기본 구현은 자동 교체하지 않으며 실제 평균 정책 성과·실패 포함 원장을 보존함.')

    report=['# 자율 개선 최종 분석', '', '## 비교의 범위', '',
        '동일한 최고800회 모델을 원래 계약으로 검증한 뒤 model-only 이전했다. 원래 학습의 strict resume가 아니며 두 군 모두 새 Adam·새 seed로 시작했다. 학습률 초기값/상한 외 보상·물리·GAE·std·목표 시간은 유지했다.', '',
        '학습 중 표본 성적과 영상의 평균 정책 성적을 구분한다. 아래128환경 값은 각 환경의 최초 에피소드와 실패를 포함한다. 두 난수는 훈련 복제2개이며128환경을 독립 훈련128개로 취급하지 않는다.', '',
        '## 마지막 저장 모델', '',
        '|조건|seed|추가 반복|AB|전체 유지|정시 전환|물리/손목|B clean초|',
        '|---|---:|---:|---:|---:|---:|---|---:|']
    for row in final:
        m=row['metrics'];report.append(f"|{row['variant']}|{row['seed']}|{row['updates']}|{m['AB']}/128|{m['full_duration_pair']}/128|{m['on_time_with_previous_tail']}/128|{m['physical']}/{m['wrist']}|{m['clean_s'][1]:.4f}|")
    report += ['', '## 판단', '', *['- '+text for text in state['interpretations']], '',
        '한 조건이라도 KL로 중단되면 마지막 유효 모델은 평가하되4군완주·개선확정으로 계산하지 않는다. 기존800회128환경 AB83.6%와 이번 model-only 대조군을 모두 참고한다. 조건당 최종128환경의 항별 보상·위치/방향/부하 탈락은 [원장](summary.json), 실제 LR/KL/entropy/9보상은 [학습 진단](learning_diagnostics.json)에 보존한다.', '',
        '## 기존 구조·엄지 비교', '',
        '|조건|seed|마지막 유효 반복|AB|B clean초|엄지 접촉 후보초|엄지 signed gap mm|',
        '|---|---:|---:|---:|---:|---:|---:|']
    previous=json.loads((out/'preceding_comparison.json').read_text()) if (out/'preceding_comparison.json').exists() else {}
    for row in previous.get('results',{}).values():
        if not row['condition'].endswith('_last_saved'):continue
        m=row['metrics'];contact=m.get('thumb_contact_candidate_s');gap=m.get('thumb_signed_gap_m')
        contact='미기록' if contact is None else f'{contact:.4f}'
        gap='미기록' if gap is None else f'{gap*1000:.3f}'
        report.append(f"|{row['condition']}|{row['seed']}|{row['total']}|{m['AB']}/{m['episodes']}|{m['clean_s'][1]:.4f}|{contact}|{gap}|")
    report += ['', 'H128은 긴 수집구간과 배치/optimizer횟수 변화를 함께 포함한다. 초기분포와 엄지21축은 각각 독립 조건이다. 엄지 접촉 후보는 실제 지지력 인증이 아니며 양수가 됐다는 이유로 기타 지지를 입증하지 않는다.', '',
        '## 다음 개선 방향', '',
        '보수적 학습률이 두 seed의 마지막 평균 동작과 전체 유지를 모두 개선하면 더 긴 반복과 새로운 목표에서 재검증한다. 일부 seed만 개선되면 기본값을 바꾸지 않고 학습 난수·목표 전환 일반화를 추가한다. 두 군 모두 무너지면 LR 단독 원인설은 지지되지 않으므로 H128/초기분포 성과와 패드 위치 탈락을 근거로 다음 독립 구조 비교를 설계한다. 엄지21축이 접촉 후보를 늘리지 못하면 도달 가능성과 초기 방향을 별도 native 검사하고 압현 성과와 혼합하지 않는다.', '',
        '[누적 평가·실제 영상](RESULTS.md) · [비교 그래프](comparison.png) · [봉인 확인](SOURCE_VERIFICATION.json)']
    (out/'ANALYSIS.md').write_text('\n'.join(report)+'\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for variant in ('control', 'conservative'):
        for seed in (7, 17):
            rows = sorted([r for r in means if r['condition'] == variant and r['seed'] == seed and r['metrics']['episodes'] == 32], key=lambda r: r['total'])
            if rows:
                axes[0].plot([r['total'] for r in rows], [100*r['metrics']['AB']/32 for r in rows], marker='o', label=f'{variant} seed{seed}')
    for i, row in enumerate(final):
        axes[1].bar(i, row['AB_rate']*100, color='steelblue' if row['variant']=='control' else 'orange')
    axes[1].set_xticks(range(len(final)))
    axes[1].set_xticklabels([f"{r['variant']}\ns{r['seed']} +{r['updates']}" for r in final], fontsize=8)
    axes[0].set_xlabel('Additional PPO updates; model-only initialization')
    axes[0].set_title('Mean-policy selection evaluation (32 envs)')
    axes[1].set_title('Last saved model confirmation (128 envs)')
    for axis in axes:
        axis.set_ylim(0, 103);axis.set_ylabel('AB achievement %');axis.grid(axis='y',alpha=.2)
    if axes[0].lines: axes[0].legend(fontsize=7)
    figure.savefig(out/'comparison.png', dpi=150);plt.close(figure)
    return summary


def render_selected(state, out):
    candidates = [r for r in state['results'].values() if r['mode']=='mean' and r['metrics']['episodes']==32]
    publications=[]
    public=ROOT/'docs/2026-11-02/압현실험/동영상'
    public.mkdir(exist_ok=True)
    selection=[]
    for variant in ('control','conservative'):
        rows=[r for r in candidates if r['condition']==variant]
        if not rows:continue
        best=max(rows,key=lambda r:(-(r['metrics']['physical']+r['metrics']['wrist']),r['metrics']['full_duration_pair'],r['metrics']['AB'],sum(r['metrics']['clean_s'])))
        last=max([r for r in rows if r['seed']==best['seed']],key=lambda r:r['total'])
        selection.append(('best',best))
        if last['checkpoint']!=best['checkpoint']:selection.append(('last',last))
    state['selected_models']=[dict(selection=kind,**row) for kind,row in selection]
    for selection_kind,row in selection:
        condition,seed,total=row['condition'],row['seed'],row['total']
        # 32환경 선택값과 128환경 확인값을 별도로 남긴다.
        label=f'{condition}_{selection_kind}_s{seed}_u{total}'
        evaluate(state,out,label,seed,total,row['checkpoint'],count=128)
        target=study.run(state,out,'render_'+label,'render',['--checkpoint',row['checkpoint'],'--num-envs',4],script=RUNTIME)
        for kind,view in (('hand','손확대'),('fullbody','전신')):
            source=target/(kind+'.mp4')
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height,nb_frames','-of','json',str(source)],text=True))
            if float(probe['format']['duration'])<=0:raise ValueError('빈 영상')
            name=f'16_성공유지학습률비교_{condition}_{selection_kind}_seed{seed}_추가{total}회_{view}.mp4'
            destination=public/name
            if not destination.exists():os.link(source,destination)
            if study.sha(source)!=study.sha(destination):raise ValueError('공개영상 불일치')
            publications.append(dict(path=str(destination),source=str(source),sha256=study.sha(source),probe=probe,checkpoint=row['checkpoint'],selection=selection_kind))
    state['publications']=publications
    study.write(out/'videos.json',publications)
    return publications


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--budget-hours',type=float,default=8.)
    args=parser.parse_args()
    out=args.out.resolve()
    if out.exists():raise FileExistsError(out)
    if not .5<=args.budget_hours<=12:raise ValueError('실험 창 .5~12시간')
    out.mkdir(parents=True)
    with (out/'study.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        def stop(signum,frame):raise KeyboardInterrupt('종료 신호 '+str(signum))
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
        seal=study.seal()
        seal.update({str(path.relative_to(ROOT)):study.sha(path) for path in TOOLS.glob('*.py')})
        deadline=datetime.now(study.KST)+timedelta(hours=args.budget_hours)
        state=dict(schema='success_retention.study.v1',status='initializing',started_at=study.now(),
            driver_pid=os.getpid(),budget_end=deadline.isoformat(timespec='minutes'),source_seal=seal,
            jobs={},results={},interpretations=[],source_checkpoint=str(SOURCE),source_sha256=study.sha(SOURCE))
        try:
            wait_for_original(state,out)
            study.check_sources(state)
            state['gpu_experiments_started_at']=study.now()
            study.write(out/'preceding_comparison.json',json.loads(CONTINUATION.read_text()))
            checkpoints={};totals={};blocked=set()
            for total in (50,100,150,200):
                if total>100:
                    # 일차4군100회는 완주. 추가는4군을 동일하게 마칠 여유가 있을 때만 시작한다.
                    if datetime.now(study.KST)+timedelta(minutes=35)>deadline or blocked:
                        state['interpretations'].append('시간/완료 균형을 위해 추가200회 비교는 시작하지 않음.')
                        break
                for seed in (7,17):
                    for variant in ('control','conservative'):
                        key=(variant,seed)
                        if key in blocked:continue
                        checkpoint=train_block(state,out,variant,seed,total,checkpoints.get(key),totals.get(key,0))
                        if checkpoint is None:
                            blocked.add(key);continue
                        checkpoints[key]=str(checkpoint);totals[key]=total
                        evaluate(state,out,variant,seed,total,checkpoint)
            for (variant,seed),checkpoint in checkpoints.items():
                evaluate(state,out,variant,seed,totals[(variant,seed)],checkpoint,count=128)
                evaluate(state,out,variant,seed,totals[(variant,seed)],checkpoint,mode='sampled')
            summarize(state,out)
            publications=render_selected(state,out)
            state['interpretations'].append('실제 평균 정책 영상 '+str(len(publications))+'개 검증·공개 완료.')
            state.update(status='complete_with_KL_failed_blocks' if blocked else 'complete',finished_at=study.now())
        except BaseException as error:
            state.update(status='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',error=repr(error),finished_at=study.now())
            raise
        finally:
            update(state,out)
            # 실패 시에도 이미 완료한 평가와 소스 상태를 원형대로 남긴다.
            try:
                study.check_sources(state)
                study.write(out/'SOURCE_VERIFICATION.json',dict(unchanged=True,count=len(state['source_seal']),checked_at=study.now()))
            except Exception as error:
                study.write(out/'SOURCE_VERIFICATION.json',dict(unchanged=False,error=str(error),checked_at=study.now()))


if __name__=='__main__':main()
