"""Measure whether bounded actions can request the proven static support target."""
import hashlib
import json
from pathlib import Path
import numpy as np

P = Path(__file__).resolve().parent
RUN = P/'smoke_on_v1/evaluations/initial_000000'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


paths = [Path(__file__).resolve(), RUN/'learning_abi.json',
         RUN/'native/episode_0001/controls.json', RUN/'native/episode_0001/initial_values.json']
before = {str(p): sha(p) for p in paths}
abi = json.loads(paths[1].read_text())['payload']
rows = json.loads(paths[2].read_text())
initial = json.loads(paths[3].read_text())
preload = np.array(initial['preload']['bounded_targets_rad'])
groups = np.array(abi['groups']); caps = np.array([abi['residual_caps_rad'][g] for g in groups])
nominal = np.array([r['nominal81_rad'] for r in rows])
delta = nominal-preload
play = np.array([r['control_tick']>=120 for r in rows])
summaries = {}
for g in ('body','head','arm','finger'):
    selected = groups==g
    unreachable = np.abs(delta[:,selected])>caps[selected]+1e-10
    summaries[g] = {'max_nominal_from_static_support_rad': float(np.abs(delta[:,selected]).max()),
        'play_ticks_any_channel_static_support_outside_residual_reach_fraction': float(np.mean(unreachable[play].any(1))),
        'worst_joint': (abi['names'][int(np.flatnonzero(selected)[np.argmax(np.max(np.abs(delta[:,selected]),axis=0))])] if np.abs(delta[:,selected]).max()>0 else None),
        'residual_cap_rad': abi['residual_caps_rad'][g]}
result = {'input_sha256': before, 'checks_inputs_unchanged': all(sha(p)==h for p,h in before.items()),
    'groups': summaries,
    'scope': 'target reachability diagnostic only; static preload is a proven 5s reference, not a necessary/sufficient contact or musical condition',
    'physics_seconds': len(rows)/60}
with (P/'nominal_support_analysis_v2.json').open('x') as f: json.dump(result,f,indent=2,ensure_ascii=False)
print(json.dumps(summaries,indent=2))
