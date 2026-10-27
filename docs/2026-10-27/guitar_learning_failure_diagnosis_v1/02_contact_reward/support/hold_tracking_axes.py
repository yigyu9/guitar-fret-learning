"""Compare source request, actual controller target and measured q in final hold."""
import json
from pathlib import Path
import numpy as np

BASE=Path(__file__).resolve().parents[1]


def main():
    goals=json.loads((BASE/'geometry24/candidates.json').read_text())['goals']
    results={}
    for folder in sorted(BASE.glob('static_*')):
        if not (folder/'report.json').exists():continue
        report=json.loads((folder/'report.json').read_text())
        if not report.get('completed'):continue
        setting=json.loads((folder/'settings.json').read_text())
        meta=json.loads((folder/'metadata.json').read_text());names=meta['joint_names']
        poses=np.load(folder/'poses60.npz');time=poses['tick']/60
        end=setting['initial_hold_s']+setting['other_finger_precondition_s']+setting['ramp_s']+setting['hold_s']
        mask=(time>end-.5)&(time<=end+1e-9)
        rows=[]
        for slot,row in enumerate(setting['trace_rows']):
            goal=goals[row];finger=('index','middle','ring','pinky')[goal['finger']-1]
            channels=[i for i,n in enumerate(names) if n.startswith('L_') or n.startswith('LH:'+finger)]
            valid=mask&poses['valid'][:,slot]
            stats=[]
            if valid.any():
                requested=np.asarray(goal['q_target105'])[channels]
                target=poses['target'][valid,slot][:,channels]
                actual=poses['q'][valid,slot][:,channels]
                for k,j in enumerate(channels):
                    stats.append(dict(joint=names[j],source_request_deg=float(np.rad2deg(requested[k])),
                        controller_target_mean_deg=float(np.rad2deg(target[:,k].mean())),
                        actual_q_mean_deg=float(np.rad2deg(actual[:,k].mean())),
                        source_to_controller_abs_p95_deg=float(np.rad2deg(np.percentile(abs(target[:,k]-requested[k]),95))),
                        controller_to_actual_abs_p95_deg=float(np.rad2deg(np.percentile(abs(target[:,k]-actual[:,k]),95)))))
                stats.sort(key=lambda r:-r['controller_to_actual_abs_p95_deg'])
            rows.append(dict(row=row,finger=finger,goal=goal['target_id'],valid_hold_endpoints=int(valid.sum()),
                requested_scope='same original source q arm12+assigned finger4; B condition changes only the other12 finger joints',
                final_hold_window_s=[end-.5,end],axes=stats))
        results[folder.name]=rows
    (BASE/'hold_tracking_axes.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    for key,rows in results.items():
        print(key,[(r['row'],r['axes'][:2]) for r in rows[:4]])


if __name__=='__main__':main()
