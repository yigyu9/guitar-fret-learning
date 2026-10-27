# Quiet 기타 오차 feedback — Y/Z 보정 OFF/ON 두 실제 5초 응답

## 실험 범위와 기준 자료

새 native trial은 OFF와 ON 각각 한 번 초기화해 1200 physics step(시뮬레이션 5.000초), 151 frame을 완료했다. 두 신규 조건은 총 2 initialization/2400 step이며 actor inference·학습 update·constraint violation은 모두 0이다. `analysis.json`의 56개 검사가 모두 통과했다. 기준 baseline은 이전 `initial_middle3_alignment_v1`에 저장한 자료이며 이번 세 번째 실행이 아니다([baseline 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/initial_values.json:1), [baseline report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/report.json:1)). OFF는 새 실행이지만 baseline의 전체 native states/trace와 81개 관절 목표가 exact하게 일치한다.

두 조건은 동일한 81관절 초기 상태와 초기 목표, 기타 world p/q 목표, 자유 기타, 고정 root·하체, 절대 strap rest length `1.1018469719600776 m`, 원래 PD, 몸통 9관절 KP×2·KD×√2, 기존 손목 X 사인 목표와 손가락 목표를 유지했다. 시작 왼손목 actual은 `L_Wrist_y=0.176372841 rad`, `L_Wrist_z=−0.273562908 rad`다. ON에서는 현재 기타 world 위치·회전 오차를 사용해 60 Hz마다 Y/Z 목표 delta를 갱신했고, 각 축 목표 범위 ±0.005 rad, 유효 변화율 한 축 최대 0.002 rad/s로 제한했다. source actor와 training은 사용하지 않았다. 두 신규 run은 각각 106개 직접 입력의 전후 SHA와 실행 사본/닫힌 로그를 기록했다.

OFF와 ON은 처음 484개 전체 81관절 명령, 첫 2초 native prefix, 다른 79개 목표와 모든 손가락 목표가 baseline과 exact하게 일치한다. 첫 ON 상태 분기는 step 485다. 두 조건 모두 각 한 번의 fresh 15-check direct-source gate를 통과했고 검사 대상 self-screen pair는 1188개였다.

## 기타 오차와 보정 결과

| 측정값 | OFF | ON |
|---|---:|---:|
| 최대 초기 위치 오차 (mm) | 14.608483 | 14.608483 |
| 최대 초기 회전 오차 (°) | 2.918412 | 2.897193 |
| 종료 위치 오차 (mm) | 13.819696 | 13.665215 |
| 종료 회전 오차 (°) | 2.918277 | 2.889313 |
| 후기 완전 1초 최대 위치 변화 (mm) | 0.648625 | 0.693968 |
| 후기 완전 1초 최대 회전 변화 (°) | 0.115306 | 0.124492 |

ON은 종료 위치·회전 오차를 각각 약 0.154481 mm와 0.028964° 줄였고, 후기 1초 최대 변화는 약간 커졌다. 작은 차이를 성공/실패 판정으로 과장하지 않는다. ON의 최종 보정은 `δY=−0.005 rad`, `δZ=+0.003548712 rad`였으며 최대 유효 rate는 `0.002000000000000014 rad/s`다. 최대 초기 위치 오차는 두 조건이 같고 2초 feedback 시작 전의 값이다. 이번 결과는 이 한 조건의 끝점 오차 변화이며 자연스러운 연주, 전역 제어 안정성 또는 policy 호환성을 인증하지 않는다.

![baseline, feedback OFF, feedback ON의 기타 초기 world 위치·회전 오차, ON/OFF 보정 delta와 baseline 대비 동시점 기타 위치 거리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/artifacts/quiet_wrist_yz_feedback_response.png)

그림은 저장 시계열을 이용한 2×2 과학 도표다. 좌상단은 초기 world 기타 위치 목표 대비 오차(mm), 우상단은 초기 방향 대비 회전 오차(°), 좌하단은 OFF/ON의 Y/Z 보정 delta(rad), 우하단은 OFF/ON 기타 world 위치와 저장 baseline 사이의 동시점 거리(mm)다. 위치·회전·actual 상태는 1201점 `t=k/240 s`, 보정 delta 및 PD target은 1200 post-step 표본 `t=1..1200/240 s`를 쓴다. 목표 갱신은 60 Hz held 제어다. 실제 PNG는 root가 열어 네 패널의 값·단위·시간·캡션과 범례가 맞는지 확인했다. 이 도표는 실제 Gym 장면 렌더가 아니다.

## 저장한 실제 장면과 영상

각 조건의 t0/t5 실제 native frame과 손·전신 camera 영상은 아래에 있다. MP4는 151 frame/30 fps이므로 재생시간은 5.033333초이며 마지막 물리 표본은 5.000초다. v17 index에 추가한 네 복사본은 native 원본과 바이트 SHA가 일치한다. strap은 표시된 경로 overlay이며 천 mesh가 아니다.

### OFF

- [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/off/initial_values.json:1), [실행 report와 gate 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/off/report.json:1), [capture/frame metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/off/capture.json:1), [videos/ffprobe metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/off/videos.json:1), [15-check 초기 source gate](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/off/initial_grip_audit.json:1)

| 시각 | 손 camera | 전신 camera |
|---|---|---|
| t=0.000 s | ![OFF 시작 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/off/frames/hands/00000.png) | ![OFF 시작 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/off/frames/whole_body/00000.png) |
| t=5.000 s | ![OFF 종료 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/off/frames/hands/00150.png) | ![OFF 종료 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/off/frames/whole_body/00150.png) |

![Feedback OFF 실제 손 camera 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/quiet_wrist_yz_feedback_v1__native__off__hands.mp4)

![Feedback OFF 실제 전신 camera 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/quiet_wrist_yz_feedback_v1__native__off__whole_body.mp4)

### ON

- [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/on/initial_values.json:1), [실행 report와 gate 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/on/report.json:1), [capture/frame metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/on/capture.json:1), [videos/ffprobe metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/on/videos.json:1), [15-check 초기 source gate](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/on/initial_grip_audit.json:1)

| 시각 | 손 camera | 전신 camera |
|---|---|---|
| t=0.000 s | ![ON 시작 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/on/frames/hands/00000.png) | ![ON 시작 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/on/frames/whole_body/00000.png) |
| t=5.000 s | ![ON 종료 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/on/frames/hands/00150.png) | ![ON 종료 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/native/on/frames/whole_body/00150.png) |

![Feedback ON 실제 손 camera 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/quiet_wrist_yz_feedback_v1__native__on__hands.mp4)

![Feedback ON 실제 전신 camera 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/quiet_wrist_yz_feedback_v1__native__on__whole_body.mp4)

전체 170개 영상은 [VIDEO_INDEX_v17](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v17.md:1)에서 찾을 수 있다.

## 접촉, 실제 관절 변화와 한계

두 trial에서 palm 양의 raw lambda 접촉은 0이고 Palm-up proxy는 true였다. 이는 실제 힘이나 force closure 증명이 아니다. `LH:thumb3` raw lambda 양의 접촉 step은 OFF 587/ON 603, `LH:index3`는 두 조건 모두 1156이다. Raw lambda를 N 단위 지지력으로 해석하지 않는다. native 실제 관절 한계 초과 최대는 OFF/ON 모두 `0.000099949539 rad`다. body9의 PD 목표는 유지됐지만 실제 `Spine_z` 좌표 변화는 OFF `0.061757788 rad`, ON `0.061760515 rad`였다. 이는 세계 몸통 SO(3) 회전량이 아니다. Root·하체는 고정이고 기타는 자유롭게 움직였다.

## 영상 수집 wrapper 오류와 별도 회수 검증

4개 완료 MP4 복사, `VIDEO_INDEX_v17.md`, `video_collection_update_v16.json` 생성까지 collector가 수행했다. 그 뒤 collection wrapper의 마지막 metadata Python이 argv slice `sys.argv[4:7]`의 세 항목을 네 변수로 unpack하면서 `ValueError`가 발생해 wrapper terminal exit 1로 끝났다. 이는 영상 또는 물리 trial 실패가 아니다. 원 wrapper·archive·사전 invocation·닫힌 log·선택 사본·네 복사본과 index/update를 보존했고 수정이나 재실행은 하지 않았다. Collector 자체의 exit status와 wall time은 저장되지 않았으며 `collection_execution.json`은 생성되지 않았다. 존재하지 않는 성공 metadata나 exit 0을 추정하지 않는다.

Root의 별도 read-only 회수 검증은 9개 검사와 2178개 입력 SHA를 통과했다. 원 2133개 사전 입력의 SHA/current, 34개 selected source copy, 이전 166개 동영상과 v16 index, 새 네 원본/복사본 SHA, 총170개 동영상 및 v17의 이전 index 내용 보존을 대조했다. 이 recovery 결과는 실패한 wrapper 실행과 분리된 검증 기록이다. [회수 감사 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/collection_recovery.json:1), [wrapper failure 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/collection_wrapper_failure.json:1), [root verification notes](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/ROOT_VERIFICATION_NOTES.md:1)를 참고한다. Recovery는 collector 재실행이나 새 물리 실행을 의미하지 않는다.

분석 보존은 직접 입력 1956개가 wrapper 1962개 closure에 포함되고 선택 사본은 11개다. Plot 단계는 직접 입력 1960개가 wrapper 1969개 closure에 포함되고 선택 사본은 32개다. 각 단계의 native 원본 경로와 전체 closure SHA를 선택 사본 집계와 분리해 기록했다. plot PNG의 SHA는 `a611a5a003e3274e8aa9d9cecb36110694c01899b76fb3e979c7b483c95403cd`다. [분석 결과 56 checks](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/analysis.json:1), [시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/series.json:1), [Root verification notes](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/ROOT_VERIFICATION_NOTES.md:1)를 보존했다.

다음 제안은 feedback 시작을 0초로 당기되 각도 한계 ±0.005 rad를 유지하고, 기존 rate의 slow와 5배 fast 두 조건으로 초기 오차를 측정하는 것이다. 이 제안은 [startup feedback 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_YZ_STARTUP_FEEDBACK_PLAN.md:1)에 있으며 아직 구현·실행되지 않았다. 유지 구간에서 관측한 응답이 startup에도 유효하다는 근거는 없다. 자연 연주, 전체 폐루프 안정성, 정책 호환성은 계속 미검증이다.
