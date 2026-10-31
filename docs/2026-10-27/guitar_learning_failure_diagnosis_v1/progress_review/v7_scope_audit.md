# V7 완료 시점 원목표 범위 감사

**원목표는 아직 미완료다.** 제어 전달·엄지 안내면의 기능 교정·보상 산술·실행/영상 검수는 상당히 증명됐다. 현재 검지4축·고정 기타·3음·seed7의 V7 결과를 네 손가락 학습, 자유 기타/J33 또는 원67음의 개선으로 확대할 수 없다. 이 감사는 기존 자료의 읽기 대조이며 새 GPU·NN·학습·체크포인트 로딩을 하지 않았다.

범위 기준: [plan](../../../plans/guitar_learning_failure_diagnosis_20261027.md) · [status](../status.json) · [readme](../README.md). 입력 경로와 SHA는 동반 JSON에 기록했다. 보고서·독립 검수 범위에 근거한 판정이며, 모든 과거 raw를 새로 재계산한 감사는 아니다.

분류는 proved(명시 범위 증명), incomplete(필수 하위요건 잔여), weak(관찰은 있으나 일반 주장에 부족), missing(정확한 요구 범위 증거 없음)이다. missing은 불가능을 의미하지 않는다. {'proved': 5, 'incomplete': 9, 'missing': 4, 'weak': 1}의 항목 수를 진척률로 환산하지 않는다.

| ID | 원계획 요구 | 분류 | 확인된 증거와 남은 범위 |
|---|---|---|---|
| R00 | 원자료·소스·계약·분모·종료 및 독립 검수 보존 | proved | 기준 실행과 실패·중단 자료를 보존하고, 최신 V7은 원672 core 입력/후기903SHA 및 영상714SHA 검수에서 원128환경·384음과 모델/종료를 대조했다. **잔여:** 이 감사가 모든 과거 raw를 다시 실행·해시 검증한 것은 아니다. 각 독립 검수의 명시적 범위에 한정한다. ([plan](../../../plans/guitar_learning_failure_diagnosis_20261027.md), [status](../status.json), [v7_review](../05_verified_fixes/index_reward_value_warmup_v7/REVIEW_ACTUAL_FINAL.md), [video](../05_verified_fixes/index_reward_value_warmup_v7/video/REVIEW_ACTUAL.md)) |
| R01 | LH21 명령→목표→실제각, 반전·B·범위·속도 전달 검사 | proved | 고정 기타 양모드 각84행 추종 창 모두 p95≤10°, B 손가락 검사 각각336/336. 지속0.05 요청의 누적/위치 의미 차이도 분리했다. **잔여:** 이 수치는 무접촉 인증·모터 토크 측정·자유 기타 안정성·학습 우열 증거가 아니다. ([control](../01_control/fixed/RESULTS.md), [status](../status.json)) |
| R02 | 기타 자유 상태에서 제어·B 동작과 지지 안정성 | incomplete | 자유 제어 행렬도 실행했고, 고정/자유 차이를 관측했다. **잔여:** 자유 조건 물리 실패가 incremental54/84·position40/84였다. 고정 기타의 성공을 자유/J33 안정성으로 옮길 수 없다. ([control](../01_control/fixed/RESULTS.md), [status](../status.json), [thumb](../05_verified_fixes/thumb_rear_surface_v3/RESULTS.md)) |
| R03 | 접촉·보상 원장 산술과 할인/PBRS 해석 | proved | 8개 시간표 핵심5항 산술, 실제 시계의9항 및 정산·원128분모·실패 비용을 검산했다. 보상 합과 무가중 달성 수를 구분한다. **잔여:** 산술 검증은 실제 도달 가능성이나 모든 negative 판정의 물리 타당성을 보증하지 않는다. ([reward](../04_ablation/reward_objective_audit/README.md), [live_release](../02_contact_reward/live_release_probe/analysis_01/RESULTS.md), [negative](../02_contact_reward/facing_direction_probe/analysis_01/RESULTS.md), [v7_review](../05_verified_fixes/index_reward_value_warmup_v7/REVIEW_ACTUAL_FINAL.md)) |
| R04 | 24개 사전선정 대표 목표 및 각 손가락 실제 positive | incomplete | 원24목표 선정과 실제 시계 실험이 있고, 이후 비엄지0.25Nm·고정 기타·유한 teacher 조건에서는 네 손가락 각각4/4 positive를 확보했다. **잔여:** 현재 대표24목표 전체 성공은 아니다(초기 실제시계6/24). 후보112/114/121은 후보 식별자이며 원곡 source index로 읽으면 안 된다. 네4/4는 별도 scripted 조건이지 동시 학습이 아니다. ([status](../status.json), [readme](../README.md), [other](../03_short_learning/other_finger_precheck_v3/analysis/RESULTS.md), [pinky](../05_verified_fixes/low_effort_pinky_oracle_v1/reproduction_v1/analysis/results_v1/RESULTS.md)) |
| R05 | 실제 loaded back-facing negative의 판정 타당성 | missing | 2479개 정적 대조 불일치0과 8조건×2의 실제 유한 방향 시험을 수행했다. **잔여:** 요구한 same-sample position=true/facing=false/loaded witness와 연속50ms witness는0/16. ±90° 요청도 실제 목표 방향에 도달하지 못했으므로 negative 확보나 불가능 증명으로 볼 수 없다. ([negative](../02_contact_reward/facing_direction_probe/analysis_01/RESULTS.md), [status](../status.json)) |
| R06 | 짧은 접촉·실제 해제 등 다른 물리 negative | incomplete | 실제128시도에서 short-only17개와 안정 해제≥50ms95개를 확보하고9항/240Hz 원장을 검산했다. **잔여:** 각 손가락의 대응 negative 전부와 대표 목표 전역을 충족한 것은 아니다. 같은 snapshot의 정적 판정과 실제 연속 episode를 합쳐 완료로 세면 안 된다. ([live_release](../02_contact_reward/live_release_probe/analysis_01/RESULTS.md), [negative](../02_contact_reward/facing_direction_probe/analysis_01/RESULTS.md), [status](../status.json)) |
| R07 | 엄지 후면 도달·접촉·유지·재접촉 기능 | proved | 실제 face 참조 정점 기반 안내면 수정 후 고정 조건 접촉/유지/해제/재접촉 프로토콜을 통과했다. 안정 유지 약2.4N, 재접근 최대11.225N을 분리했다. **잔여:** 옛 thumb_contact 키의0N은 이 수정 전 제한 실험 이력이다. 이를 현재 엄지 접촉 증거가 전혀 없다는 뜻으로 읽으면 안 된다. ([thumb](../05_verified_fixes/thumb_rear_surface_v3/RESULTS.md), [thumb_review](../05_verified_fixes/thumb_rear_surface_v3/review_native.json)) |
| R08 | 실제 엄지 부하와 자유 기타 해제·과부하 | incomplete | 자유 엄지 접촉/유지/재접촉도 관측됐고, 기존 전체128 하중관찰에서 엄지 합력 p50 약84.11N 등 과부하를 수치화했다. **잔여:** 자유 엄지 해제 후보11.39%가 원기준<10%에 미달했다. 몸체 합력/법선 성분은 접촉쌍 압력·현 압력·모터 토크가 아니며 학습 중 적절한 엄지 하중/자연스러움이 해결되지 않았다. ([thumb](../05_verified_fixes/thumb_rear_surface_v3/RESULTS.md), [loads](../05_verified_fixes/contact_load_probe/analysis/results_v1/RESULTS.md), [status](../status.json)) |
| R09 | incremental/position 공정한 짧은 학습 비교 | incomplete | 기존 소스에서 양모드 seed7/17·300회·고정 평가 비교는 끝났고, 어느 조건도 인접2회 수용 기준을 통과하지 못했다. **잔여:** 그 결과는 이후 wrist/effort/557/V2목표 교정을 반영한 현재 양모드 비교가 아니다. 같은 수치 std를 물리 탐색 크기 동일성으로 간주할 수 없다. ([status](../status.json), [control](../01_control/fixed/RESULTS.md), [gamma](../04_ablation/time_credit_ablation/corrected_source_v3/comparison_gamma_seed7/RESULTS.md)) |
| R10 | 다른 손가락에서도 실제 짧은 RL·원장·해제 성립 | incomplete | 중지와 검지의 실제 짧은 학습·퇴행/안정 사례가 있고, 네 손가락의 scripted positive가 있다. 검지 단음 B는 seed7에서50~300 모두128/128이었다. **잔여:** 현재 공통 계약의 약지/소지 RL와 반복 해제·2~4음 성공은 없다. 과거 소지 zero4/4는 팔 지원만으로 달성된 confound여서 학습 효과로 셀 수 없다. ([other](../03_short_learning/other_finger_precheck_v3/analysis/RESULTS.md), [pinky](../05_verified_fixes/low_effort_pinky_oracle_v1/reproduction_v1/analysis/results_v1/RESULTS.md), [index_single](../05_verified_fixes/low_effort_index_zero_cost_init_v1/analysis/results_v1/RESULTS.md), [status](../status.json)) |
| R11 | seed7/17 선별 및 seed27 확인·현재 결과 재현성 | incomplete | 과거 양모드7/17 및 중지 비용head B seed17 재현을 수행했고 실패도 보존했다. **잔여:** 현재 저힘·검지 단음 안정 결과와 V4~V7 세음은 주로 seed7이다. 중지 B seed17도 연속 기준 재현에 실패했고 seed27 확인 증거가 없다. 128환경은128seed가 아니다. ([status](../status.json), [seed17](../04_ablation/time_credit_ablation/corrected_source_v3/replication_cost_head_seed17/analysis/RESULTS.md), [index_single](../05_verified_fixes/low_effort_index_zero_cost_init_v1/analysis/results_v1/RESULTS.md), [v7_review](../05_verified_fixes/index_reward_value_warmup_v7/REVIEW_ACTUAL_FINAL.md)) |
| R12 | 반복 접근/유지/해제 및2~4음 NN 전환 | incomplete | V2 noNN 세음은124/128·A해제128/128로 지정 gate를 통과했다. V7은 실제 actorfit+valuewarmup+PPO300과 전평가를 수행했다. **잔여:** V7 마지막 결정론 A/B7/B8=110/18/19,all3=13,joint=5; 확률60/100/100,all3=58,joint=30이다. 원 기준 미달·생산 미채택이며 noNN 성과를 NN/해제 결합 성공으로 상속할 수 없다. ([v2](../05_verified_fixes/index_release_close_lead_v2/runs/candidate/evaluation.json), [v7](../05_verified_fixes/index_reward_value_warmup_v7/analysis/results/RESULTS.md), [v7_review](../05_verified_fixes/index_reward_value_warmup_v7/REVIEW_ACTUAL_FINAL.md)) |
| R13 | 보상·할인·실패 비용·critic 변경의 원인 분리 | incomplete | gamma-only, 비용head0, A정산 유보, reward-value warmup을 각 범위에서 독립 비교했다. V7 holdout MSE0.317608→0.026550와 초기 배우/RNG 불변도 확인됐다. **잔여:** 좋아진 가치오차가 안정 압현·해제나 원전곡 개선을 보장하지 않았다. 같은 scene holdout/단일seed/고정3음이며 현행 생산 채택 근거가 아니다. ([gamma](../04_ablation/time_credit_ablation/corrected_source_v3/comparison_gamma_seed7/RESULTS.md), [status](../status.json), [v7_review](../05_verified_fixes/index_reward_value_warmup_v7/REVIEW_ACTUAL_FINAL.md)) |
| R14 | 손가락별 수행 기반 악구→전곡 전환 및 고정 holdout | missing | 현행 코드에는 planned_transitions//4 기준 full_song_after 계약이 명시돼 있다. **잔여:** 원계획의 수행/실패 기반 전환, 다양한 악구 및 독립 최종holdout에 대한 구현·채택 비교 증거가 없다. ([plan](../../../plans/guitar_learning_failure_diagnosis_20261027.md), [launch](../../../../guitar_learning/training/launch.py), [environment](../../../../guitar_learning/gpu/finger_skill_environment.py), [status](../status.json)) |
| R15 | 자유 기타·팔/손목 공동 J33의 짧은 악구 복구 | missing | 자유 기타 제어/엄지 진단 자료는 있으나 현재 V7 수행은 고정 기타·선택 검지4축·유한 지원 조건이다. **잔여:** 모든 J33 정책 축 공동제어에서 자유 기타 악구가 원 기준을 통과한 증거는 없다. ([plan](../../../plans/guitar_learning_failure_diagnosis_20261027.md), [status](../status.json), [v7_review](../05_verified_fixes/index_reward_value_warmup_v7/REVIEW_ACTUAL_FINAL.md), [video](../05_verified_fixes/index_reward_value_warmup_v7/video/REVIEW_ACTUAL.md)) |
| R16 | 원곡67음·128환경·여러 seed의 개선 평가와 최종 채택 | missing | 원래 전곡 실패의 기준 자료와 원67목표는 보존돼 있다. **잔여:** 교정 후 원67음/free/J33/여러seed가 완료됐다는 증거가 없다. 원목표가 파일에 남는 것과 실제67음 정책평가는 다르다. ([plan](../../../plans/guitar_learning_failure_diagnosis_20261027.md), [status](../status.json), [v7_review](../05_verified_fixes/index_reward_value_warmup_v7/REVIEW_ACTUAL_FINAL.md), [readme](../README.md)) |
| R17 | 실제 영상·문서·독립 검수 | proved | V7 마지막300의 손/전신 각177frame·5.9초 영상, 원128원장/NN/물리 trace 동등성·전체decode·12프레임QA가 독립PASS다. 실패 영상도 그대로 제공했다. **잔여:** 완료 범위는 현재 진단 조건의 문서화다. 자유 J33/원67음 최종 성공 영상은 별도 미완료다. ([video](../05_verified_fixes/index_reward_value_warmup_v7/video/REVIEW_ACTUAL.md), [v7_review](../05_verified_fixes/index_reward_value_warmup_v7/REVIEW_ACTUAL_FINAL.md), [readme](../README.md), [status](../status.json)) |
| R18 | 극단 마디 분담·B/엄지 권고·자연스러움 | weak | 목표-실제 오차·PIP/DIP 분담·관절 한계·지지/손가락 기여를 관찰하고 DIP 개입의 국소 변화도 확인했다. **잔여:** 일부 자세 변화와 낮은 합력이 전손 자연스러움/안전한 접촉/자유 기타 품질의 검증은 아니다. 동작 비용0·native범위·B권고 원칙은 유지해야 한다. ([readme](../README.md), [loads](../05_verified_fixes/contact_load_probe/analysis/results_v1/RESULTS.md), [thumb](../05_verified_fixes/thumb_rear_surface_v3/RESULTS.md), [status](../status.json)) |

## 범위 해석에서 특히 주의할 점

- 엄지 접촉은 missing이 아니다. 수정된 후면 안내의 실제 접촉/유지/해제/재접촉은 고정 조건에서 증명됐다. 남은 것은 자유 조건 해제와 학습 시 부하/간섭이며, 옛0N 키를 현재 결론으로 읽으면 안 된다.
- 네 손가락 positive가 각각 있어도 약지/소지의 실제 RL이 끝난 것은 아니다. 특히 과거 소지 zero4/4는 선택 손가락 학습을 증명하기 어려운 대조였다.
- 중지 양모드 seed7/17, 중지 비용head seed17 등 과거 seed 비교는 실제로 수행됐다. 그러나 현재 저힘 검지 안정 단음과 V4~V7에 대한 seed17/27 일반화는 남았다.
- V7 가치 holdout MSE 개선0.317608→0.026550는 검증됐지만 마지막 평균행동의 B7/B8 달성18/19와 all3=13은 초기 all3=98보다 후퇴했다. 확률 all3=58/joint30의 개선은 관측된 좁은 증거이며 원 수용기준/생산 채택을 뜻하지 않는다.
- 원계획은 손가락별 달성80%·clean70%·wrong10%·실패5%와 연속2평가를 요구했다. 이후 세음 진단의 더 엄격한 gate와 혼동하지 않는다. 현재 마지막 B 달성은 원래80%에도 못 미친다.
- 기존 자유 제어/엄지 실험이나 원전곡 실패 기준은 존재한다. missing인 것은 교정 후 자유 J33 악구 및 개선된 원67음/여러seed의 최종 검증이다.

## 다음 독립 작업의 권고 순서

현재 root가 계획 중인 고정모델 평균/잡음·B 오압현 출처 감사는 좁은 원인 분리로 유지할 가치가 있다. 다만 그 성공을 기다려야만 다른 범위를 준비할 이유는 없다. 특히 확률 성공률90%를 새 확장 준비의 진입 조건으로 추가하지 않는다. 아래 CPU 준비 작업은 병행할 수 있고, 이후 native는 root가 기존 순서와 승인 범위 안에서 직렬로 수행한다.

### 1. 현재 계약의 네 손가락 evidence/target manifest를 CPU로 먼저 정리

새 물리/학습을 시작하지 않고 fullscope 누락을 가장 직접 줄이며, V7의 선택 검지·3음에 종속되지 않는다.

- 산출물: 원24목표와 네 scripted positive 후보를 원target id/source index/현행557계약/PD·effort/teacher/zero/random·물리negative·seed에 매핑한 표. 과거와 현행 호환/재검증 필요를 명시.
- 검증: 후보112/114/121을 source index로 혼동하지 않음; 각손가락 ≥1 재현가능positive와 대응negative 유무/실패분모/선정사유 명시; 소지zero4/4 confound를 표시.
- 범위: 새 NN/학습 없음. 과거 checkpoint strict load를 우회하지 않음.

### 2. loaded-facing negative와 엄지 free/부하를 독립 검증 패키지로 준비

원계획 단계2의 실제 미충족 요건이고, 다른 손가락/자유 악구 확장에서도 판정 신뢰성과 지지 안정성에 필요하다.

- 산출물: 기존 원시자료 coverage 재집계 후 누락 조건만 사전선정한 유한 접근 프로토콜. position/facing/load/candidate/clean/시간·보상을 동일표본으로 연결. 엄지는 수정면 기준 scripted 대조와 free 해제/학습 부하를 분리.
- 검증: loaded back-facing ≥50ms 실제witness 또는 도달미해결로정직하게종결; 실패시점이후제외; 고정/자유 해제 원기준유지; 실제 native pose 사용(MCP q-only FK 오차를 피부접촉 증거로 쓰지 않음).
- 범위: root만 사후 승인된 native를GPU직렬실행. 문턱/가동범위/PD 완화·매tick상태주입·압력인증 주장 없음.

### 3. 검증된 다른 손가락 한 목표와 현재 단음의 seed 재현

검지 세음 tweak만 반복하는 대신 범위 일반성과 학습/지원 confound를 분리한다.

- 산출물: 먼저 약지 후보(과거reference4/4 vszero1/4)를 현행 동일계약에서 확인; positive/negative 조건 충족 후 fresh large128/H32/300 및50간격 평가를 사전고정. 현재 안정 단음의seed17, 통과시27확인은 별도 단일비교.
- 검증: 원80%달성/70%clean/10%wrong/5%실패·연속2평가를 손가락별 적용. 본인압현·해제와zero필요성/지원상대운동을 구분. 최초조건·실패를분모에보존.
- 범위: V7확률90% 성공을 다른 분기 준비의 전제조건으로 추가하지 않음. positive 부재 손가락의 장기RL은 시작하지 않음. 추가손가락/seed grid 자동확장 없음.

### 4. J33/free-guitar와 수행 기반 전환의 CPU 계약을 별도 설계

현행 고정25% 전환과 선택4축 진단은 원래 최종학습 문제를 직접 검증하지 않는다.

- 산출물: 고정→자유/지원제어→J33를 분리하는 전환 표, actor33직접제어·teacher제거·새계약/fresh또는명시적actortransfer·optimizer/critic초기화·중력ON/strapOFF/유한Root하체 검증계획, 독립고정holdout readiness명세.
- 검증: 각단계물리/음악기준통과증거를다음단계로명시적으로연결; 손가락평균으로실패를가리지않음; 기준미달원본유지; 원67음을삭제하지않음.
- 범위: 지금 production 전환/정책이식/학습실행은 하지 않는다. 자유악구통과전 원67장기학습으로건너뛰지 않는다.

### 5. 자유 악구 통과 후 원67음 최종 평가

원목표 완료를 판정할 최종 증거이며, 진단 video 완료와 다르다.

- 산출물: 원67음·128환경·여러seed의 독립평가와 손/전신영상, 원baseline 대비 성과/실패/관절/엄지 부하 및 보상문서.
- 검증: 평가분모67×128와실패전부유지, 원목표어려운음보존, 학습용체크포인트선택과최종holdout분리, 독립검수.
- 범위: 앞단계미달시 미완료로유지하며 채택/예산확대자동화 없음.

## 완료를 선언할 때 필요한 최종 연결

각 손가락의 현행 물리 positive/negative → 해당 손가락의 안정 단음과 반복/전환 → 다른 seed 확인 → 자유 기타·지원 제거·J33 악구 → 다양한 악구/수행 기반 전환 → 원67음·여러seed 최종평가/영상의 연결이 필요하다. 현재는 앞부분의 조건별 증거가 쌓였고 뒷부분은 미완료다. 진단 실패를 숨기거나 기준을 낮추지 않은 점은 강점이며, 다음 목표는 검지 세음에서 증거 폭을 실제로 넓히는 것이다.

생성 당시 기존 입력 변경 감지: []. 이 감사는 위 두 파일만 새로 만들었으며 원계획·status·기존 소스/리뷰/보존 자료를 수정하지 않았다.
