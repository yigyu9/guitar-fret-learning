"""Read-only verification of source archives, final logs, and native media."""
from pathlib import Path
import hashlib,json,math,subprocess
import numpy as np
import torch
R=Path('/home/ajou/yigyu/3');P=Path(__file__).resolve().parents[1]
m=json.loads((P/'support/source_v22_final_manifest.json').read_text())
assert all(hashlib.sha256(Path(i['path']).read_bytes()).hexdigest()==i['sha256'] and hashlib.sha256((R/i['snapshot']).read_bytes()).hexdigest()==i['sha256'] for i in m)
a=json.loads((R/'guitar_learning/archive/20261026_before_thumb_contact_v22/manifest.json').read_text());assert all(hashlib.sha256((R/i['archive']).read_bytes()).hexdigest()==i['sha256'] for i in a)
r=json.loads((P/'train_full_100/report.json').read_text());j=r['journal'];assert r['completed'] and r['lifecycle_verified'] and not r['changed_inputs'] and not r['missing_import_pins'];assert all(j[k]==409600 for k in ('sampled','logged','durable','committed')) and not j['discarded']
metrics=[json.loads(l) for l in (P/'train_full_100/learning_metrics.jsonl').read_text().splitlines()];assert len(metrics)==100
ckpt=torch.load(P/'train_full_100/final.pt',map_location='cpu',weights_only=False)
finite=0
def check(v):
 global finite
 if torch.is_tensor(v):assert bool(torch.isfinite(v).all());finite+=1
 elif isinstance(v,dict):
  for item in v.values():check(item)
 elif isinstance(v,(list,tuple)):
  for item in v:check(item)
check({k:ckpt[k] for k in ('model','actor_optimizer','value_optimizer')})
vids={}
for file in ['eval_full/hand.mp4','eval_full/fullbody.mp4','native_thumb_smooth_tape/native_oblique.mp4']:
 path=P/file;info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(path)]))['streams'][0];vids[file]=dict(info,sha256=hashlib.sha256(path.read_bytes()).hexdigest());assert info['r_frame_rate']=='30/1'
result=dict(completed=True,active_and_frozen_python=len(m),archive_verified=len(a),finite_checkpoint_tensors=finite,journal={k:j[k] for k in ('sampled','logged','durable','committed','discarded')},
 training_log=dict(updates=len(metrics),max_post_update_analytic_kl=max(x['analytic_kl'] for x in metrics),max_attempted_kl=max(x['max_attempted_kl'] for x in metrics),kl_retries=sum(x['kl_retries'] for x in metrics),final_actor_lr=metrics[-1]['actor_lr'],mean_collection_s=sum(x['collection_s'] for x in metrics)/100,mean_ppo_s=sum(x['update_s'] for x in metrics)/100),videos=vids,
 limitations=['Short one-seed learning, no long-training adoption.','Video env0 was declared before evaluation, not selected by score.','Video last frame32.8s versus final physical/control endpoint32.8167s.','Native contact proof uses thumb-only prescribed target tape, not trained policy or contact-pair certification.'])
(P/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
