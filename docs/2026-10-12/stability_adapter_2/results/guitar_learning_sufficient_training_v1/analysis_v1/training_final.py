from pathlib import Path
import datetime,hashlib,importlib.util,json,math
base=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1');out=base/'analysis_v1';source=base/'training_long_v1';snapshot=out/'final_input_snapshot';snapshot.mkdir(exist_ok=False)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
manifest={'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source),'highest_included_completed_update':127,'completed_updates':list(range(128)),'scope':'Completed training only. Separate final evaluations pending. No old C/smoke/baseline/mid32 evaluation episode pooling.','files':{}}
paths=[source/('update_%06d.json'%i) for i in range(128)]
manifest['update_file_list_before_stream_read']=[str(p) for p in paths]
for i,path in enumerate(paths):
 payload=path.read_bytes();assert json.loads(payload)['update_index']==i;(snapshot/path.name).write_bytes(payload);manifest['files'][path.name]={'original_path':str(path),'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)}
for path in [source/n for n in ['episodes.jsonl','resources.jsonl','report.json','core_report.json','persistent_audit.json']]+[base/'training_long_v1_runtime_json_audit.json',base/'training_long_validation_v2.json']:
 payload=path.read_bytes();target=snapshot/path.name
 if path.name=='training_long_v1_runtime_json_audit.json':target=out/'final_input_snapshot_runtime_json_audit.json'
 target.write_bytes(payload);manifest['files'][str(target.relative_to(out))]={'original_path':str(path),'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)}
final=source/'final.pt';assert sha(final)=='ae9770470cdbd7141bf47c277a4a81757a753841beab18419c60de31f2e9a7e6';manifest['final_checkpoint']={'path':str(final),'sha256':sha(final)}
assert json.loads((source/'report.json').read_text())['core_report']['sha256']==sha(source/'core_report.json')
validation=json.loads((base/'training_long_validation_v2.json').read_text());assert validation['passed'] is True
spec=importlib.util.spec_from_file_location('analysis',out/'analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s=m.training_summary(snapshot);assert s['finalized_report']['recorded_pass'] and s['runtime']['recorded_pass'];assert s['recorded_updates']==128
s.update(original_training_folder=str(source),snapshot_manifest=str(out/'final_snapshot_manifest.json'),highest_included_completed_update=127,scope='Finalized training and root validation passed; final policy evaluation pending.')
rows=[];release_rewards=[]
for item in m.lines(snapshot/'episodes.jsonl'):
 row=m.episode_row(item['episode'],item['metrics']);row.update(worker_id=item['worker_id'],update_index=item['update_index']);rows.append(row)
 if not row['success']:
  terms=item['episode']['refinement']['raw_reward_terms_total'];release_rewards.append(terms['refinement_release_absent']+terms['refinement_release_success'])
assert len(rows)==1024 and sum(r['success'] for r in rows)==529
keys=['actor_lr','analytic_kl','kl_retries','std_mean','bc_mse','reward_value_loss','cost_value_loss','reward_explained_variance','cost_explained_variance','cost_reward_advantage_std_ratio','collection_s','update_s']
def group(first,last):
 subset=[r for r in rows if first<=r['update_index']<last];updates=s['updates'][first:last];failed=[r for r in subset if not r['success']]
 return {'update_indices':list(range(first,last)),**m.summarize(subset),'failure_diagnostics':{'failed_count':len(failed),'ready_zero_count':sum(r['ready_s']==0 for r in failed),'ready_positive_but_hold_failed_count':sum(r['ready_s']>0 and not r['hold_pass'] for r in failed),'hold_zero_count':sum(r['hold_fraction']==0 for r in failed),'first_clean_never_observed_count':sum(r['first_clean_s'] is None for r in failed)},'diagnostics':{key:m.bounds([u.get(key) for u in updates]) for key in keys}}
s['nonoverlap64']={'first64':group(0,64),'last64':group(64,128)};s['nonoverlap32']={str(i+1)+'_'+str(i+32):group(i,i+32) for i in range(0,128,32)};s['nonoverlap16']={str(i+1)+'_'+str(i+16):group(i,i+16) for i in range(0,128,16)};s['failure_diagnostics']=group(0,128)['failure_diagnostics'];s['failure_diagnostics']['failed_release_reward_values']=sorted(set(release_rewards));s['worker_nonoverlap64']={str(w):{name:m.summarize([r for r in rows if r['worker_id']==w and first<=r['update_index']<last]) for name,first,last in [('first64',0,64),('last64',64,128)]} for w in range(8)}
report=json.loads((snapshot/'report.json').read_text());s['timers']=report['timers'];s['root_validation']=validation;s['worker_cleanup']=report['pool_close_diagnostics'];s['persistent_lifecycle']=[]
for w in range(8):
 path=source/('worker_%03d/environment/persistent_lifecycle.json'%w);d=json.loads(path.read_text());s['persistent_lifecycle'].append({'worker_id':w,'path':str(path),'sha256':sha(path),'native_calls':d['native_calls'],'closed':d['closed'],'episode_index':d['episode_index'],'reset_records':len(json.loads((snapshot/'persistent_audit.json').read_text())['workers'][w]['resets']),'native_sim_time_s':d['native_sim_time_s'],'episode_local_physics_steps':d['episode_local_physics_steps']})
s['ready_failure_definition']='Positive accumulated clean contact in the last 200ms preparation window; not a 50ms acquisition dwell latch.';s['baseline_update_counter']=32;s['additional_updates']=128;s['final_optimizer_update_counter']=160;s['plot_ready_denominator_s']=.2
(out/'final_snapshot_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'training_final_summary.json').write_text(json.dumps(s,indent=2,allow_nan=False)+'\n');m.plot_training(s,out/'final_learning_curve.png')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_path='/usr/share/fonts/truetype/nanum/NanumSquareR.ttf'
font_manager.fontManager.addfont(font_path)
plt.rcParams['font.family']=font_manager.FontProperties(fname=font_path).get_name()
updates=s['updates'];x=list(range(1,129));success=[u['successes']/u['episodes']*100 for u in updates];hold=[u['episode_summary']['hold_fraction']['mean']*100 for u in updates];ready=[u['episode_summary']['ready_s']['mean']/.2*100 for u in updates]
def rolling(values):return [sum(values[i-15:i+1])/16 if i>=15 else float('nan') for i in range(len(values))]
fig,axes=plt.subplots(1,2,figsize=(12,4.5),sharex=True,sharey=True)
axes[0].plot(x,success,color='#2d6a9f',alpha=.18,lw=1,label='업데이트별 성공률 (8회)');axes[0].plot(x,rolling(success),color='#2166ac',lw=2.4,label='최근 16업데이트 평균');axes[0].axhline(s['all_episodes']['success_fraction']*100,color='#777777',ls='--',lw=1,label='전체 평균 51.66%');axes[0].set_title('왼손 단음 성공률');axes[0].set_ylabel('비율 (%)')
axes[1].plot(x,rolling(hold),color='#2a9d8f',lw=2.4,label='음 구간 목표 접촉 유지율');axes[1].plot(x,rolling(ready),color='#d47716',lw=2.4,label='마지막 200ms 준비 구간 접촉률');axes[1].set_title('접촉 유지와 준비 — 최근 16업데이트 평균')
for ax in axes:
 ax.axvspan(.5,14.5,color='#b6b6b6',alpha=.23,zorder=0);ax.axvline(14.5,color='#999999',lw=.8,ls=':');ax.set_xlim(.5,128.5);ax.set_ylim(0,100);ax.set_yticks([0,20,40,60,80,100]);ax.set_xlabel('이번 실행의 추가 업데이트');ax.grid(alpha=.2);ax.legend(loc='lower right',fontsize=9,framealpha=.9)
fig.suptitle('추가 128회 학습 · 1,024회 수행 · 물리 실패 0회',fontsize=14,y=.99);fig.text(.5,.015,'회색: 과거 C의 처음 14회와 정확히 재현되는 구간 · 단일 학습 계보/동일 준비 자세 · 최종 정책 평가는 별도',ha='center',fontsize=9,color='#444444');fig.tight_layout(rect=[0,.055,1,.94]);fig.savefig(str(out/'summary_learning_curve.png'),dpi=170);plt.close(fig)
print(json.dumps({'all':s['all_episodes'],'failures':s['failure_diagnostics'],'half':{k:{'success':v['success_count'],'episodes':v['episodes'],'hold':v['hold_fraction']['mean'],'ready':v['ready_s']['mean'],'wrong':v['wrong_press_s']['mean'],'missing':v['missing_press_s']['mean'],'diag':v['diagnostics']} for k,v in s['nonoverlap64'].items()},'quarter_success':[v['success_count'] for v in s['nonoverlap32'].values()],'eighth_success':[v['success_count'] for v in s['nonoverlap16'].values()],'persistent':s['persistent_lifecycle'][0]},indent=2))
