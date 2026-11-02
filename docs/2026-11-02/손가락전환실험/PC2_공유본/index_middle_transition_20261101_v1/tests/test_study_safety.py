import unittest,pathlib,importlib.util,sys,tempfile,subprocess,os
from unittest.mock import patch
D=pathlib.Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('pair_study',D/'도구/study.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class StudySafety(unittest.TestCase):
 def test_ignore_partial_last_metric_line(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'metrics';p.write_text('{"x":1}\n{"x":');self.assertEqual(m.read_complete_rows(p),[{'x':1}])
 def test_optimized_driver_rejected_before_mutation(self):
  r=subprocess.run([sys.executable,'-O',str(D/'도구/study.py'),'--profile','base','--seal'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);self.assertNotEqual(r.returncode,0);self.assertIn('optimization disabled',r.stderr)
 def test_monitor_exception_reaps_only_own_process_group(self):
  original=subprocess.Popen;children=[]
  def spawn(*args,**kwargs):
   c=original([sys.executable,'-c','import time;time.sleep(120)'],start_new_session=True);children.append(c);return c
  with tempfile.TemporaryDirectory() as d:
   try:
    with patch.object(m,'verify'),patch.object(m,'publish',side_effect=[None,ValueError('injected monitor failure')]),patch.object(m.subprocess,'Popen',side_effect=spawn):
     with self.assertRaisesRegex(ValueError,'injected'):m.stage({'results':[]},{},'test_child_cleanup',[],pathlib.Path(d)/'new')
    self.assertEqual(len(children),1);self.assertIsNotNone(children[0].poll())
   finally:
    for c in children:
     if c.poll() is None:os.killpg(c.pid,15);c.wait(timeout=5)
if __name__=='__main__':unittest.main(verbosity=2)
