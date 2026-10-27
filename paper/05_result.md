# Result

논문 제목: **From Audio to Full-Body Guitar Performance with a Freely Moving Instrument**

## 5.1 초기 자세와 손별 기술

현재 학습에 사용하는035/v14 기준은 Root 고정·하체 유한 제어·자유 기타 조건의 실용 초기 자세 후보다. 정지·반복 타현·왼손 해제·해제 상태 타현·넥 재접촉의 다섯 개별 시험을 통과했다. 이 결과를 모든 동작의 같은 실행 내 연속 완료나 범용 제어기의 완성으로 확대하지 않는다. 접촉 측정과 각 부위의 지지력 기여도도 구별한다. [초기 자세 근거](/home/ajou/yigyu/3/paper/initial_pose/current_v3/README.md)

같은 첫 음에 대한 자유 기타 손별 BC는 LH4/4·RH4/4의 품질 평가를 통과했다. 목표 접촉 후보·clean 압현·타현 준비와 복귀를 판정한 결과이며 실제 압력·음향은 아니다. 각 손이 단독으로 성공한 것이 동시 성공을 보장하지 않는다. [손별 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_local_skills_v1/README.md)

## 5.2 두 손의 동시 실행

| 실행 | 안전7초 완주 | LH품질 | RH품질 | 공동 성공 |
|---|---:|---:|---:|---:|
| 고정 두 BC 동시 실행 |1/1|1/1|0/1|0/1|
| 첫 PPO rollout, 업데이트 전 |2/2|2/2|0/2|0/2|
| 저장 PPO의 결정적 평가 |1/1|1/1|0/1|0/1|

고정 두 BC는7초420tick을 완료했고 금지API·속성 변경·물리 실패·cleanup 오류는 없었다. LH는 목표 발음 구간에서clean 압현을 유지했다. RH는 준비와 타현 후 복귀를 수행했으나accepted crossing이 목표4.12초보다2.35653초 늦었다. 다른 현의native-eligible crossing2개도 기록됐다. 따라서 원50/100ms 매칭과 협응 성공은 모두0/1이다. [고정 실행 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/fixed_experts_evaluation_v2/result.json)

같은 물리 장면에서는 손별 관측과 기타 상태가 함께 변하므로 단독 정책과 다른 동작이 나타날 수 있다. 그러나 특정 네트워크 설계나 접촉 부위가 실패의 원인이라고 확정하는 통제 실험은 수행하지 않았다.

## 5.3 공동 PPO와 저장 검증

두 환경의840전이를 모두 수집·로그·디스크 기록·PPO 반영에서 확인했고 제외 전이는0개다. 실제 업데이트1회와 체크포인트 저장을 완료했으며 양쪽 Actor·탐색 분산·Critic과optimizer 상태의 변경을 확인했다. 각worker의 물리 장면은 한 번 생성·종료했고 에피소드 경계에서 재사용했다. [최종 보고](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/ppo_smoke_v1/report.json) · [공동 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/ppo_smoke_v1/joint_report.json)

초기 Actor 학습률1e-5의 갱신은KL guard에서 재시도했고6.25e-7에서 수락됐다. 수락한analytic KL은0.0118585다. 이는 과도한 정책 변화를 제한하는 경로가 작동했다는 근거이며 학습률의 장기 최적성을 뜻하지 않는다.

저장 모델을 엄격하게 불러온 결정적 평가도 안전하게7초를 완료했다. 그러나 LH1/1·RH0/1·공동0/1이며 타현 오차는 약2.384초였다. 이번1회 업데이트 후 음악 성능 향상은 확인하지 못했다. 첫rollout의 두 에피소드는 업데이트 전 수집분이므로 학습 후 평가와 구분한다. [저장 모델 평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/ppo_evaluation_v1/result.json)

## 5.4 전곡 학습 결과

전곡 시간표는67음을 빠짐없이 포함하며 원note-on에 맞춰 두 재타현을 펼친다. 두 번째 방향은 원자료가 없어 묶음 방향을 상속한다. 500상태·독립Actor2개·중앙Critic, 연속 재무장·목표별clean 압현·일대일 타현·협응 원장을 구현하고 확인한CPU 검사40개가 통과했다.

전곡PPO는2환경에서4096전이를 모두 반영하여8업데이트를 완료했다. 제외 전이는0개다. 두 에피소드 모두32.8166667초의 전곡 구간을 안전하게 완료했고 물리 실패0, 장면 재사용 감사도 통과했다. [최종보고](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/training_v2/report.json)

학습 중 완료한 두 에피소드의 목표134개 가운데 왼손 유지 기준 충족은2개, 오른손 적시 타현은2개, 타현 순간의압현 협응은0개다. 전곡 음악 성공은0/2다. 안전 완주와 학습 경로는 확인했지만 음 전환과 협응이 부족하다. 이 결과는 학습 중 수집분이며 최종checkpoint의 별도 결정적 평가와 구분한다. [목표별 집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/training_v2/song_report.json)

## 5.5 해석과 한계

안전한 신체–기타 상호작용과 연주 사건의 정확한 시간적 결합은 별도 조건이다. 현재 결과는 초기 자세의 개별 검증과 손별 기술, 공동 학습 경로의 실행을 뒷받침하지만 공동 연주 숙련을 입증하지 못했다. 적시 협응과 음 전환을 해결해야 하며 장기 학습·다중seed·다곡·교란 비교가 남아 있다.

Root 자유 상태의 균형·보행,105축 전체 정책 학습, 사람 모션 유사성의 정량 평가, 실제 현 압력·진동·음향은 현재 결과의 범위가 아니다.
