"""Supplementary signal/resource analysis after all fixed-budget jobs finish."""
from pathlib import Path
import json,csv,collections,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parents[1];A=D/'분석';B=A/'신호자원_추가분석';W=D/'작업자료';S=W/'source_snapshot'
def csvwrite(p,rows):
 with p.open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 assert not B.exists();B.mkdir();rows=[];rewards=[];curves=[]
 for h in (32,64,128):
  name=f'H{h}_seed7';stage=S/f'study_outputs/학습/{name}/attempt01/J';r=json.loads((stage/'report.json').read_text());assert r['completed'] and r['transitions']==16777216;m=[json.loads(z) for z in (stage/'learning_metrics.jsonl').read_text().splitlines()];p=json.loads((W/(name+'_receipt.json')).read_text());n=sum(x['transitions'] for x in m);rewardkeys=list(m[0]['reward_component_means']);entry=dict(condition=name,transitions=n,updates=len(m),collection_s=sum(x['collection_s'] for x in m),update_interval_including_commit_s=sum(x['update_s'] for x in m),parent_measured_wall_s=p['wall_s'],end_to_end_transitions_per_s=n/p['wall_s'],collection_transitions_per_s=n/sum(x['collection_s'] for x in m),sampled_peak_global_gpu_used_MiB=p['peak_gpu_total_used_MiB'],sampled_peak_process_tree_RSS_GiB=p['peak_process_tree_rss_bytes']/1024**3,actor_KL_retries=sum(x['kl_retries'] for x in m),last_LR=m[-1]['actor_lr'],min_LR=min(x['actor_lr'] for x in m),max_KL=max(x['analytic_kl'] for x in m),median_clip=float(np.median([x['diagnostics']['post_update']['clip_fraction'] for x in m])),max_accepted_actor_grad_preclip=max(x['diagnostics']['minibatches']['actor_accepted']['max'].get('grad_norm_pre_clip',0) for x in m),last_reward_EV=m[-1]['diagnostics']['post_update']['critics']['reward']['explained_variance'],last_cost_EV=m[-1]['diagnostics']['post_update']['critics']['cost']['explained_variance']);rows.append(entry)
  rw=dict(condition=name,**{k:sum(x['reward_component_means'][k]*x['transitions'] for x in m)/n for k in rewardkeys});rewards.append(rw)
  for end in (4194304,8388608,12582912,16777216):
   selected=[x for x in m if end-4194304<x['curriculum']['committed_transitions']<=end];nn=sum(x['transitions'] for x in selected);assert nn==4194304;curves.append(dict(condition=name,end_transitions=end,**{k:sum(x['reward_component_means'][k]*x['transitions'] for x in selected)/nn for k in rewardkeys}))
 csvwrite(B/'자원속도.csv',rows);csvwrite(B/'보상항_경험가중평균.csv',rewards);csvwrite(B/'보상항_동일사분기.csv',curves)
 fig,axes=plt.subplots(3,3,figsize=(13,10))
 for ax,k in zip(axes.flat,[k for k in rewards[0] if k!='condition']):
  for h in (32,64,128):
   rr=[r for r in curves if r['condition']==f'H{h}_seed7'];ax.plot([r['end_transitions'] for r in rr],[r[k] for r in rr],marker='o',label=f'H{h}')
  ax.set_title(k,fontsize=9);ax.grid(alpha=.2);ax.legend(fontsize=7)
 fig.suptitle('Actual logged reward means, equal-experience quarter weighted means');fig.tight_layout();fig.savefig(B/'보상항비교.png',dpi=150);plt.close(fig)
 lines=['# 신호·자원 추가 분석','','모든 본 학습이 완료된 원래 로그만 사용한다. 추가 학습이나 물리 실행은 없다. 초기 메모리 검사 전이는 제외한다.','', '|H|실제 경과 초|수집 전이/초|전체 전이/초|샘플 GPU전체 최고 MiB|프로세스 RSS합 최고 GiB|마지막 LR|KL 재시도|','|---|---:|---:|---:|---:|---:|---:|---:|']
 for x in rows:lines.append(f"|{x['condition']}|{x['parent_measured_wall_s']:.1f}|{x['collection_transitions_per_s']:.1f}|{x['end_to_end_transitions_per_s']:.1f}|{x['sampled_peak_global_gpu_used_MiB']:.0f}|{x['sampled_peak_process_tree_RSS_GiB']:.3f}|{x['last_LR']:.8g}|{x['actor_KL_retries']}|")
 lines+=['','GPU최고는2초 주기 전역 사용량의 관찰 최고치로 그래픽 작업을 포함하며 tensor allocation의 정확한 최고가 아니다. RSS합은 프로세스별 공유 페이지를 중복 포함할 수 있어 실제 물리 RAM의 private 합과 같지 않다. update_s는PPO와commit 등을 포함한 업데이트 구간이다. CPU·GPU·직렬화·전송을 한 kernel 처리량으로 치환하지 않았다.','','9항은 실제 learning_metrics의 창 평균을 전이 수로 가중해 집계했다. raw 시점별 보상을 역산한 값이 아니며 곡 구간별 보상으로 재배치하지 않았다. 비할인 접근 보상 평균의 부호만으로 potential shaping의 오류나 gradient 지배를 결론 내리지 않는다. 보상·비용별 실제 gradient norm/cosine은 원본에 없어 제공하지 않는다.','','![보상항 비교](보상항비교.png)','','실제33축 latent std는 상위 탐색표준편차.csv의0·1/4·1/2·3/4·최종 모델에서 읽었다. entropy도latent Gaussian 진단이며 물리각 탐색 크기와 같지 않다. 기본 LR·초기 std 설정이 같아도 원래 KL 재시도와 학습에 따른 실제 LR/std 경로는 달라질 수 있다. 이번 비교에서 이 규칙이나 수치를 임의 조정하지 않았다.']
 (B/'REPORT.md').write_text('\n'.join(lines)+'\n');print('supplementary resource/reward analysis complete')
if __name__=='__main__':main()
