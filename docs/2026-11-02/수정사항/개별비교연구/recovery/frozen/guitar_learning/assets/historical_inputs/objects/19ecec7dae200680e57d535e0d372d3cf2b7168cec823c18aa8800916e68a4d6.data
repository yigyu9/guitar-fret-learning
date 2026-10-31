import json
from pathlib import Path
import tempfile
import unittest

from tab2body.tools.summarize_fret_evaluations import summarize


class EvaluationSummaryTests(unittest.TestCase):
    def test_completion_and_protocol_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, completed, f1, seed in (
                ('a', True, .3, 42), ('b', True, .2, 42),
                ('c', False, .9, 42), ('d', True, .8, 43),
            ):
                data = dict(checkpoint=name, goal_finished=completed,
                            evaluation_seed=seed,
                            episode_metrics=dict(f1_l=f1, sustain_event_success_rate=.1,
                                                 wrong_press_rate=0.))
                (Path(directory) / (name + '.events.json')).write_text(json.dumps(data))
            groups = summarize(directory)['groups']
            self.assertEqual(len(groups), 2)
            self.assertEqual(groups[0]['best_completed']['checkpoint'], 'a')

    def test_missing_metrics_are_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'a.events.json').write_text('{}')
            self.assertEqual(summarize(directory)['groups'], [])

    def test_different_evaluation_contracts_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            for contract in ('old', 'new'):
                data = dict(checkpoint=contract, goal_finished=True,
                            evaluation_contract_sha256=contract,
                            episode_metrics=dict(f1_l=.5, sustain_event_success_rate=.2,
                                                 wrong_press_rate=0.))
                (Path(directory) / (contract + '.events.json')).write_text(json.dumps(data))
            self.assertEqual(len(summarize(directory)['groups']), 2)

    def test_suffix_is_not_ranked_with_full_song(self):
        with tempfile.TemporaryDirectory() as directory:
            for frame in (0, 499):
                data = dict(checkpoint=str(frame), goal_finished=True,
                            start_frame=frame,
                            episode_metrics=dict(f1_l=.5, sustain_event_success_rate=.2,
                                                 wrong_press_rate=0.))
                (Path(directory) / (str(frame) + '.events.json')).write_text(json.dumps(data))
            self.assertEqual(len(summarize(directory)['groups']), 2)

    def test_cached_action_is_a_separate_protocol(self):
        with tempfile.TemporaryDirectory() as directory:
            for enabled in (False, True):
                data = dict(checkpoint=str(enabled), goal_finished=True,
                            cached_preparation_action=enabled,
                            episode_metrics=dict(f1_l=.5, sustain_event_success_rate=.2,
                                                 wrong_press_rate=0.))
                (Path(directory) / (str(enabled) + '.events.json')).write_text(json.dumps(data))
            self.assertEqual(len(summarize(directory)['groups']), 2)


if __name__ == '__main__':
    unittest.main()
