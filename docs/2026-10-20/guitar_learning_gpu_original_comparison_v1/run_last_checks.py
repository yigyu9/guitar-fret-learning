import json,os,subprocess,sys
from pathlib import Path
base=Path(__file__).resolve().parent
rows=[]
for name in ('subscene_one','iterations'):
 command=[sys.executable,'-B','-u',str(base/'variant_probe.py'),'--variant',name,'--out',str(base/name)]
 with (base/(name+'.log')).open('x') as stream:
  result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
 rows.append(dict(case=name,returncode=result.returncode,command=command))
 print(name,'exit',result.returncode,flush=True)
with (base/'last_check_processes.json').open('x') as stream:json.dump(rows,stream,indent=2)
