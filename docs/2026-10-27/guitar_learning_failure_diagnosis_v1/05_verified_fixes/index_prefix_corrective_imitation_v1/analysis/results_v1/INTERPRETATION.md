# 해석과 다음 단계의 경계

동일 warmstart에서 같은 추가1000×192 예산을 사용한 두 조건 모두 음악·해제·AND 기준에 미달했다. 기존 warmstart의 all3 91/128과 달리 두 새 조건은 모두 0/128이다. 현재 예산에서 reference 반복과 저장된 NN 상태의 shadow label 보강만으로 개선되었다는 근거가 없으며 100PPO 유지는 시작하지 않는다. 이를 모든 학습 예산/알고리즘의 불가능성으로 확대하지 않는다.

| NN 조건 | A/B7/B8 달성 수 | all3 | A 해제 | 물리/손목 실패 |
|---|---|---:|---:|---:|
| 기존 warmstart, 별도 검수 출처 | 113/95/91 | 91 | 67 | 0/0 |
| reference_only | 27/7/11 | 0 | 52 | 0/0 |
| corrective_mixed | 51/76/76 | 0 | 1 | 0/0 |

각 행의 분모는128이다. 새 두 조건의256시도·768음과 기존 비교 출처를 합치지 않았다. reference_only는 세 음 모두 평균 wrong0이지만 충분한 clean/달성을 얻지 못했다. mixed는 B 달성이 reference_only보다 많으나 A wrong평균 .59375와 해제 저하가 동반됐다. 다른 환경의 상세 원인을 env0에서 일반화하지 않는다.

A 달성/해제를 교차하면 reference_only는 달성+해제11, 달성+미해제16, 미달성+해제41, 미달성+미해제60이다. mixed는 각각1/50/0/77이다. 해제 수를 모두 정상 압현 후의 해제 성공으로 읽거나, 미해제를 모두 전혀 접촉을 잃지 않은 사건으로 읽지 않는다. 원 released latch와 저장된60Hz 표본의 관찰 범위만 사용한다.

## Offline 오차와 새 실행 상태의 차이

| B hold의 PIP/DIP 요청 RMS | reference_only | corrective_mixed |
|---|---:|---:|
| 원 reference 관측, env3 검산 | .00514/.00647 | .02382/.01657 |
| 이전 warmstart NN 관측의 shadow, env3 검산 | .90578/.96214 | .08098/.07911 |
| 이번 새 NN 자체 관측·oldtarget에서의 shadow, env0..3 | .66145/.83838 | 1.24826/.84057 |

mixed는 학습에 쓰인 과거 NN 분포에 대한 검산 오차를 줄였지만, 새 실행이 방문한 상태에서 같은 수준의 보정을 재현하지 못했다. 새 NN의 CPU 요청 재현 잔차는 reference_only 최대5.96e−8, corrective_mixed 최대5.2154e−7이다. 이 작은 CPU 추론 차이와 shadow 요청의 큰 차이를 구분한다. shadow는 CPU에서만 계산한 반사실 요청이며 실행하거나 새 fit에 넣지 않았다.

같은 B hold 표본의 oldtarget−예정 reference 평균은 reference_only에서 MCPx/z/PIP/DIP=[+1.05,−2.50,−2.23,−3.52]°, mixed에서 [+22.11,−20.99,−15.31,+2.29]°다. 이는 네 관측 환경에 한정한 목표 누적 오차이며 침투량이나 단독 원인 증명이 아니다. 요청 차이 적분도 guard·범위·물리 추종을 통과한 실제 변위가 아니다.

## env0의 실제 기하·동작

reference_only는 A 음중 candidate9/11, release창0/6, 손목 이동0/26이었다. B7 음중 position/facing46/46이나 loaded0/46으로 candidate0이었다. B8은 position/facing21/21, loaded/candidate10/21이다. 음중 손목 위치오차 평균은 A/B7/B8=.198/.963/.533mm, distal 순힘 평균=.058/0/.106N이다. B7의 실패를 wrong나 손목 오차만으로 설명할 수 없다.

mixed env0는 A candidate11/11, release창6/6, 이동26/26으로 이전 A 접촉 후보가 남았다. B7은 position0/46, wrong7/46이며 선택 distal의 own-wrong-fret5·own-wrong-string7이 겹쳐 관찰된다. B8은 loaded/position/candidate0/21이다. B7/B8 손목오차 평균13.38/10.12mm, 실제 PIP 음끝1.425/약0°, DIP32.13/31.06°다. A/B7/B8 distal 순힘 평균2.574/.375/0N이며 B8 검지 body2(LH:index2)에는 평균6.495N이 남는다. 목표·손가락 상태·손목 피드백이 함께 달라졌으므로 한 축/접촉쌍으로 원인을 확정하지 않는다.

CPU 기하 재구성은 저장 candidate/wrong와 불일치0, 기존1µm 초과 scalar 잔차0이다. 원 9항 합과 총보상의 최대 잔차는3.505e−6이다. 원73 상태/허용 모듈만 변경·critic/std 불변·cost2zero·빈 PPO/update0·원 identity와 새 조건 metadata·장면 닫기·입력 불변이 검산됐다. CPU 검사는 native CUDA 전체 strict 복원을 대신하지 않으며 실제 strict load 성공은 native 보고서의 출처로 구분한다.

상세 각/힘/기하/손목은 env0 60Hz, 제어 전 관측은 env0..3에 한정한다. body resultant는 접촉쌍 압력/실제 줄 압력이 아니며 candidate off는 피부 전체 분리 인증이 아니다. 이번 결과는 조건부 고정 기타의 NN 초기화 검사이며 자연스러운 압현·자유 기타/J33·전곡 학습 성공을 뜻하지 않는다. 새로운 학습·문턱 변경·예산 확대는 실행하지 않았다.
