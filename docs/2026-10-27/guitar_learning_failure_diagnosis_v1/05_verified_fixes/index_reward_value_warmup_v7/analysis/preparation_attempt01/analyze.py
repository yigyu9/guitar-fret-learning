"""Read-only V6/V7 comparison of completed artifacts; no model imports or forwards."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
V7 = HERE.parent
V6 = V7.parent/'index_cost_prior_zero_v6'
HELPER = V6/'analysis/analyze.py'
HELPER_SHA = '3b5a5d7ed944e865ffc5b8f7d7a5af5da8fe756dca3882221de6dc9b54b38eec'
SCHEMAS = {V6:'diagnostic.cost_prior_zero.v6',V7:'diagnostic.reward_value_warmup.v7'}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write(path,value): Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def require(ok,message):
    if not ok: raise ValueError(message)


def helper():
    require(sha(HELPER) == HELPER_SHA,'Frozen helper SHA changed')
    spec = importlib.util.spec_from_file_location('warmup_v7_frozen_v6_analysis',HELPER)
    value = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = value;spec.loader.exec_module(value)
    return value


def cases(root):
    return [(0,False,root/'runs/fit_deterministic',root/'runs/fit/fit.pt'),
            (0,True,root/'runs/fit_stochastic',root/'runs/fit/fit.pt')]+[
        (update,stochastic,root/('runs/ppo_eval_%06d_%s'%(update,'stochastic' if stochastic else 'det')),
         root/'runs/ppo'/('final.pt' if update == 300 else 'evaluation_%06d.pt'%update))
        for update,stochastic in [(50,False),(100,False),(150,False),(200,False),(250,False),(300,False),(300,True)]]


def required_files():
    paths = {HELPER,HERE/'analyze.py',HERE/'cpu_check.py',HERE/'cpu_verification.json',HERE/'PLAN.md'}
    for root in (V6,V7):
        paths.update(root/'runs/ppo'/name for name in ('learning_report.json','inputs_before.json',
            'inputs_after.json','metrics.jsonl','episodes.jsonl','final.pt'))
        for update,stochastic,folder,checkpoint in cases(root):
            paths.add(checkpoint)
            paths.update(folder/name for name in ('learning_report.json','inputs_before.json','inputs_after.json',
                'acceptance.json','evaluation_freeze.json','evaluation.json','learning_control_env0.npz',
                'trace_metadata.json','training_contract.json','settings.json'))
    paths.update(V7/'runs/fit'/name for name in ('learning_report.json','inputs_before.json','inputs_after.json',
        'actor_tensor_equality.json','warmup_report.json','value_predictions.npz','fit.pt'))
    paths.add(V7/'initial_comparison/verification.json')
    paths.add(V7/'actual_initial_review.json')
    return paths


def status():
    missing = sorted(str(p) for p in required_files() if not p.is_file())
    return dict(final_ready=not missing,pending=bool(missing),missing=missing,new_GPU_runs=0,new_NN_runs=0,scope='Artifact presence only; independent review gate is separate')


def prepare():
    require(sha(HELPER) == HELPER_SHA,'Helper SHA mismatch')
    paths = [HERE/name for name in ('PLAN.md','analyze.py','cpu_check.py','cpu_verification.json')]+[HELPER]
    write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins={str(p):sha(p) for p in paths},
        scope='Read-only final artifacts only; all18 evaluations and both PPO300 required; no new NN/native runs'))
    return status()


def gate():
    seal,review = read(HERE/'preparation_seal.json'),read(HERE/'review.json')
    require(seal['independent_review'] == 'passed_no_findings' and review['verdict'] == 'PASS' and not review['findings'],'Independent review required')
    require(all(sha(p) == digest for p,digest in seal['input_pins'].items()),'Prepared inputs changed')
    require(all(sha(p) == digest for p,digest in review['reviewed_sha256'].items()),'Reviewed sources changed')
    require(all(review['reviewed_sha256'].get(p) == digest for p,digest in seal['input_pins'].items()
                if Path(p).name not in ('review.json','REVIEW.md')),'Reviewed prepared map mismatch')
    return seal['input_pins']


def collect_pins(paths):
    pins = {str(p.resolve()):sha(p) for p in paths}
    # Read source-run pin declarations before processing numerical arrays.
    audits = [p for p in paths if p.name == 'inputs_after.json']
    for path in audits:
        after = read(path)
        require(after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources'],'Source input audit failed')
        require(read(path.parent/'inputs_before.json') == after['input_pins'],'Source before/after map changed')
        for name,digest in after['input_pins'].items():
            require(sha(name) == digest,'Source input SHA mismatch: '+name)
            require(name not in pins or pins[name] == digest,'Conflicting input SHA')
            pins[name] = digest
    initial_review = read(V7/'actual_initial_review.json')
    require(initial_review['verdict'] == 'PASS' and not initial_review['findings'],'Initial actual review required')
    for name,digest in initial_review['reviewed_sha256'].items():
        require(sha(name) == digest,'Initial actual review SHA changed');pins[name] = digest
    comparison = read(V7/'initial_comparison/verification.json')
    for name,digest in comparison['input_sha256'].items():
        require(sha(name) == digest,'Initial comparison input changed');pins[name] = digest
    return pins


@contextmanager
def lifecycle(out,pins):
    out = Path(out);out.mkdir(parents=True,exist_ok=False)
    write(out/'inputs_before.json',pins)
    failure = None
    try:
        require(all(sha(p) == h for p,h in pins.items()),'Initial input mismatch')
        yield out
    except BaseException as error:
        failure = dict(type=type(error).__name__,message=str(error));raise
    finally:
        changed = []
        for path,digest in pins.items():
            try:
                if sha(path) != digest: changed.append(path)
            except OSError: changed.append(path)
        verification = dict(completed=failure is None and not changed,failure=failure,changed_inputs=changed,
            input_sha256=pins,new_GPU_runs=0,new_NN_runs=0,training_steps=0,evaluations=18,
            output_sha256={p.name:sha(p) for p in out.iterdir() if p.name in
                ('analysis.json','RESULTS.md','performance.png','nine_rewards.png','cost_and_KL.png')})
        try: write(out/'verification.json',verification)
        except BaseException as error:
            if failure is None: raise
            print('Secondary analysis verification error: '+repr(error),file=sys.stderr)
        if failure is None and changed: raise RuntimeError('Analysis input mutation')


def validate_report(report,root,updates,h):
    h.audit_report(report,updates)
    require(report['schema'] == SCHEMAS[root],'Wrong run schema')
    require(report['fit_steps'] == 0,'New actor fitting during PPO/evaluation')
    if updates == 0: require(report['initialization_fit_steps'] == 1000,'Missing actorfit1000 provenance')


def warmup_evidence():
    status = read(V7/'runs/fit/learning_report.json')
    require(status['schema'] == SCHEMAS[V7] and status['completed'] and status['closed'] and not status['failure'] and not status['cleanup_errors'],'Warmup run failed')
    require(status['fit_steps'] == status['value_warmup_steps'] == 1000 and status['PPO_updates'] == status['native_runs'] == 0,'Wrong warmup provenance')
    report = read(V7/'runs/fit/warmup_report.json')
    require(report['accepted'] is True and report['steps'] == 1000 and report['batch_size'] == 512,'Warmup incomplete')
    require(report['changed_tensor_names'] and all(n.startswith(('value_encoder.','reward_critic.')) for n in report['changed_tensor_names']),'Warmup changed other tensors')
    require(report['actor_std_costhead_exact'] and report['global_RNG_exact'] and report['temporary_optimizer_discarded'],'Warmup invariants failed')
    require(report['after']['holdout']['overall']['MSE'] < report['before']['holdout']['overall']['MSE'],'Holdout did not improve')
    equality = read(V7/'runs/fit/actor_tensor_equality.json')
    require(set(equality) == {'fresh.pt','fit.pt'} and all(v['all71tensors_exact'] for v in equality.values()),'Fresh actor reproduction failed')
    comparison = read(V7/'initial_comparison/verification.json')
    for mode in ('fit_deterministic','fit_stochastic'):
        e = comparison[mode]
        require(e['attempts'] == 128 and e['note_attempts'] == 384 and
            e['full_episode_ledger_nine_rewards_and_env0_physical_NN_trace_exact'],'Initial physical comparison failed')
    worsened = {}
    for split in ('train','holdout'):
        worsened[split] = [phase for phase,before in report['before'][split]['phases'].items()
                          if report['after'][split]['phases'][phase]['MSE'] > before['MSE']]
    return dict(warmup=report,initial_actor=equality,initial_behavior=comparison,
        phases_with_MSE_worsening=worsened,scope='Same-scene env0..95 train/env96..127 holdout; fit12buffers only. Realized MC is not conditional expected-value ground truth.')


def finite_tree(value):
    if isinstance(value,float): return math.isfinite(value)
    if isinstance(value,dict): return all(finite_tree(v) for v in value.values())
    if isinstance(value,list): return all(finite_tree(v) for v in value)
    return True


def summarize(root,wrapper):
    h = wrapper.h
    evaluations = []
    for case in cases(root):
        update,stochastic,folder,checkpoint = case
        validate_report(read(folder/'learning_report.json'),root,0,h)
        # h.V5 selects the unchanged settlement audit; every data path comes from case.
        result = h.evaluation(h.V5,case)
        if result['env0_trace']['A_audible_endpoints'] == 0:
            result['env0_trace']['decoded_goal_mean_deg4'] = None
            result['env0_trace']['actual_q_mean_deg4'] = None
            result['env0_trace']['missing_scope'] = 'No A-audible endpoints in this first attempt; failures remain in128 denominator'
        if root == V7:
            require(read(folder/'settings.json') == read(V7/'runs/fit_deterministic/settings.json'),'V7 source settings changed')
        require(read(folder/'training_contract.json')['diagnostics']['cost_prior']['schema'] == 'diagnostic.cost_prior_zero.v6','Cost prior changed')
        if root == V7:
            require(read(folder/'training_contract.json')['diagnostics']['reward_value_warmup']['steps'] == 1000,'Wrong warmup contract')
        require(finite_tree(result),'Nonfinite evaluation summary')
        evaluations.append(result)
    folder = root/'runs/ppo'
    validate_report(read(folder/'learning_report.json'),root,300,h)
    metrics,episodes = h.rows(folder/'metrics.jsonl'),h.rows(folder/'episodes.jsonl')
    require(episodes,'No completed training episodes')
    require(all(finite_tree(m) for m in metrics),'Nonfinite metrics')
    require([m['update'] for m in metrics] == list(range(1,301)),'Incomplete PPO300')
    require(all(m['transitions'] == 4096 and m['total_transitions'] == m['update']*4096 for m in metrics),'Wrong transition budget')
    training = h.summarize(episodes,require_settlement=True)
    completed_steps = sum(e['steps'] for e in episodes)
    require(0 <= completed_steps <= 300*4096,'Invalid completed/open transition accounting')
    training.update(total_transitions=300*4096,completed_episode_steps=completed_steps,
        open_transitions=300*4096-completed_steps,cost_proof=wrapper.cost_proof(metrics,training['cost_sum']))
    KL = dict(retries=sum(m['kl_retries'] for m in metrics),actual_actor_lr_range=[min(m['actor_lr'] for m in metrics),max(m['actor_lr'] for m in metrics)],
        attempts=[{k:m[k] for k in ('update','kl_retries','actor_lr','analytic_kl','max_attempted_kl')} for m in metrics])
    return dict(evaluations=evaluations,training=training,metrics=metrics,KL=KL)


def plots(result,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes = plt.subplots(2,3,figsize=(13,7),sharex=True)
    for version,style in [('V6','--'),('V7','-')]:
        det = [e for e in result[version]['evaluations'] if not e['stochastic']]
        x = [e['update'] for e in det]
        curves = [('All3 /128 (%)',[e['all3']/1.28 for e in det]),('Joint /128 (%)',[e['joint']/1.28 for e in det]),
            ('A released /128 (%)',[e['A_released']/1.28 for e in det]),('A clean (%)',[e['per_note'][0]['clean_mean']*100 for e in det]),
            ('A wrong (%)',[e['per_note'][0]['wrong_mean']*100 for e in det]),('A missing (%)',[e['per_note'][0]['missing_mean']*100 for e in det])]
        for ax,(title,y) in zip(axes.flat,curves):
            ax.plot(x,y,style,marker='o',label=version);ax.set_title(title);ax.grid(alpha=.2);ax.legend();ax.set_xlabel('PPO updates')
    fig.suptitle('Original128 fixed-checkpoint attempts; failures retained');fig.tight_layout();fig.savefig(out/'performance.png',dpi=160);plt.close(fig)
    fig,axes = plt.subplots(3,3,figsize=(13,9),sharex=True)
    for ax,key in zip(axes.flat,result['V6']['evaluations'][0]['reward_components_mean']):
        for version,style in [('V6','--'),('V7','-')]:
            det = [e for e in result[version]['evaluations'] if not e['stochastic']]
            ax.plot([e['update'] for e in det],[e['reward_components_mean'][key] for e in det],style,marker='.',label=version)
        ax.set_title(key,fontsize=9);ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Nine reward means / original128 attempts');fig.tight_layout();fig.savefig(out/'nine_rewards.png',dpi=160);plt.close(fig)
    fig,axes = plt.subplots(2,4,figsize=(16,7),sharex=True)
    for version,style in [('V6','--'),('V7','-')]:
        metrics = result[version]['metrics'];x = [m['update'] for m in metrics]
        curves = [('Mean failure cost',[m['mean_failure_cost'] for m in metrics]),('Cost advantage std',[m['diagnostics']['advantages']['cost_raw']['std'] for m in metrics]),
            ('Cost value mean',[m['diagnostics']['post_update']['critics']['cost']['value']['mean'] for m in metrics]),('Cost target mean',[m['diagnostics']['post_update']['critics']['cost']['target']['mean'] for m in metrics]),
            ('Cost loss (last)',[m['cost_value_loss'] for m in metrics]),('Actual actor LR',[m['actor_lr'] for m in metrics]),('Analytic KL',[m['analytic_kl'] for m in metrics]),('KL retries',[m['kl_retries'] for m in metrics])]
        for ax,(title,y) in zip(axes.flat,curves):
            ax.plot(x,y,style,label=version);ax.set_title(title,fontsize=9);ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(out/'cost_and_KL.png',dpi=160);plt.close(fig)


def results(result,out):
    lines = ['# V7 reward 가치망 사전 보정과 V6 비교','',
        '고정기타·검지4축·원3음 view354tick·seed7의 비교다. 원128시도·384음에 실패를 포함한다. 초기 고정/확률128 및 50회간격6고정·마지막확률128을 검사하며 마지막300을 점수와 무관하게 보고한다.','',
        '|버전/회차/모드|A/B7/B8 달성|all3|A 해제|joint|실패|평균보상|','|---|---|---:|---:|---:|---:|---:|']
    for version in ('V6','V7'):
        for e in result[version]['evaluations']:
            lines.append('|%s/%d/%s|%s|%d|%d|%d|%d|%.6f|'%(version,e['update'],'확률' if e['stochastic'] else '고정',
                '/'.join(str(n['achieved']) for n in e['per_note']),e['all3'],e['A_released'],e['joint'],e['failures'],e['reward_mean']))
    lines += ['','![성과](performance.png)','','|버전/회차/모드/음|clean|wrong|missing|최장clean(s)|','|---|---:|---:|---:|---:|']
    for version in ('V6','V7'):
        for e in result[version]['evaluations']:
            for n in e['per_note']:
                lines.append('|%s/%d/%s/%d|%.5f|%.5f|%.5f|%.5f|'%(version,e['update'],'확률' if e['stochastic'] else '고정',n['source_index'],n['clean_mean'],n['wrong_mean'],n['missing_mean'],n['best_clean_streak_mean_s']))
    lines += ['','![9보상](nine_rewards.png)','','![비용·KL·실제학습률](cost_and_KL.png)','']
    for version in ('V6','V7'):
        t,k = result[version]['training'],result[version]['KL']
        lines.append('%s: PPO전이 %d, 완료episode에 속한 전이 %d, 아직 열린episode 전이 %d. 완료episode의 비용합 %.6f와 매 PPO창 비용평균을 구분한다. KL재시도합 %d, 실제actor LR범위 %.9g~%.9g.'%(version,t['total_transitions'],t['completed_episode_steps'],t['open_transitions'],t['cost_sum'],k['retries'],*k['actual_actor_lr_range']))
        lines.append('%s 실제비용 전구간0=%s, cost advantage/value/target/loss 정확0=%s. 양의 비용이 나오면 cost신호가0이라고 가정하지 않는다.'%(version,t['cost_proof']['all_actual_cost_zero'],t['cost_proof']['all_cost_signals_exact_zero']))
    evidence = result['initial_evidence']
    lines += ['', '초기 배우71tensor 및 고정/확률128의 원장·물리·NN동작은 V6와 같다. reward 가치망만 fit자료 train96환경으로1000회×512 보정했다. 별도 holdout32환경은 같은 장면이며 다른 seed/장면 holdout이 아니다. 관측 MC는 확률 수행의 실현값이며 기대가치 정답 자체가 아니다.',
        '구간별 가치 MSE가 악화한 phase(train/holdout): %s. 전체 holdout 개선이 모든 tail구간 개선을 뜻하지 않는다.'%evidence['phases_with_MSE_worsening'],
        '학습률·KL재시도 변화는 개입 이후 경로로 기록하며 수동 설정 차이로 설명하지 않는다. 단일seed 비교로 원인·일반효과를 확정하지 않는다. 다른 손가락·자유기타/J33·원67음·다른seed는 미완료다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def run(out):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '','Explicit CPU-only environment required')
    reviewed = gate()
    readiness = status();require(readiness['final_ready'],'Final artifacts pending: '+str(readiness['missing']))
    pins = collect_pins(required_files());pins.update(reviewed)
    with lifecycle(out,pins) as output:
        wrapper = helper()
        result = dict(initial_evidence=warmup_evidence())
        for version,root in [('V6',V6),('V7',V7)]: result[version] = summarize(root,wrapper)
        write(output/'analysis.json',result);plots(result,output);results(result,output)
        require(not any(n in sys.modules for n in ('torch','isaacgym')),'Forbidden model/native import')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__);sub = parser.add_subparsers(dest='command',required=True)
    sub.add_parser('prepare');sub.add_parser('status');sub.add_parser('gate-check');p = sub.add_parser('run');p.add_argument('--out',required=True)
    args = parser.parse_args()
    if args.command == 'prepare': print(json.dumps(prepare()))
    elif args.command == 'status': print(json.dumps(status()))
    elif args.command == 'gate-check':
        gate();require(not any(n in sys.modules for n in ('numpy','torch','isaacgym')),'Numerical import before gate');print('{"ready":true,"stdlib_only":true}')
    else: run(args.out)
