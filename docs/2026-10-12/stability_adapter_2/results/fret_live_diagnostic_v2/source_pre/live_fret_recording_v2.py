"""Same native cameras; copy their RGBA pixels before encoding outside Gym."""
import json
import numpy as np
from PIL import Image
from .gym_trial_recording import GymTrialRecording, sha
from .live_fret_recording import LiveFretRecording


class NativePixelRecording:
    def __init__(self, raw):
        self.env, self.out, self.frames = raw.env, raw.out, raw.frames
        self.views, self.fps, self.interval = raw.views, raw.fps, raw.interval

    def capture(self):
        from .environment import gymapi
        from .run_joint_hold import native_state
        env = self.env; before = native_state(env); images = {}
        env.gym.step_graphics(env.sim); env.gym.render_all_camera_sensors(env.sim)
        for name in self.views:
            rgba = np.array(env.gym.get_camera_image(env.sim, env.env, env.cameras[name], gymapi.IMAGE_COLOR), copy=True)
            if rgba.dtype != np.uint8 or rgba.size != 1280*720*4: raise ValueError('missing native RGBA pixels')
            path = self.out/'frames'/name/('%05d.png'%len(self.frames))
            Image.fromarray(rgba.reshape(720, 1280, 4), 'RGBA').save(path)
            images[str(path)] = sha(path)
        unchanged = native_state(env) == before
        self.frames.append(dict(physics_step=env.steps, time_s=env.steps/env.config['physics_hz'], render_preserves_states=unchanged, image_sha256=images))
        temp = self.out/'capture.tmp'
        temp.write_text(json.dumps(dict(renderer='Isaac Gym native camera RGBA + PIL PNG encoding',
            camera_config_source='stability_adapter_2/capture_isaac_gym_initial.py', graphics_device_id=0,
            fps=self.fps, frames=self.frames), indent=2)+'\n'); temp.replace(self.out/'capture.json')
        if not unchanged: raise AssertionError('native camera pixel capture changed state')

    def encode(self): return GymTrialRecording.encode(self)


class LiveFretRecordingV2(LiveFretRecording):
    def __init__(self, env, out):
        super().__init__(env, out)
        self.raw = NativePixelRecording(self.raw)
