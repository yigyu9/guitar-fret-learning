# 최신 가슴·위팔 지지의 왼손 사이클 사전 검수

요약 판정: **문제없음**. Critical0건·Warning0건. 새실행은최신near초기값과기존유한사람관절제어를유지하며왼손잡기/분리궤적과16초진단을연결한다. 실제도달·잡기·놓기·기타안정성성공은실행후판정대상이다.

## Critical

없음.

## Warning

없음.

## Suggestion

- `/home/ajou/yigyu/3/stability_adapter_2/analyze_chest_left_grip_cycle_v1.py:65`: actual_contacts는길이만endpoint와대조하므로선택적으로physics_step도1..N인지assert하면같은시간축임을더직접확인할수있다. 현재runner의같은after_physics에서두배열이기록되며기존endpoint/contact/effort/target연속성assert도있으므로차단할오류는아니다.

## 제어·실행 검토

- 기존left_grip_release_cycle_v2대비변경은놓기fraction을G[.070f,.080f+neckshift,0]m로바꾸고미분도같은비율로반영한것이다. A/B각지점에서대각분리노름106.301mm이며B는A대비G넥축40mm다. 위치목표와velocityfeedforward가정합적이다.
- Left12IK는모델한계/기준±.8rad/ball160°/위치10mm/회전.05radgate를유지한다. nativecontract가최종arm3/finger1.5rad/s로제한하며left33외other48target을exact검사한다.순간이동·손부착·실행중pose덮어쓰기가없다.
- 손목virtualforce25N/moment2Nmcap은left12humanJᵀtorque로만합산하고각model effortclip한다.other69effortexact와native상태보존을확인한다. 권위적인실제최종81벡터는left_cycle_efforts이며body/lefttracking/leftarm이전단계로그는실제tracking.save모듈까지patch해superseded_by로명시한다.
- 새runner는기존rightEW7factory를호출하지않고cycle.main을직접호출하므로75고정right경로가왼손목표를덮어쓰는충돌이없다. 오른타현OFF/준비목표유지이며오른근위팔/몸통의기존유한제어는계속된다.
- 초기native전체state를최신near실행과exact대조한다. q_ref81/finger왼21/PD/mass/Gprediction/fullbodyFK/모델한계/rootlower/sourceclear검사를유지한다. oldnear후보의역사metadata를현재geometrypass대신사용하지않는다.
- shallowAhelper/directconfig/contractinputs/OMmass/FACETS/nearreference/선언XML전체mesh/leafplan을사전·사후pin한다. main문서와독립fresh하위작업을실제물리입력처럼pin하지않는다. 카메라chest_arm_close는기존상속side카메라와이름충돌이없다.
- configdiagnostic_seconds는초안5에서실제실행소비전16으로정정됐다. scene_class(16)도같은horizon을적용한다.960control/3840physics/16초전체를기록하며예외시부분영상과실패원자료를보존한다.

## 분석 검토

- 새분석은현재TIMES/STAGES모듈과직접config/actual_contacts도pin한다. endpoint1..N/effort0..N−1/target4간격을검사하고최종target모델·rate/실제effortfinite·cap을확인한다.
- 잡기는양의rawlambda엄지+다른손가락동시접촉,놓기는zero-lambda행도포함한왼팔/손전체query접촉0으로판정한다. L_Hip을왼팔·손집계에서명시적으로제외하고Chest/상완/양허벅지는별도단계count로남긴다. forceclosure나N단위힘을주장하지않는다.
- BBbodycentre/SO3를전체/초기/2초/단계시작기준으로계산한다. A/B유지중평균손목G차이와대각놓기를포함한전체넥축extent를분리표시하므로106mm분리가40mmstation이동으로오인되지않는다.
- 세새Python AST/strictconfigJSON 및candidate/native-referenceSHA대조통과. 리뷰어GPU/물리실행은0회다. 실제양지점도달/엄지접촉/놓기연속접촉0과기타변화는native후속원자료로확인해야한다.

## 검수 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/CHEST_LEFT_GRIP_CYCLE_PLAN_V1.md`: `8ad167a987c3b87fe68dad23eb36ea0f10a05958c0a6a598de224ba1844c38f7`
- `/home/ajou/yigyu/3/stability_adapter_2/chest_left_grip_cycle_v1.py`: `ade0c307a9f9371ad4d040869bebec92778e403f5c51e4070966a31c163da74e`
- `/home/ajou/yigyu/3/stability_adapter_2/run_chest_left_grip_cycle_v1.py`: `f64c480b4fd05c58fd1001986e52125439debfbc2ea334cf6624b9c476fc2559`
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_chest_left_grip_cycle_v1.py`: `4df2ccf77b6b00adc9b7203241285668c741ff41838958b6abbb40e8b9be0d0f`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/config_v1.json`: `88b8c7fba35502875154b6663cfddb5bbfd709954afe2309c97f20714a5a3f68`
