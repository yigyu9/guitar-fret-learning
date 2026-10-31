"""격리 연구의 분포·기하 단계·학습률 복구·저장본 구분을 CPU에서 검증한다."""
import math
import copy
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
import torch
from torch.distributions import Normal
from guitar_learning.tests.test_finger_skill_policy import inputs
from guitar_learning.training.policy import FingerSkillPolicy
from guitar_learning.training.ppo import PPOConfig, DecisionPPOTrainer
from guitar_learning.tests.test_ppo import assert_tree
from guitar_learning.tool.experiments.press_research import (
    ResearchPolicy, ResearchTrainer, configuration, research_runtime)


def contract():
    relative = Path("process/learning/runs/index_s3_f6/train/J/training_contract.json")
    source = next(parent/relative for parent in Path(__file__).resolve().parents if (parent/relative).is_file())
    return json.loads(source.read_text())


def model(mode):
    return ResearchPolicy(557, size='small', contract=contract(), research=configuration(mode))


class PressResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_baseline_preserves_seeded_outputs_and_rng(self):
        torch.manual_seed(9)
        original = FingerSkillPolicy(557, size='small', contract=contract())
        torch.manual_seed(9)
        research = model('baseline')
        data = inputs()
        torch.manual_seed(17); expected = original.act(*data)
        torch.manual_seed(17); actual = research.act(*data)
        for name in expected:
            self.assertTrue(torch.equal(expected[name], actual[name]), name)

    def test_exploration_only_changes_finger_std_and_floor(self):
        instance = model('exploration')
        data = inputs()
        result = instance(*data)
        self.assertTrue(torch.allclose(result['log_std'][:, :17].exp(), torch.full((4, 17), math.exp(-3))))
        self.assertTrue(torch.allclose(result['log_std'][:, 17:33].exp(), torch.full((4, 16), .15)))
        with torch.no_grad(): instance.finger_log_std.fill_(-5)
        self.assertTrue(torch.allclose(instance(*data)['log_std'][:, 17:33].exp(), torch.full((4, 16), .1)))

    def test_sequential_gates_and_raw_latent_density(self):
        instance = model('sequential')
        state, events, mask, priority, valid = inputs()
        state.zero_(); priority.zero_(); valid.zero_(); valid[:, 0] = True
        normal_col = instance.gate_columns[3]
        priority[:, 0, normal_col] = .5
        # 행0 손목 이동 / 행1 정렬 / 행2 굽힘 / 행3 목표 없음.
        state[0, instance.wrist_indices[0]] = .02/instance.wrist_scales[0]
        priority[1, 0, instance.gate_columns[0]] = .02/instance.gate_scales[0]
        valid[3, 0] = False
        stages = instance.gate_stages(state, priority, valid)
        self.assertEqual(stages[:, 0].tolist(), [0, 1, 2, -1])
        data = (state, events, mask, priority, valid)
        for seed in (7, 17, 27):
            torch.manual_seed(seed)
            out = instance.act(*data)
            self.assertTrue(torch.isfinite(out['logp']).all())
            self.assertTrue(torch.equal(out['action'][0, 17:21], torch.zeros(4)))
            self.assertTrue(torch.equal(out['action'][1, 19:21], torch.zeros(2)))
            self.assertTrue(torch.equal(out['action'][2, 17:21], out['latent'][2, 17:21].tanh()))
            self.assertTrue(torch.equal(out['action'][3], out['latent'][3].tanh()))
            expected = Normal(out['mean'][:, :33], out['log_std'][:, :33].exp()).log_prob(out['latent'][:, :33]).sum(-1)
            self.assertTrue(torch.equal(out['logp'], expected))
            self.assertTrue(torch.equal(instance.evaluate(*data, out['latent'])['logp'], expected))
        # 높이/방향 위반이면 정렬 단계로 되돌아간다.
        priority[2, 0, instance.gate_columns[2]] = .031/instance.gate_scales[2]
        self.assertEqual(int(instance.gate_stages(state, priority, valid)[2, 0]), 1)

    def test_lr_floor_recovery_reset_and_optimizer_persistence(self):
        trainer = ResearchTrainer(model('lr'), PPOConfig(retry_lr_factor=.5))
        trainer._retry_actor_lr(0)
        self.assertEqual(trainer.actor_optimizer.param_groups[0]['lr'], 1.5e-5)
        trainer._retry_actor_lr(2)
        self.assertEqual(trainer.actor_optimizer.param_groups[0]['lr'], 7.5e-6)
        def result(kl=.001, retries=0):
            return dict(actor_lr=trainer.actor_optimizer.param_groups[0]['lr'], analytic_kl=kl, kl_retries=retries)
        for _ in range(9): trainer.recover_learning_rate(result())
        before = trainer.actor_optimizer.state_dict()
        trainer.actor_optimizer.load_state_dict(before)
        out = trainer.recover_learning_rate(result())
        self.assertEqual(out['actor_lr'], 7.5e-6)
        self.assertAlmostEqual(out['press_research_lr']['next_lr'], 9.375e-6)
        self.assertEqual(out['press_research_lr']['recovery_reason'], 'ten_stable_updates_recover')
        trainer.recover_learning_rate(result())
        trainer.recover_learning_rate(result(.006))
        self.assertEqual(trainer.actor_optimizer.param_groups[0]['press_research_stable_updates'], 0)
        for _ in range(100): trainer.recover_learning_rate(result())
        self.assertEqual(trainer.actor_optimizer.param_groups[0]['lr'], 3e-5)

    def test_baseline_retry_unchanged_and_identity_rejects_cross_mode(self):
        base = ResearchTrainer(model('baseline'))
        base._retry_actor_lr(0)
        self.assertEqual(base.actor_optimizer.param_groups[0]['lr'], 7.5e-6)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'model.pt'
            base.save(path)
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                ResearchTrainer(model('exploration')).load(path)

    def test_all_modes_real_ppo_update_is_finite(self):
        for mode in ('baseline', 'exploration', 'lr', 'combined', 'sequential'):
            torch.manual_seed(7)
            instance = model(mode)
            data = inputs(8)
            with torch.no_grad(): out = instance.act(*data)
            buffer = {name: value.reshape((2, 4)+value.shape[1:]) for name, value in zip(
                ('state', 'events', 'mask', 'priority_events', 'priority_mask'), data)}
            for name in ('latent', 'logp', 'reward_value', 'cost_value'):
                value = out[name]
                buffer[name] = value.reshape((2, 4)+value.shape[1:])
            buffer.update(old_mean=out['mean'].reshape(2, 4, 39),
                old_log_std=out['log_std'].reshape(2, 4, 39),
                next_reward_value=torch.zeros(2, 4), next_cost_value=torch.zeros(2, 4),
                reward=torch.arange(8.).reshape(2, 4)/10, cost=torch.zeros(2, 4),
                terminated=torch.zeros(2, 4, dtype=torch.bool),
                truncated=torch.zeros(2, 4, dtype=torch.bool),
                valid=torch.ones(2, 4, dtype=torch.bool), duration=torch.ones(2, 4, dtype=torch.long))
            trainer = ResearchTrainer(instance, PPOConfig(epochs=1, minibatch_size=8,
                retry_lr_factor=.5 if instance.research['lr_recovery'] else .25))
            before_model = copy.deepcopy(instance.state_dict())
            before_rng = torch.get_rng_state()
            result = trainer.update(buffer)
            if mode == 'baseline':
                after_rng = torch.get_rng_state()
                parent = FingerSkillPolicy(557, size='small', contract=contract())
                parent.load_state_dict(before_model)
                parent_trainer = DecisionPPOTrainer(parent, trainer.config)
                torch.set_rng_state(before_rng)
                parent_result = parent_trainer.update(buffer)
                assert_tree(self, instance.state_dict(), parent.state_dict())
                assert_tree(self, trainer.actor_optimizer.state_dict(), parent_trainer.actor_optimizer.state_dict())
                assert_tree(self, trainer.value_optimizer.state_dict(), parent_trainer.value_optimizer.state_dict())
                self.assertTrue(torch.equal(after_rng, torch.get_rng_state()))
                self.assertEqual(result['actor_loss'], parent_result['actor_loss'])
            self.assertEqual(trainer.updates, 1)
            self.assertTrue(math.isfinite(result['actor_loss']))
            self.assertEqual(result['actor_lr'], result['press_research_lr']['used_lr'])
            self.assertTrue(all(torch.isfinite(p).all() for p in instance.parameters()))

    def test_all_finger_stage_count_reset_and_boundaries(self):
        instance = model('sequential')
        data = inputs()
        state, events, mask, priority, valid = data
        state.zero_(); priority.zero_(); valid.zero_()
        valid[:, ::2] = torch.eye(4, dtype=torch.bool)
        priority[:, ::2, instance.gate_columns[3]] = .5
        # 각 행에 서로 다른 손가락의 단일 목표를 둔다.
        instance.act(*data)
        diagnostic = instance.stage_diagnostics(reset=True)
        self.assertEqual(diagnostic['counts'], [[3, 0, 0, 1]]*4)
        self.assertEqual(diagnostic['exposure_s'][0][3], 1/60.)
        self.assertEqual(instance.stage_diagnostics()['counts'], [[0]*4]*4)
        self.assertFalse(any('stage_counts' in name for name in instance.state_dict()))
        # 모든 손가락에서 허용 영역 양쪽을 검사한다.
        for finger in range(4):
            slot = 2*finger
            for height, expected in ((-.00101, 1), (-.00099, 2), (.02999, 2), (.03001, 1)):
                priority[finger, slot, instance.gate_columns[2]] = height/instance.gate_scales[2]
                self.assertEqual(int(instance.gate_stages(state, priority, valid)[finger, finger]), expected)
            priority[finger, slot, instance.gate_columns[2]] = 0
            for tangent, expected in ((.00799, 2), (.00801, 1)):
                priority[finger, slot, instance.gate_columns[0]] = tangent/instance.gate_scales[0]
                self.assertEqual(int(instance.gate_stages(state, priority, valid)[finger, finger]), expected)
            priority[finger, slot, instance.gate_columns[0]] = 0
            state[finger, instance.wrist_indices[0]] = .01001/instance.wrist_scales[0]
            self.assertEqual(int(instance.gate_stages(state, priority, valid)[finger, finger]), 0)
            state[finger, instance.wrist_indices[0]] = 0

    def test_nested_copy_prepared_inputs_and_provenance_in_fresh_process(self):
        script = """
import json
from guitar_learning.tool.experiments.press_research import configuration, research_runtime
from guitar_learning.native import paths
original = paths.resolve_input_path
with research_runtime(configuration('baseline')):
    from guitar_learning.runtime.prepared_reset_v1 import BASELINE_CONFIG, load_gpu_prepared_reset_contract
    assert BASELINE_CONFIG.is_file(), str(BASELINE_CONFIG)
    assert json.loads(BASELINE_CONFIG.read_text())
    prepared = load_gpu_prepared_reset_contract('left')
    assert prepared['target105'].shape == (105,)
    assert prepared['initial_pose']['sha256'] == '568d88e9b963abb794d7f9cd89f6b7cdcca4d4137a5dd1f2aed2a42e9f090377'
    assert paths.resolve_input_path(BASELINE_CONFIG) == BASELINE_CONFIG.resolve()
    assert paths.resolve_input_path('/tmp/press_research_external') == original('/tmp/press_research_external')
assert paths.resolve_input_path is original
"""
        completed = subprocess.run([sys.executable, '-B', '-c', script],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)

    def test_research_output_settings_pins_and_checkpoint_snapshot(self):
        script = """
import json
import tempfile
from pathlib import Path
from guitar_learning.tool.experiments.press_research import configuration, research_runtime
from guitar_learning.native import paths
research = configuration('baseline')
with research_runtime(research):
    from guitar_learning.training.launch import settings_document
    from guitar_learning.training.finger_skill_runner import _pins
    from guitar_learning.training.training_log_io import write
    from guitar_learning.portability import checkpoint_inputs, validate_checkpoint_inputs, settings_digest, portable
    settings = settings_document(song='virtual_finger_v9_index_s3_f6', size='large', num_envs=64,
                                 horizon=32, updates=100, seed=7, checkpoint_every=1000)
    settings['press_research'] = research
    output_root = paths.ROOT.parent/'smoke'
    output_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cpu_settings_pins_', dir=str(output_root)) as temporary:
        out = Path(temporary)
        settings_path = out/'settings.json'
        write(settings_path, portable(settings))
        pins = _pins(settings, out)
        assert str(settings_path.resolve()) in pins
        assert paths.read(settings_path)['press_research'] == research
        record = checkpoint_inputs(pins, settings, settings_path=settings_path)
        assert record['run_settings']['original_identifier'] == str(settings_path.resolve())
        validate_checkpoint_inputs(dict(input_contract=record, settings=portable(settings),
                                        settings_sha256=settings_digest(settings)))
    for name in ('smoke', 'runs', 'rendering'):
        output = paths.ROOT.parent/name/'case'/'J'/'settings.json'
        assert paths.resolve_input_path(output) == output.resolve()
    # 허용 출력 디렉토리 밖의 원 프로젝트 입력은 기존 재배치 규칙을 유지한다.
    foreign = paths.HISTORICAL_ROOT/'guitar_learning/train.py'
    assert paths.resolve_input_path(foreign) == paths.ROOT/'guitar_learning/train.py'
"""
        completed = subprocess.run([sys.executable, '-B', '-c', script],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)

    def test_process_context_restores_factories_on_failure(self):
        from guitar_learning.training import finger_skill_runner, ppo
        from guitar_learning.native import paths
        resolver = paths.resolve_input_path
        original = (finger_skill_runner._policy, ppo.DecisionPPOTrainer)
        with self.assertRaises(RuntimeError):
            with research_runtime(configuration('baseline')):
                raise RuntimeError('test cleanup')
        self.assertEqual(original, (finger_skill_runner._policy, ppo.DecisionPPOTrainer))
        self.assertIs(paths.resolve_input_path, resolver)


if __name__ == '__main__':
    unittest.main()
