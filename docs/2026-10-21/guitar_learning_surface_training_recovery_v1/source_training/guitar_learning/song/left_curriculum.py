"""Performance based reward blending for fresh left hand song learning."""
import numpy as np


SCHEMA = 'guitar_learning.left_curriculum.v1'
WINDOW = 8
STATE_SIZE = 3 + WINDOW * 3
_ENDPOINTS = dict(wrist=(1., .35, .10), contact=(.15, 1., 1.),
                  timing=(.10, .35, 1.), approach=(.2, .1, 0.))


def default_config():
    """Return the fixed, JSON safe contract recorded with training inputs."""
    return dict(schema=SCHEMA, window=WINDOW, min_episodes=4, step=.1,
                safe_threshold=.75, reach_threshold=.7, contact_threshold=.6,
                weights={name: list(values) for name, values in _ENDPOINTS.items()},
                interpolation='linear_position_press_song_connection',
                unscaled=['action_change', 'terminal_failure', 'safety_cost'])


class CurriculumState:
    """Keep a bounded episode window; partial rollouts never advance progress.

    The collector submits completed episodes once, after a PPO collection.
    Failed episodes occupy the window as zeros. State serialization includes the
    ring cursor so that checkpoint continuation preserves the exact next update.
    """

    def __init__(self):
        self.window = np.zeros((WINDOW, 3), dtype=np.float64)
        self.count = 0
        self.cursor = 0
        self.progress = 0.

    def state_vector(self):
        return np.concatenate((np.asarray([self.progress, self.count, self.cursor],
                                          dtype=np.float64), self.window.ravel()))

    def load_state(self, vector):
        """Validate the entire saved state before replacing any live value."""
        value = np.asarray(vector, dtype=np.float64)
        if value.shape != (STATE_SIZE,) or not np.isfinite(value).all():
            raise ValueError('left curriculum state must be 27 finite values')
        progress, count, cursor = value[:3]
        rows = value[3:].reshape(WINDOW, 3)
        if not (0. <= progress <= 2. and count == int(count) and
                cursor == int(cursor) and 0 <= count <= WINDOW and
                0 <= cursor < WINDOW):
            raise ValueError('invalid left curriculum progress/count/cursor')
        count, cursor = int(count), int(cursor)
        if (np.any(rows < 0.) or np.any(rows > 1.) or
                np.any((rows[:, 0] != 0.) & (rows[:, 0] != 1.)) or
                np.any(rows[rows[:, 0] == 0., 1:] != 0.)):
            raise ValueError('invalid left curriculum episode metrics')
        if count < WINDOW and (cursor != count or np.any(rows[count:] != 0.)):
            raise ValueError('invalid left curriculum unoccupied window')
        self.progress, self.count, self.cursor = float(progress), count, cursor
        self.window = rows.copy()

    def weights(self):
        index = 0 if self.progress <= 1. else 1
        fraction = self.progress - index
        return {name: float(values[index] * (1. - fraction) +
                            values[index + 1] * fraction)
                for name, values in _ENDPOINTS.items()}

    def observe(self, episodes):
        """Consume new completed episode metrics and advance at most one step."""
        rows = []
        for episode in episodes:
            safe = episode['full_safe']
            reach = float(episode['reach_fraction'])
            contact = float(episode['contact_fraction'])
            if (not isinstance(safe, (bool, np.bool_)) or
                    not np.isfinite([reach, contact]).all() or
                    not (0. <= reach <= 1. and 0. <= contact <= 1.)):
                raise ValueError('invalid completed left curriculum episode')
            rows.append([1., reach, contact] if safe else [0., 0., 0.])
        for row in rows:
            self.window[self.cursor] = row
            self.cursor = (self.cursor + 1) % WINDOW
            self.count = min(self.count + 1, WINDOW)
        if any(row[0] for row in rows) and self.count >= 4:
            safe, reach, contact = self.window[:self.count].mean(axis=0)
            eligible = safe >= .75 and reach >= .7
            if self.progress >= 1.:
                eligible = eligible and contact >= .6
            if eligible:
                ceiling = 1. if self.progress < 1. else 2.
                self.progress = min(ceiling, round(self.progress + .1, 10))
        return self.summary()

    def summary(self):
        recent = (self.window[:self.count].mean(axis=0) if self.count else
                  np.zeros(3, dtype=np.float64))
        stage = ('position' if self.progress < 1. else
                 'press' if self.progress < 2. else 'song_connection')
        return dict(schema=SCHEMA, stage=stage, progress=self.progress,
                    weights=self.weights(), recent_episodes=self.count,
                    recent_safe_fraction=float(recent[0]),
                    recent_reach_fraction=float(recent[1]),
                    recent_contact_fraction=float(recent[2]),
                    transition_thresholds=dict(min_episodes=4, safe_fraction=.75,
                                               reach_fraction=.7,
                                               contact_fraction=.6, step=.1))
