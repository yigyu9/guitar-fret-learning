"""seed17 외부 감사 래퍼의 import 순서와 복구만 CPU에서 확인한다."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

PATH=Path(__file__).with_name('bootstrap.py')
spec=importlib.util.spec_from_file_location('seed17_bootstrap',PATH)
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


class BootstrapTests(unittest.TestCase):
    def test_first_import_order(self):
        tree=ast.parse(PATH.read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        self.assertIsInstance(run.body[0],ast.Import)
        self.assertEqual(run.body[0].names[0].name,'isaacgym')
        self.assertEqual(run.body[1].module,'guitar_learning.tool.experiments.structured_geometry')
        self.assertIsInstance(run.body[2],ast.With)
        self.assertEqual(run.body[2].body[0].module,'guitar_learning.tool.experiments')

    def test_pin_lineage_and_restore(self):
        for error in (False,True):
            pins=lambda settings,out,extra=():list(extra)
            metadata=lambda **kwargs:kwargs
            official=SimpleNamespace(_pins=pins,checkpoint_metadata=metadata)
            f=SimpleNamespace(CONTROL='seed7',v=SimpleNamespace(official=official))
            try:
                with b.audit_context(f):
                    self.assertEqual(f.CONTROL,b.CONTROL)
                    self.assertIn(PATH.resolve(),official._pins({},None))
                    self.assertIn(b.CONTROL,official.checkpoint_metadata()['lineage'])
                    if error:raise RuntimeError('복구 검사')
            except RuntimeError:pass
            self.assertEqual(f.CONTROL,'seed7')
            self.assertIs(official._pins,pins);self.assertIs(official.checkpoint_metadata,metadata)


if __name__=='__main__':unittest.main()
