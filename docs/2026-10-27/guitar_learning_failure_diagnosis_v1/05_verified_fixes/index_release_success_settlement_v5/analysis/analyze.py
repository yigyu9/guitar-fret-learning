"""CPU-only, read-only completed V5 versus original completed V4 comparison.
No simulator, policy, training module, or torch import is permitted here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent
V5 = OUT.parent
V4 = V5.parent / 'index_release_reference_learning_v4'
PREFIX = 'settlement_'
# Original source score end4; local episode end3.1703 uses a different clock.
SOURCE_A_END = 5.6203
DEADLINE = SOURCE_A_END + .1


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def mean(values):
    return float(np.mean(values))


def audit_report(report, updates):
    require(report['completed'] and report['closed'], 'missing completion/close')
    require(not report['failure'] and not report['cleanup_errors'], 'failed run')
    require(not report['changed_inputs'] and not report['unpinned_project_sources'], 'source mutation')
    if updates == 0:
        require(report['selected_reference_calls'] == 0, 'forbidden teacher calls')
    elif 'selected_reference_calls' in report:
        require(report['selected_reference_calls'] == 0, 'forbidden teacher calls')
    require(report['PPO_updates'] == updates, 'wrong update count')


def audit_episode(ep, *, require_settlement=False):
    terms = ep['reward_components']
    require(len(terms) == 9, 'nine reward terms required')
    require(abs(sum(terms.values()) - ep['reward']) < 3e-5, 'reward term sum')
    require([n['source_index'] for n in ep['notes']] == [4, 7, 8], 'wrong source notes')
    if 'success_settlement' not in ep:
        require(not require_settlement, 'missing V5 episode settlement ledger')
        return
    s = ep['success_settlement']
    get = lambda key: s[PREFIX + key]
    removed, entitled = get('removed_raw'), get('entitled_raw')
    pending, paid, suppressed = get('pending_raw'), get('paid'), get('suppressed')
    require(all(-1e-8 <= x <= cap+1e-8 for x, cap in [(removed,.5),(entitled,.5),(pending,.5),(paid,.25),(suppressed,.25)]), 'A budget/once')
    require(abs(.5*entitled-paid-suppressed-.5*pending) < 1e-7, 'settlement conservation')
    require(pending == 0, 'pending at control boundary')
    a = ep['notes'][0]
    require(abs(removed - .5*bool(a['achieved'])) < 1e-8, 'removed achievement mismatch')
    eligible = a['achieved'] and a['released'] and SOURCE_A_END <= a['release_s'] <= DEADLINE
    require(abs(entitled - .5*bool(get('closed') and eligible)) < 1e-8, 'eligibility mismatch')
    if get('closed'):
        require(DEADLINE <= get('time_s') < DEADLINE+1/240+1e-8, 'wrong settlement source time')
    else:
        require(get('time_s') == 0 and entitled == 0, 'unclosed payout')
    require(suppressed == 0 or ep['cost'] > 0, 'suppression without failure')
    if not ep['failure_reasons']:
        require(abs(terms['song_left_success']-(.25*sum(n['achieved'] for n in ep['notes'][1:])+paid)) < 1e-6, 'A/B success payout')


def audit_trace(path, ep):
    a = np.load(path)
    ledger = [k for k in a.files if k.startswith(PREFIX)]
    require(len(ledger) == 7, 'missing trace settlement ledger')
    for key in ledger:
        v = a[key]
        require(np.all(np.diff(v.astype(float)) >= -1e-9), 'ledger decreases/reset inside first attempt')
        require(abs(float(v[-1])-ep['success_settlement'][key]) < 1e-7, 'trace/episode settlement mismatch')
    closed = a['settlement_closed'].astype(bool)
    require(all(float(a[k][0]) == 0 for k in ledger), 'nonzero initial/reset ledger')
    require(int(np.sum(np.diff(closed.astype(int)) == 1)) <= 1, 'multiple close edges')
    for key in ['settlement_removed_raw','settlement_entitled_raw','settlement_paid','settlement_suppressed']:
        require(int(np.sum(np.diff(a[key]) > 1e-9)) <= 1, 'multiple credit edges')
    return {'rows':len(a['time_s']), 'ledger_exact':True, 'first_row_ledger_zero':all(float(a[k][0]) == 0 for k in ledger),
            'source_local_offset_s':float(a['source_time_s'][0]-a['time_s'][0])}


def summarize(eps, *, require_settlement=False):
    for ep in eps:
        audit_episode(ep, require_settlement=require_settlement)
    return {'attempts':len(eps), 'note_opportunities':sum(len(e['notes']) for e in eps),
            'all3':sum(bool(e['achieved']) for e in eps),
            'joint':sum(bool(e['achieved'] and e['notes'][0]['released']) for e in eps),
            'A_released':sum(bool(e['notes'][0]['released']) for e in eps),
            'reward_mean':mean([e['reward'] for e in eps]),
            'reward_components_mean':{k:mean([e['reward_components'][k] for e in eps]) for k in eps[0]['reward_components']},
            'cost_sum':sum(e['cost'] for e in eps),
            'failures':sum(bool(e['failure_reasons']) for e in eps),
            'physical_failures':sum(bool(e['termination']['physical_failure']) for e in eps),
            'wrist_failures':sum(bool(e['termination']['wrist_failure']) for e in eps),
            'per_note':[{'source_index':idx, 'achieved':sum(bool(e['notes'][i]['achieved']) for e in eps),
                         'released':sum(bool(e['notes'][i]['released']) for e in eps),
                         'clean_mean':mean([e['notes'][i]['clean_fraction'] for e in eps]),
                         'wrong_mean':mean([e['notes'][i]['audible_wrong_fraction'] for e in eps]),
                         'missing_mean':mean([e['notes'][i]['missing_fraction'] for e in eps]),
                         'best_clean_streak_mean_s':mean([e['notes'][i]['note']['best_clean_streak'] for e in eps])}
                        for i,idx in enumerate([4,7,8])],
            'settlement_totals':{k:sum(float(e['success_settlement'][k]) for e in eps) for k in eps[0].get('success_settlement',{})}}


def cases(root):
    return [(0,False,root/'runs/fit_deterministic',root/'runs/fit/fit.pt'),
            (0,True,root/('runs/fit_stochastic_actual' if root == V5 else 'runs/fit_stochastic'),root/'runs/fit/fit.pt')] + [
            (u,s,root/('runs/ppo_eval_%06d_%s' % (u,'stochastic' if s else 'det')),
             root/('runs/ppo' if root == V5 else 'runs/ppo_attempt02')/('final.pt' if u == 300 else 'evaluation_%06d.pt' % u))
            for u,s in [(50,False),(100,False),(150,False),(200,False),(250,False),(300,False),(300,True)]]


def audit_evaluation_attempts(ev):
    require(ev['assigned_quotas'] == [1]*128 and len(ev['episodes']) == 128, 'original128 required')
    require(sorted(e['env_id'] for e in ev['episodes']) == list(range(128)), 'original env0..127 exactly once required')


def trace_summary(path):
    a=np.load(path/'learning_control_env0.npz')
    meta=read(path/'trace_metadata.json')
    ids=[meta['joint_names'].index(n) for n in ['LH:index1_x','LH:index1_z','LH:index2','LH:index3']]
    force=np.linalg.norm(a['net_body_force_n'][:,meta['body_names'].index('human/LH:index3')],axis=1)
    k=(a['time_s']>=3)&(a['time_s']<=3.1703)
    return {'scope':'env0 first attempt; saved60Hz endpoints, not 240Hz history or all128 cause',
            'A_audible_endpoints':int(k.sum()), 'candidate_count':int(a['candidate'][k,0].sum()),
            'unloaded_endpoints':int((force[k]<.01).sum()),
            'decoded_goal_mean_deg4':np.rad2deg(a['decoded_goal_rad'][k]).mean(0).tolist(),
            'actual_q_mean_deg4':np.rad2deg(a['q'][k][:,ids]).mean(0).tolist(),
            'records':[{'local_time_s':float(a['time_s'][i]),'candidate':bool(a['candidate'][i,0]),
                        'body_resultant_N':float(force[i]),'nearest_height_mm':float(a['surface_height_m'][i,0]*1000),
                        'wrong':bool(a['wrong'][i,0])} for i in np.flatnonzero(k)]}


def evaluation(root, case):
    update, stochastic, path, checkpoint = case
    ac = read(path/'acceptance.json')
    require(ac['stochastic'] == stochastic and ac['checkpoint_updates'] == update, 'wrong mode/checkpoint')
    require(ac['policy_performance'] and ac['selected_control'] == 'NN-only', 'not NN-only')
    report = read(path/'learning_report.json')
    audit_report(report,0)
    require(report['checkpoint_updates'] == update, 'report checkpoint mismatch')
    ev = read(path/'evaluation.json')
    audit_evaluation_attempts(ev)
    result = summarize(ev['episodes'], require_settlement=root == V5)
    require(result['note_opportunities'] == 384, 'original384 required')
    freeze = read(path/'evaluation_freeze.json')
    require(freeze['model_optimizers_updates_frozen'] and freeze['checkpoint_frozen'], 'not frozen')
    require(freeze['before'] == freeze['after'], 'optimizer/model mutation')
    cksha = sha(checkpoint)
    require(freeze['checkpoint_sha_before'] == freeze['checkpoint_sha_after'] == cksha, 'checkpoint mutation')
    require(not read(path/'inputs_after.json')['changed_paths'], 'changed input pins')
    result.update(update=update, stochastic=stochastic, path=str(path), checkpoint_sha256=cksha,
                  acceptance=ac['acceptance'], report=report, env0_trace=trace_summary(path))
    if root == V5:
        result['trace_audit'] = audit_trace(path/'learning_control_env0.npz', ev['episodes'][0])
    return result


def training(root):
    path = root/('runs/ppo' if root == V5 else 'runs/ppo_attempt02')
    report = read(path/'learning_report.json')
    audit_report(report,300)
    metrics, eps = rows(path/'metrics.jsonl'), rows(path/'episodes.jsonl')
    require([m['update'] for m in metrics] == list(range(1,301)), 'incomplete PPO300')
    transitions = metrics[-1]['total_transitions']
    completed_steps = sum(e['steps'] for e in eps)
    require(transitions == 300*128*32, 'wrong transition budget')
    result = summarize(eps, require_settlement=root == V5)
    result.update(transitions=transitions, completed_episode_steps=completed_steps,
                  open_transitions=transitions-completed_steps, report=report,
                  diagnostics={'all_actual_mean_cost_zero':all(m['mean_failure_cost']==0 for m in metrics),
                    'KL_retries':[{k:m[k] for k in ['update','kl_retries','actor_lr','max_attempted_kl','analytic_kl']} for m in metrics if m['kl_retries']],
                    'actor_grad_norm_range':[min(m['actor_grad_norm'] for m in metrics),max(m['actor_grad_norm'] for m in metrics)],
                    'samples':[{k:m[k] for k in ['update','actor_lr','analytic_kl','actor_grad_norm','cost_weight','reward_value_loss','cost_value_loss','diagnostics']} for m in metrics if m['update'] in [1,50,100,150,200,250,300]]},
                  completed_training_episode_batches=[dict(update=u, **summarize([e for e in eps if e['update']==u], require_settlement=root == V5)) for u in sorted(set(e['update'] for e in eps))])
    return result, metrics


def artifacts(result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2,2,figsize=(11,7),sharex=True)
    streak_ax=axes[1,1].twinx()
    streak_ax.set_ylabel('Mean longest clean streak (ms)')
    axes[1,1].set_ylabel('Mean A clean fraction (%)')
    for version, style in [('V4','--'),('V5','-')]:
        det = [r for r in result[version]['evaluations'] if not r['stochastic']]
        for ax,key,label in zip(axes.flat,['all3','joint','A_released',None],['All 3 achieved','All 3 AND A released','A released','A clean / streak']):
            x=[r['update'] for r in det]
            if key:
                ax.plot(x,[r[key]/128*100 for r in det],style,marker='o',label=version)
                ax.set_ylabel('Attempts (%) / original 128'); ax.set_ylim(0,103)
            else:
                ax.plot(x,[r['per_note'][0]['clean_mean']*100 for r in det],style,marker='o',label=version+' clean %')
                streak_ax.plot(x,[r['per_note'][0]['best_clean_streak_mean_s']*1000 for r in det],style,marker='x',alpha=.6,label=version+' streak ms')
            ax.set_title(label);ax.grid(alpha=.2);ax.legend(fontsize=8);ax.set_xlabel('PPO updates')
    h1,l1=axes[1,1].get_legend_handles_labels()
    h2,l2=streak_ax.get_legend_handles_labels()
    axes[1,1].legend(h1+h2,l1+l2,fontsize=7,loc='lower left',ncol=2)
    fig.tight_layout();fig.savefig(OUT/'performance.png',dpi=160);plt.close(fig)
    keys=list(result['V5']['evaluations'][0]['reward_components_mean'])
    fig,axes=plt.subplots(3,3,figsize=(12,8),sharex=True)
    for ax,key in zip(axes.flat,keys):
        for version,style in [('V4','--'),('V5','-')]:
            det=[r for r in result[version]['evaluations'] if not r['stochastic']]
            ax.plot([r['update'] for r in det],[r['reward_components_mean'][key] for r in det],style,marker='.',label=version)
        ax.set_title(key,fontsize=8);ax.grid(alpha=.2);ax.legend(fontsize=7);ax.set_xlabel('PPO updates')
    fig.suptitle('Nine reward means / original 128 fixed-checkpoint episodes');fig.tight_layout();fig.savefig(OUT/'nine_rewards.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(3,3,figsize=(12,8),sharex=True)
    for ax,key in zip(axes.flat,keys):
        for version,style in [('V4','--'),('V5','-')]:
            groups=result[version]['training']['completed_training_episode_batches']
            ax.plot([r['update'] for r in groups],[r['reward_components_mean'][key] for r in groups],style,marker='.',label=version)
        ax.set_title(key,fontsize=8);ax.grid(alpha=.2);ax.legend(fontsize=7);ax.set_xlabel('Completion update')
    fig.suptitle('Changing-policy completed training episodes: nine reward means');fig.tight_layout();fig.savefig(OUT/'training_nine_rewards.png',dpi=160);plt.close(fig)
    lines=['# V5: A 달성 보상 정산과 원 V4의 실제 비교','',
           '원 128시도·384음 전체가 분모다. 실패를 제외하거나 좋은 중간 checkpoint를 최종 결과로 대체하지 않았다. 초기 fit1000과 PPO0 이후 50 간격 고정128·최종 확률128을 모두 비교한다.','',
           '| 버전/업데이트/평가 | A/B7/B8 달성 | all3 | A 해제 | joint | 보상평균 | 실패 | gate |',
           '|---|---|---:|---:|---:|---:|---:|---|']
    for v in ['V4','V5']:
        for r in result[v]['evaluations']:
            lines.append('| %s/%d/%s | %s | %d | %d | %d | %.6f | %d | %s |' % (v,r['update'],'확률' if r['stochastic'] else '고정','/'.join(str(n['achieved']) for n in r['per_note']),r['all3'],r['A_released'],r['joint'],r['reward_mean'],r['failures'],r['acceptance']['stage_ready']))
    a,b=[next(r for r in result[v]['evaluations'] if r['update']==300 and not r['stochastic']) for v in ['V4','V5']]
    lines += ['', '마지막300 고정 평가에서 V4→V5 all3는 %d→%d, joint는 %d→%d, A 달성은 %d→%d다. 이 수치가 이번 단일 비교의 관찰 결과이며 seed 하나로 일반적 인과효과를 확정하지 않는다.' % (a['all3'],b['all3'],a['joint'],b['joint'],a['per_note'][0]['achieved'],b['per_note'][0]['achieved']), '', '![원128 성과](performance.png)', '', '| 버전/평가/음 | clean | wrong | missing | 최장 clean 평균(s) |','|---|---:|---:|---:|---:|']
    for v in ['V4','V5']:
        for r in result[v]['evaluations']:
            for n in r['per_note']:
                lines.append('| %s/%d/%s/%d | %.6f | %.6f | %.6f | %.6f |' % (v,r['update'],'확률' if r['stochastic'] else '고정',n['source_index'],n['clean_mean'],n['wrong_mean'],n['missing_mean'],n['best_clean_streak_mean_s']))
    lines += ['', '![아홉 보상항](nine_rewards.png)', '', '![변하는 학습정책의 완료 episode 보상](training_nine_rewards.png)', '', 'A의 원시 달성0.5를 회수하고 원 해제창 뒤 한 번만 정산해 최종 가중예산0.25를 지급한다. entitlement와 실수령·실패억제를 구분했다. episode별 예산·eligibility·pending=0·보상합과 env0 trace 단조·최대1회 지급·초기 reset 0을 검사했다. 시간은 원악보5.7203초 마감이며 local3.2703초와 섞지 않는다. 부분 reset과 끝경계의 합성 검사는 cpu_verification.json을 별도로 따른다.', '', '| 버전 | 학습 전이 | 완료 episode | 완료 전이 | 열린 전이 |','|---|---:|---:|---:|---:|']
    for v in ['V4','V5']:
        t=result[v]['training'];lines.append('| %s | %d | %d | %d | %d |' % (v,t['transitions'],t['attempts'],t['completed_episode_steps'],t['open_transitions']))
    lines += ['', '학습 episode와 batch 보상곡선은 정책이 변하는 중의 기록이다. 고정 checkpoint 성공률로 쓰지 않는다. V4 중단 attempt01의49업데이트는 비교계보와 분모에서 제외했다. V5 잘못 실행한 추가 고정128은 보존하되 fit_stochastic_actual만 원래 확률평가로 사용했다. 추가 소모 증거는 execution_attempts에 남아 있다.', '', '초기71 tensor 동등성과 음악/동작 일치의 기존 검증 및 독립검수를 analysis.json에 연결했다. 이 분석은 원자료·checkpoint·source pin 전후 SHA, model/optimizer freeze, 평가 교사호출0과 종료/close를 재검사한다. 훈련 report에 교사호출 counter가 없는 경우 0이라고 추정하지 않고 미계측으로 남긴다. native force는 body resultant이며 현별 압력·접촉쌍·음향을 뜻하지 않는다. 원240Hz 연속 clean/streak를60Hz 대표끝점으로 대체하지 않았다. 추가 NN 추론·물리·학습 실행은0이다.']
    lines += ['', '## 보상·정산의 정확한 원장', '', '| 평가 | A removed raw 합 | entitled raw 합 | paid 합 | suppressed 합 | closed |','|---|---:|---:|---:|---:|---:|']
    for r in result['V5']['evaluations']:
        t=r['settlement_totals']
        lines.append('| %d/%s | %.6f | %.6f | %.6f | %.6f | %d |' % (r['update'],'확률' if r['stochastic'] else '고정',t['settlement_removed_raw'],t['settlement_entitled_raw'],t['settlement_paid'],t['settlement_suppressed'],t['settlement_closed']))
    lines += ['', '| 보상항 | V4 fit0 | V5 fit0 | V4 u200 | V5 u200 | V4 u300 | V5 u300 | V5 u300 확률 |','|---|---:|---:|---:|---:|---:|---:|---:|']
    chosen=[next(r for r in result[v]['evaluations'] if r['update']==u and r['stochastic']==st) for v,u,st in [('V4',0,False),('V5',0,False),('V4',200,False),('V5',200,False),('V4',300,False),('V5',300,False),('V5',300,True)]]
    for key in keys:
        lines.append('| '+key+' | '+' | '.join('%.9f'%r['reward_components_mean'][key] for r in chosen)+' |')
    lines += ['', '## 실제 A 단절과 actor 신호', '', '| 버전/update | A candidate 끝점/11 | unloaded 끝점 | 목표 4축 평균(도) | 실제 4축 평균(도) |','|---|---:|---:|---|---|']
    for v in ['V4','V5']:
        for r in result[v]['evaluations']:
            if not r['stochastic'] and r['update'] in [0,200,250,300]:
                t=r['env0_trace']
                lines.append('| %s/%d | %d | %d | %s | %s |' % (v,r['update'],t['candidate_count'],t['unloaded_endpoints'],'/'.join('%.4f'%x for x in t['decoded_goal_mean_deg4']),'/'.join('%.4f'%x for x in t['actual_q_mean_deg4'])))
    lines += ['', 'V5 마지막 env0는 A audible 11개 저장끝점 중 처음1개 candidate 참, 이어4개 거짓(body resultant=0), 마지막6개 참이다. 이4개는 기존 load gate를 통과할 수 없었다. 앞뒤 끝점이 참이어도 원240Hz 연속 clean이 유지된다는 뜻은 아니다. 현별 압력·접촉쌍 또는 모든128환경의 실패기하로 일반화하지 않는다. 200·250과300의 여러 목표·실제 관절축이 함께 움직였으므로 특정 관절 하나를 원인으로 확정하지 않는다.', '', '| 버전/update | 수락 KL | clip전 grad norm | cost raw adv 평균/표준편차 | cost value 평균 | cost target 평균 |','|---|---:|---:|---|---:|---:|']
    for v in ['V4','V5']:
        for x in result[v]['training']['diagnostics']['samples']:
            adv=x['diagnostics']['advantages']['cost_raw'];crit=x['diagnostics']['post_update']['critics']['cost']
            lines.append('| %s/%d | %.9f | %.6f | %.9f/%.9f | %.9f | %.9f |' % (v,x['update'],x['analytic_kl'],x['actor_grad_norm'],adv['mean'],adv['std'],crit['value']['mean'],crit['target']['mean']))
    lines += ['', '두 실행은 update1에서 KL retry2회 후 actor_lr=1.875e-6이며 추가 retry 없이300을 마쳤다. 실제 failure cost는 전부0이나 cost critic·bootstrap target·cost advantage는0이 아니다. cost_weight=1로 reward−cost advantage를 구성하므로 actor 신호에 기여할 수 있다. 음의 cost value는 음의 물리비용을 뜻하지 않는다. 작은 수락 KL·학습률도 실제 접촉 연속성 보존을 보장하지 않았다. 초기 metric 전체가1..5에서 정확히 같고 첫 차이는6이다.', '', '기존 A 보상 정산만으로 마지막 퇴행은 해결되지 않았다. 다음 단일 검증 가설은 실현 cost0 구간에서도 bootstrap cost advantage가 actor를 움직이는 영향이다. 동일 fresh/fit·seed·PPO300·평가예산에서 actor cost_weight만0인 대조를 별도 승인 후 비교하고, 원 물리실패 판정·종료·cost 기록은 유지하는 방식으로 검증할 수 있다. 이는 관찰에서 나온 제안이며 cost critic이 원인이라는 결론이나 즉시 채택 권고가 아니다. joint가 개선돼도 최종 A clean/streak·전체음악·해제·실패 gate를 함께 만족해야 한다. 이번 분석에서 소스 보상·학습·GPU·NN은 추가 실행하지 않았다.']
    (OUT/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def main():
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'explicit CPU-only CUDA_VISIBLE_DEVICES required')
    # Refuse partial input before creating any final artifact.
    required=[]
    for root in [V4,V5]:
        required += [root/('runs/ppo' if root==V5 else 'runs/ppo_attempt02')/'learning_report.json']
        required += [c[2]/f for c in cases(root) for f in ['evaluation.json','learning_report.json','evaluation_freeze.json','acceptance.json','learning_control_env0.npz']]
    missing=[str(p) for p in required if not p.is_file()]
    require(not missing, 'not final-ready; missing reports/artifacts: '+str(missing))
    for root in [V4,V5]:
        audit_report(read(root/('runs/ppo' if root==V5 else 'runs/ppo_attempt02')/'learning_report.json'),300)
    files=set(required)
    for root in [V4,V5]:
        for c in cases(root):
            files.update(p for p in c[2].iterdir() if p.is_file());files.add(c[3])
        train=root/('runs/ppo' if root==V5 else 'runs/ppo_attempt02')
        files.update(p for p in train.iterdir() if p.is_file())
        pins=read(train/'inputs_after.json')['input_pins']
        for name,digest in pins.items():
            p=Path(name);require(sha(p)==digest,'source pin mismatch '+name);files.add(p)
    evidence=[V5/'initial_comparison/verification.json',V5/'initial_comparison/review.json',V5/'actual_initial_review.json',V5/'cpu_verification.json', V5/'runs/fit/initial_tensor_equality.json', V5/'execution_attempts/initial_stochastic_invocation_error.json']
    files.update(evidence);files.add(Path(__file__))
    equality=read(V5/'runs/fit/initial_tensor_equality.json')
    require(all(r['exact'] and r['tensor_count']==71 and not r['unequal'] and not r['old_checkpoint_loaded_into_model'] for r in equality.values()), 'initial tensor inequality')
    for name,row in equality.items():
        require(sha(V5/'runs/fit'/name)==row['own_sha'] and sha(V4/'runs/fit'/name)==row['reference_sha'], 'initial evidence checkpoint mismatch')
        files.update([V5/'runs/fit'/name,V4/'runs/fit'/name])
    before={str(p):sha(p) for p in sorted(files)}
    result={}
    metric_rows={}
    for version,root in [('V4',V4),('V5',V5)]:
        train,metric_rows[version]=training(root)
        result[version]={'evaluations':[evaluation(root,c) for c in cases(root)],'training':train}
    first_diff=next((i+1 for i,(a,b) in enumerate(zip(metric_rows['V4'],metric_rows['V5'])) if a!=b),None)
    result['first_training_metric_difference_update']=first_diff
    result['initial_evidence']={str(p):read(p) for p in evidence}
    result['extra_compute_excluded']={'V4_attempt01':str(V4/'execution_attempts/attempt01_interrupted.json'), 'V5_mistaken_extra_deterministic':str(V5/'execution_attempts')}
    artifacts(result)
    after={str(p):sha(Path(p)) for p in before}
    require(before==after,'analysis input changed while reading')
    (OUT/'analysis.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    verification={'all_checks_passed':True,'input_sha256_before':before,'input_sha256_after':after,'new_GPU_runs':0,'new_NN_runs':0,'training_steps':0,'evaluations':18}
    (OUT/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(json.dumps({'all_checks_passed':True,'first_training_metric_difference_update':first_diff}))


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    main()
