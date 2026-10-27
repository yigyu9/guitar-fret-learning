# 저장 궤적의 구·신 음악 판정 비교

**물리 시뮬레이션·정책 추론을 다시 실행하지 않았다.** 기존 actionable preparation의 왼손·오른손 PPO 평가 각1회, 각1,680개240Hz 표본을 새 분류기와 준비 게이트로 측정한 반사실 분석이다. 원본 실행의 성공·실패 기록을 고치거나 새로운 환경에서의 정책 성능으로 해석하지 않는다.

자료·연속 시계·후보 보존 검사: **True**, 입력 SHA 변경0개.

| 왼손 지표 | 결과 |
|---|---:|
| 전체 표본 | 1680 |
| 원 positive / 새 clean | 963 / 963 |
| correct / wrong / missing | 963 / 0 / 717 |
| higher / assignment / incidental-other / uncertain 표본 | 0 / 0 / 1374 / 1567 |
| audible 원 positive / clean 유지율 | 1.000000 / 1.000000 |
| end+100ms 이후 clear 표본 / 전체 | 0 / 612 |
| end+100ms 이후 최장 연속 clear | 0.000000s |
| 마지막 목표현 clear | False |

LH는 저장된 원 contact evidence와 같은 시점의 geometry만 사용했다. 원 TaskMeasurement를 다시 돌리지 않았고 초기 접촉을 만들어 넣지 않았다. audible 경계[4.120000,4.352200]초는 앞뒤 실제 표본으로 완전히 관측되며, 전체0.232200초의 유지 시간을 각각 적분했다. 노트 후 해제는 clean=False만으로 인정하지 않고 실제 목표현 접촉 ID가 비었는지 따로 확인했다.

| 오른손 지표 | 결과 |
|---|---:|
| 구 eligible event / 새 준비 필터 후 event | 3 / 2 |
| 구 목표방향 통과 / 새 accepted 목표통과 | 2 / 1 |
| 준비 전 / 추가 통과 | 0 / 1 |
| 최초 ready / current recovery 관측시각 | 3.1875 / 4.216666666666667 |
| 최종 current recovered / ever recovered | True / True |

RH는 실제 reset native step0의 body state와 당시 source SHA에 고정된 body-name 목록으로 geometry0을 구성하고, 저장 geometry1~1680을 순서대로 넣었다. 초기 접촉 정보는 필요하지 않다. geometry0의 피크와 저장된 첫 정책 관측의 차이는 최대1.75e-09 m이며, 원 raw crossing candidate는 그대로 재현되었다. 준비 전·추가 통과는 기존 native 기하 후보를 지우지 않고 별도 이유로 분리했다.

이 비교는 어떤 기존 행동이 새 측정에서 걸리는지 확인한다. 새 보상을 받은 정책이 실제로 개선됐다는 증거가 아니며, 압력·진동·음향·전곡 뮤팅·일반화도 인증하지 않는다. feature/sample 수를 음악 오류 횟수로 바꾸어 부르지 않는다.

[전체 분모·예시·이벤트·SHA](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_role_layout_v1/frozen_audit/trace_comparison_v2.json)
