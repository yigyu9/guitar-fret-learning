"""Reuse native command audits and classify actual thigh contacts in the guitar waist."""
import argparse
from pathlib import Path
import sys
from unittest.mock import patch
import numpy as np
from . import analyze_right_block_cradle_v7 as support
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cases',type=Path,nargs='+',required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    out=args.out.resolve();out.mkdir(exist_ok=False)
    inputs={str(p):sha(p) for case in args.cases for p in case.resolve().rglob('*') if p.is_file()}
    inputs.update({str(p):sha(p) for p in (ROOT/'stability_adapter_2').glob('*.py')})
    audit=out/'support_command_audit.json'
    with patch.object(sys,'argv',['support','--cases']+[str(p.resolve()) for p in args.cases]+['--out',str(audit)]):support.main()
    inputs[str(audit)]=sha(audit);result=read(audit);regions={}
    for case in args.cases:
        case=case.resolve();report=read(case/'report.json');config=read(report['config']);candidate=read(config['initial_candidate'])
        inputs[report['config']]=sha(report['config']);inputs[config['initial_candidate']]=sha(config['initial_candidate'])
        low,high=candidate['right_thigh_waist']['waist_G_y_interval_m'];rows=read(case/'media/physics_endpoint_contacts.json')['rows'];points=[];flags=[]
        for row in rows:
            gp,gr=pose(row['guitar_body_states']['guitar']);bp,br=pose(row['guitar_body_states']['G:body']);contacts=[]
            for contact in row['right_hip_body_contacts']:
                key='localPos0' if contact['body0_name']=='guitar/G:body' else 'localPos1'
                local=np.array([contact[key][k] for k in 'xyz']);G=gr.inv().apply(bp+br.apply(local)-gp)
                inside=bool(G[0]>0 and low<=G[1]<=high)
                record={'physics_step':row['physics_step'],'point_G_m':G.tolist(),'inside_waist':inside,'positive_raw_lambda':bool(contact['lambda']>0)};contacts.append(record);points.append(record)
            flags.append({'presence':bool(contacts),'waist_presence':any(c['inside_waist'] for c in contacts),'waist_positive':any(c['inside_waist'] and c['positive_raw_lambda'] for c in contacts)})
        regions[case.name]={'waist_G_y_interval_m':[low,high],'initial_translation_W_mm':(np.array(candidate['right_thigh_waist']['guitar_delta_W_m'])*1000).tolist(),
            'right_thigh_presence_steps':sum(f['presence'] for f in flags),'waist_presence_steps':sum(f['waist_presence'] for f in flags),'waist_positive_steps':sum(f['waist_positive'] for f in flags),
            'waist_last_half_second_presence_steps':sum(f['waist_presence'] for f in flags[-120:]),'waist_last_half_second_positive_steps':sum(f['waist_positive'] for f in flags[-120:]),
            'contact_points_G_m':points,'scope':'native local contact points converted with actual endpoint body/root poses; presence not contact-force N or substep certification'}
    assert all(sha(p)==h for p,h in inputs.items())
    save(out/'analysis.json',{'passed':True,'input_sha256':inputs,'support':result,'waist_regions':regions,'scope':'command audit plus actual waist-region contacts; evaluate seating separately from completed execution'})


if __name__=='__main__':main()
