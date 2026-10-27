"""Exploration sweep orchestration without importing or running native libraries."""
import json
from pathlib import Path
import tempfile
import types
import unittest

from guitar_learning.transition_refinement import sweep


def settings(checkpoint='/bc.pt'):
    return dict(seed=7,initial_std=.003,initialization=dict(checkpoint=checkpoint,gate_evaluations=['old']),
        refinement=dict(schema='guitar_learning.transition_refinement.v1',
            evaluation_mode='deterministic',exploration=dict(initial_std=.003,min_std=.0001,max_std=.05)))


def inputs(root):
    checkpoint = root/'bc.pt';checkpoint.write_bytes(b'fixed BC checkpoint')
    source = root/'settings.json';sweep.write(source,settings(str(checkpoint)))
    return source,checkpoint


def native_result(out, *, success=True, physical=False):
    out = Path(out);folder = out/'case_000';folder.mkdir(parents=True)
    shared = dict(source_unchanged=True,physical_flags_ok=True,forbidden_calls=[],
                  missing_import_pins=[],failure=None,cleanup_error=None)
    case = dict(shared,schema='guitar_learning.transition_capture.v1',
        parent_result_path=str(out/'result.json'),action_source='policy',teacher_intervention=False,
        completed=not physical,success=success and not physical,
        episode=dict(valid=True,reason='terminal_failure' if physical else 'timeline_complete',
            transition=dict(safety_valid=not physical,successful=success and not physical)))
    sweep.write(folder/'result.json',case)
    parent = dict(shared,schema='guitar_learning.transition_probe.v1',completed=not physical,
        case_manifests={str(folder):sweep.digest(folder/'result.json')},
        successful_cases=[str(folder)] if success and not physical else [])
    sweep.write(out/'result.json',parent)
    return case,parent


class SweepTests(unittest.TestCase):
    def test_std_zero_positive_and_matching_seed_settings(self):
        base=settings()
        zero=sweep.child_settings(base,0.,2)
        sampled=sweep.child_settings(base,.001,2)
        self.assertEqual(zero['refinement']['evaluation_mode'],'deterministic')
        self.assertEqual(zero['initial_std'],.003)
        self.assertEqual(sampled['refinement']['evaluation_mode'],'stochastic')
        self.assertEqual(sampled['initial_std'],.001)
        self.assertEqual(sampled['refinement']['exploration']['initial_std'],.001)
        self.assertEqual(zero['seed'],sampled['seed']);self.assertEqual(zero['seed'],9)
        self.assertEqual(sampled['initialization']['gate_evaluations'],[])
        self.assertEqual(base,settings())
        for std in (-1.,float('nan'),float('inf')):
            with self.assertRaises(ValueError):sweep.child_settings(base,std,0)
        base['refinement']['schema']='old'
        with self.assertRaises(ValueError):sweep.child_settings(base,.001,0)

    def test_commands_use_same_interpreter_one_episode_and_optional_supervisor(self):
        direct=sweep.child_command(Path('/settings.json'),Path('/new'))
        self.assertEqual(direct[:4],[sweep.sys.executable,'-m','guitar_learning.transition_refinement.run','eval'])
        self.assertEqual(direct[-2:],['--episodes','1'])
        wrapped=sweep.child_command(Path('/settings.json'),Path('/new'),Path('/watch.gdb'))
        self.assertEqual(wrapped[:7],['gdb','-q','-nx','-batch','-x','/watch.gdb','--args'])
        self.assertEqual(wrapped[7:],direct)

    def test_valid_music_failure_and_physical_failure_keep_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            for name,success,physical in [('success',True,False),('music_fail',False,False),('physical',False,True)]:
                out=Path(directory)/name;native_result(out,success=success,physical=physical)
                row=sweep.classify_case(out,0)
                self.assertEqual(row['classification'],'evaluated')
                self.assertEqual(row['musical_success'],success)
                self.assertEqual(row['physical_failure'],physical)

    def test_runtime_fault_missing_parent_cleanup_and_tampering_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for index,mutation in enumerate(('signal','parent','cleanup','source','manifest','unclosed')):
                out=root/str(index);case,parent=native_result(out)
                if mutation=='parent':(out/'result.json').unlink()
                if mutation in ('cleanup','source','manifest','unclosed'):
                    if mutation=='cleanup':parent['cleanup_error']={'type':'RuntimeError'}
                    if mutation=='source':parent['source_unchanged']=False
                    if mutation=='manifest':parent['case_manifests']={}
                    if mutation=='unclosed':parent['completed']=False
                    (out/'result.json').write_text(json.dumps(parent))
                row=sweep.classify_case(out,136 if mutation=='signal' else 0)
                self.assertEqual(row['classification'],'runtime_invalid')
                self.assertEqual(row['sigfpe'],mutation=='signal')

    def test_fake_runner_summary_new_outputs_and_input_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source,checkpoint=inputs(root)
            calls=[]
            def runner(command,**kwargs):
                calls.append(command)
                out=Path(command[command.index('--out')+1])
                native_result(out,success=len(calls)==1,physical=len(calls)==2)
                return types.SimpleNamespace(returncode=0)
            out=root/'sweep';report=sweep.run(source,out,[0.,.001],1,runner=runner)
            self.assertTrue(report['source_unchanged'])
            self.assertEqual(report['summary'][0]['musical_successes'],1)
            self.assertEqual(report['summary'][1]['physical_failures'],1)
            self.assertEqual(report['summary'][1]['evaluated_cases'],1)
            pins=json.loads((out/'inputs_before.json').read_text())
            self.assertEqual(pins[str(source)],sweep.digest(source))
            self.assertEqual(pins[str(checkpoint)],sweep.digest(checkpoint))
            self.assertEqual(pins[str(out/'settings_000.json')],sweep.digest(out/'settings_000.json'))
            self.assertIn(str(Path(sweep.__file__).resolve()),pins)
            with self.assertRaises(FileExistsError):sweep.run(source,out,[0.],1,runner=runner)
            self.assertEqual(len(calls),2)

    def test_input_change_invalidates_summary_and_blocks_further_children(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source,_=inputs(root);calls=[]
            def runner(command,**kwargs):
                calls.append(command)
                native_result(command[command.index('--out')+1])
                source.write_text('{}')
                return types.SimpleNamespace(returncode=0)
            report=sweep.run(source,root/'sweep',[0.],2,runner=runner)
            self.assertFalse(report['source_unchanged'])
            self.assertEqual(len(calls),1)
            self.assertEqual(report['summary'][0]['evaluated_cases'],0)
            self.assertEqual(report['summary'][0]['runtime_invalid_cases'],2)

    def test_bc_change_between_children_blocks_launch_and_invalidates_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source,checkpoint=inputs(root);calls=[]
            def runner(command,**kwargs):
                calls.append(command)
                native_result(command[command.index('--out')+1])
                checkpoint.write_bytes(b'changed BC checkpoint')
                return types.SimpleNamespace(returncode=0)
            out=root/'sweep';report=sweep.run(source,out,[0.],2,runner=runner)
            self.assertEqual(len(calls),1)
            self.assertFalse(report['source_unchanged'])
            self.assertEqual(report['summary'][0]['evaluated_cases'],0)
            before=json.loads((out/'inputs_before.json').read_text())
            after=json.loads((out/'inputs_after.json').read_text())
            self.assertNotEqual(before[str(checkpoint)],after[str(checkpoint)])
            for row in report['cases']:
                self.assertEqual(row['classification'],'runtime_invalid')
                self.assertFalse(row['musical_success']);self.assertFalse(row['physical_failure'])

    def test_first_child_settings_changed_during_later_child_invalidates_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source,_=inputs(root);calls=[]
            out=root/'sweep'
            def runner(command,**kwargs):
                calls.append(command)
                native_result(command[command.index('--out')+1])
                if len(calls)==2:
                    (out/'settings_000.json').write_text('{}')
                return types.SimpleNamespace(returncode=0)
            report=sweep.run(source,out,[0.],2,runner=runner)
            self.assertEqual(len(calls),2)
            self.assertFalse(report['source_unchanged'])
            self.assertEqual(report['summary'][0]['evaluated_cases'],0)
            self.assertEqual(report['summary'][0]['runtime_invalid_cases'],2)
            before=json.loads((out/'inputs_before.json').read_text())
            after=json.loads((out/'inputs_after.json').read_text())
            self.assertNotEqual(before[str(out/'settings_000.json')],after[str(out/'settings_000.json')])
            for index,row in enumerate(report['cases']):
                self.assertEqual(row['classification'],'runtime_invalid')
                self.assertFalse(row['musical_success']);self.assertFalse(row['physical_failure'])
                self.assertEqual(json.loads((out/('result_%03d.json'%index)).read_text()),row)

    def test_absolute_parent_traversal_paths_match_producer_canonical_manifests(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source,_=inputs(root);(root/'subdir').mkdir()
            def runner(command,**kwargs):
                native_result(command[command.index('--out')+1])
                return types.SimpleNamespace(returncode=0)
            out=root/'subdir'/'..'/'sweep'
            report=sweep.run(root/'subdir'/'..'/source.name,out,[0.],1,runner=runner)
            self.assertTrue(report['source_unchanged'])
            self.assertEqual(report['summary'][0]['musical_successes'],1)
            self.assertEqual(report['cases'][0]['out'],str(root/'sweep'/'native_000'))
            self.assertEqual(sweep.classify_case(out/'native_000',0)['classification'],'evaluated')


if __name__=='__main__':unittest.main()
