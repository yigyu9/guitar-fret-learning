# Skill curriculum 결과·추가 보조 코드 독립 검수

요약 판정: **문제없음 — 현재 제한 실행과 명시된 인증 범위**. Critical·수정이 필요한 Warning은 발견하지 못했다. 실제 손별 scripted 성공 궤적·505차원 데이터 확보와 네 학습 실행의 완료는 확인됐지만, 저장된 결정적 정책의 준비 성취는 네 조건 모두0/2다. 이를 학습된 압현·타현 전문가나 공동 음악 성공으로 해석할 수 없다.

## 범위와 검증 방법

신규 `capture_demo_v1.py`/`capture_demo_v2.py`, `evaluate_v2.py`, `advantage_diagnostic_v1.py`, `analyze_trajectories_v1.py`, `plot_results_v1.py`와 `guitar_learning/SKILL_CURRICULUM.md`의 최종 proxy 설명을 읽었다. 추가 요청에 따라 `analyze_evaluation_v1.py`·`evaluation_comparison_v1.json`, `plot_results_v2.py`의 변경과 정본 PNG2개, phase README와 G README 상단도 확인했다. 앞서 검수한 helper는 관련 연결만 대조했다. 닫힌 `learning_comparison_v1.json`, `trajectory_analysis_v1.json`, demonstration 두 건과 최종 정책 평가 네 건을 원자료와 대조했다.

검수자는 이 producer나 native 환경·학습·시험을 실행하지 않았다. 독립 점검은 저장된 JSON/gzip/NPZ의 읽기, 원 transition의 재집계, SHA 계산과 그림 열람으로 수행했다. 소유한 이 보고서 외의 파일은 변경하지 않았다. 전체 CPU189개 통과는 앞선 구현 검수에 기록한 별도 검증이며 이번 결과를 성공으로 바꾸는 근거가 아니다.

## Critical / Warning

없음.

## 신규 코드의 정합성

- **`capture_demo_v1.py:24–30` 및 v2 동일 경로:** 각 action 직전 관측을 복사해 NPZ에 저장하고, 그 action을 실제 v2 환경에 적용한 후 후속 네 물리 표본·측정·성취를 trace에 저장한다. 관측과 행동을 한 tick 잘못 짝짓는 경로가 없다. 성공은 과거 teacher의 flag를 복사하지 않고 새 환경의 안전한 전체-horizon 성취로 판정한다. 이 데이터는 scripted replay이며 학습된 policy rollout이 아니다.
- **`capture_demo_v2.py:19–21`, `evaluate_v2.py:25–28`:** 기존 명시 목록에 준비 자세/물리 입력을 추가하여 실행 전에 pin한다. 평가에는 G·stability Python 목록도 미리 넣는다. 이 추가는 측정·보상·기존 checkpoint strict load와 `parallel.FIELDS` 순서를 변경하지 않는다.
- **`advantage_diagnostic_v1.py:12–18`:** 현재 설정의 reward GAE γ=.99, cost GAE γ=1, λ=.95와 population std를 사용한다. 각각17개 tensor 필드의 첫 rollout 동등성을 기록하고 표준화 이전 advantage 산포를 비교한다. reward/cost advantage의 상관, 정책 score-function과의 결합, 이후 optimizer 영향을 계산하지 않으므로 gradient 기여율이나 후속 학습의 인과 설명이 아니다.
- **`analyze_trajectories_v1.py:16–31`:** 실제240Hz 측정에서 접촉 후보 표본·다중 native contact evidence·유효 crossing·기타/발 변위를 따로 집계한다. 후보 표본 수와 접촉 증거점 수는 분모가 다르다. 최대/최소와 지지 비율은240Hz이며 앞선 학습 요약의60Hz endpoint 지표와 구별한다. `consecutive_physics`도 기록한다.
- **`plot_results_v1.py:16–25`:** 성공률은 각 update의 완료 episode 분모다. 현재 모든 update는 완료 episode2개이므로 분모0을0%로 그리는 fallback이 이번 결과를 왜곡하지 않는다. 한 seed의 탐색 중 준비 성취와60Hz 기타 최대를 표기하며 접촉·타현 성공 그래프로 바꾸지 않는다.
- **`plot_results_v1.py:27–45`:** 별도 성공 scripted 궤적의240Hz 접촉 후보·원점 거리·피크의 string2 횡방향 위치·기타 변위를 그린다. 그림에서 학습 정책과 scripted teacher,60Hz와240Hz의 구분이 읽히며 제목·축·범례에 잘림이나 숫자·표본 주기 혼동을 발견하지 못했다. 출력 PDF의 내용 생성 경로는 같은 figure이며, 별도의 PDF 렌더 검수까지 수행했다는 주장은 하지 않는다.

## 505차원 demonstration 확인

두 NPZ 모두 다음 shape와 유한값을 확인했다: state `(240,505)`, events `(240,64,24)`, mask `(240,64)`, priority events `(240,2,24)`, priority mask `(240,2)`, action `(240,39)`.

- 저장 action240개는 각각 원래 LH servo / RH grid teacher의 action과 전부 exact다.
- 상태의 `previous_action` 구간은 첫 tick 이후 직전 action의 float32 표현과 전부 exact다. action 직전 입력을 저장한다는 코드와 맞는다.
- `left_demonstration_v1`은 native hold 성취 참, `right_demonstration_v1`은 native 기하 cross 성취 참이다. 둘 다240 ticks·960물리 표본·4초를 완료했고 원래 공동 음악 matched50/100은0이다.
- 검수 시 source pin 재계산 변화는 LH1,420개·RH1,529개 모두0이었다. LH capture v1과 RH capture v2의 pin 범위는 같지 않으므로 같은 범위의 감사라고 합쳐 쓰지 않는다.

이 데이터는 후속 초기화의 입력/행동 자료다. 이를 이용한 behavior cloning이나 PPO 초기화가 이미 수행됐거나 성공했다고 해석하지 않는다.

## 손별 실제 성취와240Hz 통계

`trajectory_analysis_v1.json`은12개의 닫힌 trial을 포함한다. 모두960개의 연속 물리 표본·4초이고 비활성 손 action 최대는0이다. 기존 실패 trial도 함께 남아 있다.

- LH servo v3, 동일 조건 반복1, v2 demonstration은 각각 후보 표본690개·유효 native fret 증거1,601개·연속 후보2.870833333초다.690은 표본 수이며1,601은 여러 접촉점의 증거 수다. 기타 최대4.981619878mm, 발 최대2.401754291mm, distal 원점 최소19.003020273mm로15mm reach proxy는 성립하지 않는다. 원래 음악 구간의 held total은0.223033333초, release count는0, matched50/100은0이다.
- RH grid native v2와 demonstration은 target string2에서 down/up/down의 유효 crossing3개, 지정 down2개를 기록한다. 속도는 각각+0.084857862/−0.085783307/+0.085190083m/s로 기존 최소속도0.05m/s를 통과한다. 기타 최대0.257665889mm·발 최대0.004452257mm이며 물리 실패는 없다. timed 및 공동 음악 매칭은0이다.
- 이전 RH grid v1의 약0.042m/s 후보는 원래 speed gate에서 거부된 채 보존된다. offline fitting이나 무효 후보를 유효 성공 수에 넣지 않는다.

이들은 현재 행동권의 실제 수행 가능 궤적을 확보했다는 근거다. 두 손을 동시에 수행하거나, 새로운 초기 조건·곡·음에 일반화했다는 근거는 아니다.

## 닫힌 비용 비교의 원자료 재집계

원 `transitions.jsonl.gz` 네 개를 독립적으로 읽어 다음을 재집계했다. 모두 report 완료 참,12업데이트·5,760전이·24완료 episode·물리 실패0·`changed_inputs=[]`이며 분석 JSON의 episode 수·성공 수·평균 return/cost·기타 최대와 일치했다.

| 학습 조건 | 탐색 중 준비 성취 | 평균 episode return | 평균 episode cost | 기타 최대 mm,60Hz |
| --- | ---: | ---: | ---: | ---: |
| LH reach, weight1 | 13/24 | 1.025586181 | 13.893383825 | 74.952191760 |
| LH reach, weight0.1 | 14/24 | 1.071437604 | 14.751259185 | 74.952191760 |
| RH ready, weight1 | 0/24 | 0.310668058 | 0.086295142 | 9.732375239 |
| RH ready, weight0.1 | 0/24 | 0.305563557 | 0.086109049 | 6.797820439 |

활성 손의 tick별 action RMS 평균도 독립 확인했다. LH1/0.1은0.234824668/0.234816766, RH1/0.1은0.226969932/0.226823577이다. 이 값은 비활성 손을 포함한39축 RMS나 모든 시각을 합친 pooled RMS가 아니다.

첫 rollout 동등성 JSON은 양손 모두17개 필드 참이며 GAE std 비율은 LH3.294453859, RH1.186757922다. weight0.1을 곱한 비율은0.329445392/0.118675798이다. 이는 첫 표본의 산포 진단만 지지한다. 위 단일 seed 결과나 작은 성취 수 차이로 비용 가중치0.1의 일반적 우월성, 안정성 향상 또는 보상 경쟁이 학습 부진의 원인이라고 결론 내릴 수 없다.

## 저장 정책의 결정적 재평가

각 결과와480 ticks의 저장 transition을 확인했다. 네 조건 모두 동일 prepared start에서2개 episode를 안전한 `timeline_complete`로 마쳤으며, 준비 성공 **0/2**, 원래 음악 매칭0이다.

| 저장 정책 | 준비 성공 | 평균 return | 평균 cost |
| --- | ---: | ---: | ---: |
| LH weight1 | 0/2 | 0.533177304 | 0.000214935393 |
| LH weight0.1 | 0/2 | 0.542264546 | 0.000110507529 |
| RH weight1 | 0/2 | 0.358468790 | 0.000117485122 |
| RH weight0.1 | 0/2 | 0.316490812 | 0.000007406978 |

평가별1,544개 pin의 현재 SHA 변화는0이며, 각 pin 목록의 checkpoint 경로는 해당 비용 학습의 `final.pt`와 같고 SHA도 일치했다. 코드는 그 경로를 strict load한다. 학습 중 탐색 성공을 이 결정적 정책의 성공으로 승계하지 않는다. 탐색과 deterministic action의 차이가 있으므로 두 모드의 비용 차이를 순수한 학습에 따른 안정성 개선으로 해석할 수도 없다. 같은 reset의 두 반복은 독립적인 새 초기 분포의 통계 표본이 아니다.

## 문서와 입력 보존의 경계

최종 `SKILL_CURRICULUM.md`는 reach를 선택 진단으로 두고, 실제 contact/hold를 우선한다고 명시한다. RH scripted 성공 경로의 y≈−0.36m/depth≈4mm/앞뒤≈8mm와 비용 파일럿 기본 guide의 차이도 밝힌다. 실험 도중 runner guide를 바꿨거나 새 경로를 정책이 학습했다고 설명하지 않는다. 현재 입력은505, 역할별 확률 출력은33/6이며 전체 모델 parameter 수와 실제 학습 대상 branch도 구별한다.

각 helper의 `source_unchanged`와 분석의 `inputs_unchanged`는 **명시된 목록**의 불변이다. prepared 입력과 G/stability Python을 넓게 pin한 v2도 BUNDLE 전체와 `tab2body/full/events.py`까지 포함한 모든 음악 입력 감사를 자동으로 뜻하지 않는다. 원래 native input union과 현재 학습의 전체 source/asset 감사는 root의 최종 보존 검증에서 별도로 연결해야 한다. 본 보고서는 그 최종 봉인 파일의 검수까지 완료했다고 주장하지 않는다.

## 정본 문서·후처리 최종 확인

phase `README.md`, G의 `SKILL_CURRICULUM.md`와 README 상단은 scripted 성취·탐색 중 성취·최종 deterministic 정책 성취를 구별한다. 학습 실행의 완료를 연주 기술의 습득으로 승계하지 않고, 이번 파일럿이 원래 guide/원점 shaping·std.25를 사용했다는 사실과 demonstration 기반 초기화·모방학습을 아직 실행하지 않았다는 사실을 명시한다. 비용1/0.1의 일반적 우열을 확정하지 않는 해석도 자료와 맞는다.

- 원 skill episode 기록에서 LH weight1의 contact/hold episode는 **7/24·2/24**, weight0.1은 **9/24·1/24**임을 독립 확인했다. RH 두 조건의 contact/hold/matching cross는 모두0이고, 실제 유효 geometric crossing 총수도0이다. 이는 준비 proxy 성취13/24·14/24와 다른 지표다. `analyze_evaluation_v1.py`의 집계와 정본 표가 이를 구별한다.
- 평가 네 개의 준비·contact·hold·geometric cross는 모두0이며 각2회 완주다. 문서의 평가 기타 최대0.221/0.106/0.141/0.051mm는60Hz endpoint 값이다. 평가가 흔들림을 적게 보였다는 사실을 학습에 의한 안정성 개선으로 확대하지 않는다.
- LH servo v3 원240Hz flags를 독립 집계하면960표본 중 하나 이상 지지960, 양발960, 삼중 동시 지지 **63/960=6.5625%**다. README의 지지 표와 일치한다. 따라서 접촉 유지 성취만으로 상완 지지 회복·왼손 하중 비의존·초기 자세 V3 정밀 조건 충족을 인증하지 않는 설명이 필요하며, 정본은 이 한계를 명시한다.
- `plot_results_v2.py`는 수치·원자료를 바꾸지 않고 범례 위치·원점 거리 제목과 저장 파일명 등을 바꾼 후처리다. `learning_comparison_v2.png`, `successful_trajectories_v2.png`를 직접 열어 데이터 가림·축/범례 잘림이 없고 기존 수치·60/240Hz·scripted/learned 구분이 유지됨을 확인했다. 정본 그림 교체를 native 재실행으로 설명하지 않는다.

여기까지 보고서는 확정한다. 이후 root가 작성하는 최종 보존 봉인은 별도 읽기 전용으로 확인하며, 이 보고서를 봉인한 뒤 그 결과를 여기 덧붙여 해시를 바꾸지 않는다.
