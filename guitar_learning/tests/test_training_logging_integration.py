"""Logging-only integration: detail, terminal semantics and interrupted reports."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from guitar_learning.training.training_log_io import format_info, classification_signature
from guitar_learning.training.training_log_io import run_evidence, finalize_summary
from guitar_learning.training.training_log_io import TransitionJournal
from guitar_learning.tool.recover_training_log import recover


class LoggingIntegrationTests(unittest.TestCase):
    def test_standard_reduction_preserves_environment_and_terminal_quality(self):
        quality=dict(role='left',stage_success=False,release_late_s=2.5,
            fretting_state=dict(status='correct',feature_diagnostics=[{'evidence_id':'1:2'}]),
            strike=dict(target_id='note',preparation={'explanation':'static'}))
        info=dict(timing=dict(config={'stage_index':1},stage_success=False),
            specialist=dict(role='left',timing={'stage_success':False},skill={'config':{'stage':1}}),
            musical_quality=quality,debug={'action':[.1]*39},resource={'pid':123})
        original=copy.deepcopy(info)
        reduced=format_info(info,np.r_[np.ones(33)*.1,np.zeros(6)])
        self.assertEqual(info,original)
        self.assertNotIn('debug',reduced)
        self.assertNotIn('config',reduced['timing'])
        self.assertEqual(reduced['specialist']['timing_ref'],'timing')
        self.assertNotIn('feature_diagnostics',reduced['musical_quality']['fretting_state'])
        self.assertEqual(reduced['action_summary']['active_channels'],33)
        self.assertTrue(reduced['action_summary']['active_nonzero'])
        info['episode']={'musical_quality':quality}
        terminal=format_info(info,np.zeros(39))
        self.assertEqual(terminal['musical_quality'],quality)
        diagnostic=format_info(original,np.zeros(39),detail='diagnostic')
        self.assertEqual(diagnostic['debug'],original['debug'])

    def test_stream_reports_filter_incomplete_and_do_not_scan_transition_gzip(self):
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)
            data=dict(accounting={'logged_transitions':4},reward_terms={'quality_release':0.},
                preparation={'first2s_logged_transitions':4},last_quality_by_worker={},open_episodes=[{'ticks':4}])
            (out/'training_summary.json').write_text(json.dumps(data))
            with (out/'episodes.jsonl').open('w') as stream:
                stream.write(json.dumps(dict(episode={'reason':'timeline_complete'},metrics={}))+'\n')
                stream.write(json.dumps(dict(episode=None,metrics={'complete':False}))+'\n')
            evidence=run_evidence(out)
            self.assertEqual(evidence['episodes'],[{'reason':'timeline_complete'}])
            self.assertEqual(evidence['logged_transitions'],4)
            self.assertEqual(evidence['evidence_source'],'streaming_summary_and_episode_records')

    def test_standard_stream_reports_use_counters_without_loading_episode_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)
            data=dict(logging_detail='standard',accounting={'logged_transitions':100},reward_terms={},
                preparation={},last_quality_by_worker={},open_episodes=[],
                episode_records={'path':'reference'},completed_episodes=3)
            (out/'training_summary.json').write_text(json.dumps(data))
            (out/'episodes.jsonl').write_text('deliberately not parsed in standard summary')
            evidence=run_evidence(out)
            self.assertEqual(evidence['episodes'],[])
            self.assertEqual(evidence['episode_stats']['completed_episodes'],3)

    def test_right_raw_selection_tracks_active_strike_changes(self):
        info=dict(musical_quality=dict(role='right',fretting_state={'status':'correct'},
            strike={'extra_count':0,'recovered':False}))
        before=classification_signature(info)
        info['musical_quality']['fretting_state']['status']='wrong'
        self.assertEqual(before,classification_signature(info))
        info['musical_quality']['strike']['extra_count']=1
        self.assertNotEqual(before,classification_signature(info))

    def test_secondary_summary_error_does_not_replace_primary_exception(self):
        with tempfile.TemporaryDirectory() as temporary:
            def broken(out):raise OSError('fake full disk')
            with self.assertRaisesRegex(KeyboardInterrupt,'primary'):
                try:raise KeyboardInterrupt('primary')
                finally:finalize_summary(temporary,broken,'quality')
            detail=json.loads((Path(temporary)/'quality_summary_error.json').read_text())
            self.assertEqual(detail['primary_exception'],'KeyboardInterrupt')

    def test_recovery_writes_new_prefix_summary_and_never_infers_ppo_commit(self):
        with tempfile.TemporaryDirectory() as temporary:
            run=Path(temporary)/'run';run.mkdir()
            path=run/'transitions.jsonl.gz'
            journal=TransitionJournal(path)
            for tick in range(61):
                journal.write(dict(reward=[0.],terminated=[False],truncated=[False],
                    infos=[dict(task_time_s=(tick+1)/60.,cost=0.,reward_terms={})]))
            journal.close()
            path.write_bytes(path.read_bytes()[:-4])
            before=path.read_bytes()
            result=recover(run,Path(temporary)/'recovered')
            self.assertEqual(result['recovery']['valid_prefix_rows'],60)
            self.assertFalse(result['recovery']['complete'])
            self.assertEqual(result['measured_prefix']['transitions'],60)
            self.assertIsNone(result['original_run_accounting'])
            self.assertEqual(path.read_bytes(),before)
            with self.assertRaises(FileExistsError):recover(run,Path(temporary)/'recovered')


if __name__=='__main__':unittest.main()
