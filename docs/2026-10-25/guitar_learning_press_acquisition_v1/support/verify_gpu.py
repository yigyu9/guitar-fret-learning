"""Audit real v19 episodes, the v18 control, exact resume, and old rejection."""
import copy
import json
from pathlib import Path
import random
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import numpy as np
import torch

from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.training.gpu_log_records import iter_episode_rows
from guitar_learning.training.ppo import PPOConfig, PPOTrainer


PHASE = Path(__file__).resolve().parents[1]
torch.set_num_threads(1)


def load(path):
    return torch.load(path, map_location='cpu', weights_only=False)


def equal(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and np.array_equal(a, b)
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return type(a) == type(b) and len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def main():
    old = PHASE/'baseline_v18'
    new = PHASE/'gpu_v19'
    before = json.loads((old/'training_contract.json').read_text())
    after = json.loads((new/'training_contract.json').read_text())
    for field in ('action', 'task', 'termination', 'native_backend', 'diagnostics'):
        assert before[field] == after[field], field
    for field in before['observation']:
        if field not in ('event_fields', 'first_contact', 'surface_geometry'):
            assert before['observation'][field] == after['observation'][field], field
    for field in before['reward']:
        if field not in ('schema', 'surface_learning'):
            assert before['reward'][field] == after['reward'][field], field
    first0, first1 = load(old/'initial.pt'), load(new/'initial.pt')
    assert equal(first0['model'], first1['model'])
    assert after['reward']['schema'] == 'guitar_learning.gpu_tensor_song_reward.v19'
    assert after['observation']['event_scales'][12:14] == [1., 1.]

    episodes = [r['episode'] for r in iter_episode_rows(new)]
    assert len(episodes) == 16
    counts = [f['target_count'] for f in episodes[0]['left_curriculum']['finger_metrics']]
    # Ledger order is the unchanged task order; obtain finger assignments from
    # the real source task rather than inferring them from contact statistics.
    from guitar_learning.song.task import make_task
    settings = json.loads((new/'settings.json').read_text())
    task = make_task(settings['song_training']['bundle'],
        pre_roll_s=settings['song']['pre_roll_s'], tail_s=settings['song']['tail_s'])
    weights = np.array([len(task.targets)/(sum(n > 0 for n in counts)*counts[t.finger-1])
                        for t in task.targets])
    errors = []
    partial = complete = safe = 0
    failures = []
    for episode in episodes:
        ledger = episode['left_note_ledger']
        assert ledger['schema'] == 'guitar_learning.surface_note_ledger.v7'
        assert ledger['target_ids'] == [t.target_id for t in task.targets]
        values = ledger['values']
        best = np.array(values['best_contact_streak'])
        progress = np.array(values['contact_progress'])
        tau = np.array([min(.05, t.end_s-t.press_s) for t in task.targets])
        np.testing.assert_allclose(progress, np.minimum(best/tau, 1), atol=1e-12, rtol=0)
        assert episode['left_curriculum']['progress'] == 0
        stage_weight = episode['left_curriculum']['weights']['contact']
        expected = .5*stage_weight*np.sum(weights*progress)
        received = episode['reward_components']['song_left_contact']
        if episode['reason'] == 'timeline_complete':
            safe += 1
            errors.append(abs(expected-received))
            assert abs(expected-received) < 1e-5
        else:
            assert episode['reason'] == 'terminal_failure'
            assert 0 <= received <= expected+1e-5
            failures.append(dict(env_id=episode['env_id'], time_s=episode['task_time_s'],
                reasons=episode['failure_reasons'],
                consumed_budget_minus_received=expected-received))
        partial += int(((progress > 0) & (progress < 1)).sum())
        complete += sum(values['contact_done'])
    assert partial > 0, 'Must exercise real partial-contact credit'

    source = load(new/'final.pt')
    initial = load(PHASE/'gpu_v19_resume/initial.pt')
    final = load(PHASE/'gpu_v19_resume/final.pt')
    restored = {k: equal(source[k], initial[k]) for k in source if k != 'metadata'}
    assert all(restored.values())
    assert (initial['updates'], final['updates']) == (65, 66)
    changed = {k: not equal(initial[k], final[k])
               for k in ('model', 'actor_optimizer', 'value_optimizer')}
    assert all(changed.values())
    policy = SpecialistPolicy(544, size='small', role='left', contract=after)
    CurriculumCoordinator(policy, SimpleNamespace(environment=SimpleNamespace(finger_counts=counts)))
    trainer = PPOTrainer(policy, PPOConfig(**settings['ppo']))
    state0 = copy.deepcopy((policy.state_dict(), trainer.actor_optimizer.state_dict(),
        trainer.value_optimizer.state_dict(), trainer.updates, trainer.cost_weight,
        torch.get_rng_state(), np.random.get_state(), random.getstate()))
    try:
        trainer.load(old/'final.pt')
    except ValueError as error:
        assert 'mismatch' in str(error)
    else:
        raise AssertionError('Real v18 must be rejected')
    state1 = (policy.state_dict(), trainer.actor_optimizer.state_dict(),
        trainer.value_optimizer.state_dict(), trainer.updates, trainer.cost_weight,
        torch.get_rng_state(), np.random.get_state(), random.getstate())
    assert equal(state0, state1)
    result = dict(verified=True, original_physics_control_success_B_PPO_preserved=True,
        initial_model_exact=True, completed_episodes=len(episodes), safe_completed_episodes=safe,
        failed_episodes=failures,
        real_partial_contact_notes=partial, real_completed_contact_notes=complete,
        maximum_stage_weighted_contact_ledger_error=max(errors),
        resume_nonmetadata_exact=restored, resumed_update_changed=changed,
        real_v18_rejected_without_mutation=True,
        scope='Implementation and recording checks; small-run learning results do not establish convergence or improvement')
    (PHASE/'gpu_verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
