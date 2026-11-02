"""Validate native teacher eligibility, full frame alignment and actor isolation."""
import copy
from pathlib import Path
import sys
import json
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import teacher_bootstrap as teacher
import numpy as np
import torch


class TeacherBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.plan = teacher.build_plan()
        cls.plan['sealed'] = True  # In-memory validator fixture; no executable plan is written.
        cls.data, cls.source, cls.target = teacher.load_teacher(cls.plan)
        capture = teacher.SOURCE/'capture'
        cls.report, cls.guard, cls.episode, cls.metadata = [teacher.read(p) for p in
            (capture/'report.json', teacher.SOURCE/'guard_report.json',
             capture/'episode_env0000.json', capture/'metadata.json')]
        with np.load(capture/'poses_env0000.npz', allow_pickle=False) as file:
            cls.poses = {k: file[k].copy() for k in file.files}

    def test_only_two_explicit_exposure_budget_fields_are_projected(self):
        source = copy.deepcopy(self.source)
        projected = teacher.target_contract(source)
        self.assertEqual(source, self.source)
        projected['task']['finger_skill']['planned_transitions'] = 1280
        projected['task']['finger_skill']['full_song_after'] = 320
        self.assertEqual(projected, source)
        wrong = copy.deepcopy(source)
        wrong['reward']['natural_preparation'] = dict(condition='E4')
        with self.assertRaises(ValueError):
            teacher.target_contract(wrong)

    def test_successful_native_teacher_is_complete_and_guarded(self):
        teacher.validate_evidence(self.report, self.guard, self.episode, self.metadata)
        teacher.validate_arrays(self.data, self.poses, self.source)
        self.assertEqual(self.data['state'].shape, (330, 557))

    def test_individual_latches_and_partial_failure_are_not_eligible(self):
        for change in ('joint', 'guard', 'partial', 'injection', 'targets'):
            report, guard, episode, metadata = copy.deepcopy(
                (self.report, self.guard, self.episode, self.metadata))
            if change == 'joint':
                episode['simultaneous_press']['clean_s'] = 0.
            elif change == 'guard':
                guard['final_state_verified'] = False
            elif change == 'partial':
                episode['steps'] = 329
            elif change == 'injection':
                metadata['no_mid_episode_state_injection'] = False
            else:
                episode['simultaneous_press']['target_ids'] = ['different', 'targets']
            report['episode'] = episode
            with self.subTest(change=change), self.assertRaises(ValueError):
                teacher.validate_evidence(report, guard, episode, metadata)

    def test_pre_action_alignment_consecutive_physics_and_all330_rows_are_required(self):
        for change in ('drop', 'action', 'clock', 'alignment'):
            data = {k: v.copy() for k, v in self.data.items()}
            poses = {k: v.copy() for k, v in self.poses.items()}
            if change == 'drop':
                data = {k: v[:-1] for k, v in data.items()}
            elif change == 'action':
                data['action'][100, 17] += .01
            elif change == 'clock':
                poses['physics_step'][100] += 1
            else:
                field = self.source['observation']['fields'].index('music.elapsed_s')
                data['state'][:, field] += 1/330.
            with self.subTest(change=change), self.assertRaises(ValueError):
                teacher.validate_arrays(data, poses, self.source)

    def test_one_supervised_actor_update_leaves_std_critics_and_buffers_fresh(self):
        policy = teacher.new_policy(self.target)
        actors = teacher.actor_parameters(policy)
        before = {k: v.clone() for k, v in policy.state_dict().items()}
        optimizer = torch.optim.Adam(list(actors.values()), lr=teacher.BUDGET['actor_lr'])
        batch = teacher.tensors({k: v[150:152] for k, v in self.data.items()})
        loss = (teacher.prediction(policy, batch)[:, :33]-batch['action'][:, :33]).square().mean()
        optimizer.zero_grad(set_to_none=True); loss.backward(); optimizer.step()
        changed = {k for k, v in policy.state_dict().items() if not torch.equal(before[k], v)}
        self.assertTrue(changed)
        self.assertTrue(changed <= set(actors))
        self.assertFalse(any('log_std' in k or 'critic' in k or 'value_encoder' in k for k in changed))
        self.assertGreater(float(loss.detach()), 0.)

    def test_unsealed_plan_and_corrupted_hash_are_rejected(self):
        plan = copy.deepcopy(self.plan); plan['sealed'] = False
        with self.assertRaises(ValueError):
            teacher.load_teacher(plan)
        plan = copy.deepcopy(self.plan)
        plan['pins'][str(teacher.SOURCE/'capture/teacher_observations.npz')] = '0'*64
        with self.assertRaises(ValueError):
            teacher.load_teacher(plan)

    def test_actor_artifact_roundtrip_preserves_fresh_critic_std_and_checks_full_contract_sha(self):
        source_policy = teacher.new_policy(self.target)
        with torch.no_grad():
            source_policy.support_head.bias.fill_(.01)
        policy = teacher.new_policy(self.target)
        frozen = {k: v.clone() for k, v in policy.state_dict().items()
                  if k not in teacher.actor_parameters(policy)}
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            plan_path = directory/'plan.json'; plan_path.write_text(json.dumps(self.plan))
            artifact = dict(schema='multi_press.teacher_actor_initialization.v1', condition='B1', environment='E0',
                architecture=teacher.portable(source_policy.architecture),
                contract_projection=teacher.PROJECTION, source_contract=self.source, contract=self.target,
                actor_state={k: v.detach() for k, v in teacher.actor_parameters(source_policy).items()},
                lineage=dict(plan=str(plan_path), plan_sha256=teacher.sha(plan_path), source_sha256=self.plan['pins']))
            path = directory/'actor.pt'; torch.save(artifact, path)
            teacher.load_actor_artifact(policy, path, self.target, teacher.sha(path))
            self.assertTrue(torch.equal(policy.support_head.bias, source_policy.support_head.bias))
            self.assertTrue(all(torch.equal(policy.state_dict()[k], v) for k, v in frozen.items()))
            wrong = copy.deepcopy(self.target); wrong['termination']['failure_cost']['base'] += 1
            with self.assertRaises(ValueError):
                teacher.load_actor_artifact(policy, path, wrong, teacher.sha(path))
            with self.assertRaises(ValueError):
                teacher.load_actor_artifact(policy, path, self.target, '0'*64)


if __name__ == '__main__':
    unittest.main()
