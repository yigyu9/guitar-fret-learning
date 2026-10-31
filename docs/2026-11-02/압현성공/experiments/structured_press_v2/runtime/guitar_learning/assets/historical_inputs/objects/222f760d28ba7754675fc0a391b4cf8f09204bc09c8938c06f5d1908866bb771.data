"""Retain the successful initial state and perturb one elbow target after settling."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read,save,sha
from .diagnose_user_guided_no_left_v1 import A,P


def main():
    out=P/'wave_v14';out.mkdir(exist_ok=False);cfg=P/'search_v13/upper50/config.json';candidate=P/'search_v13/upper50/candidate.json'
    inputs={str(p):sha(p) for p in [Path(__file__).resolve(),A/'USER_GUIDED_NO_LEFT_WAVE_V14_PLAN.md',cfg,candidate,P/'analysis_first_v1.json']+list(A.glob('*.py'))};save(out/'inputs_before.json',inputs)
    c=read(cfg);assert read(P/'analysis_first_v1.json')['cases']['native_upper50_v13_static']['left_free_5s']
    save(out/'config.json',{**c,'elbow_motion_amplitude_rad':float(np.deg2rad(5))})
    assert all(sha(p)==h for p,h in inputs.items());save(out/'package.json',{'input_sha256':inputs,'initial_candidate_unchanged':True,'changed_only':'elbow_motion_amplitude_rad=5deg','scope':'R_Elbow_y scalar target perturbation, 2.5~4.5s/0.5Hz, same initial/G/gains; no new source pose solver'})

if __name__=='__main__':main()
