"""Prepare one quantized initial-pose candidate; create no native simulator."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

from .coupled_support_source import CoupledSnapshot, np, Rotation, pose
from .build_fixed_lower_asset import ASSET
from .initial_overlap import build_probe
from .palm_side_source_checks import source_checks, intersection
from .source_patch_interval import certified_distance
from .warmstart_targets import compose

R=Path(__file__).resolve().parents[1]; A=R/'stability_adapter_2'
B=R/'docs/2026-10-12/stability_adapter_2/results'; P=B/'coupled_palm_witness_v1'
OLD=B/'body9_strap_minus2mm_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')

def main():
    assert not (P/'proposal.json').exists()
    search=read(P/'search.json'); old=read(OLD/'proposal.json'); initial=read(OLD/'native/initial_values.json')
    assert all(search['checks'].values()) and all(old['checks'].values())
    hashes=dict(search['input_sha256'])
    for p,h in old['input_sha256'].items():
        assert p not in hashes or hashes[p]==h
        hashes[p]=h
    files=[Path(__file__).resolve(),P/'search.json',OLD/'proposal.json',OLD/'native/initial_values.json',
           A/'PALM_WITNESS_INITIAL_TRIAL_PLAN.md',A/'run_small_wrist_recorded_diagnostic.py',
           A/'near_contact_initial_audit.py',A/'warmstart_targets.py',A/'run_palm_witness_initial_diagnostic.py']
    hashes.update({str(p):sha(p) for p in files});assert all(sha(p)==h for p,h in hashes.items())
    candidate=next(r for r in search['rows'] if r['step']==0 and r['fraction']==1.)
    assert candidate['source_direction_screen_passed']
    oldrow=old['rows'][0]; trial=read(oldrow['trial_path']); names=initial['human_joint_names']; bodies=initial['human_body_names']
    state0=initial['native_initial_state']; q0=np.array([d['pos'] for d in state0['human_dof_states']])
    indices=np.array([names.index(n) for n in search['selected_names']]); held=np.array([j for j in range(81) if j not in indices])
    qnew=q0.astype(np.float32);qnew[indices]=(q0[indices]+np.array(candidate['delta_rad'])).astype(np.float32)
    realized=qnew[indices].astype(float)-q0[indices]
    main_indices=np.array([names.index(n) for n in initial['main_control_joint_names']])
    offsets=np.array([trial['main_target_offsets_rad'].get(names[j],0.) for j in main_indices])
    lower=np.array(initial['PD_properties']['lower']);upper=np.array(initial['PD_properties']['upper'])
    target=compose(qnew,main_indices,offsets,lower,upper)
    original=np.array(initial['preserved_absolute_targets_rad'])
    aug={r['dof']:r for r in read(R/'docs/2026-08-19/fret_joint_limits/joint_limit_ranges.json')['rows']}
    for n in search['selected_names'][12:]:
        j=names.index(n);lower[j]=max(lower[j],aug[n]['lower_rad']);upper[j]=min(upper[j],aug[n]['upper_rad'])
    checks={'only_selected18_initial_and_target_changed':bool(np.array_equal(qnew[held],q0[held]) and np.array_equal(target[held],original[held])),
            'float32_q_and_PD_bounds':bool(np.all(qnew>=lower) and np.all(qnew<=upper) and np.all(target>=lower) and np.all(target<=upper) and np.all(abs(target[main_indices]-q0[main_indices])<=.3)),
            'source_delta_within_original_bounds':bool(np.all(abs(realized[:12])<=.05) and np.all(abs(realized[12:])<=.1))}
    for sign in (-1,1):
        moving=target.copy();moving[names.index('L_Wrist_x')]+=sign*.005
        checks['wrist_motion_bounds_'+str(sign)]=bool(np.all(moving>=lower) and np.all(moving<=upper) and np.all(abs(moving[main_indices]-q0[main_indices])<=.3))
    snap=CoupledSnapshot(names,bodies,state0,state0); poses=snap.poses(realized); expected=copy.deepcopy(state0)
    for n,(position,rotation) in poses.items():
        record=expected['human_body_states'][bodies.index(n)]['pose']
        record['p']=dict(zip('xyz',map(float,position)));record['r']=dict(zip('xyzw',map(float,rotation.as_quat())))
    for d,value in zip(expected['human_dof_states'],qnew):d['pos']=float(value)
    props=read(B/'torso_hold_native_collision_v1/initial_collision/shape_properties.json')
    gn=[r['body'] for r in props['actors']['guitar']['body_ranges']]
    config=read(A/'config.json');config['humanoid_asset']=str(ASSET)
    scene=SimpleNamespace(config=config,human=0,guitar=1,env=None,gym=SimpleNamespace(get_actor_rigid_body_names=lambda env,actor:bodies if actor==0 else gn),bodies=lambda actor:expected['human_body_states'] if actor==0 else expected['guitar_body_states'])
    model,data,shapes=build_probe(scene);meshes,hg,cross=source_checks((model,data,shapes))
    xml=ET.parse(ASSET).getroot();parents={c.get('name'):p.get('name') for p in xml.iter('body') for c in p.findall('body')}
    def distance(a,b):
        chain=[];current=a
        while current in parents:chain.append(current);current=parents[current]
        chain.append(current);steps=0;current=b
        while current not in chain and current in parents:steps+=1;current=parents[current]
        return steps+chain.index(current) if current in chain else 99
    humans=[s for s in shapes if s['actor']=='human'];masks=props['mask_audit']['native_filters'];self_cross=[]
    for i,a in enumerate(humans):
        for b in humans[i+1:]:
            if distance(a['body'],b['body'])<=2:continue
            sameleft=all(s['body'].startswith('LH:') or s['body'] in ('L_Wrist','L_Elbow') for s in (a,b))
            native_allowed=all(x&y==0 for x in masks[a['body']] for y in masks[b['body']])
            if not (sameleft or native_allowed):continue
            radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
            if radius>1e-7:self_cross.append(dict(a=a['body'],b=b['body'],common_radius_m=radius))
    gp,gq=pose(expected['guitar_body_states'][0]); gr=Rotation.from_quat(gq)
    palm_mesh=meshes[next(s['geom_id'] for s in shapes if s['actor']=='human' and s['body']=='LH:palm')]
    cert=certified_distance(palm_mesh,gp+gr.apply(np.array(old['regions_G_m']['palm'])))
    baseline=next(r for r in search['rows'] if r['step']==0 and r['fraction']==0)
    proxy=np.array(read(B/'palm_neck_side_v1/initial_audit_v2/audit.json')['palmar_normal_proxy_local'])
    up=float(poses['LH:palm'][1].apply(proxy)[2])
    checks.update(source_human_guitar_clear=not hg,source_cross_hands_clear=not cross,source_nonadjacent_self_clear=not self_cross,palm_up_hemisphere=up>0,
                  quantized_whole_palm_patch_improves=cert['distance_m']<baseline['baseline_palm_patch_lower_m']-1e-9,
                  inputs_preserved=all(sha(p)==h for p,h in hashes.items()))
    assert all(checks.values()),checks
    for n,j in zip(search['selected_names'],indices):trial['initial_settings']['joint_angles_rad'][n]=float(qnew[j])
    folder=A/'trials/coupled_palm_witness_v1';folder.mkdir(exist_ok=False);trial_path=folder/'initial_witness.json';save(trial_path,trial)
    row=dict(label='palm_witness_initial',alpha=oldrow['alpha'],target_clearance_m=.0001,
             expected_initial_angles_rad=qnew.astype(float).tolist(),expected_absolute_targets_rad=target.astype(float).tolist(),
             absolute_strap_rest_length_m=trial['initial_settings']['strap_rest_length_m'],source_state=expected,
             admitted_for_native_near_contact_diagnostic=True,source_support_search_passed=False,
             source_support_search_reasons=['complete thumb-rear/front-finger grip unverified; this is palm-witness initial admission'],
             finger_target_policy='original left33 offsets retained after coupled initial18 shift',trial_path=str(trial_path),trial_sha256=sha(trial_path))
    proposal=dict(checks=checks,input_sha256=hashes,rows=[row],facets=old['facets'],regions_G_m=old['regions_G_m'],front_outer_source_z_G_m=old['front_outer_source_z_G_m'],left33_names=old['left33_names'],
                  native_initializations=0,physics_steps=0,scope='quantized initial18 and corresponding held PD shift; fresh native admission/5s response unverified')
    save(P/'proposal.json',proposal)
    save(P/'preparation.json',dict(checks=checks,input_sha256=hashes,selected_names=search['selected_names'],realized_initial_delta_rad=realized.tolist(),PD_delta_rad=(target.astype(float)-original).tolist(),palm_patch_certificate=cert,palm_up_proxy_z=up,source_self_intersections=self_cross,source_human_guitar_intersections=hg,source_cross_hand_intersections=cross,trial_path=str(trial_path),trial_sha256=sha(trial_path),native_initializations=0,physics_steps=0))
    print(json.dumps(dict(checks=checks,palm_gap_upper_mm=cert['distance_m']*1000,max_initial_delta_rad=float(max(abs(realized))))))
if __name__=='__main__':main()
