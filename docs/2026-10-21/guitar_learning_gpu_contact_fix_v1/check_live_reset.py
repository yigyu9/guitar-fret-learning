"""Native validation of compound-root reset and logical marker/force mapping."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
p = argparse.ArgumentParser()
p.add_argument('--out', type=Path, required=True)
args = p.parse_args()
args.out.mkdir(parents=True, exist_ok=False)
import isaacgym
import torch
from guitar_learning.gpu.scene import GpuScene

torch.set_num_threads(1)
scene = GpuScene(4, 'left', out=args.out/'scene')
result = dict(completed=False)
try:
    assert scene.gym.get_sim_rigid_body_count(scene.sim) == 4 * 68
    assert scene.body_state.shape == (4, 106, 13)
    assert torch.equal(scene.com[66], torch.tensor(scene.contract['initial']['guitar_properties']['applied'][0]['COM_body_m'], device=scene.device))
    for _ in range(4):
        scene.step(scene.target.clone(), torch.zeros_like(scene.target))
    before = {k: scene.snapshot()[k].clone() for k in ('q', 'qd', 'target', 'body_state', 'contact_force', 'physics_step')}
    before_roots = scene._roots.clone()
    ids = torch.tensor([1, 3], device=scene.device)
    keep = torch.tensor([0, 2], device=scene.device)
    calls, time = scene.reset_calls, scene.physics_steps
    after = scene.reset(ids)
    assert scene.reset_calls == calls + 1 and scene.physics_steps == time
    for key, value in before.items():
        assert torch.equal(after[key][keep], value[keep]), key
    assert torch.equal(scene._roots[keep], before_roots[keep])
    assert torch.equal(scene._roots[ids, 1], scene.rigid_guitar.prepared_root.expand(2, -1))
    assert torch.equal(after['body_state'][ids], scene._prepared_bodies.expand(2, -1, -1))
    assert not bool(after['contact_force'][ids].any())
    assert not bool(after['contact_force'][:, 67:105].any())
    scene.reset(ids)
    assert scene.reset_calls == calls + 1
    try:
        scene.reset(keep)
    except RuntimeError:
        pass
    else:
        raise AssertionError('Split same-step boundary reset was accepted')
    after = scene.step(scene.target.clone(), torch.zeros_like(scene.target))
    assert torch.isfinite(after['body_state']).all() and not after['reset_body_snapshot'].any()
    physical = scene._bodies[:, 66]
    expanded = scene.rigid_guitar.expand(scene._bodies)
    # Only native aggregate force is attributed to the logical guitar root.
    assert torch.equal(scene.contact_force[:, 66], scene._native_contact_force[:, 66])
    assert torch.equal(scene.contact_force[:, :66], scene._native_contact_force[:, :66])
    assert torch.equal(scene.contact_force[:, -1], scene._native_contact_force[:, -1])
    assert torch.equal(expanded[:, 66, :7], physical[:, :7])
    result.update(completed=True, native_bodies=272, logical_body_shape=list(expanded.shape),
                  selective_reset_unchanged_rows=True, duplicate_reset_noop=True,
                  same_step_split_reset_rejected=True, physical_root_COM_velocity_restored=True,
                  original_logical_COM_retained=True, aggregate_force_only_on_logical_root=True)
finally:
    scene.close()
    result['scene'] = scene.diagnostics
    (args.out/'report.json').write_text(json.dumps(result, indent=2) + '\n')
