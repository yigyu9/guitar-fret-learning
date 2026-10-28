# 검지 목표각 출력과 기존 증분 출력의 원인 분리

작성일: 2026-10-28. 기존 진단 실행 및 필요한 추가 작업에 대한 사용자 승인 범위에서 진행한다. 기본 학습은 변경하지 않는다.

## 근거와 가설

원 참고 요청1000회 지도학습은 NN-only 세 음91/128·A해제67/128로 기준에 미달했다. 같은 모델에서1000회를 더 학습한 reference_only와 corrective_mixed는 각각 전체0/128이었다. 전자는 접촉 하중 부족, 후자는 이전 접촉 잔류와 다음 위치 이탈을 보였으며 원장·기하·명령 재현은 일치했다. 관측에는 oldtarget을 복원할 q_offset/target_error와 시계가 있으므로 입력 누락으로 확정하지 않는다.

가설은 증분 명령의 근사 오차와 상태 분포 변화가 누적 목표를 바꾸는 부담이다. 기존 position fresh PPO 실패는 보존한다. 이번은 **같은1000회 참고 지도학습에서 출력 의미만 목표각으로 바꾸는 진단**이며, position PPO가 성공했다고 주장하지 않는다.

## 1. 최소 CPU 준비 → 검증

- 원 PrefixPolicy의561입력·같은 크기/가중치 구조와 원 fresh 초기값을 사용한다. 선택 검지4축만 정규화 목표각을 출력하고 나머지 명령은 원 경로다. reference/N은 NN 실행 중 주입하지 않는다.
- 기존 position의035 준비각 기준 부호별 full-native affine 변환을 재사용한다. 정책0은035 준비 목표이며 B 강제 복귀가 아니다. 목표각과 oldtarget 차이를 기존 역 codec으로 변환해 원 incremental controller에 요청한다. 원4rad/s·한계·PD/effort·current-goal DIP guard·나머지104열을 유지한다. 실제각/목표를 매 tick 덮어쓰지 않는다.
- 정책 출력4열, 변환 후 요청4열, guard 후 최종 목표를 구분한다. 새 adapter·정책/schema·checkpoint 정체성에 출력 의미를 명시한다. 원 incremental checkpoint를 goal checkpoint로 위장하거나 strict 계약을 완화하지 않는다.
- 참고 자료의 원 관측은 재사용한다. label은 원 reference_action이 사용한 **예정 desired(t+1/60)**를 원 일정으로 재계산해 full-native 정규화 목표로 바꾼다. 포화한 증분 요청으로 desired를 역추정하지 않는다. 기존 reference_action의 요청 재현을 먼저 확인한다. 새 목표 label과 실제 실행된 원 요청의 출처를 분리한다.
- 원1000회/192표본/6구간/seed7/Adam3e-4/clip.5/env0..2·env3 검산을 유지한다. finger_encoder/indexhead만 학습하고 critic/std/다른 state를 보존한다. 최종 모델1개·빈 새 PPO/update0·명시적 지도학습1000회 metadata를 저장한다. 새 조건은 추가1000회 조건의 실패 모델에서 시작하지 않는다.
- 표준편차의 수치가 같아도 두 출력 의미의 물리적 탐색은 같지 않다. 이번은 deterministic 초기화 비교에 한정하고 PPO/확률 탐색 비교로 확대하지 않는다.
- CPU 확인: native 양끝/035/중간각 왕복, 속도/범위 및 역 codec 재현, 선택4 외 보존·guard/부호·부분 reset, NN 요청이 참고각으로 교체되지 않음, label 출처/분할/예산·모델 불변/strict 정체성·출력 보호. 기존 공용 helper를 재사용하고 관련 검증만 추가한다.

## 2. GPU 실행 → 검증

- CPU 준비·change-reviewer PASS 후 root만 직렬 실행한다. 먼저 raw 목표각 reference를 **새 adapter를 통과시켜**128회 검증한다. 구 reference 요청을 우회 투입한 결과로 대체하지 않는다. 원 음악/해제 기준 미달이면 fit을 시작하지 않는다.
- reference 통과 시 고정1000회 fit과 NN-only128 deterministic 평가를 각각 한 번 실행한다. 고정 기타·유한 손목·다른 손가락B·엄지035·비엄지0.25Nm·원105/90충돌·원9보상·음 일정·물리/손목 종료를 유지한다.
- 통과 기준은 각음 달성/clean≥90%, wrong≤10%, 전체≥90%, A해제≥90%, 물리/손목실패0으로 고정한다. 실패 시 학습량/학습률/범위를 자동 탐색하지 않는다.
- 원128원장·사전4환경 관측·env0 trace에 raw 목표 출력/변환 요청/guard 최종 목표를 구별해 기록한다. 기존1000회 incremental 결과를 별도 출처로 비교하고, native 결과·힘/기하·누적 목표오차를 검산한다.

## 3. 해석과 다음 단계

자료와 출력 의미에 따른 비교 한계, 이전 position fresh PPO 실패, 같은 장면/seed·고정F4 범위를 함께 보고한다. 통과 전100PPO·자유기타/J33·67음으로 진행하지 않는다. 기본 구현 채택이나 자연스러움 해결로 해석하지 않는다. 원 결과와 저장공간 보호는 유지한다.

## 체크리스트

- [x] 이전 두 조건의 실패를 보존하고 독립 검수에 연결
- [x] 최소 adapter/typed 목표 label/fit CPU 준비 (독립 준비 검수 판정은 review.json에 별도 기록)
- [ ] 새 adapter reference128 실제 검증
- [ ] 고정1000회 지도학습·NN-only128 평가
- [ ] 실제 비교·그림·독립 검수 및 다음 단계 결정
