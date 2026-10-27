# 현재 자세 테스트 공간 독립 검수

요약 판정: 현재 V2 문제없음. Critical: 0

검수 범위는 새 테스트 공간의 초기값·제어 재사용·GUI 상태 전이·cleanup 및 이미 완료된 0.2초 원자료이다. 검수자가 추가 물리 시험을 실행하거나 기존 봉인 파일을 수정하지 않았다.

## Critical

- 현재 V2: 0. V1의 필수 `OM_appearance` 카메라 누락 및 finally 재촬영 예외로 cleanup/report가 생략되는 두 문제는 [run_v2.py:55](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/run_v2.py:55)의 기존 native와 같은 카메라 생성과 [run_v2.py:103](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/run_v2.py:103)의 중첩 cleanup으로 보완했다. V1 원본과 0step setup 실패는 [setup_failure_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/setup_failure_v1.json:1)에 보존하며 현재 실행기는 [open_v2.sh:13](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/open_v2.sh:13)이다.

## Warning

- [README.md:43](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/README.md:43): DISPLAY가 없어 실제 viewer 생성·키/마우스·사용자 reset 후 두 번째 sim의 통합 동작은 미검증이다. 코드와 순수 상태 전이 검산을 GUI 실행 인증으로 확대하지 말고 이 제한을 유지한다.
- [report.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/sessions/20261014_215819_009632/trial_000/report.json:1): 확인된 실제 회차는 48physics/12control/0.2초이며 각 영상은 초기 프레임을 포함한 7frame/0.233333초다. 이 도구에서 새 5초 시험 또는 2초 이후 타현 재현을 검증한 것으로 설명하지 않는다. 중간 reset/종료도 정상 회차 저장이므로 `completed`만으로 5초 완주를 판단하지 않고 `stop_reason`과 step 수를 함께 본다.

## 확인 근거

- [run_v2.py:49](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/run_v2.py:49): 현재 초기 raw 상태 전체와 PD/질량을 이전 `left_neck_three_face_v1/native_off_v1`에 직접 비교한다. 저장된 initial_values 전체 및 two_block/body_effort/left_wrist_tracking/left_arm_effort/elbow_motion/actual_shape 구성 6개 JSON의 이전 원자료와 정확한 일치를 독립 확인했다.
- [run_v2.py:135](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/run_v2.py:135): 기존 V7 main의 factory/controller/recorder patch를 유지하고 runner main만 별도 episode로 교체한다. 새 상태 쓰기·추가 힘·gain 변경이 없다. 실제 physics endpoint 48행, six_joint_target 12행, pick_feedback 최종 effort 48행을 이전 native 원자료의 같은 prefix와 직접 비교해 모두 정확히 일치했다.
- [viewer.py:5](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/viewer.py:5): 시작 정지, N 1회 진행 뒤 정지, Space 재생/정지, finished 후 진행 금지, R 요청 검산을 통과했다. [viewer.py:50](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/viewer.py:50)의 대기는 graphics만 갱신하며 실제 제어는 [run_v2.py:84](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/run_v2.py:84)의 step 분기에서만 호출한다. 로컬 IsaacGym API 정의에서 draw_viewer의 세 번째 인자는 render_collision으로 확인했다.
- [run_v2.py:96](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/run_v2.py:96): 1200step 종료 후 추가 physics 없이 R/Esc를 기다린다. reset은 기존 viewer/sim 종료와 원자료 저장 후 새 trial 경로·새 scene 생성으로 이어지고 초기 상태를 매 tick 덮어쓰지 않는다. 녹화 또는 final-state 저장 오류도 sim close의 finally 경로를 유지한다.
- [run_v2.py:16](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/run_v2.py:16): 기존 native 입력의 합집합과 새 파일, XML 선언 mesh를 포함하고 mesh SHA를 기존 native 기준과 비교한다. 완료 회차 inputs_before의 모든 현재 SHA를 직접 확인해 불일치 0이었다. report는 inputs_unchanged true, forbidden_calls 0, failure null이다. 새 Python 파일 AST 검사도 통과했다.

## Suggestion

- 선택 사항 없음. 실제 데스크톱 GUI 통합 확인은 위 Warning 범위로 남긴다.
