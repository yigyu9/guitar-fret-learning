"""Available native-ledger release cross tables and saved oldtarget versus N direction."""
from pathlib import Path
import importlib.util
import json

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('release_cross_complete_guard',HERE/'analyze.py');audit=importlib.util.module_from_spec(s);s.loader.exec_module(audit);audit.preflight()
import numpy as np
import torch

BASE=HERE.parent;ORIGINAL=BASE.parent;inputs={}
def read(path):
    import hashlib
    path=Path(path);inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();return json.loads(path.read_text())
def npz(path):
    import hashlib
    path=Path(path);inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();return dict(np.load(path,allow_pickle=False))

result={};assert not torch.cuda.is_available()
for stage,folder in [('collect',ORIGINAL/'runs/collect'),('evaluate',BASE/'runs/evaluate')]:
    rows=read(folder/'evaluation.json')['episodes'];assert len(rows)==128
    notes=[r['notes'][0] for r in rows];assert all(n['source_index']==4 for n in notes)
    result[stage]=dict(attempts=128,achieved_by_released={str(a)+'_'+str(r):sum(n['achieved']==a and n['released']==r for n in notes) for a in (False,True) for r in (False,True)},
        positive_native_audible_clean_by_released={str(c)+'_'+str(r):sum((n['note']['clean']>0)==c and n['released']==r for n in notes) for c in (False,True) for r in (False,True)},
        native_ever_field_saved=any('ever' in n['note'] for n in notes),
        scope='clean>0 is saved positive audible clean duration, not an exported native ever/contact-fall history')
short=read(ORIGINAL/'cpu_inputs/settings.json')['song']['short_learning'];d=npz(BASE/'runs/evaluate/observations4.npz');m=d['phase']==2
N=np.array(short['reference_release_schedule']['negative_selected_rad'],dtype=np.float32)
reference=np.array(short['reference_release_schedule']['reference_selected_rad'],dtype=np.float32)
old=torch.from_numpy(d['old_target_rad'][m]);time=torch.from_numpy(d['start_clock'][m]).to(torch.float64)/240+1/60
start=short['view']['source_targets'][0]['end_s']-short['view']['score_offset_s']
weight=((time-start)/.10).clamp(0,1).to(old)
desired=torch.from_numpy(reference)[None]+weight[:,None]*(torch.from_numpy(N-reference)[None])
def summary(delta):
    delta=delta.numpy();return dict(mean_deg=np.rad2deg(delta).mean(0).tolist(),min_deg=np.rad2deg(delta).min(0).tolist(),max_deg=np.rad2deg(delta).max(0).tolist(),
        negative_counts4=(delta<0).sum(0).tolist(),positive_counts4=(delta>0).sum(0).tolist(),zero_counts4=(delta==0).sum(0).tolist())
result['NN_release_24_saved_precontrols']=dict(samples=int(m.sum()),old_minus_fixed_N=summary(old-torch.from_numpy(N)),old_minus_instant_requested_ramp=summary(old-desired),
    scope='native joint signed coordinate; below fixedN is not anatomical opening or physical separation; instantaneous reference request is still interpolating during .10s')
t=npz(BASE/'runs/evaluate/trace_env0_episode0.npz');after=t['time_s']>start
off=np.flatnonzero(after&~t['candidate'][:,0]);on=np.flatnonzero(after&t['candidate'][:,0])
result['env0_saved60']=dict(first_post_A_candidateoff_s=float(t['time_s'][off[0]]) if len(off) else None,
    candidate_on_after_end_samples=len(on),scope='saved60Hz endpoints only; native release0 does not mean no later contact loss or no unloading')
result['input_sha256']=inputs
out=HERE/'results_v1/release_cross.json';assert not out.exists();out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
