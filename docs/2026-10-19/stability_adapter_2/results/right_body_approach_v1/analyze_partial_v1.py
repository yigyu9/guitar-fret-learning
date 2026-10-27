"""Describe safety-aborted native recordings without treating them as five-second successes."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parent
BASE=P.parent/'right_thigh_waist_v1/analysis_final_v1/analysis.json'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    inputs={str(BASE):sha(BASE),str(Path(__file__).resolve()):sha(__file__)}
    centre=np.array(read(BASE)['support']['body_centre_G_m']);cases={}
    for folder in sorted(P.glob('native_*')):
        report=read(folder/'report.json')
        if report['completed']:continue
        inputs.update({str(f):sha(f) for f in folder.rglob('*') if f.is_file()})
        inputs.update(read(folder/'attempt.json')['input_sha256'])
        cfg=Path(report['config']);candidate=Path(read(cfg)['initial_candidate'])
        inputs.update({str(f):sha(f) for f in (cfg,candidate)})
        trace=read(folder/'trace.json');contacts=read(folder/'media/physics_endpoint_contacts.json')['rows']
        assert report['inputs_unchanged'] and not report['forbidden_calls'] and len(contacts)==report['physics_steps']
        assert len(trace)==report['control_steps']+1
        verification=read(folder/'initial_verification.json')
        assert all(verification['invariants'].values()) and verification['FK_ok'] and verification['source_audit']['source_clear']
        pos=np.array([r['position_W_m'] for r in trace]);rot=Rotation.from_quat([r['quaternion_xyzw'] for r in trace])
        body=pos+rot.apply(np.repeat(centre[None],len(trace),axis=0))
        root_mm=np.linalg.norm(pos-pos[0],axis=1)*1000;angles=np.rad2deg((rot[0].inv()*rot).magnitude())
        cases[folder.name]={'completed':False,'physics_steps':report['physics_steps'],'control_steps':report['control_steps'],
          'physics_seconds':report['physics_seconds'],'failure':report['failure'],
          'root_max_displacement_mm':float(root_mm.max()),'max_body_centre_change_mm':float(np.linalg.norm(body-body[0],axis=1).max()*1000),
          'max_rotation_change_deg':float(angles.max()),'final_rotation_change_deg':float(angles[-1]),
          'root20cm_guard_crossed':bool(root_mm[-1]>.20*1000),'rotation35deg_guard_crossed':bool(angles[-1]>35),
          'contacts_all_body_not_proximal_classified':{key:{'presence_steps':sum(bool(r[key]) for r in contacts),
          'positive_raw_lambda_steps':sum(any(c['lambda']>0 for c in r[key]) for r in contacts)} for key in
          ('right_thorax_body_contacts','right_upper_arm_body_contacts','right_hip_body_contacts','left_arm_hand_guitar_contacts')},
          'videos':{view:{'path':v['path'],'sha256':v['sha256'],'stream':v['stream']} for view,v in report['videos'].items()}}
    assert all(sha(p)==h for p,h in inputs.items())
    with (P/'partial_analysis_v1.json').open('x') as f:json.dump({'input_sha256':inputs,'cases':cases,
      'body_bbox_centre_G_m':centre.tolist(),'scope':'60Hz trace extrema and actual safety-aborted endpoints; no completed-five-second/command-audit/proximal-region/force certification'},f,ensure_ascii=False,indent=2,allow_nan=False)

if __name__=='__main__':main()
