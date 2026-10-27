"""Summarize selected native initial values and measured elbow/contact scope."""
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read, save, sha, pose
from .upper_arm_static_geometry_v1 import ROOT


def main():
    p=ROOT/'docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1'
    folders=[p/'native_upper50_v13_static',p/'native_upper50_v14_elbow5']
    paths=[Path(__file__).resolve(),ROOT/'stability_adapter_2/initial_pose_noise_v1.py',ROOT/'stability_adapter_2/upper_arm_static_geometry_v1.py',p/'analysis_final_v2.json',p/'timelines_final_v1.json']
    paths += [n/f for n in folders for f in ('initial_values.json','native_properties.json','media/physics_endpoint_contacts.json')]
    inputs={str(f):sha(f) for f in paths};save(p/'selected_summary_before_v1.json',inputs)
    analysis=read(p/'analysis_final_v2.json');timeline=read(p/'timelines_final_v1.json')
    initial=read(folders[0]/'initial_values.json');state=initial['native_initial_state']
    assert initial==read(folders[1]/'initial_values.json')
    preferred={'Torso':[10,0,-10],'Spine':[20,0,0],'Chest':[0,20,0],'R_Thorax':[0,-10,10],'R_Shoulder':[0,35,0]}
    q=analysis['cases'][folders[0].name]['initial_q_deg']
    comparisons={name:{'provided_scalar_deg':values,'selected_scalar_deg':[q[name+'_'+axis] for axis in 'xyz']} for name,values in preferred.items()}
    props=read(folders[0]/'native_properties.json');assert props==read(folders[1]/'native_properties.json')
    com=np.zeros(3);mass=0.
    for body,prop,name in zip(state['guitar_body_states'],props['applied'],initial['guitar_body_names']):
        assert prop['name']==name
        bp,br=pose(body);m=prop['mass_kg'];mass+=m;com+=m*(bp+br.apply(prop['COM_body_m']))
    com/=mass;assert abs(mass-props['total_mass_kg'])<1e-10
    motions={}
    for folder in folders:
        rows=read(folder/'media/physics_endpoint_contacts.json')['rows']
        hp=state['human_body_states'];names=initial['human_body_names']
        rel0=pose(hp[names.index('R_Shoulder')])[1].inv()*pose(hp[names.index('R_Elbow')])[1]
        relative=[(pose(r['human_body_states']['R_Shoulder'])[1].inv()*pose(r['human_body_states']['R_Elbow'])[1]) for r in rows]
        angles=np.rad2deg((rel0.inv()*Rotation.from_quat([r.as_quat() for r in relative])).magnitude())
        forearm=0;hand=0
        for row in rows:
            bodies={c[k] for c in row['right_distal_guitar_contacts'] for k in ('body0_name','body1_name')}
            forearm+=int('human/R_Elbow' in bodies)
            hand+=int(any(n=='human/R_Wrist' or n.startswith('human/RH:') for n in bodies))
        assert forearm==analysis['cases'][folder.name]['contacts']['right_forearm_body_contacts']
        motions[folder.name]={'right_wrist_hand_contact_steps':hand,'right_forearm_contact_steps':forearm,
            'max_Shoulder_to_Elbow_relative_SO3_delta_deg_240Hz':float(angles.max()),
            'actual_elbow_scalar_peak_to_peak_2p5_to5_deg_60Hz':timeline['cases'][folder.name]['elbow_actual_2p5_to_5s_range_deg']}
    assert all(sha(f)==h for f,h in inputs.items())
    save(p/'selected_summary_v1.json',{'passed':True,'input_sha256':inputs,'provided_body_centre_W_m':[.175,-.05,.665],
        'selected_body_centre_W_m':analysis['cases'][folders[0].name]['initial_BBcentre_W_m'],
        'selected_actor_root_state':state['guitar_body_states'][0],'total_guitar_mass_kg':mass,'total_guitar_COM_W_m':com.tolist(),
        'preferred_vs_selected_scalar_deg':comparisons,'selected_all81_scalar_deg':q,'movement_and_hand_contacts':motions,
        'scope':'body centre is transformed local geometry BB centre; distinct actor root and total COM; scalar joint axes are not world Euler axes; actual right hand and forearm contacts separated; native R_Hip support recorded, L_Hip contacts not recorded; no exclusive two-support or passive-equilibrium claim'})
    print(comparisons);print(motions);print('guitar mass',mass,'COM',com.tolist())


if __name__=='__main__':main()
