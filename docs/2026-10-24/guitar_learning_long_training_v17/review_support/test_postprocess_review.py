"""Independent CPU-only pipeline control-flow checks. No subprocess is executed."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PHASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('postprocess_review_target', PHASE/'postprocess.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PipelineTests(unittest.TestCase):
    def run_pipeline(self, *, best=2000, fail=None, results_error=False, tool_changed=False, training_code=0, movie_mode="valid"):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        phase = Path(temporary.name)
        run = phase/'train2000'
        run.mkdir()
        (phase/'tool.py').write_text('frozen')
        (phase/'postprocess_tool_manifest.json').write_text(json.dumps({'tool.py':hashlib.sha256(b'frozen').hexdigest()}))
        if tool_changed: (phase/'tool.py').write_text('changed')
        (phase/'train2000_launch_result.json').write_text(json.dumps({'returncode':training_code}))
        (run/'report.json').write_text(json.dumps(dict(completed=True, optimizer_updates=2000,
            transitions=65536000, failure=None, changed_inputs=[], missing_import_pins=[], cleanup_errors=[])))
        calls = []
        def subprocess_run(command, **kwargs):
            stage = next(s for s in ('verification','evaluation','analysis','render')
                         if {'verification':'verify_training.py','evaluation':'evaluate_checkpoints.py',
                             'analysis':'analyze_training.py','render':'render_video.py'}[s] in ' '.join(command))
            calls.append((stage, command))
            if stage=='evaluation':
                scores=[dict(updates=u,mean_achieved=u/1000.,safe_count=1000) for u in (0,500,1000,1500,2000)]
                (phase/'checkpoint_evaluation.json').write_text(json.dumps({'selection':{'scores':scores,'best':dict(updates=best,mean_achieved=best/1000.),'latest':dict(updates=2000,mean_achieved=2.)}}))
            if stage=='render':
                out=Path(command[command.index('--out')+1]);out.mkdir()
                choice=command[command.index('--selection')+1];view=command[command.index('--view')+1]
                movie=out/(choice+'_'+('fullbody' if view=='fullbody' else 'left_hand')+'_60fps.mp4')
                if movie_mode!='missing': movie.write_bytes(b'fake' if movie_mode=='valid' else b'')
            return type('Result', (), {'returncode':2 if stage==fail else 0})()
        real_write=Path.write_text
        def write_text(path, *args, **kwargs):
            if results_error and path.name=='RESULTS.md': raise OSError('forced result-write failure')
            return real_write(path,*args,**kwargs)
        error = None
        with patch.object(module,'PHASE',phase), patch.object(module,'RUN',run), patch.object(module,'ROOT',phase), \
             patch.object(module.subprocess,'run',side_effect=subprocess_run), patch('sys.argv',['postprocess.py']), \
             patch.object(Path,'write_text',write_text):
            try: module.main()
            except Exception as exception: error=exception
        return json.loads((phase/'pipeline_status.json').read_text()), calls, error

    def test_latest_also_best_has_two_renders(self):
        status,calls,error=self.run_pipeline()
        self.assertIsNone(error);self.assertTrue(status['completed']);self.assertEqual(status['stage'],'complete')
        self.assertEqual([s for s,c in calls],['verification','evaluation','analysis','render','render'])
        self.assertEqual(len(status['videos']),2)
    def test_distinct_best_has_four_renders(self):
        status,calls,error=self.run_pipeline(best=1500)
        self.assertIsNone(error);self.assertTrue(status['completed']);self.assertEqual(len(status['videos']),4)
        self.assertEqual([s for s,c in calls],['verification','evaluation','analysis','render','render','render','render'])
    def test_failed_verifier_stops_pipeline(self):
        status,calls,error=self.run_pipeline(fail='verification')
        self.assertIsInstance(error,RuntimeError);self.assertFalse(status['completed']);self.assertEqual(status['stage'],'error')
        self.assertEqual([s for s,c in calls],['verification']);self.assertEqual(status['steps'][0]['returncode'],2)
    def test_results_write_failure_never_claims_completion(self):
        status,calls,error=self.run_pipeline(results_error=True)
        self.assertIsInstance(error,OSError);self.assertFalse(status['completed']);self.assertEqual(status['stage'],'error')
    def test_changed_tools_stop_before_execution(self):
        status,calls,error=self.run_pipeline(tool_changed=True)
        self.assertIsInstance(error,AssertionError);self.assertFalse(status['completed']);self.assertEqual(calls,[])
    def test_training_failure_stops_before_execution(self):
        status,calls,error=self.run_pipeline(training_code=136)
        self.assertIsInstance(error,AssertionError);self.assertFalse(status['completed']);self.assertEqual(calls,[])

    def test_missing_expected_movie_stops_completion(self):
        status,calls,error=self.run_pipeline(movie_mode='missing')
        self.assertIsInstance(error,AssertionError);self.assertFalse(status['completed']);self.assertEqual(status['stage'],'error')
    def test_empty_expected_movie_stops_completion(self):
        status,calls,error=self.run_pipeline(movie_mode='empty')
        self.assertIsInstance(error,AssertionError);self.assertFalse(status['completed']);self.assertEqual(status['stage'],'error')

if __name__=='__main__': unittest.main(verbosity=2)
