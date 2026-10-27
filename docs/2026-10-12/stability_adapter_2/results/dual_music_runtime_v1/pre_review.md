# 양손 runtime v1 실행 전 독립 검수

요약 판정: **수정 권장 — 최초 캡처 실패의 종료 경로는 preload 전에, 타현 영역 판정은 pair 전에 보완해야 한다.** 소비된 v1 소스는 보존하고 새 버전에서 수정한다. 검토자는 이 파일만 작성했으며 native·checkpoint 추론·학습을 실행하지 않았다.

## Critical

- [run_dual_music_v1.py:208](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v1.py:208): 최초 `recorder.capture()`가 실패하면 첫 sample로 trace는 채워졌지만 frames는 빈 목록일 수 있다. finally의 `frames[-1]`이 IndexError를 내어 원래 실패 기록·scene close·report 저장을 건너뛴다. 빈 frames를 검사하고 cleanup/report를 보장하는 새 runner 버전이 preload 실행의 선행 조건이다.
- [runner:119](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v1.py:119): release마다 `zone_valid=True`를 전달하여 [clock:61](/home/ajou/yigyu/3/stability_adapter_2/dual_music_clock_v1.py:61)의 영역 검사를 항상 통과시킨다. 원본 [detector:331](/home/ajou/yigyu/3/tab2body/env/strike_detector.py:331)은 release의 geometry valid와 zone membership을 분리하며 [원본 Strike:3867](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3867)은 실제 zone/lane을 검사한다. 실제 detector mask를 연결하고 적용 영역·lane 계약과 raw 값을 기록하며 false-zone 반례를 검사해야 한다. 이 오류는 pair 판정에 해당하고 preload 경로에는 해당하지 않는다.

## Warning

- [runner:65](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v1.py:65): `marker_order`에 native marker 이름 대신 548D observation_manifest의 블록 목록을 저장한다. 실행 자체를 막지는 않지만 필드 의미가 다르므로 새 버전에서 observation_manifest로 구분하고 실제 marker 순서는 별도로 기록한다.
- [JointMusicClock:56](/home/ajou/yigyu/3/stability_adapter_2/dual_music_clock_v1.py:56), [설계:24](/home/ajou/yigyu/3/stability_adapter_2/DUAL_MUSIC_IMPLEMENTATION_V1.md:24): 양 끝 sounding fret와 dwell로 만든 240Hz bracket은 정확한 subframe 압현 연속성을 입증하지 않는다. 진단 한계와 training_ready=false 설명은 적절하다. CPU10 검사는 첫 canonical event를 변형한 반례 중심이며 전체 곡의 native 양손·source clock·종료 시험 완료로 확대하지 않는다.

## Suggestion

추가 취향 변경은 제안하지 않는다. 최초 실패·source 첫 done·계획 horizon·preload 총5초를 실제 report의 failure/stop_reason/physics_seconds로 구분하고, early done을 곡 전체 완료나 5초 완료로 설명하지 않는 범위를 유지한다.

## 확인한 범위

[scene](/home/ajou/yigyu/3/stability_adapter_2/dual_music_scene_v1.py:23)은 기존 LearningScene_v2를 재사용하고 contract 인스턴스의 horizon만 확장한다. preload는 저장 중립 실행 2~5초의 실제 q median 오차에서 arm±.15/finger±.05rad의 정적 목표 보정을 만들며 초기 실제 q·PD gain·body/head 기준을 바꾸지 않는다. 기존81 codec의 범위·rate·단일 제출·4 physics steps 경로를 유지한다.

pair는 source 30+30 채널의 중복·범위 교집합을 검사한 뒤 한81 요청을 만든다. 원본 source cache/apply는 tensor EMA/목표만 갱신하며 native 물리는 owner가 한 번 진행한다. Fret/Strike evaluator는 그 뒤 각각 1tick 평가 상태를 진행한다. [Strike 추출 seam](/home/ajou/yigyu/3/stability_adapter_2/dual_strike_evaluator_v1.py:10)은 source SHA와 AST prefix를 검사하여 action 제출·physics/refresh/progress prefix를 제거한다. 두 view의 native snapshot 일치, PREP countdown·PLAY0 투영과 다음 tick의 source clock 대조, 실제 최종 target의 history 반영, frozen weights 불변 검사는 코드에 있다. 아직 native 성공 여부는 미검증이다.

[CPU 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/cpu_checks.json)은 음악 반례10개·Python3.8 AST6파일·1299D compose 유한성 검사를 기록한다. 후보 [관측 compose](/home/ajou/yigyu/3/stability_adapter_2/dual_music_observation_v1.py:4)는548+420+303+28을 연결하며 최종 학습 ABI로 인증하지 않는다. 이번 검수는 소스와 검사 범위의 읽기 전용 대조이고 물리·학습 인증이 아니다.

현재 v1 preload의 나머지 경로에서 추가 실행 차단 오류는 찾지 못했다. 위 cleanup 보완본 확인 후 preload .5/1.0 두 조건을 먼저 진행하고, pair는 zone 보완과 별도 실행 전 검수를 거쳐 진행한다.
