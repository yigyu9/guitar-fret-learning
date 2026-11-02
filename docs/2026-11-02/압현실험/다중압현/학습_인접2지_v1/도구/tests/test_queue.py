"""Resource exclusion and separate scientific denominator checks; CPU only."""
import importlib.util
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location('study_queue', TOOLS/'study_queue.py')
queue = importlib.util.module_from_spec(spec); spec.loader.exec_module(queue)


class ResourceTests(unittest.TestCase):
    def ready(self):
        state = dict(schema='guitar_learning.range336.state.v1', completed=True, status='complete',
            total=336, finished=336, remaining=0, results={str(i): dict(status='done') for i in range(336)})
        gpu = [dict(uuid=queue.GPU_UUID, **{'memory.free [MiB]': '10000'})]
        return state, gpu, []

    def test_incomplete_sweep_blocks_even_if_gpu_empty(self):
        state, gpu, compute = self.ready(); state['completed'] = False
        self.assertEqual(queue.gate(state, gpu, compute), (False, 'waiting_for_single_sweep'))

    def test_finished_count_cannot_replace_full_ledger(self):
        state, gpu, compute = self.ready(); state['results'].pop('1')
        self.assertFalse(queue.gate(state, gpu, compute)[0])

    def test_leftover_compute_process_blocks_completed_sweep(self):
        state, gpu, _ = self.ready()
        self.assertEqual(queue.gate(state, gpu, [dict(gpu_uuid=queue.GPU_UUID)]),
                         (False, 'waiting_for_gpu_process_exit'))

    def test_other_uuid_or_low_memory_never_launches(self):
        state, gpu, compute = self.ready(); gpu[0]['uuid'] = 'different'
        self.assertFalse(queue.gate(state, gpu, compute)[0])
        state, gpu, compute = self.ready(); gpu[0]['memory.free [MiB]'] = '1024'
        self.assertFalse(queue.gate(state, gpu, compute)[0])

    def test_complete_empty_verified_gpu_is_ready(self):
        self.assertEqual(queue.gate(*self.ready()), (True, 'ready'))


class CheckpointIdentityTests(unittest.TestCase):
    def records(self):
        out = queue.STUDY/'로그/identity_fixture'
        bundle = queue.STUDY/'입력/song_bundles/index_middle_same'
        train = dict(mode='train', case_id='a', job_id='a_train', out=str(out))
        job = dict(case_id='a', bundle=str(bundle), checkpoint=str(out/'J/final.pt'), train_job_id='a_train')
        report = dict(job_id='a_train', case_id='a', completed=True,
                      checkpoint=str(out/'J/final.pt'), checkpoint_sha256='expected')
        metadata = dict(settings=dict(experiment=dict(schema='multi_press.adjacent_pair_training.v1',
            case_id='a', target_ids=['x', 'y'], common_window_s=[3.3, 4.8]),
            song_training=dict(bundle=str(bundle))))
        return metadata, job, ['x', 'y'], train, report, 'expected'

    def test_matching_preceding_training_checkpoint(self):
        from run_job import verify_eval_identity
        verify_eval_identity(*self.records())

    def test_other_case_bundle_target_or_checkpoint_is_rejected(self):
        from run_job import verify_eval_identity
        for kind in ('case', 'bundle', 'target', 'sha', 'parent'):
            values = self.records(); meta, job, _, _, report, _ = values
            if kind == 'case': meta['settings']['experiment']['case_id'] = 'other'
            if kind == 'bundle': meta['settings']['song_training']['bundle'] += '_other'
            if kind == 'target': meta['settings']['experiment']['target_ids'] = ['x', 'wrong']
            if kind == 'sha': report['checkpoint_sha256'] = 'different'
            if kind == 'parent': report['job_id'] = 'other_train'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                verify_eval_identity(*values)


if __name__ == '__main__':
    unittest.main()
