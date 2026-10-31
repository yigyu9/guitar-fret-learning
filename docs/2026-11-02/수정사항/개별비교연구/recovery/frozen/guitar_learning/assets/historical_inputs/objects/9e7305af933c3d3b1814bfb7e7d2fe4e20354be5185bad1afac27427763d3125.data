"""Read-only audit of actual six hand parts in the moving guitar frame."""
import argparse
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read,save,sha,pose
from .left_neck_near_geometry_v1 import FACETS
from .left_neck_three_face_geometry_v1 import measurements,placement_pass


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];n=args.case.resolve()
    staged={str(n/'report.json'):sha(n/'report.json')}
    cfgpath=Path(read(n/'report.json')['config']);staged[str(cfgpath)]=sha(cfgpath)
    candidatepath=Path(read(cfgpath)['initial_candidate']);staged[str(candidatepath)]=sha(candidatepath)
    paths=list((root/'stability_adapter_2').glob('*.py'))+[FACETS]+[f for f in n.rglob('*') if f.is_file()]+list(map(Path,staged))
    assert all(sha(p)==h for p,h in staged.items())
    inputs={str(p.resolve()):sha(p) for p in paths};save(args.out.with_name(args.out.stem+'_before.json'),inputs)
    initial=read(n/'initial_values.json');state=initial['native_initial_state'];report=read(n/'report.json')
    cfg=read(report['config']);candidate=read(cfg['initial_candidate'])['left_neck_near'];facets=read(FACETS)['facets']
    endpoints=read(n/'media/physics_endpoint_contacts.json')['rows'];first=read(n/'initial_three_faces.json')
    assert first['pass'] and first['frozen57_initial_exact'] and first['guitar_rotation39_exact']
    samples=[{'physics_step':0,'left_three_faces':first['measurements'],'left_three_faces_pass':first['pass']}]
    max_reconstruction=0.
    for row in endpoints:
        poses={name:pose(row['human_body_states'][name]) for name in first['measurements']}
        gp,gr=pose(row['guitar_body_states']['guitar']);actual=measurements(poses,gp,gr,candidate['station_G_m'],candidate['front_z_G_m'],facets)
        for name,m in actual.items():
            for field in ('point_G_m','surface_G_m','target_G_m','facet_normal_G','outward_normal_G'):
                max_reconstruction=max(max_reconstruction,float(np.max(abs(np.array(m[field])-row['left_three_faces'][name][field]))))
        assert placement_pass(actual)==row['left_three_faces_pass']
        samples.append({'physics_step':row['physics_step'],'left_three_faces':actual,'left_three_faces_pass':placement_pass(actual)})
    assert max_reconstruction<1e-10 and len(endpoints)==report['physics_steps']
    stats={}
    for name in first['measurements']:
        series=[s['left_three_faces'][name] for s in samples]
        stats[name]={field:{'initial':float(series[0][field]),'minimum':float(min(m[field] for m in series)),'maximum':float(max(m[field] for m in series)),'final':float(series[-1][field])} for field in ('facet_signed_plane_gap_m','point_target_error_m','alignment_dot')}
        stats[name]['contact_steps']=sum(any(('human/'+name) in (c['body0_name'],c['body1_name']) for c in s['left_arm_hand_guitar_contacts']) for s in endpoints)
    checkpoints={str(t):samples[min(int(t*240),len(samples)-1)] for t in (0,2,5)}
    after=[s for s in samples if s['physics_step']>=480]
    assert all(sha(p)==h for p,h in inputs.items())
    support={field:sum(bool(row[field]) for row in endpoints) for field in ('right_upper_arm_body_contacts','right_thorax_body_contacts','right_hip_body_contacts','right_forearm_body_contacts','trunk_guitar_contacts')}
    result={'support_contact_steps':support,'passed':True,'input_sha256':inputs,'native_case':str(n),'completed_5s':report['completed'] and report['physics_steps']==1200,'initial_three_faces_pass':True,'maximum_readonly_reconstruction_error':max_reconstruction,'all6_pass_fraction':sum(s['left_three_faces_pass'] for s in samples)/len(samples),'after2s_all6_pass_fraction':sum(s['left_three_faces_pass'] for s in after)/len(after) if after else None,'part_statistics':stats,'checkpoints':checkpoints,'samples':samples,'scope':'selected collision facet points and normals in actual moving guitar frame, not anatomical pad identity, minimum clearance, pressure/contact certification, or learned fret success'}
    save(args.out,result);print('actual initial six-face placement passed; after2s fraction',result['after2s_all6_pass_fraction'],flush=True)


if __name__=='__main__':main()
