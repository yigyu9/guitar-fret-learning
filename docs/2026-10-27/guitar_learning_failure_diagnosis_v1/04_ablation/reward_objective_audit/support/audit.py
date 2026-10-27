"""Prescribed labels test reward arithmetic, not physical reachability or predicates."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

from guitar_learning.gpu.simplified_finger_environment import SimplifiedFingerEnvironment
from guitar_learning.tests.test_gpu_environment import BUNDLE, SONG, fixture


ROOT = Path(__file__).resolve().parents[6]
OUT = Path(__file__).resolve().parents[1]
CASES = ('full_clean', 'late_half_clean', 'brief_repeated', 'pre_onset_only',
         'missing_all', 'wrong_all', 'clean_then_wrong', 'clean_without_release')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    torch.set_num_threads(1)
    inputs = [Path(__file__)] + [ROOT/p for p in (
        'guitar_learning/gpu/environment.py', 'guitar_learning/gpu/finger_skill_environment.py',
        'guitar_learning/gpu/simplified_finger_environment.py',
        'guitar_learning/gpu/finger_reward.py', 'guitar_learning/tests/test_gpu_environment.py')]
    before = {str(p): sha(p) for p in inputs}
    metadata, snapshot = fixture(len(CASES))
    skill = dict(schema='guitar_learning.finger_skill.v2', phase='J', exploration='independent',
                 hold_ticks=1, scope='scheduled', planned_transitions=400, full_song_after=100)
    env = SimplifiedFingerEnvironment(metadata, bundle=BUNDLE, song=SONG, skill=skill, device='cpu')
    env.reset(range(len(CASES)), snapshot)
    target = next(i for i, t in enumerate(env.task.targets)
                  if t.target_id == 'event-000052/string-3/note-53')
    onset, end, press = [float(getattr(env, name)[target]) for name in ('onset', 'end', 'press')]
    duration = end-onset
    env.focus_mask.zero_(); env.focus_mask[:, target] = True
    env.finger_weights.zero_(); env.finger_weights[:, target] = 1.
    env.score_offset[:] = onset-3.
    env.duration_ticks[:] = round((3.+duration+.5)*60)
    env.candidate.zero_(); env.previous_candidate.zero_()
    env.wrong.zero_(); env.previous_wrong.zero_()

    def labels(_snapshot):
        now = float(env._score_time()[0])
        phase = (now-onset)/duration
        in_press = press <= now <= end
        audible = onset <= now <= end
        candidate = [press <= now <= end+1/240., audible and phase >= .5,
                     audible and int((now-onset)*240) % 8 < 4,
                     press <= now < onset, False, False,
                     in_press and phase < .5, now >= press]
        wrong = [False]*len(CASES)
        wrong[5] = audible
        wrong[6] = audible and phase >= .5
        env.candidate.zero_(); env.wrong.zero_()
        env.candidate[:, target] = torch.tensor(candidate)
        env.wrong[:, target] = torch.tensor(wrong)

    ticks = []
    zeros = torch.zeros(len(CASES), 39)
    with patch.object(env, '_snapshot', side_effect=labels), \
         patch.object(env, '_safety'), \
         patch.object(env, '_surface_potential', return_value=torch.zeros(len(CASES))):
        for _ in range(int(env.duration_ticks[0])):
            env.begin_control(zeros)
            for _ in range(4):
                env.substep(dict(snapshot, physics_step=env.clock+1))
            env.end_control()
            ticks.append([float(env._local_time()[0]),
                          *[float(env.episode_reward_terms[k][i])
                            for i in range(len(CASES)) for k in (
                                'song_left_contact', 'song_clean_hold', 'song_left_success',
                                'song_wrong_press', 'song_performance_deficit')]])
    terms = ('song_left_contact', 'song_clean_hold', 'song_left_success',
             'song_wrong_press', 'song_performance_deficit')
    rows = []
    for i, name in enumerate(CASES):
        rewards = {key: float(env.episode_reward_terms[key][i]) for key in terms}
        rows.append(dict(case=name, rewards=rewards, total=sum(rewards.values()),
            achieved=bool(env.note['left'][i, target]), released=bool(env.note['released'][i, target]),
            clean_ratio=float(env.note['clean'][i, target])/duration,
            wrong_ratio=float(env.note['wrong'][i, target])/duration,
            missing_ratio=float(env.note['missing'][i, target])/duration,
            best_streak_s=float(env.note['best_clean_streak'][i, target])))
    assert all(np.isfinite(row['total']) for row in rows)
    assert rows[0]['total'] > max(row['total'] for row in rows[1:7])
    assert rows[0]['achieved'] and rows[1]['achieved']
    assert not rows[2]['achieved'] and not rows[3]['achieved']
    assert abs(rows[0]['total']-rows[7]['total']) < 1e-7
    assert rows[0]['released'] and not rows[7]['released']
    for row in rows:
        for key, upper in zip(terms[:3], (.25, 1., .25)):
            assert -.000001 <= row['rewards'][key] <= upper+.000001
        assert -.150001 <= row['rewards'][terms[3]] <= 0
        assert -.100001 <= row['rewards'][terms[4]] <= 0
    counts = [sum(t.finger == finger for t in env.task.targets) for finger in range(1, 5)]
    balance = [len(env.task.targets)/(4*count) for count in counts]
    after = {str(p): sha(p) for p in inputs}
    assert before == after
    result = dict(scope='CPU prescribed candidate/wrong labels; no physics, geometry, PBRS, standby, thumb, action-change or failure-cost comparison',
        target_id=env.task.targets[target].target_id, duration_s=duration, press_s=press,
        onset_s=onset, required_s=float(env.required[target]), rows=rows,
        full_song=dict(counts=counts, weights=balance,
            two_index_clean_budget=2*1.5*balance[0], one_ring_clean_budget=1.5*balance[2],
            note='Comparison of positive task budgets only; other notes and penalties held equal.'),
        assertions_passed=True, inputs_unchanged=True, input_sha256=before)
    (OUT/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    np.savez_compressed(OUT/'timelines.npz', values=np.asarray(ticks), cases=CASES, terms=terms)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'axes.unicode_minus': False})
    names = ('정상 유지·해제', '후반 약 절반 clean', '짧은 접촉 반복', '음 시작 전 접촉만',
             '전부 누락', '전부 오압현', '전반 clean·후반 wrong', '정상 유지·해제 안 함')
    fig, ax = plt.subplots(figsize=(13, 6.8))
    positive = np.zeros(len(rows)); negative = np.zeros(len(rows))
    for term, label, color in zip(terms, ('최초 접촉', '압현 유지', '압현 달성', '오압현', '음 수행 부족'),
                                 ('#39a2db', '#44b87d', '#9b82ce', '#e47d6e', '#ad716a')):
        values = np.array([row['rewards'][term] for row in rows])
        ax.barh(names, values, left=np.where(values >= 0, positive, negative), label=label, color=color)
        positive += np.maximum(values, 0); negative += np.minimum(values, 0)
    for i, row in enumerate(rows):
        ax.text(positive[i]+.025, i, f"합계 {row['total']:.3f}", va='center', fontsize=10)
    ax.invert_yaxis(); ax.axvline(0, color='#445566', linewidth=.8)
    ax.set_xlim(-.36, 1.85); ax.set_xlabel('원곡 중지 한 음의 점수 (균형계수 b=1)')
    ax.set_title('지정한 접촉 시간표의 보상 계산 비교\n실제 물리·기하 검증이 아닌 산술 검사 / 접근·대기·엄지·행동·실패 비용 제외', loc='left')
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.13), ncol=5)
    ax.grid(axis='x', alpha=.2); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(OUT/'reward_ordering.png', dpi=150); plt.close(fig)
    print(json.dumps(dict(rows=rows, full_song=result['full_song'], verified=True), indent=2))


if __name__ == '__main__':
    main()
