"""CPU strict input preparation; preserve all old seals and comparison raw."""
import json
from pathlib import Path

import numpy as np
import torch

from run_probe import HERE, PREVIOUS, OBSERVER, SCHEMA, observer, sha, write


def main():
    from guitar_learning.tool.experiments.short_finger_learning import runner
    assert not torch.cuda.is_initialized()
    old = json.loads((PREVIOUS/'precommit.json').read_text())
    assert all(Path(p).is_file() and sha(p) == h for p, h in old['input_pins'].items())
    payload = torch.load(old['checkpoint'], map_location='cpu')
    runner._validate_pins(payload['metadata'])
    assert payload['updates'] == 300 and 'ablation' not in payload['metadata']['settings']['song']['short_learning']
    with np.load(PREVIOUS/'fixed_inputs.npz', allow_pickle=False) as z:
        assert z['action4'].shape == (218,128,4) and z['point_local'].shape == (128,3)
        assert all(np.isfinite(z[k]).all() for k in z.files)
    observer()
    from protocol import Trace
    trace = Trace(SCHEMA,218)
    source = Path(old['source_physics']).parent
    original_report = json.loads((source/'load_probe_report.json').read_text())
    assert original_report['completed'] and all(original_report['checks'].values())
    assert trace.nbytes+original_report['selected_output_uncompressed_bytes'] < 100_000_000
    paths = {Path(p) for p in old['input_pins']}
    paths.add(PREVIOUS/'precommit.json')
    comparison = []
    for name in ('original','no_new_inward','no_new_inward_and_relax'):
        folder=PREVIOUS/('run_'+name)
        report=json.loads((folder/'target_windup_report.json').read_text())
        assert report['completed'] and all(report['checks'].values())
        launcher=PREVIOUS/(name+'_launcher.json'); assert json.loads(launcher.read_text())['returncode'] == 0
        paths.add(launcher)
        paths.update(folder/f for f in ('physics240.npz','control60.npz','target_control60.npz','first_attempt_notes.json','evaluation.json','settings.json',
            'report.json','load_probe_report.json','target_windup_report.json','inputs_before.json','inputs_after.json'))
        comparison.append(str(folder))
    with (HERE/'fixed_inputs.npz').open('xb') as f: f.write((PREVIOUS/'fixed_inputs.npz').read_bytes())
    assert sha(HERE/'fixed_inputs.npz') == sha(PREVIOUS/'fixed_inputs.npz')
    paths.update(HERE/f for f in ('run_probe.py','prepare.py','self_test.py','PLAN.md','README.md','fixed_inputs.npz'))
    contract=dict(schema='diagnostic.first_loaded_no_new_inward.v1',conditions=['first_loaded_no_new_inward'],
        only_control_change='remove clock>=480 from original signed-load gate; no relax',
        gate='current signed press-normal>original .01N, first attempt, no prior native/wrist failure, not reset, finite q/qd/pose/force/nativeJ',
        force_threshold_N=old['force_threshold_N'], environments=128,first_attempt_quota=[1]*128,
        control_hz=60,physics_hz=240,controls_max=218,physics_endpoints_max=872,
        fixed_material_source_clock=480,actual_prefix='each env through first changed-target start clock, all physics/control fields exact against source',
        projection=old['contract']['A'],numerical=old['contract']['numerical'],additional_fields=SCHEMA,
        additional_max_array_bytes=trace.nbytes,combined_source_array_bytes=trace.nbytes+original_report['selected_output_uncompressed_bytes'],
        comparison_runs=comparison,scope=old['contract']['scope'])
    write(HERE/'precommit.json',dict(contract=contract,input_pins={str(p.resolve()):sha(p) for p in sorted(paths)},
        checkpoint=old['checkpoint'],source_physics=old['source_physics'],source_control=str(source/'control60.npz'),
        source_evaluation=old['source_evaluation'],force_threshold_N=old['force_threshold_N'],
        status='CPU preparation only; root internal GPU handoff required'))
    print(json.dumps(dict(completed=True,CPU_only=True,input_pins=len(paths),fixed_inputs_exact=True,
        additional_max_array_bytes=trace.nbytes,combined_array_bytes=contract['combined_source_array_bytes'])))


if __name__=='__main__': main()
