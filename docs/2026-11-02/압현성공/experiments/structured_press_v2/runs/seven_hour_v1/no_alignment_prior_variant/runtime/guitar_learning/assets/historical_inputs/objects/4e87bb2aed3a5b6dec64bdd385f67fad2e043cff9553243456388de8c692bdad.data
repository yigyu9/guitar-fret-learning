"""Generate bounded constant-target probes around the saved alpha .45 trial."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1'
PREVIOUS=PHASE.parent/'palm_contact_boundary_v1'
TRIALS=ROOT/'stability_adapter_2/trials/palm_coupled_response_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    if PHASE.exists() or TRIALS.exists():raise FileExistsError('preserve existing trials')
    path=PREVIOUS/'analysis.json';hashes={str(path):sha(path)};analysis=read(path)
    paths=[Path(p) for p in analysis['input_sha256']]+[Path(__file__).resolve(),
        ROOT/'stability_adapter_2/PALM_COUPLED_RESPONSE_PLAN.md',ROOT/'stability_adapter_2/run_palm_finite_response.py',
        PREVIOUS/'alpha_45/report.json',PREVIOUS/'alpha_45/states.json',PREVIOUS/'environment.json']
    hashes.update({str(p):sha(p) for p in paths})
    if not all(analysis['checks'].values()) or any(sha(p)!=h for p,h in analysis['input_sha256'].items()):raise AssertionError('source analysis seal')
    report=read(PREVIOUS/'alpha_45/report.json');seed=read(PREVIOUS/'alpha_45/states.json')[0]
    bias=report['bias_rad'];q0=[seed['human_dof_states'][i]['pos'] for i in report['arm_indices']]
    low=report['lower_rad'];high=report['upper_rad'];signs=[]
    for i in range(12):
        sign=1 if q0[i]+bias[i]+.005<=high[i] else -1
        if not low[i]<=q0[i]+bias[i]+sign*.005<=high[i]:raise AssertionError('no feasible probe')
        signs.append(sign)
    candidates=[('baseline',[0.]*12)]
    for i in range(12):
        delta=[0.]*12;delta[i]=signs[i]*.005;candidates.append(('axis_'+str(i).zfill(2),delta))
    candidates.append(('heldout',[sign*.001 for sign in signs]))
    PHASE.mkdir();TRIALS.mkdir();records=[]
    for label,delta in candidates:
        target=[a+b+c for a,b,c in zip(q0,bias,delta)]
        if not all(l<=v<=h for l,v,h in zip(low,target,high)):raise AssertionError('candidate bounds')
        candidate=TRIALS/(label+'.json')
        candidate.write_text(json.dumps({'label':label,'bias_rad':[b+d for b,d in zip(bias,delta)],
            'requested_bias_delta_rad':delta,'baseline_source':str(PREVIOUS/'alpha_45/report.json')},indent=2)+'\n')
        records.append({'label':label,'candidate_path':str(candidate),'sha256':sha(candidate)})
    if any(sha(p)!=h for p,h in hashes.items()):raise AssertionError('input changed')
    manifest={'input_sha256':hashes,'candidates':records,'native_initializations_planned':14,'physics_steps_planned':336}
    (TRIALS/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (PHASE/'candidate_generation.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (PHASE/'environment.json').write_text(json.dumps(read(PREVIOUS/'environment.json'),indent=2)+'\n')
    print(json.dumps({'candidates':len(records),'signs':signs}))


if __name__=='__main__':main()
