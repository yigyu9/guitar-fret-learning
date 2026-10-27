# 이번 소단계 변경 파일과 실제 줄 번호

기존 stability_adapter/와 공용 자산/이전 실험은 변경하지 않았다. A는 계획·구현, D는 새 결과·로그·실제 Isaac Gym 이미지/영상이다. 소비된 v1을 보존했고 현재 native 실행은 v2이다.

| 파일 | 실제 줄 | 변경 내용 |
|---|---:|---|
| [ENVIRONMENT_FOUNDATION_V1.md](/home/ajou/yigyu/3/stability_adapter_2/ENVIRONMENT_FOUNDATION_V1.md:5) |5·13·28·62·79|작업계획, 초기상태, raw/548D 관측, 상체81 제어, 완료/후속 경계|
| [environment_foundation_v1.json](/home/ajou/yigyu/3/stability_adapter_2/environment_foundation_v1.json:3) |3·7·13|초기값/참조 SHA, 시계, 부위별 목표 범위/변화율|
| [environment_contract_v1.py](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py:33) |33·86·96·106|81관절 이름/범위, action→목표, clock,548D manifest|
| [environment_guard_v2.py](/home/ajou/yigyu/3/stability_adapter_2/environment_guard_v2.py:7) |7|reset 밖 상태쓰기/외력/제어권 밖 목표 setter 금지|
| [learning_scene_v2.py](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v2.py:60) |60·90·103·135|native 초기화/관측/81목표 step/fresh-scene reset|
| [run_environment_foundation_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_environment_foundation_v2.py:13) |13·48·85|두5초 진단, 초기 manifest, 상태·관측·명령·실제 영상 저장|
| [test_environment_foundation_v2.py](/home/ajou/yigyu/3/stability_adapter_2/tests/test_environment_foundation_v2.py:14) |14·20·34·53·60·72|neutral/81/rate/움직이는G/clock/548/guard9검사|
| [analyze_environment_foundation_v1.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_environment_foundation_v1.py:17) |17·59|저장된 raw/trace의 기타 이탈·실제q·목표 변화·참조 대조|
| [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:821) |821|소단계 체크 완료와 초기 지지 실패/후속 목록 추가|
| [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1939) |1939|현재 실행층/설정/결과/범위 추가|
| [결과 main README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:624) |624|새 phase 결과 색인 추가|
| [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2396) |2396|새 native 몽타주·해석 추가|

[새 결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/README.md:1), [원자료 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/analysis.json:1), [CPU 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/cpu_checks_v2.json:1)에 세부 내용을 모았다. 초기 안정성·음악/학습 성공은 아니다.

v1 guard/scene/runner/test와 cpu_checks.json/pre_review.md는 수정 전 시도 이력으로 남겼다. pre_review_v2.md는 현재 active source 실행 전 검수다. 모든 새 phase 파일의 경로·SHA는 최종 artifact_inventory.json으로 정리한다.
