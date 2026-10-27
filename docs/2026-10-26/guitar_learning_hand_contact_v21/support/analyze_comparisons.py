"""Read complete first-song evaluation cohorts; retain fixed-score denominators."""
from pathlib import Path
import json,hashlib,collections
import numpy as np
import torch
from guitar_learning.song.task import make_task
from guitar_learning.training.gpu_log_records import iter_episode_rows

ROOT=Path('/home/ajou/yigyu/3');PHASE=ROOT/'docs/2026-10-26/guitar_learning_hand_contact_v21'
task=make_task(ROOT/'data/song_bundles/05_BN2-131-B_solo',pre_roll_s=3.,tail_s=.5)
D=sum(t.end_s-t.onset_s for t in task.targets)
ARMS=('collision_only','recovery','full')
results={};initials={}
for arm in ARMS:
 run=PHASE/('train_'+arm+'_100');ev=PHASE/('eval_'+arm)
 report=json.loads((ev/'report.json').read_text());assert report['completed'] and report['first_episodes']==128
 rows=[json.loads(line) for line in (ev/'episodes.jsonl').read_text().splitlines()]
 assert sorted(e['env_id'] for e in rows)==list(range(128))
 def aggregate(es):
  n=len(es)
  if not n:return dict(episodes=0)
  def mean(f):return sum(f(e) for e in es)/n
  b=[];extreme=[]
  for f in range(4):
   windows=[e['left_episode_diagnostics']['recovery']['by_finger'][f] for e in es]
   planned=sum(w['planned_s'] for w in windows);observed=sum(w['observed_s'] for w in windows);band=sum(w['in_band_s'] for w in windows)
   b.append(dict(planned_s=planned,observed_s=observed,in_band_s=band,credited_occupancy=band/planned if planned else None,observed_occupancy=band/observed if observed else None))
   forpress={}
   for mode in ('all','idle','press'):
    valid=sum(e['left_episode_diagnostics']['extreme_combinations'][mode]['valid_s'][f] for e in es)
    forpress[mode]={key:sum(e['left_episode_diagnostics']['extreme_combinations'][mode][key][f] for e in es)/valid if valid else None for key in ('index_like_s','pinky_like_s','distal_excess_s','any_s')}
   extreme.append(forpress)
  thumb=[e['left_episode_diagnostics']['thumb_support'] for e in es]
  seen=sum(e['sampled_s'] for e in thumb);near=sum(e['near_geometry_s'] for e in thumb)
  return dict(episodes=n,mean_achieved=mean(lambda e:e['song']['left_success_count']),
    safe=sum(e['reason']=='timeline_complete' and e['left_curriculum']['full_safe'] for e in es),
    failure_reasons=dict(collections.Counter(reason for e in es for reason in e['failure_reasons'])),
    clean_score_fraction=mean(lambda e:sum(e['left_note_ledger']['values']['clean'])/D),
    wrong_score_fraction=mean(lambda e:sum(e['left_note_ledger']['values']['wrong'])/D),
    missing_score_fraction=mean(lambda e:sum(e['left_note_ledger']['values']['missing'])/D),
    B_by_finger=b,extreme_by_finger=extreme,
    thumb=dict(observed_s=seen,near_s=near,near_fraction_observed=near/seen if seen else None,
       near_fraction_fixed_song=near/(n*task.duration_s),
       mean_quality=sum(e['quality_integral'] for e in thumb)/seen if seen else None,
       mean_force_N=mean(lambda e:e['left_episode_diagnostics']['thumb_support']['native_thumb3_net_force_mean_N']),
       maximum_force_N=max(e['native_thumb3_net_force_max_N'] for e in thumb)))
 safe=[e for e in rows if e['reason']=='timeline_complete' and e['left_curriculum']['full_safe']]
 training=json.loads((run/'report.json').read_text())
 results[arm]=dict(all_first=aggregate(rows),full_safe_first=aggregate(safe),
    training=dict(completed=training['completed'],transitions=training['transitions'],episodes=training['completed_episodes'],wall_s=training['wall_s'],changed_inputs=training['changed_inputs']),
    env0=dict(reason=rows[0]['reason'],task_time_s=rows[0]['task_time_s'],achieved=rows[0]['song']['left_success_count']),
    report_sha256=hashlib.sha256((ev/'report.json').read_bytes()).hexdigest())
 initials[arm]=torch.load(run/'initial.pt',map_location='cpu',weights_only=False)['model']
ref=initials[ARMS[0]]
identical={a:list(ref)==list(m) and all(torch.equal(v,m[k]) for k,v in ref.items()) for a,m in initials.items()}
assert all(identical.values()),'Comparison initial models differ'
result=dict(results=results,initial_model_tensors_identical=identical,budget=dict(num_envs=128,updates=100,horizon=32,seed=7,size='large'),
 limitations=['One training seed; short diagnostic budget, not validated long-training performance.','Clean/wrong/missing use whole-score audible time as fixed denominator, including unobserved failure tails. They need not sum to1.','Thumb net forces are not thumb-neck pair pressure or guitar support proof.','B occupancy uses the same score-only windows in every arm; conditional/safe-only summaries are separate.'])
(PHASE/'comparison_analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
lines=['# v21 짧은 비교 학습·고정 평가','', '세 조건 모두 새 large551·seed7·128환경·H32·100업데이트다. 초기 모델의 모든 tensor가 동일함을 확인했다. 각 조건의 첫 종료곡128개를 평가했고 실패를 분모에 포함했다. 독립 학습 seed 반복은 아니다.','',
 '| 조건 | 평균 달성/67 | 안전 완주/128 | clean 고정음길이 비율 | B 점유율(검/중/약/소, 고정창) | 엄지 근접(고정곡시간) |', '|---|---:|---:|---:|---|---:|']
labels=dict(collision_only='충돌만·이전 시간창',recovery='새 B/추종 전환',full='B/추종+엄지')
for arm in ARMS:
 r=results[arm]['all_first'];b='/'.join('—' if x['credited_occupancy'] is None else f"{100*x['credited_occupancy']:.1f}%" for x in r['B_by_finger'])
 lines.append(f"| {labels[arm]} | {r['mean_achieved']:.3f} | {r['safe']} | {100*r['clean_score_fraction']:.2f}% | {b} | {100*r['thumb']['near_fraction_fixed_song']:.2f}% |")
lines+=['','B 창은 악보로 고정하며1초 복귀 여유는 잠정 진단 예산이다. 음 달성은 기하·하중 clean 유지 판정이며 실제 소리의 성공이 아니다. 엄지 근접은 안쪽 표면의 거리·방향 측정이며 접촉쌍·압력이나 보조 지지 효과를 인증하지 않는다.','',
 '원시·안전완주별 결과와 극단 조합·오압현·누락·엄지 하중은 `comparison_analysis.json`을 따른다. 결과 영상은 `eval_full/hand.mp4`, `eval_full/fullbody.mp4`이며 사전 지정env0의 첫 에피소드다. 좋은 점수로 선택한 영상이 아니다.']
(PHASE/'COMPARISON_RESULTS.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({a:results[a]['all_first']['mean_achieved'] for a in ARMS}))
