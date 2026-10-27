"""Refit the measured local target response in a larger native target box; no simulation."""
import json
from pathlib import Path
from .finger_grip_probe import PHASE
from .environment import ROOT, np
from .build_fixed_lower_asset import read, sha
from scipy.optimize import lsq_linear


def main():
    source=PHASE/'arm_start_calibration/fit.json';report_path=PHASE/'short/seed120_hold/report.json'
    fit,report=read(source),read(report_path)
    settings=Path(ROOT/'stability_adapter_2/trials/finger_grip_hold_v1/mixed/curl_120_pinky090.json')
    files=[Path(__file__).resolve(),source,report_path,settings]
    hashes={str(p):sha(p) for p in files}
    arm=np.array(report['arm_indices']);q0=np.array(report['initial_joint_targets_rad'])[arm]
    low=np.maximum(np.array(report['native_joint_lower_rad'])[arm],q0-.3)
    high=np.minimum(np.array(report['native_joint_upper_rad'])[arm],q0+.3)
    matrix=np.array(fit['matrix']);motion=np.array(fit['baseline_first_step_delta_rad'])
    result=lsq_linear(np.vstack((matrix,1e-5*np.eye(24))),np.r_[-motion,np.zeros(24)],bounds=(low-q0,high-q0),tol=1e-12,max_iter=500)
    if not result.success or not np.isfinite(result.x).all():raise AssertionError(result.message)
    path=ROOT/'stability_adapter_2/trials/finger_grip_hold_v1/arm_start_bias_seed120_wide.json'
    if path.exists():raise FileExistsError('preserve wide bias settings')
    path.write_text(json.dumps({'arm_target_bias_rad':dict(zip(report['arm_names'],result.x.tolist())),
        'target_delta_cap_rad':.3,'settings_path':str(settings),'settings_sha256':sha(settings),
        'scope':'native intersect initial +/-0.3 target preload; no larger initial pose'},indent=2)+'\n')
    out=source.with_name('fit_wide.json')
    if out.exists():raise FileExistsError('preserve refit result')
    if not all(sha(Path(p))==h for p,h in hashes.items()):raise AssertionError('refit input changed')
    out.write_text(json.dumps({'input_sha256':hashes,'bias_settings_path':str(path),'bias_settings_sha256':sha(path),
        'physics_steps':0,'native_initializations':0,'fit_success':bool(result.success),
        'predicted_norm_rad':float(np.linalg.norm(motion+matrix@result.x))},indent=2)+'\n')
    print(json.dumps({'predicted_norm_rad':np.linalg.norm(motion+matrix@result.x),'max_target_bias_rad':np.max(np.abs(result.x))}))


if __name__=='__main__':main()
