"""Read-only verification of source archives, final logs, and native media."""
from pathlib import Path
import hashlib,json,math,subprocess
import numpy as np
import torch
R=Path('/home/ajou/yigyu/3');P=Path(__file__).resolve().parents[1]
launch=json.loads((P/'support/launch_inputs.json').read_text());m=json.loads(Path(launch['source_manifest']).read_text())
assert all(hashlib.sha256(Path(i['path']).read_bytes()).hexdigest()==i['sha256'] and hashlib.sha256((R/i['snapshot']).read_bytes()).hexdigest()==i['sha256'] for i in m)
a=json.loads((R/'guitar_learning/archive/20261026_before_thumb_contact_v22/manifest.json').read_text());assert all(hashlib.sha256((R/i['archive']).read_bytes()).hexdigest()==i['sha256'] for i in a)
r=json.loads((P/'train/report.json').read_text());j=r['journal'];assert r['completed'] and r['lifecycle_verified'] and not r['changed_inputs'] and not r['missing_import_pins'];assert all(j[k]==2048000 for k in ('sampled','logged','durable','committed')) and not j['discarded']
backend=json.loads((P/'train/gpu_scene_final.json').read_text())
assert backend['physx_use_gpu'] and backend['use_gpu_pipeline'] and backend['num_envs']==128
metrics=[json.loads(l) for l in (P/'train/learning_metrics.jsonl').read_text().splitlines()];assert len(metrics)==500
ckpt=torch.load(P/'train/final.pt',map_location='cpu',weights_only=False)
assert ckpt['updates']==600
assert json.loads((P/'resume_verification.json').read_text())['completed']
checkpoints=[json.loads(l) for l in (P/'train/checkpoint_manifest.jsonl').read_text().splitlines()]
assert len(checkpoints)==3
for item in checkpoints:
 file=P/'train'/item['path']
 assert file.stat().st_size==item['bytes'] and hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256']
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
for file in ['eval_final/hand.mp4','eval_final/fullbody.mp4']:
 path=P/file;info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(path)]))['streams'][0];vids[file]=dict(info,sha256=hashlib.sha256(path.read_bytes()).hexdigest());assert info['r_frame_rate']=='30/1'
capture=json.loads((P/'eval_final/capture_metadata.json').read_text())
result=dict(gpu_backend={k:backend[k] for k in ('device','num_envs','physx_use_gpu','use_gpu_pipeline','tensor_devices')},checkpoints=checkpoints,capture=capture,completed=True,active_and_frozen_python=len(m),archive_verified=len(a),finite_checkpoint_tensors=finite,journal={k:j[k] for k in ('sampled','logged','durable','committed','discarded')},
 training_log=dict(updates=len(metrics),max_post_update_analytic_kl=max(x['analytic_kl'] for x in metrics),max_attempted_kl=max(x['max_attempted_kl'] for x in metrics),kl_retries=sum(x['kl_retries'] for x in metrics),final_actor_lr=metrics[-1]['actor_lr'],mean_collection_s=sum(x['collection_s'] for x in metrics)/500,mean_ppo_s=sum(x['update_s'] for x in metrics)/500),videos=vids,
 limitations=['One-seed continued training, not general convergence or musical performance certification.','Video env0 was declared before evaluation, not selected by score.','Video covers predeclared env0 first episode; its last sampled frame may precede the final60Hz endpoint; see capture metadata and stream duration.','Thumb resultant geometry is a contact candidate, not contact-pair or pressure certification.'])
(P/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
