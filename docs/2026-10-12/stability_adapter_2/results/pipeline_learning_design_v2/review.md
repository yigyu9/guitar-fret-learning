# 공동학습 파이프라인 개선 설계 검수

2026-10-15. change-reviewer가 상세 설계·근거 분석·상위 요약 문서를 검수했다. 본 검수 기록만 작성했으며 다른 담당자의 문서, 환경·학습 소스, 기존 결과와 봉인 파일을 수정하지 않았다. 새 모델 학습·native 실행·문헌 재검색은 수행하지 않았다.

## 요약 판정

문제없음. 최종본에서 Critical 또는 미해결 Warning은 발견하지 못했다. 검수 중 지적한 조기 물리 실패의 비용 누적 편향은 본문에 반영되었다. 이번 판정은 설계와 근거의 정합성에 관한 것이며, 새 구조의 효과·안전 보장·음악 수행을 인증하지 않는다.

## 범위와 근거 확인

[상세 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pipeline_learning_design_v2/README.md), references.json, song_audit_v2.py가 생성한 song_audit.json과 audit_attempts.json, optimizer_audit.py/json을 읽었다. [설계 요약](/home/ajou/yigyu/3/docs/plans/music_model_pipeline_20261015.md), 확인 문서, PROJECT_CONTEXT 상단 및 PLAN 음악 섹션의 연결 문구도 확인했다. 코드 근거는 기존 environment_contract_v1.py, fresh_music_v1/events.py·environment.py, fresh_learning_v1/policy.py·ppo.py와 이전 파일럿 기록을 대조했다.

- song audit의 사전/사후 입력 SHA 25개와 optimizer audit의 7개가 각각 일치하고, 현재 파일 digest도 모두 사전 값과 같았다. 분석기를 다시 실행하지 않았다.
- 실패한 첫 song_audit.py와 완료된 song_audit_v2.py가 구분되어 있다. 출력 파일명은 song_audit.json이며 schema는 v2다. 실패를 성공한 분석으로 설명하지 않는다.
- 새 확인·설계·상세 문서의 로컬 링크는 모두 존재했다. 외부 문헌의 보장이나 다른 악기 성과를 현행 PPO·자유 기타의 성과로 승계하지 않는 범위를 확인했다. 문헌 결과 자체를 재현한 검수는 아니다.

## 주요 검수 결과

| 항목 | 대조 결과와 판정 |
|---|---|
| 실제 관측과 누락 이력 | 기존548D 물리 입력에 상대 위치·속도와 직전 최종 목표가 이미 있음을 올바르게 설명한다. 별도 target 오차, dwell·matched·release 이력의 누락을 구체적으로 지적하며 기존 관측을 전부 없다고 과장하지 않는다. |
| 선형 역할 head | 같은 특징 h에 대한 세 선형층의 concat은 하나의54출력 선형층과 수학적으로 같다. 이름 분할만으로 협력 구조의 기여를 주장하지 않는 설명이 맞다. |
| 현재 actor/value | 공유 encoder, 두 value head, 고정 비용 계수1이라는 기존 구현과 맞는다. actor/value encoder 분리와 학습 가능한 multiplier는 후속 후보이며 현재 구현으로 설명하지 않는다. |
| KL 계산 | 동일 분산의 독립54D Gaussian에서 평균이 각0.01 이동한 예의 KL≈1.08926, 총 KL0.03의 RMS 평균 이동≈0.00165957은 맞다. 예시와 실제 원인을 구분한다. |
| 실제 PPO 갱신 | 이전00곡16갱신의 첫 KL0.343531, 범위0.033298–0.416007, 첫 clip fraction0.847656과 epoch 후 검사 순서가 맞다. 첫 minibatch 후 검사·weight/optimizer 복원은 아직 설계다. |
| 시간 상수 | 0.99^60≈0.547157, (0.99×0.95)^60≈0.0252074가 맞다. 후자를 미래를 전혀 학습할 수 없다는 한계로 해석하지 않는다. |
| 종료 의미 | 진짜 유한 구절 끝의 terminal과 계속되는 과제의 artificial cut을 구분하는 개선이 타당하다. 기존 음악 환경이 timeline 끝을 truncation으로 반환하는 근거와 맞으며, 현재 코드를 이미 고쳤다고 주장하지 않는다. |
| shaping | β[γΦ(next)−Φ(now)]의 시간·진행 상태, bounded potential, true terminal Φ=0 및 cut bootstrap 조건을 명시한다. 관련 MDP의 불변성 조건과 함수 근사 PPO의 실제 성공을 구분한다. |

## 새 우선 곡과 평가 계약

[song_audit.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pipeline_learning_design_v2/song_audit.json)의 원본66 event/67 target, supported65 event/65 target과 본문이 일치한다. 미지원 event-000042의 동일 줄 빠른 재타현을 누락된 운지나 완전 지원으로 오인하지 않는다.

[README:53](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pipeline_learning_design_v2/README.md:53)의 짧은 음6개는 원본 tempo에서23.2–70.9ms다. 현재 코드는 audible 구간에만 1/60초씩 유효 시간을 더하므로, 가장 긴 경우에도 최대5표본≈83.3ms이고 기존 max(100ms, 요구 길이×0.8)에 도달할 수 없다. 입력 데이터에서 가능한 목표와 실제 접촉 도달 가능성을 구분한 설명이 맞다. 느린 tempo로 바꾼 모든 경우까지 불가능하다고 확대하지 않는다.

같은 줄의 다른 owner 전환48개 중100ms 미만24개/50ms 미만17개, 첫7프렛 약지→5프렛 검지의 gap0이 분석과 일치한다. 현재 owner에 가려진 다음 준비를 별도로 표현하자는 근거가 있으며, 낮은 프렛의 동시 사전 접촉이 실제 가능하다는 부분은 아직 형상·물리 검증 가설로 제한한다.

4슬롯 span의 최소0.3947초·중앙1.10295초·최대2.9721초 및62개 표본 중46.77%가1초 미만이라는 정의가 맞다. 이를 제어 시간 전체의 비율로 설명하지 않으며, source 준비 창5개 중첩을 실제 동시5음으로 바꾸지 않는다. 현재 sustain과 미래 정보의 분리·초 단위 창·overflow 표시는 후속 계약으로 구분된다.

[README:149](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pipeline_learning_design_v2/README.md:149)의 ±50ms/±100ms 독립 일대일 ledger가 타당하다. 기존100ms greedy match를 단순 필터하면 −90ms 시도가 target을 소모하여 뒤의 정시 시도를50ms 성과로 세지 못하는 사례가 가능하다. 새 설계는 이를 분리하되 한 ledger 내 crossing/target 중복 사용과 두 기준 성공 수 합산을 금지한다. 아직 실제 narrow/wide 평가 코드를 바꾼 결과로 주장하지 않는다.

## 목적함수와 해결된 Warning

음악 성과 최대화와 기대 비용 budget은 원하는 목적이며, 고정 가중치 PPO와 구분되어 있다. multiplier의 비음수 갱신 부호가 맞고, budget과 cost return의 할인·분모·terminal 정의를 일치시킨다. 기대 비용 제약·sampled-state KL 제어·두 critic을 모든 순간의 안전 또는 CPO 보장으로 표현하지 않는다.

검수 중 [README:143](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pipeline_learning_design_v2/README.md:143)에 대해 **분모 고정만으로 조기 실패 후 누적 비용 분자가 줄어드는 문제는 해결되지 않는다**고 지적했다. 최종본은 이 한계를 명시하고 중도 물리 실패의 episode-failure 지표와 terminal 실패 비용, 독립 failure budget·평가를 필수로 두었다. C1 이탈시간 감소만으로 안정성 개선을 판정하지 않으며, 남은 음악 목표 누락과 simulator 오류 제외도 분리한다. Warning은 이 수정으로 해소되었다.

## 설계와 실측의 경계

우선 곡05_BN2-131-B_solo·±50ms 주지표/±100ms 진단, 초기 자세 연구 전 모델 설계 집중이라는 사용자 결정이 유지된다. 새 입력·pooling·actor/value 분리·budget·curriculum의 성과는 아직 실험하지 않았고, 최종 차원·폭·행동 scale·접촉/실패 문턱은 새 환경 이후 확정한다. 옛00곡16갱신과 약0.092mm의 미미한 접근 차이·접촉 유지0초를 새 곡이나 설계의 성과로 옮기지 않는다.

모든 비교군의 의미상 결함을 공통 정정한 뒤 optimizer·표현·미래 창·비용 목적·curriculum을 각각 비교하도록 했으며, 동일 물리/목표/초기 분포·전이 예산과 복수 seed·실패를 보고하는 방향이 타당하다. 이번 근거만으로 새 모델의 우월성·음향 재현·사람 모션 유사성·연구 독창성을 입증했다는 과장은 없다. 초기 자세 완료 뒤 실제 새 환경에서 이 가설들을 검증해야 한다.
