"""Camera-only replay of the completed V2 noNN scripted reference, never a policy."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent
spec = importlib.util.spec_from_file_location('release_close_video_source', SOURCE/'probe.py')
v2 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v2
spec.loader.exec_module(v2)
base = v2.base


def preflight():
    old = base.HERE
    try:
        base.HERE = SOURCE
        pins = base.gate()
    finally:
        base.HERE = old
    out = SOURCE/'runs/candidate'
    report, audit = base.read(out/'report.json'), base.read(out/'inputs_after.json')
    assert report['completed'] and report['closed'] and report['completed_attempts'] == 128
    assert all(report[k] == 0 for k in ('NN_constructors', 'checkpoint_loads', 'PPO_updates', 'fit_steps'))
    assert not report['failure'] and not report['cleanup_errors']
    assert audit['verified'] and not base.changed_pins(audit['input_pins'])
    assert audit['input_pins'] == pins
    reuse = base.read(SOURCE/'baseline_reuse.json')
    for name, digest in reuse['files'].items():
        assert base.sha(SOURCE/'runs/baseline'/name) == digest
    artifacts = [out/name for name in ('report.json', 'inputs_after.json', 'evaluation.json',
        'trace_env0_episode0.npz', 'training_contract.json')]
    assert all(p.is_file() for p in artifacts)
    return dict(pins, **{str(p): base.sha(p) for p in artifacts})


def prepare():
    pins = preflight()  # Missing headless artifacts are a hard stop, before any writes.
    (HERE/'cpu_inputs').mkdir(exist_ok=False)
    for name in ('candidate.json', 'settings.json'):
        shutil.copy2(SOURCE/'cpu_inputs'/name, HERE/'cpu_inputs'/name)
    (HERE/'runs/baseline').mkdir(parents=True, exist_ok=False)
    for name in ('evaluation.json', 'report.json'):
        shutil.copy2(SOURCE/'runs/baseline'/name, HERE/'runs/baseline'/name)
    shutil.copy2(SOURCE/'baseline_reuse.json', HERE/'baseline_reuse.json')
    own = [Path(__file__).resolve(), HERE/'cpu_check.py', HERE/'PLAN.md', HERE/'baseline_reuse.json',
           *list((HERE/'cpu_inputs').glob('*.json')), *list((HERE/'runs/baseline').glob('*.json'))]
    pins.update({str(p): base.sha(p) for p in own})
    base.write(HERE/'preparation_seal.json', dict(input_pins=pins, independent_review='pending',
        noNN=True, source='Completed V2 candidate; 128 environments; env0 first attempt preselected'))


def execute():
    preflight()
    old = base.HERE
    try:
        base.HERE = HERE
        base.gate()
    finally:
        base.HERE = old
    import isaacgym  # Must precede NumPy/Torch and shared support.
    from isaacgym import gymapi
    import numpy as np
    sys.path.insert(0, str(v2.ROOT))
    from guitar_learning.tool.demonstration import render_finger_skill as render
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym, finish_video
    shared = base.support()
    original_geometry = base.geometry_function
    holders = []

    class CapturedPool(shared.Pool):
        def __init__(self, settings, out):
            self.capture, self.videos, self.video_closed = None, {}, False
            holders.append(self)
            original = gymapi.acquire_gym
            try:
                gymapi.acquire_gym = lambda: GraphicsGym(original())
                super().__init__(settings, out)
            finally:
                gymapi.acquire_gym = original
            try:
                cameras = render._create_cameras(self.scene, gymapi)
                self.scene.gym.set_camera_location(cameras['fullbody'], self.scene.envs[0],
                    gymapi.Vec3(-.10, 3.4, 1.1), gymapi.Vec3(-.15, -.10, .65))
                for name in cameras:
                    self.videos[name] = render._encoder(out/(name+'.mp4'))
                self.capture = render._EnvZeroCapture(self, gymapi, np, cameras, self.videos)
            except BaseException:
                try:
                    self.close()
                except BaseException:
                    pass  # Preserve construction error; close writes its own lifecycle audit.
                raise

        def step(self, action):
            terms = self.environment.episode_reward_terms
            previous = {k: v[0].clone() for k, v in terms.items()}
            result = super().step(action)
            before = len(self.capture.samples)
            reward = result[1][0].detach().cpu().numpy().copy()
            rewards9 = np.asarray([float(terms[k][0]-previous[k]) for k in terms])
            assert len(terms) == 9
            try:
                self.capture.record(before, *result[1:])
            finally:
                if len(self.capture.samples) > before:
                    self.capture.samples[-1].update(reward=reward, reward_components9=rewards9)
            return result

        def close(self):
            errors = []
            if not self.video_closed:
                self.video_closed = True
                for name, video in self.videos.items():
                    code, issues = finish_video(video)
                    errors.extend(issues + ([] if code == 0 else [name+': encoder exit '+str(code)]))
                try:
                    if self.capture is not None:
                        base.save_rows(HERE/'runs/candidate/native_capture.npz', self.capture.samples)
                        base.write(HERE/'runs/candidate/capture.json', dict(noNN=True, checkpoint_loads=0,
                            completed=len(self.capture.samples) == 354 and len(self.capture.frame_times_s) == 177 and not errors,
                            frames=len(self.capture.frame_times_s), controls=len(self.capture.samples),
                            reward_names=list(self.environment.episode_reward_terms),
                            episode=self.capture.episode, frame_times_s=self.capture.frame_times_s))
                except BaseException as error:
                    errors.append(repr(error))
            try:
                super().close()
            finally:
                if errors:
                    base.write(HERE/'runs/candidate/video_cleanup_errors.json', errors)
            if errors:
                raise RuntimeError(str(errors))

    def geometry():
        old = base.HERE
        try:
            base.HERE = SOURCE
            return original_geometry()
        finally:
            base.HERE = old

    try:
        with v2.execution_scope():
            proxy = base.support()
            proxy.Pool = CapturedPool
            base.HERE, base.geometry_function = HERE, geometry
            base.run('candidate')
    finally:
        base.geometry_function = original_geometry
    out = HERE/'runs/candidate'
    try:
        capture = holders[0].capture
        assert len(capture.samples) == 354 and len(capture.frame_times_s) == 177
        z = np.load(out/'trace_env0_episode0.npz', allow_pickle=False)
        source = np.load(SOURCE/'runs/candidate/trace_env0_episode0.npz', allow_pickle=False)
        for key in ('q', 'target', 'body_state', 'candidate'):
            np.testing.assert_array_equal(z[key], source[key])
        for key in ('q', 'target', 'body_state'):
            np.testing.assert_array_equal(np.asarray([r[key] for r in capture.samples]), z[key])
        assert base.read(out/'evaluation.json')['episodes'] == base.read(SOURCE/'runs/candidate/evaluation.json')['episodes']
        base.write(out/'video_verification.json', dict(completed=True, native_pixels=True, noNN=True,
            environments=128, env_id=0, first_attempt=True, frames=177, controls=354,
            duration_s=5.9, fps=30, size=[1280,720], headless_trace_and_ledger_bitexact=True))
    except BaseException as error:
        base.write(out/'video_verification.json', dict(completed=False, failure=repr(error)))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'prepare', 'execute'))
    args = parser.parse_args()
    if args.action == 'preflight':
        preflight()
        print(json.dumps(dict(ready=True, native_runs=0)))
    elif args.action == 'prepare':
        prepare()
    else:
        execute()
