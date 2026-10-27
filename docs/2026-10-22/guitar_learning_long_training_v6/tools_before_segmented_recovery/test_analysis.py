"""CPU-only synthetic audit/aggregate fixtures; no training/native contexts."""
from contextlib import closing
import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
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
            progress=[dict(run=str(run.resolve()),optimizer_updates=i,elapsed_s=i,disk_free_bytes=9*1024**3,local_disk_free_bytes=4*1024**3,run_bytes=i*100) for i in (1,2)]
            for p,rows in [(run/'events.jsonl',events),(run/'resources.jsonl',resources),(phase/'progress.jsonl',progress)]:
                p.write_text(''.join(json.dumps(row)+'\n' for row in rows)+'{"partial":')
            result=a.memory_summary(run,1,True,phase)
            self.assertEqual([r['update_index'] for r in result['cache_boundaries']],[0])
            self.assertEqual([r['optimizer_updates'] for r in result['disk_samples']],[1])
            self.assertEqual(result['minimum_observed_disk_free_GiB'],9)
            self.assertEqual(result['minimum_observed_local_disk_free_GiB'],4)
            with self.assertRaises(ValueError):a.memory_summary(run,2,False,phase)

    def test_scalar_json_writer_actual_runtime(self):
        payload=dict(a=.1,negative_zero=-.0,finite=[1e-20,1e20])
        self.assertEqual(json.loads(v.json_io.dumps(payload,indent=2,allow_nan=False)),payload)

    def test_component_tolerance_and_no_gpu_native_import(self):
        self.assertLess(v.component_sum({'a':1.,'b':2.000001},3.,'test'),1e-5)
        with self.assertRaises(ValueError):v.component_sum({'a':1.},2.,'test')
        with self.assertRaises(ValueError):v.finite(dict(nonfinite_count=1))
        self.assertNotIn('isaacgym',sys.modules);self.assertNotIn('mujoco',sys.modules)
        self.assertFalse(v.torch.cuda.is_initialized())


    def test_v6_actual_contract_and_precise_rejections(self):
        # JSON evidence only: never import or execute a sealed tool.
        contract=v.read(v.ROOT/'docs/2026-10-22/guitar_learning_finger_inputs_v1/gpu_smoke8/training_contract.json')
        v.verify_codec(contract)
        for field in ('reward','dimension','priority','order','scales','request_cost','frame','approach'):
            item=copy.deepcopy(contract)
            if field=='reward':item['reward']['schema']='guitar_learning.gpu_tensor_song_reward.v4'
            if field=='dimension':item['observation']['dimension']=512
            if field=='priority':item['observation']['priority_slots']=2
            if field=='order':item['observation']['finger_targets']['slots'][0]='wrong'
            if field=='scales':item['observation']['scales'][-1]=2.
            if field=='request_cost':item['reward']['finger_tracking']['request_cost_factor']['far']=1.
            if field=='frame':item['reward']['finger_posture']['frame_source']['neutral_segment_direction']=[0.,1.,0.]
            if field=='approach':item['reward']['left_curriculum']['weights']['approach'][-1]=2.
            with self.subTest(field=field),self.assertRaises(ValueError):v.verify_codec(item)

    def test_architecture_544_eight_slots(self):
        architecture=dict(state_dim=544,event_dim=24,priority_slots=list(v.FINGER_TARGET_CONTRACT['slots']))
        v.verify_architecture(architecture)
        for field,value in (('state_dim',512),('event_dim',23),('priority_slots',['current','nearest_strict_deadline'])):
            item=dict(architecture);item[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):v.verify_architecture(item)

    def test_new_rate_bounds_and_reward_key_set(self):
        self.assertEqual(len(set(v.REWARD_KEYS+v.RIGHT_KEYS)),18)
        for seconds in (1/60.,32.8166666667):
            parts=dict(song_finger_tracking=4*seconds,song_finger_coordination=.05*seconds,song_finger_standby=.05*seconds)
            v.verify_rate_components(parts,seconds)
            for key in parts:
                item=dict(parts);item[key]*=1.01
                with self.subTest(seconds=seconds,key=key),self.assertRaises(ValueError):v.verify_rate_components(item,seconds)
            parts['song_finger_standby']=-1e-10
            with self.assertRaises(ValueError):v.verify_rate_components(parts,seconds)

    def test_episode_posture_rewards_are_rates_not_note_success(self):
        e=motion_episode();e.update(task_time_s=2.,reward=.3,cost=0.,song=dict(left_success_count=0),
            cost_components=dict(original_physics_and_terminal=0.,remaining_song_failure=0.),
            reward_components=dict(song_finger_coordination=.1,song_finger_standby=.04),
            left_curriculum=dict(full_safe=True,progress=0.,reach_fraction=0.,finger_metrics=[dict(
                near_fraction=0.,contact_fraction=0.,success_fraction=0.,clean_fraction=0.) for _ in range(4)]))
        e['left_note_ledger']=dict(values={key:[0.]*67 for key in v.LEDGER_KEYS})
        values,_,safe=a.episode_features(e,np.ones(67))
        self.assertTrue(safe);self.assertEqual(values['achieved_notes'],0)
        self.assertEqual(values['posture.coordination.realized_reward_per_s'],.05)
        self.assertEqual(values['posture.standby.realized_reward_per_s'],.02)

    def test_monitor_is_local_phase_not_external_run_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);phase=base/'local_phase';phase.mkdir()
            run=base/'external'/'run';run.mkdir(parents=True)
            for name in ('events.jsonl','resources.jsonl'):(run/name).write_text('')
            (phase/'progress.jsonl').write_text(json.dumps(dict(run=str(run.resolve()),optimizer_updates=1,elapsed_s=1,
                disk_free_bytes=100*1024**3,local_disk_free_bytes=4*1024**3,run_bytes=100))+'\n')
            (run.parent/'progress.jsonl').write_text('{bad ignored}\n')
            result=a.memory_summary(run,1,False,phase)
            self.assertEqual(result['minimum_observed_disk_free_GiB'],100)
            self.assertEqual(result['minimum_observed_local_disk_free_GiB'],4)
            self.assertEqual(result['disk_samples_path'],str((phase/'progress.jsonl').resolve()))
            self.assertEqual(v.DEFAULT_RUN,Path('/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v6_long/train2000'))


    def test_disk_monitor_filters_other_run_and_unattributed_legacy(self):
        with tempfile.TemporaryDirectory() as folder:
            phase=Path(folder);run=phase/'original';run.mkdir()
            for name in ('events.jsonl','resources.jsonl'):(run/name).write_text('')
            legacy=dict(optimizer_updates=1,elapsed_s=1,disk_free_bytes=1024**3,local_disk_free_bytes=2*1024**3,run_bytes=10)
            other=dict(legacy,run=str(phase/'restart'),optimizer_updates=100)
            matching=dict(legacy,run=str(run/'..'/'original'),disk_free_bytes=9*1024**3)
            progress=phase/'progress.jsonl'
            progress.write_text(''.join(json.dumps(row)+'\n' for row in (legacy,other,matching)))
            value=a.memory_summary(run,1,False,phase)
            self.assertEqual(len(value['disk_samples']),1)
            self.assertEqual(value['minimum_observed_disk_free_GiB'],9)
            # No matching explicit run means unknown, not the restart's disk value.
            progress.write_text(''.join(json.dumps(row)+'\n' for row in (legacy,other)))
            value=a.memory_summary(run,1,False,phase)
            self.assertEqual(value['disk_samples'],[])
            self.assertIsNone(value['minimum_observed_disk_free_GiB'])
            self.assertIsNone(value['minimum_observed_local_disk_free_GiB'])
            self.assertIn('legacy rows without run are excluded',value['disk_scope'])


    def test_analyze_one_committed_update_with_ended_episode(self):
        contract=v.read(v.ROOT/'docs/2026-10-22/guitar_learning_finger_inputs_v1/gpu_smoke8/training_contract.json')
        e=motion_episode();e.update(task_time_s=2.,reward=.14,cost=0.,song=dict(left_success_count=0),
            cost_components=dict(original_physics_and_terminal=0.,remaining_song_failure=0.),
            reward_components={key:0. for key in v.REWARD_KEYS+v.RIGHT_KEYS},
            left_curriculum=dict(full_safe=True,progress=0.,reach_fraction=0.,finger_metrics=[dict(
                near_fraction=0.,contact_fraction=0.,success_fraction=0.,clean_fraction=0.) for _ in range(4)]))
        e['reward_components'].update(song_finger_coordination=.1,song_finger_standby=.04)
        e['left_note_ledger']=dict(values={key:[0.]*67 for key in v.LEDGER_KEYS})
        control=contract['native_backend']['control']
        for j,name in enumerate(v.LEFT_HAND_NAMES):
            value=(control['action_lower_rad'][v.ACTIVE_NAMES.index(name)]+control['action_upper_rad'][v.ACTIVE_NAMES.index(name)])/2
            for field in ('target_min_rad','target_max_rad'):e['left_finger_motion']['values'][field][j]=value
            e['left_finger_motion']['values']['target_range_rad'][j]=0.
        curriculum=dict(progress=0.,stage='surface_approach',weights={},recent_safe_fraction=1.,recent_fingers=[])
        row=dict(update_index=0,journal=dict(committed=32768),completed_episodes=[e],left_curriculum=curriculum,
            mean_reward=.001,mean_cost=0.,actor_lr=3e-5,cost_weight=1.,analytic_kl=0.,max_attempted_kl=0.,kl_retries=0,
            collection_s=1.,update_s=1.,reward_component_means={key:0. for key in v.REWARD_KEYS+v.RIGHT_KEYS},
            diagnostics=dict(minibatches=dict(actor_accepted=dict(sample_weighted_mean={}),value=dict(sample_weighted_mean={})),
                post_update=dict(active_distribution=dict(std=dict(min=0.05,mean=.05,max=.05),collected_action_saturation_fraction=0.))))
        settings=dict(updates=2000,horizon=32,num_envs=1024)
        with tempfile.TemporaryDirectory() as folder:
            phase=Path(folder);run=phase/'external';run.mkdir()
            verification=dict(run=str(run),training_contract_sha256='sha',source_manifest_sha256='sha',
                committed_updates=1,prefix_verified=True,completed=False,checked_checkpoint_sha256='model')
            summary=dict(optimizer_updates=0,reward_schema=contract['reward']['schema'],sha256='model')
            def read(path):
                return settings if path.name=='settings.json' else contract
            with patch.object(a,'read',side_effect=read),patch.object(a,'digest',return_value='sha'), \
                    patch.object(a,'verify',return_value=verification),patch.object(a,'lines',return_value=iter([row])), \
                    patch.object(a,'checkpoint_summary',return_value=summary),patch.object(a,'memory_summary',return_value={}):
                result=a.analyze(run,phase,prefix=1,updates=2000)
            self.assertEqual(result['episode_groups']['overall/full_safe']['episodes'],1)
            self.assertEqual(result['episode_groups']['overall/full_safe']['mean']['posture.coordination.realized_reward_per_s'],.05)
            self.assertFalse(result['final_completed']);self.assertEqual(result['selected_committed_updates'],1)


if __name__=='__main__':unittest.main(verbosity=2)
