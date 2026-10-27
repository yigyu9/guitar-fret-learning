# 현재 자세값과 유지 제어

대상은 기존 035 설정·v14 실행·실용 V3다. 길이는 m, 관절각은 rad, 위치는 파일에 명시된 좌표계를 따른다. 기타 쿼터니언 순서는 `xyzw`다. 관절 목표와 물리적으로 관측된 실제 상태를 구분한다.

## 값의 역할

| 파일 | 의미와 사용 범위 |
|---|---|
| [candidate.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/pose/candidate.json) | source_v9 출발 형상. `joint_names`와 `q_ref_rad`의 105개 대응, 기타 초기 배치. 준비 완료 상태가 아니다. |
| [upper_target105.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/pose/upper_target105.json) | 기존 실행이 참조한 105채널 목표 파일. 원래 파일명과 내용을 보존했다. |
| [initial_values_baseline_v14.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/pose/initial_values_baseline_v14.json) | baseline의 native 초기 상태, 관절/바디 이름, K/D, drive/effort 상한과 position/effort 인덱스. |
| [prepared_state_baseline_v14_22s.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/pose/prepared_state_baseline_v14_22s.json) | baseline 원자료의 22초·physics step 5280 실제 상태 행. 인체·기타·의자 상태와 105축 실제 관절 상태. 관찰용이며 제어기 내부 상태를 포함한 재시작 파일은 아니다. |

최종 준비 정지 구간은 **17–22초**다. 원래 설정의 `hold_interval_s: [5,10]` 같은 이전 단계 필드나 native의 `ready_reference.json`에 저장된 **10초 참조 상태**를 최종 준비 완료 상태로 바꾸어 해석하지 않는다. 실제 준비 일정은 `ready_settled_hold_s`와 runtime의 누적 보정을 함께 확인한다.

## 배치와 제어 조건

| 항목 | 값 또는 조건 |
|---|---|
| Root 위치 | `[0, -0.18, 0.556]` m, Root 고정 |
| 의자 전체 xyz 크기 | `[0.4, 0.28, 0.456]` m |
| 의자 중심 | `[0, -0.3325, 0.228]` m, 실행 중 변경 없음 |
| 입력 채널 / 비영범위축 | 105 / 97 |
| 원래 영범위 8축 | 좌우 Knee_y,z 및 Toe_y,z; 원래 제한 보존 |
| position / effort 제어 인덱스 수 | 48 / 57, 정확한 축별 대응은 initial_values 참조 |
| 하체 유지 | 원래 가동범위 내 유한 제어, 관절 잠금 없음 |
| 가슴 제어 | 인체 관절 토크로 전달되는 최대 20N 가상 제어; 기타 직접 보조 힘과 구분 |
| 타현 | 오른팔꿈치·손목 6축 목표 변화, 오른손 파지 목표 유지 |
| 기타 | 자유 강체·중력 ON·스트랩 OFF |

## 실행 설정

다섯 설정은 원본을 수정하지 않고 복사했다. 경로·SHA·준비 보정·gain을 임의로 단순화하지 않았다.

| 시험 | 정확한 설정 | 원래 실행 폴더 |
|---|---|---|
| 정지 | [baseline_v1.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/configs/baseline_v1.json) | [native_baseline_v14](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_baseline_v14) |
| 반복 타현 | [repeat_v1.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/configs/repeat_v1.json) | [native_repeat_v14](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_repeat_v14) |
| 왼손 해제 | [release_v1.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/configs/release_v1.json) | [native_release_v14](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_release_v14) |
| 해제 상태 타현 | [free_strike_v1.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/configs/free_strike_v1.json) | [native_free_strike_v14](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_free_strike_v14) |
| 재접촉 | [regrasp_v1.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/configs/regrasp_v1.json) | [native_regrasp_v14](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/native_regrasp_v14) |

실제 제어는 [Controller runtime_v12.py](/home/ajou/yigyu/3/stability_adapter_2/front_facing_ready_v1/runtime_v12.py)와 [Scene runtime_v15.py](/home/ajou/yigyu/3/stability_adapter_2/front_facing_ready_v1/runtime_v15.py) 및 그 의존성을 따른다. 이 두 파일만으로 전체 의존성이 완결되는 것은 아니다. 원래 설정이 참조하는 준비 명세·타현 명세·보정 입력은 기존 절대 경로로 연결되며, 대표 설정의 직접 파일 참조는 [출처 목록](/home/ajou/yigyu/3/paper/initial_pose/current_v3/manifest.json)에도 기록했다.

## 원자료와 재현 범위

각 native 폴더의 `states240.json`은 실제 상태, `targets60.json`은 제출 목표, `efforts240.json`과 `contacts240.json`은 각각 제어·접촉 원자료다. 일부 파일은 확장자가 `.json`이어도 gzip 압축으로 저장되어 있다. 각 폴더의 `raw4_storage_manifest.json`에 압축 형식·SHA·행 수가 있으므로 원래 저장 형식에 맞게 읽는다.

이번 정리에서 22초 실제 상태 한 행을 압축 원자료에서 추출했으며 새로운 물리 계산이나 재실행을 하지 않았다. 해당 값으로 상태를 반복 덮어써 자세를 유지하거나 재현이 검증된 것으로 설명해서는 안 된다. 같은 조건의 재시작 재현은 남은 검증이다.
