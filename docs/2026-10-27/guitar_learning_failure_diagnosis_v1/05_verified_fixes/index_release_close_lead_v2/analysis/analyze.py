"""Read-only comparison; imports no runtime or physics code."""
import hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__file__).resolve().parent
V2=OUT.parent;V1=V2.parent/'index_release_hinge_native_v1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def dump(n,d): (OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
paths={'v1_baseline':V1/'runs/baseline','v1_candidate':V1/'runs/candidate','v2_candidate':V2/'runs/candidate'}
noisy=V2/'runs/noisy_candidate'
if (noisy/'report.json').exists() and read(noisy/'report.json').get('completed'):paths['v2_noisy_candidate']=noisy
inputs=[p for d in paths.values() for p in d.iterdir() if p.is_file()]
inputs += [V2/'baseline_reuse.json',V2/'cpu_verification.json',V2/'cpu_inputs/candidate.json']
OLD=V2.parent/'index_release_clearance_v1/runs/noisy_reference'
EXPLORATION=V2.parents[1]/'04_ablation/prefix_release_alignment_v1/exploration/results_v1/comparison.json'
inputs += [OLD/n for n in ['prefix_acceptance.json','reference_noise_report.json','reference_noise4.npz']]
inputs += [EXPLORATION]
before={str(p):sha(p) for p in inputs}
result={'scope':'fixed-guitar no-NN deterministic/native-noisy diagnostics; not policy performance','v2_single_change':'PIP/DIP closing lead0.12s; duration0.12s unchanged; N40/10deg, MCP/wrist and note clocks unchanged','baseline_reuse':read(V2/'baseline_reuse.json'),'runs':{}}
traces={};surfaces={}
for name,d in paths.items():
 e=read(d/'evaluation.json');eps=e['episodes'];a=np.load(d/'trace_env0_episode0.npz');s=np.load(d/'release_clearance4.npz');traces[name]=a;surfaces[name]=s
 meta=read(d/'trace_metadata.json');jn=meta['joint_names'];bn=meta['body_names'];t=a['time_s'];st=s['clock']/240;mins=s['point_signed_height'].min(1)*1000
 r={'attempts':len(eps),'note_opportunities':sum(len(x['notes']) for x in eps),'invalid':sum(not x['valid'] for x in eps),'all3':sum(x['achieved'] for x in eps),'acceptance':e['acceptance'],'report':read(d/'report.json'),'reward_sum':sum(x['reward'] for x in eps),'cost_sum':sum(x['cost'] for x in eps),'reward_components':{k:sum(x['reward_components'][k] for x in eps) for k in eps[0]['reward_components']},'per_note':[],'surface_windows':{}}
 for i,idx in enumerate([4,7,8]):
  ns=[x['notes'][i] for x in eps];r['per_note'].append({'index':idx,'denominator':128,'achieved':sum(x['achieved'] for x in ns),'released':sum(x['released'] for x in ns),'achieved_and_released':sum(x['achieved'] and x['released'] for x in ns),'clean_mean':float(np.mean([x['clean_fraction'] for x in ns])),'wrong_mean':float(np.mean([x['audible_wrong_fraction'] for x in ns])),'missing_mean':float(np.mean([x['missing_fraction'] for x in ns]))})
 for w,(lo,hi) in {'common_original_phase3':(3.2703,3.712),'unchanged_N_hold':(3.2703,3.592),'v2_early_closing':(3.592,3.712)}.items():
  k=(st>=lo)&(st<=hi);r['surface_windows'][w]={'bounds_local_s':[lo,hi],'rows':int(k.sum()),'minimum_mm':float(mins[k].min()),'rows_ge5mm':int((mins[k]>=5).sum()),'loaded_rows':int(s['body_loaded'][k].sum()),'candidate_rows':int(s['candidate'][k].sum())}
 r['surface_total_rows']=len(st);r['valid_surface_rows']=int(s['valid_snapshot'].sum());r['post_failure_surface_rows']=int(s['post_failure'].sum())
 r['B7_onset_bracket']=[]
 onset=3.952;ix=int(np.searchsorted(t,onset))
 for q in [ix-1,ix]:r['B7_onset_bracket'].append({'time_s':float(t[q]),**{j:{z:float(np.rad2deg(a[z][q,jn.index(j)])) for z in ['q','target']} for j in ['LH:index2','LH:index3']}})
 mask=a['candidate'][:,1]&(t>=onset)&(t<=4.7299);starts=np.flatnonzero(mask&~np.r_[False,mask[:-1]]);ends=np.flatnonzero(mask&~np.r_[mask[1:],False]);r['env0_B7_candidate_intervals']=[[float(t[x]),float(t[y])] for x,y in zip(starts,ends)]
 pins=read(d/'inputs_after.json');r['input_pin_count']=len(pins['input_pins']);r['changed_paths']=pins['changed_paths']
 result['runs'][name]=r
if 'v2_noisy_candidate' in paths:
 n=traces['v2_noisy_candidate'];det=traces['v2_candidate'];old_noise=np.load(OLD/'reference_noise4.npz');new_noise=np.load(noisy/'reference_noise4.npz');old_report=read(OLD/'reference_noise_report.json');new_meta=read(noisy/'trace_metadata.json')
 result['noise_comparison']={'old_acceptance':read(OLD/'prefix_acceptance.json'),'noise_stream_sha256_old':old_report['normal_noise_stream_sha256'],'noise_stream_sha256_v2':new_meta['noise_stream_sha256'],'saved_env0to3_scaled_noise_bitexact':old_noise['scaled_noise'].tobytes()==new_noise['scaled_noise'].tobytes(),'effective_latent_std4_dimensionless':old_report['effective_std4'],'formula':'noisy_raw=tanh(atanh(reference_raw)+Normal(0,sigma4)); angular units below are realized decoded-goal differences, not latent sigma units','scope':'Same noise stream / 128x4 draws / seed7 / noNN / fixed-guitar three notes; old source/environment path differs, deterministic baseline exact is established separately. Change combines N-hinge opening and closing lead; not an isolated lead effect against old noisy reference.'}
 delta=n['decoded_goal_rad']-det['decoded_goal_rad'];result['noise_comparison']['env0_realized_goal_delta_rms_rad']=np.sqrt((delta**2).mean(0)).tolist();result['noise_comparison']['env0_realized_goal_delta_rms_deg']=np.rad2deg(np.sqrt((delta**2).mean(0))).tolist()
 result['noise_note_diagnostics']=[]
 for i,(lo,hi) in enumerate([(3,3.1703),(3.952,4.7299),(5.3568,5.7051)]):
  k=(n['time_s']>=lo)&(n['time_s']<=hi);ids=[jn.index(j) for j in ['LH:index1_x','LH:index1_z','LH:index2','LH:index3']]
  eps=read(noisy/'evaluation.json')['episodes'];failed=[e for e in eps if not e['notes'][i]['achieved']]
  result['noise_note_diagnostics'].append({'index':[4,7,8][i],'failed_achievement_count':len(failed),'failed_and_A_unreleased':sum(not e['notes'][0]['released'] for e in failed),'env0_audible_saved_endpoints':int(k.sum()),'env0_candidate_fraction':float(n['candidate'][k,i].mean()),'env0_wrong_endpoint_count':int(n['wrong'][k,i].sum()),'env0_surface_height_mm_range':[float(n['surface_height_m'][k,i].min()*1000),float(n['surface_height_m'][k,i].max()*1000)],'env0_surface_distance_max_mm':float(n['surface_distance_m'][k,i].max()*1000),'env0_actual_target_RMS_deg':np.rad2deg(np.sqrt(((n['q'][k][:,ids]-n['target'][k][:,ids])**2).mean(0))).tolist(),'env0_decoded_goal_delta_RMS_deg':np.rad2deg(np.sqrt((delta[k]**2).mean(0))).tolist()})
colors=['#386cb0','#e17c05','#228833','#aa3377'];x=np.arange(3);w=.8/len(paths)
fig,axes=plt.subplots(1,2,figsize=(12,4))
for i,(name,r) in enumerate(result['runs'].items()):
 for ax,key in zip(axes,['achieved','clean_mean']):ax.bar(x+(i-(len(paths)-1)/2)*w,[(n[key]/128 if key=='achieved' else n[key])*100 for n in r['per_note']],w,label=name,color=colors[i])
for ax,title in zip(axes,['Original achievement / 128','Mean clean fraction']):ax.set_xticks(x,['A4','B7','B8']);ax.set_ylim(0,105);ax.set_title(title);ax.set_ylabel('%');ax.axhline(90,c='black',ls='--',lw=.8);ax.legend(fontsize=7);ax.grid(axis='y',alpha=.2)
fig.tight_layout();fig.savefig(OUT/'performance_comparison.png',dpi=160);plt.close(fig)
fig,axes=plt.subplots(4,1,figsize=(12,10),sharex=True)
for i,(name,a) in enumerate(traces.items()):
 t=a['time_s'];c=colors[i]
 for ax,j in zip(axes[:2],['LH:index2','LH:index3']):
  ax.plot(t,np.rad2deg(a['q'][:,jn.index(j)]),c=c,label=name+' actual');ax.plot(t,np.rad2deg(a['target'][:,jn.index(j)]),c=c,ls='--',alpha=.5)
 axes[2].plot(t,np.linalg.norm(a['net_body_force_n'][:,bn.index('human/LH:index3')],axis=1),c=c,label=name)
 axes[3].step(t,a['candidate'][:,1].astype(float)+i*1.2,c=c,where='post',label=name)
for ax,l in zip(axes,['PIP (deg)','DIP (deg)','Index3 net body force (N)','B7 candidate (offset)']):
 ax.set_ylabel(l);ax.set_xlim(3.1,4.75);ax.grid(alpha=.2);ax.axvspan(3.952,4.7299,color='grey',alpha=.08)
 for b in [3.1703,3.2703,3.592,3.712,3.832,3.952]:ax.axvline(b,c='grey',ls=':',lw=.7)
axes[0].legend(fontsize=7,ncol=2);axes[3].legend(fontsize=7,ncol=2);axes[-1].set_xlabel('Local episode seconds');fig.tight_layout();fig.savefig(OUT/'tracking_contact_comparison.png',dpi=160);plt.close(fig)
fig,axes=plt.subplots(3,1,figsize=(12,8),sharex=True)
for i,(name,s) in enumerate(surfaces.items()):
 for env in range(4):
  k=s['env_id']==env;t=s['clock'][k]/240
  axes[0].plot(t,s['point_signed_height'][k].min(1)*1000,c=colors[i],alpha=.6,label=name if env==0 else None)
  for ax,key in zip(axes[1:],['body_loaded','candidate']):ax.step(t,s[key][k].astype(float)+i*1.3,c=colors[i],where='post',alpha=.6)
for ax,l in zip(axes,['Min signed height (mm)','Loaded (condition offset)','A4 candidate (condition offset)']):
 ax.set_ylabel(l);ax.grid(alpha=.2);ax.axvspan(3.592,3.712,color='grey',alpha=.12);ax.axvline(3.2703,c='grey',ls=':');ax.axvline(3.592,c='grey',ls=':');ax.axvline(3.712,c='grey',ls=':')
axes[0].axhline(5,c='black',ls='--',label='5mm');axes[0].legend(fontsize=8);axes[-1].set_xlabel('Local episode seconds (env0..3 saved endpoints)');fig.tight_layout();fig.savefig(OUT/'surface_comparison.png',dpi=160);plt.close(fig)
dump('analysis.json',result)
after={str(p):sha(p) for p in inputs}
checks={'inputs_unchanged':before==after,'all128_denominator':all(r['attempts']==128 for r in result['runs'].values()),'notes384':all(r['note_opportunities']==384 for r in result['runs'].values()),'nine_reward_components':all(len(r['reward_components'])==9 for r in result['runs'].values()),'all_reports_closed':all(r['report']['closed'] for r in result['runs'].values()),'no_changed_pins':all(not r['changed_paths'] for r in result['runs'].values()),'baseline_reuse_explicit':result['baseline_reuse']['new_native_run'] is False,'v2_deterministic_gate_pass':result['runs']['v2_candidate']['acceptance']['stage_ready']}
dump('verification.json',{'all_checks_passed':all(checks.values()),'checks':checks,'input_sha256_before':before,'input_sha256_after':after,'new_GPU_runs':0,'NN_created':0,'training_steps':0,'grid_std_searches':0})
assert all(checks.values())
print(json.dumps({n:{k:r[k] for k in ['all3','acceptance','surface_windows']} for n,r in result['runs'].items()},ensure_ascii=False,indent=2))
lines=['# closing lead v2 실제128 비교 분석','','PIP/DIP closing 준비만120ms 앞당긴 V2는 결정론적 원128시도에서 음악·A해제 gate를 모두 통과했다. V1후보 대비 B7 clean이79.916%→97.843%로 회복했다. 기존 baseline128/128을 완전히 재현한 성과는 아니며 V2 전체3음 달성은124/128이다.','','## 조건과 분모','','V1 baseline은 재사용한 원 실행이다. V2 runs/baseline의 두 JSON 복사는 새 GPU실행으로 세지 않는다. 각 조건은 원128시도/384음 전체를 분모로 사용하고 실패/미달성 시도를 제외하지 않는다. V2는 N PIP40°/DIP10°와 closing길이120ms를 유지하며 closing만[3.712,3.832]→[3.592,3.712]초로 옮겼다. MCP/팔/손목, 원press/onset/end, 속도/PD/effort/충돌/보상9항/종료기준은 유지한 단일 lead 비교다.','','| 조건 | 음4/7/8 달성 | 전체3음 달성 | A4해제 | 음악/해제 gate | 물리/손목 실패 |','|---|---|---:|---:|---|---|']
for n,r in result['runs'].items():
 ac=r['acceptance'];lines.append(f"| {n} | {'/'.join(str(q['achieved']) for q in r['per_note'])} (각128) | {r['all3']}/128 | {r['per_note'][0]['released']}/128 | {ac['music_passed']}/{ac['release_passed']} | {ac['physical_failures']}/{ac['wrist_failures']} |")
lines+=['','| 조건/음 | clean 평균 | wrong 평균 | missing 평균 | 달성·해제 동시/128 |','|---|---:|---:|---:|---:|']
for n,r in result['runs'].items():
 for q in r['per_note']:lines.append(f"| {n}/{q['index']} | {q['clean_mean']:.9f} | {q['wrong_mean']:.9f} | {q['missing_mean']:.9f} | {q['achieved_and_released']} |")
lines+=['','A4 released 판정은128개 에피소드의 원값이다. B7/B8 released 값은 별개이며 이 A해제 gate를 대체하지 않는다. mean clean90%, 달성90%, wrong10% 등 원판정을 그대로 사용했다.','','![성과](performance_comparison.png)','','## 실제 추종과 접촉','','B7 onset은local3.952초다. onset직전 저장끝점3.950초에서 PIP/DIP 실제각은 baseline53.839/23.285°, V1후보51.122/20.804°, V2후보53.233/22.869°다. 다음끝점3.966667초에서 공통목표54.485/24.068°에 대해 V2실제53.393/23.023°다. V2는 V1후보보다 실제 복귀가 빨라졌다. env0의 B7 candidate는 V1후보의 초기 지연·여러 토글과 달리 V2에서3.966667..4.716667초 연속이다. 이 대표환경은 전체128환경의 개별궤적을 보장하지 않는다. net body force는 특정 현의 pair pressure나 실제 음향 측정과 구분한다.','','A4 clean은 V1후보와V2가동일하다. 최초 개방 action시작3.166667초가A끝3.1703초보다 조금 이른 기존 endpoint일정 관찰은 이번closing변경에서 고치지 않았다. 초기 개방의 모든 음질 손실 원인을 단독으로 확정하지 않는다.','','![추종과 접촉](tracking_contact_comparison.png)','','## 표면의 공통창과 바뀐 구간','','원공통창 env0..3/clock692..920는 조건별232행이며 각끝점에서 원distal128점 signed height 최소를 사용한다. 전체128환경·모든240Hz substep을 검사한 것으로 확대하지 않는다. V2의 N유지와 early closing은 분리해 비교한다.','','| 조건/창 | 끝점수 | 최소(mm) | 5mm이상 | loaded | A candidate |','|---|---:|---:|---:|---:|---:|']
for n,r in result['runs'].items():
 for w,v in r['surface_windows'].items():lines.append(f"| {n}/{w} | {v['rows']} | {v['minimum_mm']:.6f} | {v['rows_ge5mm']} | {v['loaded_rows']} | {v['candidate_rows']} |")
lines+=['','원phase3=[3.2703,3.712]초, unchanged_N_hold=[3.2703,3.592]초, v2_early_closing=[3.592,3.712]초다. V2결정론적 후보는 공통phase3에서 재접촉0을 유지하지만 5mm는80/104만 충족한다. 따라서 정적후보7.56mm 예측을 실제전체최소값이나 gate완전성공으로 옮겨적지 않는다. 바뀐28끝점의최소6.344774mm와5mm28/28은 그 짧은구간만의 값이다. 준비anchor/qtarget정적기하와 실제index1 frame·q추종·손목자세 차이의 개별 인과 기여는 여기서 분리확정하지 않는다.','','![실제 표면](surface_comparison.png)','','## 잡음 확인','']
if 'v2_noisy_candidate' in result['runs']:
 r=result['runs']['v2_noisy_candidate'];lines += [f"원4성분 std/Normal128×4 조건의 실제 noisy128 결과를 별도 조건으로 포함했다. 전체3음 달성{r['all3']}/128이며 stage_ready={r['acceptance']['stage_ready']}다. 결정론적 gate통과와 잡음 내성은 별도 결론이다. 이 한seed/한std 진단을 일반화하거나 학습 성과로 해석하지 않는다."]
else:lines+=['잡음 실행 결과는 아직 이 분석의 입력에 포함되지 않았다. 결정론적 통과를 잡음 통과로 간주하지 않는다. 완료 후 같은 스크립트를 다시 실행해 별도 조건으로 합산한다.']
if 'noise_comparison' in result:
 c=result['noise_comparison'];lines += ['', '잡음은 각60Hz 제어에서 선택4축(index1_x,index1_z,PIP,DIP)의 atanh(rawgoal) 공간에 넣는 무차원 Normal이다. 유효 sigma4='+str(c['effective_latent_std4_dimensionless'])+'이며 각도 rad값이 아니다. env0 전체354끝점의 결정론적 대비 실제decoded목표차 RMS(rad)는'+str(c['env0_realized_goal_delta_rms_rad'])+'이고, 도 단위는'+str(c['env0_realized_goal_delta_rms_deg'])+'다. 이값은 해당비선형변환·기준목표·샘플에따른측정값이며 sigma의보편적각도환산이아니다.', '', '과거 noisy_reference 전체3음2/128과 현재34/128은 동일seed7·동일Normal128×4 잡음stream SHA256 '+c['noise_stream_sha256_v2']+' 및 저장env0..3 scaled_noise byte-exact를 확인했다. 조건부비교는가능하나 과거 runtime경로/관측계약과현재경로차이가있고 현재결정론적baseline동등성은별도로확인한것이다. 또한 과거대비N열기와closing lead둘이함께다르므로32개증가를lead하나의인과효과로분리할수없다. 음악gate는현재도실패이며A해제는과거117/128에서현재102/128로낮아졌다.', '', '잡음실패는모든음에서wrong평균0과missing증가로나타난다. 결정론적closing회복만으로처음A와후속B의지속접촉취약성이해결되지않았다. env0 audible 저장끝점 candidate비율은A4 0.9091/B7 0.8696/B8 0.8095이며거리최대0.766/0.828/0.333mm로이동·접촉판정이끊긴다. 이대표값만으로128환경실패의전체기하원인을확정하지않는다. 원A해제미달26개와음별달성실패의교차는analysis.json에별도로보존했다.', '', '다음단일검증제안: V2일정/목표/PD/원잡음draw를그대로재생하면서 index1_x에실제로가하는잡음만0으로하는128시도를한번비교한다. 다른3축에는현재와동일한draw를넣고draw자체는128×4로유지한다. env0에서MCP index1_x의목표변동및추종오차가함께늘어나는관찰을근거로한성분분리검증이며, 현재원인을확정한해결책이나std검색이아니다. 성공기준은원음별/전체/해제gate및cost/물리실패,특히Aclean과해제102/128의변화다. 새실행은이분석에서수행하지않았다.']
lines+=['','## 보상9항·cost와 무결성','','| 조건 | 총reward합 | cost합 | wall초 |','|---|---:|---:|---:|']
for n,r in result['runs'].items():lines.append(f"| {n} | {r['reward_sum']:.9f} | {r['cost_sum']:.9f} | {r['report']['wall_s']:.3f} |")
lines+=['','| 보상항 | '+' | '.join(result['runs'])+' |','|---|'+'---:|'*len(result['runs'])]
for k in result['runs']['v1_baseline']['reward_components']:lines.append('| '+k+' | '+' | '.join(f"{r['reward_components'][k]:.9f}" for r in result['runs'].values())+' |')
lines+=['','원total reward와 각항합은float누적순서에따른작은반올림차이를가질수있다. analysis.json은음별실패포함분모·release교차·보상9항·원acceptance·onset전후각도·구간별표면을보존한다. verification.json은입력전후SHA256과실제8개자체검사(모두통과)를기록한다. 새 GPU실행·NN생성·학습·각도grid/std검색은모두0이며원자료/활성소스/봉인입력을수정하지않았다. 이분석은고정기타·검지3음·대표env0/표면4환경범위이며J33·다른손가락·자유기타·67음·다른seed완료를뜻하지않는다.']
(OUT/'RESULTS.md').write_text('\n'.join(lines)+'\n')
