"""Audit measured pick crossings in moving guitar frame with the original detector."""
import argparse
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose
from .search_elbow_wrist_ready_pose_v1 import ROOT,A,P,B
from .elbow_wrist_strike_source_v1 import string_segments


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--cases',nargs='+',type=Path,required=True);args=parser.parse_args()
    paths=[Path(__file__).resolve(),A/'ELBOW_WRIST_READY_CONTROL_PLAN_V3.md',B/'diagnostic_v1/diagnostic.json']+list(A.glob('*.py'))+list((ROOT/'tab2body').rglob('*.py'))+[f for n in args.cases for f in n.rglob('*') if f.is_file()]
    inputs={str(f.resolve()):sha(f) for f in paths};save(args.out.with_name(args.out.stem+'_before.json'),inputs)
    import torch
    from tab2body.env.strike_detector import PickStrikeDetector
    from tab2body.strike_cfg import STRIKE
    cfg=STRIKE['detector'];zone=STRIKE['zone'];centre=np.array(read(B/'diagnostic_v1/diagnostic.json')['guitar_centre_G_m']);results={}
    for n in args.cases:
        report=read(n/'report.json');initial=read(n/'initial_values.json');state=initial['native_initial_state'];steps=report['physics_steps'];rows=read(n/'media/physics_endpoint_contacts.json')['rows'];targets=read(n/'media/six_joint_target_rows.json')['rows']
        assert len(rows)==steps and report['inputs_unchanged'] and not report['forbidden_calls'] and not report['strap_enabled'] and not report['checkpoints_connected']
        assert all(row['other75_exact'] for row in targets)
        gs=[state['guitar_body_states'][0]]+[s['guitar_body_states']['guitar'] for s in rows];gp=np.array([pose(s)[0] for s in gs]);rot=Rotation.from_quat([pose(s)[1].as_quat() for s in gs]);body=gp+rot.apply(centre)
        hp=[state['human_body_states'][initial['human_body_names'].index('RH:pick')]]+[s['human_body_states']['RH:pick'] for s in rows];pick=np.array([pose(s)[0] for s in hp]);pick_g=rot.inv().apply(pick-gp)
        starts,ends=string_segments(initial);final=read(n/'final_state.json');fgp,fgr=pose(final['guitar_body_states'][0]);marker_error=0.
        for i in range(6):
            for key,local in [('G:string%d'%(i+1),starts[i]),('G:string%d_end'%(i+1),ends[i])]:
                actual=pose(final['guitar_body_states'][initial['guitar_body_names'].index(key)])[0];marker_error=max(marker_error,float(np.linalg.norm(actual-fgp-fgr.apply(local))))
        assert marker_error<3e-6
        detector=PickStrikeDetector(1,6,device='cpu',min_across_speed=max(cfg['min_across_speed_m_s'],cfg['min_displacement_m']*60),min_depth=cfg['min_depth_m'],rearm_separation=cfg['rearm_distance_m'],rearm_min_frames=cfg['rearm_min_frames'],parallel_epsilon=cfg['parallel_epsilon'],allowed_y=(zone['allowed_y_min_m'],zone['allowed_y_max_m']),preferred_y=(zone['preferred_y_min_m'],zone['preferred_y_max_m']))
        releases=[];frames=[];dt=1/60
        for step in range(4,steps+1,4):
            result=detector.step(torch.tensor(pick_g[step-4:step-3],dtype=torch.float64),torch.tensor(pick_g[step:step+1],dtype=torch.float64),torch.tensor(starts,dtype=torch.float64),torch.tensor(ends,dtype=torch.float64),dt=dt)
            events=[]
            for i in range(6):
                if result['release'][0,i]:
                    cross=result['crossing_pos_g'][0,i].numpy();direction=int(result['direction'][0,i]);fraction=float(result['subframe_t'][0,i]);lane=float(cross[1]);event={'physics_step':step,'time_s':(step-4+4*fraction)/240,'string':i+1,'direction':direction,'crossing_G_m':cross.tolist(),'depth_m':float(result['depth'][0,i]),'across_speed_m_s':float(result['across_speed'][0,i]),'subframe_t':fraction,'global_zone_allowed':bool(zone['allowed_y_min_m']<=lane<=zone['allowed_y_max_m']),'lane_allowed':bool(abs(lane+.325)<=zone['lane_allowed_half_width_m']),'lane_core':bool(abs(lane+.325)<=zone['lane_core_half_width_m'])}
                    events.append(event)
            events.sort(key=lambda x:x['subframe_t']);releases+=events
            frames.append({'physics_step':step,'pick_G_m':pick_g[step].tolist(),'release_strings':[e['string'] for e in events],'blocked_wait_rearm':result['blocked_wait_rearm'][0].tolist()})
        down=[e['string'] for e in releases if e['direction']==1 and e['time_s']>=3.2 and e['lane_allowed'] and e['global_zone_allowed']];up=[e['string'] for e in releases if e['direction']==-1 and e['time_s']>=3.95 and e['lane_allowed'] and e['global_zone_allowed']]
        idx=[i for i,name in enumerate(initial['joint_names']) if name.startswith(('R_Elbow_','R_Wrist_'))];trace=read(n/'trace.json');q=np.array([r['q_rad'] for r in trace]);qref=np.array(initial['q_ref_rad']);outside=[i for i in range(81) if i not in idx]
        hand_contacts=sum(any(any(v=='human/R_Wrist' or v.startswith('human/RH:') for v in (c['body0_name'],c['body1_name'])) for c in row['right_distal_guitar_contacts']) for row in rows)
        results[n.name]={'completed_5s':bool(report['completed'] and steps==1200),'physics_steps':steps,'failure':report['failure'],'left_contact_steps':sum(bool(s['left_arm_hand_guitar_contacts']) for s in rows),'right_wrist_hand_contact_steps':hand_contacts,
            'maximum_body_centre_change_mm_240Hz':float(np.linalg.norm(body-body[0],axis=1).max()*1000),'final_body_centre_change_mm':float(np.linalg.norm(body[-1]-body[0])*1000),'maximum_SO3_delta_deg_240Hz':float(np.rad2deg((rot[0].inv()*rot).magnitude()).max()),'final_SO3_delta_deg':float(np.rad2deg((rot[0].inv()*rot[-1]).magnitude())),
            'other75_targets_exact':all(row['other75_exact'] for row in targets),'actual_other75_max_scalar_change_deg_60Hz':float(np.rad2deg(abs(q[:,outside]-qref[outside]).max())),'actual_6_peak_to_peak_deg_60Hz':dict(zip([initial['joint_names'][i] for i in idx],np.rad2deg(np.ptp(q[:,idx],axis=0)).tolist())),
            'rigid_string_final_reconstruction_error_m':marker_error,'releases':releases,'detector_frames':frames,'allowed_lane_down_order':down,'allowed_lane_up_order':up,'six_string_down_pass':down==[6,5,4,3,2,1],'six_string_up_pass':up==[1,2,3,4,5,6],
            'scope':'measured pick/current guitar root at240Hz, original detector at60Hz; fixed marker geometry reconstructed from actual initial pose and checked against final raw markers; raw RELEASE plus direction/global-zone/lane, not full song-task/timing/learning success;75 fixed targets are not frozen actual states'}
        print(n.name,'5s',results[n.name]['completed_5s'],'left',results[n.name]['left_contact_steps'],'down',down,'up',up,'hand_contact',hand_contacts,flush=True)
    assert all(sha(f)==h for f,h in inputs.items());save(args.out,{'passed':True,'input_sha256':inputs,'cases':results})


if __name__=='__main__':main()
