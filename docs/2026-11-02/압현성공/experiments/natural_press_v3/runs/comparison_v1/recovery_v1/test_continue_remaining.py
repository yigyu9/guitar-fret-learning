"""계속 실행의 고정 범위·실패 격리·원본 보존을 GPU 없이 확인한다."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

spec=importlib.util.spec_from_file_location('continuation',Path(__file__).with_name('continue_remaining.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


def state():
    jobs={key:dict(status='complete') for key in ('seed7_E2_u100_train','seed7_E2_u100_aligned','seed7_E2_u100_free_v9')}
    return dict(status='running',jobs=jobs,results={'seed7_E2_u100':{}},source_seal={},
        recovery=dict(failed_blocks=[],skipped_blocks=[],artifact_errors=[]),current_job=None)


class ContinueTests(unittest.TestCase):
    def test_fixed_remaining_700_and_no_failed_block_retry(self):
        self.assertEqual(len(c.TASKS),7)
        self.assertEqual(sum(100 for _ in c.TASKS),700)
        self.assertNotIn(('E1',7,200),c.TASKS)
        self.assertEqual(c.TASKS[0],('E2',7,200))

    def test_failed_100_skips_200_and_independent_conditions_continue(self):
        current=state();calls=[];events=[]
        def block(active,condition,seed,total):
            calls.append((condition,seed,total));name=c.label(condition,seed,total)
            if condition=='E1' and total==100:
                active['current_job']=dict(operation='train',status='failed');events.append('failed')
                raise RuntimeError('KLGuard')
            active['results'][name]={}
            for kind in ('train','aligned','free_v9'):active['jobs'][name+'_'+kind]=dict(status='complete')
        study=SimpleNamespace(block=block,progress=Mock(),timestamp=lambda:'now')
        with patch.object(c,'verify',side_effect=lambda *args:events.append('verify')),patch.object(c,'finish_child',side_effect=lambda *args:events.append('finish')),patch.object(c,'results'):
            c.run_remaining(study,current)
        self.assertEqual(len(calls),6);self.assertNotIn(('E1',17,200),calls)
        self.assertIn(('E2',17,200),calls)
        self.assertEqual(current['recovery']['failed_blocks'][0]['label'],'seed17_E1_u100')
        self.assertFalse(current['recovery']['failed_blocks'][0]['model_success'])
        self.assertEqual(current['recovery']['skipped_blocks'][0]['label'],'seed17_E1_u200')
        at=events.index('failed');self.assertEqual(events[at+1:at+3],['finish','verify'])

    def test_source_change_after_failure_stops_entire_continuation(self):
        current=state()
        def block(active,*args):
            active['current_job']=dict(operation='train',status='failed');raise RuntimeError('block failed')
        study=SimpleNamespace(block=Mock(side_effect=block),progress=Mock(),timestamp=lambda:'now')
        with patch.object(c,'verify',side_effect=[None,RuntimeError('source changed')]),patch.object(c,'finish_child') as finish,patch.object(c,'results'):
            with self.assertRaisesRegex(RuntimeError,'source changed'):c.run_remaining(study,current)
        self.assertEqual(study.block.call_count,1);finish.assert_called_once()
        self.assertEqual(current['recovery']['failed_blocks'],[])

    def test_analysis_failure_is_not_completed_model_or_global_stop(self):
        current=state();name='seed7_E2_u200'
        def block(active,*args):
            for kind in ('train','aligned','free_v9'):active['jobs'][name+'_'+kind]=dict(status='complete',operation=kind)
            raise ValueError('원시 관측 분석 실패')
        study=SimpleNamespace(block=block,progress=Mock(),timestamp=lambda:'now')
        with patch.object(c,'TASKS',(('E2',7,200),)),patch.object(c,'verify'),patch.object(c,'finish_child'),patch.object(c,'results'):
            c.run_remaining(study,current)
        self.assertNotIn(name,current['results'])
        self.assertEqual(current['recovery']['failed_blocks'][0]['operation'],'analysis')
        self.assertTrue(all(current['jobs'][name+'_'+kind]['status']=='complete' for kind in ('train','aligned','free_v9')))

    def test_before_backups_and_reporting_preserve_original_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);original=root/'original';recovery=root/'recovery';original.mkdir();recovery.mkdir()
            for name in ('progress.json','진행상황.md','RESULTS.md'):(original/name).write_text('original '+name)
            (original/'summary.json').write_text('original summary')
            def write(path,value):Path(path).write_text(json.dumps(value))
            import hashlib
            digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
            def progress(active):
                active.update(estimated_finish_earliest='future',estimated_finish_latest='future')
                write(original/'progress.json',active)
                (original/'진행상황.md').write_text('- 예상 종료: future\n')
            study=SimpleNamespace(write=write,progress=progress,digest=digest)
            with patch.object(c,'HERE',recovery),patch.object(c,'ORIGINAL',original):
                c.save_before(study);before=digest(recovery/'before_RESULTS.md');c.save_before(study)
                self.assertEqual(before,digest(recovery/'before_RESULTS.md'))
                active=state();active.update(status='finished_with_failed_blocks',finished_at='actual-finish')
                active['recovery']['skipped_blocks']=[dict(label=c.label(*task)) for task in c.TASKS]
                c.install_reporting(study,active)
                study.write(original/'summary.json',{'new':'result'})
                study.progress(active)
                self.assertEqual((original/'summary.json').read_text(),'original summary')
                self.assertEqual((original/'RESULTS.md').read_text(),'original RESULTS.md')
                self.assertEqual(json.loads((recovery/'summary.json').read_text()),{'new':'result'})
                saved=json.loads((original/'progress.json').read_text())
                self.assertEqual(saved['status'],'finished_with_failed_blocks')
                self.assertEqual(saved['estimated_finish_latest'],'actual-finish')

    def test_completed_block_evidence_is_checked_without_rewriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'evidence';path.write_text('original')
            import hashlib
            digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
            current=state();name='seed7_E2_u200';current['results'][name]={}
            for kind in ('train','aligned','free_v9'):
                current['jobs'][name+'_'+kind]=dict(status='complete',report=str(path),report_sha256=digest(path),evidence_sha256={str(path):digest(path)})
            study=SimpleNamespace(digest=digest,block=Mock())
            with patch.object(c,'TASKS',(('E2',7,200),)),patch.object(c,'verify'):
                c.run_remaining(study,current)
                study.block.assert_not_called()
                path.write_text('changed')
                with self.assertRaisesRegex(RuntimeError,'보고서 변경'):c.run_remaining(study,current)

    def test_child_is_reaped_and_busy_gpu_blocks_continuation(self):
        child=Mock();child.pid=12345
        child.poll.side_effect=[None,None,0,0]
        child.wait.side_effect=[subprocess.TimeoutExpired('child',30),0,0]
        study=SimpleNamespace(CHILD=child)
        with patch.object(c.os,'killpg') as kill,patch.object(c.subprocess,'check_output',return_value=''):
            c.finish_child(study)
        self.assertIsNone(study.CHILD);self.assertEqual(kill.call_count,2)
        with patch.object(c.subprocess,'check_output',return_value='9876'):
            with self.assertRaisesRegex(RuntimeError,'GPU 프로세스'):c.finish_child(study)


if __name__=='__main__':unittest.main()
