"""Seven scalar-hinge source checks anchored to the actual rejected native pose."""
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
A = R / 'stability_adapter_2'
B = R / 'docs/2026-10-12/stability_adapter_2/results'
P = B / 'source_hand_thumb2_clearance_v1'
OLD = B / 'fixed_strap_source_hand_initial_v1'
POLICY = B / 'torso_hold_native_collision_v1/initial_collision/shape_properties.json'
PROXY = B / 'palm_neck_side_v1/initial_audit_v2/audit.json'
RANGES = B / 'fixed_strap_source_compatibility_v1/joint_ranges.jsonl'


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d): Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')


def main():
    assert not (P/'search.json').exists() and not (P/'proposal.json').exists()
    initial = read(OLD/'native/initial_values.json')
    inventory = read(OLD/'artifact_inventory.json')
    assert sha(OLD/'native/initial_values.json') == inventory[str(OLD/'native/initial_values.json')]['sha256']
    policy, old, proxy = read(POLICY),read(OLD/'proposal.json'),read(PROXY)
    names,bodies,state = initial['human_joint_names'],initial['human_body_names'],initial['native_initial_state']
    guitar_names = [v['body'] for v in policy['actors']['guitar']['body_ranges']]
    config = read(A/'config.json');config['humanoid_asset'] = str(ASSET)
    scene = SimpleNamespace(config=config,human=0,guitar=1,env=None,
        gym=SimpleNamespace(get_actor_rigid_body_names=lambda env,actor:bodies if actor == 0 else guitar_names),
        bodies=lambda actor:state['human_body_states'] if actor == 0 else state['guitar_body_states'])
    probe = build_probe(scene)
    meshes, base_hg, base_cross = source_checks(probe)
    snapshot = CoupledSnapshot(names,bodies,state,state)
    zero = snapshot.poses(np.zeros(18))
    zp = max(float(np.linalg.norm(p-pose(state['human_body_states'][bodies.index(n)])[0])) for n,(p,r) in zero.items())
    zr = max(float((r*Rotation.from_quat(pose(state['human_body_states'][bodies.index(n)])[1]).inv()).magnitude()) for n,(p,r) in zero.items())
    assert zp < 1e-6 and zr < 1e-6
    humans = [s for s in probe[2] if s['actor'] == 'human']
    guitars = [s for s in probe[2] if s['actor'] == 'guitar']
    hg_pairs = [(a,b) for a in humans for b in guitars]
    cross_pairs = [(a,b) for a in humans if a['body'].startswith('LH:') or a['body']=='L_Wrist'
                   for b in humans if b['body'].startswith('RH:') or b['body']=='R_Wrist']
    xml = ET.parse(ASSET).getroot()
    parents = {c.get('name'):p.get('name') for p in xml.iter('body') for c in p.findall('body')}
    def distance(a,b):
        chain=[];current=a
        while current in parents:chain.append(current);current=parents[current]
        chain.append(current);steps=0;current=b
        while current not in chain and current in parents:steps+=1;current=parents[current]
        return steps+chain.index(current) if current in chain else 99
    filters = policy['mask_audit']['native_filters']
    self_pairs = []
    for i,a in enumerate(humans):
        for b in humans[i+1:]:
            if distance(a['body'],b['body']) <= 2:continue
            sameleft = all(s['body'].startswith('LH:') or s['body'] in ('L_Wrist','L_Elbow') for s in (a,b))
            allowed = all(x&y == 0 for x in filters[a['body']] for y in filters[b['body']])
            if sameleft or allowed:self_pairs.append((a,b))
    assert len(self_pairs) == 1188
    moving_names = {'LH:thumb2','LH:thumb3','LH:thumb_top'}
    moving = [s for s in humans if s['body'] in moving_names]
    assert {s['body'] for s in moving} == {'LH:thumb2','LH:thumb3'}
    gp,gq = pose(state['guitar_body_states'][0]);gr = Rotation.from_quat(gq)
    patch = gr.apply(np.array(old['regions_G_m']['thumb']))+gp
    bound = {v['name']:v for v in [json.loads(s) for s in RANGES.read_text().splitlines()] if v['label']=='initial_aligned' and v['kind']=='held'}
    q0 = np.array(initial['initial_PD_target_rad'],dtype=np.float32)
    t0 = np.array(initial['preserved_absolute_targets_rad'],dtype=np.float32)
    axis = names.index('LH:thumb2')
    records = []
    for requested in [0.,-.05,.05,-.10,.10,-.20,.20]:
        angle = float(np.float32(float(q0[axis])+requested))
        delta = np.zeros(18);delta[snapshot.selected.index('LH:thumb2')] = angle-float(q0[axis])
        transformed = snapshot.meshes(meshes,moving,delta)
        def screen(pairs):
            found=[]
            for a,b in pairs:
                radius = intersection(transformed[a['geom_id']],transformed[b['geom_id']])
                if radius > 1e-7:found.append(dict(a=a['body'],b=b['body'],common_radius_m=radius))
            return found
        hg,cross,self_overlaps = screen(hg_pairs),screen(cross_pairs),screen(self_pairs)
        poses = snapshot.poses(delta)
        up = float(poses['LH:palm'][1].apply(proxy['palmar_normal_proxy_local'])[2])
        patches = {n:certified_distance(transformed[next(s['geom_id'] for s in moving if s['body']==n)],patch) for n in ['LH:thumb2','LH:thumb3']}
        within = bound['LH:thumb2']['effective_lower_rad'] <= angle <= bound['LH:thumb2']['effective_upper_rad']
        unchanged = all(float(np.linalg.norm(p-snapshot.actual[n][0])) < 1e-6 and float((r*snapshot.actual[n][1].inv()).magnitude()) < 1e-6 for n,(p,r) in poses.items() if n not in moving_names)
        assert unchanged
        records.append(dict(requested_delta_rad=requested,actual_delta_rad=angle-float(q0[axis]),initial_angle_rad=angle,
            source_human_guitar_intersections=hg,source_cross_hand_intersections=cross,source_self_intersections=self_overlaps,
            self_pair_count=len(self_pairs),palm_up_proxy_z=up,within_effective_range=within,
            other_pose_identity=unchanged,thumb_to_rear_patch=patches,
            source_clear=bool(within and not hg and not cross and not self_overlaps and up>0)))
    zero_row = records[0]
    checks = dict(seven_conditions=len(records)==7,zero_pose_identity=zp<1e-6 and zr<1e-6,
        base_hg_reproduced=zero_row['source_human_guitar_intersections'] == [dict(a=d['human'],b=d['guitar'],common_radius_m=d['common_radius_m']) for d in base_hg],
        base_cross_reproduced=zero_row['source_cross_hand_intersections'] == [dict(a=d['left'],b=d['right'],common_radius_m=d['common_radius_m']) for d in base_cross],
        zero_thumb2_reproduces_rejection=len(base_hg)==1 and base_hg[0]['human']=='LH:thumb2' and abs(base_hg[0]['common_radius_m']-.004288364821171085)<1e-12,
        all_other_poses_identity=all(v['other_pose_identity'] for v in records),
        all_angles_in_effective_range=all(v['within_effective_range'] for v in records),
        all_self_pair_counts1188=all(v['self_pair_count']==1188 for v in records))
    assert all(checks.values()),checks
    clear = [v for v in records if v['source_clear']]
    selected = min(clear,key=lambda v:(abs(v['actual_delta_rad']),v['thumb_to_rear_patch']['LH:thumb3']['distance_m'])) if clear else None
    if selected:
        row = old['rows'][0];trial = read(row['trial_path']);qnew=q0.copy();target=t0.copy()
        qnew[axis]=target[axis]=selected['initial_angle_rad']
        trial['initial_settings']['joint_angles_rad']['LH:thumb2']=float(qnew[axis])
        trial['main_target_offsets_rad']['LH:thumb2']=0.
        main_indices=[names.index(n) for n in initial['main_control_joint_names']]
        offsets=np.array([trial['main_target_offsets_rad'].get(names[i],0.) for i in main_indices])
        composed=compose(qnew,main_indices,offsets,initial['PD_properties']['lower'],initial['PD_properties']['upper'])
        assert np.array_equal(composed,target)
        assert all(bound[n]['effective_lower_rad'] <= float(qnew[i]) <= bound[n]['effective_upper_rad'] and bound[n]['effective_lower_rad'] <= float(target[i]) <= bound[n]['effective_upper_rad'] for i,n in enumerate(names))
        folder=A/'trials/source_hand_thumb2_clearance_v1';folder.mkdir(exist_ok=False)
        trial_path=folder/'thumb2_clear.json';save(trial_path,trial)
        proposal=copy.deepcopy(old);newrow=copy.deepcopy(row)
        newrow.update(label='thumb2_clear',trial_path=str(trial_path),trial_sha256=sha(trial_path),
            expected_initial_angles_rad=qnew.astype(float).tolist(),expected_absolute_targets_rad=target.astype(float).tolist(),
            finger_target_policy='Five range-compatible hinges retained; thumb2 initial/held identical at selected scalar clearance angle; other80 goals preserved')
        proposal.update(checks=checks,rows=[newrow],scope='Scalar thumb2 source candidate anchored to actual native finger1; fresh direct native admission still required')
        save(P/'proposal.json',proposal)
    save(P/'search.json',dict(checks=checks,rows=records,selected=selected,zero_pose_position_error_m=zp,zero_pose_rotation_error_rad=zr,
        native_initializations=0,physics_steps=0,scope='Static scalar hinge source proxy, not actual Gym motion or cooked contact certification; only thumb2/3/top meshes transformed; current finger1 native transforms preserved'))
    print(json.dumps(dict(checks=checks,clear_count=len(clear),selected_delta_rad=selected['actual_delta_rad'] if selected else None,
        intersections=[dict(delta=v['actual_delta_rad'],pairs=v['source_human_guitar_intersections']) for v in records]),indent=2))


if __name__ == '__main__':main()
