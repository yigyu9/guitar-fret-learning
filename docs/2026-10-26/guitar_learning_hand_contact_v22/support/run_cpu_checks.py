import json,subprocess,time,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];old=json.loads((P.parent/'guitar_learning_hand_contact_v21/support/cpu_checks.json').read_text());names=[r['module'].replace('test_gpu_hand_contact_v21','test_gpu_hand_contact_v22') for r in old]
names=list(dict.fromkeys(names+['test_thumb_contact_probe','test_left_curriculum_runtime']))
rows=[]
for name in names:
 start=time.monotonic();r=subprocess.run(['/home/ajou/miniconda3/envs/rl38/bin/python','-B','-m','unittest','-q','guitar_learning.tests.'+name],capture_output=True,text=True,env=os.environ)
 row=dict(module=name,code=r.returncode,wall_s=time.monotonic()-start,output=r.stdout+r.stderr);rows.append(row);(P/'support/cpu_checks.json').write_text(json.dumps(rows,indent=2));print(name,r.returncode,flush=True)
print('ALL_CPU_CHECKS_FINISHED',flush=True)
if any(x['code'] for x in rows):raise SystemExit(1)
