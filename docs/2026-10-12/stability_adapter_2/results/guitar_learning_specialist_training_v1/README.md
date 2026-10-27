# 손별 실제 학습과 경과 분석

왼손과 오른손을 각각 약30분 학습했다. **왼손은 목표 접근 거리를 약1.10mm 줄였지만 압현 접촉·유지를 배우지 못했고, 오른손은 유효한 현 통과를 만들지 못했다.** 두 실행 모두 정상 종료했으며 물리 실패·worker 오류·KL 재시도는0이다. 성공한 전문가가 없으므로 결합 학습은 시작하지 않았다.

## 실행 조건과 저장

| 항목 | 왼손 | 오른손 |
| --- | ---: | ---: |
| 실제 실행 시간 | 1802.61초(30분03초) | 1852.66초(30분53초) |
| 업데이트 | 28 | 29 |
| 학습 반영 전이 | 14,336 | 14,848 |
| 완료 에피소드 | 160 | 168 |
| 손별 단계 성공 | 0 | 0 |
| 물리 실패 | 0 | 0 |
| 폐기 전이 | 0 | 0 |

총29,184전이와116,736개 정책 구간 물리 표본을 수집했다. episode 경계의 실제2초 준비는 이 물리 표본 수와 별도다. 왼손4개 미완료 episode의 각64tick(총256전이), 오른손4개 미완료 episode의 각16tick(총64전이)은 bootstrap으로 PPO에 반영했고 완료 에피소드 성공률에는 넣지 않았다.

각 run은 독립4환경/H128/batch512/GPU medium/seed7, actor_lr3e-5/value_lr3e-4, epochs2/minibatch256, 초기 정규화 std exp(-3), cost_weight1을 사용했다. 두 run을 동시에 실행하여 전체 native worker는8개다. 목표는 `05_BN2-131-B_solo`의 첫 단음(물리2번 줄·7프렛·약지·down)이다.

시간 예산1800초는 새 rollout을 시작하기 전 검사한다. 오른손은 예산 직전에 시작한 마지막 배치를 완료하여 약53초 초과했으며 timeout이나 중단은 아니다. 두 실행 모두 `wall_budget`으로 종료했다.

기존 checkpoint를 불러오지 않고 새로 초기화했다. `expert_initialization.json`의 mode 문자열은 일반적인 actor-only 경로 이름이지만 실제 `transfers=[]`, `strict_resume=null`, 초기 updates0/optimizer empty다. 두 모델과 저장 RNG의 초기값은 seed7로 동일했다. 독립 seed 반복 실험은 아니다.

네트워크·보상 정의·모델·자세·gain·충돌 정책·준비2초를 변경하지 않았다. 원 권장8환경/H256/batch2048 및 이전에 이어 학습했던 공유 Actor 실험과는 시작점·수집 배치가 다르므로, 이번 결과를 구조 간 통제 비교로 해석하지 않는다.

- [왼손 최종 모델](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/left_run_v1/final.pt) · [왼손 실행 보고](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/left_run_v1/report.json)
- [오른손 최종 모델](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/right_run_v1/final.pt) · [오른손 실행 보고](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/right_run_v1/report.json)
- [왼손 설정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/left_settings_v1.json) · [오른손 설정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/right_settings_v1.json)

## 초반5회와 후반5회 비교

각 창은2560전이다. episode 반환값은 **해당 창에서 종료한 전체 episode**를 평균했다. 창 경계 이전에 시작한 episode도 끝날 때 전체 값으로 귀속한다.

| 지표 | 초반5회 | 후반5회 | 해석 |
| --- | ---: | ---: | --- |
| LH onset 직전 말단 원점–목표 거리 | 20.938949mm | 19.841487mm | 1.097462mm 감소 |
| LH episode 반환값 | −0.333742 | −0.325450 | 작은 개선, 접촉 보상은0 |
| LH 평균 안정성 비용/tick | 0.0000197693 | 0.0000113887 | 감소 |
| RH sweep 중 피크–가이드 거리 | 55.169923mm | 55.325716mm | 0.155792mm 증가 |
| RH episode 반환값 | −0.413075 | −0.413897 | 개선 확인 안 됨 |
| RH 평균 안정성 비용/tick | 0.00000141175 | 0.00000148523 | 작은 변화 |

LH onset 직전 지표는 task time67/60초(약1.1167초)의60Hz 표본을 episode마다 하나 사용했다. 초반·후반 각각28개 표본이다. RH sweep은 onset ±80ms의 가이드 활성 표본이며 각280개다. RH의 창별 종료 episode 수는28→32로 다르다. 동일 seed를 고정한 별도 평가가 아니라 현재 정책이 수집한 관측 비교이며 통계적 수렴을 인증하지 않는다.

별도 LH `[press,onset]` 전체 표본 평균은20.805251→19.771474mm다. 이 지표는 후반 창의 미완료 episode 일부도 포함하여 표본 수224→244다. 이를 위 고정 시각 지표와 혼용하지 않는다. 거리는 말단 body 원점과 피크 마커의 기하 대리 지표이며, 실제 손가락 패드 gap·현 압력은 아니다.

![손별 학습 경과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/training_progress_v2.png)

권장 그림은 v2다. v1의 축 안 설명이 일부 점에 가까워 v2에서는 설명을 제목으로 옮겼고, 왼손은 부분 episode의 영향을 피하는 고정 시각 지표로 바꿨다. 성공 축도 정수 눈금을 사용했다. v1 원본과 소스·수치는 보존했다. [공유용 PDF](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/training_progress_v2.pdf).

## 실제로 무엇을 배웠는가

왼손은 접근 보상만 조금 개선했다. 목표 손가락의 접촉 획득, 유효 유지 시간,50ms 연속 유지, 단계 성공은 모두0이다. 오른손은 시간과 무관한 유효 기하 현 통과 자체가0이므로50/100ms 매칭도0이다. 시간 오차만 큰 성공 동작을 놓친 상황으로 설명할 수 없다.

LH 전체 보상 구성은 접근+27.6082, 미달−80, 행동 변화 비용−0.00992이며 접촉·유지 보상은0이다. RH는 가이드+14.4598/방향+0.04998, 미달−84, 행동 변화 비용−0.00187이며 strict/lenient 성공 보상은0이다. 총보상은 부분 episode도 포함하므로 완료 episode 평균×episode 수와 정확히 같을 필요는 없다.

PPO는 양쪽에서 정상적으로 파라미터를 갱신했다. 최종 모델은 유한하고, 비학습 Actor17개 tensor와 해당 std는 초기값 그대로이며 비활성 손 행동도 모든 전이에서0이다. 최대 accepted KL은 LH0.008048/RH0.002166으로 한계0.02 이내였고 재시도0이다. 최종 활성 std 평균은 LH0.0497871/RH0.0497797이다. 이는 정규화된 pre-tanh Gaussian 값이며 rad 단위가 아니다.

첫 rollout의 고정된512개 관측에 checkpoint를 다시 넣은 [출력 변화 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/policy_change_v1.json)에서, 최종 결정적 출력이 만드는 unfiltered 관절 목표 offset RMS는 LH0.004018rad/RH0.001742rad였다. 네트워크는 변했지만 평균적으로 요청하는 변화는 아직 작다. 이 값은 codec smoothing/속도·관절 제한 이전이며, 실제 관절 변위나 별도 native 평가 결과가 아니다.

따라서 이번 예산에서는 **왼손의 작은 접근 개선만 확인했고, 두 기능 모두 성공을 학습했다고 볼 수 없다.** 학습 시간이 충분했다고 단정할 수도 없지만, 현재 설정을 그대로 더 오래 실행하는 것만으로 성공할 것이라는 근거도 아직 없다.

## 접촉 검사와 초기 배치의 추가 진단

[초기 상태 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/initial_state_diagnostic_v1.json)은 최초 제어 tick 직후의 실제 원자료8개를 정리한다. 초기 약지 말단 원점의 목표 대비 차이는 대략 lateral6mm/neck 방향6mm/높이17mm였다. RH 피크는 현 기준 across 방향 약47mm, 높이 약19mm 차이가 있었고, 깊이8mm를 포함한 가이드까지의 차이는 또 다르다. 이 원점·마커 수치로 패드의 실제 간격이나 도달 불가능성을 판정하지 않는다.

초기 LH는 검지와5프렛의 다른 접촉을 가지고 있었다. [읽기 전용 양성 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/contact_positive_control_v1.json)에서 같은 native 표본을 **다른 목표(검지·물리1번 줄·5프렛)**로 재질의하자4개 중3개 표본이 실제 접촉 후보였다. 본래 목표(약지·2번 줄·7프렛)를 재질의한 값은 기록과 동일하게 모두 False였다.

이는 검사기가 실제 접촉을 인식하는 사례를 제공하지만, 원래 목표의 성공이나50ms 유지가 아니다. 학습 목표·원래 label·보상은 변경하지 않았다. 특정 다른 목표의 단일 표본 양성으로 모든 형상·접촉 판정을 검증한 것도 아니다.

## 안정성과 초기화

Root 고정·하체 유한 제어·105/97/8·자유 기타/중력ON/스트랩OFF를 유지했다. 기타 직접 보조·강제부착·지속 상태 덮어쓰기는 추가하지 않았다. 매240Hz에서 기존 학습 안정성 비용과 실패 종료를 검사했다.

| 저장한60Hz 말단 표본 통계 | LH | RH |
| --- | ---: | ---: |
| 전체 지지 접촉 존재 | 100% | 100% |
| 양발 접촉 | 100% | 100% |
| 가슴·오른상완·허벅지 동시 지지 | 88.392857% | 99.986530% |
| 최대 기타 이동 | 1.992893mm | 0.572682mm |
| 최대 기타 회전 | 0.006556rad | 0.001980rad |
| 최대 발 이동 | 0.318942mm | 0.083250mm |

학습 중 지지 분담 변화는 허용하며, 삼중 지지가 항상100%였다고 설명하지 않는다. 이 표는60Hz 저장 표본의 extrema다.240Hz 실패 판정의 사유 합집합은 비어 있으나, 전체240Hz 원자료를 매 tick 보관한 것은 아니다. 작은 움직임으로 실패 없이 실행된 결과이며 큰 연주 동작의 강건성·정밀 V3 기준·Root 자유 균형 검증과도 구분한다.

시뮬레이터는 worker마다1개를 재사용했다.8개 worker 각각 create_sim1/create_env1/load_asset2/destroy_sim1이며, 종료 후 모두 exitcode0이다. LH164회·RH172회, 총336회 준비 상태 모두 삼중 지지·양발·원 물리 계약을 만족했다. 최초 준비 대비 LH 최대 기타 차이는0.422133mm/0.00154869rad, 발0.054810mm, 관절 q0.000983298rad였다. RH 기록의 최초 대비 차이는0이었다. 숨은 solver/cache까지 같다는 주장은 아니다.

## 자원과 시간

학습 시작60초 이후→종료 직전의 **run별4worker 현재 RSS 합**은 LH2.447918→2.448387GiB, RH2.448925→2.449318GiB였다. 두 run이 겹치는 host 메모리를 중복 합산하지 않았으며, 전체 가용 메모리 최솟값은23.411205GiB였다. 이번 약30분에는 이전 scene 재생성 경로의 큰 RSS 증가가 재현되지 않았다. 더 긴 시간의 누수 부재를 인증하지는 않는다.

RH PSS는 마지막에1.656077→1.745705GiB로 변했으나, LH 종료 직후인07:13:19.702→07:13:24.744UTC 사이에 발생했다. 두 표본의 RSS는2.449318GiB로 같고 이후14개 PSS 표본도 같았다. 공유 페이지 분담 변화와 일치하는 관찰이며 이 증가를 native 메모리 누수로 단정하지 않는다.

![학습 자원 경과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/runtime_progress_v1.png)

reset이 전체 wall의 LH49.00%/RH49.40%, step이49.35%/49.02%, PPO 연산이0.091%/0.093%였다. scene 재생성은 없어졌지만 실제2초 준비가 매 episode 필요하여 수집 비용이 크다. collection98.34%/98.39%는 step/reset과 중첩하므로 합산하지 않는다. 네트워크 크기를 줄이는 것만으로 현재 물리 수집 시간을 크게 줄일 것이라는 근거는 없다.

## 해석과 다음 우선순위

확인한 사실은 정상적인 최적화·안정적인 실행과 목표 행동의 경험 부족이다. 손별로 나눠도 현재 예산에서는 접촉·현 통과가 없었으므로, 손별 접근·접촉·탐색 단계도 점검해야 한다. 네트워크 용량 한계나 특정 단일 원인을 입증한 실험은 아니다.

다음은 로그에 근거한 제안이며 이번 실행에서 구현·검증한 해법은 아니다.

1. **각 손의 실제 성공 궤적부터 확보한다.** LH 약지7프렛 후보50ms 유지와 RH 단일 현 통과를 현재 행동 범위·유한 제어·자유 기타 조건에서 각각 재현한다. 기존 검증된 타현 목표와 제어 궤적을 참고할 수 있지만, 현재2초 준비와 정책 기준 offset 안에서도 같은 성공이 나는지 새로 확인해야 한다.
2. **성공 궤적으로 초기화를 돕는다.** 시뮬레이션에서 얻은 목표 궤적을 BC/teacher 초기화나 접촉에 가까운 단계별 시작 상태에 활용하는 방안을 검토한다. 기타 고정이나 잘못된 성공 label로 대신하지 않는다.
3. **역할별 탐색과 보상을 점검한다.** 특히 RH는 timing 성공 이전의 기하 통과가0이다. 실제 방문 행동이 목표 영역에 들어가는지, 시간적으로 이어지는 움직임이 필요한지, 가이드 접근과 접촉 조건이 일치하는지 확인한다. std·gain을 전신에 일괄 확대하는 변경은 하지 않았다.

성공 전문가가 확인된 뒤에 동결 상대 손과의 적응·공동 학습으로 넘어간다. 이번에는 결합·구절·다른 곡·음향·새 영상 평가를 실행하지 않았다.

## 재현 근거와 보존

- 학습: [분석 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/learning_analysis_v1.json), [검산·입력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/learning_verification_v1.json), [분석기 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/analyze_learning_v2.py), [분석 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/learning_progress.md).
- 자원/준비: [분석 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/runtime_analysis_v1.json), [검증 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/runtime_verification_v1.json), [분석기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/analyze_runtime_v1.py), [설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/runtime_progress.md).
- [실행 전 소스70개 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/source_run_v1/manifest.json)에는 기존 Python69개와 원 계획이 포함된다. 분석기 v1은 float32/native 누적 정밀도 검사를 보완하기 전 원본으로 남겼고, 최종 결과는 v2로 계산했다.
- 학습 검산은 episode 전체 재구성, 별도 scalar 재독해, checkpoint 유한성·optimizer·비활성 branch/std/행동 불변, 첫 rollout latent/logp 대조를 포함한다. checkpoint std는 미샘플링 비활성 placeholder와 구분했다.
- 최종 독립 검수는 `review.md`, 전체 보존 감사는 `final_verification.json`으로 별도 봉인한다. 기존 코드·원자료·실패·checkpoint는 덮어쓰지 않았다.
