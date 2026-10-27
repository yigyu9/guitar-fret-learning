"""Thirteen wrist source hypotheses anchored to the measured hand hierarchy."""
from pathlib import Path
from types import SimpleNamespace
import copy
import hashlib
import json
import xml.etree.ElementTree as ET

from .environment import np
from .build_fixed_lower_asset import ASSET, pose
from .coupled_support_source import CoupledSnapshot
from .initial_overlap import build_probe
from .palm_side_source_checks import source_checks, intersection
from .source_patch_interval import certified_distance
from .warmstart_targets import compose
from scipy.spatial.transform import Rotation

R = Path(__file__).resolve().parents[1]
A = R/'stability_adapter_2'
B = R/'docs/2026-10-12/stability_adapter_2/results'
P = B/'source_hand_wrist_clearance_v1'
OLD = B/'fixed_strap_source_hand_initial_v1'
POLICY = B/'torso_hold_native_collision_v1/initial_collision/shape_properties.json'
PROXY = B/'palm_neck_side_v1/initial_audit_v2/audit.json'
RANGES = B/'fixed_strap_source_compatibility_v1/joint_ranges.jsonl'
MODEL = B/'coupled_support_source_v1/model.json'


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d): Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')


def main():
    assert not (P/'search.json').exists() and not (P/'proposal.json').exists()
    initial, inventory = read(OLD/'native/initial_values.json'), read(OLD/'artifact_inventory.json')
    assert sha(OLD/'native/initial_values.json') == inventory[str(OLD/'native/initial_values.json')]['sha256']
    assert all(read(MODEL)['checks'].values())
    policy, old, proxy = read(POLICY),read(OLD/'proposal.json'),read(PROXY)
    names,bodies,state = initial['human_joint_names'],initial['human_body_names'],initial['native_initial_state']
    guitar_names = [v['body'] for v in policy['actors']['guitar']['body_ranges']]
    config = read(A/'config.json'); config['humanoid_asset'] = str(ASSET)
    scene = SimpleNamespace(config=config,human=0,guitar=1,env=None,
        gym=SimpleNamespace(get_actor_rigid_body_names=lambda env,actor:bodies if actor == 0 else guitar_names),
        bodies=lambda actor:state['human_body_states'] if actor == 0 else state['guitar_body_states'])
    probe = build_probe(scene)
    meshes, base_hg, base_cross = source_checks(probe)
    snapshot = CoupledSnapshot(names,bodies,state,state)
    zero = snapshot.poses(np.zeros(18))
    zp = max(float(np.linalg.norm(p-snapshot.actual[n][0])) for n,(p,r) in zero.items())
    zr = max(float((r*snapshot.actual[n][1].inv()).magnitude()) for n,(p,r) in zero.items())
    assert zp < 1e-6 and zr < 1e-6
    humans = [s for s in probe[2] if s['actor'] == 'human']
    guitars = [s for s in probe[2] if s['actor'] == 'guitar']
    hg_pairs = [(a,b) for a in humans for b in guitars]
    cross_pairs = [(a,b) for a in humans if a['body'].startswith('LH:') or a['body'] == 'L_Wrist'
                   for b in humans if b['body'].startswith('RH:') or b['body'] == 'R_Wrist']
    xml = ET.parse(ASSET).getroot()
    parents = {c.get('name'):p.get('name') for p in xml.iter('body') for c in p.findall('body')}
    def distance(a,b):
        chain=[]; current=a
        while current in parents: chain.append(current); current=parents[current]
        chain.append(current); steps=0; current=b
        while current not in chain and current in parents: steps+=1; current=parents[current]
        return steps+chain.index(current) if current in chain else 99
    filters = policy['mask_audit']['native_filters']
    self_pairs=[]
    for i,a in enumerate(humans):
        for b in humans[i+1:]:
            if distance(a['body'],b['body']) <= 2: continue
            sameleft = all(s['body'].startswith('LH:') or s['body'] in ('L_Wrist','L_Elbow') for s in (a,b))
            allowed = all(x&y == 0 for x in filters[a['body']] for y in filters[b['body']])
            if sameleft or allowed: self_pairs.append((a,b))
    assert len(self_pairs) == 1188
    tree = next(b for b in xml.iter('body') if b.get('name') == 'L_Wrist')
    moving_names = {b.get('name') for b in tree.iter('body')}
    assert moving_names <= set(zero)
    moving = [s for s in humans if s['body'] in moving_names]
    gp,gq = pose(state['guitar_body_states'][0]); gr=Rotation.from_quat(gq)
    patches = {n:gr.apply(np.array(old['regions_G_m'][key]))+gp for n,key in [('LH:palm','palm'),('LH:thumb3','thumb')]}
    plane = patches['LH:palm']
    neck_normal = np.cross(plane[1]-plane[0],plane[2]-plane[0])
    assert np.linalg.norm(neck_normal) > 1e-12
    neck_normal /= np.linalg.norm(neck_normal)
    bounds = {(v['kind'],v['name']):v for v in (json.loads(s) for s in RANGES.read_text().splitlines()) if v['label'] == 'initial_aligned'}
    q0 = np.array(initial['initial_PD_target_rad'],dtype=np.float32)
    t0 = np.array(initial['preserved_absolute_targets_rad'],dtype=np.float32)
    main_indices = [names.index(n) for n in initial['main_control_joint_names']]
    original = read(old['rows'][0]['trial_path'])
    assert sha(old['rows'][0]['trial_path']) == old['rows'][0]['trial_sha256']
    offsets = np.array([original['main_target_offsets_rad'].get(names[i],0.) for i in main_indices])
    props = initial['PD_properties']
    assert np.array_equal(compose(q0,main_indices,offsets,props['lower'],props['upper']),t0)
    conditions = [(None,0.)]+[(n,d) for n in ('L_Wrist_x','L_Wrist_y','L_Wrist_z') for d in (-.05,.05,-.10,.10)]
    records=[]
    for order,(name,requested) in enumerate(conditions):
        qnew=q0.copy(); delta=np.zeros(18)
        if name is not None:
            axis=names.index(name); qnew[axis]=np.float32(float(q0[axis])+requested)
            delta[snapshot.selected.index(name)] = float(qnew[axis])-float(q0[axis])
        else: axis=None
        target=compose(qnew,main_indices,offsets,props['lower'],props['upper'])
        other=[i for i in range(len(names)) if i != axis]
        unchanged_q = bool(np.array_equal(qnew[other],q0[other]) and np.array_equal(target[other],t0[other]))
        within = all(bounds[k,n]['effective_lower_rad'] <= float(values[i]) <= bounds[k,n]['effective_upper_rad'] for k,values in [('actual_initial',qnew),('held',target)] for i,n in enumerate(names))
        for sign in (-1,1):
            motion=offsets.copy(); motion[main_indices.index(names.index('L_Wrist_x'))] += sign*.005
            command=compose(qnew,main_indices,motion,props['lower'],props['upper'])
            within &= all(bounds['held',n]['effective_lower_rad'] <= float(command[i]) <= bounds['held',n]['effective_upper_rad'] for i,n in enumerate(names))
        transformed=snapshot.meshes(meshes,moving,delta); poses=snapshot.poses(delta)
        def screen(pairs):
            found=[]
            for a,b in pairs:
                radius=intersection(transformed[a['geom_id']],transformed[b['geom_id']])
                if radius > 1e-7: found.append(dict(a=a['body'],b=b['body'],common_radius_m=radius))
            return found
        hg,cross,self_overlaps=screen(hg_pairs),screen(cross_pairs),screen(self_pairs)
        up=float(poses['LH:palm'][1].apply(proxy['palmar_normal_proxy_local'])[2])
        alignment=float(abs(poses['LH:palm'][1].apply(proxy['palmar_normal_proxy_local']) @ neck_normal))
        patch_distances={n:certified_distance(transformed[next(s['geom_id'] for s in moving if s['body'] == n)],patch) for n,patch in patches.items()}
        upper_arm_identity=all(float(np.linalg.norm(p-snapshot.actual[n][0])) < 1e-6 and float((r*snapshot.actual[n][1].inv()).magnitude()) < 1e-6 for n,(p,r) in poses.items() if n not in moving_names)
        unchanged_meshes=all(np.array_equal(v.vertices,transformed[k].vertices) for k,v in meshes.items() if k not in {s['geom_id'] for s in moving})
        relative_identity=True
        for n in moving_names-{'L_Wrist'}:
            parent=parents[n]; pp,pr=poses[parent]; cp,cr=poses[n]
            op,orr=snapshot.actual[parent]; oc,ocr=snapshot.actual[n]
            relative_identity &= float(np.linalg.norm(pr.inv().apply(cp-pp)-orr.inv().apply(oc-op))) < 1e-6 and float(((pr.inv()*cr)*(orr.inv()*ocr).inv()).magnitude()) < 1e-6
        assert unchanged_q and upper_arm_identity and unchanged_meshes and relative_identity
        actual_delta=0. if axis is None else float(qnew[axis])-float(q0[axis])
        records.append(dict(order=order,joint=name,requested_delta_rad=requested,actual_delta_rad=actual_delta,
            initial_angle_rad=None if axis is None else float(qnew[axis]),held_angle_rad=None if axis is None else float(target[axis]),
            held_delta_rad=0. if axis is None else float(target[axis])-float(t0[axis]),
            source_human_guitar_intersections=hg,source_cross_hand_intersections=cross,source_self_intersections=self_overlaps,
            self_pair_count=len(self_pairs),palm_up_proxy_z=up,palm_neck_plane_alignment_abs=alignment,
            support_patch_distances=patch_distances,within_effective_ranges=bool(within),other80_q_and_held_exact=unchanged_q,
            upper_arm_identity=upper_arm_identity,other_meshes_identity=unchanged_meshes,hand_relative_identity=bool(relative_identity),
            source_clear=bool(within and not hg and not cross and not self_overlaps and up>0)))
    checks=dict(thirteen_conditions=len(records)==13,zero_pose_identity=zp<1e-6 and zr<1e-6,
        base_HG_reproduced=records[0]['source_human_guitar_intersections'] == [dict(a=v['human'],b=v['guitar'],common_radius_m=v['common_radius_m']) for v in base_hg],
        base_cross_reproduced=records[0]['source_cross_hand_intersections'] == [dict(a=v['left'],b=v['right'],common_radius_m=v['common_radius_m']) for v in base_cross],
        all_other80_exact=all(v['other80_q_and_held_exact'] for v in records),
        all_relative_and_upper_identity=all(v['hand_relative_identity'] and v['upper_arm_identity'] and v['other_meshes_identity'] for v in records),
        all_self1188=all(v['self_pair_count']==1188 for v in records),
        all_ranges_safe=all(v['within_effective_ranges'] for v in records))
    assert all(checks.values()),checks
    clear=[v for v in records if v['source_clear']]
    selected=min(clear,key=lambda v:(abs(v['actual_delta_rad']),sum(d['distance_m']**2 for d in v['support_patch_distances'].values()),-v['palm_neck_plane_alignment_abs'],v['order'])) if clear else None
    if selected:
        name=selected['joint']; axis=names.index(name); qnew=q0.copy(); qnew[axis]=selected['initial_angle_rad']
        target=compose(qnew,main_indices,offsets,props['lower'],props['upper'])
        trial=copy.deepcopy(original); trial['initial_settings']['joint_angles_rad'][name]=float(qnew[axis])
        assert trial['main_target_offsets_rad'] == original['main_target_offsets_rad']
        folder=A/'trials/source_hand_wrist_clearance_v1'; folder.mkdir(exist_ok=False)
        trial_path=folder/'wrist_clear.json'; save(trial_path,trial)
        proposal=copy.deepcopy(old); row=copy.deepcopy(old['rows'][0]); row.pop('source_state',None)
        row.update(label='wrist_clear',alpha=None,trial_path=str(trial_path),trial_sha256=sha(trial_path),
            expected_initial_angles_rad=qnew.astype(float).tolist(),expected_absolute_targets_rad=target.astype(float).tolist(),
            finger_target_policy='Measured source-hand5 finger poses unchanged; one wrist initial axis changed; all named offsets preserved; other80 initial/held exact')
        proposal.update(checks=checks,rows=[row],scope='Conditional wrist source hypothesis; fresh actual native direct admission still required')
        save(P/'proposal.json',proposal)
        delta=np.zeros(18);delta[snapshot.selected.index(name)]=selected['actual_delta_rad']
        predicted=snapshot.poses(delta)
        save(P/'source_prediction.json',dict(poses_W={n:dict(position_m=p.tolist(),quaternion_xyzw=r.as_quat().tolist()) for n,(p,r) in predicted.items()},scope='Conditional source pose prediction only; not native state replay or gate certification'))
    save(P/'search.json',dict(checks=checks,rows=records,selected=selected,zero_pose_position_error_m=zp,zero_pose_rotation_error_rad=zr,
        moving_body_names=sorted(moving_names),moving_collision_body_names=sorted({s['body'] for s in moving}),native_initializations=0,physics_steps=0,
        scope='Thirteen conditional wrist source hypotheses; measured finger1 relations held; no Gym dynamics/cooked contact or stability certification'))
    print(json.dumps(dict(checks=checks,clear_count=len(clear),selected=selected,intersections=[dict(joint=v['joint'],delta=v['actual_delta_rad'],pairs=v['source_human_guitar_intersections']) for v in records]),indent=2))


if __name__ == '__main__': main()
