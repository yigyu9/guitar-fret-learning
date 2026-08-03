"""CPU checks for the one-song repeated-practice R26 schedule."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.curriculum import PerSongCurriculum, PerSongCurriculumConfig


class Goals:
    def set_random_start_probability(self, value):
        self.value = value


class Env:
    goals = Goals()


def main():
    curriculum = PerSongCurriculum(PerSongCurriculumConfig(10, 20))
    assert curriculum.state(1)["curriculum_stage"] == "coverage"
    assert curriculum.state(10)["curriculum_random_start_probability"] == 1.0
    assert curriculum.state(20)["curriculum_random_start_probability"] == 0.5
    assert curriculum.state(30)["curriculum_random_start_probability"] == 0.0
    assert curriculum.state(31)["curriculum_stage"] == "full_song"
    state = curriculum.apply(Env(), 25)
    assert Env.goals.value == state["curriculum_random_start_probability"] == 0.25
    forced = PerSongCurriculum(PerSongCurriculumConfig(10, 20), "full_song")
    assert forced.state(1)["curriculum_random_start_probability"] == 0.0
    print("PASS: per-song coverage -> integration -> full-song curriculum")


if __name__ == "__main__":
    main()
