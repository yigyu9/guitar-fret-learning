# 손별 타이밍 PPO 학습과 실제 결과

학습 수집·PPO 업데이트·체크포인트·시뮬레이터 재사용은 정상 작동했다. 성공 궤적으로 초기화한 정책에서 출발해 기존 성공을 유지했고, 오른손 타현 시각은 소폭 개선됐다. 새 동작을 처음부터 발견하거나 곡 연주를 완성한 결과는 아니다.

## 수행한 학습

| 단계 | 시간창 | 손별 업데이트 | 손별 전이 | 왼손 목표 성공 | 오른손 목표 성공 | 물리 실패 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| stage0 | ±1.5초 | 24 | 14,400 | 46/48 | 48/48 | 0 |
| stage1 | ±0.5초 | 12 | 7,200 | 24/24 | 24/24 | 0 |

합계는 손별36회 업데이트·21,600전이, 양손 총43,200전이·144개 학습 에피소드다. 두 손은 별도로 학습했다. 학습 에피소드는 탐색 잡음이 있는 정책의 결과이며 아래 결정적 평가와 구분한다. stage0 왼손의 두 실패는 기타 이탈이 아니라 접촉 목표 실패였다.

각 실행은 독립 환경2개, horizon300, medium 모델, 입력536·출력39, seed7을 사용했다. native 정착2초 뒤 정책이 움직일 수 있는 준비1초를 두며 전체 정책 구간은5초다. 목표는 `05_BN2-131-B_solo`의 첫 단음(물리2번 줄·7프렛·약지·down)이다. Root고정·하체 유한 제어·105/97/8 구분·자유 기타·중력ON·스트랩OFF·원래 물성/충돌/의자/제어/안전 기준을 유지했다. 가슴 접촉 지속이나 삼중 접촉률은 성공의 필수조건으로 요구하지 않았다.

stage0 최종 평가가 계획한 기준을 통과한 뒤 stage1 계약으로 Actor만 이전했다. 새 단계의 Critic·optimizer·counter는 초기화했으며 기존 학습을 strict resume로 이어 붙이지 않았다. stage1 이전 후 실제2회 평가를 통과하고 추가 학습했다. 재BC 초기화나 실행 중 보상·소스 변경은 없었다.

## 탐색을 끈 실제 평가

각 행은 손별 동일 준비 시작에서2회 반복한 결과다. 왼손 유지율은 원래 음의 onset~end 구간에서 지정 손가락·현·프렛의 접촉 후보가 유효했던 비율이다. 오른손 오차는 지정 줄·방향의 **최초 실제 기하 통과**와 원래 onset의 차이며, 나중 통과 중 가장 좋은 값을 골라 대체하지 않았다.

| 정책 | 손별 단계 성공 | 왼손 음 구간 유지율 | 오른손 최초 통과 오차 | 추가 통과 |
| --- | --- | --- | ---: | --- |
| 초기 BC | 각각2/2 | 두 실행100% | +19.449ms | down1·up1 |
| stage0 12회 | 각각2/2 | 두 실행100% | +19.223ms | down1·up1 |
| stage0 24회 | 각각2/2 | 두 실행100% | +17.680ms | down1·up1 |
| stage1 이전 직후 | 각각2/2 | 두 실행100% | +15.712ms | down1·up1 |
| stage1 12회 | 각각2/2 | 두 실행100% | +12.286ms | down1·up1 |

stage0 안에서 오른손 오차는 약1.769ms, stage1 안에서는 약3.426ms 감소했다. stage0 최종에서 stage1 이전 직후의 변화는 **단계 입력 변경 효과**이므로 추가 PPO 성과에 포함하지 않는다. 같은 준비 조건의 반복이므로 작은 차이를 일반화 성능이나 통계적 우위로 확대하지 않는다.

최종 stage1의240Hz 원자료에서 기타 최대 이동은 왼손5.806/5.758mm, 오른손0.243mm였다. 발 최대 이동은 왼손3.762/3.643mm, 오른손0.0031mm였다. 주요 부위 중 한 곳 이상의 지지 접촉과 양발 접촉은 유지됐으며 물리 실패가 없었다. 접촉 부위별 분담은 상세 JSON에 남겼다. 이 최대값은 학습 로그의60Hz 끝점 대신 평가의 매 실행1,200개240Hz 표본에서 계산했다.

## 로그가 말해주는 것

1. **쉬운 단음 목표는 초기부터 포화돼 있었다.** 성공률100%가 새 학습의 성과를 모두 설명하지 않는다. 왼손은 이미 음 구간 유지율100%였고, PPO 뒤에도 유지했다. 오른손 타이밍은 조금 좋아졌지만 추가 down/up는 사라지지 않았다.
2. **왼손 보상 상승과 시간 정밀성은 다르다.** 학습 에피소드별 유지 보상 중 원래 음 구간 밖의 비율은 stage0 평균91.16%, stage1 평균82.83%였다. 현재 보상은 확장 시간창 안의 긴 접촉에 유리하다. `releases`는 측정 이력이며 명시적인 해제 보상이 아니다. 과제상 필요한 해제·다음 프렛 전환은 별도로 검증해야 한다.
3. **정책 업데이트가 민감하다.** 설정 Actor 학습률은1e-5였지만 KL 제한이 재시도하면서 실제 학습률을 낮췄다. stage0 왼손은6.25e-7, 오른손도 후반6.25e-7이었다. stage1 왼손은6.25e-7, 오른손은2.5e-6였다. 허용된 KL과 처음 시도한 KL을 그래프에 따로 표시했다. 로그만으로 네트워크 용량 부족을 결론 내릴 근거는 없다.
4. **실행 시간은 수집이 대부분이다.** 수집+PPO 업데이트 시간 중 약99.9%가 수집 루프였다. 수집에는 시뮬레이션·정책 추론·프로세스 통신이 포함되므로 물리 계산만의 프로파일은 아니다. 동시에 실행한 양손의 시간을 더해 실제 경과시간으로 설명하지 않는다.

이번 결과에서 안정성 비용 때문에 목표 수행이 전반적으로 막힌 증거는 확인되지 않았다. 동일 단음을 더 오래 반복하거나 네트워크를 먼저 키우기보다, 남은 엄격한 시간창을 실제 평가하고 통과한 목표는 다음 단계로 옮기는 편이 타당하다. 이후에는 서로 다른 프렛/손가락·다음 음 전환·필요한 해제·휴지기 추가 타현 억제를 평가해야 한다. 양손 결합은 그 다음 별도 안전 검증 대상이다. 이 제안은 이번에 추가 구현하거나 검증한 결과가 아니다.

원래 contact-conditioned 음악50/100ms 성공은 두 손의 조건을 함께 요구하므로 이번 손별 평가에서는0이다. 오른손 단독의12.286ms 기하 오차와 이를 혼동하지 않는다. 접촉 후보는 실제 현 압력·진동·음향을 인증하지 않는다. 서로 다른 시작 자세·여러 seed·여러 음·전곡·Root 자유 균형·양손 동시 연주는 이번 검증 범위에 포함하지 않는다.

## 로그·모델·분석 경로

- [stage0 최종 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage0_final_analysis_v1.md), [전체 수치 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage0_final_analysis_v1.json)
- [stage1 최종 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage1_final_summary_v1.md), [수치·원자료 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage1_final_analysis_v1.json), [수집/업데이트 시간](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/collection_update_walltime_v1.md)
- [모델 경로·단계별 counter·SHA 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/models_v1.json). `stage1`의 `final.pt` counter는12이며 Actor 계보상 누적36회와 구분한다.
- 최종 모델: [왼손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/left_stage1_v1/final.pt), [오른손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/right_stage1_v1/final.pt)
- 학습 폴더는 `left_stage0_v1`, `right_stage0_v1`, `left_stage1_v1`, `right_stage1_v1`이다. 각 폴더의 `update_*.json`, `transitions.jsonl.gz`, `events.jsonl`, `resources.jsonl`, `status.json`, `report.json`, `timing_report.json`, `persistent_audit.json`, `initial.pt`, 주기별 checkpoint와 `final.pt`를 보존했다. 터미널 출력은 같은 이름의 `.log`에 있다.
- 실제 평가 폴더는 `*_stage0_update12_eval_v1`, `*_stage0_final_eval_v1`, `*_stage1_preflight_eval_v1`, `*_stage1_final_eval_v1`이다. `result.json`과 `transitions.json.gz`에 행동·관측·매tick4개 물리 표본·원 음악 판정·안전 근거가 있다.
- [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/review_training_v1.md), [보존 사전 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/preservation_preflight_v1.md), [진행 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_timing_training_20261018.md)

학습에 소비한 코드와 기존 결과는 수정하지 않았다. 구현 검증 당시 통과한238개 CPU 검사를 소스 변경 없이 다시 실행하지 않았으며, 이번 검증은 실제 학습·결정적 평가·원자료 재집계·독립 검수에 집중했다. 분석기와 중간 집계의 이전 버전은 이 폴더의 `archive/`에 원경로·SHA와 함께 보존했다.

최종 [보존 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/preservation_final_v1.md) · [실행 소스·문서 snapshot](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/source_final_v1.json) · [최종 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/final_verification_v1.json).
