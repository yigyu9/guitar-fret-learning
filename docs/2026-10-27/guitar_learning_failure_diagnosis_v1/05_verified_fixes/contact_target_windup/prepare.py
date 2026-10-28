"""CPU-only fixed tape/material point export and original strict input check."""
import json
from pathlib import Path

import numpy as np
import torch

from run_probe import HERE, OBSERVER, MODES, SCHEMA, observer, sha, write


def main():
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.gpu.fingertip_pad import load_fingertip_pad
    from guitar_learning.gpu.environment import CONTACT_CONTRACT
    from guitar_learning.gpu.geometry import apply
    assert not torch.cuda.is_initialized()
    source = OBSERVER/'run_final300_policy'
    report = json.loads((source/'load_probe_report.json').read_text())
    assert report['completed'] and all(report['checks'].values())
    checkpoint = Path(report['condition']['checkpoint'])
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    runner._validate_pins(payload['metadata'])
    assert payload['updates'] == 300 and 'ablation' not in payload['metadata']['settings']['song']['short_learning']
    with np.load(source/'control60.npz', allow_pickle=False) as c:
        action = c['executed_action_selected4'].copy()
        assert action.shape == (218, 128, 4) and c['first_attempt'].all()
        assert (c['clock'] == 4*np.arange(1, 219)[:, None]).all()
        np.testing.assert_array_equal(action, c['policy_action_selected4'])
    with np.load(source/'physics240.npz', allow_pickle=False) as a:
        assert a['first_attempt'].all() and not a['failure_latched'].any()
        assert (a['clock'][479] == 480).all()
        indices = a['nearest_sample_index'][479].astype(np.int64)
        patch = load_fingertip_pad()
        local_index = indices-patch['points_local'].shape[1]
        assert ((local_index >= 0) & (local_index < patch['points_local'].shape[1])).all()
        local = patch['points_local'][1, local_index].astype(np.float32)
        body = torch.as_tensor(a['selected_distal_pose'][479])
        point = body[:, :3]+apply(body[:, 3:7], torch.as_tensor(local))
        reconstruction_error = float(np.abs(point.numpy()-a['nearest_point_W'][479]).max())
        geometry_tolerance = float(8*np.finfo(np.float32).eps*max(1., float(np.abs(body[:, :3].numpy()).max())))
        assert reconstruction_error <= geometry_tolerance
    with (HERE/'fixed_inputs.npz').open('xb') as stream:
        np.savez_compressed(stream, action4=action, point_local=local, source_sample_index=indices)
    observer()
    from protocol import Trace
    trace = Trace(SCHEMA, 218)
    assert trace.nbytes+report['selected_output_uncompressed_bytes'] < 100_000_000-1_000_000
    contract = dict(schema='diagnostic.fixed_tape_contact_target.v1', conditions=list(MODES),
        physics_hz=240, control_hz=60, environments=128, first_attempt_quota=[1]*128,
        controls_max=218, prefix_controls_unmodified=120, fixed_material_source_clock=480,
        gate='first attempt, clock>=480, no prior native physical/wrist failure, not reset snapshot, finite data, selected signed press-normal resultant>original loaded threshold',
        force_threshold_N=CONTACT_CONTRACT['force_threshold_n'],
        A='box Euclidean projection with g·delta>=0',
        B='same projection with g·delta>=min(max(0,-g·(old-q)),max_box g·delta)',
        numerical='float64/maxabs-g normalization; finite clip breakpoint root; finalfloat32 epsilon/4axisdot/targetscale tolerance only; residual retained; no nextafter or recovery',
        scope='finite selected4 tape diagnostic, not policy performance; arm wrist feedback remains coupled; tangent change measured, not preserved',
        additional_fields=SCHEMA, additional_max_array_bytes=trace.nbytes,
        fixed_point_reconstruction_max_error_m=reconstruction_error,
        fixed_point_numerical_tolerance_m=geometry_tolerance)
    paths = {Path(p) for p in json.loads((source/'inputs_before.json').read_text())}
    paths.update(source/f for f in ('physics240.npz', 'control60.npz', 'evaluation.json', 'load_probe_report.json', 'inputs_before.json', 'inputs_after.json'))
    paths.update(HERE/f for f in ('run_probe.py', 'projection.py', 'prepare.py', 'self_test.py', 'PLAN.md', 'README.md', 'fixed_inputs.npz'))
    paths.add(OBSERVER/'precommit.json')
    pins = {str(p.resolve()): sha(p) for p in sorted(paths)}
    write(HERE/'precommit.json', dict(contract=contract, input_pins=pins,
        checkpoint=str(checkpoint), source_physics=str(source/'physics240.npz'), source_evaluation=str(source/'evaluation.json'),
        force_threshold_N=CONTACT_CONTRACT['force_threshold_n'],
        status='CPU preparation; no GPU execution; root internal GPU handoff required'))
    print(json.dumps(dict(completed=True, CPU_only=True, input_pins=len(pins),
        additional_max_array_bytes=trace.nbytes, combined_max_array_bytes=trace.nbytes+report['selected_output_uncompressed_bytes'],
        source_point_error_m=reconstruction_error), indent=2))


if __name__ == '__main__': main()
