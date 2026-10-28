"""Supplemental CPU arm12 bounds audit of the same frozen env0 audible endpoints."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
REPRO=BASE.parent/'finger_only_oracle_acquisition_v1/reproduction_v1'
OUT=HERE/'results_v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    inputs={};rows=[];cases={}
    def read(p):
        inputs[str(p)]=sha(p);return json.loads(p.read_text())
    sys.path.insert(0,str(BASE.parents[4]))
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.core.finger_control import default_profile
    source=load_prepared_reset_contract();profile=default_profile()
    for finger in ('index','middle'):
        native=read(BASE/'runs'/finger/'native_effort_readback.json')
        for field,values in source['initial']['native_PD_properties'].items():
            expected=np.asarray(values).copy()
            if field in ('stiffness','damping'):
                for i,name in enumerate(source['initial']['joint_names']):
                    if name.startswith('LH:'):
                        expected[i]=profile[('thumb' if name.startswith('LH:thumb') else 'finger')+'_'+field]
            dtype=bool if field=='hasLimits' else np.int32 if field=='driveMode' else np.float32
            np.testing.assert_array_equal(np.asarray(native['original_profile_native_PD105'][field],dtype=dtype),expected.astype(dtype))
    for finger in ('index','middle'):
        for condition,folder in [('baseline20',REPRO/'runs'/finger),('cap025',BASE/'runs'/finger)]:
            c=read(folder/'training_contract.json')['action']['target_contract'];meta=read(folder/'trace_metadata.json')
            config=read(folder/'settings.json');path=folder/meta['file'];inputs[str(path)]=sha(path);t=dict(np.load(path))
            names=[g+'_'+a for g in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist') for a in 'xyz']
            qids=[meta['joint_names'].index(n) for n in names];aids=[c['action_order'].index(n) for n in names]
            low=np.asarray(c['action_lower_rad'])[aids];high=np.asarray(c['action_upper_rad'])[aids]
            source=config['song']['short_learning']['view']['source_target'];mask=(t['source_time_s']>=source['onset_s'])&(t['source_time_s']<source['end_s'])
            actual=t['q'][mask][:,qids];target=t['target'][mask][:,qids];requested=t['wrist_requested_arm_rad'][mask]
            assert requested.shape==actual.shape==target.shape and c['joint_names']==meta['joint_names']
            error=np.rad2deg(target-actual);requested_gap=np.rad2deg(requested-actual)
            for kind,values in [('requested',requested),('native_target',target),('actual',actual)]:
                lower=values-low;upper=high-values
                for k,n in enumerate(names):
                    rows.append(dict(finger=finger,condition=condition,kind=kind,joint=n,samples=int(mask.sum()),
                        action_lower_deg=float(np.rad2deg(low[k])),action_upper_deg=float(np.rad2deg(high[k])),
                        mean_deg=float(np.rad2deg(values[:,k]).mean()),min_deg=float(np.rad2deg(values[:,k]).min()),max_deg=float(np.rad2deg(values[:,k]).max()),
                        lower_within_or_beyond_1urad_count=int((lower[:,k]<=1e-6).sum()),upper_within_or_beyond_1urad_count=int((upper[:,k]<=1e-6).sum()),
                        lower_outside_over_1urad_count=int((lower[:,k]<-1e-6).sum()),upper_outside_over_1urad_count=int((upper[:,k]<-1e-6).sum()),
                        min_action_bound_clearance_deg=float(np.rad2deg(np.minimum(lower[:,k],upper[:,k])).min()),
                        target_minus_actual_mean_deg=float(error[:,k].mean()),target_minus_actual_max_abs_deg=float(abs(error[:,k]).max()),
                        requested_minus_actual_mean_deg=float(requested_gap[:,k].mean())))
            cases[finger+'_'+condition]=dict(arm_order=names,samples=int(mask.sum()),
                target_minus_actual_mean_deg=error.mean(0).tolist(),target_minus_actual_max_abs_deg=abs(error).max(0).tolist(),
                requested_minus_actual_mean_deg=requested_gap.mean(0).tolist(),
                requested_minus_native_target_mean_deg=np.rad2deg(requested-target).mean(0).tolist(),
                bounds_rows=[r for r in rows if r['finger']==finger and r['condition']==condition and (r['lower_within_or_beyond_1urad_count'] or r['upper_within_or_beyond_1urad_count'])])
    inputs[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
    document=dict(cases=cases,input_sha256=inputs,scope='env0 same audible60Hz post-control q/target and that-tick prephysics teacher request; actual beyond actionbox is not a native-limit failure',
        boundary_listing_epsilon_rad=1e-6,epsilon_scope='diagnostic boundary listing only; no control/predicate change or clamp causality certification',
        interpretation='actual can lie outside actionbox; target smoothing alpha=.2 and request rate/bounds precede native physical tracking; no instantaneous realization assumption')
    path=OUT/'arm_bounds.json'
    with path.open('x') as f:json.dump(document,f,indent=2);f.write('\n')
    with (OUT/'arm_bounds.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    p=OUT/'verification.json';verification=json.loads(p.read_text());verification['input_sha256'].update(inputs)
    verification['arm_action_bounds_supplement']='arm_bounds.json'
    verification['original_native105_profile_independently_matches_verified_prepared_loader']=True
    p.write_text(json.dumps(verification,indent=2)+'\n')
    for key,c in cases.items():
        print(key,'edge_rows',[(r['kind'],r['joint'],r['lower_within_or_beyond_1urad_count'],r['upper_within_or_beyond_1urad_count']) for r in c['bounds_rows']])
        print('maxerror',max(c['target_minus_actual_max_abs_deg']),'meanerror',c['target_minus_actual_mean_deg'])


if __name__=='__main__':main()
