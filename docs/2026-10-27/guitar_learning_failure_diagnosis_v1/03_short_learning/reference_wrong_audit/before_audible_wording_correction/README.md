# 중지 reference env0 오압현 출처 감사

incremental 제어의 지정 중지 reference 대조군에서, 음이 실제로 들리는 구간에 저장된 **8개 60Hz 끝점 모두 지정 중지 자신의 잘못된 프렛·줄 판정**이었다. 다른 손가락의 더 높은 프렛 간섭은 이 8개 표본에서 관측되지 않았다. 따라서 이 사례의 저장된 끝점은 다른 B 손가락 간섭보다 중지 패드의 목표 셀 불일치를 먼저 가리킨다.

## 대상과 확인 결과

대상은 [원본 평가](../smoke_wrist_inc_row8_reference/evaluation.json)의 env0 첫 에피소드다. 학습된 정책이 아니라 고정 손목 teacher와 선택 중지 4축의 유한 reference 동작을 사용한 대조군이다. 원본 요약은 압현 달성 false, clean 비율 0, audible wrong 비율 1이다.

| 항목 | 목표 또는 관측 |
| --- | --- |
| 원래 목표 | `event-000052/string-3/note-53`, 중지, 물리 3번 줄·7프렛 |
| 원래 음 시간 | 22.319–22.4364초 |
| 저장 audible 끝점 | 로컬 3.000–3.116667초, 총 8개 |
| 자신의 다른 프렛 | 8/8; 중지 끝마디 패드 sample12가 물리 3번 줄·6프렛으로 판정 |
| 자신의 다른 줄 | 8/8; 같은 중지 끝마디 패드 sample28이 물리 4번 줄·6프렛으로 판정 |
| 다른 손가락의 높은 프렛 | 0/8 |
| 지정 패드 positive / clean candidate | 각각 0/8 |
| 독립 재계산과 production·원본 저장 판정 불일치 | 0 |

두 원인은 같은 중지 `human/LH:middle3`에서 나왔다. 오압현 감점은 이 원인들의 합집합이며 두 번 더하는 감점이 아니다. 첫 끝점에서 sample12 높이는 2.635mm, 방향 cosine은 0.905였고, sample28은 1.243mm·0.978이었다. 해당 몸체 resultant는 8개 표본에서 8.352–9.657N이었다. 목표 셀까지 가장 가까운 적격 패드 표면 거리는 약 3.29–3.71mm였다.

## 재검산 방법

원본 `q`, controller target, native body pose와 net body force를 그대로 읽었다. 실제 물리 상태나 접촉을 합성하지 않았다. 중지에 할당된 pad뿐 아니라 다른 손가락의 virtual source도 함께 계산했다. 기존 단계2 독립 NumPy 재구성 함수를 재사용해 10개 손가락 몸체의 표면점·normal·셀·하중 조건과 원인별 mask를 복원하고, production helper 및 저장된 candidate/wrong와 비교했다. 원래 목표·원래 score 시각을 유지한 검사이며 다른 곡 시각으로 바꾸는 counterfactual 검사가 아니다.

[상세 결과](results.json)는 끝점별 물리 tick, score 시각, source body, 원인별 실제 셀·패드 sample, 선택 4축 actual/target 각도를 보존한다. [실행 전](inputs_before.json)·[실행 후](inputs_after.json) SHA는 원본 trace, 원곡, 측정 소스, 재사용 함수와 실행 스크립트를 포함한다. 원본 캡처와 6개 측정 소스의 SHA도 일치했다.

## 해석의 한계

- 저장 간격은 60Hz이고 실제 물리는 240Hz다. 끝점 사이 3개 물리 표본은 저장되지 않아, 전체 오압현 적분의 모든 순간을 출처별로 인증할 수 없다.
- net body force는 접촉 상대나 특정 줄의 압력을 인증하지 않는다. 여기서의 줄·프렛은 현재 기하·하중 판정의 출처다.
- 선택 중지 4축을 reference가 직접 움직인 대조군이므로 학습 정책 성과로 볼 수 없다. 한 가지 처방 자세로 도달 불가능성이나 근본적인 학습 불가능성을 결론 내릴 수 없다.
- position 대조군의 env0 성공 raw는 별도 조건이다. incremental env0 실패와 합쳐 동일 조건의 증거로 취급하지 않는다.
- GPU를 실행하지 않았고 활성 패키지·정책·teacher·기존 로그를 수정하지 않았다.
