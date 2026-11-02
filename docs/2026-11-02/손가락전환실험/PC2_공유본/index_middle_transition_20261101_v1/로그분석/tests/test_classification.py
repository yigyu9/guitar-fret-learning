import unittest,importlib.util
from pathlib import Path
L=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('raw_analysis',L/'tools/analyze_raw.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class Classification(unittest.TestCase):
 def test_no_sounding_dual_after_notes(self):
  x=a.simultaneous(7.,[True,True],[False,False],[True,True]);self.assertTrue(x['effective_dual']);self.assertFalse(x['audible_dual']);self.assertFalse(x['A_audible_B_raw_A_effective'])
 def test_higher_raw_during_lower_is_warning(self):
  self.assertTrue(a.simultaneous(3.5,[True,False],[False,False],[True,True])['A_audible_B_raw_A_effective'])
 def test_lower_incidental_while_higher_sounds(self):
  self.assertTrue(a.simultaneous(5.5,[False,True],[True,False],[True,True])['B_audible_A_lower_raw'])
 def test_wrong_excludes_effective(self):
  self.assertFalse(a.simultaneous(3.5,[True,True],[True,False],[True,True])['effective_dual'])
 def test_boundary_bins(self):
  for t,expected in [(0.,'prepare'),(3.,'A'),(4.5,'gap'),(5.25,'B'),(6.75,'tail')]:self.assertEqual(a.phase(t),expected)
if __name__=='__main__':unittest.main()
