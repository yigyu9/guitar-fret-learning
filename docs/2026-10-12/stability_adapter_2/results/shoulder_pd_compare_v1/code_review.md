# 어깨 stiffness 비교 사전 독립 검수

2026-10-07. 변경 검수자. Native 초기화·시뮬레이션 없이 코드와 순수 fixture를 검토했다.

## 요약

문제없음. Critical/미해결 Warning/Suggestion 없음. 두 사전 Warning은 수정 및 재검증했다. 실제 native 실행 결과와 안정성은 아직 검증하지 않았다.

## 범위와 승인 계약

- `/home/ajou/yigyu/3/stability_adapter_2/run_shoulder_pd_compare.py:27`: 기존 ForceEnvironment와 PALM_RATE runner를 재사용한다. Fresh 초기화 후 step0에서 L/R Shoulder x/y/z의 stiffness만 200 또는 300으로 설정한다. Damping50·effort150과 다른 structured PD field는 그대로 비교한다.
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_shoulder_pd_compare.py:21`: 저장된 short/hold_05s × kp200/kp300 네 경로만 분석한다. 초기 fullstate, 설정 차이, 표본·시점·prefix와 실제 측정 통계를 검증한다.
- `/home/ajou/yigyu/3/stability_adapter_2/SHOULDER_PD_COMPARISON_PROPOSAL.md:37`: 사용자 승인 범위는 두 조건 각0.1초, 계약 통과 후 각0.5초다. 실행 순서와 중단은 root가 관리하며 1초·다른 gain·새 제어는 포함하지 않는다.

## 수정 확인

- SDK 저장 목표 보존의 누락을 해소했다. `run_shoulder_pd_compare.py:20`에서 finite float32 전체105개 목표를 복사하며, `:45`에서 PD setter 전후 native 목표·초기 상태·Python 목표를 함께 비교한다.
- 기존 비교 원자료의 사전 봉인 누락을 해소했다. `run_shoulder_pd_compare.py:83`에서 기준200의 raw7, 시험300의 초기 states SHA를 실행 전에 저장한다. `:109`에서 중복 source SHA 충돌을 거절하고 `:113`에서 종료 시 원래 SHA를 검사한다.

## 독립 검증과 한계

AST로 추출한 실제 초기화 코드와 mock SDK를 실행했다. 200/300 모두 Shoulder6 stiffness만 바뀌며 나머지 field·상태·목표·steps0가 유지됐다. Setter 실패, 다른 effort 변경, 상태 변경 및 SDK 목표 변경은 거절하고 close했다. 목표 shape/dtype/비유한값도 거절했다.

실제 analyzer CLI를 `/tmp/shoulder_pd_reviewer_preflight_1ajlhnlj`의 합성 네 조건에 실행해 모든 분석 계약 통과를 확인했다. 기존 저장 데이터의 복사와 합성 PD metadata를 사용했으며 새로운 물리 측정이 아니다. 선언된 control 표본 하나를 제거한 fixture는 `raw coverage differs`로 실패하고 성공 출력이 생성되지 않았다.

## 최종 판정과 동결

사전 코드 검수 완료. 원래 runner·환경·제어기에는 편집하지 않았다. 초기 설정 후 runtime PD/state 쓰기를 추가하지 않으며, SDK total DOF force와 native scalar gap은 모터 전용 토크·물리 회전각·PD 부족 원인·기타 지지 성공을 인증하지 않는다. 승인된 native 비교는 root가 수행하고 별도 runtime 검수로 판단한다. 이 사전 검수 문서를 동결한다.
