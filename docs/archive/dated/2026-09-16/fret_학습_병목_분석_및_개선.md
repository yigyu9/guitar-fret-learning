# Fret 학습 병목 분석 및 개선

기준 분석일: 2026-09-08  
대상 곡: `02_Jazz1-200-B_solo`  
주 분석 run: `fret/training/runs/20260908_0943_02_Jazz1-200-B_solo`

## 1. 결론

기존 Fret-v2 학습은 정상적으로 완료되고 있지 않았다. `coarse_reach`와
`fine_reach`를 통과한 후 `isolated_press`에서 pinky가 성공하지 못했고,
구조적 실패를 sampler 비율만 바꿔 약 9,600 iteration 더 학습하면서 이미 배운
index·middle·ring 기술까지 망각했다.

주요 원인은 손가락의 물리적 도달 한계가 아니라 다음 세 계약의 충돌이었다.

1. 성공하지 못한 손끝이 15 mm 이내로 오면 고정 `-0.20`을 주는 near-miss 보상 절벽
2. 실제 압현 단계에서도 string plane 밖의 hover 높이를 선호하던 normal alignment
3. 준비 구간이 끝나는 60 frame에서 동시에 shoulder·elbow를 잠그던 action mask

또한 엄지 접촉력이 수만 N으로 보이던 현상은 실제 끼임이 아니라, 4개
PhysX substep impulse를 합산한 계측값과 마지막 substep geometry를 섞어 해석한
계측 오류였다.

수정판은 동일한 `fret_001500.pt`에서 149 iteration만 재학습한 시점에
pinky 정밀 압현을 0% -> 44.4%, pinky 물리 압현을 0% -> 50.1%로
회복했다. 이는 병목 방향이 맞았다는 강한 단기 근거이지만, 아직
`full_song` 성공을 의미하지는 않는다.

## 2. Fret 커리큘럼 13단계

| 단계 | 배우는 것 | 핵심 통과 의미 |
|---|---|---|
| `coarse_reach` | 손·손목·팔을 neck 목표 근처로 이동 | 먼 거리 도달 |
| `fine_reach` | 지정 손끝을 string/fret target에 정밀 정렬 | 접촉 전 hover 정렬 |
| `isolated_press` | 한 번에 한 손가락으로 source fret을 누름 | 4개 손가락별 단일 압현 |
| `integrated_press` | 압현을 왼손 전체 제어와 결합 | 단일 기술의 통합 |
| `chord_reach` | 여러 손가락을 코드 target으로 동시 이동 | 다중 target 도달 |
| `chord_fine_reach` | 코드 손끝의 정밀 정렬·접촉 | 동시 압현 후보 형성 |
| `static_chord` | 안정 코드를 연속 유지 | 부분 코드가 아닌 전체 완성 |
| `frozen_context` | 곡 문맥을 단계적으로 복원 | 정적 연습 -> 실제 frame 문맥 적응 |
| `goal_pair` | 현재·다음 목표의 KEEP/MOVE/REST | 압현·해제·이동 연결 |
| `transition_window` | 짧은 연속 event와 빠른 전환 | 한 목표 성공이 다음 목표를 깨지 않음 |
| `coverage` | 곡의 부족한 구간·손가락을 집중 보완 | event subgroup coverage |
| `integration` | 전체 분포에서 연결 연습 | 구간 성공의 전체 통합 |
| `full_song` | 원곡 시간축을 처음부터 끝까지 재생 | 최종 Fret source 평가 |

각 단계는 단순 평균 reward가 아니라 최소 증거량, 손가락별 성공률, 연속 유지,
오압현·안전 gate를 동시에 본다. 한 단계가 통과해도 뒤 단계에서 망각할 수
있으므로 단계 진입 성능과 현재 성능을 함께 비교한다.

## 3. 실제 학습 타임라인

| 구간 | 상태 |
|---|---|
| iteration 1~520 | `coarse_reach` |
| 528~1540 | `fine_reach` |
| 1544~현재 | `isolated_press` |
| 약 3550~13150 | pinky 회복 블록 24 x 400 iteration 소진 |

pinky는 복구 기간에 약 3,253,985 target frame을 받았으므로 표본 부족이
아니었다. 그중 압현 성공은 179 frame, 약 0.0055%였고 12 frame 연속
성공 episode는 0이었다. 같은 기간 다른 세 손가락은 약 98% 압현 성공을
보였다.

## 4. 실패 funnel

pinky 실패는 다음과 같았다.

| 축 | 관측 |
|---|---:|
| arch pass | 약 99.8~100% |
| lateral quality | 약 0.95~0.98 |
| normal quality | 약 0.98~0.99 |
| longitudinal quality | 약 0.02~0.03 |
| valid fret-region inside | 약 0% |
| 12-frame episode success | 0% |

즉 손가락 굽힘, 현 방향, 현 표면 방향은 거의 맞았지만 프렛 길이 방향으로
약 15~16 mm 빗나간 자세에 멈춄었다. 정책은 무작위로 실패한 것이 아니라,
기존 reward에서 비교적 높은 점수를 받는 지역 최적점을 찾은 것이다.

## 5. 근본 원인

### 5.1 near-miss 보상 절벽

기존 규칙은 실패 중 fine distance가 15 mm 이하인 경우에만 `-0.20`을 주었다.
따라서 15.01 mm에서 14.99 mm로 가까워지는 즉시 보상이 큰 폭으로 떨어졌다.
최신 pinky sample fraction을 실제 fret-7 cell 길이로 변환하면 오차가 약
15.7 mm였다. 정책이 벌점 경계 바깥에 정확히 자리 잡은 것이다.

### 5.2 hover-normal과 press-depth의 충돌

`isolated_press`의 fine alignment는 pad 중심이 string plane 밖쪽 약 6.8 mm에 있을
때 가장 좋았다. 반면 압현 성공은 pad 중심이 약 5.3 mm 이하까지 들어가야
했다. 접촉 전 유도 보상과 실제 성공 조건이 약 1.5 mm 반대 방향이었다.

### 5.3 고정 시간 proximal lock

episode 준비 시간도 60 frame이고 action lock 시작도 60 frame이었다. 즉 실제
압현 연습이 시작되는 순간부터 shoulder·elbow 보정을 막았다. fine-reach
말미의 pinky는 목표에 약 1.2~1.6 mm까지 도달했지만 isolated 전환 직후
오차가 약 17.5 mm로 확대됐다.

### 5.4 접촉력 계측 착시

`substeps=4`인 환경에서 PhysX 기본 `CC_ALL_SUBSTEPS`를 쓰면 control step 중간의
solver impulse를 모두 합산한다. 동일한 deterministic rollout의 물리 궤적은 유지하고
계측만 바꾸었을 때 엄지 힘은 다음과 같았다.

| 계측 | mean | p95 | max |
|---|---:|---:|---:|
| `CC_ALL_SUBSTEPS` | 5,790.7 N | 41,676.6 N | 51,762.3 N |
| `CC_LAST_SUBSTEP` | 7.16 N | 17.71 N | 20.77 N |

손바닥도 같은 차이를 보였고, thumb pad와 기타 proxy의 힘은 매 frame 정확한
작용-반작용이었다. 따라서 body index, collision filter, proxy geometry가 주원인은 아니다.

## 6. 배제한 가설

- **표본 부족:** pinky에 325만 frame 이상이 배정됐으므로 배제한다.
- **손가락 관절 한계:** reach margin은 양수였고 near-limit 비율은 낮았다.
- **finger mapping/string index 오류:** source string -> Isaac string 반전 로직과 동일 줄의 다른 finger 성공을 확인했다.
- **PPO 폭주:** 최초 병목 시점의 KL, saturation, exploration std는 정상 범위였다.
- **엄지 proxy의 깊은 관통:** 마지막 substep compression 분포와 작용-반작용을 대조해 배제했다.

## 7. 구현 변경

### Reward/geometry

- `press_near_miss_penalty`: `0.20 -> 0.0`. mask와 비율은 진단용으로 남겼다.
- 실제 압현 stage에 one-sided press-compatible normal alignment를 적용했다.
- 단일·다중 압현 모두 `0.1 <= u_fret <= 0.9`를 동일 점수의 correct region으로 통일했다.
- `physical_press` 진단과 `press_success = physical_press & position_inside`를 분리했다.
- chord target stagger도 correct region 밖으로 나가지 않게 제한했다.

### Action authority

- `isolated_press_lock_after_frames`: `60 -> 0`으로 바꾸어 기본 시간 lock을 비활성했다.
- proximal 움직임은 reward·reference posture·joint/safety 규칙으로 계속 제약한다.
- 향후 lock이 필요하면 시간이 아니라 readiness streak 후 현재 PD target을 latch하는 별도 ablation으로 추가한다.

### Physics/contact

- `contact_collection=CC_LAST_SUBSTEP`
- `max_depenetration_velocity=10.0 m/s`
- 두 값을 Fret checkpoint reward/safety 계약에 봉인했다.
- 예전 checkpoint는 일반 resume를 거부하고 `--migrate-contract`를 명시해야 한다.

### 진단

- isolated precision funnel을 `physical press -> valid position -> arch -> precise` 순서로 분리했다.
- 손가락별 target fraction, region-inside, longitudinal/lateral/normal quality, contact force를 모두 로그한다.
- 복구 block이 완전히 소진되면 이제 기본으로 마지막 checkpoint를 저장하고 학습을
  종료한다. 망각 연구 목적으로 계속할 때만 `--continue-after-curriculum-stall`을 명시한다.

## 8. 단기 재학습 검증

구현 변경 후 reward geometry, precision funnel, observation warm-start, curriculum,
checkpoint contract, thumb support, console 진단 등 관련 CPU 회귀 검사 10개가
모두 통과했다. Isaac Gym GPU에서도 action-mask 회귀 검사와 8-env 1-update
PPO smoke를 통과했다. console의 visual-geometry warning은 기존 headless asset
시각화 warning이며 physics/update는 정상 완료됐다.

비교는 동일 곡과 `fret_001500.pt`를 출발점으로 사용했다. 수정 run은
256 env, 기존 run은 1024 env이므로 완전한 단일 변수 ablation이 아닌 한계가
있다. 다만 같은 `isolated_press` stage age에서 실패 funnel이 반대로 바뀐다.

| 지표 | 기존 age 146 | 수정 age 149 |
|---|---:|---:|
| pinky physical press | 0.0% | 50.1% |
| pinky valid position | 0.0% | 44.4% |
| pinky precise press | 0.0% | 44.4% |
| pinky target distance | 25.29 mm | 6.48 mm |
| pinky sample fraction | -0.909 | -0.165 |
| 전체 episode success | 6.7% | 85.2% |
| frame F1 | 0.255 | 0.944 |
| thumb force p95 / max | 71.4 kN / 142.9 kN | 5.59 N / 14.27 N |
| penetration termination | 0 | 0 |

수정 run의 같은 시점에서 index/middle/ring 정밀 frame 성공은 각각 약
98.0%/99.9%/99.7%였다. 즉 pinky를 회복하면서 이미 배운 세 손가락이 즉시
무너지는 현상은 보이지 않았다.

이후 `press_success = physical_press & position_inside`를 reward 전체에 적용한
최종 semantics로 120 iteration을 더 학습했다. 마지막 window에서 pinky 현재
physical/position/precise는 `62.97/62.55/62.55%`, sample fraction은 `0.120`이어서
최초로 평균 압점이 10~90% correct region 안으로 들어왔다. 같은 window의
index/middle/ring precise는 `99.17/98.44/95.57%`, 전체 F1은 `0.945`,
wrong press는 `0.041%`, 관통·안전 종료는 0이었다.

다만 역사 평가 window에 초기 실패 episode가 남아 있어 pinky 12-frame-qualified
rolling success는 `46.33%`이다. 현재 frame 정확도와 시간적 유지 성공을
구분해야 하며, 다음 학습의 최우선 병목은 pinky 압현의 지속성이다.

## 9. Checkpoint 선택

- `fret_013000.pt` 이후는 pinky 실패를 해결하지 못한 채 다른 손가락까지 망각했으므로 새 학습의 기준으로 쓰지 않는다.
- 수정 전 코드를 메모리에 올린 기존 학습은 iteration 14,471에 SIGINT로 정상 종료했고 `fret_014471.pt`를 보존했다. 이 파일은 실패 분석 재현용이지 신규 학습 출발점이 아니다.
- 기존 계약 안에서의 보존 지점은 대략 `fret_009500.pt`이지만, 이미 잘못된 reward/physics로 과적합됐다.
- 수정 계약의 정식 재시작은 stage 붕괴 전이며 fine-reach 기술을 가진 `fret_001500.pt`에서 `--migrate-contract`를 명시하는 것이 적합하다.
- 단기 개발 검증을 빠르게 이어갈 때는 `fret_pinky_final_semantics_20260908/checkpoints/fret_002020.pt`를 사용할 수 있지만, 코드 등 후속 단계 결과로 해석하지 않는다.
- 최종 성능 checkpoint는 기존 계약 최신 파일이 아니라, 수정 계약으로 새로 학습한 run에서 선택한다.

## 10. Success cache에 대한 주의

checkpoint에 pinky quality 0.9876의 성공 snapshot이 남아 있지만 이를 바로 teacher로
쓰지 않았다. 해당 cache는 순간 `q`/action만 저장하고 `qdot`, root/body context,
접촉 상태, EMA 이전 action을 모두 보존하지 않는다. PhysX에서 90 frame 재생한
결과 pinky 연속 압현은 0 frame이었다.

향후 cache를 teacher/RSI로 쓰려면 full q+qdot, root/body state, PD target,
EMA history, goal identity를 저장하고 reset 후 12 frame 성공을 재생한 snapshot만
`replayable=true`로 승격해야 한다.

## 11. 통과 기준

수정의 완료 판정은 다음 AND gate를 사용한다.

1. isolated pinky physical press, valid position, precise press가 각각 0.80 이상
2. 네 손가락 최저 12-frame episode success가 0.80 이상
3. index/middle/ring의 최고점 대비 하락이 0.05 이하
4. wrong press, penetration, unsafe termination이 기준 run보다 증가하지 않음
5. `integrated_press` 전환 후에도 손가락별 성공이 유지됨
6. 후기 chord/transition/full-song gate를 별도로 통과

현재 단기 run은 원인 개선 방향을 검증했지만 1~2번의 0.80 기준을 아직
통과하지 않았다. 따라서 Fret-v2 전체 학습이 완료됐다고 판정하지 않는다.

## 12. 남은 위험과 다음 검증

- 현 방향 string 5:5 다중 할당은 Master Plan에는 확정됐지만 현재 원통형 6.3 mm pad 판정과 완전히 같지 않다.
- 다른 손가락이 같은 string/fret을 누르는 음악적 성공과 지정 finger adherence를 현 Fret training은 아직 분리하지 않았다.
- 접촉력 임계값은 LAST-substep 분포를 더 수집한 후 재보정해야 한다. 현재 4 mm compression hard guard는 유지한다.
- `30D block encoder` 대 `33D flat MLP`의 과거 성능 차이는 2x2 구조 ablation으로 분리해야 한다.
- isolated를 통과해도 chord, sustain, transition, full-song 병목은 별개이므로 단계별 검증을 계속한다.

## 13. 재현 명령

기존 1500 checkpoint를 수정 계약으로 재개하는 최소 명령은 다음과 같다.

```bash
python -m tab2body.train --task fret --song 02_Jazz1-200-B_solo \
  --checkpoint fret/training/runs/20260908_0943_02_Jazz1-200-B_solo/checkpoints/fret_001500.pt \
  --migrate-contract --iterations 50000
```

새 reward/physics 계약은 예전 checkpoint와 다르므로 `--migrate-contract`를 빼면 fail-closed하는
것이 정상이다. 장기 학습 중에는 단계 이름만 보지 말고 손가락별 funnel,
retention drop, wrong press, force/compression 로그를 함께 본다.

## 14. 구현 추적 표

| 역할 | 파일 |
|---|---|
| 압현 geometry, correct region, near-miss, press-compatible reward | `tab2body/env/rewards/fret.py` |
| isolated action authority, physical/valid press 진단 | `tab2body/env/tasks/task_fret.py` |
| 기본 수치와 10~90%, lock, near-miss 계약 | `tab2body/cfg.py` |
| PhysX contact collection·depenetration 설정 | `tab2body/env/base.py` |
| checkpoint physics contract, stall clean-stop | `tab2body/train_fret.py` |
| 정밀 reward 회귀 검사 | `tab2body/tests/test_fret_precision_reward.py` |
| geometry 회귀 검사 | `tab2body/tests/test_fret_reward_geometry.py` |
| action mask 회귀 검사 | `tab2body/tests/test_goal_pair_phase_diagnostics.py` |
| curriculum/stall 회귀 검사 | `tab2body/tests/test_frozen_context_curriculum.py` |
