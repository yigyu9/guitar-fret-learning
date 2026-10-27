"""GPU surface/contact curriculum gated by every finger present in the song."""
import numpy as np


SCHEMA = 'guitar_learning.gpu_left_surface_curriculum.v1'
WINDOW = 256
STATE_SIZE = 3 + WINDOW * 13
_ENDPOINTS = dict(wrist=(.2, .1, .05), contact=(.5, 1., 1.),
                  timing=(.5, 1., 2.), approach=(1., 1., 1.))
_FRACTIONS = ('near_fraction', 'contact_fraction', 'success_fraction')


def default_config():
    """Return the fixed JSON-safe GPU contract; weights apply to positive terms."""
    return dict(schema=SCHEMA, window=WINDOW, min_episodes=WINDOW, step=.1,
                safe_threshold=.9, near_threshold=.2, contact_threshold=.2,
                near_distance_m=.01, near_required_s=.1,
                weights={name: list(values) for name, values in _ENDPOINTS.items()},
                weights_scope='positive_terms_only',
                interpolation='linear_surface_approach_contact_hold_transition',
                failed_episode_metrics='zeros', finger_gate='all_present_fingers')


class CurriculumState:
    """Keep256 ended episodes, including failures as zero rows.

    Rows contain safe, four near fractions, four contact fractions and four
    success fractions. Fixed song finger counts come from the task contract,
    not the serialized vector. Only committed collections call observe.
    """

    def __init__(self, finger_counts):
        try:
            counts = tuple(finger_counts)
        except TypeError as error:
            raise ValueError('four nonnegative integer finger counts required') from error
        if (len(counts) != 4 or
                any(not isinstance(v, (int, np.integer)) or isinstance(v, (bool, np.bool_))
                    or v < 0 for v in counts) or sum(counts) <= 0):
            raise ValueError('four nonnegative integer finger counts with positive total required')
        self.finger_counts = tuple(int(v) for v in counts)
        self.window = np.zeros((WINDOW, 13), dtype=np.float64)
        self.count = 0
        self.cursor = 0
        self.progress = 0.

    def state_vector(self):
        return np.concatenate((np.asarray([self.progress, self.count, self.cursor],
                                          dtype=np.float64), self.window.ravel()))

    def load_state(self, vector):
        """Validate the entire vector before replacing live state."""
        value = np.asarray(vector, dtype=np.float64)
        if value.shape != (STATE_SIZE,) or not np.isfinite(value).all():
            raise ValueError('GPU left curriculum state must be3331 finite values')
        progress, count, cursor = value[:3]
        rows = value[3:].reshape(WINDOW, 13)
        if not (0. <= progress <= 2. and count == int(count) and
                cursor == int(cursor) and 0 <= count <= WINDOW and 0 <= cursor < WINDOW):
            raise ValueError('invalid GPU left curriculum progress/count/cursor')
        count, cursor = int(count), int(cursor)
        if (np.any(rows < 0.) or np.any(rows > 1.) or
                np.any((rows[:, 0] != 0.) & (rows[:, 0] != 1.)) or
                np.any(rows[rows[:, 0] == 0., 1:] != 0.)):
            raise ValueError('invalid GPU left curriculum episode metrics')
        if count < WINDOW and (cursor != count or np.any(rows[count:] != 0.)):
            raise ValueError('invalid GPU left curriculum unoccupied window')
        self.progress, self.count, self.cursor = float(progress), count, cursor
        self.window = rows.copy()

    def weights(self):
        index = 0 if self.progress <= 1. else 1
        fraction = self.progress - index
        return {name: float(values[index] * (1. - fraction) +
                            values[index + 1] * fraction)
                for name, values in _ENDPOINTS.items()}

    def observe(self, episodes):
        """Consume a committed collection atomically; advance at most0.1."""
        rows = []
        for episode in episodes:
            if not isinstance(episode, dict) or not {'full_safe', 'finger_metrics'} <= episode.keys():
                raise ValueError('GPU left completed episode fields required')
            safe, fingers = episode['full_safe'], episode['finger_metrics']
            if not isinstance(safe, (bool, np.bool_)) or not isinstance(fingers, (list, tuple)) or len(fingers) != 4:
                raise ValueError('boolean safety and four finger metrics required')
            for metrics, count in zip(fingers, self.finger_counts):
                if (not isinstance(metrics, dict) or not {'target_count', *_FRACTIONS} <= metrics.keys() or
                        not isinstance(metrics['target_count'], (int, np.integer)) or
                        isinstance(metrics['target_count'], (bool, np.bool_)) or metrics['target_count'] != count):
                    raise ValueError('finger target counts must match the fixed song contract')
            values = [metrics[name] for name in _FRACTIONS for metrics in fingers]
            if any(not isinstance(v, (int, float, np.integer, np.floating)) or
                   isinstance(v, (bool, np.bool_)) for v in values):
                raise ValueError('numeric finger fractions required')
            values = np.asarray(values, dtype=np.float64)
            if not np.isfinite(values).all() or np.any(values < 0.) or np.any(values > 1.):
                raise ValueError('finite finger fractions in[0,1] required')
            rows.append(np.concatenate(([1.], values)) if safe else np.zeros(13, dtype=np.float64))
        for row in rows:
            self.window[self.cursor] = row
            self.cursor = (self.cursor + 1) % WINDOW
            self.count = min(self.count + 1, WINDOW)
        if self.count == WINDOW and any(row[0] for row in rows):
            recent = self.window.mean(axis=0)
            start = 1 if self.progress < 1. else 5
            present = np.asarray(self.finger_counts) > 0
            if recent[0] >= .9 and np.all(recent[start:start + 4][present] >= .2):
                ceiling = 1. if self.progress < 1. else 2.
                self.progress = min(ceiling, round(self.progress + .1, 10))
        return self.summary()

    def summary(self):
        recent = self.window[:self.count].mean(axis=0) if self.count else np.zeros(13)
        stage = ('surface_approach' if self.progress < 1. else
                 'contact' if self.progress < 2. else 'hold_transition')
        fingers = [dict(target_count=count, **{name: float(recent[1 + 4 * k + i])
                    for k, name in enumerate(_FRACTIONS)}) for i, count in enumerate(self.finger_counts)]
        return dict(schema=SCHEMA, stage=stage, progress=self.progress,
                    weights=self.weights(), recent_episodes=self.count,
                    recent_safe_fraction=float(recent[0]), recent_fingers=fingers,
                    transition_thresholds=dict(min_episodes=WINDOW, safe_fraction=.9,
                        near_fraction=.2, contact_fraction=.2, step=.1,
                        finger_gate='all_present_fingers',
                        stage0_metric='near_fraction', stage1_metric='contact_fraction'))
