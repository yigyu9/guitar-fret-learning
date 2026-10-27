# 단계 2 접촉·보상 진단 준비

실행 결과와 현재 남은 검증은 [단계 2 결과](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/README.md)에 정리했다. 이 문서는 실행 전 조사 기록을 보존한다.

작성일: 2026-10-27. 기존 코드·보고서·저장된 240Hz 추적의 읽기 분석만 수행했다. 이번 문서 작성에서 GPU를 실행하거나 활성 패키지·기존 결과를 수정하지 않았다. 단계 1 제어 진단이 먼저이며, 아래 내용은 그 결과를 받은 뒤 실행할 최소 재사용안이다.

## 결론

기존 도구는 **기하 후보 탐색과 유한 제어 재생의 기반으로 재사용**할 수 있다. 그러나 기존 실행에서 중지·약지·소지가 실패한 주된 관측은 보상 부재보다 앞선 **실제 패드의 높이·프렛 셀 도달 실패**다. 기하 탐색에서는 16개 모두 후보였지만 실제 재생에서는 검지 2개만 접촉했다. 이는 실제 압현이 모든 손가락에서 가능하다는 증거가 아니다.

또한 현재 `press_acquisition.replay_geometry`는 `TensorSongEnvironment`를 직접 생성한다. 현재 학습의 `SimplifiedFingerEnvironment`에 있는 **오압현 v2, 최종 9항목 보상, 손목 종료 v2**를 검사하는 실행이 아니다. 이 차이를 유지한 채 정적 도달 검사와 현행 판정·음별 지급 검사를 구분해야 한다.

## 기존 도구가 하는 일

[press_acquisition.py](/home/ajou/yigyu/3/guitar_learning/tool/validation/press_acquisition.py)의 재사용 지점은 다음과 같다.

| 기능 | 실제 동작과 제한 |
| --- | --- |
| `select_targets` | 손가락별 빈도 최다·최저 프렛·최고 프렛·다음 빈도 순의 서로 다른 4목표. 총16개와 상세 저장 row0/4/8/12를 탐색 전에 고정 |
| `source_geometry`·`full_fk` | 준비 상태의 실제 q·몸체 자세로 보정한 source FK와 현재 source 메시의 패드128점·법선·지판 투영선을 사용 |
| `action_bounds` | 실제 controller의 팔12축 범위와 손가락 전체 native 범위를 반영 |
| `search_geometry` | 팔12축+해당 손가락4축만 최적화. 다른 손가락·엄지는 준비 참조 목표 유지. 각 목표2초기값·기본160회 평가의 국소 least-squares |
| 탐색 목적 | 프렛 셀 중심의 지판면 −0.5mm에 패드점 접근, 법선cos0.3 미달 및 참조 자세 편차에 약한 항. 실제 충돌·하중·오압현·궤적의 실행 가능성은 목적에 없음 |
| `trajectory_actions` | 원하는 유한 목표각을 기존39차원 행동으로 역변환. 누적 손가락 재생 속도는 기본1rad/s 이하이고 native 상태/목표를 직접 덮어쓰지 않음 |
| `integral_tracking_offset` | ramp 뒤 팔12+지정손가락4만 gain1.5/s, offset±0.1rad의 진단 보정. 실제 오차에 의존하므로 fixed/free에서 동일 명령이 되지 않음 |
| `replay_geometry` | 같은 단일 강체89형상 `GpuScene`의 fixed/free, 기존 `BatchedController`·기본 `TensorSongEnvironment` 측정·물리 안전 재사용 |
| `pad_axis_flags` | cell/lateral/height 각각에 대해 any-sample 통과. 세 값이 모두 참이어도 같은 표본이 동시에 통과한 뜻이 아님 |
| `diagnostic_streak` | 양끝 candidate가 참인240Hz 구간의 연속시간. 정적50/100ms 지표이며 원곡 음 달성·음 길이 보상과 다름 |

기존 v3는 초기0.5초+6초 ramp+6초 hold, 750제어tick/3000물리step이다. 실패 행은 첫 물리 실패 이후 통계에서 제외하고 다른 행이 끝날 때까지 유한 명령을 유지한다. 전체 목표별 요약은16행이지만 상세 추적·자세는 row0/4/8/12만 있다. `render_replay`는 저장된 실제 자세를 MuJoCo로 재생하며 native 카메라 평가 영상과 구분한다.

## 기존 결과에서 확인한 실패 지점

[기존 보고서](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/README.md), [fixed feedback 원문](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/fixed_feedback_v3/report.json), [free feedback 원문](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/free_feedback_v3/report.json)을 재확인했다. 아래 줄 번호는 `physical_string`의1부터 세는 값이다.

| 손가락·대표 목표 | fixed/free 전체 최저 거리 | 기존 free v3의 직접 실패 증거 |
| --- | --- | --- |
| 검지 row0, 3번줄6프렛 | 1.84 / 2.01mm | position11.867초·candidate11.846초·최장연속11.837초. 실제 접촉 사례 |
| 중지 row4, 3번줄6프렛 | 12.75 / 12.93mm | position0·height0·loaded0. 셀은12.5초 통과하지만 패드가 너무 높음 |
| 약지 row8, 3번줄7프렛 | 4.72 / 5.83mm | position0·height0·loaded0. 셀·횡위치는12.5초 통과하지만 패드가 높음 |
| 소지 row12, 4번줄11프렛 | 8.87 / 15.80mm | cell0·position0. loaded7.596초가 있어도 목표 프렛 셀을 벗어남 |

저장된 [fixed trace240](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/fixed_feedback_v3/trace240.npz)와 [free trace240](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/free_feedback_v3/trace240.npz)에서 마지막 hold `6.5 < t ≤ 12.5초`의 유효 표본을 읽었다.

| 대표 row | 최근접 패드점 높이 중앙값 fixed/free | 최근접점 법선cos 중앙값 fixed/free | 끝마디 하중 중앙값 fixed/free |
| --- | --- | --- | --- |
| 0 검지 | +1.915 / +2.276mm | 0.963 / 0.961 | 1.111 / 0.665N |
| 4 중지 | +12.844 / +12.972mm | 0.977 / 0.978 | 0 / 0N |
| 8 약지 | +4.748 / +5.419mm | 0.978 / 0.959 | 0 / 0N |
| 12 소지 | +4.650 / +6.530mm | 0.454 / 0.384 | 5.039 / 9.048N |

양성 패드 높이 허용값은 −1~+3mm다. 중지·약지 대표 사례는 방향이 나빠서 실패했다고 볼 수 없다. 저장된 `facing=0`은 **position과 법선의 결합 결과**라서 순수 법선 실패율로 해석하면 안 된다. 소지는 최근접점 높이가 높더라도 다른 패드점이 height를 통과할 수 있으며, 실제로 any-sample height는 대부분/전체 통과한다. 그럼에도 cell은 계속0이다. 끝마디 하중은 접촉 상대·목표 줄 압력을 인증하지 않는다.

대표 이외 목표까지 보면 다음이 확인된다.

- 중지 row4~7은 fixed/free 모두 position0·height0·loaded0이다. row5/7은 셀·횡위치도0, row6은 횡위치0이다. 실제 기하 도달이 우선 문제다.
- 약지 row8/9는 높이·하중0, row10은 셀0이다. row11은 free에서 position/facing이 단4물리표본(0.016667초) 통과했으나 loaded는0이다. 이 경우에도 접촉 보상이나 연속시간을 늘려서 해결할 상황이 아니다.
- 소지 row12~14는 셀0이다. row15는 cell/lateral/height 각각의 통과 시간이 있지만 position은0이다. 서로 다른 시간·표본의 독립 통과를 하나의 유효 패드 접촉으로 합치면 안 된다. row15는 상세 trace가 없어 정확한 공동 실패 표본을 지금 복원할 수 없다.
- 검지 row3도 free에서는 최장6.204초 접촉했지만 fixed에서는0.067초뿐이다. row1은 position·loaded의 독립 누적 시간이 존재하나 candidate0이며, 전체 요약만으로 시간적 불일치와 wrong veto를 분리할 수 없다. row2는 셀0이다.

16개 source 후보 모두 geometry_candidate=true였고, 최근접 거리는 약0.275~0.500mm였다. 다수 least-squares는 optimizer_converged=false였다. 이는 지정 predicate를 만족하는 후보를 찾았다는 뜻일 뿐 안정적 최적해·동적 도달 증거가 아니다. 기존 native 실제 q/body 대 source FK 오차는 v3 최대 약0.15/0.19mm로 작았지만, **목표 q에 도달한 것도 아니고 기타의 원래 위치가 유지된 것도 아니다.** 실제 목표각 오차·접촉·자유 기타 이동의 기여를 단계1과 결합해 분해해야 한다.

## 현행 소스와의 차이

기존 free_feedback_v3의 입력 목록에서 Python75개 중67개는 현재 SHA와 같고8개는 다르다: `press_acquisition.py`, `finger_reward.py`, `fingertip_pad.py`, `training/recording.py`, `gpu/control.py`, `gpu/environment.py`, `gpu/episode_diagnostics.py`, `gpu/scene.py`. 따라서 옛 geometry 입력은 현재 replay의 SHA 검사에 걸리며 그대로 실행하거나 검사 완화로 우회하면 안 된다. 현재 소스로 geometry부터 새 디렉토리에 만들어야 한다. 현재 진단 기준은 [보존 목록](/home/ajou/yigyu/3/guitar_learning/archive/20261027_before_failure_diagnosis/manifest.json)이다.

현행 `GpuScene`에는 서로 다른 왼손 손가락 마디90쌍의 선별 충돌이 있다. 현재 재생은 이 필터를 상속하므로 과거와 같은 충돌 조건이라고 가정하지 않는다. 고정/자유 간에는 같은 현재 자산·필터·마찰·solver를 사용하고 고정 여부만 바꾸되, 각각 readback으로 확인한다.

현재 positive는 `pad_target_geometry`에서 지정 끝마디의 **같은 패드 표본**이 셀/횡위치/높이/방향 조건을 만족하고 해당 몸체 하중이 있어야 한다. 현재 학습의 wrong은 [wrong_press.py](/home/ajou/yigyu/3/guitar_learning/gpu/wrong_press.py)의 **other_higher·own_wrong_fret·own_wrong_string**이고, 다른 손가락의 같은/낮은 프렛 접촉을 일괄 wrong으로 보지 않는다. 현재 단순화 환경의 `_left_wrong_contacts` override를 건너뛰는 옛 replay 출력은 현행 clean/wrong 근거가 될 수 없다.

현행 finger-skill은 설정 생성과 `FingerSkillEnvironment` 모두 position 모드를 명시적으로 거부한다. `BatchedController` 자체는 두 모드를 지원한다. **단계1의 제어 진단에서 직접 controller를 사용한 position 비교는 가능하지만, 그 결과를 기본 finger-skill 학습·checkpoint로 보고하면 안 된다.** 단계3의 position 학습 비교가 필요하면 검증된 최소 별도 실험 계약을 먼저 만들고 fresh 모델로 실행해야 한다. 기본 검증을 제거하거나 과거 checkpoint를 강제 로드하지 않는다.

## 권장 재사용 순서

1. **현재16목표 후보를 새로 생성한다.** 기존 `select_targets`/`source_geometry`/`action_bounds`/FK/패드 로더를 그대로 사용한다. 선택은 결과를 보기 전에 저장한다. 이 첫16개는 과거 대조용이며 계획의24개 최종 범위를 대체하지 않는다.
2. **단계1에서 확인한 실제 추종 조건으로 fixed/free 유한 재생을 비교한다.** 먼저 offset 없는 동일 nominal q 궤적을 쓰고, 필요할 때 기존 적분 보정을 별도 조건으로 쓴다. 최소 패드 높이·셀 경계 초과·목표/실제각 오차를 함께 기록한다. source 후보와 실제 q를 섞지 않는다.
3. **원곡에서 손가락별6개로 확장한다.** 현재 서로 다른 실제 목표 수는 검지9·중지7·약지6·소지8개라 24개 선정이 가능하다. 기존4개를 유지하고 아직 덜 대표된 줄→프렛 분산→빈도→안정된 source 순서로2개씩 추가해 선정표를 먼저 저장한다. 현재 replay는16개·대표행을 강제하므로 24개를 기존 검사에 억지로 넣지 말고, 공용 helper를 호출하는 작은 진단 실행부에서 목표 목록/행 수만 명시한다. 범용 새 simulator/framework는 만들지 않는다.
4. **도달/정적 판정과 실제 곡 보상 검사를 나눈다.** 도달 단계는 현재 GpuScene/BatchedController와 기하 helper를 사용한다. 현재 wrong 판정은 실제 표본에서 `pad_contact_cells`·`wrong_press_sources`를 호출하고 명시한 selected mask·source onset/end/press·검사 시각을 저장한다. 정적 반복을 위해 시계를 고정했다면 ‘정적 판정’으로만 표시한다. 음별 보상은 현재 SimplifiedFingerEnvironment의 실제 clock/ledger/step 흐름을 통과해야 하며 static `diagnostic_streak`만으로 보상 지급을 검증하지 않는다.
5. **기존 음/목표와 실제 접촉을 확보한 후 negative를 대조한다.** 다른 줄/프렛·다른 손가락만 접촉·타손가락 높은 프렛 간섭·잘못된 패드 방향·접촉50ms 미만·해제를 사전 선정한다. 같은/낮은 프렛의 타손가락, 하중 없는 근접, B에서 쉬는 다른 손가락은 오압현 v2의 비감점 대조군으로 포함한다. 물리적으로 만들지 못한 사례는 미해결로 기록하고 합성 입력 검사의 통과와 분리한다.
6. **현재 final coefficient의 실제 지급을 검산한다.** 최초접촉 최대0.25b/재지급 없음, 유지 최대1b, 달성0.25b1회, 오압현 최대−0.15b, 수행부족 최대−0.10b와 paid/settled 정산을 원장과 대조한다. PBRS는 할인된 telescoping/terminal Φ=0으로 검산한다. 기하/부하/오압현 판정의 실패와 지급 계산 실패를 별도로 보고한다.

보상 검사의 ‘선택 목표24개’는 물리 도달 후보 집합이고, 실제 원곡 일정의 selected mask·현재 음악 시각은 별도 입력이다. 악보 밖에서 성공을 만들기 위해 onset/end를 조용히 늘리거나 손목 실패 후에도 살아 있는 학습 에피소드처럼 집계하지 않는다. 긴 도달 진단에서 손목 종료를 shadow로만 계산한다면 진단 전용 설정·실제 종료될 시각을 함께 기록한다. 실제 학습 조건 검사는 종료를 그대로 유지한다.

## 최소 추가 기록

기존 저장을 재사용하되, 실패 원인을 확정하는 데 없는 항목만 더한다.

- 손가락별 대표와 추가 부정 사례의 실제 패드 표본별 cell/lateral/height/normal 결합 마스크, 통과 표본 ID. 최근접 접근점과 접촉을 성립시킨 점을 구분한다.
- `positive_before_wrong`, 현재 wrong3원인·소스 몸체/프렛·scope/clock, 최종candidate/clean. 셀·높이 등 독립 OR 시간만 보고하지 않는다.
- 모든24목표는 요약, 사전 지정 대표만240Hz 상세 trace. 최소 row0/4/8/12와 판정 불일치를 확인할 row1/15는 사전에 추가 선정할 수 있다. 결과를 본 뒤 성공한 행만 고르지 않는다.
- 준비/ramp/hold/release 구간별 성공 gate 시간과 목표/실제각·기타 위치를 분리한다. 원점 자세에서 이미 발생한 접촉과 의도적 접근 뒤 획득한 접촉을 구분한다.
- `source_geometry_minimum_distance_m`, 실제 거리, 마지막 hold의 추종 오차를 따로 유지한다. 기존 maximum_target_error는 모든 활성39축 최대라 지정 손가락만의 오차나 정상상태 p95로 해석하지 않는다.

이 단계의 통과는 각 손가락 최소1개의 실제 positive 유지와 대응 negative의 재현, 현재 판정 및 실제 지급의 일치다. 현재 기존 자료만으로는 중지·약지·소지 통과가 입증되지 않았으므로 아직 장기학습으로 넘어갈 근거가 없다. CPU 합성 gate 검사·FK 일치·목표 탐색 성공은 실제 GPU 접촉의 대체 증거가 아니다.
