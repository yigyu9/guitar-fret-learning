"""Prepare two arm-target matches at the same recorded half initial state."""
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
REFERENCE=BASE/'three_face_support_loss_v1'
OLD=BASE/'three_face_finger_target_hold_v1'
PHASE=BASE/'three_face_arm_initial_target_v1'
TRIALS=ROOT/'stability_adapter_2/trials/three_face_arm_initial_target_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')


def main():
    PHASE.mkdir(exist_ok=False);TRIALS.mkdir(exist_ok=False)
    paths=[Path(__file__).resolve(),ROOT/'stability_adapter_2/THREE_FACE_ARM_INITIAL_TARGET_PLAN.md',ROOT/'stability_adapter_2/warmstart_targets.py',ROOT/'stability_adapter_2/run_seed2_support_warmstart.py',REFERENCE/'analysis.json',REFERENCE/'final_verification.json',REFERENCE/'native/saved_finger_targets/initial_values.json',REFERENCE/'native/saved_finger_targets/initial_grip_audit.json',OLD/'proposal.json']
    hashes={str(p):sha(p) for p in paths};previous=read(REFERENCE/'analysis.json')
    hashes.update(previous['input_sha256']);save(PHASE/'attempt.json',{'input_sha256':hashes,'native_initializations':0,'physics_steps':0})
    if not all(read(REFERENCE/'final_verification.json')['checks'].values()) or not all(previous['checks'].values()) or any(sha(p)!=h for p,h in hashes.items()):raise AssertionError('completed previous phase/input closure')
    from .environment import np
    from .warmstart_targets import compose
    initial=read(REFERENCE/'native/saved_finger_targets/initial_values.json');audit=read(REFERENCE/'native/saved_finger_targets/initial_grip_audit.json');proposal=read(OLD/'proposal.json')
    if not all(audit['checks'].values()):raise AssertionError('saved initial source/FK admission')
    names=initial['human_joint_names'];q=np.array(initial['initial_PD_target_rad'],dtype=np.float32);left=[names.index(n) for n in initial['left33_names']];fingers=[i for i,n in enumerate(names) if n.startswith('LH:')];arm=[i for i in left if i not in fingers];main=[names.index(n) for n in initial['main_control_joint_names']];other=np.setdiff1d(np.arange(81),left)
    if (len(left),len(fingers),len(arm),len(main),len(other))!=(33,21,12,66,48):raise AssertionError('33/21/12/66/48 ownership')
    target_old=np.array(initial['preserved_absolute_targets_rad'],dtype=np.float32);target_arm=target_old.copy();target_arm[arm]=q[arm];target_both=target_arm.copy();target_both[fingers]=q[fingers]
    lower=np.array(initial['PD_properties']['lower']);upper=np.array(initial['PD_properties']['upper']);base=initial['input_trial'];rows=[]
    for label,target in [('arm_initial_saved_fingers',target_arm),('arm_and_fingers_initial',target_both)]:
        offsets={names[i]:float(target[i])-float(q[i]) for i in left};composed=compose(q,main,[offsets.get(names[i],0.) for i in main],lower,upper)
        if not np.array_equal(composed,target) or not np.array_equal(target[arm],q[arm]) or not np.array_equal(target[other],q[other]):raise AssertionError('exact native target; initial arm12 and other48 held')
        trial=copy.deepcopy(base);trial['main_target_offsets_rad']=offsets;path=TRIALS/(label+'.json');save(path,trial)
        rows.append({'label':label,'alpha':.5,'target_mode':label,'accepted_for_fresh_native':True,'trial_path':str(path),'trial_sha256':sha(path),'expected_initial_angles_rad':q.astype(float).tolist(),'expected_absolute_targets_rad':target.astype(float).tolist(),'absolute_strap_rest_length_m':initial['absolute_strap_rest_length_m'],'target_clearance_m':.001,'source_state':initial['native_initial_state']})
    checks={'same_saved_initial81_and_trial_except_offsets':all({**read(r['trial_path']),'main_target_offsets_rad':base['main_target_offsets_rad']}==base for r in rows),'both_arm12_targets_match_actual_initial_q':np.array_equal(target_arm[arm],q[arm]) and np.array_equal(target_both[arm],q[arm]),'only_finger21_targets_differ_between_new_rows':np.array_equal(target_arm[np.setdiff1d(np.arange(81),fingers)],target_both[np.setdiff1d(np.arange(81),fingers)]) and np.array_equal(target_arm[fingers],target_old[fingers]) and np.array_equal(target_both[fingers],q[fingers]),'native_float64_composition_bounds_no_clipping_and_final66':True,'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    save(PHASE/'proposal.json',{'checks':checks,'input_sha256':hashes,'rows':rows,'rejected':[],'facets':proposal['facets'],'regions_G_m':proposal['regions_G_m'],'front_outer_source_z_G_m':proposal['front_outer_source_z_G_m'],'left33_names':initial['left33_names'],'finger21_names':[names[i] for i in fingers],'arm12_names':[names[i] for i in arm],'old_initial_angles_rad':q.astype(float).tolist(),'saved_absolute_targets_rad':target_old.astype(float).tolist(),'native_initializations':0,'physics_steps':0,'scope':'same initial81, arm12 targets=actual initial q in both new rows; onlyfinger21 targets differ; stored previous native5s reference not new run; no state replay/gain/material/strap changes'})
    print(json.dumps({'checks':checks,'arm12_target_changes_rad':{names[i]:float(target_arm[i])-float(target_old[i]) for i in arm}},indent=2),flush=True)


if __name__=='__main__':main()
