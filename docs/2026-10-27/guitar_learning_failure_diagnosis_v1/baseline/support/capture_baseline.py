"""Observe strict checkpoint evaluation without changing controls or source files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

ROOT = Path('/home/ajou/yigyu/3')
OLD = ROOT/'docs/2026-10-27/guitar_learning_large_until0900_v1'
BASE = Path(__file__).resolve().parents[1]


def main():
    args = argparse.ArgumentParser()
    args.add_argument('label', choices=('initial', 'final'))
    options = args.parse_args()
    os.chdir(ROOT)
    manifest = json.loads((OLD/'source_manifest.json').read_text())
    changed = [p for p, sha in manifest.items()
               if hashlib.sha256(Path(p).read_bytes()).hexdigest() != sha]
    if changed:
        raise RuntimeError('Source changed: '+repr(changed))
    import isaacgym
    import numpy as np
    import torch
    import guitar_learning.training.gpu_pool as gpu_pool
    import guitar_learning.training.finger_skill_runner as runner
    checkpoint = OLD/'run_01/J'/(options.label+'.pt')
    out = BASE/('trace_'+options.label)
    latest, samples, done, instances = {}, {i: [] for i in range(4)}, set(), []
    original_act = runner._DeterministicPolicy.act
    original_pool = gpu_pool.GpuPool

    def observing_act(self, *inputs):
        result = original_act(self, *inputs)
        latest.clear()
        latest.update({key: result[key].detach().clone()
                       for key in ('mean', 'log_std', 'latent', 'action')})
        return result

    class ObservingPool(original_pool):
        def __init__(self, settings, path):
            super().__init__(settings, path)
            instances.append(self)
            self.before_first = None

        def step(self, actions):
            before = self.controller.target.detach().clone()
            before_sample = self.scene.snapshot()
            if self.before_first is None:
                self.before_first = {key: before_sample[key][:4].detach().cpu().numpy().copy()
                                     for key in ('q', 'qd', 'target', 'body_state', 'physics_step')}
            result = super().step(actions)
            sample = self.scene.snapshot()
            now = self.environment._score_time()
            posture = self.environment._finger_preparation(now)
            for env in range(4):
                if env in done:
                    continue
                row = {key: sample[key][env].detach().cpu().numpy().copy()
                       for key in ('q', 'qd', 'target', 'body_state', 'contact_force', 'physics_step')}
                row['action'] = actions[env].detach().cpu().numpy().copy()
                row['previous_target'] = before[env].detach().cpu().numpy().copy()
                row['score_time_s'] = np.asarray(float(now[env]))
                for key in ('mean', 'log_std', 'latent', 'action'):
                    row['policy_'+key] = latest[key][env].detach().cpu().numpy().copy()
                for key in ('gate', 'idle_weight', 'tracking_weight', 'quality', 'angles',
                            'band_inside', 'contact_veto', 'near_veto'):
                    row['finger_'+key] = posture[key][env].detach().cpu().numpy().copy()
                for key in ('candidate', 'wrong', 'surface_distance', 'focus_mask'):
                    row[key] = getattr(self.environment, key)[env].detach().cpu().numpy().copy()
                row['reward'] = result[1][env].detach().cpu().numpy().copy()
                row['cost'] = result[2][env].detach().cpu().numpy().copy()
                samples[env].append(row)
            for episode in result[-1]:
                done.add(episode['env_id'])
            return result

    runner._DeterministicPolicy.act = observing_act
    gpu_pool.GpuPool = ObservingPool
    started = time.monotonic()
    report = None
    try:
        report, _ = runner.evaluate_checkpoint(checkpoint, out, num_envs=8, scope='full_song',
            max_batches=1, max_episodes=8, deadline=time.monotonic()+1200)
    finally:
        runner._DeterministicPolicy.act = original_act
        gpu_pool.GpuPool = original_pool
        if instances:
            pool = instances[-1]
            for env, rows in samples.items():
                if rows:
                    np.savez_compressed(out/('trace_env%04d.npz'%env),
                        **{key: np.stack([row[key] for row in rows]) for key in rows[0]})
            if pool.before_first is not None:
                np.savez_compressed(out/'initial_state_env0000_0003.npz', **pool.before_first)
            task = pool.environment
            metadata = dict(schema='guitar_learning.failure_diagnosis.baseline_trace.v1',
                label=options.label, checkpoint=str(checkpoint),
                checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                package_source_count=len(manifest), source_manifest=str(OLD/'source_manifest.json'),
                package_sources_unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha
                                              for p,sha in manifest.items()),
                selected_envs=[0,1,2,3], selection='predeclared first episode per env; no success selection',
                scene_num_envs=8, scope='full_song', sample_hz=60, physics_hz=240,
                policy_mode='deterministic mean latent; no stochastic training sample captured',
                observation_hook='read-only post-step and policy result copies; no action/control/physics modification',
                joint_names=pool.scene.names, action_names=pool.controller.contract['action_order'],
                native_lower_rad=pool.scene.lower.detach().cpu().tolist(),
                native_upper_rad=pool.scene.upper.detach().cpu().tolist(),
                reference105_rad=pool.controller.reference.detach().cpu().tolist(),
                note_onset_s=task.onset.detach().cpu().tolist(),
                note_end_s=task.end.detach().cpu().tolist(),
                note_press_s=task.press.detach().cpu().tolist(),
                note_finger=task.finger.detach().cpu().tolist(),
                completed=bool(report and report['completed']), scene_closed=pool.closed,
                elapsed_wall_s=time.monotonic()-started,
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
            (out/'trace_metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(label=options.label, summary=report['summary'], completed=report['completed']),ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
