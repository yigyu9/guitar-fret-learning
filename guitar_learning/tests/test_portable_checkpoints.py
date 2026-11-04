"""복사된 checkout의 별도 Python에서 strict 모델·입력·설정 검증을 수행한다."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from guitar_learning.portability import ROOT, project_path


PROGRAM = r'''
import hashlib, json, sys
from pathlib import Path
import torch
from guitar_learning.portability import (ROOT, PATH_SCHEMA, checkpoint_inputs,
    localize, portable, settings_digest, validate_checkpoint_inputs)
from guitar_learning.training.ppo import PPOTrainer, PPOConfig

class Policy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.actor = torch.nn.Linear(2, 2)
        self.value = torch.nn.Linear(2, 1)
        self.architecture = dict(schema='portable_fixture', control=dict(mode='position'),
            source_sha256={str(ROOT/'asset.dat'): hashlib.sha256((ROOT/'asset.dat').read_bytes()).hexdigest()},
            path=str(ROOT/'asset.dat'))
    def actor_parameters(self): return self.actor.parameters()
    def value_parameters(self): return self.value.parameters()

trainer = PPOTrainer(Policy(), PPOConfig(epochs=1))
path = ROOT/'checkpoint.pt'
if sys.argv[1] in ('save', 'external-settings'):
    settings = dict(bundle=str(ROOT/'data/song'), research=dict(control='position', reward=1.0))
    # 프로젝트 내부 설정·계보를 봉인한 뒤 원본 파일 없이 복원을 검증한다.
    settings_path = ROOT/'run_settings.json'
    if sys.argv[1] == 'external-settings':
        settings_path = ROOT.parent/'external_run_settings.json'
    settings_path.write_text(json.dumps(settings, indent=2)+'\n')
    ancestor = ROOT/'ancestor.pt'
    ancestor.write_bytes(b'ancestor lineage')
    inputs = [ROOT/'asset.dat', ROOT/'guitar_learning/portability.py',
              ROOT/'guitar_learning/training/ppo.py', settings_path, ancestor]
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    metadata = dict(settings=portable(settings), settings_sha256=settings_digest(settings),
        input_contract=checkpoint_inputs(pins, settings, settings_path=settings_path, lineage=[ancestor]))
    trainer.actor_optimizer.zero_grad()
    trainer.policy.actor(torch.ones(1,2)).sum().backward()
    trainer.actor_optimizer.step()
    trainer.updates = 3
    trainer.save(path, metadata)
else:
    payload = torch.load(path, map_location='cpu', weights_only=False)
    metadata = payload['metadata']
    if sys.argv[1] == 'tamper-settings': metadata['settings']['research']['reward'] = 2.0
    if sys.argv[1] == 'tamper-snapshot': metadata['input_contract']['run_settings']['utf8'] += ' '
    validate_checkpoint_inputs(metadata)
    if sys.argv[1] == 'change-control': trainer.policy.architecture['control']['mode'] = 'incremental'
    if sys.argv[1] == 'legacy':
        payload['identity'].pop('path_schema')
        torch.save(payload, path)
    trainer.load(path)
    assert trainer.updates == 3
    assert trainer.actor_optimizer.state
    assert localize(metadata['settings'])['bundle'] == str(ROOT/'data/song')
    assert list(trainer._identity()['architecture']['source_sha256']) == ['project://asset.dat']
    print('portable strict restore OK')
'''


REAL_PROGRAM = r'''
import sys
from pathlib import Path
import torch
from guitar_learning.portability import portable, project_path, HISTORICAL_FIELDS
from guitar_learning.tests.test_gpu_environment import fixture, BUNDLE, SONG
from guitar_learning.gpu.compact_press_v5 import CompactPressV5Environment
from guitar_learning.training.compact_press_v5 import CompactPressV5Policy
from guitar_learning.training.ppo import DecisionPPOTrainer, PPOConfig

torch.set_num_threads(1)
metadata, snapshot = fixture(1)
environment = CompactPressV5Environment(metadata, bundle=BUNDLE, song=SONG, device='cpu',
    skill=dict(schema='guitar_learning.finger_skill.v3', phase='J', scope='scheduled',
               hold_ticks=1, exploration='independent', planned_transitions=32, full_song_after=8))
model = CompactPressV5Policy(464, size='small', contract=environment.contract)
trainer = DecisionPPOTrainer(model, PPOConfig(epochs=1))
checkpoint = Path(sys.argv[2])
def verify_runtime_identifiers(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key not in HISTORICAL_FIELDS:
                verify_runtime_identifiers(key)
                verify_runtime_identifiers(item)
    elif isinstance(value, list):
        for item in value: verify_runtime_identifiers(item)
    elif isinstance(value, str):
        assert not value.startswith('/'), 'external runtime contract identifier: '+value
        if value.startswith('project://'):
            assert project_path(value).exists(), 'missing runtime contract input: '+value
verify_runtime_identifiers(portable(environment.contract))
historical = environment.task.provenance['song']['source_manifest']['provenance']['registered_from']
assert portable(environment.contract)['task']['provenance']['song']['source_manifest']['provenance']['registered_from'] == historical
if sys.argv[1] == 'save':
    trainer.save(checkpoint, dict(catalog=environment.catalog.document(),
        sampler=environment.sampler.state_dict(), contract=portable(environment.contract)))
else:
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    assert payload['metadata']['catalog'] == environment.catalog.document(), 'actual catalog changed on relocation'
    def differences(left, right, path=''):
        if isinstance(left, dict) and isinstance(right, dict):
            for key in left.keys() | right.keys():
                yield from differences(left.get(key), right.get(key), path+'/'+str(key))
        elif isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
            for index, (a, b) in enumerate(zip(left, right)):
                yield from differences(a, b, path+'/'+str(index))
        elif left != right:
            yield (path, left, right)
    changes = list(differences(payload['metadata']['contract'], portable(environment.contract)))
    assert not changes, 'actual environment contract changed on relocation: '+repr(changes[:5])
    environment.sampler.load_state_dict(payload['metadata']['sampler'])
    trainer.load(checkpoint)
    print('actual environment, catalog, sampler and CompactPressV5Policy strict restore OK')
'''


class PortableCheckpointTests(unittest.TestCase):
    def _run(self, root, mode, *, success=True):
        environment = dict(os.environ, PYTHONPATH=str(root))
        result = subprocess.run([sys.executable, '-c', PROGRAM, mode], cwd='/',
                                env=environment, text=True, capture_output=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def _fixture(self, root):
        for name in ('__init__.py', 'portability.py', 'native/__init__.py',
                     'native/paths.py', 'training/__init__.py', 'training/ppo.py'):
            target = root/'guitar_learning'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/'guitar_learning'/name, target)
        assets = root/'guitar_learning/assets'
        assets.mkdir()
        (assets/'native_provenance.json').write_text(json.dumps(dict(files=[])))
        (root/'asset.dat').write_bytes(b'fixed research asset')

    def test_move_then_strict_restore_without_old_root_or_ancestor(self):
        with tempfile.TemporaryDirectory() as tmp:
            origin, moved = Path(tmp)/'original checkout', Path(tmp)/'other user/project'
            self._fixture(origin)
            self._run(origin, 'save')
            shutil.copytree(origin, moved)
            shutil.rmtree(origin)
            (moved/'ancestor.pt').unlink()
            (moved/'run_settings.json').unlink()
            self.assertIn('restore OK', self._run(moved, 'load').stdout)
            for mode, message in (('tamper-settings', 'settings SHA mismatch'),
                                  ('tamper-snapshot', 'snapshot SHA/content mismatch'),
                                  ('change-control', 'architecture/input/control/config mismatch')):
                with self.subTest(mode=mode):
                    self.assertIn(message, self._run(moved, mode, success=False).stderr)
            for path in (moved/'asset.dat', moved/'guitar_learning/training/ppo.py'):
                before = path.read_bytes()
                path.write_bytes(before+b'\n')
                self.assertIn('input sources changed', self._run(moved, 'load', success=False).stderr)
                path.write_bytes(before)
            self.assertIn('legacy checkpoints', self._run(moved, 'legacy', success=False).stderr)

    def test_rejects_settings_outside_project_before_checkpoint_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            origin = Path(tmp)/'original checkout'
            self._fixture(origin)
            result = self._run(origin, 'external-settings', success=False)
            self.assertIn('Runtime input resolves outside project', result.stderr)
            self.assertFalse((origin/'checkpoint.pt').exists())

    def test_rejects_parent_traversal_and_absolute_uri(self):
        for value in ('project://../escape', 'project:///tmp/escape', 'project://'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                project_path(value)

    def test_actual_environment_catalog_sampler_and_policy_contract_across_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            moved = Path(tmp)/'copied project'
            shutil.copytree(ROOT/'guitar_learning', moved/'guitar_learning',
                ignore=lambda directory, names: [name for name in names
                    if name == '__pycache__' or name.endswith('.pyc') or
                    (name == 'archive' and Path(directory) == ROOT/'guitar_learning')])
            shutil.copytree(ROOT/'data/song_bundles/05_BN2-131-B_solo',
                            moved/'data/song_bundles/05_BN2-131-B_solo')
            checkpoint = Path(tmp)/'actual_policy.pt'
            for root, mode in ((ROOT, 'save'), (moved, 'load')):
                result = subprocess.run([sys.executable, '-c', REAL_PROGRAM, mode, str(checkpoint)],
                    cwd='/', env=dict(os.environ, PYTHONPATH=str(root)), text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('strict restore OK', result.stdout)


if __name__ == '__main__':
    unittest.main()
