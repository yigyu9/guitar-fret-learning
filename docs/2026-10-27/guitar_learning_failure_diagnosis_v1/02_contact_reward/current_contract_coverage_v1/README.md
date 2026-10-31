# 원24목표와 현재 계약의 근거 연결

이 문서는 기존 결과의 연결표다. 새로운 GPU·native·NN 생성·checkpoint load·학습은 모두0이다. [manifest.json](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/current_contract_coverage_v1/manifest.json)의 `evidence`는 근거의 절대경로·SHA256, 각 `evidence` 참조는 JSON Pointer를 제공한다. mutable 상위 status/README를 실행 의존성으로 봉인하지 않는다. 원계획 파일은 읽은 시점의 문서 SHA로만 기록했으며 실행 입력 seal이 아니다.

## 확인된 범위

원선정24개를 순서·target_id·원곡 source index·줄·프렛·손가락·실제 음길이 그대로 보존했다. `targets[0..23]` 각각 원결과의 선택된67음 원장 위치를 대조했다. 원 actual-clock fixed/B/normal-guard 조건은 **6/24**, 검지2/6·중지0/6·약지2/6·소지2/6이다. 한 목표당1시도이며 실패를 제거하지 않았다. source press를 local3초에 맞춘 이 조건과, 이후 onset을 local3초에 맞춘 짧은 과제는 별도다. 당시 저장 report/settings에 명시되지 않은 초기자세·seed·관측차원·PD105는 unknown이다.

다음 네 positive는 모두 fixed guitar·incremental·합의035_v14 시작·finite arm/wrist teacher·비선택 B·private0.25Nm·seed7·4환경의 scripted reference 결과다. **4환경은4개 seed가 아니다.** NN 성능이나 한 공통조건의 네 손가락 평가로 합산하지 않는다.

| 손가락 | 원24행 | oracle grid 후보 | 원곡 source index | target event | positive |
|---|---:|---:|---:|---:|---:|
| 검지 | 1 | 112 | 4 | 4 | 4/4 |
| 중지 | 8 | 114 | 53 | 52 | 4/4 |
| 약지 | 16 | 해당 없음 | 54 | 53 | 4/4 |
| 소지 | 23 | 121 | 21 | 21 | 4/4 |

후보112/114/121은 grid 행번호다. 원곡 index나 event 번호가 아니다. 네 결과 모두 clean 평균1·wrong0·물리/손목 실패0이며 세부 조건/원분모는 `later_lowcap_physical_positives`에 있다. 중지 native-video 재현은 기존 reference의 추가 fresh 표본으로 합치지 않는다.

`lowcap_prelearning_controls.cases`는 reference/zero/random의 분모와 재사용 여부를 분리한다. 검지·중지·약지의 세 control은 해당 연구 내 settings가 exact다. 낮은 상한 약지는 reference4/4·zero0/4·random0/4다. 과거 원profile20Nm 약지는 reference4/4·zero1/4·random0/4이며 별도 `historical_original_profile_controls`에 있다. 낮은 상한 prelearning은 새40시도+재사용8시도이고, fresh48시도가 아니다.

소지는 조건을 특히 분리한다. 과거20Nm reference4/4와 **zero4/4**는 지원 제어 confound를 보인다. 이후 낮은 상한의 수정 전 reference0/4·zero0/4·random1/4는 또 다른 조건이다. oracle후보121의4/4에는 동일 후보각의 zero/random 결과를 찾지 못했으므로 unknown이다. 수정 전 대조를 후보121에 상속하지 않는다.

## 561→557와 물리 차이의 분리

위 네 positive의 계약은 **561 / finger_skill.v2**, 현재 V7의 저장 계약은 **557 / finger_skill.v3**다. 제거된 관측은 `phase_R`, `phase_F`, `phase_J`, `planned_ticks` 네 필드이고 추가 필드는 없다. 예전 NN/checkpoint/settings를 그대로 current557 RL에 넣을 수 없다. 관측벡터 차이만으로 과거의 실제 물리 positive를 무효화하지도 않는다.

직접 비교 결과 contact_measurement와 termination, 기존 native backend 공통 필드, 기존 action target 필드 및 incremental codec은 exact다. V7에는 별도의 index3 current-candidate DIP guard가 추가돼 전체 action 계약은 다르다. V7 reward는 success settlement가 추가됐고 surface_learning의 관측 설명은561→557로 바뀌었다. 따라서 같은 reward schema 이름만으로 동일한 제어/보상 조건이라고 쓰지 않는다.

네 positive의 실제 native PD105 전체10속성 배열은 V4 capture의 readback과 exact다. 원profile대비 변화는 index..pinky16축 effort20→0.25Nm뿐이며, 나머지89축(thumb5축 포함) 및 stiffness/damping/범위/속도 등은 유지됐다. 이는 private 진단상한이며 사람의 안전상한이나 생산 기본값이 아니다. **선택 V7 evaluation의 저장 training_contract에는 diagnostic_native_effort readback이 없다.** 상속된 loader/source와 과거 readback은 근거지만 새 V7 readback을 직접 확인했다고 주장하지 않는다. 실제 현재물리 동등성은 관측·문서 일치와 분리해 재검증한다.

V7도 selected index의 세음/고정기타 진단이다. 생산의 자유기타/J33 전체 NN 제어·원67음·여러 seed 성능으로 승격되지 않는다.

## negative와 엄지에서 남은 것

- 37실제 snapshot×67대상=2,479 정적 counterfactual은 자세·힘을 바꾸지 않고 target/time만 바꿨다. 원24개 각각의 새 closed-loop 실제 negative가 아니다. FK geometry, held static contact, 실제 원곡시계 achievement도 분리했다. shadow failure 뒤 결과는 검열된 근거다.
- 중지 source53의16시도 facing probe는 loaded back-facing witness0/16·stable50ms0/16이다. 실제 witness가 없다는 결과이며 불가능성 증명이 아니다.
- 같은 source53의 별도128시도 live short/release probe는 short-only17·stable50ms95·achieved53·물리/손목 실패0이다. 다른 손가락/현재557의 대응 negative를 대신하지 않는다. `joint`/`native_released`는 해당 probe의 정의이며 음악 전체성공이 아니다.
- 엄지 rear-surface의 fixed protocol은 통과했지만 free protocol은 실패했다. free release candidate41/360=11.39%가 선언된10% 미만 조건을 넘었다. 몸체 합력을 pair 압력으로 해석하지 않으며 현재 학습·자유기타·네 손가락 수행 중 실제 엄지부하는 미완료다.

## 다음 최소 준비안: 현재 계약 약지 scripted precheck

구현·실행은 아직 하지 않는다. 첫 확장은 원row16/source54 하나를 current557에서 reference/zero/random 각4첫시도로 재구성하는 것이 가장 작다. 낮은 상한의 기존 positive/두 대조가 모두 있고, 현재 검지 세음 학습과 독립적이다. 첫 사전검사 뒤 동일 계약의 나머지 세 손가락과 추가 seed를 결정한다. full grid나 새 장기학습은 필요 없다.

최소 재사용 경로는 현재 `guitar_learning.tool.experiments.short_finger_learning`의 `runner.make_settings(args)` → `runtime.ShortPool(settings,out)` → `runner._evaluate(...)`다. historical 전체 probe chain을 import하지 않는다. [기존 loweffort probe](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/low_effort_finger_prelearning_v1/probe.py)의 작은 `Actions`(NN 아님)와 scene 생성 시에만 적용하는 [effort_loader / verify_native](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/probe.py)의 동작을 참조한다. 기존 V1 index/세음 Environment는 약지에 재사용할 수 없다.

- teacher: `03_short_learning/other_finger_precheck_v3/teacher_ring_row16.json`
- reference: 같은 폴더의 `reference_ring_row16.json`
- make_settings 인자: `teacher=절대경로, mode=incremental, initial_std=0.1711710544767014, song=05_BN2-131-B_solo, size=large, seed=7, num_envs=4, horizon=32, updates=1, save_every=50`.
- evaluator 인자: `pool`, full39를 반환하는 noNN `Actions(selected=[25,26,27,28],control)`, `pool.spec`, `Namespace(control=reference|zero|random, reference=절대경로, episodes=4)`, 새 출력폴더. reference는 원래 evaluator의 유한 ramp/trajectory를 사용한다. random은 별도 generator seed7의 매tick Normal[4,4]×동일std 후 tanh이며 학습정책 exploration과 동일하다고 부르지 않는다.
- 이전 저장 CPU fixture는561을 가정하고 과거 동적 import/봉인을 포함한다. current make_settings의557/Jv3와 새 source pins로 재생성해야 한다. `read_teacher/read_reference`의 외부 source_evidence SHA와 target 검사는 유지하고, 불일치는 중단 사유로 기록한다. R/F나 옛 checkpoint 호환을 되살리지 않는다.
- CLI의 `evaluate`는 checkpoint를 load하고 `train`은 NN을 만든다. 두 CLI를 그대로 사용하는 안은 noNN 사전검사 요건에 맞지 않는다. 현재 evaluator에 작은 scripted action provider만 넘기는 조합을 준비한다.
- 0.25Nm를 유지한다면 private loader는 scene constructor 범위에만 두고 finally 복원한다. actual PD105/90 collisionpairs·guard·유한 제어·비선택 지원·동일 시계·모든 실패의 분모·reset 전 첫 시도·scene close/primary error 보존을 검수한다. 관측 필드 차이를 감추는 wrapper는 만들지 않는다.

새 scripted4/4가 나와도 원수용기준을 바꾸지 않는다. 손가락별 달성80%·clean70%·wrong10% 이하·물리실패5% 이하를 실패포함 분모에서 연속2회 확인해야 하며, seed7/17 선별 후27 확인·자유기타/J33·원67음·영상·실제 엄지부하는 별도 남아 있다. manifest 작성은 이 조건들의 통과를 뜻하지 않는다.
