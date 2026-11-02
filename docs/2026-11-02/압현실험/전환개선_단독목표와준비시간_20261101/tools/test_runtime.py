"""단독 B도 A6 초기 자세를 쓰며 조건·시간표·소스 계약을 섞지 않는지 검사한다."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('single_gap_runtime',HERE/'runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
spec=importlib.util.spec_from_file_location('single_gap_prepare',HERE/'prepare_targets.py')
prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)


class RuntimeContractTests(unittest.TestCase):
    def test_all_approved_sequences(self):
        expected={
            'b_only': ([(8,3.,4.5)],5.,['B']),
            'gap150': ([(6,3.,4.5),(8,6.,7.5)],8.,['A','B']),
            'gap100': ([(6,3.,4.5),(8,5.5,7.)],7.5,['A','B']),
            'gap075': ([(6,3.,4.5),(8,5.25,6.75)],7.25,['A','B']),
        }
        for condition,(events,duration,roles) in expected.items():
            settings=runtime.build_settings(condition)
            config=runtime.validate(settings)
            self.assertEqual([(r['fret'],r['onset_s'],r['end_s']) for r in config['schedule']],events)
            self.assertEqual(config['duration_s'],duration)
            self.assertEqual(config['goal_roles'],roles)
            self.assertEqual(config['detail_physics_rows'],round(duration*240))
            self.assertTrue(all(r['finger']==2 and r['string_index']==2 for r in config['schedule']))
            self.assertEqual([r['fret'] for r in prepare.fingering(condition)['notes']],[r[0] for r in events])

    def test_identical_a6_bias_algorithm_and_action_axes(self):
        base=runtime.build_settings('gap075')
        for condition in runtime.CONDITIONS:
            s=runtime.build_settings(condition)
            self.assertEqual(s['natural_press'],base['natural_press'])
            self.assertEqual(s['natural_press']['song'],'virtual_finger_v9_middle_s3_f6')
            self.assertEqual(s['natural_press']['condition'],'E4')
            self.assertEqual(len(s['natural_press']['active_axes']),16)
            self.assertEqual(s['ppo'],base['ppo'])
            self.assertEqual((s['size'],s['num_envs'],s['horizon']),('large',1024,32))
            self.assertFalse(s['transition']['thumb_active'])

    def test_geometry_is_exact_source_copy(self):
        old=runtime.BASE.parent/'중지6에서8프렛_환경수비교_20261101/geometry'
        for name in ('initial_catalog.json','initial_provenance.json'):
            self.assertEqual((old/name).read_bytes(),(runtime.BASE/'geometry'/name).read_bytes())

    def test_input_byte_hashes(self):
        for condition in runtime.CONDITIONS:
            for name,expected in runtime.sequence_config(condition)['bundle_files'].items():
                self.assertEqual(hashlib.sha256((runtime.ROOT/name).read_bytes()).hexdigest(),expected)

    def test_changed_condition_and_legacy_schema_are_rejected(self):
        base=runtime.build_settings('b_only')
        for key,value in [('condition','gap150'),('schema','guitar_learning.middle_f6_f8_environment_scale.v1'),('goal_roles',['A'])]:
            changed=copy.deepcopy(base);changed['transition'][key]=value
            with self.assertRaises(ValueError):runtime.validate(changed)
        self.assertNotEqual(runtime.TransitionPolicy.schema,'guitar_learning.middle_f6_f8_environment_scale_policy.v1')

    def test_changed_training_song_and_initial_pose_are_rejected(self):
        for field in ('song','initial','bundle_sha'):
            changed=runtime.build_settings('b_only')
            if field=='song':changed['song_training']['bundle']=str(runtime.ROOT/'data/song_bundles/virtual_middle_s3_f6_f8_gap150_v2')
            elif field=='initial':changed['natural_press']['song']='virtual_finger_v9_middle_s3_f8'
            else:changed['transition']['bundle_files'][next(iter(changed['transition']['bundle_files']))]='0'*64
            with self.assertRaises(ValueError):runtime.validate(changed)

    def test_thumb_permission_is_rejected(self):
        with self.assertRaises(ValueError):runtime.build_settings('b_only',thumb_active=True)

    def test_source_and_selected_inputs_pinned_without_archive(self):
        from guitar_learning.training import finger_skill_runner as runner
        settings=runtime.build_settings('b_only')
        with tempfile.TemporaryDirectory(prefix='single_gap_pins_',dir=runtime.ROOT/'.runtime/cache') as d:
            out=Path(d);(out/'settings.json').write_text(json.dumps(settings))
            original=runner._pins
            with runtime.transition_runtime(settings):pins=runner._pins(settings,out)
            self.assertIs(runner._pins,original)
            for p in (HERE/'runtime.py',runtime.BASE/'geometry/initial_catalog.json',runtime.ROOT/'guitar_learning/training/ppo.py'):
                self.assertEqual(pins[str(p.resolve())],runtime.natural.digest(p))
            self.assertFalse(any('/guitar_learning/archive/' in name for name in pins))


if __name__=='__main__':unittest.main()
