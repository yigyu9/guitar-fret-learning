"""Independent scalar provenance oracle; CPU only, no simulator or training."""
from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from guitar_learning.gpu.environment import TensorSongEnvironment


def main():
    torch.set_num_threads(1)
    rng = np.random.default_rng(1523)
    n, m, samples = 3, 9, 7
    count = 10*samples
    strings = rng.integers(0, 6, m)
    frets = rng.integers(1, 23, m)
    fingers = rng.integers(1, 5, m)
    onset = rng.uniform(.2, 4.6, m)
    press = onset-.2
    clock = np.array([30, 240, 930])
    body_finger = np.repeat(np.arange(5), 2*samples)
    assigned = rng.integers(0, 23, (n, count))
    nearest = rng.integers(0, 6, (n, count))
    qualifies = rng.random((n, count)) > .6
    in_goal = rng.random((n, count, m)) > .7
    positive = rng.random((n, m)) > .5
    same_string = nearest[..., None] == strings
    same_finger = body_finger[:, None] == fingers
    flags = np.zeros((n, m, 10, 3), dtype=bool)
    minimum = np.full((n, m, 10), 23, dtype=np.int16)
    maximum = np.zeros((n, m, 10), dtype=np.int16)
    wrong = np.zeros((n, m), dtype=bool)
    supported = np.zeros((n, m), dtype=bool)
    preparing = np.zeros((n, m), dtype=bool)
    for row in range(n):
        for target in range(m):
            for point in range(count):
                if not (qualifies[row, point] and nearest[row, point] == strings[target]):
                    continue
                source_fret = assigned[row, point]
                relations = [source_fret > frets[target],
                             0 < source_fret < frets[target],
                             in_goal[row, point, target] and body_finger[point] != fingers[target]]
                for cause, relation in enumerate(relations):
                    if not relation or (cause != 0 and positive[row, target]):
                        continue
                    body = point//samples
                    flags[row, target, body, cause] = True
                    minimum[row, target, body] = min(minimum[row, target, body], source_fret)
                    maximum[row, target, body] = max(maximum[row, target, body], source_fret)
                    wrong[row, target] = True
                    supported[row, target] |= bool(source_fret > 0 and
                        (cause != 2 or source_fret == frets[target]))
                    for future in range(m):
                        if (press[future]-2 <= clock[row]/240 < onset[future] and
                                strings[future] == nearest[row, point] and
                                frets[future] == source_fret and
                                fingers[future] == body_finger[point]):
                            preparing[row, target] = True
    env = SimpleNamespace(N=n, M=m, surface_count=samples,
        starts=torch.zeros(n, 6, 3), frets=torch.zeros(n, 23, 3),
        string=torch.tensor(strings), fret=torch.tensor(frets), finger=torch.tensor(fingers),
        press=torch.tensor(press), onset=torch.tensor(onset), clock=torch.tensor(clock),
        pad_fingers=torch.tensor(body_finger))
    args = [torch.tensor(value) for value in
            (qualifies, assigned, nearest, same_string, in_goal, same_finger, positive, wrong)]
    original = [value.clone() for value in args]
    TensorSongEnvironment._wrong_sources(env, *args)
    for actual, expected in [(env.wrong_source_flags, flags),
            (env.wrong_source_fret_min, minimum), (env.wrong_source_fret_max, maximum),
            (env.wrong_supported, supported), (env.wrong_ambiguous, wrong & ~supported),
            (env.wrong_next_preparation, preparing)]:
        np.testing.assert_array_equal(actual.numpy(), expected)
    for before, after in zip(original, args):
        assert torch.equal(before, after), 'Diagnostic mutated a verdict input'
    np.testing.assert_array_equal(flags.any(axis=(2, 3)), wrong)
    print('PASS: 810 body/cause flags, 270 source-fret min/max cells, '
          '27 supported/ambiguous/preparation classifications match independent scalar oracle; '
          'all verdict inputs unchanged.')


if __name__ == '__main__':
    main()
