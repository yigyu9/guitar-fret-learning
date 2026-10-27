# 15초 초기 자세 영상 사전 검수 V1

요약 판정: **문제없음**. 현재 권장 후처리 V2 기준 미해결 Critical 0건, Warning 0건. 실제 15초 결과와 산출 영상 검수는 실행 완료 후 별도로 수행한다.

## 검수 범위

- [실행 래퍼](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_long_video_v1.py:9), [후처리 V2](/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_long_video_v2.py:12), [계획](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_LONG_VIDEO_PLAN_V1.md:5), [표시 범위 보완](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_LONG_VIDEO_RENDER_ADDENDUM_V1.md:3), 새 config와 복사 audit를 읽었다. 구현·기존 실험·원자료를 수정하지 않았다.
- 새 config와 기존 margin_only strike config의 차이는 diagnostic_seconds 5→15뿐이다. 복사한 margin_only_audit.json은 기존 audit와 SHA가 같다. native runner의 후보별 audit 경로와 새 중첩 config 경로가 맞는다.
- 검수 시점 wrapper 사전 입력 5개, native attempt 입력 1,318개는 현재 SHA와 모두 일치했다. Python AST 검사도 통과했다. native report는 아직 없어 완주·물리 결과를 선판정하지 않는다.

## 제어와 기록의 정합성

- [실행 래퍼 12–17행](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_long_video_v1.py:12)은 기존 native 실행 경로를 호출하고 추가 계획/config/audit 입력을 전후 검사한다. 기타 고정이나 상태 덮어쓰기, 새 물리 제어를 추가하지 않는다.
- [기존 EW 경로](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v7.py:9)는 마지막 waypoint 이후 보간을 끝값에 제한한다. 따라서 5–15초는 현재 기타 좌표계의 마지막 목표를 유지하는 구간이며, 왕복 타현을 추가하거나 이전 영상을 반복하는 구간이 아니다.
- 계획의 451프레임은 t=0을 포함한 30Hz 표본이므로 정상 완주 영상의 예상 재생 길이는 15.033333초다. 실제 프레임 수·15초 완주 여부·안전중단은 최종 native 자료에서 확인해야 한다.
- 첫 5초 비교는 초기값·물리 trace·접촉·최종 명령 등 실제 제어 자료를 대상으로 해야 한다. 원래 5초 종료 시각의 clock.diagnostic_time_limit은 15초 실행과 의도적으로 다를 수 있으므로 전체 control JSON 동일성을 무조건 요구하면 안 된다.

## 이전 발견사항의 해소

- 후처리 V1의 직접 사용 helper/계획 입력 pin 누락은 [V2 15행](/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_long_video_v2.py:15)의 initial_pose_noise_v1.py·본 계획·보완문서 추가로 해소됐다.
- clean 원본 MP4의 현재 SHA만 수집하던 문제는 [V2 19행](/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_long_video_v2.py:19)의 native media/videos.json 기록 SHA 대조로 해소됐다. 복사본 SHA와 입력 전후 SHA도 검사한다. V1은 미실행 상태로 보존한다.
- [V2 28–37행](/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_long_video_v2.py:28)의 clean은 native 카메라에 깊이검사 6줄 overlay가 있는 기존 영상을 사용한다. 아래 설명·범례·접촉 Xray 원은 제외한다. 순수 native 픽셀과 구분하는 보완문서 및 report.scope가 있어 사용자의 기존 줄 표시 요청과 이번 설명 제외 요청이 함께 유지된다.
- 설명 버전 3시점+합본, clean 3시점+합본의 8개 영상은 같은 물리 실행에서 파생된다. clean 합본만 재인코딩하며 실제 시간의 추가나 상태 변경은 없다.

## 해석 한계

이 검수는 코드·입력 구성의 사전 검수다. 결과 영상, 첫 5초의 실제 재현성, 마지막 상태, 프레임/길이는 아직 확인하지 않았다. 이전 margin_only의 왼손 접촉이 남는 제한은 유지되며, 왼손 독립 지지·수동 평형·학습된 연주 성공을 입증한 것으로 해석하지 않는다.

검수 시점 소스 SHA:

```json
{
  "/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_long_video_v1.py": "ec9d9bbfeccea88ae54005e61dfcb9574009e853b30036677a3471cdf676794f",
  "/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_long_video_v1.py": "af3bddde1a284ea5ddbf81d5984f6c76841f93f6a80a7940ba1034fe098c917f",
  "/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_long_video_v2.py": "440dd46349832a8a4e30a1e3842c729b7c98ac39c59eead2289bbadac6d8134b",
  "/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_LONG_VIDEO_PLAN_V1.md": "a39ffcb46db1d5b16889e42d4f2a4756d60a1deacd1d448b273b16181fe04b86",
  "/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_LONG_VIDEO_RENDER_ADDENDUM_V1.md": "267b7b54489077f0b9e01ea5a509f0b15942792c9b12f4209b94da075cdd52ef"
}
```
