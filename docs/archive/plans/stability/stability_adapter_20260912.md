> **HISTORICAL — 통합 이전 기록.** 본문의 수치·명령·검증 결과는 작성 당시 기준이다. [현재 StabilityAdapter 안내](../../../../stability_adapter/README.md)를 먼저 읽는다. 보관은 미완료 검증의 완료를 뜻하지 않는다.

# StabilityAdapter 독립 복원 학습 재설계

사용자 요청: 기존 안정화 실험 구현을 교체하고, 자유 기타가 낙하하여 스트랩에
매달린 뒤 humanoid 제어로 목표 위치·회전을 복원하는 학습 구조를 만든다.
확인된 조건: 골반/root 고정, 몸통·팔 제어, 길이가 고정된 수동 스트랩.

## 범위와 계약

- 기존 static-support / arm-recovery / world-recovery 실행 코드를 새로운
  `stability-adapter` 진입점으로 교체한다. 과거 실험 결과는 역사 자료로 남긴다.
- 공용 Isaac Gym 물리·PPO와 향후 Full 통합 계약은 유지한다.
- Fret, Strike, Synchronizer, 음악 데이터, 기존 정책 checkpoint는 사용하지 않는다.
- 제어 권한: 몸통 15 + 양쪽 shoulder/elbow 12 = 27. 다른 관절은 초기 PD hold.
- 매 reset은 초기 자세에서 WAIT_SETTLE로 시작한다. 정착 상태 replay는 없다.
- WAIT_SETTLE: 정책 행동 무효, 저속·스트랩 장력·안전 상태 연속 충족 후 RECOVER.
- RECOVER: 목표 pose 오차와 속도를 줄이고 연속 dwell을 통과해야 성공.
- 기본 목표는 첫 물리 step 이전 기타 pose. world 위치 offset 및 xyzw 회전 offset으로
  다른 목표를 지정한다. reset/정착 시 목표를 덮어쓰지 않는다.
- WAIT 표본은 공용 PPO의 sample mask로 actor/critic/RMS/GAE에서 제외한다.
- 새 관측·행동·물리·보상 계약은 기존 checkpoint와 비호환이며 fresh start한다.
- 문서상의 G0는 fixed guitar를 뜻하므로 이 과제는 source-free stabilization으로 구분한다.

## 체크리스트

- [x] master_plan 및 현재 docs, 기존 실행 코드·실험 실패 기록 확인
- [x] root 고정/수동 스트랩 해석 사용자 확인
- [x] 순수 목표·관측·단계·보상 계약 및 경계 조건 검사
- [x] 새 Isaac task, 학습/resume, passive/정책 평가 구현
- [x] 이전 실행 경로 제거, 현재 문서와 실행 안내 갱신
- [x] CPU 계약·PPO mask 회귀 검사
- [x] GPU 물리/PPO smoke, checkpoint 평가·resume
- [x] change-reviewer 검수 및 수정

## 검증 기준

대기 행동이 PD target을 바꾸지 않고 보상은 0이어야 한다. 잘못된 pose에서 멈추는 것은
RECOVER 진입 조건이며 성공이 아니다. 목표 부근에서도 속도가 높거나 dwell이 끊기면
성공하면 안 된다. 비동기 reset은 해당 환경만 초기화하며 고정 목표를 보존해야 한다.
스트랩 길이는 전체 episode에서 일정해야 한다. 목표를 향한 움직임에 개선 신호가 있어야
한다. 학습 저장/재개/평가는 같은 계약을 검증해야 한다. smoke와 복원 정책 수렴을 구분한다.

## 초기 관측

기존 WSR 실험은 91개 축에 손가락·하체를 포함하며 5%/최대10도 residual을 사용했다.
기록상 정착 후 약 28 cm / 72도 이탈하며 복원 성공은 미검증이다. 새 설계는 연주와
충돌하는 손가락 권한을 제거하고 몸통/팔의 명시적 residual cap을 사용한다.
이번 구현은 장기 학습 성공을 전제하지 않는다.

## 최종 결과

[검증 기록](../../../../stability_adapter/archive/VALIDATION_20260912_14.md)에 CPU 검사, GPU 정착, 48회 PPO smoke,
checkpoint 평가·재개와 검수 결과를 기록했다. 구현 검증은 완료했으며 smoke의 복원 성공은 0회다.
기존 frictionless 총길이 cable이 느슨해지는 관측을 근거로, 새 독립 task는 어깨 no-slip 두 구간
수동 스트랩과 실제 240 Hz force 갱신을 사용한다. 이 변경은 학습 성능 개선으로 주장하지 않는다.
