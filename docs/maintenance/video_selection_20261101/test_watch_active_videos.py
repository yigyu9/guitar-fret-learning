"""실제 GPU 없이 완료·실패·경로·SHA 정리 계약을 확인한다."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('watch', Path(__file__).with_name('watch_active_videos.py'))
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.public = self.base/'동영상'
        self.public.mkdir()
        self.state = dict(status='complete', videos=[], jobs={}, results={})
        for seed in (7, 17):
            for kind in ('best', 'last'):
                label = f's{seed}_t100_{kind}_render'
                folder = self.base/'learning_v1/jobs'/label
                folder.mkdir(parents=True)
                cp = folder/'model.pt'
                cp.write_bytes(label.encode())
                report = dict(completed=True, lifecycle_verified=True, policy_unchanged=True,
                              source_checkpoint_pins_validated=True, checkpoint=str(cp), checkpoint_sha256=watch.sha(cp))
                write(folder/'report.json', report)
                # seed17 last는 평가 수치가 더 좋아도 영상 자체는 실패.
                success = not (seed == 17 and kind == 'last')
                episode = dict(valid=True, termination=dict(physical_failure=False, wrist_failure=False),
                               left_note_ledger=dict(values=dict(left=[success, success], clean=[1.5, 1.5])))
                write(folder/'episode_env0000.json', episode)
                report['episode'] = episode
                write(folder/'report.json', report)
                evidence = {str(folder/'report.json'): watch.sha(folder/'report.json')}
                self.state['jobs'][label] = dict(status='complete', operation='render', out=str(folder), evidence=evidence)
                for tag in ('final', 'repeat'):
                    score = 127 if not success else (100 if seed == 17 else 50)
                    self.state['results'][label+tag] = dict(checkpoint=str(cp), mode='mean', tag=kind+'_'+tag,
                                                          metrics=dict(episodes=128, full_duration_pair=score, AB=score, on_time_with_previous_tail=score))
                for view in ('hand', 'fullbody'):
                    source = folder/(view+'.mp4')
                    source.write_bytes((label+view).encode())
                    evidence[str(source)] = watch.sha(source)
                    target = self.public/f'middle_seed{seed}_{kind}_{view}.mp4'
                    target.write_bytes(source.read_bytes())
                    self.state['videos'].append(dict(path=str(target), checkpoint=str(cp), sha256=watch.sha(target)))
        write(self.base/'pipeline_v2.json', dict(status='complete'))
        write(self.base/'learning_v1/SOURCE_VERIFICATION.json', dict(unchanged=True))
        self.save()

    def save(self):
        write(self.base/'learning_v1/progress.json', self.state)

    def test_completed_keeps_successful_best_pair_originals_unchanged(self):
        originals = {p: watch.sha(p) for p in (self.base/'learning_v1').rglob('*') if p.is_file()}
        result = watch.cleanup(self.base)
        self.assertEqual(len(result['kept']), 2)
        self.assertEqual(len(result['removed']), 6)
        self.assertEqual(result['selected']['label'], 's17_t100_best_render')
        self.assertEqual({p: watch.sha(p) for p in originals}, originals)

    def test_failed_training_preserves_all(self):
        self.state['status'] = 'failed'
        self.save()
        with self.assertRaises(RuntimeError):
            watch.cleanup(self.base)
        self.assertEqual(len(list(self.public.iterdir())), 8)

    def test_running_preserves_all(self):
        self.state['status'] = 'running'
        self.save()
        self.assertIsNone(watch.cleanup(self.base))
        self.assertEqual(len(list(self.public.iterdir())), 8)

    def test_path_escape_rejected(self):
        self.state['videos'][0]['path'] = str(self.base/'learning_v1/progress.json')
        self.save()
        with self.assertRaises(ValueError):
            watch.cleanup(self.base)
        self.assertEqual(len(list(self.public.iterdir())), 8)

    def test_tampered_video_rejected(self):
        Path(self.state['videos'][0]['path']).write_bytes(b'tamper')
        with self.assertRaises(ValueError):
            watch.cleanup(self.base)
        self.assertEqual(len(list(self.public.iterdir())), 8)

    def test_empty_evidence_rejected(self):
        next(iter(self.state['jobs'].values()))['evidence'] = {}
        self.save()
        with self.assertRaises(ValueError):
            watch.cleanup(self.base)
        self.assertEqual(len(list(self.public.iterdir())), 8)

    def test_missing_report_evidence_rejected(self):
        job = next(iter(self.state['jobs'].values()))
        del job['evidence'][str(Path(job['out'])/'report.json')]
        self.save()
        with self.assertRaises(ValueError):
            watch.cleanup(self.base)
        self.assertEqual(len(list(self.public.iterdir())), 8)

    def test_missing_video_evidence_rejected(self):
        job = next(iter(self.state['jobs'].values()))
        del job['evidence'][str(Path(job['out'])/'hand.mp4')]
        self.save()
        with self.assertRaises(ValueError):
            watch.cleanup(self.base)
        self.assertEqual(len(list(self.public.iterdir())), 8)

    def test_source_check_failure_preserves(self):
        write(self.base/'learning_v1/SOURCE_VERIFICATION.json', dict(unchanged=False))
        with self.assertRaises(ValueError):
            watch.cleanup(self.base)
        self.assertEqual(len(list(self.public.iterdir())), 8)

    def test_public_directory_symlink_rejected(self):
        external = self.base/'external_public'
        self.public.rename(external)
        self.public.symlink_to(external, target_is_directory=True)
        with self.assertRaises(ValueError):
            watch.cleanup(self.base)
        self.assertEqual(len(list(external.iterdir())), 8)

    def test_episode_report_mismatch_rejected(self):
        job = next(iter(self.state['jobs'].values()))
        path = Path(job['out'])/'episode_env0000.json'
        data = watch.read(path)
        data['left_note_ledger']['values']['left'] = [False, False]
        write(path, data)
        with self.assertRaises(ValueError):
            watch.cleanup(self.base)
        self.assertEqual(len(list(self.public.iterdir())), 8)

    def test_all_failed_marked_diagnostic(self):
        for job in self.state['jobs'].values():
            path = Path(job['out'])/'episode_env0000.json'
            data = watch.read(path)
            data['left_note_ledger']['values']['left'] = [False, False]
            write(path, data)
            report_path = Path(job['out'])/'report.json'
            report = watch.read(report_path)
            report['episode'] = data
            write(report_path, report)
            job['evidence'][str(report_path)] = watch.sha(report_path)
        self.save()
        result = watch.cleanup(self.base)
        self.assertIn('실패 진단', result['classification'])
        self.assertFalse(result['selected']['quality']['success'])


if __name__ == '__main__':
    unittest.main()
