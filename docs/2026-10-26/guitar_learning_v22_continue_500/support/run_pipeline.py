"""Resume unchanged v22 for500 updates, then inspect and evaluate its final policy."""
import json,os,subprocess,time,hashlib
from pathlib import Path
R=Path('/home/ajou/yigyu/3');P=Path(__file__).resolve().parents[1];py='/home/ajou/miniconda3/envs/rl38/bin/python'
launch=json.loads((P/'support/launch_inputs.json').read_text());resume=Path(launch['resume'])
assert hashlib.sha256(resume.read_bytes()).hexdigest()==launch['sha256']
m=json.loads(Path(launch['source_manifest']).read_text())
assert all(hashlib.sha256(Path(i['path']).read_bytes()).hexdigest()==i['sha256'] for i in m)
records=[]
def execute(label,cmd):
 print('START',label,flush=True);start=time.time()
 with (P/'support'/(label+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=R,env=os.environ,stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(stage=label,code=r.returncode,wall_s=time.time()-start,command=cmd));(P/'support/progress.json').write_text(json.dumps(records,indent=2))
 print('END',label,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
execute('train',[py,'-B','-m','guitar_learning.train','--hand','left','--physics','gpu','--size','large','--num-envs','128','--horizon','32','--seed','7','--updates','500','--resume',str(resume),'--out',str(P/'train')])
execute('inspect',[py,'-B','-m','guitar_learning.tool.inspect_gpu_training_log','--run',str(P/'train')])
execute('evaluate',[py,'-B','-m','guitar_learning.tool.validation.evaluate_hand_contact','--run',str(P/'train'),'--out',str(P/'eval_final'),'--video'])
print('ALL_CONTINUATION_STAGES_COMPLETE',flush=True)
