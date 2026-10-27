"""Serializable R/F/J coordinator, independent of the legacy song curriculum.

This module counts committed raw control transitions and independent evaluation
episodes. The runner owns simulator boundaries and explicit actor transfers.
"""
import copy
import math


PHASES = ('R', 'F', 'J')
DEFAULT_THRESHOLDS = dict(safe_fraction=.9, wrist_inside_fraction=.8,
                          finger_opportunities=64, finger_success_fraction=.2)
DEFAULT_BUDGETS = dict(R=1_000_000, F=1_000_000, J=1_000_000)


def _count(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(name+' must be a nonnegative integer')
    return value


def _fraction(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(name+' must be a finite fraction in [0,1]')
    return float(value)


class FingerSkillCurriculum:
    schema = 'guitar_learning.finger_skill_curriculum.v1'

    def __init__(self, phase='R', budgets=None, thresholds=None):
        if phase not in PHASES:
            raise ValueError('R/F/J phase required')
        budgets = copy.deepcopy(DEFAULT_BUDGETS if budgets is None else budgets)
        if not isinstance(budgets, dict) or set(budgets) != set(PHASES):
            raise ValueError('explicit R/F/J raw transition budgets required')
        for name, value in budgets.items(): _count(value, 'budget '+name)
        supplied = {} if thresholds is None else thresholds
        if not isinstance(supplied, dict) or set(supplied)-set(DEFAULT_THRESHOLDS):
            raise ValueError('unknown finger-skill thresholds')
        thresholds = dict(DEFAULT_THRESHOLDS, **supplied)
        for name in ('safe_fraction', 'wrist_inside_fraction', 'finger_success_fraction'):
            thresholds[name] = _fraction(thresholds[name], name)
        if _count(thresholds['finger_opportunities'], 'finger_opportunities') < 1:
            raise ValueError('positive finger opportunities threshold required')
        self.config = dict(initial_phase=phase, budgets=budgets, thresholds=thresholds,
                           evaluation_scope=dict(R='phrase', F='phrase', J='full_song'))
        self.phase = phase
        self.training_transitions = dict.fromkeys(PHASES, 0)
        self.evaluation_transitions = dict.fromkeys(PHASES, 0)
        self.phase_evalhistory = dict((name, []) for name in PHASES)
        self.ready = False

    def status(self):
        used, limit = self.training_transitions[self.phase], self.config['budgets'][self.phase]
        return dict(phase=self.phase, ready=self.ready, training_transitions=used,
                    budget=limit, remaining_transitions=max(limit-used, 0),
                    budget_exhausted=used >= limit, stalled=used >= limit and not self.ready)

    def commit(self, transitions):
        """Charge actual committed 60Hz transitions, never held-action decisions."""
        _count(transitions, 'committed transitions')
        self.training_transitions[self.phase] += transitions
        if transitions:
            # A previous model's evaluation cannot authorize a later model.
            self.ready = False
        return self.status()

    def evaluate(self, episodes):
        """Evaluate one fixed batch, retaining failed episodes in every denominator.

        Each row must be marked evaluation=True and finger_skill_eval must name
        the current phase/scope. Training and censored rows are errors, rather
        than silently filtered opportunities. A failed song contributes zero
        successes for all its scheduled notes, including its unobserved tail.
        """
        if not isinstance(episodes, (list, tuple)) or not episodes:
            raise ValueError('nonempty fixed evaluation episode batch required')
        safe_count, wrist_sum, transitions = 0, 0., 0
        opportunities, successes = [0]*4, [0.]*4
        for row in episodes:
            if not isinstance(row, dict) or row.get('evaluation') is not True or row.get('valid') is not True:
                raise ValueError('explicit valid independent evaluation rows required')
            tag = row.get('finger_skill_eval')
            if (not isinstance(tag, dict) or tag.get('phase') != self.phase or
                    tag.get('scope') != self.config['evaluation_scope'][self.phase]):
                raise ValueError('evaluation phase/scope mismatch')
            reason = row.get('reason')
            if reason not in ('timeline_complete', 'terminal_failure'):
                raise ValueError('partial/censored evaluation rows are not completed episodes')
            song = row.get('song')
            if not isinstance(song, dict) or type(song.get('completed')) is not bool:
                raise ValueError('explicit song completion required')
            if song['completed'] != (reason == 'timeline_complete'):
                raise ValueError('evaluation reason/completion mismatch')
            steps = _count(row.get('steps'), 'evaluation steps')
            if steps < 1:
                raise ValueError('nonempty evaluation episode required')
            transitions += steps
            curriculum = row.get('left_curriculum')
            if not isinstance(curriculum, dict) or type(curriculum.get('full_safe')) is not bool:
                raise ValueError('explicit full-safe evaluation flag required')
            if reason == 'terminal_failure' and curriculum['full_safe']:
                raise ValueError('failed evaluation cannot be full-safe')
            safe = reason == 'timeline_complete' and curriculum['full_safe']
            safe_count += safe
            if self.phase == 'R':
                wrist = tag.get('wrist_inside_fraction')
                if wrist is None:
                    wrist = row.get('left_episode_diagnostics', {}).get('wrist', {}).get('inside_fraction')
                wrist = _fraction(wrist, 'evaluation wrist_inside_fraction')
                wrist_sum += wrist if safe else 0.
            metrics = curriculum.get('finger_metrics')
            if not isinstance(metrics, (list, tuple)) or len(metrics) != 4:
                raise ValueError('four scheduled finger opportunity rows required')
            for finger, metric in enumerate(metrics):
                if not isinstance(metric, dict):
                    raise ValueError('finger metric dictionary required')
                count = _count(metric.get('target_count'), 'finger target_count')
                fraction = _fraction(metric.get('success_fraction'), 'finger success_fraction')
                if count == 0 and fraction != 0:
                    raise ValueError('zero opportunities require zero success fraction')
                opportunities[finger] += count
                successes[finger] += count*fraction if safe else 0.
        threshold = self.config['thresholds']
        safe_fraction = safe_count/len(episodes)
        wrist_fraction = wrist_sum/len(episodes) if self.phase == 'R' else None
        fractions = [success/count if count else 0. for success, count in zip(successes, opportunities)]
        if self.phase == 'R':
            ready = safe_fraction >= threshold['safe_fraction'] and wrist_fraction >= threshold['wrist_inside_fraction']
        elif self.phase == 'F':
            ready = safe_fraction >= threshold['safe_fraction'] and all(
                count >= threshold['finger_opportunities'] and fraction >= threshold['finger_success_fraction']
                for count, fraction in zip(opportunities, fractions))
        else:
            ready = False  # J ends by its explicit training budget, not a hidden mastery gate.
        self.evaluation_transitions[self.phase] += transitions
        self.ready = bool(ready)
        summary = dict(schema=self.schema, phase=self.phase, scope=self.config['evaluation_scope'][self.phase],
            episodes=len(episodes), safe_episodes=safe_count, safe_fraction=safe_fraction,
            wrist_inside_fraction=wrist_fraction, finger_opportunities=opportunities,
            finger_successes=successes, finger_success_fractions=fractions,
            evaluation_transitions=transitions, evaluated_after_training_transitions=self.training_transitions[self.phase],
            ready=self.ready, thresholds=copy.deepcopy(threshold))
        summary.update(self.status())
        self.phase_evalhistory[self.phase].append(copy.deepcopy(summary))
        return summary

    def next_phase(self):
        """Advance only after readiness; the runner must first commit a boundary."""
        if not self.ready or self.phase == 'J':
            return None
        self.phase = PHASES[PHASES.index(self.phase)+1]
        self.ready = False
        return self.phase

    def state_dict(self):
        return copy.deepcopy(dict(schema=self.schema, config=self.config, phase=self.phase,
            training_transitions=self.training_transitions, evaluation_transitions=self.evaluation_transitions,
            phase_evalhistory=self.phase_evalhistory, ready=self.ready))

    def load_state_dict(self, state):
        expected = self.state_dict()
        if (not isinstance(state, dict) or state.keys() != expected.keys() or
                state.get('schema') != self.schema or state.get('config') != self.config or
                state.get('phase') not in PHASES or type(state.get('ready')) is not bool):
            raise ValueError('strict finger-skill curriculum schema/config/state mismatch')
        for field in ('training_transitions', 'evaluation_transitions'):
            values = state[field]
            if not isinstance(values, dict) or values.keys() != expected[field].keys():
                raise ValueError('strict curriculum counters mismatch')
            for key, value in values.items(): _count(value, field+'.'+key)
        history = state['phase_evalhistory']
        if not isinstance(history, dict) or history.keys() != expected['phase_evalhistory'].keys():
            raise ValueError('strict curriculum evaluation history mismatch')
        for phase, rows in history.items():
            if not isinstance(rows, list):
                raise ValueError('evaluation history must contain lists')
            total = 0
            for row in rows:
                if (not isinstance(row, dict) or row.get('schema') != self.schema or row.get('phase') != phase or
                        row.get('scope') != self.config['evaluation_scope'][phase] or
                        row.get('thresholds') != self.config['thresholds'] or type(row.get('ready')) is not bool):
                    raise ValueError('strict evaluation history row mismatch')
                total += _count(row.get('evaluation_transitions'), 'history evaluation_transitions')
            if total != state['evaluation_transitions'][phase]:
                raise ValueError('evaluation history/counter mismatch')
        if state['ready']:
            rows = history[state['phase']]
            if (state['phase'] == 'J' or not rows or rows[-1]['ready'] is not True or
                    rows[-1]['evaluated_after_training_transitions'] != state['training_transitions'][state['phase']]):
                raise ValueError('readiness must refer to the current committed model')
        # Complete validation precedes mutation, so failed resume is atomic.
        self.phase = state['phase']
        self.training_transitions = copy.deepcopy(state['training_transitions'])
        self.evaluation_transitions = copy.deepcopy(state['evaluation_transitions'])
        self.phase_evalhistory = copy.deepcopy(history)
        self.ready = state['ready']


class ExposureSchedule:
    """Fixed first-run exposure boundary; additional training never moves it."""
    schema = 'guitar_learning.finger_skill_exposure.v1'
    phase = 'J'

    def __init__(self, planned_transitions, full_song_after=None):
        if _count(planned_transitions, 'planned_transitions') < 1:
            raise ValueError('positive planned transitions required')
        threshold = planned_transitions//4 if full_song_after is None else full_song_after
        if _count(threshold, 'full_song_after') != planned_transitions//4:
            raise ValueError('fixed quarter of original planned transitions required')
        self.config = dict(planned_transitions=planned_transitions, full_song_after=threshold)
        self.committed_transitions = 0

    @property
    def training_transitions(self):
        return dict(J=self.committed_transitions)

    @property
    def evaluation_transitions(self):
        return {}

    def status(self):
        planned, committed = self.config['planned_transitions'], self.committed_transitions
        return dict(phase='J', planned_transitions=planned,
            full_song_after=self.config['full_song_after'], committed_transitions=committed,
            remaining_transitions=max(0, planned-committed),
            next_reset_scope='full_song' if committed >= self.config['full_song_after'] else 'phrases',
            changes_only_on_episode_reset=True, mastery_gate=False)

    def commit(self, transitions):
        self.committed_transitions += _count(transitions, 'committed transitions')
        return self.status()

    def state_dict(self):
        return dict(schema=self.schema, config=copy.deepcopy(self.config),
                    committed_transitions=self.committed_transitions)

    def load_state_dict(self, state):
        if (not isinstance(state, dict) or state.keys() != self.state_dict().keys() or
                state.get('schema') != self.schema or state.get('config') != self.config):
            raise ValueError('strict exposure schedule schema/config mismatch')
        committed = _count(state['committed_transitions'], 'committed transitions')
        self.committed_transitions = committed
