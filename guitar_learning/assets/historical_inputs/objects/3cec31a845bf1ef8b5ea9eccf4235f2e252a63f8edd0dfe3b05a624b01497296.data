"""Static guitar editor with an Euler XYZ rotation readout."""
from pathlib import Path

from . import interactive_guitar_pose_static as app
from .guitar_pose_edit import Rotation
from .guitar_pose_static import Editor as StaticEditor

HELP = app.HELP.replace(
    'F1/F2/F3: translate X/Y/Z | F4/F5/F6: rotate X/Y/Z',
    'F1/F2/F3: translate X/Y/Z | F4/F5/F6: select Euler X/Y/Z')
HELP = HELP.replace('F: fine | Tab: world/local',
                    'F: fine | Tab: world/local Euler frame')


class Editor(StaticEditor):
    def initialize(self, candidate):
        super().initialize(candidate)
        app.save(self.out/'snapshot_euler_display.json', {
            'source': str(Path(__file__).resolve()),
            'sha256': app.sha(Path(__file__).resolve()),
            'rotation_readout': 'Euler XYZ in selected world/local frame, degrees',
            'pose_storage': 'quaternion_xyzw',
            'physics_enabled': False,
        })

    def handle(self, key):
        if self.mode == 'EDIT' and self.axis >= 3 and key in ('J', 'L'):
            self.history.append((self.position.copy(), self.quaternion.copy()))
            sequence = 'XYZ' if self.local else 'xyz'
            angles = Rotation.from_quat(self.quaternion).as_euler(sequence, degrees=True)
            step = .25 if self.fine else 1.
            angles[self.axis-3] += step * (1 if key == 'L' else -1)
            self.quaternion = Rotation.from_euler(sequence, angles, degrees=True).as_quat()
            self.install_pose()
            self.status()
            return True
        return super().handle(key)

    def status(self):
        sequence = 'XYZ' if self.local else 'xyz'
        convention = 'intrinsic/local' if self.local else 'extrinsic/world'
        euler = Rotation.from_quat(self.quaternion).as_euler(sequence, degrees=True)
        print('STATIC ONLY | %s %s %s | %s | %s | strap DISPLAY %s | t=%.3fs | p=%s | Euler %s %s [deg]=%s' % (
            self.mode, 'move' if self.axis<3 else 'rotate', 'XYZ'[self.axis%3],
            'local' if self.local else 'world', 'fine' if self.fine else 'normal',
            'ON' if self.strap else 'OFF', self.env.steps/240,
            app.np.round(self.position,6), sequence, convention,
            app.np.round(euler,3)), flush=True)


def main():
    original = app.Editor
    original_help = app.HELP
    app.Editor = Editor
    app.HELP = HELP
    try:
        app.main()
    finally:
        app.Editor = original
        app.HELP = original_help


if __name__ == '__main__':
    main()
