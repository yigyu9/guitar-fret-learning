# 기타 오른쪽 초기 이동 사전 검수

요약 판정: 현재 source V2·native wrapper V2·config_v1 package 문제없음. Critical: 0

읽기 검수와 저장 결과의 독립 검산만 수행했다. 물리 실행 및 원본/타인 파일 수정은 하지 않았다. 이 판정은 새 5초 native 실행의 사전 조건 검수이며 지지·타현 성공 인증은 아니다.

## Critical

- 현재 버전: 0. [run_right_shift_initial_v1.py:51](/home/ajou/yigyu/3/stability_adapter_2/run_right_shift_initial_v1.py:51)의 새 기준 initial_values 직접 읽기가 기존 attempt 입력 목록에서 누락된 점을 보고했다. 새 [run_right_shift_initial_v2.py:30](/home/ajou/yigyu/3/stability_adapter_2/run_right_shift_initial_v2.py:30)는 해당 파일을 native 시작 전 SHA 목록에 추가한다. V1은 보존하고 실행에는 V2를 사용한다.

## Warning

- [search_right_shift_initial_v2.py:34](/home/ajou/yigyu/3/stability_adapter_2/search_right_shift_initial_v2.py:34): EW6 경로 검사는 pin된 V1의 5개 waypoint와 중간점 1개 결과를 계승한다. 모델/오차/전완 캡슐 간격 조건은 확인되지만 경로 전체의 손·손가락 swept 비겹침이나 실제 타현을 인증하지 않는다. V7 requested/final target guard를 유지한 실제 5초·원 detector 결과로 판단한다.
- [search_right_shift_initial_v2.py:37](/home/ajou/yigyu/3/stability_adapter_2/search_right_shift_initial_v2.py:37): Thorax 상한은 baseline 34.772080mm에 5mm를 더한 39.772080mm이다. 이 조건은 기존 근접 수준을 비교하며 Thorax 접촉을 요구하지 않는다. 10mm 후보의 상완 캡슐 간격은 0.171749mm로 작고, 20mm 후보의 −0.289019mm는 source 기각 근거다. 어느 값도 cooked 관통량·연속 접촉력·실제 지지 인증으로 설명하지 않는다.
- [run_right_shift_initial_v2.py:52](/home/ajou/yigyu/3/stability_adapter_2/run_right_shift_initial_v2.py:52)의 57개 raw DOF 비교는 초기 상태 불변 조건이다. 실행 중 다른 75개의 목표를 유지하는 조건과 실제 75개 관절 상태가 고정된다는 주장을 구분한다.

## 확인 근거

- [search_right_shift_initial_v1.py:33](/home/ajou/yigyu/3/stability_adapter_2/search_right_shift_initial_v1.py:33): R_Hip−L_Hip의 수평 unit 방향으로 해부학적 오른쪽을 정의한다. 두 결과의 축 norm=1, 축 투영 이동은 각각 10.000013/19.999997mm였다. 수락 후보 실제 기타 이동은 (+9.992540,+0.386536,0)mm이며 회전과 root/하체 배치는 유지한다.
- [search_right_shift_initial_v1.py:49](/home/ajou/yigyu/3/stability_adapter_2/search_right_shift_initial_v1.py:49): 양팔 24각만 초기 fit하며 오른 Thorax/Shoulder는 ±0.2rad, 나머지 팔은 ±0.3rad와 모델 bounds의 교집합이다. 두 결과의 고정 57각 exact·초기 모델 한계·보정 범위를 독립 확인했다. 양팔 8개 ball norm 160° 미만 조건도 최종 수락에 포함된다.
- [search_right_shift_initial_v2.py:18](/home/ajou/yigyu/3/stability_adapter_2/search_right_shift_initial_v2.py:18): V1 report/before 및 V2 source/plan을 먼저 pin하고, V1 전체 입력이 현재와 같은지 확인한 뒤 재구성한다. 현 source V2 map의 모든 SHA 불일치 0, 실제 human/guitar XML과 선언 mesh 37/69 전체 포함을 확인했다.
- [search_right_shift_initial_v2.py:32](/home/ajou/yigyu/3/stability_adapter_2/search_right_shift_initial_v2.py:32): 현재 각/이동으로 whole source LP와 공유 6면 조건 및 캡슐을 다시 검사한다. 최종 source 수락은 right10mm 하나, right20mm는 상완 음수 간격으로 기각이다. 준비 피크 오차는 각각 0.010347/0.032810mm이며 저장된 6개 EW6 sample 모두 모델 한계 안이었다.
- [finalize_right_shift_config_v1.py:13](/home/ajou/yigyu/3/stability_adapter_2/finalize_right_shift_config_v1.py:13): historical left joint_delta/frozen48/fit counts를 현재 최소 metadata로 교체한다. 그 외 candidate 전체와 cfg 실행 설정은 source V2 수락 후보와 정확히 같았다. package before 입력의 현재 SHA 및 cfg의 새 candidate SHA도 일치한다. metadata package는 추가 geometry/physics 후보가 아니다.
- [run_right_shift_initial_v2.py:49](/home/ajou/yigyu/3/stability_adapter_2/run_right_shift_initial_v2.py:49): 초기 57각 raw exact, 기타 전체 body quaternion raw exact 및 동일 이동 오차 3µm, 모델·PD·질량·FK·whole LP·초기 6면 검사를 유지한다. [run_right_shift_initial_v2.py:169](/home/ajou/yigyu/3/stability_adapter_2/run_right_shift_initial_v2.py:169)는 기존 V7 제어 patch를 재사용하며 새 force/gain/state write를 추가하지 않는다. 현재 5개 새 Python 파일 AST 검사를 통과했다.

## Suggestion

- 선택 사항 없음. 현재 자세 보관함 byte-copy 최종 감사 및 새 native 원자료/타현 판정은 root의 후속 범위로 남긴다.

검수 native wrapper SHA: `f40882380398c93473a9fefe9695116941c5a3559646c11994aac6c035c4d8d3`.
