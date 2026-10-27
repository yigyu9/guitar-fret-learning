# 준비035에서 팔·손가락 탐색의 기하학적 규모

2026-10-27. GPU·물리 시뮬레이션 없이 실제 controller의 목표각 변환과 source FK만 계산했다. **같은 std가 같은 패드 탐색 크기를 만들지는 않는다. 단일 tick에는 팔의 효과가 컸지만, 누적 손가락 탐색을 포함하면 차이가 줄고 평균 주변 분산의 순서도 달라졌다.** 이를 실제 손가락 움직임이나 학습 gradient 비율로 해석할 수는 없다.

## 미리 고정한 조건

[사전 계획](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/exploration_conditioning/precommit.json)은 실행 전에 기록했다. seed20261027, latent mean0/std=exp(−3)=0.049787068, 물리 행동은 tanh(std×z)이다. 단일 tick256표본, 독립16개×180tick의 iid 난수 궤적을 사용했고60tick은 같은180tick 궤적의 앞부분이다. pilot의 학습 로그나 결과로 조건을 선택하지 않았다.

같은16차원 표준 Gaussian 표본을 재사용해 팔12축에는 앞12개, 엄지를 제외한 손가락16축에는16개를 원래 행동 순서대로 넣었다. 다른 그룹·엄지5축·오른손6축 행동은0이다. 그룹 차원 수가12/16이며 각 패드에 직접 작용하는 손가락은 자기4축이라는 차이가 있다. 전체 행동 에너지나 자유도 수를 같게 정규화한 비교는 아니다.

기준은 **준비035 controller.reference105의 목표각 FK**다. 실제 준비 q/body는 FK 보정에 사용하고, 탐색 대상이 아닌 q는 controller reference에 고정했다. 따라서 실제 준비 자세에서 물리가 한 tick 진행한 결과와 구분해야 한다. 기존 [native 대 source-FK 교차 검산](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/wrist_pose_proposal_readonly.json)의 helper를 재사용했다.

## 실제 codec과의 일치

- 팔: reset reference 기준의 비대칭 affine position 행동, alpha0.2,3rad/s, native/action 범위 clipping.
- LH21: 이전 target에 action×4/60을 누적, smoothing 없음,4rad/s 및 native 범위. 이번 손가락 조건에서는 nonthumb16만 활성화했다.
- 최초 target은 reference이고 매 tick의 목표 target을 다음 tick에 이어 사용했다. 작은 난수를180회 독립 적용한 뒤에도 손가락 target은 이전 누적값을 기억한다.

NumPy 변환은 **실제 BatchedController.targets 메서드를 CPU tensor oracle로 호출해 모든 표본과 tick의 선택 채널을 대조**했고 최대 오차는0rad였다. 발 IK는 두 그룹과 분리된 하체 분기이므로 oracle에서만 identity로 두었다. 하체 물리/IK를 재현했다고 주장하지 않으며, 선택한 팔/손가락 target은 실제 메서드와 직접 같음을 검사했다.

controller.py SHA는 원래 baseline 초기 평가와 같았다. 분석 실행 전후138개 입력 SHA가 일치했고, 저장 배열은 모두 유한하며 native action 범위와 비활성 축 reference 고정을 통과했다. [전후 검증](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/exploration_conditioning/verification.json)에 결과·원시 표본·스크립트 SHA가 있다.

## 시작점에서 얼마나 떨어졌나

각 패드의 유효 source128점을 FK로 변환했다. 아래 값은 **시작 pad centroid에서 endpoint까지의 거리 중앙값(mm)**이다. 전체 이동 경로 길이나 실제 손가락 이동량이 아니다. 단일 tick은256표본,60/180tick은16개 궤적의 endpoint를 집계했다.

| 시점·그룹 | 검지 | 중지 | 약지 | 소지 |
| --- | ---: | ---: | ---: | ---: |
| 1tick 팔12 | 2.097 | 2.073 | 2.065 | 1.982 |
| 1tick 손가락16 | 0.276 | 0.323 | 0.200 | 0.217 |
| 팔/손가락 | 7.60배 | 6.42배 | 10.35배 | 9.14배 |
| 60tick 팔12 | 6.041 | 5.611 | 5.576 | 5.081 |
| 60tick 손가락16 | 1.746 | 2.114 | 1.690 | 1.763 |
| 팔/손가락 | 3.46배 | 2.65배 | 3.30배 | 2.88배 |
| 180tick 팔12 | 5.544 | 5.116 | 5.123 | 4.847 |
| 180tick 손가락16 | 3.499 | 4.276 | 2.295 | 3.003 |
| 팔/손가락 | 1.58배 | 1.20배 | 2.23배 | 1.61배 |

단일 tick에서 활성 축당 target 변화 RMS의 중앙값은 팔0.172°, 손가락0.183°로 비슷했다. 그런데 pad centroid 변화는 크게 달랐다. 이 조건에서는 팔의 긴 기하학적 지렛대와 여러 상위 관절의 영향이 한 tick 패드 변위를 크게 만들었다는 단서다.

60/180tick의 축당 target 변화 RMS 중앙값은 팔0.385°/0.365°, 손가락1.469°/2.223°였다. 팔 position은 reference 주위로 돌아오는 필터이고 손가락 incremental은 누적되므로 동일 std를 하나의 고정 배수로 비교할 수 없다. 손가락의 axis-tick clipping 비율은60tick까지3.31%,180tick까지2.10%였다. 경계 clipping으로 누적 분포도 영향을 받는다.

전체128점 RMS 변위의 중앙값도 단일 tick에서 팔약1.98~2.10mm, 손가락약0.20~0.32mm로 centroid와 비슷했다. 원시 결과에는 endpoint 최대 표본점 변위, centroid 최대 이탈, target 경로 길이도 별도로 저장했다.

## 평균 이동과 탐색 폭은 다르다

시작점에서 멀어졌다는 값에는 평균이 한쪽으로 치우친 효과도 포함된다. 팔 position의 reference~상/하한 거리가 비대칭이고 유한 표본이므로 zero-mean latent가 zero-mean 기하 이동을 보장하지 않는다.60/180tick의 팔 평균 centroid는 시작점에서 약3.4~4.7mm 떨어졌다.

이 혼동을 피하려고 **같은 고정 표본에서 표본 평균을 뺀 centroid RMS 분산 폭**을 추가로 계산했다. 조건을 새로 고르거나 난수를 더 뽑은 것은 아니다. 아래는 그 분산 폭(mm)이다.

| 시점·그룹 | 검지 | 중지 | 약지 | 소지 |
| --- | ---: | ---: | ---: | ---: |
| 1tick 팔12 | 2.318 | 2.262 | 2.249 | 2.161 |
| 1tick 손가락16 | 0.337 | 0.371 | 0.256 | 0.285 |
| 60tick 팔12 | 3.607 | 3.431 | 3.494 | 3.328 |
| 60tick 손가락16 | 2.305 | 2.562 | 1.934 | 1.665 |
| 180tick 팔12 | 3.812 | 3.654 | 3.712 | 3.523 |
| 180tick 손가락16 | 3.817 | **4.561** | 2.914 | 2.848 |

180tick에서는 검지의 분산 폭은 거의 같고 중지는 손가락 쪽이 더 크다. 따라서 **“팔 탐색이 모든 시간 규모에서 항상 더 크다”는 해석은 이 표본에서도 성립하지 않는다.**180tick의16개 궤적은 작은 예산의 정량 단서이며, population 추정이나 신뢰구간으로 확대하지 않는다.

![controller target의 source-FK 변위와 평균 주변 분산](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/exploration_conditioning/exploration_displacement.png)

위쪽 error bar는 표본 p05~p95 분위이며 신뢰구간이 아니다. 아래쪽은 평균을 뺀 RMS 분산 폭이다.

## 무엇을 판단할 수 있나

같은 latent std를 팔 position과 손가락 incremental에 공통 적용하는 것은 **동일한 단기 기하 탐색 크기를 맞추는 설정이 아니다.** 짧은 tick에서는 팔 움직임이 모든 패드 위치에 더 크게 반영될 수 있고, 손가락은 더 긴 시간에 걸쳐 target이 누적된다. 행동 방식·시간 규모·기하 지렛대를 함께 보아야 한다.

이 결과만으로 실제 학습에서 팔이 손가락보다 몇 배 더 움직였는지, 보상 gradient를 가져갔는지, 충돌 때문에 손가락이 멈췄는지를 판단할 수는 없다. source FK에는 관성·하중·힘 제한·PD 추종·접촉·손목 종료·음악 성공 판정이 없다. 실제 정책의 learned mean이나 시간 상관도 입력하지 않았다. std 변경이나 제어 방식 변경은 별도의 실제 GPU 대조로 검증해야 한다.

[상세 수치](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/exploration_conditioning/results.json), [고정 난수·target·기하 표본](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/exploration_conditioning/samples.npz), [분석 코드](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/exploration_conditioning/support/analyze_exploration.py)를 저장했다.
