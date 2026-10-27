"""CPU fixtures for copy relocation, checkpoint offsets and recovery boundaries."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch

PHASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('evaluate_recovery_checkpoints',PHASE/'evaluate_recovery_checkpoints.py')
evaluation=importlib.util.module_from_spec(spec);spec.loader.exec_module(evaluation)


class RecoveryEvaluationTests(unittest.TestCase):
    def test_explicit_global_to_segment_paths(self):
        prefix,resumed=Path('/local/prefix'),Path('/local/resumed')
        expected={0:prefix/'initial.pt',500:prefix/'checkpoint_000499.pt',1000:prefix/'checkpoint_000999.pt',
            1500:resumed/'checkpoint_000199.pt',2000:resumed/'final.pt'}
        for updates,path in expected.items():self.assertEqual(evaluation.checkpoint_path(prefix,resumed,updates),path)
        with self.assertRaises(ValueError):evaluation.checkpoint_path(prefix,resumed,1300)

    def test_only_exact_historical_run_pins_are_relocated(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);prefix=root/'local_copy';prefix.mkdir()
            source=Path('/unavailable/external run')
            saved=prefix/'settings.json';saved.write_text('original settings bytes')
            current=root/'source.py';current.write_text('current source')
            digest=evaluation.sha(saved)
            manifest=dict(schema='guitar_learning.relocated_run_copy.v1',completed=True,errors=[],source=str(source),destination=str(prefix),
                files={'settings.json':dict(source=str(source/'settings.json'),copy=str(saved),sha256=digest,bytes=saved.stat().st_size)})
            resolve=Path.resolve
            def local_only(path,*args,**kwargs):
                if str(path).startswith(str(source)):
                    raise AssertionError('Historical failed volume must not be resolved/accessed')
                return resolve(path,*args,**kwargs)
            with patch.object(Path,'resolve',local_only):
                evaluation.verify_copy_manifest(manifest,prefix)
            manifest['errors']=['Transient source EIO; successful exact-copy retry recorded']
            evaluation.verify_copy_manifest(manifest,prefix)
            original={str(source/'settings.json'):digest,str(current):evaluation.sha(current),str(source.parent/'external run sibling/settings.json'):'a'*64}
            before=copy.deepcopy(original)
            with patch.object(Path,'resolve',local_only):
                actual,records=evaluation.relocate_pins(original,manifest)
            self.assertEqual(original,before)
            self.assertEqual(actual[str(saved)],digest);self.assertEqual(actual[str(current)],evaluation.sha(current))
            self.assertIn(str(source.parent/'external run sibling/settings.json'),actual)
            self.assertEqual(records,[dict(original=str(source/'settings.json'),actual=str(saved),sha256=digest)])
            broken=copy.deepcopy(manifest);broken['files']['settings.json']['sha256']='0'*64
            with self.assertRaises(ValueError):evaluation.relocate_pins(original,broken)
            saved.write_text('changed')
            with self.assertRaises(ValueError):evaluation.verify_copy_manifest(manifest,prefix)
            with self.assertRaises(ValueError):evaluation.merge_pins({'same':'a'},{'same':'b'})

    def test_missing_failed_and_escaped_copy_proofs_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            prefix=Path(temp)
            base=dict(schema='guitar_learning.relocated_run_copy.v1',completed=True,errors=[],source='/external',destination=str(prefix),files={})
            for field,value in (('completed',False),('errors','invalid error-history type'),('destination','/wrong')):
                bad=copy.deepcopy(base);bad[field]=value
                with self.assertRaises(ValueError):evaluation.verify_copy_manifest(bad,prefix)
            bad=copy.deepcopy(base);bad['files']['../escape']=dict(source='/external/../escape',copy=str(prefix/'../escape'))
            with self.assertRaises(ValueError):evaluation.verify_copy_manifest(bad,prefix)
            with self.assertRaises(ValueError):evaluation.relocate_pins({'/external/missing':'a'},base)

    def test_exact_nonmetadata_checkpoint_restore(self):
        payload=dict(updates=1300,identity={'contract':'v6'},model={'weight':torch.arange(6.).reshape(2,3)},
            actor_optimizer={'state':{0:{'exp_avg':torch.ones(3)}}},value_optimizer={},
            torch_rng=torch.arange(8,dtype=torch.uint8),cuda_rng=[torch.arange(5,dtype=torch.uint8)],
            numpy_rng=('MT19937',np.arange(4,dtype=np.uint32),2,0,0.),python_rng=(3,(1,2,3),None),
            curriculum=torch.arange(3331,dtype=torch.float64),metadata={'kind':'old'})
        with tempfile.TemporaryDirectory() as temp:
            left,right=Path(temp)/'old.pt',Path(temp)/'initial.pt'
            torch.save(payload,left);restored=copy.deepcopy(payload);restored['metadata']={'kind':'resumed'};torch.save(restored,right)
            rng=torch.get_rng_state().clone();evaluation.verify_boundary(left,right);self.assertTrue(torch.equal(rng,torch.get_rng_state()))
            for field in ('updates','model','actor_optimizer','cuda_rng','numpy_rng','curriculum'):
                bad=copy.deepcopy(restored)
                if field=='updates':bad[field]=1299
                elif field=='model':bad[field]['weight'][0,0]=9
                elif field=='actor_optimizer':bad[field]['state'][0]['exp_avg'][0]=2
                elif field=='cuda_rng':bad[field][0][0]=4
                elif field=='numpy_rng':bad[field][1][0]=7
                else:bad[field][0]=2
                torch.save(bad,right)
                with self.subTest(field=field),self.assertRaises(ValueError):evaluation.verify_boundary(left,right)

    def test_segmented_chain_requires_explicit_reset_and_correct_counts(self):
        chain=dict(schema=evaluation.CHAIN_SCHEMA,fresh_policy=False,origin_fresh_policy=True,continuous_training=False,
            run_completed=True,source_optimizer_updates=2000,valid_prefix_updates=1300,resumed_updates=700,
            physical_episode_reset_at_resume=True,original_native_report_missing=True,
            excluded_old_update_indices=[1300,1301],excluded_old_update_file_count=2)
        evaluation.validate_recovery_chain(chain)
        for field,value in (('fresh_policy',True),('continuous_training',True),('valid_prefix_updates',1299),('resumed_updates',701),
                            ('physical_episode_reset_at_resume',False),('original_native_report_missing',False),('excluded_old_update_file_count',3)):
            bad=copy.deepcopy(chain);bad[field]=value
            with self.assertRaises(ValueError):evaluation.validate_recovery_chain(bad)
        with self.assertRaises(KeyError):evaluation.validate_recovery_chain({})

    def test_only_completed_matching_independent_segment_proof_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest=Path(temp)/'copy.json';manifest.write_text('{}')
            prefix,resumed=Path(temp)/'prefix',Path(temp)/'resumed'
            resumed.mkdir();(resumed/'final.pt').write_bytes(b'finite checkpoint fixture')
            proof=dict(schema='guitar_learning.long_training_v6_recovery_verification.v1',completed=True,old_run=str(prefix),run=str(resumed),
                committed_updates=2000,committed_transitions=65536000,segments=[dict(committed_updates=1300),
                    dict(committed_updates=700,optimizer_offset=1300,checkpoint_updates=2000)],
                restore=dict(exact_nonmetadata=True,optimizer_updates=1300),copy_manifest_sha256=evaluation.sha(manifest),
                source_manifest_sha256=evaluation.sha(PHASE/'training_source_manifest.json'),
                checked_checkpoint_path=str(resumed/'final.pt'),checked_checkpoint_sha256=evaluation.sha(resumed/'final.pt'),
                excluded_old_update_indices=[1300,1301],excluded_old_update_file_count=2)
            evaluation.verify_segmented_proof(proof,prefix,resumed,manifest)
            for field,value in (('completed',False),('committed_updates',1300),('committed_transitions',123),('old_run','/wrong')):
                bad=copy.deepcopy(proof);bad[field]=value
                with self.assertRaises(ValueError):evaluation.verify_segmented_proof(bad,prefix,resumed,manifest)
            bad=copy.deepcopy(proof);bad['checked_checkpoint_sha256']='0'*64
            with self.assertRaises(ValueError):evaluation.verify_segmented_proof(bad,prefix,resumed,manifest)
            bad=copy.deepcopy(proof);bad['segments'][1]['optimizer_offset']=1200
            with self.assertRaises(ValueError):evaluation.verify_segmented_proof(bad,prefix,resumed,manifest)


if __name__=='__main__':unittest.main()
