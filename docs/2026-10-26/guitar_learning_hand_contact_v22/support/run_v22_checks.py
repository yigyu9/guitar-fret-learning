"""Sequential fresh v22 integration and short learning; source must stay pinned."""
import os,json,subprocess,time
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-26/guitar_learning_hand_contact_v22';py='/home/ajou/miniconda3/envs/rl38/bin/python'
records=[]
def execute(label,cmd):
 print('START',label,flush=True);start=time.time()
 with (P/'support'/(label+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=R,env=os.environ,stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(label=label,code=r.returncode,wall_s=time.time()-start));(P/'support/progress.json').write_text(json.dumps(records,indent=2))
 print('END',label,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
def train(out,updates,envs,resume=None):
 cmd=[py,'-B','-m','guitar_learning.train','--hand','left','--size','large','--num-envs',str(envs),'--horizon','32','--updates',str(updates),'--seed','7','--out',str(P/out)]
 if resume:cmd+=['--resume',str(P/resume/'final.pt')]
 return cmd
execute('smoke1024',train('smoke1024',2,1024))
execute('resume1024',train('resume1024',1,1024,'smoke1024'))
execute('train_full_100',train('train_full_100',100,128))
execute('inspect_full',[py,'-B','-m','guitar_learning.tool.inspect_gpu_training_log','--run',str(P/'train_full_100')])
execute('evaluate_full',[py,'-B','-m','guitar_learning.tool.validation.evaluate_hand_contact','--run',str(P/'train_full_100'),'--out',str(P/'eval_full'),'--video'])
print('ALL_V22_CHECKS_COMPLETE',flush=True)
