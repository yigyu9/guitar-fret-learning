# 환경 기본층 최종 독립 검수

요약 판정: **문제없음 — 현재 v2의 초기화·548D 관측·81D 단일 제어 경로와 두 native 진단 기록은 범위 내에서 일치한다. 초기 지지 안정성은 실패했으며 학습 환경은 미완성이다.** 검토자는 구현·기존 산출물을 수정하거나 물리·학습을 실행하지 않았다. 소유한 사전 검수와 이 최종 검수 파일만 작성했다.

## Critical

이번 물리 기본층의 완료를 막을 추가 코드 결함이나 산출물 불일치는 확인하지 않았다. 소비된 v1을 보존한 채 새 v2로 수정한 이력이 명시되어 있다.

## Warning

- [learning_scene_v2.py:68](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v2.py:68), [분석 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/analysis.json): 초기 실제 q와 중립 PD 목표가 같아도 하중을 받는 실제 자세가 유지되지는 않는다. 중립에서 기타 최대 변위 111.790mm·초기 대비 회전 19.486°, 작은 목표 움직임에서 113.778mm·19.888°이고 두 조건 모두 위치 상자 밖 표본은 288/301개다. 다음 새 단계에서 초기 실제 관절각과 하중을 지탱할 목표를 별도로 교정하고 다시 native 관찰할 것을 권장한다. 현재 배치를 안정성 성공으로 채택하지 않는 [PLAN:827](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:827)과 결과 설명은 적절하다.
- [환경 계약 문서:49](/home/ajou/yigyu/3/stability_adapter_2/ENVIRONMENT_FOUNDATION_V1.md:49), [85행](/home/ajou/yigyu/3/stability_adapter_2/ENVIRONMENT_FOUNDATION_V1.md:85): 548D는 물리 기본 관측이고 최종 음악 정책 입력이 아니다. 음악 상태·유효 압현·crossing/hit·SO(3) 허용 집합·종료 ledger·보상·GPU 벡터 reset은 이번에 검증하지 않았다. 실제 신호와 시간 계약을 연결한 새 단계의 검수 전까지 학습 준비 완료로 판단하지 않는다.

## Suggestion

추가 취향 변경이나 이번 동결본의 수정은 제안하지 않는다. 손바닥–기타 접촉 284/301개는 어떤 기타 body와의 접촉 표본이며 넥 지지·하중 지탱·관통 없음·힘N·음악 성공의 증명이 아니다. [결과 README:24](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/README.md:24)의 해석을 유지한다.

## 코드와 실행 대조

- [사전 검수 v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/pre_review.md)의 setter 경고는 [guard v2:8](/home/ajou/yigyu/3/stability_adapter_2/environment_guard_v2.py:8)·[22행](/home/ajou/yigyu/3/stability_adapter_2/environment_guard_v2.py:22)과 CPU fake Gym 검사에서 해소됐다. legacy 66-offset 제출과 제어 step 밖 물리 적분도 차단된다. [v2 사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/pre_review_v2.md)는 별도 보존됐다.
- [scene 초기 readback](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v2.py:25)과 [runner 비교](/home/ajou/yigyu/3/stability_adapter_2/run_environment_foundation_v2.py:49)는 이름·q·한계·PD와 native 초기 상태를 저장 기준과 정확 비교한다. 두 실행의 initial_values는 동일하며 reference exact가 확인됐다. 초기 state setter 두 종류만 기록됐고 이후 금지 호출은 없다. root/하체 고정·렌더/접촉 조회의 상태 보존 검사는 성공 경로에서 통과했다.
- [targets](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py:86)와 [step](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v2.py:103)를 실제 명령에 대조했다. 각 조건 300개 최종 목표를 action/직전 최종 목표로 독립 재계산한 값과 정확히 일치했고, 81개 effective/native bound와 제어 주기당 rate 한계를 모두 만족했다. small_motion의 PREP 120개 명령은 중립 목표와 정확히 같았다. 다음 관측의 `previous_final_target` 81개는 실제 제출 목표의 정규화값과 일치했다.
- 각 조건의 상태·관측은 301행이고 시각은 0부터 1200까지 4 physics steps 간격이다. 모든 관측은 float32 기반 548개 유한값이며 상태와 관측 시각이 일치했다. 제어 60Hz·물리 240Hz·총 5.0초, PREP 경계 2.0초가 기록과 일치한다. 목표 변화율은 실제 q 변화율 보장이 아니며 [실제 q/목표 구분 표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/README.md:15)는 올바르다.
- [CPU 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/cpu_checks_v2.json)의 9개 계약 검사와 Python3.8 구문 검사 5파일 통과를 코드와 대조했다. native 실행은 [neutral report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_neutral_v2/report.json), [small_motion report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_small_motion_v2/report.json)의 완료·오류 없음·입력 보존 기록과 일치한다. 학습 업데이트는 없고 `training_ready`/`stability_success`는 모두 false다.

## 분석·그림·문서 대조

[reference_layout.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/reference_layout.json)의 human66/guitar39 body 순서는 선언된 기존 source의 목록·SHA와 일치하며 두 실행 raw 배열의 길이와도 맞는다. [분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_environment_foundation_v1.py:17)의 Chest/Pelvis index, 초기 대비 quaternion 회전각의 q/−q 동치, 실제 q와 제출 목표의 변화량, 기타 위치 상자 이탈·접촉 표본 계산을 읽기 전용 검토했다. 회전 진단각은 허용 SO(3) 포함 판정을 대신하지 않는다.

[최종 몽타주](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/initial_final_montage.png)를 직접 열어 실제 원본 프레임과 대조했다. 두 조건·두 view·시작/종료 8장이 올바르게 배치되고 캡션이 장면을 가리지 않는다. [producer_manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/producer_manifest.json)의 입력 전후 20개·출력 3개 SHA와 현재 파일이 일치함을 독립 확인했다. 분석 입력 21개 SHA도 일치한다. 네 영상은 151frame/30fps/5.033333초로, 물리 5.0초와 구분됐다.

[CHANGED_FILES](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/CHANGED_FILES.md)의 15개 절대 링크와 실제 줄 위치, 결과 README의 12개 링크를 확인했다. PLAN821/A README1939/D README624/VISUAL_REPORT2396의 새 기록은 원자료·현재 v2 진입점·그림·한계와 일치하며, 저장한 main_before 대비 네 문서의 기존 prefix가 보존된 것을 독립 확인했다. 기존 전체 파일의 보존 감사·최종 봉인·inventory는 root의 후속 책임이며 이 검수의 직접 검증 범위와 구분한다.
