# A150 이후 wrong 붕괴: 기존 raw의 원인 분리

2026-10-27. CPU 재판정만 수행했다. 기존 소스·봉인·원자료를 수정하거나 GPU/native 실험을 실행하지 않았다. 원자료/hash·재계산 방법·정확한 수치는 [WRONG_PRESS_CASES.json](WRONG_PRESS_CASES.json)에 기록했다.

## 전체128과 env0의 범위

`A_time_discount_30s_seed7/evaluation_000150/evaluation.json`은 126/128 달성, 평균 audible wrong fraction 0.013358이다. 200·250·300은 각각 0/128 달성이고 모든 시도의 audible wrong fraction이 1이다. 분모는 실패를 포함한 배정128시도다.

아래 원인 분리는 **env0 첫 시도의 저장60Hz 끝점 8개(3.000~3.1167초)**에 한정한다. 목표는 `event-000052/string-3/note-53`, 중지·**물리3현7프렛**이다. 이 문서와 JSON의 physical string은 모두 **1-based**이며 raw `string=2`와 구분한다. 전체 음 창은 local3.000~3.1174초이고 내부240Hz 원인 전이는 저장되어 있지 않다.

| 모델 | env0 audible8끝점의 재판정 |
| --- | --- |
| A150 | assigned-pad positive/candidate 참, wrong 거짓: 각각8/8 |
| A200 | 중지 distal pad(`human/LH:middle3`)의 `own_wrong_fret`: 3현6프렛. 동시에 `own_wrong_string`: 2현6·4현6프렛 후보. 각 cause8/8 |
| A300 | 중지 distal pad의 `own_wrong_string`: 1현8·2현8프렛 후보. cause8/8 |

A200·300의 다른 손가락 `other_higher` flag는 모두0/8이었다. 이 끝점에서는 다른 손가락이 목표현의 더 높은 프렛을 막았다는 설명을 지지하지 않는다. 두 모델 모두 중지 distal body의 loaded gate는8/8 참이지만 목표3현7프렛의 any-sample position/facing/positive는8/8 거짓이었다. 이는 올바른 positive가 다른 손가락 때문에 차단된 상황과 구분된다.

## nearest와 any-sample을 구분

저장 `surface_distance_m`·`surface_height_m`는 목표에 가장 가까운 eligible 패드 표본 한 점의 값이다. positive는 **어떤 한 표본이 위치·방향·body-load 조건을 함께 만족하는가**로 판정한다. own wrong도 모든 qualifying 패드 표본을 본다. nearest의 높이/거리가 단독 성공 또는 오압현 witness가 아니다.

A150에도 중지의 qualifying 패드 표본 중 3현8·4현7/8프렛 후보가 있지만, 올바른 목표 positive가 있어 incidental own wrong은 억제된다. A200의 qualifying 셀 집합은 2/3/4현6프렛, A300은1/2현8프렛이었다. 이것은 유한 표본의 기하·하중 후보이며 실제 현 압력을 인증하지 않는다.

## 실제각과 목표각

env0 audible8끝점 평균(도). 순서는 `middle1_x, middle1_z, middle2, middle3`다.

| 모델 | 실제 q | target |
| --- | --- | --- |
| A150 | 65.3, 13.0, 59.5, −5.0 | 73.6, 3.5, 66.4, −5.0 |
| A200 | 58.2, −7.6, 54.3, −5.0 | 66.3, −19.8, 61.9, −5.0 |
| A300 | 69.7, 4.8, 78.9, −5.0 | 90.0, −20.0, 90.0, −5.0 |

엄지와 비선택 왼손 손가락의 env0 목표각 시계열은 세 모델 간 전체218끝점에서 동일했다(최대 차0rad). 실제 자세와 팔 손목 teacher 반응은 달라질 수 있다. 이 상태 비교가 학습 붕괴의 인과 원인을 확정하지는 않는다.

## 재현 근거와 한계

원자료는 `../A_time_discount_30s_seed7/evaluation_000150`, `evaluation_000200`, `evaluation_000300`의 `trace_env0_episode0.npz`, `trace_metadata.json`, `settings.json`, `training_contract.json`, `inputs_before.json`이다. JSON은 각 파일의 절대 경로와 SHA256을 포함한다.

원판정 소스6개의 현재 SHA가 세 실행의 기록 pin과 모두 일치했다. CPU에서 저장 body pose·net body force를 원래 함수에 넣고 candidate/wrong를 재계산했으며 각 실행8/8 저장값과 일치했다. 함수 위치는 다음과 같다.

- `guitar_learning/gpu/environment.py:547` `_contacts()`와 `:618`의 `candidate = positive & ~wrong`.
- `guitar_learning/gpu/simplified_finger_environment.py:117` `_left_wrong_contacts()`.
- `guitar_learning/gpu/wrong_press.py:21` `pad_contact_cells()`, `:46` `wrong_press_sources()`; 다른 손가락 higher는63행, own wrong은79~95행.
- `guitar_learning/gpu/fingertip_pad.py:177` `pad_target_geometry()`의 nearest/any-sample 구분.

CPU 메타데이터는 기존 `tests/test_gpu_environment.py:23`의 `fixture()`와 준비 자료에서 읽고 저장 joint/body 순서와 대조했다. joint qd는 raw에 없으므로0으로 두었으며 이번 위치·하중·wrong 판정에는 사용되지 않는다. 저장 body velocity는 보존했다. 새 물리 적분은 없다.

원래 raw에는 `wrong_source_flags`, 원인별 cell witness, `positive_before_wrong`가 직접 저장되지 않아 env0 끝점에서만 복원했다. 나머지127환경의 body pose/force와240Hz cause 원장이 없으므로 **전체128의 원인 분포와 음 창 내부의 모든 원인 전환은 알 수 없다.** distal 순접촉힘은 접촉 상대·현 압력·음향 성공을 인증하지 않는다.
