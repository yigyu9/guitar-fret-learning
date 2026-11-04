"""활성 코드는 수정하지 않는 CPU 보상 구조 감사. 학습/물리 성공 실험이 아니다."""
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

import torch

OUT = Path(__file__).resolve().parent
ROOT = next(p for p in OUT.parents if (p/'guitar_learning').is_dir())
sys.path.insert(0, str(ROOT))
from guitar_learning.gpu.compact_press_v4 import CompactPressV4Environment
from guitar_learning.gpu.finger_skill_environment import performance_settlement
from guitar_learning.song.task import ScoreTask, ScoreTarget, make_task
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE
from guitar_learning.tests.test_compact_press_environment import SKILL

torch.set_num_threads(1)


def environment(profile):
    class Environment(CompactPressV4Environment):
        reward_profile = profile
    targets = (
        ScoreTarget('a', 'a', 0, 6, 1, 1, 3., 3.5, 2.9, 3., 3.5),
        ScoreTarget('b', 'b', 1, 8, 2, 1, 5., 5.5, 4.9, 5., 5.5),
    )
    metadata, snapshot = fixture(2)
    with patch('guitar_learning.gpu.environment.make_task', return_value=ScoreTask(targets)):
        env = Environment(metadata, bundle=BUNDLE, song=SONG, skill=SKILL, device='cpu')
    env.set_evaluation(True, full_song=True)
    env.reset([0, 1], snapshot)
    env.clock[:] = 732  # 3.05초, B는 2초 미리보기 안이지만 준비 lead보다 이전.
    return env


def preview_signal(profile):
    env = environment(profile)
    state = env._natural_state(env._score_time())
    assert state['valid'][0, 1] and int(state['selected'][0, 1]) == 1
    state['distance'] = torch.full_like(state['distance'], .10)
    state['alignment'] = torch.ones_like(state['alignment'])
    state['blend'] = torch.zeros_like(state['blend'])
    # 실제 환경의 potential 함수를 호출하되 B의 거리만 바꾸어 편미분을 검사한다.
    # 상태는 합성 측정값이며 도달 가능성이나 실제 행동 궤적을 증명하지 않는다.
    env._natural_state = lambda now: state
    before = env._surface_potential().clone()
    state['distance'][:, 1] = .08
    after = env._surface_potential().clone()
    posture = env._finger_preparation(env._score_time())
    return dict(target_exposed=True, onset_remaining_s=1.95,
        press_remaining_s=1.85, standby_gate=float(posture['standby_reward_gate'][0, 1]),
        distance_before_m=.10, distance_after_m=.08,
        potential_change=float((after-before)[0]))


preview = {p: preview_signal(p) for p in ('baseline', 'timing', 'combined')}
assert preview['baseline']['potential_change'] > 0
assert preview['timing']['potential_change'] == 0
assert preview['combined']['potential_change'] == 0

# 실제 정산 helper를 사용한다. 나머지는 계약상의 음별 예산을 대입한 해석식이다.
partial = []
for fraction in (0., .4, 1.):
    duration, best = 1., fraction
    paid, settled, increment = performance_settlement(
        torch.tensor([[1-fraction]], dtype=torch.float64),
        torch.tensor([[best]], dtype=torch.float64),
        torch.tensor([.4], dtype=torch.float64), torch.tensor([duration], dtype=torch.float64),
        torch.ones(1, 1), torch.ones(1, 1, dtype=torch.bool),
        torch.tensor([4.], dtype=torch.float64), torch.tensor([4.], dtype=torch.float64),
        torch.zeros(1, 1), torch.zeros(1, 1, dtype=torch.bool))
    achieved = best >= .4
    contact = .25 if fraction else 0.
    result = contact+fraction+.25*achieved-float(paid[0, 0])
    partial.append(dict(note_duration_s=1., continuous_clean_s=best,
        missing_s=1-fraction, achievement=achieved, strict_note_success=best >= 1.,
        first_contact_reward=contact, clean_reward=fraction,
        achievement_reward=.25*achieved, performance_penalty=-float(paid[0, 0]),
        task_reward_without_potential_standby_thumb_action=result))
assert abs(partial[1]['task_reward_without_potential_standby_thumb_action']-.84) < 1e-8
assert not partial[1]['strict_note_success']

# 접촉을 반복해도 이전 최고 진행률까지는 재지급하지 않는 예산 계산을 검사한다.
contact_streaks = torch.tensor([.01, .03, .05, 0., .02, .05], dtype=torch.float64)
best = contact_streaks.cummax(0).values
progress = (best/.05).clamp_max(1)
increments = progress-torch.cat((torch.zeros(1), progress[:-1]))
assert abs(float((.25*increments).sum())-.25) < 1e-12

# 시작 잠재값이 같은 두 경로의 실제 종료까지 할인한 잠재 차분 합을 비교한다.
gamma = .99
path_a = torch.linspace(.7, .1, 97, dtype=torch.float64)
path_b = path_a.clone()
path_b[1:-1] = torch.sin(torch.arange(1, 96, dtype=torch.float64)).square()
path_a[-1] = path_b[-1] = 0.
discount = gamma**torch.arange(96, dtype=torch.float64)
pbrs = [float((discount*(gamma*p[1:]-p[:-1])).sum()) for p in (path_a, path_b)]
assert all(abs(value+.7) < 1e-12 for value in pbrs)

# 판정 함수가 해제 이력을 요구하는지 합성 원장으로만 확인한다.
# 이 값 주입은 학습·평가 성공 증거가 아니며 실제 물리 궤적을 대체하지 않는다.
release_env = environment('baseline')
release_env.clock[:] = release_env.duration_ticks*4
release_env.note['best_clean_streak'][:] = release_env.end-release_env.onset
release_env.note['left'][:] = True
release_env.note['released'][:] = False
release_episode = release_env._episode(0, False)
release_check = dict(synthetic_ledger=True,
    released_count=int(release_env.note['released'][0].sum()),
    strict_note_success_count=release_episode['song']['strict_note_success_count'],
    strict_stage_success=release_episode['song']['stage_success'])
assert release_check['released_count'] == 0 and release_check['strict_stage_success']

task = make_task(ROOT/'data/song_bundles/05_BN2-131-B_solo')
preparation = [t.onset_s-t.press_s for t in task.targets]
sources = [ROOT/'guitar_learning/gpu'/name for name in
    ('compact_press_v4.py', 'compact_press_v3.py', 'finger_skill_environment.py', 'environment.py')]
result = dict(completed=True, scope='CPU isolated reward-function probes; no policy learning or physical feasibility claim',
    preview_signal=preview, partial_note_reward=partial,
    repeated_contact_total_reward=float((.25*increments).sum()),
    terminal_discounted_pbrs=pbrs,
    strict_release_check=release_check,
    current_song_press_to_onset_range_s=[min(preparation), max(preparation)],
    source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
(OUT/'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
