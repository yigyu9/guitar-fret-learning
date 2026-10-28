# Source oracle와 실제 손가락 자세 일관성

같은 source drive target을 현재 reference에 넣었지만, source에서 관찰한 실제 손가락 자세가 그대로 재현되지는 않았다. 원본 접촉 순간의 **실제 q**와 당시 **제출된 drive target**도 서로 다르다. 따라서 저장된 접촉 target 4개를 source의 물리 접촉 자세 자체로 취급할 수 없다. 이번 결과는 원인을 특정하거나 물리 도달 불가능을 증명하지 않는다.

## 자료와 선정 범위

기존 teacher JSON에 이미 동결된 검지 row1 **5.916666667초**, 중지 row8 **5.45초**만 source snapshot으로 사용했다. `teacher_trace60.npz`의 observed time 인덱스는 각각 205/177이다. 같은 행의 `actual_q105_rad`와 **이미 제출된** `actual_target105_rad`를 비교했다. 같은 행의 `corrected_target39_rad`는 다음 명령이므로 혼용하지 않았다.

현재 비교는 v3 `index_reference`/`middle_reference` **env0 첫 시도 60Hz** 자료다. 양쪽 모두 사전 지정한 3.0초 끝점을 사용하고, 원래 audible 전체 검지 11/중지 8개 및 post-ramp ≥2초 전체 102/99개도 빠짐없이 계산했다. source 선정 시간을 새로 최적화하지 않았으며 현재 candidate·wrong·손목 feedback 게이트를 재계산하지 않았다. 4환경 전체 성과는 별도 native 검수의 분모이고, 여기의 자세 수치는 env0만 설명한다.

원 teacher/reference를 출발점으로 따라간 `source_evidence` **57개 연결의 SHA가 모두 일치**했다. source 24-goal 목록의 목표 ID/행, teacher가 기록한 actual selected4와 실제 trace, reference selected4와 source native target의 exact 일치를 확인했다. 현재 입력 before/after도 exact이며 verified/changed-path 검사에 통과했다. 원 source에는 별도 `inputs_after.json`이 없고 당시 report의 completed·changed_inputs 빈 목록을 확인했다. 옛 전체 source pin을 현재 트리에 억지로 검증하지 않았다.

## 선택 4축: 같은 target, 다른 actual

단위 °. 축 순서는 MCP x, MCP z, PIP, DIP이며 `current target`은 아래 source drive target과 4축 모두 exact 같다.

| 조건/값 | MCP x | MCP z | PIP | DIP |
|---|---:|---:|---:|---:|
| 검지 source actual | 40.933 | 19.740 | 54.214 | 23.915 |
| 검지 source drive target = current target | 39.307 | 27.756 | 54.485 | 24.068 |
| 검지 current actual, 3.0초 | 36.742 | 17.461 | 54.485 | 24.068 |
| 중지 source actual | 63.393 | 14.454 | 56.652 | 2.310 |
| 중지 source drive target = current target | 64.175 | 11.367 | 56.954 | 2.467 |
| 중지 current actual, 3.0초 | 62.825 | 13.555 | 56.357 | 2.191 |

검지 source의 target−actual은 [−1.626, +8.016, +0.271, +0.153]°였다. 현재 actual−source actual은 [−4.191, −2.279, +0.271, +0.153]°다. 중지 source의 target−actual은 [+0.782, −3.087, +0.302, +0.157]°, 현재 actual−source actual은 [−0.569, −0.899, −0.295, −0.119]°다. source에서 actual과 target 중 어느 쪽을 저장했는지가 재현 계약에 실질적으로 중요하다.

## 팔·비선택 손가락·엄지를 분리한 대조

source의 16 teacher 채널은 **팔 12축+선택 손가락 4축**이다. 아래 비선택 손가락 12축은 이 팔 12축과 다른 묶음이다. 수치는 source frozen snapshot 대비 current 차이의 축별 최대 절댓값(°)이다.

| 조건 | 묶음 | 3초 target 차이 | 3초 actual 차이 | audible 전체 actual 차이 최대 |
|---|---|---:|---:|---:|
| 검지 | 선택 4 | 0 exact | 4.191 | 4.191 |
| 검지 | 팔 12 | 3.520 | 3.187 | 3.187 |
| 검지 | 비선택 손가락 12 | 0.00000342 | 3.476 | 3.476 |
| 검지 | 엄지 5 | 0 exact | 0.001052 | 0.001120 |
| 중지 | 선택 4 | 0 exact | 0.899 | 0.900 |
| 중지 | 팔 12 | 15.471 | 8.480 | 9.073 |
| 중지 | 비선택 손가락 12 | 0.00000342 | 2.160 | 2.160 |
| 중지 | 엄지 5 | 0 exact | 3.521 | 3.523 |

비선택 B target의 미세 차이는 저장 float32 표현 수준이다. 예를 들어 검지 조건의 source 중지 B target은 [28, −3, 38, 14]°이고 current도 같다. 그러나 중지 actual은 source [27.010, 4.442, 37.998, 14.000]°에서 current [30.486, 6.910, 37.998, 14.000]°로 다르다. 중지 조건의 비선택 검지 actual도 [29.734, −5.556, 36.449, 12.369]° 대 [28.122, −7.715, 35.896, 12.270]°다.

엄지 target은 양 조건 모두 source/current/준비 035의 5축이 **exact 동일**하다. 중지 조건의 엄지 actual은 source [0.0475, −57.5551, −0.0124, 63.7638, 44.1441]° 대 current [−0.0084, −54.0336, −0.0027, 66.4216, 43.4313]°다. 같은 B·엄지 target이라는 사실로 비선택 실제 자세까지 동일하다고 할 수 없다. 각 축 값과 전체 audible/post-ramp min/median/max는 `comparison.json`에 있다.

## 저장된 native 자세로 확인한 검지 차이

source `poses60.npz`의 trace 행 목록은 [0,6,12,18,1,21]이다. row1은 slot4/tick355이며, 이 순간의 전체 q와 target이 teacher trace snapshot과 exact 같고 valid임을 확인한 뒤 사용했다. 전역 손목 위치·회전을 제거하기 위해 **저장된 native palm frame에서** 각 검지 body의 위치와 quaternion을 비교했다. 피부점·현 접촉점의 위치를 뜻하지 않는다.

| 검지 body | 3초 palm-relative 위치 차이 norm | 3초 회전 차이 | audible 위치 norm 최대 | audible 회전 최대 |
|---|---:|---:|---:|---:|
| index1 | 0.000088 mm | 4.772° | 0.000132 mm | 4.772° |
| index2 | 3.613 mm | 4.538° | 3.613 mm | 4.538° |
| index3 | 5.020 mm | 4.408° | 5.020 mm | 4.408° |

이는 실제 저장 자세의 차이이며 MCP x/z 두 값으로 `Exp([qx,0,qz])`를 구성한 FK 결과가 아니다. 중지 row8은 source poses60에 없으므로 **원 source 중지의 native palm-relative body 자세는 미확인**이다. source q105가 있어도 이 빈칸을 MCP fullFK로 채우지 않았다.

## 같은 물리 입력과 서로 다른 실행 조건

확인된 동일 항목은 source/current의 전체 action-target 계약, native 가동범위·codec·rate/smoothing 계약, human XML·scene·hand_collision·finger_control·control·prepared-reset 소스 SHA, 고정 기타 자산/manifest/material readback 및 hand-collision 계약이다. scene readback의 차이는 환경수 24→4, 이에 따른 collision readback 환경수, 총 물리 step 수뿐이다. source도 이미 `left_inter_finger_collision.v1`이며 서로 다른 손가락 90쌍, 다른 human-shape 1395쌍 보존과 matrix SHA `57fc9b11d932f9a630ec320f24ac68d5a5e55782550cf6d3921e4370a7a92352`가 current와 같다. **v19/v22라는 명칭만으로 hand filter 차이를 주장할 근거는 없다.**

PD는 같은 준비 native properties를 복사하고 LH21에 같은 profile(손가락 K=12/D=1.5, 엄지 K=8/D=1.25)을 적용한 뒤 native 전체 property exact readback을 assert하는 동일 scene 소스가 근거다. source에 저장된 effort-cap/drive-mode 배열도 준비 입력과 exact 같다. 두 실행의 stiffness/damping 전체 배열을 별도로 저장한 파일은 없어 새 native PD 재측정을 했다고 주장하지 않는다. 공유 source pin은 검지 626/중지 628개이며 그중 6경로의 SHA가 다르다(thumb_support, finger_skill_environment, episode_diagnostics, training/gpu_pool 및 관련 테스트 2개). 따라서 **전체 실행 소스가 동일하다는 주장은 하지 않는다**. 목록과 양 SHA는 JSON에 보존했다.

반면 source는 0.5초 초기 hold 뒤 동시 2초 ramp, 2.5초부터 arm12+선택4 native point/wrist DLS 및 기존 ≥2N resultant guard를 사용한 정적 진단이다. source 접촉 snapshot은 이 hold의 훨씬 뒤인 5.917/5.45초다. 손목은 고정 6D 목표가 아니라 안내 영역 밖에서만 보정했다. 선택 reference는 이 과정의 drive target을 추출한 것이다. current는 첫 tick부터 2초 ramp 후 3초 audible의 별도 finite reference, arm-only fixed wrist pose teacher v3다. 설정의 LH 최대 rate는 양쪽 4rad/s지만 source `trajectory_actions(max_speed=1)`은 protocol의 1rad/s 제한을 추가했고 current는 4rad/s를 사용한다. `15*(desired-current)`와 `max_speed/4` action clip을 거치는 원 codec 정의에 따른 차이다. 실제 접근 경로·속도·목표 도착 후 경과시간·feedback 채널이 같지 않다.

## 남은 확인과 최소 다음 진단 제안

같은 선택 target/B/엄지 목표만으로 source actual을 재현하지 못했고, 검지는 저장 native 상대 자세 차이까지 확인했다. 어느 접촉쌍, 힘, 충돌 순서, PD 또는 경로 차이가 이를 만들었는지는 이번 자료로 분리하지 못한다. source의 정적 candidate 및 body resultant 1.713N/1.590N은 현재 음악 성과나 접촉쌍 압력의 증거가 아니다.

필요한 후속은 먼저 **원본 24-goal teacher의 동일 시간·같은 row에 전체 native 손가락 body pose가 저장되는 최소 관찰**이다. 특히 row8의 누락 pose를 채워야 한다. 재현 비교를 추가한다면 원 source finite command 경로와 현재 finite reference를 분리하고 같은 팔/B/엄지 조건에서 실제 자세·제출 target·native pose를 함께 관찰해야 한다. source actual4를 새 목표로 쓰는 것은 기존 source drive-target reference와 다른 진단 조건이므로 별도 사전 정의가 필요하며, 실제 state 대입이나 도달/개선 보장을 뜻하지 않는다. 현재 GPU/native 실행 및 제어 변경은 0이다.

재계산: `CUDA_VISIBLE_DEVICES='' python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/source_finger_pose_consistency/analyze.py`. JSON에는 입력 44개 SHA, 자체 분석 SHA, 확인 assertion과 비교 원자료가 있다. 이번 분석은 새로운 실행 봉인이나 기존 실행 입력 변경을 만들지 않는다.
