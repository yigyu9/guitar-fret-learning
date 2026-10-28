"""CPU·GPU 왼손 단계 학습의 서로 다른 계약을 한곳에서 설명한다.

읽는 순서: CPU 고정 설정 → CPULeftCurriculum → GPU 고정 설정 → GPULeftCurriculum.
각 구역은 기본 설정, 저장 상태 검증, 단계별 가중치, 완료 에피소드 반영 순서다.
CPU는 8개 에피소드의 전체 도달·접촉 비율, GPU는 256개 에피소드의
손가락별 접근·접촉·성공 비율을 사용한다. 이름을 분리해 수치·판정의 혼용을 막는다.
"""
import numpy as np


# ── CPU: 에피소드 전체의 도달·접촉 비율 ──

CPU_SCHEMA = 'guitar_learning.left_curriculum.v1'
CPU_WINDOW = 8
CPU_STATE_SIZE = 3 + CPU_WINDOW * 3
CPU_ENDPOINTS = dict(wrist=(1., .35, .10), contact=(.15, 1., 1.),
                  timing=(.10, .35, 1.), approach=(.2, .1, 0.))


def cpu_default_config():
    """학습 입력에 기록하는 고정된 JSON 저장 가능 계약을 반환한다."""
    return dict(schema=CPU_SCHEMA, window=CPU_WINDOW, min_episodes=4, step=.1,
                safe_threshold=.75, reach_threshold=.7, contact_threshold=.6,
                weights={name: list(values) for name, values in CPU_ENDPOINTS.items()},
                interpolation='linear_position_press_song_connection',
                unscaled=['action_change', 'terminal_failure', 'safety_cost'])


class CPULeftCurriculum:
    """제한된 에피소드 창을 유지하며 부분 수집만으로는 진도를 올리지 않는다.
    
    수집기는 PPO 수집 후 완료 에피소드를 한 번만 제출한다. 실패 에피소드도
    0값으로 창을 차지한다. 체크포인트 재개 시 다음 갱신을 정확히 이어가도록
    직렬화 상태에 순환 저장 위치도 포함한다.
    """

    def __init__(self):
        self.window = np.zeros((CPU_WINDOW, 3), dtype=np.float64)
        self.count = 0
        self.cursor = 0
        self.progress = 0.

    def state_vector(self):
        return np.concatenate((np.asarray([self.progress, self.count, self.cursor],
                                          dtype=np.float64), self.window.ravel()))

    def load_state(self, vector):
        """현재 값을 하나라도 바꾸기 전에 저장 상태 전체를 검증한다."""
        value = np.asarray(vector, dtype=np.float64)
        if value.shape != (CPU_STATE_SIZE,) or not np.isfinite(value).all():
            raise ValueError('left curriculum state must be 27 finite values')
        progress, count, cursor = value[:3]
        rows = value[3:].reshape(CPU_WINDOW, 3)
        if not (0. <= progress <= 2. and count == int(count) and
                cursor == int(cursor) and 0 <= count <= CPU_WINDOW and
                0 <= cursor < CPU_WINDOW):
            raise ValueError('invalid left curriculum progress/count/cursor')
        count, cursor = int(count), int(cursor)
        if (np.any(rows < 0.) or np.any(rows > 1.) or
                np.any((rows[:, 0] != 0.) & (rows[:, 0] != 1.)) or
                np.any(rows[rows[:, 0] == 0., 1:] != 0.)):
            raise ValueError('invalid left curriculum episode metrics')
        if count < CPU_WINDOW and (cursor != count or np.any(rows[count:] != 0.)):
            raise ValueError('invalid left curriculum unoccupied window')
        self.progress, self.count, self.cursor = float(progress), count, cursor
        self.window = rows.copy()

    def weights(self):
        index = 0 if self.progress <= 1. else 1
        fraction = self.progress - index
        return {name: float(values[index] * (1. - fraction) +
                            values[index + 1] * fraction)
                for name, values in CPU_ENDPOINTS.items()}

    def observe(self, episodes):
        """새로 완료된 에피소드 지표를 반영하고 한 번에 최대 한 단계만 진행한다."""
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
            self.cursor = (self.cursor + 1) % CPU_WINDOW
            self.count = min(self.count + 1, CPU_WINDOW)
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
        return dict(schema=CPU_SCHEMA, stage=stage, progress=self.progress,
                    weights=self.weights(), recent_episodes=self.count,
                    recent_safe_fraction=float(recent[0]),
                    recent_reach_fraction=float(recent[1]),
                    recent_contact_fraction=float(recent[2]),
                    transition_thresholds=dict(min_episodes=4, safe_fraction=.75,
                                               reach_fraction=.7,
                                               contact_fraction=.6, step=.1))


# ── GPU: 곡에 등장하는 손가락별 표면·접촉 비율 ──

GPU_SCHEMA = 'guitar_learning.gpu_left_surface_curriculum.v1'
GPU_WINDOW = 256
GPU_STATE_SIZE = 3 + GPU_WINDOW * 13
GPU_ENDPOINTS = dict(wrist=(.2, .1, .05), contact=(.5, 1., 1.),
                  timing=(.5, 1., 2.), approach=(1., 1., 1.))
GPU_FRACTIONS = ('near_fraction', 'contact_fraction', 'success_fraction')


def gpu_default_config():
    """양의 보상 항과 자유 손목 벌점에 적용할 GPU 단계별 가중치를 반환한다."""
    return dict(schema=GPU_SCHEMA, window=GPU_WINDOW, min_episodes=GPU_WINDOW, step=.1,
                safe_threshold=.9, near_threshold=.2, contact_threshold=.2,
                near_distance_m=.01, near_required_s=.1,
                weights={name: list(values) for name, values in GPU_ENDPOINTS.items()},
                weights_scope='positive_terms_and_wrist_region_penalty',
                interpolation='linear_surface_approach_contact_hold_transition',
                failed_episode_metrics='zeros', finger_gate='all_present_fingers')


class GPULeftCurriculum:
    """실패를 0값 행으로 포함해 종료한 에피소드 256개를 보관한다.
    
    각 행은 안전 여부와 손가락별 접근 비율 4개·접촉 비율 4개·성공 비율 4개를
    담는다. 곡의 고정 손가락 개수는 직렬화 벡터가 아닌 과제 계약에서 얻는다.
    확정된 수집만 observe를 호출한다.
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
        self.window = np.zeros((GPU_WINDOW, 13), dtype=np.float64)
        self.count = 0
        self.cursor = 0
        self.progress = 0.

    def state_vector(self):
        return np.concatenate((np.asarray([self.progress, self.count, self.cursor],
                                          dtype=np.float64), self.window.ravel()))

    def load_state(self, vector):
        """현재 상태를 바꾸기 전에 벡터 전체를 검증한다."""
        value = np.asarray(vector, dtype=np.float64)
        if value.shape != (GPU_STATE_SIZE,) or not np.isfinite(value).all():
            raise ValueError('GPU left curriculum state must be3331 finite values')
        progress, count, cursor = value[:3]
        rows = value[3:].reshape(GPU_WINDOW, 13)
        if not (0. <= progress <= 2. and count == int(count) and
                cursor == int(cursor) and 0 <= count <= GPU_WINDOW and 0 <= cursor < GPU_WINDOW):
            raise ValueError('invalid GPU left curriculum progress/count/cursor')
        count, cursor = int(count), int(cursor)
        if (np.any(rows < 0.) or np.any(rows > 1.) or
                np.any((rows[:, 0] != 0.) & (rows[:, 0] != 1.)) or
                np.any(rows[rows[:, 0] == 0., 1:] != 0.)):
            raise ValueError('invalid GPU left curriculum episode metrics')
        if count < GPU_WINDOW and (cursor != count or np.any(rows[count:] != 0.)):
            raise ValueError('invalid GPU left curriculum unoccupied window')
        self.progress, self.count, self.cursor = float(progress), count, cursor
        self.window = rows.copy()

    def weights(self):
        index = 0 if self.progress <= 1. else 1
        fraction = self.progress - index
        return {name: float(values[index] * (1. - fraction) +
                            values[index + 1] * fraction)
                for name, values in GPU_ENDPOINTS.items()}

    def observe(self, episodes):
        """확정된 수집을 한 번에 반영하고 진행 값은 최대 0.1만 높인다."""
        rows = []
        for episode in episodes:
            if not isinstance(episode, dict) or not {'full_safe', 'finger_metrics'} <= episode.keys():
                raise ValueError('GPU left completed episode fields required')
            safe, fingers = episode['full_safe'], episode['finger_metrics']
            if not isinstance(safe, (bool, np.bool_)) or not isinstance(fingers, (list, tuple)) or len(fingers) != 4:
                raise ValueError('boolean safety and four finger metrics required')
            for metrics, count in zip(fingers, self.finger_counts):
                if (not isinstance(metrics, dict) or not {'target_count', *GPU_FRACTIONS} <= metrics.keys() or
                        not isinstance(metrics['target_count'], (int, np.integer)) or
                        isinstance(metrics['target_count'], (bool, np.bool_)) or metrics['target_count'] != count):
                    raise ValueError('finger target counts must match the fixed song contract')
            values = [metrics[name] for name in GPU_FRACTIONS for metrics in fingers]
            if any(not isinstance(v, (int, float, np.integer, np.floating)) or
                   isinstance(v, (bool, np.bool_)) for v in values):
                raise ValueError('numeric finger fractions required')
            values = np.asarray(values, dtype=np.float64)
            if not np.isfinite(values).all() or np.any(values < 0.) or np.any(values > 1.):
                raise ValueError('finite finger fractions in[0,1] required')
            rows.append(np.concatenate(([1.], values)) if safe else np.zeros(13, dtype=np.float64))
        for row in rows:
            self.window[self.cursor] = row
            self.cursor = (self.cursor + 1) % GPU_WINDOW
            self.count = min(self.count + 1, GPU_WINDOW)
        if self.count == GPU_WINDOW and any(row[0] for row in rows):
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
                    for k, name in enumerate(GPU_FRACTIONS)}) for i, count in enumerate(self.finger_counts)]
        return dict(schema=GPU_SCHEMA, stage=stage, progress=self.progress,
                    weights=self.weights(), recent_episodes=self.count,
                    recent_safe_fraction=float(recent[0]), recent_fingers=fingers,
                    transition_thresholds=dict(min_episodes=GPU_WINDOW, safe_fraction=.9,
                        near_fraction=.2, contact_fraction=.2, step=.1,
                        finger_gate='all_present_fingers',
                        stage0_metric='near_fraction', stage1_metric='contact_fraction'))
