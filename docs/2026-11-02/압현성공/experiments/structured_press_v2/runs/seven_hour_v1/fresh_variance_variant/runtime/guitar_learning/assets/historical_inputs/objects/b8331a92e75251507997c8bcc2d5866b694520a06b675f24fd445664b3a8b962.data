"""Audit current native81 FK against saved poses; no native simulation."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation as R
from .underneck_initial_search import calibrated_fk, pose


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,value):p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def statistics(values):
    v=np.asarray(values);return {'maximum':float(v.max()),'rms':float(np.sqrt(np.mean(v*v)))}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--native',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];native=args.native.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    xml_path=root/'stability_adapter_2/assets/humanoid_fixed_lower.xml'
    paths=[Path(__file__).resolve(),root/'stability_adapter_2/underneck_initial_search.py',root/'stability_adapter_2/STRIKE_FK_COORDINATE_AUDIT_PLAN.md',xml_path,native/'initial_values.json',native/'trace.json']
    hashes={str(p):sha(p) for p in paths};save(out/'inputs_before.json',{'sha256':hashes})
    initial=read(native/'initial_values.json');trace=read(native/'trace.json');base=initial['native_initial_state'];names=initial['joint_names'];bodies=initial['human_body_names']
    assert len(names)==81 and len(bodies)==66 and len(trace)==151
    assert [r['physics_step'] for r in trace]==list(range(0,1201,8))
    xml=ET.parse(xml_path).getroot();parents={c.get('name'):b.get('name') for b in xml.iter('body') for c in b.findall('body')};nodes={b.get('name'):b for b in xml.iter('body')}
    def bodypose(state,n):return pose(state['human_body_states'][bodies.index(n)])
    q0=np.array([r['pos'] for r in base['human_dof_states']]);fk,_=calibrated_fk(names,bodies,base,q0);cp0,cr0=bodypose(base,'Chest')
    group_summaries={};group_rows={}
    for n in ('R_Thorax','R_Shoulder','R_Elbow','R_Wrist','L_Thorax','L_Shoulder','L_Elbow','L_Wrist'):
        joints=nodes[n].findall('joint');idx=[names.index(j.get('name')) for j in joints];B=np.column_stack([np.fromstring(j.get('axis'),sep=' ') for j in joints]);assert len(idx)==3
        rel0=bodypose(base,parents[n])[1].inv()*bodypose(base,n)[1];rows=[]
        for t in trace:
            state=t['native_state'];q=np.array([r['pos'] for r in state['human_dof_states']]);actual=bodypose(state,parents[n])[1].inv()*bodypose(state,n)[1];row={'physics_step':t['physics_step']}
            for key,basis in (('XML_B',B),('Cartesian_I',np.eye(3))):
                predicted=R.from_rotvec(basis@q[idx])*R.from_rotvec(basis@q0[idx]).inv()*rel0;row[key+'_error_deg']=float(np.degrees((predicted.inv()*actual).magnitude()))
            rows.append(row)
        group_rows[n]=rows;group_summaries[n]={'joint_indices':idx,'joint_names':[names[j] for j in idx],'XML_basis_columns':B.tolist(),**{k:statistics([r[k+'_error_deg'] for r in rows]) for k in ('XML_B','Cartesian_I')}}
    pick_rows=[]
    for t in trace:
        state=t['native_state'];q=np.array([r['pos'] for r in state['human_dof_states']]);fp,fr=fk(q)['RH:pick'];cp,cr=bodypose(state,'Chest');delta=cr*cr0.inv();ap,ar=bodypose(state,'RH:pick');predicted=cp+delta.apply(fp-cp0)
        pick_rows.append({'physics_step':t['physics_step'],'actual_W_m':ap.tolist(),'predicted_W_m':predicted.tolist(),'position_error_mm':float(np.linalg.norm(predicted-ap)*1000),'rotation_error_deg':float(np.degrees(((delta*fr).inv()*ar).magnitude()))})
    assert np.isfinite([r[k] for rows in group_rows.values() for r in rows for k in ('XML_B_error_deg','Cartesian_I_error_deg')]).all()
    assert np.isfinite([r[k] for r in pick_rows for k in ('position_error_mm','rotation_error_deg')]).all()
    save(out/'group_rows.json',group_rows);save(out/'pick_rows.json',pick_rows)
    save(out/'summary.json',{'samples':len(trace),'physics_steps_covered':1200,'groups':group_summaries,'pick_position_mm':statistics([r['position_error_mm'] for r in pick_rows]),'pick_rotation_deg':statistics([r['rotation_error_deg'] for r in pick_rows]),'scope':'saved native81 trajectory comparison, no new physics or control change; not an unobserved-direction derivative certificate','music_success':False})
    changed=[p for p,h in hashes.items() if sha(Path(p))!=h];save(out/'inputs_after.json',{'unchanged':not changed,'changed':changed});assert not changed
    print('native81 FK audit completed:',len(trace),'samples')


if __name__=='__main__':main()
