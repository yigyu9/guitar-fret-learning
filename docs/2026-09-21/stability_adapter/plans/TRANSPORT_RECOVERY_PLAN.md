# TRANSPORT recovery implementation plan

상태: 진단 반복 완료 — 성공 조건 미충족

## 성공 기준

- 교사가 palm-under support와 thumb + opposing finger 압력을 유지한다.
- 1 mm -> 2 mm -> 5 mm 이동에서 목표 오차가 감소하고 SETTLE을 통과한다.
- 실패한 교사 궤적은 행동복제 데이터에 포함하지 않는다.
- learned policy가 온라인 교사 action 없이 동일한 5 mm 과제를 수행한다.
- 최종 checkpoint, JSON report, MP4를 `transport/t05_5mm_v3/`에 저장한다.

## 체크리스트

- [x] 손가락별 bounded pressure servo와 접촉 저하 시 arm pause
- [x] 기타 위치 오차 폐루프 arm target 및 strap-aware translation teacher
- [x] 말단 접촉력 기반 robust arm-motion gate
- [ ] 성공 교사 검증 — 1 mm에서도 grip loss
- [ ] 성공 궤적 전용 학습 데이터 수집 — 성공 궤적 없음
- [ ] 완전 autonomous learned-policy rollout — arm만 learned, hand는 교사 servo
- [x] 20,000회 진단 학습과 safety-shielded learned-arm rollout
- [x] 테스트, source hash, media integrity
- [x] change review 및 learned safety gate 보완

## 최종 진단

- teacher: 위치 오차 6.286 mm, 과부하 없음, grip lost
- learned arm: 위치 오차 6.82 mm, 최종 손 하중 7.36 N, grip lost
- 산출물: `transport/t01_1mm_recovery_v1/`
- 판정: 승격 불가. 다음 반복은 BC 시간이 아니라 compliant/force-aware arm
  control과 순간 접촉력 예측이 필요하다.
