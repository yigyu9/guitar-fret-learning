"""CPU fixtures for relocation, exact restore and segmented chronology; no native."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_recovery as v
import analyze_recovery as a
import test_analysis as fixtures


def segment(updates,offset=0,final=False):
    return dict(committed_transitions=updates*32*1024,raw_rows=updates*32,
        checked_checkpoint_path='checkpoint',checked_checkpoint_sha256='sha',
        ended_episode_counts=dict(all=1,timeline_complete=1,physical_failure=0))


class RecoveryTests(unittest.TestCase):
    def test_exact_state_compares_rng_dtype_and_signed_zero(self):
        original=dict(tensor=v.torch.tensor([0.,1.]),rng=v.np.array([1,2],dtype='uint32'),nested=(.1,0.))
        self.assertTrue(v.same(original,copy.deepcopy(original)))
        for key,value in (('tensor',v.torch.tensor([-0.,1.])),('rng',v.np.array([1,3],dtype='uint32')),('nested',(.1,-0.))):
            changed=copy.deepcopy(original);changed[key]=value
            self.assertFalse(v.same(original,changed))
        self.assertFalse(v.same(v.torch.tensor([1.]),v.torch.tensor([1.],dtype=v.torch.float64)))

    def test_restore_all_nonmetadata_and_metadata_only_exception(self):
        with tempfile.TemporaryDirectory() as folder:
            old,new=(Path(folder)/name for name in ('old.pt','initial.pt'))
            value=dict(updates=1300,model=dict(q=v.torch.tensor([1.])),actor_optimizer=dict(state={1:2}),
                value_optimizer=dict(state={1:3}),rng=v.np.array([5],dtype='uint32'),metadata=dict(out='old'))
            v.torch.save(value,old);other=copy.deepcopy(value);other['metadata']={'out':'new'};v.torch.save(other,new)
            self.assertTrue(v.verify_restore(old,new)['exact_nonmetadata'])
            other['rng'][0]=6;v.torch.save(other,new)
            with self.assertRaisesRegex(ValueError,'nonmetadata'):v.verify_restore(old,new)

    def test_manifest_proves_relocation_without_reading_missing_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);destination=root/'copied';destination.mkdir();source=root/'offline'
            payload=b'{"out":"original"}\n';(destination/'settings.json').write_bytes(payload)
            expected=hashlib.sha256(payload).hexdigest()
            manifest=dict(schema='guitar_learning.relocated_run_copy.v1',source=str(source),destination=str(destination),
                completed=True,errors=['transient retry retained'],bytes=len(payload),files={'settings.json':dict(sha256=expected,bytes=len(payload),source={},copy={})})
            path=root/'copy.json';path.write_text(json.dumps(manifest))
            loaded=v.relocation_manifest(path,destination)
            v.verify_pin(str(source/'settings.json'),expected,loaded)
            with self.assertRaises(ValueError):v.verify_pin(str(source/'settings.json'),'wrong',loaded)
            with self.assertRaises(ValueError):v.verify_pin(str(source/'missing.json'),expected,loaded)
            (destination/'settings.json').write_bytes(payload+b'bad')
            with self.assertRaises(ValueError):v.relocation_manifest(path,destination)

    def test_relocation_never_applies_to_other_source_or_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);old=root/'old';old.mkdir();outside=root/'real.py';outside.write_text('source')
            relocation=dict(source=str(root/'offline'),destination=str(old),files={})
            v.verify_pin(str(outside),v.digest(outside),relocation)
            with self.assertRaises(ValueError):v.verify_pin(str(outside),'wrong',relocation)
            path=root/'manifest.json';path.write_text(json.dumps(dict(relocation,schema='guitar_learning.relocated_run_copy.v1',
                completed=True,errors=[],bytes=6,files={'../real.py':dict(sha256=v.digest(outside),bytes=6)})))
            with self.assertRaises(ValueError):v.relocation_manifest(path,old)

    def test_prefix1300_needs_no_resumed_files_and_excludes62_branch(self):
        with tempfile.TemporaryDirectory() as folder:
            phase=Path(folder);old=phase/'recovered_train2000_restart1';old.mkdir()
            for index in range(1300,1362):(old/('update_%06d.json'%index)).touch()
            with patch.object(v,'relocation_manifest',return_value=dict(files={},bytes=0,errors=[])),patch.object(v,'digest',return_value='sha'), \
                    patch.object(v,'verify_restore') as restore,patch.object(v,'verify_segment',return_value=segment(1300)) as audit:
                result=v.verify(phase,prefix=1300)
            restore.assert_not_called();self.assertEqual(audit.call_count,1)
            self.assertEqual(result['committed_transitions'],42598400);self.assertEqual(result['raw_rows'],41600)
            self.assertEqual(result['excluded_old_update_file_count'],62)
            self.assertIsNone(result['restore']);self.assertFalse(result['completed']);self.assertTrue(result['prefix_verified'])

    def test_final1300_plus700_and_prefix_global_offsets(self):
        with tempfile.TemporaryDirectory() as folder:
            phase=Path(folder);old=phase/'recovered_train2000_restart1';old.mkdir()
            for prefix,new_count,final in ((None,700,True),(1400,100,False)):
                with patch.object(v,'relocation_manifest',return_value=dict(files={},bytes=0,errors=[])),patch.object(v,'digest',return_value='sha'), \
                        patch.object(v,'read',return_value={}),patch.object(v,'verify_restore',return_value=dict(exact_nonmetadata=True)), \
                        patch.object(v,'verify_segment',side_effect=[segment(1300),segment(new_count,1300,final)]) as audit:
                    result=v.verify(phase,prefix=prefix)
                self.assertEqual(audit.call_args_list[1].kwargs,dict(offset=1300,final_mode=final))
                self.assertEqual(result['committed_updates'],1300+new_count)
                self.assertEqual(result['committed_transitions'],(1300+new_count)*32768)
                self.assertEqual(result['completed'],final)
                if final:self.assertEqual(result['committed_transitions'],65536000)

    def test_no_native_or_cuda_context(self):
        self.assertNotIn('isaacgym',sys.modules);self.assertNotIn('mujoco',sys.modules)
        self.assertFalse(v.torch.cuda.is_initialized())


    def test_chain_memory_keeps_process_baselines_and_global_progress(self):
        with tempfile.TemporaryDirectory() as folder:
            phase=Path(folder);old,new=(phase/name for name in ('old','new'))
            for run,free in ((old,8),(new,4)):
                run.mkdir()
                events=[dict(update_index=i,event='cuda_cache_release',reason='optimizer_boundary',
                    after=dict(free_bytes=(free-i)*1024**3,reserved_bytes=1024**3,allocated_bytes=100)) for i in range(3)]
                ram=[dict(update_index=i,elapsed_s=i,available_memory_bytes=10*1024**3,
                    parent_memory=dict(rss_current_bytes=1024**3)) for i in range(3)]
                (run/'events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in events))
                (run/'resources.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in ram))
            rows=[dict(run=str(run),optimizer_updates=i,elapsed_s=1,disk_free_bytes=9*1024**3,
                local_disk_free_bytes=4*1024**3,run_bytes=1) for run,i in ((phase/'offline',1),(new,1301),(new,1303))]
            rows.append(dict(optimizer_updates=1,disk_free_bytes=1))
            (phase/'progress.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
            value=a.chain_memory([(old,2,0),(new,2,1300)],phase,dict(source=str(phase/'offline')))
            self.assertEqual([r['update_index'] for r in value['cache_boundaries']],[0,1,1300,1301])
            self.assertEqual([r['estimated_nonTorch_growth_GiB'] for r in value['cache_boundaries']],[0,1,0,1])
            self.assertEqual([r['optimizer_updates'] for r in value['disk_samples']],[1,1301])
            self.assertEqual(len(value['processes']),2)

    def test_analyzer_streams1300_plus1_and_global_cohorts_without_branch(self):
        contract=v.read(v.ROOT/'docs/2026-10-22/guitar_learning_finger_inputs_v1/gpu_smoke8/training_contract.json')
        e=fixtures.motion_episode();e.update(task_time_s=2.,reward=.14,cost=0.,song=dict(left_success_count=1),
            cost_components=dict(original_physics_and_terminal=0.,remaining_song_failure=0.),
            reward_components={key:0. for key in v.REWARD_KEYS+v.RIGHT_KEYS},
            left_curriculum=dict(full_safe=True,progress=0.,reach_fraction=0.,finger_metrics=[dict(
                near_fraction=0.,contact_fraction=0.,success_fraction=0.,clean_fraction=0.) for _ in range(4)]))
        e['reward_components'].update(song_finger_coordination=.1,song_finger_standby=.04)
        e['left_note_ledger']=dict(values={key:[0.]*67 for key in v.base.LEDGER_KEYS})
        control=contract['native_backend']['control']
        for j,name in enumerate(v.base.LEFT_HAND_NAMES):
            value=(control['action_lower_rad'][v.base.ACTIVE_NAMES.index(name)]+control['action_upper_rad'][v.base.ACTIVE_NAMES.index(name)])/2
            for field in ('target_min_rad','target_max_rad'):e['left_finger_motion']['values'][field][j]=value
            e['left_finger_motion']['values']['target_range_rad'][j]=0.
        def rows(path,**kwargs):
            resumed=path.parent.name=='train_resume700'
            for local in range(1 if resumed else 1300):
                yield dict(update_index=local,optimizer_updates=1301 if resumed else local+1,
                    journal=dict(committed=(local+1)*32768),completed_episodes=[e] if resumed else [],
                    left_curriculum=dict(progress=0.,stage='surface_approach',weights={},recent_safe_fraction=1.,recent_fingers=[]),
                    mean_reward=.001,mean_cost=0.,actor_lr=3e-5,cost_weight=1.,analytic_kl=0.,max_attempted_kl=0.,kl_retries=0,
                    collection_s=1.,update_s=1.,reward_component_means={key:0. for key in v.REWARD_KEYS+v.RIGHT_KEYS},
                    diagnostics=dict(minibatches=dict(actor_accepted=dict(sample_weighted_mean={}),value=dict(sample_weighted_mean={})),
                        post_update=dict(active_distribution=dict(std=dict(min=.05,mean=.05,max=.05),collected_action_saturation_fraction=0.))))
            if not resumed:raise AssertionError('Excluded branch was read')
        with tempfile.TemporaryDirectory() as folder:
            phase=Path(folder);old=phase/'recovered_train2000_restart1';new=phase/'train_resume700'
            proof=dict(schema='guitar_learning.long_training_v6_recovery_verification.v1',old_run=str(old),run=str(new),
                committed_updates=1301,committed_transitions=1301*32768,prefix_verified=True,completed=False,
                copy_manifest_sha256='sha',source_manifest_sha256='sha',segments=[dict(training_contract_sha256='sha')]*2,
                checked_checkpoint_path=str(new/'initial.pt'),checked_checkpoint_sha256='model')
            def read(path):
                if path.name=='training_contract.json':return contract
                if path.name=='settings.json':return dict(updates=700 if path.parent==new else 2000)
                return dict(source=str(phase/'offline'))
            def model(path,c):return dict(optimizer_updates=1300 if path.parent==new else 0,sha256='model')
            with patch.object(a,'read',side_effect=read),patch.object(a,'digest',return_value='sha'), \
                    patch.object(a.recovery,'verify',return_value=proof),patch.object(a,'lines',side_effect=rows), \
                    patch.object(a,'checkpoint_summary',side_effect=model),patch.object(a,'chain_memory',return_value={}):
                value=a.analyze(phase,prefix=1301)
            self.assertEqual(len(value['update_curve']),1301)
            self.assertEqual(value['update_curve'][-1]['update_index'],1300)
            self.assertEqual(value['update_curve'][-1]['local_update_index'],0)
            self.assertEqual(value['episode_groups']['overall/full_safe']['episodes'],1)
            self.assertEqual(value['episode_groups']['updates_100/1300_1300/full_safe']['episodes'],1)
            self.assertEqual(value['episode_groups']['updates_250/1250_1300/full_safe']['episodes'],1)
            self.assertEqual(value['physical_episode_boundaries'][0]['optimizer_update'],1300)
            self.assertFalse(value['final_completed'])


if __name__=='__main__':unittest.main(verbosity=2)
