"""Durable boundaries, damaged-tail recovery and exact PPO final publication."""
import gzip
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import torch
from guitar_learning.training.training_log_io import TransitionJournal, TransitionReadError, iter_transitions, publish_final_checkpoint
from guitar_learning.training.ppo import PPOTrainer, PPOConfig
from guitar_learning.tests.test_policy import policy


def member(rows):
    return gzip.compress((''.join(json.dumps(row)+'\n' for row in rows)).encode(), mtime=0)


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.path=Path(self.folder.name)/'transitions.jsonl.gz'
        self.journals=[]

    def tearDown(self):
        for journal in self.journals:journal.close()
        self.folder.cleanup()

    def journal(self,**kwargs):
        journal=TransitionJournal(self.path,**kwargs);self.journals.append(journal);return journal

    def test_sixty_control_tick_boundary_multiworker_counts_and_explicit_commit_discard(self):
        journal=self.journal()
        for tick in range(59):journal.write(dict(tick=tick,reward=[1.,2.]))
        self.assertEqual(journal.stats['sampled'],118)
        self.assertEqual(journal.stats['logged'],118)
        self.assertEqual(journal.stats['durable'],0)
        journal.write(dict(tick=59,reward=[1.,2.]))
        self.assertEqual(journal.stats['durable'],120)
        self.assertEqual(journal.stats['completed_members'],1)
        self.assertEqual(len(list(iter_transitions(self.path))),60)
        journal.write(dict(tick=60,reward=[1.,2.]))
        journal.commit(120)
        self.assertEqual(journal.stats['durable'],122)
        self.assertEqual(journal.stats['committed'],120)
        journal.discard(2);journal.close();journal.close()
        stats=journal.stats
        self.assertEqual(stats['sampled'],122)
        self.assertEqual(stats['logged'],122)
        self.assertEqual(stats['durable'],122)
        self.assertEqual(stats['discarded'],2)
        self.assertEqual(stats['unresolved_sampled'],0)
        self.assertEqual(stats['compressed_bytes'],self.path.stat().st_size)
        self.assertEqual(stats['completed_members'],2)
        with gzip.open(self.path,'rt') as stream:self.assertEqual(len(stream.readlines()),61)
        self.assertTrue(all(stats[key]>=0. for key in ('encode_s','compress_write_s','sync_s')))

    def test_numpy_encoding_metadata_and_serialization_failure_accounted_without_logged_row(self):
        journal=self.journal(metadata={'source':'test','features':np.array([1,2])})
        journal.write(dict(reward=np.array([1,2],np.float32),terminated=np.array([False,True]),
            infos=[dict(value=np.float32(.5)),dict(value=np.int64(3))]))
        self.assertEqual(journal.stats['sampled'],2)
        with self.assertRaises(ValueError):journal.write(dict(reward=[float('nan')]))
        self.assertEqual(journal.stats['sampled'],3)
        self.assertEqual(journal.stats['logged'],2)
        journal.discard(1);journal.commit(2);journal.close()
        row=list(iter_transitions(self.path))[0]
        self.assertEqual(row['terminated'],[False,True]);self.assertEqual(row['infos'][1]['value'],3)
        self.assertEqual(json.loads(journal.metadata_path.read_text())['metadata']['features'],[1,2])
        self.assertEqual(journal.stats['unresolved_sampled'],0)

    def test_empty_log_and_invalid_accounting_never_overwrite_existing_files(self):
        journal=self.journal()
        for count in (-1,True,1):
            with self.assertRaises(ValueError):journal.commit(count)
            with self.assertRaises(ValueError):journal.discard(count)
        journal.close();diagnostics={}
        self.assertEqual(list(iter_transitions(self.path,diagnostics=diagnostics)),[])
        self.assertTrue(diagnostics['complete'])
        self.assertEqual(self.path.stat().st_size,0)
        with self.assertRaises(FileExistsError):TransitionJournal(self.path)
        with self.assertRaises(RuntimeError):journal.write({'tick':0})

    def test_fsync_failure_does_not_claim_durable_or_committed_data(self):
        journal=self.journal();journal.write(dict(reward=[1.]))
        with patch('guitar_learning.training.training_log_io.os.fsync',side_effect=OSError('injected sync failure')):
            with self.assertRaisesRegex(OSError,'injected sync'):journal.commit(1)
        self.assertTrue(journal.stats['failed'])
        self.assertEqual(journal.stats['logged'],1)
        self.assertEqual(journal.stats['durable'],0)
        self.assertEqual(journal.stats['committed'],0)
        journal.discard(1);journal.close()
        with self.assertRaises(RuntimeError):journal.checkpoint()

    def test_completed_members_and_truncated_tail_need_explicit_recovery_diagnostic(self):
        prefix=member([dict(tick=n) for n in range(60)])
        self.path.write_bytes(prefix+member([dict(tick=60)])[:-4])
        with self.assertRaises(TransitionReadError):list(iter_transitions(self.path))
        with self.assertRaises(ValueError):list(iter_transitions(self.path,strict=False))
        diagnostic={};rows=list(iter_transitions(self.path,strict=False,diagnostics=diagnostic))
        self.assertEqual([r['tick'] for r in rows],list(range(60)))
        self.assertFalse(diagnostic['complete'])
        self.assertEqual(diagnostic['error']['type'],'EOFError')
        self.assertEqual(diagnostic['valid_prefix_rows'],60)
        self.assertEqual(diagnostic['completed_members'],1)
        self.assertEqual(diagnostic['valid_compressed_prefix_bytes'],len(prefix))
        self.assertGreater(diagnostic['discarded_unverified_bytes'],0)

    def test_legacy_single_member_valid_empty_and_cut_streams_are_distinguished(self):
        data=member([{'legacy':0},{'legacy':1}]);self.path.write_bytes(data)
        self.assertEqual(list(iter_transitions(self.path)),[{'legacy':0},{'legacy':1}])
        self.path.write_bytes(data[:-1]);d={}
        self.assertEqual(list(iter_transitions(self.path,strict=False,diagnostics=d)),[])
        self.assertEqual(d['valid_prefix_rows'],0)
        self.assertIsNotNone(d['error'])  # no CRC-certified member from this legacy stream
        self.path.write_bytes(gzip.compress(b''));d={}
        self.assertEqual(list(iter_transitions(self.path,diagnostics=d)),[])
        self.assertTrue(d['complete']);self.assertEqual(d['completed_members'],1)

    def test_crc_corruption_garbage_and_bad_json_never_skip_into_later_members(self):
        prefix=member([{'tick':0}]);damaged=bytearray(member([{'tick':1}]))
        damaged[-8]^=1
        for tail in (bytes(damaged),b'not a gzip stream',gzip.compress(b'bad json\n')):
            self.path.write_bytes(prefix+tail+member([{'tick':2}]))
            diagnostic={}
            self.assertEqual(list(iter_transitions(self.path,strict=False,diagnostics=diagnostic)),[{'tick':0}])
            self.assertFalse(diagnostic['complete']);self.assertIsNotNone(diagnostic['error'])
            with self.assertRaises(TransitionReadError):list(iter_transitions(self.path))


class PublicationTests(unittest.TestCase):
    def setUp(self):self.folder=tempfile.TemporaryDirectory();self.out=Path(self.folder.name)
    def tearDown(self):self.folder.cleanup()

    def test_same_full_ppo_state_hardlinks_and_strict_load_preserves_original_metadata(self):
        trainer=PPOTrainer(policy(),PPOConfig())
        trainer.updates=1
        latest=self.out/'checkpoint_000000.pt';trainer.save(latest,metadata={'periodic':1})
        original=latest.read_bytes()
        result=publish_final_checkpoint(trainer,self.out,latest,metadata={'final':True})
        self.assertEqual(result['mode'],'hardlink_exact_PPO_state')
        self.assertEqual(latest.stat().st_ino,(self.out/'final.pt').stat().st_ino)
        self.assertEqual(latest.read_bytes(),original)
        self.assertEqual(result['state_difference_keys'],[])
        self.assertEqual(json.loads((self.out/'final_checkpoint.json').read_text())['metadata'],{'final':True})
        restored=PPOTrainer(policy(),PPOConfig())
        self.assertEqual(restored.load(self.out/'final.pt'),{'periodic':1})
        self.assertEqual(restored.updates,1)
        for key,value in trainer.policy.state_dict().items():self.assertTrue(torch.equal(value,restored.policy.state_dict()[key]))
        with self.assertRaises(FileExistsError):publish_final_checkpoint(trainer,self.out,latest)

    def test_same_update_but_changed_model_or_rng_requires_full_save(self):
        for change in ('model','rng'):
            with self.subTest(change=change):
                out=self.out/change;out.mkdir()
                trainer=PPOTrainer(policy(),PPOConfig());latest=out/'checkpoint.pt'
                trainer.save(latest,metadata={'before':True});original=latest.read_bytes()
                if change=='model':
                    with torch.no_grad():trainer.policy.log_std[0]+=.01
                else:torch.rand(1)
                result=publish_final_checkpoint(trainer,out,latest,metadata={'final':True})
                self.assertEqual(result['mode'],'full_save')
                self.assertIn('model' if change=='model' else 'torch_rng',result['state_difference_keys'])
                self.assertNotEqual(latest.stat().st_ino,(out/'final.pt').stat().st_ino)
                self.assertEqual(latest.read_bytes(),original)
                restored=PPOTrainer(policy(),PPOConfig())
                self.assertEqual(restored.load(out/'final.pt'),{'final':True})

    def test_no_latest_checkpoint_uses_save_and_external_source_is_rejected(self):
        trainer=PPOTrainer(policy(),PPOConfig())
        result=publish_final_checkpoint(trainer,self.out,metadata={'fresh':True})
        self.assertEqual(result['mode'],'full_save')
        self.assertTrue((self.out/'final.pt').is_file())
        other=self.out/'other';other.mkdir()
        with self.assertRaises(ValueError):publish_final_checkpoint(trainer,other,self.out/'final.pt')


if __name__=='__main__':unittest.main()
