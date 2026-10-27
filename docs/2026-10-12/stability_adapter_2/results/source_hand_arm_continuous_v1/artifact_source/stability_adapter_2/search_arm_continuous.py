"""Bounded left-arm optimization using recorded source geometry only."""
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
from scipy.optimize import minimize, Bounds

R = Path(__file__).resolve().parents[1]
A = R/'stability_adapter_2'
B = R/'docs/2026-10-12/stability_adapter_2/results'
P = B/'source_hand_arm_continuous_v1'
OLD = B/'fixed_strap_source_hand_initial_v1'
POLICY = B/'torso_hold_native_collision_v1/initial_collision/shape_properties.json'
PROXY = B/'palm_neck_side_v1/initial_audit_v2/audit.json'
RANGES = B/'fixed_strap_source_compatibility_v1/joint_ranges.jsonl'
MODEL = B/'coupled_support_source_v1/model.json'
PRIOR = B/'source_hand_arm_position_v1/search.json'


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
    tree = next(b for b in xml.iter('body') if b.get('name') == 'L_Thorax')
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
    arm_indices=[names.index(n) for n in snapshot.arm]
    other=[i for i in range(len(names)) if i not in arm_indices]
    full_offsets=np.zeros(len(names));full_offsets[main_indices]=offsets
    hand_names={b.get('name') for b in next(b for b in xml.iter('body') if b.get('name') == 'LH:palm').iter('body')}
    moving_ids={s['geom_id'] for s in moving}
    def materialize(requested):
        q=q0.copy();q[arm_indices]=(q0[arm_indices].astype(float)+requested).astype(np.float32)
        raw=q.astype(float);raw[main_indices]+=offsets
        return q,raw.astype(np.float32)
    def violations(q,target):
        found=[]
        values=[('actual_initial','initial',q),('held','held',target)]
        for sign in (-1,1):
            raw=q.astype(float)+full_offsets;raw[names.index('L_Wrist_x')]+=sign*.005
            values.append(('held','wrist_extreme_'+str(sign),raw.astype(np.float32)))
        for kind,stage,angles in values:
            for i,n in enumerate(names):
                lo,hi=bounds[kind,n]['effective_lower_rad'],bounds[kind,n]['effective_upper_rad']
                if not lo<=float(angles[i])<=hi:found.append(dict(stage=stage,name=n,value_rad=float(angles[i]),lower_rad=lo,upper_rad=hi))
        for i in arm_indices:
            if abs(float(q[i])-float(q0[i]))>.15:found.append(dict(stage='original_delta',name=names[i],value_rad=float(q[i])-float(q0[i]),lower_rad=-.15,upper_rad=.15))
        return found
    interval=[]
    for i in arm_indices:
        n=names[i];ib,hb=bounds['actual_initial',n],bounds['held',n]
        amplitude=.005 if n=='L_Wrist_x' else 0.
        lo=max(float(q0[i])-.15,ib['effective_lower_rad'],hb['effective_lower_rad']-full_offsets[i]+amplitude)
        hi=min(float(q0[i])+.15,ib['effective_upper_rad'],hb['effective_upper_rad']-full_offsets[i]-amplitude)
        flo,fhi=np.float32(lo),np.float32(hi)
        if float(flo)<lo:flo=np.nextafter(flo,np.float32(np.inf))
        if float(fhi)>hi:fhi=np.nextafter(fhi,np.float32(-np.inf))
        for side in ('lower','upper'):
            for _ in range(16):
                q=q0.copy();q[i]=flo if side=='lower' else fhi
                raw=q.astype(float)+full_offsets;bad=violations(q,raw.astype(np.float32))
                if not bad:break
                assert all(v['name']==n for v in bad),bad
                if side=='lower':flo=np.nextafter(flo,np.float32(np.inf))
                else:fhi=np.nextafter(fhi,np.float32(-np.inf))
            else:raise AssertionError('float32 endpoint tightening did not converge')
        assert flo<fhi and float(flo)<=float(q0[i])<=float(fhi)
        interval.append(dict(name=n,real_lower_rad=lo,real_upper_rad=hi,initial_lower_rad=float(flo),initial_upper_rad=float(fhi),lower_delta_rad=float(flo)-float(q0[i]),upper_delta_rad=float(fhi)-float(q0[i])))
    lower=np.array([v['lower_delta_rad'] for v in interval]);upper=np.array([v['upper_delta_rad'] for v in interval])
    prior=read(PRIOR);seed0=np.zeros(12);seed1=seed0.copy()
    for n,v in prior['rows'][47]['changes'].items():seed1[snapshot.arm.index(n)]=v['actual_delta_rad']
    seeds=[seed0,seed1];records=[];solves=[];seed_reproduced=[]
    def same_pairs(a,b):
        aa={(v['a'],v['b']):v['common_radius_m'] for v in a};bb={(v['a'],v['b']):v['common_radius_m'] for v in b}
        return aa.keys()==bb.keys() and all(abs(aa[k]-bb[k])<1e-10 for k in aa)
    with (P/'evaluations.jsonl').open('x') as stream:
        for seed_id,seed in enumerate(seeds):
            assert np.all(seed>=lower) and np.all(seed<=upper)
            begin=len(records)
            def objective(requested):
                assert len(records)-begin<400
                requested=np.asarray(requested,dtype=float);assert requested.shape==(12,) and np.isfinite(requested).all()
                q,target=materialize(requested);delta=np.zeros(18);delta[:12]=q[arm_indices].astype(float)-q0[arm_indices].astype(float)
                bad=violations(q,target)
                unchanged=bool(np.array_equal(q[other],q0[other]) and np.array_equal(target[other],t0[other]));assert unchanged
                record=dict(order=len(records),seed_id=seed_id,seed_evaluation=len(records)-begin,requested_delta_rad=requested.tolist(),actual_delta_rad=delta[:12].tolist(),
                    initial_delta_L2_rad=float(np.linalg.norm(delta)),raw_initial_rad=q.astype(float).tolist(),raw_absolute_targets_rad=target.astype(float).tolist(),
                    other69_q_and_held_exact=unchanged,within_effective_ranges=not bad,numeric_violations=bad,source_evaluated=not bad,source_clear=False)
                if bad:
                    record.update(source_human_guitar_intersections=None,source_cross_hand_intersections=None,source_self_intersections=None,
                        support_patch_distances=None,objective_terms=dict(hard_invalid=1e12),objective_value=1e12)
                else:
                    assert np.array_equal(compose(q,main_indices,offsets,props['lower'],props['upper']),target)
                    transformed=snapshot.meshes(meshes,moving,delta);poses=snapshot.poses(delta)
                    def screen(pairs):
                        found=[]
                        for a,b in pairs:
                            radius=intersection(transformed[a['geom_id']],transformed[b['geom_id']])
                            if radius>1e-7:found.append(dict(a=a['body'],b=b['body'],common_radius_m=radius))
                        return found
                    hg=screen(hg_pairs);up=float(poses['LH:palm'][1].apply(proxy['palmar_normal_proxy_local'])[2])
                    alignment=float(abs(poses['LH:palm'][1].apply(proxy['palmar_normal_proxy_local'])@neck_normal))
                    distances={n:certified_distance(transformed[next(s['geom_id'] for s in moving if s['body']==n)],patch) for n,patch in patches.items()}
                    cross,self_overlaps=(screen(cross_pairs),screen(self_pairs)) if not hg else (None,None)
                    affected=set()
                    for n,d in zip(snapshot.arm,delta[:12]):
                        if d:
                            subtree=next(b for b in xml.iter('body') if b.get('name')==n.rsplit('_',1)[0])
                            affected.update(b.get('name') for b in subtree.iter('body'))
                    upstream=all(np.linalg.norm(p-snapshot.actual[n][0])<1e-6 and (r*snapshot.actual[n][1].inv()).magnitude()<1e-6 for n,(p,r) in poses.items() if n not in affected)
                    other_meshes=all(np.array_equal(v.vertices,transformed[k].vertices) for k,v in meshes.items() if k not in moving_ids)
                    relative=True
                    for n in hand_names:
                        pp,pr=poses[parents[n]];cp,cr=poses[n];op,orr=snapshot.actual[parents[n]];oc,ocr=snapshot.actual[n]
                        relative &= np.linalg.norm(pr.inv().apply(cp-pp)-orr.inv().apply(oc-op))<1e-6 and ((pr.inv()*cr)*(orr.inv()*ocr).inv()).magnitude()<1e-6
                    identity=bool(upstream and other_meshes and relative)
                    invalid=up<=0 or not identity or (not hg and bool(cross or self_overlaps))
                    terms=dict(collision=1e6*sum((v['common_radius_m']*1000)**2 for v in hg),
                        support=sum((d['distance_m']*1000)**2 for d in distances.values()),posture=.01*float(np.sum((delta[:12]/.15)**2)),
                        plane=.1*(1-alignment)**2,hard_invalid=1e12 if invalid else 0.)
                    record.update(source_human_guitar_intersections=hg,source_cross_hand_intersections=cross,source_self_intersections=self_overlaps,
                        self_pair_count=1188 if not hg else None,palm_up_proxy_z=up,palm_neck_plane_alignment_abs=alignment,
                        support_patch_distances=distances,upstream_pose_identity=bool(upstream),other_meshes_identity=other_meshes,hand_relative_identity=bool(relative),
                        objective_terms=terms,objective_value=sum(terms.values()),source_clear=bool(not hg and not invalid))
                records.append(record);stream.write(json.dumps(record,allow_nan=False)+'\n');stream.flush()
                if (len(records)-begin)%50==0:print('seed',seed_id,'evaluations',len(records)-begin,'source_clear',sum(v['source_clear'] for v in records[begin:]),flush=True)
                return record['objective_value']
            result=minimize(objective,seed,method='Powell',bounds=Bounds(lower,upper),options={'maxfev':400,'xtol':1e-4,'ftol':1e-8})
            seed_reproduced.append(same_pairs(records[begin]['source_human_guitar_intersections'],prior['rows'][0 if seed_id==0 else 47]['source_human_guitar_intersections']))
            solves.append(dict(seed_id=seed_id,initial_delta_rad=seed.tolist(),success=bool(result.success),status=int(result.status),message=str(result.message),
                nfev=int(result.nfev),nit=int(result.nit),stored_evaluations=len(records)-begin,terminal_requested_delta_rad=result.x.tolist(),terminal_objective=float(result.fun)))
    clear=[v for v in records if v['source_clear']]
    selected=min(clear,key=lambda v:(sum(d['distance_m']**2 for d in v['support_patch_distances'].values()),v['initial_delta_L2_rad'],-v['palm_neck_plane_alignment_abs'],v['order'])) if clear else None
    checks=dict(zero_pose_identity=zp<1e-6 and zr<1e-6,two_seed_HG_reproduced=len(seed_reproduced)==2 and all(seed_reproduced),
        bounded_two_solves=len(solves)==2 and all(0<s['nfev']==s['stored_evaluations']<=400 for s in solves) and len(records)<=800,
        all_other69_initial_held_exact=all(v['other69_q_and_held_exact'] for v in records),
        all_geometry_inputs_range_safe=all(v['within_effective_ranges'] for v in records if v['source_evaluated']),
        exclusions_explicit=all(v['numeric_violations'] and v['source_human_guitar_intersections'] is None and not v['source_clear'] for v in records if not v['source_evaluated']),
        all_clear_full_cross_self1188_up_identity=all(v['self_pair_count']==1188 and not v['source_cross_hand_intersections'] and not v['source_self_intersections'] and v['palm_up_proxy_z']>0 and v['upstream_pose_identity'] and v['other_meshes_identity'] and v['hand_relative_identity'] for v in clear),
        all81_targets_float32=all(np.array_equal(np.array(v['raw_absolute_targets_rad'],dtype=np.float32).astype(float),v['raw_absolute_targets_rad']) for v in records),
        all_delta_original015=all(max(abs(x) for x in v['actual_delta_rad'])<=.15 for v in records),
        saved_rows_exact=[json.loads(s) for s in (P/'evaluations.jsonl').read_text().splitlines()]==records)
    assert all(checks.values()),checks
    if selected:
        qnew=np.array(selected['raw_initial_rad'],dtype=np.float32);target=np.array(selected['raw_absolute_targets_rad'],dtype=np.float32)
        trial=copy.deepcopy(original)
        for n,i in zip(snapshot.arm,arm_indices):trial['initial_settings']['joint_angles_rad'][n]=float(qnew[i])
        assert trial['main_target_offsets_rad']==original['main_target_offsets_rad']
        folder=A/'trials/source_hand_arm_continuous_v1';folder.mkdir(exist_ok=False)
        trial_path=folder/'arm_continuous_clear.json';save(trial_path,trial)
        proposal=copy.deepcopy(old);row=copy.deepcopy(old['rows'][0]);row.pop('source_state',None)
        row.update(label='arm_continuous_clear',alpha=None,trial_path=str(trial_path),trial_sha256=sha(trial_path),expected_initial_angles_rad=qnew.astype(float).tolist(),
            expected_absolute_targets_rad=target.astype(float).tolist(),finger_target_policy='Measured finger hierarchy unchanged; left-arm12 coordinated initialization, all offsets and other69 initial/held targets preserved')
        proposal.update(checks=checks,rows=[row],scope='Conditional bounded arm source hypothesis; fresh actual native direct gate still required');save(P/'proposal.json',proposal)
        delta=np.r_[selected['actual_delta_rad'],np.zeros(6)];predicted=snapshot.poses(delta)
        save(P/'source_prediction.json',dict(poses_W={n:dict(position_m=p.tolist(),quaternion_xyzw=r.as_quat().tolist()) for n,(p,r) in predicted.items()},scope='Conditional source prediction only; never native state replay'))
    save(P/'search.json',dict(checks=checks,solves=solves,intervals=interval,selected_names=snapshot.arm,rows=records,selected=selected,clear_count=len(clear),
        zero_pose_position_error_m=zp,zero_pose_rotation_error_rad=zr,moving_body_names=sorted(moving_names),moving_collision_body_names=sorted({s['body'] for s in moving}),
        native_initializations=0,physics_steps=0,scope='Bounded source-only optimization; no native dynamics/contact/playing or stability certification'))
    print(json.dumps(dict(checks=checks,solves=solves,evaluations=len(records),clear_count=len(clear),selected_order=selected['order'] if selected else None),indent=2))


if __name__=='__main__':main()
