# Strike A2 ready 기술 보존 개선

## 관측된 실패

`20260812_1948_00_SS1-68-E_comp` 실행은 A1을 iteration 312에서 통과했지만 A2에서 정체됐다.
A1 종료 시 episode ready 성공률은 약 0.99였으나 A2에서는 약 0.16으로 내려간 뒤 회복되지 않았다.
반면 episode release recall은 거의 1.0이고 false positive는 거의 0이어서 crossing만 수행하는
정책이 높은 return을 유지했다.

## 코드 원인

이전 보상은 `ready_quality`와 `ready_pulse`를 A1에서만 사용했다. A2 승급 gate는 ready 성공을
요구하지만 A2 reward는 ready를 보존할 이유를 제공하지 않았다. 또한 ready 이전의 target crossing도
crossing reward를 받고 episode를 해결할 수 있었다. `curriculum_success_rate`도 A2에서 crossing만
검사해 ready를 잃은 episode를 성공처럼 표시했다.

## 반영한 계약

1. A2 이후 ready를 획득하기 전에는 ready 위치 오차에 0점 기준 페널티를 적용한다.
2. ready pulse 보너스를 A2 이후에도 유지한다.
3. ready 이전 target crossing은 detector와 matcher 기록에는 보존하지만 crossing·timing·zone 보상을
   주지 않는다.
4. ready 이전 target crossing에는 별도 `unprepared_crossing` 페널티를 적용한다.
5. A2~A4의 `curriculum_success_rate`는 ready 성공을 필수 조건으로 포함한다.
6. `prepared_target_hit`와 `unprepared_target_hit`를 rollout 진단에 저장한다.
7. actor learning rate를 `1e-5`에서 `3e-6`으로 낮춰 KL trust region을 너무 빨리 벗어나는 현상을
   완화한다.
8. 한 단계가 설정된 최대 iteration에 도달해 `stalled`가 되면 즉시 checkpoint를 저장하고 실행을
   종료한다.

## 단계별 ready 보존 가중치

| 단계 | ready 위치 | ready 완료 pulse |
|---|---:|---:|
| A1 | +0.75 quality | +0.15 |
| A2 | -0.05 × error | +0.50 |
| A3 | -0.03 × error | +0.35 |
| A4 | -0.02 × error | +0.25 |

A2 이후 위치 항은 positive idle reward가 아니다. ready에서 멀 때만 음수가 되고 ready를 획득하면
0이 되므로, ready 위치에 머물며 crossing을 하지 않는 우회 해법을 만들지 않는다.

## 재학습 판정

새 reward와 PPO 설정은 checkpoint 의미 계약을 변경한다. 기존 A2 checkpoint를 일반 resume하지
않고 새 run으로 검증한다. 먼저 A2 진입 후 500~1,500 iteration 구간에서 다음을 확인한다.

- episode `strike_tip_ready_success_rate ≥ 0.85`
- `curriculum_unprepared_target_hit`가 감소
- release recall `≥ 0.80`
- false positive rate `≤ 0.05`
- PPO update 수가 지속적으로 40 중 4회 수준에 머물지 않음

이 조건을 만족하지 못하면 최대 A2 iteration에서 자동 종료된 checkpoint와 로그를 이용해 다음
수정을 결정한다.
