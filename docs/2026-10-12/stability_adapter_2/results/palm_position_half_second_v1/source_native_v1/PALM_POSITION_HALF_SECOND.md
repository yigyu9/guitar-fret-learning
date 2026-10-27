# 같은 3조건의 0.5초 물리 응답 비교

2026-10-07. 승인된 PALM_POSITION_COMPARISON.md의 후속 시간 연장 진단이다.
0.1초에서 PALM_RATE의 손 중심 이탈이 RATE_PI보다1.361875mm 줄었으나
기타 변화와 양손 접촉은 없었다. 이 작은 위치 개선이 지속되는지0.5초로 확인한다.
안정 후보 채택이나 제어 이득·범위를 넓히는 결정이 아니다.

- [x] 계획: 기존0.1초 producer/원자료/14 frozen copies와103입력 SHA를 확인했다.
- [ ] 후속 실행기·분석기 검수: 시간 길이와 샘플 수만 바꾸고 제어 계산은 재사용한다.
- [ ] PI/RATE_PI/PALM_RATE 각 fresh 초기화·120steps를 순차 실행한다.
  초기 source/LH 조건과 PI의 기존3초 baseline 중0.5초5배열 prefix를 대조한다.
  RATE_PI/PALM_RATE도 기존 각0.1초 원자료 prefix가 같은지 추가 확인한다.
- [ ] 실제 손 중심·palm proxy/국소 넥 위치·기타p/q·접촉·장력·목표/실제 관절 한계를 비교한다.
  초기 조건·명령 읽기의 상태 불변성·Jacobian readiness·적분/solver 기록도 검수한다.
- [ ] 그림·설명·로그와 변경 파일 줄 번호를 저장하고 독립 검수를 완료한다.
  이후1초/새설정 여부는0.5초 결과를 보고 정한다.

PI는 기존 JointHoldResidual, RATE_PI/PALM_RATE는 기존 RatePalmResidual을 그대로 쓴다.
양팔24 목표 보정은±0.15rad∩native/C02±0.3rad, 새 두 조건의 전달목표 변화는
0.02rad/60Hz update, 위치 배율2·regularizer0.05m/rad다. PD/TGS4/2/substeps1,
root 고정·몸통9/손가락42/C02하체 목표·주요66연결·기타+5mm초기p/q·고정LA를 유지한다.
실제 몸통/팔다리 상태는 움직이며 기타는 자유롭게 둔다. 상태/pose 덮어쓰기는 없다.
손 중심의 world 목표는 무연주 진단의 초기값이며 최종 연주에 영구 anchor로 승계하지 않는다.
새 기타 오차 feedback/학습/작업조건 gate를 추가하지 않는다.

기존 source SHA 기반 재생성을 유지하기 위해0.1초 runner/analyzer를 수정하지 않고,
run_palm_position_followup.py와analyze_palm_position_followup.py를 후속 producer로 저장한다.
주 제어 계산 파일은 공유하며 복사된 기록 루프에서24→120steps/25→121samples만 바꾼다.
결과는 docs/2026-10-12/stability_adapter_2/results/palm_position_half_second_v1에 둔다.
초기 source query/normal proxy는 cooked clearance·접촉력·해부학적 palm 방향 인증이 아니다.
목표/실제 상태를 구별하고 합의되지 않은 성공 수치를 임의로 만들지 않는다.
