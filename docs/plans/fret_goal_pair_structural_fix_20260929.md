# Fret goal-pair 구조 개선 계획

> 갱신: 2026-10-01. 기존 구조 수정은 완료했지만 학습 병목 해소는 미완료다.
> 이번 보완은 실행 계획이다. 아래 미완료 항목의 코드 수정·GPU 실험은 아직 수행하지 않았다.

설계 정본은 [master_plan/03_fret.md](</media/ajou/새 볼륨1/Guitar/master_plan_20261019_archived_20261027/03_fret.md>), 실행 계약은
[학습 README](../../fret/03_training/README.md)와 run manifest를 따른다.
개선안을 정하기 전 [실험 이력](../archive/dated/2026-08-24/FRET_EXPERIMENT_HISTORY.md)을 확인한다.

## 1. 목표와 범위

한 곡을 반복 학습해 **정해진 시각에 올바르게 누르고, 필요한 시간 동안 유지하는 모션**을 만든다.
평균 보상이나 curriculum 승급 자체를 최종 성공으로 삼지 않는다.

이번 순서는 `진단 → 판정·시간 계약 검증 → 원인별 최소 수정 → 대조 실험 → 장기 학습`이다.
30-action/420-observation, thorax 고정, 바레 제외, 기존 안전 종료는 유지한다.
증거 없이 hold gate 완화, 준비 시간 확대, RSI 비중 확대, 보상 여러 개 동시 변경은 하지 않는다.

## 2. 최신 근거: 무엇이 좋아졌고 무엇이 남았나

기존 수정 기준은 `20260921_0940_02_Jazz1-200-B_solo`다.
후속 학습은 `20260929_1405_02_Jazz1-200-B_solo`이며 아래 수치는 **45,830 iteration까지의 스냅샷**이다.
현재 진행 여부나 이후 결과를 뜻하지 않는다.

동일 regime인 `goal_pair / mixed 0 / preview-only / recovery 아님`의
45,040~45,830, 80개 로그를 사용했다. 조건부 비율은 target-frame 수로 가중 집계했다.
도구는 [diagnose_fret_goal_pair.py](../../tab2body/tools/diagnose_fret_goal_pair.py)이며
해당 run manifest의 설정을 사용했다.

| 항목 | 관측 | 해석 |
|---|---:|---|
| 전체 학습 F1 / PRESS-frame 성공 | 0.9672 / 96.86% | 평균은 높지만 약한 이벤트를 가릴 수 있음 |
| mastery | 검지·약지·소지 3개 | 중지 미숙련, mixed 0 정체 |
| 중지 rehearsal 압현 | 96.81%, 90,911 target-frame | 목표 부근 압현 자체는 대체로 가능 |
| 중지 rehearsal hold quality | 77.52%, gate 80% | 직접 확인되는 숙달 병목 |
| 중지 rehearsal acquired / full-hold frame | 84.97% / 70.40% | 짧은 접촉·늦은 획득·재획득을 구분해야 함 |
| 중지 rehearsal dropout | 0.112% | 획득 전 실패는 이 지표에 잡히지 않음 |
| 중지 next 접근 증거 | 330 target-frame | 오프라인 창에서 1,024 미달; runtime 누적 창과 별도 |
| 중지 full-song 학습 표본 | 압현 93.94%, hold quality 50.08% | 독립 전체곡 평가가 아니며 rehearsal과 시간 분모가 다름 |

중지 rehearsal hold는 18,000~20,000 구간 약 79.24%에서 위 창의 77.52%로 정체됐다.
따라서 단순 추가 학습의 근거는 약하다. 반면 hold 부족이 전부 접촉 유지 실패라는 결론도 아직 이르다.
PPO early-stop은 minibatch 갱신 제한이며 학습 프로세스 종료와 구분한다.

### 이전 시도에서 얻은 제약

- FRET-017: 학습 평균 F1과 무보조 전체곡 평가가 크게 달랐다. 이번 checkpoint도 독립 평가가 필요하다.
- FRET-018~020: 평균/샘플 행동 변경, 준비 시간 증가, q·EMA 복원만으로 중지 실패를 해결하지 못했다.
- FRET-022: 전체 상태 복원으로 안정 압현한 표본은 확보했다. 모든 cache가 안정하다는 증거는 아니다.
- FRET-023: recovery 뒤 mastery 보존·재검증을 구현했다. 효과 판정은 recovery 경계의 상태 로그로 한다.

## 3. 완료한 구조 수정과 남은 검증

- [x] recovery 완료 시 mastery 보존 계약 구현
- [x] 보존·회귀·재집중 회귀 테스트 추가
- [x] 짧은 중첩의 분류 경로 확인: 기존 transient 경로 사용
- [x] 손가락·문맥별 hold 획득 진단 추가
- [x] 관련 CPU 테스트 실행
- [x] 복구 후 재검증·포커스 누락에 대한 1차 검수 지적 반영
- [x] 최종 변경 검수
- [ ] 후속 run의 recovery 진입·종료 전후 mastery/verified/fail-streak 추적
- [ ] 학습 정체 해소와 무보조 전체곡 성능 개선 확인

기존 구현의 완료 기준:

1. mixed recovery 전 `mastered=True`였던 손가락은 recovery 완료 뒤 유지된다.
2. 미숙련 손가락의 streak를 다시 수집하고, 보존 손가락도 새 evidence로 재검증한다.
3. 보존된 손가락도 retention 기준을 연속 위반하면 기존처럼 해제된다.
4. 기존 goal-pair phase, sampler, checkpoint 복원 검사가 통과한다.

## 4. 1순위: 실패 위치를 이벤트 단위로 분해

기존 rollout의 `.events.json`과 trace를 먼저 활용한다. 없는 필드만 추가하고 별도 진단 환경은 만들지 않는다.
기록 경로는 해당 run의 `evaluations/`와 `videos/`이며, 비교 결과는 실험 이력에 연결한다.

각 **compiled goal의 연속 유효 PRESS 구간**에 다음을 기록한다.
raw 음표 길이만 사용하지 않는다. 같은 줄 높은 fret 우선, 역할·손가락 변경, 짧은 중첩을 반영한다.

| 필드 | 의미 |
|---|---|
| source event / finger / string / fret | 원곡 및 운지 목표에 연결되는 식별자 |
| start / end / t_press / 연결된 t_strike | 실제 goal 구간과 음악 deadline; 없는 strike는 미제공으로 표시 |
| first_correct / acquired / full_hold | 첫 성공, 연속 6 frame 획득, 연속 12 frame 도달 시각 |
| acquisition_delay / pre-deadline correctness | 눌렀지만 늦었는지 판정 |
| longest_streak / correct_frames / target_frames | 연속 유지와 단순 frame 성공을 분리 |
| interruption_after_acquisition | 획득 뒤 해제·재획득 횟수 |
| lateral / depth / effective fret / wrong press | 옆줄 정렬·깊이·음높이·오압현 실패 분해 |
| initial pose / cache / teacher / action assist | 학습 성공이 보조 조건에 의존했는지 확인 |
| completed / terminated / censored | 조기 종료나 관측 종료로 못 본 이벤트를 성공 분모와 구분 |

준비 60 frame도 별도 진단한다. 이 구간은 goal clock이 멈추고 보상은 작동하지만 공식 곡 지표에서는 제외된다.
`hold_acquired`는 한 번 획득한 뒤 유지되는 latch라 현재 접촉을 보장하지 않는다.
`dropout`은 획득 후 실패만 센다. **획득 실패·지연과 유지 실패를 별도 비율로 표시한다.**

표시 형식은 `성공 이벤트 n/N`, `올바른 target-frame n/N`, `시도 episode 수`를 분리한다.
frame을 독립 시도처럼 해석하지 않고 event·seed·reset 조건별 결과도 보존한다.
rehearsal/pair의 마지막 30 frame 집계와 sequence/full-song의 전체 시간 집계는 직접 비교하지 않는다.
시작한 이벤트는 조기 종료돼도 분모에 남기고 실패/미완료로 표시한다.
아직 시작하지 못한 후속 이벤트는 미관측 비율로 별도 보고하며, 곡 단위에서는 미완주로 처리한다.
조기 종료로 어려운 이벤트를 평가에서 빼 성공률이 올라가지 않도록 한다.

검증: 알려진 성공/미획득/늦은 획득/획득 후 이탈/목표 변경/조기 종료 trace에 대해
각 counter와 분모를 CPU 테스트로 확인한다. 기존 reward·gate 결과는 바뀌지 않아야 한다.

## 5. 2순위: hold와 goal 시간의 계약 검증

### A. 점수의 상한을 먼저 계산

현재 `update_press_hold_state()`는 6 frame부터 hold quality가 올라가고 12 frame에서 1이 된다.
완벽하게 첫 frame부터 누르는 16-frame 새 목표도 **warm-start 없는 평균 quality는 0.5**다.
반면 rehearsal은 준비 중 같은 첫 목표를 미리 누를 수 있으므로 이 상한을 그대로 적용할 수 없다.

각 실제 평가 창에 두 oracle을 넣어 점수 상한을 계산한다.

1. 준비 중부터 가능한 목표를 계속 누르는 이상적 trace.
2. 목표 시작에서만 누르기 시작하는 cold-start trace.

이는 점수·goal 시간의 산술 검사이지 물리적으로 가능한 손 자세의 증명이 아니다.
80% gate가 oracle로도 불가능한 표본이 있는지, 짧은 중첩에 12-frame 정적 조건을 잘못 적용하는지 확인한다.
문제가 확인될 때만 평가 eligibility/시간 정규화를 고친다. 실제 압현 성공·음악 deadline은 완화하지 않는다.
Synchronizer readiness의 최소 1-frame 확인과 학습용 6/12-frame 유지 점수는 목적이 다르므로 통일하지 않는다.

### B. 설계와 실행 판정을 맞춘다

[설계 정본](</media/ajou/새 볼륨1/Guitar/master_plan_20261019_archived_20261027/03_fret.md>)의 다음 사항을 실제 reward/readiness와 대조한다.

- 고정 pad marker 설계와 현재 접촉 후보 선택 방식.
- string 영역의 중점 경계와 lateral 성공 폭.
- 음악적 effective sounding fret 판정과 지정 손가락 성공 판정의 관계.
- fret 내부 10~90%의 균일 위치 점수와 접근용 20% 목표의 서로 다른 역할.
- 이벤트 lookahead, t_press, sustain, 다음 낮은 fret/개방현 전환의 시간 정합성.

불일치는 `현재 동작 / 승인 설계 / 영향 / 최소 수정 / 테스트`로 남긴다.
pad나 손가락 판정 교체는 reward·cache·checkpoint 의미까지 바꿀 수 있으므로 결과 확인 후 별도 변경한다.

검증: wire 경계·인접 줄 중점·다중 fret 우선순위·대체 손가락·짧은 lead를 포함한
합성 physics snapshot 테스트. 판정을 바꾸면 reward, readiness, overlay가 같은 결과를 소비해야 한다.

## 6. 3순위: 고정 checkpoint의 독립 평가

- 완전히 저장된 checkpoint 하나를 고정하고 hash, 코드 계약, goal hash, 설정을 기록한다.
- 기본 자세·frame 0·저장된 준비 시간, teacher/cache/action assist 없는 전체곡을 평가한다.
- `mean`과 `sample`, seed 42/43/44를 분리한다. 평가 중 weight는 갱신하지 않는다.
- 여섯 전체곡 결과는 재현성 검사다. 이벤트가 적으므로 이것만으로 통계적 개선을 확정하지 않는다.
- 실패 이벤트는 원곡 prefix부터 추가 재생한다. 유지 가능성은 검증된 전체 상태 cache 복원으로
  별도 조사하고, cache 결과를 무보조 전체곡 성공으로 합치지 않는다.
- q/qdot/root/PD/EMA를 복원해도 PhysX 내부 solver 상태까지 동일하다고 가정하지 않는다.

대조는 원본 checkpoint 계약을 보존한다. runtime 의미를 바꾼 경우 원본 평가와 migration 실험을
별도 run으로 나누고 호환 검사를 우회하지 않는다.

## 7. 진단 결과에 따른 구현 분기

| 확인된 원인 | 우선 수정 | 수정하지 않을 것 |
|---|---|---|
| oracle 상한이 gate보다 낮음 | 해당 시간 창의 eligibility/유지 평가 보정 | 전체 hold gate 일괄 인하 |
| 늦게 획득, 이후 유지 가능 | 실패 incoming 전환의 실제 prefix·deadline 표본 강화 | 정적 단일 손가락만 반복 |
| 획득 뒤 반복 이탈 | 검증된 안정 상태에서 원곡 전환 유지 연습, 필요한 hold 항만 조정 | q-only RSI 확대 |
| lateral/depth 판정 불일치 | 판정 계약과 geometry 단위검사부터 수정 | 먼저 오압현 penalty만 강화 |
| 학습은 성공, 무보조 평가 실패 | 보조 유무·reset 조건 차이를 하나씩 대조하고 의존 조건 축소 | 더 긴 준비 시간만 추가 |
| 완료 window에서도 evidence 부족 | incoming/event 표집 coverage 최소량 보장 | 증거 없는 mastery 승격 |

표집 변경은 기존 균형 sampler를 활용한다. 네 손가락 보존 표본을 유지하고
`배정 episode 비율`과 `실제 target-frame 노출 비율`을 함께 확인한다.
recovery 진입 직후 일시적 evidence 부족과 완결된 window의 지속 부족을 구분한다.

현재 recovery 표본의 기본 비율은 **sequence 40%, rehearsal 36%, pair 24%**다.
코드는 sequence를 먼저 40% 선택하고, 나머지 60% 중 60%를 rehearsal로 선택한다.
full-song은 sequence 중 10%, 즉 전체 배정의 기대 4%다. 로그의 실제 episode 배정으로 검증한다.
focus와 완료 시간 차이 때문에 이 비율이 손가락별 frame 노출과 같지는 않다.

## 8. 수정 위치와 검증 책임

| 파일 | 필요한 경우의 작업 | 검증 |
|---|---|---|
| `tab2body/env/goals.py` | 유효 PRESS 구간·prefix/전환 표집 coverage | 원곡 시간·KEEP/MOVE/REST·분포·RNG 복원 |
| `tab2body/env/rewards/fret.py` | hold/depth/lateral 판정 또는 최소 보상 수정 | 경계값·짧은 목표·획득/이탈 trace |
| `tab2body/env/tasks/task_fret.py` | physics 판정 노출·준비/공식 지표 분리 | 실제 step/reset에서 counter 재현 |
| `tab2body/learning/curriculum.py` | eligibility/evidence 또는 recovery 상태 문제 | mastery 보존·새 증거 재검증·회귀 해제 |
| `tab2body/tools/record_fret_rollout.py`와 기존 event 집계 | 부족한 이벤트 진단만 확장 | mean/sample·초기 상태·종료 이벤트 분모 |
| `tab2body/tools/diagnose_fret_goal_pair.py` | 동일 regime·run 설정 기반 진단 | runtime gate와 보고서 일치 |

기존 `test_fret_curriculum_windows.py`, `test_fret_goal_pair_diagnosis.py`,
`test_fret_rollout_contract.py` 등을 먼저 활용하고 새 사례만 추가한다.
코드 변경 뒤 CPU 회귀 → 소수 환경 GPU smoke → 별도 change-reviewer 검수 순서로 확인한다.
이번 문서 보완은 이 구현들을 완료했다는 뜻이 아니다.

## 9. 대조 실험과 장기 학습 진입 조건

1. 같은 checkpoint와 seed에서 A=기존 코드, B=원인 하나만 고친 코드로 시작한다.
   PPO·환경 수·goal·준비 시간은 동일하게 두고 별도 run과 manifest에 변경을 기록한다.
   optimizer·관측 정규화·cache·curriculum·sampler RNG의 복원 차이도 기록한다.
   migration이 상태를 초기화하면 그 차이를 실험 변수로 명시하고 완전히 동일한 재개라고 부르지 않는다.
2. 우선 2,000 iteration, 필요하면 최대 5,000까지 실행한다. 500 단위 checkpoint를 같은 고정 평가로 비교한다.
   표집 변경과 reward 변경을 동시에 넣지 않는다. seed 42 파일럿에서 개선되면 43/44로 확인한다.
3. 평가·gate만 고친 경우 점수 상승을 모션 개선으로 해석하지 않는다.
   원래 trace의 deadline correct press와 sustain 결과를 함께 비교한다.

아래는 **파일럿 채택 기준**이며 현재 curriculum gate를 대체하거나 자동 승격시키지 않는다.
평가 전 baseline과 평가 event 목록을 고정한다.

- 실패 이벤트를 재현하는 고정 조건에서 deadline 성공 또는 sustain 이벤트 성공이 10%p 이상 개선.
- 개선한 항목 이외의 deadline/sustain 이벤트 성공률 하락은 2%p 이내.
- acquisition delay는 미획득 비율과 함께 제시; 성공 사례만 빨라진 결과를 개선으로 보지 않음.
- 기존 숙련 손가락의 이벤트 성공률 하락은 5%p 이내, 전체 F1 하락은 0.02 이내.
- 오압현률 증가는 0.5%p 이내, 비정상 종료·nonfinite 증가 없음.
- 목표당 최소 32 시도를 확보하고 seed별 n/N과 완료·조기 종료·미관측 횟수를 표시.
  성공률 분모는 사전 고정하고 동일 goal 반복의 상관과 작은 원곡 event 수를 명시.
- 두 연속 1,000-iteration 구간에서 진단 지표·고정 평가 모두 개선이 없으면 장기 연장하지 않고 원인을 다시 분류.

마지막 기준은 실험 판단 지침이지 이번에 구현한 자동 종료 기능이 아니다.
GPU 진단 또는 병렬 학습은 진행 중인 사용자 학습과 자원 충돌 여부를 확인하고 시작한다.
위 조건과 mastery 재검증이 충족되면 10,000~20,000 추가 학습을 검토한다.
전체곡 평가가 개선되지 않는다면 stage 이름이 바뀌어도 성공 실험으로 채택하지 않는다.

## 10. 실행 체크리스트

- [x] 최신 병목·기존 실패 시도·계획과 구현 상태 구분
- [ ] 1단계: 기존 trace 확인, 누락 진단 필드만 추가 → counter/분모 검사
- [ ] 2단계: 실제 평가 창 oracle와 설계/구현 대조 → 불일치 목록 확정
- [ ] 3단계: 고정 checkpoint 무보조 전체곡·실패 prefix 평가 → 원인 분류
- [ ] 4단계: 해당 원인 하나만 수정 → CPU/GPU smoke·변경 검수
- [ ] 5단계: 2,000~5,000 paired 실험 → seed별 n/N·deadline/sustain 비교
- [ ] 6단계: 채택 기준 통과 시 장기 학습, 아니면 실험 이력에 실패와 다음 판단 기록

매 실험은 `문제 / 가설 / 기존 시도와의 차이 / 실제 변경 / 비교 조건 / n/N / 결과 / 다음 판단`을
실험 이력에 추가한다. 실패한 접근의 재시도는 새 근거 또는 달라진 조건을 먼저 설명한다.
