"""Quality-aware single-note measurement over unchanged native contact queries."""
import copy
from guitar_learning.core.task_measurement import TaskMeasurement
from guitar_learning.quality.fretting_quality import classify_fretting


class TaskMeasurementV2(TaskMeasurement):
    def __init__(self, task, human_names, guitar_names, physics_hz=240.):
        if len(task.targets) != 1 or not task.targets[0].fret:
            raise ValueError('quality measurement supports one fretted target only')
        super().__init__(task,human_names,guitar_names,physics_hz)
        from guitar_learning.quality.strike_quality import StrikeQualityDetector
        self.detector = StrikeQualityDetector(task.targets[0])
        self.fretting_quality = {}

    def _contacts(self, sample):
        evidence, _ = super()._contacts(sample)
        quality = {t.target_id:classify_fretting(sample['geometry'],t,evidence[t.target_id],self.contract)
                   for t in self.task.targets}
        self.fretting_quality = copy.deepcopy(quality)
        return evidence,{identity for identity,q in quality.items() if q['clean_target_candidate']}

    def _observe(self, sample, initial):
        result = super()._observe(sample,initial)
        result['schema'] = 'guitar_learning.task_measurement.v2'
        result['scope'] = 'clean single-target fretting and preparation-filtered geometric strikes; no pressure/audio certification'
        result['fretting_quality'] = copy.deepcopy(self.fretting_quality)
        for identity,quality in self.fretting_quality.items():
            result['targets'][identity].update(
                positive_target_candidate=quality['positive_target_candidate'],
                clean_target_candidate=quality['clean_target_candidate'],
                fretting_quality=copy.deepcopy(quality))
        result['strike_quality'] = copy.deepcopy(self.detector.summary())
        return result
