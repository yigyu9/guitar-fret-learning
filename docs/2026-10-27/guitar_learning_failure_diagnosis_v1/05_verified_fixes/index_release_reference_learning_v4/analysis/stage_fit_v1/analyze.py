"""Frozen fit-stage CPU evidence analysis. Does not load neural networks or physics."""
import hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__file__).resolve().parent;V4=OUT.parents[1];V2=V4.parent/'index_release_close_lead_v2'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
folders={'teacher_deterministic':V2/'runs/candidate','teacher_stochastic':V2/'runs/noisy_candidate','fit_deterministic':V4/'runs/fit_deterministic','fit_stochastic':V4/'runs/fit_stochastic'}
for name,p in folders.items():
 report='learning_report.json' if name.startswith('fit') else 'report.json';assert (p/report).exists() and read(p/report)['completed'], 'Wait for both actual128 evaluations before freezing fit stage'
files=[p for f in folders.values() for p in f.iterdir() if p.is_file()]+[p for p in (V4/'runs/fit').iterdir() if p.is_file()]
before={str(p):sha(p) for p in files}
offline=read(V4/'runs/fit/offline_errors.json');losses=offline.pop('losses');result={'stage':'stage_fit_v1','scope':'actual neural-only fit1000 evaluation vs prior V2 teacher, noPPO; separate later PPO stage','fit':{'initial_loss':losses[0],'final_loss':losses[-1],'steps':len(losses),'offline_errors':offline,'report':read(V4/'runs/fit/learning_report.json')},'offline_bucket_boundaries_local_s':[2,3.1703,3.2703,3.712,3.832],'offline_bucket_note':'six source time buckets use prediction endpoint (input time+1/60), env0..2 train/env3 heldout SAME SCENE; not unseen native states, not independent generalization','runs':{},'actual_vs_teacher':{}}
traces={};episodes={};phases={'ramp':(0,2),'pre_A':(2,3),'A_audible':(3,3.1703),'opening':(3.1703,3.2703),'N_hold':(3.2703,3.592),'early_closing':(3.592,3.712),'settle':(3.712,3.832),'B7_audible':(3.952,4.7299),'B8_audible':(5.3568,5.7051)}
for name,p in folders.items():
 ev=read(p/'evaluation.json');eps=sorted(ev['episodes'],key=lambda e:e['env_id']);episodes[name]=eps;meta=read(p/'trace_metadata.json');jn=meta['joint_names'];bn=meta['body_names'];a=np.load(p/('learning_control_env0.npz' if name.startswith('fit') else 'trace_env0_episode0.npz'));traces[name]=a
 ac=read(p/'acceptance.json')['acceptance'] if name.startswith('fit') else ev['acceptance'];report=read(p/('learning_report.json' if name.startswith('fit') else 'report.json'));pins=read(p/'inputs_after.json');force=np.linalg.norm(a['net_body_force_n'][:,bn.index('human/LH:index3')],axis=1)
 r={'attempts':len(eps),'note_opportunities':sum(len(e['notes']) for e in eps),'acceptance':ac,'all3':sum(e['achieved'] for e in eps),'report':report,'input_pin_count':len(pins['input_pins']),'changed_paths':pins['changed_paths'],'reward_sum':sum(e['reward'] for e in eps),'cost_sum':sum(e['cost'] for e in eps),'reward_components':{k:sum(e['reward_components'][k] for e in eps) for k in eps[0]['reward_components']},'per_note':[],'env0_phases':{}}
 for i,idx in enumerate([4,7,8]):
  ns=[e['notes'][i] for e in eps];r['per_note'].append({'source_index':idx,'achieved':sum(n['achieved'] for n in ns),'released':sum(n['released'] for n in ns),'clean_mean':float(np.mean([n['clean_fraction'] for n in ns])),'wrong_mean':float(np.mean([n['audible_wrong_fraction'] for n in ns])),'missing_mean':float(np.mean([n['missing_fraction'] for n in ns])),'best_clean_streak_mean_s':float(np.mean([n['note']['best_clean_streak'] for n in ns])),'achieved_and_A_released':sum(e['notes'][i]['achieved'] and e['notes'][0]['released'] for e in eps)})
 for phase,(lo,hi) in phases.items():
  k=(a['time_s']>=lo)&(a['time_s']<=hi);r['env0_phases'][phase]={'rows':int(k.sum()),'force_norm_mean_N':float(force[k].mean()),'force_norm_min_N':float(force[k].min()),'body_resultant_loaded_fraction':float((force[k]>=.01).mean()),'candidate_count3':a['candidate'][k].sum(0).tolist(),'wrong_count3':a['wrong'][k].sum(0).tolist(),'A_released_at_last_endpoint':bool(a['released'][np.flatnonzero(k)[-1],0])}
 if name.startswith('fit'):r['evaluation_freeze']=read(p/'evaluation_freeze.json')
 result['runs'][name]=r
for mode in ['deterministic','stochastic']:
 a=traces['fit_'+mode];b=traces['teacher_'+mode];assert np.array_equal(a['time_s'],b['time_s']);ids=[jn.index(j) for j in ['LH:index1_x','LH:index1_z','LH:index2','LH:index3']];cmp={'env0_phase_errors':{}}
 for phase,(lo,hi) in phases.items():
  k=(a['time_s']>=lo)&(a['time_s']<=hi);delta=np.rad2deg(a['decoded_goal_rad'][k]-b['decoded_goal_rad'][k]);actual=np.rad2deg(a['q'][k][:,ids]-b['q'][k][:,ids]);target=np.rad2deg(a['target'][k][:,ids]-b['target'][k][:,ids]);cmp['env0_phase_errors'][phase]={'decoded_goal_bias_deg4':delta.mean(0).tolist(),'decoded_goal_RMS_deg4':np.sqrt((delta**2).mean(0)).tolist(),'decoded_goal_max_abs_deg4':abs(delta).max(0).tolist(),'actual_q_RMS_deg4':np.sqrt((actual**2).mean(0)).tolist(),'finite_target_RMS_deg4':np.sqrt((target**2).mean(0)).tolist()}
 old=episodes['teacher_'+mode];new=episodes['fit_'+mode]
 for key,aa,bb in [('all3',[e['achieved'] for e in old],[e['achieved'] for e in new]),('A_release',[e['notes'][0]['released'] for e in old],[e['notes'][0]['released'] for e in new])]:cmp[key+'_same_env_outcome']={'both':sum(x and y for x,y in zip(aa,bb)),'teacher_only':sum(x and not y for x,y in zip(aa,bb)),'fit_only':sum(not x and y for x,y in zip(aa,bb)),'neither':sum(not x and not y for x,y in zip(aa,bb))}
 cmp['pairing_caveat']='same env_id/seed only; NN stochastic draws are not asserted bit-identical to prior noNN noise stream. Closed-loop states differ.';result['actual_vs_teacher'][mode]=cmp
dump('analysis.json',result)
after={str(p):sha(p) for p in files};checks={'inputs_unchanged':before==after,'all128_and384':all(r['attempts']==128 and r['note_opportunities']==384 for r in result['runs'].values()),'fit_steps1000_noPPO':result['fit']['report']['fit_steps']==1000 and result['fit']['report']['PPO_updates']==0,'eval_NN_only_no_teacher_reference_calls':all(result['runs'][n]['report']['selected_reference_calls']==0 for n in ['fit_deterministic','fit_stochastic']),'same_fit_checkpoint_both_evaluations':all(result['runs'][n]['evaluation_freeze']['checkpoint_sha_before']==result['runs'][n]['evaluation_freeze']['checkpoint_sha_after']==before[str(V4/'runs/fit/fit.pt')] for n in ['fit_deterministic','fit_stochastic']),'evaluations_frozen':all(result['runs'][n]['evaluation_freeze']['checkpoint_frozen'] and result['runs'][n]['evaluation_freeze']['model_optimizers_updates_frozen'] for n in ['fit_deterministic','fit_stochastic']),'closed_unchanged':all(r['report']['closed'] and not r['changed_paths'] for r in result['runs'].values()),'nine_reward_terms':all(len(r['reward_components'])==9 for r in result['runs'].values())}
dump('verification.json',{'all_checks_passed':all(checks.values()),'checks':checks,'input_sha256_before':before,'input_sha256_after':after,'new_GPU_runs':0,'NN_loaded_for_analysis':0,'training_steps':0});assert all(checks.values())
fig,axes=plt.subplots(4,1,figsize=(13,11),sharex=True);colors=['#386cb0','#aa3377','#228833','#e17c05']
for ci,(name,a) in enumerate(traces.items()):
 for ax,j in zip(axes[:2],['LH:index2','LH:index3']):ax.plot(a['time_s'],np.rad2deg(a['decoded_goal_rad'][:,[jn.index('LH:index1_x'),jn.index('LH:index1_z'),jn.index('LH:index2'),jn.index('LH:index3')].index(jn.index(j))]),color=colors[ci],label=name)
 force=np.linalg.norm(a['net_body_force_n'][:,bn.index('human/LH:index3')],axis=1);axes[2].plot(a['time_s'],force,c=colors[ci]);axes[3].step(a['time_s'],a['candidate'][:,0]+ci*1.2,where='post',c=colors[ci])
for ax,label in zip(axes,['PIP decoded goal (deg)','DIP decoded goal (deg)','Index3 body resultant (N)','A4 candidate (condition offset)']):
 ax.set_ylabel(label);ax.grid(alpha=.2);ax.set_xlim(2.9,4.05)
 for v in [3.1703,3.2703,3.592,3.712,3.832]:ax.axvline(v,c='grey',lw=.5,ls=':')
axes[0].legend(fontsize=8,ncol=2);axes[-1].set_xlabel('Local seconds (60Hz saved endpoints)');fig.tight_layout();fig.savefig(OUT/'actual_goal_contact.png',dpi=160);plt.close(fig)
print(json.dumps({n:r['acceptance'] for n,r in result['runs'].items()},ensure_ascii=False,indent=2))
lines=['# V4 stage_fit_v1: 오프라인초기화 뒤 실제NN128 평가','','fit1000의정규화goal MSE는0.049078→0.0000505234로낮아졌지만, NN-only 실제평가는교사V2성과를유지하지못했다. 결정론적전체98/128·A해제44/128, 확률적전체14/128·A해제111/128이다. 이문서는fit단계만고정한기록이며이후PPO300의결과/성공을대신하지않는다. 오프라인loss를실제음악성공의대리지표로쓰지않는다.','','## 원128분모의실제성과','','각조건은원128시도·384음전체다. fit모델은GoalPolicy557의새actor에서선택4축mean을1000회fit한초기화이며이단계PPO는0회다. 평가중selected reference호출은0,제어는NN-only이고checkpoint/model/optimizer가freeze되었다. 원교사와성능을비교하지만확률적환경의draw가과거noNN과byte-identical이라고확인한것은아니다.','','| 조건 | A4/B7/B8달성(각128) | 전체3음 | A해제 | 물리/손목실패 |','|---|---|---:|---:|---|']
for name,r in result['runs'].items():lines.append(f"| {name} | {'/'.join(str(n['achieved']) for n in r['per_note'])} | {r['all3']}/128 | {r['per_note'][0]['released']}/128 | {r['acceptance']['physical_failures']}/{r['acceptance']['wrist_failures']} |")
lines+=['','| 조건/음 | mean clean | mean wrong | mean missing | mean best clean streak(s) | 음달성 AND A해제/128 |','|---|---:|---:|---:|---:|---:|']
for name,r in result['runs'].items():
 for n in r['per_note']:lines.append(f"| {name}/{n['source_index']} | {n['clean_mean']:.9f} | {n['wrong_mean']:.9f} | {n['missing_mean']:.9f} | {n['best_clean_streak_mean_s']:.9f} | {n['achieved_and_A_released']} |")
lines+=['','실패하거나미달성한시도를분모에서제외하지않았다. A해제latch는ever가있고음끝후100ms안의candidate true→false를요구한다.44/128해제를84개가물리적으로영구압현했다는뜻으로읽지않는다. 원240Hz clean은현재/직전candidate가모두참인구간이고단절시연속streak를리셋한다.','','## NN 실제동작은어디서교사와갈라졌나','','env0의동일60Hz시간끝점을정렬했다. 아래는교사대비실제NN의decoded목표RMS(도)다. 이차이는closed-loop에서달라진입력상태와NN출력을함께포함하며고정teacher-state상오프라인오차와구분한다.','','| NN조건/구간 | index1_x | index1_z | PIP | DIP |','|---|---:|---:|---:|---:|']
for mode,c in result['actual_vs_teacher'].items():
 for phase in ['A_audible','opening','N_hold','early_closing','B7_audible','B8_audible']:
  v=c['env0_phase_errors'][phase]['decoded_goal_RMS_deg4'];lines.append('| '+mode+'/'+phase+' | '+' | '.join(f'{x:.6f}' for x in v)+' |')
lines+=['','N_hold=[3.2703,3.592]초에서deterministic NN PIP/DIP실제목표는교사보다평균+8.256/+7.943°더굽혀져있고최대오차14.257/14.015°다. 실제관절q의교사대비RMS도8.702/8.515°다. 교사N40°/10°를그대로유지하는실제동작이아니다. A4 audible목표bias는PIP/DIP -0.694/-0.617°이며B7 audible목표RMS는0.111/0.066°로상대적으로작다. 대표환경의해제구간추종문제와전체A해제저하는정합적관찰이나,모든환경의원인을단독으로확정하지않는다.','','env0 N_hold19끝점에서deterministic NN은A candidate/몸체loaded가8번남고해제latch=false다. 교사는동구간candidate/loaded0이다. 확률적NN env0는동구간candidate/loaded0이고해제latch=true이지만전체음악달성은14/128이다. 한대표환경의해제를전체성과로확대하지않는다. 힘의단위는N인exported body-resultant이며압력/현별contact pair/음향을측정한자료가아니다. tensor의벡터상쇄·파트너를분리할수없다. trace는60Hz끝점이고240Hz전체하중이력이아니다.','','![실제목표와접촉](actual_goal_contact.png)','','## 오프라인6bucket: 같은장면heldout과실제폐루프의구별','','bucket경계는[2,3.1703,3.2703,3.712,3.832]초이며input시각+1/60의예측끝점으로분류했다. phase3는V2의N유지와early closing을함께포함한다. train env0..2,heldout env3의같은장면teacher상태1416행을사용했다. 다음rms4는정규화goal의무차원값이며각도rad나실제접촉오차가아니다.','','| split/phase | 행수 | RMS index1_x/index1_z/PIP/DIP |','|---|---:|---|']
for split,rows in offline['errors'].items():
 for row in rows:lines.append(f"| {split}/{row['phase']} | {row['samples']} | "+'/'.join(f'{x:.7f}' for x in row['rms4'])+' |')
lines+=['','phase2의heldout normalized RMS는index1_z0.021209/PIP0.012449로다른일부구간보다크다. 그러나같은teacher-state오차가작다는것이NN자체상태의관측분포·전이/접촉을재현한다는보장은없다. 실제N목표편차를offline수치로숨기지않는다.','','## 보상9항·안전·다음PPO300의기준선','','| 항목 | '+' | '.join(result['runs'])+' |','|---|'+'---:|'*len(result['runs'])]
for k in result['runs']['teacher_deterministic']['reward_components']:lines.append('| '+k+' | '+' | '.join(f"{r['reward_components'][k]:.9f}" for r in result['runs'].values())+' |')
lines+=['','모든조건cost합0,sceneclose완료·원핀변경0이다. 원total과항목합은float누적순서의작은반올림차이가가능하다. NN실제실패를고치기위해이번fit를계속반복하거나축mask/std/각도grid를추가하지않는다. fit1000모델을그대로PPO300의고정초기기준으로삼고,현재fit deterministic98/해제44 및stochastic14/해제111과비교한다. noisy90%통과는PPO시작필수조건이아니며탐색실패는학습자료가될수있다. 원접촉기준·4축fullrange·effort cap·보상9항을유지하면서실제state에서의안정적press/hold/해제와연속streak를학습하는것이목표다. 이후실제학습업데이트/전이/중단/KL/성능을별도stage_PPO_v1로남겨동일128평가로검증해야한다.','','## 이단계기록의무결성','',f"verification.json은입력{len(files)}파일의분석전후SHA256과실제{len(checks)}검사통과를보존한다. 분석은CPU만사용했고NN/checkpoint를실행하지않았다. 이stage는fit완료+실제평가2개를고정한기록이며V4전체최종봉인이나후속PPO의완료선언이아니다. 활성소스/원결과/봉인입력을수정하지않았다."]
(OUT/'RESULTS.md').write_text('\n'.join(lines)+'\n')

dump('stage_freeze.json',{'stage':'stage_fit_v1','whole_V4_final_seal':False,'excludes_ongoing_PPO':True,'same_fit_checkpoint_sha256':before[str(V4/'runs/fit/fit.pt')],'analysis_artifact_sha256':{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='stage_freeze.json'},'input_files':len(files),'checks_passed':len(checks)})
