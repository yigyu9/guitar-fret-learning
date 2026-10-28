"""Fixed requested-goal timing and bounded first-attempt native gate counters."""
import math


def boundaries(view):
    start = view['source_targets'][0]['end_s']-view['score_offset_s']
    finish = view['source_targets'][1]['press_s']-view['score_offset_s']
    return start, start+.10, finish-.12, finish


def negative_weight(time, view):
    start, _, close, _ = boundaries(view)
    return ((time-start)/.10).clamp(0, 1)-((time-close)/.12).clamp(0, 1)


def wrist_weight(time, view):
    _, start, finish, _ = boundaries(view)
    return ((time-start)/(finish-start)).clamp(0, 1)


def phase(time, view):
    for i, limit in enumerate(boundaries(view)):
        if time < limit: return i
    return 4


class Observer:
    """Five fixed phases × four envs; counts/first events only, no body trace."""
    names = ('before', 'release', 'move', 'close', 'after')

    def __init__(self, view):
        self.view = view
        self.active = [True]*4
        self.rows = [dict(env_id=i, last_clock=0, first_censored_clock=None, previous_candidate=None,
            first_post_A_candidate_fall=None, first_valid_post_A_candidate_fall=None, phases={}) for i in range(4)]

    def observe(self, clock, candidate, loaded, wrong, force, failed):
        for i, row in enumerate(self.rows):
            if not self.active[i]: continue
            now = int(clock[i]); assert now == row['last_clock']+1 and now <= 1416
            row['last_clock'] = now
            if failed[i] and row['first_censored_clock'] is None: row['first_censored_clock'] = now
            censored = row['first_censored_clock'] is not None
            local = now/240.; name = self.names[phase(local, self.view)]
            if name not in row['phases']:
                row['phases'][name] = dict(samples=0, censored_samples=0, nonfinite_force_samples=0,
                    valid_samples=0, candidate_counts=[0]*3, loaded_counts=[0]*3, wrong_counts=[0]*3,
                    max_distal_resultant_N=None, max_valid_distal_resultant_N=None,
                    first_valid_A_candidateoff_loadedoff=None, first_valid_B_candidateoff_loadedoff=None)
            item = row['phases'][name]; item['samples'] += 1; item['censored_samples'] += int(censored)
            finite = math.isfinite(force[i]); item['nonfinite_force_samples'] += int(not finite)
            valid = finite and not censored; item['valid_samples'] += int(valid)
            for k in range(3):
                item['candidate_counts'][k] += int(candidate[i][k]); item['loaded_counts'][k] += int(loaded[i][k]); item['wrong_counts'][k] += int(wrong[i][k])
            if finite:
                item['max_distal_resultant_N'] = max(item['max_distal_resultant_N'] or 0., force[i])
                if valid: item['max_valid_distal_resultant_N'] = max(item['max_valid_distal_resultant_N'] or 0., force[i])
            event = dict(clock=now, local_time_s=local, score_time_s=local+self.view['score_offset_s'],
                candidate=list(candidate[i]), assigned_loaded=list(loaded[i]), distal_resultant_N=force[i] if finite else None, censored=censored)
            if row['previous_candidate'] is not None and row['previous_candidate'][0] and not candidate[i][0] and local >= boundaries(self.view)[0]:
                if row['first_post_A_candidate_fall'] is None: row['first_post_A_candidate_fall'] = event
                if valid and row['first_valid_post_A_candidate_fall'] is None: row['first_valid_post_A_candidate_fall'] = event
            if valid and not candidate[i][0] and not loaded[i][0] and item['first_valid_A_candidateoff_loadedoff'] is None:
                item['first_valid_A_candidateoff_loadedoff'] = event
            if valid and not any(candidate[i][1:]) and not any(loaded[i][1:]) and item['first_valid_B_candidateoff_loadedoff'] is None:
                item['first_valid_B_candidateoff_loadedoff'] = event
            row['previous_candidate'] = list(candidate[i])

    def finish(self, rows):
        for row in rows:
            i = row['env_id']
            if self.active[i]:
                self.rows[i]['first_attempt_end'] = dict(steps=row['steps'], reason=row['reason'])
                self.active[i] = False

    def document(self):
        return dict(envs=self.rows, first_attempt_active=self.active, clock_hz=240,
            scope='post original native substep; first4 attempts incl immediate+latched failure labels; events after censor excluded; native loaded flags unchanged; no pair/pressure or full-skin separation claim')
