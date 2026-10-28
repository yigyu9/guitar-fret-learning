# 소지121 새4시도 준비

root가 승인한 최소 재현 진단이다. 이 폴더만 소유하며 원 소스·grid·분석·기존 reference·teacher·봉인은 수정하지 않는다. GPU/native는 root만 실행한다. 이번 grid 실제 분석의 독립 PASS와 입력 SHA를 확인한 뒤에만 CPU prepare/최종 봉인한다.

- 원 순위121의 offset `[0,+5,0,0]`°를 새 finite reference로 기록한다. source actual 자세로 부르지 않는다. 원 `short_finger_reference.v2`/목표 ID/teacher23/2초 ramp/음시계/범위/PD/4rad/s/보상/엄지·B는 유지한다. 원 `read_reference`로 새 evidence와 목표를 검사한다.
- 원 prelearning `execute('pinky','reference',...)`를 그대로 재사용한다. 실행 중 해당 module의 `HERE` 및 `INPUTS` 객체만 새 입력 경로의 사본으로 scoped 교체하고 finally에 원 객체를 복원한다. 원 `_evaluate`, private cap0.25Nm, native105/4환경 verifier, 원90 collision pairs, 첫 시도4분모·실패·장면종료·입력 전후 검사를 유지한다. no-NN/no-checkpoint/no-training이다.
- 기존 출력/상위 symlink를 native import 전에 거부한다. 새 출력은 exclusive 생성 후 dev/inode 소유를 확인한다. stdlib gate를 native보다 먼저 실행하며, 이후 Isaac→Torch 순서를 유지한다. 실패는 원 보고서/오류를 보존하고 alias 복원 상태를 별도 기록한다.
- 음악 acceptance는 원4/4 규칙 그대로 추가 보고서에 기록한다. trace는 원 evaluator env0/60Hz뿐이며 다른3환경의 상세힘/각도나240Hz 하중 극값을 추정하지 않는다. 몸체 순힘은 접촉쌍·현 압력·모터 토크가 아니다. 손목/팔 feedback 변화가 함께 생기므로 손가락 단독 원인이나 자유 기타·정책학습 성과로 확대하지 않는다.
- 기존 소지 zero0/4는 동일 teacher/settings/noNN의 별도 원 실행을 출처 표시하여 재사용할 수 있다. 새 reference는 zero 행동 경로에서 사용되지 않는다. 이번 실행에는 새 zero/random 장면을 추가하지 않는다.

## 검증 순서

1. CPU: 기존 cap/evaluator 검사 재사용, 선택121/새 reference·원settings exact, 기존 출력 절대보존, scoped execute 실패와 constructor 검증 실패+close 이중오류에서 원 오류·복원 보존.
2. actual 분석 PASS 뒤 CPU prepare→fresh-process stdlib gate→독립 준비 검수→현재 입력 SHA/봉인 인계. 기존 결과 파일을 덮어쓰지 않는다.
3. root만 새 `runs/pinky/` 한 장면을 실행한다. 실제 native105/4환경/90pairs·4원장·장면종료·alias복원·입력 전후 검산 후 후속 actual 검수한다.

```bash
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/low_effort_pinky_oracle_v1/reproduction_v1/probe.py --prepare
# root 인계 뒤 한 GPU에서만:
/home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/low_effort_pinky_oracle_v1/reproduction_v1/probe.py --execute
```
