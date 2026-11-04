"""봉인된 학습·평가·영상 원문에서 손가락 자세와 학습 추세를 재집계한다."""
import json
from pathlib import Path

import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
STUDY = OUT.parent
RENDER = STUDY / '결과검토_20261104/영상재검증'
FINGERS = ('index', 'middle', 'ring', 'pinky')
LABELS = ('검지', '중지', '약지', '소지')


def read(path):
    return json.loads(path.read_text())


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


pose = np.load(RENDER / 'poses_env0000.npz')
contract = read(RENDER / 'training_contract.json')
control = contract['action']['target_contract']
names = control['action_order']
native_ids = [control['joint_names'].index(n) for n in names]
reference = np.array(control['reference105_rad'])[native_ids]
lower, upper = (np.array(control[k]) for k in ('action_lower_rad', 'action_upper_rad'))
action = pose['action']
actual, applied = pose['q'][:, native_ids], pose['target'][:, native_ids]
requested = reference + np.where(action >= 0, upper-reference, reference-lower)*action
time = pose['time_s']
assert np.all(np.diff(time) > 0) and all(np.isfinite(pose[k]).all() for k in pose.files)
assert read(RENDER / 'report.json')['completed']
with (STUDY / '최종평가/episodes.jsonl').open() as stream:
    episodes = [json.loads(line)['episode'] for line in stream]
with (STUDY / '학습/J/learning_metrics.jsonl').open() as stream:
    metrics = [json.loads(line) for line in stream]

samples = []
for second in (.5, 2., 5., 10., 15., 25., 32.8):
    i = int(np.argmin(abs(time-second)))
    samples.append(dict(time_s=float(time[i]), actual_deg=np.rad2deg(actual[i, 12:33]).tolist(),
        applied_deg=np.rad2deg(applied[i, 12:33]).tolist(), action=action[i, 12:33].tolist()))

finger_rows = []
for finger in FINGERS:
    ids = [i for i, n in enumerate(names) if n.startswith('LH:'+finger)]
    per_joint = np.array([e['finger_control_diagnostics']['values']['applied_tracking_error_rad_rms'] for e in episodes])
    relative_ids = [i-12 for i in ids]
    finger_rows.append(dict(finger=finger,
        action_mean=action[:, ids].mean(0).tolist(),
        action_std_over_time=action[:, ids].std(0).tolist(),
        actual_after_1s_min_deg=np.rad2deg(actual[time >= 1][:, ids].min(0)).tolist(),
        actual_after_1s_max_deg=np.rad2deg(actual[time >= 1][:, ids].max(0)).tolist(),
        applied_tracking_rms_deg=np.rad2deg(per_joint[:, relative_ids].mean(0)).tolist()))

checkpoints = []
train = STUDY / '학습/J'
for path in [train/'initial.pt', *sorted(train.glob('checkpoint_*.pt')), train/'final.pt']:
    checkpoint = torch.load(path, map_location='cpu', weights_only=False)
    std = checkpoint['model']['log_std'].exp().numpy()
    assert all(bool(torch.isfinite(v).all()) for v in checkpoint['model'].values())
    checkpoints.append(dict(file=path.name, updates=checkpoint['updates'],
        support_std_mean=float(std[:17].mean()), finger_std_mean=float(std[17:].mean()),
        finger_std_min=float(std[17:].min()), finger_std_max=float(std[17:].max())))

# 3.5GiB 에피소드 원문을 한 줄씩 읽어 전체를 메모리에 올리지 않는다.
buckets = {}
for line in (train/'episodes.jsonl').open():
    row = json.loads(line)
    episode, bucket_id = row['episode'], row['update_index']//100
    if bucket_id not in buckets:
        buckets[bucket_id] = dict(count=0, action_samples=0, action_sum=np.zeros(21),
            actual_min_sum=np.zeros(21), actual_max_sum=np.zeros(21), achieved_sum=0.,
            reward_sum={}, physical_failure=0)
    bucket = buckets[bucket_id]
    motion = episode['left_finger_motion']
    values, weight = motion['values'], motion['action_samples']
    bucket['count'] += 1
    bucket['action_samples'] += weight
    bucket['action_sum'] += np.array(values['action_mean'])*weight
    bucket['actual_min_sum'] += values['actual_min_rad']
    bucket['actual_max_sum'] += values['actual_max_rad']
    bucket['achieved_sum'] += episode['song']['left_success_count']
    bucket['physical_failure'] += episode['termination']['physical_failure']
    for key, value in episode['reward_components'].items():
        bucket['reward_sum'][key] = bucket['reward_sum'].get(key, 0.)+value
training_rows = []
for index, bucket in sorted(buckets.items()):
    n = bucket['count']
    training_rows.append(dict(first_update=index*100+1, last_update=min((index+1)*100, len(metrics)),
        episodes=n, action_mean=(bucket['action_sum']/bucket['action_samples']).tolist(),
        episode_actual_min_mean_deg=np.rad2deg(bucket['actual_min_sum']/n).tolist(),
        episode_actual_max_mean_deg=np.rad2deg(bucket['actual_max_sum']/n).tolist(),
        mean_achieved=bucket['achieved_sum']/n,
        mean_reward_components={k:v/n for k,v in bucket['reward_sum'].items()},
        physical_failure_fraction=bucket['physical_failure']/n))

lr_changes = []
for row in metrics:
    if not lr_changes or row['actor_lr'] != lr_changes[-1]['actor_lr']:
        lr_changes.append(dict(update=row['optimizer_updates'], actor_lr=row['actor_lr']))
reward_means = {key:float(np.mean([e['reward_components'][key] for e in episodes]))
                for key in episodes[0]['reward_components']}
summary = dict(joint_names=names[12:33], representative_environment=0,
    finite_pose=True, mean_action_abs_ge098_fraction=float(np.mean(abs(action[:,12:33]) >= .98)),
    actual_or_target_native_limit_fraction_max=max(
        max(e['left_finger_motion']['values'][key]) for e in episodes
        for key in ('actual_native_limit_fraction', 'target_native_limit_fraction')),
    snapshots=samples, fingers=finger_rows, checkpoints=checkpoints,
    actor_lr_changes=lr_changes, training_windows=training_rows,
    evaluation_mean_rewards=reward_means,
    diagnostics_scope='Native joint coordinates are not anatomical MCP/PIP/DIP angles; recorded geometric posture diagnostics are separate. Training action means include exploration and unequal episode lengths.')
write('diagnosis.json', summary)

plt.rcParams.update({'font.family':'NanumGothic', 'axes.unicode_minus':False, 'font.size':10})
fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True, constrained_layout=True)
for f, (finger, label) in enumerate(zip(FINGERS, LABELS)):
    ids = [names.index('LH:'+finger+suffix) for suffix in ('1_x','2','3')]
    for column, (joint, color) in enumerate(zip(('시작 굽힘축','가운데 관절','끝 관절'), ('#2878B5','#DF8F44','#699C42'))):
        axes[f].plot(time, np.rad2deg(actual[:,ids[column]]), color=color, label=joint+' 실제')
        axes[f].plot(time, np.rad2deg(applied[:,ids[column]]), color=color, ls='--', alpha=.65, linewidth=1)
    axes[f].set(ylabel=label+' 관절각 (도)', ylim=(-45,100))
    axes[f].axhline(0, color='grey', linewidth=.6)
    axes[f].grid(alpha=.2)
axes[0].legend(ncol=3, loc='upper right')
axes[-1].set_xlabel('에피소드 시간 (초)')
fig.suptitle('대표 환경0: 실제각(실선)과 적용 목표각(점선)\n시뮬레이터 관절 좌표 · 목표각을 따라 어색한 손 모양을 유지', fontsize=14)
fig.savefig(OUT/'관절각과목표각.png', dpi=170)
plt.close(fig)

fig, axes = plt.subplots(2, 1, figsize=(11,8), constrained_layout=True)
for relative_index, name in ((5,'검지 시작'),(13,'약지 시작'),(15,'약지 가운데'),(16,'약지 끝')):
    axes[0].plot([w['last_update'] for w in training_rows], [w['action_mean'][relative_index] for w in training_rows], marker='o', label=name)
axes[0].set(title='학습 중 관절별 평균 행동: 100회 구간, 행동 표본 수로 가중',ylabel='직접 목표각 행동 (-1~1)',ylim=(-1,1))
axes[0].axvline(357, color='grey', ls=':', label='전곡 노출 전환 시작')
axes[0].legend(ncol=3);axes[0].grid(alpha=.2)
axes[1].plot([x['updates'] for x in checkpoints], [x['finger_std_mean'] for x in checkpoints], marker='o',color='#2878B5',label='검지~소지 평균 탐색 표준편차')
axes[1].set(xlabel='학습 반복',ylabel='tanh 이전 잠재 Gaussian 표준편차',ylim=(0,.4))
axes[1].legend();axes[1].grid(alpha=.2)
fig.suptitle('검지는 펴는 방향, 약지는 시작을 굽히고 끝을 펴는 방향으로 편향',fontsize=14)
fig.savefig(OUT/'학습중관절편향.png',dpi=170)
plt.close(fig)
print(json.dumps(dict(episodes=sum(w['episodes'] for w in training_rows), actor_lr_changes=lr_changes,
    final_training_action_mean=training_rows[-1]['action_mean'], output=str(OUT)),ensure_ascii=False))
