"""CPU/CUDA optimizer comparison on the identical recorded native rollout."""
from pathlib import Path
import argparse,json,time,statistics
parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
import isaacgym
import torch
from guitar_learning.policy import Policy
from guitar_learning.ppo import PPOTrainer,PPOConfig
from guitar_learning.recording import digest,write
base=Path(__file__).resolve().parent
p=args.run.resolve();initial=p/'initial.pt';rollout=p/'rollout_first.pt'
torch.set_num_threads(1);torch.backends.cuda.matmul.allow_tf32=False
payload=torch.load(initial,map_location='cpu',weights_only=False);cpu_buffer=torch.load(rollout,map_location='cpu',weights_only=False)
rows=[]
for device in ['cpu','cuda:0']:
 if device.startswith('cuda') and not torch.cuda.is_available():continue
 for repeat in range(3):
  arch=payload['identity']['architecture'];model=Policy(arch['state_dim'],size=arch['size'],contract=arch['contract']).to(device)
  trainer=PPOTrainer(model,PPOConfig(**payload['identity']['config']));trainer.load(initial)
  buffer={k:v.to(device) for k,v in cpu_buffer.items()}
  if device.startswith('cuda'):torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
  begin=time.perf_counter();metrics=trainer.update(buffer)
  if device.startswith('cuda'):torch.cuda.synchronize()
  elapsed=time.perf_counter()-begin
  rows.append(dict(device=device,repeat=repeat,update_s=elapsed,metrics=metrics,allocated_peak_bytes=torch.cuda.max_memory_allocated() if device.startswith('cuda') else None,reserved_peak_bytes=torch.cuda.max_memory_reserved() if device.startswith('cuda') else None))
  del trainer,model,buffer
  print(device,repeat,elapsed,flush=True)
summary={device:statistics.median(r['update_s'] for r in rows if r['device']==device and r['repeat']>0) for device in {r['device'] for r in rows}}
write(base/'update_device_profile.json',dict(source_initial=str(initial),source_rollout=str(rollout),sha256={str(initial):digest(initial),str(rollout):digest(rollout)},rows=rows,warm_median_s=summary,scope='Optimizer only on same recorded native buffer; no new physical data or environment-count performance claim'))
