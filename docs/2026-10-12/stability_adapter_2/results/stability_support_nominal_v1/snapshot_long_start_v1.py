"""Read-only startup evidence; the running learner's live state is not sealed."""
import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
import torch
P=Path(__file__).resolve().parent;R=P/'long_on_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def equal(a,b):
 if torch.is_tensor(a):return torch.is_tensor(b) and torch.equal(a,b)
 if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return a==b
source=P/'smoke_on_v2/checkpoints/update_000001.pt';initial=R/'checkpoints/initial_000000.pt'
a=torch.load(source,map_location='cpu',weights_only=True);b=torch.load(initial,map_location='cpu',weights_only=True)
data=(R/'training.jsonl').read_bytes();prefix=data[:data.rfind(b'\n')+1]
with (P/'long_training_prefix_v1.jsonl').open('xb') as f:f.write(prefix)
entries=[json.loads(s) for s in prefix.splitlines()];pid=int((P/'long_on_v1.pid').read_text())
process=subprocess.run(['ps','-p',str(pid),'-o','pid=,etime=,args='],capture_output=True,text=True)
checks={'model_exact_resume':equal(a['model'],b['model']),'Adam_exact_resume':equal(a['optimizer'],b['optimizer']),
 'counters_resumed':a['updates']==b['updates']==1 and a['transitions']==b['transitions']==256,
 'new_updates_observed':len(entries)>0 and entries[-1]['update']>1,
 'learner_alive':process.returncode==0 and 'run_deadline_training_v8' in process.stdout,
 'logged_KL_budgets':all(0<=r['ppo']['final_analytic_kl']<=.02 and not r['ppo']['RMS_updated'] for r in entries)}
with (P/'long_start_snapshot_v1.json').open('x') as f:json.dump({'utc':datetime.now(timezone.utc).isoformat(),
 'scope':'startup and complete training-log prefix only; running learner, future checkpoints, unsaved weights and deadline outcome not sealed',
 'checks_passed':all(checks.values()),'checks':checks,'learner_pid':pid,'process':process.stdout,
 'new_log_entries':len(entries),'latest_update':entries[-1]['update'],'latest_transitions':entries[-1]['transitions'],
 'source_checkpoint':str(source),'source_sha256':sha(source),'initial_checkpoint':str(initial),'initial_sha256':sha(initial),
 'training_prefix_sha256':sha(P/'long_training_prefix_v1.jsonl'),'producer_sha256':sha(__file__)},f,indent=2)
print('startup checks',all(checks.values()),'latest update',entries[-1]['update'])
