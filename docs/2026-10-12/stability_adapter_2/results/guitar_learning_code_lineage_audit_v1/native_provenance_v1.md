# 자유 기타 native 구현·초기화·제어 코드 계보

현재 구현은 기존 자유 기타 연결부의 코드와 초기 자세 검증용 native 장면·제어기를 계승하고, 고정 기타 학습 환경의 일부 아이디어를 새 측정·목표 공간으로 옮긴 구조다. `guitar_learning` 내부에 코드를 모았지만 시뮬레이터·제어기·자산·기록 데이터는 여전히 외부 `stability_adapter_2`, `tab2body/assets`, `paper/initial_pose`, 과거 실행 결과에 의존한다. 아래는 실제 소스와 SHA를 확인한 읽기 전용 감사이며 새 실험을 수행하지 않았다.

## 1. 복사 이력과 현재 파일은 어디까지 같은가

[guitar_learning/origin_manifest.json](/home/ajou/yigyu/3/guitar_learning/origin_manifest.json:1)의15개 항목에서 **원본 SHA15/15, 정리본 SHA15/15가 현재도 일치**한다. 활성9개·보관6개이며 원본과 정리본이 byte까지 같은 것은 geometry_v1.py·fretting_v1.py·music_pipeline_v2의control.py, 총3개다. 나머지는 패키지 import·경로·소스 수집·관련 검사 변경이 있다. 자세한 차이와 전체 SHA는 동반 JSON에 기록했다.

| 원래 파일 | 현재 위치 | 구분 | 확인된 변화 |
|---|---|---|---|
| [stability_adapter_2/free_guitar_learning_v1/environment_v3.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/environment_v3.py:1) | [guitar_learning/archive/20261018_before_archive_cleanup/environment_v3.py](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_archive_cleanup/environment_v3.py:1) | archived | import 경로 교체 |
| [stability_adapter_2/free_guitar_learning_v1/geometry_v1.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/geometry_v1.py:1) | [guitar_learning/geometry_v1.py](/home/ajou/yigyu/3/guitar_learning/geometry_v1.py:1) | current | 원본 byte 그대로 |
| [stability_adapter_2/free_guitar_learning_v1/fretting_v1.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/fretting_v1.py:1) | [guitar_learning/fretting_v1.py](/home/ajou/yigyu/3/guitar_learning/fretting_v1.py:1) | current | 원본 byte 그대로 |
| [stability_adapter_2/free_guitar_learning_v1/fretting_environment_v1.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/fretting_environment_v1.py:1) | [guitar_learning/archive/20261018_before_archive_cleanup/fretting_environment_v1.py](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_archive_cleanup/fretting_environment_v1.py:1) | archived | import 경로 교체 |
| [stability_adapter_2/free_guitar_learning_v1/run_smoke_v7.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/run_smoke_v7.py:1) | [guitar_learning/archive/20261018_before_archive_cleanup/run_smoke_v7.py](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_archive_cleanup/run_smoke_v7.py:1) | archived | import·프로젝트 경로·소스 수집 범위 변경 |
| [stability_adapter_2/free_guitar_learning_v1/run_fretting_probe_v2.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/run_fretting_probe_v2.py:1) | [guitar_learning/archive/20261018_before_archive_cleanup/run_fretting_probe_v2.py](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_archive_cleanup/run_fretting_probe_v2.py:1) | archived | import·프로젝트 경로·소스 수집 범위 변경 |
| [stability_adapter_2/free_guitar_learning_v1/test_environment_v3.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/test_environment_v3.py:1) | [guitar_learning/archive/20261018_before_archive_cleanup/tests/test_environment_v3.py](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_archive_cleanup/tests/test_environment_v3.py:1) | archived | import 경로 교체 |
| [stability_adapter_2/free_guitar_learning_v1/test_geometry_v1.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/test_geometry_v1.py:1) | [guitar_learning/tests/test_geometry_v1.py](/home/ajou/yigyu/3/guitar_learning/tests/test_geometry_v1.py:1) | current | import 경로 교체 |
| [stability_adapter_2/free_guitar_learning_v1/test_fretting_v1.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/test_fretting_v1.py:1) | [guitar_learning/tests/test_fretting_v1.py](/home/ajou/yigyu/3/guitar_learning/tests/test_fretting_v1.py:1) | current | import 경로 교체 |
| [stability_adapter_2/free_guitar_learning_v1/test_fretting_environment_v1.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/test_fretting_environment_v1.py:1) | [guitar_learning/archive/20261018_before_archive_cleanup/tests/test_fretting_environment_v1.py](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_archive_cleanup/tests/test_fretting_environment_v1.py:1) | archived | import 경로 교체 |
| [stability_adapter_2/free_guitar_learning_v1/test_smoke_metadata_v1.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/test_smoke_metadata_v1.py:1) | [guitar_learning/tests/test_smoke_metadata_v1.py](/home/ajou/yigyu/3/guitar_learning/tests/test_smoke_metadata_v1.py:1) | current | 현 패키지 소스 수집·bridge 분류 검사 추가 |
| [stability_adapter_2/music_pipeline_v2/control.py](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/control.py:1) | [guitar_learning/control.py](/home/ajou/yigyu/3/guitar_learning/control.py:1) | current | 원본 byte 그대로 |
| [stability_adapter_2/music_pipeline_v3/control.py](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v3/control.py:1) | [guitar_learning/whole_body_control.py](/home/ajou/yigyu/3/guitar_learning/whole_body_control.py:1) | current | import 경로 교체 |
| [stability_adapter_2/music_pipeline_v2/test_control_v2.py](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/test_control_v2.py:1) | [guitar_learning/tests/test_control.py](/home/ajou/yigyu/3/guitar_learning/tests/test_control.py:1) | current | import 경로 교체 |
| [stability_adapter_2/music_pipeline_v3/test_control.py](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v3/test_control.py:1) | [guitar_learning/tests/test_whole_body_control.py](/home/ajou/yigyu/3/guitar_learning/tests/test_whole_body_control.py:1) | current | import 경로 교체 |

이 manifest는 옛 environment_v3의 정리본이 현재 보관 위치에 남아 있다는 증거다. 현재 환경 전체가 그때의 byte라는 뜻은 아니다. 옛 [NativeSession](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/environment_v3.py:19)과 현 [NativeSession](/home/ajou/yigyu/3/guitar_learning/native_session.py:13)은 상대 import를 정규화한 **클래스 AST가 일치**한다. 반면 옛 환경은22초를 실제 적분하고, 현 v4는 저장 자세 복원 후1~2초, v5는0초도 지원하도록 의미가 바뀌었다. 관련 지점은 [stability_adapter_2/free_guitar_learning_v1/environment_v3.py](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/environment_v3.py:122), [guitar_learning/environment_v4.py](/home/ajou/yigyu/3/guitar_learning/environment_v4.py:41), [guitar_learning/environment_v5.py](/home/ajou/yigyu/3/guitar_learning/environment_v5.py:12)다.

## 2. 실제 실행에서 내려가는 경로

[guitar_learning/environment.py](/home/ajou/yigyu/3/guitar_learning/environment.py:2)는 여전히 v4를 re-export한다. 최신 정책 준비 전환 경로는 이 alias 하나로 설명할 수 없다. [guitar_learning/actionable_preparation_environment.py](/home/ajou/yigyu/3/guitar_learning/actionable_preparation_environment.py:26)가 v5와 기존 contact/persistent 메서드를 함께 계승하고, 생성할 때만 [guitar_learning/actionable_preparation_environment.py](/home/ajou/yigyu/3/guitar_learning/actionable_preparation_environment.py:95)에서 TrainingEnvironment의 contact 클래스 바인딩을 교체한다. 기존 인스턴스나 소스 파일을 변경하는 방식은 아니다.

```text
Contact/PersistentContact(v5 + 원 contact/persistent 동작)
  └─ session_factory: PersistentHeadlessPreparedSession
       └─ HeadlessPreparedSession → PreparedSession → NativeSession
            ├─ Scene: front_facing_ready/runtime_v15
            └─ Controller: front_facing_ready/runtime_v12

정책 target39 → upper81 codec → target105
  → controller.apply(원래 foot IK; 상체81 불변 검사)
  → lower_body_release/scene_v8.Scene.command(명시적 base 호출)
  → controller.effort(기존 유한 유지 제어)
  → scene.integrate105(human effort → simulate → fetch)
```

근거: [guitar_learning/persistent_environment.py](/home/ajou/yigyu/3/guitar_learning/persistent_environment.py:18), [guitar_learning/headless_session.py](/home/ajou/yigyu/3/guitar_learning/headless_session.py:95), [guitar_learning/prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/prepared_reset_v1.py:171), [guitar_learning/native_session.py](/home/ajou/yigyu/3/guitar_learning/native_session.py:18), [guitar_learning/native_session.py](/home/ajou/yigyu/3/guitar_learning/native_session.py:31). Headless는 camera 생성을 차단하고 CPU PhysX thread 수를 지정하지만 원 Guard의 비그래픽 제한은 유지한다([guitar_learning/headless_session.py](/home/ajou/yigyu/3/guitar_learning/headless_session.py:53)). GPU 다중환경으로 바뀐 것이 아니다.

Scene 클래스의 실제 상속은 다음 순서다. Controller의 긴 전체 상속 목록과 import 원문·줄번호는 JSON에 별도 기록했다. 이 목록은 클래스 관계이며 모든 부모 메서드를 매 tick 호출한다는 뜻은 아니다.

```text
front_facing_ready.runtime_v15 → runtime_v3 → runtime_v1
 → seated_foot_support.runtime_v6 → runtime_v1
 → lower_body_release.scene_v8 → stability_adapter_2.environment.InitialEnvironment
```

유지 제어의 바탕은 [stability_adapter_2/lower_body_release_v1/controller_horizontal_v4.py](/home/ajou/yigyu/3/stability_adapter_2/lower_body_release_v1/controller_horizontal_v4.py:71)이고, foot IK는 [stability_adapter_2/seated_foot_support_v1/runtime_v6.py](/home/ajou/yigyu/3/stability_adapter_2/seated_foot_support_v1/runtime_v6.py:34), 오른팔 world support 목표는 [stability_adapter_2/grounded_guitar_support_v1/runtime_v2.py](/home/ajou/yigyu/3/stability_adapter_2/grounded_guitar_support_v1/runtime_v2.py:60), 보정 목표는 [stability_adapter_2/grounded_guitar_support_v1/runtime_v14.py](/home/ajou/yigyu/3/stability_adapter_2/grounded_guitar_support_v1/runtime_v14.py:12), hip-load bias는 [stability_adapter_2/grounded_guitar_support_v1/runtime_v17.py](/home/ajou/yigyu/3/stability_adapter_2/grounded_guitar_support_v1/runtime_v17.py:12), Chest preload는 [stability_adapter_2/grounded_guitar_support_v1/runtime_v18.py](/home/ajou/yigyu/3/stability_adapter_2/grounded_guitar_support_v1/runtime_v18.py:15), RH말단 SO(3) 오차 보정은 [stability_adapter_2/front_facing_strike_v1/runtime_v5.py](/home/ajou/yigyu/3/stability_adapter_2/front_facing_strike_v1/runtime_v5.py:31)로 계승된다.

## 3. 무엇을 재사용하고 무엇을 우회하는가

정책은 [guitar_learning/native_session.py](/home/ajou/yigyu/3/guitar_learning/native_session.py:41)에서 최하위 Scene.command를 직접 호출한다. 그래서 runtime_v15의 추가 척추 목표, ready Scene의 Motion.apply, 기존 Controller.targets의 손 IK/스크립트 타현 일정이 정책 목표를 다시 덮지 않는다. foot apply를 한 번 호출한 뒤 upper81이 그대로인지 검사한다. PreparedSession.prepare_tick 역시 [guitar_learning/prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/prepared_reset_v1.py:190)에서 저장 target을 정책 제출 경로로 보낸다. 바탕 NativeSession.prepare_tick의 옛 controller.targets 구현이 현재 준비 경로에 그대로 실행되는 것은 아니다.

그러나 생성 단계 의존성까지 제거한 것은 아니다. [stability_adapter_2/front_facing_ready_v1/runtime_v12.py](/home/ajou/yigyu/3/stability_adapter_2/front_facing_ready_v1/runtime_v12.py:9)는 옛 protocol/schedule를 검증하고, [stability_adapter_2/front_facing_ready_v1/runtime_v10.py](/home/ajou/yigyu/3/stability_adapter_2/front_facing_ready_v1/runtime_v10.py:10)는 Motion3를 생성 시 연결하며, [stability_adapter_2/front_facing_ready_v1/runtime_v1.py](/home/ajou/yigyu/3/stability_adapter_2/front_facing_ready_v1/runtime_v1.py:24)는 PreparedController의 생성자를 직접 호출해 참조/FK·support 구성을 만든다. [stability_adapter_2/front_facing_ready_v1/motion_v1.py](/home/ajou/yigyu/3/stability_adapter_2/front_facing_ready_v1/motion_v1.py:52)는 ready_spec도 읽는다. 따라서 예전 Motion 파일을 정책이 stepping하지 않는다는 이유만으로 protocol/spec/생성자 의존 파일을 삭제할 수 없다.

## 4. 고정 기타 환경은 배제됐지만 자산은 남는다

옛 [tab2body/env/base.py](/home/ajou/yigyu/3/tab2body/env/base.py:275)는 기타 fix_base=True·gravity_disabled=True로 로드하고, [tab2body/env/base.py](/home/ajou/yigyu/3/tab2body/env/base.py:698)는 고정 장면 root snapshot을 복원한다. 현재 NativeSession은 이 환경 클래스를 상속하거나 import하지 않는다. 실제 확인한 이전 stage1 양손103개·현재 smoke 양손106개 imported source 목록에도 `tab2body/env`·`archive` 모듈은0개였다. 이 실행 증거의 원경로/SHA는 JSON의 execution_corroboration에 있다.

현재 native 자산 로드는 [stability_adapter_2/environment.py](/home/ajou/yigyu/3/stability_adapter_2/environment.py:101)에서 인간 Root만 고정하고 기타는 자유·중력ON으로 설정한다. [stability_adapter_2/lower_body_release_v1/common.py](/home/ajou/yigyu/3/stability_adapter_2/lower_body_release_v1/common.py:7)의 humanoid는 여전히 `tab2body/assets/smpl_mpl_hands_body.xml`이며 기타는 [stability_adapter_2/lower_body_release_v1/scene_v8.py](/home/ajou/yigyu/3/stability_adapter_2/lower_body_release_v1/scene_v8.py:109)에서 `stability_adapter_2/assets/om_body_geometry_v3/guitar_asset.xml`로 바뀐다. 따라서 **고정 기타 시뮬레이션 코드 미사용**과 **옛 프로젝트 자산 미사용**은 다르다.

InitialEnvironment에는 strap force 코드는 남아 있다([stability_adapter_2/environment.py](/home/ajou/yigyu/3/stability_adapter_2/environment.py:250)). 하지만 [stability_adapter_2/lower_body_release_v1/scene_v8.py](/home/ajou/yigyu/3/stability_adapter_2/lower_body_release_v1/scene_v8.py:159)가 legacy step_physics를 금지하고, 현재 경로는 integrate105만 호출한다. [stability_adapter_2/lower_body_release_v1/scene_v8.py](/home/ajou/yigyu/3/stability_adapter_2/lower_body_release_v1/scene_v8.py:47) Guard도 외부 force/state/property 변경을 제한한다. strap 모듈의 point_kinematics를 쓰는 것은 strap 힘을 활성화한 것과 다르다. 생성 때 route/rest_length를 계산하는 옛 데이터 의존은 남아 있다.

## 5. 초기 상태는 현재 candidate 한 파일로 재현되지 않는다

[guitar_learning/prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/prepared_reset_v1.py:14)는 정확한035 baseline, 과거 fretting native probe의 prepared.json·initial_values.json·inputs_before.json을 SHA로 고정한다. baseline 경로는 현재 `paper/initial_pose/archive/experiment_records/...`로 resolve된다. 기록된 물리 step5280(22초) sample의 human DOF·기타 상태와 최종 target105를 불러오며, 실제 매번22초를 다시 적분하지 않는다. [guitar_learning/prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/prepared_reset_v1.py:56)는 XML과 선언 mesh의 기존 SHA까지 검사한다.

그 밖에 기본 config/pose/gain, working_initial_pose의 과거 upper81 PD 기록, source_v9 candidate/upper_target105, 기타 mass/inertia native_properties, right_goal_spec·hip_load_bias_spec/report/원 efforts, ready_spec 등이 장면·제어기 생성에 남아 있다. 실제 읽는 지점은 [stability_adapter_2/environment.py](/home/ajou/yigyu/3/stability_adapter_2/environment.py:44), [stability_adapter_2/environment.py](/home/ajou/yigyu/3/stability_adapter_2/environment.py:144), [stability_adapter_2/lower_body_release_v1/scene_v8.py](/home/ajou/yigyu/3/stability_adapter_2/lower_body_release_v1/scene_v8.py:31), [stability_adapter_2/lower_body_release_v1/scene_v8.py](/home/ajou/yigyu/3/stability_adapter_2/lower_body_release_v1/scene_v8.py:78), [stability_adapter_2/lower_body_release_v1/controller_horizontal_v4.py](/home/ajou/yigyu/3/stability_adapter_2/lower_body_release_v1/controller_horizontal_v4.py:34)다. baseline의 모든 path 필드는 JSON에 기록했지만, provenance용 필드가 모두 매 tick 읽힌다고 해석하지 않는다.

생성자에서 만든 FK·anchor·support 참조를 유지한 뒤 저장 DOF/기타 상태만 복원한다([guitar_learning/prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/prepared_reset_v1.py:178)). Root·의자는 이미 같은지 검사하고 human rigid setter는 쓰지 않는다([guitar_learning/prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/prepared_reset_v1.py:128)). controller.s의 시간만 +5280인 ControlPhaseView를 제공하고 real scene.steps는0이다([guitar_learning/prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/prepared_reset_v1.py:80)). 기존 support/SO(3) 일정의 성숙 구간을 쓰기 위한 명시적 제어 조건이며 초기 물리 시각을22초로 속인 것이 아니다. Persistent reset은 같은 scene/controller/FK를 유지하고 경계에서 상태·일부 history를 복원한다([guitar_learning/persistent_session.py](/home/ajou/yigyu/3/guitar_learning/persistent_session.py:162)). 숨은 PhysX cache까지 완전히 같은 checkpoint라고 주장하지 않는다.

## 6. 전신·하체·오른손 제어의 정확한 범위

| 항목 | 실제 구현 범위 |
|---|---|
| Native105 / 비영범위97 / 영범위8 | Root 제외 원래 이름/범위를 검사. 원 영범위8은 Knee/Toe의 y,z축을 보존하며 effort0. 실제 상태의 수치0을 보증하는 뜻은 아님. |
| 정책 출력39 | LH 팔12+손21=33, RH elbow/wrist6. |
| Upper held42 | support15(Torso/Spine/Chest/R_Thorax/R_Shoulder), RH 파지손가락21, Neck/Head6의 actuator 목표를 reset reference에 유지. 실제 물리상태 lock 아님. |
| Lower24 | 정책 출력에 포함되지 않음. 외부 finite foot IK와 rotational stablePD, 실제 가동16축·원 영범위8축. |
| Native actuation | POSITION48 + EFFORT57(upper33+lower24), 각각 원 effort cap. |
| Root | 고정. 전신 유지 제어는 있으나 전신105 policy action·자유Root 균형은 아님. |

근거는 [guitar_learning/control.py](/home/ajou/yigyu/3/guitar_learning/control.py:22), [guitar_learning/control.py](/home/ajou/yigyu/3/guitar_learning/control.py:79), [guitar_learning/environment_v4.py](/home/ajou/yigyu/3/guitar_learning/environment_v4.py:64), [stability_adapter_2/lower_body_release_v1/scene_v8.py](/home/ajou/yigyu/3/stability_adapter_2/lower_body_release_v1/scene_v8.py:112), [stability_adapter_2/lower_body_release_v1/controller_horizontal_v4.py](/home/ajou/yigyu/3/stability_adapter_2/lower_body_release_v1/controller_horizontal_v4.py:139)다. control.py의 원 codec metadata에는 아직 fixed-lower 문구가 남아 있지만 v4는 [guitar_learning/environment_v4.py](/home/ajou/yigyu/3/guitar_learning/environment_v4.py:92)에서 복사한 반환 metadata를 유한 하체 제어 범위로 보정한다. 내부 원 codec metadata와 실제 실행/반환 설명을 구분해야 한다.

또한 [guitar_learning/whole_body_control.py](/home/ajou/yigyu/3/guitar_learning/whole_body_control.py:28)의 WholeBodyTargetContract와 torques 함수는 순수 CPU 설계 모듈이다. 현 v4는 그 파일에서 EXPECTED_NAMES만 import해105 이름집합을 검증한다. 실제 actuator 토크가 이 순수 PD함수로 계산된다고 설명하면 안 된다. native 쪽 하체 mass/rotation stablePD와 기존 mixed POSITION/EFFORT를 쓴다. RH 파지손가락이 held인 것과 오른팔 전체가 고정인 것도 다르며, 오른쪽 support 관절은 유한 effort로 실제 미세 움직임이 가능하다.

## 7. 자유 기타 측정으로 옮긴 의미와 아직 옮기지 않은 부분

[guitar_learning/geometry_v1.py](/home/ajou/yigyu/3/guitar_learning/geometry_v1.py:19)는 매 sample의 현재 기타 Root 좌표로 변환한다. [guitar_learning/geometry_v1.py](/home/ajou/yigyu/3/guitar_learning/geometry_v1.py:63)는 현/프렛 marker·피크·손가락 말단 원점을 live 상태에서 재구성한다. [guitar_learning/geometry_v1.py](/home/ajou/yigyu/3/guitar_learning/geometry_v1.py:97)는 이전·현재 각각의 기타 좌표에서 상대 sweep를 만들고 현 local geometry의 강체 일관성을 검사한다.

[guitar_learning/strike.py](/home/ajou/yigyu/3/guitar_learning/strike.py:1)는 옛 [tab2body/env/strike_detector.py](/home/ajou/yigyu/3/tab2body/env/strike_detector.py:1)의 선분 교차 아이디어를 Numpy240Hz 측정으로 옮긴 **의미적 변형**이며 direct import·byte 복사가 아니다. 깊이 상한·영역·재무장·고유 crossing ID를 현재 계약으로 계산한다. 선형 상대보간은 한 물리 interval의 근사이며 실제 현 진동/음향을 생성하는 충돌 모델은 아니다.

압현은 [guitar_learning/fretting_v1.py](/home/ajou/yigyu/3/guitar_learning/fretting_v1.py:56)의 같은 시각 raw 접촉 pair와 현재 기타 줄/프렛 cell을 결합한다. 유효 candidate는 적절한 손가락·줄 lane·프렛 구역 등의 native 증거로 정해지고, distal 원점의 midpoint 거리와는 분리된다([guitar_learning/fretting_v1.py](/home/ajou/yigyu/3/guitar_learning/fretting_v1.py:148)). open fret0은 옛 task의 DONT_CARE0과 구분한다([guitar_learning/geometry_v1.py](/home/ajou/yigyu/3/guitar_learning/geometry_v1.py:3)). 기존 task_fret/task_strike 환경·고정장면 reset·기존 훈련 checkpoint를 그대로 현 환경에 올린 형태가 아니다. 네트워크/PPO 이식 계보는 별도 상위 감사가 다룬다.

## 감사 한계

이 문서는 직접 import·복사 SHA·AST 동일성·상속/호출·의미적 변형·미이식을 분리했다. 런타임 import 증거는 확인한4개 종료 보고서에 한정하며, 새 시뮬레이션을 실행하지 않았다. 원15개 manifest 밖의 후속 파일은 소스 차이와 호출 근거로 설명했으며 역사적 manifest에 소급 추가하지 않았다. 기존 코드·보관본·원자료는 수정하지 않았다. 모든 원경로와 전체 SHA·정적 import 줄번호는 native_provenance_v1.json에 있다.
