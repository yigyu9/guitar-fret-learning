"""Fresh spawned worker logger binding must not capture itself recursively."""
import subprocess
import sys
import unittest


class WorkerBindingTests(unittest.TestCase):
    def test_fresh_worker_binds_original_logger_before_override(self):
        script = '''
import sys,types
from unittest.mock import patch
sys.modules['isaacgym']=types.ModuleType('isaacgym')
from guitar_learning import parallel
original=parallel._compact
from guitar_learning.train_musical_quality import native_environment,compact
with patch('guitar_learning.musical_quality_environment.build_environment',return_value='built'):
    result=native_environment(dict(config={},out='/tmp/quality-log-test',bundle='unused',specialist={'role':'left'},timing={'pre_roll_s':3.},stage='B'),0)
assert result=='built'
from guitar_learning import specialist_parallel
assert specialist_parallel.base_compact is original
assert parallel._compact is compact
try: compact(None,{},[])
except (KeyError,AttributeError): pass
else: raise AssertionError('incomplete info should not be accepted')
'''
        result=subprocess.run([sys.executable,'-c',script],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
