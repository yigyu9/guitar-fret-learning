"""Compare actual native posture geometry with the preserved waist initial baseline."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation
from stability_adapter_2.initial_pose_noise_v1 import pose
P=Path(__file__).resolve().parent
BASE=P.parent/'right_thigh_waist_v1/native_static_v2/initial_values.json'
HELPER=P.parents[4]/'stability_adapter_2/initial_pose_noise_v1.py'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cases',type=Path,nargs='+',required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    paths=[BASE,HELPER,Path(__file__).resolve()]
    for folder in args.cases:paths += [folder/'initial_values.json',folder/'final_state.json',folder/'report.json']
    inputs={str(f.resolve()):sha(f) for f in paths};baseline=read(BASE);names=baseline['human_body_names'];bs=baseline['native_initial_state']
    def poses(s):return {n:pose(b) for n,b in zip(names,s['human_body_states'])}
    original=poses(bs);right=original['R_Hip'][0]-original['L_Hip'][0];right[2]=0;right/=np.linalg.norm(right)
    front=np.array([-right[1],right[0],0.]);gp,gr=pose(bs['guitar_body_states'][0])
    # Unchanged geometry bbox centre previously audited in the sealed baseline analysis.
    bbox_file=BASE.parent.parent/'analysis_final_v1/analysis.json';inputs[str(bbox_file)]=sha(bbox_file)
    bbox=np.array(read(bbox_file)['support']['body_centre_G_m']);centre=gp+gr.apply(bbox)
    inward=centre-original['R_Elbow'][0];inward/=np.linalg.norm(inward)
    def tilt(ps):
        up=ps['Chest'][1].apply([0,0,1]);return float(np.rad2deg(np.arctan2(up@front,up[2])))
    def geometry(s):
        ps=poses(s);g,r=pose(s['guitar_body_states'][0]);current= g+r.apply(bbox)
        return {'Chest_localZ_forward_tilt_deg':tilt(ps),'right_elbow_to_current_body_bbox_centre_m':float(np.linalg.norm(ps['R_Elbow'][0]-current))}
    cases={}
    for folder in args.cases:
        v=read(folder/'initial_values.json');s=v['native_initial_state'];report=read(folder/'report.json')
        assert report['completed'] and v['human_body_names']==names
        ps=poses(s);parent_rotations={}
        for parent,child in [('Pelvis','Torso'),('Torso','Spine'),('Spine','Chest')]:
            before=original[parent][1].inv()*original[child][1];after=ps[parent][1].inv()*ps[child][1]
            parent_rotations[parent+'->'+child]=float(np.rad2deg((before.inv()*after).magnitude()))
        guitar_errors=[]
        for old,new in zip(bs['guitar_body_states'],s['guitar_body_states']):
            p0,r0=pose(old);p1,r1=pose(new);guitar_errors.append((np.linalg.norm(p1-p0),(r0.inv()*r1).magnitude()))
        assert len(guitar_errors)==len(bs['guitar_body_states'])
        assert max(e[0] for e in guitar_errors)<3e-6 and max(e[1] for e in guitar_errors)<1e-5
        q0=np.array(baseline['q_ref_rad']);q=np.array(v['q_ref_rad']);body=[i for i,n in enumerate(v['joint_names']) if n.startswith(('Torso_','Spine_','Chest_'))]
        cases[folder.name]={'initial':geometry(s),'final':geometry(read(folder/'final_state.json')),
          'actual_initial_Chest_tilt_reduction_deg':tilt(original)-tilt(ps),
          'actual_initial_elbow_inward_projection_m':float((ps['R_Elbow'][0]-original['R_Elbow'][0])@inward),
          'actual_initial_elbow_distance_reduction_m':float(np.linalg.norm(original['R_Elbow'][0]-centre)-np.linalg.norm(ps['R_Elbow'][0]-centre)),
          'initial_body9_max_scalar_delta_deg':float(np.rad2deg(abs(q[body]-q0[body]).max())),
          'initial_parent_child_rotation_delta_deg':parent_rotations,
          'initial_guitar39_max_position_error_m':float(max(e[0] for e in guitar_errors)),
          'initial_guitar39_max_rotation_error_rad':float(max(e[1] for e in guitar_errors))}
    assert all(sha(p)==h for p,h in inputs.items())
    with args.out.open('x') as f:json.dump({'input_sha256':inputs,'baseline_case':str(BASE.parent),'baseline_geometry':geometry(bs),
      'cases':cases,'scope':'actual body-origin/rotation posture comparison; Chest localZ tilt is a defined frame projection, not clinical spinal flexion or sum of scalar DOFs; bbox is not mass centre'},f,ensure_ascii=False,indent=2,allow_nan=False)

if __name__=='__main__':main()
