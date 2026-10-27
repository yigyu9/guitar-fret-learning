# 환경 기본층 실행 전 독립 검수 — v2 진입점

요약 판정: **문제없음 — 지정된 두 무학습 native 진단을 실행할 수 있다.** v1 사전 검수는 보존했고, 이번 검수는 새 v2의 좁은 변경과 CPU 결과를 대조했다. 실제 native 초기 상태·제어·카메라 검증은 아직 실행 전이다.

## Critical

현재 진단 실행을 막을 결함은 확인하지 않았다.

## Warning

- [learning_scene_v2.py:30](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v2.py:30), [run_environment_foundation_v2.py:49](/home/ajou/yigyu/3/stability_adapter_2/run_environment_foundation_v2.py:49): native 초기 q/한계/PD/raw state의 정확 일치와 카메라 기록은 CPU 검사 범위를 벗어난다. 결과가 성공 또는 중단인지를 실제 readback·로그·종료 시각으로 구분해야 한다. 음악 보상·학습 준비·안정성 성공은 이 실행으로 인증하지 않는다.

## Suggestion

추가 변경 제안 없음. 직접 노출된 native 객체를 보안 경계로 해석하지 않고 지정된 단일 제어 경로를 사용한다.

## 변경 대조

- [environment_guard_v2.py:8](/home/ajou/yigyu/3/stability_adapter_2/environment_guard_v2.py:8)은 tensor position-target setter 두 종류를 소유권 검사에 추가하고, [22행](/home/ajou/yigyu/3/stability_adapter_2/environment_guard_v2.py:22)은 `set_rigid_transform`을 reset 초기화 경계에 포함했다. v1에서 지적한 세 setter의 passthrough 경고는 v2에서 해소됐다.
- [learning_scene_v2.py:9](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v2.py:9)와 [run_environment_foundation_v2.py:20](/home/ajou/yigyu/3/stability_adapter_2/run_environment_foundation_v2.py:20)의 차이는 각각 v2 guard와 v2 scene 연결뿐이다. 초기화·548D 관측·81D 목표 변환·제어 주기당 rate 제한 한 번·60/240Hz·2초 PREP·총 5초 관찰 계약은 v1과 같다.
- [CPU 검사 v2:83](/home/ajou/yigyu/3/stability_adapter_2/tests/test_environment_foundation_v2.py:83)는 위 세 setter의 reset 이후 거부를 추가 검증한다. [검사 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/cpu_checks_v2.json)의 9개 통과 및 Python3.8 구문 검사 5파일 통과를 코드와 대조했다. 기록된 5개 SHA와 보존한 v1 소비 소스 7개 SHA가 모두 현재 파일과 일치함을 독립 확인했다.

[v1 사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/pre_review.md)의 native 실행 전 한계는 그대로 적용한다. 검토자는 구현 파일을 수정하거나 물리 실행을 수행하지 않았다. 최종 검수는 새 v2 실행 결과와 산출물 완성 후 별도 기록한다.
