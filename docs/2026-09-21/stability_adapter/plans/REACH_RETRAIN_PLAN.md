# StabilityAdapter REACH 재학습 기록과 다음 계획

## 목표

`free-guitar-strapped-v1`의 WAIT 종료 상태에서 왼손이 넥 아래로 접근한다. Torso
변형은 2도 이내로 억제하고, L_Thorax와 왼팔 관절을 주로 사용한다. 손바닥이 넥의
바닥 방향 면에 먼저 닿은 뒤, 안전한 접촉력을 유지하는 독립 정책을 최종 목표로 한다.

## 이번 구현

- WAIT 저속 조건을 240 frame 연속으로 강화하고 timeout을 3,000 frame으로 늘렸다.
- WAIT 뒤 측정 관절각으로 PD target을 덮어쓰던 문제를 제거해 중력 보상 토크를 보존했다.
- REACH action은 Torso 3 + L_Thorax 3 + 왼팔 9 = 15축이다.
- weighted DLS 비용은 Torso:L_Thorax:왼팔 = 100:5:1이다.
- Torso 목표 예산은 2도, L_Thorax 목표 예산은 15도다.
- 사전접촉 위치는 넥 아래 10 cm이며, 최종 접근에서는 Torso/L_Thorax 명령을 고정하고
  왼팔 관절만 갱신한다.
- 손가락 선접촉, 아래쪽 접근 위반, 과도한 충격과 스트랩 실패를 별도 판정한다.

## 학습 및 평가 결과

- 폐루프 교사 궤적 3,000 frame을 수집해 20,000 optimizer step으로 behavior cloning했다.
- 최종 BC MSE는 `1.3108436e-7`, 최대 action 절대오차는 `0.01193`이다.
- 교사 재생은 손바닥 접촉을 한 번 획득하고 기하 자세를 유지했다. 최종 상대속도는
  `0.00789 m/s`, 기타 선속도는 `0.00972 m/s`, 각속도는 `0.02079 rad/s`였다.
- 그러나 교사 종료 시 손바닥 접촉력은 `0 N`이다. 따라서 이 결과는 지속 접촉 성공이
  아니라 **접촉 획득 후 기하 자세 유지 후보**다.
- standalone BC 정책은 17 frame에서 손가락 충격 `933.7 N`으로 종료했다. 배포 또는
  다음 단계 입력용 성공 체크포인트로 승격하지 않았다.
- 공식 `REACH_SUCCESS`는 collider-pair 접촉 귀속이 구현되지 않아 계속 비활성화되어 있다.

## 판정 기준

최종 성공은 다음을 모두 만족해야 한다.

- 손바닥-넥 collider pair가 확인된 연속 접촉
- 손바닥 접촉력 1 N 이상과 안전 상한 이내
- 손가락보다 손바닥이 먼저 접촉
- 위치, palm-up, heading, under, 상대속도 gate를 30 frame 연속 만족
- 아래쪽 접근 위반, 접촉 실패, 환경 실패 없음
- teacher 없이 standalone policy가 동일 조건을 재현

이번 산출물은 위 기준을 충족하지 않는다.

## 다음 학습 단계

1. CPU collider-pair replay로 손바닥-넥 접촉 귀속과 지속 접촉 gate를 먼저 검증한다.
2. 단일 궤적 BC 대신 learner 방문 상태를 수집하는 DAgger 또는 teacher residual 정책을
   적용한다.
3. 충격 직전 상태를 집중 수집하고 action 변화율과 접촉 접근 속도를 제한한다.
4. 독립 rollout 성공 뒤에만 checkpoint를 후보로 승격하고 같은 checkpoint로 영상을 만든다.

## 산출물

- `environment/wait/reference/free_guitar_until_settle.mp4`: 강화된 WAIT 기준 영상
- `reach/current/rollouts/reach_contact_acquired_hold_teacher_candidate.mp4`:
  교사 접촉 획득·기하 유지 후보
- `reach/current/rollouts/reach_trained_bc_failed_contact.mp4`: standalone BC 접촉 실패
- `reach/current/checkpoints/reach_policy_failed_contact.pt`: 승격되지 않은 실패 체크포인트
- `reach/current/training/training_summary.json`: 학습 곡선과 독립 평가 결과
