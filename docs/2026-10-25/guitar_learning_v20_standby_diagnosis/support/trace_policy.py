"""Observe v20 A500 first-song standby decisions at actual 240 Hz endpoints.

No training, extra physics steps, control edits, or historical output writes.
Run in a fresh GPU process; the existing frozen evaluator retains every guard.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PHASE = Path(__file__).resolve().parents[1]
ROOT = PHASE.parents[2]
EVALUATOR = ROOT/'docs/2026-10-25/guitar_learning_v20_A500/support/evaluate.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PhysicsTrace:
    """Bounded copies for the predeclared first eight first episodes only."""
    def __init__(self, env, max_steps=7876, count=8):
        import torch
        self.env, self.count, self.step = env, count, 0
        self.episodes = {}
        self.active = torch.ones(count, dtype=torch.bool, device=env.device)
        shapes = {
            'clock': ((), torch.int64), 'time_s': ((), torch.float64),
            'approach_weight': ((), torch.float64), 'control_failed': ((), torch.bool),
            **{k: ((4,), torch.float64) for k in
                ('gate', 'quality', 'idle_weight', 'per_finger_rate', 'shape_per_finger_rate')},
            'angles': ((4, 3), torch.float32), 'valid': ((4, 3), torch.bool),
            **{k: ((4,), torch.bool) for k in
                ('near_veto', 'contact_veto', 'nonfinite_veto', 'band_inside', 'pressing')},
            **{k: ((21,), torch.float32) for k in ('q', 'target', 'action')},
            'outward': ((21,), torch.bool),
            'tracking_indices': ((4, 2), torch.int64), 'tracking_valid': ((4, 2), torch.bool),
            'distance': ((env.M,), torch.float32),
            **{k: ((env.M,), torch.bool) for k in
                ('candidate', 'wrong', 'previous_candidate', 'previous_wrong')},
            'segment_position': ((4, 3, 3), torch.float32),
            'segment_quaternion': ((4, 3, 4), torch.float32),
            'segment_contact_force': ((4, 3, 3), torch.float32),
            'palm_contact_force': ((3,), torch.float32),
        }
        self.arrays = {k: torch.zeros((max_steps, count)+shape, dtype=dtype, device=env.device)
                       for k, (shape, dtype) in shapes.items()}

    def record(self, posture, pressing, now):
        import torch
        from guitar_learning.gpu.finger_reward import finger_target_indices
        if self.step >= len(self.arrays['clock']):
            raise ValueError('Physics trace exceeds predeclared one-song budget')
        env, n = self.env, self.count
        values = {k: posture[k][:n] for k in ('gate', 'quality', 'idle_weight', 'angles',
            'valid', 'near_veto', 'contact_veto', 'nonfinite_veto', 'per_finger_rate',
            'shape_per_finger_rate', 'band_inside')}
        values.update(clock=env.clock[:n], time_s=now[:n], pressing=pressing[:n],
            q=env.snapshot['q'][:n, env.finger_joint_indices],
            target=env.snapshot['target'][:n, env.finger_joint_indices],
            action=env.action[:n, env.finger_action_indices], outward=env.finger_outward[:n],
            distance=env.surface_distance[:n],
            segment_position=env.body[:n, env.finger_segment_indices, :3],
            segment_quaternion=env.body[:n, env.finger_segment_indices, 3:7],
            segment_contact_force=env.snapshot['contact_force'][:n, env.finger_segment_indices],
            palm_contact_force=env.snapshot['contact_force'][:n, env.finger_palm_index])
        for name in ('candidate', 'wrong', 'previous_candidate', 'previous_wrong'):
            values[name] = getattr(env, name)[:n]
        # The selector is pure. Evaluate only the eight observed rows; never
        # replace a reward helper or any tensor consumed by the live policy.
        tracking = finger_target_indices(now[:n], env.onset, env.end, env.press, env.finger)
        values.update(tracking_indices=tracking['indices'], tracking_valid=tracking['valid'])
        for key, value in values.items():
            target = self.arrays[key][self.step]
            active = self.active.reshape((n,)+(1,)*(target.ndim-1))
            target.copy_(torch.where(active, value.detach(), target))
        self.step += 1

    def end_control(self, episodes):
        if self.step % 4:
            raise ValueError('Control boundary requires four recorded physics endpoints')
        env = self.env
        failed = env.tick_failure[:self.count].any(-1)
        for key, values in (('control_failed', failed),
                            ('approach_weight', env._weights()['approach'])):
            self.arrays[key][self.step-4:self.step] = values*self.active
        for episode in episodes:
            index = episode['env_id']
            if index < self.count and index not in self.episodes:
                if episode['steps']*4 != self.step:
                    raise ValueError('First episode/physics boundary differs')
                self.episodes[index] = episode
                self.active[index] = False

    def save(self, output):
        import numpy as np
        if set(self.episodes) != set(range(self.count)):
            raise ValueError('Every predeclared traced first episode must end')
        output.mkdir(exist_ok=False)
        host = {k: v[:self.step].cpu().numpy() for k, v in self.arrays.items()}
        captures = []
        for index, episode in sorted(self.episodes.items()):
            length = episode['steps']*4
            arrays = {k: v[:length, index] for k, v in host.items()}
            if not np.array_equal(arrays['clock'], np.arange(1, length+1)):
                raise ValueError('Trace must contain every first-episode physics clock')
            if not np.allclose(arrays['time_s'], arrays['clock']/240., atol=1e-12, rtol=0):
                raise ValueError('Recorded actual reward time differs from physics clock')
            if not all(np.isfinite(v).all() for k, v in arrays.items() if k != 'distance'):
                raise ValueError('Unexpected nonfinite trace field')
            # Distance nonfiniteness is an explicitly recorded gate veto, so
            # retain it rather than hiding or rejecting the observation.
            d = episode['left_episode_diagnostics']['standby']
            raw = arrays['per_finger_rate'].sum(0)/240.
            weighted = (arrays['per_finger_rate']*arrays['approach_weight'][:, None]*
                        (~arrays['control_failed'])[:, None]).sum(0)/240.
            if not np.allclose(raw, d['raw_standby_reward'], atol=1e-8, rtol=0):
                raise ValueError('Trace raw B integral differs from native diagnostics')
            if not np.allclose(weighted, d['weighted_standby_reward'], atol=1e-8, rtol=0):
                raise ValueError('Trace weighted B integral differs from native diagnostics')
            native = episode['reward_components']['song_finger_standby']
            if abs(weighted.sum()-native) > 1e-5:
                raise ValueError('Trace weighted B differs from actual episode reward ledger')
            path = output/('physics_env%04d.npz'%index)
            np.savez_compressed(path, **arrays)
            captures.append(dict(env_id=index, frames=length, path=path.name, sha256=sha(path),
                raw_B_by_finger=raw.tolist(), weighted_B_by_finger=weighted.tolist(),
                native_weighted_B=native, weighted_B_error=float(weighted.sum()-native)))
        return captures


def attach_trace(env, trace):
    """Attach after pool initialization; reset helper calls are never traced."""
    original = env.episode_diagnostics.physics

    def observed_physics(posture, pressing, wrist_delta, now=None):
        # Copy before the original summary sees the same unmodified object.
        trace.record(posture, pressing, now)
        return original(posture, pressing, wrist_delta, now=now)

    env.episode_diagnostics.physics = observed_physics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=PHASE/'gpu_trace')
    args = parser.parse_args()
    output = args.out.resolve()
    if output.exists():
        raise ValueError('Use a new trace/evaluation output directory')
    sys.path.insert(0, str(ROOT))
    import isaacgym  # Must precede NumPy/Torch and GPU package imports.
    from guitar_learning.training import gpu_pool
    spec = importlib.util.spec_from_file_location('v20_A500_frozen_evaluator', EVALUATOR)
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    original_pool, original_write = gpu_pool.GpuPool, evaluator.write
    own_pins = {str(Path(__file__).resolve()): sha(__file__)}
    traces = []

    def pinned_write(path, value):
        if Path(path) == output/'inputs_before.json':
            # Mutate the fresh evaluator's own pins dictionary, so every
            # existing pre-/post-close unchanged-input check includes us.
            value.update(own_pins)
        return original_write(path, value)

    class ObservedPool(original_pool):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            trace = PhysicsTrace(self.environment)
            traces.append(trace)
            attach_trace(self.environment, trace)

        def step(self, actions):
            result = super().step(actions)
            traces[0].end_control(result[-1])
            return result

    old_argv = sys.argv
    gpu_pool.GpuPool, evaluator.write = ObservedPool, pinned_write
    try:
        sys.argv = [str(EVALUATOR), '--out', str(output), '--repeat', '1']
        evaluator.main()
        if len(traces) != 1:
            raise ValueError('Expected exactly one native evaluation pool')
        captures = traces[0].save(output/'physics')
        pins = json.loads((output/'inputs_before.json').read_text())
        if not all(sha(path) == expected for path, expected in pins.items()):
            raise ValueError('Evaluation/trace inputs changed')
        original_write(output/'trace_report.json', dict(completed=True,
            physics_hz=240, capture_envs=list(range(8)), captures=captures,
            fields=list(traces[0].arrays), input_pins_verified=len(pins), inputs_unchanged=True,
            finger_joint_names=[traces[0].env.names[i] for i in traces[0].env.finger_joint_indices.tolist()],
            segment_body_names=[[traces[0].env.body_names[i] for i in row]
                for row in traces[0].env.finger_segment_indices.tolist()],
            palm_body_name=traces[0].env.body_names[traces[0].env.finger_palm_index],
            net_force_source='Native human snapshot.contact_force on actual twelve finger bodies and palm only; no guitar-marker force distribution. Net resultants do not identify body pairs or certify string pressure.',
            helper_hook='Original diagnostic physics method called exactly once per physical endpoint; only immutable copies recorded. No reset helper interception.',
            clock_audit='Each first episode has steps*4 endpoints, clocks1..steps*4; raw/weighted B agrees with native diagnostics and reward ledger.',
            limitations='New deterministic GPU evaluation can differ from previous video trajectories. Gate exclusion flags overlap. Geometry/load candidates do not certify pressure or sound.'))
    finally:
        gpu_pool.GpuPool, evaluator.write, sys.argv = original_pool, original_write, old_argv


if __name__ == '__main__':
    main()
