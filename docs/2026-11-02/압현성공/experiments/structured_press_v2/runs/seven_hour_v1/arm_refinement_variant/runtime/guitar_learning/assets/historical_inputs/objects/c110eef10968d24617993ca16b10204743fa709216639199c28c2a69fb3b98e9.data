"""Small initial guitar translation and native-coordinate left-wrist approach."""
import copy
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from .fixed_lower_environment import FixedLowerEnvironment
from .environment import ROOT, np
from .build_fixed_lower_asset import read, sha, pose
from .replay_contact_geometry import recorded_probe
from .render_best_run_video import set_saved_pose
from .search_hand_support import palm_neck_gap
from .pose_strap_inputs import pose_metrics
from .plot_neck_palm import geometry
import mujoco
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
from scipy.optimize import least_squares, linprog
from types import SimpleNamespace

PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1'
BASE_RUN=PHASE.parent/'lower_body_fixed_v1/full_1s'
BASE_SETTINGS=ROOT/'stability_adapter_2/trials/left_palm_boundary_v1/l_wrist_x_minus0125.json'
TRIALS=Path(__file__).with_name('trials')/'thigh_palm_support_v1/elbow_wrist'


class SupportEnvironment(FixedLowerEnvironment):
    def __init__(self,settings,guitar_shift):
        self.guitar_initial_translation_m=np.asarray(guitar_shift,dtype=float)
        super().__init__(settings)

    def _create_scene(self):
        # One creation-pose change; no state write during integration.
        self.goal_position+=self.guitar_initial_translation_m
        super()._create_scene()


def intersection(a,b):
    if np.any(np.minimum(a.bounds[1],b.bounds[1])-np.maximum(a.bounds[0],b.bounds[0])<=1e-7):
        return 0.
    equations=np.vstack((ConvexHull(a.vertices).equations,ConvexHull(b.vertices).equations))
    matrix=np.column_stack((equations[:,:3],np.ones(len(equations))))
    result=linprog([0,0,0,-1],A_ub=matrix,b_ub=-equations[:,3],bounds=[(None,None)]*3+[(0,None)],method='highs')
    if result.status==2:
        return 0.
    if not result.success or np.maximum(matrix@result.x+equations[:,3],0).max()>1e-7:
        raise RuntimeError('source intersection solve failed')
    return float(result.x[3])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--near-touch',action='store_true')
    args=parser.parse_args()
    trials=TRIALS.parent/'near_touch' if args.near_touch else TRIALS
    output=PHASE/('search_near_touch.json' if args.near_touch else 'search.json')
    if trials.exists() or output.exists():
        raise FileExistsError('preserve support search')
    report=read(BASE_RUN/'report.json');state0=read(BASE_RUN/'states.json')[0]
    names=report['human_joint_names'];body_names=report['human_body_names']
    q0=np.array(report['initial_joint_targets_rad']);base=read(BASE_SETTINGS)
    preflight=read(PHASE/'preflight.json')
    for chain in (report['source_sha256'],preflight['input_sha256']):
        if not all(sha(Path(p))==h for p,h in chain.items()):
            raise ValueError('historical input SHA mismatch before merging')
    inputs=dict(report['source_sha256']);inputs.update(preflight['input_sha256'])
    files=[Path(__file__).resolve(),PHASE/'preflight.json',BASE_RUN/'report.json',BASE_RUN/'states.json',BASE_SETTINGS]
    files += [Path(__file__).with_name(n) for n in ('search_hand_support.py','pose_strap_inputs.py',
        'plot_neck_palm.py','replay_contact_geometry.py','render_best_run_video.py')]
    inputs.update({str(p):sha(p) for p in files})
    if not all(sha(Path(p))==h for p,h in inputs.items()):
        raise ValueError('search input/source SHA mismatch before calculation')
    contact=preflight['right_thigh_to_guitar'][0]
    direction=np.array(contact['guitar_witness_world_m'])-contact['centerline_witness_world_m']
    direction/=np.linalg.norm(direction)
    thigh_gap=.000002 if args.near_touch else .00005
    shift=-direction*(contact['capsule_surface_separation_m']-thigh_gap)
    model,data,shapes=recorded_probe(BASE_RUN,0)
    xml=ET.parse(ROOT/'tab2body/assets/smpl_mpl_hands_body.xml').getroot()
    parents={c:p for p in xml.iter('body') for c in p.findall('body')}
    limb=next(b for b in xml.iter('body') if b.get('name')=='L_Thorax')
    relatives={};axes={}
    for b in limb.iter('body'):
        name=b.get('name');parent=parents[b].get('name')
        pp,pq=pose(state0['human_body_states'][body_names.index(parent)])
        bp,bq=pose(state0['human_body_states'][body_names.index(name)])
        rp,rb=Rotation.from_quat(pq),Rotation.from_quat(bq)
        relatives[name]=(parent,rp.inv().apply(bp-pp),rp.inv()*rb)
        if name in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'):
            joints=b.findall('joint')
            axes[name]=(np.column_stack([np.fromstring(j.get('axis'),sep=' ') for j in joints]),
                [names.index(j.get('name')) for j in joints])

    def fk(q):
        state=copy.deepcopy(state0)
        for name,(parent,position,relative) in relatives.items():
            pp,pq=pose(state['human_body_states'][body_names.index(parent)]);rp=Rotation.from_quat(pq)
            if name in axes:
                basis,indices=axes[name]
                relative=Rotation.from_rotvec(basis@q[indices])*Rotation.from_rotvec(basis@q0[indices]).inv()*relative
            bp=pp+rp.apply(position);bq=(rp*relative).as_quat()
            body=state['human_body_states'][body_names.index(name)]
            body['pose']={'p':dict(zip('xyz',bp)),'r':dict(zip(('x','y','z','w'),bq))}
        for body in state['guitar_body_states']:
            for a,d in zip('xyz',shift):body['pose']['p'][a]+=float(d)
        for i,value in enumerate(q):state['human_dof_states'][i]['pos']=float(value)
        return state

    palm_witness=min(preflight['left_palm_to_neck_unsigned_convex_QP'],key=lambda r:r['distance_m'])
    pp,pq=pose(state0['human_body_states'][body_names.index('LH:palm')])
    local_point=Rotation.from_quat(pq).inv().apply(np.array(palm_witness['witness_world_m'][0])-pp)
    normal=np.array(palm_witness['witness_world_m'][1])-palm_witness['witness_world_m'][0];normal/=np.linalg.norm(normal)
    indices=[names.index('L_Wrist_'+a) for a in 'xyz']+[names.index('L_Elbow_x')]
    arm_names=report['arm_names']
    lower=np.array([report['diagnostic_lower_rad'][arm_names.index(names[i])] for i in indices])
    upper=np.array([report['diagnostic_upper_rad'][arm_names.index(names[i])] for i in indices])
    lower=np.maximum(lower,q0[indices]-.025);upper=np.minimum(upper,q0[indices]+.025)
    rows=[];trials.mkdir(parents=True)
    for clear in ((.000002,) if args.near_touch else (.00005,.0001,.00015)):
        target=np.array(palm_witness['witness_world_m'][1])+shift-normal*clear
        def residual(values):
            q=q0.copy();q[indices]=values
            p,r=pose(fk(q)['human_body_states'][body_names.index('LH:palm')])
            return np.r_[(p+Rotation.from_quat(r).apply(local_point)-target)*1000,
                .01*(values-q0[indices])]
        solve=least_squares(residual,q0[indices],bounds=(lower,upper),xtol=1e-12,ftol=1e-12,gtol=1e-12)
        q=q0.copy();q[indices]=solve.x;state=fk(q)
        set_saved_pose(model,mujoco,report,state);mujoco.mj_forward(model,data)
        probe=(model,data,shapes);gap=palm_neck_gap(probe)
        scene=SimpleNamespace(human=0,guitar=1,human_bodies=body_names,guitar_bodies=report['guitar_body_names'],
            bodies=lambda actor:state['human_body_states'] if actor==0 else state['guitar_body_states'])
        hand=pose_metrics(scene,probe)
        meshes={s['geom_id']:geometry(model,data,s) for s in shapes}
        unintended=[];hand_pairs=[]
        for a in [s for s in shapes if s['actor']=='human']:
            for b in [s for s in shapes if s['actor']=='guitar']:
                radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
                if radius>1e-7:unintended.append({'human':a['body'],'guitar':b['body'],'common_radius_m':radius})
        for a in [s for s in shapes if s['body'].startswith('LH:') or s['body']=='L_Wrist']:
            for b in [s for s in shapes if s['body'].startswith('RH:') or s['body']=='R_Wrist']:
                if intersection(meshes[a['geom_id']],meshes[b['geom_id']])>1e-7:hand_pairs.append([a['body'],b['body']])
        angles=dict(base['joint_angles_rad']);angles.update({names[i]:float(q[i]) for i in indices})
        settings=dict(base,joint_angles_rad=angles,strap_rest_length_m=None)
        name='clear_'+str(round(clear*1e6))+'um'
        (trials/(name+'.json')).write_text(json.dumps(settings,indent=2)+'\n')
        rows.append({'name':name,'settings_path':str(trials/(name+'.json')),
            'joint_delta_rad':dict(zip([names[i] for i in indices],(q[indices]-q0[indices]).tolist())),
            'point_fit_error_m':float(np.linalg.norm(solve.fun[:3])/1000),'palm_neck':gap,'hand':hand,
            'source_intersections':unintended,'hand_intersections':hand_pairs,
            'accepted':bool(solve.success and np.linalg.norm(solve.fun[:3])<.001 and not unintended and not hand_pairs
                and hand['palm_normal_valid'] and hand['neck_projection_in_range']
                and hand['palm_up_dot']>=0 and hand['palm_height_vs_local_lower_m']<=0),
            'predicted_state':state})
    if not all(sha(Path(p))==h for p,h in inputs.items()):
        raise ValueError('search inputs changed during calculation')
    output.write_text(json.dumps({'guitar_initial_translation_m':shift.tolist(),'right_thigh_target_source_gap_m':thigh_gap,
        'scope':'Calibrated initial-only spherical FK proposals; fresh native FK and contact checks still required. Capsule hulls are inner approximations.',
        'rows':rows,'input_sha256':inputs,'inputs_verified_before_and_after':True},indent=2,allow_nan=False)+'\n')
    print(json.dumps({'shift_m':shift.tolist(),'rows':[{k:r[k] for k in ('name','joint_delta_rad','point_fit_error_m','accepted','source_intersections')} for r in rows]},indent=2))


if __name__=='__main__':main()
