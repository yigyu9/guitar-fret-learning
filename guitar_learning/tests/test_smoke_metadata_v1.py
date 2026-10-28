"""CPU-only regression for None-valued namespace module source metadata."""
import unittest
from pathlib import Path
from types import SimpleNamespace
from guitar_learning.training.training_log_io import project_source_paths, bridge_dependency


class ModuleSourceMetadata(unittest.TestCase):
    def test_namespace_and_missing_file_are_ignored(self):
        modules = [('guitar_learning.native.namespace', SimpleNamespace(__file__=None)),
                   ('guitar_learning.native.other_namespace', SimpleNamespace())]
        self.assertEqual(project_source_paths(modules), set())

    def test_project_python_source_collected_and_external_sources_excluded(self):
        source = str(Path(__file__).resolve())
        current = str((Path(__file__).resolve().parents[1] / 'core/environment_v4.py').resolve())
        package = str((Path(__file__).resolve().parents[1] / '__init__.py').resolve())
        modules = [('guitar_learning.native.free_guitar_learning_v1.test_smoke_metadata_v1', SimpleNamespace(__file__=source)),
                   ('guitar_learning.core.environment_v4', SimpleNamespace(__file__=current)),
                   ('guitar_learning', SimpleNamespace(__file__=package)),
                   ('numpy.external', SimpleNamespace(__file__=source)),
                   ('guitar_learning.native.compiled', SimpleNamespace(__file__=source + 'c')),
                   ('guitar_learning.native.namespace', SimpleNamespace(__file__=None))]
        self.assertEqual(project_source_paths(modules), {source, current, package})

    def test_current_package_is_new_bridge_and_native_runtime_is_original(self):
        self.assertTrue(bridge_dependency(str(Path(__file__).resolve())))
        self.assertFalse(bridge_dependency('/project/guitar_learning/native/front_facing_ready_v1/runtime_v15.py'))


if __name__ == '__main__':
    unittest.main()
