"""Prepare two finger-target conditions at the same recorded half initial pose."""
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1'
PHASE=OLD.parent/'three_face_finger_target_hold_v1'
TRIALS=ROOT/'stability_adapter_2/trials/three_face_finger_target_hold_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')


def main():
    PHASE.mkdir(exist_ok=False);TRIALS.mkdir(exist_ok=False)
    paths=[OLD/'final_verification.json',OLD/'analysis.json',OLD/'proposal.json',OLD/'native/three_face_half/initial_values.json',OLD/'native/three_face_half/initial_grip_audit.json',Path(__file__).resolve(),ROOT/'stability_adapter_2/THREE_FACE_FINGER_TARGET_HOLD_PLAN.md',ROOT/'stability_adapter_2/warmstart_targets.py',ROOT/'stability_adapter_2/run_seed2_support_warmstart.py']
    hashes={str(p):sha(p) for p in paths};previous=read(OLD/'analysis.json')
    hashes.update({p:sha(p) for p in previous['input_sha256']});save(PHASE/'attempt.json',{'input_sha256':hashes,'native_initializations':0,'physics_steps':0})
    if not all(read(OLD/'final_verification.json')['checks'].values()) or not all(previous['checks'].values()) or any(sha(p)!=h for p,h in previous['input_sha256'].items()):raise AssertionError('completed previous phase/input closure')
    from .environment import np
    from .warmstart_targets import compose
    initial=read(OLD/'native/three_face_half/initial_values.json');audit=read(OLD/'native/three_face_half/initial_grip_audit.json');proposal=read(OLD/'proposal.json')
    if not all(audit['checks'].values()):raise AssertionError('saved half initial source/FK admission')
    names=initial['human_joint_names'];q=np.array(initial['initial_PD_target_rad'],dtype=np.float32);left=[names.index(n) for n in initial['left33_names']];fingers=[i for i,n in enumerate(names) if n.startswith('LH:')];main=[names.index(n) for n in initial['main_control_joint_names']];other=np.setdiff1d(np.arange(81),left);arm=[i for i in left if i not in fingers]
    if (len(left),len(fingers),len(main),len(other),len(arm))!=(33,21,66,48,12):raise AssertionError('33/21/66/48/12 ownership')
    target_old=np.array(initial['preserved_absolute_targets_rad'],dtype=np.float32);target_new=target_old.copy();target_new[fingers]=q[fingers]
    bounds=initial['PD_properties'];lower=np.array(bounds['lower']);upper=np.array(bounds['upper']);rows=[]
    base=initial['input_trial'];differences={names[i]:float(target_new[i])-float(target_old[i]) for i in fingers}
    for label,target in [('saved_finger_targets',target_old),('initial_finger_targets',target_new)]:
        offsets={names[i]:float(target[i])-float(q[i]) for i in left};expected=compose(q,main,[offsets.get(names[i],0.) for i in main],lower,upper)
        if not np.array_equal(expected,target) or not np.array_equal(target[other],q[other]) or not np.array_equal(target[arm],target_old[arm]):raise AssertionError('native exact target or held arm/other48')
        trial=copy.deepcopy(base);trial['main_target_offsets_rad']=offsets;path=TRIALS/(label+'.json');save(path,trial)
        rows.append({'label':label,'alpha':.5,'finger_target_mode':label,'accepted_for_fresh_native':True,'trial_path':str(path),'trial_sha256':sha(path),'expected_initial_angles_rad':q.astype(float).tolist(),'expected_absolute_targets_rad':target.astype(float).tolist(),'absolute_strap_rest_length_m':initial['absolute_strap_rest_length_m'],'target_clearance_m':.001,'source_state':initial['native_initial_state']})
    checks={'saved_half_source_native_FK_admitted':True,'same_all81_initial_q_and_trial_except_offsets':all({**read(r['trial_path']),'main_target_offsets_rad':base['main_target_offsets_rad']}==base for r in rows),'only21_finger_absolute_targets_differ_native_unclipped':np.array_equal(target_old[arm],target_new[arm]) and np.array_equal(target_old[other],target_new[other]),'float64_composed_native_targets_exact_relative_bounds':True,'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    save(PHASE/'proposal.json',{'checks':checks,'input_sha256':hashes,'rows':rows,'rejected':[],'facets':proposal['facets'],'regions_G_m':proposal['regions_G_m'],'front_outer_source_z_G_m':proposal['front_outer_source_z_G_m'],'left33_names':initial['left33_names'],'finger21_names':[names[i] for i in fingers],'old_initial_angles_rad':q.astype(float).tolist(),'saved_absolute_targets_rad':target_old.astype(float).tolist(),'finger_absolute_target_changes_rad':differences,'initial_route_length_m':initial['initial_route_length_m'],'native_initializations':0,'physics_steps':0,'scope':'same half initial state, old versus initial left21 finger targets; left12 arm absolute targets and other48 held; source admission rechecked fresh native; no force/attachment/state replay'})
    print(json.dumps({'checks':checks,'changed_finger21_targets_rad':differences},indent=2),flush=True)


if __name__=='__main__':main()
