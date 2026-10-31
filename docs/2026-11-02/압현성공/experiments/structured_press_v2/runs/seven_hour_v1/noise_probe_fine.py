"""기존 잡음 진단의 계산을 재사용하여 .05/.1 배율만 추가로 평가한다."""
if __name__ == '__main__':
    import isaacgym

from contextlib import contextmanager
from pathlib import Path
import noise_probe as base


@contextmanager
def fine_sampling_override(sp, official, scale):
    with original_override(sp, official, scale):
        original_pins = official._pins
        def pins(settings, out, extra=()):
            return original_pins(settings, out, list(extra)+[Path(__file__).resolve()])
        official._pins = pins
        try:
            yield
        finally:
            official._pins = original_pins


original_override = base.sampling_override
if __name__ == '__main__':
    base.SCALES = (0., .05, .1, .25, .5, 1.)
    base.sampling_override = fine_sampling_override
    base.main()
