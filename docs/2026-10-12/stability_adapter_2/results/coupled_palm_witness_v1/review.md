# Palm witness source 탐색 독립 검수

## 요약 판정

**문제없음.** 이번 source-only 실행 코드와 실제 저장 결과의 범위·수치·판정은 정합한다. Critical/Warning/Suggestion은 모두 없다. 이 판정은 실제 PD 보정 채택·새 초기자세 native trial의 검수나 성공을 뜻하지 않는다.

## 실행·보존 확인

- [계획](/home/ajou/yigyu/3/stability_adapter_2/COUPLED_PALM_WITNESS_PLAN.md:10)과 [producer](/home/ajou/yigyu/3/stability_adapter_2/search_coupled_palm_witness.py:88)의 변경은 현재 feasible palm/finite-patch witness의 local anchor화, 새18축 Jacobian, palm 우선·현재 finger-feature hold 목적이다. 기존 v3의 bounds·PD base·held63·전체 source pair·same-left110·finite-patch gate를 보존한다.
- 실행 전 검수 SHA와 실행 전후/current/source 복사본 SHA는 모두 `e959cc35bb7888d8580ae0e71599b743b189de6711198ca118ef6faa7a605f99`로 일치한다. AST 검사 통과. `search.json`의 선언 입력 SHA 불일치는0이다. 출력 SHA는 `5189ac81c20490e198376288fdf1ecdf09ced900f92ed85804122b84f5c3ee74`다.
- [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/search_execution.json:1)은 exit0, 약10.277초, native 초기화/physics0이다. 저장 log SHA `ba71426cddc2228b34446b24cda31c30d5962e225d2f9d276e6b9663c8139239`와 실제 파일이 맞고 `/tmp` 원 log와도 bytes가 같다. wrapper는 예상 SHA와 새 phase 미존재를 먼저 검사해 원본 source snapshot·wrapper·log를 실행 후 새 phase에 복사한다. 기존 상위 sealed phase는 수정하지 않는다.

## Witness·Jacobian·제어 범위

- 네 저장 시점의 source witness를 현재 palm pose로 역변환하고 zero-delta feature로 복원한 위치 차이는 최대 `1.15e−16m`다. 목표는 patch witness에서 palm 쪽으로0.1mm이며 현재 witness와 patch의 거리는 네 시점 모두0.1mm보다 크다. 접근 방향과 목표 offset 부호가 맞다.
- 저장18축 Jacobian을 다시 중앙차분해 exact 일치했다. h=0.0001/0.00005rad의 최대 차이는 `1.2467804567e−9`로 기준1e−6보다 작고 모든18열이 finite/nonzero다. 엄지/검지/중지의 목표 point와 normal은 현재 feature와 exact 동일하며 palm normal만 기존 source facet 방향에 대한 soft 선호다. 이는 새 witness의 실제 접촉 법선·해부학적 pad 인증이 아니다.
- 네 solve의 native/Aug19 한계, current actualq의 팔±0.05/hinge±0.10rad, 저장 original PD base의 한계와 초기q 기준 target offset±0.3rad 교집합을 독립 계산해 exact 일치했다. 네 solve는 선형 제약과 bounds에 feasible이며 optimizer success도 모두 참이다.
- 16행의 `fraction×dq`, actualq+delta, 원 control PD base+delta와 비선택63 target unchanged를 독립 대조했다. t0 base는 `preserved_absolute_targets_rad`다. 임시18축은 최종66 제어권을 제한하지 않는다. 같은 저장 G pose를 유지한 가상 인체 source 재배치이며 simulator state를 바꾸는 runtime 보정이 아니다.

## 전체 source 결과 재계산

- 네 snapshot의 offline source probe와 각 행의 delta mesh를 다시 구성했다. **16×2562=40,992개** pair LP를 독립 재계산해 저장 양의 교차 목록·공통구 반경·새 교차/반경 증가·blocking 판정과 일치했다. 각 행의 same-left LH/Wrist/Elbow graph>2 쌍은110개이며 native mask와 무관하게 모두 포함한다. Graph≤2 연결부만 진단으로 blocking에서 제외한다.
- 16×4body=64개 거리 certificate의 source-hull witness feasibility, patch witness 평면/내부 여부, witness 거리 상한과 support-plane 하한을 독립 확인했다. 저장값과 최대 차이는 `1.79e−13m`다. 전 행의 whole-palm 상한<baseline 하한 gate, anchor 목표오차 감소, upward proxy, actual/PD bounds와 최종 screen boolean을 다시 계산해 일치했다.

아래 값은 whole-palm–finite-patch 거리 **상한mm**이며 ✓만 source 방향 screen 통과다.

| 저장 시점(s) | fraction0 | fraction1 | fraction0.5 | fraction0.25 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 0.421670 | 0.109505 ✓ | 0.265551 ✓ | 0.343601 ✓ |
| 0.1 | 5.259589 | 0.000000019 | 2.694465 ✓ | 3.980326 ✓ |
| 0.5 | 9.994145 | 0.891303 | 5.452394 | 7.726163 |
| 5 | 8.912923 | 1.008573 | 4.944934 | 6.925270 ✓ |

- 통과는6행: t0의1/.5/.25, 0.1초의.5/.25, 5초의.25다. 7개 저장 check가 모두 참이다.
- t0 full은 기준 interval `[0.421669302, 0.421669522]mm`에서 `[0.109504651, 0.109504850]mm`로 접근한다. Anchor 목표오차는 `0.321669522 → 0.009761849mm`, 최대 선택 joint delta는 `0.002616480012rad`다. 이 행의 양의 source 교차20개는 모두 연결부 진단이며 비연결 source 교차0이다.
- 0.1초 full은 patch 거리만 거의0이지만 palm–G 및 middle3–fret4 교차 증가로 거절된다. 0.5초는 모든 제안에서 middle3–G 반경 증가 약0.079379/0.045612/0.020744mm가 남아 거절된다. 5초 full/half도 index3–G 증가로 거절된다. 거리 감소만으로 통과시키지 않는다.

## 후속 시험과의 경계

이번 결과는 기존 weighted 목적보다 여러 snapshot에서 접근 방향을 찾았다는 source 근거다. 네 시점 모두 통과하는 동일 보정량이나 연속5초 runtime 보정을 검증한 결과가 아니다. 일부 시점의 pass를 같은 delta의5초 지속 적용 근거로 삼지 않는 [계획:28](/home/ajou/yigyu/3/stability_adapter_2/COUPLED_PALM_WITNESS_PLAN.md:28)의 제한을 유지한다.

Root가 제안한 별도 초기자세 trial은 초기q selected18 변경과 기존33개 PD offset을 보존하는 기준 target shift를 명시하는 새 계약이 필요하다. 이 기록은 그 준비 코드·float32 q/target 조립·fresh native FK/source gate·1200step 실제 결과를 검수하거나 승인하지 않는다. 해당 검수는 별도 요청 범위다. 현재 모델은 측정 finger1 상대변환을 공급하는 조건부 모델이며 전역 finger FK·미래 PD 응답·cooked 접촉·지지력 인증이 아니다.

## 별도 초기자세 trial 준비 — 실행 전 검수

검수한 [준비 소스](/home/ajou/yigyu/3/stability_adapter_2/prepare_palm_witness_initial_trial.py:23)의 SHA는 `8dd8a914e319d52b9c07db06c19e39208f60b4ba757a671e67b42231b6bdc751`이며 AST 검사 통과다. 아직 준비 main/proposal/trial 생성은 하지 않았다. [새 leaf 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_WITNESS_INITIAL_TRIAL_PLAN.md:10)은 runtime 보정과 별도 초기자세·유지 목표 변경을 구분하며 기존 runner의 ‘same initialq’ 범위를 trial 내부 일관성으로 설명한다.

- [준비:38](/home/ajou/yigyu/3/stability_adapter_2/prepare_palm_witness_initial_trial.py:38)의 초기q float32와 target compose를 독립 계산했다. q와 PD target은 각각 정확히18개만 변하고 비선택63개는 exact 유지된다. 원 trial의33개 offset을 그대로 쓰면 기존 target이 exact 복원되며, 새 q 기준으로 합성한 target도 clipping 없이 한계를 충족한다. 원 trial은 기존 input closure에 포함되고 row SHA도 실제 파일과 같다.
- [준비:53](/home/ajou/yigyu/3/stability_adapter_2/prepare_palm_witness_initial_trial.py:53)의 손목±0.005rad 양끝은 이번 실제 입력에서 runner의 float64 offset→float32 compose와 exact 일치한다. 가장 가까운 native 손목 한계까지 약2.174rad, 기존 초기q 기준 ±0.3rad offset 경계까지 약0.2887rad 여유가 있다.
- Quantized18 delta로 expected source pose를 독립 구성해 검사했다. Human–G/cross-hands 교차0, native 허용 또는 same-left graph>2 self1188쌍의 교차0이다. Palm interval은 `[0.109512385, 0.109512592]mm`로 기준보다 작고 up proxy는0.956547127이다. 최대 실제 초기delta는 `0.002616494894rad`다. 이 수치는 가상 source 준비 검증이며 fresh native 결과가 아니다.
- 준비 소스는 기존 trial 복사본의18 초기각만 바꾸고 offset/G/LA/gain을 보존한다. 최소 proposal의 fields는 기존 runner가 읽는 admission·expected q/PD·LA·source_state·left33 계약과 맞는다. `source_support_search_passed=False`와 미검증 사유도 유지한다. 준비 source 실행을 막는 오류는 발견하지 않았다.

### Warning — fresh native self-screen 범위

[near_contact_initial_audit.py:26](/home/ajou/yigyu/3/stability_adapter_2/near_contact_initial_audit.py:26)의 fresh native self 검사는 LH/Wrist/Elbow graph>2만 열거한다. [준비:73](/home/ajou/yigyu/3/stability_adapter_2/prepare_palm_witness_initial_trial.py:73)의 전체 native-allowed graph>2 self 검사는 fresh native에서 반복하지 않는다. [runner:102](/home/ajou/yigyu/3/stability_adapter_2/run_small_wrist_recorded_diagnostic.py:102)은 해당 좁은 audit과 FK tolerance(위치0.1mm/회전0.001rad) 등을 통과하면1200step을 시작한다.

따라서 새 leaf의 ‘fresh source no-overlap’이 전체 native-allowed self까지 뜻한다면 원본을 보존한 새 runner/wrapper variant에서 동일 검사를 native step 이전 gate에 추가해야 한다. 기존 gate를 재사용한다면 leaf에 fresh self 검사의 범위가 LH로 제한된다는 점을 명시해야 한다. 이는 준비 main 실행의 blocker가 아니라 **actual 실행 계약의 범위 주의점**이며 root에 회신했다. 준비 소스 Critical0, actual gate 범위 Warning1이다.

## 준비·actual entrypoint 재검수 — Warning 해결

위 fresh self-screen Warning은 실행 전 새 [entrypoint](/home/ajou/yigyu/3/stability_adapter_2/run_palm_witness_initial_diagnostic.py:16)로 해결했다. SHA는 `2f6565f3e5bf79b682a5704fcbbaf5978ff925c53fd6a130a92f46e145bdd380`다. Frozen runner와 original audit는 수정하지 않고 process 내 audit hook만 확장한다.

- [entrypoint:18](/home/ajou/yigyu/3/stability_adapter_2/run_palm_witness_initial_diagnostic.py:18)은 실제 rigid-shape properties와 body shape spans로 body별 native filter를 읽고 reference 정책과 exact 일치를 gate에 포함한다. [entrypoint:32](/home/ajou/yigyu/3/stability_adapter_2/run_palm_witness_initial_diagnostic.py:32)은 실제 native pose의 source probe에서 전체 native-allowed 또는 same-left graph>2 self pair를 검사한다. Human–G/cross 재검사와 zero-step/readonly 확인도 기존 admission의 checks에 추가한다.
- Runner는 함수 안에서 admission을 import하므로 hook이 실제 호출되는 경로다. [runner:108](/home/ajou/yigyu/3/stability_adapter_2/run_small_wrist_recorded_diagnostic.py:108)이 추가 checks까지 모두 참인지 확인한 뒤 첫 step에 진입한다. 새 entrypoint의 `finally`가 예외 발생 시에도 원 audit hook을 복구한다. 새 state/target/filter setter나 physics writer는 없다. 이는 코드 경로 검수이며 fresh native 실행 성공을 미리 인증한 것이 아니다.
- 준비 소스는 소비 전에 새 entrypoint의 입력 SHA를 추가했다. 최종 준비 SHA는 `64f5dee86b55cdbf4fa58b2c5adbcfdd701e65aae954fec04e4ce2ba6ec857bf`이며 float32/offset/source 계산은 위 검수본과 같다. 새 wrapper의 예상 SHA도 이 값과 일치한다. 준비/entrypoint AST 검사 통과. **준비 실행 blocker 없음**, 이전 fresh-gate Warning은 해결됐다.

### 새 analyzer의 coverage 보완

초기 analyzer SHA `f08810fcdfa1a84bf2e85e85ef7f78c20743e3fad69e2a8bf4199414c13fd6ad`는 state 길이만 확인하고 trace/contact 전체 coverage를 확인하지 않아 일부 raw 행 누락을 최대/후기/장력/접촉 수치로 소비할 수 있었다. 소비 전 root에 Warning으로 회신했다.

최종 [analyzer:37](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_witness_initial.py:37)은 양조건 state/trace1201행, control/contact1200행, state/control/contact의 모든 step 번호와 trace의0~5초 정확한 time coverage를 검사하고 metrics 계산 전에 assert한다. 최종 SHA `afc4d4f44a4992ef41526843a9d258954fa925615945d777674fe07ca04e07b6`와 AST를 확인했다. 기존 LA−2mm 원자료로 새 coverage predicate가 전부 참임을 독립 확인해 이 Warning도 해결됐다.

Analyzer의10개 공통 조건·선택18 외 초기q/1200 target63개·original33 offset에 따른1200 target 재합성·동일 wrist clock/waveform·604 PNG SHA·body9 실제 scalar 변화/한계초과·모든 human–G 양의 raw lambda body별 step/first/last 계산 범위는 이번 비교와 맞는다. 현재 새 native 자료는 없으므로 analyzer main이나 수치 산출은 실행하지 않았다.

재검수 최종 판정은 **문제없음**, 미해결 Critical/Warning/Suggestion0이다. 준비 결과·fresh native 실제 gate 및1200step 결과는 root 실행 후 별도 원자료 대조 대상이다.

## 준비 실제 출력·actual wrapper 최종 대조

Root가 수행한 준비 session28032는 exit0, 약7.176초이며11개 check가 모두 참이다. 검수한 source SHA64f5…와 실행 전후/current/archive가 같고 source/wrapper/log 보존본도 일치한다. Proposal/preparation의 선언 입력 closure는11,455개이며 실제 파일 SHA 불일치0이다.

- 저장 proposal의81 float32 초기각,81 float32 PD 목표,18개 realized delta와81개 PD delta를 원 native 초기각·source t0 full delta·원33 offset에서 독립 재구성해 exact 일치했다. Q/target은 각각18개만 바뀌고 held63은 exact 유지된다. Trial의 선택18각을 원값으로 되돌리면 기존 trial과 전체 dict가 같다. 원33 offset·G 생성조건·LA·gain은 그대로다.
- Expected source_state의 body pose와81 DOF pos를 별도 CoupledSnapshot 합성으로 다시 구성해 전체 dict가 exact 일치했다. G body states는 원본과 같고 LA는 `1.0998469719600776m`다. 저장 quantized palm upper `0.10951259162877781mm`와 최대 realized delta `0.002616494894rad`도 앞선 독립 source 검수값과 맞는다.
- 최소 proposal에 frozen runner가 요구하는 trial SHA/path, admitted flag, expected q/PD·LA/source_state, alpha·left33·facets·regions·clearance가 모두 있다. 초기 설정 validation을 통과한다. `source_support_search_passed=False` 및 미검증 사유도 유지한다.
- Proposal SHA는 `c49d04dd3ed2c79a4b498c20bf11e377db3b2bc131baa008e147d14452f86ac6`, 새 trial SHA는 `e0bed188c8dcd6e7819a0d50e935140c5040e9ef057775cd83aed2429871eadd`다. Actual wrapper `/tmp/run_palm_witness_native.py`의 예상 entrypoint2f656…/frozen runner34d50… SHA와 실제 파일이 일치한다. 새 native 경로/실행 기록 미존재, trial SHA/checks guard와 source/wrapper 보존 경로도 맞고 wrapper AST 검사 통과다. Proposal 전체 closure는 frozen runner가 native 초기화 전에 다시 검사한다.

**실제 실행 blocker 없음**으로 root에 회신했다. 이는 새 native 초기화 후 expanded admission의 q/FK·전체 native-allowed/same-left self·human–G/cross·filter/readonly gate가 모두 통과할 때만1200step을 실행한다는 조건부 판단이다. 검수 당시 새 native 실행은 시작하지 않았고 실제 접촉/후기 안정성 결과를 인증하지 않았다.

## 실제 native t0 admission 독립 대조

Root의 단 한 번 진행 중인 session15929에서 이미 완성된 `native/initial_values.json`, `initial_grip_audit.json`과 첫 state만 검수했다. 이후 step/5초 완료를 이 절에서 판정하지 않는다.

- 실제 t0의81 q는 prepared float32 q와 exact 일치하며 선택18개만 기준 대비 바뀌고 held63은 exact 유지된다. 실제 초기 PD target=q, 보존 유지 target=prepared PD81이다. 첫 `states.jsonl` 기록과 native initial state가 같다. G 초기 body states·LA·PD properties·physics와 root/하체 초기 body states는 LA−2mm 기준과 exact 동일하다.
- Audit가 저장한66 body의 실제 native filter readback을 reference와 대조해 모두 exact 일치했다. 실제 저장 native pose에서 offline source probe를 별도로 구성해 전체 native-allowed 또는 same-left graph>2 **1188쌍**을 재계산했다. 그중 same-left110쌍이 포함되고 교차0이다. Human–G와 cross-hands도 재계산해0이며 저장 audit와 맞는다.
- 실제66 body pose와 prepared conditional source_state의 최대 오차를 독립 재계산했다. 위치 `0.00018284415555mm`, 회전 `3.6926874338e−7rad`로 저장 audit와 exact 일치한다. 여섯 source-hull/finite-patch certificate를 실제 pose에서 다시 계산한 차이는0이다. Fresh palm 상한은 `0.10952308332374mm`, up proxy는0.9565471586이다. 전체 source face 거리3mm 조건은 thumb 등의 잔여 간격 때문에 지원 성공으로 승격하지 않는다.
- 실제 admission의14 check가 모두 참이며 expanded audit가 zero-step 상태에서 native state before/after equality를 직접 gate로 검사하는 코드 경로를 확인했다. State/filter writer는 추가되지 않았다. 검수자는 저장된 readonly 관측과 코드 guard를 확인했으며 진행 중 native process에 재질의하지 않았다. 별도 before/after state dump를 다시 얻어 독립 live 측정한 것은 아니다.

`/tmp/run_palm_witness_analysis.py`의 최종 analyzer SHAafc4… 확인, 새 analysis 출력/실행 기록 미존재, native execution exit0 선행 조건, source/wrapper 사전 보존·log·전후 SHA 기록을 확인했고 AST 검사 통과다. Analyzer는 위에서 검수한 동일 코드다. 이 절의 최종 판정은 **t0/후처리 계약 문제없음**이며5초 actual 결과와 분석 실행 수치는 별도 완료 자료 대조 범위다.

## 실제5초 완료·분석·영상 모음 독립 검수

Native session15929와 analysis session54267의 exit0 기록을 확인했다. Native는 초기화 시도/성공 각1회,1200step/5.0초, 두151frame 영상이며 report의 모든 check가 참이고 constraint violation은 없다. Analysis는16check가 모두 참이다. Native/analysis/collection 로그 SHA, 실행 전후 입력/source SHA와 보존 복사본을 대조해 일치했다. Native report와 analysis가 선언한 모든 입력 closure의 실제 SHA 불일치는0이다.

- 양조건의 state/trace 각1201행(0..1200), control/contact 각1200행(1..1200), trace clock을 원자료에서 전수 확인했다. 기존과 새 trial의 총2400개 명령을 초기float32 q+원33 offset+실제1Hz 파형으로 재합성해 exact 일치했다. 매4step의300개 갱신·동일 clock/waveform, 모든1200행 held63 target과 초기 held63 q가 맞고 모든 명령은 native/offset bounds 안이다. 전체1201 state의 root/하체는 초기 상태와 exact 동일하다.
- Raw G pose에서 위치 오차와 상대회전 각을 다시 계산했다. Trace quaternion은 raw native quaternion의 정규화 값과 일치한다. 초기/종료 최대 오차와2초 기준 후기 변화를 analysis와 대조해 수치 오차1e−8 이내로 일치했다. 각조건1200개 strap 입력의 route 길이/길이속도로 tension-only 법칙을 직접 재계산해 다음 trace의 적용 장력과1e−8N 이내 일치했다.
- 실제 scalar 손목q에서 기존 static baseline을 뺀2~5초의 constant/trend/1Hz 회귀를 독립 계산해 저장 진폭과 exact 일치했다. Body9 실제 scalar 좌표 편차와 실제 native 한계 초과도 독립 재계산해 일치한다. 몸통 목표 유지와 실제 몸통 고정, target bounds와 physics 후 실제q bounds를 구분한다.

| 측정 | 기존 LA−2mm | 새 초기18 후보 |
| --- | ---: | ---: |
| 최대 초기 G 위치 오차(mm) | 14.010555659 | 14.085147532 |
| 최대 초기 G 회전 오차(°) | 2.607664763 | 2.616524646 |
| 종료 초기 G 위치 오차(mm) | 13.735693689 | 13.803474304 |
| 종료 초기 G 회전 오차(°) | 2.607148981 | 2.616195704 |
| 2초 기준 후기 위치 변화(mm) | 0.363488152 | 0.373544434 |
| 2초 기준 후기 회전 변화(°) | 0.070088885 | 0.072412256 |
| 초기 slack(mm) | 14.013697132 | 14.102284892 |
| Peak 법칙 장력(N) | 28.152161370 | 27.358932455 |
| 실제 손목1Hz scalar 진폭(°) | 0.147836216 | 0.147967329 |
| Body9 최대 실제 scalar 초기 편차(°) | 3.538189108 | 3.538202768 |
| 최대 실제 native 한계 초과(rad) | 0.000099950 | 0.000099845 |

접촉 raw 전체를 재집계해 human–G 양의 lambda body별 step/first/last와 analysis가 일치했다. Palm 양의 lambda는 양조건0이고 human self-contact step도0이다. Lambda를 N이나 특정 지지면의 연속 지지력으로 바꾸어 해석하지 않는다.

| Body | 기존 step수 / 마지막step | 새 후보 step수 / 마지막step |
| --- | ---: | ---: |
| LH:index3 | 1155 / 1200 | 1156 / 1200 |
| LH:middle3 | 20 / 48 | 24 / 65 |
| LH:thumb3 | 194 / 1054 | 191 / 1058 |
| R_Hip | 1200 / 1200 | 1200 / 1200 |

- Capture의151개 step0,8,…1200/time0..5초와 raw/overlay readonly 기록을 전수 대조했다. 매 frame의13개 strap route points는 해당 physics step의 trace와 exact 일치한다. Raw302+overlay302=604개 실제 PNG SHA·1280×720 크기·두 view를 전수 확인했다. Overlay 전후 동일 native pixel 비율은 모든 frame에서 최소95.305%이며 새 물리/형상 렌더를 합성한 자료가 아니다. 실제 손 view의0초/5초 PNG도 열어 native 인체/기타와 passive strap route 표시를 확인했다.
- 두 MP4의 실제 SHA를 확인하고 ffprobe를 별도 실행해 각각1280×720,30fps,151frame/5.033333초 encoded duration을 저장 기록과 대조했다. Physics 시간5.0초와 t0 포함151frame의 encoded duration을 구분한다.
- Collection의 새 두 영상 source/copy SHA와 size가 exact 일치한다. 실제 모음128개, `video_collection_update_v4.json`의 producer/old/new index SHA가 맞고 `VIDEO_INDEX_v5.md`의 suffix는 이전v4 전체 원문과 같다. 이전126개/index를 덮어쓰지 않은 추가 방식이다.

[최신 결정:27](/home/ajou/yigyu/3/stability_adapter_2/PALM_WITNESS_INITIAL_DECISION.md:27)의 새 초기각 미채택·기존−2mm 비교기준 유지 판단은 실제 수치와 맞다. [결정:45](/home/ajou/yigyu/3/stability_adapter_2/PALM_WITNESS_INITIAL_DECISION.md:45)의 평가기록으로 checkpoint 선별→frozen/residual0 관측·action/history 계약→무학습 단일 연주 baseline→공동66 residual/held-out 평가 순서도 기존 학습 평가 계획과 정합하다. 완전 palm 고정접촉을 연주 필수 선행조건으로 두거나 source 접근을 실제 지지 성공으로 확대하지 않는다. 이번 actor inference/training update는0이며 초기world p/q 복원 제어는 미구현이다.

이 완료 자료 범위의 판정은 **문제없음**, 미해결 Critical/Warning/Suggestion0이다. Luna의 추가 artifacts producer/PNG/manifest 최종판과 최종 결과 README의 보존 감사·QA는 이 절의 판정에 포함하지 않는다.

## 최종 그림·복구 범위·문서 검수

- 현재 revised PNG와 recovered v1 PNG를 실제 열어 확인했다. 두 actual native trace의 위치mm/회전deg/직전step cable 장력N과 별도16개 이산 source 거리 상한 panel을 구분한다. Revised의4개 fraction 색상+pass/fail 표식 범례, whole-palm finite-patch upper-bound 라벨, 축과 title 배치가 맞고 범례가 표본을 가리지 않는다. Source 점은 연결하지 않는다. Fraction0의 false는 방향을 제안하지 않은 reference라는 설명이 [README:18](README.md:18)에 있으며 native 충돌 실패로 해석하지 않는다.
- [producer:89](/home/ajou/yigyu/3/stability_adapter_2/make_palm_witness_artifacts.py:89)의 두조건3곡선은 원 trace의1201개 time/값에 해당 단위 변환만 적용한다. Source16행의 palm certificate는 모두1개이므로 [producer:109](/home/ajou/yigyu/3/stability_adapter_2/make_palm_witness_artifacts.py:109)의 첫 값과 전체 최솟값이 같다. Fraction/pass6 표시도 원 search와 맞는다. Source candidate 거리0.109504850, quantized 준비0.109512592, fresh native source0.109523083mm를 최종 README 표에서 구분한다.
- Revised producer SHA는 `4c4b2ccfbaedd9606747cad537777a69829c1d280cebe975360dca29d0095c2a`, PNG SHA는 `caea7d49d10525994ef3af93a4e2ec3a4909d9659b73342664796e8dd16f81a2`다. Manifest의45입력 before/after가 같고 실제 SHA 불일치0이다. Relative output key는 해당 `artifacts/` 기준으로 해석해 PNG/log/execution metadata SHA 모두 확인했다. Revised source와 manifest/PNG/log/execution metadata5개는 `artifact_revised_preserved/` 복사본과 exact 일치한다. Producer AST 검사 통과이며 검수자가 그림을 재생성하지 않았다.

### 보존 이력의 인증 한계

첫 artifact source/출력을 사전 보존하지 않고 같은 경로에서 고친 사실은 [README:67](README.md:67)과 [복구 기록](artifact_revision_preservation.json)에 공개되어 있다. 이 사전 보존 누락을 원본 실행 일식의 정상 보존으로 인증하지 않는다.

현재 영구 복구 source 두복사본의 SHA는 root가 최초 관측했다고 보고한 `61ea48b82aed0f27d3c005c17bedfc9b3edec157d55b7f6cdc712a18b95161fe`, 복구 PNG는 `db6c6964dacc0c816272be17179b33813144b6692bd97dde1b4b3f412bfde68f`와 각각 일치한다. Recovered manifest의45입력과 PNG SHA도 대조했고 producer 경로는 실제 복구 실행의 `/tmp` source다. 영구 source와 해당 source의 bytes/SHA가 같다.

**원 v1 실행 manifest/log/metadata 전체의 byte 복구는 인증되지 않았다.** Recovered manifest는 새 재생성 기록이며 최초 실행 manifest가 아니다. 복구 실행의 전체 독립 local stdout capture도 보존되지 않았다는 제한이 metadata에 명시되어 있다. 원 source/PNG의 reported SHA 일치와 현재 revised 일식의 exact archive까지가 확인 범위다. Native/analysis 원자료·영상·소비된 physics source/leaf/inputs의 SHA는 이 artifact 수정/복구 후에도 모두 일치한다.

### 최종 문서 정합

최종 결과 README/CHANGED_FILES/root notes, [결정](/home/ajou/yigyu/3/stability_adapter_2/PALM_WITNESS_INITIAL_DECISION.md:1), 메인 [README:976](/home/ajou/yigyu/3/stability_adapter_2/README.md:976), [PLAN:1752](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1752), [VISUAL_REPORT:1824](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1824)을 대조했다. 수치·미채택·한조건1회 한계·학습 후속 순서가 정합하고 로컬 링크54개에 파일 누락/줄 번호 범위 초과0이다.

검수 중 지적한 PD startup q와 이후33 offset 유지 target의 혼동, phase의 실제1init/1200step과 artifact 생성의 추가native0 범위 혼동, 이미 작성된 검수 문서의 예정 표시를 수정한 최종본을 확인했다. 보존 이력의 위 제한도 README/변경색인/root notes에 명시되어 있다. 검수한 최종 결과 README SHA는 `e61b17032286cee4e79e119dba0441d0ccf7d058a39db1c4b91a52da5019796b`, CHANGED_FILES SHA는 `6acd1153fad4a8839b8b854e0168c2ba48de9c7cac58a6d4c7600410fdb53f91`다.

**최종 판정: 현재 source/준비/native/분석/collection/revised 그림과 문서는 문제없음. 미해결 코드·수치 수정 요구0.** 위 original v1 artifact 실행 provenance의 복구 미인증 한계는 남으며 원본 일식 완전 보존으로 표시하면 안 된다. 그림과 문서의 재검수를 마쳤고 실제 새 초기자세는 수치에 따라 미채택으로 기록한다.

검수자는 main·탐색 최적화·physics·actor inference·학습을 재실행하지 않았다. 저장 입력으로 source mesh/LP와 certificate·완료 raw 수치를 독립 재계산했으며 Gym scene은 생성하지 않았다. 수정한 파일은 이 `review.md`뿐이다.
