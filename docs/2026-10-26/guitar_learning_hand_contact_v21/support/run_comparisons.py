"""Sequential, predeclared v21 diagnostic budget; no concurrent GPU scenes."""
import json,os,subprocess,time
from pathlib import Path
ROOT=Path('/home/ajou/yigyu/3');PHASE=ROOT/'docs/2026-10-26/guitar_learning_hand_contact_v21'
python='/home/ajou/miniconda3/envs/rl38/bin/python'
records=[]
for arm in ('collision_only','recovery','full'):
 out=PHASE/('train_'+arm+'_100')
 commands=[('train',[python,'-B','-m','guitar_learning.tool.validation.hand_contact_comparison','--arm',arm,'--updates','100','--num-envs','128','--out',str(out)]),
 ('inspect',[python,'-B','-m','guitar_learning.tool.inspect_gpu_training_log','--run',str(out)]),
 ('evaluate',[python,'-B','-m','guitar_learning.tool.validation.evaluate_hand_contact','--run',str(out),'--out',str(PHASE/('eval_'+arm))]+(['--video'] if arm=='full' else []))]
 for stage,command in commands:
  start=time.time();log=PHASE/'support'/(arm+'_'+stage+'.log')
  print('START',arm,stage,flush=True)
  with log.open('x') as stream:result=subprocess.run(command,cwd=ROOT,env=os.environ,stdout=stream,stderr=subprocess.STDOUT)
  row=dict(arm=arm,stage=stage,code=result.returncode,wall_s=time.time()-start,log=str(log));records.append(row)
  (PHASE/'support/comparison_progress.json').write_text(json.dumps(records,indent=2))
  print('END',arm,stage,result.returncode,flush=True)
  if result.returncode:raise SystemExit(result.returncode)
print('ALL_COMPARISONS_COMPLETE',flush=True)
