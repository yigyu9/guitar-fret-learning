"""Local BC/PPO dispatch and evaluation guards use CPU doubles, never native."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

import torch

from guitar_learning.training import parallel, ppo
from guitar_learning.training import runner as train_parallel
from guitar_learning.tool.training import train_musical_quality
from guitar_learning.quality import musical_quality_transfer, musical_quality_environment
from guitar_learning.tool.evaluation import evaluate_musical_quality
from guitar_learning.skills import specialist_parallel
from guitar_learning.tool.training import train_specialists
from guitar_learning.tool.training import train_actionable_preparation
from guitar_learning.quality import actionable_preparation_transfer
from guitar_learning.timing import timing_transfer
from guitar_learning.tool.training import train_timing
from guitar_learning.tool.experiments.local_skills import learning, train, evaluate
from guitar_learning.tests.test_local_skill_learning import fitted
from guitar_learning.native.lower_body_release_v1 import common


def settings(path,data):
    return learning.settings_document(dict(actor_initialization=str(path),actor_initialization_kind='bc',
        specialist=dict(role=data['role']),timing=copy.deepcopy(data['contract']['task']['timing']['config']),
        local_skills=dict(schema=learning.SETTINGS_SCHEMA),device='cpu'))


class LocalDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def test_parser_keeps_explicit_bc_and_rejects_changed_semantics(self):
        with tempfile.TemporaryDirectory() as folder:
            path,data,_,_=fitted(folder);s=settings(path,data)
            self.assertEqual(s['actor_initialization_kind'],'bc')
            for value in [dict(s,actor_initialization_kind='ppo'),dict(s,local_skills={'schema':'unknown'}),
                          dict(s,local_skills={'schema':learning.SETTINGS_SCHEMA,'extra':1}),
                          dict(s,musical_quality={'changed':True}),dict(s,specialist={'role':'right'})]:
                with self.assertRaises(ValueError):learning.settings_document(value)
            with self.assertRaisesRegex(ValueError,'native evaluation gate'):train.validate_gate(s)

    def dispatch(self,root,resume=False,fail=False):
        path,data,_,_=fitted(root);s=settings(path,data);sp=Path(root)/'settings.json';sp.write_text('{}')
        args=SimpleNamespace(settings=sp,out=Path(root)/'train',resume=Path(root)/'resume.pt' if resume else None)
        args.out.mkdir();calls=[]
        class Trainer:
            def __init__(self,model,config=None):calls.append('optimizer')
        def transfer(model,path,*,kind):self.assertEqual(kind,'bc');calls.append('actor');return {}
        base_pool=parallel.Pool;factory=train_musical_quality.native_environment
        original_transfer=musical_quality_transfer.apply_actor_initialization;original_argv=sys.argv
        def pin(config,extra=()):return learning.dataset_manifest(extra)
        def core():
            self.assertEqual(train_parallel.settings_document({}),s)
            with patch.object(base_pool,'__init__',return_value=None) as pool:parallel.Pool([{}])
            self.assertIs(pool.call_args.kwargs['worker_factory'],factory)
            ppo.PPOTrainer(object())
            if fail:raise KeyboardInterrupt()
        with patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}), \
                patch.object(train,'validate_gate',return_value={}) as gate, \
                patch.object(learning,'apply_actor_initialization',side_effect=transfer), \
                patch.object(ppo,'PPOTrainer',Trainer),patch.object(common,'pin',side_effect=pin), \
                patch.object(train_parallel,'main',side_effect=core):
            if fail:
                with self.assertRaises(KeyboardInterrupt):train.run(s,args)
            else:train.run(s,args)
            self.assertEqual(gate.call_count,0 if resume else 1)
        self.assertIs(parallel.Pool,base_pool)
        self.assertIs(train_musical_quality.native_environment,factory)
        self.assertIs(musical_quality_transfer.apply_actor_initialization,original_transfer)
        self.assertIs(sys.argv,original_argv)
        return calls

    def test_actor_before_fresh_optimizer_and_binding_restored_after_failure(self):
        for fail in (False,True):
            with tempfile.TemporaryDirectory() as folder:self.assertEqual(self.dispatch(folder,fail=fail),['actor','optimizer'])

    def test_strict_resume_skips_actor_reinitialization_and_new_gate(self):
        with tempfile.TemporaryDirectory() as folder:self.assertEqual(self.dispatch(folder,resume=True),['optimizer'])

    def native_double(self,path,data,args,quality=True,reset=None,close=None):
        def execute(settings,args):
            args.out.mkdir()
            env=musical_quality_environment.build_environment()
            try:
                env.reset();env.step(None)
                episode=copy.deepcopy(data['result']['episode'])
                episode['musical_quality']['stage_success']=quality
                result=dict(completed=True,source_unchanged=True,kind='actor_migration',role=data['role'],
                    checkpoint=str(path),requested_episodes=args.episodes,episodes=[copy.deepcopy(episode) for _ in range(args.episodes)])
                metrics=dict(mode='deterministic_evaluation',role=data['role'],checkpoint_sha256=learning.dataset_manifest([path])[str(path)],
                    policy_initialization_mode='actor_migration',completed_episodes=args.episodes,requested_episodes=args.episodes,
                    quality_successful_episodes=args.episodes if quality else 0,physical_failure_episodes=0)
                for name,value in [('musical_quality_result.json',result),('evaluation_metrics.json',metrics),
                                   ('inputs_before.json',learning.dataset_manifest([path,args.settings]))]:
                    (args.out/name).write_text(json.dumps(value))
                return result
            finally:env.close()
        env=Mock();env.reset.side_effect=reset;env.close.side_effect=close
        return env,execute

    def test_policy_only_gate_requires_actual_result_metrics_and_exact_artifact(self):
        for quality in (False,True):
            with tempfile.TemporaryDirectory() as folder:
                path,data,_,_=fitted(folder);s=settings(path,data);sp=Path(folder)/'settings.json';sp.write_text('{}')
                args=SimpleNamespace(settings=sp,out=Path(folder)/'eval',initialization=path,run=None,episodes=4)
                env,execute=self.native_double(path,data,args,quality)
                with patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}), \
                        patch.object(musical_quality_environment,'build_environment',return_value=env), \
                        patch.object(evaluate_musical_quality,'evaluate',side_effect=execute), \
                        patch.object(evaluate,'available_memory_bytes',return_value=16*1024**3):
                    evaluate.evaluate(s,args)
                env.close.assert_called_once()
                gate=args.out/'local_skill_gate.json';self.assertEqual(json.loads(gate.read_text())['passed'],quality)
                s['local_skills']['evaluation_gate']=str(gate)
                if not quality:
                    with self.assertRaises(ValueError):train.validate_gate(s)
                else:
                    proof=train.validate_gate(s);self.assertEqual(len(proof),4)
                    metrics=args.out/'evaluation_metrics.json';metrics.write_text('{}')
                    with self.assertRaises(RuntimeError):train.validate_gate(s)

    def test_start_memory_guard_creates_failure_without_native_build_or_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            path,data,_,_=fitted(folder);s=settings(path,data);sp=Path(folder)/'settings.json';sp.write_text('{}')
            args=SimpleNamespace(settings=sp,out=Path(folder)/'eval',initialization=path,run=None,episodes=4)
            env,execute=self.native_double(path,data,args)
            with patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}), \
                    patch.object(musical_quality_environment,'build_environment',return_value=env) as build, \
                    patch.object(evaluate_musical_quality,'evaluate',side_effect=execute), \
                    patch.object(evaluate,'available_memory_bytes',return_value=7*1024**3):
                with self.assertRaises(evaluate.LowMemoryError):evaluate.evaluate(s,args)
            build.assert_not_called();env.close.assert_not_called()
            self.assertTrue((args.out/'local_skill_evaluation_failure.json').is_file())
            self.assertFalse((args.out/'local_skill_gate.json').exists())

    def test_total_budget_includes_result_serialization_before_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            path,data,_,_=fitted(folder);s=settings(path,data);sp=Path(folder)/'settings.json';sp.write_text('{}')
            args=SimpleNamespace(settings=sp,out=Path(folder)/'eval',initialization=path,run=None,episodes=4)
            env,execute=self.native_double(path,data,args);clock={'now':0.}
            def slow(settings,args):
                result=execute(settings,args);clock['now']=3001.;return result
            with patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}), \
                    patch.object(musical_quality_environment,'build_environment',return_value=env), \
                    patch.object(evaluate_musical_quality,'evaluate',side_effect=slow), \
                    patch.object(evaluate,'available_memory_bytes',return_value=16*1024**3), \
                    patch.object(evaluate.time,'monotonic',side_effect=lambda:clock['now']):
                with self.assertRaises(TimeoutError):evaluate.evaluate(s,args)
            env.close.assert_called_once();self.assertFalse((args.out/'local_skill_gate.json').exists())
            self.assertTrue((args.out/'local_skill_evaluation_failure.json').exists())

    def test_periodic_memory_and_case_wall_guards_close_and_preserve_primary(self):
        for mode in ('memory','wall'):
            with tempfile.TemporaryDirectory() as folder:
                path,data,_,_=fitted(folder);s=settings(path,data);sp=Path(folder)/'settings.json';sp.write_text('{}')
                args=SimpleNamespace(settings=sp,out=Path(folder)/'eval',initialization=path,run=None,episodes=4)
                clock={'now':0.}
                def reset():
                    if mode=='wall':clock['now']=601.
                env,execute=self.native_double(path,data,args,reset=reset,close=OSError('cleanup'))
                memory=[16*1024**3,16*1024**3,5*1024**3] if mode=='memory' else [16*1024**3]*3
                with patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}), \
                        patch.object(musical_quality_environment,'build_environment',return_value=env), \
                        patch.object(evaluate_musical_quality,'evaluate',side_effect=execute), \
                        patch.object(evaluate,'available_memory_bytes',side_effect=memory), \
                        patch.object(evaluate.time,'monotonic',side_effect=lambda:clock['now']):
                    with self.assertRaises(evaluate.LowMemoryError if mode=='memory' else TimeoutError):evaluate.evaluate(s,args)
                env.close.assert_called_once();self.assertFalse((args.out/'local_skill_gate.json').exists())
                failure=json.loads((args.out/'local_skill_evaluation_failure.json').read_text())
                self.assertEqual(failure['cleanup_errors'][0]['message'],'cleanup')


if __name__=='__main__':unittest.main()
