import hashlib,json,os,subprocess,time
from pathlib import Path
root=Path('/home/ajou/yigyu/3');result=root/'docs/2026-10-26/guitar_learning_active_press_v25';folder=result/'support'
env=dict(os.environ);env['PATH']='/home/ajou/miniconda3/envs/rl38/bin:'+env.get('PATH','');env['LD_LIBRARY_PATH']='/home/ajou/miniconda3/envs/rl38/lib:'+env.get('LD_LIBRARY_PATH','')
manifest=json.loads((folder/'source_manifest.json').read_text());records=[]
base=['/home/ajou/miniconda3/envs/rl38/bin/python','-u','-B','-m','guitar_learning.tool.experiments.active_press_v25.run','train','--num-envs','1024','--max-wall-seconds','300']
for name,updates,extra in [('large1024',2,[]),('resume1024',1,['--resume',str(result/'large1024/J/final.pt')])]:
 assert all(hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'] for x in manifest)
 command=base+['--updates',str(updates),'--out',str(result/name)]+extra
 print('START',name,flush=True);started=time.monotonic()
 with (folder/(name+'.log')).open('x') as out:
  completed=subprocess.run(command,cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT)
 records.append(dict(name=name,code=completed.returncode,wall_s=time.monotonic()-started,command=command));(folder/'large_resume_checks.json').write_text(json.dumps(records,indent=2)+'\n');print('END',name,completed.returncode,flush=True)
 if completed.returncode:raise SystemExit(completed.returncode)
