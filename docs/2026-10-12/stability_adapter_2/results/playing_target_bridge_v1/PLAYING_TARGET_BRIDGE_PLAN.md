# 연주 prior 후보와 단일 목표 합성의 CPU 검증

## 목적과 현재 근거

직전 실제 palm-witness 후보는 미채택, LA−2mm의 작은 손목 동작 유지 기준을 보존한다.
자유 기타의 현재 G 연주 오차와 초기 world p/q 유지 오차를 공동66 residual로 줄이려면
먼저 source 선정과 목표/history 의미를 확인해야 한다. 이번 단계의 새 native/physics/actor추론/학습은0이다.
완전 palm접촉이나 WAIT 순서를 연주 선행 조건으로 두지 않는다.

앞선 ABI 조사 예시는 최종 source가 아니다. 직접 평가 자료는 fret47,500의 낮은 압현 성능과
strike10,708의 중단 저장 이력을 보인다. Strike10,000의 기존 fixed-guitar single-pick 평가와
현재 checkpoint SHA 연결을 확인하고, Fret47,000은 좁은 진단 후보로만 검토한다.
Full G0 적격성과 자유 기타의 성능을 혼동하지 않는다. 평가 시점 파일 SHA 부재도 기록한다.

현재 유지 target을 Fret hard-limit profile로 대조하면 손6관절이 범위를 벗어난다.
따라서 source 범위 밖 목표를 몰래 clip하거나 시작 시 바로 정책을 붙이지 않는다.
이 불일치와 원본 목표→source history의 표현 가능성을 이번 CPU 결과에 명시한다.

## 구현·검증 범위

1. source checkpoint/contract/원본 평가/선정·역사 문서의 SHA를 봉인하고 직접 평가 연결을 정리한다.
   Fret 원래 실패와 자유 기타 전이 실패를 분리하며 낮은 성능을 성공한 prior로 표시하지 않는다.
2. `playing_target_bridge.py`는 **단계별 후처리가 끝난 normalized source action30+30**과
   Thorax 기준6, 명시적66 residual 한도를 받아 하나의81D target을 계산한다.
   Source action을 rad offset으로 오해하지 않고 이름별로 절대각을 복원한다.
   이전 최종 목표에서 source history를 역변환하고 한 EMA만 적용한다. 목표는 native/source/
   normalized 표현 범위의 교집합 안에 두며 실제 float32 최종 목표의 history를 회신한다.
   선택 외15관절은 기준 목표를 exact 유지한다. Residual 크기/평활화는 CPU 시험 입력이며
   새 물리 controller gain이나 학습 범위 채택이 아니다.
3. `check_playing_target_bridge.py`는 원본 Base.apply_actions AST를 Isaac 없이 실행해
   residual0의 source EMA/절대각 변환을 직접 비교한다. 이름순서 permutation, batch,
   모든66 권한·held15·한계·포화 후 history·비유한/중복/불일치 거절을 검사한다.
   실제−2mm 유지target의 source 표현 불가와 허용범위까지의 최소 목표 변경폭을 수치로 기록한다.
   입력 tensor를 수정하지 않고 autograd residual 경로도 검사한다.
4. 독립 change-reviewer가 수치·범위·거절 경계와 문구를 검수한다. Luna는 확정 수치의
   그림/표/기존 실제 이미지 설명만 만든다. Native0을 실제 연주 영상으로 설명하지 않는다.
   이전53개 phase 원본·Aug19·legacy와 main문서 prefix를 root가 보존 감사한다.

이 함수는 source stage mask/synergy/pick-grip 후처리,420/303 전체 observation,
정규화·event clock·actor 추론 또는 물리 backend를 구현한 것이 아니다.
Task 특유의 추가 최종 목표 범위와 actuator/COM 관측 계약은 실제 연결 전에 검증한다.
이 CPU 통과를 전체 연주 연결이나 기타 초기p/q 복원 성공으로 표시하지 않는다.

- [ ] 평가 기반 후보와 현재 source profile 불일치 수치 봉인.
- [ ] 60+6→81 단일 합성·history CPU 구현과 독립 원본식 비교.
- [ ] 검수·산출물·원본 보존 감사, 다음 물리/학습 결정 기록.

메인 구현/계획은 stability_adapter_2, 결과는
[playing_target_bridge_v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1)에 새로 저장한다.
