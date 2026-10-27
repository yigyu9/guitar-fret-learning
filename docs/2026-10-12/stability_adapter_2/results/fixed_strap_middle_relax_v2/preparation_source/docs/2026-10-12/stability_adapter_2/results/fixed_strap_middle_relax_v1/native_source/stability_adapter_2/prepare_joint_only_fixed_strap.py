"""Declare a preserved palm-witness pose at the original fixed strap length."""
from pathlib import Path
import copy, hashlib, json
R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2';B=R/'docs/2026-10-12/stability_adapter_2/results';P=B/'joint_only_fixed_strap_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def main():
    source=B/'coupled_palm_witness_v1/proposal.json';old=read(source);row=old['rows'][0];original=read(B/'small_wrist_motion_v1/native/initial_values.json')
    target=A/'trials/joint_only_fixed_strap_v1/palm_witness_original_LA.json'
    assert not target.exists() and not (P/'proposal.json').exists()
    assert all(sha(p)==h for p,h in old['input_sha256'].items())
    hashes=dict(old['input_sha256'])
    for p in [source,Path(row['trial_path']),B/'small_wrist_motion_v1/native/initial_values.json',B/'coupled_palm_witness_v1/preparation.json',Path(__file__).resolve(),A/'JOINT_ONLY_FIXED_STRAP_PLAN.md',A/'run_palm_witness_initial_diagnostic.py',A/'run_small_wrist_recorded_diagnostic.py']:
        hashes[str(p)]=sha(p)
    assert all(old['checks'].values()) and all(sha(p)==h for p,h in hashes.items())
    assert sha(row['trial_path'])==row['trial_sha256']
    trial=read(row['trial_path']);preserved=copy.deepcopy(trial);length=original['absolute_strap_rest_length_m']
    assert length==1.1018469719600776
    trial['initial_settings']['strap_rest_length_m']=length
    restored=copy.deepcopy(trial);restored['initial_settings']['strap_rest_length_m']=preserved['initial_settings']['strap_rest_length_m']
    checks=dict(previous_source_checks_passed=all(old['checks'].values()),only_previous_witness_LA_changed=restored==preserved,original_reference_LA_exact=length==original['input_trial']['initial_settings']['strap_rest_length_m'])
    target.parent.mkdir(exist_ok=False);save(target,trial)
    proposal=copy.deepcopy(old);proposal['input_sha256']=hashes
    newrow=proposal['rows'][0];newrow.update(label='joint_only_fixed_original_LA',trial_path=str(target),trial_sha256=sha(target),absolute_strap_rest_length_m=length)
    proposal['checks'].update(checks);proposal['scope']='same preserved initial18 source geometry and PD goals; original LA fixed; fresh native response unverified'
    checks['inputs_preserved']=all(sha(p)==h for p,h in hashes.items());assert all(checks.values())
    save(P/'proposal.json',proposal)
    save(P/'preparation.json',dict(checks=checks,input_sha256=hashes,trial_path=str(target),trial_sha256=sha(target),absolute_strap_rest_length_m=length,selected_names=read(B/'coupled_palm_witness_v1/preparation.json')['selected_names'],native_initializations=0,physics_steps=0))
    print(json.dumps(checks))
if __name__=='__main__':main()
