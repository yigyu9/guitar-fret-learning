"""Completed V5/V6 only; CPU tensor reads, no simulator/model construction/forward."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent
V6 = OUT.parent
V5 = V6.parent/'index_release_success_settlement_v5'
HELPER = V5/'analysis/analyze.py'
HELPER_SHA = 'c35a1810b91f6b5c76c76a56d0a881ed29f08d5ea93e0ff4f3b2ae51e07beb38'
import hashlib
# Verify before importing even pure helper code.
if hashlib.sha256(HELPER.read_bytes()).hexdigest() != HELPER_SHA:
    raise ValueError('frozen V5 helper changed')
spec = importlib.util.spec_from_file_location('frozen_v5_analysis', HELPER)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
read, rows, sha, require = h.read, h.rows, h.sha, h.require
SCHEMAS = {V5:'diagnostic.release_success_settlement.v5', V6:'diagnostic.cost_prior_zero.v6'}
HEAD = ['cost_critic.bias','cost_critic.weight']


def cases(root):
    return [(0,False,root/'runs/fit_deterministic',root/'runs/fit/fit.pt'),
            (0,True,root/('runs/fit_stochastic_actual' if root == V5 else 'runs/fit_stochastic'),root/'runs/fit/fit.pt')] + [
        (u,s,root/('runs/ppo_eval_%06d_%s' % (u,'stochastic' if s else 'det')),
         root/'runs/ppo'/('final.pt' if u == 300 else 'evaluation_%06d.pt' % u))
        for u,s in [(50,False),(100,False),(150,False),(200,False),(250,False),(300,False),(300,True)]]


def audit_pins(path, files):
    before, after = [read(path/f) for f in ['inputs_before.json','inputs_after.json']]
    require(after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources'], 'input pins changed')
    require(before == after['input_pins'] and bool(after['input_pins']), 'pin set changed/empty')
    for name,digest in after['input_pins'].items():
        p=Path(name); require(sha(p)==digest, 'pin SHA mismatch '+name); files.add(p)
    return after['input_pins']


def report(path, root, updates):
    r=read(path/'learning_report.json'); h.audit_report(r,updates)
    require(r['schema']==SCHEMAS[root], 'report schema mismatch')
    if updates == 0:
        require(r['fit_steps']==0 and r['initialization_fit_steps']==1000, 'wrong eval fit budget')
    return r


def audit_mode(acceptance, update, stochastic):
    require(acceptance['stochastic'] is stochastic and acceptance['checkpoint_updates']==update, 'wrong/missing evaluation mode')


def evaluation(root, case, files):
    path=case[2]; report(path,root,0); audit_pins(path,files)
    audit_mode(read(path/'acceptance.json'),case[0],case[1])
    # Root selects settlement checking only; all data locations come from case.
    result=h.evaluation(h.V5,case)
    require(read(path/'training_contract.json')['diagnostics'].get('cost_prior',{}).get('schema') == SCHEMAS[root]
            if root == V6 else 'cost_prior' not in read(path/'training_contract.json')['diagnostics'], 'contract schema mismatch')
    return result


def zero_summary(s):
    require(s['count']==4096 and s['nonfinite_count']==0, 'zero proof missing/full finite samples')
    return all(s[k]==0 for k in ['mean','std','min','max'])


def cost_proof(metrics, cost_sum):
    signals=[]
    for m in metrics:
        d=m['diagnostics']; c=d['post_update']['critics']['cost']
        require(m['cost_weight']==d['advantages']['cost_weight_used']==1, 'failure cost weight changed')
        require(d['valid_decisions']==d['physical_transitions']==4096, 'incomplete K1 diagnostics')
        summaries=[d['advantages']['cost_raw'],c['value'],c['target']]
        zeroes=[zero_summary(s) for s in summaries]
        signals.append(m['cost_value_loss']==m['cost_value_loss_last']==c['mse']==0 and
                       all(zeroes) and
                       d['minibatches']['value']['sample_weighted_mean']['cost_loss']==0 and
                       d['minibatches']['value']['max']['cost_loss']==0)
    actual_zero=all(m['mean_failure_cost']==0 for m in metrics) and cost_sum==0
    return dict(all_actual_cost_zero=actual_zero, all_cost_signals_exact_zero=all(signals),
                nonzero_signal_updates=[m['update'] for m,z in zip(metrics,signals) if not z],
                zero_cost_signal_proof=actual_zero and all(signals))


def training(root, files):
    path=root/'runs/ppo'; r=report(path,root,300); audit_pins(path,files)
    metrics,eps=rows(path/'metrics.jsonl'),rows(path/'episodes.jsonl')
    require([m['update'] for m in metrics]==list(range(1,301)), 'incomplete PPO300')
    require(all(m['transitions']==4096 and m['total_transitions']==m['update']*4096 for m in metrics), 'transition budget')
    result=h.summarize(eps,require_settlement=True)
    proof=cost_proof(metrics,result['cost_sum'])
    if root == V6 and proof['all_actual_cost_zero']:
        require(proof['zero_cost_signal_proof'], 'zero actual costs but nonzero cost signals')
    result.update(report=r,transitions=300*4096,completed_episode_steps=sum(e['steps'] for e in eps),
                  open_transitions=300*4096-sum(e['steps'] for e in eps),cost_proof=proof)
    return result,metrics


def checkpoint(path,root,update):
    import torch
    c=torch.load(path,map_location='cpu',weights_only=False)
    require(c['updates']==update and c['cost_weight']==1, 'checkpoint update/weight mismatch')
    require(c['metadata']['schema']==SCHEMAS[root], 'checkpoint metadata schema')
    require(c['identity']['architecture']['schema']==SCHEMAS[root]+'.goal_policy', 'checkpoint architecture schema')
    require(c['metadata']['fit_steps']==1000 and c['metadata']['fresh_only'], 'checkpoint initialization mismatch')
    require(c['metadata']['settings']==read(root/'inputs/settings.json'), 'checkpoint settings mismatch')
    if root == V6:
        require(c['metadata']['cost_prior']==read(root/'runs/fit_deterministic/training_contract.json')['diagnostics']['cost_prior'], 'checkpoint cost-prior contract mismatch')
    require(c['identity']['architecture']['contract']==read(root/'runs/fit_deterministic/training_contract.json'), 'checkpoint contract mismatch')
    require(bool(c['metadata']['input_pins']), 'missing checkpoint pins')
    for name,digest in c['metadata']['input_pins'].items():
        require(sha(Path(name))==digest, 'checkpoint input pin mismatch '+name)
    return c


def initial_evidence(files):
    p=V6/'runs/fit/initial_tensor_equality.json'; evidence=read(p); files.add(p)
    import torch
    for name,r in evidence.items():
        require(r['tensor_count']==71 and r['unchanged_tensor_count']==69 and not r['full_model_exact'] and
                r['controlled_differences']==HEAD and r['zero_cost_head'] and not r['old_checkpoint_loaded_into_model'], 'initial69+2 evidence')
        a,b=V5/'runs/fit'/name,V6/'runs/fit'/name; files.update([a,b])
        require(sha(a)==r['reference_sha'] and sha(b)==r['own_sha'], 'initial checkpoint SHA')
        old,new=[torch.load(p,map_location='cpu',weights_only=False)['model'] for p in [a,b]]
        require(len(old)==len(new)==71 and old.keys()==new.keys(), 'initial model keys')
        require(sorted(k for k in old if not torch.equal(old[k],new[k]))==HEAD, 'initial actual69+2')
        require(all(torch.count_nonzero(new[k]).item()==0 for k in HEAD), 'initial head nonzero')
    p=V6/'initial_comparison/verification.json'; v=read(p); files.add(p)
    for name in ['fit_deterministic','fit_stochastic']:
        require(v[name]['full_episode_ledger_and_nine_rewards_exact'] and v[name]['actual_q_targets_body_candidates_NN_goals_and_rewards_exact'], 'initial actual comparison')
    for name,digest in v['input_sha256'].items():
        p=Path(name); require(sha(p)==digest,'initial evidence pin changed');files.add(p)
    return evidence


def artifacts(result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(13,7),sharex=True)
    for v,style in [('V5','--'),('V6','-')]:
        det=[e for e in result[v]['evaluations'] if not e['stochastic']]; x=[e['update'] for e in det]
        curves=[('All 3 achieved (%)',[e['all3']/1.28 for e in det]),('All 3 AND A released (%)',[e['joint']/1.28 for e in det]),
                ('A released (%)',[e['A_released']/1.28 for e in det]),('A clean (%)',[e['per_note'][0]['clean_mean']*100 for e in det]),
                ('A longest clean streak (ms)',[e['per_note'][0]['best_clean_streak_mean_s']*1000 for e in det]),('A audible wrong (%)',[e['per_note'][0]['wrong_mean']*100 for e in det])]
        for ax,(title,y) in zip(axes.flat,curves):
            ax.plot(x,y,style,marker='o',label=v);ax.set_title(title);ax.set_xlabel('PPO updates');ax.grid(alpha=.2);ax.legend()
    fig.suptitle('Original 128 attempts; failures retained');fig.tight_layout();fig.savefig(OUT/'performance.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(3,3,figsize=(13,9),sharex=True)
    for ax,key in zip(axes.flat,result['V5']['evaluations'][0]['reward_components_mean']):
        for v,style in [('V5','--'),('V6','-')]:
            det=[e for e in result[v]['evaluations'] if not e['stochastic']]
            ax.plot([e['update'] for e in det],[e['reward_components_mean'][key] for e in det],style,marker='.',label=v)
        ax.set_title(key,fontsize=9);ax.set_xlabel('PPO updates');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Nine reward means / original 128 fixed-checkpoint attempts');fig.tight_layout();fig.savefig(OUT/'nine_rewards.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(13,7),sharex=True)
    for v,style in [('V5','--'),('V6','-')]:
        ms=result[v]['metrics'];x=[m['update'] for m in ms]
        curves=[('Actual mean failure cost',[m['mean_failure_cost'] for m in ms]),('Cost advantage std',[m['diagnostics']['advantages']['cost_raw']['std'] for m in ms]),
                ('Post-update cost value mean',[m['diagnostics']['post_update']['critics']['cost']['value']['mean'] for m in ms]),('Cost target mean',[m['diagnostics']['post_update']['critics']['cost']['target']['mean'] for m in ms]),
                ('Cost value loss (last minibatch)',[m['cost_value_loss'] for m in ms]),('Actual actor learning rate',[m['actor_lr'] for m in ms])]
        for ax,(title,y) in zip(axes.flat,curves):
            ax.plot(x,y,style,label=v);ax.set_title(title,fontsize=9);ax.set_xlabel('PPO updates');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'cost_signals.png',dpi=160);plt.close(fig)
    write_results(result)


def write_results(result):
    lines=['# V6: 비용 예측기 초기값 0과 V5 비교','',
           '원128시도·384음 전체와 실패를 포함했다. PPO300 및 초기 2평가·후속 7평가를 모두 검사했다. 마지막300 모델이 최종 결과다. V5 잘못 명명된 추가 평가와 V4 부분 실행은 성과에서 제외한다.','',
           '|버전/회차/모드|A/B7/B8 달성|all3|A 해제|joint|실패|평균 보상|gate|','|---|---|---:|---:|---:|---:|---:|---|']
    for v in ['V5','V6']:
        for e in result[v]['evaluations']:
            lines.append('|%s/%d/%s|%s|%d|%d|%d|%d|%.6f|%s|'%(v,e['update'],'확률' if e['stochastic'] else '고정','/'.join(str(n['achieved']) for n in e['per_note']),e['all3'],e['A_released'],e['joint'],e['failures'],e['reward_mean'],e['acceptance']['stage_ready']))
    a,b=[next(e for e in result[v]['evaluations'] if e['update']==300 and not e['stochastic']) for v in ['V5','V6']]
    lines+=['','마지막 고정평가 V5→V6 all3 %d→%d, joint %d→%d, A 달성 %d→%d. 단일 seed 관찰이며 일반적 인과효과를 확정하지 않는다.'%(a['all3'],b['all3'],a['joint'],b['joint'],a['per_note'][0]['achieved'],b['per_note'][0]['achieved']),'','![성과](performance.png)','','|버전/회차/모드/음|clean|wrong|missing|최장 clean(s)|','|---|---:|---:|---:|---:|']
    for v in ['V5','V6']:
        for e in result[v]['evaluations']:
            for n in e['per_note']:
                lines.append('|%s/%d/%s/%d|%.5f|%.5f|%.5f|%.5f|'%(v,e['update'],'확률' if e['stochastic'] else '고정',n['source_index'],n['clean_mean'],n['wrong_mean'],n['missing_mean'],n['best_clean_streak_mean_s']))
    lines+=['','![9보상](nine_rewards.png)','','![비용 신호](cost_signals.png)','','초기71개 중69개는 동일하고 비용 head2개만0이다. 초기 동작·9보상·전체128원장은 동일하다. 최초 update부터 차이가 가능하며 최초5회 지표 동일성을 전제하지 않는다.','']
    for v in ['V5','V6']:
        p=result[v]['training']['cost_proof']; ms=result[v]['metrics']
        lines.append('%s 실제 비용 전구간0=%s, cost advantage/value/target·loss 전구간 정확0=%s, 최종 비용 head0=%s. KL 재시도 합계%d, 실제 LR 범위 %.9g~%.9g.'%(v,p['all_actual_cost_zero'],p['all_cost_signals_exact_zero'],result[v]['final_cost_head_zero'],sum(m['kl_retries'] for m in ms),min(m['actor_lr'] for m in ms),max(m['actor_lr'] for m in ms)))
    lines+=['','학습률·KL 재시도의 후속 차이는 개입이 매개한 경로이며 수동 설정 차이가 아니다. 공유 value encoder 때문에 reward critic 표현도 달라질 수 있어 actor만의 격리가 아니다. 실제 비용이 양수라면 신호0을 유지한다고 가정할 수 없다. 학습 보고에 없는 teacher counter를0으로 만들지 않았다.','',
            'A goal/q/body-resultant 요약은 analysis.json 각 env0_trace에 모두 수록한다. env0 첫 시도60Hz 끝점의 관찰이며240Hz 전체 이력·128환경의 원인이나 접촉쌍/압력/음향의 증명이 아니다.','']
    for v in ['V5','V6']:
        e=next(e for e in result[v]['evaluations'] if e['update']==300 and not e['stochastic']);t=e['env0_trace']
        lines.append('%s 마지막 고정 env0: A 말기 %d끝점, 후보%d, resultant<0.01N %d; goal4(deg)=%s, 실제q4(deg)=%s.'%(v,t['A_audible_endpoints'],t['candidate_count'],t['unloaded_endpoints'],t['decoded_goal_mean_deg4'],t['actual_q_mean_deg4']))
    lines+=['','이 증거만으로 다른 seed·손가락·자유 기타·전곡의 성공을 주장하지 않는다. 다음 행동은 마지막 평가의 개선 여부와 실제 A 제어 관측을 검토한 뒤 결정한다.']
    (OUT/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='', 'explicit CPU-only environment required')
    required=[]
    for root in [V5,V6]:
        required += [root/'runs/ppo'/f for f in ['learning_report.json','inputs_before.json','inputs_after.json','metrics.jsonl','episodes.jsonl','final.pt']]
        required += [c[2]/f for c in cases(root) for f in ['evaluation.json','learning_report.json','evaluation_freeze.json','acceptance.json','learning_control_env0.npz','trace_metadata.json','inputs_before.json','inputs_after.json','training_contract.json']]
        required += [c[3] for c in cases(root)]
    require(all(p.is_file() for p in required), 'not final-ready; missing '+str([str(p) for p in required if not p.is_file()]))
    for root in [V5,V6]:
        report(root/'runs/ppo',root,300)
        for c in cases(root): report(c[2],root,0)
    require(not (OUT/'verification.json').exists(), 'final analysis already exists; preserve reviewed artifacts')
    files=set(required)|{HELPER,Path(__file__),OUT/'cpu_check.py',OUT/'PLAN.md',OUT/'cpu_verification.json'}
    files.update(root/'inputs/settings.json' for root in [V5,V6])
    evidence=initial_evidence(files)
    for root in [V5,V6]:
        audit_pins(root/'runs/ppo',files)
        for c in cases(root): audit_pins(c[2],files)
    before={str(p):sha(p) for p in sorted(files)}
    result={'initial_69_plus_2':evidence}
    for v,root in [('V5',V5),('V6',V6)]:
        train,ms=training(root,files);evaluations=[evaluation(root,c,files) for c in cases(root)]
        for u,s,p,ck in cases(root): checkpoint(ck,root,u)
        final=checkpoint(root/'runs/ppo/final.pt',root,300)
        import torch
        headzero=all(torch.count_nonzero(final['model'][k]).item()==0 for k in HEAD)
        if root==V6 and train['cost_proof']['all_actual_cost_zero']:
            require(headzero, 'zero-cost final cost head changed')
        result[v]=dict(training=train,metrics=ms,evaluations=evaluations,final_cost_head_zero=headzero)
    result['first_metric_difference_update']=next((a['update'] for a,b in zip(result['V5']['metrics'],result['V6']['metrics']) if a!=b),None)
    after={str(p):sha(Path(p)) for p in before}; require(before==after, 'input changed during analysis')
    artifacts(result)
    (OUT/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    verification=dict(all_checks_passed=True,input_sha256_before=before,input_sha256_after=after,new_GPU_runs=0,new_NN_runs=0,training_steps=0,evaluations=18)
    verification['output_sha256']={str(p):sha(p) for p in OUT.iterdir() if p.name in ['analysis.json','RESULTS.md','performance.png','nine_rewards.png','cost_signals.png']}
    (OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(json.dumps(dict(all_checks_passed=True,evaluations=18)))


if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args();main()
