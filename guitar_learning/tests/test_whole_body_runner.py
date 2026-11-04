"""합성 관측으로 실행기·저장·재개·평가 연결을 검사하며 물리 성공은 검증하지 않는다.

GPU 장면과 전체 자산 봉인만 명시적으로 대체한다. 환경/PPO/체크포인트의
실제 계약·입력 SHA 검사는 그대로 실행한다.
"""
import copy
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import torch

from guitar_learning.gpu.whole_body import WholeBodyEnvironment
from guitar_learning.native.paths import ROOT
from guitar_learning.tests.test_whole_body_environment import body_fixture
from guitar_learning.training import whole_body_runner as runner
from guitar_learning.training.whole_body import WholeBodyPolicy


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SyntheticWholeBodyPool:
    """물리를 진행하지 않는 검사 전용 풀. 실제 전신 환경에 합성240Hz 표본을 전달한다."""
    def __init__(self, settings, out, *, fail_first=False):
        self.num_envs, self.valid, self.closed = settings['num_envs'], True, False
        if self.num_envs != 2 or settings['device'] != 'cpu':
            raise ValueError('synthetic test fixture requires exactly two CPU environments')
        metadata, self.base = body_fixture()
        self.environment = WholeBodyEnvironment(metadata, duration_s=settings['duration_s'], device='cpu')
        self.contract = copy.deepcopy(self.environment.contract)
        self.fail_first, self.actions = fail_first, []
        self.observation = self.reset()[0]

    def reset(self, indices=None):
        ids = torch.arange(self.num_envs) if indices is None else indices
        self.observation = self.environment.reset(ids, copy.deepcopy(self.base))
        return self.observation, None

    def step(self, actions):
        if actions.shape != (self.num_envs, 39) or (actions[:, 37:] != 0).any():
            raise ValueError('synthetic pool accepts body37 plus two inert zero channels')
        self.actions.append(actions.detach().clone())
        env = self.environment
        env.begin_control(actions[:, :37])
        for _ in range(4):
            sample = copy.deepcopy(self.base)
            sample['physics_step'] = env.clock.clone()+1
            # 목표 오차 관측에만 행동을 반영한다. q·몸체 상태는 물리로 생성한 값이 아니다.
            sample['target'][:, env.active_joints] += .01*actions[:, :37]
            if self.fail_first:
                sample['qd'][0, 0] = 51.
            env.substep(sample)
        self.fail_first = False
        return env.end_control()

    def close(self):
        self.closed = True


class WholeBodyRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='.whole_body_runner_test_', dir=ROOT)
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.source = self.folder/'source.py'
        self.source.write_text('# synthetic test input, not a simulator\n', encoding='utf-8')
        self.settings = runner.configuration(num_envs=2, horizon=2, updates=2,
            checkpoint_every=1, duration_s=.05, device='cpu')
        self.pools = []

        def make_pool(settings, out):
            pool = SyntheticWholeBodyPool(settings, out)
            self.pools.append(pool)
            return pool

        def lightweight_pins(settings, out, lineage=()):
            paths = [self.source, Path(out)/'settings.json', *(Path(p) for p in lineage)]
            return {str(path): digest(path) for path in paths}

        # 실제 native 자산 전체 검증 대신 이 검사에 봉인한 파일 바이트를 비교한다.
        def verify_test_inputs(pins):
            return all(Path(path).is_file() and digest(path) == expected for path, expected in pins.items())

        for target, replacement in (('WholeBodyPool', make_pool), ('_pins', lightweight_pins),
                                    ('verify', verify_test_inputs)):
            patcher = patch.object(runner, target, side_effect=replacement)
            patcher.start()
            self.addCleanup(patcher.stop)

    def train(self):
        report = runner.run(self.settings, self.folder/'train')
        self.assertTrue(report['completed'])
        self.assertEqual(report['updates'], 2)
        self.assertEqual(report['transitions'], 8)
        self.assertTrue(self.pools[-1].closed)
        return self.folder/'train/final.pt'

    def test_training_strict_resume_and_saved_progress(self):
        checkpoint = self.train()
        saved, policy = runner.read_checkpoint(checkpoint)
        self.assertEqual(saved, self.settings)
        self.assertEqual(policy.architecture['learned_action_dim'], 37)
        self.assertEqual(torch.load(checkpoint, weights_only=False)['updates'], 2)
        continuation = dict(self.settings, updates=1)
        report = runner.run(continuation, self.folder/'resume', resume=checkpoint)
        self.assertEqual(report['transitions'], 4)
        final = self.folder/'resume/final.pt'
        self.assertEqual(torch.load(final, weights_only=False)['updates'], 3)
        self.assertEqual(runner.read_checkpoint(final)[0], continuation)
        self.assertTrue(all(pool.closed for pool in self.pools))
        self.assertTrue(all((action[:, 37:] == 0).all() for pool in self.pools for action in pool.actions))

    def test_bad_metadata_source_and_settings_fail_before_pool_creation(self):
        checkpoint = self.train()
        bad = torch.load(checkpoint, weights_only=False)
        bad['metadata']['schema'] = 'other-policy'
        bad_path = self.folder/'bad.pt'
        torch.save(bad, bad_path)
        with patch.object(runner, 'WholeBodyPool') as pool:
            with self.assertRaisesRegex(ValueError, 'whole body checkpoint required'):
                runner.run(self.settings, self.folder/'bad_metadata', resume=bad_path)
            pool.assert_not_called()
            original = self.source.read_text(encoding='utf-8')
            self.source.write_text('# modified pinned input\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'input sources changed'):
                runner.run(self.settings, self.folder/'bad_source', resume=checkpoint)
            pool.assert_not_called()
            self.source.write_text(original, encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'strict resume setting mismatch: duration_s'):
                runner.run(dict(self.settings, duration_s=.1), self.folder/'bad_settings', resume=checkpoint)
            pool.assert_not_called()
            with self.assertRaises(FileExistsError):
                runner.run(self.settings, self.folder/'train')
            pool.assert_not_called()
        self.assertFalse((self.folder/'bad_metadata').exists())
        self.assertFalse((self.folder/'bad_source').exists())
        self.assertFalse((self.folder/'bad_settings').exists())

    def test_evaluation_uses_actor_only_and_counts_first_failure(self):
        checkpoint = self.train()
        pool = SyntheticWholeBodyPool(self.settings, self.folder/'evaluate', fail_first=True)
        with patch.object(runner, 'WholeBodyPool', return_value=pool), patch.object(
                WholeBodyPolicy, 'forward', side_effect=AssertionError('actor/critic forward called during evaluation')):
            result = runner.evaluate(checkpoint, self.folder/'evaluate')
        self.assertTrue(result['completed'])
        self.assertTrue(pool.closed)
        self.assertEqual(result['environment_count'], 2)
        self.assertEqual(result['safe_completions'], 1)
        records = {row['env_id']: row for row in result['episodes']}
        self.assertEqual(set(records), {0, 1})
        self.assertTrue(records[0]['failed'])
        self.assertFalse(records[0]['safe_completion'])
        self.assertTrue(records[1]['safe_completion'])

    def test_cli_help_and_inspect_do_not_import_native_or_initialize_cuda(self):
        code = """
import sys
from guitar_learning.tool.training.train_whole_body import main
try:
    main(['--help'])
except SystemExit as error:
    assert error.code == 0
assert 'torch' not in sys.modules and 'isaacgym' not in sys.modules
main(['inspect', '--device', 'cpu'])
import torch
assert 'isaacgym' not in sys.modules and not torch.cuda.is_initialized()
"""
        result = subprocess.run([sys.executable, '-c', code], cwd=ROOT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('configuration only; no GPU scene or training', result.stdout)


if __name__ == '__main__':
    unittest.main()
