"""Compare guitar trajectories at identical saved 60Hz timestamps."""
import argparse
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--case',type=Path,required=True)
    parser.add_argument('--centre-source',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    files=[Path(__file__).resolve(),Path(__file__).with_name('initial_pose_noise_v1.py'),args.centre_source]
    files += [d/n for d in (args.baseline,args.case) for n in ('report.json','trace.json')]
    inputs={str(p.resolve()):sha(p) for p in files};centre=np.array(read(args.centre_source)['body_centre_G_m'])
    traces=[read(d/'trace.json') for d in (args.baseline,args.case)]
    assert all(read(d/'report.json')['completed'] for d in (args.baseline,args.case))
    assert len(traces[0])==len(traces[1])==301
    bodies=[];rotations=[]
    for trace in traces:
        rotation=Rotation.from_quat([r['quaternion_xyzw'] for r in trace]);gp=np.array([r['position_W_m'] for r in trace])
        bodies.append(gp+rotation.apply(np.tile(centre,(len(trace),1))));rotations.append(rotation)
    assert [r['physics_step'] for r in traces[0]]==[r['physics_step'] for r in traces[1]]==list(range(0,1201,4))
    delta=np.linalg.norm(bodies[1]-bodies[0],axis=1)*1000;angles=np.rad2deg((rotations[0].inv()*rotations[1]).magnitude())
    assert all(sha(p)==h for p,h in inputs.items())
    save(args.out,{'input_sha256':inputs,'body_centre_G_m':centre.tolist(),'sample_hz':60,
        'maximum_same_time_BB_centre_difference_mm':float(delta.max()),'final_same_time_BB_centre_difference_mm':float(delta[-1]),
        'maximum_same_time_SO3_difference_deg':float(angles.max()),'final_same_time_SO3_difference_deg':float(angles[-1]),
        'rows':[{'physics_step':t['physics_step'],'time_s':t['physics_step']/240,'BB_centre_difference_mm':float(x),'SO3_difference_deg':float(y)} for t,x,y in zip(traces[0],delta,angles)],
        'scope':'same-time comparison of completed static trials; 60Hz sampled maxima, not difference of separate peak values'})

if __name__=='__main__':main()
