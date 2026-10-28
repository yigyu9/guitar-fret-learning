# A distal negative 명령을 이용한 release→이동→재압현 가설

**PLAN만 작성, 구현/GPU/native0.** 기존3음실패의actual독립PASS와원자료/분석/972봉인을동결한다. 새범용제어기·grid·gain/물리/성공기준변경이아닌한번의유한명령일정가설이다. 실행여부는root후속판단이다.

## 이미 확인된 A negative 명령 N

N의 정확한 명칭은 **검증된 A distal 무하중/압현 candidate negative 목표**이다. 원A teacher/cap0.25/90쌍·동일settings/view의noNN zero128은0/128·clean0/wrong0/물리손목실패0이었다. env0 저장221끝점의선택4 target는아래N으로상수다. reference와zero의time/source_time/wrist목표위치·quaternion 배열도exact동일했다. 다만actual손목/팔feedback/힘은명령에따라달랐으므로실제팔궤적동일성을주장하지않는다.

선택순서 `[index1_x,index1_z,index2,index3]`:

- A112 reference: 약 `[39.306946,27.755503,54.484707,24.067577]`°.
- N: native저장각 `[0.7078000903129578,0.43403303623199463,0.9057778716087341,0.36218151450157166]`rad, 약 `[40.553955,24.868259,51.897247,20.751471]`°.
- N−A: `[+1.247012,−2.887244,−2.587460,−3.316106]`°. 원4rad/s의1tick허용폭3.819719°보다작지만실제q이동/접촉상실을보장하지않는다.

원zero128 env0음중11표본: body1/2/3 평균 `[8.474546,.243129,0]`N, CPU6gate `[0,11,11,0,0,0]`, wrist오차1.651013mm/.423822°이다. **position/facing geometry는남고distal하중만0**이므로N을피부전체분리·다른접촉해제·표면normal후퇴라고부르지않는다. 상세힘/gate는env0만이며다른127환경의힘을추정하지않는다. proximal1의8.47N도남아N반환만으로wrist고착이풀릴것은미검증이다. N은준비reset부터유지한사례이지, 이미압현한A에서N으로움직여해제한사례나B자세에서N을유지한사례가아니다. MCP2축fullFK로피부궤적을가정하지않는다.

근거경로는 `low_effort_index_learning_v1/runs/precheck_zero/{settings,evaluation,trace_env0_episode0.npz}`와`precheck_analysis/results_v1/{comparison,verification,review.json}`이다. review SHA `07566ae9cd31fd861216a434558a6b9834166c24cdac32360edb8f74cf2015d0`, zero trace SHA `172c624eb9af70e6055c6c68dc3446a045865c0db2f3d728637bb28f582703d9`, settings SHA `3c041fe49ae6d89811ba2156833c05bb4a3eb0553a32d12065a8a6fc2c993c04`, evaluation SHA `5fd95385f983edc65df32ae168897eb8593a33c5ae8b780b60ca2e565ee6b8d3`를읽기대조했다. 새구현시원actual검수SHA와검증입력을그대로pin한다. B비용초기화모델/NN초기행동과혼용하지않는다.

## 고정3phase 초안: 원 gap0.6617초 유지

원67행·선택[4,7,8]·offset2.4497·354control/1416physics·음시계/기회수3/각음원수용AND를유지한다. A end local3.1703→B공유press3.832 사이만아래일정으로바꾼다. 초기2초A ramp·A음창은보존하고B7/8무음gap에서는다시강제해제하지않는다.

| phase | local 시간 | 선택4 목표 | wrist 위치 목표 |
|---|---|---|---|
| 해제 가설 | 3.1703→3.2703 (.10s) | Aref→N 선형유한이동 | A 유지 |
| 이동 가설 | 3.2703→3.7120 (.4417s) | N 유지 | A→B 선형이동 |
| 재압현 가설 | 3.7120→3.8320 (.12s) | N→원reference 선형복귀 | B 유지 |

위치는검증된A/B셀차29.523457mm만사용한다. 이동구간이기존.6617초보다짧아져Cartesian **목표일정속도**는44.6176→66.8405mm/s(약1.498배)가된다. 이차이를숨기지않으며nativejoint4rad/s·wrist .5도/tick cap·K/D·범위/effort/90쌍은변경하지않는다. 이것은실제손목속도증명이나cap완화가아니다. 선택4의최대선형요청속도는해제약.57877rad/s·복귀약.48231rad/s로원4rad/s이내지만실제native제출target에도기존oldtarget±4/60∩bounds를검사한다.

시간표는원처럼 **다음60Hz control끝점의요청목표** 기준이다. 실제제출은control시작에일어나고4physics가그목표를추종하므로비정렬된음경계부근에서목표전환과실제움직임은표의연속시간과완전히일치하지않는다. source/audio시계를옮기거나240Hz중간목표/상태를덮어쓰지않고submit_clock/endpoint_clock/phase를함께기록한다. 따라서원A release창 `[end,end+.10]` 안에실제candidatefall이있었는지를원native판정그대로확인하며, 늦거나없으면그대로미달이다.

## 최소 연결과 실제 검증

후속승인시새버전에서만현재prefix의view/catalog/environment/compact/collector와원fixedScene·cap4verifier·wristv3·trajectory_actions를재사용한다. 새동작은선택4 finite목표일정과wrist위치일정의두piecewise 함수뿐이다. arm12 feedforward/quat·비선택B·엄지035·보상9항/실패/음별원장/가동범위·sourceassets는그대로다. 새일정/N출처/시각을pool생성전별도계약으로명시하고현재972봉인이나기존teacher/reference를수정하지않는다. 학습/정책이식없음,단1scene/noNN4firstattempt이며원실패prefix4를대조로재사용한다.

검증은N을목표로냈다는사실과실제A release/B negative를분리한다. 원native released/release_s와기존candidate/assigned-distal-loaded gate(.01N원문턱)를그대로관찰한다. 필요하면원substep호출후읽기observer로4환경각phase의최초candidatefall·candidateoff/loadedoff·최대하중/표본수를bounded사건/집계만보관한다(전체body240trace나새threshold없음). N구간에서A/B어느쪽candidate와distalload가남는지도실패포함분모로기록한다. loadedoff도피부전체분리/실제현압력인증은아니다.

중간release/negative가없어도새조기종료·대기·조건부추가시간·보상·원음창변경을하지않는다. 고정일정을그대로관찰하고해당중간가설미확인과최종각음결과를나눠보고한다. 원release창을늘리거나candidateoff를새음악성공gate로만들지않는다. 최종원4분모/12note/9episode보상·각음기존acceptance및AND를보존한다. 실제q/선택3힘/손목/팔요청경계·원wrongfret/string/higher·원A candidate잔존을기존관찰과비교하되단일원인/접촉쌍으로확정하지않는다.

CPU에서는N의원target상수/출처·전체bounds·각phase연속유한/시간합.6617/원음시계불변·원67/3mask/기회수·targetrate/codec·4quota/실패및retry제외·원release latch관찰/9보상보존·입력/alias/close/기존out보호를검사한다. 독립CPU검수와새봉인후root만실행여부를정한다. 실패를B불가능으로확대하거나새grid/속도·gain/힘문턱탐색을자동추가하지않는다.
