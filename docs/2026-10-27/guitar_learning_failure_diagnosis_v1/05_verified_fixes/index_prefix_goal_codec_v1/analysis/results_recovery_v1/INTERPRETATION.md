# 음악 개선과 A 해제 미달의 분리

새 goal 출력 NN은 음악 기준을 통과했으나 A 해제 기준에 미달했다. 따라서 AND readiness는 False이고100PPO를 시작하지 않는다. 원 fit은 종료1·보고서2개 누락을 보존했으며, 별도 독립검수된1000회 산출물의 회복 수용 뒤 이 NN 평가만 종료0이다. 새 fit·추가1000회는 없다. 모델/fit 자체 감사는 회복 검수 근거를 재사용했다.

| 별도 출처의 조건, 각128시도 | A/B7/B8 달성 수 | all3 | A 해제 | 음악/해제/AND |
|---|---|---:|---:|---|
| 원 incremental1000 NN | 113/95/91 | 91 | 67 | False/False/False |
| 새 goal reference, noNN | 128/128/128 | 128 | 128 | True/True/True |
| 새 goal1000 NN 회복 평가 | 126/128/128 | 126 | 73 | True/False/False |

새 NN의 clean평균은 A/B7/B8=.982610/.983079/1, wrong0이고 물리·손목실패0이다. 새128시도/384음과 기존 비교 출처를 합치지 않았다. 같은1000회·같은 fresh 파라미터 값과 구조를 사용했지만 출력 의미/학습 label 단위/정체성이 바뀐 deterministic 초기화 비교이며, 확률 PPO나 자연스러운 손동작의 해결로 해석하지 않는다.

A 달성+해제71, 달성+미해제55, 미달성+해제2, 미달성+미해제0이다. 따라서 해제73을 모두 정상 압현 후의 해제로 세거나, 미해제를 압현 자체 미달로 설명하지 않는다. released73개의 원 source release_s−A end는 최소.000533/중앙.017200/최대.096367s다. 이것은 원 native 원장의 시각 차이며, 저장60Hz 후보에서 새로운240Hz 사건을 추정한 값이 아니다.

## 원 해제창의 목표와 요청

원 phase2의 여섯 요청 endpoint만 env0..3에서 보았다(24행). 음수 물리 DIP 요청은 각 환경4회, 양수2회이며 DIP guard blocked는0/24이다. 마지막 요청 endpoint3.266667s의 decoded 목표와 제출된 final 목표는 모두 full N보다 DIP+2.198~2.253°에 있고, 같은 시각 예정 desired보다+2.078~2.132°에 있다. PIP도 full N보다+1.700~1.742°다. full N과 그 시각 아직 보간 중인 desired를 구분한 값이다.

따라서 이24표본에서 열기 방향 물리 요청이 guard에 막혔다는 근거는 없다. NN이 낸 목표가 예정 해제 목표와 달랐고 제출 목표는 그 decode 값에 맞았다. N 방향의 부호는 reference→N 벡터로 명시했다(MCPx는양수, 나머지는음수). 모든 행동 부호를 해부학적 열기로 일반화하지 않는다. N 자체도 전체 피부 분리나 다른 접촉 해제를 보장하지 않는다.

env0의 A 후보는 해제창6/6 남았다. 마지막 창 안 저장 endpoint에서 actual PIP/DIP−full N은+2.189/+2.816°, target 오차는+1.742/+2.253°다. 최초 **저장60Hz** A 후보off는3.283333s(A end+.113033s)로 원+.10s 창 밖이며 native A released=False와 일치한다. 정확한240Hz 최초 후보 이탈은 이 trace에서 복원하지 않는다. 네 관측 환경의 목표 오차를 다른124환경의 상세 원인으로 확대하지 않는다.

원 reference 상태 env3의 검수된 phase2 normalized-goal PIP/DIP RMS는.001630/.001147이다. 이번 NN 자체 상태24표본의 값은.025309/.018066이며, 각도 오차 RMS는.964/1.251°다. 출력/상태 분포 차이와 해제창 목표 지연을 함께 관찰할 수 있지만, 한 요인이 전체55건의 해제 미달을 유발했다고 확정하지 않는다. raw 목표 NN CPU 재현 잔차는2.384e−7이고 decode·물리 요청 재생 잔차는0이므로 변환 오류와 구분된다.

## 기존 관측 token의 전환

아래는 env0에서 읽은 precontrol 표이며 같은4환경에서도 동일한 선택 전환을 확인했다. 세 source onset으로 token을 식별할 때 최대 시간 복원 잔차는1.114e−7s다.

| precontrol local시각 | main events/mask | index tracking / next | A 관련 정보 |
|---|---|---|---|
| 3.166667s | A4/B7/B8 | A4/B7 | A end_delta+.003633s |
| 3.183333s | A4/B7/B8 | B7/B8 | A end가 지난 token은 main에 남음 |
| 3.266667s | A4/B7/B8 | B7/B8 | A main token 유지; 다음 요청 endpoint3.283333s는 창밖 |
| 3.283333s | B7/B8 | B7/B8 | A main token 제거 |

priority의 A tracking은 A end 직후 B7으로 바뀌지만, main event에는 원 end_delta/candidate/released 정보가+.10s 유예까지 남아 있다. global clock도 존재한다. 따라서 시계 누락이나 A 관련 정보 전체 부재로 단정하지 않는다. 별도 N3phase label이 원 입력에 직접 제공된다는 뜻도 아니다. token 전환과 NN raw goal 지연의 동시 관찰만 제시하며, NN이 어느 token을 실제로 사용했는지나 인과적 필요성을 증명하지 않는다.

## 검산 범위

원9항 합 최대 잔차는5.682e−6, CPU 기하 candidate/wrong 불일치와1µm 초과 scalar 잔차는0이다. native105/0.25Nm/90쌍·닫기·alias·입력 감사와 NN1/reference_calls0·모델/RNG frozen을 원 보고서로 확인했다. 모델 감사의 full identity/73/54불변19허용·빈PPO0 등은 별도 회복 검수 출처이며 이번 CPU 모델 추론으로 CUDA strict 복원을 대체하지 않는다.

env0 음중 distal 순힘 평균은 A/B7/B8=.139/.232/.277N, 손목 위치오차 평균=.818/.999/1.075mm다. 상세 물리관찰은env0 60Hz, 제어전관측은4환경에 한정한다. body resultant는 실제 줄 압력/접촉쌍 인증이 아니고, 기준 통과는 자연스러움·자유 기타/J33·전곡 성과를 뜻하지 않는다. 추가 학습·문턱 변경·native 재실행은 하지 않았다.
