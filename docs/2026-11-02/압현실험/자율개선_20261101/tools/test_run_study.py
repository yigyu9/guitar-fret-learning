"""미완료·비유한·입력 이상을 정상 독립 조건처럼 처리하지 않는지 확인한다."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('autonomous_study',Path(__file__).with_name('run_study.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class FailureClassification(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.out=Path(self.temp.name);self.folder=self.out/'job';(self.folder/'J').mkdir(parents=True)
        self.phase=dict(failure=dict(type='KLGuardError'),lifecycle_verified=True,
                        changed_inputs=[],missing_import_pins=[],cleanup_errors=[],optimizer_updates=12)
        self.outer=dict(failure=dict(type='KLGuardError'),changed_inputs=[],missing_import_pins=[],cleanup_errors=[])
        self.diagnostic=dict(finite=True,diagnostic=dict(attempted_kl=.021,target_kl=.02))
        self.state=dict(jobs={'x':dict(out=str(self.folder))},source_seal={},interpretations=[])

    def check(self):
        for name,data in [('J/report.json',self.phase),('report.json',self.outer),('kl_failure.json',self.diagnostic)]:
            (self.folder/name).write_text(json.dumps(data))
        return module.protected_kl(self.state,self.out,'x')

    def test_clean_finite_guard_is_preserved(self):
        self.assertTrue(self.check());self.assertEqual(len(self.state['protected_failures']),1)
        self.assertIn('report_sha256',self.state['protected_failures'][0])

    def test_nonfinite_guard_is_fatal(self):
        self.diagnostic['finite']=False;self.assertFalse(self.check())

    def test_missing_pins_is_fatal(self):
        self.phase['missing_import_pins']=['bad'];self.assertFalse(self.check())

    def test_cleanup_error_is_fatal(self):
        self.phase['cleanup_errors']=['bad'];self.assertFalse(self.check())

    def test_other_failure_is_fatal(self):
        self.phase['failure']['type']='FloatingPointError';self.assertFalse(self.check())

    def test_failed_preceding_study_does_not_start_gpu(self):
        path=self.out/'previous.json';path.write_text(json.dumps(dict(status='failed')))
        state=dict(jobs={},results={},interpretations=[],budget_end='test',status='initializing',source_seal={})
        proof=self.out/'validation/preflight.json';proof.parent.mkdir();proof.write_text(json.dumps(dict(completed=True,source_unchanged=True,preceding_driver_resumed=True,operations=[dict(exit_code=0,completed=True)]*7)))
        with patch.object(module,'BASE',self.out),patch.object(module,'CONTINUATION',path),patch.object(module.subprocess,'check_output') as gpu:
            with self.assertRaisesRegex(RuntimeError,'선행 비교 미완료'):module.wait_for_original(state,self.out)
            gpu.assert_not_called()


class ResultSummary(unittest.TestCase):
    def test_actual_metrics_can_be_summarized_and_failure_blocks_adoption(self):
        fixture=module.ORIGINAL/'analysis/review_20261101/seed7_u800_mean128/analysis.json'
        metrics=json.loads(fixture.read_text())
        with tempfile.TemporaryDirectory() as temp:
            state=dict(jobs={},results={},interpretations=[],protected_failures=[{'label':'failed'}])
            for variant in ('control','conservative'):
                for seed in (7,17):
                    key=f'{variant}_{seed}'
                    state['results'][key]=dict(condition=variant,seed=seed,total=100,mode='mean',checkpoint='checkpoint.pt',metrics=metrics)
            summary=module.summarize(state,Path(temp))
            self.assertEqual(len(summary['final']),4)
            self.assertFalse(summary['complete_two_seed_pairs'])
            self.assertFalse(summary['conservative_meets_90pct_all_three'])
            self.assertTrue((Path(temp)/'comparison.png').is_file())
            self.assertTrue((Path(temp)/'learning_diagnostics.json').is_file())


    def test_balanced_four_arm_schedule_completes_summary(self):
        fixture=module.ORIGINAL/'analysis/review_20261101/seed7_u800_mean128/analysis.json'
        metrics=json.loads(fixture.read_text());calls=[]
        def fake_train(state,out,variant,seed,total,previous,previous_total):
            calls.append((variant,seed,total,total-previous_total))
            return out/f'{variant}_{seed}_{total}.pt'
        def fake_evaluate(state,out,variant,seed,total,checkpoint,mode='mean',count=32):
            row=dict(condition=variant,seed=seed,total=total,checkpoint=str(checkpoint),mode=mode,metrics=dict(metrics,episodes=count))
            state['results'][f'{variant}_{seed}_{total}_{mode}_{count}']=row
            return row['metrics']
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'new'
            with patch.object(module,'wait_for_original'),patch.object(module,'train_block',side_effect=fake_train),patch.object(module,'evaluate',side_effect=fake_evaluate),patch.object(module,'render_selected',return_value=[]),patch.object(module.study,'seal',return_value={}),patch.object(module.sys,'argv',['study','--out',str(out),'--budget-hours','.5']):
                module.main()
            state=json.loads((out/'progress.json').read_text())
            self.assertEqual(state['status'],'complete')
            self.assertEqual(len(calls),8)
            self.assertEqual({(v,s) for v,s,t,d in calls if t==100},{('control',7),('control',17),('conservative',7),('conservative',17)})
            self.assertTrue(all(d==50 for v,s,t,d in calls))
            self.assertTrue((out/'summary.json').is_file())


if __name__=='__main__':unittest.main()
