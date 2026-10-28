# 검지 원곡 source4→7→8 최소 prefix 계획

**계획만 작성. 구현·GPU/native 실행0.** 기존 source/준비/단음 결과를 수정하지 않는다. A112 source4와 평행이동 source7의 각각4/4 단음 긍정 기록은 전환 성공 증거가 아니다. source7의 actual 독립검수와 이 계획의 root 검토 뒤에만 새 구현을 결정한다.

## 범위·원곡 시계

원 `make_task`의67개 target와 순서/ID/press/onset/end/source provenance를 전부 보존한다. 새 focus/selected mask는 검지 source index `[4,7,8]`만 true이고 다른64개는 false이다. 다른 손가락 source5/6/9/10을 수행하지 않는 **조건부 단일finger prefix**이며 원곡 전체 구간 재현이 아니다. 해당 목표·기하를 지우거나 원 wrong predicate/virtual string을 수정하지 않는다.

offset은 source4의 원 SongTask onset5.4497−3 = **2.4497s**로 고정한다. 아래 local 시간에 원 시계와 같은3초 pre-roll을 반영했다. source7/8은 physical2현5fret/finger1이며 같은 원 press/release를 공유한다.

| source | physical 현/fret | local press | local onset | local end | 원 audio release |
|---|---|---:|---:|---:|---:|
| 4 | 3/4 | 2.8800 | 3.0000 | 3.1703 | 2.6200 |
| 7 | 2/5 | 3.8320 | 3.9520 | 4.7299 | 5.1548 |
| 8 | 2/5 | 3.8320 | 5.3568 | 5.7051 | 5.1548 |

source7 end는 audio4.1796이며 공유 release5.1548까지 늘리지 않는다. source7→8의 무음 gap에서도 B 목표를 계속 유지하고 강제 retract/해제/상태 overwrite를 하지 않는다. 원 native `released/release_s`는 각 음 end 후 candidate 상실로 정해지는 별도 latch이다. 따라서 B7에서 release가 기록되지 않아도 공유 release나 B8 성공을 새로 정의하지 않는다. 실제값을 그대로 보고한다.

## 354tick의 근거와 원 catalog와의 차이

원 `song/finger_phrases.py:build_phrase_catalog.interval`의 end/next_press control 경계 산술을 이 조건부 검지 view에 재사용한다. 마지막 local end5.7051, 다음 제외 검지 group `[11,12]`의 원 press8.3599−offset2.4497 =5.9102s이다.

- `minimum=floor(5.7051*60+1e−9)+1=343`.
- 원 tail0.5초의 `desired=ceil((5.7051+.5)*60−1e−9)=373`.
- `maximum=floor(5.9102*60+1e−9)=354`; `ticks=min(desired,maximum)=354`.
- `5.7051 < 354/60=5.9 < 5.9102`; 마지막 음은 자연종료 전에 끝나고 다음 검지 press에는 들어가지 않는다. 물리 상한1416endpoint이다.

원 **all-finger** overlap catalog는 실제 `[7,8,9,10,11,12]`를 한 그룹으로 묶으므로 이3음 view를 그대로 반환하지 않는다. 새 view는 다른finger를 제외한 검지 조건에서 동일 interval 산술을 쓰는 새 진단 계약이다. 기존 catalog의 closed-group/full-song 보장이나 단음 `spec.subset`의 무조건0.5초tail373tick과 동일하다고 주장하지 않는다. 이 차이를 계약/보고서에 명시하고 원67행 자체는 불변 검증한다.

## 유일한 새 동작 가설

원035 초기상태에서 첫2초 A teacher/ref112로 이동하는 ramp, arm12 feedforward·quaternion·선택4 reference각 상수·엄지035/비선택B·cap0.25/원90pairs·K/D·native/actionbounds·4rad/s·wristv3/.5도cap을 보존한다. 원 A 목표를 local3.1703까지 유지하고, **A end3.1703→B press3.832** 사이에 wrist_position_G만 A→B로 선형 전환한다. 이후 끝5.9까지 B 목표를 유지한다. 이동량은 검증된 원 cell-center ΔG29.523457mm, 목표 평균속도 약44.6176mm/s이며 이는 물리 추종속도 보장이 아니다. 동일 quaternion/arm12를 유지해도 원 wrist feedback이 실제 팔 요청을 바꾸는 효과는 남는다. 새 joint gain/속도/힘 gate·강제 q대입·임의 release는 없다.

## 필요한 최소 연결점

1. **view/catalog/environment:** 기존 단음 `spec.subset`와 ShortEnvironment의 single-note view 검증만 명시적인 새 Prefix view로 대체한다. 원 SimplifiedFingerEnvironment의 측정/원장/보상/실패·FingerSkillEnvironment reset/sampler를 재사용한다. `selected_indices=(4,7,8)`, opportunities검지3·presentfinger1을 선언한다. 원 view 기반 reward 정규화도3기회로 계산하고 단음 n=1 가중치를 몰래 유지하지 않는다. 새 prefix descriptor/입력SHA를 pool 계약 생성 전 포함하며 기존 단음 strict identity와 혼용하지 않는다.
2. **teacher:** 기존 ShortPool/wristv3/trajectory_actions/effort wrapper를 유지하고 desired wrist 위치만 위 piecewise 함수로 공급한다. 원 initial ramp·팔 proposal·실제target메모리·별도 previous_request/rate/bounds는 그대로다. 단음 `_wrist_feedback` 목표가 하나라는 지점만 새 진단에서 명시 대체한다.
3. **compact/evaluate/trace:** 기존 `compact_episode/_evaluate/summary`는 단음만 집계하므로 그대로 호출하지 않는다. 원4quota/첫시도·실패 endpoint/최대354tick 수집 틀을 재사용하되 각 종료행에 source4/7/8의3개 note ledger를 모두 기록하고 전체67 target ID 매핑을 보존한다. `released/release_s`는 원 compact/left_note_ledger에 빠져 있으므로 새 환경 `_episode`에서 reset 전 native note의3선택 latch를 추가 관찰한다. 원9지급보상은 episode합계 그대로 보존하며 임의 음별 분해하지 않는다. env0 trace에는 같은 시각의3 target candidate/wrong/geometry와 teacher phase/goal을 저장하고 다른3환경 상세힘을 추정하지 않는다.

## 구현 전후 검증·수용 조건

CPU에서 원67행 SHA/내용·선택3mask·source 순서/공유press-release·offset·독립354 산술, 3note catalog/기회수·기하·선형함수 양끝/연속성/유한값을 검사한다. A/B arm12/quat/선택각 exact·변화는 위치일정뿐임을 확인한다. joint target rate/native/action bounds·현재strict 계약/old 단음교차거부·4quota(초기실패/재시도 제외)·3음 모두/해제 latch·오류시 alias/loader복원·기존출력/symlink 보호를 합성fixture로 검증한다. CPU 독립검수와 새 봉인 뒤 root만 단1scene4첫시도 실행한다.

native에서는105속성·16 cap0.25/기타89·90쌍·입력전후·sceneclose·실제launcher0와354control/1416physics 상한(공유장면, 각환경 동일 시계상한)을 확인한다. 각음4분모와 전체4시도 분모를 함께 보고, 각음 원 achieved/clean/wrong/fail 및 전체3음 동시충족을 별도로 제시한다. 원 acceptance의4/4·clean≥.70·wrong≤.10·fail0 기준을 각음/전체에 그대로 적용하되 release latch는 별도 원값으로 보고하고 새 성공 gate를 발명하지 않는다. 실패시 특정 음/전환/손목/loaded/geometry·실제각을 분리하고 B 불가능 결론이나 조건확장을 하지 않는다. 성공도 자유기타/J33·학습·전곡·자연성·영구채택 증명이 아니다.
