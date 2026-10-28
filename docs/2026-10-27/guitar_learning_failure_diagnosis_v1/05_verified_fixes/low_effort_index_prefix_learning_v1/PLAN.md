# 검지 원곡3음 조건부 F4 fresh 학습 계획

상태: **root PLAN 승인, 새폴더 구현·CPU 준비 단계만 허용; GPU/학습 실행0**. 기존 source/1515·1420·1215 등 모든 봉인·준비·원자료·결과는 변경하지 않는다. staged release-transfer 실제 독립 PASS review SHA `fde9560714e62c36d17433a59583f24cc79bc15c181f84ae86851577e45ee122`를 근거로만 연결하며 새 guard+128 조건의 성공을 상속하지 않는다. 새 범용 훈련기를 만들지 않고 원 short runner/PPO/policy와 검수된 3음·128cap helper를 최소 adapter로 연결한다.

## 고정 과제와 첫 tick 제어

검지 선택4축은 reset 뒤 **첫 tick부터 NN 행동**을 쓴다. NN 학습/정책평가/정책영상에 scripted N 일정이나 선택관절 reference target을 주입하지 않는다. negative/reference trajectory는 별도의 비NN `reference` 대조에만 존재한다. 팔12축은 staged wrist teacher, 다른 손가락 B·엄지035·고정 기타·90 충돌쌍·전체 native 범위·원4rad/s/PD·손목v3·원9보상/실패/PPO gamma .99/cost weight1을 유지한다. 16손가락 native effort .25는 원105속성/128실제 readback으로 검증하고 다른89축/그 외 속성은 원본이다.

| source index / ID | 물리 현/프렛 | 원 task press / onset / end (s) | local press / onset / end (s) |
|---|---|---|---|
| 4 / event-000004/string-3/note-4 | 3현4프렛 | 5.3297 / 5.4497 / 5.6200 | 2.8800 / 3.0000 / 3.1703 |
| 7 / event-000007/string-2/note-7 | 2현5프렛 | 6.2817 / 6.4017 / 7.1796 | 3.8320 / 3.9520 / 4.7299 |
| 8 / event-000008/string-2/note-8 | 2현5프렛 | 6.2817 / 7.8065 / 8.1548 | 3.8320 / 5.3568 / 5.7051 |

원67 targets를 그대로 보존하고 focus만 [4,7,8], 검지 opportunities=3으로 한다. 다른 손가락 기회는 이 진단 subset에서 제외된다. score offset=2.4497s, duration354 controls=5.9s, 다음 검지 press8.3599s 전의 기존 cap을 그대로 사용한다. 7/8의 shared press와 무음 gap을 유지하고 개별음/press/end를 앞당기지 않는다. 원 audio onset/end는 위 task 시각에서 원 pre-roll3s를 뺀 값이다.

손목만 기존 staged 일정을 쓴다: 초기2s ramp, A 고정→local3.1703부터 .10s는 A에 유지→3.2703..3.7120에 A→B 선형 이동→B 유지. 같은 quaternion/finite arm feedforward·원 qpos-Jv3 feedback을 유지한다. 선택4축 N은 이 손목 일정에서 분리한다. `reference` 대조에 한해 기존 `negative_weight`의 A end 뒤 .10s N ramp와 B press 앞 .12s close를 재사용한다. 원 reference JSON은 A/source4 provenance를 유지하며, 같은 positive4각을 B 위치에서도 요청하는 진단 schedule임을 별도로 선언한다.

## 현재 목표와 DIP guard의 새 계약

매 **pre-control 현재** env `_score_time()`와 원 end tensor로, 선택 [4,7,8] 중 `now < end`인 earliest를 각 행에서 독립 선정한다. 초기 준비는4, 4 end 뒤에는 무음 gap도7, 7 end 뒤에는 shared press를 보존해8, 8 end 뒤에는 none이다. 다음 endpoint 시각으로 앞당기지 않고 achieved/released flag를 선택에 사용하지 않는다. 부분 reset은 해당 env clock만 초기화한다. none은 명시 mask하며 -1 gather가 마지막 원곡음으로 오인되지 않게 한다.

해당 현재 목표의 `candidate & ~wrong`와 원 valid/reset/finite/failure 보호가 통과한 행에서만, 원 controller가 계산한 DIP **추가 양의 목표증분**을 old target으로 유지한다. negative/opening·zero·MCPx/z/PIP와 나머지104열은 원함수 결과 그대로다. actual q를 덮어쓰거나 억제 증분을 이월하지 않는다. gate 상실/current none에서는 새 원제어를 재개한다. native range/rate/메모리 반환 alias/scene 제출/target_error 관측 일치를 검산한다.

`short_learning`은 새 `diagnostic.index_prefix_learning.v1` schema를 쓰고 원 B cost-initialization descriptor와 current-goal/guard/staged-wrist descriptor를, `action.target_contract`에는 동일한 실행 guard 계약을 **policy 생성 전에** 저장한다. 이는 prefix+손목+guard+cost0의 결합된 조건부 실험이며 원 B cost-only 비교로 부르지 않는다. `variants.descriptor('B_zero_cost_head')` 원문은 초기화 설명으로 보존하되 전체 실험의 변경이 cost뿐이라고 해석하지 않는다. eval/render는 `fresh=False`; 실제 학습된 cost head를 다시0으로 만들지 않는다. 단음/무guard/다른goal-selection 계약과 strict 교차 load를 거부한다.

## 최소 연결 지점과 그대로 쓸 수 없는 부분

- `guitar_learning/tool/experiments/short_finger_learning/runner.py:76` `run`, `:149` `_train`, 원 `DecisionCollector`/PPO/save/load를 재사용한다. 새 문서 wrapper에서 `make_settings`만 봉인된3음 설정으로 연결한다(원 `make_settings:27`은 단음 subset으로 되돌리므로 그대로 호출해 끝내면 안 됨). eval은 checkpoint settings를 그대로 사용한다. runner의 checkpoint schema binding은 새 선언과 일치시키고 runner/runtime의 top-level Pool/Policy alias와 두 `_pins` 경로를 모두 scope/superset으로 연결한 뒤 finally 복원한다. 기존 spec.SCHEMA나 old policy validation을 바꿔 통과시키지 않는다.
- `runtime.py:61`의 ShortPolicy는 단음 schema를 검증한다. **새 작은 PrefixPolicy(FingerSkillPolicy 상속)**에 독자 schema 검증과 원 ShortPolicy의 선택4 freeze/mask/std 설정 약20줄을 명시적으로 재사용/필요복제한다. 원 tensor 구조/초기 RNG draw 순서는 보존한다. `variants.policy_type`은 ShortPolicy를 하드코딩하므로 factory를 억지로 감싸지 않고 원 B descriptor만 재사용해 새 ctor에서 fresh=True일 때만 cost weight/bias2개를0으로 한다. old schema 임시 치환·거짓 단음 contract·policy 생성 후 정체성 덮어쓰기는 하지 않는다.
- `index_prefix_4_7_8_v1/prefix_runtime.py:19` `view_and_catalog`, `:73` `PrefixPool._wrist_feedback`과 staged `index_prefix_release_transfer_v1/schedule.py:16` `wrist_weight`를 재사용한다. **새 local PrefixLearningEnvironment의 작은 초기화 adapter**로 원 catalog/focus/episode 기능을 재사용하면서 새 schema/실제 정책 scope를 처음부터 정확히 저장한다. inherited noNN 진단 문구도 실제 범위로 갱신한다. frozen prefix module의 schema/원자료는 바꾸지 않는다.
- `prefix_runtime.py:97` 3음 compact를 재사용한다. 이것은 내부에서 `runner.compact_episode`를 다시 호출하므로 단순 alias 대입은 재귀가 된다. 원 single compact를 먼저 보존하고, 동기 compact 호출 동안만 그 원 alias로 되돌려3음 helper를 호출한 뒤 finally 복원하는 좁은 seam을 CPU 검증한다. `_train`/collector를 복사하지 않는다.
- `prefix_runtime.py:116` 기존3음 evaluator는 **hard4/reference-only**다. 원 단음 `_evaluate:178`도 scalar selected_index/단음 trace를 가정한다. 새 local3음 eval adapter는 기존 quota/reset/compact/trace 루프를 최소 일반화해128·policy/reference/zero/random을 받는다. policy branch는 NN을 그대로 사용하고 N은 reference branch에만 둔다. 별도 generic evaluator/collector를 만들지 않는다.
- `low_effort_index_learning_v1/probe.py:83` `verify128`와 `:105` `effort_scope`를 재사용한다. 새로운 LearningPool alias를 먼저 준비한 뒤 cap scope→검증된 Pool→새 descriptor/guard 순으로 구성하여 실제128×105 readback/90pair/controller cap을 policy 생성 전에 확인한다. hard4/135/180 검사를 숫자만 바꿔 우회하지 않는다.
- `index_candidate_dip_guard_v1/probe.py:39` low-level `target_filter`는 재사용할 수 있다. `:75` observer는 selected_index4 고정/첫시도 영구 mask/episode 길이 budget이므로 **train에 그대로 쓰지 않는다**. 학습은 매 reset의 새 episode에 guard를 적용하고 300업데이트 전체를 유지한다. eval만 완료-env retry를 집계에서 제외한다. 원소별 현재goal gather·epoch 통계 정도만 추가하며 전체105 body 로그를 전128에 늘리지 않는다.
- 기존 renderer는 strict loader/camera/encoder를 재사용할 수 있으나 단음 checkpoint-schema/selected_index/target-count1 metadata가 있어 **3음 정책영상에 CLI만 바꿔 직접 쓰지 않는다**. 후속 최소3음 schema/metadata/trace adapter는 새 PrefixPolicy·동일 guard 계약·fresh=False를 사용한다. old spec.SCHEMA나 reference/noNN 문구로 정책실행을 위장하지 않고, renderer가 호출하지 않은 evaluator fingerprint를 수행했다고 표기하지 않는다.

## 실행 전 고정할 분모·판정

| 단계 | 분모 및 실행 | 사전 판정 |
|---|---|---|
| 비NN precheck | reference/zero/random 각128 첫시도=384 attempts/1,152 note opportunities. 실패/미도달도 분모에 포함. | reference의 각음 달성≥90%, 각음 평균clean≥.90/wrong≤.10, all3달성≥90%, 물리/손목실패0을 **music_passed**로 저장. A의 원 native released latch 비율≥90%를 독립 **release_passed**로 저장. **stage_ready=music_passed AND release_passed**가 train gate. zero/random은 실패를 요구하지 않고 전체 공개. |
| fresh NN 학습/고정평가 | large128/H32/seed7/300·50간격. 1,228,800 raw transitions; initial/50/100/150/200/250/300 각128=896 attempts/2,688 opportunities. | 각 고정평가의 **모든3음 각각** 달성≥.90/clean≥.90/wrong≤.10, all3달성≥.90, 물리/손목실패0이 music_passed; A release≥.90이 release_passed; 둘의 AND가 stage_ready. initial을 제외한 인접50→100…250→300 중2회 연속을 각 판정별로 보고. |
| 후반 유지 | 200/250/300 세 평가를 모두 공개 | 세 시점 모두 위 음악/all3/실패 기준 통과 여부와 A release 기준을 각각 별도 보고. 앞쪽 best 단일 평가로 후반 유지 실패를 가리지 않음. |

A release는 기존 `gpu/environment.py:1011`의 candidate falling edge·ever·원 end..end+.1s native latch를 그대로 사용한다. **원 음악 성공에 release를 섞어 재정의하지 않는다.** 이는 전체 피부분리/낮은 하중 인증이 아니다. B7/B8은 같은 위치/shared press이므로 사이의 별도 release를 새 성공조건으로 강제하지 않는다. B7/B8 및 말미 release latch/시각·이동 중 재접촉·몸체합력은 모두 공개한다. PIP/DIP/선택4 actual-target/범위체류·arm/wrist 추종·9항보상·actual failure cost와GAE/critic·개입/negative 통과는 진단이며, 임의의 자연성/힘/각도 문턱을 추가하지 않는다.

plain precheck는 NN 없는 Gaussian→tanh/zero/scripted reference이며 NN initial0과 다르다. 기존 검수된 `Actions` provider(mean0/std .1711710544767014/seed7/local Generator)는 가변128 batch를 지원하므로 재사용한다. fresh NN은 원 seed7·float32·initial_std·optimizer를 유지하고 cost final head2개만0이다. CPU에서 동일 새 contract의 기본 초기화와71 tensor exact+cost2zero/RNG·actor/reward critic/std/optimizer 구성을 비교하고, 기존 B initial과도 **model-only** 동일성 가능성을 검사하되 계약 정체성과 분리한다. 결과 전73/71/RNG exact를 단정하거나 old checkpoint를 새 과제로 strict resume하지 않는다.

7평가는 모두 공개한다. best 사전순위는 `(all3달성률, 3음 평균clean, −3음 평균wrong, −물리OR손목실패율, update큰순)`이며 latest300은 별도다. 같으면1모델, 다르면2모델의 동일128 env0 손/전신 영상을 후속 검증한다. 자연성/해제의 시각적 인상을 순위로 쓰지 않는다.

## 승인 뒤 단계와 CPU 확인

- [x] root PLAN 검토/승인과 staged 실제분석 독립 PASS/SHA 확인. 승인된 새폴더의 CPU 준비만 진행한다.
- [x] 새폴더 최소 wrapper/adapter만 구현. active/원 runner·정책·보상·native/default J33/기존 준비/결과 변경0.
- [x] CPU: 원67 targets/3opportunities/timing·354tick·기회선택 경계/none/부분reset/달성무관, training 매episode guard 재활성/negative·104열, NN선택4 첫tick 제어, compact 비재귀/alias·실제virtual ctorreset/닫기2차오류보존, 원128 cap helper의불법count/속성거부, 새strict same-load/old교차거부/freshFalse head보존·초기/RNG 비교 통과. source의N호출은reference branch만이며 새native 메모리/scene/관측/목표주입 실제정합은 root128사전대조에서 확인한다.
- [ ] fresh stdlib gate/전체 입력·settings·source/checkpoint 계약 봉인/독립 준비검수 PASS 뒤 root만128 precheck3scene 실행. actual 독립 PASS와 사전 gate 통과 전 train 명령은 거부.
- [ ] root만 fresh300+7평가8scene 실행. 전체 실제 종료 전 결과생성0. CPU 실제분석+독립검수, 선택 best/latest 후 영상QA. 한 seed·고정 기타/finite wrist 조건부 F4이며 자유 기타/J33/다른손가락/전곡으로 확대하지 않음.

정상 무실패/동일354tick만 계속된다는 가정에서는 9600control/env의27회 완료×128=3456episode와42×128=5376open raw transitions가 예상된다. 이는 actual clock/failed/reset 로그로 검산할 예상일 뿐 사전 확정값이 아니다. 세음 audible 합1.2965s/5.9≈21.97%로 과거 단음과 노출 비율도 달라지므로 결합조건 결과를 원 B cost-only 인과비교로 부르지 않는다.

CPU 초기검사에서 새 policy 기본생성과의73중71 동일/cost2zero·RNG 동일, 기존 B initial과의model73 exact를 확인했다. 이는 CPU float32 모델값 비교이며 새 native 초기값/환경성과·full trainer 이전을 보증하지 않는다. 이 PLAN은 독립준비검수·최종봉인 이후 동결하고 이후 실행진행은 root status/master에만 기록한다.
