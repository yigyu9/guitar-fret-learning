# 원시 분석·추가 평가 독립 검수

대상은 새 `tools/analyze_raw.py`, `finish_analysis.py`, `learning.py`, `trajectory.py`와 `analysis_ledger.json`, `learning_ledger.json`, `summary.json`, `repeat_results.json`, `trajectory_comparison.json`, 보상 관찰 파일 및 CSV다. 코드는 읽기 검수했고 추가 평가 원시 행은 GPU 없이 CPU에서 읽어 검산했다. 검수자가 작성한 파일은 이 문서뿐이다. 원본·공유 소스·기존 모델·기존 status/results를 수정하지 않았고 학습·물리·GPU 작업을 실행하지 않았다.

## 판단

현재 확인한 추가 평가 수치와 기본 미채택 판단을 뒤집는 분석 오류는 발견하지 못했다. 다음 세 가지 집계 범위 보완을 요청했으며 수정된 코드에서 반영을 확인했다. 최종 재생성 산출물과 보고서의 반영 확인은 아래 후속 기록에 남긴다.

1. 몸체별 프렛 범위가 cause별 범위처럼 보이는 열 이름을 `body_all_causes_fret_min/max`로 정정.
2. `whole_AB`와 `AB_ids`에도 AB와 동일한 physical/wrist safe 조건 적용. 새 6회 평가는 실패가 모두 0이므로 이 수정은 AB 1/28/56 수치를 바꾸지 않는다.
3. PPO의 update 마지막 accepted minibatch norm과 전체 accepted minibatch 최댓값을 구분. 최대는 diagnostics의 `actor_accepted.max.grad_norm_pre_clip`, 중앙값은 `median_update_last_actor_grad_norm`으로 범위를 명시.

## 첫 episode 분모와 반복 결과

analyze_raw는 완료/lifecycle에 연결된 report 조건과 각 환경의 단일 첫 episode를 확인하고 env_id를 정렬한다. 후보 trace와 새 보상 trace는 완료 원장의 `finger_control_diagnostics.episode_id`와 맞춰 후속 episode를 제외한다. 새 원시 보상 파일 6개를 독립 검산한 결과, 모든 환경의 첫 episode에 60Hz 기록 435개·연속 시계·종료 1회가 있었고 원장 steps와 일치했다. 환경별 비용 합계와 episode cost의 차이는 0이었다. 9개 보상 항의 키 순서도 유지됐다.

|추가 평가|반복1 AB|반복2 AB|반복3 AB|첫32 AB|
|---|---:|---:|---:|---|
|N32|0/32|0/32|0/32|모두0/32|
|N128|1/128|28/128|56/128|각각0/32|

모두 같은 seed17·200회 checkpoint의 mean 평가이며 추가 학습이 아니다. 특히 같은 N128에서도 결과가 달라지므로 **개선이나 학습 진행이 아니라 반복 민감도**로 분류해야 한다. 56/128도 기존 90% 문턱에 미달한다. 좋은 반복만 선택하거나 기존 12/128·5/128과 혼합해 성공률을 새 채택 기준으로 만들지 않는다.

N32 반복의 기록된 비교 필드에는 1e-9 문턱 초과 차이가 없었지만 이는 저장된 필드와 한정된 반복의 결과다. 모든 숨은 상태나 미래 실행의 bit 재현 보장은 아니다. N128의 차이는 관측기 동기화, 세계 좌표·환경 배치의 수치 처리, native 물리와 제어 피드백 등 가능한 요인을 분리한 결과가 아니므로 PhysX 또는 특정 원인 하나로 확정하지 않는다.

## body×cause 원장의 프렛 범위와 source-string

`wrong_source_time[target,body,cause]`는 실제 audible overlap에 대한 누적 시간이다. 반면 `wrong_source_fret_min/max[target,body]`에는 cause 축이 없다. 같은 몸체의 여러 cause·시각에서 관측된 프렛을 합친 **그 음 전체 범위**다. 특정 cause와 특정 프렛이 같은 시각·표본에서 결합 관측됐다는 뜻으로 해석하면 안 된다.

예를 들어 중지3의 own_wrong_fret와 own_wrong_string에 같은 5..6 범위가 붙어도, “목표6프렛인데 own_wrong_fret가6프렛에서 발생했다”는 결론을 낼 수 없다. 6은 다른 줄 cause에서 나온 그 몸체의 범위일 수 있다. 정정한 CSV 열 이름과 이 제한을 보고서에 함께 유지해야 한다.

`source_string='not logged'`는 원시 source-string 필드가 없다는 보수적인 표기다. 규칙상 other_higher/own_wrong_fret는 목표와 같은 줄을 가리키지만, own_wrong_string은 목표 줄이 아니라는 사실만 알 수 있으며 정확히 어느 줄·어느 표본인지는 복원할 수 없다. 출처 body/cause 시간은 서로 겹칠 수 있으므로 합산해서 총 wrong 시간이나 중복 패널티를 만들지 않는다. 시각별 원인 변화와 실제 접촉 상대·현 압력도 누적 원장으로 역산하지 않는다.

## raw/effective/audible 동시성

새 분석은 `raw_dual`, `effective_dual`, `audible_dual`, A 발음 중 높은 B raw와 A effective의 동시성, B 발음 중 낮은 A raw 잔류를 구분한다. raw positive는 담당 loaded distal 패드 기하이며 effective는 wrong 제외 후다. 기존 후보가 이미 effective라는 이전 정정은 그대로 유효하다.

확인한 추가 N128 반복에서는 준비 구간 raw dual이 306/920/3865개 환경-끝점 등으로 존재하지만 effective dual은 0이었다. A audible 중 B raw와 A effective의 의심 조합도 0이었다. 따라서 **이번 실제 자료에서 기존 all-time effective-dual assert가 평가를 잘못 탈락시킨 사례를 확인한 것은 아니다.**

audible dual 0은 A/B 창이 겹치지 않는 일정에서 정의상 자명하므로 veto 정상의 단독 근거가 될 수 없다. 반대로 원시 두 패드의 동시 후보 자체는 두 음의 동시 성공이나 보상 모순이 아니다. 준비·휴지·말미의 후보, 음 구간의 후보와 실제 앞/뒤 끝점 기반 clean 적분을 구분해야 한다. endpoint 수/240은 끝점 노출 환산이며 원장 적분값과 완전히 같은 계산이 아니다.

## 신규 60Hz 지급 보존

관찰 도구는 실제 `_reward_components` 반환을 복사한 9개 항, 반환 total reward, 누적 counter 차이, 별도 cost를 저장한다. 새 6평가의 기존 보존 검사 결과는 다음 범위였다.

- 9항 합과 반환 reward의 최대 절대차: 약 9.23e-8 이하.
- 항별 지급과 float32 누적 counter 차이의 최대 절대차: 약 2.39e-7 이하.
- 첫 episode의 항별 지급 합과 완료 원장 counter의 최대 절대차: 약 4.36e-6 이하.
- 독립 원시 검산에서 첫 episode 비용 합계 오차: 0.

현재 보존 문턱 1e-5/1e-4 안이며 counter 반올림과 지급 텐서를 구분한 점이 타당하다. phase 집계는 60Hz 구간의 중간 시각으로 배정하는 명시적 bin이다. 접근 potential·수행 부족 정산·실패 cost 같은 60Hz 경계 항을 240Hz로 균등 배분하거나, 지급량·advantage std를 경사 기여율로 바꾸면 안 된다. reward phase는 모든 첫 episode를 고정 분모로 사용한다.

## 학습·궤적 분석 해석

learning은 6개 checkpoint를 CPU에서 strict identity와 pin으로 읽고 저장된 잠재 std를 추출한다. 기록된 mean action에서 복원한 잠재 mean을 이용한 32-node 적분은 **요청각의 수치 근사 기대값**이며 실제 q·접촉·성공의 기대값이 아니다. 요청각 차이를 4개 중지 축과 env0 B구간에 걸쳐 요약한 값이라는 범위를 유지한다. 저장된 observation/latent/value rollout이 없어 항별 실제 학습 경사를 복원하지 않는다.

PPO 상위 `actor_grad_norm`, reward/value loss는 마지막 minibatch 값이라는 범위를 명시해야 한다. accepted/rejected step, 전체 accepted 최대 norm, update-last 중앙값, post-update clip fraction은 서로 다른 통계다. gradient norm·정책 clipping이나 std가 관측됐다는 사실만으로 credit 또는 보상 항의 원인을 확정하지 않는다.

trajectory의 현재 비교는 모두 1740개 정렬된 240Hz 행을 기록한다. 다만 저장된 first endpoint 이후의 비교이며, 각 threshold는 rad/m/bool 등 해당 필드 단위를 따른다. env0 관절과 모든 환경의 거리·후보 배열은 범위가 다르다. 기존128 반복의 전체 거리 최초 차이는 약0.008333초/env100/A/2.976μm로 env0 q의0.158333초보다 이르다. 따라서 env0 q를 전체 시스템의 최초 차이로 표현하면 안 된다. 문턱 이하 차이·기록하지 않은 제어힘·숨은 상태의 시작 원인도 배제하지 않는다.

## 최종 재생성·보고서 후속 확인

수정 후 재생성된 `summary.json`·CSV와 `REPORT.md`를 후속 읽기 확인했다. body_all_causes 프렛 범위, safe whole_AB/AB_ids, accepted minibatch 최대 norm과 update-last 중앙값 구분이 반영됐다. seed17 전체 accepted 최대 norm은 15.3095이며 예전 update-last 최댓값 15.0862와 구분된다. 보고서의 수행·보상·원인 시간·학습 표 수치는 읽은 원자료와 반올림 범위에서 일치한다.

### 교사와 정책의 조건 차이

보고서는 참조 1환경·정답 q 궤적·고정 전환 시점과 정책 학습64/평가32·128환경·관측 기반 행동을 구분한다. 같은 유한 제어기와 자산을 사용했어도 정보·실행 배치가 같지 않으므로, 참조 성공을 정책 학습 성공이나 안정성의 증거로 확대하지 않는 설명이 타당하다. 대표 env0의 요청·적용·실제각을 전체 환경 궤적으로 확대하지 않은 점도 적절하다.

### L_Thorax_y 상한 초기화

`tables/active_axis_stats.csv`의 100/200/300회·양 seed·mean/sampled 대표 env0 B구간에서 L_Thorax_y 포화율100%와 요청·적용 약10도를 확인했다. catalog의 reference 약9도·hold 약10도·upper 약10도 및 NaturalPolicy의 normalized action→clamped atanh bias 초기화와 일치한다. 같은 제어기의 참조 B 요청 약8.236도도 saturation 자료에 보존됐다. 실제 q의 차이·움직임을 해당 정책 축의 요청 탐색과 구분한 해석이 맞다.

처음 제시된 latent 7.2543286은 float64의 atanh(0.999999) 값이었다. 실제 초기화의 float32 clamp 값 0.999998986721과 bias **7.2477326393**을 구분하도록 요청했고, 수정된 `saturation.json`은 두 값을 따로 저장하며 REPORT는 약7.248을 사용한다. 미세 요청각 표준편차 계산은 연속 변환의 국소 근사이며 float32 출력 분포의 정밀한 실측 분산으로 해석하지 않는다.

상한 부근의 tanh 압축과 대표 기록의 요청 탐색 억제는 확인된 현상이다. 그러나 참조와 정책은 이 축 외에도 행동과 정보가 달라, 이 축이 B 실패를 일으켰다는 인과적 기여는 확인되지 않았다. REPORT의 표현이 “우선 검증할 미검증 가설”로 정정됐음을 확인했다. 어느 실제 관절이 기계적으로 고정됐거나 모델 구조가 단절됐다는 결론도 아니다.

### 후속 실험 계획의 범위

세 계획은 아직 실행하거나 채택한 개선이 아니다. 평가 재현성의 추가 관찰 및 계산 배치 분리, fresh 정책의 해당 한 축 초기 bias만 내부로 이동, 별도 조건에서 근접 potential 정밀도만 비교하는 순서와 분리가 명시됐다. 초기 actual q·자산·가동범위·성공 판정과 동일한 두 seed·학습량을 고정하고 기존 checkpoint를 수정 재개하지 않는 범위는 적절하다. 단일 축 bias 개입은 참조8.236도를 정답 명령으로 강제하는 제안과 구분됐다.

제시한 효과·반복 범위 문턱은 앞으로 사용할 운영상 선별 기준이며 유의성 보장이나 기존90% 채택 문턱의 대체가 아니다. 관찰 계약을 추가해도 기록하지 않은 상태·힘과 동기화 영향은 남으므로, 반복 범위가 작아졌다는 사실만으로 GPU 전체 결정성을 인증하면 안 된다. 초기화 이동 후 축이 움직여도 B 수행이 개선되지 않으면 주원인 가설이 약화된다는 기각 방향도 보고서에 명시됐다.

**최종 판단:** 현재 읽은 재생성 자료와 REPORT에 추가 필수 수정 사항은 없다. 원본 데이터·성공 기준·공유 기본 코드를 변경할 이유가 발견된 것은 아니며, 신규128 AB 1/28/56을 개선으로 채택하지 않는 결론도 유지된다. 이 후속 검수는 파일 읽기와 이 문서 갱신만 수행했고 추가 평가·학습·GPU 실행을 하지 않았다.
