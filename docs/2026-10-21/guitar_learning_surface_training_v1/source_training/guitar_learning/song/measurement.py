"""Multi-note clean contact measurement with the continuous native detector.

Classification uses full original contact evidence. Returned rows omit repeated
feature dictionaries; IDs/counts retain the evidence provenance, not pressure.
"""
import copy
from guitar_learning.core.task_measurement import TaskMeasurement
from guitar_learning.quality.fretting_quality import classify_fretting


class SongMeasurement(TaskMeasurement):
    def __init__(self, task, human_names, guitar_names, physics_hz=240.,
                 lookahead_s=2., window_s=.5):
        if any(not t.fret for t in task.targets):
            raise ValueError('song v1 explicitly supports all-fretted scores only')
        super().__init__(task, human_names, guitar_names, physics_hz)
        self.fretting_quality = {}

    def _contacts(self, sample):
        evidence, _ = super()._contacts(sample)
        cached, quality = {}, {}
        for target in self.task.targets:
            key = (target.string, target.fret, target.finger)
            if key not in cached:
                classified = classify_fretting(sample['geometry'], target,
                                               evidence[target.target_id], self.contract)
                # All features were classified before this compact projection.
                cached[key] = {name: copy.deepcopy(value) for name, value in classified.items()
                               if name != 'feature_diagnostics'}
                cached[key]['feature_count'] = len(classified['feature_diagnostics'])
            quality[target.target_id] = copy.deepcopy(cached[key])
            original = evidence[target.target_id]
            evidence[target.target_id] = {name: copy.deepcopy(original[name]) for name in
                ('target', 'contract', 'fretting_contact_candidate', 'valid_evidence_ids')}
            evidence[target.target_id].update(contact_feature_count=len(original['contact_evidence']),
                scope='classified full native features; compact IDs/counts, no repeated feature dictionaries')
        self.fretting_quality = quality
        return evidence, {identity for identity, value in quality.items() if value['clean_target_candidate']}

    def _observe(self, sample, initial):
        result = super()._observe(sample, initial)
        result['schema'] = 'guitar_learning.song_measurement.v1'
        result['scope'] = ('all selected fretted targets measured at every native sample; '
            'continuous original StrikeDetector and original50/100ms MusicLedger; '
            'clean contact and marker geometry, not pressure/audio')
        for identity, quality in self.fretting_quality.items():
            result['targets'][identity].update(
                positive_target_candidate=quality['positive_target_candidate'],
                clean_target_candidate=quality['clean_target_candidate'],
                fretting_quality=copy.deepcopy(quality))
        return result
