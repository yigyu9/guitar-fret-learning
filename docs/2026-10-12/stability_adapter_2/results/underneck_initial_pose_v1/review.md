# 무스트랩 넥 아래 초기 자세 구성 독립 검수

검수 범위는 [구성 계획](/home/ajou/yigyu/3/stability_adapter_2/UNDERNECK_INITIAL_BUILD.md:1), arm/hand source 탐색 v1/v2, fresh native trial v1/v2와 finger refinement, 현재 저장 source/static 결과다. 다른 담당자 파일은 수정하지 않고 Python3.8 AST·현재 SHA·저장 좌표/관절 범위의 독립 수학만 확인했다. solver·검색·native·분석·렌더 본체는 재실행하지 않았다.

## 코드·저장 범위

- Source calibrated FK는 저장 native 상대 변환과 XML 부모/관절 축에 조건부로 구성한다. 새로운 관절값에 대한 미래 PD/contact 인증이 아니다. 전체 native link FK 대조를 물리 연장 전 확인하도록 구현했다.
- source search_060의 3개 fit은 모두 HG 관통(16/18/13쌍)이 남았다. search_120의 3개 fit은 HG 4/0/4쌍이며 seed1을 fresh native 정적으로 확인했다. fit_success를 관통 없는 지지나 실제 접촉 성공으로 해석하지 않는다.
- 첫 search_060 manifest에는 실제 실행 producer가 빠졌다. [search_revision_reason.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/search_revision_reason.json)이 실행 후 관측 SHA와 beforehash 미인증 한계를 기록한다. v2는 `Path(__file__)`를 명시 포함한다. 두 source·두 native·refine manifest의 현재 입력 64/65/82/84/66개 SHA는 모두 일치했다.
- native_060_rejected와 native_120_seed1은 81/66 구성·names·initialq·전체 FK·G p/q·0step·외력호출 없음의 9판정이 true다. 전자는 HG16/self3, 후자는 HG0/self2로 source_clear false이며 물리 단계는 모두 0이다. 정적 완료를 초기 관통 통과나 5초 완료로 표현하면 안 된다.
- native120의 최대 FK 위치 오차 `2.700893391222606e-7 m`와 회전 `5.382849236818354e-7 rad`는 관측된 초기 상태 대조 범위다. actual81 초기각은 native lower/upper 안이며 palm source-facet 방향 world Z는 독립 계산 `0.9902906115613453`이다.
- RH 거리 v1의 mj_geomDistance 해석 한계를 보존하고 v2는 face-used source 볼록형상의 단위 separating-plane lower bound로 교체했다. seed1의 보수적 source RH gap `51.9969957655 mm`는 actual cooked/손 패드 clearance 인증이 아니다.
- seed1 source 면 거리는 palm `0.326350920 mm`, thumb `0.023697181 mm`, index `0.814978806 mm`, middle `0.942480001 mm`, ring `4.257823255 mm`, pinky 약 `0.000007725 mm`다. front는 outer source z plane 대리 영역으로 실제 프렛/현/PhysX 접촉 성공을 뜻하지 않는다. 약지 목표 불충족과 실제 접촉 readback 필요를 숨기면 안 된다.
- refine는 thumb를 제외한 LH 16 DOF만 기존 actual각 ±0.18/native bounds 안에서 조정한다. source 손 내부 pair만 refinement에서 재평가하므로 최종 후보의 전체 HG/self/RH 검사는 fresh native trial에서 다시 수행해야 한다. 기존 thumb·팔·G·몸통을 변화시키는 제어로 확대하지 않는다.
- NoStrapGym과 실제 step 경로는 strap force 제출 없이 simulate/fetch만 수행한다. 실행 중 코드에는 관절 상태/G pose를 새로 쓰는 호출이 없으며 유지 PD 목표만 사용한다. 정적 모드는 NoPhysicsGym으로 통합된다. 강제 손 부착·moving-target controller·새 학습은 구현하지 않았다.

## 범위상 보완 주의

Warning: [underneck_pose_trial_v2.py initial_audit](/home/ajou/yigyu/3/stability_adapter_2/underneck_pose_trial_v2.py:79)의 `source_clear`는 HG/self/RHgap gate이며 palm-up·사용자 actor-root 범위·native joint bounds를 별도 hard 판정으로 포함하지 않는다. 현재 seed1의 up/native bounds는 독립 확인했고 finger-only refinement는 palm을 유지하므로 현재 후보의 즉시 차단 근거는 아니다. 이후 다른 후보의 일반적인 전체 제약 admission이라고 설명해서는 안 되며 실제 연장 후보의 저장 상태에서 별도 확인하거나 새 버전 gate로 보완해야 한다.

현재 검수 판정: source 및 static 결과와 구현 범위는 정합한다. source_clear인 최종 refinement의 fresh native/5초 결과·최종 문서·보존 감사는 후속 검수 대상이며 아직 완료 판정을 하지 않는다.

## 정제 후보의 fresh 정적 확인

native_refine10000은 fresh 9판정/source_clear true로 0step 정적 완료했다. 실제 관절 81개는 native 한계 안이며 palm source 방향 world Z `0.9902906115613453`이다. G actor-root `[-0.2304154634475708,0.08671234548091888,0.7009729981422425]`와 실제 Chest 높이 `0.8837383985519409`로 위치 상자 안을 독립 확인했고 horizontal q는 직전 허용 회전 동치 범위다. 정제 전후 변화는 LH non-thumb 16관절뿐이며 모두 ±0.18 안, 다른 65개·G p/q·PD properties는 exact, 초기 PD는 actual q와 같다. 해당 fresh manifest 입력 SHA도 현재 파일과 일치한다.

위의 palm-up/위치/native bound Warning은 이번 제출 후보에서 별도 실제 저장값 검산으로 충족된다. 다만 runner 일반 gate의 구현 범위는 그대로다. NoStrapGym의 호출 차단도 특정 apply force/effort 및 네 state setter 경로이며 모든 indexed setter/effort API를 포괄하는 일반 방어막으로 인증하지 않는다. 현재 제출 경로에는 해당 우회 호출이 없다. 동적 실행 결과·실접촉·최종 문서/감사는 아직 검수 완료 범위에 포함하지 않았다.

## OFF 실제 경과와 follower v3

OFF v2는 한 초기화/1200step/151개 30Hz trace·두 151frame/30fps 영상으로 완료했다. 저장 input84 SHA·영상 SHA·clock0..1200 stride8·render readonly 판정과 초기 6개 pre_dynamic_gate를 대조했다. raw p/q를 독립 재계산한 30Hz 표본 최대 변화는 `133.433616417 mm / 28.5467697644°`, 마지막 actor-root Z `0.5990248918533325 m`로 사용자 위치 범위를 이탈했다. 실행 완료는 안정 성공이 아니다.

v3는 기존 initial source_clear에 native 한계·palm-up·초기 box·수평/정면 판정을 추가하고, set_*state 및 set_*effort guard를 확장했다. 명시 producer/facet/새 계획을 입력에 포함하며 현재 SHA `8025e4e8115ff34cc26e6fbad581742da9360f760498a0a730e4bbb90117fb6a` 및 Python3.8 AST를 확인했다. 기존 실제 v2 기록은 변경하지 않는다.

현재 G 좌표로 저장 wrist 상대 pose를 변환하고, 초기 Chest에서 계산한 FK를 현재 Chest의 rigid delta로 바꾸는 식은 부모 frame 정합과 일치한다. 팔12에만 제한된 IK 목표를 합성하고 다른69 목표는 초기값으로 되돌린 뒤 한 PD 제출만 한다. 실제 G/사람 상태 변경이나 외력 제출은 구현하지 않는다. 모든속도 접촉 유지/회전 범위 복귀/손가락별 제어는 구현 범위가 아니다.

Warning: [v3:96](/home/ajou/yigyu/3/stability_adapter_2/underneck_pose_trial_v3.py:96)의 손 목표 projection은 Z 하한 실험값 .66 및 상한 **현재** Chest z를 사용한다. 초기 Chest z로 정의한 사용자 허용 범위 판정기와 동일한 것으로 인증하지 않는다. 실제 G에는 projection을 쓰지 않는다. 구체적인 경계·controller 한계는 후속 결과 설명에 남겨야 한다.

## 저장 ON/OFF 독립 대조

ON 결과도 1200step/151trace·300개의 60Hz controls로 완료되었다. control 제출 clock은 step1,5,…1197이다. ON/OFF initial_values의 모든 공통 필드(실제 전체 상태/q/G·PD·self policy 포함)는 exact다. 현재 입력 및 두 영상 SHA·저장 ffprobe의 151frame/30fps/5.033333s 메타데이터를 대조했으며 새 ffprobe/물리 실행은 하지 않았다.

ON 30Hz 표본 최대 변화는 독립 재계산 `261.399432546 mm / 70.4043015627°`, 마지막 Z `0.5927485227584839 m`로 OFF보다 악화되었고 위치 범위를 이탈했다. 실제 native 한계 안이지만 max arm delta `0.30000007152557373 rad`, max update `0.013333380222320557 rad`로 nominal .3 및 .8/60와 float32 반올림 차이가 있다. 정확한 수치를 숨기거나 strict 무오차 bounds/rate로 설명하지 않는다. 267/300개 control에서 max delta≥.29999로 포화했고 IK fit_success false 32개, 최대 wrist 위치 오차는 `82.179209012 mm`다.

contact_step_counts는 lambda>0 필터 없는 native contact-row pair의 전체1200step aggregate다. 상세 원행은 8step마다 150개 sample로 보존되므로 모든1200 aggregate를 독립 raw 행으로 재산출했다고 주장하지 않는다. 선택된 guitar/guitar–해당 인체 body pair는 OFF palm1133/thumb3 1195/ring3 1017/pinky3 1170, ON palm1140/thumb3 1195/ring3 1136/pinky3 1169/middle3 1038 step으로 기록되었다. fret 등 다른 G body pair가 별도로 있어 이 값은 손가락 전체 pair의 union step 수가 아니다. index와 RH 관련 기타 pair는 양쪽에서 없었다. 접촉 행 발생은 힘 N·positive load·force closure·모든 요구 손가락 지지 인증이 아니다.

OFF/ON 실제 손 t=5s PNG를 확인했다. 새로운 초기 배치와 제한된 팔 follower의 실제 동작은 기록되었으나 사용자 box 유지·모든 요구 접촉·지지/추종 성공은 달성하지 못했다. 최종 설명/보존 metadata는 후속 확인하며 아직 최종 PASS로 동결하지 않는다.

## 팔24 목표 유지 PI v4 사전 검수

[UNDERNECK_ARM_HOLD_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/UNDERNECK_ARM_HOLD_PLAN.md:1), [BoundedArmHold](/home/ajou/yigyu/3/stability_adapter_2/bounded_arm_hold.py:5), trial v4와 테스트를 읽고 3개 소스의 Python3.8 AST를 독립 확인했다. 실험/테스트 본체는 실행하지 않았다. helper SHA `0373918dc35661f19c0fe74c4f7d7d1076ed250f8b58aba99b535c320d223a14`, runner v4 SHA `954c19ecd266f10e6f07db17a323e03a33282c2d8aa26ef43aa7da5c4151db1e`다.

reference±.3와 native 범위 교집합 안에서 목표를 제한하고 이전 목표±.8dt로 rate 제한한다. 이전 목표가 bounds 안이고 제한된 새 목표도 안이므로 rate clipping 후에도 bounds 안이다. 오차 방향의 raw 보정이 적용 보정을 초과하면 해당 적분을 동결하고 반대 오차의 unwind는 허용하는 conditional anti-windup 식이 정합한다. 2개 테스트는 cap/rate·포화 후 회복, 작은 model bound와 reachable integration 및 잘못된 입력을 다룬다.

hold는 양팔24만 수정하며 다른57(손가락·몸통·머리) 목표와 PD gain을 유지한다. follow/hold는 상호 배타적이며 dynamic 모드에서만 작동한다. 제출 후 즉시 native state 비교로 상태 쓰기를 검사한다. 현재 기타 복귀/음악/접촉력 제어가 아니라 팔 목표각 유지의 별도 물리 비교이며 오른팔을 지지점으로 사용하는 정책은 없다.

v4의 follow 선택 경로는 Z 상한을 reference Chest 값으로 고쳐 이전 Warning의 설계 불일치를 해결했다. hold 경로에서는 G projection 자체를 사용하지 않는다. PI double 내부 목표와 실제 float32 제출 사이 nominal ±.3/rate의 ULP 차이는 가능하므로 실제 max delta/step을 후속 원자료에서 확인해야 한다. 새 물리 결과와 초기 OFF 동일성은 아직 사전 검수 완료 범위가 아니다.

사전 판정: 현재 코드의 명백한 blocking 오류 없음. 실제 5초 결과·최종 설명은 후속 대조하며 review는 미동결이다.

## v4 guard의 추가 실패와 v5 보완

[hold_cpu_tests.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/hold_cpu_tests.log)에는 PI 2개 및 state guard 검사 통과와 force/effort guard 검사 실패가 함께 보존되어 있다. v4 set_*effort 분기는 `set_dof_actuation_force_tensor`를 차단하지 않아 RuntimeError가 발생하지 않았다. 실제 runner 경로에서 이 API 호출은 없지만 `no_forbidden` 결과를 일반적인 전체 force API 차단 인증으로 해석하면 안 된다. 소비 v4 소스/물리 기록은 수정하지 않는다.

v5는 set_* 중 force 또는 effort 이름을 모두 차단하고 별도 hardening 계획을 입력 manifest에 추가했다. v4 대비 나머지 PI/초기화/물리/목표 합성 로직은 동일하다. guard v5 테스트는 해당 tensor/effort 호출과 integration 뒤 state setter 차단 및 position targets 허용을 확인한다. 저장 v5 테스트 로그를 확인했으며 검수자는 재실행하지 않았다. v5 새 runner 및 guard test의 Python3.8 AST도 확인했다. 별도 v5 물리 실행은 아직 결과 독립 대조 전이며 기존 v4 실행을 대체·삭제한 것으로 기록하지 않는다.

## 팔 목표 유지 v5 실제 결과 및 저장 분석의 독립 확인

검수자는 물리·분석·테스트·렌더 본체를 재실행하지 않고 저장 원자료와 순수 수학을 대조했다. OFF/ON/hold/v5의 공통 초기 상태·PD는 동일하고 v4/v5 trace와 controls는 byte exact다. v5의 300회 PI 계산을 오차·조건부 적분·cap/rate·float32 제출까지 독립 재계산해 일치했다. 다른57 목표 유지와 실제 한계 검사, root/하체 및 render readonly 저장 판정도 대조했다. v5는 한 초기화/1200step/151trace와 두 151frame/30fps 영상으로 완료했고 입력89개 및 영상 SHA가 일치한다. 영상 길이 5.033333초와 물리 구간 0~5초를 구분했다.

raw p/q로 독립 계산한 v5 최대 변화는 `62.437593975 mm / 15.539565602°`, 종료는 `34.364379855 mm / 4.619507909°`다. 최소 Z `0.6493386626243591 m`로 하한보다 최대 `0.661337376 mm` 낮고 151시점 중 3개가 이탈했다. 2초 상태 기준 2~5초 최대 변화는 `1.852202660 mm / 0.298401180°`이며 rolling window나 초기 상태 기준 오차가 아니다. 마지막 L_Shoulder_x 실제각−초기각은 `1.730753714°`로 해당 관절 좌표 오차다. cap127/300, 실제 float32 max delta `0.30000001192092896 rad` 및 update `0.013333350419998169 rad`를 확인했다. nominal 경계의 ULP 차이를 무오차 제어 인증으로 해석하지 않는다.

150개 stride8 접촉 표본의 기타-body 전체 union은 palm0/thumb149/index0/middle0/ring12/pinky150/RH0이며 positive raw lambda 표본은 thumb149/ring11/pinky148이다. 별도 전체1200step pair-count에는 palm2step이 있어 표본0과 모순되지 않는다. lambda는 힘 N·force closure·연속 지지 인증이 아니다. v4/v5 접촉 행의 byte exact는 주장하지 않는다. 새 초기 근접 배치와 팔 유지의 일부 개선은 확인됐으나 palm/index/middle 유지 접촉·전체 위치/회전 범위·연주 성공은 달성 또는 인증하지 못했다.

[분석 v1 실패](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/analysis_failure.json)는 OFF controls 파일 존재 가정의 FileNotFoundError로 보존됐다. 별도 [analyze_trials_v2.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/analyze_trials_v2.py:1)는 그 입력 분기만 보완했다. 현재 입력28개 SHA와 네 run의 peak/final·Z 범위·2초 기준 변화·접촉 표본/positive lambda를 독립 대조했다. v4 force-setter guard의 실패는 남아 있고 v5 저장 테스트 4개 통과 및 실제 경로 대조로 보완됐다.

## 최종 그림·문서·보존 delta

실제 초기 contact sheet와 별도 v2 비교 PNG를 열어 확인했다. 초기 sheet는 저장 native step0 세 이미지를 균일 축소한 자료이며 새 장면 렌더가 아니다. v2의 세 패널은 저장 151시점 위치 변화 mm·회전 deg·world Z m 및 하한0.65m를 표시하고 공통 범례가 자료를 가리지 않는다. 세 artifact manifest의 입력/producer/output SHA와 실행 metadata를 현재 파일에 대조했다. v1 producer·PNG·manifest·실행 metadata의 이전 사본은 원본과 byte exact이며 v2 출력은 별도다. artifact 경과 시간은 미측정 null이고 별도 원문 실행 로그 인증을 주장하지 않는다.

최종 README의 손가락16관절 표현, 실제각−초기각, 2초 기준 late 설명과 존재하지 않던 로그 링크 제거를 확인했다. README/변경 색인의 모든 절대 파일·줄 링크가 존재한다. main PLAN의 CPU 정의 완료/실초기 배치 완료/5초 비교 완료/실제 접촉 제어 미완료 구분과 README·CURRENT_FILES 최신 설명은 실제 결과 및 최신 무스트랩 조건에 맞다. main 이전 원문·문서 정정 전 사본을 보존하고 PLAN만 별도 delta로 supersede한다.

source_final의 58개 snapshot SHA, 현재 canonical(PLAN 제외), 별도 현재 PLAN snapshot, 외부 입력50개 SHA와 10 attempt의 실제 입력 closure를 대조했다. 보존 범위는 직접 패키지/새 소스와 기존 외부 경로의 SHA이며 완전한 독립 재현 패키지로 인증하지 않는다. 최초 search producer beforehash 누락과 v4 guard 실패 원문은 삭제·소급 인증하지 않았다. [REPRODUCE.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/REPRODUCE.md:1)의 candidate/v5 모듈·dynamic/hold 옵션·새 out 경로는 해당 CLI와 맞고 존재하는 out을 거절한다. 명령 예시를 검수자가 새로 실행한 것은 아니다.

최종 README SHA: `dcac35f74cdd658a51c51ff97013407b15f2f80c10a949d550c713a90db5e165`.
최종 CHANGED_FILES SHA: `227ba3b8505a0b6b6ab3052900ab310d5c66db9583b7be82865e5168901d207b`.
최종 비교 PNG SHA: `1e564ee27e3386dfb44e3a4ffdfb31336f1427eeab57a792b958ffaeebce5631`.

요약 판정: 문제없음. 남은 과학적 한계는 결과에 명시됐으며 현재 문서/자료 정합을 차단하는 미해결 오류는 없다. 최종 PASS는 위의 검수 범위에 한정한다. 최종 보존 감사와 inventory 생성은 root가 이후 수행하며 이 기록은 그 실행 결과를 선인증하지 않는다.

최종 판정: PASS
