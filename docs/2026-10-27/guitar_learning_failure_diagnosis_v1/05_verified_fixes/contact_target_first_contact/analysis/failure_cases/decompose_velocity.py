"""Same-clock fixed-pad velocity decomposition at selected control starts only."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
CLOCKS={26:(676,680,684,688),8:(724,728,732,736)}


def rotate(q,v):return v+2*np.cross(q[:3],np.cross(q[:3],v)+q[3]*v)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    folder=BASE/'run_01';out=HERE/'results_v1'
    with np.load(folder/'physics240.npz') as z:a={k:z[k] for k in ('clock','actual_LH21','qd_selected4','selected_distal_pose','guitar_pose','nearest_sample_index')}
    with np.load(folder/'target_control60.npz') as z:t={k:z[k] for k in z.files}
    with np.load(BASE/'fixed_inputs.npz') as z:local=z['point_local'];fixed=z['source_sample_index']
    metadata=json.loads((folder/'load_probe_report.json').read_text())['metadata']
    selected=[metadata['hand_joint_names'].index(n) for n in metadata['selected_joint_names']]
    com=np.asarray(metadata['selected_body_COM_local_m']);plane=np.asarray(metadata['press_plane_G'])[:3]
    records=[]
    for env,clocks in CLOCKS.items():
        for clock in clocks:
            row=clock-1;ctrl=clock//4
            assert int(a['clock'][row,env])==int(t['start_clock'][ctrl,env])==clock
            valid=bool(t['gate'][ctrl,env])
            r=dict(env_id=env,clock=clock,time_s=clock/240.,gate=valid,available=valid,
                fixed_sample=int(fixed[env]),nearest_sample=int(a['nearest_sample_index'][row,env]),
                point_reconstruction_error_m=None,velocity_reconstruction_error_m_s=None,selected_normal_m_s=None,
                remainder_measured_normal_m_s=None,remainder_predicted_normal_m_s=None,measured_normal_m_s=None,
                predicted_normal_m_s=None,closure_normal_m_s=None,closure_norm_m_s=None)
            if valid:
                body=a['selected_distal_pose'][row,env].astype(float);guitar=a['guitar_pose'][row,env].astype(float)
                point=body[:3]+rotate(body[3:7],local[env]);offset=rotate(body[3:7],local[env]-com)
                measured=body[7:10]+np.cross(body[10:13],offset)
                normal=rotate(guitar[3:7],plane/np.linalg.norm(plane))
                np.testing.assert_array_equal(t['actual4'][ctrl,env],a['actual_LH21'][row,env,selected])
                point_error=float(np.max(np.abs(point-t['fixed_point_W'][ctrl,env])))
                velocity_error=float(np.max(np.abs(measured-t['point_velocity_W'][ctrl,env])))
                assert point_error<4e-6 and velocity_error<4e-6
                np.testing.assert_allclose(normal,t['normal_W'][ctrl,env],atol=1e-6,rtol=0)
                selected_velocity=t['point_J'][ctrl,env].astype(float)@a['qd_selected4'][row,env].astype(float)
                measured=t['point_velocity_W'][ctrl,env].astype(float);predicted=t['predicted_velocity_W'][ctrl,env].astype(float)
                r.update(point_reconstruction_error_m=point_error,velocity_reconstruction_error_m_s=velocity_error,
                    selected_normal_m_s=float(normal@selected_velocity),remainder_measured_normal_m_s=float(normal@(measured-selected_velocity)),
                    remainder_predicted_normal_m_s=float(normal@(predicted-selected_velocity)),measured_normal_m_s=float(normal@measured),
                    predicted_normal_m_s=float(normal@predicted),closure_normal_m_s=float(normal@(predicted-measured)),
                    closure_norm_m_s=float(np.linalg.norm(predicted-measured)))
                np.testing.assert_allclose(r['selected_normal_m_s']+r['remainder_measured_normal_m_s'],r['measured_normal_m_s'],atol=1e-15,rtol=0)
            records.append(r)
    paths=[Path(__file__),folder/'physics240.npz',folder/'target_control60.npz',folder/'load_probe_report.json',BASE/'fixed_inputs.npz']
    inputs={str(p.resolve()):sha(p) for p in paths}
    with (out/'fixed_point_velocity_components.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    with (out/'velocity_verification.json').open('x') as f:
        json.dump(dict(completed=True,CPU_only=True,GPU_executed=False,rows=records,input_sha256=inputs,
            limits='No interpolation or105qd reconstruction. Exact peak681/730 fixed point Jacobians unavailable; nearest points differ. Gate-off clock732 stored zeros are unavailable. Measured remainder includes closure residual; predicted remainder also shown. Not force or contact-pair attribution.'),f,indent=2,allow_nan=False);f.write('\n')
    assert all(sha(Path(p))==h for p,h in inputs.items())
    print(json.dumps(records,indent=2))


if __name__=='__main__':main()
