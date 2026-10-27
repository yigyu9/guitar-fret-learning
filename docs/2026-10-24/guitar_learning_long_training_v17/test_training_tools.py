"""Small, standalone CPU fixtures for the v17 collection audit/analysis tools."""
from contextlib import closing
import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
import zlib

import numpy as np
from analyze_training import Summary, bucket_updates
from verify_training import (LEDGER_KEYS, BASE_FIELDS, raw_rows, verify_ledger,
    verify_rate_components, restore_boundary, verify_preparation_contract, encoded, torch)


SCHEDULE = [dict(target_id='n0',onset_s=1.,end_s=2.,press_s=.8,finger=1,string=0,fret=3)]


def episode(best=.2, clean=.4, safe=False):
    values={k:[False if k in ('left','near_done','contact_done') else 0.] for k in LEDGER_KEYS}
    values.update(left=[best>=.4],near_done=[True],contact_done=[True],clean=[clean],
        best_clean_streak=[best],contact_time=[.08],contact_streak=[0.],clean_streak=[0.],
        wrong=[.1],wrong_supported_time=[.07],wrong_ambiguous_time=[.03],
        wrong_next_preparation_time=[.02],exposure_time=[.5],surface_min=[.01])
    times=np.zeros((1,10,3));times[0,0,0]=.1;times[0,1,1]=.1
    low=np.zeros((1,10),dtype=int);high=low.copy();low[0,:2]=[2,3];high[0,:2]=[3,4]
    provenance=dict(contract=dict(schema='guitar_learning.wrong_press_sources.v1',causes=['higher','lower','assignment']),
        body_names=['body'+str(i) for i in range(10)],target_strings_1based=[1],values=dict(
            wrong_source_time=times.tolist(),wrong_source_fret_min=low.tolist(),wrong_source_fret_max=high.tolist()))
    return dict(env_id=3,reason='timeline_complete' if safe else 'terminal_failure',
        failure_reasons=[] if safe else ['guitar_displacement'],task_time_s=2. if safe else 1.5,
        reward=1.,cost=0. if safe else 5.,cost_components=dict(original_physics_and_terminal=0.,remaining_song_failure=0. if safe else 5.),
        reward_components=dict(song_clean_hold=.2),song=dict(stage_success=safe and best>=.4,left_success_count=int(best>=.4)),
        left_note_ledger=dict(schema='guitar_learning.surface_note_ledger.v6',target_ids=['n0'],required_clean_s=[.4],
            values=values,wrong_press_sources=provenance))


class LedgerTests(unittest.TestCase):
    def test_continuous_achievement_not_cumulative(self):
        sample=episode(best=.2,clean=.6)
        verify_ledger(sample,SCHEDULE)
        sample['left_note_ledger']['values']['left']=[True]
        with self.assertRaisesRegex(ValueError,'best continuous'):verify_ledger(sample,SCHEDULE)

    def test_latched_after_current_streak_drops(self):
        sample=episode(best=.4,clean=.5)
        verify_ledger(sample,SCHEDULE)
        self.assertTrue(sample['left_note_ledger']['values']['left'][0])
        self.assertEqual(sample['left_note_ledger']['values']['contact_streak'],[0.])

    def test_wrong_partition_and_overlap(self):
        sample=episode();verify_ledger(sample,SCHEDULE)
        sample['left_note_ledger']['values']['wrong_ambiguous_time']=[.04]
        with self.assertRaisesRegex(ValueError,'partition'):verify_ledger(sample,SCHEDULE)

    def test_unseen_fret_range_rejected(self):
        sample=episode()
        sample['left_note_ledger']['wrong_press_sources']['values']['wrong_source_fret_max'][0][9]=4
        with self.assertRaisesRegex(ValueError,'unseen'):verify_ledger(sample,SCHEDULE)

    def test_positive_duration_required(self):
        schedule=copy.deepcopy(SCHEDULE);schedule[0]['end_s']=1.
        with self.assertRaisesRegex(ValueError,'Positive'):verify_ledger(episode(),schedule)


class AnalysisTests(unittest.TestCase):
    def test_best_deficit_and_equal_episode_denominator(self):
        summary=Summary(SCHEDULE)
        summary.add(episode(best=.2,clean=.6),1)
        summary.add(episode(best=.4,clean=.5,safe=True),2)
        result=summary.result(detailed=True)
        self.assertEqual(result['episodes'],2)
        self.assertEqual(result['outcomes'],dict(timeline_complete=1,physical_failure=1,task_success=1))
        self.assertEqual(result['all_notes']['note_episode_denominator'],2)
        self.assertAlmostEqual(result['all_notes']['mean_deficit'],.25)
        self.assertAlmostEqual(result['all_notes']['note_fractions']['success'],.5)
        self.assertAlmostEqual(result['all_notes']['wrong_fraction_scheduled'],.1)
        self.assertAlmostEqual(result['all_notes']['wrong_fraction_observed'],.2/1.5)
        self.assertEqual(result['wrong_press_sources']['targets'][0]['source_fret_min'][9],None)
        self.assertEqual(result['wrong_press_sources']['total_target_body_cause_seconds'][0][0],.2)

    def test_unvisited_target_remains_in_denominator(self):
        schedule=copy.deepcopy(SCHEDULE)+[dict(SCHEDULE[0],target_id='future',onset_s=10.,end_s=11.,press_s=9.8,finger=2)]
        sample=episode();ledger=sample['left_note_ledger']
        for key,values in ledger['values'].items():values.append(False if key in ('left','near_done','contact_done') else 0.)
        provenance=ledger['wrong_press_sources']['values']
        provenance['wrong_source_time'].append(np.zeros((10,3)).tolist())
        provenance['wrong_source_fret_min'].append([0]*10);provenance['wrong_source_fret_max'].append([0]*10)
        summary=Summary(schedule);summary.add(sample,0)
        result=summary.result()
        self.assertEqual(result['all_notes']['note_episode_denominator'],2)
        self.assertEqual(result['fingers']['middle']['mean_deficit'],1.)
        self.assertEqual(result['fingers']['middle']['observed_audible_seconds'],0.)
        self.assertIsNone(result['fingers']['middle']['wrong_fraction_observed'])

    def test_batch_means_not_cumulative_totals(self):
        result=bucket_updates([dict(update_index=0,metric=2.,optional=None,reward_components=dict(x=1.)),
            dict(update_index=1,metric=6.,optional=4.,reward_components=dict(x=3.))])
        self.assertEqual(result['mean']['metric'],4.)
        self.assertEqual(result['mean']['optional'],4.)
        self.assertEqual(result['reward_component_means']['x'],2.)


class RawTests(unittest.TestCase):
    def rows(self, payload):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        path=Path(temporary.name)/'raw.gz';path.write_bytes(payload)
        return path

    def test_concatenated_members_crc_eof(self):
        first=gzip.compress(b'{"a":1}\n');second=gzip.compress(b'{"a":2}\n');status={}
        self.assertEqual(list(raw_rows(self.rows(first+second),True,status)),[dict(a=1),dict(a=2)])
        self.assertEqual(status['completed_members'],2)
        self.assertTrue(status['complete']);self.assertEqual(status['valid_compressed_prefix_bytes'],len(first+second))

    def test_crc_failure_before_yield(self):
        payload=bytearray(gzip.compress(b'{"a":1}\n'));payload[-8]^=1
        with self.assertRaises(zlib.error):next(raw_rows(self.rows(payload),True,{}))

    def test_truncation_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unfinished'):list(raw_rows(self.rows(gzip.compress(b'{}\n')[:-2]),True,{}))

    def test_prefix_never_claims_whole_file_eof(self):
        first=gzip.compress(b'{"a":1}\n');status={}
        with closing(raw_rows(self.rows(first+gzip.compress(b'{}\n')[:-2]),False,status)) as stream:
            self.assertEqual(next(stream),dict(a=1))
        self.assertFalse(status['complete']);self.assertEqual(status['completed_members'],1)
        self.assertEqual(status['valid_compressed_prefix_bytes'],len(first))

    def test_invalid_jsonl_rows(self):
        for payload in (b'{}',b'\n'):
            with self.subTest(payload=payload),self.assertRaisesRegex(ValueError,'JSONL'):
                list(raw_rows(self.rows(gzip.compress(payload)),True,{}))


class ContractTests(unittest.TestCase):
    def test_current_rate_limits(self):
        parts=dict(song_finger_tracking=2.,song_finger_standby=.01,song_finger_coordination=0.,song_wrist_position=-1.,action_change=-.01)
        verify_rate_components(parts,1.)
        for key,value in [('song_finger_tracking',4.),('song_finger_standby',.05),('song_finger_coordination',.01)]:
            with self.subTest(key=key),self.assertRaises(ValueError):verify_rate_components(dict(parts,**{key:value}),1.)

    def test_exact_nonmetadata_resume(self):
        sample=dict(model=dict(x=torch.tensor([1.])),actor_optimizer=dict(x=torch.tensor([2.])),
            value_optimizer=dict(x=torch.tensor([3.])),rng_state=np.array([4],dtype=np.uint32),metadata=dict(host='a'))
        restored=copy.deepcopy(sample);restored['metadata']['host']='b';restore_boundary(sample,restored)
        for key in ('model','actor_optimizer','value_optimizer'):
            changed=copy.deepcopy(restored);changed[key]['x']+=1
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'nonmetadata'):restore_boundary(sample,changed)

    def test_actual_base_pose_names(self):
        self.assertIn('zero_y_command_rotation_error_max_rad',BASE_FIELDS)
        self.assertNotIn('zero_y_command_rotation_error_max_abs_rad',BASE_FIELDS)


    def test_v17_exact_independent_preparation_contract(self):
        from guitar_learning.gpu.finger_reward import FINGER_PREPARATION_CONTRACT
        posture=copy.deepcopy(FINGER_PREPARATION_CONTRACT)
        posture['frame_source']=dict(schema='guitar_learning.source_finger_flex_frames.v1')
        verify_preparation_contract(posture)
        for key,value in [('gate','minimum of all four idle weights'),
                          ('contact_veto','any finger blocks the whole hand'),
                          ('proximity_veto','any score target blocks the whole hand'),
                          ('rate','0.01/s * mean of only eligible fingers'),
                          ('half_band_degrees',10.),('standby_rate_per_s',.05)]:
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'Exact v17'):
                verify_preparation_contract(dict(posture,**{key:value}))

    def test_global_preparation_v1_rejected(self):
        from guitar_learning.gpu.finger_reward import FINGER_PREPARATION_CONTRACT
        posture=dict(FINGER_PREPARATION_CONTRACT,schema='guitar_learning.gpu_finger_preparation_rate.v1')
        with self.assertRaisesRegex(ValueError,'Exact v17'):verify_preparation_contract(posture)

    def test_extra_preparation_semantics_rejected(self):
        from guitar_learning.gpu.finger_reward import FINGER_PREPARATION_CONTRACT
        with self.assertRaisesRegex(ValueError,'Exact v17'):
            verify_preparation_contract(dict(FINGER_PREPARATION_CONTRACT,thumb_bonus=.01))

    def test_dragon4_canonical_finite_and_key_order(self):
        self.assertEqual(encoded(dict(x=1e-9,y=.0025)),encoded(dict(y=.0025,x=1e-9)))
        self.assertEqual(json.loads(encoded(dict(x=1e-9,y=.0025))),dict(x=1e-9,y=.0025))
        with self.assertRaises(ValueError):encoded(dict(x=float('nan')))


if __name__=='__main__':unittest.main()
