# 음악 정책 Jacobian sampling 호환성 검수 v3

2026-10-15. 독립 change-reviewer가 신규 v3 환경·실행기·테스트·native 진단 기록을 검수했다. 기존 소스와 결과는 수정하지 않았다.

## 요약 판정

코드의 Critical은 발견하지 못했다. **수정 권장: 실제 qualification의 범위를 제한하여 판정해야 한다.** 원래 실패한 명령 replay와 zero-action 전체 시간축은 통과했지만, ±0.8 uniform random 행동은 모두 중단했다. 따라서 전체 7개 qualification 통과나 넓은 행동 탐색 안정성 확보를 주장할 수 없다. 이후 제한된 pilot을 실행하더라도 오류 시 fatal·미완료 rollout 미학습 조건을 유지하는 추가 검증 실행이다.

## 보존된 v2 실패

[pilot_b16_v2/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/pilot_b16_v2/report.json)은 153 attempted / 152 valid / 0 accepted PPO steps / 0 갱신, 파라미터 변화 0으로 중단했다. 실패 control은 물리608에서 시작하여611까지 진행했다. 그 시점의 전체 COM 최대 잔차는 현재 Jacobian 0.000778946m/s, 이전610 Jacobian 0.010418709m/s였다. faulting controller의 effort는 제출되지 않았다. 152개 미완료 rollout 전이를 정상 종료 전이로 바꾸거나 학습하지 않았으며, 실패 원본과 fault checkpoint는 보존되어 있다.

## 구현 검수

- [environment_v3.py:36](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/environment_v3.py:36)는 각 시점 후보에서 전체 human COM 및 모든 지지점 잔차의 최대값을 계산한다. 현재 후보 전체가 0.01m/s 이하면 현재를 선택하고, 그렇지 않을 때 정확히 k−1 후보 전체가 통과해야 fallback한다. body/component별 최소값을 섞지 않는다. 두 후보가 실패하면 typed `JacobianConsistencyError`로 중단한다.
- 이전 Jacobian은 정확히 한 물리 step 전이어야 하고 초기 시점은 기존 zero-velocity 규칙을 유지한다. 후보 support point는 해당 후보 pose의 lever를 `Jpoint`와 `native COM velocity + angular velocity × lever` 양변에 동일하게 사용한다. 이전 후보의 판정은 해당 candidate lever에서의 sampling 호환성이지 현재 실제 지점의 정확한 물리 검증이 아니다.
- 각 body angular 잔차는 rad/s 진단으로 기록한다. 0.01m/s 문턱을 angular 값에 적용하거나 angular consistency까지 인증했다고 주장하지 않는다.
- 중력 및 지지점 torque는 계속 현재 Jacobian·현재 pose에서 계산한다. PD, 힘 cap, effort cap과 물리/행동 경로는 기존 구현을 유지한다. 선택한 validation Jacobian으로 torque를 바꾸지 않는다. v3 reset은 새 제어기를 설치하고 ABI/metadata에 검증 계약을 남긴다. 신규 실행기와 launcher의 변경은 환경 import 및 자기 실행 경로다.
- 어느 후보의 `J·qdot` 잔차 통과도 해당 관측 속도와의 호환성만 확인한다. solver projection 원인이나 Jacobian 전체 방향·현재 torque Jacobian 정확성을 단독으로 증명하지 않는다. 문턱, 데이터 폐기 방식 또는 학습 종료 의미를 완화하지 않는다.

## 검증 결과

전체 CPU 31개 테스트(events7 + environment11 + reward-v2 4 + alignment-v3 5 + runner4)가 통과했다. 추가로 실제 `_validation_jacobian` 경로에 isolated CPU fixture를 사용하여 current COM 통과/support 실패 시 전역 fallback, 서로 다른 시점의 COM/support를 섞어야만 통과하는 경우 typed fatal, 잘못된 historical timestamp의 fatal 처리를 확인했다. 이 세 검사에서 native import의 skew 함수만 isolated fixture로 대체했다. 신규 환경·실행기·테스트 AST와 launcher 문법 검사도 통과했다.

[native qualification 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/guard_qualification_v1/report.json)의 실제 결과는 다음과 같다.

| 조건 | 실제 controls / physics steps | 결과와 범위 |
|---|---:|---|
| 기존 실패 명령 B replay | 153 / 612 | 이전 152개 valid 전이의 실제 native motion·최종 목표·제출 effort 모두 exact. 기존611 실패를 통과. 전체 B 시간축 완료는 아님 |
| zero B | 245 / 980 | 전체 시간축 완료 |
| zero C | 251 / 1004 | 전체 시간축 완료 |
| zero D | 475 / 1900 | 전체 시간축 완료 |
| uniform random ±0.8 B/C/D 각각 | 68 / 274 | 모두 두 후보 실패로 fatal. 전체 시간축 미완료 |

random 실패 시 current COM 최대 잔차는 0.019114855m/s, previous COM은 0.018448380m/s로 두 후보 모두 기존 0.01m/s 기준을 넘었다. 실패한 controller effort는 제출되지 않았다. 세 random 조건은 같은 seed101과 같은 초기 물리·행동 구간을 공유하므로 서로 다른 세 탐색 분포의 검증 근거가 아니다. zero 시간축 완료는 압현·타현 후보 또는 음향 성공이 아니다.

## Warning과 감사 범위

1. [실행된 진단 script의 완료 predicate](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/guard_qualification_v1_sources/stability_adapter_2/fresh_music_v1/replay_music_guard_v1.py:94)는 replay 명령 전부와 prefix 전부를 대조했는지, 원래 실패를 통과했는지를 최종 pass 조건에 직접 연결하지 않았다. 이번 기록에서는 원자료의 controls153, compared_controls152, all_exact=true, physics612>611을 별도로 확인하여 이 replay 범위에 한해 보완했다. 향후 다른 replay 입력에 대한 일반 완료 판정으로 사용하지 않는다.
2. 진단 실행 동결 시점과 완료 predicate 편집이 겹쳐 검사 당시 working script의 SHA가 달라졌다. 실행 원본 snapshot SHA `2ef688294037852b04c4c473fbc19b8e08edbb3b0a09c87ec44ef83b94eb9f2a`는 inputs_before의 SHA와 일치하며, 변경본 SHA는 `16bef8ff6656e4d56045be4a0f5e020da9efe85326f8890a0f8d4c4aaf002d83`였다. 사전 pin된 입력 중 이 script만 달라졌음을 확인했다. 실행 종료 뒤 root는 변경본을 신규 replay_music_guard_v2.py로 보존하고 v1은 사전 snapshot 원문으로 복원했으며 [변경 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/guard_source_change_record.json)에 두 SHA를 남겼다. 실제 diff는 replay_complete 조건 3줄 추가와 completed 조건 1줄 수정으로 한정된다. 원자료의 inputs_unchanged=false와 all_cases_passed=false는 그대로 보존되며, 복원이나 신규 predicate를 실행 당시 판정으로 소급하지 않는다.

현재 코드에 추가 수정이 필요한 Critical은 없다. broad random qualification 실패 및 script 입력 변경이라는 두 제한은 실제 원자료와 함께 보존하고, 이후 검증/학습 성과를 이번 결과로 앞당겨 설명하지 않는다.
