"""Static editor entry with atomic, viewer-line-free camera snapshots."""
from pathlib import Path
from . import interactive_guitar_pose_static as app


class Editor(app.Editor):
    def initialize(self, candidate):
        super().initialize(candidate)
        app.save(self.out/'snapshot_implementation.json', {
            'source': str(Path(__file__).resolve()), 'sha256': app.sha(Path(__file__).resolve()),
            'physics_enabled': False, 'scope': 'clear viewer debug lines before native camera capture'})

    def save_candidate(self):
        if self.viewer is not None:
            self.env.gym.clear_lines(self.viewer)
        try:
            return super().save_candidate()
        finally:
            if self.viewer is not None:
                self.draw()


def main():
    original = app.Editor
    app.Editor = Editor
    try:
        app.main()
    finally:
        app.Editor = original


if __name__ == '__main__': main()
