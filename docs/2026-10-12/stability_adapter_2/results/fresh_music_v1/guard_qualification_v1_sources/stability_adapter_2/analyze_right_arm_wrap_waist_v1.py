"""Classify thigh seating from stored native contacts, without repeating the command audit."""
import argparse
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read, save, sha, pose


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cases',type=Path,nargs='+',required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    inputs={str(Path(__file__).resolve()):sha(__file__),
            str(Path(__file__).with_name('initial_pose_noise_v1.py')):sha(Path(__file__).with_name('initial_pose_noise_v1.py'))}
    def load(path):
        path=Path(path).resolve();inputs[str(path)]=sha(path);return read(path)
    results={}
    for case in args.cases:
        report=load(case/'report.json');config=load(report['config']);candidate=load(config['initial_candidate'])
        low,high=candidate['right_thigh_waist']['waist_G_y_interval_m']
        rows=load(case/'media/physics_endpoint_contacts.json')['rows'];assert len(rows)==report['physics_steps']
        points=[];flags=[]
        for row in rows:
            gp,gr=pose(row['guitar_body_states']['guitar']);bp,br=pose(row['guitar_body_states']['G:body']);contacts=[]
            for contact in row['right_hip_body_contacts']:
                assert 'guitar/G:body' in (contact['body0_name'],contact['body1_name'])
                key='localPos0' if contact['body0_name']=='guitar/G:body' else 'localPos1'
                local=np.array([contact[key][k] for k in 'xyz']);G=gr.inv().apply(bp+br.apply(local)-gp)
                record={'physics_step':row['physics_step'],'point_G_m':G.tolist(),
                        'inside_waist':bool(G[0]>0 and low<=G[1]<=high),'positive_raw_lambda':bool(contact['lambda']>0)}
                contacts.append(record);points.append(record)
            flags.append({'waist_presence':any(c['inside_waist'] for c in contacts),
                          'waist_positive':any(c['inside_waist'] and c['positive_raw_lambda'] for c in contacts)})
        results[case.name]={'waist_G_y_interval_m':[low,high],'physics_steps':len(rows),
            'waist_presence_steps':sum(f['waist_presence'] for f in flags),
            'waist_positive_steps':sum(f['waist_positive'] for f in flags),
            'waist_last120_presence_steps':sum(f['waist_presence'] for f in flags[1080:]) if report['completed'] else None,
            'waist_last120_positive_steps':sum(f['waist_positive'] for f in flags[1080:]) if report['completed'] else None,
            'contact_points_G_m':points}
    assert all(sha(p)==h for p,h in inputs.items())
    save(args.out,{'input_sha256':inputs,'cases':results,'scope':'actual endpoint local contacts transformed to actor-root guitar frame; positive lambda is not force N; partial late windows are null'})


if __name__=='__main__':main()
