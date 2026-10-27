"""Missing or inconsistent lifecycle evidence must not produce a successful run."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from guitar_learning.persistent_audit import finalize_persistent_run
from guitar_learning import train_persistent,train_parallel


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value))


class PersistentAuditTests(unittest.TestCase):
    def fixture(self,out):
        core=dict(completed=True,stopped='updates_complete',failure=None,settings=dict(num_envs=1))
        write(out/'report.json',core)
        folder=out/'worker_000/environment'
        ids=dict(scene=10,sim=11,env=12,controller=13,fk=14)
        counts=dict(create_sim=1,create_env=1,load_asset=2,destroy_sim=1)
        final=dict(closed=True,native_calls=counts,forbidden_calls_total=0,episode_index=1,native_identities=ids,initial_state_calls_total=6)
        write(folder/'persistent_lifecycle.json',final)
        for number in range(2):
            d=dict(episode_index=number,native_identities=ids,native_calls=dict(counts,destroy_sim=0),
                episode_local_physics_steps=0,controller_target_history_length=0,forbidden_calls_total=0,
                native_properties_unchanged=True,initial_state_calls_total=4+2*number)
            readback=dict(human_DOF_pos_vel_max_error=0.,guitar_velocity_max_scalar_error=0.,
                body_pose_readback=dict(guitar=dict(max_position_error_m=0.,max_rotation_error_rad=0.)))
            write(folder/('episode_%04d'%number)/'persistent_reset.json',dict(diagnostics=d,readback=readback))
        return core,folder

    def test_complete_lifecycle_preserves_original_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);core,_=self.fixture(out);before=(out/'report.json').read_bytes()
            self.assertTrue(finalize_persistent_run(out))
            self.assertEqual((out/'core_report.json').read_bytes(),before)
            report=json.loads((out/'report.json').read_text())
            self.assertTrue(report['completed']);self.assertTrue(report['persistent_audit']['completed'])
            self.assertEqual(json.loads((out/'core_report.json').read_text()),core)

    def test_missing_or_reconstructed_lifecycle_fails_combined_report(self):
        for mode in ('missing','recreated','extra_state'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp);_,folder=self.fixture(out)
                if mode=='missing':(folder/'persistent_lifecycle.json').unlink()
                else:
                    p=folder/'persistent_lifecycle.json';v=json.loads(p.read_text());
                    if mode=='recreated':v['native_calls']['create_sim']=2
                    else:v['initial_state_calls_total']+=1
                    write(p,v)
                self.assertFalse(finalize_persistent_run(out))
                report=json.loads((out/'report.json').read_text())
                self.assertFalse(report['completed']);self.assertEqual(report['stopped'],'error')
                self.assertEqual(report['failure']['type'],'PersistentLifecycleAuditError')

    def test_secondary_audit_failure_preserves_original_interruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);core,folder=self.fixture(out)
            core.update(completed=False,stopped='interrupted',failure=dict(type='KeyboardInterrupt'))
            write(out/'report.json',core);(folder/'persistent_lifecycle.json').unlink()
            self.assertFalse(finalize_persistent_run(out))
            report=json.loads((out/'report.json').read_text())
            self.assertEqual(report['stopped'],'interrupted')
            self.assertEqual(report['failure']['type'],'KeyboardInterrupt')
            self.assertFalse(report['persistent_audit']['completed'])

    def test_existing_output_is_never_reaudited_by_failed_new_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);self.fixture(out);before=(out/'report.json').read_bytes()
            with patch.object(sys,'argv',['train_persistent','--out',str(out)]), \
                 patch.object(train_parallel,'main',side_effect=FileExistsError('existing run')), \
                 patch('guitar_learning.persistent_audit.finalize_persistent_run') as audit:
                with self.assertRaises(FileExistsError):train_persistent.main()
                audit.assert_not_called()
            self.assertEqual((out/'report.json').read_bytes(),before)


if __name__=='__main__':unittest.main()
