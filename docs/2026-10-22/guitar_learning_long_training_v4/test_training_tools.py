"""CPU-only synthetic audit/aggregate fixtures; no training/native contexts."""
from contextlib import closing
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_training as v
import analyze_training as a


def motion_episode():
    values={k:[0.]*21 for k in v.MOTION_FIELDS}
    values['actual_max_rad']=[.1]*21;values['actual_range_rad']=[.1]*21
    values['target_max_rad']=[.1]*21;values['target_range_rad']=[.1]*21
    values['action_zero_fraction']=[1.]*21
    base={k:[number]*4 for k,number in zip(v.BASE_FIELDS,(.1,.2,.3,.4,.2,.3))}
    return dict(steps=2,env_id=0,reason='timeline_complete',left_finger_motion=dict(
        schema='guitar_learning.gpu_left_finger_motion.v2',joint_names=list(v.LEFT_HAND_NAMES),
        sampling_hz=60,range_samples=3,endpoint_samples=2,action_samples=2,action_change_pairs=1,values=values,
        base_rotation=dict(schema='guitar_learning.gpu_left_finger_base_rotation.v1',body_names=v.BASE_NAMES,
            sampling_hz=60,endpoint_samples=2,values=base)))


class TrainingToolTests(unittest.TestCase):
    def test_motion_v2_identity_and_base_metric_bounds(self):
        e=motion_episode();control=dict(action_lower_rad=[-2.]*39,action_upper_rad=[2.]*39)
        v.verify_motion(e,control)
        for bad in ('oldschema','wrongshape','projected_gt_full','wrongcount'):
            item=copy.deepcopy(e)
            if bad=='oldschema':item['left_finger_motion']['schema']='guitar_learning.gpu_left_finger_motion.v1'
            if bad=='wrongshape':item['left_finger_motion']['base_rotation']['values'][v.BASE_FIELDS[0]]=[0.]*3
            if bad=='projected_gt_full':item['left_finger_motion']['base_rotation']['values'][v.BASE_FIELDS[4]]=[.31]*4
            if bad=='wrongcount':item['left_finger_motion']['base_rotation']['endpoint_samples']=3
            with self.subTest(bad=bad),self.assertRaises(ValueError):v.verify_motion(item,control)

    def test_summary_base_pose_equal_episode_means_not_pooled_rms(self):
        s=a.Summary();e=motion_episode()
        features=dict(achieved_notes=2.,physical_failure=0.,exposed_notes=0.)
        s.add(e,features,0,{})
        e=copy.deepcopy(e);e['env_id']=1;e['steps']=200
        for k in v.BASE_FIELDS:e['left_finger_motion']['base_rotation']['values'][k]=[.5]*4
        s.add(e,features,1,{})
        result=s.result([])
        self.assertEqual(result['episodes'],2)
        self.assertAlmostEqual(result['base_rotation']['values'][v.BASE_FIELDS[0]][0],.3)
        self.assertIn('not pooled',result['base_rotation']['aggregation'])

    def test_partial_tail_is_only_live_and_not_malformed_complete_line(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'rows.jsonl';p.write_text('{"n":0}\n{"n":')
            self.assertEqual(list(v.lines(p,live_tail=True)),[dict(n=0)])
            with self.assertRaisesRegex(ValueError,'Incomplete log line'):list(v.lines(p))
            p.write_text('{"n":0}\n{broken}\n{"n":2}\n')
            with self.assertRaises(json.JSONDecodeError):list(v.lines(p,live_tail=True))

    def test_crc_verified_prefix_and_corruption_are_not_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'raw.gz';member=gzip.compress(b'{"n":0}\n',mtime=0)
            p.write_bytes(member+gzip.compress(b'{"n":1}\n',mtime=0)[:-4])
            diagnostic={}
            with closing(v.iter_transitions(p,strict=True,diagnostics=diagnostic)) as stream:
                self.assertEqual(next(stream),dict(n=0))
            self.assertFalse(diagnostic['complete'])
            with self.assertRaises(ValueError):list(v.iter_transitions(p,strict=True))
            damaged=bytearray(member);damaged[-8]^=1;p.write_bytes(damaged)
            stream=v.iter_transitions(p,strict=True)
            with self.assertRaises(ValueError):next(stream)

    def test_final_raw_blank_or_unfinished_line_is_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'raw.gz'
            for payload in (b'{"n":0}\n\n',b'{"n":0}'):
                p.write_bytes(gzip.compress(payload,mtime=0))
                with self.assertRaises(ValueError):list(v.raw_rows(p,True,{}))
            p.write_bytes(gzip.compress(b'{"n":0}\n',mtime=0));status={}
            self.assertEqual(list(v.raw_rows(p,True,status)),[dict(n=0)])
            self.assertTrue(status['complete'])

    def test_memory_prefix_filters_future_and_keeps_observed_disk_only(self):
        with tempfile.TemporaryDirectory() as folder:
            phase=Path(folder);run=phase/'run';run.mkdir()
            events=[dict(update_index=i,event='cuda_cache_release',reason='optimizer_boundary',
                after=dict(free_bytes=(8-i)*1024**3,reserved_bytes=1024**3,allocated_bytes=100)) for i in range(2)]
            resources=[dict(update_index=i,elapsed_s=i,available_memory_bytes=10*1024**3,
                parent_memory=dict(rss_current_bytes=1024**3)) for i in range(2)]
            progress=[dict(optimizer_updates=i,elapsed_s=i,disk_free_bytes=9*1024**3,run_bytes=i*100) for i in (1,2)]
            for p,rows in [(run/'events.jsonl',events),(run/'resources.jsonl',resources),(phase/'progress.jsonl',progress)]:
                p.write_text(''.join(json.dumps(row)+'\n' for row in rows)+'{"partial":')
            result=a.memory_summary(run,1,True)
            self.assertEqual([r['update_index'] for r in result['cache_boundaries']],[0])
            self.assertEqual([r['optimizer_updates'] for r in result['disk_samples']],[1])
            self.assertEqual(result['minimum_observed_disk_free_GiB'],9)
            with self.assertRaises(ValueError):a.memory_summary(run,2,False)

    def test_scalar_json_writer_actual_runtime(self):
        payload=dict(a=.1,negative_zero=-.0,finite=[1e-20,1e20])
        self.assertEqual(json.loads(v.json_io.dumps(payload,indent=2,allow_nan=False)),payload)

    def test_component_tolerance_and_no_gpu_native_import(self):
        self.assertLess(v.component_sum({'a':1.,'b':2.000001},3.,'test'),1e-5)
        with self.assertRaises(ValueError):v.component_sum({'a':1.},2.,'test')
        with self.assertRaises(ValueError):v.finite(dict(nonfinite_count=1))
        self.assertNotIn('isaacgym',sys.modules);self.assertNotIn('mujoco',sys.modules)
        self.assertFalse(v.torch.cuda.is_initialized())


if __name__=='__main__':unittest.main(verbosity=2)
