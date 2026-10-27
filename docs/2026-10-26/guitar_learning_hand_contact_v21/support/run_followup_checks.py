"""Finish native return-budget checks; add the planned B0.04 arm only if needed."""
import json,os,subprocess,time
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-26/guitar_learning_hand_contact_v21';py='/home/ajou/miniconda3/envs/rl38/bin/python'
while True:
 p=P/'support/comparison_progress.json'
 rows=json.loads(p.read_text()) if p.exists() else []
 if any(r['code'] for r in rows):raise SystemExit('Primary comparison failed')
 if any(r['arm']=='full' and r['stage']=='evaluate' for r in rows):break
 time.sleep(5)
records=[]
def execute(label,cmd):
 print('START',label,flush=True);start=time.time()
 with (P/'support'/('followup_'+label+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=R,env=os.environ,stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(label=label,code=r.returncode,wall_s=time.time()-start));(P/'support/followup_progress.json').write_text(json.dumps(records,indent=2))
 print('END',label,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
for thumb in ('held','return_initial'):
 execute('return_'+thumb,[py,'-B','-m','guitar_learning.tool.validation.hand_contact_probe','--out',str(P/('B_return_'+thumb)),'--controls','900','--video','--tape',str(P/'support'/('B_return_thumb_'+thumb+'.npz'))])
execute('primary_analysis',[py,'-B',str(P/'support/analyze_comparisons.py')])
e=[json.loads(s) for s in (P/'eval_full/episodes.jsonl').read_text().splitlines()]
b=[]
for f in range(4):
 w=[r['left_episode_diagnostics']['recovery']['by_finger'][f] for r in e];den=sum(r['planned_s'] for r in w);b.append(sum(r['in_band_s'] for r in w)/den if den else None)
needed=any(x is not None and x<.8 for x in b)
(P/'support/B04_decision.json').write_text(json.dumps(dict(full_fixed_B_occupancy=b,threshold=.8,needed=needed,reason='Planned weak0.04 coefficient comparison when0.02 does not attain the provisional return occupancy criterion; not an automatic default change'),indent=2))
if needed:
 execute('B04_train',[py,'-B',str(P/'support/run_B04.py')])
 execute('B04_inspect',[py,'-B','-m','guitar_learning.tool.inspect_gpu_training_log','--run',str(P/'train_full_B04_100')])
 execute('B04_evaluate',[py,'-B','-m','guitar_learning.tool.validation.evaluate_hand_contact','--run',str(P/'train_full_B04_100'),'--out',str(P/'eval_full_B04')])
print('ALL_FOLLOWUP_CHECKS_COMPLETE',flush=True)
