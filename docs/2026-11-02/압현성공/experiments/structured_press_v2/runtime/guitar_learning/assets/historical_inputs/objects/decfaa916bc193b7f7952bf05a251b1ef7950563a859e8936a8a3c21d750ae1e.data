"""Small bounded action candidates; no simulator, state writes or success gates.

Call from policy time0 before every native control tick. ``context`` describes
the already measured state, so an accepted crossing can affect only the next
action. A held normalized command is different from holding the applied codec
target: existing smoothing/rate limits may still advance toward the command.
"""
import copy
import math
from ..control import ACTIVE_NAMES

FLEX_NAMES = tuple('LH:'+finger+str(joint) for finger in
    ('thumb', 'index', 'middle', 'ring', 'pinky') for joint in (2, 3))


def candidate_configs(role):
    if role == 'left':
        return [dict(name='left_return_reference', role=role, trigger='note_end',
                     duration_s=.3, named_offsets={}),
                dict(name='left_return_reference_open_flex', role=role, trigger='note_end',
                     duration_s=.3, named_offsets={name: -1. for name in FLEX_NAMES})]
    if role == 'right':
        return [dict(name='right_hold_last_command', role=role, trigger='first_accepted',
                     duration_s=0., named_offsets={}),
                dict(name='right_hold_applied_target', role=role, trigger='first_accepted',
                     duration_s=0., named_offsets={})]
    raise ValueError('single left/right role required')


def _vector(value, label, *, bounded=False):
    try: values = [float(x) for x in value]
    except (TypeError, ValueError) as error: raise ValueError(label+' requires39 finite values') from error
    if (len(values) != 39 or not all(math.isfinite(x) for x in values) or
            (bounded and any(abs(x) > 1. for x in values))):
        raise ValueError(label+' requires39 finite'+(' bounded' if bounded else '')+' values')
    return values


def normalize_target(target_active39, reference39, lower39, upper39):
    """Invert the original asymmetric codec; clip native limits, zero empty spans.

    The caller selects39 semantic ACTIVE_NAMES from its81/105 ordering. This
    returns commands, not physical positions. No native state is modified.
    """
    target, reference, lower, upper = [_vector(v, name) for v, name in (
        (target_active39, 'target'), (reference39, 'reference'), (lower39, 'lower'), (upper39, 'upper'))]
    result = []
    for q, ref, lo, hi in zip(target, reference, lower, upper):
        if not lo <= ref <= hi: raise ValueError('native bounds must contain reference')
        q = min(hi, max(lo, q))
        delta = q-ref
        span = hi-ref if delta >= 0. else ref-lo
        result.append(min(1., max(-1., delta/span)) if span > 0. else 0.)
    return result


class Controller:
    """Preserve the policy prefix, then latch one explicitly declared candidate.

    Required context: time_s, task_end_s, musical_quality_before. Intervention
    also requires applied_normalized39. The open-flex candidate additionally
    needs reference39/lower39/upper39 in semantic action order. Reset per episode.
    ``diagnostic`` records the trigger time, interpolation and fixed goal but
    makes no claim about contact, physical recovery or musical success.
    """
    def __init__(self, role, candidate):
        known = candidate_configs(role)
        name = candidate if isinstance(candidate, str) else candidate.get('name') if isinstance(candidate, dict) else None
        matches = [item for item in known if item['name'] == name]
        if len(matches) != 1 or (isinstance(candidate, dict) and candidate != matches[0]):
            raise ValueError('one known unmodified local candidate for this role required')
        self.role, self.config = role, copy.deepcopy(matches[0])
        self.inactive = range(33, 39) if role == 'left' else range(33)
        self.reset()

    def reset(self):
        self.start_s = self.previous_time_s = self.task_end_s = None
        self.last_output = self.anchor = self.goal = None
        self.diagnostic = dict(intervention=False, candidate=self.config['name'])

    def _role_action(self, value, label):
        result = _vector(value, label, bounded=True)
        if any(result[i] != 0. for i in self.inactive):
            raise ValueError('inactive hand must be exactly zero')
        return result

    def action(self, policy_action, context):
        policy = self._role_action(policy_action, 'policy_action')
        now, end = context['time_s'], context['task_end_s']
        if (isinstance(now, bool) or isinstance(end, bool) or not math.isfinite(now) or
                not math.isfinite(end) or now < 0. or end <= 0.):
            raise ValueError('finite nonnegative policy time and positive note end required')
        if self.previous_time_s is None:
            if abs(now) > 1e-9: raise ValueError('controller must observe the actual policy prefix from time0')
        elif abs(now-self.previous_time_s-1/60.) > 1e-8:
            raise ValueError('one call per consecutive60Hz control tick required')
        if self.task_end_s is not None and end != self.task_end_s:
            raise ValueError('reset controller before changing target/episode')
        before = context['musical_quality_before']
        accepted = bool(before.get('strike', {}).get('accepted_crossing_ids', []))
        trigger = now >= end if self.role == 'left' else accepted
        if self.start_s is None and trigger:
            if self.last_output is None:
                raise ValueError('a measured intervention needs a previously issued policy action')
            applied = self._role_action(context['applied_normalized39'], 'applied_normalized39')
            self.anchor = applied
            self.goal = [0.]*39 if self.role == 'left' else (
                self.last_output.copy() if self.config['name'] == 'right_hold_last_command' else applied.copy())
            if self.config['named_offsets']:
                # Request the native lower target through the same inverse used
                # by the runner. A lower==reference/zero-span axis yields0.
                lower = normalize_target(context['lower39'], context['reference39'], context['lower39'], context['upper39'])
                for name in self.config['named_offsets']:
                    index = ACTIVE_NAMES.index(name)
                    self.goal[index] = lower[index]
            self.start_s = float(now)
        intervened = self.start_s is not None
        fraction = (min(1., (now-self.start_s)/self.config['duration_s'])
                    if intervened and self.config['duration_s'] > 0. else 1. if intervened else 0.)
        output = ([self.anchor[i]+fraction*(self.goal[i]-self.anchor[i]) for i in range(39)]
                  if intervened else policy.copy())
        # The first RH action after accepted must hold its goal immediately.
        output = self._role_action(output, 'candidate_action')
        self.previous_time_s, self.task_end_s, self.last_output = float(now), float(end), output.copy()
        self.diagnostic = dict(candidate=self.config['name'], intervention=intervened,
            start_s=self.start_s, fraction=fraction, goal_action39=copy.deepcopy(self.goal),
            scope='bounded target command candidate only; original native quality/safety decides success')
        return output, intervened
