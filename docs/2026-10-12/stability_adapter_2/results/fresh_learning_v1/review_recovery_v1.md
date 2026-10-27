# 제한된 rollout 복구 collector 검수

2026-10-15 change-reviewer 검수. 코드·기존 실행 결과는 수정하지 않고 이 검수 기록만 작성했다. 대상은 [run_recovery_v1.py](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/run_recovery_v1.py), [launcher](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/launch_recovery_v1.sh), [CPU 테스트](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/test_recovery_v1.py), [최종 분석기](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/audit_recovery_v1.py)다.

## 요약 판정

**지정된 원 v5 fault_checkpoint0027에서 시작한 collector 구현·최종 회계는 문제없음. Critical 및 이번 실행의 미해결 Warning 없음.** 원27갱신에 accepted37갱신을 더하여 목표64에 도달한 기록과 단일 paired 평가를 확인했다. 이를 일반적 정책 성능·안전성의 합격 판정으로 확대하지 않는다. 아래 감사 Warning 두 항목은 이번 실행의 별도 봉인 검사로 보완되었다.

이 실행은 [v5의 실패 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/pilot64_v5/report.json)를 보존하고 시작하는 별도 collector 조건이다. 원 실행은 27갱신·6951개 정상 control 후 중단했고, 6912개는 완료 갱신에 사용되었으며39개는 미갱신 수집이다. 검증 오류가 행동·상태에 의존하므로 통과한 rollout만 사용하는 선택 편향이 남는다. 이를 원래 환경의 무편향 on-policy PPO, 정책 안전성 학습, 음악 수행 성공으로 설명하지 않는다.

## 구현 확인

- 복구 catch는 env.step의 JacobianConsistencyError에 한정된다. policy 추론·reset·로그/체크포인트 보존 오류 및 다른 예외는 복구하지 않는다.
- 불확실한 step은 정상 전이를 반환하지 않으며, 오류가 발생한 현재 rollout 전체는 PPO에 전달하지 않는다. optimizer 호출은 완성된 accepted buffer에만 있다. 오류 상태·시도 명령·부분 물리 진행량·모델·Adam·RNG를 보존하고, native 유한성·속도50rad/s 이내·고정 하체·금지 API 검사까지 통과해야 새 seed의 fresh episode로 넘어간다. guard 한도·물리·v5 필터는 변경하지 않았다.
- 목표64는 원27에서 추가37갱신, 새 accepted transition9472개를 뜻한다. prior rejection1을 포함한 전체 한도8은 새 fault7개째에서 기록 후 중단하므로, 성공적인 재수집으로 넘어가는 복구는 최대6회다. 별도의 attempted control 상한11264가 있다.
- command·rollout·rejection 번호는 서로 분리되어 단조 증가한다. 같은 update에서 오류가 반복되어도 rejection checkpoint 파일명이 충돌하지 않는다. accepted·discarded·pending·failed attempt를 구분한다.
- 가중치 로딩 전에 자체 정책/PPO schema, 환경v5 ABI·관측 구간·task·원 seed101을 대조하고 모델 유한성을 검사한다. 출처 체크포인트의 SHA가 payload와 metadata 전체를 고정한다. collector가 직접 읽지 않는 원 report는 별도 최종 감사 입력으로 고정하면 된다. 중간 물리 상태의 연속 재개를 지원한다는 뜻은 아니다.

## 검증

- 기존 복구 테스트6개를 직접 재실행하여 통과했다. 전체 rollout 폐기, reset 전 final observation bootstrap, 다른 오류의 fatal 처리, 거부 한도, 보존 실패 중단, policy에서 발생한 typed error의 비복구를 포함한다.
- 추가 메모리 기반 경계 테스트3개도 통과했다. prior1에서 실제 새 fault7개가 발생하면 전체8에서 중단하며 추가 reset/PPO가 없다. reset 내부의 같은 typed error는 복구되지 않는다. attempted control 상한에 도달하면 추가 native step과 PPO가 실행되지 않는다. 합계9개 테스트이며, 추가 테스트는 검수용 프로세스에서만 실행하고 코드 파일을 수정하지 않았다.
- Python AST와 launcher shell 문법 검사가 통과했다.
- 진행 중 recovery64_v1의 처음28개 완료 rollout 원장을 대조했다. accepted27개는 각256개, 합계6912개의 전이를 포함하고 update28~54가 연속이었다. 해당 접두 구간의 rollout·command ID가 고유/연속이고, rejected rollout의 폐기 수와 전이 수가 일치했다. 이 접두 구간 검사를 전체 실행 완료로 해석하지 않는다.
- 실제 rejection_01과 rejection_02에서 각각 정상 전이54개/215개와 실패 시도1개가 분리되었고 ppo_updated=false였다. 오류 상태·명령·rejection checkpoint를 보존했으며 native 유한성·관절속도·고정 하체·API 검사 모두 true였다. 이후 accepted rollout 수집이 계속되었다. 검수 시 collector 입력 SHA1304개를 재대조하여 불일치0개를 확인했다.

## 감사 Warning과 이번 실행의 보완 확인

**보완 확인 — audit_recovery_v1.py:29,60:** 분석기는 checkpoint의 update 수를 report와 비교하지만 평가가 바로 그 파일을 읽었는지까지 증명하지 않는다. 이번 최종 평가 report의 loaded_checkpoint와 attempt.arguments.checkpoint가 recovery의 실제 checkpoint0064 절대 경로와 같고, 해당 입력 SHA가 실제 파일 SHA와 같음을 직접 확인했다. 최종 봉인에도 같은 검사가 포함되었다.

**보완 확인 — audit_recovery_v1.py:71:** checks에 false가 있어도 분석기 종료 코드는0이다. 이번에는 recovery_v1_analysis.json의17개 boolean이 모두 true임을 직접 확인했고, 최종 봉인에서도 개별 검사값을 확인했다. 종료 코드만으로 합격 판정하지 않았다. 이후 다른 실행에서 fault/attempt 예산으로 끝나면 미완료를 그대로 보고해야 하며, 원 report를 성공으로 덮어쓰면 안 된다.

원 report·config·metrics·transition·checkpoint 및 분석기가 실제 읽는 미디어·소스 사본 등을 감사 입력 SHA에 포함하고 전후 불변을 확인해야 한다. 외부 작업자의 무관한 변경을 되돌리거나 엄격한 changed_inputs 판정을 숨기지 않는다.

추가 범위 제한: run_recovery_v1.py:193–198의 source_control_accounting은 이번 원 v5 fault27의 누적 control 번호에서 올바르게 계산된다. 이 collector가 만든 후속 checkpoint의 control 번호는 프로세스 내 번호이므로, 이를 다시 source로 사용할 경우 같은 식을 그대로 적용하면 잘못된 누적/음수 폐기 수가 나올 수 있다. 다른 재개 경로는 본 검수의 승인 범위에 포함하지 않는다.

## 완료 결과와 최종 봉인

[recovery64_v1 최종 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/recovery64_v1/report.json)의 원장·전이·명령을 직접 대조했다. 완료 update는 원27+신규37=64, 새 PPO accepted transition은9472개다. 새 시도9803개 중 정상 control9800개는 accepted9472+폐기328+pending0으로 정확히 분할된다. 나머지3개는 정상 전이를 반환하지 않은 오류 시도다. 폐기328은 rejected rollout의54+215+59개 전이이며 optimizer에 들어가지 않았다. 새 fault3개와 기존 v5 fault1개를 합한4개는 전체 한도8 이내이고, 시도9803은 상한11264 이내다. command ID·accepted update28~64가 연속이며 모든 accepted rollout이256개 전이를 갖는다.

새 오류 세 건의 부분 진행은 각각3/3/0 physics step으로 보존되었다. 최종 예외·금지 API·입력 변경은 없었다. 원본 fault27과 최종 checkpoint64의 모델을 직접 비교하여 공유 인코더, 세 Actor head, 두 Critic이 이번 후속 구간에서도 모두 변경되었음을 확인했다. 이는 optimizer 실행의 증거이며 비용 합계0에서 안전성 비용 학습의 효과가 검증되었다는 뜻은 아니다.

[단일 held-out 평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/heldout_eval64_recovery_v1/report.json)는 seed9002에서300 control/5초를 완료했다. 기준 실행과 환경 ABI·초기 native 상태·목표가 정확히 같았다. ACTIVE 손바닥 RMS 오차는 기준20.437616→정책6.772075mm, 최대 기타 actor-root 이동은15.200773→14.342907mm, 최대 초기 회전은4.408002→4.171406°였고 두 비용 합계는0이었다. 이는 이 한 조건의 관측값이며 3mm 추종 성공·다중 seed 일반화·압현·타현·음악 성공의 증거가 아니다. 전신/손 영상은 각각151프레임으로 시작부터5초까지 포함한다.

[최종 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/final_verification.json)의7개 검사와 [분석 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/recovery_v1_analysis.json)의17개 검사가 모두 true임을 확인했다. 봉인은 감사 입력4548개 전후 불변, 실제 평가 체크포인트 경로·SHA, 유지27개 목표·노력 제어기 입력·유한성, 영상/프레임 hash를 별도 확인한다. 원 v3/v4/v5 실패 report와 폐기 자료는 보존되었으며 무오류64갱신 실행으로 바꾸어 설명하지 않는다.

## 검수 시 SHA256

| 파일 | SHA256 |
|---|---|
| run_recovery_v1.py | e14e7dd5b43e52944591bd4a5d3aceb844cdd8679daa462875abfbb59775e468 |
| launch_recovery_v1.sh | 310cc38e2a7d16f936123c17f1c5b58410a2fdc896731470885d44970c39abb6 |
| test_recovery_v1.py | d461d02201f333da308c6a386147961575a876384b7045b2495c5ba0806881b3 |
| audit_recovery_v1.py | c12ba7b094cc42493f09cbe5d385462b9e8bcc219a4ad9190ae489e7e1e73dd5 |
