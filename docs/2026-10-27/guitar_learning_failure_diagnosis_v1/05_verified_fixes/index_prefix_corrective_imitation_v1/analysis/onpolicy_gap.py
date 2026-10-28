"""Offline requests at the two new NN trajectories; no new executed labels."""
from pathlib import Path
import importlib.util
import json
import sys
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('corrective_gap_audit',HERE/'analyze.py');audit=importlib.util.module_from_spec(s);s.loader.exec_module(audit)
audit.complete(audit.read(audit.BASE/'01_launcher.json'),audit.read(audit.BASE/'cpu_inputs/commands.json'))
assert (HERE/'results_v1/comparison.json').is_file()
probe=audit.module('corrective_gap_probe',audit.BASE/'probe.py');sys.path.insert(0,str(probe.grid.ROOT))
import numpy as np
import torch
from guitar_learning.tool.experiments.short_finger_learning import runner
torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
inputs={}
def track(p):p=Path(p);inputs[str(p)]=probe.grid.sha(p);return p
ref=dict(np.load(track(probe.base.COLLECT/'observations4.npz'),allow_pickle=False))
short=probe.source.parent.settings()['song']['short_learning'];schedule=short['reference_release_schedule']
contract=audit.read(track(probe.base.COLLECT/'training_contract.json'))['action']['target_contract']
selected=[contract['joint_names'].index(n) for n in short['learned_action_names']]
base=np.asarray(contract['reference105_rad'])[selected];positive=np.asarray(schedule['reference_selected_rad']);negative=np.asarray(schedule['negative_selected_rad'])
reference=runner.read_reference(track(probe.source.parent.base.pre.INPUTS['index'][1]),short)
result={}
for condition in audit.CONDITIONS:
    d=dict(np.load(track(probe.output(condition,'evaluate')/'observations4.npz'),allow_pickle=False))
    shadow=probe.support().requested_reference(probe,d);request=d['requested_NN_action'];difference=request-shadow
    t=torch.from_numpy(d['start_clock']).to(torch.float64)/240.+1/60.
    fraction=(t/reference['ramp_s']).clamp(0,1).numpy()
    weight=probe.source.parent.support().timing.negative_weight(t,short['view']).numpy()
    desired=base[None]+fraction[:,None]*(positive-base)[None]+weight[:,None]*(negative-positive)[None]
    reference_lookup={(int(e),int(c)):i for i,(e,c) in enumerate(zip(ref['env_id'],ref['start_clock']))}
    counterpart=np.asarray([reference_lookup[(int(e),int(c))] for e,c in zip(d['env_id'],d['start_clock'])])
    target_difference=d['old_target_rad']-ref['old_target_rad'][counterpart]
    state_difference=d['state']-ref['state'][counterpart]
    phases=[]
    for j in range(6):
        m=d['phase']==j;error=difference[m];target_error=d['old_target_rad'][m]-desired[m]
        phases.append(dict(phase=j,samples=int(m.sum()),request_minus_shadow_rms4=np.sqrt(np.mean(error**2,axis=0)).tolist(),
            mean_NN_request4=request[m].mean(0).tolist(),mean_shadow_request4=shadow[m].mean(0).tolist(),
            oldtarget_minus_scheduled_reference_mean_deg=np.rad2deg(target_error).mean(0).tolist(),oldtarget_minus_scheduled_reference_max_abs_deg=np.rad2deg(abs(target_error)).max(0).tolist(),
            sameclock_oldtarget_minus_native_reference_mean_deg=np.rad2deg(target_difference[m]).mean(0).tolist(),
            sameclock_oldtarget_minus_native_reference_max_abs_deg=np.rad2deg(abs(target_difference[m])).max(0).tolist(),
            sameclock_normalized_state_difference_L2_median=float(np.median(np.linalg.norm(state_difference[m],axis=1))),
            request_minus_shadow_integral_rad_by_env={str(i):(difference[m&(d['env_id']==i)].sum(0)*(4/60)).tolist() for i in range(4)}))
    result[condition]=dict(phases=phases,samples=len(d['env_id']),max_abs_request_minus_shadow=float(abs(difference).max()),
        scope='Original reference function at saved new NN clock/oldtarget; shadow never executed; four observed env only; integration is a proxy, not native displacement')
track(Path(__file__));out=HERE/'results_v1/onpolicy_gap.json';assert not out.exists()
probe.grid.write(out,dict(cases=result,input_sha256=inputs,scope='No data augmentation/fit/native execution; prescribed postcapture CPU comparison only'))
print(json.dumps({c:[p['request_minus_shadow_rms4'] for p in v['phases']] for c,v in result.items()}))
