"""Resource safeguards use fake probes; never create actual host pressure."""
import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from guitar_learning.training.monitoring import Monitor, LowMemoryError, process_memory, available_memory_bytes, save_failure_checkpoint, stopped_reason


class MonitoringTests(unittest.TestCase):
    def make_monitor(self,out,memory=lambda:8*1024**3,**kwargs):
        return Monitor(out,memory_probe=memory,process_probe=lambda pid:dict(pid=pid,rss_current_bytes=123,
            pss_current_bytes=100,rss_peak_bytes=456),console=io.StringIO(),**kwargs)

    def test_flushed_wait_progress_resources_and_atomic_status(self):
        with tempfile.TemporaryDirectory() as out:
            monitor=self.make_monitor(out)
            monitor.start()
            monitor.set_phase('collecting',update_index=2,ticks=0,horizon=128)
            monitor.wait(dict(operation='step',pending_workers=[1],worker_status=[dict(worker_id=1,pid=42,alive=True,exitcode=None)]))
            monitor.progress(dict(ticks=7,horizon=128))
            monitor.sample(force=True)
            current=json.loads((Path(out)/'status.json').read_text())
            self.assertEqual(current['pending_workers'],[1])
            self.assertEqual(current['ticks'],7)
            self.assertEqual(current['workers'][0]['memory']['rss_current_bytes'],123)
            self.assertEqual(current['workers'][0]['memory']['rss_peak_bytes'],456)
            self.assertTrue((Path(out)/'resources.jsonl').read_text().endswith('\n'))
            monitor.close('updates_complete')
            self.assertEqual(json.loads((Path(out)/'status.json').read_text())['stopped'],'updates_complete')
            self.assertFalse((Path(out)/'status.json.tmp').exists())

    def test_low_memory_wait_aborts_without_real_pressure(self):
        state=[8*1024**3]
        with tempfile.TemporaryDirectory() as out:
            monitor=self.make_monitor(out,memory=lambda:state[0],resource_interval_seconds=.001)
            monitor.start()
            state[0]=3*1024**3
            time.sleep(.003)
            with self.assertRaises(LowMemoryError):
                monitor.wait(dict(operation='reset',pending_workers=[0]))
            monitor.close('memory_guard')
            events=[json.loads(line) for line in (Path(out)/'events.jsonl').read_text().splitlines()]
            self.assertEqual(sum(row['event']=='low_memory' for row in events),1)
            self.assertEqual(events[-1]['reason'],'memory_guard')

    def test_background_heartbeat_and_guard_during_quiet_work(self):
        state=[8*1024**3]
        with tempfile.TemporaryDirectory() as out:
            monitor=self.make_monitor(out,memory=lambda:state[0],heartbeat_seconds=.01,resource_interval_seconds=.01)
            monitor.start()
            state[0]=2*1024**3
            deadline=time.monotonic()+1
            while monitor.low_memory is None and time.monotonic()<deadline:time.sleep(.01)
            self.assertIsNotNone(monitor.low_memory)
            with self.assertRaises(LowMemoryError):monitor.check()
            self.assertIn('[training]',monitor.console.getvalue())
            monitor.close('memory_guard')

    def test_probe_failure_is_visible_and_stops_guarded_work(self):
        def fail():raise OSError('fake unavailable proc')
        with tempfile.TemporaryDirectory() as out:
            monitor=self.make_monitor(out,memory=fail)
            with self.assertRaisesRegex(RuntimeError,'resource monitor failed'):monitor.start()
            monitor.close('error')

    def test_failure_save_and_save_failure_do_not_replace_original_error(self):
        class Trainer:
            def save(self,path,metadata):Path(path).write_text(json.dumps(metadata))
        class Broken:
            def save(self,path,metadata):raise OSError('fake disk full')
        with tempfile.TemporaryDirectory() as out:
            saved=save_failure_checkpoint(Trainer(),out,dict(stopped='memory_guard'))
            self.assertTrue(Path(saved['path']).exists())
            result=save_failure_checkpoint(Broken(),out,{})
            self.assertEqual(result['error']['type'],'OSError')
            self.assertIsNone(result['path'])
            self.assertEqual(save_failure_checkpoint(None,out,{})['reason'],'trainer_not_created')

    def test_strict_resume_failure_cannot_create_recovery_checkpoint(self):
        import hashlib
        from guitar_learning.training.ppo import PPOTrainer
        from guitar_learning.tests.test_policy import policy
        with tempfile.TemporaryDirectory() as out:
            source=Path(out)/'legacy.pt'
            PPOTrainer(policy()).save(source)
            source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
            dense=policy()
            dense.architecture['contract']['reward']={'mode':'dense_v2'}
            trainer=PPOTrainer(dense)
            eligible=False
            try:
                trainer.load(source)
                eligible=True
            except ValueError:
                pass
            self.assertFalse(eligible)
            recovery=save_failure_checkpoint(trainer,out,{},eligible=eligible)
            self.assertEqual(recovery['reason'],'resume_not_validated')
            self.assertIsNone(recovery['path'])
            self.assertFalse((Path(out)/'failure_last_valid.pt').exists())
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),source_hash)

    def test_successful_strict_resume_enables_recovery_checkpoint(self):
        from guitar_learning.training.ppo import PPOTrainer
        from guitar_learning.tests.test_policy import policy
        with tempfile.TemporaryDirectory() as out:
            source=Path(out)/'initial.pt'
            PPOTrainer(policy()).save(source)
            trainer=PPOTrainer(policy())
            eligible=False
            trainer.load(source)
            eligible=True
            recovery=save_failure_checkpoint(trainer,out,{},eligible=eligible)
            self.assertIsNotNone(recovery['path'])
            PPOTrainer(policy()).load(recovery['path'])

    def test_reason_classification(self):
        for error,reason in ((LowMemoryError(),'memory_guard'),(TimeoutError(),'worker_timeout'),
            (KeyboardInterrupt(),'interrupted'),(RuntimeError('worker failed: 2'),'worker_failed'),
            (ValueError('wrong shape'),'error')):
            self.assertEqual(stopped_reason(error),reason)

    def test_real_proc_fields_are_separate(self):
        import os
        self.assertGreater(available_memory_bytes(),0)
        row=process_memory(os.getpid())
        self.assertGreater(row['rss_current_bytes'],0)
        self.assertGreaterEqual(row['rss_peak_bytes'],row['rss_current_bytes'])
        self.assertIsNone(process_memory(999999999)['rss_current_bytes'])
