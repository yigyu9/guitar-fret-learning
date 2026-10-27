# 하체 완전 고정 1초 실행 영상

사용자가 요청한 오른발 이상·하체 고정 조건의 단일 1초 실행을 기록했다. 이전 최선 실행의 step 0 자세를 사용하되, 이번 조건에서 하체 24개 관절을 제거해 다리를 물리적으로 고정했다. 나머지 humanoid DOF 81개, root 고정, 기타 자유·중력, 상체 목표와 기존 제어는 유지했다. 이는 과거 54개 실행의 재순위가 아니다.

## 영상

- [0.25배속, 60 fps, 4.0167초 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/videos/best_run_slow_0p25x.mp4)
- [실시간, 240 fps, 1.0042초 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/videos/best_run_realtime_1x.mp4)
- 미리보기: [시작](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/images/preview_step_000.png), [중간](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/images/preview_step_120.png), [종료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/images/preview_step_240.png)

영상은 full run의 241개 저장 상태(step 0–240, 240 Hz)를 source collision geometry에 적용한 재구성이다. 전신·기타와 손·넥을 나란히 보여주며 저장 trace의 strap route를 표시한다. PhysX 렌더가 아니고, 영상 생성은 native 초기화나 physics step을 추가하지 않았다.

![하체 고정 조건 중간 시점의 저장 자세 재생](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/images/preview_step_120.png)

## 측정 결과

| 측정 | 결과 |
|---|---:|
| 검사 | run 11/11, 고정 하체 12/12 통과 |
| 1초 기타 위치 최대·종료 오차 | 149.372986 mm |
| 1초 기타 회전 최대·종료 오차 | 62.331933° |
| 종료 선속도 / 각속도 | 0.892343 m/s / 3.413599 rad/s |
| 8개 하체 링크의 저장 pose·속도 | 전체 run에서 동일; 위치 변화·선속도·각속도 0 |
| 회전 비교 | quaternion `acos` 수치 잔차 최대 0.000002415° |

초기 고정 링크와 이전 기준의 step 0 pose 비교 잔차는 위치 최대 7.773e−7 m, quaternion `acos` 최대 8.538e−6°였다. run report의 `stability_success`는 null이며 성공 인증은 없다. 이번 실행을 안정성 성공으로 보지 않는다. 이전 동적 하체 기준 run의 최대 위치·회전 오차 73.268255 mm / 13.439339°보다 이번 고정 조건의 오차가 컸다. 하체 고정 조건은 외부 지지 조건이므로 이 비교는 오른발 문제의 원인을 특정하거나 연주 성공을 증명하지 않는다. 오른발 초기 모양은 교정하지 않았다.

0.1초 `short_v4` 입력 및 고정 링크 검사도 통과했다. 실패했던 mesh 경로와 float32-angle 시도는 삭제하지 않고 이 결과 폴더에 보존했다.

## 입력과 재생 provenance

실행 원자료 6개 파일 해시와 이번 조건만 담은 단일 run 선택은 [selection_inputs_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/selection_inputs_manifest.json), [selection.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/selection.json), [full_run_candidates.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_run_candidates.json)에 있다. 저장 원자료는 [report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/report.json), [states.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/states.json), [trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/trace.json) 및 같은 디렉터리의 `controls.json`, `contacts.json`, `leg_torques.json`이다.

새 [render_fixed_lower_video.py](/home/ajou/yigyu/3/stability_adapter_2/render_fixed_lower_video.py)는 기존 저장 자세 renderer를 재사용하고 footer를 실제 report 상태에 맞춰 “Stability success not certified”로 표시한다. report 값은 null이다. 최종영상은 [render_v2/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/)에 있으며 ffmpeg·ffprobe 결과, producer·asset·입력·출력 SHA는 [render_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/render_manifest.json), 실행은 [render_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/render_execution.json)과 [render_execution.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/render_execution.log)에 기록했다. 첫 제작본은 [render_v1/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v1/)에 바이트 그대로 보존했다. 그 옛 영상 footer의 `stability_success=False` 표시는 report의 null과 맞지 않아 archive-only이며, [relocation_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v1/relocation_manifest.json)이 이전 경로와 보존된 파일 SHA를 연결한다.

하체 고정 조건과 검증 계획은 [LOWER_BODY_FIXED_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/LOWER_BODY_FIXED_PLAN.md)에 있다. [최종 독립 검수](review.md:7)는 완료했고 남은 finding이 없다.
