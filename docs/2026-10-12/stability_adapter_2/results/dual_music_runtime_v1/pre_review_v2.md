# 양손 runtime v2 실행 전 독립 검수

요약 판정: **문제없음 — v1의 실행 전 차단 항목은 v2에서 보완됐다. preload 두 조건과 이후 실험적 pair 진단의 추가 코드 차단 항목은 확인하지 않았다.** 아직 native 초기 지지·두 checkpoint의 실제 연결·음악 성공·최종 학습 ABI를 인증한 것은 아니다. 검토자는 이 파일만 작성했다.

## Critical

추가 차단 항목 없음. [runner v2:215](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v2.py:215)는 빈 frames를 먼저 검사하므로 최초 capture 실패가 `frames[-1]` 오류로 cleanup/report를 가로막던 경로가 해소됐다. [121행](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v2.py:121)은 실제 `detection['zone_allowed']`를 clock에 전달한다. 영역 마스크·fraction·방향의 raw 기록과 source stage와 독립인 영역 gate도 명시됐다.

## Warning

- [runner:185](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v2.py:185), [원본 역변환:785](/home/ajou/yigyu/3/tab2body/env/base.py:785): source history는 실제 final target의 원본 action 역변환값이다. 역변환은 action_scale과 [-1,1] clip을 포함하므로 native rate 과도기 목표가 source 표현범위 밖이면 실제 target을 완전히 재구성하지 못할 수 있다. clipping/재구성 오차를 실행 결과에서 구분하고 무조건적인 정확 일치로 설명하지 않는다. 물리548D의 직전 최종 목표는 이 문제와 별개다.
- [기존 native view:67](/home/ajou/yigyu/3/stability_adapter_2/strike_native_view.py:67)·[state_rows:14](/home/ajou/yigyu/3/stability_adapter_2/strike_native_view.py:14)는 native COM linear velocity를 source tensor에 그대로 복사한다. 원본 [guitar-relative twist:1065](/home/ajou/yigyu/3/tab2body/env/base.py:1065)의 body-origin offset 해석과 물리548D의 COM→origin 보정 경로에는 의미 차이가 남을 수 있다. 이번은 기존 source ABI를 유지한 전이 진단이므로 정확한 원본 실행 동등성이나 모든 source twist의 물리 정확성을 인증하지 않는다. 향후 보정은 새 view와 호환성 검사로 진행한다.
- [설계:24](/home/ajou/yigyu/3/stability_adapter_2/DUAL_MUSIC_IMPLEMENTATION_V1.md:24)의 240Hz endpoint bracket은 정확한 subframe 압현 연속성을 보장하지 않는다. CPU12 반례 통과를 실제 양손 episode 성공이나 학습 준비 완료로 확대하지 않는 범위를 유지한다.

## Suggestion

preload의5초 관찰 종료, pair의 첫 source done, 계획 horizon, 실제 runtime 오류는 failure/stop_reason/physics_seconds로 구분해 남긴다. source clock의 허용 drift와 owner clock으로 투영한 추론은 원본 시계 그대로의 실행과 구분한다.

## 좁은 변경 대조

v1→v2 diff는 guard 조건·실제 zone/raw 기록·marker metadata·contract 입력 SHA·Strike numeric clock projection의 보완이다. marker_order는 MARKERS이고 observation_manifest는 별도 필드로 구분됐다. source clocks는 먼저 Fret frame 일치와 Strike drift≤1/240초를 검사한 뒤 owner frame/60으로 투영하고 투영 전 값을 기록한다. 원본 전체 source step 호출이나 추가 native 물리 진행은 추가되지 않았다.

[tests v2](/home/ajou/yigyu/3/stability_adapter_2/tests/test_dual_music_v2.py:67)는 false-zone 무보상과 chord wrong-order 반례를 추가한다. [cpu_checks_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/cpu_checks_v2.json)의12개 통과·Python3.8 AST6파일·1299D compose 범위를 코드와 대조했다. v2 기록의 입력6개 SHA와 보존된 v1 CPU 기록의 입력6개 SHA가 현재 파일과 모두 일치함을 독립 확인했다.

[v1 사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pre_review.md)는 보존했다. 현재 .5/1.0 preload를 먼저 관찰하고 pair는 그 결과 및 실제 view/clock/readback 검사를 대조하며 진행할 수 있다. 실행 결과는 이후 별도 최종 검수 대상이다.
