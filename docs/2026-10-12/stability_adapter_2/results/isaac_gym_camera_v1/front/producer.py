"""Capture the current initial scene using Isaac Gym camera sensors, no physics steps."""
import argparse
import json
from pathlib import Path

from .self_collision_environment import SelfCollisionEnvironment
from .self_collision_probe import SUPPORT_PHASE
from .environment import ROOT, gymapi, np
from .build_fixed_lower_asset import read, sha
from .run_joint_hold import native_state
from .run_self_collision import audit


class GraphicsGym:
    def __init__(self, gym):
        self.gym = gym

    def __getattr__(self, name):
        return getattr(self.gym, name)

    def create_sim(self, compute, graphics, engine, params):
        return self.gym.create_sim(compute, 0, engine, params)


class CameraEnvironment(SelfCollisionEnvironment):
    def __init__(self, settings, shift):
        acquire = gymapi.acquire_gym
        gymapi.acquire_gym = lambda: GraphicsGym(acquire())
        try:
            super().__init__(settings, shift)
        finally:
            gymapi.acquire_gym = acquire

    def _create_scene(self):
        super()._create_scene()
        for actor, names in ((self.human, self.human_bodies), (self.guitar, self.guitar_bodies)):
            for index, name in enumerate(names):
                rgb = (.12, .65, .3) if name.startswith('LH:') else (
                    (.8, .12, .5) if name.startswith('RH:') else
                    (.12, .3, .8) if actor == self.guitar else (.7, .7, .7))
                self.gym.set_rigid_body_color(self.env, actor, index,
                    gymapi.MESH_VISUAL_AND_COLLISION, gymapi.Vec3(*rgb))
        self.cameras = {}
        for name, position, target in (
                ('whole_body', (.9, 1.8, 1.15), (-.06, 0, .68)),
                ('hands', (-.05, .72, .89), (-.105, .095, .735)),
                ('hands_collision', (-.05, .72, .89), (-.105, .095, .735))):
            props = gymapi.CameraProperties()
            props.width, props.height = 1280, 720
            props.use_collision_geometry = name.endswith('_collision')
            camera = self.gym.create_camera_sensor(self.env, props)
            if camera < 0:
                raise RuntimeError('Isaac Gym camera creation failed: ' + name)
            self.gym.set_camera_location(camera, self.env,
                gymapi.Vec3(*position), gymapi.Vec3(*target))
            self.cameras[name] = camera


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    search_path = SUPPORT_PHASE / 'search_near_touch.json'
    search = read(search_path)
    settings_path = Path(search['rows'][0]['settings_path'])
    reference_path = ROOT / 'docs/2026-10-12/stability_adapter_2/results/self_collision_v1/short/on/states.json'
    inputs = [Path(__file__).resolve(), search_path, settings_path, reference_path]
    inputs += [Path(p) for p in read(reference_path.with_name('report.json'))['source_sha256']]
    hashes = {str(p): sha(p) for p in inputs}
    (args.out / 'attempt.json').write_text(json.dumps({
        'renderer': 'Isaac Gym native camera', 'graphics_device_id': 0,
        'requested_physics_steps': 0, 'input_sha256': hashes}, indent=2) + '\n')
    env = CameraEnvironment(read(settings_path), search['guitar_initial_translation_m'])
    try:
        state = native_state(env)
        if state != read(reference_path)[0]:
            raise AssertionError('graphics initialization changed initial state')
        mask_audit = audit(env)
        env.gym.step_graphics(env.sim)
        env.gym.render_all_camera_sensors(env.sim)
        outputs = {}
        for name, camera in env.cameras.items():
            rgba = env.gym.get_camera_image(env.sim, env.env, camera, gymapi.IMAGE_COLOR)
            if rgba is None or np.asarray(rgba).size != 1280 * 720 * 4:
                raise RuntimeError('native camera returned no RGBA image')
            path = args.out / (name + '.png')
            env.gym.write_camera_image_to_file(env.sim, env.env, camera, gymapi.IMAGE_COLOR, str(path))
            outputs[str(path)] = sha(path)
        checks = {'initial_state_exact': True, 'render_preserves_state': native_state(env) == state,
            'zero_physics_steps': env.steps == 0,
            'inputs_unchanged': all(sha(Path(p)) == h for p, h in hashes.items())}
        (args.out / 'capture.json').write_text(json.dumps({
            'checks': checks, 'physics_steps': env.steps, 'initial_state': state,
            'mask_audit': mask_audit, 'output_sha256': outputs,
            'input_sha256': hashes}, indent=2, allow_nan=False) + '\n')
        if not all(checks.values()):
            raise AssertionError(checks)
        print(json.dumps(checks))
    finally:
        env.close()


if __name__ == '__main__':
    main()
