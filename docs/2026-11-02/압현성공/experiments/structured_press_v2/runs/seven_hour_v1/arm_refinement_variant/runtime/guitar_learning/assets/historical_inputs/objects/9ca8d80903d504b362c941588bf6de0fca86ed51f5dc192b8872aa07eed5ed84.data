"""Smooth bounded endpoint teacher. Native codec smoothing/rate limits still apply."""
import copy
import math


class Controller:
    def __init__(self, plan, task, transition=None):
        if len(plan['candidates']) != 4:
            raise ValueError('exact four proposals required')
        self.actions = {row['name']: self._checked(row['action39']) for row in plan['candidates']}
        if set(self.actions) != {'single_a', 'overlap', 'single_b', 'release'}:
            raise ValueError('exact A/overlap/B/release proposal set required')
        targets = task.targets
        if len(targets) not in (1, 2):
            raise ValueError('one or two targets required')
        self.task = task
        self.previous = None
        self.diagnostic = {}
        self.transition = copy.deepcopy(transition)
        a, b = targets[0], targets[-1]
        if len(targets) == 1:
            self.waypoints = [(0., [0.] * 39, 'reference'),
                (.7 * float(a.onset_s), self.actions['single_a'], 'single_a'),
                (float(a.end_s), self.actions['single_a'], 'single_a'),
                (min(float(task.duration_s), float(a.end_s) + .3), self.actions['release'], 'release')]
        else:
            self.waypoints = [(0., [0.] * 39, 'reference'),
                (.7 * float(a.onset_s), self.actions['single_a'], 'single_a'),
                (float(a.onset_s), self.actions['overlap'], 'overlap'),
                (float(a.end_s), self.actions['overlap'], 'overlap'),
                (min(float(b.end_s), max(float(b.onset_s), float(a.end_s)) + .08), self.actions['single_b'], 'single_b'),
                (float(b.end_s), self.actions['single_b'], 'single_b'),
                (min(float(task.duration_s), float(b.end_s) + .3), self.actions['release'], 'release')]
        if any(t < 0 or not math.isfinite(t) for t, _, _ in self.waypoints):
            raise ValueError('finite nonnegative waypoint times required')
        if any(self.waypoints[i][0] > self.waypoints[i+1][0] for i in range(len(self.waypoints)-1)):
            raise ValueError('ordered overlap schedule required')

    @staticmethod
    def _checked(action):
        values = [float(v) for v in action]
        if (len(values) != 39 or any(not math.isfinite(v) or abs(v) > 1 for v in values)
                or any(v != 0. for v in values[33:])):
            raise ValueError('finite bounded39 proposal with exactly zero right6 required')
        return values

    def action(self, now, observation=None, env=None):
        if isinstance(now, bool) or not math.isfinite(now) or now < 0:
            raise ValueError('finite nonnegative policy time required')
        if self.previous is None and abs(now) > 1e-9:
            raise ValueError('teacher must start at policy time0')
        if self.previous is not None and abs(now-self.previous-1/60.) > 1e-8:
            raise ValueError('one call per consecutive60Hz tick; new controller after reset')
        left = self.waypoints[0]
        right = self.waypoints[-1]
        for item in self.waypoints:
            if item[0] <= now:
                left = item
            else:
                right = item
                break
        if now >= self.waypoints[-1][0]:
            right = left = self.waypoints[-1]
        fraction = ((now-left[0])/(right[0]-left[0]) if right[0] > left[0] else 1.)
        fraction = max(0., min(1., fraction))
        smooth = fraction*fraction*(3.-2.*fraction)
        output = self._checked([a+smooth*(b-a) for a, b in zip(left[1], right[1])])
        self.previous = float(now)
        self.diagnostic = dict(from_waypoint=left[2], to_waypoint=right[2], fraction=fraction,
            interpolated_command=True, live_guitar_tracking=False,
            scope='snapshot geometric teacher commands only; same native codec and quality/safety gates; not learned success')
        return output
