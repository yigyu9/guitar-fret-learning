# 반복 초기 설정·batch 실행 계획

## 목적과 경계

이번 단위는 기존 환경에 관절 절대 초기각과 절대 strap rest length를 명시적으로 입력하고, 격리된 짧은 trial을 순차 실행·기록·부분 재개할 수 있게 한다. 구현과 trial 조건·결과 판정은 GPT-6.1 Sol이 맡는다. 기존 `run_initialization` 및 인자 없는 환경 생성의 기본 동작은 유지한다.

이는 입력·실행·체크포인트 계약을 확인하는 기능 진단이다. 정량 안정성 성공, 무관통 후보, 자동 후보 탐색 범위를 승인하지 않는다. H0의 관통 후보가 남아 있으므로 안전한 물리 배치로 인증하지 않는다.

## 입력 계약

`initial_settings` JSON은 `joint_angles_rad`, `strap_rest_length_m` 및 승인된 `guitar_initial_z_offset_m`을 담는다. 관절 맵은 관절 이름에서 유한한 절대 rad 값으로 매핑하고, 길이는 유한한 절대 m 값으로 받는다. 생략 관절은 기존 source clip 목표를 유지한다. 명시값은 모델 관절 한계 안이어야 하며 알 수 없는 이름, bool, NaN/Inf, 범위 밖 값, 음수 길이는 거부한다. 기타 Z offset은 0 또는 승인된 +0.005m만 받으며 생략 시 0이다. 올린 목표와 원본 공통 위치 오차를 분리한다.

설정 가능한 관절은 Thorax부터 손가락까지 주 제어 66관절의 부분집합이다. 승인된 예외로 양쪽 Hip/Knee/Ankle/Toe 중 native 한계 폭이 양수인 초기각만 기준각 ±0.05rad와 모델 한계의 교집합에서 변경할 수 있다. 하체 action은 추가하지 않는다. Torso/Spine/Chest 9관절의 PD 목표와 humanoid root, 기타 회전은 유지한다. 자유 시뮬레이션 중 몸통 실제 각과 기타 실제 p/q는 달라질 수 있으며 별도로 측정한다. 환경 constructor의 선택적 설정은 초기화 중 한 번만 적용하고, `step()`에서 관절 상태나 기타 pose를 재주입하지 않는다.

초기 route 길이와 요청된 절대 rest length를 각각 기록한다. 자세 변경 후 route 길이로 rest length를 자동 재설정하지 않는다. H1 계열도 지정한 공통 절대 길이를 그대로 사용한다.

## Batch와 격리

Manifest는 공통 `control_steps`와 `trials: [{id, initial_settings}]`를 가진다. 로컬 batch runner는 각 trial을 별도 subprocess와 고유 run 디렉토리에서 순차 실행한다. 설정·manifest snapshot·실제 초기 상태·초기/최종 측정·source hash·원문 stdout/stderr를 report와 log로 보존한다. `control_steps`는 기능 계약용 실행 길이이며 안정성 success 기준이 아니다.

Checkpoint에는 manifest hash와 현재 trial 위치, 각 trial attempt 상태, 현재 코드·공용 asset·mesh hash를 기록한다. 재개는 이 입력 hash가 모두 일치할 때만 허용한다. 완료 report의 완료 marker가 기록된 trial만 완료로 간주하고 재실행하지 않는다. 중단된 trial은 기존 partial attempt를 보존하고 재개 시 새 attempt 디렉토리로 다시 시작한다. `max-trials`로 일부만 실행하고 재개하는 흐름을 확인한다.

## 제한된 기능 진단 세 설정

첫 두 설정은 공통 절대 rest length `L_A = 1.0891851746440693 m`를 사용한다. 세 번째는 `L_A + 0.001 m`로 분리한다. 모든 설정은 기타 기준 목표 p/q와 초기 속도를 동일하게 유지하며, 각 trial은 0.1초 진단이다.

1. H0 관절 설정 + `L_A`.
2. H0에서 `R_Elbow_x` 절대각에 `+0.02 rad`를 더한 설정 + 같은 `L_A`.
3. H0 관절 설정 + `L_A + 0.001 m`.

이 세 조건은 상체 관절 설정 입력과 절대 길이의 짧은 실행·기록 계약만 진단한다. 개선 방향, 반복 탐색 범위 또는 정량 성공을 승인하지 않는다. H0 관통 후보를 계속 명시한다.

## 기록 범위와 미구현 사항

초기 CPU source-shape query와 signed palm-normal 측정은 가능한 기존 진단 값을 기록용으로 연결한다. 두 값 모두 시작 허용 gate나 PhysX clearance 판정이 아니다. PhysX clearance, 자동 start gate/reset, runtime feedback, 학습·보상, 수치 success 판정은 구현하지 않는다.

각 trial report에는 설정된 절대값과 source clip 유지 관절, 불변 target, route length/rest length 분리, 초기 겹침 query 범위, signed palm-normal 정의/단위, 기타 p/q drift 측정, 실행시간, 제한 및 hash를 기록한다. 설명 그래프는 결과에서 파생하고 측정값과 가상 설명점을 구분한다.

## 단계별 계획과 체크리스트

- [x] 입력 계약·검증 helper 구현 → 유효/무효 설정 거부와 생략 관절의 source clip 유지 확인
- [x] constructor 1회 적용 및 run trial 경로 구현 → 초기 입력 적용, held targets/root/기준 기타 목표 유지, step 중 pose 재주입 없음 확인
- [x] batch 부분 실행·재개 구현 → 완료 trial 미실행, hash 변조 재개 거부, partial attempt 보존 확인
- [x] 세 진단 trial 실행·산출물 기록 → raw report/log·비교 그림·누적 보고서 근거 대조
- [x] GPT-6.1 Sol 구현·수치 검토 후 별도 change-reviewer가 변경 파일 검수 — 남은 Critical/Warning/Suggestion 없음

기존 v3 source 코드는 결과 디렉토리에 기준 사본으로 보존한 뒤 필요한 `stability_adapter_2` 구현만 수정한다. 자료원 원본·기존 실행 결과는 삭제하거나 덮어쓰지 않는다. 검증은 새 run 경로에 기록한다.

## 결과 경로

설정·runner·helper·계약 검사는 `stability_adapter_2/`에 둔다. run report, logs, checkpoint, 비교 그림과 설명은 `docs/2026-10-12/stability_adapter_2/`의 고유 run/batch 경로에 저장하고 `VISUAL_REPORT.md`에 조건·출처·판정·한계를 누적한다. 코드·설정·계획·보고서 변경은 batch 단위로 별도 검수한다.
