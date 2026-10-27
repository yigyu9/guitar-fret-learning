"""Compare only actually simulated matching times, without extrapolating the abort."""
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha
from .upper_arm_static_geometry_v1 import ROOT


def main():
    d=ROOT/'docs/2026-10-19/stability_adapter_2/results';p=d/'left_hand_off_current_v1'
    current=p/'native_back100_static/trace.json';baseline=d/'right_arm_wrap_forward_v1/native_elbow10_static/trace.json';timeline=p/'timelines_v1.json'
    inputs={str(f):sha(f) for f in (Path(__file__).resolve(),current,baseline,timeline)}
    save(p/'same_time_before_v1.json',inputs)
    c=read(current);b=read(baseline)[:len(c)];assert [r['physics_step'] for r in c]==[r['physics_step'] for r in b]
    centre=np.array(read(timeline)['body_centre_G_m'])
    def series(rows):
        r=Rotation.from_quat([row['quaternion_xyzw'] for row in rows]);return np.array([row['position_W_m'] for row in rows])+r.apply(centre),r
    cp,cr=series(c);bp,br=series(b);delta=np.linalg.norm(cp-bp,axis=1)*1000;angles=np.rad2deg((br.inv()*cr).magnitude())
    result={'input_sha256':inputs,'matched_samples':len(c),'last_physics_seconds':c[-1]['physics_step']/240.,
        'maximum_same_time_BB_centre_difference_mm':float(delta.max()),'final_same_time_BB_centre_difference_mm':float(delta[-1]),
        'maximum_same_time_SO3_difference_deg':float(angles.max()),'final_same_time_SO3_difference_deg':float(angles[-1]),
        'scope':'matching 60Hz samples through actual .933333s abort only; no 5s comparison or causal decomposition of changed left mass posture versus support removal'}
    assert all(sha(f)==h for f,h in inputs.items());save(p/'same_time_v1.json',result)


if __name__=='__main__':main()
