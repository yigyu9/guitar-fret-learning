# 기존 가중치 없이 시작한 공동 정책 — 첫 실행

2026-10-14 사용자 지시에 따라 기존 Fret·Strike·잔차 정책을 사용하지 않는 새 학습으로 전환했다. 기존 체크포인트는 비교와 재현을 위해 보존했다. 현재 과제는 기타를 지지하며 작은 손 이동을 수행하는 Stage A다. 압현·타현·곡 연주 학습은 이 실행에 포함하지 않았다.

## 실행 상태

| 실행 | 내용 | 확인된 상태 |
|---|---|---|
| baseline_v1 | 환경v1 초기 구성 | 질량·관성 비교 참조 오류로0스텝 중단. 소스와 실패 기록 보존 |
| baseline_v2 |0 행동의5초 기준 실행, seed9001 |300제어 스텝 완료. 최대 기타 actor-root 이동15.20mm·회전4.408° |
| smoke_v2 | 새 난수 초기화,512스텝·2갱신 | 가중치 최대 변화0.00210309. 이전 정책 미사용, 체크포인트 저장 |
| smoke_eval_v2 |2갱신 체크포인트, seed9001 영상 평가 |5초 완료. 학습/평가의 환경 ABI와 체크포인트 재로딩 확인 |
| pilot64_v3 | 새 난수 초기화, seed101,256스텝×64갱신 예산 |23갱신·6067스텝에서 Jacobian 속도 검증 불일치로 중단. 정규 저장 최신은20갱신 |
| heldout_baseline_v3 | seed9002의 동일 목표 기준 실행 |5초 완료. 최종 체크포인트 비교용으로 보존 |
| pilot64_v4 | 시점을 맞춘 속도 검증, 같은 난수 초기화 |23갱신·6067스텝 후 다음 physics269에서 재중단.23갱신 fault checkpoint 보존 |
| heldout_baseline_v4 | 환경v4, seed9002의 기준 실행 |5초 native 영상 완료 |
| pilot64_v5 | 목표를20%씩 변경하는 환경v5, 새 난수 초기화 |27갱신·6951개 유효 전이 후 검증 오류로 중단.27갱신 fault checkpoint 보존 |
| recovery64_v1 |27갱신 새 정책을 이어 제한된 재수집 | 37회 추가 갱신으로 누적64회 완료. 새 오류3구간·328전이 제외,9472전이 학습 |
| heldout_eval64_recovery_v1 |64갱신 정책, seed9002의 단회 평가 |5초 완료. 동작 구간 palm RMS6.772mm, 최대 기타 이동14.34mm·회전4.171° |
| heldout_eval27_v5 |27갱신 정책, seed9002 |5초 완료. 동작 구간 palm RMS10.566mm, 최대 기타 이동14.10mm·회전4.041° |
| heldout_baseline_v5 | 환경v5, seed9002 기준 실행 | 5초 완료. 동작 구간 palm RMS20.438mm |

[첫 학습 지표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/pilot64_v3/metrics.jsonl) · [첫 학습 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/pilot64_v3.launch.log) · [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/review_v1.md)

pilot64_v3은64갱신을 완료하지 않았다. 마지막 상태의 관절속도는 유한하고 최대2.35rad/s였으며, 다음 적분 전에 검증에서 멈췄다. 실패 시 실제 Jacobian 불일치 수치가 충분히 저장되지 않아 원인을 재현 검사 중이다. 이미 갱신한23회, 실제 저장된20회, 갱신에 쓰이지 않은179개 수집 전이를 구분한다. 검증 오류를 정상 연주 실패로 해석하거나 검사 기준을 단순 완화하지 않는다.

후속 diagnostic_v2~v4에서67개 행동을 재생하여 중단 상태를 정확히 재현했다. 모든65개 body에 대해 현재 Jacobian과 native 속도의 최대 차이는0.01402m/s였고 직전 물리 스텝의 Jacobian을 사용하면0.001217m/s였다. 환경v4는 실제 힘 계산을 바꾸지 않고 검증 시점을 맞췄다. diagnostic_v5의 이전 실패 상태·정지5초·무작위 행동5초 두 회를 통과했으며,0.01m/s 한도와 오류 시 중단을 유지했다. 검증 오류를 학습 보상이나 정상 종료 전이로 바꾸는 후보는 채택하지 않았다.

다만 pilot64_v4의 다음 적분269에서는 현재/직전 Jacobian 모두 잔차가0.01m/s를 넘었다. diagnostic_v6에서68개 명령으로 이 상태도 정확히 재현했다. 왼손 접촉과 함께 팔에서 손끝으로 잔차가 커졌으나, 정확한 solver 내부 원인은 확정하지 못했다. 이 차이를 곧바로 물리 폭주나 Jacobian 오염으로 해석하지 않는다. v4의 시점 보정만으로 장기 학습 문제가 해결됐다고 주장하지 않는다. 후속으로 행동 목표의 변화 속도를 줄이는 별도 제어 조건을 검증한다.

pilot64_v4의 보수적 입력 목록에 포함된 다른 분석용 Python 파일1개가 외부에서 수정되었다. 실제 학습·물리 모듈의 변경과 구분하며, 기존 보고서의 `changed_inputs`를 수정하지 않는다. 다른 담당자의 파일을 되돌리지 않았다.

[현재 재실행 지표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/pilot64_v5/metrics.jsonl) · [현재 재실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/pilot64_v5.launch.log)

## 해석 범위

54차원 정책은 support15/fret33/strike6을 함께 출력하며 보상·비용 Critic 두 개로 학습한다. 목표각을 실제 native 제어에 적용하고, 남은27개 목표는 준비값을 유지한다. 이전 모델 가중치를 불러오지 않는다. 준비 자세, PD·중력 보상, 오른 근위부의 제한된 지지 피드백은 사용한다. 루트·하체는 고정이고 기타는 자유 상태이며 스트랩은 OFF다.

목표 중심은 정착 후가 아닌 t0 palm 위치다. 기준 실행의2초 손 위치 RMS 오차가 약20mm이므로 현재 과제는 정착 드리프트 회복을 포함한다.3mm 목표 이동을 정확히 추적했다는 결과로 해석하지 않는다. 비용 계수1의 고정 패널티를 사용하며, 비용 한도·안정성 보장을 제공하지 않는다. 비용이 발생하지 않은 시험은 위험 상태의 대처를 학습했다는 증거가 아니다.

신규 코드와 재실행 방법은 [학습 설명](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/README.md), 단계별 상태는 [실행 계획](/home/ajou/yigyu/3/docs/plans/fresh_guitar_learning_20261014.md)에 기록했다. 기존 논문 원고의 실험 결과는 이번 새 구조의 성과로 대체하지 않았다.

## 제한된 후속 학습 계획

pilot64_v5에서 검증 오류 직전까지 완료한27갱신을 보존했다. 별도 목표9002의5초 평가는 정상 완료했다. recovery64_v1은 이 새 정책만 이어받고 환경v5를 유지한다. env.step의 JacobianConsistencyError만 재수집 대상으로 삼고, 해당 미갱신 rollout 전체를 버린 뒤 고유 seed의 새 에피소드에서 시작한다. 오류를 보상·종료 전이로 넣지 않는다. 원래 오류1회를 포함해 총8회에 도달하면 중단하며, 새 시도는 최대11264개 제어 명령이다.27→64의37회 추가 갱신이 예산이다. 모든 거절 구간·진단·체크포인트를 보존한다. 이 방식은 수집 분포에 선택 편향이 있으므로 일반적인 무편향 PPO나 물리 안전성의 증거로 설명하지 않는다. 평가에는 이 재시도를 적용하지 않는다.

## 최종 결과 — 2026-10-15

기존 정책 가중치를 사용하지 않은 Stage A 파일럿을 누적64갱신까지 완료했다. 첫27갱신의6912개와 후속37갱신의9472개를 합쳐16384개 전이를 학습에 사용했다. 원래 실행의 검증 오류1구간39개와 후속3구간328개, 총4구간367개 전이는 제외해 보존했다. 후속 실행은9803개 명령(정상9800개·오류3개), 미처리 전이0개로 회계가 일치한다. 무오류 연속 학습의 결과로 표시하지 않는다.

| seed9002, 동작 구간2~5초 |0 행동 기준 | 새64갱신 정책 |
|---|---:|---:|
| 양손 palm 위치 RMS 오차 |20.438mm |6.772mm |
| 전체5초 최대 기타 actor-root 이동 |15.201mm |14.343mm |
| 전체5초 최대 기타 회전 |4.408° |4.171° |

같은 목표와 물리 조건에서 최종 정책을 재시도 없이 한 번 평가했다. 기준·평가 모두300제어 스텝을 완료했고, 비용은0이었다. 비용이 발생하지 않았으므로 비용 Critic이 위험 대응을 배웠다는 근거가 아니다. 초기 정착 드리프트의 회복을 포함하는 한 목표의 결과이며 일반화·실제 연주·인간 유사성·안전성의 입증은 아니다. 루트·하체는 고정이다.

- [최종 체크포인트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/recovery64_v1/checkpoint_0064.pt)
- [최종 학습 회계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/recovery64_v1/report.json)
- [원자료 비교·보존 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/recovery_v1_analysis.json)

전신 평가 영상(준비2초 포함 전체5초):

![새64갱신 정책 전신 평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/heldout_eval64_recovery_v1/whole_body.mp4)

![새64갱신 정책 양손 평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/heldout_eval64_recovery_v1/hands.mp4)

[독립 복구 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/review_recovery_v1.md) · [최종 입력·평가 파일 일치 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/final_verification.json)

후속 연구 과제: 속도/Jacobian 검증 잔차의 근본 원인 규명, 다수 목표·학습 seed 검증, 실제 압현·타현·음악 시간 조건 추가. 복구 수집기v1은 이번 원27갱신 체크포인트부터의 단일 재개만 검수했으며 범용 재개 도구로 사용하지 않는다.
