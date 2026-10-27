"""Prepare two constant shoulder-target probes from the current fixed-LA pose."""
from pathlib import Path
import copy,hashlib,json
from .warmstart_targets import compose
import numpy as np
R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2';B=R/'docs/2026-10-12/stability_adapter_2/results';P=B/'fixed_strap_shoulder_response_v1';OLD=B/'joint_only_fixed_strap_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def main():
    old=read(OLD/'proposal.json');row=old['rows'][0];initial=read(OLD/'native/initial_values.json');original=read(row['trial_path'])
    assert not (P/'proposal.json').exists() and all(old['checks'].values())
    assert all(sha(p)==h for p,h in old['input_sha256'].items()) and sha(row['trial_path'])==row['trial_sha256']
    hashes=dict(old['input_sha256'])
    for p in [OLD/'proposal.json',OLD/'native/initial_values.json',Path(row['trial_path']),Path(__file__).resolve(),A/'FIXED_STRAP_SHOULDER_RESPONSE_PLAN.md',A/'warmstart_targets.py']:
        assert str(p) not in hashes or hashes[str(p)]==sha(p)
        hashes[str(p)]=sha(p)
    names=initial['human_joint_names'];main=[names.index(n) for n in initial['main_control_joint_names']];axis=names.index('L_Shoulder_y');kw=names.index('L_Wrist_x')
    q=np.array(initial['initial_PD_target_rad'],dtype=np.float32);lo=np.array(initial['PD_properties']['lower']);hi=np.array(initial['PD_properties']['upper']);baseline=np.array(initial['preserved_absolute_targets_rad'],dtype=np.float32)
    other=[j for j in range(81) if j!=axis];folder=A/'trials/fixed_strap_shoulder_response_v1';folder.mkdir(exist_ok=False);rows=[];checks={};preflight=[]
    for label,delta in [('minus008',-.008),('plus008',.008)]:
        trial=copy.deepcopy(original);trial['main_target_offsets_rad']['L_Shoulder_y']+=delta
        offsets=np.array([trial['main_target_offsets_rad'].get(names[j],0.) for j in main]);target=compose(q,main,offsets,lo,hi)
        restored=copy.deepcopy(trial);restored['main_target_offsets_rad']['L_Shoulder_y']=original['main_target_offsets_rad']['L_Shoulder_y']
        checks[label+'_only_one_offset_changed']=restored==original and np.array_equal(target[other],baseline[other])
        checks[label+'_fixed_original_LA']=trial['initial_settings']['strap_rest_length_m']==1.1018469719600776
        requested=q.copy();requested[main]=(q[main].astype(float)+offsets).astype(np.float32)
        checks[label+'_float32_target_unclipped']=np.array_equal(target,requested) and bool(np.all(target>=lo) and np.all(target<=hi) and np.all(abs(offsets)<=.3))
        for sign in [-1,1]:
            moving=offsets.copy();moving[main.index(kw)]+=sign*.005;command=compose(q,main,moving,lo,hi);desired=q.copy();desired[main]=(q[main].astype(float)+moving).astype(np.float32)
            checks[label+'_wrist_extreme_'+str(sign)]=np.array_equal(command,desired) and bool(np.all(abs(moving)<=.3))
        assert all(checks.values()),checks
        path=folder/(label+'.json');save(path,trial);newrow=copy.deepcopy(row);newrow.update(label=label,trial_path=str(path),trial_sha256=sha(path),expected_absolute_targets_rad=target.astype(float).tolist(),finger_target_policy='finger21 and other offsets retained; Shoulder_y probe offset only');rows.append(newrow)
        preflight.append(dict(label=label,requested_delta_rad=delta,actual_float32_target_delta_rad=float(target[axis]-baseline[axis]),target_rad=float(target[axis]),baseline_target_rad=float(baseline[axis]),trial_path=str(path),trial_sha256=sha(path)))
    checks['all_inputs_unchanged']=all(sha(p)==h for p,h in hashes.items());assert all(checks.values())
    proposal=copy.deepcopy(old);proposal.update(checks=checks,input_sha256=hashes,rows=rows,scope='same native initial state; only Shoulder_y PD goal plus/minus .008rad, same fixed LA/wrist motion; physical response unverified')
    save(P/'proposal.json',proposal);save(P/'preparation.json',dict(checks=checks,input_sha256=hashes,axis='L_Shoulder_y',preflight=preflight,native_initializations=0,physics_steps=0));print(json.dumps(dict(checks=checks,preflight=preflight)))
if __name__=='__main__':main()
