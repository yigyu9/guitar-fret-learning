"""Run the finger experiment with real Isaac Gym cameras at each control frame."""
import argparse
import json
import sys
from pathlib import Path

from . import run_finger_grip_hold as runner
from .capture_isaac_gym_initial import CameraEnvironment
from .environment import gymapi
from .run_joint_hold import native_state
from .build_fixed_lower_asset import sha


def main():
    parser=argparse.ArgumentParser(description=__doc__,add_help=False)
    parser.add_argument('--record-root',type=Path,required=True)
    args,remaining=parser.parse_known_args()
    args.record_root.mkdir(parents=True,exist_ok=False)
    frames=[]
    inputs=[Path(__file__).resolve(),Path(__file__).with_name('capture_isaac_gym_initial.py')]
    hashes={str(p):sha(p) for p in inputs}

    class RecordedEnvironment(CameraEnvironment):
        def __init__(self,settings,shift):
            super().__init__(settings,shift)
            self.capture()

        def capture(self):
            before=native_state(self)
            self.gym.step_graphics(self.sim)
            self.gym.render_all_camera_sensors(self.sim)
            images={}
            for name in ('whole_body','hands'):
                folder=args.record_root/name
                folder.mkdir(exist_ok=True)
                path=folder/('%05d.png'%self.steps)
                self.gym.write_camera_image_to_file(self.sim,self.env,self.cameras[name],gymapi.IMAGE_COLOR,str(path))
                images[str(path.resolve())]=sha(path)
            unchanged=native_state(self)==before
            frames.append({'physics_step':self.steps,'time_s':self.steps/self.config['physics_hz'],
                           'render_preserves_states':unchanged,'image_sha256':images})
            (args.record_root/'capture.json').write_text(json.dumps({'renderer':'Isaac Gym native camera',
                'graphics_device_id':0,'graphics_backend_identity':'not queried',
                'frames':frames,'input_sha256':hashes},indent=2)+'\n')
            if not unchanged:raise AssertionError('graphics changed native state')

        def step_physics(self):
            super().step_physics()
            if self.steps%4==0:self.capture()

    previous=runner.SelfCollisionEnvironment
    argv=sys.argv
    runner.SelfCollisionEnvironment=RecordedEnvironment
    sys.argv=[argv[0]]+remaining
    try:
        runner.main()
        if not all(sha(Path(p))==v for p,v in hashes.items()):raise AssertionError('camera inputs changed')
    finally:
        runner.SelfCollisionEnvironment=previous
        sys.argv=argv


if __name__=='__main__':main()
