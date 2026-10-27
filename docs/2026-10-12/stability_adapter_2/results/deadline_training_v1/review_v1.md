# 정오 마감 시험 학습 독립 검수 v1

요약 판정: **문제없음 — 현재 명시된 시험 학습 범위에서 추가 실행 차단 오류를 발견하지 않았다.** 아래 시간 제한·중단 저장의 한계는 별도로 남긴다. 정식 reward v4/v5 인증, 안정성·연주 성공, 장기 학습 완료를 승인하는 검수가 아니다.

검수자는 소스와 저장된 CPU/native 결과를 읽고 SHA를 대조했다. 직접 native 실행·정책 추론·학습을 추가하지 않았으며, 이 검수 파일 외에는 생성하거나 수정하지 않았다. [추가 지침](/home/ajou/yigyu/3/stability_adapter_2/AGENTS.md:1), [최신 메인 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1), [이번 동결 계획](/home/ajou/yigyu/3/stability_adapter_2/DEADLINE_TRAINING_PILOT_V1.md:1)을 기준으로 검토했다.

## Critical — 발견 후 해결된 항목

- [runner v1:82](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v1.py:82)의 `dict | dict`는 실제 Python 3.8에서 실행되지 않는다. 구문 검사만으로 닫히지 않는 오류를 실행 전에 전달했고, 실패 로그·v1을 보존한 [runner v2:82](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v2.py:82)의 `dict(vars(args), ...)`로 해결했다. v2 실제 실행은 성공했다. [최종 runner v3:109](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v3.py:109)도 같은 수정이다.
- 검토 당시 v3 초안의 cutoff checkpoint 저장은 예외 처리 밖에 있어 저장 실패에도 최종 보고서의 `failure`가 비어 있을 수 있었다. [v3:221](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v3.py:221)에서 저장과 평가를 같은 `try` 안으로 옮겨 실패 상태를 기록하도록 수정했다. 수정 전 초안은 [보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/runner_checks_v3/reviewed_draft_before_correction.py:1)으로 남았다.

최종 v3 소스 SHA256은 `d5d13dcf8f3cd07033c19fe180d4c0e8417747ca59e95ae554d6603108c27357`이며 [소비 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/runner_checks_v3/attempt.json:1)·보존본과 일치한다. 미해결 Critical은 없다.

## Warning — 보장 범위와 후속 주의

- [runner v3:64](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v3.py:64), [v3:184](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v3.py:184): cutoff는 다음 제어/reset 호출 및 optimizer 진입을 차단한다. 이미 진행 중인 native reset·step·CUDA update를 선점하지는 않는다. **11:40을 엄격한 순간 중단 보장으로 설명하지 말 것.** 미완료 rollout은 반환되지 않아 optimizer에 사용되지 않는다.
- [runner v3:125](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v3.py:125): 평가에 최대600초 대기와 TERM15초/KILL5초를 두었다. 그러나 KILL 뒤 대기마저 실패하면 `finally`에서 추가 종료 대기를 시도하므로 20초 reserve가 절대 상한은 아니다. 평가 timeout은 실패로 기록하며, 정오 전 완성 영상의 무조건 보장으로 설명하지 말 것. [scheduler CPU3개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/runner_checks_v3/tests.log:1)는 제어 gate·준비성 위임 검사이고 subprocess/신호 처리 전체의 실제 통합 시험은 아니다.
- [native:335](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v1.py:335): `_finished=True`와 영상 encode가 controls/trace/music JSON 저장보다 먼저 실행된다. final encode 도중 SIGTERM이 들어오면 `close()`가 다시 저장하지 못할 수 있다. **이미 저장한 PNG와 부모 실패 로그 보존은 가능하지만, 중단된 episode의 완성 MP4·원시 JSON까지 모두 보존된다는 주장은 피할 것.** 현재 정상 완료한 두 평가의 파일과는 구분한다.
- [native:293](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v1.py:293): 원본 Fret/Strike done은 진단으로만 집계하고 고정 곡 horizon을 진행한다. 이번 계약은 비유한 상태·고정 하체 변화·금지 API·관측된 `abs(qdot)>50rad/s` 등을 실행 오류로 중단하는 시험이다. source 손목 실패 무시를 일반 물리 안전 인증으로 해석하지 말 것. dropout·distal pad·fatal 할인 정산·정확한 SO(3) 외부 거리 등 미구현 항은 [시험 profile](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v1.py:15)에 공개되어 있으며 정식 학습 gate는 닫혀 있다.

## 정확성 대조

- [native:190](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v1.py:190): 준비2초에는 검증된 preload, PLAY에는 현재 공통 score frame의 실제 동결 Fret/Strike 요청을 명목 목표로 사용한다. source는 tensor-only 요청·평가이며 하나의 상체81 owner만 목표를 제출하고 물리를 진행한다. source30+30 및 나머지21과 학습81의 역할이 구분된다. 실제 최종 목표의 역변환 history 오차는 기록하며 source 동등성·교사 유효성을 인증하지 않는다.
- [native:226](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v1.py:226), [runner v3:47](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v3.py:47): 실제739 관측에 현재 명목81을 더한820 ABI이며 행동81이 명시된다. 평가 checkpoint 파일 자체는 `source_sha256`에서 제외해 resume 자기참조 mismatch를 막는다. 기존 baseline checkpoint/계약 SHA는 별도 ABI에 남는다. Isaac Gym 진입을 Torch보다 먼저 한다.
- [GAE:44](/home/ajou/yigyu/3/stability_adapter_2/joint_ppo_v1.py:44), [PPO:76](/home/ajou/yigyu/3/stability_adapter_2/joint_ppo_v1.py:76): 종료는 bootstrap을 끄고 절단은 bootstrap을 유지하면서 두 경우 모두 episode 간 GAE carry를 끊는다. 실제 transition의 final observation을 사용한다. log-prob는 표본 latent/action 기준이며 실행 PD 목표 역변환을 넣지 않는다. collection·likelihood 재평가 동안 RMS를 동결하고 update 뒤에만 바꾼다. 미종료 collection은 관측을 이어간다.
- [checkpoint:27](/home/ajou/yigyu/3/stability_adapter_2/deadline_ppo_v1.py:27): model/Adam/RMS·CPU/CUDA/Python/NumPy RNG와 ABI를 저장하며 atomic hardlink로 기존 checkpoint 덮어쓰기를 거절한다. ABI·config·정확 RNG 복원의 device 조건을 state 복원 전에 확인한다. 복원은 새 물리 episode이며 중간 episode 재현을 주장하지 않는다.
- [회전 검사 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/rotation_checks/attempt_v3_rl38/report.json:1):8검사 통과, gimbal/경계와 두 Euler branch를 다루며 외부 거리는 conservative lower/feasible upper proxy다. 정확 외부 최단 거리·production gate 완료를 주장하지 않는다. 실패 v1/v2도 보존되었다.

## 실제 검증 근거

[native 계약 CPU7개 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/native_checks/pure_tests_v1.log:1), [PPO CPU 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/ppo_checks_v1/cpu.log:1), [PPO CUDA 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/ppo_checks_v1/cuda.log:1), 회전8검사 및 scheduler3검사 기록을 읽었다. PPO CPU/CUDA 결과는 실제 Actor/Critic 갱신·RNG 복원·ABI 거절·불변 저장을 포함한다. 이 CPU 검사들이 native 전체 안전이나 음악적 성공을 증명하는 것은 아니다.

[smoke v2 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/report.json:1)와 두 native raw controls/trace/events를 대조했다. 실제 CUDA PPO update1/256 transitions·optimizer step1이 기록되었다. initial/update 평가 각각982 control·3928 physics·16.366667초이며 controls982행/trace983행이다. Fret/Strike 각각862회 실제 추론, 동결 가중치 불변·금지 호출0,42 event 정산·공동 성공0·accepted crossing0이다. 고정 곡 horizon 평가와 학습용256-transition 부분 episode를 구분한다.

초기 return−397.140450, update1 return−397.744697로, 한 회 갱신을 품질 개선이나 연주 성공이라고 해석하지 않는다. 두 평가 모두 RMS 변경 없이 deterministic 실행했다. 네 MP4의 기록 SHA를 실제 파일과 대조했고 각각492프레임/30fps/16.4초다. 물리16.366667초와 인코딩 길이는 구분된다. [한국어 결과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/artifacts_smoke_v2/README.md:1)의 수치와 제한 범위도 이 원자료와 일치한다.

독립 SHA 재계산에서 smoke 학습 attempt1119개, initial/update 평가 attempt각1120개 입력의 변경·누락은0이었다. 주요 source 소비 SHA도 현재 파일과 일치했다. 이것은 기록된 입력집합의 보존 확인이며 프로젝트 전체 최종 보존 감사와 이후 장기 실행 마감은 root 책임이다. v3의 장기 native 실행·30분 반복 스케줄·최종 마감 결과는 이 검수 시점에 아직 검증하지 않았다.
