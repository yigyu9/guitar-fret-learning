# 수동 기타 초기 배치 도구 실행 전 코드 검수

## 1차 검수 — 2026-10-08

요약 판정: 수정 권장. 물리 실행과 산출물 생성은 하지 않았다. 검수자의 변경은 이 문서 생성/append에 한정한다. 기존 자동 실험의 중단과 기존 소스·봉인 결과 보존은 유지한다.

Critical: 없음.

Warning:
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose.py:234` — 일반 인코딩 예외는 보고 후 정리하지만 `KeyboardInterrupt`는 `Exception`에 잡히지 않는다. 이 경우 `main`의 354~358행에서 `close()`를 거쳐 같은 recorder를 다시 인코딩한다(326행). encode 중 Ctrl-C도 실패 기록과 recorder 해제를 통과하도록 보완할 것을 root에 즉시 전달했다. 일반 ffmpeg 오류의 이전 재시도 문제는 228~248행 수정으로 해결된 것을 확인했다.

Suggestion:
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose.py:149` — 모든 기타 link에 동일 강체변환을 적용하는 수식(138~144행)은 맞다. 현재 native readback assertion은 root link만 검사한다. `/home/ajou/yigyu/3/stability_adapter_2/verify_interactive_guitar_pose.py:69`의 편집 검증에 각 link의 상대 pose 보존을 추가하면 재사용 native setter의 전체-link 동작도 직접 확인할 수 있다. 현 수식의 오류를 뜻하지 않으며 추가 물리 trial을 요구하는 지적은 아니다.

확인한 변경 범위:
- `/home/ajou/yigyu/3/stability_adapter_2/guitar_pose_edit.py:15` — world 회전은 좌곱, local 회전은 우곱이며 이동 local 축은 현재 quaternion으로 회전한다. 회전 시 actor root 위치를 유지하고 world 상대 회전은 `R_new R_ref^-1`로 기록한다.
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose.py:131` — 정지 EDIT에서만 기타 상태를 제출한다. 전체 guitar link의 기준 root에 대한 위치와 자세에 같은 변환을 적용하고 속도를 0으로 둔다. 사람 native 상태와 steps=0을 확인한다.
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose.py:184` — 초기값/trace를 만든 뒤 state/transform setter guard를 잠그고 PREVIEW에 들어간다. 한 preview에 1200 physics steps, 시작 포함 151 frames, 2개 영상이 있어야 completed다. 이후 advance는 멈춘다.
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose.py:213` — ON은 기존 strap force/PD/gravity/contact 경로, OFF는 cable force 호출 없이 simulate/fetch만 수행한다. OFF recorder에는 strap overlay도 없다. 별도 wrist 파형·feedback·policy 호출은 없다.
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose.py:250` — E는 이전 viewer/sim을 파괴하고 새 환경을 만든 다음 선택한 초기 pose를 다시 제출한다. 이동/회전·스트랩 변경은 PREVIEW에서 처리하지 않는다.
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose.py:76` — candidate는 baseline SHA와 boolean strap 입력을 확인한 뒤 유한 pose를 읽고, 새 후보는 exclusive 생성 경로에 absolute pose/초기각/constant PD targets/LA와 함께 저장한다.
- `/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose.py:67` — constructor 실패 시 장면을 정리한다. viewer 이벤트 조회는 재사용 Isaac Gym API의 list 반환 계약을 따르고 viewer 파괴 후 같은 viewer로 draw하지 않는다. launcher는 인자를 shell 배열 형태로 보존한다.
- `/home/ajou/yigyu/3/stability_adapter_2/verify_interactive_guitar_pose.py:51` — 실제 X11 키 이벤트, 6축 편집, 사람 상태 불변, guard 차단, 단일 5초 preview, 완료 후 정지, fresh scene 복원, 후보 reload를 검사하는 구조다. Xvfb 이벤트 검사는 사용자 데스크톱의 마우스 조작 검증과 구별해야 한다. 이 검수에서 검증 스크립트를 실행하지 않았다.

읽기 전용 검증: Python 4파일은 AST Python 3.8 문법 PASS, launcher는 bash -n PASS. baseline initial_values의 81 joint names/81 preserved targets와 입력 LA=1.1018469719600776m를 확인했다. native·unit test·recording·plot 실행은 0회다. 재사용 CameraEnvironment, InitialEnvironment, GymTrialRecording, StrapTrialRecording 및 로컬 Isaac Gym viewer API 문서를 읽었다.

검수 시 소스 SHA256:
- INTERACTIVE_GUITAR_POSE_PLAN.md: `ba3110af59ebe79096e32c77d365ab9f7663dec65088d8240f44fd187cd66dcd`
- guitar_pose_edit.py: `de493939aa944989d798628811bb18f7d10adb3e933f9233e82880b0c1891315`
- interactive_guitar_pose.py: `0a85f0d73ff30851acdf9fc491d26099ea6ee1203e49eb33265dc4c3a11963ae`
- open_guitar_pose_editor.sh: `005dd2dc27d530a934b9db9a5e65a25033c4d6cb68c26aed98b0bc6872045d05`
- tests/test_guitar_pose_edit.py: `04e11813e38760e9b130708e98fe08cc563053e653abf37e676761751aa7dd6a`
- verify_interactive_guitar_pose.py: `f959fb28350dc56a6b2a942cb1c733b6df4a713956c2e5112465c20bae49f5b3`

이 판정은 실행 전 코드 범위이며 native 검증 성공·안정성·연주 가능성을 인증하지 않는다.

## 보완 후 실행 전 최종 검수 — 2026-10-08

요약 판정: 문제없음. 실행 전 코드 판정: PASS.

Critical: 없음. Warning: 없음. 위 1차 검수의 Ctrl-C 종료 문제는 해결됐다. 전체 guitar link native readback 확대는 선택적 검증 제안으로 남으며 실행 차단 사유가 아니다.

`/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose.py:234`가 `BaseException`을 잡아 encode 중 KeyboardInterrupt도 failure report 저장, recorder=None, PREVIEW STOPPED 설정을 거친다(238~248행). 이어 main finally의 close에서는 recorder가 없어 같은 encode를 재호출하지 않는다. report에는 완료=false와 실제 예외 repr이 남고 이미 생긴 부분 파일은 삭제하지 않는다. 일반 encode 실패와 Ctrl-C 모두 같은 경로를 따른다.

`/home/ajou/yigyu/3/stability_adapter_2/verify_interactive_guitar_pose.py:59`의 synthetic InterruptedEncoding은 native 환경 생성 전 별도 경로에서 KeyboardInterrupt를 발생시켜 recorder 해제와 STOPPED를 검사한다. 해당 기록은 실제 5초 영상으로 설명하지 않는다. 이 추가 코드도 실행하지 않고 읽기와 AST 3.8 검사만 수행했다. 나머지 입력·물리·변환·viewer lifecycle 검수 결과는 위 기록과 같다.

최종 수정 파일 SHA256:
- interactive_guitar_pose.py: `47e1fe0ad2501b07468a28610d1d356a1e738a965bf6268978930911e2f04051`
- verify_interactive_guitar_pose.py: `3505214b589e824860f91536e8d30369d869276b2a94f13d975b3214cb67c44c`

나머지 4개 계획/helper/launcher/test SHA는 1차 기록과 같다. 검수자 native·단위검사·영상 생성 실행은 끝까지 0회이며, 실행 전 판정은 예정된 native smoke 검증의 성공을 대신하지 않는다.
