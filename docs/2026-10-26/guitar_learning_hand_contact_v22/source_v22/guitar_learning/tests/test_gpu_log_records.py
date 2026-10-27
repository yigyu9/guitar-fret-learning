"""Canonical log round trips, independent raw checks and failed-write behavior."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from guitar_learning.training.gpu_log_records import (
    EpisodeWriter, CheckpointRecorder, METRICS_SCHEMA, TRANSITION_SCHEMA,
    episode_summary, iter_episode_rows, iter_learning_metrics, iter_gpu_transitions)
from guitar_learning.training.training_log_io import TransitionJournal, TransitionReadError
from guitar_learning.tool.inspect_gpu_training_log import inspect


def episode(env=0, notes=1):
    song = dict(schema='song.v1', role='left', stage_success=False, provisional_success=False,
        left_success_count=notes, right_success_count=0, target_count=2,
        safety_invalidated=False, contact_measurement={'schema': 'contact.v1'}, scope='geometry only')
    return dict(env_id=env, worker_id=env, reason='timeline_complete', valid=True,
        reward=1., cost=0., steps=1, task_time_s=1/60, song=song,
        musical_quality=dict(schema='song.v1', song=copy.deepcopy(song)),
        left_note_ledger=dict(schema='ledger.v1', target_ids=['a', 'b'], required_clean_s=[.1, .2],
            scope='overlapping times', values=dict(clean=[.1, 0.]),
            wrong_press_sources=dict(contract={'schema': 'wrong.v1'}, body_names=['finger'],
                target_strings_1based=[1, 2], values={'wrong_source_time': [[0.], [0.]]})),
        left_finger_motion=dict(schema='motion.v1', joint_names=['MCP'], scope={'hz':60},
            values={'actual_min_rad': [0.1]}))


def line(path, value):
    with path.open('a') as stream:
        stream.write(json.dumps(value, allow_nan=False)+'\n')


class CompactGpuLogTests(unittest.TestCase):
    def test_episode_round_trip_and_metadata_written_once(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            writer = EpisodeWriter(run)
            first, second = episode(), episode(1, 2)
            originals = copy.deepcopy([first, second])
            writer.append(first, 0, 0)
            metadata_before = (run/'episode_metadata.json').read_bytes()
            writer.append(second, 0, 1)
            writer.close()
            self.assertEqual([first, second], originals)
            records = [json.loads(x) for x in (run/'episodes.jsonl').read_text().splitlines()]
            for record in records:
                self.assertNotIn('song', record['episode']['musical_quality'])
                self.assertNotIn('target_ids', record['episode']['left_note_ledger'])
                self.assertNotIn('scope', record['episode']['left_finger_motion'])
            self.assertEqual(metadata_before, (run/'episode_metadata.json').read_bytes())
            self.assertEqual([r['episode'] for r in iter_episode_rows(run)], originals)

    def test_metadata_drift_and_conflicting_song_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            writer = EpisodeWriter(directory)
            writer.append(episode(), 0, 0)
            changed = episode()
            changed['left_note_ledger']['target_ids'][0] = 'other'
            with self.assertRaisesRegex(ValueError, 'metadata changed'):
                writer.append(changed, 1, 0)
            changed = episode()
            changed['musical_quality']['song']['target_count'] = 10
            with self.assertRaisesRegex(ValueError, 'differs'):
                writer.append(changed, 1, 0)
            self.assertEqual(writer.count, 1)
            writer.close()

    def test_metrics_and_transition_refs_restore_details_without_duplicate_ledgers(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            writer = EpisodeWriter(run)
            original = episode()
            ref = writer.append(original, 0, 0)
            writer.close()
            metrics = dict(schema=METRICS_SCHEMA, update_index=0, completed_episode_ids=[0],
                episode_summary=episode_summary([original]))
            line(run/'learning_metrics.jsonl', metrics)
            journal = TransitionJournal(run/'transitions.jsonl.gz')
            journal.write(dict(schema=TRANSITION_SCHEMA, update_index=0, tick_in_update=0,
                reward=[1.], cost=[0.], terminated=[True], truncated=[False], episode_refs=[ref]))
            journal.commit(1)
            journal.close()
            self.assertEqual(list(iter_learning_metrics(run, expand_episodes=False)), [metrics])
            self.assertNotIn('completed_episodes', metrics)
            self.assertNotIn('left_note_ledger', (run/'learning_metrics.jsonl').read_text())
            self.assertEqual(next(iter_learning_metrics(run))['completed_episodes'], [original])
            self.assertEqual(next(iter_gpu_transitions(run))['episodes'], [original])
            self.assertNotIn('episodes', next(iter_gpu_transitions(run, expand_episodes=False)))
            self.assertEqual(journal.stats['sampled'], journal.stats['durable'])
            self.assertEqual(journal.stats['sampled'], journal.stats['committed'])

    def test_empty_episode_run_needs_no_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            writer = EpisodeWriter(run)
            writer.close()
            line(run/'learning_metrics.jsonl', dict(schema=METRICS_SCHEMA,
                update_index=0, completed_episode_ids=[], episode_summary=episode_summary([])))
            self.assertEqual(list(iter_episode_rows(run)), [])
            self.assertEqual(next(iter_learning_metrics(run))['completed_episodes'], [])
            self.assertFalse((run/'episode_metadata.json').exists())

    def test_legacy_records_remain_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            original = episode()
            line(run/'episodes.jsonl', dict(update_index=0, episode=original))
            line(run/'learning_metrics.jsonl', dict(update_index=0, completed_episodes=[original]))
            journal = TransitionJournal(run/'transitions.jsonl.gz')
            journal.write(dict(schema='guitar_learning.gpu_transition.v1', reward=[1.], episodes=[original]))
            journal.close()
            self.assertEqual(next(iter_episode_rows(run))['episode'], original)
            self.assertEqual(list(iter_learning_metrics(run))[0]['completed_episodes'], [original])
            self.assertEqual(next(iter_gpu_transitions(run))['episodes'], [original])

    def test_reader_rejects_torn_tail_missing_refs_or_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            writer = EpisodeWriter(run)
            writer.append(episode(), 0, 0)
            writer.close()
            line(run/'learning_metrics.jsonl', dict(schema=METRICS_SCHEMA,
                update_index=0, completed_episode_ids=[1]))
            with self.assertRaisesRegex(ValueError, 'reference'):
                list(iter_learning_metrics(run))
            (run/'episode_metadata.json').unlink()
            with self.assertRaises(FileNotFoundError):
                list(iter_episode_rows(run))
            with (run/'episodes.jsonl').open('w') as stream:
                stream.write('{"update_index":0}')
            with self.assertRaisesRegex(ValueError, 'Incomplete JSONL'):
                list(iter_episode_rows(run))

    def test_nonsequential_ids_and_uncommitted_tail_are_not_certified(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            writer = EpisodeWriter(run)
            writer.append(episode(), 0, 0)
            writer.close()
            (run/'learning_metrics.jsonl').touch()
            with self.assertRaisesRegex(ValueError, 'absent from committed'):
                list(iter_learning_metrics(run))
            record = json.loads((run/'episodes.jsonl').read_text())
            record['episode_id'] = 2
            (run/'episodes.jsonl').write_text(json.dumps(record)+'\n')
            with self.assertRaisesRegex(ValueError, 'Nonsequential'):
                list(iter_episode_rows(run))

    def test_checkpoint_records_cover_saves_and_exclude_failed_attempts(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            recorder = CheckpointRecorder(run)
            for i, kind in enumerate(('initial', 'periodic', 'final')):
                path = run/(kind+'.pt')
                recorder.record(path, kind, i, lambda p=path: p.write_bytes(b'state'))
            def broken():
                raise OSError('storage failure')
            with self.assertRaises(OSError):
                recorder.record(run/'failed.pt', 'periodic', 4, broken)
            recorder.record(run/'missing.pt', 'recovery', 4, lambda: {'path':None, 'error':'failed'})
            self.assertEqual(recorder.stats['count'], 3)
            self.assertEqual(recorder.stats['bytes'], 15)
            self.assertGreaterEqual(recorder.stats['save_s'], 0.)
            recorder.close()
            entries = [json.loads(x) for x in (run/'checkpoint_manifest.jsonl').read_text().splitlines()]
            self.assertEqual([x['kind'] for x in entries], ['initial', 'periodic', 'final'])

    def test_inspector_crosschecks_raw_arrays_flags_and_checkpoint_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            original = episode()
            writer = EpisodeWriter(run)
            ref = writer.append(original, 0, 0)
            writer.close()
            journal = TransitionJournal(run/'transitions.jsonl.gz')
            journal.write(dict(schema=TRANSITION_SCHEMA, update_index=0, tick_in_update=0,
                reward=[1.], cost=[0.], terminated=[True], truncated=[False], episode_refs=[ref]))
            journal.commit(1)
            journal.close()
            metric = dict(schema=METRICS_SCHEMA, update_index=0, optimizer_updates=1,
                transitions=1, completed_episode_ids=[0], episode_summary=episode_summary([original]),
                mean_reward=1., mean_cost=0.)
            line(run/'learning_metrics.jsonl', metric)
            checkpoints = CheckpointRecorder(run)
            for kind in ('initial', 'final'):
                path = run/(kind+'.pt')
                checkpoints.record(path, kind, int(kind=='final'), lambda p=path: p.write_bytes(b'model'))
            checkpoints.close()
            report = dict(completed=True, failure=None, lifecycle_verified=True,
                changed_inputs=[], missing_import_pins=[], cleanup_errors=[],
                settings=dict(horizon=1, num_envs=1), updates=[dict(update_index=0, optimizer_updates=1)],
                transitions=1, completed_episodes=1, journal=journal.stats, checkpoints=checkpoints.stats)
            (run/'report.json').write_text(json.dumps(report))
            self.assertEqual(inspect(run)['mean_left_success_count'], 1.)
            manifest = run/'checkpoint_manifest.jsonl'
            manifest_bytes = manifest.read_bytes()
            manifest.unlink()
            with self.assertRaisesRegex(ValueError, 'Missing checkpoint manifest'):
                inspect(run)
            manifest.write_bytes(manifest_bytes)
            metric['mean_reward'] = 2.
            (run/'learning_metrics.jsonl').write_text(json.dumps(metric)+'\n')
            with self.assertRaisesRegex(ValueError, 'reward differs'):
                inspect(run)
            metric['mean_reward'] = 1.
            (run/'learning_metrics.jsonl').write_text(json.dumps(metric)+'\n')
            (run/'final.pt').write_bytes(b'wrong')
            with self.assertRaisesRegex(ValueError, 'Checkpoint hash'):
                inspect(run)

    def test_gzip_crc_failure_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            journal = TransitionJournal(run/'transitions.jsonl.gz')
            journal.write(dict(schema=TRANSITION_SCHEMA, update_index=0, reward=[1.], episode_refs=[]))
            journal.close()
            path = run/'transitions.jsonl.gz'
            path.write_bytes(path.read_bytes()[:-3])
            with self.assertRaises(TransitionReadError):
                list(iter_gpu_transitions(run))

class RunnerDurabilityTests(unittest.TestCase):
    def _run(self, directory, interrupted, fail_sync=False):
        """Exercise actual runner ordering with CPU fakes; no native/GPU startup."""
        from types import SimpleNamespace
        from unittest.mock import patch
        import contextlib
        import io
        import torch
        from guitar_learning.training import gpu_runner
        from guitar_learning.training import monitoring, gpu_pool, ppo
        from guitar_learning.skills import specialist_policy
        from guitar_learning.runtime import prepared_reset_v1
        from guitar_learning.native.lower_body_release_v1 import common
        instances = {}

        class CheckedEpisodes(EpisodeWriter):
            def __init__(self, out):
                super().__init__(out)
                instances['episodes'] = self
                self.inject_sync_failure = fail_sync

            def sync(self):
                if self.inject_sync_failure and self.dirty:
                    self.inject_sync_failure = False
                    raise OSError('Injected canonical fsync failure')
                super().sync()

        class CheckedJournal(TransitionJournal):
            def checkpoint(self):
                if self._pending_rows:
                    self.assert_clean()
                return super().checkpoint()

            def assert_clean(self):
                if instances['episodes'].dirty:
                    raise AssertionError('Raw journal sealed before canonical episode fsync')

        class Policy:
            def __init__(self, *args, **kwargs):
                self.log_std = torch.zeros(1)

            def to(self, device):
                return self

        class Trainer:
            def __init__(self, *unused):
                self.updates = 0

            def save(self, path, metadata):
                path.write_bytes(b'state')

            def update(self, buffer, episodes):
                self.updates += 1
                return {}

        scene = SimpleNamespace(physics_steps=0, diagnostics=dict(closed=True, physx_use_gpu=True,
            use_gpu_pipeline=True, simulator_count=1, environment_count=1))
        pool = SimpleNamespace(contract={}, observation={'state':torch.zeros(1, 1)},
            scene=scene, environment=SimpleNamespace(reset_reward_window=lambda:None), close=lambda:None)

        class Collector:
            def __init__(self, *unused):
                pass

            def collect(self, horizon, progress_callback, transition_callback):
                completed = []
                for tick in range(horizon):
                    ended = [episode()] if tick in (0, 59, 60) else []
                    completed.extend(ended)
                    transition_callback(tick, torch.ones(1), torch.zeros(1),
                        torch.tensor([bool(ended)]), torch.tensor([False]), ended)
                    if interrupted and tick == 60:
                        raise RuntimeError('Injected collector interruption')
                return {'reward':torch.ones(horizon, 1), 'cost':torch.zeros(horizon, 1)}, completed

        monitor = SimpleNamespace(start=lambda:None, check=lambda:None, progress=lambda context:None,
            set_phase=lambda *args, **kwargs:None, event=lambda *args, **kwargs:None,
            close=lambda reason:None, minimum_available=10**10)
        settings = dict(device='cuda:0', seed=7, song_training={'bundle':str(Path(directory)/'unused')},
            min_available_memory_gib=0, size='small', specialist={'role':'right'},
            initial_std=.05, ppo={}, updates=1, horizon=64, num_envs=1,
            max_wall_seconds=None, checkpoint_every=250)
        out = Path(directory)/'run'
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict('sys.modules', {'isaacgym':SimpleNamespace()}))
            for target, attr, value in (
                (torch.cuda, 'is_available', lambda:True), (torch.cuda, 'reset_peak_memory_stats', lambda:None),
                (torch.cuda, 'mem_get_info', lambda:(10**10, 10**10)),
                (torch.cuda, 'memory_allocated', lambda:0), (torch.cuda, 'memory_reserved', lambda:0),
                (torch.cuda, 'max_memory_allocated', lambda:0), (torch.cuda, 'max_memory_reserved', lambda:0),
                (torch.cuda, 'empty_cache', lambda:None), (torch.cuda, 'synchronize', lambda:None),
                (torch, 'manual_seed', lambda seed:None), (torch, 'set_num_threads', lambda count:None),
                (monitoring, 'Monitor', lambda *args, **kwargs:monitor),
                (prepared_reset_v1, 'prepared_input_paths', lambda:[]),
                (common, 'pin', lambda *args, **kwargs:{}),
                (gpu_runner, 'project_source_paths', lambda unused:set()),
                (gpu_runner, 'EpisodeWriter', CheckedEpisodes),
                (gpu_pool, 'GpuPool', lambda *args:pool), (gpu_pool, 'TensorCollector', Collector),
                (ppo, 'PPOTrainer', Trainer), (specialist_policy, 'SpecialistPolicy', Policy)):
                stack.enter_context(patch.object(target, attr, value))
            from guitar_learning.training import training_log_io
            stack.enter_context(patch.object(training_log_io, 'TransitionJournal', CheckedJournal))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            if fail_sync:
                with self.assertRaisesRegex(OSError, 'Injected canonical fsync failure'):
                    gpu_runner.run(settings, SimpleNamespace(out=out, resume=None))
            elif interrupted:
                with self.assertRaisesRegex(RuntimeError, 'Injected collector interruption'):
                    gpu_runner.run(settings, SimpleNamespace(out=out, resume=None))
            else:
                gpu_runner.run(settings, SimpleNamespace(out=out, resume=None))
        return out

    def test_auto60_and_committed_episode_refs_are_durable(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self._run(directory, False)
            report = json.loads((run/'report.json').read_text())
            self.assertTrue(report['completed'])
            self.assertEqual(report['checkpoints']['count'], 2)
            self.assertEqual(report['timers']['checkpoint_s'], report['checkpoints']['save_s'])
            self.assertEqual(len(list(run.glob('update_*.json'))), 0)
            metrics = list(iter_learning_metrics(run))
            self.assertEqual(len(metrics[0]['completed_episodes']), 3)
            self.assertTrue(inspect(run)['verified'])

    def test_interrupted_partial_member_syncs_canonical_before_close(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self._run(directory, True)
            report = json.loads((run/'report.json').read_text())
            self.assertFalse(report['completed'])
            self.assertEqual(report['journal']['sampled'], 61)
            self.assertEqual(report['journal']['committed'], 0)
            self.assertEqual(report['journal']['discarded'], 61)
            self.assertEqual(report['journal']['durable'], 61)
            self.assertEqual(report['checkpoints']['count'], 2)
            self.assertEqual(report['checkpoints']['bytes'], 10)
            self.assertEqual(len(list(iter_gpu_transitions(run))), 61)
            self.assertFalse(report['cleanup_errors'])

    def test_episode_sync_failure_prevents_journal_member_and_optimizer_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self._run(directory, False, fail_sync=True)
            report = json.loads((run/'report.json').read_text())
            self.assertFalse(report['completed'])
            self.assertEqual(report['journal']['sampled'], 59)
            self.assertEqual(report['journal']['committed'], 0)
            self.assertEqual(report['journal']['discarded'], 59)
            self.assertEqual(report['optimizer_updates'], 0)
            self.assertEqual(len(list(iter_gpu_transitions(run))), 59)
            self.assertFalse(report['cleanup_errors'])
            with self.assertRaisesRegex(ValueError, 'absent from committed'):
                list(iter_learning_metrics(run))


if __name__ == '__main__':
    unittest.main()
