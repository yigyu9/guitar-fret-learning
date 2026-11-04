"""실제 체크포인트·로그와 CPU 최소 예제로 실행/PPO 경로를 감사한다.

원본은 읽기만 하며 이 디렉토리의 audit.json만 쓴다. 학습·GPU 실험이 아니다.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

import torch

OUT = Path(__file__).resolve().parent
ROOT = next(p for p in OUT.parents if (p / 'guitar_learning').is_dir())
sys.path.insert(0, str(ROOT))
V4 = ROOT / 'docs/2026-11-09/압현_보상개선_v4/검증'
V2 = ROOT / 'docs/2026-11-09/압현_상태443_목표16/전곡학습_7시간_결합512_v2'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checkpoint(directory, name):
    """출력 manifest와 일치하는 저장본만 CPU로 읽는다. 모델 실행/변환은 하지 않는다."""
    path = directory / name
    manifest = [json.loads(x) for x in (directory / 'checkpoint_manifest.jsonl').read_text().splitlines()]
    recorded = next(row for row in manifest if row['path'] == name)
    actual = sha(path)
    assert actual == recorded['sha256'], 'checkpoint SHA 불일치'
    payload = torch.load(path, map_location='cpu', weights_only=False)
    std = payload['model']['log_std'].exp()
    groups = {}
    for group, first, last in (('arm12', 0, 12), ('thumb5', 12, 17), ('finger16', 17, 33)):
        values = std[first:last]
        groups[group] = dict(mean=float(values.mean()), min=float(values.min()), max=float(values.max()))
    return dict(path=str(path.relative_to(ROOT)), sha256=actual, manifest_sha_verified=True,
        optimizer_updates=payload['updates'], settings_initial_std=payload['metadata']['settings']['initial_std'],
        custom_initialization=payload['metadata']['settings'].get('song_run_initialization'), std=groups)


torch.set_num_threads(1)
torch.manual_seed(7)
native_settings = read(V4 / 'native_train/J/settings.json')
pins = read(V4 / 'native_train/J/inputs_before.json')
sources = ['tool/experiments/compact_press_v4.py', 'tool/experiments/compact_press_v3.py',
    'training/compact_press.py', 'training/compact_press_v3.py', 'training/policy.py',
    'training/rollout.py', 'training/ppo.py', 'training/finger_skill_runner.py',
    'training/launch.py', 'training/training_log_io.py', 'gpu/compact_press_v4.py',
    'tests/test_compact_press_v3_policy.py', 'tests/test_finger_decisions.py']
source_checks = {}
for source in sources:
    path = ROOT / 'guitar_learning' / source
    current = sha(path)
    assert pins.get(str(path)) == current, 'native 검증 적용 소스 변경: ' + source
    source_checks[source] = current

from guitar_learning.training.ppo import compute_decision_gae, DecisionPPOTrainer, PPOConfig
from guitar_learning.training.compact_press_v3 import CompactPressV3Policy
from guitar_learning.training.rollout import DecisionCollector
from guitar_learning.training.finger_skill_runner import ExposureSchedule
from guitar_learning.tests.test_compact_press_v3_policy import contract, inputs
from guitar_learning.tests.test_finger_decisions import TinyDecisionPolicy, FakeDecisionPool
from guitar_learning.gpu.compact_press_v4 import reward_configuration

gamma, lam = native_settings['ppo']['gamma'], native_settings['ppo']['gae_lambda']
discounts = [dict(seconds=s, ticks=round(s * 60), reward_discount=gamma ** round(s * 60),
                  gae_residual_discount=(gamma * lam) ** round(s * 60))
             for s in (.25, .5, 1., 2., 3., 10., 30.)]
count = 180
rewards = torch.zeros(count, 1)
rewards[120] = 1.
zero = torch.zeros_like(rewards)
flags = torch.zeros_like(rewards, dtype=torch.bool)
duration = torch.ones_like(rewards, dtype=torch.long)
valid = torch.ones_like(flags)
full, _ = compute_decision_gae(rewards, zero, zero, flags, flags, duration, valid, gamma, lam)
short, _ = compute_decision_gae(*(v[:32] for v in (rewards, zero, zero, flags, flags, duration, valid)), gamma, lam)
assert short[0, 0] == 0 and full[0, 0] > 0

spec = contract()
spec['reward'] = dict(schema='guitar_learning.compact_press_reward.v4',
    compact_press_v4=reward_configuration('combined'))
model = CompactPressV3Policy(452, contract=spec)
data = list(inputs())
data[4][:, 1::2] = False
data[3].requires_grad_()
initial_mean = model(*data)['mean']
initial_goal_grad = torch.autograd.grad(initial_mean[:, :33].sum(), data[3])[0]
assert initial_goal_grad.count_nonzero() == 0
with torch.no_grad():
    model.actor_head.weight.normal_(0, .01)
mean = model(*data)['mean']
gradient = torch.autograd.grad(mean[:, :33].sum(), data[3])[0]
assert gradient[data[4]].abs().sum() > 0 and gradient[~data[4]].count_nonzero() == 0
before = model(*data)
data[3] = data[3].detach().clone()
data[3][~data[4]] = float('nan')
after = model(*data)
for key in before:
    torch.testing.assert_close(before[key], after[key], rtol=0, atol=0)
actor_ids = {id(p) for p in model.actor_parameters()}
value_ids = {id(p) for p in model.value_parameters()}
assert not actor_ids.intersection(value_ids)

# 원본 재시도 함수를 호출하되 학습하지 않는다. 같은 minibatch의 before 상태로 복원한다.
trainer = DecisionPPOTrainer(model, PPOConfig(lambda_lr=0.))
snapshot = trainer._actor_snapshot()
attempts = []
for retry in range(3):
    trainer._actor_restore(snapshot)
    trainer._retry_actor_lr(retry)
    attempts.append(trainer.actor_optimizer.param_groups[0]['lr'])

pool = FakeDecisionPool(failure=False)
collector = DecisionCollector(TinyDecisionPolicy(), pool)
collector.collect(16)
first_clock = pool.clock.tolist()
buffer, _ = collector.collect(16)
assert pool.clock.tolist() == [32., 32.] and not pool.resets
assert bool((buffer['duration'] == 1).all()) and bool(buffer['valid'].all())

metrics_path = V2 / '학습/J/learning_metrics.jsonl'
metrics = [json.loads(x) for x in metrics_path.read_text().splitlines()]
changes = [dict(update=row['optimizer_updates'], actor_lr=row['actor_lr'], kl_retries=row['kl_retries'])
           for i, row in enumerate(metrics) if i == 0 or row['actor_lr'] != metrics[i - 1]['actor_lr']]
last = metrics[-1]
recent = metrics[-100:]
recent_count = sum(x['episode_summary']['count'] for x in recent)
recent_failures = sum(x['episode_summary'].get('physical_failure', 0) for x in recent)
native_metrics = [json.loads(x) for x in (V4 / 'native_train/J/learning_metrics.jsonl').read_text().splitlines()]
native_report = read(V4 / 'native_train/J/report.json')
schedule = ExposureSchedule(native_settings['finger_skill']['planned_transitions'])
schedule.commit(native_settings['num_envs'] * native_settings['horizon'])
assert schedule.status()['next_reset_scope'] == 'full_song'

result = dict(schema='compact_press_training_audit.v1',
    scope='원문 체크포인트/로그 읽기 + CPU 합성 경로 검사; 새로운 물리/학습 실험 없음',
    applied_sources_sha256=source_checks,
    checkpoints=[checkpoint(folder, name) for folder in (V4 / 'native_train/J', V2 / '학습/J')
                 for name in ('initial.pt', 'final.pt')],
    temporal=dict(horizon=native_settings['horizon'], control_hz=60,
        direct_rollout_seconds=native_settings['horizon'] / 60,
        gamma=gamma, gae_lambda=lam, cost_gamma=native_settings['ppo']['cost_gamma'],
        reward_discount_time_constant_s=-1 / math.log(gamma) / 60,
        gae_residual_time_constant_s=-1 / math.log(gamma * lam) / 60,
        weights=discounts, reward_at_tick120=dict(full180_start_advantage=float(full[0, 0]),
            first32_start_advantage=float(short[0, 0]), critic_bootstrap='둘 모두0으로 둔 합성 비교')),
    gradient=dict(actor_parameters=sum(p.numel() for p in model.actor_parameters()),
        value_parameters=sum(p.numel() for p in model.value_parameters()), initial_actor_head='zero, therefore initial actor encoder gradient is zero before first head update',
        initial_goal_gradient_l1=float(initial_goal_grad.abs().sum()),
        nonzero_head_valid_goal_gradient_l1=float(gradient[data[4]].abs().sum()),
        invalid_goal_gradient_l1=float(gradient[~data[4]].abs().sum()),
        invalid_nan_payload_outputs_identical=True, actor_value_parameters_disjoint=True,
        note='정책망 경로 검사이며 실제 학습된 정책이 목표를 충분히 활용한다는 증거는 아님'),
    lr_retry=dict(base=3e-5, same_minibatch_restore_then_retry=attempts,
        recovery_floor=False, entropy_bonus=False, exploration_recovery=False),
    rollout=dict(first16_clock=first_clock, next16_clock=pool.clock.tolist(), resets=pool.resets,
        duration_per_decision=1, h_boundary_terminates_episode=False),
    previous_v2_long_run=dict(metrics_path=str(metrics_path.relative_to(ROOT)), sha256=sha(metrics_path),
        updates=len(metrics), lr_changes=changes, total_kl_retries=sum(x['kl_retries'] for x in metrics),
        last_accepted_kl=last['analytic_kl'], last_clip_fraction=last['diagnostics']['post_update']['clip_fraction'],
        last_critics=last['diagnostics']['post_update']['critics'],
        exposure=last['cumulative_exposure_transitions'],
        last100=dict(updates=len(recent), completed_episodes=recent_count, physical_failures=recent_failures,
            physical_failure_fraction=recent_failures / recent_count,
            reward_advantage_std_mean=sum(x['diagnostics']['advantages']['reward_raw']['std'] for x in recent) / len(recent),
            cost_advantage_std_mean=sum(x['diagnostics']['advantages']['cost_raw']['std'] for x in recent) / len(recent),
            note='확률 학습의 완결 episode 집계; 평균정책 평가와 구분')), 
    v4_native_smoke=dict(updates=len(native_metrics), full_song_next_reset_after_update1=True,
        actual_exposure=native_report['exposure_transitions'], final_lr=native_metrics[-1]['actor_lr'],
        note='4회 갱신/2.13초로 episode reset에 미도달, 전곡 노출0은 예정 동작. 성과 평가에는 짧음'),
    checkpoint_selection=dict(automatic_best=False, saved=['initial', 'periodic', 'final', 'recovery'],
        evaluation_policy='deterministic mean', training_policy='stochastic tanh Normal',
        note='공용 학습기는 평가 결과 기반 best 선정이나 정책 조기종료를 하지 않음'))
(OUT / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
print(json.dumps(dict(checkpoints_sha_verified=4, sources_checked=len(source_checks),
    invalid_slot_gradient=0., lr_changes=changes, direct_rollout_seconds=32 / 60), ensure_ascii=False))
