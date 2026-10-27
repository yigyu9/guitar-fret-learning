# TRANSPORT grip-lock / load-settle implementation plan

상태: 구현·학습·렌더 완료, 승격 실패

## 목표

충분한 그립 압력을 즉시 실패로 처리하지 않고, 손을 잠근 상태에서
`L_Thorax` 하위 어깨·팔꿈치 관절로 기타를 이동한다.

## 구현 체크리스트

- [x] TRANSPORT 진입 시 arm PD 목표를 실측각으로 다시 캡처
- [x] 기존 SECURE를 `LOAD_SETTLE`로 명명하고 arm 이동을 금지
- [x] 안정된 뒤 `ARM_TRANSPORT`에서만 distal arm 9DoF 이동
- [x] soft pressure는 arm 정지·digit별 완화, 즉시 실패하지 않음
- [x] hard pressure는 증가 추세·상대속도·침투와 결합한 dwell 뒤 종료
- [x] hard 50 N 판정은 active 4개 digit의 proximal/middle/distal 전체 검사
- [x] 안정된 높은 그립과 순간 충격을 구분하는 단위 테스트
- [x] 1차 1 mm teacher smoke: overload=false, ARM_TRANSPORT 진입,
  404 samples 뒤 hand load=5.42 N 및 grip loss
- [x] 35% compression-retain teacher smoke: overload=false,
  ARM_TRANSPORT 1,151 samples, final load=7.16 N, grip loss,
  final error=27.81 mm
- [x] 35% 버전 20,000 update 학습 및 learned-arm 렌더:
  overload=false, final load=6.94 N, thumb loss 600 frames,
  final error=30.16 mm
- [x] 실패 분석: bounded recovery보다 압력 소실이 빨라 hand lock이 해제됨
- [x] hand acquisition target 100% lock teacher smoke: hard overload=false,
  그러나 soft pressure에서도 target을 완화해 final load=7.62 N 및 grip loss
- [x] soft pressure는 arm만 정지하고 hand target은 유지하도록 분리
- [x] 수정된 100% hand lock teacher smoke: 결과 동일, 손 target이 아니라
  contact flicker 때 arm을 완전히 정지한 것이 접촉 소실의 원인
- [x] contact flicker 중 arm 25% 저속 추종, finger loss grace 1초 적용
- [x] contact-recovery teacher smoke: hard overload=false, 361 MOVE samples,
  final error=26.65 mm, thumb support loss로 grip loss
- [x] 최종 MOVE-only 20,000 update 학습: 361 samples, loss=1.02e-7
- [x] teacher-guided learned-arm rollout 렌더 및 JSON/README 저장:
  5,200 frame grip retained, overload=false, position error=28.49 mm,
  transport success=false
- [x] reviewer 안전 지적 반영: all-active-segment 50 N 경계 테스트 추가,
  v5 20,000 update 재학습 및 source-bound 영상 재생성

## 합격 기준

- 단일 고압 샘플 또는 안정된 약 60 N 손 하중만으로 종료하지 않는다.
- hard overload가 6프레임 지속되면 반드시 종료한다.
- arm action은 `ARM_TRANSPORT`에서만 변경된다.
- teacher와 learned-arm 모두 과압 없이 1 mm 목표의 SETTLE을 완료해야 승격한다.
