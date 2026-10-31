"""Publication guards and exact teacher reconstruction; no native success claim."""
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

import numpy as np

from guitar_learning.tool.experiments.contact_recovery.audit import _audit_native, _audit_recovery, _teacher_environment
from guitar_learning.tool.experiments.contact_recovery.controller import Controller
from guitar_learning.tool.experiments.contact_recovery.dataset import export, main as dataset_main
from guitar_learning.training.parallel import FIELDS
from guitar_learning.training.recording import digest, write
from guitar_learning.tests.test_transition_contact_teacher import environment


def fake_evidence(indices=(1,), contract=None):
    shapes = dict(state=(500,), events=(64,24), mask=(64,),
                  priority_events=(2,24), priority_mask=(2,), action=(39,), task_time_s=())
    arrays = {name:np.zeros((3,)+shape, dtype=np.bool_ if 'mask' in name else np.float32)
              for name,shape in shapes.items()}
    arrays['state'][:,0] = [1.,2.,3.]
    arrays['task_time_s'] = np.arange(3, dtype=np.float64)/60.
    return dict(contract=contract or {'schema':'test-contract'}, arrays=arrays,
        source_pins={'/proof/source':'a'*64}, selected_indices=list(indices),
        recovery=dict(recovery_success=True), teacher_replayed=True,
        refinement_reward_replayed=True)


class RecoveryAuditTests(unittest.TestCase):
    def test_reconstruct_original_named_codec_and_previous_targets(self):
        env, task, plan = environment()
        codec = env.control.contract
        names = list(env.control.session.scene.names)
        target = np.zeros(105)
        for i,name in enumerate(codec.names): target[names.index(name)] = codec.q_ref[i]
        context = dict(names=names, human_names=list(env.control.session.scene.human_bodies),
                       guitar_names=list(env.control.session.scene.guitar_bodies))
        initial = dict(target105=target.tolist(), sample=env.last_sample,
                       measured=env.last_measured, safety={'failure_reasons':[]})
        reconstructed, indices = _teacher_environment(
            {'action':{'target_contract':codec.metadata}}, context, initial)
        self.assertEqual(reconstructed.control.contract.metadata, codec.metadata)
        np.testing.assert_array_equal(reconstructed.control.codec_previous, codec.q_ref)
        self.assertEqual(indices, [names.index(name) for name in codec.names])

    def test_actual_measured_teacher_and_probe_replay_matches_and_rejects_forged_labels(self):
        # This exercises the pure teacher/recovery replay with synthetic contacts.
        # It is deliberately not passed to the full native capture auditor.
        env, task, plan = environment()
        codec = env.control.contract
        target = task.targets[0]
        names = list(env.control.session.scene.names)
        native_start = env.last_sample['native']['physics_step']
        def music(step):
            clean = not .3 <= step/240. < .4
            quality = dict(clean_target_candidate=clean, positive_target_candidate=clean,
                positive_evidence_ids=['synthetic-native-feature'] if clean else [],
                status='correct' if clean else 'missing')
            return dict(physics_step=native_start+step, task_time_s=step/240., targets={
                target.target_id:dict(candidate=clean, clean_target_candidate=clean,
                    positive_target_candidate=clean, fretting_quality=quality)})
        env.last_measured = music(0)
        env.last_safety = dict(failure_reasons=[])
        target105 = np.zeros(105)
        upper = [names.index(name) for name in codec.names]
        target105[upper] = codec.q_ref
        initial = copy.deepcopy(dict(sample=env.last_sample, measured=env.last_measured,
            safety=env.last_safety, target105=target105.tolist()))
        context = dict(names=names, human_names=list(env.control.session.scene.human_bodies),
                       guitar_names=list(env.control.session.scene.guitar_bodies))
        perturbation = dict(channel='L_Wrist_x', delta_rad=.005, start_s=.2,
            duration_s=1/60., eligibility='held')
        controller = Controller(plan, task, perturbation)
        rows = []
        for tick in range(240):
            action = np.asarray(controller.action(tick/60., {}, env), dtype=np.float32)
            diagnostic = copy.deepcopy(controller.diagnostic)
            _, actual_target = codec.targets(action, env.control.codec_previous)
            target105[upper] = actual_target
            env.control.codec_previous = actual_target
            samples, measurements = [], []
            for substep in range(1,5):
                step = tick*4+substep
                sample = copy.deepcopy(env.last_sample)
                sample['native']['physics_step'] = sample['geometry']['physics_step'] = native_start+step
                current = music(step)
                controller.observe_physics(current, env.last_safety)
                measurements.append(dict(music=current, stability=env.last_safety))
                samples.append(sample)
                env.last_sample, env.last_measured = sample, current
            rows.append(dict(task_time_before_s=tick/60., before_observation={}, action=action.tolist(),
                teacher_diagnostic=diagnostic,
                teacher_action39_float32=np.asarray(diagnostic['teacher_action39'], dtype=np.float32).tolist(),
                info=dict(physics_measurements=measurements, native_control={'physics_samples240':samples},
                    failure_reasons=[]), target105=target105.tolist()))
        summary = controller.ledger.summary(True, musical_success=True)
        self.assertTrue(summary['recovery_success'])
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name,value in (('initial.json',initial),('context.json',context),('plan.json',plan),('recovery.json',summary)):
                write(folder/name, value)
            def trace():
                with gzip.open(folder/'trace.jsonl.gz', 'wt') as stream:
                    for row in rows: stream.write(json.dumps(row)+'\n')
            trace()
            evidence = dict(settings={'transition':{}}, report=dict(perturbation=perturbation,
                episode={'transition':{'successful':True}}), contract={'action':{'target_contract':codec.metadata}})
            with patch('guitar_learning.tool.experiments.transition.task.make_task', return_value=task):
                _audit_recovery(folder, evidence)
                self.assertTrue(evidence['teacher_replayed'])
                self.assertGreater(len(evidence['selected_indices']), 0)
                self.assertTrue(all(index > 12 for index in evidence['selected_indices']))
                rows[0]['teacher_action39_float32'][0] += .01
                trace()
                with self.assertRaisesRegex(ValueError, 'canonical float32 teacher label'):
                    _audit_recovery(folder, evidence)

    def test_old_capture_schema_and_unassisted_policy_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); case = root/'case'; case.mkdir()
            parent = dict(schema='guitar_learning.contact_recovery_probe.v1', completed=True,
                source_unchanged=True, physical_flags_ok=True, failure=None, cleanup_error=None)
            report = dict(schema='guitar_learning.contact_recovery_capture.v1', success=True,
                completed=True, source_unchanged=True, physical_flags_ok=True,
                parent_result_path=str(root/'result.json'), action_source='policy',
                teacher_intervention=False)
            for mode in ('old_schema', 'policy'):
                value = dict(report)
                if mode == 'old_schema': value['schema'] = 'guitar_learning.transition_capture.v1'
                (case/'result.json').write_text(json.dumps(value))
                parent['case_manifests'] = {str(case):digest(case/'result.json')}
                (root/'result.json').write_text(json.dumps(parent))
                with self.assertRaises(ValueError): _audit_native(case)

    def test_changed_initial_state_or_case_spec_sha_is_rejected_before_replay(self):
        artifacts = {'trace_sha256':'trace.jsonl.gz', 'demonstration_sha256':'demonstration.npz',
            'contract_sha256':'contract.json', 'settings_sha256':'settings.json',
            'inputs_before_sha256':'inputs_before.json', 'context_sha256':'context.json',
            'initial_sha256':'initial.json', 'recovery_sha256':'recovery.json', 'plan_sha256':'plan.json',
            'initial_state_sha256':'initial_state.json', 'case_spec_sha256':'case_spec.json'}
        for changed in ('initial_state.json', 'case_spec.json'):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); case = root/'case'; case.mkdir()
                for filename in artifacts.values(): (case/filename).write_bytes(b'original')
                report = dict(schema='guitar_learning.contact_recovery_capture.v1', success=True,
                    completed=True, source_unchanged=True, physical_flags_ok=True, mode='collect',
                    parent_result_path=str(root/'result.json'), action_source='solver', teacher_intervention=True)
                report.update({key:digest(case/name) for key,name in artifacts.items()})
                (case/'result.json').write_text(json.dumps(report))
                parent = dict(schema='guitar_learning.contact_recovery_probe.v1', completed=True,
                    source_unchanged=True, physical_flags_ok=True,
                    case_manifests={str(case):digest(case/'result.json')})
                (root/'result.json').write_text(json.dumps(parent))
                (case/changed).write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'capture artifact SHA mismatch'):
                    _audit_native(case)

    def test_filtered_export_selects_only_audited_indices_and_new_schema(self):
        evidence = fake_evidence()
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)/'dataset'
            with patch('guitar_learning.tool.experiments.contact_recovery.audit.audit_capture', return_value=evidence), \
                    patch('guitar_learning.imitation.imitation.dataset_manifest', return_value=evidence['source_pins']):
                result = export([Path(directory)/'raw'], out)
            self.assertEqual(result['row_count'], 1)
            self.assertEqual(result['sources'][0]['source_indices'], [1])
            self.assertEqual(result['sources'][0]['source_pins'], evidence['source_pins'])
            self.assertFalse(result['training_performed'])
            self.assertFalse((out/'demonstration.npz').exists())
            with np.load(out/'filtered_demonstration.npz', allow_pickle=False) as data:
                self.assertEqual(set(data.files), set((*FIELDS,'action','task_time_s')))
                self.assertEqual(data['state'][:,0].tolist(), [2.])
            self.assertEqual(result['artifacts']['filtered_demonstration_sha256'],
                             digest(out/'filtered_demonstration.npz'))

    def test_empty_baseline_rows_and_contract_mismatch_never_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('guitar_learning.tool.experiments.contact_recovery.audit.audit_capture', return_value=fake_evidence(())):
                with self.assertRaisesRegex(ValueError, 'no native-audited'):
                    export([root/'raw'], root/'empty')
            self.assertFalse((root/'empty').exists())
            with patch('guitar_learning.tool.experiments.contact_recovery.audit.audit_capture',
                    side_effect=[fake_evidence(),fake_evidence(contract={'different':True})]):
                with self.assertRaisesRegex(ValueError, 'exact same'):
                    export([root/'raw1',root/'raw2'], root/'mismatch')
            self.assertFalse((root/'mismatch').exists())

    def test_failed_native_audit_and_changed_pins_never_publish_success_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); evidence = fake_evidence()
            with patch('guitar_learning.tool.experiments.contact_recovery.audit.audit_capture', side_effect=ValueError('native fail')):
                with self.assertRaisesRegex(ValueError, 'native fail'):
                    export([root/'raw'], root/'failed')
            self.assertFalse((root/'failed').exists())
            with patch('guitar_learning.tool.experiments.contact_recovery.audit.audit_capture', return_value=evidence), \
                    patch('guitar_learning.imitation.imitation.dataset_manifest', side_effect=[evidence['source_pins'], {}]):
                with self.assertRaisesRegex(RuntimeError, 'no manifest published'):
                    export([root/'raw'], root/'changed')
            self.assertFalse((root/'changed'/'manifest.json').exists())

    def test_existing_output_and_duplicate_capture_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); marker = root/'marker'; marker.write_text('keep')
            with self.assertRaises(FileExistsError): export([root/'raw'], root)
            self.assertEqual(marker.read_text(), 'keep')
            with self.assertRaisesRegex(ValueError, 'unique'): export([root/'raw',root/'raw'], root/'new')

    def test_export_cli_records_checked_runtime_for_success_and_failure(self):
        # Native import is stubbed: this verifies CLI/audit lifecycle, not PhysX.
        for failure in (False, True):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); out = root/'export'
                argv = ['dataset', '--capture', str(root/'first'), '--capture', str(root/'second'), '--out', str(out)]
                options = {'side_effect':ValueError('native audit rejected')} if failure else {
                    'return_value':{'completed':True, 'row_count':4}}
                with patch.object(sys, 'argv', argv), patch.dict(sys.modules, {'isaacgym':ModuleType('isaacgym')}), \
                        patch('guitar_learning.tool.experiments.contact_recovery.dataset.export', **options) as exporter:
                    if failure:
                        with self.assertRaisesRegex(ValueError, 'native audit rejected'): dataset_main()
                    else:
                        dataset_main()
                    exporter.assert_called_once_with([root/'first', root/'second'], out)
                audit = json.loads((root/'export_runtime_json_audit.json').read_text())
                self.assertEqual(audit['completed'], not failure)
                self.assertEqual(audit['mode'], 'export')
                self.assertEqual(audit['out'], str(out))
                self.assertFalse(audit['state_mutations'])
                self.assertGreater(audit['checks'], 0)
                self.assertEqual(audit['failure'] is not None, failure)


if __name__ == '__main__': unittest.main()
