"""Actual per-worker reset selection and constant ABI probe; no policy update."""
import argparse
from pathlib import Path
from .initial_pose_noise_v1 import save,sha,read

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--bank',type=Path,required=True);a=p.parse_args()
    from .dual_music_scene_v1 import DualMusicScene
    from .parallel_initial_noise_v1 import ParallelInitialNoiseEnvironment
    import numpy as np
    a.out.mkdir(parents=True,exist_ok=False);env=ParallelInitialNoiseEnvironment(2,a.out/'workers',a.bank,103);rows=[];first=None
    try:
        for i in range(3):
            obs=env.reset();env.require_training_ready();abi=env.abi()
            if first is None:first=abi
            if abi!=first:raise AssertionError('sample selected index changed ABI')
            snapshots=env.snapshots()
            for s in snapshots:
                entry=s['initial_pose_noise']['entry'];cfg=read(entry['config_path']);expected=read(cfg['native_reference'])['native_initial_state']
                if s['native_state']!=expected or s['physics_steps']!=0 or s['forbidden_calls']:raise AssertionError('unexpected reset native state')
            rows.append({'reset':i+1,'snapshots':snapshots,'observation_finite':bool(np.isfinite(obs).all())})
        indices=[[s['initial_pose_noise']['index'] for s in row['snapshots']] for row in rows]
        if len(set(sum(indices,[])))<2:raise AssertionError('no selected-pose diversity in probe')
        save(a.out/'report.json',{'completed':True,'resets':3,'workers':2,'indices':indices,'ABI_constant':True,'all_initial_native_exact':True,'physics_steps':0,'rows':rows,'bank_sha256':sha(a.bank),'scope':'six actual fresh scene resets; no dynamics or policy update'})
    finally:env.close()
if __name__=='__main__':main()
