"""Re-fit saved normal PD response within a larger runtime target box."""
import argparse
import json
from pathlib import Path
from scipy.optimize import lsq_linear
from .palm_side_feedback import PHASE as PREVIOUS,SOURCE_PHASE,context,np
from .palm_normal_task import prepare
from .build_fixed_lower_asset import read,sha

PHASE=PREVIOUS.parent/'palm_normal_control_v1'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cap',type=float,choices=(.3,.5),required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    source=PHASE/'calibration/calibration.json';result=read(source);ctx=prepare(context())
    for p,h in result['input_sha256'].items():
        if sha(Path(p))!=h:raise ValueError('saved calibration inputs changed')
    audit_path=SOURCE_PHASE/'initial_audit_v2/audit.json';audit=read(audit_path);arm=ctx['indices'];q0=ctx['q0'][arm]
    low=np.maximum(np.array(audit['native_lower_rad'])[arm],q0-args.cap)
    high=np.minimum(np.array(audit['native_upper_rad'])[arm],q0+args.cap)
    matrix=np.array(result['response']['matrix']);baseline=np.array(result['response']['baseline_error_m_scaled_rad'])
    fit=lsq_linear(np.vstack((matrix,1e-5*np.eye(12))),np.r_[baseline,np.zeros(12)],
        bounds=(low-q0,high-q0),tol=1e-12,max_iter=500)
    if not fit.success:raise AssertionError(fit.message)
    result['input_sha256'].update({str(p):sha(p) for p in (source,audit_path,Path(__file__).resolve())})
    result['response'].update(bias_rad=fit.x.tolist(),predicted_error_m_scaled_rad=(baseline-matrix@fit.x).tolist())
    result['runtime_cap_rad']=args.cap;result['lower_rad']=low.tolist();result['upper_rad']=high.tolist()
    result['checks']['bias_in_bounds']=bool(((q0+fit.x>=low)&(q0+fit.x<=high)).all())
    result['scope']='same source-normal response; runtime target box enlarged, initial configuration unchanged; +/-0.03 response extrapolation requires actual first-step validation'
    result['checks']['inputs_unchanged']=all(sha(Path(p))==h for p,h in result['input_sha256'].items())
    (args.out/'calibration.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if not all(result['checks'].values()):raise AssertionError(result['checks'])
    print(json.dumps({'cap':args.cap,'checks':result['checks'],'bias_rad':fit.x.tolist()}))


if __name__=='__main__':main()
