"""Final native selective-reset and held-effort ownership check."""
import hashlib
import json
from pathlib import Path
import sys
import isaacgym
import torch
from guitar_learning.training.start import settings_document
from guitar_learning.training.gpu_pool import GpuPool

out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=False)
settings = settings_document('left', num_envs=2, device='cuda:0', physics='gpu')
root = Path(__file__).resolve().parents[4]
sources = [p for p in (root/'guitar_learning').rglob('*.py') if 'archive' not in p.parts]
sources.append(Path(__file__).resolve())
pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
(out/'sources_before.json').write_text(json.dumps(pins, indent=2)+'\n')
pool = None
try:
    pool = GpuPool(settings, out)
    action = torch.zeros(2, 39, device='cuda:0')
    for _ in range(2):
        with torch.no_grad():
            pool.step(action)
    scene = pool.scene
    q, qd, roots = scene.q.clone(), scene.qd.clone(), scene._roots.clone()
    held = pool.last_valid_efforts.clone()
    clocks = pool.environment.clock.clone()
    native_step, reset_calls = scene.physics_steps, scene.reset_calls
    pool.reset([0])
    sample = scene.snapshot()
    checks = dict(other_dof_unchanged=torch.equal(q[1], scene.q[1]),
        other_velocity_unchanged=torch.equal(qd[1], scene.qd[1]),
        other_roots_unchanged=torch.equal(roots[1], scene._roots[1]),
        selected_dof_restored=torch.equal(scene.q[0], scene._prepared_dofs[:, 0]),
        selected_velocity_restored=torch.equal(scene.qd[0], scene._prepared_dofs[:, 1]),
        selected_guitar_restored=torch.equal(scene._roots[0, 1], scene._prepared_bodies[len(scene.human_bodies)]),
        selected_effort_cache_zero=bool((pool.last_valid_efforts[0] == 0).all()),
        other_effort_cache_unchanged=torch.equal(held[1], pool.last_valid_efforts[1]),
        selected_contact_cache_zero=bool((sample['contact_force'][0] == 0).all()),
        selective_clock_reset=pool.environment.clock.tolist() == [0, int(clocks[1])],
        no_hidden_step=scene.physics_steps == native_step,
        exactly_one_reset=scene.reset_calls == reset_calls+1)
    with torch.no_grad():
        pool.step(action)
    checks['next_actual_four_steps'] = pool.environment.clock.tolist() == [4, int(clocks[1])+4]
    pool.close()
    checks['closed'] = pool.scene.diagnostics['closed']
    checks['inputs_unchanged'] = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha for p, sha in pins.items())
    result = dict(passed=all(checks.values()), checks=checks, scene=pool.scene.diagnostics)
    (out/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    if not result['passed']:
        raise RuntimeError('selective reset verification failed')
finally:
    if pool is not None:
        pool.close()
