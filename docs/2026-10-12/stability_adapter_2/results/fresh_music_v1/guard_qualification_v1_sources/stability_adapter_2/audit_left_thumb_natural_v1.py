"""Compare actual initial palm/fingers and fixed thumb targets to the accepted seat."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read, save, sha, pose
from .search_left_thumb_natural_v1 import A,E,P,FACETS


def main():
    n=P/'native_v1';old=E/'native_pick_feedback_v1'
    paths=[Path(__file__).resolve(),FACETS]+[f for folder in (n,old) for f in folder.rglob('*') if f.is_file()]
    paths+=list(A.glob('*.py'))
    inputs={str(p.resolve()):sha(p) for p in paths};save(P/'thumb_audit_before_v1.json',inputs)
    baseline=read(old/'initial_values.json');current=read(n/'initial_values.json')
    names=current['joint_names'];bodies=current['human_body_names'];assert names==baseline['joint_names'] and bodies==baseline['human_body_names']
    thumb=np.array([i for i,name in enumerate(names) if name.startswith('LH:thumb')]);fixed=np.ones(81,dtype=bool);fixed[thumb]=False
    q0=np.array(current['q_ref_rad']);oldq=np.array(baseline['q_ref_rad']);assert np.array_equal(q0[fixed],oldq[fixed])
    assert current['PD_properties']==baseline['PD_properties']
    state=current['native_initial_state'];oldstate=baseline['native_initial_state']
    assert state['guitar_body_states']==oldstate['guitar_body_states']
    pose_rows=[]
    for name,a,b in zip(bodies,state['human_body_states'],oldstate['human_body_states']):
        if name.startswith('LH:thumb'):continue
        p,r=pose(a);bp,br=pose(b)
        position=float(np.linalg.norm(p-bp));rotation=float((br.inv()*r).magnitude())
        assert position<1e-6 and rotation<1e-5
        pose_rows.append({'body':name,'raw_pose_exact':a['pose']==b['pose'],'position_difference_m':position,'rotation_difference_rad':rotation})
    targets=read(n/'media/six_joint_target_rows.json')['rows']
    assert len(targets)==300
    for row in targets:
        assert np.array_equal(np.array(row['requested_target81_rad'])[thumb],q0[thumb])
        assert np.array_equal(np.array(row['final_target81_rad'])[thumb],q0[thumb]) and row['other75_exact']
    trace=read(n/'trace.json');q=np.array([row['q_rad'] for row in trace])
    facet=read(FACETS)['facets']['LH:thumb3'];measurements=[]
    for label,s in [('initial',state),('final',read(n/'final_state.json'))]:
        gp,gr=pose(s['guitar_body_states'][0]);p,r=pose(s['human_body_states'][bodies.index('LH:thumb3')])
        point=gr.inv().apply(p+r.apply(facet['point_local_m'])-gp);normal=gr.inv().apply(r.apply(facet['normal_local']))
        measurements.append({'state':label,'facet_point_G_m':point.tolist(),'facet_normal_G':normal.tolist(),'back_plane_gap_m':float(-.008-point[2]),'scope':'selected collision facet and back-plane reference; not contact/nearest finite-surface distance/anatomical pad certification'})
    endpoints=read(n/'media/physics_endpoint_contacts.json')['rows'];contacts=[]
    for row in endpoints:
        contacts.extend([c for c in row['left_arm_hand_guitar_contacts'] if any(v.startswith('human/LH:thumb') for v in (c['body0_name'],c['body1_name']))])
    capture=read(n/'media/capture.json')
    assert len(capture['frames'])==151 and all(r['render_preserves_states'] for r in capture['frames'])
    assert all('thumb_back' in r['cameras'] for r in capture['frames'])
    assert all(sha(p)==h for p,h in inputs.items())
    save(P/'thumb_audit_v1.json',{'passed':True,'input_sha256':inputs,'other76_initial_angles_exact':True,
        'PD_properties_exact':True,'guitar_initial_raw_states_exact':True,'nonthumb_initial_pose_comparison':pose_rows,
        'nonthumb_initial_position_difference_max_m':max(r['position_difference_m'] for r in pose_rows),
        'nonthumb_initial_rotation_difference_max_rad':max(r['rotation_difference_rad'] for r in pose_rows),
        'initial_thumb_deg':dict(zip([names[i] for i in thumb],np.rad2deg(q0[thumb]).tolist())),
        'baseline_thumb_deg':dict(zip([names[i] for i in thumb],np.rad2deg(oldq[thumb]).tolist())),
        'actual_thumb_max_error_deg_60Hz':dict(zip([names[i] for i in thumb],np.rad2deg(abs(q[:,thumb]-q0[thumb]).max(axis=0)).tolist())),
        'thumb5_targets_fixed_all300_controls':True,'thumb_guitar_contact_records':len(contacts),'facet_measurements':measurements,
        'render_frames':151,'render_states_preserved':True,'views':['whole_body','hands','thumb_back'],
        'scope':'initial pose retained to stated native float tolerance; actual dynamics remain free; preset hand goals, not new fret checkpoint or forced contact'})
    print('thumb initial5 degrees',np.rad2deg(q0[thumb]).tolist(),'nonthumb max position/rotation',max(r['position_difference_m'] for r in pose_rows),max(r['rotation_difference_rad'] for r in pose_rows),'thumbcontacts',len(contacts))


if __name__=='__main__':main()
