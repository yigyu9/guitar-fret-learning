"""Derive normal-task calibration from saved native FK and PD response probes."""
import argparse
import json
from pathlib import Path
from scipy.optimize import lsq_linear
from .palm_side_feedback import PHASE as PREVIOUS,context,input_paths,np
from .palm_normal_task import prepare,error_from_state
from .build_fixed_lower_asset import read,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    out=parser.parse_args().out;out.mkdir(parents=True,exist_ok=False)
    ctx=prepare(context());paths=input_paths()+[Path(__file__).resolve(),Path(__file__).with_name('palm_normal_task.py')]
    paths += [PREVIOUS/k/n for k in ('fk','response') for n in ('calibration.json','columns.json')]
    paths += [Path(p) for p in read(PREVIOUS/'preflight_v2/validation.json')['input_sha256']]
    hashes={str(p):sha(p) for p in paths};result={'checks':{},'input_sha256':hashes,'native_initializations':0,'physics_steps':0}
    for kind in ('fk','response'):
        data=read(PREVIOUS/kind/'columns.json');rows=data['rows'];calibration=read(PREVIOUS/kind/'calibration.json')
        if len(rows)!=14 or not all(calibration['checks'].values()) or not all(all(r['checks'].values()) for r in rows):
            raise AssertionError('saved probe coverage/contracts')
        baseline=error_from_state(rows[0]['after_state'],ctx);columns=[]
        for j,row in enumerate(rows[1:13]):
            delta=np.array(row['actual_delta_rad'])
            if np.count_nonzero(delta)!=1 or abs(delta[j])<1e-6:raise AssertionError('single-axis probe')
            columns.append((baseline-error_from_state(row['after_state'],ctx))/delta[j])
        matrix=np.array(columns).T
        result[kind]={'matrix':matrix.tolist(),'baseline_error_m_scaled_rad':baseline.tolist(),
            'singular_values':np.linalg.svd(matrix,compute_uv=False).tolist()}
        if kind=='fk':
            held=rows[-1];residual=(baseline-error_from_state(held['after_state'],ctx))-matrix@held['actual_delta_rad']
            result[kind]['heldout_error_m_scaled_rad']=residual.tolist()
            result['checks']['heldout_position_below_2um']=bool(np.linalg.norm(residual[:3])<2e-6)
            result['checks']['heldout_normal_rotation_below_20urad']=bool(np.linalg.norm(residual[3:])/.08<2e-5)
        else:
            q0=ctx['q0'][ctx['indices']]
            fit=lsq_linear(np.vstack((matrix,1e-5*np.eye(12))),np.r_[baseline,np.zeros(12)],
                bounds=(ctx['lower']-q0,ctx['upper']-q0),tol=1e-12,max_iter=500)
            if not fit.success:raise AssertionError(fit.message)
            result[kind].update(bias_rad=fit.x.tolist(),predicted_error_m_scaled_rad=(baseline-matrix@fit.x).tolist())
            result['checks']['bias_in_bounds']=bool(((q0+fit.x>=ctx['lower'])&(q0+fit.x<=ctx['upper'])).all())
        result['checks'][kind+'_matrix_finite']=bool(np.isfinite(matrix).all())
    result['checks']['inputs_unchanged']=all(sha(Path(p))==h for p,h in hashes.items())
    result['scope']='source normals transformed by saved native poses; normal-axis twist unpenalized; not a stationary actuation/contact certification'
    (out/'calibration.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if not all(result['checks'].values()):raise AssertionError(result['checks'])
    print(json.dumps({'checks':result['checks'],'response':result['response']},indent=2))


if __name__=='__main__':main()
