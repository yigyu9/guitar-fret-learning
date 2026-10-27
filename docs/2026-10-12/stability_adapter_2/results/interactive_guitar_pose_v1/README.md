# 수동 기타 초기 배치 편집기 v1

Isaac Gym viewer에서 기타의 초기 world 위치와 회전을 키보드로 직접 조정하고 후보로 저장하는 도구와 실제 preview 기록이다. 후보는 사용자가 편집해 저장한 값이며 자연스러운 최종 배치, 접촉·clearance, 안정성의 인증값이 아니다. 작업 범위와 키 설명은 [편집 계획](/home/ajou/yigyu/3/stability_adapter_2/INTERACTIVE_GUITAR_POSE_PLAN.md:1), 구현 위치는 [실행 파일](/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose.py:19)과 [pose 조작 함수](/home/ajou/yigyu/3/stability_adapter_2/guitar_pose_edit.py:15)다.

## 실행과 조작

그래픽 desktop의 DISPLAY가 설정된 터미널에서 실행한다. [wrapper](/home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_editor.sh:1)는 rl38 Python과 프로젝트 경로를 설정해 모듈을 실행한다.

```bash
bash /home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_editor.sh
bash /home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_editor.sh --no-strap
bash /home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_editor.sh --candidate /absolute/path/candidate/pose.json
```

F1–F3은 X/Y/Z 이동, F4–F6은 X/Y/Z 회전 축을 고른다. J/L은 선택축을 음/양 방향으로 이동하며 기본 increment는 2 mm 또는 1°, F를 눌러 정밀 모드로 바꾸면 0.5 mm 또는 0.25°다. Tab은 world/local 축, Z는 undo, R은 기준 기타 pose 복귀, T는 strap ON/OFF, C는 전체/손 카메라, G는 visual/collision geometry, S는 후보와 정지 장면 이미지를 저장한다. Space는 해당 pose에서 5초 free-physics preview, E는 새 환경에서 편집으로 복귀, H는 도움말, Esc는 종료다. 회전은 기타 actor root 원점을 pivot으로 한다. 사람 상태를 직접 마우스로 조작하는 검증은 포함하지 않는다.

## 보존한 실험 조건과 범위

기준은 기존 `initial_middle3_alignment_v1`의 저장 초기값이다. humanoid root와 하체는 고정되고, body 9개 관절은 기존 초기 PD 목표를 유지하며 Thorax부터 손가락까지 66개 관절의 기존 제어를 보존한다. 기타는 world Z-up의 자유 actor다. strap ON은 기존 rest length `1.1018469719600776 m`; OFF는 힘과 overlay 표시를 끈다. Preview는 일정한 PD 목표로만 실행되고 편집기에는 wrist 파형, feedback, actor/policy 학습이 없다. 편집은 시간 정지 상태의 초기 배치에서만 허용되고 preview가 시작되면 state setter를 잠근다. 5초 종료는 정해진 실행 구간의 끝이지 평형 상태 판정이 아니다.

## 저장 후보와 실제 preview

`candidate_000`은 기준 배치와 strap ON이며, `candidate_001`은 화면 조작의 6축 기능 확인을 위한 임의 편집 후보다. `candidate_002`는 같은 편집 pose의 strap OFF 값이다. 세 후보 모두 도구 기능검증에서 저장한 시험 입력으로, 자동 선택이나 자연스러운 배치 채택을 뜻하지 않는다. 각 후보의 world 위치, xyzw quaternion, 기준 대비 delta, 실제 초기 joint angles/PD targets, strap 조건은 해당 [candidate_000](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/session/candidate_000/pose.json:1), [candidate_001](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/session/candidate_001/pose.json:1), [candidate_002](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/session/candidate_002/pose.json:1) JSON에 있다.

아래 정지 장면들은 실제 Isaac Gym native camera capture다. 첫 이미지는 기준 candidate_000의 전체 장면, 다음 두 이미지는 편집 candidate_001의 전체 장면과 손 camera다. Strap route는 주황색 실제 경로 overlay이며 천의 두께·처짐이나 추가 물리를 나타내지 않는다. 정지 장면만으로 실제 접촉이나 형상 clearance를 인증하지 않는다.

![기준 배치 candidate_000 전체 장면, native t=0 capture](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/session/candidate_000/images/frames/whole_body/00000.png)

![수동 편집 candidate_001 전체 장면, native t=0 capture](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/session/candidate_001/images/frames/whole_body/00000.png)

![수동 편집 candidate_001 손 camera, native t=0 capture](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/session/candidate_001/images/frames/hands/00000.png)

`preview_000`은 편집 pose에서 strap ON으로 기록한 실제 native 실행이다. [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/session/preview_000/report.json:1)는 `completed=true`, 1200 physics steps/5.000 s, 151 frames, 두 영상 모두 151 frames/30 fps/5.033333 s, post-start state writes 0, 의도적 blocked write 1을 기록한다. [초기값과 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/session/preview_000/initial_values.json:1)는 preview 입력과 상태를 보존한다. 아래는 저장된 실제 native 영상이며 과학 그래프나 접촉 인증이 아니다.

![preview_000 실제 Isaac Gym whole-body 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/interactive_guitar_pose_v1__preview_000__whole_body.mp4)

![preview_000 실제 Isaac Gym hands 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/interactive_guitar_pose_v1__preview_000__hands.mp4)

각 중앙 영상은 preview 원본과 SHA-256 exact copy다. 파일 SHA는 whole-body `45aa95d3c26364385016d3f255fac7a1d11f1626bae1f5faf5d9a4dc2d2f1244`, hands `26d66c1df88d2635fb5c1c5dadef6c45e2ba60721a29b4eea229f87dca0044a1`이다. 누적 인덱스 [VIDEO_INDEX_v18](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v18.md:1)은 기존 v17 170개를 유지하고 이 preview 영상 두 개를 더해 172개로 기록한다.

## 실행·검증 기록 해석

Static v2 검증은 27/27 checks가 true이고 `new_physics_steps=0`으로 완료됐다. fresh native static scene에서 X11 F3/L 입력으로 Z +2 mm를 확인했고, 전체 기타 link의 상대 pose 오차는 위치 최대 `9.357739674962331e-08 m`, 회전 최대 `1.8212640260610922e-07 rad`였다. 초기 human state, 81개 PD target 및 PD properties는 기준과 exact 일치했다. 6축 편집/undo, camera·geometry toggle, save/reload와 정적 strap OFF capture도 확인했다. [static verification 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/static_verification_v2/verification.json:1)를 참조한다. strap OFF는 이번에 5초 물리 preview를 실행하지 않았으며 정적 OFF 표시와 raw native recorder 분기만 검사했다.

원 native harness는 마지막 JSON 직렬화에서 `numpy.bool_` 오류로 exit 1이 났고 truncated verification 및 원 log를 보존했다. 이 실패를 성공으로 바꾸지 않으며, 위에서 별도로 보고한 completed strap-ON `preview_000`과 혼동하지 않는다. 별도의 첫 source-copy 준비는 external font 경로 `relative_to` 오류로 native 실행 전에 멈췄다. 첫 `source_before`에는 오류 전에 부분 복사된 14,029개 파일이 있고, 두 번째 `source_before_v2`에는 14,030개 파일이 있다. 두 세트는 runtime import 위치가 아니라 보존본이다. 원 [preparation_failure.txt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/preparation_failure.txt:1)의 “empty” 설명은 부정확하며, 파일을 수정하지 않고 [preparation correction](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/preparation_correction.json:1)에 실제 파일 수와 정정 근거를 기록했다. 이후 v2 sourcecopy는 external 경로를 별도 매핑해 원본 입력을 보존했다. [준비 실패 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/preparation_failure.txt:1), [원 실행 log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_execution.log:1), [원 truncated verification](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/verification.json:1), [preflight review](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/review_preflight.md:1), [review 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/review_final.md:1)에 각 이력을 분리해 남겼다. 최종 보존 감사는 root 담당이다.
