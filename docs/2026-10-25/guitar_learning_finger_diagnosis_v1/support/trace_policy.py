"""Observe existing v19 helpers at240Hz; never alter their returned tensors."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PHASE = Path(__file__).resolve().parents[1]
ROOT = PHASE.parents[2]
TRAINING = ROOT/'docs/2026-10-25/guitar_learning_long_training_v19_3000'
EVALUATOR = TRAINING/'support/evaluate_checkpoints.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PhysicsTrace:
    """Fixed bounded buffers of copies from the first eight first episodes."""
    def __init__(self, env, max_steps=7876, count=8):
        import torch
        self.env, self.count, self.step = env, count, 0
        self.last_tracking = None
        self.lengths = {}
        shapes = {
            'clock': ((), torch.int64),
            **{k: ((4,), torch.float64) for k in ('gate', 'quality', 'idle_weight')},
            'angles': ((4, 3), torch.float32), 'valid': ((4, 3), torch.bool),
            **{k: ((4,), torch.bool) for k in ('near_veto', 'contact_veto', 'nonfinite_veto', 'pressing')},
            **{k: ((21,), torch.float32) for k in ('q', 'target', 'action')},
            'outward': ((21,), torch.bool),
            'tracking_indices': ((4,), torch.int64), 'tracking_valid': ((4,), torch.bool),
            'tracking_quality': ((4,), torch.float32),
            'distance': ((env.M,), torch.float32),
            **{k: ((env.M,), torch.bool) for k in ('candidate', 'wrong')},
        }
        self.arrays = {k: torch.empty((max_steps, count)+shape, dtype=dtype, device=env.device)
                       for k, (shape, dtype) in shapes.items()}

    def record(self, posture, pressing):
        if self.step >= len(self.arrays['clock']):
            raise ValueError('Physics trace exceeds predeclared one-song budget')
        env, n = self.env, self.count
        values = {k: posture[k][:n] for k in ('gate', 'quality', 'idle_weight', 'angles',
            'valid', 'near_veto', 'contact_veto', 'nonfinite_veto')}
        values.update(clock=env.clock[:n], pressing=pressing[:n],
            q=env.snapshot['q'][:n, env.finger_joint_indices],
            target=env.snapshot['target'][:n, env.finger_joint_indices],
            action=env.action[:n, env.finger_action_indices], outward=env.finger_outward[:n],
            distance=env.surface_distance[:n], candidate=env.candidate[:n], wrong=env.wrong[:n])
        for k in ('indices', 'valid', 'quality'):
            values['tracking_'+k] = self.last_tracking[k][:n]
        for key, value in values.items():
            self.arrays[key][self.step].copy_(value)
        self.step += 1

    def end_control(self, episodes):
        for episode in episodes:
            i = episode['env_id']
            if i < self.count and i not in self.lengths:
                self.lengths[i] = episode['steps']*4
                if self.lengths[i] != self.step:
                    raise ValueError('First episode/physics trace boundary differs')

    def save(self, output):
        import numpy as np
        if set(self.lengths) != set(range(self.count)):
            raise ValueError('Every traced first episode must end')
        output.mkdir(exist_ok=False)
        # Transfer once per field, outside all policy/physics loops.
        host = {k: v[:self.step].cpu().numpy() for k, v in self.arrays.items()}
        captures = []
        for i in range(self.count):
            arrays = {k: v[:self.lengths[i], i] for k, v in host.items()}
            assert np.array_equal(arrays['clock'], np.arange(1, self.lengths[i]+1))
            assert all(np.isfinite(v).all() for v in arrays.values())
            path = output/('physics_env%04d.npz'%i)
            np.savez_compressed(path, **arrays)
            captures.append(dict(env_id=i, frames=self.lengths[i], path=path.name, sha256=sha(path)))
        return captures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', default='observed')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    import isaacgym  # Must precede NumPy/Torch and all GPU package imports.
    from guitar_learning.training import gpu_pool
    from guitar_learning.gpu import environment
    spec = importlib.util.spec_from_file_location('v19_fixed_evaluator', EVALUATOR)
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    pins = {str(p): sha(p) for p in (Path(__file__).resolve(), EVALUATOR,
        TRAINING/'training_source_manifest.json', TRAINING/'train3000/final.pt')}
    original_pool = gpu_pool.GpuPool
    original_tracking = environment.pad_tracking_reward
    trace_holder = []

    def observed_tracking(*a, **kw):
        result = original_tracking(*a, **kw)
        trace_holder[0].last_tracking = result
        return result

    class ObservedPool(original_pool):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            trace = PhysicsTrace(self.environment)
            trace_holder.append(trace)
            original_physics = self.environment.episode_diagnostics.physics

            def observed_physics(posture, pressing, wrist_delta):
                result = original_physics(posture, pressing, wrist_delta)
                trace.record(posture, pressing)
                return result

            self.environment.episode_diagnostics.physics = observed_physics

        def step(self, actions):
            result = super().step(actions)
            trace_holder[0].end_control(result[-1])
            return result

    gpu_pool.GpuPool = ObservedPool
    environment.pad_tracking_reward = observed_tracking
    try:
        sys.argv = [str(EVALUATOR), '--out', str(PHASE), '--tag', args.tag]
        evaluator.main()
        captures = trace_holder[0].save(PHASE/('physics_'+args.tag))
        assert all(sha(p)==h for p,h in pins.items())
        report = dict(completed=True, fields=list(trace_holder[0].arrays),
            physics_hz=240, capture_envs=list(range(8)), captures=captures,
            evaluation='evaluation_'+args.tag+'_final_1024', input_sha256=pins,
            inputs_unchanged=True, helper_return='original result object returned unchanged',
            policy='unchanged deterministic final3000; no PPO/curriculum update',
            scope='Read-only copies of actual posture/tracking helpers and state; episode summaries independently audit integrals. Gate flags overlap.')
        (PHASE/('trace_'+args.tag+'_report.json')).write_text(json.dumps(report,indent=2)+'\n')
    finally:
        gpu_pool.GpuPool = original_pool
        environment.pad_tracking_reward = original_tracking


if __name__ == '__main__':
    main()
