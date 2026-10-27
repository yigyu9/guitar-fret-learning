# 새 기타 construction 물성 보완 사전 검수 v2

요약 판정: **문제없음 — v2 native 사전 구현 범위.** v1의 물성 guard와 COM/관성 readback 지적은 해결됐으며 미결 Critical은 없습니다. 실제 native cooking·물성 적용·5초 안정성은 후속 결과로 확인해야 합니다.

- [ConstructionPropertyGuard:8](/home/ajou/yigyu/3/stability_adapter_2/construction_property_guard_v1.py:8)은 초기화 완료 또는 명시적 window가 닫힌 rigid-body property setter를 native 호출 전에 거절하고 실제 허가/거절 카운터를 기록합니다. [runner:67](/home/ajou/yigyu/3/stability_adapter_2/run_realistic_guitar_trial_v2.py:67)은 기존 GraphicsGym 내부에 InitializationGuard subclass를 유지합니다. temporary PropertyGym 복원 뒤에도 guard가 남고 기존 factory의 isinstance 검사 및 strap force wrapper와 호환됩니다.
- [runner:51](/home/ajou/yigyu/3/stability_adapter_2/run_realistic_guitar_trial_v2.py:51)은 요청 mass/COM/I를 저장하고 setter 허가 window를 finally에서 닫습니다. 57행은 전체 요청/readback mass·COM·관성을 대조하며, 86행은 기타 total mass·양 끝 route_COM·Observation.COM 캐시를 applied 값과 대조합니다. 97행은 실제 setter0/1회·거절0·닫힌 window를 종료 전에 검사합니다. setter→parent 캐시→LearningScene 캐시 순서는 적절합니다.
- [CPU 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/cpu_guard_tests_v1.log:1)의4검사 통과를 확인했습니다. fake backend로 window 밖/초기화 완료 뒤 setter가 native에 도달하지 않는3조건과 construction 허가1조건을 검사합니다. 이는 실제 native readback 결과를 대신하지 않습니다.
- [v2 계획](/home/ajou/yigyu/3/stability_adapter_2/REALISTIC_GUITAR_PROPORTIONS_PLAN_V2.md:3)은 v1 runner 미실행·소비 builder/asset/source fit 보존과 신규 runner 사용을 구분합니다. [v1 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/review_preflight_v1.md:1)의 자산 치수·기존 음악/frame 보존 및 형상/초기배치 인과 비교 제한은 그대로 적용합니다. 새 학습·Actor·음악·runtime IK를 연결하는 변경은 없습니다.

## Warning

추가 collision camera의 [생성 경로](/home/ajou/yigyu/3/stability_adapter_2/run_realistic_guitar_trial_v2.py:73)는 기존 camera와 달리 음수 handle 즉시 검사가 없습니다. 향후 새 버전에서 실패 handle을 image query 전에 명확히 거절하는 것을 권장합니다. 현재 guard·물성 보완의 추가 차단 오류로 판단하지는 않습니다.

## SHA·검수 범위

[source_before_native_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/source_before_native_v2.json:1)의9파일을 현재 SHA와 대조해 일치했습니다.

- runner v2: `3f94ec0bc9f7c9fc59af072d9f40bab6c6da611de0d9b609f51c26ef3eb545b1`
- property guard: `9352956555d6c46a5deb0a0bb39c774863832063de67dee59f0c5c3f12c32535`
- guard test: `9480a7d72bf0cff208ab66462b14fa1ff176c07c9b3ae6016889370a13704a23`

검수자는 새 리뷰만 작성했으며 추가 native/물리/학습과 기존 파일 수정은 하지 않았습니다. 새 자산의 COM·관성 검사는 실물 중공 기타의 질량 분포 인증과 다르며, old/new 초기 배치와 strap route가 달라 형상만의 효과를 분리하지 않습니다.
