"""One-pass, read-only aggregation of v19 ended training episodes.

Writes a new derived JSON report only. Histograms preserve exact integer-score
quantiles without storing episode objects. Source raw/metrics/reports are never
modified. These collections are not frozen-policy checkpoint evaluations.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import numpy as np
from guitar_learning.training.gpu_log_records import iter_episode_rows

FINGERS = ('index', 'middle', 'ring', 'little')
FIELDS = ('left', 'near_done', 'contact_done', 'contact_progress', 'contact_time',
    'best_contact_streak', 'clean', 'best_clean_streak', 'wrong', 'missing',
    'exposure_time', 'near_time', 'geometry_time', 'facing_time', 'body_load_time',
    'loaded_target_time', 'higher_time', 'lower_time', 'assignment_time')


def require(value, message):
    if not value:
        raise ValueError(message)


def distribution(histogram):
    count = sum(histogram)
    if not count:
        return dict(n=0, mean=None, median=None, p10=None, p25=None, p75=None,
            p90=None, p95=None, maximum=None, zero_fraction=None)
    samples = np.repeat(np.arange(len(histogram)), histogram)
    quantiles = np.quantile(samples, [.1, .25, .5, .75, .9, .95])
    return dict(n=int(count), mean=float(np.dot(np.arange(len(histogram)), histogram)/count),
        median=float(quantiles[2]), p10=float(quantiles[0]), p25=float(quantiles[1]),
        p75=float(quantiles[3]), p90=float(quantiles[4]), p95=float(quantiles[5]),
        maximum=int(samples[-1]), zero_fraction=histogram[0]/count,
        integer_score_histogram=list(map(int, histogram)))


class Aggregate:
    def __init__(self, start, end, targets):
        self.start, self.end, self.targets = start, end, targets
        self.n = self.safe = self.full_safe = self.failed = self.success = 0
        self.hist = np.zeros(68, dtype=np.int64)
        self.safe_hist = self.hist.copy()
        self.full_hist = self.hist.copy()
        self.failures = Counter()
        self.sum = {key: np.zeros(67, dtype=np.float64) for key in FIELDS}
        self.exposed = np.zeros(67, dtype=np.int64)
        self.surface_sum = np.zeros(67, dtype=np.float64)
        self.partial_contact = np.zeros(67, dtype=np.int64)
        self.completed_contact = np.zeros(67, dtype=np.int64)
        self.any_contact_progress = np.zeros(67, dtype=np.int64)
        self.finger_raw = np.zeros((4, 4), dtype=np.float64)
        self.finger_curriculum = np.zeros((4, 4), dtype=np.float64)
        self.finger_safe = np.zeros((4, 4), dtype=np.float64)
        self.reward = self.cost = self.duration = self.clean_fraction = 0.
        self.contact_reward = 0.

    def add(self, episode, arrays, fingers):
        self.n += 1
        song = episode['song']
        safe = not song['safety_invalidated']
        full_safe = bool(episode['left_curriculum']['full_safe'] and episode['reason']=='timeline_complete')
        require(not full_safe or safe, 'full_safe with invalid safety')
        left = song['left_success_count']
        self.hist[left] += 1
        if safe:
            self.safe += 1
            self.safe_hist[left] += 1
            self.finger_safe += fingers
        if full_safe:
            self.full_safe += 1
            self.full_hist[left] += 1
            self.finger_curriculum += fingers
        self.failed += episode['reason'] == 'terminal_failure'
        self.success += bool(song['stage_success'])
        self.failures.update(episode['failure_reasons'])
        self.reward += episode['reward']
        self.cost += episode['cost']
        self.duration += episode['task_time_s']
        self.clean_fraction += song['mean_clean_audible_fraction']
        self.contact_reward += episode['reward_components']['song_left_contact']
        self.finger_raw += fingers
        for key in FIELDS:
            self.sum[key] += arrays[key]
        exposed = arrays['exposure_time'] > 0
        self.exposed += exposed
        self.surface_sum += np.where(exposed, arrays['surface_min'], 0.)
        progress = arrays['contact_progress']
        self.partial_contact += (progress > 0) & ~arrays['contact_done'].astype(bool)
        self.completed_contact += arrays['contact_done'].astype(bool)
        self.any_contact_progress += progress > 0

    def result(self, counts):
        n = self.n
        def mean(value, denominator=n):
            return float(value/denominator) if denominator else None
        fingers = []
        for index, (name, count) in enumerate(zip(FINGERS, counts)):
            mask = np.asarray([t['finger'] == index+1 for t in self.targets])
            row = dict(finger=name, finger_id=index+1, targets_per_song=count)
            for label, matrix, denominator in (
                ('raw_all_ended', self.finger_raw, n),
                ('raw_safe_only', self.finger_safe, self.safe),
                ('curriculum_failures_zeroed', self.finger_curriculum, n)):
                row[label] = {metric:mean(matrix[index, j], denominator)
                    for j, metric in enumerate(('near_fraction', 'contact_fraction', 'success_fraction', 'clean_fraction'))}
                row[label]['mean_successful_notes'] = mean(matrix[index, 2]*count, denominator)
            row['contact_progress'] = dict(mean_budget_progress_sum=mean(self.sum['contact_progress'][mask].sum()),
                mean_partial_notes=mean(self.partial_contact[mask].sum()),
                mean_complete_notes=mean(self.completed_contact[mask].sum()))
            fingers.append(row)
        notes = []
        for index, target in enumerate(self.targets):
            duration = target['end_s']-target['onset_s']
            note = {key:target[key] for key in ('target_id', 'finger', 'fret', 'onset_s', 'end_s', 'press_s')}
            note.update(target_index=index, string_1based=target['string']+1,
                success_fraction=mean(self.sum['left'][index]), near_fraction=mean(self.sum['near_done'][index]),
                first_contact_complete_fraction=mean(self.sum['contact_done'][index]),
                contact_progress_mean=mean(self.sum['contact_progress'][index]),
                contact_partial_fraction=mean(self.partial_contact[index]),
                contact_complete_fraction=mean(self.completed_contact[index]),
                contact_any_progress_fraction=mean(self.any_contact_progress[index]),
                exposure_episode_count=int(self.exposed[index]), exposure_episode_fraction=mean(self.exposed[index]),
                surface_min_mean_exposed_m=mean(self.surface_sum[index], self.exposed[index]))
            note['mean_times_s_all_ended'] = {key:mean(self.sum[key][index]) for key in FIELDS
                if key not in ('left', 'near_done', 'contact_done', 'contact_progress')}
            note['wrong_mean_fraction_of_audible_interval'] = mean(self.sum['wrong'][index]/duration)
            note['missing_mean_fraction_of_audible_interval'] = mean(self.sum['missing'][index]/duration)
            notes.append(note)
        return dict(update_start_inclusive=self.start, update_end_exclusive=self.end,
            ended_episodes=n, safe_episodes=self.safe, safe_fraction=mean(self.safe),
            full_safe_episodes=self.full_safe, physical_failures=self.failed, physical_failure_fraction=mean(self.failed),
            successful_episodes=self.success, failure_reason_counts=dict(self.failures),
            successful_notes=distribution(self.hist), safe_only_successful_notes=distribution(self.safe_hist),
            full_safe_only_successful_notes=distribution(self.full_hist),
            means=dict(reward=mean(self.reward), cost=mean(self.cost), ended_duration_s=mean(self.duration),
                clean_audible_fraction=mean(self.clean_fraction), contact_paid_reward=mean(self.contact_reward)),
            contact_progress=dict(mean_budget_progress_sum=mean(self.sum['contact_progress'].sum()),
                mean_partial_notes=mean(self.partial_contact.sum()),
                mean_complete_notes=mean(self.completed_contact.sum()),
                mean_any_progress_notes=mean(self.any_contact_progress.sum()),
                target_episode_partial_fraction=mean(self.partial_contact.sum(), n*67),
                target_episode_complete_fraction=mean(self.completed_contact.sum(), n*67)),
            fingers=fingers, targets=notes)


def analyze(phase):
    run = phase/'train3000'
    inspection = json.loads((phase/'log_inspection.json').read_text())
    contract = json.loads((run/'training_contract.json').read_text())
    targets = contract['task']['provenance']['song']['schedule']
    ids = [t['target_id'] for t in targets]
    counts = [sum(t['finger']==finger for t in targets) for finger in range(1, 5)]
    require(len(targets)==67 and len(set(ids))==67 and counts==[25, 18, 12, 12], 'Target denominator/order')
    groups = {name:Aggregate(start, end, targets) for name, start, end in (
        ('all', 0, 3000), ('first100', 0, 100), ('first250', 0, 250),
        ('last100', 2900, 3000), ('last250', 2750, 3000), ('last500', 2500, 3000))}
    bins100 = [Aggregate(start, start+100, targets) for start in range(0, 3000, 100)]
    bins250 = [Aggregate(start, start+250, targets) for start in range(0, 3000, 250)]
    previous = -1
    total = 0
    for row in iter_episode_rows(run):
        index, episode = row['update_index'], row['episode']
        require(previous <= index < 3000, 'Nonmonotonic/out-of-budget episode update')
        previous = index
        require(episode['valid'] is True and episode['reason'] in ('timeline_complete', 'terminal_failure'), 'Unexpected episode')
        ledger = episode['left_note_ledger']
        require(ledger['target_ids']==ids and len(ledger['required_clean_s'])==67, 'Ledger target order')
        arrays = {key:np.asarray(ledger['values'][key], dtype=np.float64) for key in FIELDS+('surface_min',)}
        require(all(a.shape==(67,) and np.isfinite(a).all() for a in arrays.values()), 'Nonfinite/malformed note ledger')
        require(all((arrays[key]>=0).all() for key in FIELDS), 'Negative note metric')
        require(((arrays['contact_progress']>=0)&(arrays['contact_progress']<=1)).all(), 'Contact progress out of range')
        require(int(arrays['left'].sum())==episode['song']['left_success_count'], 'Song/ledger successful note mismatch')
        threshold = np.asarray([min(.05, t['end_s']-t['press_s']) for t in targets])
        require(np.array_equal(arrays['contact_done'].astype(bool), arrays['best_contact_streak']+1e-12>=threshold), 'Contact complete/streak threshold mismatch')
        raw = episode['left_curriculum']['finger_metrics']
        require([f['target_count'] for f in raw]==counts, 'Per-finger denominators')
        fingers = np.asarray([[finger[key] for key in ('near_fraction', 'contact_fraction', 'success_fraction', 'clean_fraction')]
            for finger in raw], dtype=np.float64)
        require(np.isfinite(fingers).all() and ((fingers>=0)&(fingers<=1)).all(), 'Finger metric range')
        for i in range(4):
            mask = np.asarray([t['finger']==i+1 for t in targets])
            for j, key in enumerate(('near_done', 'contact_done', 'left')):
                require(abs(float(arrays[key][mask].mean())-fingers[i, j])<1e-6, 'Finger/ledger metric mismatch')
        selected = [g for g in groups.values() if g.start<=index<g.end]
        selected.extend((bins100[index//100], bins250[index//250]))
        for group in selected:
            group.add(episode, arrays, fingers)
        total += 1
        if total%10000==0:
            print('Read %d ended episodes through update %d' % (total, index), flush=True)
    result = dict(schema='guitar_learning.v19_ended_episode_analysis.v1',
        source=str(run/'episodes.jsonl'), episode_stream_passes=1,
        target_count=67, finger_target_counts=counts,
        groups={name:group.result(counts) for name, group in groups.items()},
        bins100=[g.result(counts) for g in bins100], bins250=[g.result(counts) for g in bins250],
        definitions=dict(scope='on-policy ended training collections, including physical failures; not final frozen-policy evaluation',
            safe='song.safety_invalidated is false; full_safe additionally requires timeline completion',
            failure_causes='overlapping flags; reason counts need not sum to physical failure count',
            curriculum='only full_safe/timeline_complete rows retain raw fractions; failures enter curriculum windows as all-zero rows',
            bins='episode assigned by update in which it ended, including trajectories spanning earlier updates',
            surface_min='mean only for target-episode rows with exposure_time>0; zero with no exposure is excluded; unit meter',
            contact_progress='raw consumed best-contact-streak/tau budget in [0,1], not paid reward; complete=canonical contact_done (best_streak+1e-12>=tau); partial=progress>0 and not complete; floating progress can be infinitesimally below1 on completed notes',
            overlapping_times='geometry/facing/load/wrong-cause times may overlap; do not sum to infer exclusive causes',
            quantiles='exact NumPy linear quantiles of ended-episode integer achieved-note counts'))
    all_group = result['groups']['all']
    require(inspection['verified'] and all_group['ended_episodes']==inspection['completed_episodes'], 'Inspector episode count')
    require(all_group['safe_episodes']==inspection['safe_episodes'], 'Inspector safe count')
    require(math.isclose(all_group['successful_notes']['mean'], inspection['mean_left_success_count'], rel_tol=0, abs_tol=1e-12), 'Inspector mean mismatch')
    require(sum(g['ended_episodes'] for g in result['bins100'])==total and sum(g['ended_episodes'] for g in result['bins250'])==total, 'Bin count mismatch')
    result['inspector_crosscheck'] = dict(passed=True, episodes=total, safe_episodes=all_group['safe_episodes'],
        mean_left_success_count=all_group['successful_notes']['mean'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    phase = args.phase.resolve()
    output = args.out or phase/'analysis/episodes.json'
    result = analyze(phase)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    for name, group in result['groups'].items():
        print(name, json.dumps(dict(n=group['ended_episodes'], safe=group['safe_fraction'],
            mean=group['successful_notes']['mean'], median=group['successful_notes']['median'],
            maximum=group['successful_notes']['maximum'], safe_mean=group['safe_only_successful_notes']['mean'],
            finger_mean=[f['raw_all_ended']['mean_successful_notes'] for f in group['fingers']],
            failures=group['failure_reason_counts'])), flush=True)


if __name__=='__main__':
    main()
