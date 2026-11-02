from pathlib import Path
import sys,os,subprocess,json
D=Path(__file__).resolve().parents[1];R=next(p for p in D.parents if (p/'scripts/tab2body.py').exists());runtime=D/'도구/runtime.py';env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',MAX_JOBS='2',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1');base=[sys.executable,str(R/'scripts/tab2body.py'),'--cache-root','/home/yigyu/.cache/tab2body','run','-u',str(runtime)]
a=D/'진단/smoke_train_final/J/final.pt';b=D/'진단/smoke_resume_final';c=D/'진단/smoke_evaluate_final'
for name,args in [('smoke_resume_final',['train','--updates','1','--seed','7','--num-envs','64','--resume',str(a),'--out',str(b)]),('smoke_evaluate_final',['evaluate','--num-envs','32','--action-mode','mean','--checkpoint',str(b/'J/final.pt'),'--out',str(c)])]:
 with (D/'로그'/f'{name}.log').open('w') as log:subprocess.run(base+args,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
print('strict resume and evaluation stages completed')
