"""Prepare the declared strap-only variant; preserve the measured initial pose and goals."""
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
PHASE=BASE/'body9_strap_minus4mm_v1'
TRIAL=ROOT/'stability_adapter_2/trials/body9_strap_minus4mm_v1/la_minus4mm.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def main():
    old_trial=ROOT/'stability_adapter_2/trials/palm_patch_priority_diagnostic_v1/palm_wide_near17.json'
    old_proposal=BASE/'palm_patch_priority_diagnostic_v1/palm_wide_near17_proposal.json'
    old=read(old_proposal);row=next(r for r in old['rows'] if r['trial_path']==str(old_trial))
    assert sha(old_trial)==row['trial_sha256']
    inputs=dict(old['input_sha256'])
    for p in (old_trial,old_proposal,Path(__file__).resolve(),ROOT/'stability_adapter_2/BODY9_STRAP_MINUS4MM_EXECUTION.md',BASE/'small_wrist_motion_v1/preflight.json'):
        inputs[str(p)]=sha(p)
    assert all(sha(p)==h for p,h in inputs.items())
    trial=read(old_trial);new=copy.deepcopy(trial);new['initial_settings']['strap_rest_length_m']-=.004
    assert new['initial_settings']['strap_rest_length_m']==1.0978469719600776
    restored=copy.deepcopy(new);restored['initial_settings']['strap_rest_length_m']=trial['initial_settings']['strap_rest_length_m'];assert restored==trial
    TRIAL.parent.mkdir(exist_ok=False);save(TRIAL,new)
    inputs[str(TRIAL)]=sha(TRIAL);PHASE.mkdir(exist_ok=False)
    proposal=copy.deepcopy(old);changed=copy.deepcopy(row);changed.update(label='la_minus4mm',trial_path=str(TRIAL),trial_sha256=sha(TRIAL),absolute_strap_rest_length_m=new['initial_settings']['strap_rest_length_m'],native_proposal_path=str(PHASE/'proposal.json'))
    kept={k:v for k,v in changed.items() if k not in ('label','trial_path','trial_sha256','absolute_strap_rest_length_m','native_proposal_path')}
    assert kept=={k:v for k,v in row.items() if k not in ('label','trial_path','trial_sha256','absolute_strap_rest_length_m','native_proposal_path')}
    proposal['rows']=[changed];proposal['input_sha256']=inputs;proposal['strap_only_variant_of']=str(old_proposal);proposal['scope']='existing no-overlap source pose and original PD goals retained; only passive rest length -4mm; fresh native t0 admission still required; no new physical trial in preparation'
    save(PHASE/'proposal.json',proposal);assert all(sha(p)==h for p,h in inputs.items())
    save(PHASE/'preparation.json',dict(checks=dict(original_trial_SHA_exact=True,only_initial_rest_length_changed=True,source_pose_anchors_targets_exact=True,all_source_inputs_preserved=True),input_sha256=inputs,trial_path=str(TRIAL),proposal_path=str(PHASE/'proposal.json'),length_before_m=trial['initial_settings']['strap_rest_length_m'],length_after_m=new['initial_settings']['strap_rest_length_m'],native_initializations=0,physics_steps=0))
    print(str(TRIAL))


if __name__=='__main__':main()
