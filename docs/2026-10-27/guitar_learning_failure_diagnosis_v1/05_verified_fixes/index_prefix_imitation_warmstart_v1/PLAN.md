# 세 음 전환의 신경망 재현·초기값 진단 계획

작성일: 2026-10-28. 상태: 최소 CPU 구현 준비 승인·실행 전. 접촉 기억 실제 검수와 보상 목적 감사 검수를 완료하고, 이 준비 구현도 검수한 뒤에만 native 실행한다.

## 가정과 질문

원 계획은 실제 NN의 압현·해제·다음 음 수행을 확인하는 것이다. 실행 중 참고 각도를 대신 넣지 않는 조건을 유지하면서, 검증된 참고 동작을 **사전 지도학습 자료**로 사용할 수 있다고 가정한다. 이는 기존 fresh PPO와 다른 초기화 실험이고 RL만의 학습 성과나 자유 기타/전곡 성과로 보고하지 않는다. 기본 학습 코드는 바꾸지 않는다.

현재 세 음 fresh PPO는 A만 또는 B7/B8만 성공했고 전체 성공0/896이었다. 접촉 기억 비교의 예비 결과도 해제·전체 성공은0이었다. 보상 계수를 동시에 바꾸기 전에, 같은 신경망이 알려진 성공 동작을 표현하고 독자적으로 실행할 수 있는지 분리한다. 참고 동작을 네트워크로 재현해도 보상 구조의 적합성이나 장기 PPO 안정성이 입증되는 것은 아니다.

## 1. 기존 성공 참고 동작에서 필요한 관측만 추가 수집

- 기존3음 조건과 원 reference_action·pool·evaluator·0.25Nm readback을 재사용한다. 고정 기타, 유한 손목 안내, 원 current-goal DIP guard를 유지한다. 새 접촉 기억 제어를 섞지 않는다.
- 기존 참고 대조에는 사전 NN 관측이 저장되지 않았다. 새 한 번의128환경 첫시도에서 env0/1/2/3만 제어 직전 state/events/mask/priority_events/priority_mask와 요청된 선택4행동을 저장한다. 시간·원 target index·phase·종료/실패를 함께 기록한다. 전128의 음악·해제 분모도 보존한다.
- N/참고각도 주입은 이 명시적 비NN 자료 수집에서만 허용한다. 정책 평가와 이후 PPO에는 주입하지 않는다.
- NN-only 평가에서도 동일env0..3의 제어 전5관측·시계·선택4 요청/직전target을 같은 유한 크기로 보존한다. reference의 `requested_reference_action`과 NN의 `requested_NN_action`을 구분하고 NN 자료는 초기 fit에 넣지 않는다. 이 capture는 oracle 요청 계산을 호출하지 않는다.
- 검증: 참고의 각음/전체/해제≥90%, 물리·손목 실패0, 원 reward/시간/범위/속도 유지. 기존 결과를 새 NN 성과로 합치지 않는다.

## 2. 명시적 지도학습 초기화와 NN 전용 재생

- 원 fresh seed7 초기 모델에서 검지 head와 finger encoder만 지도학습한다. 나머지 actor, critic, 행동 표준편차는 원본 그대로 보존한다. PPO optimizer/critic/update 수를 이어받지 않는다.
- 지도학습 label은 실제 참고 요청 행동의 선택4열이다. 기존 원장·guard를 통해 물리로 보낸 행동을 자동으로 정답 요청이라고 바꾸지 않는다. 손가락 움직임 보상이나 관절 결합은 추가하지 않는다.
- 다른 actor 불변은 support/비선택 head **파라미터** 불변이다. 공유 finger encoder가 변하므로 비선택 head 출력 동일성은 주장하지 않는다. 실제 실행에서 다른 손가락은 기존 B 유한 제어를 따른다.
- 짧은 해제 구간이 긴 준비 구간에 묻히지 않도록 사전 지정한 A 접근/유지, 해제, 이동, 재접근, B 유지 구간의 평균 오차를 동등 가중한다. 이 가중은 지도학습 손실에만 적용하며 RL 보상은 유지한다.
- 예산은 Adam 학습률3e-4·1000회·배치192(6구간 각32개 복원추출)·seed7·gradient norm .5로 고정한다. env0/1/2를 학습, env3을 동일 장면의 미사용 관측 검산으로 두며 독립 seed/목표 일반화라고 부르지 않는다. 초기 접근 경계는 원 reference ramp_s, 나머지 네 경계는 원 schedule 값을 사용하며 제어 요청 끝점 시간으로 분류한다.
- 손실은 선택4열의 `tanh(mean)`와 참고 요청 행동 간 제곱오차다. ±1 label을 바꾸기 위한 임의 atanh clipping은 하지 않는다. 각 구간 RMS/최대오차와 누적 요청 오차를 보고한다. 최종1000회 모델 한 개만 native 평가하며 낮은 offline 오차로 물리 통과를 대신하지 않는다. 학습률·std·구간·모델을 native 성과에 맞춰 자동 탐색하지 않는다.
- 기존과 다른 초기화·자료/학습 이력·checkpoint metadata schema와 source/input SHA를 별도로 기록한다. 관측/행동/정책 구조는 원 PrefixPolicy 그대로이므로 원 환경/정책 계약을 위장 교체하지 않는다. CPU에서 초기73 tensor의 원 fresh initial 일치를 확인하고, 최종 cost2개0·전체 critic·다른 actor·std/buffer 불변을 검산한다. 지도학습 optimizer는 별도이며 저장 시 새 PPO optimizer/updates0을 명시한다. 원 checkpoint 계약을 완화해 읽거나 optimizer를 위장 상속하지 않는다.
- `metadata.settings`는 원 exact 검증의 source 설정이다. 원 `simple_start.initialization` 문구는 `source_settings_initialization`으로 인용하고 `settings_scope`와 새 `actual_initialization`으로 이번 지도학습 절차를 구분한다. 원문을 이번 초기화의 설명으로 주장하지 않는다.
- NN-only128 새 첫시도에서 첫 tick부터 선택4축을 NN이 제어한다. 참고4각도/N 목표를 평가 중 대신 넣지 않는다. 원 evaluator의 각음/전체/해제 기준과 실패 분모를 그대로 사용한다.
- 검증: 각음 달성/clean≥90%, wrong≤10%, 전체와 A 해제≥90%, 실패0. 학습 자료에서 오차가 작아도 native 기준에 미달이면 closed-loop 재현 실패로 기록하고 자동 장기학습하지 않는다.

## 3. 통과한 경우에만 원 PPO에서 유지 여부 확인

- NN-only 통과 뒤 별도의 fresh PPO optimizer로 이어 학습한다. 참고 감독·N 주입은 제거하고 원9항·gamma/PPO·std·제어·힘·곡을 유지한다.
- 유지 검사는 첫100회 PPO·50/100 각128평가를 1차 예산으로 고정한다. 초기 NN 성과와 PPO 이후 성과를 구분한다. 그 뒤300회 확장은 이 결과로 별도 결정하며, 새로운 보상 변경이나 접촉 기억 제어는 이 비교에 섞지 않는다.
- 학습이 다시 퇴행하면 보상 credit/탐색/목표각 누적을 추가 원인으로 좁히고 무작정 반복수를 늘리지 않는다. 그 다음 변경은 별도 계획으로 남긴다.

## 체크리스트

- [x] 접촉 기억 실제 결과·독립 검수와 보상 목적 감사 완료
- [x] 현재 증거에 비추어 단일 초기화 실험으로 필요성과 예산 확정(보상/제어/탐색 분산 고정)
- [ ] 최소 구현·CPU 검사·change-reviewer 검수
- [ ] reference 관측 수집과 원장/장면 종료 검증
- [ ] 지도학습·초기화 불변 검산·NN-only128 평가
- [ ] 통과 시에만 PPO 유지 비교 및 선정 영상·문서

보관/정리 중지와 원 기준·기존 진단 전체 제외는 계속 유지한다. 기존 활성 소스·봉인 자료는 수정하지 않는다.

CPU 구현 메모: 원 `parent.execution_scope/base.effort_scope` 안의 작은 관측 wrapper만 사용한다. reference/NN 평가 모두 원128 evaluator·native105/90쌍·현재목표 guard를 따른다. 별도 `fit`은 장면 없이 실행하는 GPU 학습 명령이며 현재 CPU 검사에서는 실행하지 않는다. 요청 끝점 구간별 control 수는 각env119/71/6/26/7/125이다. 수집 실패 endpoint는 저장하되 원 reference acceptance가 미달이면 fit gate가 거부한다.100PPO 유지는 아직 구현하지 않는다.
