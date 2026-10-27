"""Confirm all guitar native body frames and applied inertia scaling are preserved."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    paths=[P/'native_baseline_v2/initial_values.json',P/'native_realistic_v2/initial_values.json',R/'tab2body/assets/guitar_asset.xml',R/'tab2body/assets/mesh/guitar_neck1.obj',R/'tab2body/assets/mesh/guitar_neck2.obj'];inputs={str(p):sha(p) for p in paths};inputs[str(Path(__file__))]=sha(__file__);a,b=[json.loads(p.read_text()) for p in paths[:2]]
    def pose(s):return np.array([s['pose']['p'][k] for k in 'xyz']),Rotation.from_quat([s['pose']['r'][k] for k in 'xyzw'])
    ap,ar=pose(a['native_initial_state']['guitar_body_states'][0]);bp,br=pose(b['native_initial_state']['guitar_body_states'][0]);errors={}
    for n,x,y in zip(a['guitar_body_names'],a['native_initial_state']['guitar_body_states'],b['native_initial_state']['guitar_body_states']):
        xp,xr=pose(x);yp,yr=pose(y);errors[n]={'relative_position_error_m':float(np.linalg.norm(ar.inv().apply(xp-ap)-br.inv().apply(yp-bp))),'relative_orientation_error_deg':float(np.rad2deg(((ar.inv()*xr).inv()*(br.inv()*yr)).magnitude()))}
    checks={'native_body_name_order_exact':a['guitar_body_names']==b['guitar_body_names'],'all_native_guitar_body_frames_preserved':max(e['relative_position_error_m'] for e in errors.values())<1e-6 and max(e['relative_orientation_error_deg'] for e in errors.values())<.01,'actual_inertia_equals_imported_times_mass_ratio':all(np.allclose(e['inertia_COM_kg_m2'],np.asarray(i['inertia_COM_kg_m2'])*(e['mass_kg']/i['mass_kg']),atol=1e-9,rtol=1e-5) and np.allclose(e['COM_body_m'],i['COM_body_m'],atol=1e-7,rtol=1e-6) for e,i in zip(b['mass_properties']['applied'],b['mass_properties']['imported'])),'inputs_unchanged':all(sha(p)==h for p,h in inputs.items())}
    root=ET.parse(paths[2]).getroot();body=next(x for x in root.iter('body') if x.get('name')=='G:body');tail=float(np.fromstring(body.get('pos'),sep=' ')[1]-np.fromstring(body.find('geom').get('size'),sep=' ')[1]);tips=[]
    for p in paths[3:]:tips.extend(float(l.split()[2]) for l in p.read_text().splitlines() if l.startswith('v '))
    result={'passed':all(checks.values()),'checks':checks,'input_sha256':inputs,'native_guitar_frame_errors':errors,'old_source_body_tail_G_y_m':tail,'old_source_head_tip_G_y_m':max(tips),'old_source_total_longitudinal_length_m':max(tips)-tail,'scope':'native rigid body frames and symbolic music geometry unchanged; checkpoint music accuracy remains untested; total old length is source box/neck outline bound, not hardware measurement'}
    with (P/'native_geometry_ABI_verification_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'passed':result['passed'],'checks':checks,'old_length_cm':result['old_source_total_longitudinal_length_m']*100},ensure_ascii=False,indent=2));assert result['passed'],checks
if __name__=='__main__':main()
