"""Freeze one completed source near-pose and explicit physical finger-target diagnostics."""
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
PHASE=BASE/'palm_patch_priority_diagnostic_v1'
TRIALS=ROOT/'stability_adapter_2/trials/palm_patch_priority_diagnostic_v1'

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,value):Path(p).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def main():
    if (PHASE/'proposal.json').exists():raise FileExistsError('consumed diagnostic inputs')
    partial=BASE/'palm_patch_priority_initial_v1/proposal.json'
    raw=partial.read_bytes();selection=json.loads(raw);source_row=next(r for r in selection['rejected'] if r['label']=='wide_near17')
    if partial.read_bytes()!=raw:raise RuntimeError('partial updated during snapshot; retry before any trial')
    # Freeze the completed row, not the mutable running selection file.
    snap=PHASE/'completed_source_row_snapshot.json';save(snap,source_row)
    save(PHASE/'source_snapshot_provenance.json',{'completed_source_proposal':str(partial),'observed_file_sha256':hashlib.sha256(raw).hexdigest(),'completed_label':'wide_near17','scope':'one completed immutable source proposal row frozen; source support failure remains; no physical support success'})
    from .environment import np
    from .warmstart_targets import compose
    initial=read(BASE/'three_face_support_loss_v1/native/saved_finger_targets/initial_values.json')
    previous=read(BASE/'palm_patch_priority_initial_v1/proposal.json')
    pre=read(BASE/'palm_patch_priority_initial_v1/root_preflight.json')
    hashes=dict(previous['input_sha256'])
    for p,h in pre['input_sha256'].items():
        if p in hashes and hashes[p]!=h:raise AssertionError('inconsistent source closure')
        hashes[p]=h
    for p in [Path(__file__).resolve(),ROOT/'stability_adapter_2/run_strap_recorded_diagnostic.py',ROOT/'stability_adapter_2/near_contact_initial_audit.py',ROOT/'stability_adapter_2/source_patch_interval.py',ROOT/'stability_adapter_2/PALM_PRIORITY_NATIVE_DIAGNOSTIC_PLAN.md',snap,PHASE/'source_snapshot_provenance.json',PHASE/'previous_native_runner_source.py',PHASE/'previous_runner_preservation.json',BASE/'palm_patch_priority_initial_v1/proposal.json']:
        hashes[str(p)]=sha(p)
    if not all(sha(p)==h for p,h in hashes.items()):raise AssertionError('source inputs changed')
    names=initial['human_joint_names'];left=initial['left33_names'];indices=[names.index(n) for n in pre['coordinate_names']];main_indices=[names.index(n) for n in initial['main_control_joint_names']]
    q=np.array(source_row['expected_initial_angles_rad']);q0=np.array(previous['old_initial_angles_rad']);old_target=np.array(initial['preserved_absolute_targets_rad'],dtype=np.float32);lo=np.array(initial['PD_properties']['lower']);hi=np.array(initial['PD_properties']['upper']);fingers=[i for i,n in enumerate(names) if n.startswith('LH:')]
    checks={'initial_source_human_guitar_clear':not source_row['source_intersections'],'initial_cross_hands_clear':not source_row['cross_hand_intersections'],'initial_nonadjacent_left_hand_clear':not source_row['nonadjacent_left_hand_intersections'],'palm_up_proxy':source_row['palm_up_proxy_z']>0,'all_initial_native_bounds':bool(np.all(q>=lo) and np.all(q<=hi)),'same33_source_bounds':bool(np.all(q[indices]>=pre['lower_rad']) and np.all(q[indices]<=pre['upper_rad'])),'other48_initial_angles_held':bool(np.array_equal(q[np.setdiff1d(np.arange(81),indices)],q0[np.setdiff1d(np.arange(81),indices)])),'source_support_search_failure_retained':source_row['accepted_for_fresh_native'] is False and bool(source_row['reasons']),'finger21_main66_interface':len(fingers)==21 and len(main_indices)==66}
    if not all(checks.values()):raise AssertionError(checks)
    TRIALS.mkdir(exist_ok=False);rows=[]
    for label in ['palm_wide_near17']:
        target=old_target.copy()
        offsets={n:float(target[names.index(n)])-float(q[names.index(n)]) for n in left}
        if any(abs(v)>.3 for v in offsets.values()) or np.any(target<lo) or np.any(target>hi):raise AssertionError('diagnostic target limits')
        result=compose(q,main_indices,[offsets.get(names[i],0.) for i in main_indices],lo,hi)
        if not np.array_equal(result,target):raise AssertionError('declared target exactness')
        trial=copy.deepcopy(initial['input_trial']);trial['initial_settings']['joint_angles_rad'].update({n:float(q[names.index(n)]) for n in left});trial['main_target_offsets_rad']=offsets
        path=TRIALS/(label+'.json');save(path,trial)
        row=copy.deepcopy(source_row);row.update(label=label,admitted_for_native_near_contact_diagnostic=True,source_support_search_passed=False,source_support_search_reasons=source_row['reasons'],finger_target_policy=label,expected_absolute_targets_rad=target.astype(float).tolist(),trial_path=str(path),trial_sha256=sha(path),native_proposal_path=str(PHASE/(label+'_proposal.json')))
        rows.append(row)
    checks['saved_absolute81_PD_targets_unchanged']=rows[0]['expected_absolute_targets_rad']==old_target.astype(float).tolist()
    if not all(checks.values()) or not all(sha(p)==h for p,h in hashes.items()):raise AssertionError('diagnostic preparation checks')
    proposal={'checks':checks,'input_sha256':hashes,'rows':rows,'rejected':[],'facets':source_row['source_facets'],'regions_G_m':previous['regions_G_m'],'front_outer_source_z_G_m':previous['front_outer_source_z_G_m'],'left33_names':left,'source_search_constraints_relaxed':False,'native_diagnostic_admission':'no-initial-source-overlap; support gates remain unmet and are observed physically','native_initializations':0,'physics_steps':0,'scope':'single completed palm-priority near-contact initial pose with preserved old81 PD targets; thumb source approach unmet; not accepted grip/support or cooked clearance certification'}
    save(PHASE/'proposal.json',proposal)
    for row in rows:
        context=copy.deepcopy(proposal);context['rows']=[row];save(row['native_proposal_path'],context)
    print(json.dumps({'checks':checks,'trials':[r['trial_path'] for r in rows],'native_initializations':0,'physics_steps':0}))

if __name__=='__main__':main()
