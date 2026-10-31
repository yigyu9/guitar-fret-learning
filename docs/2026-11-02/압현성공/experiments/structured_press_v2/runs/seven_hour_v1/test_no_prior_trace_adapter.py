"""GPU 없는 명시 경로 허용/원본 매핑 우선/중첩 fallback/복원 검사."""
from pathlib import Path
from types import SimpleNamespace
import unittest
import no_prior_trace_adapter as adapter


class AdapterTests(unittest.TestCase):
    def test_exact_whitelist_delegate_and_restore(self):
        calls=[];mapped={};original=lambda p:(calls.append(p) or Path('/native-result'))
        pins=lambda settings,out,extra=():extra
        paths=SimpleNamespace(resolve_input_path=original,_lexical=lambda p:Path(p).absolute(),_mapping=lambda:(mapped,{}))
        official=SimpleNamespace(_pins=pins)
        with self.assertRaisesRegex(RuntimeError,'test'):
            with adapter.adapter_context(paths,official):
                for path in adapter.FILES:self.assertEqual(paths.resolve_input_path(path),path)
                neighbour=adapter.FILES[0].parent/'noise_probe.py'
                self.assertEqual(paths.resolve_input_path(neighbour),Path('/native-result'))
                mapped[str(adapter.FILES[0])]='mapped'
                self.assertEqual(paths.resolve_input_path(adapter.FILES[0]),Path('/native-result'))
                self.assertIn(Path(adapter.__file__).resolve(),official._pins({},Path('/tmp')))
                raise RuntimeError('test')
        self.assertIs(paths.resolve_input_path,original);self.assertIs(official._pins,pins)

    def test_actual_variant_nested_and_portable_roundtrip(self):
        import sys
        runtime=adapter.probe.ROOT/'no_alignment_prior_variant/runtime'
        sys.path.insert(0,str(runtime))
        from guitar_learning.native import paths
        from guitar_learning.portability import portable,localize
        from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
        old=paths.resolve_input_path;official=SimpleNamespace(_pins=lambda *args:args)
        with adapter.adapter_context(paths,official):
            with nested_input_paths():
                for source in adapter.FILES:
                    restored=localize(portable(str(source)))
                    self.assertEqual(paths.resolve_input_path(restored),source)
                    self.assertEqual(adapter.probe.digest(source),adapter.probe.digest(paths.resolve_input_path(restored)))
                mapped=next(iter(paths._mapping()[0]))
                self.assertEqual(paths.resolve_input_path(mapped),old(mapped))
                sibling=adapter.FILES[0].parent/'noise_probe.py'
                self.assertEqual(paths.resolve_input_path(sibling),old(sibling))
        self.assertIs(paths.resolve_input_path,old)


if __name__=='__main__':unittest.main()
