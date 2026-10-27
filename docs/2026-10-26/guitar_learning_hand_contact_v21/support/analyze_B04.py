"""Summarize the predeclared B0.04 coefficient experiment without refitting gates."""
import json,hashlib
from pathlib import Path
import torch
P=Path(__file__).resolve().parents[1]
rows=[json.loads(s) for s in (P/'eval_full_B04/episodes.jsonl').read_text().splitlines()]
b=[]
for f in range(4):
 w=[e['left_episode_diagnostics']['recovery']['by_finger'][f] for e in rows]
 den=sum(r['planned_s'] for r in w)
 b.append(dict(planned_s=den,in_band_s=sum(r['in_band_s'] for r in w),occupancy=sum(r['in_band_s'] for r in w)/den if den else None))
a=torch.load(P/'train_full_100/initial.pt',map_location='cpu',weights_only=False)['model'];c=torch.load(P/'train_full_B04_100/initial.pt',map_location='cpu',weights_only=False)['model']
identical=list(a)==list(c) and all(torch.equal(v,c[k]) for k,v in a.items());assert identical
r=json.loads((P/'eval_full_B04/report.json').read_text())
result=dict(completed=r['completed'],mean_achieved=r['mean_achieved_notes'],safe=r['safe_first'],episodes=len(rows),B_by_finger=b,initial_tensors_identical=identical,model_tensor_count=len(a),default_rate_per_s=.02,decision='retain0.02; no support for doubling under this diagnostic budget',limitation='One seed100updates128env; not a long-training convergence or causal statistical result')
(P/'support/B04_analysis.json').write_text(json.dumps(result,indent=2))
with (P/'COMPARISON_RESULTS.md').open('a') as f:f.write('\n추가 B 계수 비교: 같은 초기72모델 텐서·seed7·100업데이트에서 .04/초 조건은 평균0.344/67·안전128/128, 고정 B 점유율은 '+str([round(100*x['occupancy'],2) for x in b])+'%였다. .02 조건의5.148/67보다 낮아 기본 .02를 유지한다. 단일 seed의 짧은 비교이며 장기 수렴을 판단한 것은 아니다. 자세한 값은 `support/B04_analysis.json`을 따른다.\n')
print(json.dumps(result))
