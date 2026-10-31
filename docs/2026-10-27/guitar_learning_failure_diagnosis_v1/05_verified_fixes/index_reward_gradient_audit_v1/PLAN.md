# V6 보상·구간별 초기 정책 기울기 진단

이전 goal turn은 진행이었다. V6의 실제300회와7평가·분석·영상 검수를 완료했고, 비용 신호가 전구간0이어도 압현이 퇴행한다는 새 근거를 얻었다. 비용 초기값 계획 5번의 후속 진단을 진행한다. 기존 사용자 승인 범위인 실패 진단과 필요한 추가 작업이며, 장기 학습이나 생산 보상 변경은 이번 진단에 포함하지 않는다.

## 확인하려는 문제

같은 신경망이 접근·압현 유지·해제에서 상반된 행동을 학습하는지, 어떤 보상과 공통 가치 예측 잔차가 정책 기울기를 주도하는지 측정한다. 기울기 충돌은 관측 근거이며 단독 원인이나 개선 성공을 뜻하지 않는다.

## 사전 고정 범위

- 원 V6 fit1000/update0, update50, update100, 마지막300 네 저장본. 점수가 나쁘더라도 제외하지 않는다.
- 각 저장본에서 fresh reset, seed7, 원128환경, 전곡이 아닌 기존3음 과제354tick을 확률적으로 수행한다. V6 기존 엄격 load/입력/물리/9보상/실패 비용/cost_weight1을 유지한다. 저장본을 갱신하지 않는다.
- 원 DecisionCollector를 사용하고 H32씩 연결한다. 마지막은2tick이다. 종료 시 nextV/reset/GAE는 실제플래그를 따른다. H32 GAE와 마지막2tick은 구분한다.
- 이것은 고정 저장본의 새 확률 수행과 full-rollout 초기 기울기다. 과거 학습의 실제 미니배치·KL재시도·Adam변화를 복원했다고 주장하지 않는다.
- 실제 음악 phase는 score clock과 A/B7/B8의 press/onset/end·A해제deadline으로 나눈다. 원 reference 동작구간이나 정책 J단계와 혼동하지 않는다. 전이의 출발시점 phase를 사용하며 경계 통과 tick도 별도로 기록한다.

## 정확한 분해

원 compute_decision_gae를 사용해 9개 reward stream의 zero-value GAE와 별도 공통 reward critic/bootstrap 잔차, 비용 advantage 기여를 분리한다. 합은 원 reward/cost GAE 및 joint 정규화 advantage와 오차 범위 내 일치해야 한다. 각 항의 독립 표준편차를 쓰지 않는다.

고정 정책의 ratio1 지점에서 원 total-advantage clipped loss와 항목별 선형 surrogate의 gradient 합을 검산한다. phase mask의 분모는 phase행 수가 아니라 원전체 valid행 수다. 전체 actor parameter gradient의 norm·cosine 및 선택4축 mean에 대한 방향을 기록한다. gradient clipping·Adam parameter delta의 항목별 분해라고 설명하지 않는다.

## 단계와 검증

- [ ] 진단 wrapper·수학·CPU fixture 구현: 최종9보상 합, terminal/truncation/reset/H경계, 정규화/gradient합, 입력봉인·오류시복원 검사.
- [ ] 별도 준비 검수·새 소스/네 저장본/기존549핀 SHA 봉인. Isaac/수치 import 전 gate 확인.
- [ ] GPU 네 수행을 직렬로 수집하고, 저장본/model/optimizer/입력 불변·원128시도/384음 분모·no PPO/no fit를 확인한다.
- [ ] 실제 rl38 CPU에서 저장 buffer의 원 입력·표본·가치로 독립 재계산하고 phase/reward별 그림·분석과 독립 검수를 남긴다.
- [ ] 근거에 따라 다음 단일 개선을 고른다. 전체 원계획의 다른 seed·손가락·자유 기타/J33·67음은 계속 미완료다.

원자료는 압축된 원 rollout으로 보존해 gradient 검산을 가능하게 한다. 중복 full stream·영상·모델 사본을 만들지 않는다. 실행 이후 이 PLAN은 입력으로 동결하고 현재 상태는 상위 README/status/전체계획에 기록한다.
