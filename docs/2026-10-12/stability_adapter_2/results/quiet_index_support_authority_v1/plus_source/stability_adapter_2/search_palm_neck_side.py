"""Initial arm FK proposals for the selected blue neck side; no dynamics."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

from .audit_palm_side_target import PHASE, BASE, PROPOSAL, closest_polygon
from .environment import ROOT, np
from .build_fixed_lower_asset import read, sha, pose
from .replay_contact_geometry import recorded_probe
from .render_best_run_video import set_saved_pose
from .plot_neck_palm import geometry
from .pose_strap_inputs import pose_metrics
from .thigh_palm_support import intersection
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
import mujoco

REFERENCE=ROOT/'docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/short/baseline'
TRIALS=ROOT/'stability_adapter_2/trials/palm_neck_side_v1'


def arm_fk(reference,q0,state0):
    names=reference['human_joint_names'];body_names=reference['human_body_names']
    xml=ET.parse(ROOT/'tab2body/assets/smpl_mpl_hands_body.xml').getroot()
    parents={c:p for p in xml.iter('body') for c in p.findall('body')}
    relatives={};axes={}
    limb=next(b for b in xml.iter('body') if b.get('name')=='L_Thorax')
    for body in limb.iter('body'):
        name=body.get('name');parent=parents[body].get('name')
        pp,pq=pose(state0['human_body_states'][body_names.index(parent)])
        bp,bq=pose(state0['human_body_states'][body_names.index(name)])
        rp,rb=Rotation.from_quat(pq),Rotation.from_quat(bq)
        relatives[name]=(parent,rp.inv().apply(bp-pp),rp.inv()*rb)
        if name in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'):
            joints=body.findall('joint')
            axes[name]=(np.column_stack([np.fromstring(j.get('axis'),sep=' ') for j in joints]),
                        [names.index(j.get('name')) for j in joints])

    def fk(q):
        state=copy.deepcopy(state0)
        for name,(parent,position,relative0) in relatives.items():
            pp,pq=pose(state['human_body_states'][body_names.index(parent)])
            rp=Rotation.from_quat(pq);relative=relative0
            if name in axes:
                basis,indices=axes[name]
                relative=Rotation.from_rotvec(basis@q[indices])*Rotation.from_rotvec(basis@q0[indices]).inv()*relative0
            bp=pp+rp.apply(position);bq=(rp*relative).as_quat()
            state['human_body_states'][body_names.index(name)]['pose']={'p':dict(zip('xyz',bp)), 'r':dict(zip('xyzw',bq))}
        for i,value in enumerate(q):state['human_dof_states'][i]['pos']=float(value)
        return state
    return fk


def main():
    out=PHASE/'fk_search';out.mkdir(exist_ok=False);TRIALS.mkdir(exist_ok=False)
    audit_path=PHASE/'initial_audit/audit.json';audit=read(audit_path)
    reference=read(REFERENCE/'report.json');base=read(BASE)
    q0=np.array(audit['initial_joint_targets_rad']);names=audit['human_joint_names'];bodies=audit['human_body_names']
    indices=np.array(reference['arm_indices'][:12])
    low=np.array(reference['diagnostic_lower_rad'][:12]);high=np.array(reference['diagnostic_upper_rad'][:12])
    files=[Path(__file__).resolve(),Path(__file__).with_name('audit_palm_side_target.py'),audit_path,
           BASE,PROPOSAL,REFERENCE/'report.json',REFERENCE/'states.json']
    files += [Path(p) for p in audit['input_sha256'] if '/docs/' not in p]
    hashes={str(p):sha(p) for p in files}
    fk=arm_fk(reference,q0,audit['initial_state'])
    model,data,shapes=recorded_probe(REFERENCE,0)
    local=np.array(audit['palmar_ray_point_local_m']);normal_local=np.array(audit['palmar_normal_proxy_local'])
    normal=np.array(audit['target_outward_normal_W']);center=np.array(audit['target_center_W_m'])
    polygon=np.array(audit['target_polygon_W_m'])
    rows=[]
    for clear in (.001,.003,.006,.01):
        target=center+normal*clear
        def residual(values):
            q=q0.copy();q[indices]=values;state=fk(q)
            p,r=pose(state['human_body_states'][bodies.index('LH:palm')]);rotation=Rotation.from_quat(r)
            return np.r_[1000*(p+rotation.apply(local)-target),30*(rotation.apply(normal_local)+normal),.02*(values-q0[indices])]
        fit=least_squares(residual,np.clip(q0[indices],low+1e-10,high-1e-10),bounds=(low,high),
                          xtol=1e-11,ftol=1e-11,gtol=1e-11,max_nfev=1000)
        q=q0.copy();q[indices]=fit.x;state=fk(q)
        set_saved_pose(model,mujoco,reference,state);mujoco.mj_forward(model,data)
        probe=(model,data,shapes);meshes={s['geom_id']:geometry(model,data,s) for s in shapes}
        overlaps=[];crosshands=[]
        for a in [s for s in shapes if s['actor']=='human']:
            for b in [s for s in shapes if s['actor']=='guitar']:
                radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
                if radius>1e-7:overlaps.append({'human':a['body'],'guitar':b['body'],'common_radius_m':radius})
        for a in [s for s in shapes if s['body'].startswith('LH:') or s['body']=='L_Wrist']:
            for b in [s for s in shapes if s['body'].startswith('RH:') or s['body']=='R_Wrist']:
                radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
                if radius>1e-7:crosshands.append({'left':a['body'],'right':b['body'],'common_radius_m':radius})
        scene=SimpleNamespace(human=0,guitar=1,human_bodies=bodies,guitar_bodies=reference['guitar_body_names'],
                              bodies=lambda actor:state['human_body_states'] if actor==0 else state['guitar_body_states'])
        hand=pose_metrics(scene,probe)
        palm=meshes[next(s['geom_id'] for s in shapes if s['body']=='LH:palm')]
        p,r=pose(state['human_body_states'][bodies.index('LH:palm')]);rotation=Rotation.from_quat(r)
        point=p+rotation.apply(local)
        name='clear_'+str(round(clear*1000))+'mm'
        settings=dict(base,joint_angles_rad=dict(base['joint_angles_rad']))
        settings['joint_angles_rad'].update({names[i]:float(q[i]) for i in indices})
        path=TRIALS/(name+'.json');path.write_text(json.dumps(settings,indent=2)+'\n')
        row={'name':name,'settings_path':str(path),'settings_sha256':sha(path),'source_state':state,
             'target_clearance_m':clear,'point_fit_error_m':float(np.linalg.norm(point-target)),
             'palm_normal_to_inward_target_dot':float(rotation.apply(normal_local)@(-normal)),
             'source_hull_to_blue_polygon':closest_polygon(palm,polygon),'source_intersections':overlaps,
             'cross_hand_intersections':crosshands,'hand':hand,
             'left_arm_delta_rad':dict(zip([names[i] for i in indices],(q[indices]-q0[indices]).tolist())),
             'fit_success':bool(fit.success),'source_clear':not overlaps and not crosshands,
             'accepted_for_fresh_native':bool(fit.success and not overlaps and not crosshands and
                 hand['palm_normal_valid'] and hand['palm_up_dot']>=0 and hand['neck_projection_in_range'] and
                 hand['palm_height_vs_local_lower_m']<=0)}
        rows.append(row)
        (out/'search.json').write_text(json.dumps({'rows':rows,'input_sha256':hashes,'physics_steps':0,
            'native_initializations':0,'scope':'calibrated FK proposal; fresh native proof required'},indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:row[k] for k in ('name','point_fit_error_m','palm_normal_to_inward_target_dot','source_hull_to_blue_polygon','source_intersections','cross_hand_intersections','accepted_for_fresh_native')},indent=2),flush=True)
    if not all(sha(Path(p))==h for p,h in hashes.items()):raise AssertionError('search inputs changed')


if __name__=='__main__':main()
