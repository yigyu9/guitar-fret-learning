# 현재 기타 기준 준비 gate 독립 검수

검수 소유권은 이 review.md뿐이다. 계획/helper·테스트·source 초기 탐색·실제 준비 runner·사전 보존 wrapper를 읽고 Python3.8 AST와 저장 자료·작은 순수 predicate 반례를 확인했다. 테스트/검색/solver/actor/native/분석/그림/봉인 본체를 재실행하지 않았으며 소비 source·원자료·기존 봉인 기록은 변경하지 않았다. 최종 자료 해석·문서/미디어·보존 감사는 후속 검수 대상이다.

## 요약 판정: 수정 권장

### Critical — 계약의 RH 비접촉 판정

[guitar_relative_readiness.py:29](/home/ajou/yigyu/3/stability_adapter_2/guitar_relative_readiness.py:29)의 positive lambda 필터가 RH 접촉 판정보다 먼저 적용된다. 정상 LH support/front/grip fixture에 RH–G native contact 행을 추가하는 순수 predicate 반례에서 lambda0 및 NaN은 right_noncontact=True/ready_now=True이고 lambda1만 차단됐다. 계획의 ‘준비 중 오른손–기타 실접촉은 ready 차단’과 다르다. LH 지지의 positive finite lambda 조건과 RH 모든 접촉 행 차단을 별도 처리하고, 유한하지 않은 접촉 증거는 fail closed로 다뤄야 한다. 현재 소비본을 수정하지 말고 새 variant로 보완한 뒤 그 gate를 일반 준비 계약으로 인증한다. **이번 실제 저장300frame에는 RH–G 행이 없고 ready0/actor0이므로 이 반례가 실제 PLAY 우회를 일으켰다고 주장하지 않는다.**

### Warning — PREPARE와 PLAY front 기준

[run_guitar_relative_ready.py:126](/home/ajou/yigyu/3/stability_adapter_2/run_guitar_relative_ready.py:126)는 PLAY에서도 helper의 right_front_side를 요구한다. [helper:60](/home/ajou/yigyu/3/stability_adapter_2/guitar_relative_readiness.py:60)는 center보다3mm 이상 앞쪽이므로 피크가 아직 앞쪽0~3mm인 경우에도 HOLD가 된다. 계획의 ‘뒤면으로 넘어가면 중단’과 동일한 판정이 아니다. 준비 stand-off와 PLAY backside 판정을 새 버전에서 분리하거나 최종 설명에 실제로 더 엄격한 PLAY3mm 조건임을 명시한다. 이번 PLAY는 실행되지 않아 해당 전이의 실제 성능은 미검증이다.

### Warning — 아직 실행되지 않은 handoff

저장 handoff_preflight는 task-local reset/history의 readonly 대조이며 실제6frame gate→PLAY 전이를 실행한 근거가 아니다. actor0/PREPARE 종료 자료로 phase/clock/detector의 실제 PLAY 동작·타현 성공을 인증하면 안 된다. CPU 공통 변환 검사는 translation/Z축 회전 범위이며 고정 world-Z palm-up 조건 때문에 임의3D scene 회전 불변성까지 확대하지 않는다.

## 구현 정합과 실제 저장의 좁은 대조

- helper는 native positive raw lambda의 LH:palm under-neck point와 최소 한 LH 손가락 neck point를 구분한다. G body의 localPos를 현재 body pose로 world에 변환한 뒤 현재 guitar actor frame으로 바꾼다. neck 범위/taper와3mm 여유는 source 영역 설명이며 actual cooked 면·해부학적 pad/힘 N·연속 지지 인증이 아니다. 현재 수평 배치의 underside는 local+X 쪽이며 world palm-up 조건을 별도로 둔다.
- RH 준비 기준50mm 및 front3mm는 원본 ready 획득10mm와 별도다. target은 source ready_G+[0,0,.03]를 current G p/q로 world 변환한다. geometry 없는 RH:pick에 physical 면을 만들지 않았고 원본 좌식 pick relative rotation은 초기 soft preference뿐이다. original grip_success는21관절 reference 판정이며 실제 pick grasp 인증이 아니다.
- source search는 초기 measured q를 기준으로 RH arm12 ±1.2/native 및 RH21 grip만 바꾸고 source moving 전체 RH hull·비인접 human pair/HG를 검사한다. candidate0은 pick target error76.395814mm 및 RElbow–Gbody source LP0.529318mm로 rejected, candidate1은2.201253mm 및 검사 범위 source overlap0으로 accepted다. 두 경우 모두 native 초기화1/물리0 source 결과이며 fresh contact 준비 성공으로 해석하지 않는다. q 원JSON double→native float32 표현 차이와 실제 유지 비교를 구분했고 candidate1 fresh other48 native 초기각은 이전 native_refine10000과 exact, G 목표p/q도 유지된다.
- PREPARE의 calibrated FK는 initial Chest에 고정된 팔 subtree를 현재 Chest rigid delta로 변환하고 현재 actual RH관절을 사용한다. RH12는 fresh candidate±.3/native 교집합의 IK이고 LH12는 기존 conditional PI다. 최종81을 한 번 제출하며 RH21 및 other36은 초기/reference 목표 유지한다. PLAY시 원source RH30이 제어하고 RThorax3는 handoff 목표로 유지한다. source history에는 실제 최종float32 목표를 회신한다. SDK 이후 state쓰기/effort/strap 외력 없이 PD목표+simulate/fetch를 사용하고 source reset은 task-local뿐이다.
- search before/after964 및 native before/after966 superset changed0 기록을 읽고 해당 시점 존재한 새 source/계획 사본의 before/current SHA를 대조했다. 검색 시점에는 아직 native runner가 작성되지 않아 search superset에 없으며 검색 실행 의존성도 아니다. native superset에는 runner가 포함된다. 전체 큰 superset의 최종 보존 검산은 root 후속 범위다.
- 현재 저장 native_v1은 failure없음/1200step/151frame/300control/PREPARE 종료·play_start=null·actor0이다. 300명령의 other36 exact·native bounds와 max update0.013333350419998169rad를 독립 대조했다. source song_time은 모든control에서 원본 시작값−0.47690001130104065초로 정지한다. clock이0이라고 설명하지 않는다.
- left_palm_under_neck_contact는 step12 한 controlframe에서 true였지만 그 시점 finger_neck_contact=false다. ready_now는 전체300개 모두false이며 debounce6frames를 충족하지 못했다. ‘손바닥 접촉이 전혀 없었다’라는 전체0 표현도 정확하지 않다. RH–G contact row는 전체300개 저장control에서0이었다. 현재 부족한 LH support를 우회해 PLAY한 증거는 없다.

## 현재 source 식별

계획 `444e3b152dd3c65fb9b6b61250ee86cd21dcfbffb06f5a1689c59325c9e1770b`.
helper `a114dd2484f033dc20d9460094aabdf6a1e58a02737cf88747a1ad987a1a44a3`.
tests `e5acb05b783aab93e35afc05511e79c1ab69c23e8f968eb2b1f3b8c7cd859801`.
search `3c361fda06fcf1e48dd7f4f6451538b79991470d797ad88778c1fadd7307eb9e`.
native runner `fabfbbdcd1a27bd7af1ce50218b18f833a8da78278057485643aec4c2aa82b3e`.
wrapper `ef773253b56e92ab7ae9cf6d9b616df85d0ce6055a0bc7d3432ad713443e4995`.

현재 진단의 저장된 부정 결과와 위 구현 한계를 분리한다. 최종 PASS·review 동결은 최종 분석/문서 및 보완 범위 전달 후 별도 판정한다.

## v2 보완 및 v3 handoff 코드 추가 검수

요약 판정: **v2의 두 predicate 지적은 보완됨. handoff 목표 재선택 지적은 v3 코드에서 보완됐으나 실제 PLAY 전이는 아직 미검증이다.** 소비된 v1/v2 원문과 위 지적을 보존한다. 이번 추가 검수도 AST·저장 자료·작은 순수 predicate/PI 검산만 수행했고 테스트/actor/native/분석 본체를 재실행하지 않았다.

- [v2 helper:35](/home/ajou/yigyu/3/stability_adapter_2/guitar_relative_readiness_v2.py:35)는 RH 접촉 행을 finite/positive lambda 필터 전에 모은다. 같은 작은 반례의 lambda0/NaN/1 모두 준비를 차단함을 확인했다. LH 지지 증거의 finite positive 조건은 유지된다.
- [v2 helper:78](/home/ajou/yigyu/3/stability_adapter_2/guitar_relative_readiness_v2.py:78)와 [v2 runner:126](/home/ajou/yigyu/3/stability_adapter_2/run_guitar_relative_ready_v2.py:126)는 PREPARE front3mm와 PLAY body rearplane−3mm를 분리한다. 현재 [G:body source:124](/home/ajou/yigyu/3/tab2body/assets/guitar_asset.xml:124)는 회전 없는 child이며 box geom 위치0, half-thickness.02m다. 현재 native body pose와 해당 source box를 이용한 rearplane 계산에 정합한다. 정상 string-plane 통과/뒤면 반례를 독립 대조했으며 전영역 cooked collision 인증으로 확대하지 않는다.
- [PI helper:16](/home/ajou/yigyu/3/stability_adapter_2/preparation_joint_tracking.py:16)는 moving reference와 actual 오차에 P.7/I.5를 적용하고 raw correction±.15·초기/native 교집합·.8rad/s 제한에 대해 조건부 적분을 한다. 현재 caller의 previous 목표가 bounds 안이라는 조건에서 작은 60회 표본의 최대 update.013333333333333336rad와 bound에서 적분0을 확인했다. 실제 최종 reference 차이는 rate 제한 때문에±.15보다 클 수 있다는 revision 설명도 맞다. source PLAY시 PI를 중단하며 최종81 및 실제 목표 역변환 history를 한 번 합성한다. PI가 준비 성능을 개선했다는 인증은 없다.
- v2 저장300control의 other36 exact/native bounds/RH 초기±.3와 최대 update.013333380222320557rad를 독립 대조했다. 1200step/151frame·모든 report check true·973입력 changed0이며 관련 소비 source 사본/current bytes도 일치했다. palm28/finger299/ready1(physics step12), 최대 연속 ready1이므로 6frame gate는 실패했다. actor0/PREPARE 종료다. 마지막 RH ready distance104.324010mm/최대123.844443mm로 v1 마지막56.300324mm/최대60.255158mm보다 커졌다. ‘palm 접촉 없음’이나 PI 채택 성공으로 설명하지 않는다.

### Warning — v2의 gate 이후 목표 재선택; v3 구현 보완

[v2 runner:25](/home/ajou/yigyu/3/stability_adapter_2/run_guitar_relative_ready_v2.py:25)의 seed_play_state는 [원본 task reset:1897](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:1897)의 event 재선택 및 [lane 재선택:1942](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:1942)를 호출한다. [v2 handoff:131](/home/ajou/yigyu/3/stability_adapter_2/run_guitar_relative_ready_v2.py:131)에서도 다시 호출하므로 준비 gate가 확인한 ready와 첫 PLAY 목표가 달라질 수 있다. v2 실제 PLAY0이라 발생한 성공/실패 사건이라고 해석하지 않는다.

신규 [handoff helper:5](/home/ajou/yigyu/3/stability_adapter_2/strike_preparation_handoff.py:5)는 reset 없이 final PD/action history/현재 previous pick만 갱신하고 current target geometry tensor exact 불변을 검사한다. [v3 runner:48](/home/ajou/yigyu/3/stability_adapter_2/run_guitar_relative_ready_v3.py:48)의 초기 task reset과 [실제 전이:124](/home/ajou/yigyu/3/stability_adapter_2/run_guitar_relative_ready_v3.py:124)의 history 갱신을 분리했다. 신규 테스트 원문과 저장 CPU1pass 로그·Python3.8 AST를 확인했고 이번 변경에서 별도 blocker는 발견하지 않았다. 실제 gate→PLAY에서 event/lane/clock/history 불변을 입증한 물리 근거는 추후 자료로 구분한다.

source 검색의2.201253mm는 검색 당시 ready_G.y−.325232446 기준이다. native 초기 task reset 후 ready_G.y는−.308914542이고 pick_G.y−.325642437이므로 그 숫자를 native current-ready 오차로 바꾸어 설명하면 안 된다. 현재 runner는 매 control의 current-ready를 다시 읽는다.

### 최종 제출 목표에서 source history 독립 대조

[원본 inverse:765](/home/ajou/yigyu/3/tab2body/env/base.py:765)와 native backend의 lower/upper로 float32 mid/half를 재구성하고 checkpoint controlled-name 순서의 실제 final30 목표를 역산했다. checkpoint action_scale=1.0이며 v1/v2 각각 전체300명령의 저장 source_history와 최대 절대차0이었다. 첫 preflight만의 검사에 의존하지 않았다. 실제 actor/handoff0을 유지하며 이것은 최종 목표 회신 수치 계약의 대조다.

v2 helper SHA `79ffdaa6d307d4d66f0b89680d84e722db40e31d8a36b377315472f025ed6e90`; PI `5be1a90d78ad18e75f242d5a24b383bc043bafa7323926b83c8972e16b03245f`; runner `94e3e577c6cea1793b6c1ebce408ab8a05518607757e74b46c7473aba4aedfab`; wrapper `4d6529b472ba232874357a164e62e194a0240840de7dc69cf011cd6449b1704e`.

v3 handoff helper SHA `f30a3ae8232af82b6bc476162212f07b3f5234eecb4c2f584ce0db31032ae8bc`; runner `aa506dd447b53252e7725050ac2a6fcdac6fcb15df3d214239028d8f92631395`; wrapper `d9dd75d4e1e89dc9e22e710d06534afde13c59598663e71e2b8196fc73f3f9f9`; revision `a4c8af57fe077ce13c16aab2344db2a56f2f2b9bd1831ed25ce776a6d4eb92e8`.

현재 review는 중간 기록이며 최종 동결 전이다. v3 이후 실제 자료·최종 제어 선택·산출물/문서는 별도 검수한다.

## v3 실제 재현 및 최종 v4 코드 선택 추가 검수

v3 저장 trace.json은 v2와 byte exact이며 두 조건300control의 readiness도 전부 exact였다. v3 report는1200step/151frame·14checks true·actor0/PREPARE 종료·target geometry preflight true다. 입력978개 before/after changed0 기록과 정합한다. 따라서 v3 실제 PLAY 전이 검증으로 확대하지 않는다.

[최종 선택 근거:3](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_READY_BASELINE_SELECTION.md:3)의 tradeoff를 저장 자료로 대조했다. v1→v2 최종 G drift37.426503→24.942781mm/5.157437→2.304045°와 palm+finger 동시 표본0→28은 맞지만 RH ready 거리는 악화되고 준비6frame gate는 두 조건 모두 실패했다. 준비 기준 실패와 기타 drift 감소를 구분하여 추가 RH PI를 채택하지 않는 판단은 자료 범위 안이다.

v3→v4 코드 diff는 RH PI import·constructor·update/기록을 제거하고 RH12에 fit.x를 제출하는 변경이며, wrapper는 실행 모듈만 v4로 바꾼다. LH PI·current G IK·body rearplane·RH 모든 contact 행 차단·reset 없는 handoff·최종81/history/native bounds/rate/other36 및 no-forbidden/readonly 조건은 유지된다. Python3.8 AST와 저장 최종 pure13pass 로그를 읽었고 이 변경의 코드 blocker는 없다. v4 실제 결과 대조는 실행 종료 후 별도로 수행한다.

v4 runner SHA `2cd5e842da920ac99492a9691e7c9a01eb42bb5a119aa15ceabd29ddea5ca089`; wrapper `a283aeaa19ca2aeacf750e271930d850fc38b67e065ca36c15eba4eab36abdba`; 선택 문서 `b9610d32df9408f327872cd07d4a4542f49df9bc4ea5e50b2366e311b427ecf9`. 최종 review 동결 전이다.

## 최종 v4 실제 저장 및 네 조건 분석 추가 검수

요약 판정: 저장 실행·분석 수치는 **문제없음**. 실제 준비 gate/handoff/연주 성공은 **미완료·미검증**이다. 이후 최종 문서와 미디어 검수 전까지 review를 동결하지 않는다.

v4는1200step/151frame/300control·report14checks true·failure없음·actor0·PLAY시작null·PREPARE 종료다. v4 trace 원문은 v1과 byte exact, 네 조건의 native 초기 fullstate와 PD properties는 exact였다. 300명령 시점은 step0..1196 stride4,151trace 시점은 step0..1200 stride8이며 마지막 control4.983333초와 물리 종료5초를 구분한다. v4 palm1/finger298/동시0/ready0/RHnear9는 저장 조건에서 직접 재집계됐다. source model의 최종 runtime frozencheck가 true이며 checkpoint 입력SHA와 소비 코드가 보존됨을 확인했다. final model tensor를 별도 직렬화한 자료는 없어 그 밖의 독립 final-weight 비교를 수행했다고 주장하지 않는다.

최종 [저장 analyzer:20](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/analyze_preparation.py:20)의 AST·27입력 before/after/current SHA를 대조했다. 본체 재실행 없이 네 조건 raw controls에서 조건 count·ready/stand-off 거리 min/max/last를 계산하고 raw G p/q에서 종료·최대 drift를 재계산해 summary 수치와 일치했다. 각 조건 current-G target150표본은 raw pose 변환과 차0이었다. 모든4조건300명령의 final30→source history를 checkpoint action_scale1.0/native float32 mid/half로 독립 역산해 차0을 확인했다. source2.201253mm/search lane와 native initial ready33.711651mm/stand-off16.862091mm를 분리한 분석 설명은 정확하다.

v4 결과는 v1과 같은 ready distance 마지막56.300324/최대60.255158mm, stand-off 마지막34.066849mm이며 G 종료37.426503mm/5.157437°, 최대59.578528mm/9.525696°다. 이 자료는 current-G IK·bounded PD 준비 진단의 부정 결과이고5초 연주나 연속 LH 지지 성공이 아니다. v2/v3의 동시 palm+finger28표본·최대연속20에도 전체 ready 최대연속1이므로 준비 조건 일부와 전체 gate를 구분한다.

v4 종료 입력981개 changed0 기록 후, 검수 시점 current979개는 exact였다. 달라진 두 canonical main PLAN/README는 승인된 후기 append다. [main_before PLAN](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/main_before/PLAN.md)과 [main_before README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/main_before/README.md)는 v4 before SHA exact이고 current main이 해당 원문 prefix를 보존함을 확인했다. 코드/물리 입력의 drift로 해석하지 않는다.

analyzer SHA `fd8f20eaf726168bccea078f12fd97688de980e0d0680c5c980112ce9a9af957`. 최종 산출물/문서와 봉인 논리 검수는 후속이다.

## 최종 산출물·문서·봉인 사전 검수 및 동결

요약 판정: **문제없음**. 초기 검수 지적은 소비본을 보존하고 v2 predicate/v3 handoff/v4 제어 선택으로 보완했다. 이 판정은 구현·저장 진단·후처리/문서 및 봉인 사전 논리의 정합 판정이며, **준비 gate 획득·실제 PLAY handoff·타현 성공을 인증하지 않는다.** 원자료/코드/테스트/검색/분석/그림/물리/봉인 본체를 추가 실행하거나 다른 담당자의 파일을 수정하지 않았다.

- canonical v2 PNG를 실제 열어 두 패널의 거리곡선·50mm 외부 근접·10mm 원본 READY 맥락·1/298/9/0 조건 표본·6연속 조건·시간/단위를 확인했다. 범례는 축 밖으로 이동해 자료를 가리지 않는다. 보존 v1→v2 producer diff는 범례 위치 한 줄뿐이며 계산/원자료는 같다. 두 variant의3입력·PNG output/current SHA 및 manifest/execution 일치·exit0·닫힌 로그 존재를 확인했다. 그림은 saved control 그래프이며 native render와 구분된다.
- v4 native 전신t0/t5와 손t5 PNG를 실제 열어 문서의 카메라 구도 및 무스트랩 장면 설명과 대조했다. 네 조건8영상의 current bytes SHA는 report와 일치하고 저장 ffprobe는 모두151frames/30fps/5.033333초다. 물리5초·마지막 control4.983333초·MP45.033333초를 구분한다. 초기 문서의 v1 26frame/0.866667초 오표기는 최종 문서에서151frame으로 정정됐다.
- 최종 [README:3](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/README.md:3)의 몸통9를 포함한 other36 유지·주요66권한과 최종81제출 구분, [표/설명:9](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/README.md:9)의 전체조건참1표본과6연속 gate 미획득 구분을 확인했다. 네 조건 표 수치·source search lane 대 native ready/stand-off·raw lambda 비힘인증·실제 PLAY0·후속 지지/추종 개선 미실행이 확정 자료와 정합한다. 영상8개 inline embed 및 그림/자료 링크는 존재한다.
- [CHANGED_FILES:18](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/CHANGED_FILES.md:18)의 새23개 A 계획/구현/test/main 문서와 phase analyzer/그림/sealer 색인을 읽고 파일/line 존재를 확인했다. 마지막 `new_names` 링크40→51 수정은 보존된 직전 문서와 해당 한 곳만 다름을 대조했다. [main PLAN:142](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:142), [README:1447](/home/ajou/yigyu/3/stability_adapter_2/README.md:1447), [VISUAL §125:2234](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2234)의 완료한 준비 구현/5초 기록과 실제 준비·연주 미완료 구분은 정합하고 승인된 원문 prefix를 보존한다.
- 미소비 [seal_phase.py:18](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/seal_phase.py:18)의 AST·보존 논리를 검수했다. v4 closure 중 허용 main2 append와 원문SHA/prefix, VISUAL prefix, trace 두 쌍/300 final goals, analysis27/current+after, 그림v1/v2 manifest/execution input/output/producer current SHA, 이전 strike654inventory를 검사한다. 이전654파일 SHA도 검수자가 별도 읽기 대조해 exact였다. 소스사본 후 inventory와 readonly 재검산·최종 verification을 발행하며 자기 inventory/finalverification만 재귀해시에서 제외한다. 이번 봉인은 phase-local 열린 stdout log를 만들지 않고 모든 writer/log 종료 후 root가 실행하는 조건이다. 봉인 자체의 실행 결과는 root가 이후 작성한다.

최종 README SHA `08022a63cedaabb24074226d8e87b82fed00e8979287f1adf71393def0d3d098`.
CHANGED_FILES SHA `1e378bf9eccc1c04ca08b79f86bb1fb75628f9bceadeab798a1a6170bce31caa`.
VISUAL_REPORT SHA `c312cf77c4fc244fd400449d55266c5b951a39429819abc86f6baab915e5b8fb`.
canonical PNG SHA `6e81bf95e730cd4f24b56564f28800593d46d9a773ca8d19287a2e8d104820b5`.
봉인 producer SHA `3053030a092c4ac69f333881a7c27d0cf3362a8ac168e6bd98c0a61be84d192a`.

남은 material blocker 없음. 이후 이 review.md를 동결한다.

최종 판정: PASS
