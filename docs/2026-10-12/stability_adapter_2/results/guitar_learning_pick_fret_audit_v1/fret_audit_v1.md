# 현재 압현 판정·보상 읽기전용 감사

현재 경로는 **기존 fret 보상을 그대로 쓰지 않는다.** 지정한 현·프렛·손가락에 유효한 접촉이 있는지는 여러 조건으로 검사하지만, 정상 압현·오압현·미압현을 서로 배타적인 음악적 상태로 완전히 분류하는 구조는 아니다. 목표 접촉이 하나라도 유효하면 다른 접촉이 동시에 있어도 현재 후보 판정은 참이다. 오압현에 대한 별도 적극 감점도 현재 타이밍 보상에는 없다.

이번 감사는 코드와 저장된 실제 실행을 읽기만 했다. 판정 기준·보상·학습·원자료는 변경하지 않았다.

## 1. 현재 target candidate가 참이 되는 조건

대상은 물리2번현·7프렛·약지다. 매240Hz 표본에서 현재 움직이는 기타 좌표계의 실제 body/contact 상태를 사용한다. 아래 조건을 **모두** 만족하는 접촉 feature가 하나 이상 있어야 한다.

| 조건 | 현재 기준 |
|---|---|
| 손가락 몸체 | 지정 손가락의2번 또는3번 body. 이번 목표는 `LH:ring2` 또는 `LH:ring3` |
| 기타 몸체 | `guitar/guitar` 또는 목표 프렛 몸체 `guitar/G:fret7` |
| 실제 접촉 신호 | raw native `lambda > 0`; 보정된 힘 N이나 현 압력은 아님 |
| 양쪽 접촉 feature 일치 | 같은 접촉 쌍의 world witness 간격≤0.0001m(0.1mm) |
| 현 구분 | 해당 y에서 실측한 여섯 현 가운데 목표 현이 유일한 최근접 현이어야 함 |
| 유한 현·가로 위치 | 목표 현 선분 안이며 lateral 거리≤3mm |
| 높이 | 목표 현 높이와 차이의 절댓값≤3mm |
| 프렛 위치 | 목표 프렛의 양쪽 wire 경계로 구성한 cell에±2mm margin을 포함한 범위 |

근거: [접촉 판정 조건](/home/ajou/yigyu/3/guitar_learning/fretting_v1.py:86), [명시 임계값](/home/ajou/yigyu/3/guitar_learning/fretting_v1.py:24), [유효 feature의 OR로 최종 후보 결정](/home/ajou/yigyu/3/guitar_learning/fretting_v1.py:145).

`marker_approach_distance≤15mm`는 손가락 distal body 원점과 프렛 중간 목표점 사이의 별도 진단이다. 이 거리 조건을 통과해야 접촉 후보가 되는 것은 아니다. 실제 후보는 위 접촉 feature 조건으로 정한다. 또한 `FretContract.minimum_dwell_s=.05`가 설정되어도 raw candidate 자체는 순간 접촉 판정이며, 연속 유지 조건은 ledger가 별도로 처리한다. [진단과 후보의 분리](/home/ajou/yigyu/3/guitar_learning/fretting_v1.py:148), [측정기 설정](/home/ajou/yigyu/3/guitar_learning/task_measurement.py:23).

## 2. 오압현·미압현이 어떤 형태로 기록되는가

| 기록 | 실제 의미 | 보상에서의 사용 |
|---|---|---|
| `wrong_finger_or_disallowed_human_body` | 이 목표의 허용 손가락 body가 아닌 feature | 해당 feature만 거절. 독립 오압현 감점 아님 |
| `wrong_fret_or_disallowed_guitar_body` | 기타 root 또는 목표 프렛 body가 아닌 feature | 해당 feature만 거절 |
| `wrong_string_or_ambiguous_lane` | 목표 현이 최근접 현이 아니거나 동률로 모호함 | 해당 feature만 거절 |
| 기타 거리·높이·cell·witness 거절 이유 | 해당 feature가 목표 접촉 조건을 만족하지 못함 | 해당 feature만 거절 |
| `candidate=False` + `no_qualifying_same_finger_native_contact` | 목표를 만족하는 feature를 찾지 못함 | 유효 유지 보상을 받지 못함. 지속 실패는 시간창 종료 후 miss 처리 |
| `wrong_crossings` | 목표 음악에 매칭되지 않은 우손 피크 통과 또는 타이밍 ledger의 창/방향 불일치 | 압현 오류와 별개인 타현 항목 |

이유들은 한 feature에 여러 개가 함께 붙을 수 있다. 정상·오압현·미압현의 배타적인3개 class가 아니다. 특히 전체 human–guitar 접촉을 순회하므로 가슴·오른팔·허벅지의 정상적인 기타 지지에도 `wrong_finger...`가 붙는다. 이 raw 이유 개수를 오압현 횟수로 세면 안 된다. [전체 접촉 순회와 개별 거절 이유](/home/ajou/yigyu/3/guitar_learning/fretting_v1.py:92).

`candidate=False`만으로 “아무것도 누르지 않았다”와 “다른 손가락·현·프렛을 접촉했다”를 구분할 수 없다. 원자료에는 이 차이를 살펴볼 evidence가 있지만, 현재 runtime은 이를 별도 음악 오류 class로 집계하지 않는다. 정상 목표와 잘못된 feature의 동시 존재도 최종 후보를 무효화하지 않는다.

## 3. 이전 fret 구현과의 차이

이전 `tab2body`의 `FretReward`는 손가락 segment의 기하 pad-depth와 hysteresis로 현×손가락×프렛의 압현 상태를 만들었다. 현재는 위에서 설명한 **native 접촉 feature를 조건으로 한 목표별 후보**를 사용한다. 동일한 판정기나 동일한 보상식을 그대로 가져온 것이 아니다. [이전 geometric press state](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:1920).

이전 구현은 `fret>0`을 PRESS, `fret<0`을 NO_PRESS, `fret=0`을 DONT_CARE로 구분한다. 양수 목표에서는 목표 프렛보다 높은 프렛을 NO_PRESS로 설정하고, 금지 프렛에 압현이 하나라도 있으면 `wrong_press=True`가 된다. 목표 손가락이 목표 프렛을 누르고 있어도 이 오압현이 있으면 `physical_press`를 무효화한다. NO_PRESS 성공·오압현 회피·오압현 감점 및 PRESS/NO_PRESS 보상 균형도 있다. 설정 파일의 `wrong_press_penalty`는0.35다. [이전 요구 마스크](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:932), [이전 오압현 veto](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:2275), [이전 NO_PRESS와 회피 항](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:2400), [이전 명시 감점](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:3002), [이전 기본 설정](/home/ajou/yigyu/3/tab2body/cfg.py:91).

현재 fretted target 경로에는 이와 같은 전현·전프렛의 금지 압현 veto가 없다. 목표보다 높은 프렛, 다른 현의 추가 접촉, 불필요한 손가락 접촉이 존재해도 목표 feature가 유효하면 후보가 유지될 수 있다. 이전의10–90% 위치 성공 조건과 현재 wire cell±2mm 조건도 동일하지 않다. [이전 위치 성공 조건](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:2307).

현재 음악 이벤트의 열린현 `fret=0`은 이전의 DONT_CARE와 다르다. 일반 `TaskMeasurement`는 열린현에서 엄지를 포함한 손가락2/3의 양성 접촉이 해당 현 lane을 막는지 검사하는 별도 clear-candidate 분기가 있다. 다만 현재 actionable timing 환경은 **단일 fretted target만 허용**하므로 이 열린현 분기는 이번 학습·평가에서 사용하지 않았다. 열린현 obstruction 진단도 실제 소리·뮤팅의 검증은 아니다. [열린현 blocker 검사](/home/ajou/yigyu/3/guitar_learning/task_measurement.py:76), [현재 단일 fretted target 제한](/home/ajou/yigyu/3/guitar_learning/actionable_preparation_environment.py:88).

## 4. 지금 학습에 실제 들어가는 보상

기본 환경에는 strict/lenient 음악 매칭, wrong crossing, strict miss, audible hold, timely release, 거리 접근 보상이 구현되어 있다. 그러나 그 값들이 현재 최종 보상으로 모두 전달되는 것은 아니다. 먼저 skill wrapper가 교체하고, timing wrapper는 다시 **`action_change`·`terminal_failure`만 남긴 뒤 timing 항으로 대체**한다. actionable wrapper가 첫2초의 실제 후보 접촉 준비 보상만 추가한다. 계약에 예전 보상 계수가 남아 있다는 사실과 현재 reward 합에 그 항이 들어간다는 것은 구분해야 한다. [기본 보상](/home/ajou/yigyu/3/guitar_learning/training_environment.py:125), [skill 교체](/home/ajou/yigyu/3/guitar_learning/skill_environment.py:297), [timing 교체](/home/ajou/yigyu/3/guitar_learning/timing_environment.py:131).

현재 왼손 stage1은 다음 방식이다.

- press−0.5초부터 end+0.5초 사이의 유효 후보 접촉 구간에2.0/s 유지 보상을 준다. 이전·현재 표본이 모두 양성이어야 실제 구간 길이를 적분한다.
- 첫 유효 후보 획득에0.25, 현재 단계 유지 성공에1.0을 한 번씩 주며 press 시각과의 가까움에 정밀도 보상을 준다.
- stage1 유지 성공은 연속 약92.88ms다. 이번 원 audible 길이232.2ms의40%이며, 전체 audible coverage100%와 같은 성공 조건은 아니다.
- 한 번 단계 목표를 달성하면 `achieved`는 유지된다. 이후 접촉 상실은 유지 보상 감소와 release 이력으로 기록되지만, 별도 오압현·dropout·해제 감점은 없다.
- 미달 상태가 window 끝을 지난 첫240Hz 표본에서 `timing_missed=-0.5`를 한 번 받는다. 이번 window는[3.5,4.8522]초이며 해당 첫 표본은 약4.854167초다. 즉 목표를 안 누르는 매 표본에 적극 감점하는 구조는 아니다.
- 첫2초 준비 보상은 원 target candidate의 이전·현재 양성 구간만0.2/s로 적분한다. 거리 proxy 보상은 사용하지 않는다.

[왼손 유지·획득·정밀도·단계 성공](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:123), [miss 시점과 계수](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:192), [준비 접촉 보상](/home/ajou/yigyu/3/guitar_learning/actionable_preparation_environment.py:53).

원 joint-music strict miss는 onset+50ms를 지난 시점의 별도 측정 이력이다. 이것은 현재 왼손 stage1 miss와 다르며, 원 `missed_strict` 보상은 timing wrapper에서 제거된다. 우손 타현이 없는 왼손 단독 시험에서는 압현 coverage가100%여도 joint music 매칭은0일 수 있다. [원 strict miss](/home/ajou/yigyu/3/guitar_learning/task_measurement.py:154), [원 접촉조건 음악 매칭](/home/ajou/yigyu/3/guitar_learning/music_task.py:248).

## 5. 최신 실제 왼손 평가에서 확인한 동시 접촉

분석 대상은 actionable preparation의 최신 왼손 PPO 평가 **1회·420제어 tick·1,680개240Hz 표본**이다. 목표는2번현7프렛약지이며, 원 audible coverage는100%였다.

| 항목 | 실제 분모·값 |
|---|---:|
| 목표 후보 참 | 963/1,680표본 |
| 목표 후보 거짓 | 717/1,680표본 |
| raw human–guitar evidence | 28,074 feature records |
| 유효 목표 evidence | 2,658 feature records |
| 목표 참이면서 다른 rejected evidence도 존재 | 963/963 목표 참 표본 |
| 지지부위를 제외한 좁은 넥 접촉 진단에서도 rejected feature 공존 | 963/963 목표 참 표본 |
| 좁은 넥 접촉 진단의 rejected feature | 2,585 records; 음악 오류 횟수 아님 |

좁은 진단은 LH 손가락2/3·기타 root 또는 fret body·양성lambda·witness≤0.1mm·실측 최근접 현에 lateral/height≤3mm·실제 넥 cell 내부인 feature만 별도 모은 것이다. 기존 판정을 재정의하거나 학습에 반영한 것이 아니다. 기타 지지의 허벅지 접촉을 오압현으로 세는 오류를 피하기 위한 읽기전용 진단이다. 손가락의 다른 현 접촉이 실제 음을 바꾸거나 뮤팅했는지는 이 기준으로 인증하지 않는다.

실제 예시는2.991667초, physics step718이다. 목표 약지 접촉 `718:33`은 유효했고, 동시에 `LH:pinky3`–`G:fret8` 접촉 `718:31`도 있었다. 후자의 실측 최근접 현은3번, 기하 cell은8이었고 witness 간격은약3.32nm, 최근접 현 lateral은2.472mm, height는−1.332mm였다. 해당 feature에는 wrong finger/fret/string 등의 이유가 기록되었지만 **목표 후보는 참으로 유지**되었다.

0.1625초에는 목표 후보가 거짓인 상태에서 `LH:pinky3`–`G:fret8`, 최근접4번현·cell8의 좁은 넥 접촉도 있었다. 이때 최종 이유는 다른 미후보 표본과 똑같이 `no_qualifying_same_finger_native_contact`였다. 목표 미접촉과 다른 위치 접촉을 최종 class 수준에서 분리하지 않는다는 예다.

이 좁은 진단에서는 **목표와 같은2번현의 더 높은 프렛 접촉**은 별도로 관측되지 않았다. 따라서 이번 실행에서 그것이 실제로 발생했다고 주장하지 않는다. 코드가 그 경우를 전체 veto하지 않는다는 구조적 한계와 이번 원자료의 실제 발생 여부를 구분한다.

최근 실행의 최종 reward 합에는 `timing_hold=2.7044`, acquisition0.25, success1.0, precision0.5, 작은 action-change 비용이 있었다. miss·wrong crossing·preparation_contact는0이었다. 첫2초에는 목표 후보 자체가 없었고 최초 후보는2.991667초였다. 여기서 잘못된 넥 feature가 공존해도 별도 오압현 감점이 발생하지 않았다는 점을 확인할 수 있다.

## 결론과 범위

“목표 압현 후보를 인식하는가”에는 구체적인 접촉·기하 필터가 구현되어 있다. “다른 곳을 동시에 누르지 않고, 눌러야 할 때만 누르고, 필요한 때 떼는가”는 현재 후보·보상이 충분히 보장하지 않는다. 이전 fret의 오압현 억제·NO_PRESS 구조가 현재 경로에 그대로 남아 있다고 설명하면 부정확하다.

현의 실제 압력·진동·피치·음향·muting은 검증하지 않았다. raw lambda는 양성 접촉의 근거이지 보정된 압현 힘이 아니다. 이번 결과는 성공 상태 재분류나 판정기준 재설계의 근거로 자동 적용하지 않는다.

원자료 분모·feature 예시·이유별 counts·코드 SHA는 [기계 판독 감사 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_pick_fret_audit_v1/fret_audit_v1.json)에 보존했다.
