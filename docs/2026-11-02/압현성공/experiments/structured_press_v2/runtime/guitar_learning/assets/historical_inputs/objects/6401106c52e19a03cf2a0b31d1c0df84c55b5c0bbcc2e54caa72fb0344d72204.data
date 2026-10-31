"""Compare two closed native trajectories without changing either run."""
from pathlib import Path
import json,hashlib
import numpy as np
P=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1')
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    paths=[Path(__file__).resolve()]+[P/f'native_v{v}'/name for v in (1,2) for name in ('trace.json','initial_values.json')]+[P/f'analysis_v{v}.json' for v in (1,2)]
    pins={str(p):sha(p) for p in paths};out=P/'repeat_comparison_v1.json';assert not out.exists()
    before=P/'repeat_comparison_before_v1.json';assert not before.exists();before.write_text(json.dumps(pins,indent=2)+'\n')
    a,b=[read(P/f'native_v{v}/trace.json') for v in (1,2)];assert len(a)==len(b)==961
    pa,pb=[np.array([r['position_W_m'] for r in t]) for t in (a,b)];qa,qb=[np.array([r['quaternion_xyzw'] for r in t]) for t in (a,b)]
    analysis=read(P/'analysis_v2.json')['measured'];stages={r['stage']:r for r in analysis['stages']}
    delta=(np.array(stages['hold_B']['mean_actual_wrist_G_m'])-np.array(stages['hold_A']['mean_actual_wrist_G_m']))*1000
    row={'input_sha256':pins,'same_initial_state':read(P/'native_v1/initial_values.json')==read(P/'native_v2/initial_values.json'),
         'guitar_trace_exact':bool(np.array_equal(pa,pb) and np.array_equal(qa,qb)),'maximum_actor_root_trace_difference_m':float(np.linalg.norm(pa-pb,axis=1).max()),
         'maximum_quaternion_component_difference':float(abs(qa-qb).max()),'mean_wrist_B_minus_A_G_mm':delta.tolist(),'neck_axis_actual_station_difference_mm':float(delta[1]),
         'scope':'two identical-condition deterministic diagnostics; not randomized robustness/force closure or learned music'}
    assert all(sha(p)==h for p,h in pins.items());out.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');print(row)
if __name__=='__main__':main()
